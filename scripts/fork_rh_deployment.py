"""Execute the full Robinhood launch graph on a fork of Robinhood mainnet.

This is a QUALIFICATION HARNESS, not a deployment path. It never submits a
transaction to the real chain: titanoboa's fork keeps all state local, and the
fork is discarded when the process exits. It deliberately does not go through
scripts/migrate.py, whose MIGRATION_FORK policy for Robinhood is
blocked_pending_policy -- that gate is left untouched.

The difference from tests/deployment/test_clean_deployment.py is what backs the
external dependencies. That test deploys mocks onto a fresh EVM; this forks the
real chain, so USDG, WETH, the SteakHouse VaultV2, the three Chainlink feeds,
the Morpho V2 factory and the Curve AddressProvider are the actual deployed
contracts. That is the only way to exercise the constructor paths that read
them -- notably CurvePrices, which reads meta-registry id 7 and factory ids
11/12/13 and reverts if any is absent.

Usage:
    python scripts/fork_rh_deployment.py

Requires ROBINHOOD_MAINNET_RPC_URL in the environment or .env. The URL is never
logged: it may carry a provider key in its path.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import boa  # noqa: E402

from config import BluePrint as source_blueprint  # noqa: E402
from scripts.utils.robinhood_backends import (  # noqa: E402
    BoaRobinhoodBackend,
    LOCAL_GOVERNANCE_REFERENCES,
    ZERO_ADDRESS,
)
from scripts.utils.robinhood_executor import RobinhoodStageExecutor  # noqa: E402
from tests.deployment.robinhood_execution_support import (  # noqa: E402
    MigrationHandoff,
    build_bound_plan,
)


def _rpc_url() -> str:
    url = os.environ.get("ROBINHOOD_MAINNET_RPC_URL")
    if not url:
        env = ROOT / ".env"
        if env.exists():
            for line in env.read_text().splitlines():
                if line.startswith("ROBINHOOD_MAINNET_RPC_URL="):
                    url = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not url:
        raise SystemExit("ROBINHOOD_MAINNET_RPC_URL is not set")
    return url


def _production_files(root: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for parent in (root / "contracts", root / "interfaces"):
        for path in parent.rglob("*.vy"):
            if "testing" not in path.parts:
                files[path.stem] = str(path)
    return files


def main() -> int:
    print("Forking Robinhood mainnet (URL withheld -- may contain a key)")
    boa.fork(_rpc_url())
    # NOTE: boa.env.evm.chain.chain_id reports boa's own local chain id (1), not
    # the forked chain's -- do not use it to identify the fork. Read a contract
    # that only exists on Robinhood instead.
    usdg = boa.loads_abi(
        '[{"type":"function","name":"symbol","stateMutability":"view",'
        '"inputs":[],"outputs":[{"name":"","type":"string"}]}]'
    ).at(source_blueprint.ROBINHOOD_ADDRESSES["USDG"])
    symbol = usdg.symbol()
    if symbol != "USDG":
        raise SystemExit(
            f"fork does not look like Robinhood: USDG address returned {symbol!r}"
        )
    print(f"  verified fork identity: USDG at canonical address returns {symbol!r}")

    sender = boa.env.generate_address()
    final_sender = boa.env.generate_address()
    for account in (sender, final_sender):
        boa.env.set_balance(account, 10**20)
    print(f"  temporary governance (deployer): {sender}")
    print(f"  final governance (stand-in Safe): {final_sender}")

    overrides = {
        "binding:temporary-local-governance": ("address", str(sender)),
        "input:Deployment.DP-18.roles.governance": ("address", str(final_sender)),
        # Take the CREATE path, not the BIND path. create_or_bind_pool binds to
        # a pre-existing pool when this is a non-zero address, and requires code
        # there. No GREEN/USDG pool can exist on Robinhood yet -- GREEN is
        # deployed by this very run -- so binding is impossible and creating
        # through the real StableSwap-NG factory is what a launch would do.
        "curve:pool.address": ("address", ZERO_ADDRESS),
    }

    plan = build_bound_plan(ROOT, overrides=overrides)
    backend = BoaRobinhoodBackend(
        boa_module=boa,
        files=_production_files(ROOT),
        sender=sender,
        final_governance_sender=final_sender,
        # No external_contracts mapping: on a fork the real deployments are
        # already at their canonical addresses.
        external_contracts={},
    )
    executor = RobinhoodStageExecutor(plan, repository_root=ROOT, backend=backend)

    print(f"\nExecuting {sum(len(s['actions']) for s in plan['stages'])} actions "
          f"across {len(plan['stages'])} stages against forked state\n")
    for stage in plan["stages"]:
        executor(MigrationHandoff(), stage)
        print(f"  {stage['migration_id']} {stage['semantic_id']:<34} ok")

    print("\nEnd state:")
    print(f"  actions executed        {len(executor.results)}")
    print(f"  production deployments  {len(backend.production_deployments)}")
    print(f"  handed off              {backend.handed_off}")

    hq = backend.contracts["address:RIPE_HQ"]
    print(f"  RipeHq governance       {backend._address(hq.governance())}")
    print(f"  expected (final Safe)   {backend._address(final_sender)}")

    for reference in LOCAL_GOVERNANCE_REFERENCES:
        local = backend._address(backend.contracts[reference].governance())
        assert local == ZERO_ADDRESS, f"{reference} retained local gov {local}"
    print(f"  all {len(LOCAL_GOVERNANCE_REFERENCES)} departments at zero local governance")

    assert backend._address(hq.governance()) == backend._address(final_sender)
    print("\nFORK QUALIFICATION PASSED (local fork only; nothing was submitted)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
