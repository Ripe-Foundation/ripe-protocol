# @version 0.4.1

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

interface ChainlinkFeed:
    def latestRoundData() -> ChainlinkRound: view
    def decimals() -> uint8: view 

interface ControlRoom:
    def getPriceStaleTime() -> uint256: view

struct ChainlinkRound:
    roundId: uint80
    answer: int256
    startedAt: uint256
    updatedAt: uint256
    answeredInRound: uint80

struct ChainlinkConfig:
    feed: address
    decimals: uint256
    needsEthToUsd: bool
    needsBtcToUsd: bool

struct PendingChainlinkConfig:
    actionId: uint256
    config: ChainlinkConfig

event NewChainlinkFeedPending:
    asset: indexed(address)
    feed: indexed(address)
    needsEthToUsd: bool
    needsBtcToUsd: bool
    confirmationBlock: uint256
    actionId: uint256

event NewChainlinkFeedAdded:
    asset: indexed(address)
    feed: indexed(address)
    needsEthToUsd: bool
    needsBtcToUsd: bool

event NewChainlinkFeedCancelled:
    asset: indexed(address)
    feed: indexed(address)

event ChainlinkFeedUpdatePending:
    asset: indexed(address)
    feed: indexed(address)
    needsEthToUsd: bool
    needsBtcToUsd: bool
    confirmationBlock: uint256
    oldFeed: indexed(address)
    actionId: uint256

event ChainlinkFeedUpdated:
    asset: indexed(address)
    feed: indexed(address)
    needsEthToUsd: bool
    needsBtcToUsd: bool
    oldFeed: indexed(address)

event ChainlinkFeedUpdateCancelled:
    asset: indexed(address)
    feed: indexed(address)
    oldFeed: indexed(address)

event DisableChainlinkFeedPending:
    asset: indexed(address)
    feed: indexed(address)
    confirmationBlock: uint256
    actionId: uint256

event ChainlinkFeedDisabled:
    asset: indexed(address)
    feed: indexed(address)

event DisableChainlinkFeedCancelled:
    asset: indexed(address)
    feed: indexed(address)

# core config
feedConfig: public(HashMap[address, ChainlinkConfig]) # asset -> config

# pending changes
pendingUpdates: public(HashMap[address, PendingChainlinkConfig]) # asset -> config

# default assets
WETH: public(immutable(address))
ETH: public(immutable(address))
BTC: public(immutable(address))

NORMALIZED_DECIMALS: constant(uint256) = 18


@deploy
def __init__(
    _ripeHq: address,
    _minPriceChangeTimeLock: uint256,
    _maxPriceChangeTimeLock: uint256,
    _wethAddr: address,
    _ethAddr: address,
    _btcAddr: address,
    _ethUsdFeed: address,
    _btcUsdFeed: address,
):
    gov.__init__(_ripeHq, empty(address), 0, 0, 0)
    addys.__init__(_ripeHq)
    priceData.__init__(False)
    timeLock.__init__(_minPriceChangeTimeLock, _maxPriceChangeTimeLock, 0)

    # set default assets
    assert empty(address) not in [_wethAddr, _ethAddr, _btcAddr] # dev: invalid asset addrs
    WETH = _wethAddr
    ETH = _ethAddr
    BTC = _btcAddr

    # set default feeds
    if _ethUsdFeed != empty(address):
        assert self._setDefaultFeedOnDeploy(_ethAddr, _ethUsdFeed) # dev: invalid feed
        assert self._setDefaultFeedOnDeploy(_wethAddr, _ethUsdFeed) # dev: invalid feed
    if _btcUsdFeed != empty(address):
        assert self._setDefaultFeedOnDeploy(_btcAddr, _btcUsdFeed) # dev: invalid feed


# set default feeds


@internal
def _setDefaultFeedOnDeploy(_asset: address, _newFeed: address) -> bool:
    decimals: uint256 = convert(staticcall ChainlinkFeed(_newFeed).decimals(), uint256)
    if not self._isValidNewFeed(_asset, _newFeed, decimals, False, False):
        return False
    self.feedConfig[_asset] = ChainlinkConfig(
        feed=_newFeed,
        decimals=decimals,
        needsEthToUsd=False,
        needsBtcToUsd=False,
    )
    priceData._addPricedAsset(_asset)
    return True


###############
# Core Prices #
###############


# get price


@view
@external
def getPrice(_asset: address, _staleTime: uint256 = 0, _priceDesk: address = empty(address)) -> uint256:
    config: ChainlinkConfig = self.feedConfig[_asset]
    if config.feed == empty(address):
        return 0
    return self._getPrice(config.feed, config.decimals, config.needsEthToUsd, config.needsBtcToUsd, _staleTime)


@view
@external
def getPriceAndHasFeed(_asset: address, _staleTime: uint256 = 0, _priceDesk: address = empty(address)) -> (uint256, bool):
    config: ChainlinkConfig = self.feedConfig[_asset]
    if config.feed == empty(address):
        return 0, False
    return self._getPrice(config.feed, config.decimals, config.needsEthToUsd, config.needsBtcToUsd, _staleTime), True


@view
@internal
def _getPrice(
    _feed: address, 
    _decimals: uint256,
    _needsEthToUsd: bool,
    _needsBtcToUsd: bool,
    _staleTime: uint256,
) -> uint256:
    price: uint256 = self._getChainlinkData(_feed, _decimals, _staleTime)
    if price == 0:
        return 0

    # if price needs ETH -> USD conversion
    if _needsEthToUsd:
        ethConfig: ChainlinkConfig = self.feedConfig[ETH]
        ethUsdPrice: uint256 = self._getChainlinkData(ethConfig.feed, ethConfig.decimals, _staleTime)
        price = price * ethUsdPrice // (10 ** NORMALIZED_DECIMALS)

    # if price needs BTC -> USD conversion
    elif _needsBtcToUsd:
        btcConfig: ChainlinkConfig = self.feedConfig[BTC]
        btcUsdPrice: uint256 = self._getChainlinkData(btcConfig.feed, btcConfig.decimals, _staleTime)
        price = price * btcUsdPrice // (10 ** NORMALIZED_DECIMALS)

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


##################
# Chainlink Data #
##################


@view
@external
def getChainlinkData(_feed: address, _decimals: uint256, _staleTime: uint256 = 0) -> uint256:
    return self._getChainlinkData(_feed, _decimals, _staleTime)


@view
@internal
def _getChainlinkData(_feed: address, _decimals: uint256, _staleTime: uint256) -> uint256:
    oracle: ChainlinkRound = staticcall ChainlinkFeed(_feed).latestRoundData()

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
    _needsEthToUsd: bool = False,
    _needsBtcToUsd: bool = False,
) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validation
    decimals: uint256 = 0
    if _newFeed != empty(address):
        decimals = convert(staticcall ChainlinkFeed(_newFeed).decimals(), uint256)
    assert self._isValidNewFeed(_asset, _newFeed, decimals, _needsEthToUsd, _needsBtcToUsd) # dev: invalid feed

    # set to pending state
    aid: uint256 = timeLock._initiateAction()
    self.pendingUpdates[_asset] = PendingChainlinkConfig(
        actionId=aid,
        config=ChainlinkConfig(
            feed=_newFeed,
            decimals=decimals,
            needsEthToUsd=_needsEthToUsd,
            needsBtcToUsd=_needsBtcToUsd,
        ),
    )

    log NewChainlinkFeedPending(asset=_asset, feed=_newFeed, needsEthToUsd=_needsEthToUsd, needsBtcToUsd=_needsBtcToUsd, confirmationBlock=timeLock._getActionConfirmationBlock(aid), actionId=aid)
    return True


# confirm new feed


@external
def confirmNewPriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validate again
    d: PendingChainlinkConfig = self.pendingUpdates[_asset]
    assert d.config.feed != empty(address) # dev: no pending new feed
    if not self._isValidNewFeed(_asset, d.config.feed, d.config.decimals, d.config.needsEthToUsd, d.config.needsBtcToUsd):
        self._cancelNewPendingPriceFeed(_asset, d.actionId)
        return False

    # check time lock
    assert timeLock._confirmAction(d.actionId) # dev: time lock not reached

    # save new feed config
    self.feedConfig[_asset] = d.config
    self.pendingUpdates[_asset] = empty(PendingChainlinkConfig)
    priceData._addPricedAsset(_asset)

    log NewChainlinkFeedAdded(asset=_asset, feed=d.config.feed, needsEthToUsd=d.config.needsEthToUsd, needsBtcToUsd=d.config.needsBtcToUsd)
    return True


# cancel new feed


@external
def cancelNewPendingPriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    d: PendingChainlinkConfig = self.pendingUpdates[_asset]
    self._cancelNewPendingPriceFeed(_asset, d.actionId)
    log NewChainlinkFeedCancelled(asset=_asset, feed=d.config.feed)
    return True


@internal
def _cancelNewPendingPriceFeed(_asset: address, _aid: uint256):
    assert timeLock._cancelAction(_aid) # dev: cannot cancel action
    self.pendingUpdates[_asset] = empty(PendingChainlinkConfig)


# validation


@view
@external
def isValidNewFeed(_asset: address, _newFeed: address, _decimals: uint256, _needsEthToUsd: bool, _needsBtcToUsd: bool) -> bool:
    return self._isValidNewFeed(_asset, _newFeed, _decimals, _needsEthToUsd, _needsBtcToUsd)


@view
@internal
def _isValidNewFeed(_asset: address, _newFeed: address, _decimals: uint256, _needsEthToUsd: bool, _needsBtcToUsd: bool) -> bool:
    if priceData.indexOfAsset[_asset] != 0 or self.feedConfig[_asset].feed != empty(address): # use the `updatePriceFeed` function instead
        return False
    return self._isValidFeedConfig(_asset, _newFeed, _decimals, _needsEthToUsd, _needsBtcToUsd)


###############
# Update Feed #
###############


# initiate update feed


@external
def updatePriceFeed(
    _asset: address, 
    _newFeed: address, 
    _needsEthToUsd: bool = False,
    _needsBtcToUsd: bool = False,
) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validation
    decimals: uint256 = 0
    if _newFeed != empty(address):
        decimals = convert(staticcall ChainlinkFeed(_newFeed).decimals(), uint256)
    oldFeed: address = self.feedConfig[_asset].feed
    assert self._isValidUpdateFeed(_asset, _newFeed, oldFeed, decimals, _needsEthToUsd, _needsBtcToUsd) # dev: invalid feed

    # set to pending state
    aid: uint256 = timeLock._initiateAction()
    self.pendingUpdates[_asset] = PendingChainlinkConfig(
        actionId=aid,
        config=ChainlinkConfig(
            feed=_newFeed,
            decimals=decimals,
            needsEthToUsd=_needsEthToUsd,
            needsBtcToUsd=_needsBtcToUsd,
        ),
    )
    log ChainlinkFeedUpdatePending(asset=_asset, feed=_newFeed, needsEthToUsd=_needsEthToUsd, needsBtcToUsd=_needsBtcToUsd, confirmationBlock=timeLock._getActionConfirmationBlock(aid), oldFeed=oldFeed, actionId=aid)
    return True


# confirm update feed


@external
def confirmPriceFeedUpdate(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validate again
    d: PendingChainlinkConfig = self.pendingUpdates[_asset]
    assert d.config.feed != empty(address) # dev: no pending update feed
    oldFeed: address = self.feedConfig[_asset].feed
    if not self._isValidUpdateFeed(_asset, d.config.feed, oldFeed, d.config.decimals, d.config.needsEthToUsd, d.config.needsBtcToUsd):
        self._cancelPriceFeedUpdate(_asset, d.actionId)
        return False

    # check time lock
    assert timeLock._confirmAction(d.actionId) # dev: time lock not reached

    # save new feed config
    self.feedConfig[_asset] = d.config
    self.pendingUpdates[_asset] = empty(PendingChainlinkConfig)

    log ChainlinkFeedUpdated(asset=_asset, feed=d.config.feed, needsEthToUsd=d.config.needsEthToUsd, needsBtcToUsd=d.config.needsBtcToUsd, oldFeed=oldFeed)
    return True


# cancel update feed


@external
def cancelPriceFeedUpdate(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    d: PendingChainlinkConfig = self.pendingUpdates[_asset]
    self._cancelPriceFeedUpdate(_asset, d.actionId)
    log ChainlinkFeedUpdateCancelled(asset=_asset, feed=d.config.feed, oldFeed=self.feedConfig[_asset].feed)
    return True


@internal
def _cancelPriceFeedUpdate(_asset: address, _aid: uint256):
    assert timeLock._cancelAction(_aid) # dev: cannot cancel action
    self.pendingUpdates[_asset] = empty(PendingChainlinkConfig)


# validation


@view
@external
def isValidUpdateFeed(_asset: address, _newFeed: address, _decimals: uint256, _needsEthToUsd: bool, _needsBtcToUsd: bool) -> bool:
    return self._isValidUpdateFeed(_asset, _newFeed, self.feedConfig[_asset].feed, _decimals, _needsEthToUsd, _needsBtcToUsd)


@view
@internal
def _isValidUpdateFeed(_asset: address, _newFeed: address, _oldFeed: address, _decimals: uint256, _needsEthToUsd: bool, _needsBtcToUsd: bool) -> bool:
    if _newFeed == _oldFeed:
        return False
    if priceData.indexOfAsset[_asset] == 0 or _oldFeed == empty(address): # use the `addNewPriceFeed` function instead
        return False
    return self._isValidFeedConfig(_asset, _newFeed, _decimals, _needsEthToUsd, _needsBtcToUsd)


@view
@internal
def _isValidFeedConfig(
    _asset: address, 
    _feed: address,
    _decimals: uint256,
    _needsEthToUsd: bool,
    _needsBtcToUsd: bool,
) -> bool:
    if empty(address) in [_asset, _feed]:
        return False
    if _needsEthToUsd and _needsBtcToUsd:
        return False

    staleTime: uint256 = 0
    controlRoom: address = addys._getControlRoomAddr()
    if controlRoom != empty(address):
        staleTime = staticcall ControlRoom(controlRoom).getPriceStaleTime()

    return self._getPrice(_feed, _decimals, _needsEthToUsd, _needsBtcToUsd, staleTime) != 0


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
    self.pendingUpdates[_asset] = PendingChainlinkConfig(
        actionId=aid,
        config=empty(ChainlinkConfig),
    )

    log DisableChainlinkFeedPending(asset=_asset, feed=oldFeed, confirmationBlock=timeLock._getActionConfirmationBlock(aid), actionId=aid)
    return True


# confirm disable feed


@external
def confirmDisablePriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validate again
    oldFeed: address = self.feedConfig[_asset].feed
    d: PendingChainlinkConfig = self.pendingUpdates[_asset]
    assert d.actionId != 0 # dev: no pending disable feed
    if not self._isValidDisablePriceFeed(_asset, oldFeed):
        self._cancelDisablePriceFeed(_asset, d.actionId)
        return False

    # check time lock
    assert timeLock._confirmAction(d.actionId) # dev: time lock not reached

    # disable feed
    self.feedConfig[_asset] = empty(ChainlinkConfig)
    self.pendingUpdates[_asset] = empty(PendingChainlinkConfig)
    priceData._removePricedAsset(_asset)
    
    log ChainlinkFeedDisabled(asset=_asset, feed=oldFeed)
    return True


# cancel disable feed


@external
def cancelDisablePriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    self._cancelDisablePriceFeed(_asset, self.pendingUpdates[_asset].actionId)
    log DisableChainlinkFeedCancelled(asset=_asset, feed=self.feedConfig[_asset].feed)
    return True


@internal
def _cancelDisablePriceFeed(_asset: address, _aid: uint256):
    assert timeLock._cancelAction(_aid) # dev: cannot cancel action
    self.pendingUpdates[_asset] = empty(PendingChainlinkConfig)


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
    return _asset not in [ETH, WETH, BTC]
