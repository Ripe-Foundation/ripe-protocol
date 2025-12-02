#!/usr/bin/env python3
"""
Output Deployments Script for Ripe Protocol

Fetches and displays all contract addresses from Ripe Protocol
on Base mainnet, formatted as markdown tables.

This is the canonical source for all live contract addresses.

Usage:
    python scripts/params/deployments.py
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
    GREEN_TOKEN_ID,
    SAVINGS_GREEN_ID,
    RIPE_TOKEN_ID,
    LEDGER_ID,
    MISSION_CONTROL_ID,
    SWITCHBOARD_ID,
    PRICE_DESK_ID,
    VAULT_BOOK_ID,
    AUCTION_HOUSE_ID,
    AUCTION_HOUSE_NFT_ID,
    BOARDROOM_ID,
    BOND_ROOM_ID,
    CREDIT_ENGINE_ID,
    ENDAOMENT_ID,
    HUMAN_RESOURCES_ID,
    LOOTBOX_ID,
    TELLER_ID,
    DELEVERAGE_ID,
    CREDIT_REDEEM_ID,
    TELLER_UTILS_ID,
    ENDAOMENT_FUNDS_ID,
    ENDAOMENT_PSM_ID,
    setup_boa_etherscan,
    boa_fork_context,
    print_report_header,
    print_report_footer,
    output_to_file,
)

# ============================================================================
# Global state
# ============================================================================


class DeploymentState:
    """Holds all contract addresses."""

    def __init__(self):
        self.hq = None
        self.core_addresses = {}
        self.switchboard_addresses = {}
        self.price_desk_addresses = {}
        self.vault_book_addresses = {}
        self.derived_addresses = {}
        self.token_addresses = {}


state = DeploymentState()


# ============================================================================
# Contract Loading
# ============================================================================


def load_core_addresses(hq):
    """Load all core contract addresses from RipeHQ registry."""
    print("  Loading core addresses from RipeHQ...", file=sys.stderr)
    addresses = {}

    # Map registry IDs to names
    id_to_name = {
        GREEN_TOKEN_ID: "GREEN",
        SAVINGS_GREEN_ID: "SavingsGreen",
        RIPE_TOKEN_ID: "RIPE",
        LEDGER_ID: "Ledger",
        MISSION_CONTROL_ID: "MissionControl",
        SWITCHBOARD_ID: "Switchboard",
        PRICE_DESK_ID: "PriceDesk",
        VAULT_BOOK_ID: "VaultBook",
        AUCTION_HOUSE_ID: "AuctionHouse",
        AUCTION_HOUSE_NFT_ID: "AuctionHouseNFT",
        BOARDROOM_ID: "Boardroom",
        BOND_ROOM_ID: "BondRoom",
        CREDIT_ENGINE_ID: "CreditEngine",
        ENDAOMENT_ID: "Endaoment",
        HUMAN_RESOURCES_ID: "HumanResources",
        LOOTBOX_ID: "Lootbox",
        TELLER_ID: "Teller",
        DELEVERAGE_ID: "Deleverage",
        CREDIT_REDEEM_ID: "CreditRedeem",
        TELLER_UTILS_ID: "TellerUtils",
        ENDAOMENT_FUNDS_ID: "EndaomentFunds",
        ENDAOMENT_PSM_ID: "EndaomentPSM",
    }

    num_addrs = hq.numAddrs()
    for i in range(1, num_addrs):
        time.sleep(RPC_DELAY)
        addr_info = hq.addrInfo(i)
        addr = str(addr_info.addr)
        if addr != ZERO_ADDRESS:
            name = id_to_name.get(i, addr_info.description)
            addresses[i] = {
                "name": name,
                "description": addr_info.description,
                "address": addr,
            }

    return addresses


def load_switchboard_addresses(sb_addr):
    """Load all switchboard config addresses."""
    print("  Loading Switchboard addresses...", file=sys.stderr)
    time.sleep(RPC_DELAY)
    sb = boa.from_etherscan(sb_addr, name="Switchboard")
    addresses = {}

    num_addrs = sb.numAddrs()
    for i in range(1, num_addrs):
        time.sleep(RPC_DELAY)
        addr_info = sb.addrInfo(i)
        addr = str(addr_info.addr)
        if addr != ZERO_ADDRESS:
            addresses[i] = {
                "description": addr_info.description,
                "address": addr,
            }

    return addresses


def load_price_desk_addresses(pd_addr):
    """Load all price source addresses from PriceDesk."""
    print("  Loading PriceDesk addresses...", file=sys.stderr)
    time.sleep(RPC_DELAY)
    pd = boa.from_etherscan(pd_addr, name="PriceDesk")
    addresses = {}

    num_addrs = pd.numAddrs()
    for i in range(1, num_addrs):
        time.sleep(RPC_DELAY)
        addr_info = pd.addrInfo(i)
        addr = str(addr_info.addr)
        if addr != ZERO_ADDRESS:
            addresses[i] = {
                "description": addr_info.description,
                "address": addr,
            }

    return addresses


def load_vault_book_addresses(vb_addr):
    """Load all vault addresses from VaultBook."""
    print("  Loading VaultBook addresses...", file=sys.stderr)
    time.sleep(RPC_DELAY)
    vb = boa.from_etherscan(vb_addr, name="VaultBook")
    addresses = {}

    num_addrs = vb.numAddrs()
    for i in range(1, num_addrs):
        time.sleep(RPC_DELAY)
        addr_info = vb.addrInfo(i)
        addr = str(addr_info.addr)
        if addr != ZERO_ADDRESS:
            addresses[i] = {
                "description": addr_info.description,
                "address": addr,
            }

    return addresses


def load_derived_addresses(hq, core_addresses):
    """Load derived contract addresses (from sub-contracts)."""
    print("  Loading derived addresses...", file=sys.stderr)
    derived = {}

    # BondBooster from BondRoom
    bond_room_addr = core_addresses.get(BOND_ROOM_ID, {}).get("address")
    if bond_room_addr and bond_room_addr != ZERO_ADDRESS:
        time.sleep(RPC_DELAY)
        bond_room = boa.from_etherscan(bond_room_addr, name="BondRoom")
        bb_addr = str(bond_room.bondBooster())
        if bb_addr != ZERO_ADDRESS:
            derived["BondBooster"] = {
                "source": "BondRoom.bondBooster()",
                "address": bb_addr,
            }

    # Contributor Blueprint from MissionControl.hrConfig()
    mc_addr = core_addresses.get(MISSION_CONTROL_ID, {}).get("address")
    if mc_addr and mc_addr != ZERO_ADDRESS:
        time.sleep(RPC_DELAY)
        mc = boa.from_etherscan(mc_addr, name="MissionControl")
        hr_config = mc.hrConfig()
        contrib_template = str(hr_config[0])  # contribTemplate is first field
        if contrib_template != ZERO_ADDRESS:
            derived["ContributorBlueprint"] = {
                "source": "MissionControl.hrConfig().contribTemplate",
                "address": contrib_template,
            }

    # GREEN Pool from CurvePrices (find in PriceDesk)
    pd_addr = core_addresses.get(PRICE_DESK_ID, {}).get("address")
    if pd_addr and pd_addr != ZERO_ADDRESS:
        time.sleep(RPC_DELAY)
        pd = boa.from_etherscan(pd_addr, name="PriceDesk")
        num_sources = pd.numAddrs()
        for i in range(1, num_sources):
            time.sleep(RPC_DELAY)
            source_addr = str(pd.getAddr(i))
            if source_addr == ZERO_ADDRESS:
                continue
            source = boa.from_etherscan(source_addr, name=f"PriceSource_{i}")
            if hasattr(source, 'greenRefPoolConfig'):
                config = source.greenRefPoolConfig()
                pool_addr = str(config[0])
                if pool_addr != ZERO_ADDRESS:
                    derived["GREENPool"] = {
                        "source": "CurvePrices.greenRefPoolConfig()",
                        "address": pool_addr,
                    }
                break

    return derived


def initialize_deployments():
    """Load all contract addresses from RIPE_HQ."""
    print("Loading contract addresses...", file=sys.stderr)

    # Load HQ first
    state.hq = boa.from_etherscan(RIPE_HQ, name="RipeHQ")

    # Load core addresses
    state.core_addresses = load_core_addresses(state.hq)

    # Load token addresses (subset of core)
    state.token_addresses = {
        "GREEN": state.core_addresses.get(GREEN_TOKEN_ID, {}).get("address"),
        "SavingsGreen": state.core_addresses.get(SAVINGS_GREEN_ID, {}).get("address"),
        "RIPE": state.core_addresses.get(RIPE_TOKEN_ID, {}).get("address"),
    }

    # Load sub-registry addresses
    sb_addr = state.core_addresses.get(SWITCHBOARD_ID, {}).get("address")
    if sb_addr and sb_addr != ZERO_ADDRESS:
        state.switchboard_addresses = load_switchboard_addresses(sb_addr)

    pd_addr = state.core_addresses.get(PRICE_DESK_ID, {}).get("address")
    if pd_addr and pd_addr != ZERO_ADDRESS:
        state.price_desk_addresses = load_price_desk_addresses(pd_addr)

    vb_addr = state.core_addresses.get(VAULT_BOOK_ID, {}).get("address")
    if vb_addr and vb_addr != ZERO_ADDRESS:
        state.vault_book_addresses = load_vault_book_addresses(vb_addr)

    # Load derived addresses
    state.derived_addresses = load_derived_addresses(state.hq, state.core_addresses)

    print("  All addresses loaded successfully.\n", file=sys.stderr)


# ============================================================================
# Output Functions
# ============================================================================


def print_table_of_contents():
    """Print a clickable table of contents."""
    print("""
## Table of Contents

1. [Core Registry (RipeHQ)](#core-registry)
2. [Core Contracts](#core-contracts)
3. [Switchboard Registry](#switchboard-registry)
4. [PriceDesk Registry](#price-desk-registry)
5. [VaultBook Registry](#vault-book-registry)
6. [Derived Contracts](#derived-contracts)
7. [Token Contracts](#token-contracts)
""")


def print_all_addresses():
    """Print all contract addresses."""

    # RipeHQ
    print("\n<a id=\"core-registry\"></a>")
    print("## Core Registry")
    print("\n| Contract | Address |")
    print("| --- | --- |")
    print(f"| RipeHQ | `{RIPE_HQ}` |")

    # Core Contracts
    print("\n<a id=\"core-contracts\"></a>")
    print("## Core Contracts (from RipeHQ)")
    print("\n| ID | Contract | Description | Address |")
    print("| --- | --- | --- | --- |")
    for reg_id in sorted(state.core_addresses.keys()):
        info = state.core_addresses[reg_id]
        print(f"| {reg_id} | {info['name']} | {info['description']} | `{info['address']}` |")

    # Switchboard Registry
    if state.switchboard_addresses:
        print("\n<a id=\"switchboard-registry\"></a>")
        print("## Switchboard Registry")
        print("\n| ID | Description | Address |")
        print("| --- | --- | --- |")
        for reg_id in sorted(state.switchboard_addresses.keys()):
            info = state.switchboard_addresses[reg_id]
            print(f"| {reg_id} | {info['description']} | `{info['address']}` |")

    # PriceDesk Registry
    if state.price_desk_addresses:
        print("\n<a id=\"price-desk-registry\"></a>")
        print("## PriceDesk Registry (Oracle Sources)")
        print("\n| ID | Description | Address |")
        print("| --- | --- | --- |")
        for reg_id in sorted(state.price_desk_addresses.keys()):
            info = state.price_desk_addresses[reg_id]
            print(f"| {reg_id} | {info['description']} | `{info['address']}` |")

    # VaultBook Registry
    if state.vault_book_addresses:
        print("\n<a id=\"vault-book-registry\"></a>")
        print("## VaultBook Registry")
        print("\n| ID | Description | Address |")
        print("| --- | --- | --- |")
        for reg_id in sorted(state.vault_book_addresses.keys()):
            info = state.vault_book_addresses[reg_id]
            print(f"| {reg_id} | {info['description']} | `{info['address']}` |")

    # Derived Contracts
    if state.derived_addresses:
        print("\n<a id=\"derived-contracts\"></a>")
        print("## Derived Contracts")
        print("\n| Contract | Source | Address |")
        print("| --- | --- | --- |")
        for name, info in state.derived_addresses.items():
            print(f"| {name} | {info['source']} | `{info['address']}` |")

    # Token Contracts
    print("\n<a id=\"token-contracts\"></a>")
    print("## Token Contracts")
    print("\n| Token | Address |")
    print("| --- | --- |")
    for name, addr in state.token_addresses.items():
        if addr and addr != ZERO_ADDRESS:
            print(f"| {name} | `{addr}` |")


# ============================================================================
# Main Entry Point
# ============================================================================


def main():
    """Main entry point."""
    # Output file path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, "deployments_output.md")

    print("Connecting to Base mainnet via Alchemy...", file=sys.stderr)

    # Set etherscan API
    setup_boa_etherscan()

    # Fork at latest block
    with boa_fork_context() as block_number:
        print(f"Connected. Block: {block_number}\n", file=sys.stderr)

        # Load all contract addresses
        initialize_deployments()

        print(f"Writing output to {output_file}...", file=sys.stderr)

        # Write report to file
        with output_to_file(output_file):
            # Header
            print_report_header("Ripe Protocol Deployments", block_number)

            print("\nComplete list of all live contract addresses in the Ripe Protocol.\n")

            # Table of Contents
            print_table_of_contents()

            # All addresses
            print_all_addresses()

            # Footer
            print_report_footer(block_number)

        print(f"Done! Output saved to {output_file}", file=sys.stderr)


if __name__ == "__main__":
    main()
