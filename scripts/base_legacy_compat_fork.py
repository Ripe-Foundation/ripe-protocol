"""Production-runner rehearsal and real-oracle gas diagnostics; local fork only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from unittest.mock import patch

import boa
from web3 import Web3

from scripts.utils.deploy_args import DeployArgs
from scripts.utils.mock_account import MockAccount
from scripts.utils.migration_helpers import load_vyper_files
from scripts.utils.migration import Migration
from scripts.utils.migration_runner import MigrationRunner
from scripts.utils.readonly_fork import readonly_fork
from scripts.utils.fork_reports import fingerprint, require_new_report, sanitize
from scripts.verify_legacy_vault_cutover import ROOT, SUFFIX, attach, verify_candidates


def rehearse(rpc, block, output, measure_gas=False):
    require_new_report(output)
    report = {"mode": "local fork; read-only upstream transport", "live_transactions_sent": 0,
              "block": block, "source": fingerprint(ROOT), "command": "BASE_RPC_URL=<RPC> python -m scripts.base_legacy_compat_fork --block " + str(block) + " --output <new-report.json>" + (" --measure-gas" if measure_gas else "")}
    w3 = Web3(Web3.HTTPProvider(rpc))
    if w3.eth.chain_id != 8453:
        raise RuntimeError("WRONG_CHAIN")
    report["block_hash"] = w3.eth.get_block(block).hash.hex()
    history_source = ROOT / "migration_history/base-mainnet/v1"
    report["input_manifest_sha256"] = hashlib.sha256((history_source / "current-manifest.json").read_bytes()).hexdigest()

    class ObservedMigration(Migration):
        # The production methods execute unchanged. Only journal evidence is
        # copied before end() removes the completed transaction journal.
        def end(self):
            report["simulated_transactions"] = self._count
            report["journal"] = self._transactions.copy()
            return super().end()

    try:
        with tempfile.TemporaryDirectory(prefix="ripe-legacy-compat-fork-") as temp:
            history = Path(temp) / "history"
            shutil.copytree(history_source, history)
            with readonly_fork(rpc, block) as env:
                boa.deployments.set_deployments_db(boa.deployments.DeploymentsDB(":memory:"))
                sender = MockAccount(str(env.eoa))
                env.set_balance(sender.address, 10**20)
                report["stager"] = sender.address
                args = DeployArgs(sender, "base-mainnet", False, "base", rpc, local_preview=True)
                runner = MigrationRunner(ROOT / "migrations/base-mainnet", history, load_vyper_files())
                with patch("scripts.utils.migration_runner.Migration", ObservedMigration):
                    report["migration_gas"] = runner.run(args, "2026091900", "2026091900")
                manifest = json.loads((history / "current-manifest.json").read_text())
                report["candidate_manifest"] = json.loads((history / "2026091900-manifest.json").read_text())
                report["deployments"] = len(report["candidate_manifest"]["contracts"])
                report["verification"] = verify_candidates(manifest["contracts"], sender.address)
                report["staging_passed"] = True
                if measure_gas:
                    from scripts.utils.legacy_vault_gas import measure
                    report["gas_diagnostic"] = {}
                    measure(manifest["contracts"], report["gas_diagnostic"])
                report["passed"] = True
    except Exception as error:
        report["error"] = str(error)
        raise
    finally:
        output.write_text(json.dumps(sanitize(report, rpc, ROOT), indent=2, default=str) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--block", type=int, required=True)
    parser.add_argument("--rpc-env", default="BASE_RPC_URL")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--measure-gas", action="store_true")
    args = parser.parse_args()
    rehearse(os.environ[args.rpc_env], args.block, args.output, args.measure_gas)


if __name__ == "__main__":
    main()
