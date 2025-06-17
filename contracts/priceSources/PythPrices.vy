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

interface PythNetwork:
    def getPriceUnsafe(_priceFeedId: bytes32) -> PythPrice: view
    def priceFeedExists(_priceFeedId: bytes32) -> bool: view
    def getUpdateFee(_payLoad: Bytes[2048]) -> uint256: view
    def updatePriceFeeds(_payLoad: Bytes[2048]): payable

interface MissionControl:
    def getPriceStaleTime() -> uint256: view

struct PythPrice:
    price: int64
    confidence: uint64
    exponent: int32
    publishTime: uint64

struct PendingPythFeed:
    actionId: uint256
    feedId: bytes32

event NewPythFeedPending:
    asset: indexed(address)
    feedId: bytes32
    confirmationBlock: uint256
    actionId: uint256

event NewPythFeedAdded:
    asset: indexed(address)
    feedId: bytes32

event NewPythFeedCancelled:
    asset: indexed(address)
    feedId: bytes32

event PythFeedUpdatePending:
    asset: indexed(address)
    feedId: bytes32
    confirmationBlock: uint256
    oldFeedId: bytes32
    actionId: uint256

event PythFeedUpdated:
    asset: indexed(address)
    feedId: bytes32
    oldFeedId: bytes32

event PythFeedUpdateCancelled:
    asset: indexed(address)
    feedId: bytes32
    oldFeedId: bytes32

event DisablePythFeedPending:
    asset: indexed(address)
    feedId: bytes32
    confirmationBlock: uint256
    actionId: uint256

event PythFeedDisabled:
    asset: indexed(address)
    feedId: bytes32

event DisablePythFeedCancelled:
    asset: indexed(address)
    feedId: bytes32

event PythPriceUpdated:
    payload: Bytes[2048]
    feeAmount: uint256
    caller: indexed(address)

event EthRecoveredFromPyth:
    recipient: indexed(address)
    amount: uint256

# data
feedConfig: public(HashMap[address, bytes32]) # asset -> feed
pendingUpdates: public(HashMap[address, PendingPythFeed]) # asset -> feed

PYTH: public(immutable(address))

NORMALIZED_DECIMALS: constant(uint256) = 18
MAX_PRICE_UPDATES: constant(uint256) = 20


@deploy
def __init__(
    _ripeHq: address,
    _pythNetwork: address,
    _minPriceChangeTimeLock: uint256,
    _maxPriceChangeTimeLock: uint256,
):
    assert _pythNetwork != empty(address) # dev: invalid pyth network
    PYTH = _pythNetwork

    gov.__init__(_ripeHq, empty(address), 0, 0, 0)
    addys.__init__(_ripeHq)
    priceData.__init__(False, False)
    timeLock.__init__(_minPriceChangeTimeLock, _maxPriceChangeTimeLock, 0, _maxPriceChangeTimeLock)


###############
# Core Prices #
###############


# get price


@view
@external
def getPrice(_asset: address, _staleTime: uint256 = 0, _priceDesk: address = empty(address)) -> uint256:
    feedId: bytes32 = self.feedConfig[_asset]
    if feedId == empty(bytes32):
        return 0
    return self._getPrice(feedId, _staleTime)


@view
@external
def getPriceAndHasFeed(_asset: address, _staleTime: uint256 = 0, _priceDesk: address = empty(address)) -> (uint256, bool):
    feedId: bytes32 = self.feedConfig[_asset]
    if feedId == empty(bytes32):
        return 0, False
    return self._getPrice(feedId, _staleTime), True


@view
@internal
def _getPrice(_feedId: bytes32, _staleTime: uint256) -> uint256:
    data: PythPrice = staticcall PythNetwork(PYTH).getPriceUnsafe(_feedId)

    # no price
    if data.price <= 0:
        return 0

    # price is too stale
    publishTime: uint256 = convert(data.publishTime, uint256)
    if _staleTime != 0 and block.timestamp - publishTime > _staleTime:
        return 0

    price: uint256 = convert(data.price, uint256)
    confidence: uint256 = convert(data.confidence, uint256)
    scale: uint256 = 10 ** NORMALIZED_DECIMALS
    exponent: uint256 = 0

    # negative exponent: multiply by 10^(18-|exponent|)
    if data.exponent < 0:
        exponent = convert(-data.exponent, uint256)
        price = price * scale // (10 ** exponent)
        confidence = confidence * scale // (10 ** exponent)

    # positive exponent: multiply by 10^(18+exponent)
    else:
        exponent = convert(data.exponent, uint256)
        price = price * scale * (10 ** exponent)
        confidence = confidence * scale * (10 ** exponent)

    # invalid price
    if confidence >= price:
        return 0

    return price - confidence


# utilities


@view
@external
def hasPriceFeed(_asset: address) -> bool:
    return self.feedConfig[_asset] != empty(bytes32)


@view
@external
def hasPendingPriceFeedUpdate(_asset: address) -> bool:
    return timeLock._hasPendingAction(self.pendingUpdates[_asset].actionId)


################
# Add New Feed #
################


# initiate new feed


@external
def addNewPriceFeed(_asset: address, _feedId: bytes32) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validation
    assert self._isValidNewFeed(_asset, _feedId) # dev: invalid feed

    # set to pending state
    aid: uint256 = timeLock._initiateAction()
    self.pendingUpdates[_asset] = PendingPythFeed(actionId=aid, feedId=_feedId)

    log NewPythFeedPending(asset=_asset, feedId=_feedId, confirmationBlock=timeLock._getActionConfirmationBlock(aid), actionId=aid)
    return True


# confirm new feed


@external
def confirmNewPriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validate again
    d: PendingPythFeed = self.pendingUpdates[_asset]
    assert d.feedId != empty(bytes32) # dev: no pending new feed
    if not self._isValidNewFeed(_asset, d.feedId):
        self._cancelNewPendingPriceFeed(_asset, d.actionId)
        return False

    # check time lock
    assert timeLock._confirmAction(d.actionId) # dev: time lock not reached

    # save new feed
    self.feedConfig[_asset] = d.feedId
    self.pendingUpdates[_asset] = empty(PendingPythFeed)
    priceData._addPricedAsset(_asset)

    log NewPythFeedAdded(asset=_asset, feedId=d.feedId)
    return True


# cancel new feed


@external
def cancelNewPendingPriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    d: PendingPythFeed = self.pendingUpdates[_asset]
    self._cancelNewPendingPriceFeed(_asset, d.actionId)
    log NewPythFeedCancelled(asset=_asset, feedId=d.feedId)
    return True


@internal
def _cancelNewPendingPriceFeed(_asset: address, _aid: uint256):
    assert timeLock._cancelAction(_aid) # dev: cannot cancel action
    self.pendingUpdates[_asset] = empty(PendingPythFeed)


# validation


@view
@external
def isValidNewFeed(_asset: address, _feedId: bytes32) -> bool:
    return self._isValidNewFeed(_asset, _feedId)


@view
@internal
def _isValidNewFeed(_asset: address, _feedId: bytes32) -> bool:
    if priceData.indexOfAsset[_asset] != 0 or self.feedConfig[_asset] != empty(bytes32): # use the `updatePriceFeed` function instead
        return False
    return self._isValidFeedConfig(_asset, _feedId)


###############
# Update Feed #
###############


# initiate update feed


@external
def updatePriceFeed(_asset: address, _feedId: bytes32) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validation
    oldFeedId: bytes32 = self.feedConfig[_asset]
    assert self._isValidUpdateFeed(_asset, _feedId, oldFeedId) # dev: invalid feed

    # set to pending state
    aid: uint256 = timeLock._initiateAction()
    self.pendingUpdates[_asset] = PendingPythFeed(actionId=aid, feedId=_feedId)

    log PythFeedUpdatePending(asset=_asset, feedId=_feedId, confirmationBlock=timeLock._getActionConfirmationBlock(aid), oldFeedId=oldFeedId, actionId=aid)
    return True


# confirm update feed


@external
def confirmPriceFeedUpdate(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validate again
    d: PendingPythFeed = self.pendingUpdates[_asset]
    assert d.feedId != empty(bytes32) # dev: no pending update feed
    oldFeedId: bytes32 = self.feedConfig[_asset]
    if not self._isValidUpdateFeed(_asset, d.feedId, oldFeedId):
        self._cancelPriceFeedUpdate(_asset, d.actionId)
        return False

    # check time lock
    assert timeLock._confirmAction(d.actionId) # dev: time lock not reached

    # save new feed
    self.feedConfig[_asset] = d.feedId
    self.pendingUpdates[_asset] = empty(PendingPythFeed)

    log PythFeedUpdated(asset=_asset, feedId=d.feedId, oldFeedId=oldFeedId)
    return True


# cancel update feed


@external
def cancelPriceFeedUpdate(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    d: PendingPythFeed = self.pendingUpdates[_asset]
    self._cancelPriceFeedUpdate(_asset, d.actionId)
    log PythFeedUpdateCancelled(asset=_asset, feedId=d.feedId, oldFeedId=self.feedConfig[_asset])
    return True


@internal
def _cancelPriceFeedUpdate(_asset: address, _aid: uint256):
    assert timeLock._cancelAction(_aid) # dev: cannot cancel action
    self.pendingUpdates[_asset] = empty(PendingPythFeed)


# validation


@view
@external
def isValidUpdateFeed(_asset: address, _feedId: bytes32) -> bool:
    return self._isValidUpdateFeed(_asset, _feedId, self.feedConfig[_asset])


@view
@internal
def _isValidUpdateFeed(_asset: address, _feedId: bytes32, _oldFeedId: bytes32) -> bool:
    if _feedId == _oldFeedId:
        return False
    if priceData.indexOfAsset[_asset] == 0 or _oldFeedId == empty(bytes32): # use the `addNewPriceFeed` function instead
        return False
    return self._isValidFeedConfig(_asset, _feedId)


@view
@internal
def _isValidFeedConfig(_asset: address, _feedId: bytes32) -> bool:
    if _asset == empty(address):
        return False

    if not staticcall PythNetwork(PYTH).priceFeedExists(_feedId):
        return False

    # not looking at staleness here
    return self._getPrice(_feedId, 0) != 0


################
# Disable Feed #
################


# initiate disable feed


@external
def disablePriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validation
    oldFeedId: bytes32 = self.feedConfig[_asset]
    assert self._isValidDisablePriceFeed(_asset, oldFeedId) # dev: invalid asset

    # set to pending state
    aid: uint256 = timeLock._initiateAction()
    self.pendingUpdates[_asset] = PendingPythFeed(actionId=aid, feedId=empty(bytes32))

    log DisablePythFeedPending(asset=_asset, feedId=oldFeedId, confirmationBlock=timeLock._getActionConfirmationBlock(aid), actionId=aid)
    return True


# confirm disable feed


@external
def confirmDisablePriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validate again
    oldFeedId: bytes32 = self.feedConfig[_asset]
    d: PendingPythFeed = self.pendingUpdates[_asset]
    assert d.actionId != 0 # dev: no pending disable feed
    if not self._isValidDisablePriceFeed(_asset, oldFeedId):
        self._cancelDisablePriceFeed(_asset, d.actionId)
        return False

    # check time lock
    assert timeLock._confirmAction(d.actionId) # dev: time lock not reached

    # disable feed
    self.feedConfig[_asset] = empty(bytes32)
    self.pendingUpdates[_asset] = empty(PendingPythFeed)
    priceData._removePricedAsset(_asset)
    
    log PythFeedDisabled(asset=_asset, feedId=oldFeedId)
    return True


# cancel disable feed


@external
def cancelDisablePriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    self._cancelDisablePriceFeed(_asset, self.pendingUpdates[_asset].actionId)
    log DisablePythFeedCancelled(asset=_asset, feedId=self.feedConfig[_asset])
    return True


@internal
def _cancelDisablePriceFeed(_asset: address, _aid: uint256):
    assert timeLock._cancelAction(_aid) # dev: cannot cancel action
    self.pendingUpdates[_asset] = empty(PendingPythFeed)


# validation


@view
@external
def isValidDisablePriceFeed(_asset: address) -> bool:
    return self._isValidDisablePriceFeed(_asset, self.feedConfig[_asset])


@view
@internal
def _isValidDisablePriceFeed(_asset: address, _oldFeedId: bytes32) -> bool:
    if priceData.indexOfAsset[_asset] == 0:
        return False
    return _oldFeedId != empty(bytes32)


################
# Update Price #
################


@external
def updateManyPythPrices(_payloads: DynArray[Bytes[2048], MAX_PRICE_UPDATES]) -> uint256:
    pythNetwork: address = PYTH
    numUpdated: uint256 = 0
    for p: Bytes[2048] in _payloads:
        didUpdate: bool = self._updatePythPrice(p, pythNetwork)
        if didUpdate:
            numUpdated += 1
        else:
            break
    return numUpdated


@external
def updatePythPrice(_payload: Bytes[2048]) -> bool:
    return self._updatePythPrice(_payload, PYTH)


@internal
def _updatePythPrice(_payload: Bytes[2048], _pythNetwork: address) -> bool:
    feeAmount: uint256 = staticcall PythNetwork(_pythNetwork).getUpdateFee(_payload)
    if self.balance < feeAmount:
        return False
    extcall PythNetwork(_pythNetwork).updatePriceFeeds(_payload, value=feeAmount)
    log PythPriceUpdated(payload=_payload, feeAmount=feeAmount, caller=msg.sender)
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
    log EthRecoveredFromPyth(recipient=_recipient, amount=balance)
    return True