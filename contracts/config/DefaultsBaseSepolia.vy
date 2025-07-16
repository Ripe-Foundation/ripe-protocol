# Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
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
DAY_IN_BLOCKS: constant(uint256) = 43_200
WEEK_IN_BLOCKS: constant(uint256) = 7 * DAY_IN_BLOCKS
MONTH_IN_BLOCKS: constant(uint256) = 30 * DAY_IN_BLOCKS
YEAR_IN_BLOCKS: constant(uint256) = 365 * DAY_IN_BLOCKS

UNDERSCORE_REGISTRY: immutable(address)


@deploy
def __init__(_underscoreRegistry: address):
    UNDERSCORE_REGISTRY = _underscoreRegistry


# general config


@view
@external
def genConfig() -> cs.GenConfig:
    return cs.GenConfig(
        perUserMaxVaults = 5,
        perUserMaxAssetsPerVault = 10,
        priceStaleTime = 0,
        canDeposit = True,
        canWithdraw = True,
        canBorrow = True,
        canRepay = True,
        canClaimLoot = True,
        canLiquidate = True,
        canRedeemCollateral = True,
        canRedeemInStabPool = True,
        canBuyInAuction = True,
        canClaimInStabPool = True,
    )


# debt config


@view
@external
def genDebtConfig() -> cs.GenDebtConfig:
    return cs.GenDebtConfig(
        perUserDebtLimit = 1_000_000 * EIGHTEEN_DECIMALS,
        globalDebtLimit = 100_000_000 * EIGHTEEN_DECIMALS,
        minDebtAmount = 100 * EIGHTEEN_DECIMALS,
        numAllowedBorrowers = 50,
        maxBorrowPerInterval = 100_000 * EIGHTEEN_DECIMALS,
        numBlocksPerInterval = 100,
        minDynamicRateBoost = 50_00,
        maxDynamicRateBoost = 5 * HUNDRED_PERCENT,
        increasePerDangerBlock = 10,
        maxBorrowRate = HUNDRED_PERCENT,
        maxLtvDeviation = 10_00,
        keeperFeeRatio = 1_00,
        minKeeperFee = EIGHTEEN_DECIMALS,
        maxKeeperFee = 10_0000 * EIGHTEEN_DECIMALS,
        isDaowryEnabled = True,
        ltvPaybackBuffer = 5_00,
        genAuctionParams = cs.AuctionParams(
            hasParams = True,
            startDiscount = 0,
            maxDiscount = 50_00,
            delay = 0,
            duration = DAY_IN_BLOCKS,
        ),
    )


# hr config


@view
@external
def hrConfig() -> cs.HrConfig:
    return cs.HrConfig(
        contribTemplate = empty(address),
        maxCompensation = 0, # set this later, after core contributor vesting setup
        minCliffLength = 1 * WEEK_IN_SECONDS,
        maxStartDelay = 1 * MONTH_IN_SECONDS,
        minVestingLength = 1 * MONTH_IN_SECONDS,
        maxVestingLength = 5 * YEAR_IN_SECONDS,
    )


# ripe bond config


@view
@external
def ripeBondConfig() -> cs.RipeBondConfig:
    return cs.RipeBondConfig(
        asset = 0x611ce0729f6C052f49536c84a8fD717E619D5dc6,
        amountPerEpoch = 100_000 * (10 ** 6),
        canBond = True,
        minRipePerUnit = 1 * EIGHTEEN_DECIMALS,
        maxRipePerUnit = 100 * EIGHTEEN_DECIMALS,
        maxRipePerUnitLockBonus = HUNDRED_PERCENT,
        epochLength = 1000,
        shouldAutoRestart = True,
        restartDelayBlocks = 100,
    )


# ripe rewards config


@view
@external
def rewardsConfig() -> cs.RipeRewardsConfig:
    return cs.RipeRewardsConfig(
        arePointsEnabled = True,
        ripePerBlock = 1 * EIGHTEEN_DECIMALS,
        borrowersAlloc = 50_00,
        stakersAlloc = 10_00,
        votersAlloc = 0,
        genDepositorsAlloc = 0,
        autoStakeRatio = 90_00,
        autoStakeDurationRatio = 10_00,
        stabPoolRipePerDollarClaimed = 1 * EIGHTEEN_DECIMALS,
    )


# ripe gov vault config


@view
@external
def ripeTokenVaultConfig() -> cs.RipeGovVaultConfig:
    return cs.RipeGovVaultConfig(
        lockTerms = cs.LockTerms(
            minLockDuration = 1 * DAY_IN_BLOCKS,
            maxLockDuration = 1 * MONTH_IN_BLOCKS,
            maxLockBoost = 2 * HUNDRED_PERCENT,
            canExit = True,
            exitFee = 10_00,
        ),
        assetWeight = HUNDRED_PERCENT,
        shouldFreezeWhenBadDebt = True,
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
    return empty(address)


# should check last touch


@view
@external
def shouldCheckLastTouch() -> bool:
    return True


# ripe available


@view
@external
def ripeAvailForRewards() -> uint256:
    return 100_000_000 * EIGHTEEN_DECIMALS


@view
@external
def ripeAvailForHr() -> uint256:
    return 100_000_000 * EIGHTEEN_DECIMALS


@view
@external
def ripeAvailForBonds() -> uint256:
    return 100_000_000 * EIGHTEEN_DECIMALS