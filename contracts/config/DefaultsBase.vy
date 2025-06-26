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

# initial adddresses
CONTRIB_TEMPLATE: immutable(address)
TRAINING_WHEELS: immutable(address)


@deploy
def __init__(
    _contribTemplate: address,
    _trainingWheels: address,
):
    CONTRIB_TEMPLATE = _contribTemplate
    TRAINING_WHEELS = _trainingWheels


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
        perUserDebtLimit = 100 * EIGHTEEN_DECIMALS,
        globalDebtLimit = 1000 * EIGHTEEN_DECIMALS,
        minDebtAmount = 1 * EIGHTEEN_DECIMALS,
        numAllowedBorrowers = 50,
        maxBorrowPerInterval = 50 * EIGHTEEN_DECIMALS,
        numBlocksPerInterval = 1 * DAY_IN_BLOCKS,
        minDynamicRateBoost = 1 * HUNDRED_PERCENT,
        maxDynamicRateBoost = 5 * HUNDRED_PERCENT,
        increasePerDangerBlock = 10,
        maxBorrowRate = HUNDRED_PERCENT,
        maxLtvDeviation = 10_00,
        keeperFeeRatio = 1_00,
        minKeeperFee = 1 * EIGHTEEN_DECIMALS,
        maxKeeperFee = 25_000 * EIGHTEEN_DECIMALS,
        isDaowryEnabled = True,
        ltvPaybackBuffer = 5_00,
        genAuctionParams = cs.AuctionParams(
            hasParams = True,
            startDiscount = 1_00,
            maxDiscount = 50_00,
            delay = 0,
            duration = 1 * DAY_IN_BLOCKS,
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
        asset = empty(address),
        amountPerEpoch = 10 * (10 ** 6),
        canBond = False,
        minRipePerUnit = 1 * EIGHTEEN_DECIMALS,
        maxRipePerUnit = 100 * EIGHTEEN_DECIMALS,
        maxRipePerUnitLockBonus = 1 * EIGHTEEN_DECIMALS,
        epochLength = 1 * DAY_IN_BLOCKS,
        shouldAutoRestart = False,
        restartDelayBlocks = 0,
    )


# ripe rewards config


@view
@external
def rewardsConfig() -> cs.RipeRewardsConfig:
    return cs.RipeRewardsConfig(
        arePointsEnabled = False,
        ripePerBlock = 0,
        borrowersAlloc = 10_00,
        stakersAlloc = 90_00,
        votersAlloc = 0,
        genDepositorsAlloc = 0,
        autoStakeRatio = 90_00,
        autoStakeDurationRatio = 25_00,
        stabPoolRipePerDollarClaimed = 1 * EIGHTEEN_DECIMALS,
    )


# ripe token config for ripe gov vault


@view
@external
def ripeTokenVaultConfig() -> cs.RipeGovVaultConfig:
    return cs.RipeGovVaultConfig(
        lockTerms = cs.LockTerms(
            minLockDuration = 1 * DAY_IN_BLOCKS,
            maxLockDuration = 1 * WEEK_IN_BLOCKS,
            maxLockBoost = 5 * HUNDRED_PERCENT,
            canExit = True,
            exitFee = 50_00,
        ),
        assetWeight = HUNDRED_PERCENT,
        shouldFreezeWhenBadDebt = True,
    )


# hr config


@view
@external
def hrConfig() -> cs.HrConfig:
    return cs.HrConfig(
        contribTemplate = CONTRIB_TEMPLATE,
        maxCompensation = 0, # set this later, after core contributor vesting setup
        minCliffLength = 1 * WEEK_IN_SECONDS,
        maxStartDelay = 3 * MONTH_IN_SECONDS,
        minVestingLength = 1 * WEEK_IN_SECONDS,
        maxVestingLength = 10 * YEAR_IN_SECONDS,
    )


# underscore registry


UNDERSCORE_REGISTRY: constant(address) = 0x7BcD6d471D1A068012A79347C7a944d1Df01a1AE


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
    return True
