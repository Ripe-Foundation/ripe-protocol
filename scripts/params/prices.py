#!/usr/bin/env python3
"""
Output Price Source Configurations Script for Ripe Protocol

Fetches and displays all price source configurations from PriceDesk
on Base mainnet, formatted as markdown tables.

Includes:
- PriceDesk registry overview
- Per-source global config
- Per-source asset configurations (Chainlink, Pyth, BlueChipYield, UndyVault, Curve)

Usage:
    python scripts/params/prices.py
"""

import os
import sys
import time

import boa

# Import shared utilities
from params_utils import (
    RIPE_HQ,
    RPC_DELAY,
    ZERO_ADDRESS,
    PRICE_DESK_ID,
    PROTOCOL_NAMES,
    format_address,
    format_percent,
    format_blocks_to_time,
    get_token_name,
    print_table,
    setup_boa_etherscan,
    boa_fork_context,
    print_report_header,
    print_report_footer,
    output_to_file,
    print_local_gov_params,
    print_address_registry_params,
    print_timelock_params,
)

# ============================================================================
# Global state
# ============================================================================


class PriceState:
    """Holds loaded contracts and price source data."""

    def __init__(self):
        self.hq = None
        self.pd = None
        self.price_sources = {}  # reg_id -> {addr, description, contract}

    def get_known_addresses(self) -> dict:
        """Return known addresses for name resolution."""
        known = {}
        if self.pd:
            known[str(self.pd.address).lower()] = "PriceDesk"
        for reg_id, source in self.price_sources.items():
            known[source["address"].lower()] = source["description"]
        return known


state = PriceState()


# ============================================================================
# Contract Loading
# ============================================================================


def initialize_prices():
    """Load PriceDesk and all price source contracts."""
    print("Loading price source configurations...", file=sys.stderr)

    # Load HQ and PriceDesk
    state.hq = boa.from_etherscan(RIPE_HQ, name="RipeHQ")
    time.sleep(RPC_DELAY)

    pd_addr = state.hq.getAddr(PRICE_DESK_ID)
    state.pd = boa.from_etherscan(pd_addr, name="PriceDesk")
    time.sleep(RPC_DELAY)

    # Load all price sources
    num_sources = state.pd.numAddrs()
    print(f"  Found {num_sources - 1} registered price sources...", file=sys.stderr)

    for i in range(1, num_sources):
        time.sleep(RPC_DELAY)
        addr_info = state.pd.addrInfo(i)
        addr = str(addr_info.addr)
        if addr == ZERO_ADDRESS:
            continue

        time.sleep(RPC_DELAY)
        source = boa.from_etherscan(addr, name=f"PriceSource_{i}")

        state.price_sources[i] = {
            "address": addr,
            "description": addr_info.description,
            "contract": source,
        }

    print("  All price sources loaded.\n", file=sys.stderr)


# ============================================================================
# Output Functions
# ============================================================================


def print_table_of_contents():
    """Print a clickable table of contents."""
    print("""
## Table of Contents

1. [PriceDesk Overview](#price-desk-overview)
2. [Price Source Configurations](#price-source-configs)
""")

    # Add links for each price source
    for reg_id, source in sorted(state.price_sources.items()):
        anchor = source["description"].lower().replace(" ", "-")
        print(f"   - [{source['description']}](#{anchor})")


def print_price_desk_overview():
    """Print PriceDesk registry overview."""
    print("\n<a id=\"price-desk-overview\"></a>")
    print("## PriceDesk Overview")
    print(f"\nAddress: `{state.pd.address}`\n")

    # Constants
    eth_addr = str(state.pd.ETH())
    rows = [
        ("ETH", format_address(eth_addr)),
    ]
    print_table("Constants", ["Parameter", "Value"], rows, level=3)

    # AddressRegistry Module params
    print_address_registry_params(state.pd, registry_name="price sources", level=3)

    # LocalGov Module params
    print_local_gov_params(state.pd, state.get_known_addresses, level=3)

    # Registered sources summary
    print("\n### Registered Price Sources")
    print("\n| Reg ID | Description | Address |")
    print("| --- | --- | --- |")
    for reg_id, source in sorted(state.price_sources.items()):
        print(f"| {reg_id} | {source['description']} | `{source['address']}` |")


def print_price_source_config(reg_id: int, source_info: dict):
    """Print detailed configuration for a single price source."""
    source = source_info["contract"]
    source_name = source_info["description"]
    anchor = source_name.lower().replace(" ", "-")

    print(f"\n<a id=\"{anchor}\"></a>")
    print(f"### {source_name}")
    print(f"Address: `{source_info['address']}`")

    # Global config - these methods are optional depending on price source type
    rows = []
    if hasattr(source, 'isPaused'):
        rows.append(("isPaused", source.isPaused()))

    if hasattr(source, 'maxConfidenceRatio'):
        rows.append(("maxConfidenceRatio", format_percent(source.maxConfidenceRatio())))

    num_assets = 0
    if hasattr(source, 'numAssets'):
        num_assets = source.numAssets()
        rows.append(("numAssets", num_assets - 1 if num_assets > 0 else 0))

    if rows:
        print_table("Global Config", ["Parameter", "Value"], rows, level=4)

    # LocalGov Module params
    print_local_gov_params(source, state.get_known_addresses, level=4)

    # TimeLock Module params
    print_timelock_params(source, level=4)

    # Per-asset configurations
    if num_assets > 1:
        _print_price_source_assets(source, source_name, num_assets)

    # GREEN Reference Pool config (Curve Prices only)
    if hasattr(source, 'greenRefPoolConfig'):
        _print_green_ref_pool_config(source)

    # Pending price feed changes
    if num_assets > 1:
        _print_pending_price_changes(source, num_assets)


def _print_green_ref_pool_config(source):
    """Print GREEN Reference Pool configuration for Curve Prices."""
    try:
        config = source.greenRefPoolConfig()
        data = source.greenRefPoolData()
    except Exception:
        return  # No GREEN ref pool configured

    # Check if pool is configured (non-zero address)
    if str(config.pool) == ZERO_ADDRESS:
        return

    print("\n#### GREEN Reference Pool Configuration")

    # Get alt asset name
    alt_asset_name = get_token_name(str(config.altAsset))

    print(f"\n**Pool Config**")
    print(f"- Pool: `{config.pool}`")
    print(f"- LP Token: `{config.lpToken}`")
    print(f"- GREEN Index: {config.greenIndex}")
    print(f"- Alt Asset: {alt_asset_name} (`{config.altAsset}`)")
    print(f"- Alt Asset Decimals: {config.altAssetDecimals}")
    print(f"- Max Num Snapshots: {config.maxNumSnapshots}")
    print(f"- Danger Trigger: {format_percent(config.dangerTrigger)}")
    print(f"- Stale Blocks: {format_blocks_to_time(config.staleBlocks)}")
    print(f"- Stabilizer Adjust Weight: {config.stabilizerAdjustWeight}")
    print(f"- Stabilizer Max Pool Debt: {config.stabilizerMaxPoolDebt / (10**18):,.2f} GREEN")

    # Current status from data
    print(f"\n**Current Status**")
    print(f"- Num Blocks In Danger: {data.numBlocksInDanger}")
    print(f"- Next Index: {data.nextIndex}")

    # Last snapshot
    if data.lastSnapshot.update > 0:
        now = int(time.time())
        seconds_ago = now - data.lastSnapshot.update
        if seconds_ago < 60:
            time_ago = f"~{seconds_ago:.0f}s ago"
        elif seconds_ago < 3600:
            time_ago = f"~{seconds_ago/60:.1f}m ago"
        elif seconds_ago < 86400:
            time_ago = f"~{seconds_ago/3600:.1f}h ago"
        else:
            time_ago = f"~{seconds_ago/86400:.1f}d ago"

        print(f"- Last Snapshot:")
        print(f"  - GREEN Balance: {data.lastSnapshot.greenBalance / (10**18):,.2f} GREEN")
        print(f"  - Ratio: {data.lastSnapshot.ratio / (10**18):.6f}")
        print(f"  - In Danger: {data.lastSnapshot.inDanger}")
        print(f"  - Update: {data.lastSnapshot.update} ({time_ago})")


def _print_pending_price_changes(source, num_assets: int):
    """Print pending price feed updates for a price source."""
    # Check if source has pending update checking method
    if not hasattr(source, 'hasPendingPriceFeedUpdate'):
        return

    pending_assets = []

    # Check each registered asset for pending updates
    for j in range(1, num_assets):
        time.sleep(RPC_DELAY)
        asset_addr = str(source.assets(j))
        if asset_addr == ZERO_ADDRESS:
            continue

        try:
            time.sleep(RPC_DELAY)
            has_pending = source.hasPendingPriceFeedUpdate(asset_addr)
            if has_pending:
                asset_name = get_token_name(asset_addr)
                pending_assets.append({
                    "asset": asset_name,
                    "asset_addr": asset_addr,
                })
        except Exception:
            continue

    if not pending_assets:
        return

    print(f"\n#### ⏳ Pending Price Feed Updates ({len(pending_assets)})")

    for item in pending_assets:
        asset_name = item["asset"]
        asset_addr = item["asset_addr"]

        print(f"\n**{asset_name}** (`{asset_addr}`)")

        # Get pending config details based on source type
        try:
            if hasattr(source, 'pendingUpdates'):
                # Chainlink, Pyth, Stork, Curve
                pending = source.pendingUpdates(asset_addr)
                if hasattr(pending, 'actionId') and pending.actionId > 0:
                    print(f"- Action ID: {pending.actionId}")

                    # Try to get action info from TimeLock
                    if hasattr(source, 'actions'):
                        action = source.actions(pending.actionId)
                        if hasattr(action, 'confirmBlock') and action.confirmBlock > 0:
                            print(f"- Confirm Block: {action.confirmBlock}")

                    # Show pending config details
                    if hasattr(pending, 'config'):
                        config = pending.config
                        if hasattr(config, 'feed') and str(config.feed) != ZERO_ADDRESS:
                            print(f"- Pending Feed: `{config.feed}`")
                        if hasattr(config, 'feedId') and config.feedId:
                            print(f"- Pending Feed ID: `0x{config.feedId.hex()}`")
                        if hasattr(config, 'staleTime'):
                            print(f"- Pending Stale Time: {config.staleTime}s")
                        if hasattr(config, 'pool') and str(config.pool) != ZERO_ADDRESS:
                            print(f"- Pending Pool: `{config.pool}`")

            elif hasattr(source, 'pendingPriceConfigs'):
                # BlueChipYield, UndyVault, AeroRipe
                pending = source.pendingPriceConfigs(asset_addr)
                if hasattr(pending, 'actionId') and pending.actionId > 0:
                    print(f"- Action ID: {pending.actionId}")

                    # Try to get action info from TimeLock
                    if hasattr(source, 'actions'):
                        action = source.actions(pending.actionId)
                        if hasattr(action, 'confirmBlock') and action.confirmBlock > 0:
                            print(f"- Confirm Block: {action.confirmBlock}")

                    # Show pending config details
                    if hasattr(pending, 'config'):
                        config = pending.config
                        if hasattr(config, 'underlyingAsset') and str(config.underlyingAsset) != ZERO_ADDRESS:
                            underlying_name = get_token_name(str(config.underlyingAsset))
                            print(f"- Pending Underlying: {underlying_name}")
                        if hasattr(config, 'minSnapshotDelay'):
                            print(f"- Pending Min Snapshot Delay: {format_blocks_to_time(config.minSnapshotDelay)}")
                        if hasattr(config, 'staleTime'):
                            print(f"- Pending Stale Time: {config.staleTime}s")

        except Exception as e:
            print(f"- Error retrieving pending config: {e}")


def _print_price_source_assets(source, source_name: str, num_assets: int):
    """Print per-asset config for a price source."""
    asset_rows = []  # For Chainlink (table format)
    curve_configs = []
    yield_configs = []  # BlueChipYield / UndyVault with underlyingAsset
    pyth_configs = []
    stork_configs = []
    aero_configs = []  # AeroRipePrices (priceConfigs without underlyingAsset)

    for j in range(1, num_assets):
        time.sleep(RPC_DELAY)
        asset_addr = str(source.assets(j))
        if asset_addr == ZERO_ADDRESS:
            continue

        asset_name = get_token_name(asset_addr)

        # Different price source types have different config methods
        if hasattr(source, 'feedConfig'):
            config = source.feedConfig(asset_addr)
            if hasattr(config, 'feed'):
                # Chainlink: feed, decimals, needsEthToUsd, needsBtcToUsd, staleTime
                feed_addr = format_address(str(config.feed)) if str(config.feed) != ZERO_ADDRESS else "N/A"
                needs_eth = getattr(config, 'needsEthToUsd', False)
                needs_btc = getattr(config, 'needsBtcToUsd', False)
                stale = getattr(config, 'staleTime', 0)
                asset_rows.append([
                    asset_name,
                    feed_addr,
                    f"ETH:{needs_eth}, BTC:{needs_btc}",
                    f"{stale}s"
                ])
            elif hasattr(config, 'feedId'):
                # Pyth or Stork: feedId, staleTime
                # Distinguish by source having maxConfidenceRatio (Pyth) or not (Stork)
                if hasattr(source, 'maxConfidenceRatio'):
                    pyth_configs.append({
                        "asset": asset_name,
                        "asset_addr": asset_addr,
                        "config": config,
                    })
                else:
                    stork_configs.append({
                        "asset": asset_name,
                        "asset_addr": asset_addr,
                        "config": config,
                    })
        elif hasattr(source, 'priceConfigs'):
            config = source.priceConfigs(asset_addr)
            # BlueChipYield/UndyVault have underlyingAsset, AeroRipePrices does not
            if hasattr(config, 'underlyingAsset') and str(config.underlyingAsset) != ZERO_ADDRESS:
                yield_configs.append({
                    "asset": asset_name,
                    "asset_addr": asset_addr,
                    "config": config,
                })
            elif hasattr(config, 'minSnapshotDelay') and config.minSnapshotDelay > 0:
                # AeroRipePrices style - has minSnapshotDelay but no underlyingAsset
                aero_configs.append({
                    "asset": asset_name,
                    "asset_addr": asset_addr,
                    "config": config,
                })
        elif hasattr(source, 'curveConfig'):
            # Curve style - collect for separate display
            config = source.curveConfig(asset_addr)
            if config and str(config.pool) != ZERO_ADDRESS:
                curve_configs.append({
                    "asset": asset_name,
                    "asset_addr": asset_addr,
                    "config": config,
                })
        else:
            # Fallback - just show asset is registered
            asset_rows.append([asset_name, "Configured", "-", "-"])

    if asset_rows:
        headers = ["Asset", "Feed/Underlying", "Config", "StaleTime"]
        print(f"\n#### Registered Assets ({len(asset_rows)})")
        print(f"| {' | '.join(headers)} |")
        print(f"| {' | '.join(['---' for _ in headers])} |")
        for row in asset_rows:
            print(f"| {' | '.join(str(cell) for cell in row)} |")

    # Curve configs - display separately in cleaner format
    if curve_configs:
        pool_type_names = {
            1: "STABLESWAP_NG",
            2: "TWO_CRYPTO_NG",
            4: "TRICRYPTO_NG",
            8: "TWO_CRYPTO",
            16: "METAPOOL",
            32: "CRYPTO",
        }

        print(f"\n#### Curve Pool Configs ({len(curve_configs)})")
        for item in curve_configs:
            config = item["config"]
            asset_name = item["asset"]
            pool_type = pool_type_names.get(config.poolType, f"Type:{config.poolType}")

            # Get underlying tokens
            underlying_names = []
            for k in range(config.numUnderlying):
                u_addr = str(config.underlying[k])
                if u_addr != ZERO_ADDRESS:
                    underlying_names.append(get_token_name(u_addr))

            print(f"\n**{asset_name}**")
            print(f"- Pool: `{config.pool}`")
            print(f"- Type: {pool_type}")
            print(f"- Underlying ({config.numUnderlying}): {', '.join(underlying_names)}")
            print(f"- LP Token: `{config.lpToken}`")
            print(f"- Has Eco Token: {config.hasEcoToken}")

    # Yield configs (BlueChipYield / UndyVault) - display in list format
    if yield_configs:
        print(f"\n#### Yield Token Configs ({len(yield_configs)})")
        for item in yield_configs:
            config = item["config"]
            asset_name = item["asset"]

            # Get protocol name
            protocol_id = getattr(config, 'protocol', 0)
            protocol_name = PROTOCOL_NAMES.get(protocol_id, f"ID:{protocol_id}")

            # Get underlying token name
            underlying = get_token_name(str(config.underlyingAsset))

            # Get last snapshot info
            last_snapshot = getattr(config, 'lastSnapshot', None)

            print(f"\n**{asset_name}**")
            print(f"- Protocol: {protocol_name}")
            print(f"- Underlying: {underlying} (`{config.underlyingAsset}`)")
            print(f"- Underlying Decimals: {config.underlyingDecimals}")
            print(f"- Vault Token Decimals: {config.vaultTokenDecimals}")
            print(f"- Min Snapshot Delay: {format_blocks_to_time(config.minSnapshotDelay)}")
            print(f"- Max Snapshots: {config.maxNumSnapshots}")
            print(f"- Max Upside Deviation: {config.maxUpsideDeviation / 100:.2f}%")
            print(f"- Stale Time: {config.staleTime}s")
            print(f"- Next Index: {config.nextIndex}")
            if last_snapshot and last_snapshot.lastUpdate > 0:
                # lastUpdate is a Unix timestamp - calculate time ago
                now = int(time.time())
                seconds_ago = now - last_snapshot.lastUpdate
                if seconds_ago < 60:
                    time_ago = f"~{seconds_ago:.0f}s ago"
                elif seconds_ago < 3600:
                    time_ago = f"~{seconds_ago/60:.1f}m ago"
                elif seconds_ago < 86400:
                    time_ago = f"~{seconds_ago/3600:.1f}h ago"
                else:
                    time_ago = f"~{seconds_ago/86400:.1f}d ago"
                print(f"- Last Snapshot: supply={last_snapshot.totalSupply}, pps={last_snapshot.pricePerShare}, block={last_snapshot.lastUpdate} ({time_ago})")

    # Pyth configs - display in list format
    if pyth_configs:
        print(f"\n#### Pyth Feed Configs ({len(pyth_configs)})")
        for item in pyth_configs:
            config = item["config"]
            asset_name = item["asset"]
            asset_addr = item["asset_addr"]

            feed_id = config.feedId.hex() if config.feedId else "N/A"
            stale = getattr(config, 'staleTime', 0)

            print(f"\n**{asset_name}**")
            print(f"- Asset Address: `{asset_addr}`")
            print(f"- Feed ID: `0x{feed_id}`")
            print(f"- Stale Time: {stale}s")

    # Stork configs - display in list format
    if stork_configs:
        print(f"\n#### Stork Feed Configs ({len(stork_configs)})")
        for item in stork_configs:
            config = item["config"]
            asset_name = item["asset"]
            asset_addr = item["asset_addr"]

            feed_id = config.feedId.hex() if config.feedId else "N/A"
            stale = getattr(config, 'staleTime', 0)

            print(f"\n**{asset_name}**")
            print(f"- Asset Address: `{asset_addr}`")
            print(f"- Feed ID: `0x{feed_id}`")
            print(f"- Stale Time: {stale}s")

    # AeroRipe configs - display in list format
    if aero_configs:
        print(f"\n#### RIPE Price Configs ({len(aero_configs)})")
        for item in aero_configs:
            config = item["config"]
            asset_name = item["asset"]
            asset_addr = item["asset_addr"]

            # Get last snapshot info
            last_snapshot = getattr(config, 'lastSnapshot', None)

            print(f"\n**{asset_name}**")
            print(f"- Asset Address: `{asset_addr}`")
            print(f"- Min Snapshot Delay: {format_blocks_to_time(config.minSnapshotDelay)}")
            print(f"- Max Snapshots: {config.maxNumSnapshots}")
            print(f"- Max Upside Deviation: {config.maxUpsideDeviation / 100:.2f}%")
            print(f"- Stale Time: {config.staleTime}s")
            print(f"- Next Index: {config.nextIndex}")
            if last_snapshot and last_snapshot.lastUpdate > 0:
                # lastUpdate is a Unix timestamp - calculate time ago
                now = int(time.time())
                seconds_ago = now - last_snapshot.lastUpdate
                if seconds_ago < 60:
                    time_ago = f"~{seconds_ago:.0f}s ago"
                elif seconds_ago < 3600:
                    time_ago = f"~{seconds_ago/60:.1f}m ago"
                elif seconds_ago < 86400:
                    time_ago = f"~{seconds_ago/3600:.1f}h ago"
                else:
                    time_ago = f"~{seconds_ago/86400:.1f}d ago"
                print(f"- Last Snapshot: price={last_snapshot.price}, block={last_snapshot.lastUpdate} ({time_ago})")


def print_all_price_sources():
    """Print all price source configurations."""
    print("\n<a id=\"price-source-configs\"></a>")
    print("## Price Source Configurations")

    for reg_id in sorted(state.price_sources.keys()):
        source_info = state.price_sources[reg_id]
        print_price_source_config(reg_id, source_info)
        print("\n---")


# ============================================================================
# Main Entry Point
# ============================================================================


def main():
    """Main entry point."""
    # Output file path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, "prices_output.md")

    print("Connecting to Base mainnet via Alchemy...", file=sys.stderr)

    # Set etherscan API
    setup_boa_etherscan()

    # Fork at latest block
    with boa_fork_context() as block_number:
        print(f"Connected. Block: {block_number}\n", file=sys.stderr)

        # Load all price source configurations
        initialize_prices()

        print(f"Writing output to {output_file}...", file=sys.stderr)

        # Write report to file
        with output_to_file(output_file):
            # Header
            print_report_header("Ripe Protocol - Price Source Configurations", block_number)

            print("\nDetailed configuration for all price sources registered in PriceDesk.\n")

            # Table of Contents
            print_table_of_contents()

            # PriceDesk overview
            print_price_desk_overview()

            # All price source configs
            print_all_price_sources()

            # Footer
            print_report_footer(block_number)

        print(f"Done! Output saved to {output_file}", file=sys.stderr)


if __name__ == "__main__":
    main()
