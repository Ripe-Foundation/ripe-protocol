# @version 0.4.1

initializes: gov
initializes: registry

exports: gov.__interface__

import contracts.modules.LocalGov as gov
import contracts.modules.Registry as registry

from ethereum.ercs import IERC20Detailed
import interfaces.PriceSource as PriceSource

event PriorityPriceSourceIdsModified:
    numIds: uint256

event StaleTimeSet:
    staleTime: uint256

# custom config
priorityPriceSourceIds: public(DynArray[uint256, MAX_PRIORITY_PARTNERS])
staleTime: public(uint256)

ETH: public(immutable(address))
MIN_STALE_TIME: public(immutable(uint256))
MAX_STALE_TIME: public(immutable(uint256))
MIN_PRICE_SOURCE_CHANGE_DELAY: public(immutable(uint256))
MAX_PRICE_SOURCE_CHANGE_DELAY: public(immutable(uint256))

MAX_PRIORITY_PARTNERS: constant(uint256) = 10


@deploy
def __init__(
    _ripeHq: address,
    _ethAddr: address,
    _minStaleTime: uint256,
    _maxStaleTime: uint256,
    _minPriceSourceChangeDelay: uint256,
    _maxPriceSourceChangeDelay: uint256,
):
    assert empty(address) not in [_ripeHq, _ethAddr] # dev: invalid addrs
    ETH = _ethAddr
    MIN_STALE_TIME = _minStaleTime
    MAX_STALE_TIME = _maxStaleTime
    MIN_PRICE_SOURCE_CHANGE_DELAY = _minPriceSourceChangeDelay
    MAX_PRICE_SOURCE_CHANGE_DELAY = _maxPriceSourceChangeDelay

    # initialize modules
    gov.__init__(empty(address), _ripeHq, 0, 0)
    registry.__init__(_minPriceSourceChangeDelay, _maxPriceSourceChangeDelay, "PriceDesk.vy")


#########
# Price #
#########


@view
@external
def getPrice(_asset: address, _shouldRaise: bool = False) -> uint256:
    if _asset == empty(address):
        return 0
    return self._getPrice(_asset, _shouldRaise)


@view
@internal
def _getPrice(_asset: address, _shouldRaise: bool = False) -> uint256:
    price: uint256 = 0
    hasFeedConfig: bool = False
    alreadyLooked: DynArray[uint256, MAX_PRIORITY_PARTNERS] = []
    staleTime: uint256 = self.staleTime

    # go thru priority partners first
    priorityIds: DynArray[uint256, MAX_PRIORITY_PARTNERS] = self.priorityPriceSourceIds
    for pid: uint256 in priorityIds:
        hasFeed: bool = False
        price, hasFeed = self._getPriceFromPriceSource(pid, _asset, staleTime)
        if price != 0:
            break
        if hasFeed:
            hasFeedConfig = True
        alreadyLooked.append(pid)

    # go thru rest of price sources
    if price == 0:
        numSources: uint256 = registry.numAddys
        for id: uint256 in range(1, numSources, bound=max_value(uint256)):
            if id in alreadyLooked:
                continue
            hasFeed: bool = False
            price, hasFeed = self._getPriceFromPriceSource(id, _asset, staleTime)
            if price != 0:
                break
            if hasFeed:
                hasFeedConfig = True

    # raise exception if feed exists but no price
    if price == 0 and hasFeedConfig and _shouldRaise:
        raise "has price config, no price"

    return price


@view
@internal
def _getPriceFromPriceSource(_pid: uint256, _asset: address, _staleTime: uint256) -> (uint256, bool):
    priceSource: address = registry._getAddy(_pid)
    if priceSource == empty(address):
        return 0, False
    return staticcall PriceSource(priceSource).getPriceAndHasFeed(_asset, _staleTime, self)


# other utils


@view
@external
def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool = False) -> uint256:
    if _amount == 0 or _asset == empty(address):
        return 0
    price: uint256 = self._getPrice(_asset, _shouldRaise)
    if price == 0:
        return 0
    decimals: uint256 = convert(staticcall IERC20Detailed(_asset).decimals(), uint256)
    return price * _amount // (10 ** decimals)


@view
@external
def getAssetAmount(_asset: address, _usdValue: uint256, _shouldRaise: bool = False) -> uint256:
    if _usdValue == 0 or _asset == empty(address):
        return 0
    price: uint256 = self._getPrice(_asset, _shouldRaise)
    if price == 0:
        return 0
    decimals: uint256 = convert(staticcall IERC20Detailed(_asset).decimals(), uint256)
    return _usdValue * (10 ** decimals) // price


@view
@external
def hasPriceFeed(_asset: address) -> bool:
    numSources: uint256 = registry.numAddys
    for id: uint256 in range(1, numSources, bound=max_value(uint256)):
        priceSource: address = registry._getAddy(id)
        if priceSource == empty(address):
            continue
        if staticcall PriceSource(priceSource).hasPriceFeed(_asset):
            return True
    return False


@view
@external
def getEthUsdValue(_amount: uint256, _shouldRaise: bool = False) -> uint256:
    if _amount == 0:
        return 0
    return self._getPrice(ETH, _shouldRaise) * _amount // (10 ** 18)


@view
@external
def getEthAmount(_usdValue: uint256, _shouldRaise: bool = False) -> uint256:
    if _usdValue == 0:
        return 0
    price: uint256 = self._getPrice(ETH, _shouldRaise)
    if price == 0:
        return 0
    return _usdValue * (10 ** 18) // price


#########################
# Register Price Source #
#########################


@view
@external
def isValidNewPriceSourceAddr(_addr: address) -> bool:
    return registry._isValidNewAddy(_addr)


@external
def registerNewPriceSource(_addr: address, _description: String[64]) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._registerNewAddy(_addr, _description)


@external
def confirmNewPriceSourceRegistration(_addr: address) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    priceSourceId: uint256 = registry._confirmNewAddy(_addr)
    if priceSourceId != 0:
        assert extcall PriceSource(_addr).setPriceSourceId(priceSourceId) # dev: set id failed
    return priceSourceId


@external
def cancelPendingNewPriceSourceRegistration(_addr: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._cancelPendingNewAddy(_addr)


#######################
# Update Price Source #
#######################


@view
@external
def isValidPriceSourceUpdate(_priceSourceId: uint256, _newAddr: address) -> bool:
    return registry._isValidAddyUpdate(_priceSourceId, _newAddr, registry.addyInfo[_priceSourceId].addr)


@external
def updatePriceSourceAddr(_priceSourceId: uint256, _newAddr: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._updateAddyAddr(_priceSourceId, _newAddr)


@external
def confirmPriceSourceUpdate(_priceSourceId: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    didUpdate: bool = registry._confirmAddyUpdate(_priceSourceId)
    if didUpdate:
        priceSourceAddr: address = registry.addyInfo[_priceSourceId].addr
        assert extcall PriceSource(priceSourceAddr).setPriceSourceId(_priceSourceId) # dev: set id failed
    return didUpdate


@external
def cancelPendingPriceSourceUpdate(_priceSourceId: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._cancelPendingAddyUpdate(_priceSourceId)


########################
# Disable Price Source #
########################


@view
@external
def isValidPriceSourceDisable(_priceSourceId: uint256) -> bool:
    return registry._isValidAddyDisable(_priceSourceId, registry.addyInfo[_priceSourceId].addr)


@external
def disablePriceSourceAddr(_priceSourceId: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._disableAddyAddr(_priceSourceId)


@external
def confirmPriceSourceDisable(_priceSourceId: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._confirmAddyDisable(_priceSourceId)


@external
def cancelPendingPriceSourceDisable(_priceSourceId: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._cancelPendingAddyDisable(_priceSourceId)


#######################
# Price Source Change #
#######################


@external
def setPriceSourceChangeDelay(_numBlocks: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._setAddyChangeDelay(_numBlocks)


@view
@external
def priceSourceChangeDelay() -> uint256:
    return registry.addyChangeDelay


@external
def setPriceSourceChangeDelayToMin() -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._setAddyChangeDelay(registry.MIN_ADDY_CHANGE_DELAY)


##########################
# Priority Price Sources #
##########################


@view 
@external 
def getPriorityPriceSourceIds() -> DynArray[uint256, MAX_PRIORITY_PARTNERS]:
    return self.priorityPriceSourceIds


@view
@internal
def _sanitizePriorityPriceSourceIds(_priorityIds: DynArray[uint256, MAX_PRIORITY_PARTNERS]) -> DynArray[uint256, MAX_PRIORITY_PARTNERS]:
    sanitizedIds: DynArray[uint256, MAX_PRIORITY_PARTNERS] = []
    for pid: uint256 in _priorityIds:
        if not registry._isValidAddyId(pid):
            continue
        if pid in sanitizedIds:
            continue
        sanitizedIds.append(pid)
    return sanitizedIds


@view
@external
def areValidPriorityPriceSourceIds(_priorityIds: DynArray[uint256, MAX_PRIORITY_PARTNERS]) -> bool:
    priorityIds: DynArray[uint256, MAX_PRIORITY_PARTNERS] = self._sanitizePriorityPriceSourceIds(_priorityIds)
    return self._areValidPriorityPriceSourceIds(priorityIds)


@view
@internal
def _areValidPriorityPriceSourceIds(_priorityIds: DynArray[uint256, MAX_PRIORITY_PARTNERS]) -> bool:
    return len(_priorityIds) != 0


@external
def setPriorityPriceSourceIds(_priorityIds: DynArray[uint256, MAX_PRIORITY_PARTNERS]) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms

    priorityIds: DynArray[uint256, MAX_PRIORITY_PARTNERS] = self._sanitizePriorityPriceSourceIds(_priorityIds)
    if not self._areValidPriorityPriceSourceIds(priorityIds):
        return False

    self.priorityPriceSourceIds = priorityIds
    log PriorityPriceSourceIdsModified(numIds=len(priorityIds))
    return True


##############
# Stale Time #
##############


@view
@external
def isValidStaleTime(_staleTime: uint256) -> bool:
    return self._isValidStaleTime(_staleTime)


@view
@internal
def _isValidStaleTime(_staleTime: uint256) -> bool:
    return _staleTime >= MIN_STALE_TIME and _staleTime <= MAX_STALE_TIME


@external
def setStaleTime(_staleTime: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms

    if not self._isValidStaleTime(_staleTime):
        return False

    self.staleTime = _staleTime
    log StaleTimeSet(staleTime=_staleTime)
    return True


#################
# Views / Utils #
#################


@view
@external
def numPriceSourcesRaw() -> uint256:
    return registry.numAddys


# is valid


@view
@external
def isValidPriceSourceAddr(_addr: address) -> bool:
    return registry._isValidAddyAddr(_addr)


@view
@external
def isValidPriceSourceId(_priceSourceId: uint256) -> bool:
    return registry._isValidAddyId(_priceSourceId)


# oracle partner getters


@view
@external
def getPriceSourceId(_addr: address) -> uint256:
    return registry._getAddyId(_addr)


@view
@external
def getPriceSourceAddr(_priceSourceId: uint256) -> address:
    return registry._getAddy(_priceSourceId)


@view
@external
def getPriceSourceInfo(_priceSourceId: uint256) -> registry.AddyInfo:
    return registry.addyInfo[_priceSourceId]


@view
@external
def getPriceSourceDescription(_priceSourceId: uint256) -> String[64]:
    return registry.addyInfo[_priceSourceId].description


# high level


@view
@external
def getNumPriceSources() -> uint256:
    return registry._getNumAddys()


@view
@external
def getLastPriceSourceAddr() -> address:
    return registry._getLastAddyAddr()


@view
@external
def getLastPriceSourceId() -> uint256:
    return registry._getLastAddyId()
