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

interface ChainlinkInterface:
    def latestRoundData() -> ChainlinkRound: view
    def decimals() -> uint8: view 

interface PriceDesk:
    def getPrice(_asset: address, _shouldRaise: bool = False) -> uint256: view

interface MissionControl:
    def getPriceStaleTime() -> uint256: view

struct ChainlinkRound:
    roundId: uint80
    answer: int256
    startedAt: uint256
    updatedAt: uint256
    answeredInRound: uint80

struct RedStoneConfig:
    feed: address
    decimals: uint256
    needsEthToUsd: bool
    staleTime: uint256

struct PendingRedStoneConfig:
    actionId: uint256
    config: RedStoneConfig

event NewRedStoneFeedPending:
    asset: indexed(address)
    feed: indexed(address)
    needsEthToUsd: bool
    staleTime: uint256
    confirmationBlock: uint256
    actionId: uint256

event NewRedStoneFeedAdded:
    asset: indexed(address)
    feed: indexed(address)
    needsEthToUsd: bool
    staleTime: uint256

event NewRedStoneFeedCancelled:
    asset: indexed(address)
    feed: indexed(address)

event RedStoneFeedUpdatePending:
    asset: indexed(address)
    feed: indexed(address)
    needsEthToUsd: bool
    staleTime: uint256
    confirmationBlock: uint256
    oldFeed: indexed(address)
    actionId: uint256

event RedStoneFeedUpdated:
    asset: indexed(address)
    feed: indexed(address)
    needsEthToUsd: bool
    staleTime: uint256
    oldFeed: indexed(address)

event RedStoneFeedUpdateCancelled:
    asset: indexed(address)
    feed: indexed(address)
    oldFeed: indexed(address)

event DisableRedStoneFeedPending:
    asset: indexed(address)
    feed: indexed(address)
    confirmationBlock: uint256
    actionId: uint256

event RedStoneFeedDisabled:
    asset: indexed(address)
    feed: indexed(address)

event DisableRedStoneFeedCancelled:
    asset: indexed(address)
    feed: indexed(address)

# config
feedConfig: public(HashMap[address, RedStoneConfig]) # asset -> config
pendingUpdates: public(HashMap[address, PendingRedStoneConfig]) # asset -> pending config

ETH: public(immutable(address))
NORMALIZED_DECIMALS: constant(uint256) = 18


@deploy
def __init__(
    _ripeHq: address,
    _tempGov: address,
    _ethAddr: address,
    _minPriceChangeTimeLock: uint256,
    _maxPriceChangeTimeLock: uint256,
):
    gov.__init__(_ripeHq, _tempGov, 0, 0, 0)
    addys.__init__(_ripeHq)
    priceData.__init__(False)
    timeLock.__init__(_minPriceChangeTimeLock, _maxPriceChangeTimeLock, 0, _maxPriceChangeTimeLock)

    # set default assets
    assert _ethAddr != empty(address) # dev: invalid addr
    ETH = _ethAddr


###############
# Core Prices #
###############


# get price


@view
@external
def getPrice(_asset: address, _staleTime: uint256 = 0, _priceDesk: address = empty(address)) -> uint256:
    config: RedStoneConfig = self.feedConfig[_asset]
    if config.feed == empty(address):
        return 0
    staleTime: uint256 = max(_staleTime, config.staleTime)
    return self._getPrice(config.feed, config.decimals, config.needsEthToUsd, staleTime, _priceDesk)


@view
@external
def getPriceAndHasFeed(_asset: address, _staleTime: uint256 = 0, _priceDesk: address = empty(address)) -> (uint256, bool):
    config: RedStoneConfig = self.feedConfig[_asset]
    if config.feed == empty(address):
        return 0, False
    staleTime: uint256 = max(_staleTime, config.staleTime)
    return self._getPrice(config.feed, config.decimals, config.needsEthToUsd, staleTime, _priceDesk), True


@view
@internal
def _getPrice(
    _feed: address, 
    _decimals: uint256,
    _needsEthToUsd: bool,
    _staleTime: uint256,
    _priceDesk: address,
) -> uint256:
    price: uint256 = self._getRedStoneData(_feed, _decimals, _staleTime)
    if price == 0:
        return 0

    # if price needs ETH -> USD conversion
    if _needsEthToUsd:
        priceDesk: address = _priceDesk
        if _priceDesk == empty(address):
            priceDesk = addys._getPriceDeskAddr()
        ethUsdPrice: uint256 = staticcall PriceDesk(priceDesk).getPrice(ETH, True)
        price = price * ethUsdPrice // (10 ** NORMALIZED_DECIMALS)

    return price


# utilities


@view
@external
def hasPriceFeed(_asset: address) -> bool:
    return self.feedConfig[_asset].feed != empty(address)


@view
@external
def hasPendingPriceFeedUpdate(_asset: address) -> bool:
    return timeLock._hasPendingAction(self.pendingUpdates[_asset].actionId)


@external 
def addPriceSnapshot(_asset: address) -> bool:
    return False


#################
# RedStone Data #
#################


@view
@external
def getRedStoneData(_feed: address, _decimals: uint256, _staleTime: uint256 = 0) -> uint256:
    return self._getRedStoneData(_feed, _decimals, _staleTime)


@view
@internal
def _getRedStoneData(_feed: address, _decimals: uint256, _staleTime: uint256) -> uint256:
    oracle: ChainlinkRound = staticcall ChainlinkInterface(_feed).latestRoundData()

    # oracle has no price
    if oracle.answer <= 0:
        return 0

    # bad decimals
    if _decimals > NORMALIZED_DECIMALS:
        return 0

    # cannot have future timestamp
    if oracle.updatedAt > block.timestamp:
        return 0

    # validate round ID
    if oracle.roundId == 0:
        return 0
    if oracle.answeredInRound < oracle.roundId:
        return 0

    # price is too stale
    if _staleTime != 0 and block.timestamp - oracle.updatedAt > _staleTime:
        return 0

    # handle decimal normalization
    price: uint256 = convert(oracle.answer, uint256)
    decimals: uint256 = _decimals
    if decimals < NORMALIZED_DECIMALS:
        decimals = NORMALIZED_DECIMALS - decimals
        price = price * (10 ** decimals)

    return price


################
# Add New Feed #
################


# initiate new feed


@external
def addNewPriceFeed(
    _asset: address, 
    _newFeed: address, 
    _staleTime: uint256 = 0,
    _needsEthToUsd: bool = False,
) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validation
    decimals: uint256 = 0
    if _newFeed != empty(address):
        decimals = convert(staticcall ChainlinkInterface(_newFeed).decimals(), uint256)
    assert self._isValidNewFeed(_asset, _newFeed, decimals, _needsEthToUsd, _staleTime) # dev: invalid feed

    # set to pending state
    aid: uint256 = timeLock._initiateAction()
    self.pendingUpdates[_asset] = PendingRedStoneConfig(
        actionId=aid,
        config=RedStoneConfig(
            feed=_newFeed,
            decimals=decimals,
            needsEthToUsd=_needsEthToUsd,
            staleTime=_staleTime,
        ),
    )

    log NewRedStoneFeedPending(asset=_asset, feed=_newFeed, needsEthToUsd=_needsEthToUsd, staleTime=_staleTime, confirmationBlock=timeLock._getActionConfirmationBlock(aid), actionId=aid)
    return True


# confirm new feed


@external
def confirmNewPriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validate again
    d: PendingRedStoneConfig = self.pendingUpdates[_asset]
    assert d.config.feed != empty(address) # dev: no pending new feed
    if not self._isValidNewFeed(_asset, d.config.feed, d.config.decimals, d.config.needsEthToUsd, d.config.staleTime):
        self._cancelNewPendingPriceFeed(_asset, d.actionId)
        return False

    # check time lock
    assert timeLock._confirmAction(d.actionId) # dev: time lock not reached

    # save new feed config
    self.feedConfig[_asset] = d.config
    self.pendingUpdates[_asset] = empty(PendingRedStoneConfig)
    priceData._addPricedAsset(_asset)

    log NewRedStoneFeedAdded(asset=_asset, feed=d.config.feed, needsEthToUsd=d.config.needsEthToUsd, staleTime=d.config.staleTime)
    return True


# cancel new feed


@external
def cancelNewPendingPriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    d: PendingRedStoneConfig = self.pendingUpdates[_asset]
    self._cancelNewPendingPriceFeed(_asset, d.actionId)
    log NewRedStoneFeedCancelled(asset=_asset, feed=d.config.feed)
    return True


@internal
def _cancelNewPendingPriceFeed(_asset: address, _aid: uint256):
    assert timeLock._cancelAction(_aid) # dev: cannot cancel action
    self.pendingUpdates[_asset] = empty(PendingRedStoneConfig)


# validation


@view
@external
def isValidNewFeed(_asset: address, _newFeed: address, _decimals: uint256, _needsEthToUsd: bool, _staleTime: uint256) -> bool:
    return self._isValidNewFeed(_asset, _newFeed, _decimals, _needsEthToUsd, _staleTime)


@view
@internal
def _isValidNewFeed(_asset: address, _newFeed: address, _decimals: uint256, _needsEthToUsd: bool, _staleTime: uint256) -> bool:
    if priceData.indexOfAsset[_asset] != 0 or self.feedConfig[_asset].feed != empty(address): # use the `updatePriceFeed` function instead
        return False
    return self._isValidFeedConfig(_asset, _newFeed, _decimals, _needsEthToUsd, _staleTime)


###############
# Update Feed #
###############


# initiate update feed


@external
def updatePriceFeed(
    _asset: address, 
    _newFeed: address, 
    _staleTime: uint256 = 0,
    _needsEthToUsd: bool = False,
) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validation
    decimals: uint256 = 0
    if _newFeed != empty(address):
        decimals = convert(staticcall ChainlinkInterface(_newFeed).decimals(), uint256)
    oldFeed: address = self.feedConfig[_asset].feed
    assert self._isValidUpdateFeed(_asset, _newFeed, oldFeed, decimals, _needsEthToUsd, _staleTime) # dev: invalid feed

    # set to pending state
    aid: uint256 = timeLock._initiateAction()
    self.pendingUpdates[_asset] = PendingRedStoneConfig(
        actionId=aid,
        config=RedStoneConfig(
            feed=_newFeed,
            decimals=decimals,
            needsEthToUsd=_needsEthToUsd,
            staleTime=_staleTime,
        ),
    )
    log RedStoneFeedUpdatePending(asset=_asset, feed=_newFeed, needsEthToUsd=_needsEthToUsd, staleTime=_staleTime, confirmationBlock=timeLock._getActionConfirmationBlock(aid), oldFeed=oldFeed, actionId=aid)
    return True


# confirm update feed


@external
def confirmPriceFeedUpdate(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validate again
    d: PendingRedStoneConfig = self.pendingUpdates[_asset]
    assert d.config.feed != empty(address) # dev: no pending update feed
    oldFeed: address = self.feedConfig[_asset].feed
    if not self._isValidUpdateFeed(_asset, d.config.feed, oldFeed, d.config.decimals, d.config.needsEthToUsd, d.config.staleTime):
        self._cancelPriceFeedUpdate(_asset, d.actionId)
        return False

    # check time lock
    assert timeLock._confirmAction(d.actionId) # dev: time lock not reached

    # save new feed config
    self.feedConfig[_asset] = d.config
    self.pendingUpdates[_asset] = empty(PendingRedStoneConfig)

    log RedStoneFeedUpdated(asset=_asset, feed=d.config.feed, needsEthToUsd=d.config.needsEthToUsd, staleTime=d.config.staleTime, oldFeed=oldFeed)
    return True


# cancel update feed


@external
def cancelPriceFeedUpdate(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    d: PendingRedStoneConfig = self.pendingUpdates[_asset]
    self._cancelPriceFeedUpdate(_asset, d.actionId)
    log RedStoneFeedUpdateCancelled(asset=_asset, feed=d.config.feed, oldFeed=self.feedConfig[_asset].feed)
    return True


@internal
def _cancelPriceFeedUpdate(_asset: address, _aid: uint256):
    assert timeLock._cancelAction(_aid) # dev: cannot cancel action
    self.pendingUpdates[_asset] = empty(PendingRedStoneConfig)


# validation


@view
@external
def isValidUpdateFeed(_asset: address, _newFeed: address, _decimals: uint256, _needsEthToUsd: bool, _staleTime: uint256) -> bool:
    return self._isValidUpdateFeed(_asset, _newFeed, self.feedConfig[_asset].feed, _decimals, _needsEthToUsd, _staleTime)


@view
@internal
def _isValidUpdateFeed(_asset: address, _newFeed: address, _oldFeed: address, _decimals: uint256, _needsEthToUsd: bool, _staleTime: uint256) -> bool:
    if _newFeed == _oldFeed:
        return False
    if priceData.indexOfAsset[_asset] == 0 or _oldFeed == empty(address): # use the `addNewPriceFeed` function instead
        return False
    return self._isValidFeedConfig(_asset, _newFeed, _decimals, _needsEthToUsd, _staleTime)


@view
@internal
def _isValidFeedConfig(
    _asset: address, 
    _feed: address,
    _decimals: uint256,
    _needsEthToUsd: bool,
    _staleTime: uint256,
) -> bool:
    if empty(address) in [_asset, _feed]:
        return False

    staleTime: uint256 = _staleTime
    missionControl: address = addys._getMissionControlAddr()
    if missionControl != empty(address):
        staleTime = max(staleTime, staticcall MissionControl(missionControl).getPriceStaleTime())

    return self._getPrice(_feed, _decimals, _needsEthToUsd, staleTime) != 0


################
# Disable Feed #
################


# initiate disable feed


@external
def disablePriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validation
    oldFeed: address = self.feedConfig[_asset].feed
    assert self._isValidDisablePriceFeed(_asset, oldFeed) # dev: invalid asset

    # set to pending state
    aid: uint256 = timeLock._initiateAction()
    self.pendingUpdates[_asset] = PendingRedStoneConfig(
        actionId=aid,
        config=empty(RedStoneConfig),
    )

    log DisableRedStoneFeedPending(asset=_asset, feed=oldFeed, confirmationBlock=timeLock._getActionConfirmationBlock(aid), actionId=aid)
    return True


# confirm disable feed


@external
def confirmDisablePriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validate again
    oldFeed: address = self.feedConfig[_asset].feed
    d: PendingRedStoneConfig = self.pendingUpdates[_asset]
    assert d.actionId != 0 # dev: no pending disable feed
    if not self._isValidDisablePriceFeed(_asset, oldFeed):
        self._cancelDisablePriceFeed(_asset, d.actionId)
        return False

    # check time lock
    assert timeLock._confirmAction(d.actionId) # dev: time lock not reached

    # disable feed
    self.feedConfig[_asset] = empty(RedStoneConfig)
    self.pendingUpdates[_asset] = empty(PendingRedStoneConfig)
    priceData._removePricedAsset(_asset)
    
    log RedStoneFeedDisabled(asset=_asset, feed=oldFeed)
    return True


# cancel disable feed


@external
def cancelDisablePriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    self._cancelDisablePriceFeed(_asset, self.pendingUpdates[_asset].actionId)
    log DisableRedStoneFeedCancelled(asset=_asset, feed=self.feedConfig[_asset].feed)
    return True


@internal
def _cancelDisablePriceFeed(_asset: address, _aid: uint256):
    assert timeLock._cancelAction(_aid) # dev: cannot cancel action
    self.pendingUpdates[_asset] = empty(PendingRedStoneConfig)


# validation


@view
@external
def isValidDisablePriceFeed(_asset: address) -> bool:
    return self._isValidDisablePriceFeed(_asset, self.feedConfig[_asset].feed)


@view
@internal
def _isValidDisablePriceFeed(_asset: address, _oldFeed: address) -> bool:
    if priceData.indexOfAsset[_asset] == 0:
        return False
    if _oldFeed == empty(address):
        return False
    return _asset != ETH
