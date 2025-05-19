# @version 0.4.1

implements: Department

exports: gov.__interface__
exports: registry.__interface__
exports: addys.__interface__
exports: deptBasics.__interface__

initializes: gov
initializes: registry[gov := gov]
initializes: addys
initializes: deptBasics[addys := addys]

import contracts.modules.LocalGov as gov
import contracts.modules.AddressRegistry as registry
import contracts.modules.Addys as addys
import contracts.modules.DeptBasics as deptBasics

from interfaces import PriceSource
from interfaces import Department
from ethereum.ercs import IERC20Detailed

event PriorityPriceSourceIdsModified:
    numIds: uint256

event StaleTimeSet:
    staleTime: uint256

# config
priorityPriceSourceIds: public(DynArray[uint256, MAX_PRIORITY_PARTNERS])
staleTime: public(uint256)

ETH: public(immutable(address))
MIN_STALE_TIME: public(immutable(uint256))
MAX_STALE_TIME: public(immutable(uint256))

MAX_PRIORITY_PARTNERS: constant(uint256) = 10


@deploy
def __init__(
    _ripeHq: address,
    _ethAddr: address,
    _minStaleTime: uint256,
    _maxStaleTime: uint256,
    _minRegistryTimeLock: uint256,
    _maxRegistryTimeLock: uint256,
):
    assert _ethAddr != empty(address) # dev: invalid eth addr
    ETH = _ethAddr

    assert _minStaleTime < _maxStaleTime # dev: invalid stale time range
    MIN_STALE_TIME = _minStaleTime
    MAX_STALE_TIME = _maxStaleTime

    # modules
    gov.__init__(_ripeHq, empty(address), 0, 0, 0)
    registry.__init__(_minRegistryTimeLock, _maxRegistryTimeLock, 0, "PriceDesk.vy")
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, False, False) # no minting


#############################
# Asset Amount -> USD Value #
#############################


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


#############################
# USD Value -> Asset Amount #
#############################


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


#############
# Get Price #
#############


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
        numSources: uint256 = registry.numAddrs
        if numSources != 0:
            for pid: uint256 in range(1, numSources, bound=max_value(uint256)):
                if pid in alreadyLooked:
                    continue
                hasFeed: bool = False
                price, hasFeed = self._getPriceFromPriceSource(pid, _asset, staleTime)
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
    priceSource: address = registry._getAddr(_pid)
    if priceSource == empty(address):
        return 0, False
    return staticcall PriceSource(priceSource).getPriceAndHasFeed(_asset, _staleTime, self)


###############
# Other Utils #
###############


# ETH


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


# has feed


@view
@external
def hasPriceFeed(_asset: address) -> bool:
    numSources: uint256 = registry.numAddrs
    for pid: uint256 in range(1, numSources, bound=max_value(uint256)):
        priceSource: address = registry._getAddr(pid)
        if priceSource == empty(address):
            continue
        if staticcall PriceSource(priceSource).hasPriceFeed(_asset):
            return True
    return False


##########################
# Priority Price Sources #
##########################


@external
def setPriorityPriceSourceIds(_priorityIds: DynArray[uint256, MAX_PRIORITY_PARTNERS]) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: not activated

    priorityIds: DynArray[uint256, MAX_PRIORITY_PARTNERS] = self._sanitizePrioritySources(_priorityIds)
    assert self._areValidPriorityPriceSourceIds(priorityIds) # dev: invalid priority sources

    self.priorityPriceSourceIds = priorityIds
    log PriorityPriceSourceIdsModified(numIds=len(priorityIds))
    return True


# validation


@view
@external
def areValidPriorityPriceSourceIds(_priorityIds: DynArray[uint256, MAX_PRIORITY_PARTNERS]) -> bool:
    priorityIds: DynArray[uint256, MAX_PRIORITY_PARTNERS] = self._sanitizePrioritySources(_priorityIds)
    return self._areValidPriorityPriceSourceIds(priorityIds)


@view
@internal
def _areValidPriorityPriceSourceIds(_priorityIds: DynArray[uint256, MAX_PRIORITY_PARTNERS]) -> bool:
    return len(_priorityIds) != 0


# utilities


@view 
@external 
def getPriorityPriceSourceIds() -> DynArray[uint256, MAX_PRIORITY_PARTNERS]:
    return self.priorityPriceSourceIds


@view
@internal
def _sanitizePrioritySources(_priorityIds: DynArray[uint256, MAX_PRIORITY_PARTNERS]) -> DynArray[uint256, MAX_PRIORITY_PARTNERS]:
    sanitizedIds: DynArray[uint256, MAX_PRIORITY_PARTNERS] = []
    for pid: uint256 in _priorityIds:
        if not registry._isValidRegId(pid):
            continue
        if pid in sanitizedIds:
            continue
        sanitizedIds.append(pid)
    return sanitizedIds


##############
# Stale Time #
##############


@external
def setStaleTime(_staleTime: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: not activated

    assert self._isValidStaleTime(_staleTime) # dev: invalid stale time
    self.staleTime = _staleTime
    log StaleTimeSet(staleTime=_staleTime)
    return True


# validation


@view
@external
def isValidStaleTime(_staleTime: uint256) -> bool:
    return self._isValidStaleTime(_staleTime)


@view
@internal
def _isValidStaleTime(_staleTime: uint256) -> bool:
    return _staleTime >= MIN_STALE_TIME and _staleTime <= MAX_STALE_TIME