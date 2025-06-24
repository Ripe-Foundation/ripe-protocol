# Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
# Ripe Foundation (C) 2025

# @version 0.4.3

implements: Defaults
from interfaces import Defaults
import interfaces.ConfigStructs as cs

EIGHTEEN_DECIMALS: constant(uint256) = 10 ** 18


@deploy
def __init__():
    pass


# general config


@view
@external
def genConfig() -> cs.GenConfig:
    return empty(cs.GenConfig)


# debt config


@view
@external
def genDebtConfig() -> cs.GenDebtConfig:
    return empty(cs.GenDebtConfig)


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


# ripe bond config


@view
@external
def ripeBondConfig() -> cs.RipeBondConfig:
    return empty(cs.RipeBondConfig)


# ripe rewards config


@view
@external
def rewardsConfig() -> cs.RipeRewardsConfig:
    return empty(cs.RipeRewardsConfig)


# ripe token config for ripe gov vault


@view
@external
def ripeTokenVaultConfig() -> cs.RipeGovVaultConfig:
    return empty(cs.RipeGovVaultConfig)


# hr config


@view
@external
def hrConfig() -> cs.HrConfig:
    return empty(cs.HrConfig)


# underscore registry


@view
@external
def underscoreRegistry() -> address:
    return empty(address)


# should check last touch


@view
@external
def shouldCheckLastTouch() -> bool:
    return False

