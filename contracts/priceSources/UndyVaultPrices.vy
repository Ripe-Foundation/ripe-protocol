# Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
# Ripe Foundation (C) 2026

# @version 0.4.3

implements: PriceSource

exports: gov.__interface__
exports: addys.__interface__
exports: priceData.__interface__
exports: timeLock.__interface__

initializes: gov
initializes: addys
initializes: priceData[addys := addys]
initializes: timeLock[gov := gov]

import contracts.modules.LocalGov as gov
import contracts.modules.Addys as addys
import contracts.priceSources.modules.PriceSourceData as priceData
import contracts.modules.TimeLock as timeLock

import interfaces.PriceSource as PriceSource
from ethereum.ercs import IERC20Detailed
from ethereum.ercs import IERC4626
from ethereum.ercs import IERC20

interface PriceDesk:
    def getPrice(_asset: address, _shouldRaise: bool = False) -> uint256: view

interface UnderscoreVault:
    def convertToAssets(_shareAmount: uint256) -> uint256: view

interface VaultRegistry:
    def isEarnVault(_vaultAddr: address) -> bool: view

interface UndyRegistry:
    def getAddr(_regId: uint256) -> address: view

interface MissionControl:
    def underscoreRegistry() -> address: view

struct PriceConfig:
    underlyingAsset: address
    underlyingDecimals: uint256
    vaultTokenDecimals: uint256
    minSnapshotDelay: uint256
    maxNumSnapshots: uint256
    maxUpsideDeviation: uint256
    staleTime: uint256
    lastSnapshot: PriceSnapshot
    nextIndex: uint256

struct PriceSnapshot:
    totalSupply: uint256
    pricePerShare: uint256
    lastUpdate: uint256

struct PendingPriceConfig:
    actionId: uint256
    config: PriceConfig

event NewPriceConfigPending:
    asset: indexed(address)
    underlyingAsset: indexed(address)
    minSnapshotDelay: uint256
    maxNumSnapshots: uint256
    maxUpsideDeviation: uint256
    staleTime: uint256
    confirmationBlock: uint256
    actionId: uint256

event NewPriceConfigAdded:
    asset: indexed(address)
    underlyingAsset: indexed(address)
    minSnapshotDelay: uint256
    maxNumSnapshots: uint256
    maxUpsideDeviation: uint256
    staleTime: uint256

event NewPriceConfigCancelled:
    asset: indexed(address)
    underlyingAsset: indexed(address)

event PriceConfigUpdatePending:
    asset: indexed(address)
    underlyingAsset: indexed(address)
    minSnapshotDelay: uint256
    maxNumSnapshots: uint256
    maxUpsideDeviation: uint256
    staleTime: uint256
    confirmationBlock: uint256
    actionId: uint256

event PriceConfigUpdated:
    asset: indexed(address)
    underlyingAsset: indexed(address)
    minSnapshotDelay: uint256
    maxNumSnapshots: uint256
    maxUpsideDeviation: uint256
    staleTime: uint256

event PriceConfigUpdateCancelled:
    asset: indexed(address)
    underlyingAsset: indexed(address)

event DisablePriceConfigPending:
    asset: indexed(address)
    underlyingAsset: indexed(address)
    confirmationBlock: uint256
    actionId: uint256

event DisablePriceConfigConfirmed:
    asset: indexed(address)
    underlyingAsset: indexed(address)

event DisablePriceConfigCancelled:
    asset: indexed(address)
    underlyingAsset: indexed(address)

event PricePerShareSnapshotAdded:
    asset: indexed(address)
    underlyingAsset: indexed(address)
    totalSupply: uint256
    pricePerShare: uint256

# data 
priceConfigs: public(HashMap[address, PriceConfig]) # asset -> config
snapShots: public(HashMap[address, HashMap[uint256, PriceSnapshot]]) # asset -> index -> snapshot
pendingPriceConfigs: public(HashMap[address, PendingPriceConfig]) # asset -> pending config

HUNDRED_PERCENT: constant(uint256) = 100_00 # 100%
UNDERSCORE_VAULT_REGISTRY_ID: constant(uint256) = 10
MAX_SNAPSHOTS: constant(uint256) = 25
MAX_SAFE_DECIMALS: constant(uint256) = 77


@deploy
def __init__(
    _ripeHq: address,
    _tempGov: address,
    _minPriceChangeTimeLock: uint256,
    _maxPriceChangeTimeLock: uint256,
):
    gov.__init__(_ripeHq, _tempGov, 0, 0, 0)
    addys.__init__(_ripeHq)
    priceData.__init__(False)
    timeLock.__init__(_minPriceChangeTimeLock, _maxPriceChangeTimeLock, 0, _maxPriceChangeTimeLock)


###############
# Core Prices #
###############


# get price


@view
@external
def getPrice(_asset: address, _staleTime: uint256 = 0, _priceDesk: address = empty(address)) -> uint256:
    config: PriceConfig = self.priceConfigs[_asset]
    if config.underlyingAsset == empty(address):
        return 0
    return self._getPrice(_asset, config, _priceDesk)


@view
@external
def getPriceAndHasFeed(_asset: address, _staleTime: uint256 = 0, _priceDesk: address = empty(address)) -> (uint256, bool):
    config: PriceConfig = self.priceConfigs[_asset]
    if config.underlyingAsset == empty(address):
        return 0, False
    return self._getPrice(_asset, config, _priceDesk), True


@view
@internal
def _getPrice(
    _asset: address,
    _config: PriceConfig,
    _priceDesk: address,
) -> uint256:
    # NOTE: not using Mission Control `_staleTime` in this contract.
    # These vault tokens are different/unique. Each config has its own stale time.

    priceDesk: address = _priceDesk
    if priceDesk == empty(address):
        priceDesk = addys._getPriceDeskAddr()

    # get price
    weightedPricePerShare: uint256 = self._getWeightedPrice(_asset, _config)
    underlyingPrice: uint256 = staticcall PriceDesk(priceDesk).getPrice(_config.underlyingAsset, False)
    return self._getUnderscoreVaultPrice(_asset, _config, weightedPricePerShare, underlyingPrice)


# utilities


@view
@external
def hasPriceFeed(_asset: address) -> bool:
    return self.priceConfigs[_asset].underlyingAsset != empty(address)


@view
@external
def hasPendingPriceFeedUpdate(_asset: address) -> bool:
    return timeLock._hasPendingAction(self.pendingPriceConfigs[_asset].actionId)


################
# Add New Feed #
################


# initiate new feed


@external
def addNewPriceFeed(
    _asset: address,
    _minSnapshotDelay: uint256 = 60 * 5, # 5 minutes
    _maxNumSnapshots: uint256 = 20,
    _maxUpsideDeviation: uint256 = 10_00, # 10%
    _staleTime: uint256 = 60 * 60 * 24, # 1 day
) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    p: PriceConfig = self._getPriceConfig(_asset, _minSnapshotDelay, _maxNumSnapshots, _maxUpsideDeviation, _staleTime)
    assert self._isValidNewPriceConfig(_asset, p) # dev: invalid feed

    # set to pending state
    aid: uint256 = timeLock._initiateAction()
    self.pendingPriceConfigs[_asset] = PendingPriceConfig(actionId=aid, config=p)
    log NewPriceConfigPending(
        asset=_asset,
        underlyingAsset=p.underlyingAsset,
        minSnapshotDelay=p.minSnapshotDelay,
        maxNumSnapshots=p.maxNumSnapshots,
        maxUpsideDeviation=p.maxUpsideDeviation,
        staleTime=p.staleTime,
        confirmationBlock=timeLock._getActionConfirmationBlock(aid),
        actionId=aid,
    )
    return True


# confirm new feed


@external
def confirmNewPriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validate again
    d: PendingPriceConfig = self.pendingPriceConfigs[_asset]
    assert d.config.underlyingAsset != empty(address) # dev: no pending config
    if not self._hasExpectedMetadata(_asset, d.config):
        self._cancelNewPendingPriceFeed(_asset, d.actionId)
        return False
    if not self._isValidNewPriceConfig(_asset, d.config, False):
        self._cancelNewPendingPriceFeed(_asset, d.actionId)
        return False

    # check time lock
    assert timeLock._confirmAction(d.actionId) # dev: time lock not reached

    config: PriceConfig = self._resetSnapshots(_asset, d.config)

    # save new feed config
    self.priceConfigs[_asset] = config
    self.pendingPriceConfigs[_asset] = empty(PendingPriceConfig)
    priceData._addPricedAsset(_asset)

    log NewPriceConfigAdded(
        asset=_asset,
        underlyingAsset=d.config.underlyingAsset,
        minSnapshotDelay=d.config.minSnapshotDelay,
        maxNumSnapshots=d.config.maxNumSnapshots,
        maxUpsideDeviation=d.config.maxUpsideDeviation,
        staleTime=d.config.staleTime,
    )
    return True


# cancel new feed


@external
def cancelNewPendingPriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    d: PendingPriceConfig = self.pendingPriceConfigs[_asset]
    self._cancelNewPendingPriceFeed(_asset, d.actionId)
    log NewPriceConfigCancelled(
        asset=_asset,
        underlyingAsset=d.config.underlyingAsset,
    )
    return True


@internal
def _cancelNewPendingPriceFeed(_asset: address, _aid: uint256):
    assert timeLock._cancelAction(_aid) # dev: cannot cancel action
    self.pendingPriceConfigs[_asset] = empty(PendingPriceConfig)


# validation


@view
@external
def isValidNewFeed(
    _asset: address,
    _minSnapshotDelay: uint256,
    _maxNumSnapshots: uint256,
    _maxUpsideDeviation: uint256,
    _staleTime: uint256,
) -> bool:
    config: PriceConfig = self._getPriceConfig(_asset, _minSnapshotDelay, _maxNumSnapshots, _maxUpsideDeviation, _staleTime)
    return self._isValidNewPriceConfig(_asset, config)


@view
@internal
def _isValidNewPriceConfig(_asset: address, _config: PriceConfig, _requireValidSnapshot: bool = True) -> bool:
    if priceData.indexOfAsset[_asset] != 0 or self.priceConfigs[_asset].underlyingAsset != empty(address): # use the `updatePriceConfig` function instead
        return False
    return self._isValidFeedConfig(_asset, _config, _requireValidSnapshot)


@view
@internal
def _isValidFeedConfig(_asset: address, _config: PriceConfig, _requireValidSnapshot: bool = True) -> bool:
    if empty(address) in [_asset, _config.underlyingAsset]:
        return False

    # verify the vault is an earn vault
    underscore: address = staticcall MissionControl(addys._getMissionControlAddr()).underscoreRegistry()
    if underscore == empty(address):
        return False
    vaultRegistry: address = staticcall UndyRegistry(underscore).getAddr(UNDERSCORE_VAULT_REGISTRY_ID)
    if not staticcall VaultRegistry(vaultRegistry).isEarnVault(_asset):
        return False

    if _config.minSnapshotDelay > (60 * 60 * 24 * 7): # 1 week
        return False
    if _config.maxNumSnapshots == 0 or _config.maxNumSnapshots > MAX_SNAPSHOTS:
        return False
    if _config.maxUpsideDeviation > HUNDRED_PERCENT:
        return False
    if 0 in [_config.underlyingDecimals, _config.vaultTokenDecimals]:
        return False
    if _config.underlyingDecimals > MAX_SAFE_DECIMALS or _config.vaultTokenDecimals > MAX_SAFE_DECIMALS:
        return False

    # verify underlying asset has a price feed
    if staticcall PriceDesk(addys._getPriceDeskAddr()).getPrice(_config.underlyingAsset, False) == 0:
        return False

    if not _requireValidSnapshot:
        return True

    # verify the vault implements convertToAssets and returns a valid price
    pricePerShare: uint256 = staticcall UnderscoreVault(_asset).convertToAssets(10 ** _config.vaultTokenDecimals)
    return pricePerShare != 0


# create price config


@view
@internal
def _getPriceConfig(
    _asset: address,
    _minSnapshotDelay: uint256,
    _maxNumSnapshots: uint256,
    _maxUpsideDeviation: uint256,
    _staleTime: uint256,
) -> PriceConfig:
    underlyingAsset: address = staticcall IERC4626(_asset).asset()

    underlyingDecimals: uint256 = 0
    if underlyingAsset != empty(address):
        underlyingDecimals = convert(staticcall IERC20Detailed(underlyingAsset).decimals(), uint256)

    # vault token decimals
    vaultTokenDecimals: uint256 = 0
    if _asset != empty(address):
        vaultTokenDecimals = convert(staticcall IERC20Detailed(_asset).decimals(), uint256)

    return PriceConfig(
        underlyingAsset=underlyingAsset,
        underlyingDecimals=underlyingDecimals,
        vaultTokenDecimals=vaultTokenDecimals,
        minSnapshotDelay=_minSnapshotDelay,
        maxNumSnapshots=_maxNumSnapshots,
        maxUpsideDeviation=_maxUpsideDeviation,
        staleTime=_staleTime,
        lastSnapshot=empty(PriceSnapshot),
        nextIndex=0,
    )


@view
@internal
def _hasExpectedMetadata(_asset: address, _config: PriceConfig) -> bool:
    underlyingAsset: address = staticcall IERC4626(_asset).asset()
    if underlyingAsset != _config.underlyingAsset:
        return False
    if convert(staticcall IERC20Detailed(underlyingAsset).decimals(), uint256) != _config.underlyingDecimals:
        return False
    return convert(staticcall IERC20Detailed(_asset).decimals(), uint256) == _config.vaultTokenDecimals


#################
# Update Config #
#################


@external
def updatePriceConfig(
    _asset: address,
    _minSnapshotDelay: uint256 = 60 * 5, # 5 minutes
    _maxNumSnapshots: uint256 = 20,
    _maxUpsideDeviation: uint256 = 10_00, # 10%
    _staleTime: uint256 = 60 * 60 * 24, # 1 day
) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    p: PriceConfig = self.priceConfigs[_asset]
    p.minSnapshotDelay = _minSnapshotDelay
    p.maxNumSnapshots = _maxNumSnapshots
    p.maxUpsideDeviation = _maxUpsideDeviation
    p.staleTime = _staleTime
    assert self._isValidUpdateConfig(_asset, p) # dev: invalid config

    # set to pending state
    aid: uint256 = timeLock._initiateAction()
    self.pendingPriceConfigs[_asset] = PendingPriceConfig(actionId=aid, config=p)
    log PriceConfigUpdatePending(
        asset=_asset,
        underlyingAsset=p.underlyingAsset,
        minSnapshotDelay=p.minSnapshotDelay,
        maxNumSnapshots=p.maxNumSnapshots,
        maxUpsideDeviation=p.maxUpsideDeviation,
        staleTime=p.staleTime,
        confirmationBlock=timeLock._getActionConfirmationBlock(aid),
        actionId=aid,
    )
    return True


# confirm new feed


@external
def confirmPriceFeedUpdate(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validate again
    d: PendingPriceConfig = self.pendingPriceConfigs[_asset]
    assert d.config.underlyingAsset != empty(address) # dev: no pending config
    currentConfig: PriceConfig = self.priceConfigs[_asset]
    if not self._hasExpectedMetadata(_asset, d.config):
        self._cancelPriceFeedUpdate(_asset, d.actionId)
        return False
    requireValidSnapshot: bool = d.config.maxNumSnapshots == currentConfig.maxNumSnapshots
    if not self._isValidUpdateConfig(_asset, d.config, requireValidSnapshot):
        self._cancelPriceFeedUpdate(_asset, d.actionId)
        return False

    # check time lock
    assert timeLock._confirmAction(d.actionId) # dev: time lock not reached

    # preserve snapshot progress made while the config update was pending
    d.config.lastSnapshot = currentConfig.lastSnapshot
    if d.config.maxNumSnapshots == currentConfig.maxNumSnapshots:
        d.config.nextIndex = currentConfig.nextIndex
    else:
        d.config = self._resetSnapshots(_asset, d.config)

    # save new feed config
    self.priceConfigs[_asset] = d.config
    self.pendingPriceConfigs[_asset] = empty(PendingPriceConfig)

    log PriceConfigUpdated(
        asset=_asset,
        underlyingAsset=d.config.underlyingAsset,
        minSnapshotDelay=d.config.minSnapshotDelay,
        maxNumSnapshots=d.config.maxNumSnapshots,
        maxUpsideDeviation=d.config.maxUpsideDeviation,
        staleTime=d.config.staleTime,
    )
    return True


# cancel new feed


@external
def cancelPriceFeedUpdate(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    d: PendingPriceConfig = self.pendingPriceConfigs[_asset]
    self._cancelPriceFeedUpdate(_asset, d.actionId)
    log PriceConfigUpdateCancelled(
        asset=_asset,
        underlyingAsset=d.config.underlyingAsset,
    )
    return True


@internal
def _cancelPriceFeedUpdate(_asset: address, _aid: uint256):
    assert timeLock._cancelAction(_aid) # dev: cannot cancel action
    self.pendingPriceConfigs[_asset] = empty(PendingPriceConfig)


# validation


@view
@external
def isValidUpdateConfig(_asset: address, _maxNumSnapshots: uint256, _staleTime: uint256) -> bool:
    p: PriceConfig = self.priceConfigs[_asset]
    p.maxNumSnapshots = _maxNumSnapshots
    p.staleTime = _staleTime
    return self._isValidUpdateConfig(_asset, p)


@view
@internal
def _isValidUpdateConfig(_asset: address, _config: PriceConfig, _requireValidSnapshot: bool = True) -> bool:
    if priceData.indexOfAsset[_asset] == 0 or _config.underlyingAsset == empty(address): # must add new feed first
        return False
    return self._isValidFeedConfig(_asset, _config, _requireValidSnapshot)


################
# Disable Feed #
################


# initiate disable feed


@external
def disablePriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validation
    prevConfig: PriceConfig = self.priceConfigs[_asset]
    assert self._isValidDisablePriceFeed(_asset, prevConfig.underlyingAsset) # dev: invalid asset

    # set to pending state
    aid: uint256 = timeLock._initiateAction()
    self.pendingPriceConfigs[_asset] = PendingPriceConfig(actionId=aid, config=empty(PriceConfig))

    log DisablePriceConfigPending(
        asset=_asset,
        underlyingAsset=prevConfig.underlyingAsset,
        confirmationBlock=timeLock._getActionConfirmationBlock(aid),
        actionId=aid,
    )
    return True


# confirm disable feed


@external
def confirmDisablePriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validate again
    prevConfig: PriceConfig = self.priceConfigs[_asset]
    d: PendingPriceConfig = self.pendingPriceConfigs[_asset]
    assert d.actionId != 0 # dev: no pending disable feed
    if not self._isValidDisablePriceFeed(_asset, prevConfig.underlyingAsset):
        self._cancelDisablePriceFeed(_asset, d.actionId)
        return False

    # check time lock
    assert timeLock._confirmAction(d.actionId) # dev: time lock not reached

    # disable feed
    self.priceConfigs[_asset] = empty(PriceConfig)
    self.pendingPriceConfigs[_asset] = empty(PendingPriceConfig)
    priceData._removePricedAsset(_asset)

    log DisablePriceConfigConfirmed(
        asset=_asset,
        underlyingAsset=prevConfig.underlyingAsset,
    )
    return True


# cancel disable feed


@external
def cancelDisablePriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    self._cancelDisablePriceFeed(_asset, self.pendingPriceConfigs[_asset].actionId)
    prevConfig: PriceConfig = self.priceConfigs[_asset]
    log DisablePriceConfigCancelled(
        asset=_asset,
        underlyingAsset=prevConfig.underlyingAsset,
    )
    return True


@internal
def _cancelDisablePriceFeed(_asset: address, _aid: uint256):
    assert timeLock._cancelAction(_aid) # dev: cannot cancel action
    self.pendingPriceConfigs[_asset] = empty(PendingPriceConfig)


# validation


@view
@external
def isValidDisablePriceFeed(_asset: address) -> bool:
    return self._isValidDisablePriceFeed(_asset, self.priceConfigs[_asset].underlyingAsset)


@view
@internal
def _isValidDisablePriceFeed(_asset: address, _underlyingAsset: address) -> bool:
    if priceData.indexOfAsset[_asset] == 0:
        return False
    return _underlyingAsset != empty(address)


###################
# Price Snapshots #
###################


@internal
def _clearSnapshots(_asset: address):
    for i: uint256 in range(MAX_SNAPSHOTS):
        self.snapShots[_asset][i] = empty(PriceSnapshot)


@internal
def _resetSnapshots(_asset: address, _config: PriceConfig) -> PriceConfig:
    config: PriceConfig = _config
    newSnapshot: PriceSnapshot = self._getLatestSnapshot(_asset, config)
    assert newSnapshot.pricePerShare != 0 # dev: invalid snapshot

    self._clearSnapshots(_asset)
    self.snapShots[_asset][0] = newSnapshot
    config.lastSnapshot = newSnapshot
    config.nextIndex = 1
    if config.maxNumSnapshots == 1:
        config.nextIndex = 0

    log PricePerShareSnapshotAdded(
        asset=_asset,
        underlyingAsset=config.underlyingAsset,
        totalSupply=newSnapshot.totalSupply,
        pricePerShare=newSnapshot.pricePerShare,
    )
    return config


# get weighted price


@view
@external
def getWeightedPrice(_asset: address) -> uint256:
    config: PriceConfig = self.priceConfigs[_asset]
    return self._getWeightedPrice(_asset, config)


@view
@internal
def _getWeightedPrice(_asset: address, _config: PriceConfig) -> uint256:
    if _config.underlyingAsset == empty(address) or _config.maxNumSnapshots == 0 or _config.maxNumSnapshots > MAX_SNAPSHOTS:
        return 0
    if _config.nextIndex >= _config.maxNumSnapshots:
        return 0

    # traverse the circular ring from its next write position, which is the
    # oldest slot once full and precedes empty slots while partially filled.
    numerator: uint256 = 0
    denominator: uint256 = 0
    previous: PriceSnapshot = empty(PriceSnapshot)
    hasPrevious: bool = False
    for offset: uint256 in range(_config.maxNumSnapshots, bound=MAX_SNAPSHOTS):
        index: uint256 = _config.nextIndex + offset
        if index >= _config.maxNumSnapshots:
            index -= _config.maxNumSnapshots

        snapShot: PriceSnapshot = self.snapShots[_asset][index]
        if snapShot.pricePerShare == 0 or snapShot.totalSupply == 0 or snapShot.lastUpdate == 0:
            continue

        # too stale, skip
        if _config.staleTime != 0:
            didAdd: bool = False
            staleAt: uint256 = 0
            didAdd, staleAt = self._tryAdd(snapShot.lastUpdate, _config.staleTime)
            if not didAdd:
                return 0
            if block.timestamp > staleAt:
                continue

        if hasPrevious:
            if snapShot.lastUpdate <= previous.lastUpdate:
                return 0
            duration: uint256 = unsafe_sub(snapShot.lastUpdate, previous.lastUpdate)
            didCalculate: bool = False
            weightedValue: uint256 = 0
            didCalculate, weightedValue = self._tryMul(previous.pricePerShare, duration)
            if not didCalculate:
                return 0
            didCalculate, numerator = self._tryAdd(numerator, weightedValue)
            if not didCalculate:
                return 0
            didCalculate, denominator = self._tryAdd(denominator, duration)
            if not didCalculate:
                return 0
        previous = snapShot
        hasPrevious = True

    if hasPrevious:
        if previous.lastUpdate > block.timestamp:
            return 0
        duration: uint256 = unsafe_sub(block.timestamp, previous.lastUpdate)
        if duration != 0:
            didCalculate: bool = False
            weightedValue: uint256 = 0
            didCalculate, weightedValue = self._tryMul(previous.pricePerShare, duration)
            if not didCalculate:
                return 0
            didCalculate, numerator = self._tryAdd(numerator, weightedValue)
            if not didCalculate:
                return 0
            didCalculate, denominator = self._tryAdd(denominator, duration)
            if not didCalculate:
                return 0

    if denominator != 0:
        return numerator // denominator

    # A lone observation in its creation block has no duration yet. Fall back
    # only while the latest valid snapshot remains fresh.
    lastSnapshot: PriceSnapshot = _config.lastSnapshot
    if lastSnapshot.pricePerShare == 0 or lastSnapshot.lastUpdate == 0:
        return 0
    if _config.staleTime != 0:
        didAdd: bool = False
        staleAt: uint256 = 0
        didAdd, staleAt = self._tryAdd(lastSnapshot.lastUpdate, _config.staleTime)
        if not didAdd or block.timestamp > staleAt:
            return 0

    return lastSnapshot.pricePerShare


# add price snapshot


@external 
def addPriceSnapshot(_asset: address) -> bool:
    config: PriceConfig = self.priceConfigs[_asset]
    if config.underlyingAsset == empty(address):
        return False
    assert addys._isValidRipeAddr(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused
    return self._addPriceSnapshot(_asset, config)


@internal 
def _addPriceSnapshot(_asset: address, _config: PriceConfig) -> bool:
    config: PriceConfig = _config
    if config.underlyingAsset == empty(address):
        return False

    # already have snapshot for this time
    if config.lastSnapshot.lastUpdate == block.timestamp:
        return False

    # check if snapshot is too recent
    if config.minSnapshotDelay != 0:
        didAdd: bool = False
        nextSnapshotAt: uint256 = 0
        didAdd, nextSnapshotAt = self._tryAdd(config.lastSnapshot.lastUpdate, config.minSnapshotDelay)
        if not didAdd or nextSnapshotAt > block.timestamp:
            return False

    # create and store new snapshot
    newSnapshot: PriceSnapshot = self._getLatestSnapshot(_asset, config)
    if newSnapshot.pricePerShare == 0:
        return False
    config.lastSnapshot = newSnapshot
    self.snapShots[_asset][config.nextIndex] = newSnapshot

    # update index
    config.nextIndex += 1
    if config.nextIndex >= config.maxNumSnapshots:
        config.nextIndex = 0

    # save config data
    self.priceConfigs[_asset] = config

    log PricePerShareSnapshotAdded(
        asset=_asset,
        underlyingAsset=config.underlyingAsset,
        totalSupply=newSnapshot.totalSupply,
        pricePerShare=newSnapshot.pricePerShare,
    )
    return True


# latest snapshot


@view
@external
def getLatestSnapshot(_asset: address) -> PriceSnapshot:
    config: PriceConfig = self.priceConfigs[_asset]
    if config.underlyingAsset == empty(address):
        return empty(PriceSnapshot)
    return self._getLatestSnapshot(_asset, config)


@view
@internal
def _getLatestSnapshot(_asset: address, _config: PriceConfig) -> PriceSnapshot:
    totalSupply: uint256 = staticcall IERC20(_asset).totalSupply() // (10 ** _config.vaultTokenDecimals)
    pricePerShare: uint256 = self._getCurrentVaultPricePerShare(_asset, _config.vaultTokenDecimals)
    pricePerShare = self._throttleUpside(pricePerShare, _config.lastSnapshot.pricePerShare, _config.maxUpsideDeviation)
    return PriceSnapshot(
        totalSupply=totalSupply,
        pricePerShare=pricePerShare,
        lastUpdate=block.timestamp,
    )


@view
@internal
def _throttleUpside(_newValue: uint256, _prevValue: uint256, _maxUpside: uint256) -> uint256:
    if _maxUpside == 0 or _prevValue == 0 or _newValue == 0:
        return _newValue
    didCalculate: bool = False
    weightedUpside: uint256 = 0
    didCalculate, weightedUpside = self._tryMul(_prevValue, _maxUpside)
    if not didCalculate:
        return 0
    maxPricePerShare: uint256 = 0
    didCalculate, maxPricePerShare = self._tryAdd(_prevValue, weightedUpside // HUNDRED_PERCENT)
    if not didCalculate:
        return 0
    return min(_newValue, maxPricePerShare)


#####################
# Underscore Vaults #
#####################


@view
@internal
def _getUnderscoreVaultPrice(
    _asset: address,
    _config: PriceConfig,
    _weightedPricePerShare: uint256,
    _underlyingPrice: uint256,
) -> uint256:
    pricePerShare: uint256 = _weightedPricePerShare
    if pricePerShare == 0 or _underlyingPrice == 0:
        return 0

    # allow downside if current price per share is lower
    currentPricePerShare: uint256 = self._getCurrentVaultPricePerShare(_asset, _config.vaultTokenDecimals)
    if currentPricePerShare == 0:
        return 0
    pricePerShare = min(pricePerShare, currentPricePerShare)

    didCalculate: bool = False
    product: uint256 = 0
    didCalculate, product = self._tryMul(_underlyingPrice, pricePerShare)
    if not didCalculate:
        return 0
    return product // (10 ** _config.underlyingDecimals)


@view
@internal
def _getCurrentVaultPricePerShare(_asset: address, _decimals: uint256) -> uint256:
    return staticcall UnderscoreVault(_asset).convertToAssets(10 ** _decimals)


######################
# Checked Arithmetic #
######################


@pure
@internal
def _tryAdd(_a: uint256, _b: uint256) -> (bool, uint256):
    if _a > max_value(uint256) - _b:
        return False, 0
    return True, unsafe_add(_a, _b)


@pure
@internal
def _tryMul(_a: uint256, _b: uint256) -> (bool, uint256):
    if _a == 0 or _b == 0:
        return True, 0
    if _a > max_value(uint256) // _b:
        return False, 0
    return True, unsafe_mul(_a, _b)
