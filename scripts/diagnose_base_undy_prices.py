"""Read-only-to-mainnet diagnostic; all deployments/actions occur in boa.fork."""
import hashlib
import os
import argparse
from pathlib import Path

import boa
from dotenv import load_dotenv

from scripts.base_full_update_fork import FullUpdate, ROOT, positional
from scripts.base_upgrade_fork import error_text
from scripts.utils.fork_reports import require_unoptimized

ASSETS = {
    "undyETH": "0x02981DB1a99A14912b204437e7a2E02679B57668",
    "undyEURC": "0x1cb8DAB80f19fC5Aca06C2552AECd79015008eA8",
    "undyUSDC": "0x99e65176F7FA8743E3fbaEF277d1Da448e361367",
}


def failures(computation):
    rows = []
    if computation.is_error:
        rows.append({"address": "0x" + computation.msg.code_address.hex(),
                     "selector": "0x" + computation.msg.data_as_bytes[:4].hex(),
                     "error": str(computation._error),
                     "gas_used": computation.get_gas_used()})
    for child in computation.children:
        rows.extend(failures(child))
    return rows


def main():
    require_unoptimized()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--block", required=True, type=int)
    parser.add_argument("--defaults", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--diagnose-replacing-pending", action="store_true")
    args = parser.parse_args()
    if args.block != 51312366:
        parser.error("expected-outcome cases are defined only for historical block 51312366")
    load_dotenv(ROOT / ".env")
    run = FullUpdate(os.environ["BASE_MAINNET_RPC_URL"], args.block, args.report, overwrite=args.overwrite)
    run.diagnose_replacing_pending = args.diagnose_replacing_pending
    run.report.update(scope="isolated oracle diagnosis, not full upgrade qualification",
                      diagnostic_sha256=hashlib.sha256((ROOT / "scripts/diagnose_base_undy_prices.py").read_bytes()).hexdigest())
    try:
        header = run.rpc_read("eth_getBlockByNumber", [hex(args.block), False])
        finalized = run.rpc_read("eth_getBlockByNumber", ["finalized", False])
        if int(run.rpc_read("eth_chainId", []), 16) != 8453 or args.block > int(finalized["number"], 16):
            raise RuntimeError("DIAGNOSIS_WRONG_CHAIN_OR_UNFINALIZED_BLOCK")
        run.report.update(block_hash=header["hash"], snapshot_finalized=True)
        diagnose(run, args.defaults)
    except Exception as e:
        run.report.update(status="diagnosis_incomplete", error=run.sanitized(error_text(e)))
        run.save()
        print(run.report["error"], flush=True)
        return 1
    run.report["status"] = "diagnosis_complete_not_upgrade_qualified"
    run.save()
    return 2


def diagnose(run, defaults):
    with boa.fork(run.rpc, block_identifier=run.block):
        assert boa.env.evm.patch.chain_id == 8453
        run.inventory()
        run.stage_all(defaults)
        source = run.new["UndyVaultPrices"]
        old = run.at("UndyVaultPrices")
        run.report["initial_timestamp"] = boa.env.evm.patch.timestamp
        # Independent branch: prove registration with the unchanged, fresh
        # pinned observations, BEFORE waiting. The anchor undoes these actions.
        with run.diagnostic_branch("fresh_observations_before_wait"):
            fresh = {}
            for name, asset in ASSETS.items():
                config = old.priceConfigs(asset)
                run.transact(source.addNewPriceFeed, asset, *config[3:7])
                run.transact(source.confirmNewPriceFeed, asset)
                fresh[name] = {"registered": source.hasPriceFeed(asset),
                               "direct_price": source.getPrice(asset),
                               "underlying_price": run.old["PriceDesk"].getPrice(config[0])}
                if not fresh[name]["registered"] or fresh[name]["direct_price"] <= 0 or fresh[name]["underlying_price"] <= 0:
                    raise RuntimeError("FRESH_REGISTRATION_PRICE_FAILED:" + name)
            run.report["before_governance_wait"] = fresh
        run.register_candidates()
        run.activate_departments()
        run.configure_oracles()
        desk = run.new["PriceDesk"]
        run.report["price_source_price_gas"] = desk.PRICE_SOURCE_PRICE_GAS()
        run.report["after_wait_timestamp"] = boa.env.evm.patch.timestamp
        results = {}
        for name, asset in ASSETS.items():
            config = source.priceConfigs(asset)
            row = {"registered": source.hasPriceFeed(asset), "config": positional(config)}
            row["weighted_share_price"] = source.getWeightedPrice(asset)
            row["underlying_price"] = desk.getPrice(old.priceConfigs(asset)[0])
            row["direct_source_price"] = source.getPrice(asset)
            row["direct_source_gas"] = source._computation.get_gas_used()
            row["via_price_desk"] = desk.getPrice(asset)
            row["price_desk_failures"] = failures(desk._computation)
            results[name] = row
            run.report["price_diagnosis"] = results
            run.save()
            if name in ("undyETH", "undyUSDC"):
                if row["direct_source_price"] <= 0 or row["direct_source_price"] != row["via_price_desk"] or row["price_desk_failures"]:
                    raise RuntimeError("MATCHING_QUOTE_CASE_FAILED:" + name)
            elif row["underlying_price"] != 0 or row["via_price_desk"] != 0:
                raise RuntimeError("HISTORICAL_STALE_EURC_CASE_FAILED")
        run.report["price_diagnosis"] = results
        print("DIAGNOSIS", run.sanitized(results), flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
