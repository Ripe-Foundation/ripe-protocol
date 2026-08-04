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


def _ledger_address(index: int) -> str:
    """Read the deployer address from a connected Ledger, nothing more.

    Deliberately does NOT construct LedgerAccount: that opens a Web3 connection
    and prints balances, and we need no RPC here. get_account_by_path talks to
    the dongle alone, so this prompts for nothing and leaks no endpoint.

    Signing is not part of this: boa.fork() runs an in-process EVM, so no
    transaction is ever serialised, signed, or broadcast. What this proves is
    that the derivation index resolves to the address you expect and that the
    whole launch graph executes with that address as deployer and governance.
    """
    try:
        from ledgerblue.comm import getDongle
        from ledgereth.accounts import get_account_by_path
    except ImportError as error:
        raise SystemExit(
            "Ledger support unavailable -- the native hidapi library is "
            f"missing. On macOS: brew install hidapi. ({error})"
        ) from None
    dongle = getDongle(False)
    try:
        return get_account_by_path(f"44'/60'/0'/0/{index}", dongle=dongle).address
    finally:
        dongle.close()


def main(ledger_index: int | None = None) -> int:
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

    if ledger_index is None:
        sender = boa.env.generate_address()
    else:
        sender = _ledger_address(ledger_index)
        print(f"  Ledger account {ledger_index} resolved: {sender}")
    boa.env.set_balance(sender, 10**20)

    # The final governance stand-in must be a CONTRACT, not an EOA:
    # LocalGov.finishRipeHqSetup asserts `_newGov.is_contract`. On the real
    # chain that is satisfied by the Safe; here a minimal contract stands in.
    # This is the same constraint that would abort a live run at the last
    # action if the Safe were not yet deployed on the target chain.
    final_sender = boa.loads(
        """
@external
@view
def isGovernanceStandIn() -> bool:
    return True
""",
        name="robinhood_final_governance_standin",
    ).address
    boa.env.set_balance(final_sender, 10**20)
    # The deployer must hold the USDG it seeds the pool with. On the real chain
    # that is the funding_source's responsibility; on a fork we write the
    # balance directly rather than hunting for a holder, since a young chain may
    # have no USDG whale to prank.
    usdg_address = source_blueprint.ROBINHOOD_ADDRESSES["USDG"]
    seed_usdg, _seed_green = next(
        row.value
        for row in source_blueprint.ROBINHOOD_CURVE_LAUNCH_INPUTS
        if row.input_id == "pool.production_liquidity_amount"
    )
    # boa.deal adjusts totalSupply alongside the balance, so both must be in the
    # ABI. Keeping the adjustment (rather than passing adjust_supply=False)
    # leaves the token self-consistent: dealt balances never exceed supply.
    usdg_token = boa.loads_abi(
        '[{"type":"function","name":"balanceOf","stateMutability":"view",'
        '"inputs":[{"name":"o","type":"address"}],'
        '"outputs":[{"name":"","type":"uint256"}]},'
        '{"type":"function","name":"totalSupply","stateMutability":"view",'
        '"inputs":[],"outputs":[{"name":"","type":"uint256"}]}]'
    ).at(usdg_address)
    boa.deal(usdg_token, sender, seed_usdg)
    print(f"  temporary governance (deployer): {sender}")
    print(f"  dealt {seed_usdg / 10**6:.2f} USDG to the deployer for pool seeding")
    print(f"  final governance (stand-in Safe): {final_sender}")

    overrides = {
        "binding:temporary-local-governance": ("address", str(sender)),
        # The deployer seeds the pool, so it receives the initial GREEN.
        "binding:green-supply-recipient": ("address", str(sender)),
        "input:Deployment.DP-18.roles.governance": ("address", str(final_sender)),
        # 100,000 RIPE is minted to the governance Safe, as Base minted its
        # supply to blueprint.ADDYS["GOVERNANCE"]. On the fork the Safe is the
        # stand-in contract, so the mint lands there and can be checked.
        "input:Deployment.DP-19.supply.RIPE.recipient": (
            "address",
            str(final_sender),
        ),
        # sGREEN has a zero supply; a zero recipient makes the credit
        # impossible rather than merely unused.
        "input:Deployment.DP-19.supply.SGREEN.recipient": (
            "address",
            ZERO_ADDRESS,
        ),
        # Empty at launch by owner decision; Base seeded four addresses here.
        "input:Deployment.DP-18.roles.trainingWheelsAllowlist": (
            "address-array",
            [],
        ),
        # Take the CREATE path, not the BIND path. create_or_bind_pool binds to
        # a pre-existing pool when this is a non-zero address, and requires code
        # there. No GREEN/USDG pool can exist on Robinhood yet -- GREEN is
        # deployed by this very run -- so binding is impossible and creating
        # through the real StableSwap-NG factory is what a launch would do.
        "curve:pool.address": ("address", ZERO_ADDRESS),
        # NOTE: the pool parameters are deliberately NOT overridden here. They
        # are now resolved in the blueprint (owner-approved Base GREEN config),
        # so the fork exercises the real configuration path. Overriding them
        # would shadow exactly what we want this run to prove.
    }

    import time as _time
    _t = _time.monotonic()
    plan = build_bound_plan(ROOT, overrides=overrides)
    print(f"  plan build {_time.monotonic() - _t:.1f}s")
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
    import time as _time
    started = _time.monotonic()
    for stage in plan["stages"]:
        stage_started = _time.monotonic()
        executor(MigrationHandoff(), stage)
        print(
            f"  {stage['migration_id']} {stage['semantic_id']:<34} ok"
            f"  {_time.monotonic() - stage_started:6.1f}s"
        )
    print(f"\n  execution total {_time.monotonic() - started:.1f}s")

    print("\nEnd state:")
    print(f"  actions executed        {len(executor.results)}")
    print(f"  production deployments  {len(backend.production_deployments)}")
    print(f"  handed off              {backend.handed_off}")
    ripe = backend.contracts["address:RIPE_TOKEN"]
    ripe_supply = int(ripe.totalSupply())
    ripe_held = int(ripe.balanceOf(final_sender))
    print(f"  RIPE total supply       {ripe_supply / 10**18:,.0f}")
    print(f"  RIPE held by governance {ripe_held / 10**18:,.0f}")
    assert ripe_supply == 100_000 * 10**18, ripe_supply
    assert ripe_held == ripe_supply, ripe_held
    sgreen = backend.contracts["address:SGREEN_TOKEN"]
    assert int(sgreen.totalSupply()) == 0
    print("  sGREEN total supply     0")
    minted = getattr(backend, "seed_minted_lp", None)
    if minted is not None:
        print(f"  pool LP minted          {minted / 10**18:.6f}")
        print(f"  LP custodian            {getattr(backend, 'seed_custodian', '?')}")

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
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ledger",
        type=int,
        default=None,
        metavar="INDEX",
        help=(
            "Read the deployer address from a connected Ledger at this account "
            "index instead of generating one. Reads only -- the device is never "
            "asked to sign, because a boa fork signs nothing."
        ),
    )
    raise SystemExit(main(parser.parse_args().ledger))
