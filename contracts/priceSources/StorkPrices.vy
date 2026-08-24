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

interface StorkNetwork:
    def updateTemporalNumericValuesV1(_payload: DynArray[TemporalNumericValueInput, MAX_PRICE_UPDATES]): payable
    def getUpdateFeeV1(_payload: DynArray[TemporalNumericValueInput, MAX_PRICE_UPDATES]) -> uint256: view
    def getTemporalNumericValueUnsafeV1(_feedId: bytes32) -> TemporalNumericValue: view

interface MissionControl:
    def canPerformLiteAction(_user: address) -> bool: view
    def getPriceStaleTime() -> uint256: view

struct StorkFeedConfig:
    feedId: bytes32
    staleTime: uint256

struct PendingStorkFeed:
    actionId: uint256
    config: StorkFeedConfig

struct TemporalNumericValue:
    timestampNs: uint64
    quantizedValue: int192

struct TemporalNumericValueInput:
    temporalNumericValue: TemporalNumericValue
    id: bytes32
    publisherMerkleRoot: bytes32
    valueComputeAlgHash: bytes32
    r: bytes32
    s: bytes32
    v: uint8

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
    payload: DynArray[TemporalNumericValueInput, MAX_PRICE_UPDATES]
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
MAX_FEED_STALE_TIME: constant(uint256) = 60 * 60 * 24 * 7 # 7 days


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
    # A nonzero value is only the canonical PriceDesk-forwarded global.
    if _staleTime != 0:
        priceDesk: address = addys._getPriceDeskAddr()
        if msg.sender != priceDesk or _priceDesk != priceDesk:
            return 0
    staleTime: uint256 = 0
    isValid: bool = False
    staleTime, isValid = self._resolveStaleTime(_staleTime, config.staleTime)
    if not isValid:
        return 0
    return self._getPrice(config.feedId, staleTime)


@view
@external
def getPriceAndHasFeed(_asset: address, _staleTime: uint256 = 0, _priceDesk: address = empty(address)) -> (uint256, bool):
    config: StorkFeedConfig = self.feedConfig[_asset]
    if config.feedId == empty(bytes32):
        return 0, False
    # A nonzero value is only the canonical PriceDesk-forwarded global.
    if _staleTime != 0:
        priceDesk: address = addys._getPriceDeskAddr()
        if msg.sender != priceDesk or _priceDesk != priceDesk:
            return 0, True
    staleTime: uint256 = 0
    isValid: bool = False
    staleTime, isValid = self._resolveStaleTime(_staleTime, config.staleTime)
    if not isValid:
        return 0, True
    return self._getPrice(config.feedId, staleTime), True


@view
@internal
def _getPrice(_feedId: bytes32, _staleTime: uint256) -> uint256:
    data: TemporalNumericValue = staticcall StorkNetwork(STORK).getTemporalNumericValueUnsafeV1(_feedId)

    # official 1e18 as-is; reject non-positive int192
    if data.quantizedValue <= 0:
        return 0

    # validate publish time and staleness
    # Sub-second future values within the current second truncate to current time.
    publishTime: uint256 = convert(data.timestampNs, uint256) // 1_000_000_000
    if publishTime == 0 or publishTime > block.timestamp:
        return 0
    if _staleTime != 0 and block.timestamp - publishTime > _staleTime:
        return 0

    return convert(data.quantizedValue, uint256)


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


@view
@internal
def _resolveStaleTime(_globalStaleTime: uint256, _feedStaleTime: uint256) -> (uint256, bool):
    if _feedStaleTime != 0:
        if _feedStaleTime > MAX_FEED_STALE_TIME:
            return 0, False
        return _feedStaleTime, True

    globalStaleTime: uint256 = _globalStaleTime
    if globalStaleTime == 0:
        isValid: bool = False
        globalStaleTime, isValid = self._getGlobalStaleTime()
        if not isValid:
            return 0, False
    elif globalStaleTime > MAX_FEED_STALE_TIME:
        return 0, False
    return globalStaleTime, True


@view
@internal
def _getGlobalStaleTime() -> (uint256, bool):
    missionControl: address = addys._getMissionControlAddr()
    if missionControl == empty(address):
        return 0, False

    staleTime: uint256 = staticcall MissionControl(missionControl).getPriceStaleTime()
    if staleTime == 0 or staleTime > MAX_FEED_STALE_TIME:
        return 0, False
    return staleTime, True


################
# Add New Feed #
################


# initiate new feed


@external
def addNewPriceFeed(_asset: address, _feedId: bytes32, _staleTime: uint256 = 0) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused
    assert self.pendingUpdates[_asset].actionId == 0 # dev: pending feed action

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
    assert self.feedConfig[_asset].feedId == empty(bytes32) # dev: no pending new feed
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
    assert d.actionId != 0 # dev: no pending new feed
    assert d.config.feedId != empty(bytes32) # dev: no pending new feed
    assert self.feedConfig[_asset].feedId == empty(bytes32) # dev: no pending new feed
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
def updatePriceFeed(_asset: address, _feedId: bytes32, _staleTime: uint256 = 0) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused
    assert _feedId != self.feedConfig[_asset].feedId # dev: invalid feed

    return self._initiatePriceFeedUpdate(_asset, _feedId, _staleTime)


@external
def updateStaleTime(_asset: address, _staleTime: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    config: StorkFeedConfig = self.feedConfig[_asset]
    return self._initiatePriceFeedUpdate(_asset, config.feedId, _staleTime)


@internal
def _initiatePriceFeedUpdate(_asset: address, _feedId: bytes32, _staleTime: uint256) -> bool:
    assert self.pendingUpdates[_asset].actionId == 0 # dev: pending feed action

    # validation
    oldFeedId: bytes32 = self.feedConfig[_asset].feedId
    assert self._isValidUpdateFeed(_asset, _feedId, _staleTime) # dev: invalid feed

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
    assert oldFeedId != empty(bytes32) # dev: no pending update feed
    if not self._isValidUpdateFeed(_asset, d.config.feedId, d.config.staleTime):
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
    assert d.actionId != 0 # dev: no pending update feed
    assert d.config.feedId != empty(bytes32) # dev: no pending update feed
    assert self.feedConfig[_asset].feedId != empty(bytes32) # dev: no pending update feed
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
    if _feedId == self.feedConfig[_asset].feedId:
        return False
    return self._isValidUpdateFeed(_asset, _feedId, _staleTime)


@view
@external
def isValidStaleTimeUpdate(_asset: address, _staleTime: uint256) -> bool:
    config: StorkFeedConfig = self.feedConfig[_asset]
    return self._isValidUpdateFeed(_asset, config.feedId, _staleTime)


@view
@internal
def _isValidUpdateFeed(_asset: address, _feedId: bytes32, _staleTime: uint256) -> bool:
    oldConfig: StorkFeedConfig = self.feedConfig[_asset]
    if priceData.indexOfAsset[_asset] == 0 or oldConfig.feedId == empty(bytes32): # use the `addNewPriceFeed` function instead
        return False
    if _feedId == oldConfig.feedId and _staleTime == oldConfig.staleTime:
        return False

    return self._isValidFeedConfig(_asset, _feedId, _staleTime)


@view
@internal
def _isValidFeedConfig(_asset: address, _feedId: bytes32, _staleTime: uint256) -> bool:
    if _asset == empty(address):
        return False

    data: TemporalNumericValue = staticcall StorkNetwork(STORK).getTemporalNumericValueUnsafeV1(_feedId)
    if data.quantizedValue <= 0:
        return False
    publishTime: uint256 = convert(data.timestampNs, uint256) // 1_000_000_000
    if publishTime == 0 or publishTime > block.timestamp:
        return False

    staleTime: uint256 = 0
    isValid: bool = False
    staleTime, isValid = self._resolveStaleTime(0, _staleTime)
    if not isValid:
        return False
    if block.timestamp - publishTime > staleTime:
        return False
    return True


################
# Disable Feed #
################


# initiate disable feed


@external
def disablePriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused
    assert self.pendingUpdates[_asset].actionId == 0 # dev: pending feed action

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
    assert d.config.feedId == empty(bytes32) # dev: no pending disable feed
    assert oldFeedId != empty(bytes32) # dev: no pending disable feed
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

    d: PendingStorkFeed = self.pendingUpdates[_asset]
    assert d.actionId != 0 # dev: no pending disable feed
    assert d.config.feedId == empty(bytes32) # dev: no pending disable feed
    assert self.feedConfig[_asset].feedId != empty(bytes32) # dev: no pending disable feed
    self._cancelDisablePriceFeed(_asset, d.actionId)
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
def updateStorkPrice(_payload: DynArray[TemporalNumericValueInput, MAX_PRICE_UPDATES]) -> bool:
    assert staticcall MissionControl(addys._getMissionControlAddr()).canPerformLiteAction(msg.sender) # dev: not authorized
    assert msg.value != 0 # dev: payment required
    return self._updateStorkPrice(_payload, STORK, msg.value, True)


@external
def updateStorkPriceNoPay(_payload: DynArray[TemporalNumericValueInput, MAX_PRICE_UPDATES]) -> bool:
    assert staticcall MissionControl(addys._getMissionControlAddr()).canPerformLiteAction(msg.sender) # dev: not authorized
    return self._updateStorkPrice(_payload, STORK, self.balance, False)


@internal
def _updateStorkPrice(_payload: DynArray[TemporalNumericValueInput, MAX_PRICE_UPDATES], _stork: address, _payment: uint256, _shouldRefund: bool) -> bool:
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
