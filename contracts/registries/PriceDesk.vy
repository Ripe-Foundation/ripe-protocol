
#            ___       ___                     ___          ___                  _____         ___          ___          ___     
#           /  /\     /  /\       ___         /  /\        /  /\                /  /::\       /  /\        /  /\        /__/|    
#          /  /::\   /  /::\     /  /\       /  /:/       /  /:/_              /  /:/\:\     /  /:/_      /  /:/_      |  |:|    
#         /  /:/\:\ /  /:/\:\   /  /:/      /  /:/       /  /:/ /\            /  /:/  \:\   /  /:/ /\    /  /:/ /\     |  |:|    
#        /  /:/~/://  /:/~/:/  /__/::\     /  /:/  ___  /  /:/ /:/_          /__/:/ \__\:| /  /:/ /:/_  /  /:/ /::\  __|  |:|    
#       /__/:/ /://__/:/ /:/___\__\/\:\__ /__/:/  /  /\/__/:/ /:/ /\         \  \:\ /  /://__/:/ /:/ /\/__/:/ /:/\:\/__/\_|:|____
#       \  \:\/:/ \  \:\/:::::/   \  \:\/\\  \:\ /  /:/\  \:\/:/ /:/          \  \:\  /:/ \  \:\/:/ /:/\  \:\/:/~/:/\  \:\/:::::/
#        \  \::/   \  \::/~~~~     \__\::/ \  \:\  /:/  \  \::/ /:/            \  \:\/:/   \  \::/ /:/  \  \::/ /:/  \  \::/~~~~ 
#         \  \:\    \  \:\         /__/:/   \  \:\/:/    \  \:\/:/              \  \::/     \  \:\/:/    \__\/ /:/    \  \:\     
#          \  \:\    \  \:\        \__\/     \  \::/      \  \::/                \__\/       \  \::/       /__/:/      \  \:\    
#           \__\/     \__\/                   \__\/        \__\/                              \__\/        \__\/        \__\/    
#
#     ╔════════════════════════════════════════════╗
#     ║  ** Price Desk **                          ║
#     ║  Registry for all oracles, price sources   ║
#     ╚════════════════════════════════════════════╝
#
#     Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
#     Ripe Foundation (C) 2025

# @version 0.4.3

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
import contracts.registries.modules.AddressRegistry as registry
import contracts.modules.Addys as addys
import contracts.modules.DeptBasics as deptBasics

from interfaces import PriceSource
from interfaces import Department
from ethereum.ercs import IERC20Detailed

interface MissionControl:
    def getPriceConfig() -> PriceConfig: view
    def underscoreRegistry() -> address: view

interface UnderscoreRegistry:
    def getAddr(_regId: uint256) -> address: view

struct PriceConfig:
    staleTime: uint256
    priorityPriceSourceIds: DynArray[uint256, MAX_PRIORITY_PRICE_SOURCES]

ETH: public(immutable(address))
MAX_PRIORITY_PRICE_SOURCES: constant(uint256) = 10
UNDERSCORE_APPRAISER_ID: constant(uint256) = 7


@deploy
def __init__(
    _ripeHq: address,
    _tempGov: address,
    _ethAddr: address,
    _minRegistryTimeLock: uint256,
    _maxRegistryTimeLock: uint256,
):
    assert _ethAddr != empty(address) # dev: invalid eth addr
    ETH = _ethAddr

    # modules
    gov.__init__(_ripeHq, _tempGov, 0, 0, 0)
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

    numerator: uint256 = price * _amount
    denominator: uint256 = 10 ** convert(staticcall IERC20Detailed(_asset).decimals(), uint256)

    # important to return non-zero value -- Stability Pool dust issues 
    if numerator < denominator:
        return 1
    
    return numerator // denominator


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
    alreadyLooked: DynArray[uint256, MAX_PRIORITY_PRICE_SOURCES] = []

    # config
    config: PriceConfig = staticcall MissionControl(addys._getMissionControlAddr()).getPriceConfig()

    # go thru priority partners first
    for pid: uint256 in config.priorityPriceSourceIds:
        hasFeed: bool = False
        price, hasFeed = self._getPriceFromPriceSource(pid, _asset, config.staleTime)
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
                price, hasFeed = self._getPriceFromPriceSource(pid, _asset, config.staleTime)
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
    if numSources == 0:
        return False
    for pid: uint256 in range(1, numSources, bound=max_value(uint256)):
        priceSource: address = registry._getAddr(pid)
        if priceSource == empty(address):
            continue
        if staticcall PriceSource(priceSource).hasPriceFeed(_asset):
            return True
    return False


############
# Registry #
############


# new address


@external
def startAddNewAddressToRegistry(_addr: address, _description: String[64]) -> bool:
    assert self._canPerformAction(msg.sender) # dev: no perms
    return registry._startAddNewAddressToRegistry(_addr, _description)


@external
def confirmNewAddressToRegistry(_addr: address) -> uint256:
    assert self._canPerformAction(msg.sender) # dev: no perms
    return registry._confirmNewAddressToRegistry(_addr)


@external
def cancelNewAddressToRegistry(_addr: address) -> bool:
    assert self._canPerformAction(msg.sender) # dev: no perms
    return registry._cancelNewAddressToRegistry(_addr)


# address update


@external
def startAddressUpdateToRegistry(_regId: uint256, _newAddr: address) -> bool:
    assert self._canPerformAction(msg.sender) # dev: no perms
    return registry._startAddressUpdateToRegistry(_regId, _newAddr)


@external
def confirmAddressUpdateToRegistry(_regId: uint256) -> bool:
    assert self._canPerformAction(msg.sender) # dev: no perms
    return registry._confirmAddressUpdateToRegistry(_regId)


@external
def cancelAddressUpdateToRegistry(_regId: uint256) -> bool:
    assert self._canPerformAction(msg.sender) # dev: no perms
    return registry._cancelAddressUpdateToRegistry(_regId)


# address disable


@external
def startAddressDisableInRegistry(_regId: uint256) -> bool:
    assert self._canPerformAction(msg.sender) # dev: no perms
    return registry._startAddressDisableInRegistry(_regId)


@external
def confirmAddressDisableInRegistry(_regId: uint256) -> bool:
    assert self._canPerformAction(msg.sender) # dev: no perms
    return registry._confirmAddressDisableInRegistry(_regId)


@external
def cancelAddressDisableInRegistry(_regId: uint256) -> bool:
    assert self._canPerformAction(msg.sender) # dev: no perms
    return registry._cancelAddressDisableInRegistry(_regId)


###################
# Price Snapshots #
###################


@external 
def addPriceSnapshot(_asset: address) -> bool:
    if not addys._isValidRipeAddr(msg.sender):
        assert self._isUndyAppraiser(msg.sender) # dev: no perms

    numSources: uint256 = registry.numAddrs
    if numSources == 0:
        return False

    didUpdate: bool = False
    for pid: uint256 in range(1, numSources, bound=max_value(uint256)):
        priceSource: address = registry._getAddr(pid)
        if priceSource == empty(address):
            continue

        if staticcall PriceSource(priceSource).hasPriceFeed(_asset):
            extcall PriceSource(priceSource).addPriceSnapshot(_asset)
            didUpdate = True

    return didUpdate


@view
@internal
def _isUndyAppraiser(_addr: address) -> bool:
    underscore: address = staticcall MissionControl(addys._getMissionControlAddr()).underscoreRegistry()
    if underscore == empty(address):
        return False
    return _addr == staticcall UnderscoreRegistry(underscore).getAddr(UNDERSCORE_APPRAISER_ID)


#############
# Utilities #
#############


@view
@internal
def _canPerformAction(_caller: address) -> bool:
    return gov._canGovern(_caller) and not deptBasics.isPaused