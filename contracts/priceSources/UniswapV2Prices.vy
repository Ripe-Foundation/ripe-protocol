# Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
# Ripe Foundation (C) 2026

# @version 0.4.3

implements: PriceSource

import interfaces.PriceSource as PriceSource

interface IUniswapV2Pair:
    def getReserves() -> (uint256, uint256, uint256): view
    def token0() -> address: view
    def token1() -> address: view

interface PriceDesk:
    def getPrice(_asset: address, _shouldRaise: bool = False) -> uint256: view

interface RipeHq:
    def getAddr(_id: uint256) -> address: view

interface TokenDecimals:
    def decimals() -> uint256: view

PRICE_DESK_ID: constant(uint256) = 7
EIGHTEEN_DECIMALS: constant(uint256) = 10 ** 18
MAX_UINT112: constant(uint256) = 2 ** 112 - 1
MAX_UINT32: constant(uint256) = 2 ** 32 - 1

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

    token0: address = staticcall IUniswapV2Pair(_ripeWethPool).token0()
    token1: address = staticcall IUniswapV2Pair(_ripeWethPool).token1()
    ripeIsToken0: bool = token0 == _ripeToken and token1 == _wethToken
    ripeIsToken1: bool = token0 == _wethToken and token1 == _ripeToken
    assert ripeIsToken0 or ripeIsToken1 # dev: not ripe weth pool

    # These immutables define the canonical RIPE/WETH convenience views. The
    # generic view below accepts other caller-supplied asset/pool/partner tuples;
    # this constructor does not qualify those pools or tokens.
    assert staticcall TokenDecimals(_ripeToken).decimals() == 18 # dev: invalid ripe decimals
    assert staticcall TokenDecimals(_wethToken).decimals() == 18 # dev: invalid weth decimals

    RIPE_HQ = _ripeHq
    RIPE_WETH_POOL = _ripeWethPool
    RIPE_TOKEN = _ripeToken
    WETH_TOKEN = _wethToken
    RIPE_IS_TOKEN0 = ripeIsToken0


####################
# Monitoring views #
####################


@view
@external
def isMonitoringOnly() -> bool:
    return True


@view
@external
def getPoolMonitoringPrice(
    _asset: address,
    _pool: address,
    _partner: address,
) -> uint256:
    # This generic view is intentionally stateless. Off-chain monitoring config
    # supplies and independently qualifies each asset/pool/partner tuple,
    # including factory provenance and acceptable liquidity. Decoded invalid
    # state returns zero; typed-call failures from a pool, token, RipeHq, or
    # PriceDesk propagate to the caller.
    if empty(address) in [_asset, _pool, _partner] or _asset == _partner:
        return 0

    token0: address = staticcall IUniswapV2Pair(_pool).token0()
    token1: address = staticcall IUniswapV2Pair(_pool).token1()
    assetIsToken0: bool = token0 == _asset and token1 == _partner
    assetIsToken1: bool = token0 == _partner and token1 == _asset
    if not assetIsToken0 and not assetIsToken1:
        return 0

    valid: bool = False
    assetReserve: uint256 = 0
    partnerReserve: uint256 = 0
    na: uint256 = 0
    valid, assetReserve, partnerReserve, na = self._readPoolState(_pool, assetIsToken0)
    if not valid or assetReserve == 0 or partnerReserve == 0:
        return 0

    assetDecimals: uint256 = staticcall TokenDecimals(_asset).decimals()
    partnerDecimals: uint256 = staticcall TokenDecimals(_partner).decimals()
    if assetDecimals > 18 or partnerDecimals > 18:
        return 0

    # Partner units per whole asset, normalized to 18 decimals. The uint112
    # reserve bounds and <=18-decimal constraint keep the numerator in uint256.
    partnerPerAsset: uint256 = (
        partnerReserve * (10 ** assetDecimals) * EIGHTEEN_DECIMALS
        // assetReserve
        // (10 ** partnerDecimals)
    )

    if partnerPerAsset == 0:
        return 0

    partnerUsdPrice: uint256 = self._readPartnerUsdPrice(_partner)
    if partnerUsdPrice == 0:
        return 0

    didMultiply: bool = False
    assetUsdPrice: uint256 = 0
    didMultiply, assetUsdPrice = self._mulDivOne(partnerPerAsset, partnerUsdPrice)
    return assetUsdPrice if didMultiply else 0


@view
@external
def getRipePoolState() -> (uint256, uint256, uint256):
    valid: bool = False
    ripeReserve: uint256 = 0
    wethReserve: uint256 = 0
    lastUpdate: uint256 = 0
    valid, ripeReserve, wethReserve, lastUpdate = self._readPoolState(RIPE_WETH_POOL, RIPE_IS_TOKEN0)
    if not valid:
        return 0, 0, 0
    return ripeReserve, wethReserve, lastUpdate


@view
@external
def getRipeWethMonitoringPrice() -> uint256:
    valid: bool = False
    ripeReserve: uint256 = 0
    wethReserve: uint256 = 0
    na: uint256 = 0
    valid, ripeReserve, wethReserve, na = self._readPoolState(RIPE_WETH_POOL, RIPE_IS_TOKEN0)
    if not valid or ripeReserve == 0 or wethReserve == 0:
        return 0
    return wethReserve * EIGHTEEN_DECIMALS // ripeReserve


@view
@external
def getRipeUsdMonitoringPrice() -> uint256:
    valid: bool = False
    ripeReserve: uint256 = 0
    wethReserve: uint256 = 0
    na: uint256 = 0
    valid, ripeReserve, wethReserve, na = self._readPoolState(RIPE_WETH_POOL, RIPE_IS_TOKEN0)
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
def _readPoolState(_pool: address, _assetIsToken0: bool) -> (bool, uint256, uint256, uint256):
    reserve0: uint256 = 0
    reserve1: uint256 = 0
    lastUpdate: uint256 = 0
    reserve0, reserve1, lastUpdate = staticcall IUniswapV2Pair(_pool).getReserves()
    if reserve0 > MAX_UINT112 or reserve1 > MAX_UINT112 or lastUpdate > MAX_UINT32:
        return False, 0, 0, 0

    if _assetIsToken0:
        return True, reserve0, reserve1, lastUpdate
    return True, reserve1, reserve0, lastUpdate


@view
@internal
def _readWethUsdPrice() -> uint256:
    return self._readPartnerUsdPrice(WETH_TOKEN)


@view
@internal
def _readPartnerUsdPrice(_partner: address) -> uint256:
    # Resolve PriceDesk dynamically so a registry rotation does not stale this
    # direct monitoring view. Neither this read nor its result is a feed.
    priceDesk: address = staticcall RipeHq(RIPE_HQ).getAddr(PRICE_DESK_ID)
    if priceDesk == empty(address):
        return 0
    return staticcall PriceDesk(priceDesk).getPrice(_partner, False)


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
