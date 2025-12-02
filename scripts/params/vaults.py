#!/usr/bin/env python3
"""
Output Vault Configurations Script for Ripe Protocol

Fetches and displays all vault configurations from VaultBook
on Base mainnet, formatted as markdown tables.

Includes:
- VaultBook registry overview
- StabilityPool configuration
- RipeGovVault configuration
- Per-vault asset balances

Usage:
    python scripts/params/vaults.py
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
    VAULT_BOOK_ID,
    STABILITY_POOL_VB_ID,
    RIPE_GOV_VAULT_VB_ID,
    format_address,
    format_blocks_to_time,
    format_token_amount,
    format_token_amount_precise,
    get_token_name,
    get_token_decimals,
    print_table,
    setup_boa_etherscan,
    boa_fork_context,
    print_report_header,
    print_report_footer,
    output_to_file,
    print_local_gov_params,
    print_address_registry_params,
)

# ============================================================================
# Global state
# ============================================================================


class VaultState:
    """Holds loaded contracts and vault data."""

    def __init__(self):
        self.hq = None
        self.vb = None
        self.vaults = {}  # reg_id -> {addr, description, contract}

    def get_known_addresses(self) -> dict:
        """Return known addresses for name resolution."""
        known = {}
        if self.vb:
            known[str(self.vb.address).lower()] = "VaultBook"
        for reg_id, vault in self.vaults.items():
            known[vault["address"].lower()] = vault["description"]
        return known


state = VaultState()


# ============================================================================
# Contract Loading
# ============================================================================


def initialize_vaults():
    """Load VaultBook and all vault contracts."""
    print("Loading vault configurations...", file=sys.stderr)

    # Load HQ and VaultBook
    state.hq = boa.from_etherscan(RIPE_HQ, name="RipeHQ")
    time.sleep(RPC_DELAY)

    vb_addr = state.hq.getAddr(VAULT_BOOK_ID)
    state.vb = boa.from_etherscan(vb_addr, name="VaultBook")
    time.sleep(RPC_DELAY)

    # Load all vaults
    num_vaults = state.vb.numAddrs()
    print(f"  Found {num_vaults - 1} registered vaults...", file=sys.stderr)

    for i in range(1, num_vaults):
        time.sleep(RPC_DELAY)
        addr_info = state.vb.addrInfo(i)
        addr = str(addr_info.addr)
        if addr == ZERO_ADDRESS:
            continue

        time.sleep(RPC_DELAY)
        vault = boa.from_etherscan(addr, name=f"Vault_{i}")

        state.vaults[i] = {
            "address": addr,
            "description": addr_info.description,
            "contract": vault,
        }

    print("  All vaults loaded.\n", file=sys.stderr)


# ============================================================================
# Output Functions
# ============================================================================


def print_table_of_contents():
    """Print a clickable table of contents."""
    print("""
## Table of Contents

1. [VaultBook Overview](#vault-book-overview)
2. [Vault Configurations](#vault-configs)
""")

    # Add links for each vault
    for reg_id, vault in sorted(state.vaults.items()):
        anchor = vault["description"].lower().replace(" ", "-")
        print(f"   - [{vault['description']}](#{anchor})")


def print_vault_book_overview():
    """Print VaultBook registry overview."""
    print("\n<a id=\"vault-book-overview\"></a>")
    print("## VaultBook Overview")
    print(f"\nAddress: `{state.vb.address}`\n")

    # AddressRegistry Module params
    print_address_registry_params(state.vb, registry_name="vaults", level=3)

    # LocalGov Module params
    print_local_gov_params(state.vb, state.get_known_addresses, level=3)

    # Registered vaults summary
    print("\n### Registered Vaults")
    print("\n| Reg ID | Description | Address |")
    print("| --- | --- | --- |")
    for reg_id, vault in sorted(state.vaults.items()):
        print(f"| {reg_id} | {vault['description']} | `{vault['address']}` |")


def print_vault_config(reg_id: int, vault_info: dict):
    """Print detailed configuration for a single vault."""
    vault = vault_info["contract"]
    vault_name = vault_info["description"]
    anchor = vault_name.lower().replace(" ", "-")

    print(f"\n<a id=\"{anchor}\"></a>")
    print(f"### {vault_name}")
    print(f"Address: `{vault_info['address']}`")

    # Basic status
    rows = []
    if hasattr(vault, 'isPaused'):
        rows.append(("isPaused", vault.isPaused()))

    num_assets = 0
    if hasattr(vault, 'numAssets'):
        num_assets = vault.numAssets()
        rows.append(("numAssets", num_assets - 1 if num_assets > 0 else 0))

    # RipeGovVault specific
    if hasattr(vault, 'totalGovPoints'):
        total_points = vault.totalGovPoints()
        rows.append(("totalGovPoints", f"{total_points:,}"))

    if rows:
        print_table("Vault Status", ["Parameter", "Value"], rows, level=4)

    # Asset balances (if vault has vaultAssets method)
    if num_assets > 1 and hasattr(vault, 'vaultAssets'):
        _print_vault_assets(vault, num_assets)
        # Stability Pool specific: claimable assets
        _print_stability_pool_claimables(vault, num_assets)


def _print_vault_assets(vault, num_assets: int):
    """Print assets held in a vault with balances."""
    asset_rows = []

    for j in range(1, num_assets):
        time.sleep(RPC_DELAY)
        asset_addr = str(vault.vaultAssets(j))
        if asset_addr == ZERO_ADDRESS:
            continue

        asset_name = get_token_name(asset_addr)
        total_bal = vault.getTotalAmountForVault(asset_addr)
        decimals = get_token_decimals(asset_addr)

        asset_rows.append([
            asset_name,
            f"`{asset_addr}`",
            format_token_amount(total_bal, decimals, ""),
        ])

    if asset_rows:
        print(f"\n#### Assets in Vault ({len(asset_rows)})")
        print("| Asset | Address | Total Balance |")
        print("| --- | --- | --- |")
        for row in asset_rows:
            print(f"| {row[0]} | {row[1]} | {row[2]} |")


def _print_stability_pool_claimables(vault, num_assets: int):
    """Print claimable assets for each stability pool asset."""
    # Check if this vault has claimable methods (StabilityPool)
    if not hasattr(vault, 'numClaimableAssets'):
        return

    print("\n#### Claimable Assets by Stability Pool Asset")

    # Track all unique claimable assets for totalClaimableBalances
    all_claimable_assets = set()

    for j in range(1, num_assets):
        time.sleep(RPC_DELAY)
        stab_asset_addr = str(vault.vaultAssets(j))
        if stab_asset_addr == ZERO_ADDRESS:
            continue

        stab_asset_name = get_token_name(stab_asset_addr)
        num_claimable = vault.numClaimableAssets(stab_asset_addr)

        print(f"\n**{stab_asset_name}** (`{stab_asset_addr}`)")

        if num_claimable == 0:
            print("- No claimable assets")
            continue

        print(f"- Num Claimable Assets: {num_claimable}")

        for k in range(1, num_claimable + 1):
            time.sleep(RPC_DELAY)
            claimable_addr = str(vault.claimableAssets(stab_asset_addr, k))
            if claimable_addr == ZERO_ADDRESS:
                continue

            all_claimable_assets.add(claimable_addr)
            claimable_name = get_token_name(claimable_addr)
            claimable_decimals = get_token_decimals(claimable_addr)

            time.sleep(RPC_DELAY)
            claimable_bal = vault.claimableBalances(stab_asset_addr, claimable_addr)

            print(f"  - {claimable_name}: {format_token_amount_precise(claimable_bal, claimable_decimals, claimable_name)}")

    # Print totalClaimableBalances for all unique claimable assets
    if all_claimable_assets:
        print("\n#### Total Claimable Balances (across all stability pools)")
        print("| Asset | Total Claimable Balance |")
        print("| --- | --- |")
        for claimable_addr in sorted(all_claimable_assets):
            time.sleep(RPC_DELAY)
            claimable_name = get_token_name(claimable_addr)
            claimable_decimals = get_token_decimals(claimable_addr)
            total_claimable = vault.totalClaimableBalances(claimable_addr)
            print(f"| {claimable_name} | {format_token_amount_precise(total_claimable, claimable_decimals, claimable_name)} |")


def print_all_vaults():
    """Print all vault configurations."""
    print("\n<a id=\"vault-configs\"></a>")
    print("## Vault Configurations")

    for reg_id in sorted(state.vaults.keys()):
        vault_info = state.vaults[reg_id]
        print_vault_config(reg_id, vault_info)
        print("\n---")


# ============================================================================
# Main Entry Point
# ============================================================================


def main():
    """Main entry point."""
    # Output file path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, "vaults_output.md")

    print("Connecting to Base mainnet via Alchemy...", file=sys.stderr)

    # Set etherscan API
    setup_boa_etherscan()

    # Fork at latest block
    with boa_fork_context() as block_number:
        print(f"Connected. Block: {block_number}\n", file=sys.stderr)

        # Load all vault configurations
        initialize_vaults()

        print(f"Writing output to {output_file}...", file=sys.stderr)

        # Write report to file
        with output_to_file(output_file):
            # Header
            print_report_header("Ripe Protocol - Vault Configurations", block_number)

            print("\nDetailed configuration for all vaults registered in VaultBook.\n")

            # Table of Contents
            print_table_of_contents()

            # VaultBook overview
            print_vault_book_overview()

            # All vault configs
            print_all_vaults()

            # Footer
            print_report_footer(block_number)

        print(f"Done! Output saved to {output_file}", file=sys.stderr)


if __name__ == "__main__":
    main()
