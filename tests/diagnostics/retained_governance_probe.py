"""Contract-only Base fork checks for the combined #233 + #238 sources.

Run beside pricedesk_gas_probe.py from #238. No production deployment files or
state are modified. Local graph substitutions are test assumptions, not proof
of an operator's deployment procedure.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path

import boa
from boa.environment import Env
from eth_abi import decode

try:
    from pricedesk_gas_probe import (
        ReadOnlyRPC,
        attach,
        cold,
        configure_local_graph,
        install_desk,
        outcome,
        set_pointer,
        storage_layout,
        SUFFIX,
    )
except ModuleNotFoundError:
    raise SystemExit(
        "Run in the combined #233 + #238 test tree with pricedesk_gas_probe.py present"
    )

ROOT = Path(__file__).resolve().parents[2]
ZERO = "0x" + "00" * 20
OWNER = "0x7190081341F0e0223E237270b8479159951A5a46"
MIXED = [
    "0x381490fF607bb11de75E730FF0698d72573fAedb",
    "0x9bc27f929C72eCe55a0dcB0A1D845ec90be95275",
    "0xD8Ac9b9f640699c7E6f4464a1A0da629017fe567",
    "0xF1133e9AeF370d8BD8a71abDd64ADbb9298b4f4F",
]


def constructor_args(record):
    constructor = next(a for a in record["abi"] if a["type"] == "constructor")
    return decode(
        [a["type"] for a in constructor["inputs"]], bytes.fromhex(record["args"])
    )


def run(records, quote, snapshot, transaction_gas):
    report = {
        "local_overrides": [
            "candidate MC configuration",
            "HQ department pointers",
            "current Teller/AuctionHouse/Deleverage/PriceDesk code on recorded local candidate state",
            "local retained-only VaultBook",
        ],
        "cases": [],
    }
    hq, ledger, rg = (attach(records, n) for n in ("RipeHq", "Ledger", "RipeGov"))
    ripe = records["RipeToken"]["address"]
    assert str(hq.getAddr(4)).lower() == ledger.address.lower()
    provenance = json.loads(
        (ROOT / "tests/fixtures/legacy_governance/provenance.json").read_text()
    )
    assert (
        hashlib.sha256(boa.env.get_code(ledger.address)).hexdigest()
        == provenance["ledger"]["runtime_sha256"]
    )
    gp = json.loads((ROOT / "tests/fixtures/legacy_pool/provenance.json").read_text())[
        "ripe_gov"
    ]
    assert (
        hashlib.sha256(boa.env.get_code(rg.address)).hexdigest()
        == gp["deployed_sha256"]
    )
    contributors = []
    for i in range(1, ledger.numContributors()):
        addr = ledger.contributors(i)
        assert ledger.isHrContributor(addr)
        c = attach(records, "Contributor", addr)
        digest = hashlib.sha256(boa.env.get_code(addr)).hexdigest()
        assert digest == provenance["contributor"]["runtime_sha256"], (
            "unknown historical generation"
        )
        contributors.append(
            {
                "address": str(addr),
                "owner": str(c.owner()),
                "runtime_sha256": digest,
                "shares": rg.userBalances(addr, ripe),
                "gov": list(rg.userGovData(addr, ripe)),
                "points": list(ledger.userDepositPoints(addr, 2, ripe)),
            }
        )
    assert contributors
    report["contributors"] = contributors
    # Create a pending historical callback before replacing HR; local fork only.
    first = attach(records, "Contributor", contributors[0]["address"])
    first.initiateRipeTransfer(False, sender=first.owner())
    hq, mc, setup, hl = configure_local_graph(records)
    old_book = attach(records, "VaultBook", hq.getAddr(8))
    retained = [old_book.getAddr(i) for i in range(1, 6)]
    book = boa.load(
        str(ROOT / "contracts/registries/VaultBook.vy"),
        hq.address,
        ZERO,
        old_book.minRegistryTimeLock(),
        old_book.maxRegistryTimeLock(),
        retained[0],
    )
    for i, vault in enumerate(retained, 1):
        book.startAddNewAddressToRegistry(vault, "retained", sender=hq.governance())
        assert book.confirmNewAddressToRegistry(vault, sender=hq.governance()) == i
    book.setRegistryTimeLockAfterSetup(sender=hq.governance())
    set_pointer(hq, hl, 8, book.address)
    report["runtime_sha256"] = {}
    for slot, name in (
        (9, "AuctionHouse"),
        (13, "CreditEngine"),
        (15, "HumanResources"),
        (16, "Lootbox"),
        (17, "Teller"),
        (18, "Deleverage"),
        (20, "TellerUtils"),
        (21, "EndaomentFunds"),
    ):
        record = records[name + SUFFIX]
        compiled = boa.load(
            str(ROOT / "contracts/core" / (name + ".vy")), *constructor_args(record)
        )
        code = boa.env.get_code(compiled.address)
        assert compiled.compiler_data.storage_layout[
            "storage_layout"
        ] == storage_layout(record)
        if name in ("Teller", "AuctionHouse", "Deleverage"):
            boa.env.set_code(record["address"], code)
        else:
            assert code == boa.env.get_code(record["address"]), (
                "candidate/source mismatch: " + name
            )
        set_pointer(hq, hl, slot, record["address"])
        report["runtime_sha256"][name] = hashlib.sha256(code).hexdigest()
    desk = install_desk(records, quote, snapshot)
    report["runtime_sha256"]["PriceDesk"] = hashlib.sha256(
        boa.env.get_code(desk.address)
    ).hexdigest()
    assert mc.coreRipeGovVaultId() == 2 and mc.isRipeGovVaultId(2)
    assert (
        str(book.getAddr(2)).lower() == rg.address.lower()
        and book.getRegId(rg.address) == 2
    )
    assert str(hq.getAddr(4)).lower() == ledger.address.lower()
    for asset in (ripe, "0x765824aD2eD0ECB70ECc25B0Cf285832b335d6A9"):
        assert list(mc.assetConfig(asset)[0]) == [2] and mc.rewardVaultId(asset) == 2
    if not setup.rewardsInitialized():
        setup.initRewards(sender=hq.governance(), gas=16_000_000)
    alpha = records["SwitchboardAlpha" + SUFFIX]["address"]
    for name in ("Teller", "CreditEngine", "Lootbox", "HumanResources"):
        c = attach(records, name + SUFFIX)
        if c.isPaused():
            c.pause(False, sender=alpha)
    for row in contributors:
        assert rg.userBalances(row["address"], ripe) == row["shares"]
        assert list(rg.userGovData(row["address"], ripe)) == row["gov"]
        assert list(ledger.userDepositPoints(row["address"], 2, ripe)) == row["points"]
    teller, loot, ce = (
        attach(records, n + SUFFIX) for n in ("Teller", "Lootbox", "CreditEngine")
    )
    for i, row in enumerate(contributors):
        cold()
        with boa.env.anchor():
            c = attach(records, "Contributor", row["address"])
            if i:
                c.initiateRipeTransfer(False, sender=row["owner"])
            blocks = c.pendingRipeTransfer()[2] - boa.env.evm.patch.block_number
            if blocks > 0:
                boa.env.time_travel(blocks=blocks)
            shares = rg.userBalances(c.address, ripe)
            before = rg.userBalances(row["owner"], ripe)
            c.confirmRipeTransfer(False, sender=row["owner"], gas=16_000_000)
            assert rg.userBalances(c.address, ripe) == 0
            assert rg.userBalances(row["owner"], ripe) == before + shares
            report["cases"].append(
                {
                    "operation": "historical transfer",
                    "contributor": row["address"],
                    "pending_across_switch": i == 0,
                    "passed": True,
                }
            )
    token = attach(records, "RipeToken")
    auto_stake_ratio = mc.rewardsConfig()[6]
    for limit in transaction_gas:
        for stake in (False, True):
            # Quote and pre-state reads stay outside the cold transaction.
            amount = loot.getClaimableLoot(OWNER, gas=16_000_000)
            before_supply = token.totalSupply()
            before_wallet = token.balanceOf(OWNER)
            before_custody = token.balanceOf(rg.address)
            assert amount > 0
            cold()
            with boa.env.anchor():
                result = outcome(
                    teller,
                    lambda: teller.claimLoot(OWNER, stake, sender=OWNER, gas=limit),
                )
                result.update(
                    operation="reward claim",
                    stake=stake,
                    quote=amount,
                    funded_execution_gas=limit,
                    auto_stake_ratio=auto_stake_ratio,
                )
                if result["passed"]:
                    minted = token.totalSupply() - before_supply
                    cash = token.balanceOf(OWNER) - before_wallet
                    staked = token.balanceOf(rg.address) - before_custody
                    assert minted == result["value"] > 0
                    expected_staked = (
                        minted if stake else minted * auto_stake_ratio // 10_000
                    )
                    assert staked == expected_staked and cash == minted - staked
                    result["minted"] = minted
                    result["cash"] = cash
                    result["staked"] = staked
                report["cases"].append(result)
                print(json.dumps(result), flush=True)
    for user in MIXED:
        cold()
        result = outcome(
            ce, lambda: ce.getLatestUserDebtAndTerms(user, True, gas=16_000_000)[0][0]
        )
        result.update(operation="strict mixed-holder valuation", user=user)
        report["cases"].append(result)
    # Current retained settlements, preserving real prices/custody/debt.
    from scripts.legacy_vault_preflight import reconcile

    pool = attach(records, "StabilityPool")
    dl = attach(records, "Deleverage" + SUFFIX)
    lp, sg = pool.vaultAssets(2), hq.getAddr(2)
    groups = json.loads(
        (
            ROOT
            / "docs/chains/base/legacy-vault-rehearsal/re-review/qualification.json"
        ).read_text()
    )["gas_diagnostic"]["all_sample_groups"]
    batches = {
        "mixed": [(MIXED[0], 10**18)],
        "lp_then_sg": [(groups["lp"][0], 10**18), (groups["sg"][0], 10**18)],
        "sg_then_lp": [(groups["sg"][0], 10**18), (groups["lp"][0], 10**18)],
    }
    for user in MIXED:
        values = [pool.getTotalUserValue(user, asset) for asset in (lp, sg)]
        first = (
            0
            if pool.indexOfUserAsset(user, lp) < pool.indexOfUserAsset(user, sg)
            else 1
        )
        target = values[first] + 10**18
        if ledger.userDebt(user)[0] > 2 * target and values[1 - first] > 2 * 10**18:
            batches["both_cohorts"] = [(user, target)]
            break
    assert "both_cohorts" in batches
    for limit in transaction_gas:
        for label, batch in batches.items():
            before = [ledger.userDebt(user)[0] for user, _ in batch]
            cold()
            with boa.env.anchor():
                result = outcome(
                    teller,
                    lambda: teller.deleverageManyUsers(
                        batch, sender=dl.address, gas=limit
                    ),
                )
                result.update(
                    operation="retained settlement",
                    sample=label,
                    funded_execution_gas=limit,
                )
                if result["passed"]:
                    comp = teller._computation
                    logs = [
                        {
                            "address": "0x" + a.hex(),
                            "topics": [t.to_bytes(32, "big") for t in topics],
                            "data": data,
                        }
                        for a, topics, data in comp.get_log_entries()
                    ]
                    result["reconciliation"] = reconcile(
                        [{"user": u, "target": t} for u, t in batch], dl.address, logs
                    )
                    assert all(
                        ledger.userDebt(u)[0] < previous
                        for (u, _), previous in zip(batch, before)
                    )
                report["cases"].append(result)
                print(json.dumps(result), flush=True)
    stress = json.loads(
        (
            ROOT / "docs/chains/base/legacy-vault-rehearsal/review-qualification.json"
        ).read_text()
    )["gas_diagnostic"]["stress_claims"]
    assert len(stress) == len(set(stress)) == 26
    report["stress_price_checks"] = []
    for asset in stress:
        cold()
        result = outcome(desk, lambda: desk.getPrice(asset, True, gas=8_000_000))
        result["asset"] = asset
        report["stress_price_checks"].append(result)
    # No claim inventory or nominal balances are added here; full synthetic
    # 26-claim batch capacity remains the historical diagnostic's separate limit.
    report.update(
        quote_allowance=quote,
        snapshot_allowance=snapshot,
        passed=all(
            row["passed"] for row in report["cases"] + report["stress_price_checks"]
        ),
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--block", type=int, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--transaction-gas", type=int, nargs="+", default=[15_950_000]
    )
    parser.add_argument("--quote", type=int, default=3_000_000)
    parser.add_argument("--snapshot", type=int, default=3_000_000)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists")
    boa.interpret.set_cache_dir(str(args.output.parent / ".boa-cache"))
    rpc = ReadOnlyRPC(os.environ.get("BASE_RPC_URL", "https://mainnet.base.org"))
    assert int(rpc.fetch("eth_chainId", []), 16) == 8453
    block = rpc.fetch("eth_getBlockByNumber", [hex(args.block), False])
    env = Env()
    env.fork_rpc(rpc, block_identifier=args.block)
    records = json.loads(args.manifest.read_text())["contracts"]
    with boa.set_env(env):
        report = run(records, args.quote, args.snapshot, args.transaction_gas)
    report.update(
        block=args.block,
        block_hash=block["hash"],
        live_transactions=0,
        manifest_sha256=hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
        probe_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        source_sha256={
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((ROOT / "contracts").rglob("*.vy"))
        },
    )
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    assert report["passed"], "one or more cases failed at the supplied gas; see report"


if __name__ == "__main__":
    main()
