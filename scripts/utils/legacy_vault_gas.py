"""Pinned Base gas experiment; all state changes are explicit fork-only diagnostics."""
import copy
import json
from collections import Counter
from eth_utils import keccak
from eth_utils.abi import collapse_if_tuple
from vyper.cli.vyper_json import compile_json
import boa

from scripts.verify_legacy_vault_cutover import ROOT, SUFFIX, attach
from scripts.utils.legacy_vault_compat import PREVIOUS_SUFFIX, address, require

ALLOWANCE = 8_000_000
TX_BUDGET = 16_000_000


def cold():
    # Boa 0.2.7 keeps access warmth and transient caches between calls.
    boa.env.evm.reset_access_counters()
    boa.env.evm.vm.state.clear_transient_storage()


def walk(computation):
    yield computation
    for child in computation.children:
        yield from walk(child)


def layout(record):
    output = compile_json(copy.deepcopy(record["solc_json"]))
    require(not output.get("errors"), "GAS_LAYOUT_COMPILATION")
    return next(iter(output["contracts"][record["file"]].values()))["layout"]["storage_layout"]


def write(target, fields, module, name, keys, value):
    slot = (fields[module] if module else fields)[name]["slot"]
    for key in keys:
        key = int(str(key), 16) if isinstance(key, str) else key
        slot = int.from_bytes(keccak(slot.to_bytes(32, "big") + key.to_bytes(32, "big")), "big")
    boa.env.set_storage(target, slot, int(str(value), 16) if isinstance(value, str) else value)


def measure(records, evidence):
    hq, pool = attach(records, "RipeHq"), attach(records, "StabilityPool")
    book = attach(records, "VaultBook" + SUFFIX)
    mc, pd = attach(records, "MissionControl", hq.getAddr(5)), attach(records, "PriceDesk", hq.getAddr(7))
    lp = pool.vaultAssets(2)
    sg, green = hq.getAddr(2), hq.getAddr(1)
    saved = json.loads((ROOT / "docs/chains/base/fork-rehearsal/full-update-final.json").read_text())
    positions = [r for r in saved["positions"]["1"].values() if r["shares"] and address(r["asset"]) == address(lp)]
    user = next(r["user"] for r in positions if pool.userBalances(r["user"], lp))
    index = pool.indexOfUserAsset(user, lp)
    inventory = []
    assets = [pool.claimableAssets(lp, i) for i in range(1, pool.numClaimableAssets(lp))]
    for asset in assets:
        cold()
        price = pd.getPrice(asset, True)
        trace = pd._computation
        inventory.append({"asset": str(asset), "claim_balance": pool.claimableBalances(lp, asset), "unit_price": price,
                          "cold_price_gas": trace.get_gas_used(),
                          "route_calls": list(dict.fromkeys("0x" + c.msg.code_address.hex() + ":" + bytes(c.msg.data)[:4].hex() for c in walk(trace)))})
    evidence.update(units="EVM execution gas; excludes intrinsic gas", allowance_per_optional_read=ALLOWANCE,
                    transaction_budget=TX_BUDGET, inventory=inventory, original_claim_count=len(assets),
                    price_desk=str(pd.address), price_sources=[str(pd.getAddr(i)) for i in range(1, pd.numAddrs())],
                    funded_probe_user=user, measurements={}, fork_only_overrides=[])
    require(len(assets) == 11, "LIVE_INVENTORY_DRIFT")
    # Real token routes configured in the pinned desk; no oracle code, feed,
    # price or token custody is changed. Added claim-ledger dust models read
    # cost, not redeemable or custodied new claims.
    additional = [mc.assets(i) for i in range(1, mc.numAssets())]
    additional += ["0x820C137fa70C8691f0e44Dc420a5e53c168921Dc", "0x60a3e35cc302bfa44cb288bc5a4f316fdb1adb42"]
    stress = list(assets)
    for asset in additional:
        if any(address(asset) == address(a) for a in (*stress, lp, sg, green)):
            continue
        cold()
        if pd.getPrice(asset, True) != 0:
            stress.append(asset)
    require(len(stress) == 26, "STRESS_INVENTORY_COUNT:" + str(len(stress)))
    evidence["stress_claims"] = [str(a) for a in stress]
    baseline = {}
    evidence["active_configuration_reads"] = baseline
    for getter in ("getTotalAmountForUser", "getTotalUserValue"):
        cold(); getattr(pool, getter)(user, lp)
        baseline[getter] = {"cold": pool._computation.get_gas_used()}
        getattr(pool, getter)(user, lp); baseline[getter]["warm"] = pool._computation.get_gas_used()
    cold(); book.getDeleverageTraversalAsset(user, pool.address, index, True)
    baseline["traversal"] = {"cold": book._computation.get_gas_used()}
    book.getDeleverageTraversalAsset(user, pool.address, index, True)
    baseline["traversal"]["warm"] = book._computation.get_gas_used()
    pool_layout = layout(records["StabilityPool"])
    hq_layout = layout(records["RipeHq"])
    # Candidate-pointer simulation is solely an execution gas diagnostic,
    # not a final activation rehearsal or permission audit.
    roles = {5: "MissionControl", 13: "CreditEngine", 16: "Lootbox", 17: "Teller", 20: "TellerUtils", 21: "EndaomentFunds"}
    replacements = {i: records[n + PREVIOUS_SUFFIX]["address"] for i, n in roles.items()}
    replacements.update({6: records["Switchboard" + SUFFIX]["address"], 8: book.address,
                         9: records["AuctionHouse" + SUFFIX]["address"], 18: records["Deleverage" + SUFFIX]["address"]})
    for i, target in replacements.items():
        old = hq.getAddr(i)
        write(hq.address, hq_layout, "registry", "addrInfo", [i], target)
        write(hq.address, hq_layout, "registry", "addrToRegId", [old], 0)
        write(hq.address, hq_layout, "registry", "addrToRegId", [target], i)
    evidence["fork_only_overrides"].append({"kind": "HQ candidate-pointer diagnostic", "slots": replacements})
    staged_mc = attach(records, "MissionControl" + PREVIOUS_SUFFIX)
    copied = []
    for i in range(1, mc.numAssets()):
        asset = mc.assets(i)
        staged_mc.setAssetConfig(asset, mc.assetConfig(asset), sender=records["SwitchboardAlpha" + SUFFIX]["address"])
        require(tuple(staged_mc.assetConfig(asset)) == tuple(mc.assetConfig(asset)), "GAS_CONFIG_COPY")
        copied.append(str(asset))
    evidence["fork_only_overrides"].append({"kind": "copy active asset policy into staged MissionControl", "assets": copied})
    dl = attach(records, "Deleverage" + SUFFIX)
    teller = attach(records, "Teller" + PREVIOUS_SUFFIX)
    # Pause flags are staging controls; explicitly open them only in this
    # disposable gas branch, using the registered controller authority.
    for name in ("Teller", "CreditEngine", "Lootbox"):
        candidate = attach(records, name + PREVIOUS_SUFFIX)
        if candidate.isPaused():
            candidate.pause(False, sender=records["SwitchboardAlpha" + SUFFIX]["address"])
            evidence["fork_only_overrides"].append({"kind": "unpause candidate for gas", "contract": name})
    ledger = attach(records, "Ledger", hq.getAddr(4))
    ce = attach(records, "CreditEngine" + PREVIOUS_SUFFIX)
    borrowers = {u.lower() for u in saved["borrowers"]}
    users = [r["user"] for r in positions if r["user"].lower() in borrowers and r["amount"] > 10**18 and ledger.userDebt(r["user"])[0] > 10**18]
    require(len(users) >= 4, "GAS_BORROWER_SAMPLE")
    evidence["batch_users"] = users[:4]
    for count in (11, 26):
        if count == 26:
            for i, asset in enumerate(stress, 1):
                write(pool.address, pool_layout, "stabVault", "claimableAssets", [lp, i], asset)
                write(pool.address, pool_layout, "stabVault", "indexOfClaimableAsset", [lp, asset], i)
                if asset not in assets:
                    write(pool.address, pool_layout, "stabVault", "claimableBalances", [lp, asset], 1)
            write(pool.address, pool_layout, "stabVault", "numClaimableAssets", [lp], 27)
            evidence["fork_only_overrides"].append({"kind": "26 distinct priced non-GREEN claim entries", "new_entry_balance": 1, "custody_or_prices_modified": False})
        if count == 26:
            # Qualify the same 26 reads under active MissionControl as well;
            # its priority source order differs from the staged defaults.
            write(hq.address, hq_layout, "registry", "addrInfo", [5], mc.address)
            active_stress = {}; evidence["active_configuration_26_reads"] = active_stress
            for getter in ("getTotalAmountForUser", "getTotalUserValue"):
                cold(); getattr(pool, getter)(user, lp)
                active_stress[getter] = pool._computation.get_gas_used()
                print("ACTIVE_STRESS_GAS", getter, active_stress[getter], flush=True)
                require(active_stress[getter] < ALLOWANCE, "ACTIVE_OPTIONAL_GAS_ALLOWANCE")
            write(hq.address, hq_layout, "registry", "addrInfo", [5], staged_mc.address)
        row = {}; evidence["measurements"][str(count)] = row
        for name in ("getTotalAmountForUser", "getTotalUserValue"):
            cold(); result = getattr(pool, name)(user, lp)
            row[name] = {"cold": pool._computation.get_gas_used(), "result": result}
            getattr(pool, name)(user, lp); row[name]["warm"] = pool._computation.get_gas_used()
            print("LIVE_GAS", count, name, row[name], flush=True)
            require(row[name]["cold"] < ALLOWANCE, "OPTIONAL_GAS_ALLOWANCE")
        cold(); result = book.getDeleverageTraversalAsset(user, pool.address, index, True)
        row["traversal"] = {"cold": book._computation.get_gas_used()}
        require(result[1] == row["getTotalAmountForUser"]["result"] and result[1] > 0, "GAS_NAV")
        book.getDeleverageTraversalAsset(user, pool.address, index, True)
        row["traversal"]["warm"] = book._computation.get_gas_used()
        cold(); dl.getDeleverageInfo(user); row["info"] = dl._computation.get_gas_used()
        for size in (1, 2, 4):
            before = [ce.getLatestUserDebtAndTerms(u, False)[0][0] for u in users[:size]]
            cold()
            with boa.env.anchor():
                paid = teller.deleverageManyUsers([(u, 10**18) for u in users[:size]], sender=dl.address, gas=64_000_000)
                gas = teller._computation.get_gas_used()
                require(paid > 0 and all(ledger.userDebt(u)[0] < d for u, d in zip(users[:size], before)), "GAS_SETTLEMENT")
                selectors = {keccak(text=a["name"] + "(" + ",".join(collapse_if_tuple(i) for i in a["inputs"]) + ")")[:4]: a["name"]
                             for a in records["StabilityPool"]["abi"] if a["type"] == "function"}
                calls = Counter(selectors.get(bytes(c.msg.data)[:4], "unknown") for c in walk(teller._computation)
                                if c.msg.code_address == bytes.fromhex(str(pool.address)[2:]))
                row["batch_" + str(size)] = {"gas": gas, "repaid": paid, "pool_calls": dict(calls),
                                            "fits_operational_budget": gas <= TX_BUDGET * 8 // 10}
                print("LIVE_GAS", count, "batch", size, gas, flush=True)
    evidence["measurement_outer_limit"] = 64_000_000
    evidence["measurement_limit_note"] = "64M is diagnostic-only so unsupported batches can be measured to completion; operator budget remains 16M with 20% reserved headroom."
    evidence["supported_max_batch_by_inventory"] = {
        count: max([0] + [size for size in (1, 2, 4) if row["batch_" + str(size)]["fits_operational_budget"]])
        for count, row in evidence["measurements"].items()
    }
    evidence["preflight_requirement"] = "Strict probes pass for all included cohorts; estimate exact batch <= 12.8M gas with a 16M budget. Quarantine failed/expensive cohorts. ABI ceiling 25 is not an operational allowance."
    evidence["passed"] = True
