"""Pinned Base snapshot regression. All writes are in a disposable local fork."""

import argparse
import os
from pathlib import Path

import boa
from dotenv import load_dotenv

from scripts.base_upgrade_fork import Rehearsal, ROOT, ZERO, error_text
from scripts.utils.fork_reports import fingerprint, require_unoptimized

BLOCK = 51_312_366
ASSET = "0x99e65176F7FA8743E3fbaEF277d1Da448e361367"
USER = "0x0e1f4AF8F4233dB542Ac7D858382b30F87C93660"


def diagnose(run):
    with boa.fork(run.rpc, block_identifier=BLOCK):
        if boa.env.evm.patch.chain_id != 8453:
            raise RuntimeError("WRONG_CHAIN")
        run.inventory()
        old = run.at("UndyVaultPrices")
        config = old.priceConfigs(ASSET)
        source = run.deploy("UndyVaultPrices", run.hq.address, ZERO, 3600, 302400)
        run.transact(source.addNewPriceFeed, ASSET, *config[3:7])
        run.transact(source.confirmNewPriceFeed, ASSET)
        old_desk = run.old["PriceDesk"]
        desks = {}
        for budget in (150_000, 1_500_000):
            desk = run.deploy("Desk" + str(budget), run.hq.address, ZERO,
                              old_desk.ETH(), 3600, 302400, 1_500_000, budget,
                              path=ROOT / "contracts/registries/PriceDesk.vy")
            # Only one source is needed to characterize snapshot forwarding.
            run.transact(desk.startAddNewAddressToRegistry, source.address, "Undy snapshot regression")
            run.transact_expect(1, desk.confirmNewAddressToRegistry, source.address)
            desks[budget] = desk
        boa.env.time_travel(seconds=int(config[3]) + 1)
        before = tuple(source.priceConfigs(ASSET)[7])
        results = {}
        for budget, desk in desks.items():
            with run.diagnostic_branch("capped_snapshot_" + str(budget)):
                run.transact(run.hq.startAddressUpdateToRegistry, 7, desk.address)
                boa.env.time_travel(blocks=run.hq.registryChangeTimeLock(), block_delta=2)
                run.transact(run.hq.confirmAddressUpdateToRegistry, 7)
                # The registered Teller is the authenticated caller here;
                # below we exercise its actual withdrawal/deposit entrypoints.
                updated = desk.addPriceSnapshot(ASSET, sender=run.old["Teller"].address)
                gas = desk._computation.get_gas_used()
                results[str(budget)] = {"updated": updated, "snapshot_before": before,
                                       "snapshot_after": tuple(source.priceConfigs(ASSET)[7]), "execution_gas": gas}
        with run.diagnostic_branch("direct_snapshot"):
            boa.env.time_travel(blocks=run.hq.registryChangeTimeLock(), block_delta=2)
            updated = source.addPriceSnapshot(ASSET, sender=run.old["Teller"].address)
            gas = source._computation.get_gas_used()
            results["direct"] = {"updated": updated, "snapshot_after": tuple(source.priceConfigs(ASSET)[7]),
                                 "execution_gas": gas}
        run.report["snapshot_comparison"] = results
        run.save()
        assert not results["150000"]["updated"], "OLD_CAP_UNEXPECTEDLY_REFRESHED"
        assert results["150000"]["snapshot_after"] == before, "OLD_CAP_CHANGED_STATE"
        assert results["1500000"]["updated"] and results["direct"]["updated"], "NEW_CAP_OR_DIRECT_FAILED"
        assert results["1500000"]["snapshot_after"] != before, "NEW_CAP_DID_NOT_ADVANCE"

        # Install a full price registry for the unchanged live Teller's actual
        # housekeeping calls. Preserve the disabled slot and all other routes.
        desk = run.deploy("TellerDesk", run.hq.address, ZERO, old_desk.ETH(),
                          3600, 302400, 1_500_000, 1_500_000,
                          path=ROOT / "contracts/registries/PriceDesk.vy")
        for slot in range(1, int(old_desk.numAddrs())):
            address = old_desk.getAddr(slot)
            if slot == 3:
                address = run.at("BlueChipYieldPrices").address
            elif slot == 8:
                address = source.address
            run.transact(desk.startAddNewAddressToRegistry, address, str(slot))
            run.transact_expect(slot, desk.confirmNewAddressToRegistry, address)
            if slot == 3:
                run.transact(desk.startAddressDisableInRegistry, slot)
                run.transact(desk.confirmAddressDisableInRegistry, slot)
        for asset in (ASSET, config[0]):
            run.transact(desk.syncTokenScale, asset)
        run.transact(run.hq.startAddressUpdateToRegistry, 7, desk.address)
        boa.env.time_travel(blocks=run.hq.registryChangeTimeLock(), block_delta=2)
        run.transact(run.hq.confirmAddressUpdateToRegistry, 7)
        teller = run.old["Teller"]
        token = boa.loads_abi('[{"type":"function","name":"approve","stateMutability":"nonpayable","inputs":[{"type":"address"},{"type":"uint256"}],"outputs":[{"type":"bool"}]}]').at(ASSET)
        amount = 1_000_000  # one USDC-denominated share unit; returned in each cycle
        observations = []
        for _ in range(2):
            prior = tuple(source.priceConfigs(ASSET)[7])
            teller.withdraw(ASSET, amount, USER, ZERO, 5, sender=USER)
            after_withdraw = tuple(source.priceConfigs(ASSET)[7])
            assert after_withdraw != prior, "TELLER_WITHDRAW_SNAPSHOT_DID_NOT_ADVANCE"
            boa.env.time_travel(seconds=int(config[3]) + 1)
            token.approve(teller.address, amount, sender=USER)
            teller.deposit(ASSET, amount, USER, ZERO, 5, sender=USER)
            after_deposit = tuple(source.priceConfigs(ASSET)[7])
            assert after_deposit != after_withdraw, "TELLER_DEPOSIT_SNAPSHOT_DID_NOT_ADVANCE"
            price = desk.getPrice(ASSET, True)
            assert price > 0
            observations.append({"before": prior, "withdraw": after_withdraw,
                                 "deposit": after_deposit, "price": price})
            boa.env.time_travel(seconds=int(config[3]) + 1)
        run.report["teller_refreshes"] = observations
        run.report["teller_binding"] = str(teller.address)
        boa.env.time_travel(seconds=int(config[6]) + 1)
        assert source.getWeightedPrice(ASSET) == 0, "STALE_SNAPSHOT_DID_NOT_EXPIRE"
        run.report["stale_snapshot_expired"] = True


def main():
    require_unoptimized()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    load_dotenv(ROOT / ".env")
    run = Rehearsal(os.environ["BASE_MAINNET_RPC_URL"], BLOCK, args.report, overwrite=args.overwrite)
    run.report["input_fingerprint"] = fingerprint(ROOT)
    try:
        header = run.rpc_read("eth_getBlockByNumber", [hex(BLOCK), False])
        finalized = run.rpc_read("eth_getBlockByNumber", ["finalized", False])
        assert BLOCK <= int(finalized["number"], 16)
        run.report.update(block_hash=header["hash"], snapshot_finalized=True,
                          scope="snapshot regression using live Teller; not final-candidate operation qualification")
        diagnose(run)
    except Exception as e:
        run.report.update(status="incomplete", error=run.sanitized(error_text(e)))
        run.save()
        print(run.report["error"], flush=True)
        return 1
    run.report["status"] = "snapshot_regression_passed_not_upgrade_qualified"
    run.save()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
