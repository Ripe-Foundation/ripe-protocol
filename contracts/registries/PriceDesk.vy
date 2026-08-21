
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
#     Ripe Foundation (C) 2026

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

from interfaces import Department

interface MissionControl:
    def getPriceConfig() -> PriceConfig: view
    def underscoreRegistry() -> address: view

interface UnderscoreRegistry:
    def getAddr(_regId: uint256) -> address: view

interface IERC20Detailed:
    def decimals() -> uint8: view

struct PriceConfig:
    staleTime: uint256
    priorityPriceSourceIds: DynArray[uint256, MAX_PRIORITY_PRICE_SOURCES]

event TokenScaleSet:
    asset: indexed(address)
    decimals: indexed(uint256)
    scale: indexed(uint256)

ETH: public(immutable(address))
MAX_PRIORITY_PRICE_SOURCES: constant(uint256) = 10
UNDERSCORE_APPRAISER_ID: constant(uint256) = 7
PRICE_SOURCE_PRICE_GAS: constant(uint256) = 250_000
PRICE_SOURCE_HAS_FEED_GAS: constant(uint256) = 75_000
PRICE_SOURCE_SNAPSHOT_GAS: constant(uint256) = 150_000
MAX_SUPPORTED_TOKEN_DECIMALS: constant(uint256) = 77

# 0 = unset. 1 = valid zero-decimal token (10 ** 0).
tokenScale: public(HashMap[address, uint256])


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

    tokenScale: uint256 = self._readTokenScale(_asset, _shouldRaise)
    if tokenScale == 0:
        return 0

    price: uint256 = self._getPrice(_asset, _shouldRaise)
    if price == 0:
        return 0

    numerator: uint256 = price * _amount
    denominator: uint256 = tokenScale

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

    tokenScale: uint256 = self._readTokenScale(_asset, _shouldRaise)
    if tokenScale == 0:
        return 0

    price: uint256 = self._getPrice(_asset, _shouldRaise)
    if price == 0:
        return 0

    return _usdValue * tokenScale // price


#############
# Get Price #
#############


@view
@external
def getPrice(_asset: address, _shouldRaise: bool = False, _staleTime: uint256 = 0) -> uint256:
    if _asset == empty(address):
        return 0
    return self._getPrice(_asset, _shouldRaise, _staleTime)


@view
@internal
def _getPrice(_asset: address, _shouldRaise: bool = False, _staleTime: uint256 = 0) -> uint256:
    price: uint256 = 0
    mustRaiseOnZero: bool = False
    alreadyLooked: DynArray[uint256, MAX_PRIORITY_PRICE_SOURCES] = []

    # config
    config: PriceConfig = staticcall MissionControl(addys._getMissionControlAddr()).getPriceConfig()
    staleTime: uint256 = 0
    if _staleTime == 0:
        staleTime = config.staleTime
    elif config.staleTime == 0:
        staleTime = _staleTime
    else:
        staleTime = min(_staleTime, config.staleTime)

    # go thru priority partners first
    for pid: uint256 in config.priorityPriceSourceIds:
        sourceStatus: uint256 = 0
        price, sourceStatus = self._getPriceFromPriceSource(pid, _asset, staleTime)
        if price != 0:
            break
        if sourceStatus != 0:
            mustRaiseOnZero = True
        alreadyLooked.append(pid)

    # go thru rest of price sources
    if price == 0:
        numSources: uint256 = registry.numAddrs
        if numSources != 0:
            for pid: uint256 in range(1, numSources, bound=max_value(uint256)):
                if pid in alreadyLooked:
                    continue
                sourceStatus: uint256 = 0
                price, sourceStatus = self._getPriceFromPriceSource(pid, _asset, staleTime)
                if price != 0:
                    break
                if sourceStatus != 0:
                    mustRaiseOnZero = True

    # A failed source leaves feed coverage uncertain, so strict callers still
    # fail closed if no later healthy source establishes a usable price.
    if price == 0 and mustRaiseOnZero and _shouldRaise:
        raise "has price config, no price"

    return price


# price from source


@view
@internal
def _getPriceFromPriceSource(_pid: uint256, _asset: address, _staleTime: uint256) -> (uint256, uint256):
    # status: 0 = valid/no feed, 1 = valid/feed, 2 = failed or malformed
    priceSource: address = registry._getAddr(_pid)
    if priceSource == empty(address):
        return 0, 0

    return self._getPriceFromSource(priceSource, _asset, _staleTime)


@view
@external
def qualifyCallerPriceSource(_asset: address, _staleTime: uint256 = 0) -> (uint256, uint256):
    # admission checks call from the candidate source itself, so no aggregate
    # fallback can mask a source that is not executable under the live stipend.
    return self._getPriceFromSource(msg.sender, _asset, _staleTime)


@view
@internal
def _getPriceFromSource(_priceSource: address, _asset: address, _staleTime: uint256) -> (uint256, uint256):
    # status: 0 = valid/no feed, 1 = valid/feed, 2 = failed or malformed

    success: bool = False
    response: Bytes[65] = b""
    success, response = raw_call(
        _priceSource,
        abi_encode(
            _asset,
            _staleTime,
            self,
            method_id=method_id("getPriceAndHasFeed(address,uint256,address)"),
        ),
        max_outsize=65,
        gas=PRICE_SOURCE_PRICE_GAS,
        is_static_call=True,
        revert_on_failure=False,
    )
    if not success or len(response) != 64:
        return 0, 2

    price: uint256 = 0
    hasFeedWord: uint256 = 0
    price, hasFeedWord = abi_decode(response, (uint256, uint256))
    if hasFeedWord > 1:
        return 0, 2
    if price != 0 and hasFeedWord == 0:
        return 0, 2
    return price, hasFeedWord


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
    return self._hasPriceFeed(_asset)


@view
@internal
def _hasPriceFeed(_asset: address) -> bool:
    numSources: uint256 = registry.numAddrs
    if numSources == 0:
        return False
    for pid: uint256 in range(1, numSources, bound=max_value(uint256)):
        priceSource: address = registry._getAddr(pid)
        if priceSource == empty(address):
            continue
        valid: bool = False
        hasFeed: bool = False
        valid, hasFeed = self._safeHasPriceFeed(priceSource, _asset)
        if valid and hasFeed:
            return True
    return False


@view
@internal
def _safeHasPriceFeed(_priceSource: address, _asset: address) -> (bool, bool):
    success: bool = False
    response: Bytes[33] = b""
    success, response = raw_call(
        _priceSource,
        abi_encode(_asset, method_id=method_id("hasPriceFeed(address)")),
        max_outsize=33,
        gas=PRICE_SOURCE_HAS_FEED_GAS,
        is_static_call=True,
        revert_on_failure=False,
    )
    if not success or len(response) != 32:
        return False, False

    hasFeedWord: uint256 = abi_decode(response, uint256)
    if hasFeedWord > 1:
        return False, False
    return True, hasFeedWord == 1


################
# Token Scales #
################


@external
def syncTokenScale(_asset: address):
    assert _asset != empty(address) and _asset != ETH # dev: invalid asset

    # permissionless if not gov or switchboard
    if not gov._canGovern(msg.sender) and not addys._isSwitchboardAddr(msg.sender):
        assert self._hasPriceFeed(_asset) # dev: no price feed
        assert self.tokenScale[_asset] == 0 # dev: already set
    
    decimals: uint256 = convert(staticcall IERC20Detailed(_asset).decimals(), uint256)
    assert decimals <= MAX_SUPPORTED_TOKEN_DECIMALS # dev: invalid token decimals
    scale: uint256 = 10 ** decimals
    self.tokenScale[_asset] = scale
    log TokenScaleSet(asset=_asset, decimals=decimals, scale=scale)


@view
@internal
def _readTokenScale(_asset: address, _shouldRaise: bool) -> uint256:
    if _asset == ETH:
        return 10 ** 18

    scale: uint256 = self.tokenScale[_asset]
    if scale == 0:
        if _shouldRaise:
            raise "missing token scale"
        return 0
    return scale


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

        valid: bool = False
        hasFeed: bool = False
        valid, hasFeed = self._safeHasPriceFeed(priceSource, _asset)
        if not valid or not hasFeed:
            continue
        if self._safeAddPriceSnapshot(priceSource, _asset):
            didUpdate = True

    return didUpdate


@internal
def _safeAddPriceSnapshot(_priceSource: address, _asset: address) -> bool:
    success: bool = False
    response: Bytes[33] = b""
    success, response = raw_call(
        _priceSource,
        abi_encode(_asset, method_id=method_id("addPriceSnapshot(address)")),
        max_outsize=33,
        gas=PRICE_SOURCE_SNAPSHOT_GAS,
        revert_on_failure=False,
    )
    if not success or len(response) != 32:
        return False

    resultWord: uint256 = abi_decode(response, uint256)
    return resultWord == 1


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
