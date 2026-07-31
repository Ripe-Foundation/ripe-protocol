"""
Run the Robinhood migration set against a throwaway EVM.

This deliberately bypasses `scripts/migrate.py`. That command routes through the
network-profile guard, which holds MIGRATION_FORK and MIGRATION_LIVE BLOCKED for
both Robinhood profiles and leaves `blueprint_id` unset -- by design, since live
Robinhood deployment is gated on approvals that are still open. This script is a
development harness for exercising the migration graph, NOT a deployment path.

Two modes:

  --local  (default)  fresh in-memory pyevm chain. Every external dependency the
                      migrations touch is replaced with a mock deployed at the
                      blueprint's address, so the whole graph runs with no RPC.

  --rpc URL           fork a real chain. External addresses must actually exist
                      there. No transaction is ever broadcast: titanoboa's fork
                      mode keeps all state local.

Manifests are written to a scratch history directory, never to
migration_history/, so no run can be mistaken for deployment evidence.

Usage:
    python scripts/run_rh_migrations.py
    python scripts/run_rh_migrations.py --rpc $SOME_RPC_URL
    python scripts/run_rh_migrations.py --keep-history /tmp/rh-run
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import boa  # noqa: E402

from config import BluePrint as bp  # noqa: E402
from scripts.utils import log  # noqa: E402
from scripts.utils.deploy_args import DeployArgs  # noqa: E402
from scripts.utils.migration_helpers import load_vyper_files  # noqa: E402
from scripts.utils.migration_runner import MigrationRunner  # noqa: E402
from scripts.utils.mock_account import MockAccount  # noqa: E402

BLUEPRINT = "robinhood"
MIGRATIONS_DIR = ROOT / "migrations/robinhood-mainnet/v1"
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

# ArbSys precompile. Ledger's constructor probes this and reverts if the exact
# approved ABI cannot be executed and decoded, so local runs must provide it.
ARB_SYS = "0x0000000000000000000000000000000000000064"


def _install_local_mocks(account):
    """
    Put a working contract behind every external address the migrations read.

    Without this the graph dies at the first constructor that validates an
    external dependency -- Ledger probing ArbSys, ChainlinkPrices reading feed
    decimals, BlueChipYieldPrices calling isMetaMorpho.

    Everything is deployed with override_address so the mock lands exactly where
    the blueprint says it is, constructor storage included.
    """
    addys = bp.ADDYS[BLUEPRINT]
    core = bp.CORE_TOKENS[BLUEPRINT]
    yields = bp.YIELD_TOKENS[BLUEPRINT]

    log.h2("Installing local mocks for external dependencies")

    # --- ArbSys: a child-block height that advances independently of
    # `block.number`. That divergence is the entire reason Ledger takes an
    # explicit action-block source on this chain.
    boa.loads(
        """
@external
@view
def arbBlockNumber() -> uint256:
    return block.number * 120
""",
        override_address=ARB_SYS,
    )
    log.info(f"  ArbSys              -> {ARB_SYS}")

    # --- Governance.
    #
    # LocalGov.finishRipeHqSetup asserts `_newGov.is_contract`, so the
    # governance address must have code. This is a real constraint on the live
    # deploy too: the Robinhood governance Safe/contract has to exist on chain
    # BEFORE 2003 runs, or the handoff reverts.
    governance = addys["GOVERNANCE"]
    boa.loads(
        """
@external
@view
def isGovernance() -> bool:
    return True
""",
        override_address=governance,
    )
    log.info(f"  Governance          -> {governance}")

    # --- ERC20s
    mock_erc20 = boa.load_partial(str(ROOT / "contracts/mock/MockErc20.vy"))
    seen: set[str] = set()
    for label, address, name, symbol, decimals in (
        ("WETH (ADDYS)", addys["WETH"], "Wrapped Ether", "WETH", 18),
        ("WETH (CORE_TOKENS)", core["WETH"], "Wrapped Ether", "WETH", 18),
        ("USDG", core["USDG"], "Global Dollar", "USDG", 6),
    ):
        if address == ZERO_ADDRESS or address.lower() in seen:
            continue
        seen.add(address.lower())
        mock_erc20.deploy(account, name, symbol, decimals, 0, override_address=address)
        log.info(f"  {label:19} -> {address}")

    # --- Chainlink feeds. MockChainlinkFeed takes an 18-decimal price and
    # narrows it to the 8-decimal answer Chainlink actually reports.
    mock_feed = boa.load_partial(str(ROOT / "contracts/mock/MockChainlinkFeed.vy"))
    for label, key, price in (
        ("ETH/USD", "CHAINLINK_ETH_USD", 3_000 * 10**18),
        ("BTC/USD", "CHAINLINK_BTC_USD", 100_000 * 10**18),
        ("USDG/USD", "CHAINLINK_USDG_USD", 1 * 10**18),
    ):
        address = addys.get(key, ZERO_ADDRESS)
        if address == ZERO_ADDRESS:
            continue
        mock_feed.deploy(price, override_address=address)
        log.info(f"  Feed {label:14} -> {address}")

    # --- Morpho Vaults V2: an ERC-4626 vault at the collateral address plus a
    # factory answering isVaultV2. Deliberately NOT isMetaMorpho -- the real
    # chain runs Vaults V2, and mocking the MetaMorpho interface here is what
    # previously hid the mismatch behind a passing run.
    vault_addr = yields.get("MORPHO_STEAKHOUSE_USDG", ZERO_ADDRESS)
    if vault_addr != ZERO_ADDRESS:
        boa.load_partial(str(ROOT / "contracts/mock/MockErc4626Vault.vy")).deploy(
            core["USDG"], override_address=vault_addr
        )
        log.info(f"  VaultV2 collateral  -> {vault_addr}")

        factory = addys["MORPHO_V2_FACTORY"]
        if factory != ZERO_ADDRESS:
            boa.loads(
                f"""
@external
@view
def isVaultV2(_vault: address) -> bool:
    return _vault == {vault_addr}
""",
                override_address=factory,
            )
            log.info(f"  VaultV2Factory      -> {factory}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rpc", default=None, help="fork this RPC instead of running local")
    parser.add_argument("--local", action="store_true", help="explicit local mode (default)")
    parser.add_argument("--keep-history", default=None, help="write manifests here instead of a temp dir")
    parser.add_argument("--start", default="0", help="start timestamp")
    parser.add_argument("--end", default="0", help="end timestamp")
    parser.add_argument("--skip-verify", action="store_true", help="skip end-state checks")
    args = parser.parse_args()

    if args.rpc:
        log.h1(f"Forking {args.rpc}")
        boa.env.fork(args.rpc)
    else:
        log.h1("Running on a fresh in-memory pyevm chain")

    account = boa.env.generate_address()
    boa.env.set_balance(account, 10**24)
    boa.env.eoa = account
    log.info(f"Deployer: {account}")

    if not args.rpc:
        _install_local_mocks(account)

    history_dir = args.keep_history or tempfile.mkdtemp(prefix="rh-migrations-")
    os.makedirs(history_dir, exist_ok=True)
    log.info(f"History (scratch, NOT deployment evidence): {history_dir}")

    # Migration._run reads sender.address, so the raw boa Address needs wrapping
    deploy_args = DeployArgs(
        MockAccount(account),
        "robinhood-mainnet",
        ignore_logs=True,
        blueprint=BLUEPRINT,
        rpc=args.rpc,
    )

    vyper_files = load_vyper_files()
    log.info(f"Loaded {len(vyper_files)} Vyper files.")

    runner = MigrationRunner(str(MIGRATIONS_DIR), history_dir, vyper_files)
    gas = runner.run(deploy_args, start_timestamp=args.start, end_timestamp=args.end)

    log.h1(f"Migrations complete. Total gas: {gas:,}")

    if args.skip_verify:
        return 0

    log.h1("Verifying end state")

    # A Migration built against the finished history reads current-manifest.json,
    # which gives get_contract/get_address access to everything just deployed.
    from scripts.utils.migration import Migration
    from scripts.verify_rh_deployment import verify

    probe = Migration(deploy_args, vyper_files, "9999", None, history_dir)
    failures = verify(probe, deploy_args.blueprint, account, log)

    if failures:
        log.h1(f"{len(failures)} CHECK(S) FAILED")
        for failure in failures:
            log.info(f"  - {failure}")
        return 1

    log.h1("All end-state checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
