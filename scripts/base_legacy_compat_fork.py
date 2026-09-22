"""Production-runner rehearsal; local fork only, archive-capable Base RPC required."""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from unittest.mock import patch

import boa
import boa.interpret as boa_interpret
from web3 import Web3

from scripts.utils.deploy_args import DeployArgs
from scripts.utils.mock_account import MockAccount
from scripts.utils.migration_helpers import load_vyper_files
from scripts.utils.migration import Migration
from scripts.utils.migration_runner import MigrationRunner
from scripts.utils.readonly_fork import readonly_fork
from scripts.utils.fork_reports import fingerprint, require_new_report, sanitize
from scripts.verify_legacy_vault_cutover import ROOT, load_inputs, verify_candidates
from scripts.utils.legacy_vault_compat import require


@contextmanager
def isolated_compiler_cache():
    """Boa bundles retain resolved paths; never share them across checkouts.

    Match the production CLI's cache isolation, while keeping this disposable
    checkout clean and restoring the caller's exact cache object on every exit.
    """
    previous = boa_interpret._disk_cache
    with tempfile.TemporaryDirectory(prefix="ripe-legacy-boa-") as cache:
        try:
            boa_interpret.set_cache_dir(cache)
            yield
        finally:
            boa_interpret._disk_cache = previous


@contextmanager
def staged_fork(rpc, block, report):
    """Replay the actual runner in disposable local state; never broadcast."""
    history_source = ROOT / "migration_history/base-mainnet/v1"
    report["input_manifest_sha256"] = hashlib.sha256((history_source / "current-manifest.json").read_bytes()).hexdigest()
    class ObservedMigration(Migration):
        def end(self):
            report["simulated_transactions"] = self._count
            report["journal"] = self._transactions.copy()
            return super().end()
    with isolated_compiler_cache(), tempfile.TemporaryDirectory(prefix="ripe-legacy-compat-fork-") as temp:
        history = Path(temp) / "history"
        shutil.copytree(history_source, history)
        with readonly_fork(rpc, block) as env:
            boa.deployments.set_deployments_db(boa.deployments.DeploymentsDB(":memory:"))
            sender = MockAccount(str(env.eoa))
            env.set_balance(sender.address, 10**20)
            report["stager"] = sender.address
            args = DeployArgs(sender, "base-mainnet", False, "base", rpc, local_preview=True)
            runner = MigrationRunner(ROOT / "migrations/archive/base-mainnet", history, load_vyper_files())
            with patch("scripts.utils.migration_runner.Migration", ObservedMigration):
                report["migration_gas"] = runner.run(args, "2026091900", "2026091900")
            report["candidate_manifest"] = json.loads((history / "2026091900-manifest.json").read_text())
            report["deployments"] = len(report["candidate_manifest"]["contracts"])
            yield history / "current-manifest.json", sender.address


def rehearse(rpc, block, output, baseline_path, baseline_hash, measure_gas=False, development=False):
    require_new_report(output)
    report = {"passed": False, "mode": "local fork; read-only upstream transport", "live_transactions_sent": 0,
              "block": block, "source": fingerprint(ROOT), "qualification": not development,
              "command": "BASE_RPC_URL=<archive-capable-RPC> python -m scripts.base_legacy_compat_fork --block " + str(block) +
                         " --baseline-manifest <reviewed-baseline.json> --baseline-sha256 " + baseline_hash +
                         " --output <new-report.json>" + (" --measure-gas" if measure_gas else "")}
    try:
        require(development or not report["source"]["dirty"], "CLEAN_CHECKOUT_REQUIRED")
        require(development or not Path(output).resolve().is_relative_to(ROOT), "EVIDENCE_OUTPUT_MUST_BE_OUTSIDE_CHECKOUT")
        # Check independently supplied input before any local deployment.
        baseline, _, _ = load_inputs(baseline_path, baseline_hash, ROOT / "migration_history/base-mainnet/v1/current-manifest.json")
        require(baseline["block"] == block, "BASELINE_BLOCK")
        w3 = Web3(Web3.HTTPProvider(rpc))
        require(w3.eth.chain_id == 8453, "WRONG_CHAIN")
        report["block_hash"] = w3.eth.get_block(block).hash.hex()
        require(report["block_hash"] == baseline["block_hash"], "BASELINE_BLOCK_HASH")
        with staged_fork(rpc, block, report) as (manifest_path, stager):
            baseline, records, inputs = load_inputs(baseline_path, baseline_hash, manifest_path)
            report.update(inputs)
            report["verification"] = verify_candidates(records, stager, baseline, "staged")
            report["staging_passed"] = True
            if measure_gas:
                from scripts.utils.legacy_vault_gas import measure
                report["gas_diagnostic"] = {}
                measure(records, report["gas_diagnostic"])
                report["gas_qualification_passed"] = bool(report["gas_diagnostic"]["passed"])
                require(report["gas_qualification_passed"], "GAS_QUALIFICATION_BLOCKED")
            after = fingerprint(ROOT)
            require(development or after == report["source"], "QUALIFICATION_INPUT_DRIFT")
            report["passed"] = True
    except Exception as error:
        report["error"] = str(error)
        raise
    finally:
        report["source_after"] = {k: v for k, v in fingerprint(ROOT).items() if k != "sha256"}
        output.write_text(json.dumps(sanitize(report, rpc, ROOT), indent=2, default=str) + "\n")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--block", type=int, required=True)
    parser.add_argument("--rpc-env", default="BASE_RPC_URL")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--measure-gas", action="store_true")
    parser.add_argument("--baseline-manifest", type=Path, required=True)
    parser.add_argument("--baseline-sha256", required=True)
    parser.add_argument("--development", action="store_true", help="Allow dirty local debugging; output is not qualification evidence")
    args = parser.parse_args()
    rehearse(os.environ[args.rpc_env], args.block, args.output, args.baseline_manifest, args.baseline_sha256, args.measure_gas, args.development)


if __name__ == "__main__":
    main()
