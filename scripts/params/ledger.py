#!/usr/bin/env python3
"""
Output Live Protocol Data Script for Ripe Protocol

Fetches and displays all live protocol data from Ledger.vy on Base mainnet,
formatted as markdown tables.

This is runtime/production data that is NOT configurable params, but rather
live state that changes during protocol operation.

Includes:
- Debt Statistics
- RIPE Rewards Pool
- Global Deposit Points
- Global Borrow Points
- Bond/Epoch Data
- Liquidation Statistics
- Endaoment Pool Debt
- HR Overview
- Contributors (detailed)

Usage:
    python scripts/params/ledger.py
"""

import os
import sys
import time
from datetime import datetime, timezone

import boa

# Import shared utilities
from params_utils import (
    RIPE_HQ,
    RPC_DELAY,
    ZERO_ADDRESS,
    LEDGER_ID,
    PRICE_DESK_ID,
    format_address,
    format_percent,
    format_wei,
    format_blocks_to_time,
    format_blocks_ago,
    format_token_amount,
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


class LedgerState:
    """Holds loaded contracts and data."""

    def __init__(self):
        self.hq = None
        self.ledger = None
        self.pd = None
        self.green_pool_addr = None
        self.contributors = {}  # index -> {addr, contract}
        self.block_number = 0


state = LedgerState()


# ============================================================================
# Contract Loading
# ============================================================================


def initialize_ledger():
    """Load Ledger and related contracts."""
    print("Loading contracts...", file=sys.stderr)

    # Load HQ
    state.hq = boa.from_etherscan(RIPE_HQ, name="RipeHQ")
    time.sleep(RPC_DELAY)

    # Load Ledger
    print("  Loading Ledger...", file=sys.stderr)
    state.ledger = boa.from_etherscan(state.hq.getAddr(LEDGER_ID), name="Ledger")
    time.sleep(RPC_DELAY)

    # Load PriceDesk to find GREEN Pool
    print("  Loading PriceDesk...", file=sys.stderr)
    state.pd = boa.from_etherscan(state.hq.getAddr(PRICE_DESK_ID), name="PriceDesk")
    time.sleep(RPC_DELAY)

    # Find GREEN Pool from CurvePrices
    print("  Looking for GREEN Pool...", file=sys.stderr)
    num_sources = state.pd.numAddrs()
    for i in range(1, num_sources):
        time.sleep(RPC_DELAY)
        source_addr = str(state.pd.getAddr(i))
        if source_addr == ZERO_ADDRESS:
            continue
        source = boa.from_etherscan(source_addr, name=f"PriceSource_{i}")
        if hasattr(source, 'greenRefPoolConfig'):
            config = source.greenRefPoolConfig()
            state.green_pool_addr = str(config[0])
            break

    # Load contributors
    print("  Loading contributors...", file=sys.stderr)
    num_contributors = state.ledger.numContributors()
    actual_count = num_contributors - 1 if num_contributors > 0 else 0
    print(f"    Found {actual_count} contributors...", file=sys.stderr)

    for i in range(1, num_contributors):
        time.sleep(RPC_DELAY)
        contrib_addr = str(state.ledger.contributors(i))
        if contrib_addr == ZERO_ADDRESS:
            continue

        time.sleep(RPC_DELAY)
        try:
            contrib_contract = boa.from_etherscan(contrib_addr, name=f"Contributor_{i}")
            state.contributors[i] = {
                "address": contrib_addr,
                "contract": contrib_contract,
            }
        except Exception as e:
            print(f"    Warning: Could not load contributor {i} at {contrib_addr}: {e}", file=sys.stderr)

    print("  All contracts loaded.\n", file=sys.stderr)


# ============================================================================
# Output Functions
# ============================================================================


def print_table_of_contents():
    """Print a clickable table of contents."""
    print("""
## Table of Contents

1. [Debt Statistics](#debt-statistics)
2. [RIPE Rewards Pool](#ripe-rewards-pool)
3. [Global Deposit Points](#global-deposit-points)
4. [Global Borrow Points](#global-borrow-points)
5. [Bond/Epoch Data](#bond-epoch-data)
6. [Liquidation Statistics](#liquidation-statistics)
7. [Endaoment Pool Debt](#endaoment-pool-debt)
8. [HR Overview](#hr-overview)
9. [Contributors](#contributors)
""")


def print_debt_statistics():
    """Print debt statistics from Ledger."""
    ledger = state.ledger

    print("\n<a id=\"debt-statistics\"></a>")
    print("## Debt Statistics")

    total_debt = ledger.totalDebt()
    num_borrowers = ledger.numBorrowers()
    unrealized_yield = ledger.unrealizedYield()
    bad_debt = ledger.badDebt()

    rows = [
        ("totalDebt", format_token_amount(total_debt)),
        ("numBorrowers", num_borrowers - 1 if num_borrowers > 0 else 0),
        ("unrealizedYield", format_token_amount(unrealized_yield)),
        ("badDebt", format_token_amount(bad_debt)),
    ]
    print_table("Current Debt State", ["Parameter", "Value"], rows, level=3)


def print_ripe_rewards_pool():
    """Print RIPE rewards pool data."""
    ledger = state.ledger

    print("\n<a id=\"ripe-rewards-pool\"></a>")
    print("## RIPE Rewards Pool")

    ripe_rewards = ledger.ripeRewards()
    ripe_avail = ledger.ripeAvailForRewards()

    rows = [
        ("borrowers allocation", format_token_amount(ripe_rewards.borrowers, 18, "RIPE")),
        ("stakers allocation", format_token_amount(ripe_rewards.stakers, 18, "RIPE")),
        ("voters allocation", format_token_amount(ripe_rewards.voters, 18, "RIPE")),
        ("genDepositors allocation", format_token_amount(ripe_rewards.genDepositors, 18, "RIPE")),
        ("newRipeRewards", format_token_amount(ripe_rewards.newRipeRewards, 18, "RIPE")),
        ("lastUpdate (block)", format_blocks_ago(ripe_rewards.lastUpdate, state.block_number)),
        ("ripeAvailForRewards", format_token_amount(ripe_avail, 18, "RIPE")),
    ]
    print_table("Reward Allocations", ["Parameter", "Value"], rows, level=3)


def print_global_deposit_points():
    """Print global deposit points data."""
    ledger = state.ledger

    print("\n<a id=\"global-deposit-points\"></a>")
    print("## Global Deposit Points")

    # Note: lastUsdValue is pre-normalized (divided by 10^18 in contract to prevent overflow)
    global_points = ledger.globalDepositPoints()

    rows = [
        ("lastUsdValue (normalized)", f"{global_points.lastUsdValue:,}"),
        ("ripeStakerPoints", f"{global_points.ripeStakerPoints:,}"),
        ("ripeVotePoints", f"{global_points.ripeVotePoints:,}"),
        ("ripeGenPoints", f"{global_points.ripeGenPoints:,}"),
        ("lastUpdate", format_blocks_ago(global_points.lastUpdate, state.block_number)),
    ]
    print_table("Deposit Points", ["Parameter", "Value"], rows, level=3)

    print("\n*Note: lastUsdValue is pre-normalized (divided by 10^18) in contract to prevent overflow*")


def print_global_borrow_points():
    """Print global borrow points data."""
    ledger = state.ledger

    print("\n<a id=\"global-borrow-points\"></a>")
    print("## Global Borrow Points")

    # Note: lastPrincipal is pre-normalized (divided by 10^18 in contract to prevent overflow)
    borrow_points = ledger.globalBorrowPoints()

    rows = [
        ("lastPrincipal (normalized)", f"{borrow_points.lastPrincipal:,}"),
        ("points", f"{borrow_points.points:,}"),
        ("lastUpdate", format_blocks_ago(borrow_points.lastUpdate, state.block_number)),
    ]
    print_table("Borrow Points", ["Parameter", "Value"], rows, level=3)

    print("\n*Note: lastPrincipal is pre-normalized (divided by 10^18) in contract to prevent overflow*")


def print_bond_epoch_data():
    """Print bond/epoch data."""
    ledger = state.ledger

    print("\n<a id=\"bond-epoch-data\"></a>")
    print("## Bond/Epoch Data")

    epoch_start = ledger.epochStart()
    epoch_end = ledger.epochEnd()
    bad_debt = ledger.badDebt()
    ripe_paid_bad_debt = ledger.ripePaidOutForBadDebt()
    payment_avail = ledger.paymentAmountAvailInEpoch()
    ripe_avail_bonds = ledger.ripeAvailForBonds()

    # Calculate epoch status
    current_block = state.block_number
    epoch_status = "Not Started"
    if epoch_start > 0:
        if current_block < epoch_start:
            blocks_until = epoch_start - current_block
            epoch_status = f"Starts in {format_blocks_to_time(blocks_until)}"
        elif current_block <= epoch_end:
            blocks_remaining = epoch_end - current_block
            epoch_status = f"Active ({format_blocks_to_time(blocks_remaining)} remaining)"
        else:
            blocks_since = current_block - epoch_end
            epoch_status = f"Ended {format_blocks_to_time(blocks_since)} ago"

    rows = [
        ("epochStart (block)", epoch_start),
        ("epochEnd (block)", epoch_end),
        ("**Epoch Status**", f"**{epoch_status}**"),
        ("badDebt", format_token_amount(bad_debt)),
        ("ripePaidOutForBadDebt (cumulative)", format_token_amount(ripe_paid_bad_debt, 18, "RIPE")),
        ("paymentAmountAvailInEpoch", format_token_amount(payment_avail)),
        ("ripeAvailForBonds", format_token_amount(ripe_avail_bonds, 18, "RIPE")),
    ]
    print_table("Epoch & Bond State", ["Parameter", "Value"], rows, level=3)


def print_liquidation_statistics():
    """Print liquidation statistics."""
    ledger = state.ledger

    print("\n<a id=\"liquidation-statistics\"></a>")
    print("## Liquidation Statistics")

    num_liq_users = ledger.numFungLiqUsers()
    actual_count = num_liq_users - 1 if num_liq_users > 0 else 0

    rows = [
        ("numFungLiqUsers (users in liquidation)", actual_count),
    ]
    print_table("Active Liquidations", ["Parameter", "Value"], rows, level=3)

    # List liquidated users if any
    if actual_count > 0:
        print("\n### Users in Liquidation")
        print("\n| Index | User Address |")
        print("| --- | --- |")
        for i in range(1, num_liq_users):
            time.sleep(RPC_DELAY)
            liq_user = str(ledger.fungLiqUsers(i))
            if liq_user != ZERO_ADDRESS:
                print(f"| {i} | `{liq_user}` |")


def print_endaoment_pool_debt():
    """Print Endaoment pool debt."""
    ledger = state.ledger

    print("\n<a id=\"endaoment-pool-debt\"></a>")
    print("## Endaoment Pool Debt")

    if state.green_pool_addr:
        green_pool_debt = ledger.greenPoolDebt(state.green_pool_addr)
        rows = [
            ("GREEN Pool Address", f"`{state.green_pool_addr}`"),
            ("greenPoolDebt", format_token_amount(green_pool_debt)),
        ]
        print_table("Pool Debt Tracking", ["Parameter", "Value"], rows, level=3)
    else:
        print("\n*GREEN Pool not found - no pool debt to display*")


def print_hr_overview():
    """Print HR overview."""
    ledger = state.ledger

    print("\n<a id=\"hr-overview\"></a>")
    print("## HR Overview")

    ripe_avail_hr = ledger.ripeAvailForHr()
    num_contributors = ledger.numContributors()
    actual_count = num_contributors - 1 if num_contributors > 0 else 0

    rows = [
        ("ripeAvailForHr", format_token_amount(ripe_avail_hr, 18, "RIPE")),
        ("numContributors", actual_count),
    ]
    print_table("Human Resources", ["Parameter", "Value"], rows, level=3)


def format_timestamp(timestamp: int, current_timestamp: int) -> str:
    """Format a Unix timestamp with relative time."""
    if timestamp == 0:
        return "0 (never)"

    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    formatted = dt.strftime('%Y-%m-%d %H:%M UTC')

    diff = current_timestamp - timestamp
    if diff < 0:
        # Future timestamp
        diff = -diff
        if diff < 60:
            rel = f"in {diff}s"
        elif diff < 3600:
            rel = f"in {diff/60:.1f}m"
        elif diff < 86400:
            rel = f"in {diff/3600:.1f}h"
        else:
            rel = f"in {diff/86400:.1f}d"
    else:
        # Past timestamp
        if diff < 60:
            rel = f"{diff}s ago"
        elif diff < 3600:
            rel = f"{diff/60:.1f}m ago"
        elif diff < 86400:
            rel = f"{diff/3600:.1f}h ago"
        else:
            rel = f"{diff/86400:.1f}d ago"

    return f"{formatted} ({rel})"


def print_contributors():
    """Print detailed contributor data."""
    print("\n<a id=\"contributors\"></a>")
    print("## Contributors")

    if not state.contributors:
        print("\n*No contributors registered*")
        return

    print(f"\n*{len(state.contributors)} contributor(s) found*")

    # Get current timestamp for relative time calculations
    current_timestamp = int(time.time())

    for i, contrib_info in sorted(state.contributors.items()):
        contrib = contrib_info["contract"]
        addr = contrib_info["address"]

        print(f"\n### Contributor {i}: `{addr}`")

        # Basic terms
        time.sleep(RPC_DELAY)
        compensation = contrib.compensation()
        time.sleep(RPC_DELAY)
        total_claimed = contrib.totalClaimed()
        time.sleep(RPC_DELAY)
        claimable = contrib.getClaimable()
        time.sleep(RPC_DELAY)
        unvested = contrib.getUnvestedComp()

        # Timeline
        time.sleep(RPC_DELAY)
        start_time = contrib.startTime()
        time.sleep(RPC_DELAY)
        cliff_time = contrib.cliffTime()
        time.sleep(RPC_DELAY)
        unlock_time = contrib.unlockTime()
        time.sleep(RPC_DELAY)
        end_time = contrib.endTime()

        # Admin
        time.sleep(RPC_DELAY)
        owner = str(contrib.owner())
        time.sleep(RPC_DELAY)
        manager = str(contrib.manager())
        time.sleep(RPC_DELAY)
        is_frozen = contrib.isFrozen()

        # Config
        time.sleep(RPC_DELAY)
        deposit_lock_duration = contrib.depositLockDuration()
        time.sleep(RPC_DELAY)
        key_action_delay = contrib.keyActionDelay()

        # Pending operations
        time.sleep(RPC_DELAY)
        has_pending_owner = contrib.hasPendingOwnerChange()
        time.sleep(RPC_DELAY)
        has_pending_transfer = contrib.hasPendingRipeTransfer()

        # Compensation & Vesting
        rows = [
            ("compensation (total)", format_token_amount(compensation, 18, "RIPE")),
            ("totalClaimed", format_token_amount(total_claimed, 18, "RIPE")),
            ("**claimable (now)**", f"**{format_token_amount(claimable, 18, 'RIPE')}**"),
            ("unvested", format_token_amount(unvested, 18, "RIPE")),
        ]
        print_table("Compensation", ["Parameter", "Value"], rows, level=4)

        # Calculate vesting progress
        if compensation > 0:
            vested_pct = (compensation - unvested) / compensation * 100
            claimed_pct = total_claimed / compensation * 100
            print(f"\n**Vesting Progress:** {vested_pct:.2f}% vested, {claimed_pct:.2f}% claimed")

        # Timeline
        rows = [
            ("startTime", format_timestamp(start_time, current_timestamp)),
            ("cliffTime", format_timestamp(cliff_time, current_timestamp)),
            ("unlockTime", format_timestamp(unlock_time, current_timestamp)),
            ("endTime", format_timestamp(end_time, current_timestamp)),
        ]
        print_table("Vesting Timeline", ["Parameter", "Value"], rows, level=4)

        # Admin
        rows = [
            ("owner", format_address(owner)),
            ("manager", format_address(manager)),
            ("isFrozen", is_frozen),
        ]
        print_table("Admin", ["Parameter", "Value"], rows, level=4)

        # Config
        rows = [
            ("depositLockDuration", format_blocks_to_time(deposit_lock_duration)),
            ("keyActionDelay", format_blocks_to_time(key_action_delay)),
        ]
        print_table("Configuration", ["Parameter", "Value"], rows, level=4)

        # Pending operations
        if has_pending_owner or has_pending_transfer:
            pending_rows = []
            if has_pending_owner:
                pending_rows.append(("Pending Owner Change", "Yes"))
            if has_pending_transfer:
                pending_rows.append(("Pending RIPE Transfer", "Yes"))
            print_table("Pending Operations", ["Operation", "Status"], pending_rows, level=4)
        else:
            print("\n*No pending operations*")

        print("\n---")


# ============================================================================
# Main Entry Point
# ============================================================================


def main():
    """Main entry point."""
    # Output file path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, "ledger_output.md")

    print("Connecting to Base mainnet via Alchemy...", file=sys.stderr)

    # Set etherscan API
    setup_boa_etherscan()

    # Fork at latest block
    with boa_fork_context() as block_number:
        print(f"Connected. Block: {block_number}\n", file=sys.stderr)

        # Store block number in state for relative time calculations
        state.block_number = block_number

        # Load all contracts
        initialize_ledger()

        print(f"Writing output to {output_file}...", file=sys.stderr)

        # Write report to file
        with output_to_file(output_file):
            # Header
            print_report_header("Ripe Protocol - Live Protocol Data", block_number)

            print("\nLive protocol state from Ledger.vy - runtime data that changes during protocol operation.")
            print("This is NOT configurable params, but rather live state.\n")

            # Table of Contents
            print_table_of_contents()

            # Debt Statistics
            print_debt_statistics()

            # RIPE Rewards Pool
            print_ripe_rewards_pool()

            # Global Deposit Points
            print_global_deposit_points()

            # Global Borrow Points
            print_global_borrow_points()

            # Bond/Epoch Data
            print_bond_epoch_data()

            # Liquidation Statistics
            print_liquidation_statistics()

            # Endaoment Pool Debt
            print_endaoment_pool_debt()

            # HR Overview
            print_hr_overview()

            # Contributors
            print_contributors()

            # Footer
            print_report_footer(block_number)

        print(f"Done! Output saved to {output_file}", file=sys.stderr)


if __name__ == "__main__":
    main()
