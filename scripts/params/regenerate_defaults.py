#!/usr/bin/env python3
"""
Regenerate DefaultsBase.vy from Live MissionControl Parameters

This script reads current production parameters from MissionControl on Base mainnet
and generates a new DefaultsBase.vy file that can be used for MissionControl redeployment.

This is a safety measure to preserve all current params when redeploying MissionControl.

Usage:
    python scripts/params/regenerate_defaults.py
"""

import os
import sys
import time

import boa

# Import shared utilities
from params_utils import (
    RIPE_HQ,
    RPC_DELAY,
    MISSION_CONTROL_ID,
    RIPE_TOKEN_ID,
    setup_boa_etherscan,
    boa_fork_context,
)

# ============================================================================
# CONSTANTS FOR VYPER VALUE FORMATTING
# ============================================================================

EIGHTEEN_DECIMALS = 10 ** 18
HUNDRED_PERCENT = 10_000
HOUR_IN_BLOCKS = 1_800  # ~2 second blocks
DAY_IN_BLOCKS = 24 * HOUR_IN_BLOCKS  # 43_200
WEEK_IN_BLOCKS = 7 * DAY_IN_BLOCKS
MONTH_IN_BLOCKS = 30 * DAY_IN_BLOCKS
YEAR_IN_BLOCKS = 365 * DAY_IN_BLOCKS

DAY_IN_SECONDS = 60 * 60 * 24
WEEK_IN_SECONDS = 7 * DAY_IN_SECONDS
MONTH_IN_SECONDS = 30 * DAY_IN_SECONDS
YEAR_IN_SECONDS = 365 * DAY_IN_SECONDS

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

# Minimal ERC20 ABI for symbol()
ERC20_ABI = """
[
    {"name": "symbol", "type": "function", "stateMutability": "view", "inputs": [], "outputs": [{"type": "string"}]}
]
"""

# Minimal VaultBook ABI for addrInfo()
VAULT_BOOK_ABI = """
[
    {"name": "addrInfo", "type": "function", "stateMutability": "view", "inputs": [{"name": "arg0", "type": "uint256"}], "outputs": [{"name": "", "type": "tuple", "components": [{"name": "addr", "type": "address"}, {"name": "version", "type": "uint256"}, {"name": "lastModified", "type": "uint256"}, {"name": "description", "type": "string"}]}]}
]
"""

# Minimal Vault ABI for getTotalAmountForVault()
VAULT_ABI = """
[
    {"name": "getTotalAmountForVault", "type": "function", "stateMutability": "view", "inputs": [{"name": "_asset", "type": "address"}], "outputs": [{"name": "", "type": "uint256"}]}
]
"""

# Minimal PriceDesk ABI for getPrice() and getUsdValue()
PRICE_DESK_ABI = """
[
    {"name": "getPrice", "type": "function", "stateMutability": "view", "inputs": [{"name": "_asset", "type": "address"}], "outputs": [{"name": "", "type": "uint256"}]},
    {"name": "getUsdValue", "type": "function", "stateMutability": "view", "inputs": [{"name": "_asset", "type": "address"}, {"name": "_amount", "type": "uint256"}, {"name": "_shouldRaise", "type": "bool"}], "outputs": [{"name": "", "type": "uint256"}]}
]
"""

# Minimal ERC20 ABI for decimals()
ERC20_DECIMALS_ABI = """
[
    {"name": "decimals", "type": "function", "stateMutability": "view", "inputs": [], "outputs": [{"name": "", "type": "uint8"}]}
]
"""

# Registry IDs
VAULT_BOOK_ID = 8
PRICE_DESK_ID = 7


# ============================================================================
# TOKEN HELPERS
# ============================================================================


def get_token_symbol(addr: str) -> str:
    """Fetch ERC20 token symbol for an address."""
    try:
        token = boa.loads_abi(ERC20_ABI, name="ERC20").at(addr)
        time.sleep(RPC_DELAY)
        return token.symbol()
    except Exception:
        return "???"


def get_token_decimals(addr: str) -> int:
    """Fetch ERC20 token decimals for an address."""
    try:
        token = boa.loads_abi(ERC20_DECIMALS_ABI, name="ERC20").at(addr)
        time.sleep(RPC_DELAY)
        return token.decimals()
    except Exception:
        return 18  # Default to 18


# ============================================================================
# VAULT BALANCE HELPER
# ============================================================================

# Cache for vault addresses
_vault_addr_cache = {}


def get_vault_address(vault_book, vault_id: int) -> str:
    """Get vault contract address from vault ID."""
    if vault_id in _vault_addr_cache:
        return _vault_addr_cache[vault_id]
    try:
        time.sleep(RPC_DELAY)
        info = vault_book.addrInfo(vault_id)
        addr = str(info[0])  # addr is first element of tuple
        _vault_addr_cache[vault_id] = addr
        return addr
    except Exception:
        return ZERO_ADDRESS


def get_asset_total_balance(vault_book, asset_addr: str, vault_ids: list) -> int:
    """Get total balance of an asset across all its vaults."""
    total = 0
    for vault_id in vault_ids:
        if vault_id == 0:
            continue
        vault_addr = get_vault_address(vault_book, vault_id)
        if vault_addr == ZERO_ADDRESS:
            continue
        try:
            vault = boa.loads_abi(VAULT_ABI, name="Vault").at(vault_addr)
            time.sleep(RPC_DELAY)
            balance = vault.getTotalAmountForVault(asset_addr)
            total += balance
        except Exception:
            pass
    return total


# ============================================================================
# VALUE FORMATTING HELPERS
# ============================================================================


def format_vyper_uint(value: int, context: str = "") -> str:
    """Convert integer to Vyper-friendly format using constants where possible.

    Args:
        value: The integer value to format
        context: Hint about the field (e.g., 'blocks', 'seconds', 'percent', 'amount')
    """
    if value == 0:
        return "0"

    # Check for clean multiples of EIGHTEEN_DECIMALS (token amounts)
    if value >= EIGHTEEN_DECIMALS and value % EIGHTEEN_DECIMALS == 0:
        multiplier = value // EIGHTEEN_DECIMALS
        if multiplier == 1:
            return "1 * EIGHTEEN_DECIMALS"
        return f"{multiplier:_} * EIGHTEEN_DECIMALS".replace(",", "_")

    # Check for clean multiples of 10^6 (USDC-like amounts)
    # Only apply this for smaller values that are clearly 6-decimal tokens (not 18-decimal partial amounts)
    # Max reasonable 6-decimal amount: 10 billion tokens = 10^10 * 10^6 = 10^16
    if context == "amount6" and value >= 10**6 and value % (10**6) == 0:
        multiplier = value // (10**6)
        return f"{multiplier} * (10 ** 6)"

    # Check for block-based time durations
    if context in ("blocks", "duration", "interval", "delay"):
        # Check year first (largest)
        if value >= YEAR_IN_BLOCKS and value % YEAR_IN_BLOCKS == 0:
            years = value // YEAR_IN_BLOCKS
            return f"{years} * YEAR_IN_BLOCKS"
        # Then month
        if value >= MONTH_IN_BLOCKS and value % MONTH_IN_BLOCKS == 0:
            months = value // MONTH_IN_BLOCKS
            return f"{months} * MONTH_IN_BLOCKS"
        # Then week
        if value >= WEEK_IN_BLOCKS and value % WEEK_IN_BLOCKS == 0:
            weeks = value // WEEK_IN_BLOCKS
            return f"{weeks} * WEEK_IN_BLOCKS"
        # Then day
        if value >= DAY_IN_BLOCKS and value % DAY_IN_BLOCKS == 0:
            days = value // DAY_IN_BLOCKS
            return f"{days} * DAY_IN_BLOCKS"
        # Then hour
        if value >= HOUR_IN_BLOCKS and value % HOUR_IN_BLOCKS == 0:
            hours = value // HOUR_IN_BLOCKS
            return f"{hours} * HOUR_IN_BLOCKS"

    # Check for second-based time durations
    if context in ("seconds", "cliff", "vesting", "startDelay"):
        # Check year first (largest)
        if value >= YEAR_IN_SECONDS and value % YEAR_IN_SECONDS == 0:
            years = value // YEAR_IN_SECONDS
            return f"{years} * YEAR_IN_SECONDS"
        # Then month
        if value >= MONTH_IN_SECONDS and value % MONTH_IN_SECONDS == 0:
            months = value // MONTH_IN_SECONDS
            return f"{months} * MONTH_IN_SECONDS"
        # Then week
        if value >= WEEK_IN_SECONDS and value % WEEK_IN_SECONDS == 0:
            weeks = value // WEEK_IN_SECONDS
            return f"{weeks} * WEEK_IN_SECONDS"
        # Then day
        if value >= DAY_IN_SECONDS and value % DAY_IN_SECONDS == 0:
            days = value // DAY_IN_SECONDS
            return f"{days} * DAY_IN_SECONDS"

    # Check for percentage values (format as XX_YY for readability)
    if context in ("percent", "rate", "ratio", "alloc", "boost", "fee"):
        # Clean multiples of HUNDRED_PERCENT use the constant
        if value >= HUNDRED_PERCENT and value % HUNDRED_PERCENT == 0:
            multiplier = value // HUNDRED_PERCENT
            return f"{multiplier} * HUNDRED_PERCENT"
        if value == HUNDRED_PERCENT:
            return "HUNDRED_PERCENT"
        # For other percentage values, format with underscore before last 2 digits
        # e.g., 5000 -> 50_00, 1000 -> 10_00, 100 -> 1_00, 8000 -> 80_00
        if value >= 100:
            whole_part = value // 100
            decimal_part = value % 100
            return f"{whole_part}_{decimal_part:02d}"

    # For large values, try to express as X * 10**Y for readability
    if value >= 10**9:
        # Find the largest power of 10 that divides evenly
        for exp in range(17, 5, -1):  # Check from 10^17 down to 10^6
            power = 10 ** exp
            if value % power == 0:
                multiplier = value // power
                # Only use this format if multiplier is reasonably small
                if multiplier <= 1000:
                    return f"{multiplier} * 10**{exp}"
                break

    # Raw value with underscores for readability (for values >= 1000)
    if value >= 1000:
        return f"{value:_}".replace(",", "_")

    return str(value)


def format_vyper_bool(value: bool) -> str:
    """Convert boolean to Vyper format."""
    return "True" if value else "False"


def format_vyper_address(addr: str) -> str:
    """Convert address to Vyper format."""
    # Normalize address
    addr_str = str(addr).lower()
    if addr_str == ZERO_ADDRESS.lower() or addr_str == "0x" + "0" * 40:
        return "empty(address)"
    # In Vyper, addresses are written without quotes
    return str(addr)


# ============================================================================
# VYPER CODE GENERATION
# ============================================================================


def calc_usd_value(amount: int, price: int, decimals: int) -> float:
    """Calculate USD value from amount and price.

    Args:
        amount: Token amount in native decimals
        price: Price in 18 decimals (from PriceDesk.getPrice)
        decimals: Token decimals
    """
    if amount == 0 or price == 0:
        return 0.0
    # USD = amount * price / 10^decimals / 10^18
    return (amount * price) / (10 ** (decimals + 18))


def generate_asset_config_inline(config: tuple, price: int = 0, decimals: int = 18) -> str:
    """Generate inline Vyper code for a single AssetConfig (for if/elif return).

    If price is provided, adds USD value comments to deposit limits.
    """
    vault_ids = list(config[0])
    debt_terms = config[6]
    custom_auction = config[18]

    # Format vault IDs as a list
    vault_ids_str = ", ".join(str(v) for v in vault_ids) if vault_ids else ""

    # Calculate USD values for deposit limits if price is available
    per_user_usd_comment = ""
    global_usd_comment = ""
    min_balance_usd_comment = ""
    if price > 0:
        per_user_usd = calc_usd_value(config[3], price, decimals)
        global_usd = calc_usd_value(config[4], price, decimals)
        min_balance_usd = calc_usd_value(config[5], price, decimals)
        per_user_usd_comment = f"  # {format_usd_value(per_user_usd)}"
        global_usd_comment = f"  # {format_usd_value(global_usd)}"
        min_balance_usd_comment = f"  # {format_usd_value(min_balance_usd, high_precision=True)}"

    return f'''cs.AssetConfig(
            vaultIds=[{vault_ids_str}],
            stakersPointsAlloc={format_vyper_uint(config[1], "alloc")},
            voterPointsAlloc={format_vyper_uint(config[2], "alloc")},
            perUserDepositLimit={format_vyper_uint(config[3], "amount")},{per_user_usd_comment}
            globalDepositLimit={format_vyper_uint(config[4], "amount")},{global_usd_comment}
            minDepositBalance={format_vyper_uint(config[5], "amount")},{min_balance_usd_comment}
            debtTerms=cs.DebtTerms(
                ltv={format_vyper_uint(debt_terms[0], "percent")},
                redemptionThreshold={format_vyper_uint(debt_terms[1], "percent")},
                liqThreshold={format_vyper_uint(debt_terms[2], "percent")},
                liqFee={format_vyper_uint(debt_terms[3], "percent")},
                borrowRate={format_vyper_uint(debt_terms[4], "percent")},
                daowry={format_vyper_uint(debt_terms[5], "percent")},
            ),
            shouldBurnAsPayment={format_vyper_bool(config[7])},
            shouldTransferToEndaoment={format_vyper_bool(config[8])},
            shouldSwapInStabPools={format_vyper_bool(config[9])},
            shouldAuctionInstantly={format_vyper_bool(config[10])},
            canDeposit={format_vyper_bool(config[11])},
            canWithdraw={format_vyper_bool(config[12])},
            canRedeemCollateral={format_vyper_bool(config[13])},
            canRedeemInStabPool={format_vyper_bool(config[14])},
            canBuyInAuction={format_vyper_bool(config[15])},
            canClaimInStabPool={format_vyper_bool(config[16])},
            specialStabPoolId={config[17]},
            customAuctionParams=cs.AuctionParams(
                hasParams={format_vyper_bool(custom_auction[0])},
                startDiscount={format_vyper_uint(custom_auction[1], "percent")},
                maxDiscount={format_vyper_uint(custom_auction[2], "percent")},
                delay={format_vyper_uint(custom_auction[3], "blocks")},
                duration={format_vyper_uint(custom_auction[4], "blocks")},
            ),
            whitelist={format_vyper_address(str(config[19]))},
            isNft={format_vyper_bool(config[20])},
        )'''


def format_usd_value(usd_value: float, high_precision: bool = False) -> str:
    """Format USD value for display (e.g., $1.2M, $500k, $1.5k).

    Args:
        usd_value: The USD value to format
        high_precision: If True, show more decimals for small values (useful for minDepositBalance)
    """
    if usd_value >= 1_000_000:
        return f"${usd_value / 1_000_000:.1f}M"
    elif usd_value >= 1_000:
        return f"${usd_value / 1_000:.1f}k"
    elif usd_value >= 1:
        return f"${usd_value:.2f}"
    elif high_precision:
        # For very small values, show more precision
        if usd_value >= 0.01:
            return f"${usd_value:.4f}"
        elif usd_value >= 0.0001:
            return f"${usd_value:.6f}"
        elif usd_value > 0:
            return f"${usd_value:.8f}"
        else:
            return "$0"
    else:
        return f"${usd_value:.2f}"


def generate_asset_configs_vyper(asset_configs: list) -> str:
    """Generate assetConfigs() function returning DynArray of AssetConfigEntry.

    asset_configs: list of (address, config, symbol, usd_value, price, decimals) tuples
    """
    # Generate each entry with comments
    entries = []
    for addr, config, symbol, usd_value, price, decimals in asset_configs:
        config_code = generate_asset_config_inline(config, price=price, decimals=decimals)
        usd_str = format_usd_value(usd_value)
        # Add comment header before each entry
        entry = f"""        # {symbol}
        # USD Value: {usd_str}
        cs.AssetConfigEntry(asset={addr}, config={config_code}),"""
        entries.append(entry)

    entries_code = "\n".join(entries)

    return f'''
# asset configs


@view
@external
def assetConfigs() -> DynArray[cs.AssetConfigEntry, 100]:
    return [
{entries_code}
    ]
'''


def generate_priority_lists_vyper(
    priority_liq_vaults: list,
    priority_stab_vaults: list,
    priority_price_source_ids: list,
    symbol_map: dict,
) -> str:
    """Generate priority lists Vyper code.

    symbol_map: dict mapping address -> symbol
    """

    # Priority liq vaults
    liq_entries = []
    for v in priority_liq_vaults:
        vault_id = v[0]
        asset = str(v[1])
        symbol = symbol_map.get(asset, "???")
        liq_entries.append(f"    cs.VaultLite(vaultId={vault_id}, asset={asset}), # {symbol}")
    liq_code = "\n".join(liq_entries) if liq_entries else ""

    # Priority stab vaults
    stab_entries = []
    for v in priority_stab_vaults:
        vault_id = v[0]
        asset = str(v[1])
        symbol = symbol_map.get(asset, "???")
        stab_entries.append(f"    cs.VaultLite(vaultId={vault_id}, asset={asset}), # {symbol}")
    stab_code = "\n".join(stab_entries) if stab_entries else ""

    # Priority price source IDs
    price_ids = ", ".join(str(pid) for pid in priority_price_source_ids)

    return f'''
# priority lists


@view
@external
def priorityLiqAssetVaults() -> DynArray[cs.VaultLite, 20]:
    return [
{liq_code}
    ]


@view
@external
def priorityStabVaults() -> DynArray[cs.VaultLite, 20]:
    return [
{stab_code}
    ]


@view
@external
def priorityPriceSourceIds() -> DynArray[uint256, 10]:
    return [{price_ids}]
'''


def generate_defaults_vyper(
    gen_config: tuple,
    gen_debt_config: tuple,
    hr_config: tuple,
    ripe_bond_config: tuple,
    rewards_config: tuple,
    ripe_gov_vault_config: tuple,
    should_check_last_touch: bool,
    contrib_template: str,
    underscore_registry: str,
    training_wheels: str,
    asset_configs: list,
    priority_liq_vaults: list,
    priority_stab_vaults: list,
    priority_price_source_ids: list,
    symbol_map: dict,
) -> str:
    """Generate the complete DefaultsBase.vy file content."""

    # Extract nested structs
    auction_params = gen_debt_config[16]  # genAuctionParams
    lock_terms = ripe_gov_vault_config[0]  # lockTerms

    # Generate asset config code
    asset_config_code = generate_asset_configs_vyper(asset_configs)

    # Generate priority lists code
    priority_lists_code = generate_priority_lists_vyper(
        priority_liq_vaults, priority_stab_vaults, priority_price_source_ids, symbol_map
    )

    vyper_code = f'''# Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
# Ripe Foundation (C) 2025

# @version 0.4.3

implements: Defaults
from interfaces import Defaults
import interfaces.ConfigStructs as cs

EIGHTEEN_DECIMALS: constant(uint256) = 10 ** 18
HUNDRED_PERCENT: constant(uint256) = 100_00

# seconds
DAY_IN_SECONDS: constant(uint256) = 60 * 60 * 24
WEEK_IN_SECONDS: constant(uint256) = 7 * DAY_IN_SECONDS
MONTH_IN_SECONDS: constant(uint256) = 30 * DAY_IN_SECONDS
YEAR_IN_SECONDS: constant(uint256) = 365 * DAY_IN_SECONDS

# blocks
HOUR_IN_BLOCKS: constant(uint256) = 1_800
DAY_IN_BLOCKS: constant(uint256) = 24 * HOUR_IN_BLOCKS
WEEK_IN_BLOCKS: constant(uint256) = 7 * DAY_IN_BLOCKS
MONTH_IN_BLOCKS: constant(uint256) = 30 * DAY_IN_BLOCKS
YEAR_IN_BLOCKS: constant(uint256) = 365 * DAY_IN_BLOCKS

# addresses
CONTRIB_TEMPLATE: constant(address) = {contrib_template}
TRAINING_WHEELS: constant(address) = {training_wheels}
UNDERSCORE_REGISTRY: constant(address) = {underscore_registry}


@deploy
def __init__():
    pass


# general config


@view
@external
def genConfig() -> cs.GenConfig:
    return cs.GenConfig(
        perUserMaxVaults = {gen_config[0]},
        perUserMaxAssetsPerVault = {gen_config[1]},
        priceStaleTime = {format_vyper_uint(gen_config[2], "seconds")},
        canDeposit = {format_vyper_bool(gen_config[3])},
        canWithdraw = {format_vyper_bool(gen_config[4])},
        canBorrow = {format_vyper_bool(gen_config[5])},
        canRepay = {format_vyper_bool(gen_config[6])},
        canClaimLoot = {format_vyper_bool(gen_config[7])},
        canLiquidate = {format_vyper_bool(gen_config[8])},
        canRedeemCollateral = {format_vyper_bool(gen_config[9])},
        canRedeemInStabPool = {format_vyper_bool(gen_config[10])},
        canBuyInAuction = {format_vyper_bool(gen_config[11])},
        canClaimInStabPool = {format_vyper_bool(gen_config[12])},
    )


# debt config


@view
@external
def genDebtConfig() -> cs.GenDebtConfig:
    return cs.GenDebtConfig(
        perUserDebtLimit = {format_vyper_uint(gen_debt_config[0], "amount")},
        globalDebtLimit = {format_vyper_uint(gen_debt_config[1], "amount")},
        minDebtAmount = {format_vyper_uint(gen_debt_config[2], "amount")},
        numAllowedBorrowers = {gen_debt_config[3]},
        maxBorrowPerInterval = {format_vyper_uint(gen_debt_config[4], "amount")},
        numBlocksPerInterval = {format_vyper_uint(gen_debt_config[5], "blocks")},
        minDynamicRateBoost = {format_vyper_uint(gen_debt_config[6], "percent")},
        maxDynamicRateBoost = {format_vyper_uint(gen_debt_config[7], "percent")},
        increasePerDangerBlock = {gen_debt_config[8]},
        maxBorrowRate = {format_vyper_uint(gen_debt_config[9], "percent")},
        maxLtvDeviation = {format_vyper_uint(gen_debt_config[10], "percent")},
        keeperFeeRatio = {format_vyper_uint(gen_debt_config[11], "percent")},
        minKeeperFee = {format_vyper_uint(gen_debt_config[12], "amount")},
        maxKeeperFee = {format_vyper_uint(gen_debt_config[13], "amount")},
        isDaowryEnabled = {format_vyper_bool(gen_debt_config[14])},
        ltvPaybackBuffer = {format_vyper_uint(gen_debt_config[15], "percent")},
        genAuctionParams = cs.AuctionParams(
            hasParams = {format_vyper_bool(auction_params[0])},
            startDiscount = {format_vyper_uint(auction_params[1], "percent")},
            maxDiscount = {format_vyper_uint(auction_params[2], "percent")},
            delay = {format_vyper_uint(auction_params[3], "blocks")},
            duration = {format_vyper_uint(auction_params[4], "blocks")},
        ),
    )


# ripe available


@view
@external
def ripeAvailForRewards() -> uint256:
    return 1_000 * EIGHTEEN_DECIMALS


@view
@external
def ripeAvailForHr() -> uint256:
    return 1_000 * EIGHTEEN_DECIMALS


@view
@external
def ripeAvailForBonds() -> uint256:
    return 1_000 * EIGHTEEN_DECIMALS


# ripe bond config


@view
@external
def ripeBondConfig() -> cs.RipeBondConfig:
    return cs.RipeBondConfig(
        asset = {format_vyper_address(str(ripe_bond_config[0]))},
        amountPerEpoch = {format_vyper_uint(ripe_bond_config[1], "amount6")},
        canBond = {format_vyper_bool(ripe_bond_config[2])},
        minRipePerUnit = {format_vyper_uint(ripe_bond_config[3], "amount")},
        maxRipePerUnit = {format_vyper_uint(ripe_bond_config[4], "amount")},
        maxRipePerUnitLockBonus = {format_vyper_uint(ripe_bond_config[5], "percent")},
        epochLength = {format_vyper_uint(ripe_bond_config[6], "blocks")},
        shouldAutoRestart = {format_vyper_bool(ripe_bond_config[7])},
        restartDelayBlocks = {format_vyper_uint(ripe_bond_config[8], "blocks")},
    )


# ripe rewards config


@view
@external
def rewardsConfig() -> cs.RipeRewardsConfig:
    return cs.RipeRewardsConfig(
        arePointsEnabled = {format_vyper_bool(rewards_config[0])},
        ripePerBlock = {format_vyper_uint(rewards_config[1], "amount")},
        borrowersAlloc = {format_vyper_uint(rewards_config[2], "alloc")},
        stakersAlloc = {format_vyper_uint(rewards_config[3], "alloc")},
        votersAlloc = {format_vyper_uint(rewards_config[4], "alloc")},
        genDepositorsAlloc = {format_vyper_uint(rewards_config[5], "alloc")},
        autoStakeRatio = {format_vyper_uint(rewards_config[6], "ratio")},
        autoStakeDurationRatio = {format_vyper_uint(rewards_config[7], "ratio")},
        stabPoolRipePerDollarClaimed = {format_vyper_uint(rewards_config[8], "amount")},
    )


# ripe token config for ripe gov vault


@view
@external
def ripeTokenVaultConfig() -> cs.RipeGovVaultConfig:
    return cs.RipeGovVaultConfig(
        lockTerms = cs.LockTerms(
            minLockDuration = {format_vyper_uint(lock_terms[0], "blocks")},
            maxLockDuration = {format_vyper_uint(lock_terms[1], "blocks")},
            maxLockBoost = {format_vyper_uint(lock_terms[2], "boost")},
            canExit = {format_vyper_bool(lock_terms[3])},
            exitFee = {format_vyper_uint(lock_terms[4], "fee")},
        ),
        assetWeight = {format_vyper_uint(ripe_gov_vault_config[1], "percent")},
        shouldFreezeWhenBadDebt = {format_vyper_bool(ripe_gov_vault_config[2])},
    )


# hr config


@view
@external
def hrConfig() -> cs.HrConfig:
    return cs.HrConfig(
        contribTemplate = CONTRIB_TEMPLATE,
        maxCompensation = {format_vyper_uint(hr_config[1], "amount")}, # set this later, after core contributor vesting setup
        minCliffLength = {format_vyper_uint(hr_config[2], "cliff")},
        maxStartDelay = {format_vyper_uint(hr_config[3], "startDelay")},
        minVestingLength = {format_vyper_uint(hr_config[4], "vesting")},
        maxVestingLength = {format_vyper_uint(hr_config[5], "vesting")},
    )


# underscore registry


@view
@external
def underscoreRegistry() -> address:
    return UNDERSCORE_REGISTRY


# training wheels


@view
@external
def trainingWheels() -> address:
    return TRAINING_WHEELS


# should check last touch


@view
@external
def shouldCheckLastTouch() -> bool:
    return {format_vyper_bool(should_check_last_touch)}
'''

    # Append asset configs and priority lists
    vyper_code += asset_config_code
    vyper_code += priority_lists_code

    return vyper_code


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


def main():
    """Main entry point."""
    print("=" * 60)
    print("Regenerate DefaultsBase.vy from Live MissionControl")
    print("=" * 60)

    print("\nConnecting to Base mainnet via Alchemy...")

    # Set etherscan API
    setup_boa_etherscan()

    # Fork at latest block
    with boa_fork_context() as block_number:
        print(f"Connected. Block: {block_number}\n")

        # Load RipeHQ
        print("Loading RipeHQ...")
        hq = boa.from_etherscan(RIPE_HQ, name="RipeHQ")
        time.sleep(RPC_DELAY)

        # Load MissionControl
        print("Loading MissionControl...")
        mc_addr = hq.getAddr(MISSION_CONTROL_ID)
        mc = boa.from_etherscan(mc_addr, name="MissionControl")
        time.sleep(RPC_DELAY)
        print(f"  Address: {mc_addr}")

        # Load RIPE token address for ripeGovVaultConfig
        print("Loading RIPE token address...")
        ripe_addr = hq.getAddr(RIPE_TOKEN_ID)
        time.sleep(RPC_DELAY)
        print(f"  Address: {ripe_addr}")

        # Read all configs
        print("\nReading MissionControl configs...")

        print("  - genConfig()")
        time.sleep(RPC_DELAY)
        gen_config = mc.genConfig()

        print("  - genDebtConfig()")
        time.sleep(RPC_DELAY)
        gen_debt_config = mc.genDebtConfig()

        print("  - hrConfig()")
        time.sleep(RPC_DELAY)
        hr_config = mc.hrConfig()

        print("  - ripeBondConfig()")
        time.sleep(RPC_DELAY)
        ripe_bond_config = mc.ripeBondConfig()

        print("  - rewardsConfig()")
        time.sleep(RPC_DELAY)
        rewards_config = mc.rewardsConfig()

        print("  - ripeGovVaultConfig(ripeToken)")
        time.sleep(RPC_DELAY)
        ripe_gov_vault_config = mc.ripeGovVaultConfig(ripe_addr)

        print("  - shouldCheckLastTouch()")
        time.sleep(RPC_DELAY)
        should_check_last_touch = mc.shouldCheckLastTouch()

        print("  - hrConfig().contribTemplate")
        contrib_template = hr_config[0]  # Already read above

        print("  - underscoreRegistry()")
        time.sleep(RPC_DELAY)
        underscore_registry = mc.underscoreRegistry()

        print("  - trainingWheels()")
        time.sleep(RPC_DELAY)
        training_wheels = mc.trainingWheels()

        # Load VaultBook and PriceDesk
        print("\nLoading VaultBook...")
        vault_book_addr = hq.getAddr(VAULT_BOOK_ID)
        time.sleep(RPC_DELAY)
        vault_book = boa.loads_abi(VAULT_BOOK_ABI, name="VaultBook").at(vault_book_addr)
        print(f"  Address: {vault_book_addr}")

        print("\nLoading PriceDesk...")
        price_desk_addr = hq.getAddr(PRICE_DESK_ID)
        time.sleep(RPC_DELAY)
        price_desk = boa.loads_abi(PRICE_DESK_ABI, name="PriceDesk").at(price_desk_addr)
        print(f"  Address: {price_desk_addr}")

        # Read asset configs (skipping canDeposit=False)
        print("\nReading asset configs (skipping canDeposit=False)...")
        time.sleep(RPC_DELAY)
        num_assets = mc.numAssets()
        asset_configs = []  # List of (address, config, symbol, usd_value, price, decimals) tuples
        symbol_map = {}  # address -> symbol for priority lists
        skipped_count = 0
        for i in range(1, num_assets):
            time.sleep(RPC_DELAY)
            asset_addr = mc.assets(i)
            if asset_addr == "0x0000000000000000000000000000000000000000":
                continue
            time.sleep(RPC_DELAY)
            config = mc.assetConfig(asset_addr)
            symbol = get_token_symbol(str(asset_addr))
            symbol_map[str(asset_addr)] = symbol

            # Check canDeposit - skip if False (except GREEN which we need configured but not depositable)
            can_deposit = config[11]  # canDeposit field
            if not can_deposit and symbol != "GREEN":
                print(f"  - Asset {i}: {symbol} - SKIPPED (canDeposit=False)")
                skipped_count += 1
                continue

            # Get price and decimals once per asset
            decimals = get_token_decimals(str(asset_addr))
            try:
                time.sleep(RPC_DELAY)
                price = price_desk.getPrice(asset_addr)
            except Exception:
                price = 0

            # Get total balance and calculate USD value for sorting
            vault_ids = list(config[0])  # vaultIds is first field
            total_balance = get_asset_total_balance(vault_book, str(asset_addr), vault_ids)
            usd_value = calc_usd_value(total_balance, price, decimals)

            asset_configs.append((str(asset_addr), config, symbol, usd_value, price, decimals))
            print(f"  - Asset {i}: {symbol} ({asset_addr[:10]}...) - {format_usd_value(usd_value)}")
        print(f"  Total: {len(asset_configs)} assets (skipped {skipped_count} with canDeposit=False)")

        # Sort assets: highest LTV first, then by USD value for same LTV
        def sort_key(item):
            addr, config, symbol, usd_value, price, decimals = item
            ltv = config[6][0]  # debtTerms.ltv
            # Sort by LTV desc, then by USD value desc
            # Use negative values for descending sort
            return (-ltv, -usd_value)

        asset_configs.sort(key=sort_key)
        print("\nSorted assets by LTV (desc), then USD value (desc):")
        for addr, config, symbol, usd_value, price, decimals in asset_configs:
            ltv = config[6][0]
            print(f"  - {symbol}: LTV={ltv/100:.0f}%, USD={format_usd_value(usd_value)}")

        # Read priority lists
        print("\nReading priority lists...")
        time.sleep(RPC_DELAY)
        priority_liq_vaults = mc.getPriorityLiqAssetVaults()
        print(f"  - priorityLiqAssetVaults: {len(priority_liq_vaults)} entries")

        time.sleep(RPC_DELAY)
        priority_stab_vaults = mc.getPriorityStabVaults()
        print(f"  - priorityStabVaults: {len(priority_stab_vaults)} entries")

        time.sleep(RPC_DELAY)
        priority_price_source_ids = mc.getPriorityPriceSourceIds()
        print(f"  - priorityPriceSourceIds: {list(priority_price_source_ids)}")

        # Print summary of read values
        print("\n" + "=" * 60)
        print("Summary of Live Values Read:")
        print("=" * 60)

        print("\ngenConfig:")
        print(f"  perUserMaxVaults: {gen_config[0]}")
        print(f"  perUserMaxAssetsPerVault: {gen_config[1]}")
        print(f"  priceStaleTime: {gen_config[2]}")
        print(f"  canDeposit: {gen_config[3]}")
        print(f"  canBorrow: {gen_config[5]}")
        print(f"  canLiquidate: {gen_config[8]}")

        print("\ngenDebtConfig:")
        print(f"  perUserDebtLimit: {gen_debt_config[0] / 10**18:.2f} GREEN")
        print(f"  globalDebtLimit: {gen_debt_config[1] / 10**18:.2f} GREEN")
        print(f"  numAllowedBorrowers: {gen_debt_config[3]}")
        print(f"  maxBorrowRate: {gen_debt_config[9] / 100:.2f}%")

        print("\nhrConfig:")
        print(f"  maxCompensation: {hr_config[1]}")
        print(f"  maxVestingLength: {hr_config[5] / DAY_IN_SECONDS:.1f} days")

        print("\nripeBondConfig:")
        print(f"  canBond: {ripe_bond_config[2]}")

        print("\nrewardsConfig:")
        print(f"  arePointsEnabled: {rewards_config[0]}")
        print(f"  ripePerBlock: {rewards_config[1]}")

        print("\nripeGovVaultConfig:")
        lock_terms = ripe_gov_vault_config[0]
        print(f"  minLockDuration: {lock_terms[0] / DAY_IN_BLOCKS:.1f} days")
        print(f"  maxLockDuration: {lock_terms[1] / DAY_IN_BLOCKS:.1f} days")

        print(f"\nshouldCheckLastTouch: {should_check_last_touch}")

        print(f"\nAddresses:")
        print(f"  contribTemplate: {contrib_template}")
        print(f"  underscoreRegistry: {underscore_registry}")
        print(f"  trainingWheels: {training_wheels}")

        # Generate Vyper code
        print("\n" + "=" * 60)
        print("Generating DefaultsBase.vy...")
        print("=" * 60)

        vyper_code = generate_defaults_vyper(
            gen_config=gen_config,
            gen_debt_config=gen_debt_config,
            hr_config=hr_config,
            ripe_bond_config=ripe_bond_config,
            rewards_config=rewards_config,
            ripe_gov_vault_config=ripe_gov_vault_config,
            should_check_last_touch=should_check_last_touch,
            contrib_template=contrib_template,
            underscore_registry=underscore_registry,
            training_wheels=training_wheels,
            asset_configs=asset_configs,
            priority_liq_vaults=priority_liq_vaults,
            priority_stab_vaults=priority_stab_vaults,
            priority_price_source_ids=priority_price_source_ids,
            symbol_map=symbol_map,
        )

        # Write output file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(script_dir, "../../contracts/config/DefaultsBase.vy")
        output_path = os.path.normpath(output_path)

        print(f"\nWriting to: {output_path}")

        with open(output_path, "w") as f:
            f.write(vyper_code)

        print("\nDone!")
        print(f"\nGenerated DefaultsBase.vy at block {block_number}")
        print("\nNote: ripeAvailFor* values are kept as hardcoded defaults (1000 * 10^18)")
        print("\nTo verify syntax, run:")
        print(f"  vyper {output_path}")


if __name__ == "__main__":
    main()
