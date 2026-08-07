# Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
# Ripe Foundation (C) 2025

# @version 0.4.3

# Seeds a REPLACEMENT MissionControl from the one already running.
#
# MissionControl copies its defaults into storage at construction, so a
# redeployed MissionControl built against DefaultsRobinhood would come up
# holding launch values and silently forget everything governance changed
# since -- on Robinhood that is eight registered assets, a 10x lower
# ripePerBlock, an extra stability-vault route and three lite signers.
#
# Rather than transcribe those into a constants file, where they would be
# stale again the moment governance touches anything, this reads them back
# off the live MissionControl at construction time. Nothing is hardcoded, so
# the copy is exact whenever the redeploy actually runs.
#
# DefaultsRobinhood remains the right source for a brand-new chain; this is
# only for replacing a MissionControl that already exists.
#
# The three ripeAvail* values live on Ledger, not MissionControl, so they are
# read from there. Note those are consumed balances rather than config: Ledger
# is not being redeployed, so nothing reads these back today.

implements: Defaults
from interfaces import Defaults
import interfaces.ConfigStructs as cs

interface MissionControl:
    def ripeGovVaultConfig(_asset: address) -> cs.RipeGovVaultConfig: view
    def getPriorityLiqAssetVaults() -> DynArray[cs.VaultLite, 20]: view
    def getPriorityPriceSourceIds() -> DynArray[uint256, 10]: view
    def getPriorityStabVaults() -> DynArray[cs.VaultLite, 20]: view
    def assetConfig(_asset: address) -> cs.AssetConfig: view
    def genDebtConfig() -> cs.GenDebtConfig: view
    def rewardsConfig() -> cs.RipeRewardsConfig: view
    def ripeBondConfig() -> cs.RipeBondConfig: view
    def liteSigners(_index: uint256) -> address: view
    def shouldCheckLastTouch() -> bool: view
    def assets(_index: uint256) -> address: view
    def underscoreRegistry() -> address: view
    def genConfig() -> cs.GenConfig: view
    def numLiteSigners() -> uint256: view
    def trainingWheels() -> address: view
    def hrConfig() -> cs.HrConfig: view
    def numAssets() -> uint256: view

interface Ledger:
    def ripeAvailForRewards() -> uint256: view
    def ripeAvailForBonds() -> uint256: view
    def ripeAvailForHr() -> uint256: view

MISSION_CONTROL: public(immutable(address))
LEDGER: public(immutable(address))

MAX_ASSETS: constant(uint256) = 50
MAX_GOV_VAULT_CONFIGS: constant(uint256) = 5
MAX_LITE_SIGNERS: constant(uint256) = 10


@deploy
def __init__(_missionControl: address, _ledger: address):
    assert empty(address) not in [_missionControl, _ledger] # dev: invalid source
    MISSION_CONTROL = _missionControl
    LEDGER = _ledger


# general config


@view
@external
def genConfig() -> cs.GenConfig:
    return staticcall MissionControl(MISSION_CONTROL).genConfig()


# debt config


@view
@external
def genDebtConfig() -> cs.GenDebtConfig:
    return staticcall MissionControl(MISSION_CONTROL).genDebtConfig()


# ripe available


@view
@external
def ripeAvailForRewards() -> uint256:
    return staticcall Ledger(LEDGER).ripeAvailForRewards()


@view
@external
def ripeAvailForHr() -> uint256:
    return staticcall Ledger(LEDGER).ripeAvailForHr()


@view
@external
def ripeAvailForBonds() -> uint256:
    return staticcall Ledger(LEDGER).ripeAvailForBonds()


# ripe bond config


@view
@external
def ripeBondConfig() -> cs.RipeBondConfig:
    return staticcall MissionControl(MISSION_CONTROL).ripeBondConfig()


# ripe rewards config


@view
@external
def rewardsConfig() -> cs.RipeRewardsConfig:
    return staticcall MissionControl(MISSION_CONTROL).rewardsConfig()


# ripe gov vault configs


@view
@external
def ripeGovVaultConfigs() -> DynArray[cs.RipeGovVaultConfigEntry, MAX_GOV_VAULT_CONFIGS]:
    # MissionControl keys these by asset with no list to enumerate, so the
    # registered assets are walked and the ones carrying a config are kept.
    # An unset entry is all-zero, and assetWeight is nonzero for every real
    # one, so that is what distinguishes them.
    mc: address = MISSION_CONTROL
    configs: DynArray[cs.RipeGovVaultConfigEntry, MAX_GOV_VAULT_CONFIGS] = []
    numAssets: uint256 = staticcall MissionControl(mc).numAssets()
    for i: uint256 in range(1, numAssets, bound=MAX_ASSETS):
        if len(configs) == MAX_GOV_VAULT_CONFIGS:
            break
        asset: address = staticcall MissionControl(mc).assets(i)
        if asset == empty(address):
            continue
        config: cs.RipeGovVaultConfig = staticcall MissionControl(mc).ripeGovVaultConfig(asset)
        if config.assetWeight == 0:
            continue
        configs.append(cs.RipeGovVaultConfigEntry(asset=asset, config=config))
    return configs


# hr config


@view
@external
def hrConfig() -> cs.HrConfig:
    return staticcall MissionControl(MISSION_CONTROL).hrConfig()


# underscore registry


@view
@external
def underscoreRegistry() -> address:
    return staticcall MissionControl(MISSION_CONTROL).underscoreRegistry()


# training wheels


@view
@external
def trainingWheels() -> address:
    return staticcall MissionControl(MISSION_CONTROL).trainingWheels()


# should check last touch


@view
@external
def shouldCheckLastTouch() -> bool:
    return staticcall MissionControl(MISSION_CONTROL).shouldCheckLastTouch()


# asset configs


@view
@external
def assetConfigs() -> DynArray[cs.AssetConfigEntry, MAX_ASSETS]:
    # Index 0 is unused: MissionControl starts numAssets at 1 so that 0 can
    # mean "not registered".
    mc: address = MISSION_CONTROL
    entries: DynArray[cs.AssetConfigEntry, MAX_ASSETS] = []
    numAssets: uint256 = staticcall MissionControl(mc).numAssets()
    for i: uint256 in range(1, numAssets, bound=MAX_ASSETS):
        asset: address = staticcall MissionControl(mc).assets(i)
        if asset == empty(address):
            continue
        entries.append(cs.AssetConfigEntry(
            asset=asset,
            config=staticcall MissionControl(mc).assetConfig(asset),
        ))
    return entries


# priority lists


@view
@external
def priorityLiqAssetVaults() -> DynArray[cs.VaultLite, 20]:
    return staticcall MissionControl(MISSION_CONTROL).getPriorityLiqAssetVaults()


@view
@external
def priorityStabVaults() -> DynArray[cs.VaultLite, 20]:
    return staticcall MissionControl(MISSION_CONTROL).getPriorityStabVaults()


@view
@external
def priorityPriceSourceIds() -> DynArray[uint256, 10]:
    return staticcall MissionControl(MISSION_CONTROL).getPriorityPriceSourceIds()


# lite signers


@view
@external
def liteSigners() -> DynArray[address, MAX_LITE_SIGNERS]:
    # Same 1-based indexing as assets: index 0 means "not in list".
    mc: address = MISSION_CONTROL
    signers: DynArray[address, MAX_LITE_SIGNERS] = []
    numSigners: uint256 = staticcall MissionControl(mc).numLiteSigners()
    for i: uint256 in range(1, numSigners, bound=MAX_LITE_SIGNERS):
        signer: address = staticcall MissionControl(mc).liteSigners(i)
        if signer == empty(address):
            continue
        signers.append(signer)
    return signers
