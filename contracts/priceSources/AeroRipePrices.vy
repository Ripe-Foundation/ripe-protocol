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
from ethereum.ercs import IERC20Detailed

interface AeroClassicPool:
    def getReserves() -> (uint256, uint256, uint256): view
    def tokens() -> (address, address): view

interface PriceDesk:
    def getPrice(_asset: address, _shouldRaise: bool = False) -> uint256: view

struct PriceConfig:
    minSnapshotDelay: uint256
    maxNumSnapshots: uint256
    maxUpsideDeviation: uint256
    staleTime: uint256
    lastSnapshot: PriceSnapshot
    nextIndex: uint256

struct PriceSnapshot:
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

event PriceSnapshotAdded:
    asset: indexed(address)
    price: uint256
    lastUpdate: uint256

# data 
priceConfigs: public(HashMap[address, PriceConfig]) # asset -> config
snapShots: public(HashMap[address, HashMap[uint256, PriceSnapshot]]) # asset -> index -> snapshot
pendingPriceConfigs: public(HashMap[address, PendingPriceConfig]) # asset -> pending config

HUNDRED_PERCENT: constant(uint256) = 100_00
EIGHTEEN_DECIMALS: constant(uint256) = 10 ** 18

RIPE_WETH_POOL: public(immutable(address))
RIPE_TOKEN: public(immutable(address))


@deploy
def __init__(
    _ripeHq: address,
    _tempGov: address,
    _ripeWethPool: address,
    _ripeToken: address,
    _minPriceChangeTimeLock: uint256,
    _maxPriceChangeTimeLock: uint256,
):
    gov.__init__(_ripeHq, _tempGov, 0, 0, 0)
    addys.__init__(_ripeHq)
    priceData.__init__(False)
    timeLock.__init__(_minPriceChangeTimeLock, _maxPriceChangeTimeLock, 0, _maxPriceChangeTimeLock)

    RIPE_WETH_POOL = _ripeWethPool
    RIPE_TOKEN = _ripeToken

    # set ripe token config
    if _ripeToken != empty(address):
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
    return self._getPrice(ripe, config, _priceDesk)


@view
@external
def getPriceAndHasFeed(_asset: address, _staleTime: uint256 = 0, _priceDesk: address = empty(address)) -> (uint256, bool):
    ripe: address = RIPE_TOKEN
    if _asset != ripe:
        return 0, False
    config: PriceConfig = self.priceConfigs[ripe]
    return self._getPrice(ripe, config, _priceDesk), True


@view
@internal
def _getPrice(_asset: address, _config: PriceConfig, _priceDesk: address) -> uint256:
    # NOTE: not using Mission Control `_staleTime` in this contract.
    # Config here has its own stale time.

    price: uint256 = self._getAeroRipePrice(_asset, _priceDesk)

    weightedPrice: uint256 = self._getWeightedPrice(_asset, _config)
    if weightedPrice != 0:
        price = min(weightedPrice, price)

    return price


# utilities


@view
@external
def hasPriceFeed(_asset: address) -> bool:
    return _asset == RIPE_TOKEN


@view
@external
def hasPendingPriceFeedUpdate(_asset: address) -> bool:
    ripe: address = RIPE_TOKEN
    if _asset != ripe:
        return False
    return timeLock._hasPendingAction(self.pendingPriceConfigs[ripe].actionId)


###################
# Aero Ripe Price #
###################


@view
@external
def getAeroRipePrice(_asset: address) -> uint256:
    ripe: address = RIPE_TOKEN
    if _asset != ripe:
        return 0
    return self._getAeroRipePrice(ripe, addys._getPriceDeskAddr())


@view
@internal
def _getAeroRipePrice(_asset: address, _priceDesk: address) -> uint256:
    pool: address = RIPE_WETH_POOL

    token0: address = empty(address)
    token1: address = empty(address)
    token0, token1 = staticcall AeroClassicPool(pool).tokens()

    # alt price
    altPrice: uint256 = 0
    if _asset == token0:
        altPrice = staticcall PriceDesk(_priceDesk).getPrice(token1, False)
    else:
        altPrice = staticcall PriceDesk(_priceDesk).getPrice(token0, False)

    # return early if no alt price
    if altPrice == 0:
        return 0

    # reserves
    reserve0: uint256 = 0
    reserve1: uint256 = 0
    na: uint256 = 0
    reserve0, reserve1, na = staticcall AeroClassicPool(pool).getReserves()

    # avoid division by zero
    if reserve0 == 0 or reserve1 == 0:
        return 0  

    # price of token0 in token1
    priceZeroToOne: uint256 = reserve1 * EIGHTEEN_DECIMALS // reserve0

    # adjust for decimals: price should be in 18 decimals
    decimals0: uint256 = convert(staticcall IERC20Detailed(token0).decimals(), uint256)
    decimals1: uint256 = convert(staticcall IERC20Detailed(token1).decimals(), uint256)
    if decimals0 > decimals1:
        scaleFactor: uint256 = 10 ** (decimals0 - decimals1)
        priceZeroToOne = priceZeroToOne * scaleFactor
    elif decimals1 > decimals0:
        scaleFactor: uint256 = 10 ** (decimals1 - decimals0)
        priceZeroToOne = priceZeroToOne // scaleFactor

    # if _asset is token1, make price inverse
    priceToOther: uint256 = priceZeroToOne
    if _asset == token1:
        priceToOther = EIGHTEEN_DECIMALS * EIGHTEEN_DECIMALS // priceZeroToOne

    return altPrice * priceToOther // EIGHTEEN_DECIMALS


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
    return self._getWeightedPrice(ripe, config)


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
        if snapShot.price == 0 or snapShot.lastUpdate == 0:
            continue

        # too stale, skip
        if _config.staleTime != 0 and block.timestamp > snapShot.lastUpdate + _config.staleTime:
            continue

        numerator += snapShot.price
        denominator += 1

    # weighted price
    weightedPrice: uint256 = 0
    if numerator != 0:
        weightedPrice = numerator // denominator
    else:
        weightedPrice = _config.lastSnapshot.price

    return weightedPrice


# add price snapshot


@external 
def addPriceSnapshot(_asset: address) -> bool:
    ripe: address = RIPE_TOKEN
    if _asset != ripe:
        return False

    assert addys._isValidRipeAddr(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused
    return self._addPriceSnapshot(ripe, self.priceConfigs[ripe])


@internal 
def _addPriceSnapshot(_asset: address, _config: PriceConfig) -> bool:
    config: PriceConfig = _config

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

    log PriceSnapshotAdded(
        asset=_asset,
        price=newSnapshot.price,
        lastUpdate=newSnapshot.lastUpdate,
    )
    return True


# latest snapshot


@view
@external
def getLatestSnapshot(_asset: address) -> PriceSnapshot:
    ripe: address = RIPE_TOKEN
    if _asset != ripe:
        return empty(PriceSnapshot)
    return self._getLatestSnapshot(ripe, self.priceConfigs[ripe])


@view
@internal
def _getLatestSnapshot(_asset: address, _config: PriceConfig) -> PriceSnapshot:
    price: uint256 = self._getAeroRipePrice(_asset, addys._getPriceDeskAddr())

    # throttle upside (extra safety check)
    price = self._throttleUpside(price, _config.lastSnapshot.price, _config.maxUpsideDeviation)

    return PriceSnapshot(
        price=price,
        lastUpdate=block.timestamp,
    )


@view
@internal
def _throttleUpside(_newValue: uint256, _prevValue: uint256, _maxUpside: uint256) -> uint256:
    if _maxUpside == 0 or _prevValue == 0 or _newValue == 0:
        return _newValue
    maxPrice: uint256 = _prevValue + (_prevValue * _maxUpside // HUNDRED_PERCENT)
    return min(_newValue, maxPrice)


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
