# Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
# Ripe Foundation (C) 2026

# @version 0.4.3

implements: PriceSource

import interfaces.PriceSource as PriceSource


interface AeroClassicPool:
    def getReserves() -> (uint256, uint256, uint256): view
    def tokens() -> (address, address): view


interface TokenDecimals:
    def decimals() -> uint256: view


PRICE_DESK_ID: constant(uint256) = 7
EIGHTEEN_DECIMALS: constant(uint256) = 10 ** 18
MAX_UINT112: constant(uint256) = 2 ** 112 - 1
MAX_UINT32: constant(uint256) = 2 ** 32 - 1
MAX_ADDRESS: constant(uint256) = 2 ** 160 - 1

RIPE_HQ: public(immutable(address))
RIPE_WETH_POOL: public(immutable(address))
RIPE_TOKEN: public(immutable(address))
WETH_TOKEN: public(immutable(address))
RIPE_IS_TOKEN0: public(immutable(bool))


@deploy
def __init__(
    _ripeHq: address,
    _ripeWethPool: address,
    _ripeToken: address,
    _wethToken: address,
):
    assert empty(address) not in [_ripeHq, _ripeWethPool, _ripeToken, _wethToken] # dev: invalid monitoring config
    assert _ripeToken != _wethToken # dev: invalid monitoring tokens

    token0: address = empty(address)
    token1: address = empty(address)
    token0, token1 = staticcall AeroClassicPool(_ripeWethPool).tokens()
    ripeIsToken0: bool = token0 == _ripeToken and token1 == _wethToken
    ripeIsToken1: bool = token0 == _wethToken and token1 == _ripeToken
    assert ripeIsToken0 or ripeIsToken1 # dev: not ripe weth pool

    # This monitor is deliberately specific to the canonical 18-decimal
    # RIPE/WETH pair. It is not a generic Aerodrome asset adapter.
    assert staticcall TokenDecimals(_ripeToken).decimals() == 18 # dev: invalid ripe decimals
    assert staticcall TokenDecimals(_wethToken).decimals() == 18 # dev: invalid weth decimals

    RIPE_HQ = _ripeHq
    RIPE_WETH_POOL = _ripeWethPool
    RIPE_TOKEN = _ripeToken
    WETH_TOKEN = _wethToken
    RIPE_IS_TOKEN0 = ripeIsToken0


#########################
# RIPE monitoring views #
#########################


@view
@external
def isMonitoringOnly() -> bool:
    return True


@view
@external
def getRipePoolState() -> (uint256, uint256, uint256):
    """Return RIPE reserve, WETH reserve, and the pool's update timestamp."""
    valid: bool = False
    ripeReserve: uint256 = 0
    wethReserve: uint256 = 0
    lastUpdate: uint256 = 0
    valid, ripeReserve, wethReserve, lastUpdate = self._readPoolState()
    if not valid:
        return 0, 0, 0
    return ripeReserve, wethReserve, lastUpdate


@view
@external
def getRipeWethMonitoringPrice() -> uint256:
    """Return the manipulable spot WETH-per-RIPE observation, scaled to 1e18."""
    valid: bool = False
    ripeReserve: uint256 = 0
    wethReserve: uint256 = 0
    na: uint256 = 0
    valid, ripeReserve, wethReserve, na = self._readPoolState()
    if not valid or ripeReserve == 0 or wethReserve == 0:
        return 0
    return wethReserve * EIGHTEEN_DECIMALS // ripeReserve


@view
@external
def getRipeUsdMonitoringPrice() -> uint256:
    """Return the manipulable spot RIPE/USD observation for monitoring only."""
    return self._getRipeUsdMonitoringPrice()


@view
@external
def getAeroRipePrice(_asset: address) -> uint256:
    """Temporary frontend compatibility alias for the RIPE/USD monitor."""
    # Remove after the frontend moves to getRipeUsdMonitoringPrice().
    if _asset != RIPE_TOKEN:
        return 0
    return self._getRipeUsdMonitoringPrice()


@view
@internal
def _getRipeUsdMonitoringPrice() -> uint256:
    valid: bool = False
    ripeReserve: uint256 = 0
    wethReserve: uint256 = 0
    na: uint256 = 0
    valid, ripeReserve, wethReserve, na = self._readPoolState()
    if not valid or ripeReserve == 0 or wethReserve == 0:
        return 0

    wethUsdPrice: uint256 = self._readWethUsdPrice()
    if wethUsdPrice == 0:
        return 0

    ripeWethPrice: uint256 = wethReserve * EIGHTEEN_DECIMALS // ripeReserve
    didMultiply: bool = False
    ripeUsdPrice: uint256 = 0
    didMultiply, ripeUsdPrice = self._mulDivOne(ripeWethPrice, wethUsdPrice)
    return ripeUsdPrice if didMultiply else 0


@view
@internal
def _readPoolState() -> (bool, uint256, uint256, uint256):
    success: bool = False
    response: Bytes[97] = b""
    success, response = raw_call(
        RIPE_WETH_POOL,
        method_id("getReserves()"),
        max_outsize=97,
        is_static_call=True,
        revert_on_failure=False,
    )
    if not success or len(response) != 96:
        return False, 0, 0, 0

    reserve0: uint256 = 0
    reserve1: uint256 = 0
    lastUpdate: uint256 = 0
    reserve0, reserve1, lastUpdate = abi_decode(response, (uint256, uint256, uint256))
    # Aerodrome returns full uint256 values. The retained uint112/uint32 limits
    # are conservative monitoring sanity bounds, not pool storage assumptions.
    if reserve0 > MAX_UINT112 or reserve1 > MAX_UINT112 or lastUpdate > MAX_UINT32:
        return False, 0, 0, 0

    if RIPE_IS_TOKEN0:
        return True, reserve0, reserve1, lastUpdate
    return True, reserve1, reserve0, lastUpdate


@view
@internal
def _readWethUsdPrice() -> uint256:
    # Resolve PriceDesk dynamically so a registry rotation does not stale this
    # direct monitoring view. Neither this read nor its result is a feed.
    success: bool = False
    response: Bytes[33] = b""
    success, response = raw_call(
        RIPE_HQ,
        abi_encode(PRICE_DESK_ID, method_id=method_id("getAddr(uint256)")),
        max_outsize=33,
        is_static_call=True,
        revert_on_failure=False,
    )
    if not success or len(response) != 32:
        return 0
    priceDeskValue: uint256 = abi_decode(response, uint256)
    if priceDeskValue > MAX_ADDRESS:
        return 0
    priceDesk: address = convert(priceDeskValue, address)
    if priceDesk == empty(address):
        return 0

    success, response = raw_call(
        priceDesk,
        abi_encode(WETH_TOKEN, False, method_id=method_id("getPrice(address,bool)")),
        max_outsize=33,
        is_static_call=True,
        revert_on_failure=False,
    )
    if not success or len(response) != 32:
        return 0
    return abi_decode(response, uint256)


#############################
# Inert PriceSource surface #
#############################


@view
@external
def getPrice(_asset: address, _staleTime: uint256 = 0, _oracleRegistry: address = empty(address)) -> uint256:
    return 0


@view
@external
def getPriceAndHasFeed(_asset: address, _staleTime: uint256 = 0, _oracleRegistry: address = empty(address)) -> (uint256, bool):
    return 0, False


@view
@external
def hasPriceFeed(_asset: address) -> bool:
    return False


@view
@external
def hasPendingPriceFeedUpdate(_asset: address) -> bool:
    return False


@view
@external
def getPricedAssets() -> DynArray[address, 50]:
    return empty(DynArray[address, 50])


@external
def addPriceSnapshot(_asset: address) -> bool:
    return False


@external
def confirmNewPriceFeed(_asset: address) -> bool:
    return False


@external
def cancelNewPendingPriceFeed(_asset: address) -> bool:
    return False


@external
def confirmPriceFeedUpdate(_asset: address) -> bool:
    return False


@external
def cancelPriceFeedUpdate(_asset: address) -> bool:
    return False


@external
def disablePriceFeed(_asset: address) -> bool:
    return False


@external
def confirmDisablePriceFeed(_asset: address) -> bool:
    return False


@external
def cancelDisablePriceFeed(_asset: address) -> bool:
    return False


@view
@external
def actionTimeLock() -> uint256:
    return 0


@view
@external
def hasPendingAction(_actionId: uint256) -> bool:
    return False


@view
@external
def getActionConfirmationBlock(_actionId: uint256) -> uint256:
    return 0


@external
def setActionTimeLock(_numBlocks: uint256) -> bool:
    return False


@external
def setActionTimeLockAfterSetup(_numBlocks: uint256 = 0) -> bool:
    return False


@view
@external
def isPaused() -> bool:
    return False


@external
def pause(_shouldPause: bool):
    raise "monitoring only"


@external
def recoverFunds(_recipient: address, _asset: address):
    raise "monitoring only"


@external
def recoverFundsMany(_recipient: address, _assets: DynArray[address, 20]):
    raise "monitoring only"


@view
@internal
def _mulDivOne(_a: uint256, _b: uint256) -> (bool, uint256):
    whole: uint256 = _a // EIGHTEEN_DECIMALS
    remainder: uint256 = _a % EIGHTEEN_DECIMALS
    if whole != 0 and _b > max_value(uint256) // whole:
        return False, 0
    wholeProduct: uint256 = whole * _b
    if remainder != 0 and _b > max_value(uint256) // remainder:
        return False, 0
    remainderProduct: uint256 = remainder * _b // EIGHTEEN_DECIMALS
    if wholeProduct > max_value(uint256) - remainderProduct:
        return False, 0
    return True, wholeProduct + remainderProduct
