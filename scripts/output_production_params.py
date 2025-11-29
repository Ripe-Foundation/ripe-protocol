#!/usr/bin/env python3
"""
Output Production Parameters Script

Fetches and displays all current production configuration from Ripe Protocol
smart contracts on Base mainnet, formatted as markdown tables.

Usage:
    python scripts/output_production_params.py
"""

import os
import sys
from datetime import datetime, timezone

import boa

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.BluePrint import CORE_TOKENS, YIELD_TOKENS, ADDYS

# Contract addresses (Base Mainnet)
MISSION_CONTROL = "0xB59b84B526547b6dcb86CCF4004d48E619156CF3"
RIPE_HQ = "0x6162df1b329E157479F8f1407E888260E0EC3d2b"
PRICE_DESK = "0xDFe8D79bc05420a3fFa14824135016a738eE8299"
VAULT_BOOK = "0xB758e30C14825519b895Fd9928d5d8748A71a944"
LEDGER = "0x365256e322a47Aa2015F6724783F326e9B24fA47"
CREDIT_ENGINE = "0x30aa8eB041AcB3B22228516297C331B313b81462"
BOND_BOOSTER = "0xA1872467AC4fb442aeA341163A65263915ce178a"
ENDAOMENT = "0x70fA85Aa99a39161A2623627377F1c791fd091f6"
ENDAOMENT_PSM = "0x2893d0dfa54571bDc7DE60F2d8a456d3377CcAA7"
GREEN_TOKEN = "0xd1Eac76497D06Cf15475A5e3984D5bC03de7C707"
RIPE_TOKEN = "0x2A0a59d6B975828e781EcaC125dBA40d7ee5dDC0"
SAVINGS_GREEN = "0xaa0f13488CE069A7B5a099457c753A7CFBE04d36"
STABILITY_POOL = "0x2a157096af6337b2b4bd47de435520572ed5a439"
GREEN_POOL = "0xd6c283655B42FA0eb2685F7AB819784F071459dc"

# Additional contracts
LOOTBOX = "0x1f90ef42Da9B41502d2311300E13FAcf70c64be7"
BOND_ROOM = "0x707f660A7834d00792DF9a28386Bb2cCC6446154"
RIPE_GOV_VAULT = "0xe42b3dC546527EB70D741B185Dc57226cA01839D"
SWITCHBOARD = "0xc68A90A40B87ae1dABA93Da9c02642F8B74030F9"

# Core Lending contracts
AUCTION_HOUSE = "0x8a02aC4754b72aFBDa4f403ec5DA7C2950164084"
TELLER = "0xae87deB25Bc5030991Aa5E27Cbab38f37a112C13"
DELEVERAGE = "0x75EeBb8c6f1A5727e7c0c1f9d64Ed07cd0966F27"
CREDIT_REDEEM = "0x3bfB0F72642aeFA2486da00Db855c5F0b787e3FB"

# Treasury contracts
ENDAOMENT_FUNDS = "0x4Ce5FB8D572917Eb96724eA1866b505B2a6B0873"
HUMAN_RESOURCES = "0xF9aCDFd0d167b741f9144Ca01E52FcdE16BE108b"

# RPC URL
RPC_URL = f"https://base-mainnet.g.alchemy.com/v2/{os.environ.get('WEB3_ALCHEMY_API_KEY')}"

# Constants for formatting
HUNDRED_PERCENT = 100_00  # 100.00%
DECIMALS_18 = 10**18
DECIMALS_6 = 10**6

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

# Cache for resolved token symbols
_token_symbol_cache = {}


def get_token_name(address: str, try_fetch: bool = True) -> str:
    """Resolve address to token symbol or return truncated address.

    Args:
        address: The token address
        try_fetch: If True, attempt to fetch symbol from contract for unknown addresses
    """
    if address == "0x0000000000000000000000000000000000000000":
        return "None"

    addr_lower = address.lower()

    # Check cache first
    if addr_lower in _token_symbol_cache:
        return _token_symbol_cache[addr_lower]

    # Check CORE_TOKENS
    for name, addr in CORE_TOKENS.get("base", {}).items():
        if addr.lower() == addr_lower:
            _token_symbol_cache[addr_lower] = name
            return name

    # Check YIELD_TOKENS
    for name, addr in YIELD_TOKENS.get("base", {}).items():
        if addr.lower() == addr_lower:
            _token_symbol_cache[addr_lower] = name
            return name

    # Check ADDYS for known protocol addresses
    for name, addr in ADDYS.get("base", {}).items():
        if addr.lower() == addr_lower:
            _token_symbol_cache[addr_lower] = name
            return name

    # Known protocol addresses
    known_addresses = {
        MISSION_CONTROL.lower(): "MissionControl",
        RIPE_TOKEN.lower(): "RIPE",
        ENDAOMENT.lower(): "Endaoment",
        "0xd1eac76497d06cf15475a5e3984d5bc03de7c707": "GREEN",
        "0xaa0f13488ce069a7b5a099457c753a7cfbe04d36": "sGREEN",
        "0x44cf3c4f000dfd76a35d03298049d37be688d6f9": "UnderscoreRegistry",
    }
    if addr_lower in known_addresses:
        _token_symbol_cache[addr_lower] = known_addresses[addr_lower]
        return known_addresses[addr_lower]

    # Try to fetch symbol from contract
    if try_fetch:
        try:
            token_contract = boa.from_etherscan(address, name=f"Token_{address[:8]}")
            symbol = token_contract.symbol()
            if symbol:
                _token_symbol_cache[addr_lower] = symbol
                return symbol
        except Exception:
            pass

    truncated = f"{address[:6]}...{address[-4:]}"
    _token_symbol_cache[addr_lower] = truncated
    return truncated


def get_token_decimals(address: str) -> int:
    """Get token decimals, with caching and fallback to 18."""
    try:
        token_contract = boa.from_etherscan(address, name=f"Token_{address[:8]}")
        return token_contract.decimals()
    except Exception:
        return 18


def format_address(address: str) -> str:
    """Format address with resolved name."""
    name = get_token_name(address)
    if name != f"{address[:6]}...{address[-4:]}":
        return f"{name} ({address[:6]}...{address[-4:]})"
    return name


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


def format_token_amount(raw_value: int, decimals: int = 18, symbol: str = "GREEN") -> str:
    """Format token amount, showing 'Unlimited' for very large values.

    Note: GREEN token has 18 decimals, USDC has 6 decimals.
    """
    amount = raw_value / (10 ** decimals)
    # If amount exceeds 1 trillion, consider it "unlimited/very high"
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


def print_table(title: str, headers: list, rows: list, anchor: str = None):
    """Print a markdown table with optional anchor."""
    if anchor:
        print(f"\n<a id=\"{anchor}\"></a>")
    print(f"\n## {title}")
    print(f"| {' | '.join(headers)} |")
    print(f"| {' | '.join(['---' for _ in headers])} |")
    for row in rows:
        print(f"| {' | '.join(str(cell) for cell in row)} |")


def print_table_of_contents():
    """Print a clickable table of contents."""
    print("""
## Table of Contents

1. [Executive Summary](#executive-summary)
2. [MissionControl Configuration](#mission-control)
   - [General Config](#general-config)
   - [Debt Config](#debt-config)
   - [Rewards Config](#rewards-config)
   - [Registered Assets](#registered-assets)
3. [RipeHQ Registry](#ripe-hq)
4. [Switchboard Registry](#switchboard)
5. [PriceDesk Oracles](#price-desk)
6. [VaultBook Registry](#vault-book)
7. [Ledger Statistics](#ledger)
8. [Endaoment PSM](#endaoment-psm)
9. [Core Lending Contracts](#core-lending)
   - [CreditEngine](#credit-engine)
   - [AuctionHouse](#auction-house)
   - [Teller](#teller)
   - [Deleverage](#deleverage)
   - [CreditRedeem](#credit-redeem)
   - [StabilityPool](#stability-pool)
10. [Treasury & Rewards Contracts](#treasury-rewards)
    - [Endaoment](#endaoment)
    - [BondBooster](#bond-booster)
    - [Lootbox](#lootbox)
    - [BondRoom](#bond-room)
    - [HumanResources](#human-resources)
11. [Governance Contracts](#governance)
    - [RipeGovVault](#ripe-gov-vault)
12. [Price Source Configurations](#price-sources)
13. [Token Statistics](#token-statistics)
""")


def print_executive_summary(mc, ledger, green, sgreen, ripe):
    """Print an executive summary with key protocol metrics."""
    print("\n<a id=\"executive-summary\"></a>")
    print("## 📊 Executive Summary\n")

    try:
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

        # Protocol status
        gen_config = mc.genConfig()
        status_flags = []
        if gen_config[3]:  # canDeposit
            status_flags.append("✅ Deposits")
        else:
            status_flags.append("❌ Deposits")
        if gen_config[5]:  # canBorrow
            status_flags.append("✅ Borrowing")
        else:
            status_flags.append("❌ Borrowing")
        if gen_config[8]:  # canLiquidate
            status_flags.append("✅ Liquidations")
        else:
            status_flags.append("❌ Liquidations")

        print(f"| **Protocol Status** | {' / '.join(status_flags)} |")

    except Exception as e:
        print(f"*Error generating summary: {e}*")


def fetch_mission_control_data(mc):
    """Fetch and print all MissionControl configuration data."""

    # Header
    print("\n<a id=\"mission-control\"></a>")
    print("# MissionControl - Core Protocol Configuration")
    print(f"Address: {MISSION_CONTROL}")

    # ====== General Config ======
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
    print_table("General Config", ["Parameter", "Value"], rows)

    # ====== General Debt Config ======
    gen_debt = mc.genDebtConfig()
    auction_params = gen_debt[16]  # genAuctionParams tuple
    # Note: GREEN token has 6 decimals like USDC
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
    print_table("General Debt Config", ["Parameter", "Value"], rows)

    # Auction Params sub-table
    rows = [
        ("hasParams", auction_params[0]),
        ("startDiscount", format_percent(auction_params[1])),
        ("maxDiscount", format_percent(auction_params[2])),
        ("delay", format_blocks_to_time(auction_params[3])),
        ("duration", format_blocks_to_time(auction_params[4])),
    ]
    print_table("General Auction Parameters", ["Parameter", "Value"], rows)

    # ====== HR Config ======
    hr_config = mc.hrConfig()
    rows = [
        ("contribTemplate", format_address(hr_config[0])),
        ("maxCompensation", f"{format_wei(hr_config[1], 18)} RIPE"),
        ("minCliffLength", format_blocks_to_time(hr_config[2])),
        ("maxStartDelay", format_blocks_to_time(hr_config[3])),
        ("minVestingLength", format_blocks_to_time(hr_config[4])),
        ("maxVestingLength", format_blocks_to_time(hr_config[5])),
    ]
    print_table("HR Config (Compensation)", ["Parameter", "Value"], rows)

    # ====== RIPE Bond Config ======
    bond_config = mc.ripeBondConfig()
    rows = [
        ("asset", format_address(bond_config[0])),
        ("amountPerEpoch", f"{format_wei(bond_config[1], 6)} (asset units)"),
        ("canBond", bond_config[2]),
        ("minRipePerUnit", f"{format_wei(bond_config[3], 18)} RIPE"),
        ("maxRipePerUnit", f"{format_wei(bond_config[4], 18)} RIPE"),
        ("maxRipePerUnitLockBonus", f"{format_wei(bond_config[5], 18)} RIPE"),
        ("epochLength", format_blocks_to_time(bond_config[6])),
        ("shouldAutoRestart", bond_config[7]),
        ("restartDelayBlocks", format_blocks_to_time(bond_config[8])),
    ]
    print_table("RIPE Bond Config", ["Parameter", "Value"], rows)

    # ====== Rewards Config ======
    rewards_config = mc.rewardsConfig()
    rows = [
        ("arePointsEnabled", rewards_config[0]),
        ("ripePerBlock", f"{format_wei(rewards_config[1], 18)} RIPE"),
        ("borrowersAlloc", format_percent(rewards_config[2])),
        ("stakersAlloc", format_percent(rewards_config[3])),
        ("votersAlloc", format_percent(rewards_config[4])),
        ("genDepositorsAlloc", format_percent(rewards_config[5])),
        ("autoStakeRatio", format_percent(rewards_config[6])),
        ("autoStakeDurationRatio", format_percent(rewards_config[7])),
        ("stabPoolRipePerDollarClaimed", f"{format_wei(rewards_config[8], 18)} RIPE"),
    ]
    print_table("RIPE Rewards Config", ["Parameter", "Value"], rows)

    # ====== Total Points Allocations ======
    total_points = mc.totalPointsAllocs()
    rows = [
        ("stakersPointsAllocTotal", format_percent(total_points[0])),
        ("voterPointsAllocTotal", format_percent(total_points[1])),
    ]
    print_table("Total Points Allocations", ["Parameter", "Value"], rows)

    # ====== RIPE Gov Vault Config ======
    ripe_vault_config = mc.ripeGovVaultConfig(RIPE_TOKEN)
    lock_terms = ripe_vault_config[0]  # LockTerms tuple
    rows = [
        ("minLockDuration", format_blocks_to_time(lock_terms[0])),
        ("maxLockDuration", format_blocks_to_time(lock_terms[1])),
        ("maxLockBoost", format_percent(lock_terms[2])),
        ("canExit", lock_terms[3]),
        ("exitFee", format_percent(lock_terms[4])),
        ("assetWeight", ripe_vault_config[1]),
        ("shouldFreezeWhenBadDebt", ripe_vault_config[2]),
    ]
    print_table("RIPE Token Governance Vault Config", ["Parameter", "Value"], rows)

    # ====== Other Settings ======
    rows = [
        ("underscoreRegistry", format_address(mc.underscoreRegistry())),
        ("trainingWheels", format_address(mc.trainingWheels())),
        ("shouldCheckLastTouch", mc.shouldCheckLastTouch()),
    ]
    print_table("Other Settings", ["Parameter", "Value"], rows)

    # ====== Priority Price Source IDs ======
    try:
        price_source_ids = mc.getPriorityPriceSourceIds()
        if price_source_ids:
            rows = [(i, source_id) for i, source_id in enumerate(price_source_ids)]
            print_table("Priority Price Source IDs", ["Priority", "Source ID"], rows)
        else:
            print("\n## Priority Price Source IDs")
            print("*No priority price sources configured*")
    except Exception as e:
        print(f"\n## Priority Price Source IDs")
        print(f"*Error fetching: {e}*")

    # ====== Priority Liquidation Asset Vaults ======
    try:
        liq_vaults = mc.getPriorityLiqAssetVaults()
        if liq_vaults:
            rows = [(v[0], format_address(v[1])) for v in liq_vaults]
            print_table("Priority Liquidation Asset Vaults", ["Vault ID", "Asset"], rows)
        else:
            print("\n## Priority Liquidation Asset Vaults")
            print("*No priority liquidation vaults configured*")
    except Exception as e:
        print(f"\n## Priority Liquidation Asset Vaults")
        print(f"*Error fetching: {e}*")

    # ====== Priority Stability Pool Vaults ======
    try:
        stab_vaults = mc.getPriorityStabVaults()
        if stab_vaults:
            rows = [(v[0], format_address(v[1])) for v in stab_vaults]
            print_table("Priority Stability Pool Vaults", ["Vault ID", "Asset"], rows)
        else:
            print("\n## Priority Stability Pool Vaults")
            print("*No priority stability pool vaults configured*")
    except Exception as e:
        print(f"\n## Priority Stability Pool Vaults")
        print(f"*Error fetching: {e}*")

    # ====== Registered Assets ======
    num_assets = mc.numAssets()
    print(f"\n## Registered Assets ({num_assets - 1} total)")

    if num_assets > 1:
        # Headers for asset config table
        headers = [
            "Asset", "Vault IDs", "LTV", "Liq Threshold", "Borrow Rate",
            "canDeposit", "canBorrow"
        ]
        rows = []

        # Start from index 1 (index 0 is unused)
        for i in range(1, num_assets):
            asset_addr = mc.assets(i)
            asset_config = mc.assetConfig(asset_addr)
            # Access nested struct via attribute (index 6 is debtTerms)
            debt_terms = asset_config.debtTerms

            vault_ids = asset_config.vaultIds
            vault_ids_str = ", ".join(str(v) for v in vault_ids) if vault_ids else "None"

            rows.append([
                format_address(asset_addr),
                vault_ids_str,
                format_percent(debt_terms.ltv),
                format_percent(debt_terms.liqThreshold),
                format_percent(debt_terms.borrowRate),
                asset_config.canDeposit,
                debt_terms.ltv > 0,  # has LTV means can borrow against it
            ])

        print(f"| {' | '.join(headers)} |")
        print(f"| {' | '.join(['---' for _ in headers])} |")
        for row in rows:
            print(f"| {' | '.join(str(cell) for cell in row)} |")

        # Detailed asset configs
        print("\n### Detailed Asset Configurations")
        for i in range(1, num_assets):
            asset_addr = mc.assets(i)
            asset_config = mc.assetConfig(asset_addr)
            debt_terms = asset_config.debtTerms
            custom_auction = asset_config.customAuctionParams

            asset_name = get_token_name(asset_addr)
            print(f"\n#### {asset_name} ({asset_addr})")

            # Core settings
            rows = [
                ("vaultIds", ", ".join(str(v) for v in asset_config.vaultIds) if asset_config.vaultIds else "None"),
                ("stakersPointsAlloc", format_percent(asset_config.stakersPointsAlloc)),
                ("voterPointsAlloc", format_percent(asset_config.voterPointsAlloc)),
                ("perUserDepositLimit", f"{format_wei(asset_config.perUserDepositLimit, 6)}"),
                ("globalDepositLimit", f"{format_wei(asset_config.globalDepositLimit, 6)}"),
                ("minDepositBalance", f"{format_wei(asset_config.minDepositBalance, 6)}"),
            ]
            print_table(f"{asset_name} - Deposit Settings", ["Parameter", "Value"], rows)

            # Debt terms
            rows = [
                ("ltv", format_percent(debt_terms.ltv)),
                ("redemptionThreshold", format_percent(debt_terms.redemptionThreshold)),
                ("liqThreshold", format_percent(debt_terms.liqThreshold)),
                ("liqFee", format_percent(debt_terms.liqFee)),
                ("borrowRate", format_percent(debt_terms.borrowRate)),
                ("daowry", format_percent(debt_terms.daowry)),
            ]
            print_table(f"{asset_name} - Debt Terms", ["Parameter", "Value"], rows)

            # Liquidation settings
            rows = [
                ("shouldBurnAsPayment", asset_config.shouldBurnAsPayment),
                ("shouldTransferToEndaoment", asset_config.shouldTransferToEndaoment),
                ("shouldSwapInStabPools", asset_config.shouldSwapInStabPools),
                ("shouldAuctionInstantly", asset_config.shouldAuctionInstantly),
                ("specialStabPoolId", asset_config.specialStabPoolId if asset_config.specialStabPoolId != 0 else "None"),
            ]
            print_table(f"{asset_name} - Liquidation Settings", ["Parameter", "Value"], rows)

            # Action flags
            whitelist_addr = str(asset_config.whitelist)
            rows = [
                ("canDeposit", asset_config.canDeposit),
                ("canWithdraw", asset_config.canWithdraw),
                ("canRedeemCollateral", asset_config.canRedeemCollateral),
                ("canRedeemInStabPool", asset_config.canRedeemInStabPool),
                ("canBuyInAuction", asset_config.canBuyInAuction),
                ("canClaimInStabPool", asset_config.canClaimInStabPool),
                ("whitelist", format_address(whitelist_addr) if whitelist_addr != "0x0000000000000000000000000000000000000000" else "None"),
                ("isNft", asset_config.isNft),
            ]
            print_table(f"{asset_name} - Action Flags", ["Parameter", "Value"], rows)

            # Custom auction params if set
            if custom_auction.hasParams:
                rows = [
                    ("hasParams", custom_auction.hasParams),
                    ("startDiscount", format_percent(custom_auction.startDiscount)),
                    ("maxDiscount", format_percent(custom_auction.maxDiscount)),
                    ("delay", format_blocks_to_time(custom_auction.delay)),
                    ("duration", format_blocks_to_time(custom_auction.duration)),
                ]
                print_table(f"{asset_name} - Custom Auction Params", ["Parameter", "Value"], rows)


def fetch_ripe_hq_data(hq):
    """Fetch and print RipeHQ registry and minting config with per-contract details."""
    print("\n" + "=" * 80)
    print("\n<a id=\"ripe-hq\"></a>")
    print("# RipeHQ - Main Registry & Minting Config")
    print(f"Address: {RIPE_HQ}")

    # Minting circuit breaker
    rows = [
        ("mintEnabled", hq.mintEnabled()),
    ]
    print_table("Minting Circuit Breaker", ["Parameter", "Value"], rows)

    # Core tokens
    rows = [
        ("greenToken (ID 1)", format_address(hq.greenToken())),
        ("savingsGreen (ID 2)", format_address(hq.savingsGreen())),
        ("ripeToken (ID 3)", format_address(hq.ripeToken())),
    ]
    print_table("Core Token Registry", ["Token", "Address"], rows)

    # Registry info
    try:
        num_addrs = hq.numAddrs()
        registry_timelock = hq.registryChangeTimeLock()
        rows = [
            ("numAddrs", num_addrs),
            ("registryChangeTimeLock", format_blocks_to_time(registry_timelock)),
        ]
        print_table("Registry Config", ["Parameter", "Value"], rows)

        # List all registered addresses with details
        if num_addrs > 1:
            print("\n### All Registered Contracts")
            headers = ["ID", "Description", "Address", "Mint GREEN", "Mint RIPE", "Blacklist", "Paused"]
            rows = []
            for i in range(1, num_addrs):
                try:
                    addr_info = hq.addrInfo(i)
                    contract_addr = str(addr_info.addr)
                    if contract_addr == "0x0000000000000000000000000000000000000000":
                        continue

                    hq_config = hq.hqConfig(i)

                    # Try to get isPaused from the contract
                    is_paused = "-"
                    try:
                        contract = boa.from_etherscan(contract_addr, name=f"Contract{i}")
                        is_paused = contract.isPaused()
                    except:
                        pass

                    rows.append([
                        i,
                        addr_info.description,
                        format_address(contract_addr),
                        "✓" if hq_config.canMintGreen else "-",
                        "✓" if hq_config.canMintRipe else "-",
                        "✓" if hq_config.canSetTokenBlacklist else "-",
                        is_paused,
                    ])
                except Exception:
                    pass

            if rows:
                print(f"| {' | '.join(headers)} |")
                print(f"| {' | '.join(['---' for _ in headers])} |")
                for row in rows:
                    print(f"| {' | '.join(str(cell) for cell in row)} |")
    except Exception as e:
        print(f"*Error fetching registry: {e}*")


def fetch_switchboard_data(sb):
    """Fetch and print Switchboard registry data with per-switchboard details."""
    print("\n" + "=" * 80)
    print("\n<a id=\"switchboard\"></a>")
    print("# Switchboard - Configuration Contracts Registry")
    print(f"Address: {SWITCHBOARD}")

    try:
        num_addrs = sb.numAddrs()
        registry_timelock = sb.registryChangeTimeLock()
        rows = [
            ("numAddrs (switchboards)", num_addrs - 1 if num_addrs > 0 else 0),
            ("registryChangeTimeLock", format_blocks_to_time(registry_timelock)),
        ]
        print_table("Registry Config", ["Parameter", "Value"], rows)

        # List all switchboards with details
        if num_addrs > 1:
            print("\n### Registered Switchboards")
            headers = ["ID", "Description", "Address", "Paused"]
            rows = []
            for i in range(1, num_addrs):
                try:
                    addr_info = sb.addrInfo(i)
                    contract_addr = str(addr_info.addr)
                    if contract_addr == "0x0000000000000000000000000000000000000000":
                        continue

                    # Try to get isPaused
                    is_paused = "-"
                    try:
                        contract = boa.from_etherscan(contract_addr, name=f"Switchboard{i}")
                        is_paused = contract.isPaused()
                    except:
                        pass

                    rows.append([
                        i,
                        addr_info.description,
                        format_address(contract_addr),
                        is_paused,
                    ])
                except Exception:
                    continue

            if rows:
                print(f"| {' | '.join(headers)} |")
                print(f"| {' | '.join(['---' for _ in headers])} |")
                for row in rows:
                    print(f"| {' | '.join(str(cell) for cell in row)} |")

    except Exception as e:
        print(f"*Error fetching Switchboard: {e}*")


def fetch_price_desk_data(pd):
    """Fetch and print PriceDesk registry data."""
    print("\n" + "=" * 80)
    print("\n<a id=\"price-desk\"></a>")
    print("# PriceDesk - Oracle Registry")
    print(f"Address: {PRICE_DESK}")

    try:
        # ETH address
        rows = [
            ("ETH", format_address(pd.ETH())),
        ]
        print_table("Constants", ["Parameter", "Value"], rows)

        # Registry info
        num_addrs = pd.numAddrs()
        registry_timelock = pd.registryChangeTimeLock()
        rows = [
            ("numAddrs (price sources)", num_addrs - 1 if num_addrs > 0 else 0),
            ("registryChangeTimeLock", format_blocks_to_time(registry_timelock)),
        ]
        print_table("Registry Config", ["Parameter", "Value"], rows)

        # List all price sources
        if num_addrs > 1:
            print("\n### Registered Price Sources")
            headers = ["Reg ID", "Description", "Address"]
            rows = []
            for i in range(1, num_addrs):
                try:
                    addr_info = pd.addrInfo(i)
                    if str(addr_info.addr) != "0x0000000000000000000000000000000000000000":
                        rows.append([
                            i,
                            addr_info.description,
                            format_address(str(addr_info.addr)),
                        ])
                except Exception:
                    pass
            if rows:
                print(f"| {' | '.join(headers)} |")
                print(f"| {' | '.join(['---' for _ in headers])} |")
                for row in rows:
                    print(f"| {' | '.join(str(cell) for cell in row)} |")
    except Exception as e:
        print(f"*Error fetching PriceDesk: {e}*")


def fetch_vault_book_data(vb):
    """Fetch and print VaultBook registry data with per-vault details."""
    print("\n" + "=" * 80)
    print("\n<a id=\"vault-book\"></a>")
    print("# VaultBook - Vault Registry")
    print(f"Address: {VAULT_BOOK}")

    try:
        num_addrs = vb.numAddrs()
        registry_timelock = vb.registryChangeTimeLock()
        rows = [
            ("numAddrs (vaults)", num_addrs - 1 if num_addrs > 0 else 0),
            ("registryChangeTimeLock", format_blocks_to_time(registry_timelock)),
        ]
        print_table("Registry Config", ["Parameter", "Value"], rows)

        # List all vaults with detailed info
        if num_addrs > 1:
            for i in range(1, num_addrs):
                try:
                    addr_info = vb.addrInfo(i)
                    vault_addr = str(addr_info.addr)
                    if vault_addr == "0x0000000000000000000000000000000000000000":
                        continue

                    print(f"\n### Vault {i}: {addr_info.description}")
                    print(f"Address: {vault_addr}")

                    # Load vault contract and get details
                    try:
                        vault = boa.from_etherscan(vault_addr, name=f"Vault{i}")

                        vault_rows = []
                        try:
                            is_paused = vault.isPaused()
                            vault_rows.append(("isPaused", is_paused))
                        except AttributeError:
                            pass

                        try:
                            num_assets = vault.numAssets()
                            vault_rows.append(("numAssets", num_assets - 1 if num_assets > 0 else 0))
                        except AttributeError:
                            num_assets = 0

                        if vault_rows:
                            print_table("Vault Status", ["Parameter", "Value"], vault_rows)

                        # Show assets in vault with balances
                        if num_assets > 1:
                            asset_rows = []
                            for j in range(1, num_assets):
                                try:
                                    asset_addr = vault.vaultAssets(j)
                                    if str(asset_addr) == "0x0000000000000000000000000000000000000000":
                                        continue
                                    asset_name = get_token_name(str(asset_addr))
                                    try:
                                        total_bal = vault.totalBalances(asset_addr)
                                        # Try to get decimals
                                        decimals = 18
                                        try:
                                            asset_contract = boa.from_etherscan(str(asset_addr), name=f"Asset{j}")
                                            decimals = asset_contract.decimals()
                                        except:
                                            pass
                                        asset_rows.append([
                                            asset_name,
                                            format_token_amount(total_bal, decimals, "")
                                        ])
                                    except:
                                        asset_rows.append([asset_name, "N/A"])
                                except:
                                    continue

                            if asset_rows:
                                print(f"\n**Assets in Vault ({len(asset_rows)}):**")
                                print("| Asset | Total Balance |")
                                print("| --- | --- |")
                                for row in asset_rows:
                                    print(f"| {row[0]} | {row[1]} |")

                    except Exception as e:
                        print(f"*Could not load vault contract: {e}*")

                except Exception:
                    continue

    except Exception as e:
        print(f"*Error fetching VaultBook: {e}*")


def fetch_ledger_data(ledger):
    """Fetch and print Ledger protocol-wide data."""
    print("\n" + "=" * 80)
    print("\n<a id=\"ledger\"></a>")
    print("# Ledger - Core Protocol Data")
    print(f"Address: {LEDGER}")

    try:
        # Debt statistics
        total_debt = ledger.totalDebt()
        num_borrowers = ledger.numBorrowers()
        unrealized_yield = ledger.unrealizedYield()

        rows = [
            ("totalDebt", format_token_amount(total_debt)),
            ("numBorrowers", num_borrowers - 1 if num_borrowers > 0 else 0),
            ("unrealizedYield", format_token_amount(unrealized_yield)),
        ]
        print_table("Debt Statistics", ["Parameter", "Value"], rows)

        # RIPE Rewards
        ripe_rewards = ledger.ripeRewards()
        ripe_avail = ledger.ripeAvailForRewards()
        rows = [
            ("borrowers allocation", format_token_amount(ripe_rewards.borrowers, 18, "RIPE")),
            ("stakers allocation", format_token_amount(ripe_rewards.stakers, 18, "RIPE")),
            ("voters allocation", format_token_amount(ripe_rewards.voters, 18, "RIPE")),
            ("genDepositors allocation", format_token_amount(ripe_rewards.genDepositors, 18, "RIPE")),
            ("newRipeRewards", format_token_amount(ripe_rewards.newRipeRewards, 18, "RIPE")),
            ("lastUpdate (block)", ripe_rewards.lastUpdate),
            ("ripeAvailForRewards", format_token_amount(ripe_avail, 18, "RIPE")),
        ]
        print_table("RIPE Rewards Pool", ["Parameter", "Value"], rows)

        # Global Deposit Points
        global_points = ledger.globalDepositPoints()
        rows = [
            ("lastUsdValue", f"${global_points.lastUsdValue / DECIMALS_6:,.2f}"),
            ("ripeStakerPoints", global_points.ripeStakerPoints),
            ("ripeVotePoints", global_points.ripeVotePoints),
            ("ripeGenPoints", global_points.ripeGenPoints),
            ("lastUpdate (block)", global_points.lastUpdate),
        ]
        print_table("Global Deposit Points", ["Parameter", "Value"], rows)

        # Global Borrow Points
        borrow_points = ledger.globalBorrowPoints()
        rows = [
            ("lastPrincipal", format_token_amount(borrow_points.lastPrincipal)),
            ("points", borrow_points.points),
            ("lastUpdate (block)", borrow_points.lastUpdate),
        ]
        print_table("Global Borrow Points", ["Parameter", "Value"], rows)

        # Liquidation Statistics
        num_liq_users = ledger.numFungLiqUsers()
        rows = [
            ("numFungLiqUsers (active liquidations)", num_liq_users - 1 if num_liq_users > 0 else 0),
        ]
        print_table("Liquidation Statistics", ["Parameter", "Value"], rows)

        # HR Data
        ripe_avail_hr = ledger.ripeAvailForHr()
        num_contributors = ledger.numContributors()
        rows = [
            ("ripeAvailForHr", format_token_amount(ripe_avail_hr, 18, "RIPE")),
            ("numContributors", num_contributors - 1 if num_contributors > 0 else 0),
        ]
        print_table("Human Resources", ["Parameter", "Value"], rows)

        # Bond/Epoch Data
        epoch_start = ledger.epochStart()
        epoch_end = ledger.epochEnd()
        bad_debt = ledger.badDebt()
        ripe_paid_bad_debt = ledger.ripePaidOutForBadDebt()
        payment_avail = ledger.paymentAmountAvailInEpoch()
        ripe_avail_bonds = ledger.ripeAvailForBonds()
        rows = [
            ("epochStart (block)", epoch_start),
            ("epochEnd (block)", epoch_end),
            ("badDebt", format_token_amount(bad_debt)),
            ("ripePaidOutForBadDebt", format_token_amount(ripe_paid_bad_debt, 18, "RIPE")),
            ("paymentAmountAvailInEpoch", format_token_amount(payment_avail)),
            ("ripeAvailForBonds", format_token_amount(ripe_avail_bonds, 18, "RIPE")),
        ]
        print_table("Bond Epoch Data", ["Parameter", "Value"], rows)

        # Green Pool Debt (Endaoment)
        try:
            green_pool_debt = ledger.greenPoolDebt(GREEN_POOL)
            rows = [
                ("greenPoolDebt (GREEN Pool)", format_token_amount(green_pool_debt)),
            ]
            print_table("Endaoment Pool Debt", ["Parameter", "Value"], rows)
        except Exception:
            pass

    except Exception as e:
        print(f"*Error fetching Ledger: {e}*")


def fetch_credit_engine_data(ce):
    """Fetch and print CreditEngine config."""
    print("\n" + "=" * 80)
    print("\n<a id=\"credit-engine\"></a>")
    print("# CreditEngine - Credit Configuration")
    print(f"Address: {CREDIT_ENGINE}")

    undy_discount = ce.undyVaulDiscount()
    buyback_ratio = ce.buybackRatio()

    rows = [
        ("undyVaultDiscount", format_percent(undy_discount)),
        ("buybackRatio", format_percent(buyback_ratio)),
    ]
    print_table("Credit Engine Config", ["Parameter", "Value"], rows)


def fetch_bond_booster_data(bb):
    """Fetch and print BondBooster config."""
    print("\n" + "=" * 80)
    print("\n<a id=\"bond-booster\"></a>")
    print("# BondBooster - Bond Boost Configuration")
    print(f"Address: {BOND_BOOSTER}")

    try:
        max_boost = bb.maxBoostRatio()
        max_units = bb.maxUnits()
        min_lock = bb.minLockDuration()

        rows = [
            ("maxBoostRatio", format_percent(max_boost)),
            ("maxUnits", max_units),
            ("minLockDuration", format_blocks_to_time(min_lock)),
        ]
        print_table("Bond Booster Global Config", ["Parameter", "Value"], rows)
    except Exception as e:
        print(f"*Error fetching BondBooster: {e}*")


def fetch_lootbox_data(lootbox):
    """Fetch and print Lootbox (RIPE rewards) config."""
    print("\n" + "=" * 80)
    print("\n<a id=\"lootbox\"></a>")
    print("# Lootbox - RIPE Rewards & Underscore Config")
    print(f"Address: {LOOTBOX}")

    has_undy = lootbox.hasUnderscoreRewards()
    send_interval = lootbox.underscoreSendInterval()
    last_send = lootbox.lastUnderscoreSend()
    deposit_rewards = lootbox.undyDepositRewardsAmount()
    yield_bonus = lootbox.undyYieldBonusAmount()

    rows = [
        ("hasUnderscoreRewards", has_undy),
        ("underscoreSendInterval", format_blocks_to_time(send_interval)),
        ("lastUnderscoreSend (block)", last_send),
        ("undyDepositRewardsAmount", format_token_amount(deposit_rewards, 18, "RIPE")),
        ("undyYieldBonusAmount", format_token_amount(yield_bonus, 18, "RIPE")),
    ]
    print_table("Underscore Rewards Config", ["Parameter", "Value"], rows)


def fetch_bond_room_data(bond_room):
    """Fetch and print BondRoom config."""
    print("\n" + "=" * 80)
    print("\n<a id=\"bond-room\"></a>")
    print("# BondRoom - Bond Purchase Configuration")
    print(f"Address: {BOND_ROOM}")

    is_paused = bond_room.isPaused()
    booster_addr = bond_room.bondBooster()

    rows = [
        ("isPaused", is_paused),
        ("bondBooster", format_address(str(booster_addr))),
    ]
    print_table("Bond Room Config", ["Parameter", "Value"], rows)


def fetch_ripe_gov_vault_data(ripe_gov):
    """Fetch and print RipeGov vault data."""
    print("\n" + "=" * 80)
    print("\n<a id=\"ripe-gov-vault\"></a>")
    print("# Ripe Gov Vault - Governance Staking")
    print(f"Address: {RIPE_GOV_VAULT}")

    is_paused = ripe_gov.isPaused()
    total_points = ripe_gov.totalGovPoints()

    rows = [
        ("isPaused", is_paused),
        ("totalGovPoints", f"{total_points:,}"),
    ]
    print_table("Governance Vault Stats", ["Parameter", "Value"], rows)


def fetch_price_source_configs(pd):
    """Fetch and print price source configurations with per-asset details."""
    print("\n" + "=" * 80)
    print("\n<a id=\"price-sources\"></a>")
    print("# Price Source Configurations")

    try:
        num_addrs = pd.numAddrs()
        if num_addrs <= 1:
            print("*No price sources configured*")
            return

        for i in range(1, num_addrs):
            try:
                addr_info = pd.addrInfo(i)
                if str(addr_info.addr) == "0x0000000000000000000000000000000000000000":
                    continue

                source_addr = str(addr_info.addr)
                source_name = addr_info.description

                print(f"\n## {source_name}")
                print(f"Address: {source_addr}")

                # Try to load the price source and get its config
                try:
                    source = boa.from_etherscan(source_addr, name=f"PriceSource{i}")

                    # Global config
                    rows = []
                    try:
                        is_paused = source.isPaused()
                        rows.append(("isPaused", is_paused))
                    except AttributeError:
                        pass

                    try:
                        max_conf = source.maxConfidenceRatio()
                        rows.append(("maxConfidenceRatio", format_percent(max_conf)))
                    except AttributeError:
                        pass

                    try:
                        num_assets = source.numAssets()
                        rows.append(("numAssets", num_assets - 1 if num_assets > 0 else 0))
                    except AttributeError:
                        num_assets = 0

                    if rows:
                        print_table(f"{source_name} Global Config", ["Parameter", "Value"], rows)

                    # Per-asset configurations
                    if num_assets > 1:
                        _fetch_price_source_assets(source, source_name, num_assets)

                except Exception as e:
                    print(f"*Could not load contract: {e}*")

            except Exception:
                continue

    except Exception as e:
        print(f"*Error fetching price sources: {e}*")


def _fetch_price_source_assets(source, source_name, num_assets):
    """Fetch per-asset config for a price source."""
    asset_rows = []

    for j in range(1, num_assets):
        try:
            asset_addr = source.assets(j)
            if str(asset_addr) == "0x0000000000000000000000000000000000000000":
                continue

            asset_name = get_token_name(str(asset_addr))

            # Try to get feedConfig (Chainlink style)
            try:
                config = source.feedConfig(asset_addr)
                # Chainlink: feed, decimals, needsEthToUsd, needsBtcToUsd, staleTime
                if hasattr(config, 'feed'):
                    feed_addr = format_address(str(config.feed)) if str(config.feed) != "0x0000000000000000000000000000000000000000" else "N/A"
                    needs_eth = getattr(config, 'needsEthToUsd', False)
                    needs_btc = getattr(config, 'needsBtcToUsd', False)
                    stale = getattr(config, 'staleTime', 0)
                    asset_rows.append([
                        asset_name,
                        feed_addr,
                        f"ETH:{needs_eth}, BTC:{needs_btc}",
                        f"{stale}s" if stale > 0 else "default"
                    ])
                # Pyth: feedId, staleTime
                elif hasattr(config, 'feedId'):
                    feed_id = config.feedId.hex() if config.feedId else "N/A"
                    stale = getattr(config, 'staleTime', 0)
                    asset_rows.append([
                        asset_name,
                        f"0x{feed_id[:8]}...{feed_id[-8:]}" if len(feed_id) > 16 else feed_id,
                        "-",
                        f"{stale}s" if stale > 0 else "default"
                    ])
                continue
            except AttributeError:
                pass

            # Try priceConfigs (BlueChipYield / UndyVault style)
            try:
                config = source.priceConfigs(asset_addr)
                if hasattr(config, 'underlyingAsset'):
                    underlying = get_token_name(str(config.underlyingAsset))
                    protocol_id = getattr(config, 'protocol', 0)
                    protocol_name = PROTOCOL_NAMES.get(protocol_id, f"ID:{protocol_id}")
                    stale = getattr(config, 'staleTime', 0)
                    max_snapshots = getattr(config, 'maxNumSnapshots', 0)
                    asset_rows.append([
                        asset_name,
                        underlying,
                        f"{protocol_name}, snaps:{max_snapshots}",
                        f"{stale}s" if stale > 0 else "default"
                    ])
                continue
            except AttributeError:
                pass

            # Try curveConfig (Curve style)
            try:
                config = source.curveConfig(asset_addr)
                if config:
                    asset_rows.append([
                        asset_name,
                        "Curve Pool",
                        "-",
                        "-"
                    ])
                continue
            except AttributeError:
                pass

            # Fallback - just show asset is registered
            asset_rows.append([asset_name, "Configured", "-", "-"])

        except Exception:
            continue

    if asset_rows:
        headers = ["Asset", "Feed/Underlying", "Config", "StaleTime"]
        print(f"\n### {source_name} - Registered Assets ({len(asset_rows)})")
        print(f"| {' | '.join(headers)} |")
        print(f"| {' | '.join(['---' for _ in headers])} |")
        for row in asset_rows:
            print(f"| {' | '.join(str(cell) for cell in row)} |")


def fetch_stability_pool_data(stab_pool):
    """Fetch and print StabilityPool data."""
    print("\n" + "=" * 80)
    print("\n<a id=\"stability-pool\"></a>")
    print("# Stability Pool - Liquidation Buffer")
    print(f"Address: {STABILITY_POOL}")

    is_paused = stab_pool.isPaused()
    num_assets = stab_pool.numAssets()

    rows = [
        ("isPaused", is_paused),
        ("numAssets", num_assets - 1 if num_assets > 0 else 0),
    ]
    print_table("Stability Pool Config", ["Parameter", "Value"], rows)


def fetch_auction_house_data(auction_house):
    """Fetch and print AuctionHouse data."""
    print("\n" + "=" * 80)
    print("\n<a id=\"auction-house\"></a>")
    print("# Auction House - Liquidation Auctions")
    print(f"Address: {AUCTION_HOUSE}")

    is_paused = auction_house.isPaused()

    rows = [
        ("isPaused", is_paused),
    ]
    print_table("Auction House Status", ["Parameter", "Value"], rows)


def fetch_teller_data(teller):
    """Fetch and print Teller data."""
    print("\n" + "=" * 80)
    print("\n<a id=\"teller\"></a>")
    print("# Teller - User Interaction Gateway")
    print(f"Address: {TELLER}")

    is_paused = teller.isPaused()

    rows = [
        ("isPaused", is_paused),
    ]
    print_table("Teller Status", ["Parameter", "Value"], rows)


def fetch_deleverage_data(deleverage):
    """Fetch and print Deleverage data."""
    print("\n" + "=" * 80)
    print("\n<a id=\"deleverage\"></a>")
    print("# Deleverage - Deleverage Engine")
    print(f"Address: {DELEVERAGE}")

    is_paused = deleverage.isPaused()

    rows = [
        ("isPaused", is_paused),
    ]
    print_table("Deleverage Status", ["Parameter", "Value"], rows)


def fetch_credit_redeem_data(credit_redeem):
    """Fetch and print CreditRedeem data."""
    print("\n" + "=" * 80)
    print("\n<a id=\"credit-redeem\"></a>")
    print("# Credit Redeem - Redemptions Engine")
    print(f"Address: {CREDIT_REDEEM}")

    is_paused = credit_redeem.isPaused()

    rows = [
        ("isPaused", is_paused),
    ]
    print_table("Credit Redeem Status", ["Parameter", "Value"], rows)


def fetch_endaoment_data(endaoment):
    """Fetch and print Endaoment (main treasury) data."""
    print("\n" + "=" * 80)
    print("\n<a id=\"endaoment\"></a>")
    print("# Endaoment - Treasury & GREEN Stabilization")
    print(f"Address: {ENDAOMENT}")

    is_paused = endaoment.isPaused()
    weth = endaoment.WETH()

    rows = [
        ("isPaused", is_paused),
        ("WETH", format_address(str(weth))),
    ]
    print_table("Endaoment Status", ["Parameter", "Value"], rows)


def fetch_human_resources_data(hr):
    """Fetch and print HumanResources data."""
    print("\n" + "=" * 80)
    print("\n<a id=\"human-resources\"></a>")
    print("# Human Resources - Contributor Management")
    print(f"Address: {HUMAN_RESOURCES}")

    is_paused = hr.isPaused()

    rows = [
        ("isPaused", is_paused),
    ]
    print_table("Human Resources Status", ["Parameter", "Value"], rows)
    print("\n*Note: numContributors is tracked in Ledger contract*")


def fetch_endaoment_psm_data():
    """Fetch and print Endaoment PSM (Peg Stability Module) config."""
    print("\n" + "=" * 80)
    print("\n<a id=\"endaoment-psm\"></a>")
    print("# Endaoment PSM - Peg Stability Module")

    # Try to find PSM address dynamically, fall back to Endaoment
    psm_address = ENDAOMENT_PSM if ENDAOMENT_PSM else ENDAOMENT
    print(f"Address: {psm_address}")

    try:
        psm = boa.from_etherscan(psm_address, name="EndaomentPSM")

        # Mint config
        mint_rows = []
        try:
            can_mint = psm.canMint()
            mint_rows.append(("canMint", "✅ Enabled" if can_mint else "❌ Disabled"))
        except AttributeError:
            pass

        try:
            mint_fee = psm.mintFee()
            mint_rows.append(("mintFee", format_percent(mint_fee)))
        except AttributeError:
            pass

        try:
            max_interval_mint = psm.maxIntervalMint()
            mint_rows.append(("maxIntervalMint", format_token_amount(max_interval_mint)))
        except AttributeError:
            pass

        try:
            enforce_allowlist = psm.shouldEnforceMintAllowlist()
            mint_rows.append(("shouldEnforceMintAllowlist", enforce_allowlist))
        except AttributeError:
            pass

        if mint_rows:
            print_table("PSM Mint Configuration", ["Parameter", "Value"], mint_rows)

        # Redeem config
        redeem_rows = []
        try:
            can_redeem = psm.canRedeem()
            redeem_rows.append(("canRedeem", "✅ Enabled" if can_redeem else "❌ Disabled"))
        except AttributeError:
            pass

        try:
            redeem_fee = psm.redeemFee()
            redeem_rows.append(("redeemFee", format_percent(redeem_fee)))
        except AttributeError:
            pass

        try:
            max_interval_redeem = psm.maxIntervalRedeem()
            redeem_rows.append(("maxIntervalRedeem", format_token_amount(max_interval_redeem)))
        except AttributeError:
            pass

        try:
            enforce_redeem_allowlist = psm.shouldEnforceRedeemAllowlist()
            redeem_rows.append(("shouldEnforceRedeemAllowlist", enforce_redeem_allowlist))
        except AttributeError:
            pass

        if redeem_rows:
            print_table("PSM Redeem Configuration", ["Parameter", "Value"], redeem_rows)

        # Interval config
        interval_rows = []
        try:
            num_blocks_per_interval = psm.numBlocksPerInterval()
            interval_rows.append(("numBlocksPerInterval", format_blocks_to_time(num_blocks_per_interval)))
        except AttributeError:
            pass

        try:
            should_auto_deposit = psm.shouldAutoDeposit()
            interval_rows.append(("shouldAutoDeposit", should_auto_deposit))
        except AttributeError:
            pass

        try:
            usdc_yield_position = psm.usdcYieldPosition()
            if hasattr(usdc_yield_position, 'legoId'):
                interval_rows.append(("usdcYieldPosition.legoId", usdc_yield_position.legoId))
                interval_rows.append(("usdcYieldPosition.vaultToken", format_address(str(usdc_yield_position.vaultToken))))
        except AttributeError:
            pass

        if interval_rows:
            print_table("PSM Interval & Yield Configuration", ["Parameter", "Value"], interval_rows)

        # Current interval stats
        stats_rows = []
        try:
            global_mint_interval = psm.globalMintInterval()
            if hasattr(global_mint_interval, 'startBlock'):
                stats_rows.append(("Mint Interval Start", global_mint_interval.startBlock))
                stats_rows.append(("Mint Interval Amount", format_token_amount(global_mint_interval.amount)))
        except AttributeError:
            pass

        try:
            global_redeem_interval = psm.globalRedeemInterval()
            if hasattr(global_redeem_interval, 'startBlock'):
                stats_rows.append(("Redeem Interval Start", global_redeem_interval.startBlock))
                stats_rows.append(("Redeem Interval Amount", format_token_amount(global_redeem_interval.amount)))
        except AttributeError:
            pass

        if stats_rows:
            print_table("PSM Current Interval Stats", ["Parameter", "Value"], stats_rows)

        # USDC info
        try:
            usdc_addr = psm.USDC()
            print(f"\n**USDC Address:** {format_address(str(usdc_addr))}")
        except AttributeError:
            pass

    except Exception as e:
        print(f"*Error fetching PSM data: {e}*")
        print("*Note: PSM contract may not be deployed or verified yet*")


def fetch_token_data():
    """Fetch and print token supply data with savings rate calculation."""
    print("\n" + "=" * 80)
    print("\n<a id=\"token-statistics\"></a>")
    print("# Token Statistics")

    try:
        # GREEN Token
        green = boa.from_etherscan(GREEN_TOKEN, name="GreenToken")
        green_supply = green.totalSupply()
        rows = [
            ("totalSupply", format_token_amount(green_supply)),
            ("decimals", green.decimals()),
            ("name", green.name()),
            ("symbol", green.symbol()),
        ]
        print_table("GREEN Token", ["Parameter", "Value"], rows)
    except Exception as e:
        print(f"\n## GREEN Token")
        print(f"*Error fetching: {e}*")

    try:
        # RIPE Token
        ripe = boa.from_etherscan(RIPE_TOKEN, name="RipeToken")
        ripe_supply = ripe.totalSupply()
        rows = [
            ("totalSupply", format_token_amount(ripe_supply, 18, "RIPE")),
            ("decimals", ripe.decimals()),
            ("name", ripe.name()),
            ("symbol", ripe.symbol()),
        ]
        print_table("RIPE Token", ["Parameter", "Value"], rows)
    except Exception as e:
        print(f"\n## RIPE Token")
        print(f"*Error fetching: {e}*")

    try:
        # Savings GREEN (sGREEN) with exchange rate and savings yield
        sgreen = boa.from_etherscan(SAVINGS_GREEN, name="SavingsGreen")
        sgreen_supply = sgreen.totalSupply()
        sgreen_assets = sgreen.totalAssets()

        # Calculate exchange rate and effective yield
        exchange_rate = sgreen_assets / sgreen_supply if sgreen_supply > 0 else 1
        accumulated_yield = (exchange_rate - 1) * 100  # How much above 1:1

        rows = [
            ("totalSupply (shares)", format_token_amount(sgreen_supply)),
            ("totalAssets (GREEN)", format_token_amount(sgreen_assets)),
            ("**Exchange Rate**", f"**{exchange_rate:.6f} GREEN per sGREEN**"),
            ("**Accumulated Yield**", f"**{accumulated_yield:+.4f}%** above 1:1"),
            ("decimals", sgreen.decimals()),
            ("name", sgreen.name()),
            ("symbol", sgreen.symbol()),
        ]
        print_table("Savings GREEN (sGREEN)", ["Parameter", "Value"], rows)

        # Show what 1000 sGREEN would be worth
        print(f"\n*Example: 1,000 sGREEN = {1000 * exchange_rate:,.4f} GREEN*")

    except Exception as e:
        print(f"\n## Savings GREEN")
        print(f"*Error fetching: {e}*")


def main():
    """Main entry point."""
    print("Connecting to Base mainnet via Alchemy...")

    # Set etherscan API for contract loading
    boa.set_etherscan(
        api_key=os.environ["ETHERSCAN_API_KEY"],
        uri="https://api.etherscan.io/v2/api?chainid=8453"
    )

    # Fork at latest block (no block_identifier)
    with boa.fork(RPC_URL):
        block_number = boa.env.evm.patch.block_number
        print(f"Connected. Block: {block_number}\n")

        # Load contracts from Etherscan
        print("Loading contracts from Etherscan...")
        mc = boa.from_etherscan(MISSION_CONTROL, name="MissionControl")
        hq = boa.from_etherscan(RIPE_HQ, name="RipeHQ")
        sb = boa.from_etherscan(SWITCHBOARD, name="Switchboard")
        pd = boa.from_etherscan(PRICE_DESK, name="PriceDesk")
        vb = boa.from_etherscan(VAULT_BOOK, name="VaultBook")
        ledger = boa.from_etherscan(LEDGER, name="Ledger")
        ce = boa.from_etherscan(CREDIT_ENGINE, name="CreditEngine")
        bb = boa.from_etherscan(BOND_BOOSTER, name="BondBooster")
        lootbox = boa.from_etherscan(LOOTBOX, name="Lootbox")
        bond_room = boa.from_etherscan(BOND_ROOM, name="BondRoom")
        ripe_gov = boa.from_etherscan(RIPE_GOV_VAULT, name="RipeGovVault")
        stab_pool = boa.from_etherscan(STABILITY_POOL, name="StabilityPool")

        # Core lending contracts
        auction_house = boa.from_etherscan(AUCTION_HOUSE, name="AuctionHouse")
        teller = boa.from_etherscan(TELLER, name="Teller")
        deleverage = boa.from_etherscan(DELEVERAGE, name="Deleverage")
        credit_redeem = boa.from_etherscan(CREDIT_REDEEM, name="CreditRedeem")

        # Treasury contracts
        endaoment = boa.from_etherscan(ENDAOMENT, name="Endaoment")
        hr = boa.from_etherscan(HUMAN_RESOURCES, name="HumanResources")

        # Load token contracts for executive summary
        green = boa.from_etherscan(GREEN_TOKEN, name="GreenToken")
        sgreen = boa.from_etherscan(SAVINGS_GREEN, name="SavingsGreen")
        ripe = boa.from_etherscan(RIPE_TOKEN, name="RipeToken")

        print("Fetching configuration data...\n")
        print("=" * 80)

        # Header
        print("# Ripe Protocol Production Parameters")
        print(f"\n**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"**Block:** {block_number}")
        print(f"**Network:** Base Mainnet")

        # Table of Contents
        print_table_of_contents()

        # Executive Summary
        print_executive_summary(mc, ledger, green, sgreen, ripe)

        print("\n" + "=" * 80)

        # Fetch and display all data
        fetch_mission_control_data(mc)
        fetch_ripe_hq_data(hq)
        fetch_switchboard_data(sb)
        fetch_price_desk_data(pd)
        fetch_vault_book_data(vb)
        fetch_ledger_data(ledger)

        # Endaoment PSM
        fetch_endaoment_psm_data()

        # Core Lending Contracts
        print("\n" + "=" * 80)
        print("\n<a id=\"core-lending\"></a>")
        print("# Core Lending Contracts")

        fetch_credit_engine_data(ce)
        fetch_auction_house_data(auction_house)
        fetch_teller_data(teller)
        fetch_deleverage_data(deleverage)
        fetch_credit_redeem_data(credit_redeem)
        fetch_stability_pool_data(stab_pool)

        # Treasury & Rewards Contracts
        print("\n" + "=" * 80)
        print("\n<a id=\"treasury-rewards\"></a>")
        print("# Treasury & Rewards Contracts")

        fetch_endaoment_data(endaoment)
        fetch_bond_booster_data(bb)
        fetch_lootbox_data(lootbox)
        fetch_bond_room_data(bond_room)
        fetch_human_resources_data(hr)

        # Governance Contracts
        print("\n" + "=" * 80)
        print("\n<a id=\"governance\"></a>")
        print("# Governance Contracts")

        fetch_ripe_gov_vault_data(ripe_gov)

        # Price Sources
        fetch_price_source_configs(pd)

        # Token Statistics
        fetch_token_data()

        print("\n" + "=" * 80)
        print("\n---")
        print(f"*Report generated at block {block_number} on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC*")


if __name__ == "__main__":
    main()
