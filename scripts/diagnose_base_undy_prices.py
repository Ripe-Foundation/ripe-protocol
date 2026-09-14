"""Read-only-to-mainnet diagnostic; all deployments/actions occur in boa.fork."""
import hashlib
import os

import boa
from dotenv import load_dotenv

from scripts.base_full_update_fork import FullUpdate, ROOT, positional

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
    load_dotenv(ROOT / ".env")
    block = 51312366
    run = FullUpdate(os.environ["BASE_MAINNET_RPC_URL"], block,
                     ROOT / "docs/chains/base/fork-rehearsal/undy-price-diagnosis.json")
    run.diagnose_replacing_pending = True
    run.report.update(scope="isolated oracle diagnosis, not full upgrade qualification",
                      diagnostic_sha256=hashlib.sha256((ROOT / "scripts/diagnose_base_undy_prices.py").read_bytes()).hexdigest())
    with boa.fork(run.rpc, block_identifier=block):
        assert boa.env.evm.patch.chain_id == 8453
        run.inventory()
        run.stage_all(ROOT / "docs/chains/base/fork-rehearsal/Defaults.wave1-51312366.vy")
        source = run.new["UndyVaultPrices"]
        old = run.at("UndyVaultPrices")
        run.report["initial_timestamp"] = boa.env.evm.patch.timestamp
        # Independent branch: prove registration with the unchanged, fresh
        # pinned observations, BEFORE waiting. The anchor undoes these actions.
        with boa.env.anchor():
            fresh = {}
            for name, asset in ASSETS.items():
                config = old.priceConfigs(asset)
                run.transact(source.addNewPriceFeed, asset, *config[3:7])
                run.transact(source.confirmNewPriceFeed, asset)
                fresh[name] = {"registered": source.hasPriceFeed(asset),
                               "direct_price": source.getPrice(asset),
                               "underlying_price": run.old["PriceDesk"].getPrice(config[0])}
            run.report["before_governance_wait"] = fresh
        run.register_candidates()
        run.activate_departments()
        run.configure_oracles()
        desk = run.new["PriceDesk"]
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
        print("DIAGNOSIS", results, flush=True)
    run.report["status"] = "diagnosis_complete_not_upgrade_qualified"
    run.save()


if __name__ == "__main__":
    main()
