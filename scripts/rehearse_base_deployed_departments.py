"""Check deployed candidates and rehearse HQ changes on a read-only-upstream fork.

Produces a proposal-only Safe batch; never signs or broadcasts transactions.
The frozen-feed 12h result and current-timestamp routing diagnostic are separate.
"""
import json
import os
from pathlib import Path

import boa
from dotenv import load_dotenv
from web3 import Web3

from scripts.base_upgrade_fork import HQ_IDS, plain
from scripts.utils.readonly_fork import readonly_fork

ROOT = Path(__file__).resolve().parents[1]
ZERO = "0x" + "00" * 20
GOV = "0xe488a42D33b3Af5d3E5Cd5680938d8369716D1bf"
OUT = ROOT / "docs/chains/base/deployed-cutover-20260922"


def main():
    load_dotenv(ROOT / ".env")
    rpc = os.environ["BASE_MAINNET_RPC_URL"]
    web3 = Web3(Web3.HTTPProvider(rpc))
    assert web3.eth.chain_id == 8453
    block = web3.eth.block_number
    records = json.loads((ROOT / "migration_history/base-mainnet/v1/current-manifest.json").read_text())["contracts"]
    report = {"block": block, "live_transactions_sent": 0, "confirmation_passed": False,
              "scope": "HQ proposals/confirmations and state/price checks; not full operational cutover qualification"}
    OUT.mkdir(parents=True, exist_ok=True)

    def save():
        (OUT / "report.json").write_text(json.dumps(plain(report), indent=2) + "\n")

    with readonly_fork(rpc, block) as env:
        def at(name, address=None):
            return boa.loads_abi(json.dumps(records[name]["abi"])).at(address or records[name]["address"])

        def attempt(fn, *args):
            try:
                return plain(fn(*args))
            except Exception:
                return "reverted"

        hq = at("RipeHq")
        assert str(hq.address).lower() == "0x6162df1b329e157479f8f1407e888260e0ec3d2b"
        assert str(hq.governance()).lower() == GOV.lower()
        assert hq.numAddrs() == 25
        old = {name: at(name, hq.getAddr(slot)) for slot, name in HQ_IDS.items()}
        new = {}
        for slot, name in HQ_IDS.items():
            if slot == 4:
                continue
            suffix = "BaseConfig20260921" if slot == 5 else "BasePrices20260921" if slot == 7 else "BaseDepartments20260921"
            new[name] = at(name + suffix)
        additions = ("VaultMigrator", "RipeReserveEngine", "RipeReserveVesting")
        for name in additions:
            new[name] = at(name + "BaseDepartments20260921")
        report["candidates"] = {n: str(c.address) for n, c in new.items()}
        for c in new.values():
            assert len(env.get_code(c.address)) > 0
        fox = at("SwitchboardFoxtrotBaseConfig20260921")
        assert fox.initStep() == 5 and fox.missionControl() == new["MissionControl"].address
        report["foxtrot"] = {"initStep": fox.initStep(), "rewardsInitialized": fox.rewardsInitialized()}
        for i in range(1, 6):
            assert new["VaultBook"].getAddr(i) == old["VaultBook"].getAddr(i)
        assert new["Switchboard"].getAddr(6) == fox.address
        for n in ("Switchboard", "VaultBook", "PriceDesk"):
            assert new[n].registryChangeTimeLock() == 0
            assert str(new[n].governance()).lower() == ZERO
        report["hq_delay_blocks"] = int(hq.registryChangeTimeLock())
        assert report["hq_delay_blocks"] == 21_600
        assets = [old["MissionControl"].assets(i) for i in range(1, int(old["MissionControl"].numAssets()))]
        assert assets == [new["MissionControl"].assets(i) for i in range(1, int(new["MissionControl"].numAssets()))]
        report["mc_asset_config_differences"] = [str(a) for a in assets if tuple(old["MissionControl"].assetConfig(a)) != tuple(new["MissionControl"].assetConfig(a))]
        vaults = {i: at(next(n for n, r in records.items() if r["address"].lower() == str(old["VaultBook"].getAddr(i)).lower())) for i in range(1, 6)}
        ledger = old["Ledger"]
        borrowers = [ledger.borrowers(i) for i in range(1, ledger.getNumBorrowers() + 1)]
        def balances():
            return {"ledger": {n: plain(getattr(ledger, n)()) for n in ("totalDebt", "badDebt", "ripeAvailForRewards", "ripeAvailForHr", "ripeAvailForBonds")},
                    "borrower_debt": {str(u): plain(ledger.userDebt(u)) for u in borrowers},
                    "vault_totals": {str(i): {str(v.vaultAssets(j)): v.totalBalances(v.vaultAssets(j)) for j in range(1, v.getNumVaultAssets() + 1)} for i, v in vaults.items()}}
        before = balances()
        report["before"] = before
        erc = boa.loads_abi('[{"type":"function","name":"balanceOf","stateMutability":"view","inputs":[{"name":"user","type":"address"}],"outputs":[{"name":"","type":"uint256"}]},{"type":"function","name":"symbol","stateMutability":"view","inputs":[],"outputs":[{"name":"","type":"string"}]}]')
        treasury_assets = list(dict.fromkeys(assets + [old["EndaomentPSM"].USDC(), old["EndaomentPSM"].usdcYieldPosition()[1]]))
        report["treasury_known_asset_balances"] = {n: {str(a): attempt(erc.at(a).balanceOf, old[n].address) for a in treasury_assets} for n in ("Endaoment", "EndaomentFunds", "EndaomentPSM")}
        report["treasury_inventory_scope"] = "MC assets plus PSM underlying/yield token; not exhaustive incoming-transfer discovery"
        wrapped = at("wsuperOETHbPrices", new["PriceDesk"].getAddr(7))
        assets = list(dict.fromkeys(assets + [wrapped.MCBETH(), wrapped.VVV()]))
        names = {str(a): attempt(erc.at(a).symbol) for a in assets}
        report["prices_before"] = {str(a): attempt(old["PriceDesk"].getPrice, a, False) for a in assets}
        print("INVENTORY_COMPLETE", block, len(borrowers), "borrowers", flush=True)
        transactions = []
        def add_tx(name, inputs, values):
            transactions.append({"to": str(hq.address), "value": "0", "data": None,
                                 "contractMethod": {"name": name, "payable": False, "inputs": inputs},
                                 "contractInputsValues": values})
        timestamp = env.timestamp
        active_before = [hq.getAddr(i) for i in range(1, 25)]
        with env.prank(GOV):
            for slot, name in HQ_IDS.items():
                if slot == 4:
                    continue
                pending = hq.pendingAddrUpdate(slot)
                assert str(pending[0]).lower() == ZERO, f"EXISTING_PENDING_UPDATE:{slot}:{pending}"
                assert all(int(x) == 0 for x in hq.pendingAddrDisable(slot)), f"PENDING_DISABLE:{slot}"
                assert hq.startAddressUpdateToRegistry(slot, new[name].address)
                add_tx("startAddressUpdateToRegistry", [{"name": "_regId", "type": "uint256"}, {"name": "_newAddr", "type": "address"}], {"_regId": str(slot), "_newAddr": str(new[name].address)})
            for name in additions:
                assert hq.startAddNewAddressToRegistry(new[name].address, name)
                add_tx("startAddNewAddressToRegistry", [{"name": "_addr", "type": "address"}, {"name": "_description", "type": "string"}], {"_addr": str(new[name].address), "_description": name})
            assert [hq.getAddr(i) for i in range(1, 25)] == active_before
            print("ALL_PROPOSALS_PASS", len(transactions), flush=True)
            env.time_travel(blocks=21_601, block_delta=2)
            report["confirmation_gas"] = {}
            for slot in [6, 8, 5, 7] + [i for i in HQ_IDS if i not in (4, 5, 6, 7, 8)]:
                assert hq.confirmAddressUpdateToRegistry(slot)
                assert hq.getAddr(slot) == new[HQ_IDS[slot]].address
                report["confirmation_gas"][str(slot)] = hq._computation.get_gas_used()
            for slot, name in enumerate(additions, 25):
                assert hq.confirmNewAddressToRegistry(new[name].address) == slot
                report["confirmation_gas"][str(slot)] = hq._computation.get_gas_used()
        assert balances() == before
        assert hq.getAddr(4) == ledger.address
        report["confirmation_passed"] = True
        report["unchanged_ledger_borrower_records_vault_totals"] = True
        print("ALL_CONFIRMATIONS_PASS", flush=True)
        report["prices_after_frozen_12h"] = {str(a): attempt(new["PriceDesk"].getPrice, a, False) for a in assets}
        # Diagnostic only: restored timestamp separates oracle staleness from routing changes.
        env.timestamp = timestamp
        env.evm.patch.block_number = block
        report["prices_current_timestamp_diagnostic"] = {str(a): attempt(new["PriceDesk"].getPrice, a, False) for a in assets}
        report["asset_symbols"] = names
        report["sp_nav_current_timestamp"] = {str(a): attempt(vaults[1].getTotalValue, a) for a in [vaults[1].vaultAssets(j) for j in range(1, vaults[1].getNumVaultAssets() + 1)]}
        report["dust_values"] = {str(a): attempt(new["PriceDesk"].getUsdValue, a, 1, True) for a in (wrapped.MCBETH(), wrapped.VVV())}
        report["configuration_remaining"] = {"CE_buybackRatio": new["CreditEngine"].buybackRatio(), "Teller_paused": new["Teller"].isPaused(), "PSM_canMint": new["EndaomentPSM"].canMint(), "PSM_canRedeem": new["EndaomentPSM"].canRedeem(), "PSM_enforceRedeemAllowlist": new["EndaomentPSM"].shouldEnforceRedeemAllowlist(), "MC_rewardsInitialized": fox.rewardsInitialized()}
        # Test the agreed settings separately; no corresponding transactions in exported batch.
        with env.anchor(), env.prank(GOV):
            alpha = at("SwitchboardAlphaBaseDepartments20260921")
            echo = at("SwitchboardEchoBaseDepartments20260921")
            alpha.executePendingAction(alpha.setBuybackRatio(8000))
            echo.executePendingAction(echo.setPsmShouldEnforceRedeemAllowlist(True))
            echo.executePendingAction(echo.setPsmCanRedeem(True))
            assert new["CreditEngine"].buybackRatio() == 8000
            assert new["EndaomentPSM"].canRedeem() and new["EndaomentPSM"].shouldEnforceRedeemAllowlist()
            report["post_activation_setting_calls_passed"] = True
        batch = {"version": "1.0", "chainId": "8453", "createdAt": timestamp * 1000,
                 "meta": {"name": "Base department upgrade — START HQ timelocks only", "description": "18 replacements plus 3 additions. No confirmations, funds transfers, or parameter changes. Recheck pending proposals and deployment addresses before execution.", "createdFromSafeAddress": GOV},
                 "transactions": transactions}
        (OUT / "start-hq-timelocks.safe.json").write_text(json.dumps(batch, indent=2) + "\n")
        report["proposal_count"] = len(transactions)
        save()
        print("REPORT", OUT / "report.json", flush=True)


if __name__ == "__main__":
    main()
