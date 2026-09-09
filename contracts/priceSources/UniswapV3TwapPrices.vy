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

interface UniswapV3Pool:
    def observe(_secondsAgos: DynArray[uint32, 2]) -> (DynArray[int56, 2], DynArray[uint160, 2]): view
    def observations(_index: uint256) -> Observation: view
    def liquidity() -> uint128: view
    def token0() -> address: view
    def token1() -> address: view
    def slot0() -> Slot0: view
    def fee() -> uint24: view

interface PriceDesk:
    def qualifyCallerPriceSource(_asset: address, _staleTime: uint256 = 0) -> (uint256, uint256): view
    def getPrice(_asset: address, _shouldRaise: bool = False) -> uint256: view

interface UniswapV3Factory:
    def getPool(_tokenA: address, _tokenB: address, _fee: uint24) -> address: view

interface TokenDecimals:
    def decimals() -> uint256: view

struct Slot0:
    sqrtPriceX96: uint160
    tick: int24
    observationIndex: uint16
    observationCardinality: uint16
    observationCardinalityNext: uint16
    feeProtocol: uint8
    unlocked: bool

struct Observation:
    blockTimestamp: uint32
    tickCumulative: int56
    secondsPerLiquidityCumulativeX128: uint160
    initialized: bool

struct UniV3FeedConfig:
    pool: address
    fee: uint24
    quoteAsset: address
    assetIsToken0: bool
    assetDecimals: uint256
    quoteDecimals: uint256
    baseLiquidity: uint128 # harmonic liquidity over the window when proposed
    twapWindow: uint32 # seconds, 0 inherits feedDefaults
    maxObservationAge: uint32 # seconds, 0 inherits feedDefaults

struct PendingUniV3Feed:
    actionId: uint256
    config: UniV3FeedConfig

struct FeedDefaults:
    twapWindow: uint32 # seconds
    maxObservationAge: uint32 # seconds
    minLiquidityRatio: uint256 # basis points of baseLiquidity (100_00 = 100%)
    minObservationCardinality: uint16

event NewUniV3FeedPending:
    asset: indexed(address)
    pool: indexed(address)
    quoteAsset: address
    twapWindow: uint32
    baseLiquidity: uint128
    confirmationBlock: uint256
    actionId: uint256

event NewUniV3FeedAdded:
    asset: indexed(address)
    pool: indexed(address)
    quoteAsset: address
    twapWindow: uint32

event NewUniV3FeedCancelled:
    asset: indexed(address)
    pool: indexed(address)

event UniV3FeedUpdatePending:
    asset: indexed(address)
    pool: indexed(address)
    prevPool: indexed(address)
    quoteAsset: address
    twapWindow: uint32
    baseLiquidity: uint128
    confirmationBlock: uint256
    actionId: uint256

event UniV3FeedUpdated:
    asset: indexed(address)
    pool: indexed(address)
    prevPool: indexed(address)
    quoteAsset: address
    twapWindow: uint32

event UniV3FeedUpdateCancelled:
    asset: indexed(address)
    pool: indexed(address)
    prevPool: indexed(address)

event DisableUniV3FeedPending:
    asset: indexed(address)
    pool: indexed(address)
    confirmationBlock: uint256
    actionId: uint256

event UniV3FeedDisabled:
    asset: indexed(address)
    pool: indexed(address)

event DisableUniV3FeedCancelled:
    asset: indexed(address)
    pool: indexed(address)

event FeedDefaultsSet:
    twapWindow: uint32
    maxObservationAge: uint32
    minLiquidityRatio: uint256
    minObservationCardinality: uint16

# core config
feedConfig: public(HashMap[address, UniV3FeedConfig]) # asset -> config
feedDefaults: public(FeedDefaults)

# pending changes
pendingUpdates: public(HashMap[address, PendingUniV3Feed]) # asset -> config

# uniswap v3
FACTORY: public(immutable(address))

HUNDRED_PERCENT: constant(uint256) = 100_00 # 100%
NORMALIZED_DECIMALS: constant(uint256) = 18
MAX_PRICED_ASSETS: constant(uint256) = 50
MIN_TWAP_WINDOW: constant(uint32) = 30 * 60 # 30 minutes
MAX_TWAP_WINDOW: constant(uint32) = 4 * 60 * 60 # 4 hours
MAX_OBSERVATION_AGE: constant(uint32) = 24 * 60 * 60 # 1 day


@deploy
def __init__(
    _ripeHq: address,
    _tempGov: address,
    _minPriceChangeTimeLock: uint256,
    _maxPriceChangeTimeLock: uint256,
    _factory: address,
):
    assert _factory != empty(address) # dev: invalid factory
    FACTORY = _factory

    # feeds inherit these unless a proposal overrides window / age
    self.feedDefaults = FeedDefaults(
        twapWindow=60 * 60, # 1 hour
        maxObservationAge=60 * 60, # 1 hour
        minLiquidityRatio=50_00, # 50% of the liquidity seen at proposal
        minObservationCardinality=500,
    )

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
    config: UniV3FeedConfig = self.feedConfig[_asset]
    if config.pool == empty(address):
        return 0
    return self._getPrice(config, _priceDesk)


@view
@external
def getPriceAndHasFeed(_asset: address, _staleTime: uint256 = 0, _priceDesk: address = empty(address)) -> (uint256, bool):
    config: UniV3FeedConfig = self.feedConfig[_asset]
    if config.pool == empty(address):
        return 0, False
    return self._getPrice(config, _priceDesk), True


@view
@internal
def _getPrice(_config: UniV3FeedConfig, _priceDesk: address) -> uint256:
    # raw quote-asset units received for one whole asset token, at the pool's
    # time-weighted mean tick
    quotePerAsset: uint256 = self._getPoolTwapQuote(_config)
    if quotePerAsset == 0:
        return 0

    # quote asset -> usd via price desk (freshness is that feed's own policy)
    priceDesk: address = _priceDesk
    if priceDesk == empty(address):
        priceDesk = addys._getPriceDeskAddr()
    quotePrice: uint256 = staticcall PriceDesk(priceDesk).getPrice(_config.quoteAsset, False)
    if quotePrice == 0:
        return 0

    # usd per whole asset token, 18 decimals
    isValid: bool = False
    price: uint256 = 0
    isValid, price = twapMath._mulDiv(quotePerAsset, quotePrice, 10 ** _config.quoteDecimals)
    return price if isValid else 0


# utilities


@view
@external
def hasPriceFeed(_asset: address) -> bool:
    return self.feedConfig[_asset].pool != empty(address)


@view
@external
def hasPendingPriceFeedUpdate(_asset: address) -> bool:
    return timeLock._hasPendingAction(self.pendingUpdates[_asset].actionId)


@external
def addPriceSnapshot(_asset: address) -> bool:
    return False


# qualify price source


@view
@internal
def _qualifyPriceSource(_asset: address):
    # the desk calls this source back under its own live stipend; a staged
    # config that cannot price through the desk is not admitted
    qualifiedPrice: uint256 = 0
    sourceStatus: uint256 = 0
    qualifiedPrice, sourceStatus = staticcall PriceDesk(addys._getPriceDeskAddr()).qualifyCallerPriceSource(_asset)
    assert qualifiedPrice != 0 and sourceStatus == 1 # dev: price source not executable


###################
# Uniswap V3 Twap #
###################


@view
@internal
def _getPoolTwapQuote(_config: UniV3FeedConfig) -> uint256:
    pool: address = _config.pool
    defaults: FeedDefaults = self.feedDefaults
    window: uint32 = _config.twapWindow if _config.twapWindow != 0 else defaults.twapWindow
    maxAge: uint32 = _config.maxObservationAge if _config.maxObservationAge != 0 else defaults.maxObservationAge
    minLiquidity: uint256 = convert(_config.baseLiquidity, uint256) * defaults.minLiquidityRatio // HUNDRED_PERCENT

    # pool must not be mid-swap (a swap callback could otherwise read a half-updated state)
    slot0: Slot0 = staticcall UniswapV3Pool(pool).slot0()
    if not slot0.unlocked:
        return 0

    # current in-range liquidity must hold the ratio of what was seen at proposal
    if convert(staticcall UniswapV3Pool(pool).liquidity(), uint256) < minLiquidity:
        return 0

    # the latest observation must be initialized and recent enough. This bounds
    # how far the pool extrapolates past its last write, not trade age.
    latest: Observation = staticcall UniswapV3Pool(pool).observations(convert(slot0.observationIndex, uint256))
    if not latest.initialized:
        return 0
    now: uint32 = convert(block.timestamp % (2 ** 32), uint32)
    if unsafe_sub(now, latest.blockTimestamp) > maxAge:
        return 0

    # mean tick and harmonic liquidity over the window
    isValid: bool = False
    meanTick: int256 = 0
    harmonicLiquidity: uint256 = 0
    isValid, meanTick, harmonicLiquidity = self._observe(pool, window)
    if not isValid or harmonicLiquidity < minLiquidity:
        return 0

    return twapMath._getQuoteAtTick(meanTick, 10 ** _config.assetDecimals, _config.assetIsToken0)


@view
@internal
def _observe(_pool: address, _window: uint32) -> (bool, int256, uint256):
    # cumulative accumulators at the window start and now. The pool reverts
    # with `OLD` when it lacks history for the full window.
    tickCumulatives: DynArray[int56, 2] = []
    liquidityCumulatives: DynArray[uint160, 2] = []
    tickCumulatives, liquidityCumulatives = staticcall UniswapV3Pool(_pool).observe([_window, 0])

    # time-weighted mean tick
    isValid: bool = False
    meanTick: int256 = 0
    isValid, meanTick = twapMath._getMeanTick(tickCumulatives[0], tickCumulatives[1], _window)
    if not isValid:
        return False, 0, 0

    # harmonic mean liquidity over the window
    harmonicLiquidity: uint256 = twapMath._getHarmonicLiquidity(liquidityCumulatives[0], liquidityCumulatives[1], _window)
    return harmonicLiquidity != 0, meanTick, harmonicLiquidity


# liquidity views


@view
@external
def getPoolLiquidity(_pool: address, _twapWindow: uint32 = 0) -> (uint256, uint256):
    # (current, harmonic over the window); zero window uses the default
    window: uint32 = _twapWindow if _twapWindow != 0 else self.feedDefaults.twapWindow
    na: bool = False
    meanTick: int256 = 0
    harmonicLiquidity: uint256 = 0
    na, meanTick, harmonicLiquidity = self._observe(_pool, window)
    return convert(staticcall UniswapV3Pool(_pool).liquidity(), uint256), harmonicLiquidity


@view
@external
def getFeedLiquidity(_asset: address) -> (uint256, uint256, uint256):
    # (current, harmonic over the feed's window, active floor) for an active feed
    config: UniV3FeedConfig = self.feedConfig[_asset]
    if config.pool == empty(address):
        return 0, 0, 0
    defaults: FeedDefaults = self.feedDefaults
    window: uint32 = config.twapWindow if config.twapWindow != 0 else defaults.twapWindow
    na: bool = False
    meanTick: int256 = 0
    harmonicLiquidity: uint256 = 0
    na, meanTick, harmonicLiquidity = self._observe(config.pool, window)
    minLiquidity: uint256 = convert(config.baseLiquidity, uint256) * defaults.minLiquidityRatio // HUNDRED_PERCENT
    return convert(staticcall UniswapV3Pool(config.pool).liquidity(), uint256), harmonicLiquidity, minLiquidity


################
# Add New Feed #
################


# initiate new feed


@external
def addNewPriceFeed(
    _asset: address,
    _pool: address,
    _twapWindow: uint32 = 0, # inherit feedDefaults
    _maxObservationAge: uint32 = 0, # inherit feedDefaults
) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused
    assert self.pendingUpdates[_asset].actionId == 0 # dev: pending feed action

    # validation
    config: UniV3FeedConfig = self._getFeedConfig(_asset, _pool, _twapWindow, _maxObservationAge)
    assert self._isValidNewFeed(_asset, config) # dev: invalid feed

    # set to pending state
    aid: uint256 = timeLock._initiateAction()
    self.pendingUpdates[_asset] = PendingUniV3Feed(
        actionId=aid,
        config=config,
    )

    log NewUniV3FeedPending(asset=_asset, pool=_pool, quoteAsset=config.quoteAsset, twapWindow=_twapWindow, baseLiquidity=config.baseLiquidity, confirmationBlock=timeLock._getActionConfirmationBlock(aid), actionId=aid)
    return True


# confirm new feed


@external
def confirmNewPriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validate again
    d: PendingUniV3Feed = self.pendingUpdates[_asset]
    assert d.config.pool != empty(address) # dev: no pending new feed
    assert self.feedConfig[_asset].pool == empty(address) # dev: no pending new feed
    if not self._isCurrentFeedIdentity(_asset, d.config) or not self._isValidNewFeed(_asset, d.config):
        self._cancelNewPendingPriceFeed(_asset, d.actionId)
        return False

    # check time lock
    assert timeLock._confirmAction(d.actionId) # dev: time lock not reached

    # stage the config so the desk can qualify this exact source. Any failure
    # reverts the staging, the time lock consumption and the pending state.
    self.feedConfig[_asset] = d.config
    self._qualifyPriceSource(_asset)

    self.pendingUpdates[_asset] = empty(PendingUniV3Feed)
    priceData._addPricedAsset(_asset)

    log NewUniV3FeedAdded(asset=_asset, pool=d.config.pool, quoteAsset=d.config.quoteAsset, twapWindow=d.config.twapWindow)
    return True


# cancel new feed


@external
def cancelNewPendingPriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    d: PendingUniV3Feed = self.pendingUpdates[_asset]
    assert d.actionId != 0 # dev: no pending new feed
    assert d.config.pool != empty(address) # dev: no pending new feed
    assert self.feedConfig[_asset].pool == empty(address) # dev: no pending new feed
    self._cancelNewPendingPriceFeed(_asset, d.actionId)
    log NewUniV3FeedCancelled(asset=_asset, pool=d.config.pool)
    return True


@internal
def _cancelNewPendingPriceFeed(_asset: address, _aid: uint256):
    assert timeLock._cancelAction(_aid) # dev: cannot cancel action
    self.pendingUpdates[_asset] = empty(PendingUniV3Feed)


# validation


@view
@external
def isValidNewFeed(_asset: address, _pool: address, _twapWindow: uint32 = 0, _maxObservationAge: uint32 = 0) -> bool:
    config: UniV3FeedConfig = self._getFeedConfig(_asset, _pool, _twapWindow, _maxObservationAge)
    return self._isValidNewFeed(_asset, config)


@view
@internal
def _isValidNewFeed(_asset: address, _config: UniV3FeedConfig) -> bool:
    if priceData.indexOfAsset[_asset] != 0 or self.feedConfig[_asset].pool != empty(address): # use the `updatePriceFeed` function instead
        return False
    return self._isValidFeedConfig(_asset, _config)


###############
# Update Feed #
###############


# initiate update feed


@external
def updatePriceFeed(
    _asset: address,
    _pool: address,
    _twapWindow: uint32 = 0, # inherit feedDefaults
    _maxObservationAge: uint32 = 0, # inherit feedDefaults
) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused
    assert self.pendingUpdates[_asset].actionId == 0 # dev: pending feed action

    # validation (an update always re-baselines liquidity, so the same settings are allowed)
    prevPool: address = self.feedConfig[_asset].pool
    config: UniV3FeedConfig = self._getFeedConfig(_asset, _pool, _twapWindow, _maxObservationAge)
    assert self._isValidUpdateFeed(_asset, config) # dev: invalid feed

    # set to pending state
    aid: uint256 = timeLock._initiateAction()
    self.pendingUpdates[_asset] = PendingUniV3Feed(
        actionId=aid,
        config=config,
    )

    log UniV3FeedUpdatePending(asset=_asset, pool=_pool, prevPool=prevPool, quoteAsset=config.quoteAsset, twapWindow=_twapWindow, baseLiquidity=config.baseLiquidity, confirmationBlock=timeLock._getActionConfirmationBlock(aid), actionId=aid)
    return True


# confirm update feed


@external
def confirmPriceFeedUpdate(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validate again
    d: PendingUniV3Feed = self.pendingUpdates[_asset]
    assert d.config.pool != empty(address) # dev: no pending update feed
    prevPool: address = self.feedConfig[_asset].pool
    assert prevPool != empty(address) # dev: no pending update feed
    if not self._isCurrentFeedIdentity(_asset, d.config) or not self._isValidUpdateFeed(_asset, d.config):
        self._cancelPriceFeedUpdate(_asset, d.actionId)
        return False

    # check time lock
    assert timeLock._confirmAction(d.actionId) # dev: time lock not reached

    # stage and qualify the updated config under the desk's live stipend
    self.feedConfig[_asset] = d.config
    self._qualifyPriceSource(_asset)

    self.pendingUpdates[_asset] = empty(PendingUniV3Feed)

    log UniV3FeedUpdated(asset=_asset, pool=d.config.pool, prevPool=prevPool, quoteAsset=d.config.quoteAsset, twapWindow=d.config.twapWindow)
    return True


# cancel update feed


@external
def cancelPriceFeedUpdate(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    d: PendingUniV3Feed = self.pendingUpdates[_asset]
    assert d.actionId != 0 # dev: no pending update feed
    assert d.config.pool != empty(address) # dev: no pending update feed
    assert self.feedConfig[_asset].pool != empty(address) # dev: no pending update feed
    self._cancelPriceFeedUpdate(_asset, d.actionId)
    log UniV3FeedUpdateCancelled(asset=_asset, pool=d.config.pool, prevPool=self.feedConfig[_asset].pool)
    return True


@internal
def _cancelPriceFeedUpdate(_asset: address, _aid: uint256):
    assert timeLock._cancelAction(_aid) # dev: cannot cancel action
    self.pendingUpdates[_asset] = empty(PendingUniV3Feed)


# validation


@view
@external
def isValidUpdateFeed(_asset: address, _pool: address, _twapWindow: uint32 = 0, _maxObservationAge: uint32 = 0) -> bool:
    config: UniV3FeedConfig = self._getFeedConfig(_asset, _pool, _twapWindow, _maxObservationAge)
    return self._isValidUpdateFeed(_asset, config)


@view
@internal
def _isValidUpdateFeed(_asset: address, _config: UniV3FeedConfig) -> bool:
    if priceData.indexOfAsset[_asset] == 0 or self.feedConfig[_asset].pool == empty(address): # use the `addNewPriceFeed` function instead
        return False
    return self._isValidFeedConfig(_asset, _config)


# feed config


@view
@internal
def _getFeedIdentity(_asset: address, _pool: address) -> UniV3FeedConfig:
    # the pool decides the quote asset: whichever of its two tokens is not the
    # asset. Callers validate the result; missing code yields an empty config.
    config: UniV3FeedConfig = empty(UniV3FeedConfig)
    if not _pool.is_contract or not _asset.is_contract:
        return config

    token0: address = staticcall UniswapV3Pool(_pool).token0()
    token1: address = staticcall UniswapV3Pool(_pool).token1()
    if _asset != token0 and _asset != token1:
        return config
    quoteAsset: address = token1 if _asset == token0 else token0
    if not quoteAsset.is_contract:
        return config

    config.pool = _pool
    config.fee = staticcall UniswapV3Pool(_pool).fee()
    config.quoteAsset = quoteAsset
    config.assetIsToken0 = _asset == token0
    config.assetDecimals = staticcall TokenDecimals(_asset).decimals()
    config.quoteDecimals = staticcall TokenDecimals(quoteAsset).decimals()
    return config


@view
@internal
def _getFeedConfig(_asset: address, _pool: address, _twapWindow: uint32, _maxObservationAge: uint32) -> UniV3FeedConfig:
    config: UniV3FeedConfig = self._getFeedIdentity(_asset, _pool)
    if config.pool == empty(address):
        return config
    config.twapWindow = _twapWindow
    config.maxObservationAge = _maxObservationAge

    # snapshot the pool's harmonic liquidity over the window; the read-time
    # floors are a ratio of this value
    window: uint32 = _twapWindow if _twapWindow != 0 else self.feedDefaults.twapWindow
    isValid: bool = False
    meanTick: int256 = 0
    harmonicLiquidity: uint256 = 0
    isValid, meanTick, harmonicLiquidity = self._observe(_pool, window)
    if isValid:
        config.baseLiquidity = convert(harmonicLiquidity, uint128)
    return config


@view
@internal
def _isCurrentFeedIdentity(_asset: address, _config: UniV3FeedConfig) -> bool:
    # bind confirmation to the reviewed pool, quote asset and decimals; the
    # liquidity baseline and settings are the proposal's own
    live: UniV3FeedConfig = self._getFeedIdentity(_asset, _config.pool)
    if live.pool != _config.pool or live.fee != _config.fee or live.quoteAsset != _config.quoteAsset:
        return False
    if live.assetIsToken0 != _config.assetIsToken0:
        return False
    return live.assetDecimals == _config.assetDecimals and live.quoteDecimals == _config.quoteDecimals


@view
@internal
def _isValidFeedConfig(_asset: address, _config: UniV3FeedConfig) -> bool:
    if empty(address) in [_asset, _config.pool, _config.quoteAsset]:
        return False
    if _config.assetDecimals > NORMALIZED_DECIMALS or _config.quoteDecimals > NORMALIZED_DECIMALS:
        return False
    if _config.baseLiquidity == 0:
        return False

    # settings: zero inherits feedDefaults, otherwise inside the domain
    if _config.twapWindow != 0 and (_config.twapWindow < MIN_TWAP_WINDOW or _config.twapWindow > MAX_TWAP_WINDOW):
        return False
    if _config.maxObservationAge > MAX_OBSERVATION_AGE:
        return False

    # the canonical factory must map (asset, quote, fee) to this exact pool
    if staticcall UniswapV3Factory(FACTORY).getPool(_asset, _config.quoteAsset, _config.fee) != _config.pool:
        return False

    # the observation ring must be able to hold a real history for the window
    slot0: Slot0 = staticcall UniswapV3Pool(_config.pool).slot0()
    if slot0.observationCardinality < self.feedDefaults.minObservationCardinality:
        return False

    # no v3 feed may depend on another v3 feed: the quote asset must be priced
    # elsewhere, and this asset must not be the quote of an existing feed
    if self.feedConfig[_config.quoteAsset].pool != empty(address) or self.pendingUpdates[_config.quoteAsset].actionId != 0:
        return False
    if self._isQuoteOfActiveFeed(_asset):
        return False

    # must be priceable under the proposed settings
    return self._getPrice(_config, empty(address)) != 0


@view
@internal
def _isQuoteOfActiveFeed(_asset: address) -> bool:
    numAssets: uint256 = priceData.numAssets
    if numAssets == 0:
        return False
    for i: uint256 in range(1, numAssets, bound=MAX_PRICED_ASSETS):
        if self.feedConfig[priceData.assets[i]].quoteAsset == _asset:
            return True
    return False


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
    prevPool: address = self.feedConfig[_asset].pool
    assert self._isValidDisablePriceFeed(_asset, prevPool) # dev: invalid asset

    # set to pending state
    aid: uint256 = timeLock._initiateAction()
    self.pendingUpdates[_asset] = PendingUniV3Feed(
        actionId=aid,
        config=empty(UniV3FeedConfig),
    )

    log DisableUniV3FeedPending(asset=_asset, pool=prevPool, confirmationBlock=timeLock._getActionConfirmationBlock(aid), actionId=aid)
    return True


# confirm disable feed


@external
def confirmDisablePriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validate again
    prevPool: address = self.feedConfig[_asset].pool
    d: PendingUniV3Feed = self.pendingUpdates[_asset]
    assert d.actionId != 0 # dev: no pending disable feed
    assert d.config.pool == empty(address) # dev: no pending disable feed
    assert prevPool != empty(address) # dev: no pending disable feed
    if not self._isValidDisablePriceFeed(_asset, prevPool):
        self._cancelDisablePriceFeed(_asset, d.actionId)
        return False

    # check time lock
    assert timeLock._confirmAction(d.actionId) # dev: time lock not reached

    # disable feed
    self.feedConfig[_asset] = empty(UniV3FeedConfig)
    self.pendingUpdates[_asset] = empty(PendingUniV3Feed)
    priceData._removePricedAsset(_asset)

    log UniV3FeedDisabled(asset=_asset, pool=prevPool)
    return True


# cancel disable feed


@external
def cancelDisablePriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    d: PendingUniV3Feed = self.pendingUpdates[_asset]
    assert d.actionId != 0 # dev: no pending disable feed
    assert d.config.pool == empty(address) # dev: no pending disable feed
    assert self.feedConfig[_asset].pool != empty(address) # dev: no pending disable feed
    self._cancelDisablePriceFeed(_asset, d.actionId)
    log DisableUniV3FeedCancelled(asset=_asset, pool=self.feedConfig[_asset].pool)
    return True


@internal
def _cancelDisablePriceFeed(_asset: address, _aid: uint256):
    assert timeLock._cancelAction(_aid) # dev: cannot cancel action
    self.pendingUpdates[_asset] = empty(PendingUniV3Feed)


# validation


@view
@external
def isValidDisablePriceFeed(_asset: address) -> bool:
    return self._isValidDisablePriceFeed(_asset, self.feedConfig[_asset].pool)


@view
@internal
def _isValidDisablePriceFeed(_asset: address, _prevPool: address) -> bool:
    if priceData.indexOfAsset[_asset] == 0:
        return False
    return _prevPool != empty(address)


#################
# Feed Defaults #
#################


@external
def setFeedDefaults(
    _twapWindow: uint32,
    _maxObservationAge: uint32,
    _minLiquidityRatio: uint256,
    _minObservationCardinality: uint16,
) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert self._isValidFeedDefaults(_twapWindow, _maxObservationAge, _minLiquidityRatio, _minObservationCardinality) # dev: invalid defaults

    self.feedDefaults = FeedDefaults(
        twapWindow=_twapWindow,
        maxObservationAge=_maxObservationAge,
        minLiquidityRatio=_minLiquidityRatio,
        minObservationCardinality=_minObservationCardinality,
    )
    log FeedDefaultsSet(twapWindow=_twapWindow, maxObservationAge=_maxObservationAge, minLiquidityRatio=_minLiquidityRatio, minObservationCardinality=_minObservationCardinality)
    return True


# validation


@view
@external
def isValidFeedDefaults(
    _twapWindow: uint32,
    _maxObservationAge: uint32,
    _minLiquidityRatio: uint256,
    _minObservationCardinality: uint16,
) -> bool:
    return self._isValidFeedDefaults(_twapWindow, _maxObservationAge, _minLiquidityRatio, _minObservationCardinality)


@pure
@internal
def _isValidFeedDefaults(
    _twapWindow: uint32,
    _maxObservationAge: uint32,
    _minLiquidityRatio: uint256,
    _minObservationCardinality: uint16,
) -> bool:
    if _twapWindow < MIN_TWAP_WINDOW or _twapWindow > MAX_TWAP_WINDOW:
        return False
    if _maxObservationAge == 0 or _maxObservationAge > MAX_OBSERVATION_AGE:
        return False
    if _minLiquidityRatio > HUNDRED_PERCENT:
        return False
    return _minObservationCardinality != 0
