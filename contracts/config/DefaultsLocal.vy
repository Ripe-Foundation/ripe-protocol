# @version 0.4.1

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


# hr config


@view
@external
def hrConfig() -> cs.HrConfig:
    return empty(cs.HrConfig)


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


# ripe gov vault config


@view
@external
def ripeGovVaultConfig() -> cs.RipeGovVaultConfig:
    return empty(cs.RipeGovVaultConfig)


# stab claim rewards config


@view
@external
def stabClaimRewardsConfig() -> cs.StabClaimRewardsConfig:
    return empty(cs.StabClaimRewardsConfig)


# underscore registry


@view
@external
def underscoreRegistry() -> address:
    return empty(address)


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