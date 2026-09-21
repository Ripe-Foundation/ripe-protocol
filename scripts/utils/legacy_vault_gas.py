"""Pinned Base gas experiment; all state changes are explicit fork-only diagnostics."""
import copy
import json
from collections import Counter
from eth_utils import keccak
from eth_abi import decode
from eth_utils.abi import collapse_if_tuple
from vyper.cli.vyper_json import compile_json
import boa

from scripts.verify_legacy_vault_cutover import ROOT, SUFFIX, attach
from scripts.base_upgrade_fork import HQ_IDS
from scripts.utils.legacy_vault_compat import PREVIOUS_SUFFIX, address, require

ALLOWANCE = 8_000_000
TX_BUDGET = 16_000_000
REPLACEMENT_ROLES = {slot: HQ_IDS[slot] for slot in (5, 13, 15, 16, 17, 20, 21)}


def verify_department_graph(hq, replacements, retained_endaoment):
    """Reject a rehearsal wired to old HR or a clobbered Endaoment slot."""
    require(address(hq.getAddr(14)) == address(retained_endaoment), "GAS_ENDAOMENT_CHANGED")
    for slot, target in replacements.items():
        require(address(hq.getAddr(slot)) == address(target), f"GAS_HQ_ADDRESS:{slot}")
        require(hq.getRegId(target) == slot and hq.isValidRegId(slot), f"GAS_HQ_IDENTITY:{slot}")


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
    """Actual release configuration; all pointer/claim edits stay in this fork."""
    import hashlib
    from scripts.legacy_vault_preflight import reconcile, probe
    hq, pool = attach(records, "RipeHq"), attach(records, "StabilityPool")
    retained_endaoment = hq.getAddr(14)
    book = attach(records, "VaultBook" + SUFFIX)
    hq_layout, pool_layout = layout(records["RipeHq"]), layout(records["StabilityPool"])
    evidence.update(units="EVM execution gas; add intrinsic gas to funded limits", allowance_per_optional_read=ALLOWANCE,
                    transaction_budget=TX_BUDGET, operational_execution_limit=12_800_000, measurements={}, fork_only_overrides=[])
    def point(slot, target):
        old = hq.getAddr(slot)
        write(hq.address, hq_layout, "registry", "addrInfo", [slot], target)
        write(hq.address, hq_layout, "registry", "addrToRegId", [old], 0)
        write(hq.address, hq_layout, "registry", "addrToRegId", [target], slot)
    # Foxtrot must finish config while the candidate MC is inactive.
    point(6, records["Switchboard" + SUFFIX]["address"])
    setup = attach(records, "SwitchboardFoxtrotSetup" + PREVIOUS_SUFFIX)
    while setup.initStep() < 5:
        setup.initConfig(sender=hq.governance(), gas=64_000_000)
    replacements = {i: records[n + PREVIOUS_SUFFIX]["address"] for i, n in REPLACEMENT_ROLES.items()}
    replacements.update({7: records["PriceDeskBridge" + PREVIOUS_SUFFIX]["address"],
                         6: records["Switchboard" + SUFFIX]["address"], 8: book.address,
                         9: records["AuctionHouse" + SUFFIX]["address"], 18: records["Deleverage" + SUFFIX]["address"]})
    for slot, target in replacements.items():
        point(slot, target)
    verify_department_graph(hq, replacements, retained_endaoment)
    setup.initRewards(sender=hq.governance(), gas=64_000_000)
    mc, pd = attach(records, "MissionControl" + PREVIOUS_SUFFIX), attach(records, "PriceDeskBridge" + PREVIOUS_SUFFIX)
    dl, teller = attach(records, "Deleverage" + SUFFIX), attach(records, "Teller" + PREVIOUS_SUFFIX)
    for name in ("Teller", "CreditEngine", "Lootbox"):
        candidate = attach(records, name + PREVIOUS_SUFFIX)
        if candidate.isPaused():
            candidate.pause(False, sender=records["SwitchboardAlpha" + SUFFIX]["address"])
    evidence["fork_only_overrides"].append({"kind": "candidate HQ pointers plus actual Foxtrot Defaults config/rewards sequence and candidate unpause", "slots": replacements})
    evidence.update(price_desk=str(pd.address), mission_control=str(mc.address), defaults=str(setup.defaults()),
                    price_config=list(mc.getPriceConfig()), price_source_price_gas=pd.PRICE_SOURCE_PRICE_GAS(),
                    price_source_snapshot_gas=pd.PRICE_SOURCE_SNAPSHOT_GAS(), gen_liq_config=list(mc.getGenLiqConfig()), foxtrot_final={"initStep": setup.initStep(), "nextAssetIndex": setup.nextAssetIndex(), "rewardsInitialized": setup.rewardsInitialized()},
                    price_sources=[{"id": i, "address": str(pd.getAddr(i)), "valid": pd.isValidRegId(i),
                                    "runtime_sha256": hashlib.sha256(boa.env.get_code(pd.getAddr(i))).hexdigest()} for i in range(1, pd.numAddrs())],
                    active_hq={str(i): str(hq.getAddr(i)) for i in range(1, hq.numAddrs())},
                    runtime_sha256={str(slot): hashlib.sha256(boa.env.get_code(target)).hexdigest() for slot, target in replacements.items()})
    sg, green, lp = hq.getAddr(2), hq.getAddr(1), pool.vaultAssets(2)
    ledger, ce = attach(records, "Ledger", hq.getAddr(4)), attach(records, "CreditEngine" + PREVIOUS_SUFFIX)
    saved = json.loads((ROOT / "docs/chains/base/fork-rehearsal/full-update-final.json").read_text())
    users = sorted({r["user"] for r in saved["positions"]["1"].values() if r["shares"]})
    groups = {"lp": [], "sg": [], "mixed": []}
    positions = {}
    evidence["rejected_borrower_samples"] = []
    for user in users:
        balances = [int(pool.userBalances(user, asset)) for asset in (lp, sg)]
        if not any(balances) or ledger.userDebt(user)[0] < 2 * 10**18:
            continue
        values = [pool.getTotalUserValue(user, asset) if balance else 0 for asset, balance in zip((lp, sg), balances)]
        if sum(values) < 2 * 10**18:
            continue
        kind = "mixed" if all(balances) else "lp" if balances[0] else "sg"
        groups[kind].append(user)
        positions[user] = {"shares": balances, "values": values, "debt": ce.getLatestUserDebtAndTerms(user, False)[0][0],
                           "indices": [pool.indexOfUserAsset(user, asset) for asset in (lp, sg)]}
        cold()
        try:
            strict_debt = ce.getLatestUserDebtAndTerms(user, True, gas=64_000_000)[0][0]
        except Exception:
            output = bytes(ce._computation.output)
            reason = decode(["string"], output[4:])[0] if output[:4] == keccak(text="Error(string)")[:4] else output.hex()
            evidence["rejected_borrower_samples"].append({"user": user, "reason": reason, "stage": "strict current collateral valuation", "gas_used": ce._computation.get_gas_used()})
            continue
        positions[user]["debt"] = strict_debt
    require(all(groups.values()), "GAS_COHORT_SAMPLE")
    rejected = {row["user"] for row in evidence["rejected_borrower_samples"]}
    evidence["all_sample_groups"] = {kind: list(users) for kind, users in groups.items()}
    groups = {kind: [u for u in users if u not in rejected] or users for kind, users in groups.items()}
    evidence["representative_inventory"] = {"source": "historical census, each sample balance/debt re-read at pinned block; not complete current user inventory", "groups": groups, "positions": positions}
    inventory, original = {}, {}
    for kind, asset in (("lp", lp), ("sg", sg)):
        claims = [pool.claimableAssets(asset, i) for i in range(1, pool.numClaimableAssets(asset))]
        original[kind] = claims
        inventory[kind] = []
        for claim in claims:
            cold()
            quote = pd.getPrice(claim, True)
            trace = pd._computation
            inventory[kind].append({"asset": str(claim), "claim_balance": pool.claimableBalances(asset, claim), "unit_price": quote,
                                   "cold_price_gas": trace.get_gas_used(), "route_calls": list(dict.fromkeys("0x" + c.msg.code_address.hex() + ":" + bytes(c.msg.data)[:4].hex() for c in walk(trace)))})
    evidence["inventory"] = inventory
    require(len(original["lp"]) == 11, "LIVE_INVENTORY_DRIFT")
    # Preserve the exact previously measured stress inventory. A newly failing
    # route is a qualification failure, never replaced by a cheaper asset.
    stress = json.loads((ROOT / "docs/chains/base/legacy-vault-rehearsal/review-qualification.json").read_text())["gas_diagnostic"]["stress_claims"]
    require(len(stress) == 26 and len({address(a) for a in stress}) == 26, "STRESS_INVENTORY_COUNT")
    evidence["stress_claims"] = stress
    evidence["stress_price_probes"] = []
    for asset in stress:
        cold()
        quote = probe(pd.address, "getPrice(address,bool)", ["address", "bool"], [asset, True])
        evidence["stress_price_probes"].append({"asset": str(asset), "probe": quote})
    l, s, m = groups["lp"], groups["sg"], groups["mixed"]
    cases = {"lp_1": [(l[0], 10**18)], "sg_1": [(s[0], 10**18)], "mixed_holder_1": [(m[0], 10**18)],
             "lp_then_sg": [(l[0], 10**18), (s[0], 10**18)], "sg_then_lp": [(s[0], 10**18), (l[0], 10**18)],
             "mixed_then_sg": [(m[0], 10**18), (s[0], 10**18)], "sg_then_mixed": [(s[0], 10**18), (m[0], 10**18)]}
    for kind in ("lp", "sg"):
        for count in (2, 4):
            if len(groups[kind]) >= count:
                cases[f"{kind}_{count}"] = [(u, 10**18) for u in groups[kind][:count]]
    # A real mixed holder with enough debt to consume its first cohort and
    # continue into the second, without editing debt, balances, prices or order.
    for user in m:
        p = positions[user]
        first = 0 if p["indices"][0] < p["indices"][1] else 1
        target = p["values"][first] + 10**18
        if p["debt"] > target * 2 and p["values"][1-first] > 2 * 10**18:
            cases["mixed_holder_both_cohorts"] = [(user, target)]
            break
    require("mixed_holder_both_cohorts" in cases, "MIXED_SETTLEMENT_SAMPLE")
    selectors = {keccak(text=a["name"] + "(" + ",".join(collapse_if_tuple(i) for i in a["inputs"]) + ")")[:4]: a["name"] for a in records["StabilityPool"]["abi"] if a["type"] == "function"}
    def execute(batch, limit):
        before = [ce.getLatestUserDebtAndTerms(u, False)[0][0] for u, _ in batch]
        cold()  # outside the anchor: resetting journal warmth inside breaks Boa checkpoints
        with boa.env.anchor():
            try:
                paid = teller.deleverageManyUsers(batch, sender=dl.address, gas=limit)
            except Exception:
                output = bytes(teller._computation.output)
                reason = decode(["string"], output[4:])[0] if output[:4] == keccak(text="Error(string)")[:4] else output.hex() or str(teller._computation.error)
                return {"passed": False, "error": reason, "failed_calls": [
                    {"target": "0x" + c.msg.code_address.hex(), "selector": bytes(c.msg.data)[:4].hex(),
                     "gas_limit": c.msg.gas, "gas_left": c.get_gas_remaining(), "output": bytes(c.output).hex()}
                    for c in walk(teller._computation) if c.is_error]}
            comp = teller._computation
            logs = [{"address": "0x" + a.hex(), "topics": [t.to_bytes(32, "big") for t in topics], "data": data} for a, topics, data in comp.get_log_entries()]
            intended = [{"user": u, "target": t} for u, t in batch]
            try:
                reconciled = reconcile(intended, dl.address, logs)
            except RuntimeError as error:
                return {"passed": False, "transaction_succeeded": True, "gas_used": comp.get_gas_used(), "error": str(error)}
            require(all(ledger.userDebt(u)[0] < d for (u, _), d in zip(batch, before)), "GAS_DEBT_SETTLEMENT")
            calls = Counter(selectors.get(bytes(c.msg.data)[:4], "unknown") for c in walk(comp) if c.msg.code_address == bytes.fromhex(str(pool.address)[2:]))
            withdrawals = []
            for call in walk(comp):
                if call.msg.code_address == bytes.fromhex(str(pool.address)[2:]) and selectors.get(bytes(call.msg.data)[:4]) == "withdrawTokensFromVault":
                    user, asset, amount, recipient = decode(["address", "address", "uint256", "address"], bytes(call.msg.data)[4:132])
                    withdrawals.append({"user": user, "asset": asset, "amount": amount, "recipient": recipient})
            if {address(u) for u, _ in batch} != {w["user"] for w in withdrawals if w["amount"] > 0}:
                return {"passed": False, "transaction_succeeded": True, "gas_used": comp.get_gas_used(), "error": "intended cohort did not settle for every user", "pool_withdrawals": withdrawals}
            convert = [c for c in walk(comp) if c.msg.code_address == bytes.fromhex(str(sg)[2:]) and bytes(c.msg.data)[:4] == keccak(text="convertToAssets(uint256)")[:4]]
            optional = [c.msg.gas for c in walk(comp) if c.msg.sender == bytes.fromhex(str(book.address)[2:]) and bytes(c.msg.data)[:4] in
                        (keccak(text="getTotalAmountForUser(address,address)")[:4], keccak(text="getTotalUserValue(address,address)")[:4], keccak(text="convertToAssets(uint256)")[:4], keccak(text="getUsdValue(address,uint256)")[:4])]
            require(optional and all(g == ALLOWANCE for g in optional), "OPTIONAL_FORWARDING")
            return {"passed": True, "gas_used": comp.get_gas_used(), "repaid": paid, "reconciliation": reconciled,
                    "pool_calls": dict(calls), "pool_withdrawals": withdrawals, "convert_to_assets_calls": len(convert), "optional_forwarded_gas": optional}
    for label in ("current", "26_claims"):
        if label == "26_claims":
            for kind, asset in (("lp", lp), ("sg", sg)):
                for i, claim in enumerate(stress, 1):
                    write(pool.address, pool_layout, "stabVault", "claimableAssets", [asset, i], claim)
                    write(pool.address, pool_layout, "stabVault", "indexOfClaimableAsset", [asset, claim], i)
                    if all(address(claim) != address(a) for a in original[kind]):
                        write(pool.address, pool_layout, "stabVault", "claimableBalances", [asset, claim], 1)
                write(pool.address, pool_layout, "stabVault", "numClaimableAssets", [asset], 27)
            evidence["fork_only_overrides"].append({"kind": "26 priced claim entries per cohort", "new_entry_balance": 1, "custody_or_prices_modified": False})
        row = {"reads": {}, "batches": {}}
        evidence["measurements"][label] = row
        for kind, asset in (("lp", lp), ("sg", sg)):
            user = groups[kind][0]
            reads = {}; row["reads"][kind] = reads
            for getter in ("getTotalAmountForUser", "getTotalUserValue"):
                cold()
                read = probe(pool.address, getter + "(address,address)", ["address", "address"], [user, asset])
                reads[getter] = read
                if label == "current":
                    require(read["status"] == "ok" and read["values"][0] > 0, "STRICT_READ_ZERO")
            cold()
            traversal = probe(book.address, "getDeleverageTraversalAsset(address,address,uint256,bool)",
                              ["address", "address", "uint256", "bool"], [user, pool.address, pool.indexOfUserAsset(user, asset), True],
                              gas=64_000_000, outputs=("address", "uint256"))
            reads["traversal"] = traversal
            if label == "current":
                require(traversal["status"] == "ok" and traversal["values"][1] == reads["getTotalAmountForUser"]["values"][0], "GAS_NAV")
        for name, batch in cases.items():
            high, low = 64_000_000, 0
            positive = execute(batch, high)
            if not positive["passed"]:
                row["batches"][name] = positive
                require(label == "26_claims" or any(u in rejected for u, _ in batch), "GAS_POSITIVE_CONTROL:" + name + ":" + positive.get("error", ""))
                row["batches"][name] = dict(positive, intended=[{"user": u, "target": t} for u, t in batch],
                    diagnostic_limit=high, fits_operational_budget=False, qualification="rejected: full-limit execution did not reconcile all users")
                print("REJECTED_QUALIFICATION", label, name, positive["error"], flush=True)
                continue
            boundary = execute(batch, 12_800_000)
            if boundary["passed"]:
                high = 12_800_000
            else:
                low = 12_800_000
            while high - low > 10_000:
                mid = (high + low) // 2
                trial = execute(batch, mid)
                if trial["passed"]:
                    high = mid
                else:
                    low = mid
            final = execute(batch, high)
            require(final["passed"], "GAS_FUNDED_LIMIT")
            if name == "mixed_holder_both_cohorts":
                require({w["asset"] for w in final["pool_withdrawals"]} == {address(lp), address(sg)}, "BOTH_COHORTS_NOT_SETTLED")
            if name.startswith("sg") or name.endswith("sg") or name == "mixed_holder_both_cohorts":
                require(final["convert_to_assets_calls"] > 0, "CONVERT_BRANCH_NOT_EXERCISED")
            final.update(intended=[{"user": u, "target": t} for u, t in batch], minimum_funded_limit_interval=[low+1, high],
                         qualification_limit=high, fits_operational_budget=boundary["passed"], gas_resolution=10_000)
            row["batches"][name] = final
            print("QUALIFIED_GAS", label, name, high, final["gas_used"], flush=True)
    evidence["supported_measured_batch_sizes"] = {label: {name: len(row["intended"]) if row["fits_operational_budget"] else 0 for name, row in measurements["batches"].items()} for label, measurements in evidence["measurements"].items()}
    evidence["prior_26_claim_result"] = "The previously measured 26-claim active-desk configuration supports no keeper batch within the 16M budget. This report separately measures the exact bridge/defaults configuration; no ABI-based capacity assumption is permitted."
    evidence["current_keeper_caller_note"] = "Gas simulations use a registered Deleverage caller. Production preflight must use the actual keeper caller and independently pass its authorization/eligibility checks."
    evidence["measurement_outer_limit"] = 64_000_000
    evidence["preflight_requirement"] = "Exact intended users must pass strict probes, a fully reconciled simulation with execution limit <=12.8M plus intrinsic gas within 16M, and post-receipt reconciliation. The ABI ceiling 25 is not capacity."
    evidence["completed"] = True
    evidence["passed"] = all(row["passed"] for row in evidence["measurements"]["current"]["batches"].values())
    evidence["activation_ready"] = False
    evidence["remaining_gate"] = "Strict collateral valuation of sampled current mixed holders and the exact 26-claim stress inventory fails on the bridge source allowance; no supported batch for those cases. Claim price and keeper integration gates also remain open."
