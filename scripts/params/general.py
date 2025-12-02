#!/usr/bin/env python3
"""
Output General Parameters Script for Ripe Protocol

Fetches and displays all general protocol configurations on Base mainnet,
formatted as markdown tables.

Includes:
- Executive Summary
- Token statistics
- MissionControl general configs
- RipeHQ registry
- Switchboard registry
- Endaoment contracts (Endaoment + PSM)
- Departments (all core protocol contracts)

Note: Live protocol data (debt, rewards, contributors) is in ledger.py

Usage:
    python scripts/params/general.py
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
    DECIMALS_6,
    GREEN_TOKEN_ID,
    SAVINGS_GREEN_ID,
    RIPE_TOKEN_ID,
    LEDGER_ID,
    MISSION_CONTROL_ID,
    SWITCHBOARD_ID,
    PRICE_DESK_ID,
    VAULT_BOOK_ID,
    AUCTION_HOUSE_ID,
    BOND_ROOM_ID,
    CREDIT_ENGINE_ID,
    ENDAOMENT_ID,
    ENDAOMENT_FUNDS_ID,
    HUMAN_RESOURCES_ID,
    LOOTBOX_ID,
    TELLER_ID,
    DELEVERAGE_ID,
    CREDIT_REDEEM_ID,
    ENDAOMENT_PSM_ID,
    STABILITY_POOL_VB_ID,
    RIPE_GOV_VAULT_VB_ID,
    format_address,
    format_percent,
    format_wei,
    format_blocks_to_time,
    format_token_amount,
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


class GeneralState:
    """Holds all loaded contracts."""

    def __init__(self):
        self.hq = None
        self.mc = None
        self.ledger = None
        self.sb = None
        self.vb = None
        self.pd = None
        self.green = None
        self.sgreen = None
        self.ripe = None
        self.ce = None
        self.auction_house = None
        self.teller = None
        self.deleverage = None
        self.credit_redeem = None
        self.endaoment = None
        self.hr = None
        self.lootbox = None
        self.bond_room = None
        self.bb = None
        self.psm = None
        self.endaoment_funds = None
        self.stab_pool = None
        self.ripe_gov = None
        self.green_pool_addr = None
        self.switchboards = {}  # reg_id -> {addr, description, contract}
        self.block_number = 0  # current block number


state = GeneralState()


# ============================================================================
# Contract Loading
# ============================================================================


def initialize_general():
    """Load all contracts needed for general params."""
    print("Loading contracts...", file=sys.stderr)

    # Load HQ
    state.hq = boa.from_etherscan(RIPE_HQ, name="RipeHQ")
    time.sleep(RPC_DELAY)

    # Load core contracts
    print("  Loading core contracts...", file=sys.stderr)
    state.mc = boa.from_etherscan(state.hq.getAddr(MISSION_CONTROL_ID), name="MissionControl")
    time.sleep(RPC_DELAY)
    state.ledger = boa.from_etherscan(state.hq.getAddr(LEDGER_ID), name="Ledger")
    time.sleep(RPC_DELAY)
    state.sb = boa.from_etherscan(state.hq.getAddr(SWITCHBOARD_ID), name="Switchboard")
    time.sleep(RPC_DELAY)
    state.vb = boa.from_etherscan(state.hq.getAddr(VAULT_BOOK_ID), name="VaultBook")
    time.sleep(RPC_DELAY)
    state.pd = boa.from_etherscan(state.hq.getAddr(PRICE_DESK_ID), name="PriceDesk")
    time.sleep(RPC_DELAY)

    # Load tokens
    print("  Loading token contracts...", file=sys.stderr)
    state.green = boa.from_etherscan(state.hq.getAddr(GREEN_TOKEN_ID), name="GreenToken")
    time.sleep(RPC_DELAY)
    state.sgreen = boa.from_etherscan(state.hq.getAddr(SAVINGS_GREEN_ID), name="SavingsGreen")
    time.sleep(RPC_DELAY)
    state.ripe = boa.from_etherscan(state.hq.getAddr(RIPE_TOKEN_ID), name="RipeToken")
    time.sleep(RPC_DELAY)

    # Load lending contracts
    print("  Loading lending contracts...", file=sys.stderr)
    state.ce = boa.from_etherscan(state.hq.getAddr(CREDIT_ENGINE_ID), name="CreditEngine")
    time.sleep(RPC_DELAY)
    state.auction_house = boa.from_etherscan(state.hq.getAddr(AUCTION_HOUSE_ID), name="AuctionHouse")
    time.sleep(RPC_DELAY)
    state.teller = boa.from_etherscan(state.hq.getAddr(TELLER_ID), name="Teller")
    time.sleep(RPC_DELAY)
    state.deleverage = boa.from_etherscan(state.hq.getAddr(DELEVERAGE_ID), name="Deleverage")
    time.sleep(RPC_DELAY)
    state.credit_redeem = boa.from_etherscan(state.hq.getAddr(CREDIT_REDEEM_ID), name="CreditRedeem")
    time.sleep(RPC_DELAY)

    # Load treasury/rewards contracts
    print("  Loading treasury contracts...", file=sys.stderr)
    state.endaoment = boa.from_etherscan(state.hq.getAddr(ENDAOMENT_ID), name="Endaoment")
    time.sleep(RPC_DELAY)
    state.hr = boa.from_etherscan(state.hq.getAddr(HUMAN_RESOURCES_ID), name="HumanResources")
    time.sleep(RPC_DELAY)
    state.lootbox = boa.from_etherscan(state.hq.getAddr(LOOTBOX_ID), name="Lootbox")
    time.sleep(RPC_DELAY)
    state.bond_room = boa.from_etherscan(state.hq.getAddr(BOND_ROOM_ID), name="BondRoom")
    time.sleep(RPC_DELAY)
    state.bb = boa.from_etherscan(state.bond_room.bondBooster(), name="BondBooster")
    time.sleep(RPC_DELAY)
    state.psm = boa.from_etherscan(state.hq.getAddr(ENDAOMENT_PSM_ID), name="EndaomentPSM")
    time.sleep(RPC_DELAY)
    state.endaoment_funds = boa.from_etherscan(state.hq.getAddr(ENDAOMENT_FUNDS_ID), name="EndaomentFunds")
    time.sleep(RPC_DELAY)

    # Load vaults from VaultBook
    print("  Loading vault contracts...", file=sys.stderr)
    state.stab_pool = boa.from_etherscan(state.vb.getAddr(STABILITY_POOL_VB_ID), name="StabilityPool")
    time.sleep(RPC_DELAY)
    state.ripe_gov = boa.from_etherscan(state.vb.getAddr(RIPE_GOV_VAULT_VB_ID), name="RipeGovVault")
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

    # Load individual switchboard configs
    print("  Loading individual switchboards...", file=sys.stderr)
    num_switchboards = state.sb.numAddrs()
    for i in range(1, num_switchboards):
        time.sleep(RPC_DELAY)
        addr_info = state.sb.addrInfo(i)
        addr = str(addr_info.addr)
        if addr == ZERO_ADDRESS:
            continue
        time.sleep(RPC_DELAY)
        sb_contract = boa.from_etherscan(addr, name=f"Switchboard_{i}")
        state.switchboards[i] = {
            "address": addr,
            "description": addr_info.description,
            "contract": sb_contract,
        }

    print("  All contracts loaded.\n", file=sys.stderr)


# ============================================================================
# Output Functions
# ============================================================================


def print_table_of_contents():
    """Print a clickable table of contents."""
    print("""
## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Token Statistics](#token-statistics)
3. [MissionControl Configuration](#mission-control)
   - [General Config](#general-config)
   - [Debt Config](#debt-config)
   - [Rewards Config](#rewards-config)
   - [Priority Lists](#priority-lists)
4. [RipeHQ Registry](#ripe-hq)
5. [Switchboard Registry](#switchboard)
   - [Individual Switchboard Configurations](#individual-switchboard-configurations)
6. [Endaoment Contracts](#endaoment)
7. [Departments](#departments)

*Note: Live protocol data (debt, rewards, points, contributors) is in `ledger_output.md`*
""")


def print_executive_summary():
    """Print executive summary with key protocol metrics."""
    print("\n<a id=\"executive-summary\"></a>")
    print("## Executive Summary\n")

    mc = state.mc
    ledger = state.ledger
    green = state.green
    sgreen = state.sgreen
    ripe = state.ripe

    # Key metrics
    gen_debt = mc.genDebtConfig()
    total_debt = ledger.totalDebt()
    global_limit = gen_debt[1]
    utilization = (total_debt / global_limit * 100) if global_limit > 0 else 0

    num_borrowers = ledger.numBorrowers()
    num_assets = mc.numAssets()
    bad_debt = ledger.badDebt()

    green_supply = green.totalSupply()
    ripe_supply = ripe.totalSupply()
    sgreen_supply = sgreen.totalSupply()
    sgreen_assets = sgreen.totalAssets()

    # Calculate savings rate
    savings_rate = 0
    if sgreen_supply > 0:
        exchange_rate = sgreen_assets / sgreen_supply
        savings_rate = (exchange_rate - 1) * 100

    print("| Metric | Value |")
    print("| --- | --- |")
    print(f"| **Total GREEN Supply** | {format_token_amount(green_supply)} |")
    print(f"| **Total Debt Outstanding** | {format_token_amount(total_debt)} |")
    print(f"| **Debt Utilization** | {utilization:.2f}% of {format_token_amount(global_limit)} limit |")
    print(f"| **Active Borrowers** | {num_borrowers - 1 if num_borrowers > 0 else 0} |")
    print(f"| **Registered Assets** | {num_assets - 1 if num_assets > 0 else 0} |")
    print(f"| **Bad Debt** | {format_token_amount(bad_debt)} |")
    print(f"| **RIPE Total Supply** | {format_token_amount(ripe_supply, 18, 'RIPE')} |")
    print(f"| **sGREEN Exchange Rate** | {sgreen_assets / sgreen_supply:.6f} GREEN per sGREEN ({savings_rate:+.4f}% vs 1:1) |")

    # Protocol status flags
    gen_config = mc.genConfig()
    status_flags = []
    if gen_config[3]:  # canDeposit
        status_flags.append("Deposits ON")
    else:
        status_flags.append("Deposits OFF")
    if gen_config[5]:  # canBorrow
        status_flags.append("Borrowing ON")
    else:
        status_flags.append("Borrowing OFF")
    if gen_config[8]:  # canLiquidate
        status_flags.append("Liquidations ON")
    else:
        status_flags.append("Liquidations OFF")

    print(f"| **Protocol Status** | {' / '.join(status_flags)} |")


def print_mission_control_config():
    """Print MissionControl configuration."""
    mc = state.mc

    print("\n" + "=" * 80)
    print("\n<a id=\"mission-control\"></a>")
    print("## MissionControl - Core Protocol Configuration")
    print(f"Address: `{mc.address}`")

    # General Config
    gen_config = mc.genConfig()
    rows = [
        ("perUserMaxVaults", gen_config[0]),
        ("perUserMaxAssetsPerVault", gen_config[1]),
        ("priceStaleTime", f"{gen_config[2]} seconds"),
        ("canDeposit", gen_config[3]),
        ("canWithdraw", gen_config[4]),
        ("canBorrow", gen_config[5]),
        ("canRepay", gen_config[6]),
        ("canClaimLoot", gen_config[7]),
        ("canLiquidate", gen_config[8]),
        ("canRedeemCollateral", gen_config[9]),
        ("canRedeemInStabPool", gen_config[10]),
        ("canBuyInAuction", gen_config[11]),
        ("canClaimInStabPool", gen_config[12]),
    ]
    print_table("General Config", ["Parameter", "Value"], rows, anchor="general-config", level=3)

    # General Debt Config
    gen_debt = mc.genDebtConfig()
    auction_params = gen_debt[16]
    rows = [
        ("perUserDebtLimit", format_token_amount(gen_debt[0])),
        ("globalDebtLimit", format_token_amount(gen_debt[1])),
        ("minDebtAmount", format_token_amount(gen_debt[2])),
        ("numAllowedBorrowers", gen_debt[3]),
        ("maxBorrowPerInterval", format_token_amount(gen_debt[4])),
        ("numBlocksPerInterval", format_blocks_to_time(gen_debt[5])),
        ("minDynamicRateBoost", format_percent(gen_debt[6])),
        ("maxDynamicRateBoost", format_percent(gen_debt[7])),
        ("increasePerDangerBlock", format_percent(gen_debt[8])),
        ("maxBorrowRate", format_percent(gen_debt[9])),
        ("maxLtvDeviation", format_percent(gen_debt[10])),
        ("keeperFeeRatio", format_percent(gen_debt[11])),
        ("minKeeperFee", format_token_amount(gen_debt[12])),
        ("maxKeeperFee", format_token_amount(gen_debt[13])),
        ("isDaowryEnabled", gen_debt[14]),
        ("ltvPaybackBuffer", format_percent(gen_debt[15])),
    ]
    print_table("General Debt Config", ["Parameter", "Value"], rows, anchor="debt-config", level=3)

    # Auction Params
    rows = [
        ("hasParams", auction_params[0]),
        ("startDiscount", format_percent(auction_params[1])),
        ("maxDiscount", format_percent(auction_params[2])),
        ("delay", format_blocks_to_time(auction_params[3])),
        ("duration", format_blocks_to_time(auction_params[4])),
    ]
    print_table("General Auction Parameters", ["Parameter", "Value"], rows, level=3)

    # HR Config
    hr_config = mc.hrConfig()
    max_comp = hr_config[1]
    max_comp_display = "No Limit" if max_comp == 0 else f"{format_wei(max_comp, 18)} RIPE"
    rows = [
        ("contribTemplate", format_address(str(hr_config[0]))),
        ("maxCompensation", max_comp_display),
        ("minCliffLength", format_blocks_to_time(hr_config[2])),
        ("maxStartDelay", format_blocks_to_time(hr_config[3])),
        ("minVestingLength", format_blocks_to_time(hr_config[4])),
        ("maxVestingLength", format_blocks_to_time(hr_config[5])),
    ]
    print_table("HR Config (Compensation)", ["Parameter", "Value"], rows, level=3)

    # RIPE Bond Config
    bond_config = mc.ripeBondConfig()
    rows = [
        ("asset", format_address(str(bond_config[0]))),
        ("amountPerEpoch", f"{format_wei(bond_config[1], 6)} (asset units)"),
        ("canBond", bond_config[2]),
        ("minRipePerUnit", f"{format_wei(bond_config[3], 18)} RIPE"),
        ("maxRipePerUnit", f"{format_wei(bond_config[4], 18)} RIPE"),
        ("maxRipePerUnitLockBonus", f"{format_wei(bond_config[5], 18)} RIPE"),
        ("epochLength", format_blocks_to_time(bond_config[6])),
        ("shouldAutoRestart", bond_config[7]),
        ("restartDelayBlocks", format_blocks_to_time(bond_config[8])),
    ]
    print_table("RIPE Bond Config", ["Parameter", "Value"], rows, level=3)

    # RIPE Gov Vault Config (needed for derived autoStakeLockDuration calculation)
    ripe_vault_config = mc.ripeGovVaultConfig(state.ripe.address)
    lock_terms = ripe_vault_config[0]
    min_lock = lock_terms[0]
    max_lock = lock_terms[1]

    # Rewards Config
    rewards_config = mc.rewardsConfig()
    auto_stake_duration_ratio = rewards_config[7]

    # Calculate derived autoStakeLockDuration
    # Formula from MissionControl._getLockDuration:
    # lockDuration = (maxLockDuration - minLockDuration) * autoStakeDurationRatio / HUNDRED_PERCENT
    if max_lock > min_lock and auto_stake_duration_ratio > 0:
        duration_range = max_lock - min_lock
        auto_stake_lock_duration = duration_range * auto_stake_duration_ratio // 10000  # HUNDRED_PERCENT = 10000
    else:
        auto_stake_lock_duration = min_lock

    rows = [
        ("arePointsEnabled", rewards_config[0]),
        ("ripePerBlock", f"{format_wei(rewards_config[1], 18)} RIPE"),
        ("borrowersAlloc", format_percent(rewards_config[2])),
        ("stakersAlloc", format_percent(rewards_config[3])),
        ("votersAlloc", format_percent(rewards_config[4])),
        ("genDepositorsAlloc", format_percent(rewards_config[5])),
        ("autoStakeRatio", format_percent(rewards_config[6])),
        ("autoStakeDurationRatio", format_percent(rewards_config[7])),
        ("**autoStakeLockDuration (derived)**", f"**{format_blocks_to_time(auto_stake_lock_duration)}**"),
        ("stabPoolRipePerDollarClaimed", f"{format_wei(rewards_config[8], 18)} RIPE"),
    ]
    print_table("RIPE Rewards Config", ["Parameter", "Value"], rows, anchor="rewards-config", level=3)

    # Total Points Allocations
    total_points = mc.totalPointsAllocs()
    rows = [
        ("stakersPointsAllocTotal", format_percent(total_points[0])),
        ("voterPointsAllocTotal", format_percent(total_points[1])),
    ]
    print_table("Total Points Allocations", ["Parameter", "Value"], rows, level=3)

    # RIPE Gov Vault Config
    rows = [
        ("minLockDuration", format_blocks_to_time(lock_terms[0])),
        ("maxLockDuration", format_blocks_to_time(lock_terms[1])),
        ("maxLockBoost", format_percent(lock_terms[2])),
        ("canExit", lock_terms[3]),
        ("exitFee", format_percent(lock_terms[4])),
        ("assetWeight", ripe_vault_config[1]),
        ("shouldFreezeWhenBadDebt", ripe_vault_config[2]),
    ]
    print_table("RIPE Token Governance Vault Config", ["Parameter", "Value"], rows, level=3)

    # Other Settings
    rows = [
        ("underscoreRegistry", format_address(str(mc.underscoreRegistry()))),
        ("trainingWheels", format_address(str(mc.trainingWheels()))),
        ("shouldCheckLastTouch", mc.shouldCheckLastTouch()),
    ]
    print_table("Other Settings", ["Parameter", "Value"], rows, level=3)

    # Priority Lists
    print("\n<a id=\"priority-lists\"></a>")
    print("### Priority Lists")

    price_source_ids = mc.getPriorityPriceSourceIds()
    if price_source_ids:
        rows = []
        for i, source_id in enumerate(price_source_ids):
            # Look up the price source name from PriceDesk
            try:
                addr_info = state.pd.addrInfo(source_id)
                source_name = addr_info.description
            except Exception:
                source_name = "Unknown"
            rows.append((i, source_id, source_name))
        print_table("Priority Price Source IDs", ["Priority", "Source ID", "Name"], rows, level=4)
    else:
        print("\n#### Priority Price Source IDs")
        print("*No priority price sources configured*")

    liq_vaults = mc.getPriorityLiqAssetVaults()
    if liq_vaults:
        rows = []
        for i, v in enumerate(liq_vaults):
            vault_id = v[0]
            asset = format_address(str(v[1]))
            # Look up the vault name from VaultBook
            try:
                addr_info = state.vb.addrInfo(vault_id)
                vault_name = addr_info.description
            except Exception:
                vault_name = "Unknown"
            rows.append((i, vault_id, vault_name, asset))
        print_table("Priority Liquidation Asset Vaults", ["Priority", "Vault ID", "Vault Name", "Asset"], rows, level=4)
    else:
        print("\n#### Priority Liquidation Asset Vaults")
        print("*No priority liquidation vaults configured*")

    stab_vaults = mc.getPriorityStabVaults()
    if stab_vaults:
        rows = []
        for i, v in enumerate(stab_vaults):
            vault_id = v[0]
            asset = format_address(str(v[1]))
            # Look up the vault name from VaultBook
            try:
                addr_info = state.vb.addrInfo(vault_id)
                vault_name = addr_info.description
            except Exception:
                vault_name = "Unknown"
            rows.append((i, vault_id, vault_name, asset))
        print_table("Priority Stability Pool Vaults", ["Priority", "Vault ID", "Vault Name", "Asset"], rows, level=4)
    else:
        print("\n#### Priority Stability Pool Vaults")
        print("*No priority stability pool vaults configured*")


def print_ripe_hq_data():
    """Print RipeHQ registry data."""
    hq = state.hq

    print("\n" + "=" * 80)
    print("\n<a id=\"ripe-hq\"></a>")
    print("## RipeHQ - Main Registry & Minting Config")
    print(f"Address: `{RIPE_HQ}`")

    rows = [("mintEnabled", hq.mintEnabled())]
    print_table("Minting Circuit Breaker", ["Parameter", "Value"], rows, level=3)

    # AddressRegistry Module params
    print_address_registry_params(hq, registry_name="contracts", level=3)

    # LocalGov Module params
    print_local_gov_params(hq, level=3)

    # All Registered Contracts with HqConfig
    num_addrs = hq.numAddrs()
    if num_addrs > 1:
        print("\n### Registered Contracts & Permissions")
        headers = ["ID", "Description", "Address", "Mint GREEN", "Mint RIPE", "Blacklist", "Paused"]
        rows = []

        for i in range(1, num_addrs):
            time.sleep(RPC_DELAY)
            addr_info = hq.addrInfo(i)
            contract_addr = str(addr_info.addr)
            if contract_addr == ZERO_ADDRESS:
                continue

            # Get HqConfig for this contract
            hq_config = hq.hqConfig(i)

            # Try to get isPaused from the contract
            is_paused = "-"
            try:
                contract = boa.from_etherscan(contract_addr, name=f"Contract{i}")
                if hasattr(contract, 'isPaused'):
                    is_paused = contract.isPaused()
            except Exception:
                pass

            # Use addr_info.description as it has the full name
            description = addr_info.description if addr_info.description else hq_config.description
            rows.append([
                i,
                description,
                f"`{contract_addr}`",
                "Yes" if hq_config.canMintGreen else "-",
                "Yes" if hq_config.canMintRipe else "-",
                "Yes" if hq_config.canSetTokenBlacklist else "-",
                is_paused,
            ])

        if rows:
            print(f"\n| {' | '.join(headers)} |")
            print(f"| {' | '.join(['---' for _ in headers])} |")
            for row in rows:
                print(f"| {' | '.join(str(cell) for cell in row)} |")

    # Pending HQ Config Changes
    _print_pending_hq_config_changes(hq, num_addrs)


def _print_pending_hq_config_changes(hq, num_addrs: int):
    """Print pending HQ config changes for registered contracts."""
    if not hasattr(hq, 'hasPendingHqConfigChange'):
        return

    pending_changes = []

    for i in range(1, num_addrs):
        time.sleep(RPC_DELAY)
        try:
            has_pending = hq.hasPendingHqConfigChange(i)
            if has_pending:
                time.sleep(RPC_DELAY)
                addr_info = hq.addrInfo(i)
                pending = hq.pendingHqConfig(i)
                pending_changes.append({
                    "reg_id": i,
                    "description": addr_info.description,
                    "address": str(addr_info.addr),
                    "pending": pending,
                })
        except Exception:
            continue

    if not pending_changes:
        return

    print(f"\n### ⏳ Pending HQ Config Changes ({len(pending_changes)})")

    for item in pending_changes:
        print(f"\n**{item['description']}** (ID: {item['reg_id']})")
        print(f"- Address: `{item['address']}`")

        pending = item["pending"]
        if hasattr(pending, 'initiatedBlock'):
            print(f"- Initiated Block: {pending.initiatedBlock}")
        if hasattr(pending, 'confirmBlock'):
            print(f"- Confirm Block: {pending.confirmBlock}")

        if hasattr(pending, 'newHqConfig'):
            new_config = pending.newHqConfig
            print(f"- New Description: {new_config.description}")
            print(f"- New canMintGreen: {new_config.canMintGreen}")
            print(f"- New canMintRipe: {new_config.canMintRipe}")
            print(f"- New canSetTokenBlacklist: {new_config.canSetTokenBlacklist}")


def print_switchboard_data():
    """Print Switchboard registry data."""
    sb = state.sb

    print("\n" + "=" * 80)
    print("\n<a id=\"switchboard\"></a>")
    print("## Switchboard - Configuration Contracts Registry")
    print(f"Address: `{sb.address}`")

    # AddressRegistry Module params
    print_address_registry_params(sb, registry_name="switchboards", level=3)

    # LocalGov Module params
    print_local_gov_params(sb, level=3)

    # Registered switchboards summary
    if state.switchboards:
        print("\n### Registered Switchboards")
        print("\n| Reg ID | Description | Address |")
        print("| --- | --- | --- |")
        for reg_id, sw_info in sorted(state.switchboards.items()):
            print(f"| {reg_id} | {sw_info['description']} | `{sw_info['address']}` |")

        # Individual switchboard configs
        print("\n### Individual Switchboard Configurations")
        for reg_id, sw_info in sorted(state.switchboards.items()):
            sw = sw_info["contract"]
            print(f"\n#### {sw_info['description']}")
            print(f"Address: `{sw_info['address']}`")

            # LocalGov Module params
            print_local_gov_params(sw, level=5)

            # TimeLock Module params
            print_timelock_params(sw, level=5)


def print_endaoment_contracts():
    """Print Endaoment and EndaomentPSM configuration."""
    print("\n" + "=" * 80)
    print("\n<a id=\"endaoment\"></a>")
    print("## Endaoment Contracts")

    # Endaoment (main yield aggregator)
    print(f"\n### Endaoment")
    print(f"Address: `{state.endaoment.address}`")
    rows = [
        ("isPaused", state.endaoment.isPaused()),
        ("WETH", format_address(str(state.endaoment.WETH()))),
    ]
    print_table("Status", ["Parameter", "Value"], rows, level=4)

    # EndaomentPSM
    psm = state.psm
    print(f"\n### Endaoment PSM - Peg Stability Module")
    print(f"Address: `{psm.address}`")

    # Mint config
    can_mint = psm.canMint()
    mint_fee = psm.mintFee()
    max_interval_mint = psm.maxIntervalMint()
    enforce_allowlist = psm.shouldEnforceMintAllowlist()

    rows = [
        ("canMint", "Enabled" if can_mint else "Disabled"),
        ("mintFee", format_percent(mint_fee)),
        ("maxIntervalMint", format_token_amount(max_interval_mint)),
        ("shouldEnforceMintAllowlist", enforce_allowlist),
    ]
    print_table("PSM Mint Configuration", ["Parameter", "Value"], rows, level=3)

    # Redeem config
    can_redeem = psm.canRedeem()
    redeem_fee = psm.redeemFee()
    max_interval_redeem = psm.maxIntervalRedeem()
    enforce_redeem_allowlist = psm.shouldEnforceRedeemAllowlist()

    rows = [
        ("canRedeem", "Enabled" if can_redeem else "Disabled"),
        ("redeemFee", format_percent(redeem_fee)),
        ("maxIntervalRedeem", format_token_amount(max_interval_redeem)),
        ("shouldEnforceRedeemAllowlist", enforce_redeem_allowlist),
    ]
    print_table("PSM Redeem Configuration", ["Parameter", "Value"], rows, level=3)

    # Interval config
    num_blocks_per_interval = psm.numBlocksPerInterval()
    should_auto_deposit = psm.shouldAutoDeposit()
    usdc_yield_position = psm.usdcYieldPosition()

    rows = [
        ("numBlocksPerInterval", format_blocks_to_time(num_blocks_per_interval)),
        ("shouldAutoDeposit", should_auto_deposit),
        ("usdcYieldPosition.legoId", usdc_yield_position[0]),
        ("usdcYieldPosition.vaultToken", format_address(str(usdc_yield_position[1]))),
    ]
    print_table("PSM Interval & Yield Configuration", ["Parameter", "Value"], rows, level=3)

    # Current interval stats
    global_mint_interval = psm.globalMintInterval()
    global_redeem_interval = psm.globalRedeemInterval()

    rows = [
        ("Mint Interval Start", global_mint_interval[0]),
        ("Mint Interval Amount", format_token_amount(global_mint_interval[1])),
        ("Redeem Interval Start", global_redeem_interval[0]),
        ("Redeem Interval Amount", format_token_amount(global_redeem_interval[1])),
    ]
    print_table("PSM Current Interval Stats", ["Parameter", "Value"], rows, level=3)

    # USDC info
    usdc_addr = psm.USDC()
    print(f"\n**USDC Address:** {format_address(str(usdc_addr))}")

    # EndaomentFunds
    ef = state.endaoment_funds
    print(f"\n### EndaomentFunds")
    print(f"Address: `{ef.address}`")

    rows = []
    if hasattr(ef, 'isPaused'):
        rows.append(("isPaused", ef.isPaused()))
    if rows:
        print_table("Status", ["Parameter", "Value"], rows, level=4)

    # LocalGov Module params
    print_local_gov_params(ef, level=4)

    # TimeLock Module params
    print_timelock_params(ef, level=4)


def print_departments():
    """Print all department contracts - those with config first, status-only last."""
    print("\n" + "=" * 80)
    print("\n<a id=\"departments\"></a>")
    print("## Departments")

    # =========================================================================
    # Contracts WITH configuration (ordered first)
    # =========================================================================

    # CreditEngine
    print(f"\n### CreditEngine")
    print(f"Address: `{state.ce.address}`")
    rows = [
        ("undyVaultDiscount", format_percent(state.ce.undyVaulDiscount())),
        ("buybackRatio", format_percent(state.ce.buybackRatio())),
    ]
    print_table("Config", ["Parameter", "Value"], rows, level=4)

    # BondBooster
    print(f"\n### BondBooster")
    print(f"Address: `{state.bb.address}`")
    rows = [
        ("maxBoostRatio", format_percent(state.bb.maxBoostRatio())),
        ("maxUnits", state.bb.maxUnits()),
        ("minLockDuration", format_blocks_to_time(state.bb.minLockDuration())),
    ]
    print_table("Config", ["Parameter", "Value"], rows, level=4)

    # Lootbox
    print(f"\n### Lootbox")
    print(f"Address: `{state.lootbox.address}`")
    rows = [
        ("hasUnderscoreRewards", state.lootbox.hasUnderscoreRewards()),
        ("underscoreSendInterval", format_blocks_to_time(state.lootbox.underscoreSendInterval())),
        ("lastUnderscoreSend (block)", state.lootbox.lastUnderscoreSend()),
        ("undyDepositRewardsAmount", format_token_amount(state.lootbox.undyDepositRewardsAmount(), 18, "RIPE")),
        ("undyYieldBonusAmount", format_token_amount(state.lootbox.undyYieldBonusAmount(), 18, "RIPE")),
    ]
    print_table("Underscore Rewards Config", ["Parameter", "Value"], rows, level=4)

    # HumanResources
    print(f"\n### HumanResources")
    print(f"Address: `{state.hr.address}`")
    rows = [("isPaused", state.hr.isPaused())]
    print_table("Status", ["Parameter", "Value"], rows, level=4)

    # LocalGov Module params
    print_local_gov_params(state.hr, level=4)

    # TimeLock Module params
    print_timelock_params(state.hr, level=4)

    print("*Note: numContributors is tracked in Ledger contract*")

    # StabilityPool
    print(f"\n### StabilityPool")
    print(f"Address: `{state.stab_pool.address}`")
    num_assets = state.stab_pool.numAssets()
    rows = [
        ("isPaused", state.stab_pool.isPaused()),
        ("numAssets", num_assets - 1 if num_assets > 0 else 0),
    ]
    print_table("Status", ["Parameter", "Value"], rows, level=4)

    # =========================================================================
    # Other Contracts with Module Params
    # =========================================================================

    print("\n---")

    # BondRoom
    print(f"\n### BondRoom")
    print(f"Address: `{state.bond_room.address}`")
    rows = [
        ("isPaused", state.bond_room.isPaused()),
        ("bondBooster", format_address(str(state.bond_room.bondBooster()))),
    ]
    print_table("Status", ["Parameter", "Value"], rows, level=4)

    # LocalGov Module params
    print_local_gov_params(state.bond_room, level=4)

    # TimeLock Module params
    print_timelock_params(state.bond_room, level=4)

    # RipeGovVault
    print(f"\n### RipeGovVault")
    print(f"Address: `{state.ripe_gov.address}`")
    rows = [
        ("isPaused", state.ripe_gov.isPaused()),
        ("totalGovPoints", f"{state.ripe_gov.totalGovPoints():,}"),
    ]
    print_table("Status", ["Parameter", "Value"], rows, level=4)

    # AuctionHouse
    print(f"\n### AuctionHouse")
    print(f"Address: `{state.auction_house.address}`")
    rows = [("isPaused", state.auction_house.isPaused())]
    print_table("Status", ["Parameter", "Value"], rows, level=4)

    # LocalGov Module params
    print_local_gov_params(state.auction_house, level=4)

    # TimeLock Module params
    print_timelock_params(state.auction_house, level=4)

    # Teller
    print(f"\n### Teller")
    print(f"Address: `{state.teller.address}`")
    rows = [("isPaused", state.teller.isPaused())]
    print_table("Status", ["Parameter", "Value"], rows, level=4)

    # LocalGov Module params
    print_local_gov_params(state.teller, level=4)

    # TimeLock Module params
    print_timelock_params(state.teller, level=4)

    # Deleverage
    print(f"\n### Deleverage")
    print(f"Address: `{state.deleverage.address}`")
    rows = [("isPaused", state.deleverage.isPaused())]
    print_table("Status", ["Parameter", "Value"], rows, level=4)

    # LocalGov Module params
    print_local_gov_params(state.deleverage, level=4)

    # TimeLock Module params
    print_timelock_params(state.deleverage, level=4)

    # CreditRedeem
    print(f"\n### CreditRedeem")
    print(f"Address: `{state.credit_redeem.address}`")
    rows = [("isPaused", state.credit_redeem.isPaused())]
    print_table("Status", ["Parameter", "Value"], rows, level=4)

    # LocalGov Module params
    print_local_gov_params(state.credit_redeem, level=4)

    # TimeLock Module params
    print_timelock_params(state.credit_redeem, level=4)


def print_token_statistics():
    """Print token supply data."""
    print("\n" + "=" * 80)
    print("\n<a id=\"token-statistics\"></a>")
    print("## Token Statistics")

    # GREEN Token
    green_supply = state.green.totalSupply()
    rows = [
        ("totalSupply", format_token_amount(green_supply)),
        ("decimals", state.green.decimals()),
        ("name", state.green.name()),
        ("symbol", state.green.symbol()),
    ]
    print_table("GREEN Token", ["Parameter", "Value"], rows, level=3)

    # RIPE Token
    ripe_supply = state.ripe.totalSupply()
    rows = [
        ("totalSupply", format_token_amount(ripe_supply, 18, "RIPE")),
        ("decimals", state.ripe.decimals()),
        ("name", state.ripe.name()),
        ("symbol", state.ripe.symbol()),
    ]
    print_table("RIPE Token", ["Parameter", "Value"], rows, level=3)

    # Savings GREEN (sGREEN)
    sgreen_supply = state.sgreen.totalSupply()
    sgreen_assets = state.sgreen.totalAssets()
    exchange_rate = sgreen_assets / sgreen_supply if sgreen_supply > 0 else 1
    accumulated_yield = (exchange_rate - 1) * 100

    rows = [
        ("totalSupply (shares)", format_token_amount(sgreen_supply)),
        ("totalAssets (GREEN)", format_token_amount(sgreen_assets)),
        ("**Exchange Rate**", f"**{exchange_rate:.6f} GREEN per sGREEN**"),
        ("**Accumulated Yield**", f"**{accumulated_yield:+.4f}%** above 1:1"),
        ("decimals", state.sgreen.decimals()),
        ("name", state.sgreen.name()),
        ("symbol", state.sgreen.symbol()),
    ]
    print_table("Savings GREEN (sGREEN)", ["Parameter", "Value"], rows, level=3)

    print(f"\n*Example: 1,000 sGREEN = {1000 * exchange_rate:,.4f} GREEN*")


# ============================================================================
# Main Entry Point
# ============================================================================


def main():
    """Main entry point."""
    # Output file path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, "general_output.md")

    print("Connecting to Base mainnet via Alchemy...", file=sys.stderr)

    # Set etherscan API
    setup_boa_etherscan()

    # Fork at latest block
    with boa_fork_context() as block_number:
        print(f"Connected. Block: {block_number}\n", file=sys.stderr)

        # Store block number in state for relative time calculations
        state.block_number = block_number

        # Load all contracts
        initialize_general()

        print(f"Writing output to {output_file}...", file=sys.stderr)

        # Write report to file
        with output_to_file(output_file):
            # Header
            print_report_header("Ripe Protocol - General Parameters", block_number)

            print("\nGeneral protocol configuration, statistics, and contract status.\n")

            # Table of Contents
            print_table_of_contents()

            # Executive Summary
            print_executive_summary()

            # Token Statistics
            print_token_statistics()

            # MissionControl
            print_mission_control_config()

            # RipeHQ
            print_ripe_hq_data()

            # Switchboard
            print_switchboard_data()

            # Endaoment Contracts
            print_endaoment_contracts()

            # Departments
            print_departments()

            # Footer
            print_report_footer(block_number)

        print(f"Done! Output saved to {output_file}", file=sys.stderr)


if __name__ == "__main__":
    main()
