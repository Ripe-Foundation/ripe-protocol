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

interface StorkNetwork:
    def getTemporalNumericValueUnsafeV1(_feedId: bytes32) -> TemporalNumericValue: view
    def updateTemporalNumericValuesV1(_payload: Bytes[2048]): payable
    def getUpdateFeeV1(_payload: Bytes[2048]) -> uint256: view

interface MissionControl:
    def canPerformLiteAction(_user: address) -> bool: view

struct TemporalNumericValue:
    timestampNs: uint64
    quantizedValue: uint256

struct StorkFeedConfig:
    feedId: bytes32
    staleTime: uint256

struct PendingStorkFeed:
    actionId: uint256
    config: StorkFeedConfig

event NewStorkFeedPending:
    asset: indexed(address)
    feedId: bytes32
    staleTime: uint256
    confirmationBlock: uint256
    actionId: uint256

event NewStorkFeedAdded:
    asset: indexed(address)
    feedId: bytes32
    staleTime: uint256

event NewStorkFeedCancelled:
    asset: indexed(address)
    feedId: bytes32

event StorkFeedUpdatePending:
    asset: indexed(address)
    feedId: bytes32
    staleTime: uint256
    confirmationBlock: uint256
    oldFeedId: bytes32
    actionId: uint256

event StorkFeedUpdated:
    asset: indexed(address)
    feedId: bytes32
    staleTime: uint256
    oldFeedId: bytes32

event StorkFeedUpdateCancelled:
    asset: indexed(address)
    feedId: bytes32
    oldFeedId: bytes32

event DisableStorkFeedPending:
    asset: indexed(address)
    feedId: bytes32
    confirmationBlock: uint256
    actionId: uint256

event StorkFeedDisabled:
    asset: indexed(address)
    feedId: bytes32

event DisableStorkFeedCancelled:
    asset: indexed(address)
    feedId: bytes32

event StorkPriceUpdated:
    payload: Bytes[2048]
    feeAmount: uint256
    caller: indexed(address)

event EthRecoveredFromStork:
    recipient: indexed(address)
    amount: uint256

# data
feedConfig: public(HashMap[address, StorkFeedConfig]) # asset -> feed
pendingUpdates: public(HashMap[address, PendingStorkFeed]) # asset -> feed

STORK: public(immutable(address))

MAX_PRICE_UPDATES: constant(uint256) = 20


@deploy
def __init__(
    _ripeHq: address,
    _tempGov: address,
    _stork: address,
    _minPriceChangeTimeLock: uint256,
    _maxPriceChangeTimeLock: uint256,
):
    assert _stork != empty(address) # dev: invalid stork network
    STORK = _stork

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
    config: StorkFeedConfig = self.feedConfig[_asset]
    if config.feedId == empty(bytes32):
        return 0
    staleTime: uint256 = max(_staleTime, config.staleTime)
    return self._getPrice(config.feedId, staleTime)


@view
@external
def getPriceAndHasFeed(_asset: address, _staleTime: uint256 = 0, _priceDesk: address = empty(address)) -> (uint256, bool):
    config: StorkFeedConfig = self.feedConfig[_asset]
    if config.feedId == empty(bytes32):
        return 0, False
    staleTime: uint256 = max(_staleTime, config.staleTime)
    return self._getPrice(config.feedId, staleTime), True


@view
@internal
def _getPrice(_feedId: bytes32, _staleTime: uint256) -> uint256:
    data: TemporalNumericValue = staticcall StorkNetwork(STORK).getTemporalNumericValueUnsafeV1(_feedId)

    # no price
    if data.quantizedValue == 0:
        return 0

    # price is too stale
    publishTime: uint256 = convert(data.timestampNs, uint256) // 1_000_000_000
    if _staleTime != 0 and block.timestamp - publishTime > _staleTime:
        return 0

    return data.quantizedValue


# utilities


@view
@external
def hasPriceFeed(_asset: address) -> bool:
    return self.feedConfig[_asset].feedId != empty(bytes32)


@view
@external
def hasPendingPriceFeedUpdate(_asset: address) -> bool:
    return timeLock._hasPendingAction(self.pendingUpdates[_asset].actionId)


@external 
def addPriceSnapshot(_asset: address) -> bool:
    return False


################
# Add New Feed #
################


# initiate new feed


@external
def addNewPriceFeed(_asset: address, _feedId: bytes32, _staleTime: uint256 = 60 * 60 * 24) -> bool: # 1 day
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validation
    assert self._isValidNewFeed(_asset, _feedId, _staleTime) # dev: invalid feed

    # set to pending state
    aid: uint256 = timeLock._initiateAction()
    self.pendingUpdates[_asset] = PendingStorkFeed(
        actionId=aid, 
        config=StorkFeedConfig(feedId=_feedId, staleTime=_staleTime)
    )

    log NewStorkFeedPending(asset=_asset, feedId=_feedId, staleTime=_staleTime, confirmationBlock=timeLock._getActionConfirmationBlock(aid), actionId=aid)
    return True


# confirm new feed


@external
def confirmNewPriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validate again
    d: PendingStorkFeed = self.pendingUpdates[_asset]
    assert d.config.feedId != empty(bytes32) # dev: no pending new feed
    if not self._isValidNewFeed(_asset, d.config.feedId, d.config.staleTime):
        self._cancelNewPendingPriceFeed(_asset, d.actionId)
        return False

    # check time lock
    assert timeLock._confirmAction(d.actionId) # dev: time lock not reached

    # save new feed
    self.feedConfig[_asset] = d.config
    self.pendingUpdates[_asset] = empty(PendingStorkFeed)
    priceData._addPricedAsset(_asset)

    log NewStorkFeedAdded(asset=_asset, feedId=d.config.feedId, staleTime=d.config.staleTime)
    return True


# cancel new feed


@external
def cancelNewPendingPriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    d: PendingStorkFeed = self.pendingUpdates[_asset]
    self._cancelNewPendingPriceFeed(_asset, d.actionId)
    log NewStorkFeedCancelled(asset=_asset, feedId=d.config.feedId)
    return True


@internal
def _cancelNewPendingPriceFeed(_asset: address, _aid: uint256):
    assert timeLock._cancelAction(_aid) # dev: cannot cancel action
    self.pendingUpdates[_asset] = empty(PendingStorkFeed)


# validation


@view
@external
def isValidNewFeed(_asset: address, _feedId: bytes32, _staleTime: uint256) -> bool:
    return self._isValidNewFeed(_asset, _feedId, _staleTime)


@view
@internal
def _isValidNewFeed(_asset: address, _feedId: bytes32, _staleTime: uint256) -> bool:
    if priceData.indexOfAsset[_asset] != 0 or self.feedConfig[_asset].feedId != empty(bytes32): # use the `updatePriceFeed` function instead
        return False
    return self._isValidFeedConfig(_asset, _feedId, _staleTime)


###############
# Update Feed #
###############


# initiate update feed


@external
def updatePriceFeed(_asset: address, _feedId: bytes32, _staleTime: uint256 = 60 * 60 * 24) -> bool: # 1 day
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validation
    oldFeedId: bytes32 = self.feedConfig[_asset].feedId
    assert self._isValidUpdateFeed(_asset, _feedId, oldFeedId, _staleTime) # dev: invalid feed

    # set to pending state
    aid: uint256 = timeLock._initiateAction()
    self.pendingUpdates[_asset] = PendingStorkFeed(
        actionId=aid, 
        config=StorkFeedConfig(feedId=_feedId, staleTime=_staleTime)
    )

    log StorkFeedUpdatePending(asset=_asset, feedId=_feedId, staleTime=_staleTime, confirmationBlock=timeLock._getActionConfirmationBlock(aid), oldFeedId=oldFeedId, actionId=aid)
    return True


# confirm update feed


@external
def confirmPriceFeedUpdate(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validate again
    d: PendingStorkFeed = self.pendingUpdates[_asset]
    assert d.config.feedId != empty(bytes32) # dev: no pending update feed
    oldFeedId: bytes32 = self.feedConfig[_asset].feedId
    if not self._isValidUpdateFeed(_asset, d.config.feedId, oldFeedId, d.config.staleTime):
        self._cancelPriceFeedUpdate(_asset, d.actionId)
        return False

    # check time lock
    assert timeLock._confirmAction(d.actionId) # dev: time lock not reached

    # save new feed
    self.feedConfig[_asset] = d.config
    self.pendingUpdates[_asset] = empty(PendingStorkFeed)

    log StorkFeedUpdated(asset=_asset, feedId=d.config.feedId, staleTime=d.config.staleTime, oldFeedId=oldFeedId)
    return True


# cancel update feed


@external
def cancelPriceFeedUpdate(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    d: PendingStorkFeed = self.pendingUpdates[_asset]
    self._cancelPriceFeedUpdate(_asset, d.actionId)
    log StorkFeedUpdateCancelled(asset=_asset, feedId=d.config.feedId, oldFeedId=self.feedConfig[_asset].feedId)
    return True


@internal
def _cancelPriceFeedUpdate(_asset: address, _aid: uint256):
    assert timeLock._cancelAction(_aid) # dev: cannot cancel action
    self.pendingUpdates[_asset] = empty(PendingStorkFeed)


# validation


@view
@external
def isValidUpdateFeed(_asset: address, _feedId: bytes32, _staleTime: uint256) -> bool:
    return self._isValidUpdateFeed(_asset, _feedId, self.feedConfig[_asset].feedId, _staleTime)


@view
@internal
def _isValidUpdateFeed(_asset: address, _feedId: bytes32, _oldFeedId: bytes32, _staleTime: uint256) -> bool:
    if _feedId == _oldFeedId:
        return False
    if priceData.indexOfAsset[_asset] == 0 or _oldFeedId == empty(bytes32): # use the `addNewPriceFeed` function instead
        return False
    return self._isValidFeedConfig(_asset, _feedId, _staleTime)


@view
@internal
def _isValidFeedConfig(_asset: address, _feedId: bytes32, _staleTime: uint256) -> bool:
    if _asset == empty(address):
        return False

    data: TemporalNumericValue = staticcall StorkNetwork(STORK).getTemporalNumericValueUnsafeV1(_feedId)
    return data.timestampNs != 0


################
# Disable Feed #
################


# initiate disable feed


@external
def disablePriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validation
    oldFeedId: bytes32 = self.feedConfig[_asset].feedId
    assert self._isValidDisablePriceFeed(_asset, oldFeedId) # dev: invalid asset

    # set to pending state
    aid: uint256 = timeLock._initiateAction()
    self.pendingUpdates[_asset] = PendingStorkFeed(
        actionId=aid, 
        config=empty(StorkFeedConfig)
    )

    log DisableStorkFeedPending(asset=_asset, feedId=oldFeedId, confirmationBlock=timeLock._getActionConfirmationBlock(aid), actionId=aid)
    return True


# confirm disable feed


@external
def confirmDisablePriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validate again
    oldFeedId: bytes32 = self.feedConfig[_asset].feedId
    d: PendingStorkFeed = self.pendingUpdates[_asset]
    assert d.actionId != 0 # dev: no pending disable feed
    if not self._isValidDisablePriceFeed(_asset, oldFeedId):
        self._cancelDisablePriceFeed(_asset, d.actionId)
        return False

    # check time lock
    assert timeLock._confirmAction(d.actionId) # dev: time lock not reached

    # disable feed
    self.feedConfig[_asset] = empty(StorkFeedConfig)
    self.pendingUpdates[_asset] = empty(PendingStorkFeed)
    priceData._removePricedAsset(_asset)
    
    log StorkFeedDisabled(asset=_asset, feedId=oldFeedId)
    return True


# cancel disable feed


@external
def cancelDisablePriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    self._cancelDisablePriceFeed(_asset, self.pendingUpdates[_asset].actionId)
    log DisableStorkFeedCancelled(asset=_asset, feedId=self.feedConfig[_asset].feedId)
    return True


@internal
def _cancelDisablePriceFeed(_asset: address, _aid: uint256):
    assert timeLock._cancelAction(_aid) # dev: cannot cancel action
    self.pendingUpdates[_asset] = empty(PendingStorkFeed)


# validation


@view
@external
def isValidDisablePriceFeed(_asset: address) -> bool:
    return self._isValidDisablePriceFeed(_asset, self.feedConfig[_asset].feedId)


@view
@internal
def _isValidDisablePriceFeed(_asset: address, _oldFeedId: bytes32) -> bool:
    if priceData.indexOfAsset[_asset] == 0:
        return False
    return _oldFeedId != empty(bytes32)


################
# Update Price #
################


@payable
@external
def updateStorkPrice(_payload: Bytes[2048]) -> bool:
    assert staticcall MissionControl(addys._getMissionControlAddr()).canPerformLiteAction(msg.sender) # dev: not authorized
    assert msg.value != 0 # dev: payment required
    return self._updateStorkPrice(_payload, STORK, msg.value, True)


@external
def updateStorkPriceNoPay(_payload: Bytes[2048]) -> bool:
    assert staticcall MissionControl(addys._getMissionControlAddr()).canPerformLiteAction(msg.sender) # dev: not authorized
    return self._updateStorkPrice(_payload, STORK, self.balance, False)


@internal
def _updateStorkPrice(_payload: Bytes[2048], _stork: address, _payment: uint256, _shouldRefund: bool) -> bool:
    feeAmount: uint256 = staticcall StorkNetwork(_stork).getUpdateFeeV1(_payload)
    assert _payment >= feeAmount # dev: insufficient payment

    # update oracle price feeds
    extcall StorkNetwork(_stork).updateTemporalNumericValuesV1(_payload, value=feeAmount)
    log StorkPriceUpdated(payload=_payload, feeAmount=feeAmount, caller=msg.sender)

    # refund excess payment to caller
    excess: uint256 = _payment - feeAmount
    if _shouldRefund and excess > 0:
        send(msg.sender, excess)

    return True


###############
# Recover ETH #
###############


@external
def recoverEthBalance(_recipient: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    balance: uint256 = self.balance
    assert _recipient != empty(address) and balance != 0 # dev: invalid recipient or balance
    send(_recipient, balance)
    log EthRecoveredFromStork(recipient=_recipient, amount=balance)
    return True