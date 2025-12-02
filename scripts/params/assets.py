#!/usr/bin/env python3
"""
Output Asset Configurations Script for Ripe Protocol

Fetches and displays all per-asset configurations from MissionControl
on Base mainnet, formatted as markdown tables.

Includes:
- Registered assets overview
- Per-asset deposit settings
- Per-asset debt terms
- Per-asset liquidation settings
- Per-asset action flags
- Per-asset custom auction params

Usage:
    python scripts/params/assets.py
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
    MISSION_CONTROL_ID,
    format_address,
    format_percent,
    format_wei,
    get_token_name,
    print_table,
    setup_boa_etherscan,
    boa_fork_context,
    print_report_header,
    print_report_footer,
    output_to_file,
)

# ============================================================================
# Global state
# ============================================================================


class AssetState:
    """Holds loaded contracts and asset data."""

    def __init__(self):
        self.hq = None
        self.mc = None
        self.assets = []  # List of asset addresses
        self.asset_configs = {}  # address -> config

    def get_known_addresses(self) -> dict:
        """Return known addresses for name resolution."""
        known = {}
        if self.mc:
            known[str(self.mc.address).lower()] = "MissionControl"
        return known


state = AssetState()


# ============================================================================
# Contract Loading
# ============================================================================


def initialize_assets():
    """Load MissionControl and all asset configurations."""
    print("Loading asset configurations...", file=sys.stderr)

    # Load HQ and MissionControl
    state.hq = boa.from_etherscan(RIPE_HQ, name="RipeHQ")
    time.sleep(RPC_DELAY)

    mc_addr = state.hq.getAddr(MISSION_CONTROL_ID)
    state.mc = boa.from_etherscan(mc_addr, name="MissionControl")
    time.sleep(RPC_DELAY)

    # Load all assets
    num_assets = state.mc.numAssets()
    print(f"  Found {num_assets - 1} registered assets...", file=sys.stderr)

    for i in range(1, num_assets):
        time.sleep(RPC_DELAY)
        asset_addr = str(state.mc.assets(i))
        state.assets.append(asset_addr)

        time.sleep(RPC_DELAY)
        asset_config = state.mc.assetConfig(asset_addr)
        state.asset_configs[asset_addr] = asset_config

    print("  All asset configurations loaded.\n", file=sys.stderr)


# ============================================================================
# Output Functions
# ============================================================================


def print_table_of_contents():
    """Print a clickable table of contents."""
    print("""
## Table of Contents

1. [Registered Assets Overview](#assets-overview)
2. [Per-Asset Configurations](#per-asset-configs)
""")

    # Add links for each asset
    for i, asset_addr in enumerate(state.assets, 1):
        asset_name = get_token_name(asset_addr)
        anchor = asset_name.lower().replace(" ", "-").replace("(", "").replace(")", "")
        print(f"   - [{asset_name}](#{anchor})")


def print_assets_overview():
    """Print overview table of all registered assets."""
    print("\n<a id=\"assets-overview\"></a>")
    print("## Registered Assets Overview")
    print(f"\n*{len(state.assets)} total registered assets*\n")

    headers = [
        "Asset", "Vault IDs", "LTV", "Liq Threshold", "Borrow Rate",
        "canDeposit", "canBorrow"
    ]
    rows = []

    for asset_addr in state.assets:
        config = state.asset_configs[asset_addr]
        debt_terms = config.debtTerms

        vault_ids = config.vaultIds
        vault_ids_str = ", ".join(str(v) for v in vault_ids) if vault_ids else "None"

        rows.append([
            format_address(asset_addr, known_addresses_fn=state.get_known_addresses),
            vault_ids_str,
            format_percent(debt_terms.ltv),
            format_percent(debt_terms.liqThreshold),
            format_percent(debt_terms.borrowRate),
            config.canDeposit,
            debt_terms.ltv > 0,  # has LTV means can borrow against it
        ])

    print(f"| {' | '.join(headers)} |")
    print(f"| {' | '.join(['---' for _ in headers])} |")
    for row in rows:
        print(f"| {' | '.join(str(cell) for cell in row)} |")


def print_asset_details(asset_addr: str):
    """Print detailed configuration for a single asset."""
    config = state.asset_configs[asset_addr]
    debt_terms = config.debtTerms
    custom_auction = config.customAuctionParams

    asset_name = get_token_name(asset_addr)
    anchor = asset_name.lower().replace(" ", "-").replace("(", "").replace(")", "")

    print(f"\n<a id=\"{anchor}\"></a>")
    print(f"### {asset_name}")
    print(f"Address: `{asset_addr}`")

    # Deposit Settings
    rows = [
        ("vaultIds", ", ".join(str(v) for v in config.vaultIds) if config.vaultIds else "None"),
        ("stakersPointsAlloc", format_percent(config.stakersPointsAlloc)),
        ("voterPointsAlloc", format_percent(config.voterPointsAlloc)),
        ("perUserDepositLimit", format_wei(config.perUserDepositLimit, 6)),
        ("globalDepositLimit", format_wei(config.globalDepositLimit, 6)),
        ("minDepositBalance", format_wei(config.minDepositBalance, 6)),
    ]
    print_table("Deposit Settings", ["Parameter", "Value"], rows, level=4)

    # Debt Terms
    rows = [
        ("ltv", format_percent(debt_terms.ltv)),
        ("redemptionThreshold", format_percent(debt_terms.redemptionThreshold)),
        ("liqThreshold", format_percent(debt_terms.liqThreshold)),
        ("liqFee", format_percent(debt_terms.liqFee)),
        ("borrowRate", format_percent(debt_terms.borrowRate)),
        ("daowry", format_percent(debt_terms.daowry)),
    ]
    print_table("Debt Terms", ["Parameter", "Value"], rows, level=4)

    # Liquidation Settings
    rows = [
        ("shouldBurnAsPayment", config.shouldBurnAsPayment),
        ("shouldTransferToEndaoment", config.shouldTransferToEndaoment),
        ("shouldSwapInStabPools", config.shouldSwapInStabPools),
        ("shouldAuctionInstantly", config.shouldAuctionInstantly),
        ("specialStabPoolId", config.specialStabPoolId if config.specialStabPoolId != 0 else "None"),
    ]
    print_table("Liquidation Settings", ["Parameter", "Value"], rows, level=4)

    # Action Flags
    whitelist_addr = str(config.whitelist)
    rows = [
        ("canDeposit", config.canDeposit),
        ("canWithdraw", config.canWithdraw),
        ("canRedeemCollateral", config.canRedeemCollateral),
        ("canRedeemInStabPool", config.canRedeemInStabPool),
        ("canBuyInAuction", config.canBuyInAuction),
        ("canClaimInStabPool", config.canClaimInStabPool),
        ("whitelist", format_address(whitelist_addr) if whitelist_addr != ZERO_ADDRESS else "None"),
        ("isNft", config.isNft),
    ]
    print_table("Action Flags", ["Parameter", "Value"], rows, level=4)

    # Custom Auction Params (if set)
    if custom_auction.hasParams:
        from params_utils import format_blocks_to_time
        rows = [
            ("hasParams", custom_auction.hasParams),
            ("startDiscount", format_percent(custom_auction.startDiscount)),
            ("maxDiscount", format_percent(custom_auction.maxDiscount)),
            ("delay", format_blocks_to_time(custom_auction.delay)),
            ("duration", format_blocks_to_time(custom_auction.duration)),
        ]
        print_table("Custom Auction Parameters", ["Parameter", "Value"], rows, level=4)


def print_all_asset_details():
    """Print detailed configuration for all assets."""
    print("\n<a id=\"per-asset-configs\"></a>")
    print("## Per-Asset Configurations")

    for asset_addr in state.assets:
        print_asset_details(asset_addr)
        print("\n---")


# ============================================================================
# Main Entry Point
# ============================================================================


def main():
    """Main entry point."""
    # Output file path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, "assets_output.md")

    print("Connecting to Base mainnet via Alchemy...", file=sys.stderr)

    # Set etherscan API
    setup_boa_etherscan()

    # Fork at latest block
    with boa_fork_context() as block_number:
        print(f"Connected. Block: {block_number}\n", file=sys.stderr)

        # Load all asset configurations
        initialize_assets()

        print(f"Writing output to {output_file}...", file=sys.stderr)

        # Write report to file
        with output_to_file(output_file):
            # Header
            print_report_header("Ripe Protocol - Asset Configurations", block_number)

            print("\nDetailed configuration for all registered assets in MissionControl.\n")

            # Table of Contents
            print_table_of_contents()

            # Assets overview
            print_assets_overview()

            # Detailed per-asset configs
            print_all_asset_details()

            # Footer
            print_report_footer(block_number)

        print(f"Done! Output saved to {output_file}", file=sys.stderr)


if __name__ == "__main__":
    main()
