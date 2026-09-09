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
import contracts.priceSources.modules.UniswapV3TwapMath as twapMath

import interfaces.PriceSource as PriceSource

struct FeedParams:
    pool: address
    twapWindowSeconds: uint32
    minCurrentLiquidity: uint128
    minHarmonicLiquidity: uint128
    maxObservationAgeSeconds: uint32
    quoteStaleTime: uint256 # 0 inherits the global policy

struct UniV3FeedConfig:
    params: FeedParams
    assetIsToken0: bool
    assetDecimals: uint8
    fee: uint24

struct PendingUniV3Feed:
    actionId: uint256
    kind: uint256 # ACTION_ADD / ACTION_UPDATE / ACTION_DISABLE (0 = none)
    config: UniV3FeedConfig

event UniV3FeedProposed:
    asset: indexed(address)
    actionId: indexed(uint256)
    kind: uint256
    confirmationBlock: uint256
    expirationBlock: uint256
    pool: address
    twapWindowSeconds: uint32
    minCurrentLiquidity: uint128
    minHarmonicLiquidity: uint128
    maxObservationAgeSeconds: uint32
    quoteStaleTime: uint256
    assetIsToken0: bool
    assetDecimals: uint8
    fee: uint24

event UniV3FeedConfirmed:
    asset: indexed(address)
    actionId: indexed(uint256)
    kind: uint256
    confirmationBlock: uint256
    expirationBlock: uint256
    pool: address
    twapWindowSeconds: uint32
    minCurrentLiquidity: uint128
    minHarmonicLiquidity: uint128
    maxObservationAgeSeconds: uint32
    quoteStaleTime: uint256
    assetIsToken0: bool
    assetDecimals: uint8
    fee: uint24

event UniV3FeedCancelled:
    asset: indexed(address)
    actionId: indexed(uint256)
    kind: uint256

# feed config
feedConfig: HashMap[address, UniV3FeedConfig] # asset -> config

# pending changes
pendingUpdates: HashMap[address, PendingUniV3Feed] # asset -> pending action

# permanent asset decimals (bound on first successful add, kept through update / disable / re-add)
hasBoundDecimals: HashMap[address, bool] # asset -> is bound
boundDecimals: HashMap[address, uint8] # asset -> decimals

# deployment bindings
FACTORY: immutable(address)
WETH: immutable(address)
ETH_USD_FEED: immutable(address)
ANCHOR_DECIMALS: immutable(uint8)

ETH: constant(address) = 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE
NORMALIZED_DECIMALS: constant(uint256) = 18
EIGHTEEN_DECIMALS: constant(uint256) = 10 ** 18
MAX_PRICED_ASSETS: constant(uint256) = 50

# ripe hq registry ids
MISSION_CONTROL_ID: constant(uint256) = 5
PRICE_DESK_ID: constant(uint256) = 7

# pending feed action kinds
ACTION_ADD: constant(uint256) = 1
ACTION_UPDATE: constant(uint256) = 2
ACTION_DISABLE: constant(uint256) = 3

# price desk token scale compatibility
SCALE_UNREADABLE: constant(uint256) = 0
SCALE_COMPATIBLE: constant(uint256) = 1
SCALE_MISMATCH: constant(uint256) = 2

# feed parameter domains (seconds)
MIN_TWAP_WINDOW: constant(uint32) = 30 * 60 # 30 minutes
MAX_TWAP_WINDOW: constant(uint32) = 4 * 60 * 60 # 4 hours
MAX_OBSERVATION_AGE: constant(uint32) = 24 * 60 * 60 # 1 day
MIN_LOCAL_STALE_TIME: constant(uint256) = 5 * 60 # 5 minutes
MAX_EFFECTIVE_STALE_TIME: constant(uint256) = 7 * 24 * 60 * 60 # 7 days

# gas caps for bounded static calls
PRICE_READ_GAS: constant(uint256) = 15_000 # hot-path scalar reads (hq, desk scale, policy, decimals, pool state)
OBSERVE_GAS: constant(uint256) = 120_000 # pool observe()
ANCHOR_READ_GAS: constant(uint256) = 30_000 # chainlink latestRoundData()
METADATA_READ_GAS: constant(uint256) = 30_000 # constructor / proposal / confirmation reads
QUALIFY_GAS: constant(uint256) = 400_000 # price desk admission callback (its wrapper + 250k source call)
FAILURE_RESERVE: constant(uint256) = 20_000 # kept back so an unavailable result can still be decoded and returned

# abi payload sizes (capture N + 1 bytes, accept exactly N)
WORD: constant(uint256) = 32
MAX_CALLDATA: constant(uint256) = 4 + 4 * WORD
SLOT0_SIZE: constant(uint256) = 7 * WORD
OBSERVATION_SIZE: constant(uint256) = 4 * WORD
OBSERVE_SIZE: constant(uint256) = 8 * WORD
ROUND_DATA_SIZE: constant(uint256) = 5 * WORD
QUALIFY_SIZE: constant(uint256) = 2 * WORD

# narrow type bounds
MAX_UINT8: constant(uint256) = 2 ** 8 - 1
MAX_UINT16: constant(uint256) = 2 ** 16 - 1
MAX_UINT24: constant(uint256) = 2 ** 24 - 1
MAX_UINT32: constant(uint256) = 2 ** 32 - 1
MAX_UINT80: constant(uint256) = 2 ** 80 - 1
MAX_UINT128: constant(uint256) = 2 ** 128 - 1
MAX_UINT160: constant(uint256) = 2 ** 160 - 1
MAX_INT256: constant(uint256) = 2 ** 255 - 1
MIN_INT56: constant(int256) = -(2 ** 55)
MAX_INT56: constant(int256) = 2 ** 55 - 1


@deploy
def __init__(
    _ripeHq: address,
    _tempGov: address,
    _minActionTimeLock: uint256,
    _maxActionTimeLock: uint256,
    _factory: address,
    _weth: address,
    _ethUsdFeed: address,
):
    assert _ripeHq.is_contract and _factory.is_contract and _weth.is_contract and _ethUsdFeed.is_contract # dev: invalid dependencies

    # weth must be 18 decimals; anchor decimals (0..18) are bound for the life of the deployment
    isValid: bool = False
    decimals: uint256 = 0
    isValid, decimals = self._readWord(_weth, method_id("decimals()"), METADATA_READ_GAS)
    assert isValid and decimals == NORMALIZED_DECIMALS # dev: invalid dependencies
    isValid, decimals = self._readWord(_ethUsdFeed, method_id("decimals()"), METADATA_READ_GAS)
    assert isValid and decimals <= NORMALIZED_DECIMALS # dev: invalid dependencies

    FACTORY = _factory
    WETH = _weth
    ETH_USD_FEED = _ethUsdFeed
    ANCHOR_DECIMALS = convert(decimals, uint8)

    gov.__init__(_ripeHq, _tempGov, 0, 0, 0)
    addys.__init__(_ripeHq)
    priceData.__init__(False)

    # the feed-action delay is live from deployment (initial = min) and actions
    # expire `_maxActionTimeLock` blocks after unlocking. There is no zero-delay
    # setup phase: exclude this source from any FinishSetup
    # `setActionTimeLockAfterSetup` sweep, which it rejects with `already set`.
    timeLock.__init__(_minActionTimeLock, _maxActionTimeLock, _minActionTimeLock, _maxActionTimeLock)


###############
# Core Prices #
###############


# get price


@view
@external
def getPrice(_asset: address, _staleTime: uint256 = 0, _priceDesk: address = empty(address)) -> uint256:
    config: UniV3FeedConfig = self.feedConfig[_asset]
    if config.params.pool == empty(address):
        return 0
    return self._getPrice(_asset, config, _staleTime, _priceDesk)


@view
@external
def getPriceAndHasFeed(_asset: address, _staleTime: uint256 = 0, _priceDesk: address = empty(address)) -> (uint256, bool):
    config: UniV3FeedConfig = self.feedConfig[_asset]
    if config.params.pool == empty(address):
        return 0, False
    return self._getPrice(_asset, config, _staleTime, _priceDesk), True


@view
@internal
def _getPrice(
    _asset: address,
    _config: UniV3FeedConfig,
    _staleTime: uint256,
    _priceDesk: address,
) -> uint256:
    # resolve hq's current price desk once; it serves both the token scale
    # check and caller authentication (never trust a caller-supplied desk)
    priceDesk: address = empty(address)
    scaleStatus: uint256 = 0
    priceDesk, scaleStatus = self._getPriceDeskAndScaleStatus(_asset, _config.assetDecimals)
    if scaleStatus != SCALE_COMPATIBLE:
        return 0

    # zero is the direct-call sentinel. A nonzero stale time is accepted only
    # as the global policy forwarded by the canonical price desk
    if _staleTime != 0 and (msg.sender != priceDesk or _priceDesk != priceDesk):
        return 0

    # quote freshness governs the eth/usd leg only
    staleTime: uint256 = self._getEffectiveStaleTime(_config.params.quoteStaleTime, _staleTime)
    if staleTime == 0:
        return 0

    # live asset and anchor decimals must still match their bindings
    if not self._hasExpectedDecimals(_asset, convert(_config.assetDecimals, uint256), PRICE_READ_GAS):
        return 0
    if not self._hasExpectedDecimals(ETH_USD_FEED, convert(ANCHOR_DECIMALS, uint256), PRICE_READ_GAS):
        return 0

    # raw weth per whole asset token (weth has 18 decimals)
    wethPerAsset: uint256 = self._getPoolTwapQuote(_config)
    if wethPerAsset == 0:
        return 0

    # eth/usd, normalized to 18 decimals
    ethUsdPrice: uint256 = self._getEthUsdPrice(staleTime)
    if ethUsdPrice == 0:
        return 0

    # usd per whole asset token (18 decimals); unrepresentable means unavailable
    isValid: bool = False
    price: uint256 = 0
    isValid, price = twapMath._mulDiv(wethPerAsset, ethUsdPrice, EIGHTEEN_DECIMALS)
    return price if isValid else 0


# utilities


@view
@external
def hasPriceFeed(_asset: address) -> bool:
    return self.feedConfig[_asset].params.pool != empty(address)


@view
@external
def hasPendingPriceFeedUpdate(_asset: address) -> bool:
    # any uncleared add / update / disable, including an expired one. The
    # proposal also stays visible while the desk's confirmation callback runs,
    # after the time lock action itself has been consumed
    return self.pendingUpdates[_asset].actionId != 0


@external
def addPriceSnapshot(_asset: address) -> bool:
    return False


@view
@internal
def _getEffectiveStaleTime(_feedStaleTime: uint256, _forwardedStaleTime: uint256) -> uint256:
    # a nonzero local policy is an absolute override (never min(global, local)).
    # Zero inherits the forwarded global policy or, on a direct call, mission
    # control's. Zero result means unavailable
    if _feedStaleTime != 0:
        if _feedStaleTime < MIN_LOCAL_STALE_TIME or _feedStaleTime > MAX_EFFECTIVE_STALE_TIME:
            return 0
        return _feedStaleTime

    staleTime: uint256 = _forwardedStaleTime
    if staleTime == 0:
        staleTime = self._getGlobalStaleTime()
    if staleTime == 0 or staleTime > MAX_EFFECTIVE_STALE_TIME:
        return 0
    return staleTime


@view
@internal
def _getGlobalStaleTime() -> uint256:
    missionControl: address = self._getRipeHqAddr(MISSION_CONTROL_ID)
    if missionControl == empty(address):
        return 0

    isValid: bool = False
    staleTime: uint256 = 0
    isValid, staleTime = self._readWord(missionControl, method_id("getPriceStaleTime()"), PRICE_READ_GAS)
    return staleTime if isValid else 0


@view
@internal
def _getPriceDeskAndScaleStatus(_asset: address, _decimals: uint8) -> (address, uint256):
    # returns hq's current price desk and whether its cached `tokenScale` is
    # compatible with the bound decimals. Zero scale is allowed (source-only
    # admission before scale setup); a nonzero mismatch is not
    priceDesk: address = self._getRipeHqAddr(PRICE_DESK_ID)
    if priceDesk == empty(address):
        return priceDesk, SCALE_UNREADABLE

    isValid: bool = False
    scale: uint256 = 0
    isValid, scale = self._readWord(priceDesk, abi_encode(_asset, method_id=method_id("tokenScale(address)")), PRICE_READ_GAS)
    if not isValid:
        return priceDesk, SCALE_UNREADABLE
    if scale != 0 and scale != 10 ** convert(_decimals, uint256):
        return priceDesk, SCALE_MISMATCH
    return priceDesk, SCALE_COMPATIBLE


@view
@internal
def _getRipeHqAddr(_regId: uint256) -> address:
    # bounded `RipeHq.getAddr`; only a deployed contract counts as an identity
    isValid: bool = False
    word: uint256 = 0
    isValid, word = self._readWord(addys._getRipeHq(), abi_encode(_regId, method_id=method_id("getAddr(uint256)")), PRICE_READ_GAS)
    if not isValid or word == 0 or word > MAX_UINT160:
        return empty(address)
    addr: address = convert(word, address)
    return addr if addr.is_contract else empty(address)


@view
@internal
def _hasExpectedDecimals(_target: address, _expectedDecimals: uint256, _gasCap: uint256) -> bool:
    isValid: bool = False
    decimals: uint256 = 0
    isValid, decimals = self._readWord(_target, method_id("decimals()"), _gasCap)
    return isValid and decimals == _expectedDecimals


# bounded calls


@view
@internal
def _readWord(_target: address, _data: Bytes[MAX_CALLDATA], _gasCap: uint256) -> (bool, uint256):
    # single-word static read: any revert, missing code or payload other
    # than exactly 32 bytes is reported as invalid, never propagated
    success: bool = False
    response: Bytes[WORD + 1] = b""
    success, response = raw_call(
        _target,
        _data,
        max_outsize=WORD + 1,
        gas=self._getCallGas(_gasCap),
        is_static_call=True,
        revert_on_failure=False,
    )
    if not success or len(response) != WORD:
        return False, 0
    return True, abi_decode(response, uint256)


@view
@internal
def _getCallGas(_cap: uint256) -> uint256:
    # forward at most the cap, and always keep the failure reserve so the
    # unavailable result can still be decoded and returned after a dependency
    # burns its whole allowance
    available: uint256 = msg.gas
    if available <= FAILURE_RESERVE:
        return 0
    return min(_cap, available - FAILURE_RESERVE)


###################
# Uniswap V3 Pool #
###################


@view
@internal
def _getPoolTwapQuote(_config: UniV3FeedConfig) -> uint256:
    # raw weth received for one whole asset token at the window's mean tick,
    # or zero when any pool guard fails
    pool: address = _config.params.pool
    window: uint32 = _config.params.twapWindowSeconds

    # slot0: initialized, unlocked and internally consistent; yields the latest observation index
    isValid: bool = False
    observationIndex: uint256 = 0
    isValid, observationIndex = self._getLatestObservationIndex(pool)
    if not isValid:
        return 0

    # current in-range liquidity must meet the feed's floor
    if not self._hasMinCurrentLiquidity(pool, _config.params.minCurrentLiquidity):
        return 0

    # latest observation must be initialized and no older than the feed's ceiling
    if not self._isLatestObservationFresh(pool, observationIndex, _config.params.maxObservationAgeSeconds):
        return 0

    # observe([window, 0]): time-weighted mean tick and harmonic mean liquidity
    meanTick: int256 = 0
    harmonicLiquidity: uint256 = 0
    isValid, meanTick, harmonicLiquidity = self._observeWindow(pool, window)
    if not isValid or harmonicLiquidity < convert(_config.params.minHarmonicLiquidity, uint256):
        return 0

    return twapMath._getQuoteAtTick(meanTick, 10 ** convert(_config.assetDecimals, uint256), _config.assetIsToken0)


@view
@internal
def _getLatestObservationIndex(_pool: address) -> (bool, uint256):
    success: bool = False
    response: Bytes[SLOT0_SIZE + 1] = b""
    success, response = raw_call(
        _pool,
        method_id("slot0()"),
        max_outsize=SLOT0_SIZE + 1,
        gas=self._getCallGas(PRICE_READ_GAS),
        is_static_call=True,
        revert_on_failure=False,
    )
    if not success or len(response) != SLOT0_SIZE:
        return False, 0

    # slot0() -> (sqrtPriceX96 uint160, tick int24, observationIndex uint16,
    #   observationCardinality uint16, observationCardinalityNext uint16,
    #   feeProtocol uint8, unlocked bool)
    slot0: uint256[7] = abi_decode(response, uint256[7])
    sqrtPriceX96: uint256 = slot0[0]
    tick: int256 = convert(convert(slot0[1], bytes32), int256)
    observationIndex: uint256 = slot0[2]
    cardinality: uint256 = slot0[3]
    cardinalityNext: uint256 = slot0[4]
    feeProtocol: uint256 = slot0[5]
    unlocked: uint256 = slot0[6]

    # initialized price within the tick math domain
    if sqrtPriceX96 < twapMath.MIN_SQRT_RATIO or sqrtPriceX96 >= twapMath.MAX_SQRT_RATIO:
        return False, 0
    if tick < twapMath.MIN_TICK or tick > twapMath.MAX_TICK:
        return False, 0

    # 1 <= cardinality <= cardinalityNext <= uint16 max, index inside the ring
    if cardinality == 0 or cardinality > MAX_UINT16 or observationIndex >= cardinality:
        return False, 0
    if cardinalityNext < cardinality or cardinalityNext > MAX_UINT16:
        return False, 0

    # canonical narrow words; the pool must not be mid-swap
    if feeProtocol > MAX_UINT8 or unlocked != 1:
        return False, 0
    return True, observationIndex


@view
@internal
def _hasMinCurrentLiquidity(_pool: address, _minLiquidity: uint128) -> bool:
    isValid: bool = False
    liquidity: uint256 = 0
    isValid, liquidity = self._readWord(_pool, method_id("liquidity()"), PRICE_READ_GAS)
    if not isValid or liquidity == 0 or liquidity > MAX_UINT128:
        return False
    return liquidity >= convert(_minLiquidity, uint256)


@view
@internal
def _isLatestObservationFresh(_pool: address, _observationIndex: uint256, _maxAge: uint32) -> bool:
    success: bool = False
    response: Bytes[OBSERVATION_SIZE + 1] = b""
    success, response = raw_call(
        _pool,
        abi_encode(_observationIndex, method_id=method_id("observations(uint256)")),
        max_outsize=OBSERVATION_SIZE + 1,
        gas=self._getCallGas(PRICE_READ_GAS),
        is_static_call=True,
        revert_on_failure=False,
    )
    if not success or len(response) != OBSERVATION_SIZE:
        return False

    # observations(i) -> (blockTimestamp uint32, tickCumulative int56,
    #   secondsPerLiquidityCumulativeX128 uint160, initialized bool)
    observation: uint256[4] = abi_decode(response, uint256[4])
    timestamp: uint256 = observation[0]
    tickCumulative: int256 = convert(convert(observation[1], bytes32), int256)
    liquidityCumulative: uint256 = observation[2]
    initialized: uint256 = observation[3]
    if timestamp > MAX_UINT32 or tickCumulative < MIN_INT56 or tickCumulative > MAX_INT56:
        return False
    if liquidityCumulative > MAX_UINT160 or initialized != 1:
        return False

    # uint32 modular age, matching the pool's own timestamp arithmetic. This
    # bounds extrapolation past the last written observation, not trade age
    now32: uint32 = convert(block.timestamp % 2 ** 32, uint32)
    age: uint32 = unsafe_sub(now32, convert(timestamp, uint32))
    return age <= _maxAge


@view
@internal
def _observeWindow(_pool: address, _window: uint32) -> (bool, int256, uint256):
    # exactly observe([window, 0]). The pool reverts with `OLD` when it lacks
    # history for the full window; the interval is never shortened or
    # substituted with spot
    secondsAgos: DynArray[uint32, 2] = [_window, 0]
    success: bool = False
    response: Bytes[OBSERVE_SIZE + 1] = b""
    success, response = raw_call(
        _pool,
        abi_encode(secondsAgos, method_id=method_id("observe(uint32[])")),
        max_outsize=OBSERVE_SIZE + 1,
        gas=self._getCallGas(OBSERVE_GAS),
        is_static_call=True,
        revert_on_failure=False,
    )
    if not success or len(response) != OBSERVE_SIZE:
        return False, 0, 0

    # observe(uint32[]) -> (int56[] tickCumulatives, uint160[] secondsPerLiquidityCumulativeX128s)
    # encoded as [offset 64, offset 160, len 2, tickPast, tickNow, len 2, liquidityPast, liquidityNow]
    words: uint256[8] = abi_decode(response, uint256[8])
    if words[0] != 64 or words[1] != 160 or words[2] != 2 or words[5] != 2:
        return False, 0, 0
    tickCumulativePast: int256 = convert(convert(words[3], bytes32), int256)
    tickCumulativeNow: int256 = convert(convert(words[4], bytes32), int256)
    liquidityCumulativePast: uint256 = words[6]
    liquidityCumulativeNow: uint256 = words[7]
    if tickCumulativePast < MIN_INT56 or tickCumulativePast > MAX_INT56:
        return False, 0, 0
    if tickCumulativeNow < MIN_INT56 or tickCumulativeNow > MAX_INT56:
        return False, 0, 0
    if liquidityCumulativePast > MAX_UINT160 or liquidityCumulativeNow > MAX_UINT160:
        return False, 0, 0

    # accumulator deltas are taken at their native widths inside the math
    # module so legitimate wraps survive; a zero tick delta is valid
    isValid: bool = False
    meanTick: int256 = 0
    isValid, meanTick = twapMath._getMeanTick(convert(tickCumulativePast, int56), convert(tickCumulativeNow, int56), _window)
    if not isValid:
        return False, 0, 0

    harmonicLiquidity: uint256 = twapMath._getHarmonicLiquidity(convert(liquidityCumulativePast, uint160), convert(liquidityCumulativeNow, uint160), _window)
    if harmonicLiquidity == 0:
        return False, 0, 0
    return True, meanTick, harmonicLiquidity


##################
# ETH/USD Anchor #
##################


@view
@internal
def _getEthUsdPrice(_staleTime: uint256) -> uint256:
    # direct chainlink read of the bound feed (no recursive desk lookup),
    # normalized to 18 decimals. Zero means unavailable
    success: bool = False
    response: Bytes[ROUND_DATA_SIZE + 1] = b""
    success, response = raw_call(
        ETH_USD_FEED,
        method_id("latestRoundData()"),
        max_outsize=ROUND_DATA_SIZE + 1,
        gas=self._getCallGas(ANCHOR_READ_GAS),
        is_static_call=True,
        revert_on_failure=False,
    )
    if not success or len(response) != ROUND_DATA_SIZE:
        return 0

    # latestRoundData() -> (roundId uint80, answer int256, startedAt uint256, updatedAt uint256, answeredInRound uint80)
    round: uint256[5] = abi_decode(response, uint256[5])
    roundId: uint256 = round[0]
    answer: uint256 = round[1]
    updatedAt: uint256 = round[3]
    answeredInRound: uint256 = round[4]

    # canonical round ids, answered in this round or later, positive answer
    if roundId == 0 or roundId > MAX_UINT80 or answeredInRound > MAX_UINT80 or answeredInRound < roundId:
        return 0
    if answer == 0 or answer > MAX_INT256:
        return 0

    # not from the future, and within the effective quote stale time
    if updatedAt == 0 or updatedAt > block.timestamp or block.timestamp - updatedAt > _staleTime:
        return 0

    # normalize to 18 decimals without overflow
    scale: uint256 = 10 ** (NORMALIZED_DECIMALS - convert(ANCHOR_DECIMALS, uint256))
    if answer > max_value(uint256) // scale:
        return 0
    return answer * scale


###############
# Feed Config #
###############


@view
@external
def getFeedConfig(_asset: address) -> UniV3FeedConfig:
    return self.feedConfig[_asset]


@view
@external
def getPendingFeed(_asset: address) -> PendingUniV3Feed:
    return self.pendingUpdates[_asset]


@view
@external
def getBoundAssetDecimals(_asset: address) -> (bool, uint8):
    return self.hasBoundDecimals[_asset], self.boundDecimals[_asset]


@view
@external
def factory() -> address:
    return FACTORY


@view
@external
def weth() -> address:
    return WETH


@view
@external
def ethUsdFeed() -> address:
    return ETH_USD_FEED


@view
@external
def anchorDecimals() -> uint8:
    return ANCHOR_DECIMALS


################
# Feed Changes #
################


# add new feed


@external
def addNewPriceFeed(_asset: address, _params: FeedParams) -> bool:
    return self._initiateFeedAction(_asset, _params, ACTION_ADD)


@external
def confirmNewPriceFeed(_asset: address) -> bool:
    return self._confirmFeedAction(_asset, ACTION_ADD)


@external
def cancelNewPendingPriceFeed(_asset: address) -> bool:
    return self._cancelFeedAction(_asset, ACTION_ADD)


# update feed


@external
def updatePriceFeed(_asset: address, _params: FeedParams) -> bool:
    return self._initiateFeedAction(_asset, _params, ACTION_UPDATE)


@external
def confirmPriceFeedUpdate(_asset: address) -> bool:
    return self._confirmFeedAction(_asset, ACTION_UPDATE)


@external
def cancelPriceFeedUpdate(_asset: address) -> bool:
    return self._cancelFeedAction(_asset, ACTION_UPDATE)


# disable feed


@external
def disablePriceFeed(_asset: address) -> bool:
    return self._initiateFeedAction(_asset, empty(FeedParams), ACTION_DISABLE)


@external
def confirmDisablePriceFeed(_asset: address) -> bool:
    return self._confirmFeedAction(_asset, ACTION_DISABLE)


@external
def cancelDisablePriceFeed(_asset: address) -> bool:
    return self._cancelFeedAction(_asset, ACTION_DISABLE)


# initiate feed action


@internal
def _initiateFeedAction(_asset: address, _params: FeedParams, _kind: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused
    assert _asset not in [empty(address), ETH, WETH] # dev: invalid asset

    # one action per asset at a time. Add needs no active feed; update and
    # disable need one. A pending add holds no capacity, so the cap is
    # rechecked at confirmation
    activeConfig: UniV3FeedConfig = self.feedConfig[_asset]
    if _kind == ACTION_ADD:
        assert activeConfig.params.pool == empty(address) # dev: feed already exists
    else:
        assert activeConfig.params.pool != empty(address) # dev: no active feed
    assert self.pendingUpdates[_asset].actionId == 0 # dev: pending feed action
    if _kind == ACTION_ADD:
        assert priceData.numAssets <= MAX_PRICED_ASSETS # dev: too many assets

    # disable carries the config being removed; add and update derive and
    # validate the candidate, which must already price under its own settings
    candidate: UniV3FeedConfig = activeConfig
    if _kind != ACTION_DISABLE:
        isValid: bool = False
        isValid, candidate = self._buildFeedConfig(_asset, _params)
        assert isValid # dev: invalid feed
        assert not self.hasBoundDecimals[_asset] or candidate.assetDecimals == self.boundDecimals[_asset] # dev: asset decimals changed
        if _kind == ACTION_UPDATE:
            assert keccak256(abi_encode(candidate)) != keccak256(abi_encode(activeConfig)) # dev: no change
        assert self._getPrice(_asset, candidate, 0, empty(address)) != 0 # dev: invalid feed

    # set to pending state
    aid: uint256 = timeLock._initiateAction()
    self.pendingUpdates[_asset] = PendingUniV3Feed(actionId=aid, kind=_kind, config=candidate)

    action: timeLock.PendingAction = timeLock.pendingActions[aid]
    log UniV3FeedProposed(
        asset=_asset,
        actionId=aid,
        kind=_kind,
        confirmationBlock=action.confirmBlock,
        expirationBlock=action.expiration,
        pool=candidate.params.pool,
        twapWindowSeconds=candidate.params.twapWindowSeconds,
        minCurrentLiquidity=candidate.params.minCurrentLiquidity,
        minHarmonicLiquidity=candidate.params.minHarmonicLiquidity,
        maxObservationAgeSeconds=candidate.params.maxObservationAgeSeconds,
        quoteStaleTime=candidate.params.quoteStaleTime,
        assetIsToken0=candidate.assetIsToken0,
        assetDecimals=candidate.assetDecimals,
        fee=candidate.fee,
    )
    return True


# confirm feed action


@internal
def _confirmFeedAction(_asset: address, _kind: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    pending: PendingUniV3Feed = self.pendingUpdates[_asset]
    aid: uint256 = pending.actionId
    assert aid != 0 # dev: no pending feed action
    assert pending.kind == _kind # dev: wrong feed operation

    # active state and capacity can have changed since the proposal
    if _kind == ACTION_ADD:
        assert self.feedConfig[_asset].params.pool == empty(address) # dev: feed already exists
        assert priceData.numAssets <= MAX_PRICED_ASSETS # dev: too many assets
    else:
        assert self.feedConfig[_asset].params.pool != empty(address) # dev: no active feed
    assert timeLock._canConfirmAction(aid) # dev: time lock not reached
    action: timeLock.PendingAction = timeLock.pendingActions[aid]

    # revalidate the candidate: identity metadata must be unchanged, the
    # canonical desk's token scale compatible, and the price still usable.
    # Pool price and liquidity may move; derived identity metadata cannot
    candidate: UniV3FeedConfig = pending.config
    priceDesk: address = empty(address)
    if _kind != ACTION_DISABLE:
        isValid: bool = False
        liveConfig: UniV3FeedConfig = empty(UniV3FeedConfig)
        isValid, liveConfig = self._buildFeedConfig(_asset, candidate.params)

        # an existing binding is checked before the metadata comparison. A first
        # add has no binding, so decimal drift there surfaces as changed metadata
        if isValid:
            assert not self.hasBoundDecimals[_asset] or liveConfig.assetDecimals == self.boundDecimals[_asset] # dev: asset decimals changed
        assert isValid and keccak256(abi_encode(liveConfig)) == keccak256(abi_encode(candidate)) # dev: feed metadata changed

        scaleStatus: uint256 = 0
        priceDesk, scaleStatus = self._getPriceDeskAndScaleStatus(_asset, candidate.assetDecimals)
        assert scaleStatus != SCALE_UNREADABLE # dev: invalid price desk
        assert scaleStatus == SCALE_COMPATIBLE # dev: token scale mismatch
        assert self._getPrice(_asset, candidate, 0, empty(address)) != 0 # dev: invalid feed

    # consume the time lock action. Everything below must succeed in this
    # same transaction; any later failure reverts the consumption too
    assert timeLock._confirmAction(aid) # dev: time lock not reached

    if _kind == ACTION_DISABLE:
        # disable never depends on a working pool, quote or desk
        self.feedConfig[_asset] = empty(UniV3FeedConfig)
        priceData._removePricedAsset(_asset)
    else:
        # provisional writes: the desk's static callback sees the complete
        # candidate config and the first-add decimal binding, while the
        # proposal stays readable and enumeration is unchanged. All of it,
        # plus the consumed action and logs, rolls back if qualification fails
        self.feedConfig[_asset] = candidate
        if _kind == ACTION_ADD and not self.hasBoundDecimals[_asset]:
            self.hasBoundDecimals[_asset] = True
            self.boundDecimals[_asset] = candidate.assetDecimals

        self._assertPriceSourceIsExecutable(priceDesk, _asset)
        if _kind == ACTION_ADD:
            priceData._addPricedAsset(_asset)

    self.pendingUpdates[_asset] = empty(PendingUniV3Feed)
    log UniV3FeedConfirmed(
        asset=_asset,
        actionId=aid,
        kind=_kind,
        confirmationBlock=action.confirmBlock,
        expirationBlock=action.expiration,
        pool=candidate.params.pool,
        twapWindowSeconds=candidate.params.twapWindowSeconds,
        minCurrentLiquidity=candidate.params.minCurrentLiquidity,
        minHarmonicLiquidity=candidate.params.minHarmonicLiquidity,
        maxObservationAgeSeconds=candidate.params.maxObservationAgeSeconds,
        quoteStaleTime=candidate.params.quoteStaleTime,
        assetIsToken0=candidate.assetIsToken0,
        assetDecimals=candidate.assetDecimals,
        fee=candidate.fee,
    )
    return True


@view
@internal
def _assertPriceSourceIsExecutable(_priceDesk: address, _asset: address):
    # the canonical desk calls this source back (default stale time 0) under
    # its own 250k stipend; it must return a positive price with status 1
    success: bool = False
    response: Bytes[QUALIFY_SIZE + 1] = b""
    success, response = raw_call(
        _priceDesk,
        abi_encode(_asset, method_id=method_id("qualifyCallerPriceSource(address)")),
        max_outsize=QUALIFY_SIZE + 1,
        gas=self._getCallGas(QUALIFY_GAS),
        is_static_call=True,
        revert_on_failure=False,
    )
    assert success and len(response) == QUALIFY_SIZE # dev: price source not executable

    result: uint256[2] = abi_decode(response, uint256[2])
    assert result[0] != 0 and result[1] == 1 # dev: price source not executable


# cancel feed action


@internal
def _cancelFeedAction(_asset: address, _kind: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    pending: PendingUniV3Feed = self.pendingUpdates[_asset]
    assert pending.actionId != 0 # dev: no pending feed action
    assert pending.kind == _kind # dev: wrong feed operation

    # cancellation needs an existing action, not a confirmable one: expired
    # proposals can still be cancelled, with no pool, quote or desk dependency
    assert timeLock._cancelAction(pending.actionId) # dev: no pending feed action
    self.pendingUpdates[_asset] = empty(PendingUniV3Feed)

    log UniV3FeedCancelled(asset=_asset, actionId=pending.actionId, kind=_kind)
    return True


# validation


@pure
@internal
def _isValidFeedParams(_params: FeedParams) -> bool:
    if _params.twapWindowSeconds < MIN_TWAP_WINDOW or _params.twapWindowSeconds > MAX_TWAP_WINDOW:
        return False
    if _params.minCurrentLiquidity == 0 or _params.minHarmonicLiquidity == 0:
        return False
    if _params.maxObservationAgeSeconds == 0 or _params.maxObservationAgeSeconds > MAX_OBSERVATION_AGE:
        return False

    # zero inherits the global policy; a local override must sit inside the explicit domain
    if _params.quoteStaleTime != 0 and (_params.quoteStaleTime < MIN_LOCAL_STALE_TIME or _params.quoteStaleTime > MAX_EFFECTIVE_STALE_TIME):
        return False
    return True


@view
@internal
def _buildFeedConfig(_asset: address, _params: FeedParams) -> (bool, UniV3FeedConfig):
    # derives the candidate config from bounded metadata reads and verifies
    # the pool's identity against the bound factory. Invalid means the
    # returned config must be ignored
    config: UniV3FeedConfig = empty(UniV3FeedConfig)
    if not self._isValidFeedParams(_params) or not _params.pool.is_contract:
        return False, config

    # asset decimals (0..18)
    isValid: bool = False
    value: uint256 = 0
    isValid, value = self._readWord(_asset, method_id("decimals()"), METADATA_READ_GAS)
    if not isValid or value > NORMALIZED_DECIMALS:
        return False, config
    config.params = _params
    config.assetDecimals = convert(value, uint8)

    # anchor decimals must still match the deployment binding
    if not self._hasExpectedDecimals(ETH_USD_FEED, convert(ANCHOR_DECIMALS, uint256), METADATA_READ_GAS):
        return False, config

    # pool must report the bound factory ...
    isValid, value = self._readWord(_params.pool, method_id("factory()"), METADATA_READ_GAS)
    if not isValid or value != convert(FACTORY, uint256):
        return False, config

    # ... and hold exactly asset / weth in canonical (numeric address) order
    config.assetIsToken0 = convert(_asset, uint256) < convert(WETH, uint256)
    token0: address = _asset if config.assetIsToken0 else WETH
    token1: address = WETH if config.assetIsToken0 else _asset
    isValid, value = self._readWord(_params.pool, method_id("token0()"), METADATA_READ_GAS)
    if not isValid or value != convert(token0, uint256):
        return False, config
    isValid, value = self._readWord(_params.pool, method_id("token1()"), METADATA_READ_GAS)
    if not isValid or value != convert(token1, uint256):
        return False, config

    # fee tier, and the factory must map (asset, weth, fee) back to this exact pool
    isValid, value = self._readWord(_params.pool, method_id("fee()"), METADATA_READ_GAS)
    if not isValid or value > MAX_UINT24:
        return False, config
    config.fee = convert(value, uint24)
    isValid, value = self._readWord(FACTORY, abi_encode(_asset, WETH, config.fee, method_id=method_id("getPool(address,address,uint24)")), METADATA_READ_GAS)
    if not isValid or value != convert(_params.pool, uint256):
        return False, config

    return True, config
