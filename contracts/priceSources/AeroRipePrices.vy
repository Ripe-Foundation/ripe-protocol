# Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
# Ripe Foundation (C) 2025

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
from ethereum.ercs import IERC20

struct PriceConfig:
    minSnapshotDelay: uint256
    maxNumSnapshots: uint256
    maxUpsideDeviation: uint256
    staleTime: uint256
    lastSnapshot: PriceSnapshot
    nextIndex: uint256

struct PriceSnapshot:
    totalSupply: uint256
    price: uint256
    lastUpdate: uint256

struct PendingPriceConfig:
    actionId: uint256
    config: PriceConfig

event PriceConfigUpdatePending:
    asset: indexed(address)
    minSnapshotDelay: uint256
    maxNumSnapshots: uint256
    maxUpsideDeviation: uint256
    staleTime: uint256
    confirmationBlock: uint256
    actionId: uint256

# data 
priceConfigs: public(HashMap[address, PriceConfig]) # asset -> config
snapShots: public(HashMap[address, HashMap[uint256, PriceSnapshot]]) # asset -> index -> snapshot
pendingPriceConfigs: public(HashMap[address, PendingPriceConfig]) # asset -> pending config

HUNDRED_PERCENT: constant(uint256) = 100_00 # 100%

RIPE_TOKEN: public(immutable(address))
WETH_TOKEN: public(immutable(address))


@deploy
def __init__(
    _ripeHq: address,
    _tempGov: address,
    _minPriceChangeTimeLock: uint256,
    _maxPriceChangeTimeLock: uint256,
    _ripeToken: address,
    _wethToken: address,
):
    gov.__init__(_ripeHq, _tempGov, 0, 0, 0)
    addys.__init__(_ripeHq)
    priceData.__init__(False)
    timeLock.__init__(_minPriceChangeTimeLock, _maxPriceChangeTimeLock, 0, _maxPriceChangeTimeLock)

    RIPE_TOKEN = _ripeToken
    WETH_TOKEN = _wethToken

    # set ripe token config
    self.priceConfigs[RIPE_TOKEN] = PriceConfig(
        minSnapshotDelay = 60 * 5, # 5 minutes
        maxNumSnapshots = 20,
        maxUpsideDeviation = 10_00, # 10%
        staleTime = 0,
        lastSnapshot = empty(PriceSnapshot),
        nextIndex = 0,
    )
    priceData._addPricedAsset(RIPE_TOKEN)


###############
# Core Prices #
###############


# get price


@view
@external
def getPrice(_asset: address, _staleTime: uint256 = 0, _priceDesk: address = empty(address)) -> uint256:
    ripe: address = RIPE_TOKEN
    if _asset != ripe:
        return 0
    config: PriceConfig = self.priceConfigs[ripe]
    return self._getPrice(_asset, config, _priceDesk)


@view
@external
def getPriceAndHasFeed(_asset: address, _staleTime: uint256 = 0, _priceDesk: address = empty(address)) -> (uint256, bool):
    ripe: address = RIPE_TOKEN
    if _asset != ripe:
        return 0, False
    config: PriceConfig = self.priceConfigs[ripe]
    return self._getPrice(_asset, config, _priceDesk), True


@view
@internal
def _getPrice(_asset: address, _config: PriceConfig, _priceDesk: address) -> uint256:
    # NOTE: not using Mission Control `_staleTime` in this contract.
    # Config here has its own stale time.

    weightedPrice: uint256 = self._getWeightedPrice(_asset, _config)
    currentPrice: uint256 = self._getAeroRipePrice()

    return min(weightedPrice, currentPrice)


# utilities


@view
@external
def hasPriceFeed(_asset: address) -> bool:
    return _asset == RIPE_TOKEN


@view
@external
def hasPendingPriceFeedUpdate(_asset: address) -> bool:
    return timeLock._hasPendingAction(self.pendingPriceConfigs[RIPE_TOKEN].actionId)


###################
# Aero Ripe Price #
###################


@view
@external
def _getAeroRipePrice() -> uint256:
    return 0 # TODO: aero price


#################
# Update Config #
#################


@external
def updatePriceConfig(
    _minSnapshotDelay: uint256,
    _maxNumSnapshots: uint256,
    _maxUpsideDeviation: uint256,
    _staleTime: uint256,
) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    p: PriceConfig = self.priceConfigs[RIPE_TOKEN]
    p.minSnapshotDelay = _minSnapshotDelay
    p.maxNumSnapshots = _maxNumSnapshots
    p.maxUpsideDeviation = _maxUpsideDeviation
    p.staleTime = _staleTime
    assert self._isValidPriceConfig(p) # dev: invalid config

    # set to pending state
    aid: uint256 = timeLock._initiateAction()
    self.pendingPriceConfigs[RIPE_TOKEN] = PendingPriceConfig(actionId=aid, config=p)
    log PriceConfigUpdatePending(
        asset=RIPE_TOKEN,
        minSnapshotDelay=p.minSnapshotDelay,
        maxNumSnapshots=p.maxNumSnapshots,
        maxUpsideDeviation=p.maxUpsideDeviation,
        staleTime=p.staleTime,
        confirmationBlock=timeLock._getActionConfirmationBlock(aid),
        actionId=aid,
    )
    return True


# validation


@view
@external
def isValidPriceConfig(
    _minSnapshotDelay: uint256,
    _maxNumSnapshots: uint256,
    _maxUpsideDeviation: uint256,
    _staleTime: uint256,
) -> bool:
    p: PriceConfig = self.priceConfigs[RIPE_TOKEN]
    p.minSnapshotDelay = _minSnapshotDelay
    p.maxNumSnapshots = _maxNumSnapshots
    p.maxUpsideDeviation = _maxUpsideDeviation
    p.staleTime = _staleTime
    return self._isValidPriceConfig(p)


@view
@internal
def _isValidPriceConfig(_config: PriceConfig) -> bool:
    if _config.minSnapshotDelay > (60 * 60 * 24 * 7): # 1 week
        return False
    if _config.maxNumSnapshots == 0 or _config.maxNumSnapshots > 25:
        return False
    return _config.maxUpsideDeviation <= HUNDRED_PERCENT


###################
# Price Snapshots #
###################


# get weighted price


@view
@external
def getWeightedPrice(_asset: address) -> uint256:
    ripe: address = RIPE_TOKEN
    if _asset != ripe:
        return 0
    config: PriceConfig = self.priceConfigs[ripe]
    return self._getWeightedPrice(_asset, config)


@view
@internal
def _getWeightedPrice(_asset: address, _config: PriceConfig) -> uint256:
    if _config.maxNumSnapshots == 0:
        return 0

    # calculate weighted average price using all valid snapshots
    numerator: uint256 = 0
    denominator: uint256 = 0
    for i: uint256 in range(_config.maxNumSnapshots, bound=max_value(uint256)):

        snapShot: PriceSnapshot = self.snapShots[_asset][i]
        if snapShot.price == 0 or snapShot.totalSupply == 0 or snapShot.lastUpdate == 0:
            continue

        # too stale, skip
        if _config.staleTime != 0 and block.timestamp > snapShot.lastUpdate + _config.staleTime:
            continue

        numerator += (snapShot.totalSupply * snapShot.price)
        denominator += snapShot.totalSupply

    # weighted price per share
    weightedPricePerShare: uint256 = 0
    if numerator != 0:
        weightedPricePerShare = numerator // denominator
    else:
        weightedPricePerShare = _config.lastSnapshot.pricePerShare

    return weightedPricePerShare


# add price snapshot


@external 
def addPriceSnapshot(_asset: address) -> bool:
    assert addys._isValidRipeAddr(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused
    return self._addPriceSnapshot(_asset, self.priceConfigs[_asset])


@internal 
def _addPriceSnapshot(_asset: address, _config: PriceConfig) -> bool:
    config: PriceConfig = _config
    if config.underlyingAsset == empty(address):
        return False

    # aave v3 and compound v3 - not using snapshots
    if _config.protocol == Protocol.COMPOUND_V3 or _config.protocol == Protocol.AAVE_V3:
        return False

    # already have snapshot for this time
    if config.lastSnapshot.lastUpdate == block.timestamp:
        return False

    # check if snapshot is too recent
    if config.lastSnapshot.lastUpdate + config.minSnapshotDelay > block.timestamp:
        return False

    # create and store new snapshot
    newSnapshot: PriceSnapshot = self._getLatestSnapshot(_asset, config)
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
    return self._getLatestSnapshot(_asset, self.priceConfigs[_asset])


@view
@internal
def _getLatestSnapshot(_asset: address, _config: PriceConfig) -> PriceSnapshot:
    totalSupply: uint256 = staticcall IERC20(_asset).totalSupply() // (10 ** _config.vaultTokenDecimals)
    pricePerShare: uint256 = 0

    # erc4626 vaults
    if _config.protocol == Protocol.MORPHO or _config.protocol == Protocol.EULER or _config.protocol == Protocol.FLUID:
        pricePerShare = self._getCurrentErc4626PricePerShare(_asset, _config.vaultTokenDecimals)

    # moonwell
    elif _config.protocol == Protocol.MOONWELL:
        pricePerShare = self._getCurrentMoonwellPricePerShare(_asset, _config.vaultTokenDecimals)

    # TODO: implement rest of protocols

    # throttle upside (extra safety check)
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
    maxPricePerShare: uint256 = _prevValue + (_prevValue * _maxUpside // HUNDRED_PERCENT)
    return min(_newValue, maxPricePerShare)


# other


@external
def confirmNewPriceFeed(_asset: address) -> bool:
    return True


@external
def cancelNewPendingPriceFeed(_asset: address) -> bool:
    return True


@external
def confirmPriceFeedUpdate(_asset: address) -> bool:
    return True


@external
def cancelPriceFeedUpdate(_asset: address) -> bool:
    return True


@external
def disablePriceFeed(_asset: address) -> bool:
    return True


@external
def confirmDisablePriceFeed(_asset: address) -> bool:
    return True


@external
def cancelDisablePriceFeed(_asset: address) -> bool:
    return True
