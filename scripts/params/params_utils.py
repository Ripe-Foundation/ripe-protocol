#!/usr/bin/env python3
"""
Shared utilities for Ripe Protocol params scripts.

This module provides common constants, formatting functions, address resolution,
and utility functions used across deployments.py, assets.py, prices.py,
vaults.py, and general.py.
"""

import os
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Callable

import boa

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.BluePrint import CORE_TOKENS, YIELD_TOKENS, ADDYS
from tests.constants import ZERO_ADDRESS

# ============================================================================
# CONFIGURATION CONSTANTS
# ============================================================================

RIPE_HQ = "0x6162df1b329E157479F8f1407E888260E0EC3d2b"
RPC_URL = f"https://base-mainnet.g.alchemy.com/v2/{os.environ.get('WEB3_ALCHEMY_API_KEY')}"
RPC_DELAY = 0.15  # seconds between RPC calls

# Formatting constants
HUNDRED_PERCENT = 100_00  # 100.00%
DECIMALS_18 = 10**18
DECIMALS_6 = 10**6

# Registry IDs (matching contracts/modules/Addys.vy)
GREEN_TOKEN_ID = 1
SAVINGS_GREEN_ID = 2
RIPE_TOKEN_ID = 3
LEDGER_ID = 4
MISSION_CONTROL_ID = 5
SWITCHBOARD_ID = 6
PRICE_DESK_ID = 7
VAULT_BOOK_ID = 8
AUCTION_HOUSE_ID = 9
AUCTION_HOUSE_NFT_ID = 10
BOARDROOM_ID = 11
BOND_ROOM_ID = 12
CREDIT_ENGINE_ID = 13
ENDAOMENT_ID = 14
HUMAN_RESOURCES_ID = 15
LOOTBOX_ID = 16
TELLER_ID = 17
DELEVERAGE_ID = 18
CREDIT_REDEEM_ID = 19
TELLER_UTILS_ID = 20
ENDAOMENT_FUNDS_ID = 21
ENDAOMENT_PSM_ID = 22

# VaultBook IDs for derived contracts
STABILITY_POOL_VB_ID = 1
RIPE_GOV_VAULT_VB_ID = 2

# Protocol ID mapping for BlueChipYield price sources
PROTOCOL_NAMES = {
    1: "Morpho",
    2: "Euler",
    4: "Moonwell",
    8: "Fluid",
    16: "Fluid",
    32: "AaveV3",
    64: "CompoundV3",
}

# Build KNOWN_TOKENS from BluePrint (invert address -> symbol mapping)
KNOWN_TOKENS = {}
for name, addr in CORE_TOKENS.get("base", {}).items():
    KNOWN_TOKENS[addr.lower()] = name
for name, addr in YIELD_TOKENS.get("base", {}).items():
    KNOWN_TOKENS[addr.lower()] = name
for name, addr in ADDYS.get("base", {}).items():
    KNOWN_TOKENS[addr.lower()] = name

# ============================================================================
# ADDRESS RESOLUTION (with shared cache)
# ============================================================================

_token_symbol_cache = {}


def get_token_name(
    address: str,
    known_addresses_fn: Callable[[], dict] = None,
    try_fetch: bool = True,
) -> str:
    """Resolve address to token symbol or return full address.

    Args:
        address: The address to resolve
        known_addresses_fn: Optional callback to get protocol-specific known addresses
        try_fetch: Whether to try fetching symbol from contract if not found
    """
    if address == ZERO_ADDRESS:
        return "None"

    addr_lower = address.lower()

    # Check cache first
    if addr_lower in _token_symbol_cache:
        return _token_symbol_cache[addr_lower]

    # Check known external tokens (from BluePrint)
    if addr_lower in KNOWN_TOKENS:
        _token_symbol_cache[addr_lower] = KNOWN_TOKENS[addr_lower]
        return KNOWN_TOKENS[addr_lower]

    # Check dynamically loaded protocol addresses
    if known_addresses_fn:
        known_addresses = known_addresses_fn()
        if addr_lower in known_addresses:
            _token_symbol_cache[addr_lower] = known_addresses[addr_lower]
            return known_addresses[addr_lower]

    # Try to fetch symbol from contract
    if try_fetch:
        try:
            time.sleep(RPC_DELAY)
            token_contract = boa.from_etherscan(address, name=f"Token_{address[:8]}")
            symbol = token_contract.symbol()
            if symbol:
                _token_symbol_cache[addr_lower] = symbol
                return symbol
        except Exception:
            pass

    # Return full address if no name found
    _token_symbol_cache[addr_lower] = address
    return address


def get_token_decimals(address: str) -> int:
    """Get token decimals, with caching and fallback to 18."""
    try:
        token_contract = boa.from_etherscan(address, name=f"Token_{address[:8]}")
        return token_contract.decimals()
    except Exception:
        return 18


def format_address(
    address: str,
    known_addresses_fn: Callable[[], dict] = None,
    try_fetch: bool = False,
) -> str:
    """Format address with resolved name and full address.

    Args:
        address: The address to format
        known_addresses_fn: Optional callback to get protocol-specific known addresses
        try_fetch: Whether to try fetching symbol from contract if not found
    """
    if address == ZERO_ADDRESS:
        return "None"
    name = get_token_name(address, known_addresses_fn=known_addresses_fn, try_fetch=try_fetch)
    # Check if we got a real name (not just the address)
    if name and not name.startswith("0x"):
        return f"{name} (`{address}`)"
    return f"`{address}`"


# ============================================================================
# FORMATTING HELPERS
# ============================================================================


def format_percent(value: int, base: int = HUNDRED_PERCENT) -> str:
    """Format a percentage value."""
    return f"{value / base * 100:.2f}%"


def format_wei(value: int, decimals: int = 18) -> str:
    """Format a wei value with appropriate decimals."""
    return f"{value / 10**decimals:,.6f}"


def format_blocks_to_time(blocks: int, block_time: float = 2.0) -> str:
    """Convert blocks to approximate time (Base ~2s blocks)."""
    seconds = blocks * block_time
    if seconds < 60:
        return f"{blocks} blocks (~{seconds:.0f}s)"
    elif seconds < 3600:
        return f"{blocks} blocks (~{seconds/60:.1f}m)"
    elif seconds < 86400:
        return f"{blocks} blocks (~{seconds/3600:.1f}h)"
    else:
        return f"{blocks} blocks (~{seconds/86400:.1f}d)"


def format_blocks_ago(last_block: int, current_block: int, block_time: float = 2.0) -> str:
    """Format a block number with relative time ago."""
    if last_block == 0:
        return "0 (never)"
    blocks_ago = current_block - last_block
    if blocks_ago < 0:
        return f"{last_block}"
    seconds_ago = blocks_ago * block_time
    if seconds_ago < 60:
        time_str = f"{seconds_ago:.0f}s ago"
    elif seconds_ago < 3600:
        time_str = f"{seconds_ago/60:.1f}m ago"
    elif seconds_ago < 86400:
        time_str = f"{seconds_ago/3600:.1f}h ago"
    else:
        time_str = f"{seconds_ago/86400:.1f}d ago"
    return f"{last_block} ({time_str})"


def format_token_amount(raw_value: int, decimals: int = 18, symbol: str = "GREEN") -> str:
    """Format token amount with human-readable units (K, M, B).

    Note: GREEN token has 18 decimals, USDC has 6 decimals.
    """
    amount = raw_value / (10**decimals)
    if amount >= 1_000_000_000_000:
        return f"Very High ({amount:.2e} {symbol})"
    elif amount >= 1_000_000_000:
        return f"{amount / 1_000_000_000:,.2f}B {symbol}"
    elif amount >= 1_000_000:
        return f"{amount / 1_000_000:,.2f}M {symbol}"
    elif amount >= 1_000:
        return f"{amount / 1_000:,.2f}K {symbol}"
    else:
        return f"{amount:,.2f} {symbol}"


def format_token_amount_precise(raw_value: int, decimals: int = 18, symbol: str = "") -> str:
    """Format token amount with full precision (all decimal places)."""
    amount = raw_value / (10**decimals)
    # Show up to `decimals` decimal places, but strip trailing zeros
    formatted = f"{amount:,.{decimals}f}".rstrip('0').rstrip('.')
    return f"{formatted} {symbol}" if symbol else formatted


# ============================================================================
# TABLE PRINTING
# ============================================================================


def print_table(title: str, headers: list, rows: list, anchor: str = None, level: int = 2):
    """Print a markdown table with optional anchor.

    Args:
        title: The table title
        headers: List of column headers
        rows: List of row data (each row is a list)
        anchor: Optional HTML anchor ID
        level: Header level (2 = ##, 3 = ###)
    """
    if anchor:
        print(f"\n<a id=\"{anchor}\"></a>")
    header_prefix = "#" * level
    print(f"\n{header_prefix} {title}")
    print(f"| {' | '.join(headers)} |")
    print(f"| {' | '.join(['---' for _ in headers])} |")
    for row in rows:
        print(f"| {' | '.join(str(cell) for cell in row)} |")


# ============================================================================
# BOA SETUP HELPERS
# ============================================================================


def setup_boa_etherscan():
    """Configure boa for Etherscan API access on Base mainnet."""
    boa.set_etherscan(
        api_key=os.environ["ETHERSCAN_API_KEY"],
        uri="https://api.etherscan.io/v2/api?chainid=8453"
    )


@contextmanager
def boa_fork_context(rpc_url: str = None):
    """Context manager for boa fork connection.

    Yields the block number for convenience.

    Usage:
        with boa_fork_context() as block_number:
            # do stuff with forked state
    """
    url = rpc_url or RPC_URL
    with boa.fork(url):
        block_number = boa.env.evm.patch.block_number
        yield block_number


# ============================================================================
# REPORT UTILITIES
# ============================================================================


def print_report_header(title: str, block_number: int):
    """Print standard report header with title, timestamp, and block info."""
    print("=" * 80)
    print(f"# {title}")
    print(f"\n**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"**Block:** {block_number}")
    print(f"**Network:** Base Mainnet")


def print_report_footer(block_number: int):
    """Print standard report footer."""
    print("\n" + "=" * 80)
    print("\n---")
    print(f"*Report generated at block {block_number} on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC*")


@contextmanager
def output_to_file(output_file: str):
    """Context manager to redirect stdout to a file.

    Usage:
        with output_to_file("output.md"):
            print("This goes to the file")
    """
    with open(output_file, "w") as f:
        old_stdout = sys.stdout
        sys.stdout = f
        try:
            yield f
        finally:
            sys.stdout = old_stdout


# ============================================================================
# MODULE PARAM HELPERS (LocalGov, AddressRegistry, TimeLock)
# ============================================================================


def print_local_gov_params(
    contract,
    known_addresses_fn: Callable[[], dict] = None,
    level: int = 3,
):
    """Print LocalGov module params for a contract.

    Shows governance, govChangeTimeLock, and pendingGov if applicable.

    Args:
        contract: The boa contract object
        known_addresses_fn: Optional callback to resolve addresses
        level: Header level for the table
    """
    if not hasattr(contract, 'governance'):
        return

    time.sleep(RPC_DELAY)
    governance = str(contract.governance())
    time.sleep(RPC_DELAY)
    gov_timelock = contract.govChangeTimeLock()

    gov_rows = [
        ("governance", format_address(governance, known_addresses_fn)),
        ("govChangeTimeLock", format_blocks_to_time(gov_timelock)),
    ]

    # Check for pending gov change
    if hasattr(contract, 'pendingGov'):
        time.sleep(RPC_DELAY)
        pending_gov = contract.pendingGov()
        pending_new_gov = str(pending_gov[0]) if pending_gov else ZERO_ADDRESS
        if pending_new_gov != ZERO_ADDRESS:
            gov_rows.append(("pendingGov.newGov", format_address(pending_new_gov, known_addresses_fn)))
            gov_rows.append(("pendingGov.initiatedBlock", pending_gov[1]))
            gov_rows.append(("pendingGov.confirmBlock", pending_gov[2]))
        else:
            gov_rows.append(("pendingGov", "None"))

    print_table("Governance Settings (LocalGov Module)", ["Parameter", "Value"], gov_rows, level=level)


def print_address_registry_params(
    contract,
    registry_name: str = "registry",
    level: int = 3,
):
    """Print AddressRegistry module params for a contract.

    Shows numAddrs and registryChangeTimeLock.

    Args:
        contract: The boa contract object
        registry_name: What to call the registry items (e.g., "departments", "vaults")
        level: Header level for the table
    """
    if not hasattr(contract, 'numAddrs'):
        return

    time.sleep(RPC_DELAY)
    num_addrs = contract.numAddrs()
    time.sleep(RPC_DELAY)
    registry_timelock = contract.registryChangeTimeLock()

    rows = [
        (f"numAddrs ({registry_name})", num_addrs - 1 if num_addrs > 0 else 0),
        ("registryChangeTimeLock", format_blocks_to_time(registry_timelock)),
    ]

    print_table("Registry Config (AddressRegistry Module)", ["Parameter", "Value"], rows, level=level)


def print_timelock_params(
    contract,
    level: int = 3,
):
    """Print TimeLock module params for a contract.

    Shows minActionTimeLock, maxActionTimeLock, actionTimeLock, and expiration.

    Args:
        contract: The boa contract object
        level: Header level for the table
    """
    if not hasattr(contract, 'minActionTimeLock'):
        return

    time.sleep(RPC_DELAY)
    min_timelock = contract.minActionTimeLock()
    time.sleep(RPC_DELAY)
    max_timelock = contract.maxActionTimeLock()
    time.sleep(RPC_DELAY)
    action_timelock = contract.actionTimeLock()
    time.sleep(RPC_DELAY)
    expiration = contract.expiration()

    rows = [
        ("minActionTimeLock", format_blocks_to_time(min_timelock)),
        ("maxActionTimeLock", format_blocks_to_time(max_timelock)),
        ("actionTimeLock", format_blocks_to_time(action_timelock)),
        ("expiration", format_blocks_to_time(expiration)),
    ]

    print_table("Timelock Settings (TimeLock Module)", ["Parameter", "Value"], rows, level=level)
