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


struct OracleConfig:
    twapWindowSeconds: uint256
    maxAveragingPeriodSeconds: uint256
    maxAverageStalenessSeconds: uint256
    minRipeReserve: uint256
    minQuoteReserve: uint256
    maxSpotToTwapDeviationBps: uint256
    sequencerRestartGraceSeconds: uint256
    maxQuoteStaleSeconds: uint256
    activated: bool


struct PendingOracleConfig:
    actionId: uint256
    config: OracleConfig


struct Checkpoint:
    price0Cumulative: uint256
    price1Cumulative: uint256
    pairTimestamp: uint256
    localTimestamp: uint256
    reserve0: uint256
    reserve1: uint256


struct Average:
    price0Average: uint256
    price1Average: uint256
    averagingPeriodSeconds: uint256
    updatedAt: uint256


event CumulativePriceCheckpointUpdated:
    price0Cumulative: uint256
    price1Cumulative: uint256
    pairTimestamp: uint256
    localTimestamp: uint256
    reserve0: uint256
    reserve1: uint256


event CumulativePriceAverageUpdated:
    price0Average: uint256
    price1Average: uint256
    averagingPeriodSeconds: uint256
    averageUpdatedAt: uint256


event CumulativePriceCheckpointResynchronized:
    previousTimestamp: uint256
    newTimestamp: uint256
    reasonCode: uint256


event OracleConfigUpdatePending:
    actionId: uint256
    twapWindowSeconds: uint256
    maxAveragingPeriodSeconds: uint256
    maxAverageStalenessSeconds: uint256
    minRipeReserve: uint256
    minQuoteReserve: uint256
    maxSpotToTwapDeviationBps: uint256
    sequencerRestartGraceSeconds: uint256
    maxQuoteStaleSeconds: uint256
    confirmationBlock: uint256


event OracleConfigUpdatePrevious:
    actionId: uint256
    twapWindowSeconds: uint256
    maxAveragingPeriodSeconds: uint256
    maxAverageStalenessSeconds: uint256
    minRipeReserve: uint256
    minQuoteReserve: uint256
    maxSpotToTwapDeviationBps: uint256
    sequencerRestartGraceSeconds: uint256
    maxQuoteStaleSeconds: uint256
    activated: bool


event OracleConfigUpdateConfirmed:
    actionId: uint256
    twapWindowSeconds: uint256
    maxAveragingPeriodSeconds: uint256
    maxAverageStalenessSeconds: uint256
    minRipeReserve: uint256
    minQuoteReserve: uint256
    maxSpotToTwapDeviationBps: uint256
    sequencerRestartGraceSeconds: uint256
    maxQuoteStaleSeconds: uint256
    activated: bool


event OracleConfigUpdateCancelled:
    actionId: uint256


event OracleActivationPending:
    actionId: uint256
    confirmationBlock: uint256


event OracleActivated:
    actionId: uint256
    activationTimestamp: uint256


event OracleDeactivated:
    reasonCode: uint256


event OracleDisablePending:
    actionId: uint256
    confirmationBlock: uint256


# immutable source identity
RIPE_TOKEN: public(immutable(address))
QUOTE_TOKEN: public(immutable(address))
PAIR: public(immutable(address))
FACTORY: public(immutable(address))
SEQUENCER_UPTIME_FEED: public(immutable(address))
MODE: public(immutable(uint256))
RIPE_DECIMALS: public(immutable(uint256))
QUOTE_DECIMALS: public(immutable(uint256))
RIPE_IS_TOKEN0: public(immutable(bool))

# governed state
oracleConfig: public(OracleConfig)
pendingOracleConfig: public(PendingOracleConfig)
checkpoint: public(Checkpoint)
average: public(Average)
activationActionId: public(uint256)
disableActionId: public(uint256)
feedPending: public(bool)
activationTimestamp: public(uint256)

# exact Robinhood source identities
OFFICIAL_ROBINHOOD_V2_FACTORY: constant(address) = 0x8bcEaA40B9AcdfAedF85AdF4FF01F5Ad6517937f
OFFICIAL_ROBINHOOD_WETH: constant(address) = 0x0Bd7D308f8E1639FAb988df18A8011f41EAcAD73

# no accepted official Robinhood sequencer uptime feed currently exists
OFFICIAL_ROBINHOOD_SEQUENCER_FEED: constant(address) = empty(address)

MONITOR_BOUND: constant(uint256) = 1
PROTOCOL_ACCOUNTING: constant(uint256) = 2

UQ112: constant(uint256) = 2 ** 112
UINT32_MODULUS: constant(uint256) = 2 ** 32
MAX_UINT112: constant(uint256) = 2 ** 112 - 1
ONE: constant(uint256) = 10 ** 18
BPS: constant(uint256) = 10_000
MAX_DECIMALS: constant(uint256) = 18
MAX_TWAP_WINDOW: constant(uint256) = 24 * 60 * 60
MAX_QUOTE_STALE: constant(uint256) = 48 * 60 * 60
MIN_WINDOW_OR_GRACE: constant(uint256) = 30 * 60
MAX_DEVIATION_BPS: constant(uint256) = 2_000
EXTERNAL_CALL_GAS: constant(uint256) = 100_000
PRICE_DESK_CALL_GAS: constant(uint256) = 1_000_000

# diagnostic status codes
STATUS_OK: constant(uint256) = 0
STATUS_INACTIVE: constant(uint256) = 1
STATUS_PAIR_UNAVAILABLE: constant(uint256) = 2
STATUS_PAIR_IDENTITY: constant(uint256) = 3
STATUS_RESERVES: constant(uint256) = 4
STATUS_AVERAGE_ABSENT: constant(uint256) = 5
STATUS_AVERAGE_STALE: constant(uint256) = 6
STATUS_MATH: constant(uint256) = 7
STATUS_SPOT_DEVIATION: constant(uint256) = 8
STATUS_QUOTE_UNAVAILABLE: constant(uint256) = 9
STATUS_QUOTE_STALE_POLICY: constant(uint256) = 10
STATUS_SEQUENCER: constant(uint256) = 11

RESYNC_OVERLONG_PERIOD: constant(uint256) = 1
RESYNC_RESERVE_FLOOR: constant(uint256) = 2
DEACTIVATED_BY_GOVERNANCE: constant(uint256) = 1


@deploy
def __init__(
    _ripeHq: address,
    _tempGov: address,
    _factory: address,
    _ripeToken: address,
    _quoteToken: address,
    _pair: address,
    _minPriceChangeTimeLock: uint256,
    _maxPriceChangeTimeLock: uint256,
    _sequencerUptimeFeed: address,
    _mode: uint256,
):
    gov.__init__(_ripeHq, _tempGov, 0, 0, 0)
    addys.__init__(_ripeHq)
    priceData.__init__(False)
    timeLock.__init__(
        _minPriceChangeTimeLock,
        _maxPriceChangeTimeLock,
        0,
        _maxPriceChangeTimeLock,
    )

    assert _factory == OFFICIAL_ROBINHOOD_V2_FACTORY  # dev: invalid factory
    assert _quoteToken == OFFICIAL_ROBINHOOD_WETH  # dev: invalid quote
    assert empty(address) not in [_ripeToken, _quoteToken, _pair]  # dev: invalid source
    assert _ripeToken != _quoteToken  # dev: identical tokens
    assert _mode in [MONITOR_BOUND, PROTOCOL_ACCOUNTING]  # dev: invalid mode

    # Protocol accounting remains structurally unavailable until an official
    # Robinhood sequencer uptime feed is accepted and this constant is revised.
    if _mode == PROTOCOL_ACCOUNTING:
        raise "accounting unavailable"
    elif _sequencerUptimeFeed != empty(address):
        assert _sequencerUptimeFeed == OFFICIAL_ROBINHOOD_SEQUENCER_FEED  # dev: unverified sequencer

    validFactory: bool = False
    factoryPair: address = empty(address)
    validFactory, factoryPair = self._readFactoryPair(_factory, _ripeToken, _quoteToken)
    assert validFactory and factoryPair == _pair  # dev: factory pair mismatch

    validIdentity: bool = False
    pairFactory: address = empty(address)
    token0: address = empty(address)
    token1: address = empty(address)
    validIdentity, pairFactory, token0, token1 = self._readPairIdentity(_pair)
    assert validIdentity  # dev: pair identity unavailable
    assert pairFactory == _factory  # dev: pair factory mismatch
    assert token0 != token1 and _ripeToken in [token0, token1] and _quoteToken in [token0, token1]  # dev: token mismatch

    validReserves: bool = False
    reserve0: uint256 = 0
    reserve1: uint256 = 0
    pairTimestamp: uint256 = 0
    validReserves, reserve0, reserve1, pairTimestamp = self._readReserves(_pair)
    assert validReserves and reserve0 != 0 and reserve1 != 0  # dev: empty pair

    validSupply: bool = False
    totalSupply: uint256 = 0
    validSupply, totalSupply = self._readUint(_pair, method_id("totalSupply()"))
    assert validSupply and totalSupply != 0  # dev: empty lp supply

    validRipeDecimals: bool = False
    ripeDecimals: uint256 = 0
    validRipeDecimals, ripeDecimals = self._readUint(_ripeToken, method_id("decimals()"))
    assert validRipeDecimals and ripeDecimals <= MAX_DECIMALS  # dev: invalid ripe decimals

    validQuoteDecimals: bool = False
    quoteDecimals: uint256 = 0
    validQuoteDecimals, quoteDecimals = self._readUint(_quoteToken, method_id("decimals()"))
    assert validQuoteDecimals and quoteDecimals <= MAX_DECIMALS  # dev: invalid quote decimals

    FACTORY = _factory
    RIPE_TOKEN = _ripeToken
    QUOTE_TOKEN = _quoteToken
    PAIR = _pair
    SEQUENCER_UPTIME_FEED = _sequencerUptimeFeed
    MODE = _mode
    RIPE_DECIMALS = ripeDecimals
    QUOTE_DECIMALS = quoteDecimals
    RIPE_IS_TOKEN0 = token0 == _ripeToken

    # Retain the RIPE relationship only for direct lifecycle diagnostics.
    # MONITOR_BOUND is structurally invisible through the PriceSource
    # interface and must never be registered as an authoritative price feed.
    priceData._addPricedAsset(_ripeToken)
    self.feedPending = True


################
# Core pricing #
################


@view
@external
def getPrice(_asset: address, _staleTime: uint256 = 0, _oracleRegistry: address = empty(address)) -> uint256:
    return 0


@view
@external
def getPriceAndHasFeed(
    _asset: address,
    _staleTime: uint256 = 0,
    _oracleRegistry: address = empty(address),
) -> (uint256, bool):
    return 0, False


@view
@external
def hasPriceFeed(_asset: address) -> bool:
    return False


@view
@external
def hasPendingPriceFeedUpdate(_asset: address) -> bool:
    if _asset != RIPE_TOKEN:
        return False
    return (
        self.feedPending
        or timeLock._hasPendingAction(self.pendingOracleConfig.actionId)
        or timeLock._hasPendingAction(self.activationActionId)
        or timeLock._hasPendingAction(self.disableActionId)
    )


@external
def addPriceSnapshot(_asset: address) -> bool:
    return False


@view
@internal
def _getSafetyState(
    _staleTime: uint256,
    _oracleRegistry: address,
) -> (uint256, uint256, uint256, uint256, uint256, uint256, uint256):
    config: OracleConfig = self.oracleConfig
    if priceData.isPaused or not config.activated:
        return STATUS_INACTIVE, 0, 0, 0, 0, 0, 0

    if not self._sequencerIsHealthy(config.sequencerRestartGraceSeconds):
        return STATUS_SEQUENCER, 0, 0, 0, 0, 0, 0

    identityOk: bool = False
    pairFactory: address = empty(address)
    token0: address = empty(address)
    token1: address = empty(address)
    identityOk, pairFactory, token0, token1 = self._readPairIdentity(PAIR)
    if not identityOk:
        return STATUS_PAIR_UNAVAILABLE, 0, 0, 0, 0, 0, 0

    factoryOk: bool = False
    factoryPair: address = empty(address)
    factoryOk, factoryPair = self._readFactoryPair(FACTORY, RIPE_TOKEN, QUOTE_TOKEN)
    if (
        not factoryOk
        or factoryPair != PAIR
        or pairFactory != FACTORY
        or token0 == token1
        or RIPE_TOKEN not in [token0, token1]
        or QUOTE_TOKEN not in [token0, token1]
    ):
        return STATUS_PAIR_IDENTITY, 0, 0, 0, 0, 0, 0

    supplyOk: bool = False
    totalSupply: uint256 = 0
    supplyOk, totalSupply = self._readUint(PAIR, method_id("totalSupply()"))
    if not supplyOk:
        return STATUS_PAIR_UNAVAILABLE, 0, 0, 0, 0, 0, 0
    if totalSupply == 0:
        return STATUS_RESERVES, 0, 0, 0, 0, 0, 0

    reservesOk: bool = False
    reserve0: uint256 = 0
    reserve1: uint256 = 0
    pairTimestamp: uint256 = 0
    reservesOk, reserve0, reserve1, pairTimestamp = self._readReserves(PAIR)
    if not reservesOk:
        return STATUS_PAIR_UNAVAILABLE, 0, 0, 0, 0, 0, 0

    cumulative0Ok: bool = False
    cumulative1Ok: bool = False
    ignoredCumulative0: uint256 = 0
    ignoredCumulative1: uint256 = 0
    cumulative0Ok, ignoredCumulative0 = self._readUint(PAIR, method_id("price0CumulativeLast()"))
    cumulative1Ok, ignoredCumulative1 = self._readUint(PAIR, method_id("price1CumulativeLast()"))
    if not cumulative0Ok or not cumulative1Ok:
        return STATUS_PAIR_UNAVAILABLE, 0, 0, 0, 0, 0, 0

    reserveRipe: uint256 = reserve0 if RIPE_IS_TOKEN0 else reserve1
    reserveQuote: uint256 = reserve1 if RIPE_IS_TOKEN0 else reserve0
    if (
        reserveRipe == 0
        or reserveQuote == 0
        or reserveRipe < config.minRipeReserve
        or reserveQuote < config.minQuoteReserve
    ):
        return STATUS_RESERVES, 0, 0, reserveRipe, reserveQuote, 0, 0

    avg: Average = self.average
    if avg.updatedAt == 0 or avg.averagingPeriodSeconds < config.twapWindowSeconds:
        return STATUS_AVERAGE_ABSENT, 0, 0, reserveRipe, reserveQuote, 0, 0
    if block.timestamp < avg.updatedAt:
        return STATUS_AVERAGE_STALE, 0, 0, reserveRipe, reserveQuote, 0, 0
    averageAge: uint256 = block.timestamp - avg.updatedAt
    if averageAge > config.maxAverageStalenessSeconds:
        return STATUS_AVERAGE_STALE, 0, 0, reserveRipe, reserveQuote, averageAge, 0

    ripeQuoteAverage: uint256 = avg.price0Average if RIPE_IS_TOKEN0 else avg.price1Average
    quotePerRipe: uint256 = self._normalizeUq(ripeQuoteAverage)
    if quotePerRipe == 0:
        return STATUS_MATH, 0, 0, reserveRipe, reserveQuote, averageAge, 0

    spotUq: uint256 = reserveQuote * UQ112 // reserveRipe
    spotQuotePerRipe: uint256 = self._normalizeUq(spotUq)
    if spotQuotePerRipe == 0:
        return STATUS_MATH, 0, 0, reserveRipe, reserveQuote, averageAge, 0

    deviationOk: bool = False
    spotDeviation: uint256 = 0
    deviationOk, spotDeviation = self._deviationBps(spotQuotePerRipe, quotePerRipe)
    if not deviationOk:
        return STATUS_MATH, 0, 0, reserveRipe, reserveQuote, averageAge, 0
    if spotDeviation > config.maxSpotToTwapDeviationBps:
        return STATUS_SPOT_DEVIATION, 0, 0, reserveRipe, reserveQuote, averageAge, spotDeviation

    # PriceDesk does not expose quote timestamps or accept a caller-selected
    # stale ceiling. Refuse a looser supplied MissionControl ceiling instead
    # of silently accepting it.
    if _staleTime == 0 or _staleTime > config.maxQuoteStaleSeconds:
        return STATUS_QUOTE_STALE_POLICY, 0, 0, reserveRipe, reserveQuote, averageAge, spotDeviation

    quoteOk: bool = False
    quoteUsd: uint256 = 0
    quoteOk, quoteUsd = self._readQuoteUsd(_oracleRegistry)
    if not quoteOk or quoteUsd == 0:
        return STATUS_QUOTE_UNAVAILABLE, 0, 0, reserveRipe, reserveQuote, averageAge, spotDeviation

    priceOk: bool = False
    ripeUsd: uint256 = 0
    priceOk, ripeUsd = self._mulDivOne(quotePerRipe, quoteUsd)
    if not priceOk or ripeUsd == 0:
        return STATUS_MATH, 0, quoteUsd, reserveRipe, reserveQuote, averageAge, spotDeviation

    return STATUS_OK, ripeUsd, quoteUsd, reserveRipe, reserveQuote, averageAge, spotDeviation


################
# Observations #
################


@external
def update() -> bool:
    if priceData.isPaused:
        return False
    config: OracleConfig = self.oracleConfig
    if not self._isValidOracleConfig(config):
        return False
    if not self._sequencerIsHealthy(config.sequencerRestartGraceSeconds):
        return False

    valid: bool = False
    price0Cumulative: uint256 = 0
    price1Cumulative: uint256 = 0
    pairTimestamp: uint256 = 0
    reserve0: uint256 = 0
    reserve1: uint256 = 0
    valid, price0Cumulative, price1Cumulative, pairTimestamp, reserve0, reserve1 = self._getCurrentCumulativePrices()
    if not valid:
        return False

    reserveRipe: uint256 = reserve0 if RIPE_IS_TOKEN0 else reserve1
    reserveQuote: uint256 = reserve1 if RIPE_IS_TOKEN0 else reserve0
    cp: Checkpoint = self.checkpoint
    if cp.localTimestamp == 0:
        self._storeCheckpoint(price0Cumulative, price1Cumulative, pairTimestamp, reserve0, reserve1)
        return True

    if reserveRipe < config.minRipeReserve or reserveQuote < config.minQuoteReserve:
        previousTimestamp: uint256 = cp.localTimestamp
        self.average = empty(Average)
        self._storeCheckpoint(price0Cumulative, price1Cumulative, pairTimestamp, reserve0, reserve1)
        log CumulativePriceCheckpointResynchronized(
            previousTimestamp=previousTimestamp,
            newTimestamp=block.timestamp,
            reasonCode=RESYNC_RESERVE_FLOOR,
        )
        return True

    if block.timestamp <= cp.localTimestamp:
        return False
    elapsed: uint256 = block.timestamp - cp.localTimestamp
    if elapsed < config.twapWindowSeconds:
        return False

    if elapsed > config.maxAveragingPeriodSeconds:
        previousTimestamp: uint256 = cp.localTimestamp
        self.average = empty(Average)
        self._storeCheckpoint(price0Cumulative, price1Cumulative, pairTimestamp, reserve0, reserve1)
        log CumulativePriceCheckpointResynchronized(
            previousTimestamp=previousTimestamp,
            newTimestamp=block.timestamp,
            reasonCode=RESYNC_OVERLONG_PERIOD,
        )
        return True

    price0Average: uint256 = unsafe_sub(price0Cumulative, cp.price0Cumulative) // elapsed
    price1Average: uint256 = unsafe_sub(price1Cumulative, cp.price1Cumulative) // elapsed
    if price0Average == 0 or price1Average == 0:
        return False

    self.average = Average(
        price0Average=price0Average,
        price1Average=price1Average,
        averagingPeriodSeconds=elapsed,
        updatedAt=block.timestamp,
    )
    log CumulativePriceAverageUpdated(
        price0Average=price0Average,
        price1Average=price1Average,
        averagingPeriodSeconds=elapsed,
        averageUpdatedAt=block.timestamp,
    )
    self._storeCheckpoint(price0Cumulative, price1Cumulative, pairTimestamp, reserve0, reserve1)
    return True


@internal
def _storeCheckpoint(
    _price0Cumulative: uint256,
    _price1Cumulative: uint256,
    _pairTimestamp: uint256,
    _reserve0: uint256,
    _reserve1: uint256,
):
    self.checkpoint = Checkpoint(
        price0Cumulative=_price0Cumulative,
        price1Cumulative=_price1Cumulative,
        pairTimestamp=_pairTimestamp,
        localTimestamp=block.timestamp,
        reserve0=_reserve0,
        reserve1=_reserve1,
    )
    log CumulativePriceCheckpointUpdated(
        price0Cumulative=_price0Cumulative,
        price1Cumulative=_price1Cumulative,
        pairTimestamp=_pairTimestamp,
        localTimestamp=block.timestamp,
        reserve0=_reserve0,
        reserve1=_reserve1,
    )


@view
@internal
def _getCurrentCumulativePrices() -> (bool, uint256, uint256, uint256, uint256, uint256):
    identityOk: bool = False
    pairFactory: address = empty(address)
    token0: address = empty(address)
    token1: address = empty(address)
    identityOk, pairFactory, token0, token1 = self._readPairIdentity(PAIR)
    if (
        not identityOk
        or pairFactory != FACTORY
        or token0 == token1
        or RIPE_TOKEN not in [token0, token1]
        or QUOTE_TOKEN not in [token0, token1]
    ):
        return False, 0, 0, 0, 0, 0

    factoryOk: bool = False
    factoryPair: address = empty(address)
    factoryOk, factoryPair = self._readFactoryPair(FACTORY, RIPE_TOKEN, QUOTE_TOKEN)
    if not factoryOk or factoryPair != PAIR:
        return False, 0, 0, 0, 0, 0

    supplyOk: bool = False
    totalSupply: uint256 = 0
    supplyOk, totalSupply = self._readUint(PAIR, method_id("totalSupply()"))
    if not supplyOk or totalSupply == 0:
        return False, 0, 0, 0, 0, 0

    reservesOk: bool = False
    reserve0: uint256 = 0
    reserve1: uint256 = 0
    lastPairTimestamp: uint256 = 0
    reservesOk, reserve0, reserve1, lastPairTimestamp = self._readReserves(PAIR)
    if not reservesOk or reserve0 == 0 or reserve1 == 0:
        return False, 0, 0, 0, 0, 0

    cumulative0Ok: bool = False
    price0Cumulative: uint256 = 0
    cumulative0Ok, price0Cumulative = self._readUint(PAIR, method_id("price0CumulativeLast()"))
    if not cumulative0Ok:
        return False, 0, 0, 0, 0, 0

    cumulative1Ok: bool = False
    price1Cumulative: uint256 = 0
    cumulative1Ok, price1Cumulative = self._readUint(PAIR, method_id("price1CumulativeLast()"))
    if not cumulative1Ok:
        return False, 0, 0, 0, 0, 0

    currentTimestamp: uint256 = block.timestamp % UINT32_MODULUS
    elapsedSincePairWrite: uint256 = self._uint32Elapsed(currentTimestamp, lastPairTimestamp)
    if elapsedSincePairWrite != 0:
        price0: uint256 = reserve1 * UQ112 // reserve0
        price1: uint256 = reserve0 * UQ112 // reserve1
        price0Cumulative = unsafe_add(price0Cumulative, unsafe_mul(price0, elapsedSincePairWrite))
        price1Cumulative = unsafe_add(price1Cumulative, unsafe_mul(price1, elapsedSincePairWrite))

    return True, price0Cumulative, price1Cumulative, currentTimestamp, reserve0, reserve1


#################
# Configuration #
#################


@external
def updateOracleConfig(
    _twapWindowSeconds: uint256,
    _maxAveragingPeriodSeconds: uint256,
    _maxAverageStalenessSeconds: uint256,
    _minRipeReserve: uint256,
    _minQuoteReserve: uint256,
    _maxSpotToTwapDeviationBps: uint256,
    _sequencerRestartGraceSeconds: uint256,
    _maxQuoteStaleSeconds: uint256,
) -> bool:
    assert gov._canGovern(msg.sender)  # dev: no perms
    assert not priceData.isPaused  # dev: contract paused
    assert timeLock.actionTimeLock != 0  # dev: setup incomplete
    assert not timeLock._hasPendingAction(self.pendingOracleConfig.actionId)  # dev: config already pending

    config: OracleConfig = OracleConfig(
        twapWindowSeconds=_twapWindowSeconds,
        maxAveragingPeriodSeconds=_maxAveragingPeriodSeconds,
        maxAverageStalenessSeconds=_maxAverageStalenessSeconds,
        minRipeReserve=_minRipeReserve,
        minQuoteReserve=_minQuoteReserve,
        maxSpotToTwapDeviationBps=_maxSpotToTwapDeviationBps,
        sequencerRestartGraceSeconds=_sequencerRestartGraceSeconds,
        maxQuoteStaleSeconds=_maxQuoteStaleSeconds,
        activated=self.oracleConfig.activated,
    )
    assert self._isValidOracleConfig(config)  # dev: invalid config

    aid: uint256 = timeLock._initiateAction()
    self.pendingOracleConfig = PendingOracleConfig(actionId=aid, config=config)
    log OracleConfigUpdatePending(
        actionId=aid,
        twapWindowSeconds=_twapWindowSeconds,
        maxAveragingPeriodSeconds=_maxAveragingPeriodSeconds,
        maxAverageStalenessSeconds=_maxAverageStalenessSeconds,
        minRipeReserve=_minRipeReserve,
        minQuoteReserve=_minQuoteReserve,
        maxSpotToTwapDeviationBps=_maxSpotToTwapDeviationBps,
        sequencerRestartGraceSeconds=_sequencerRestartGraceSeconds,
        maxQuoteStaleSeconds=_maxQuoteStaleSeconds,
        confirmationBlock=timeLock._getActionConfirmationBlock(aid),
    )
    return True


@view
@external
def isValidOracleConfig(
    _twapWindowSeconds: uint256,
    _maxAveragingPeriodSeconds: uint256,
    _maxAverageStalenessSeconds: uint256,
    _minRipeReserve: uint256,
    _minQuoteReserve: uint256,
    _maxSpotToTwapDeviationBps: uint256,
    _sequencerRestartGraceSeconds: uint256,
    _maxQuoteStaleSeconds: uint256,
) -> bool:
    return self._isValidOracleConfig(
        OracleConfig(
            twapWindowSeconds=_twapWindowSeconds,
            maxAveragingPeriodSeconds=_maxAveragingPeriodSeconds,
            maxAverageStalenessSeconds=_maxAverageStalenessSeconds,
            minRipeReserve=_minRipeReserve,
            minQuoteReserve=_minQuoteReserve,
            maxSpotToTwapDeviationBps=_maxSpotToTwapDeviationBps,
            sequencerRestartGraceSeconds=_sequencerRestartGraceSeconds,
            maxQuoteStaleSeconds=_maxQuoteStaleSeconds,
            activated=False,
        )
    )


@view
@internal
def _isValidOracleConfig(_config: OracleConfig) -> bool:
    if _config.twapWindowSeconds < MIN_WINDOW_OR_GRACE or _config.twapWindowSeconds > MAX_TWAP_WINDOW:
        return False
    if (
        _config.maxAveragingPeriodSeconds < _config.twapWindowSeconds
        or _config.maxAveragingPeriodSeconds > 2 * _config.twapWindowSeconds
    ):
        return False
    if (
        _config.maxAverageStalenessSeconds < _config.twapWindowSeconds
        or _config.maxAverageStalenessSeconds > 2 * _config.twapWindowSeconds
    ):
        return False
    if _config.minRipeReserve == 0 or _config.minQuoteReserve == 0:
        return False
    if _config.maxSpotToTwapDeviationBps == 0 or _config.maxSpotToTwapDeviationBps > MAX_DEVIATION_BPS:
        return False
    if (
        _config.sequencerRestartGraceSeconds < MIN_WINDOW_OR_GRACE
        or _config.sequencerRestartGraceSeconds > MAX_TWAP_WINDOW
    ):
        return False
    return _config.maxQuoteStaleSeconds != 0 and _config.maxQuoteStaleSeconds <= MAX_QUOTE_STALE


@external
def confirmPriceFeedUpdate(_asset: address) -> bool:
    if _asset != RIPE_TOKEN:
        return False
    assert gov._canGovern(msg.sender)  # dev: no perms
    assert not priceData.isPaused  # dev: contract paused

    pending: PendingOracleConfig = self.pendingOracleConfig
    assert pending.actionId != 0  # dev: no pending config
    assert self._isValidOracleConfig(pending.config)  # dev: invalid config
    assert timeLock._confirmAction(pending.actionId)  # dev: time lock not reached

    oldConfig: OracleConfig = self.oracleConfig
    newConfig: OracleConfig = pending.config
    # Activation is a separate lifecycle action. A config proposal snapshots
    # parameters only; confirmation preserves the then-current live state.
    newConfig.activated = oldConfig.activated
    self.oracleConfig = newConfig
    self.pendingOracleConfig = empty(PendingOracleConfig)
    log OracleConfigUpdatePrevious(
        actionId=pending.actionId,
        twapWindowSeconds=oldConfig.twapWindowSeconds,
        maxAveragingPeriodSeconds=oldConfig.maxAveragingPeriodSeconds,
        maxAverageStalenessSeconds=oldConfig.maxAverageStalenessSeconds,
        minRipeReserve=oldConfig.minRipeReserve,
        minQuoteReserve=oldConfig.minQuoteReserve,
        maxSpotToTwapDeviationBps=oldConfig.maxSpotToTwapDeviationBps,
        sequencerRestartGraceSeconds=oldConfig.sequencerRestartGraceSeconds,
        maxQuoteStaleSeconds=oldConfig.maxQuoteStaleSeconds,
        activated=oldConfig.activated,
    )
    log OracleConfigUpdateConfirmed(
        actionId=pending.actionId,
        twapWindowSeconds=newConfig.twapWindowSeconds,
        maxAveragingPeriodSeconds=newConfig.maxAveragingPeriodSeconds,
        maxAverageStalenessSeconds=newConfig.maxAverageStalenessSeconds,
        minRipeReserve=newConfig.minRipeReserve,
        minQuoteReserve=newConfig.minQuoteReserve,
        maxSpotToTwapDeviationBps=newConfig.maxSpotToTwapDeviationBps,
        sequencerRestartGraceSeconds=newConfig.sequencerRestartGraceSeconds,
        maxQuoteStaleSeconds=newConfig.maxQuoteStaleSeconds,
        activated=newConfig.activated,
    )
    return True


@external
def cancelPriceFeedUpdate(_asset: address) -> bool:
    if _asset != RIPE_TOKEN:
        return False
    assert gov._canGovern(msg.sender)  # dev: no perms
    assert not priceData.isPaused  # dev: contract paused

    aid: uint256 = self.pendingOracleConfig.actionId
    assert timeLock._cancelAction(aid)  # dev: cannot cancel action
    self.pendingOracleConfig = empty(PendingOracleConfig)
    log OracleConfigUpdateCancelled(actionId=aid)
    return True


####################
# Feed activation  #
####################


@external
def initiateActivation() -> bool:
    assert gov._canGovern(msg.sender)  # dev: no perms
    assert not priceData.isPaused  # dev: contract paused
    assert timeLock.actionTimeLock != 0  # dev: setup incomplete
    assert not self.oracleConfig.activated  # dev: already active
    assert not timeLock._hasPendingAction(self.activationActionId)  # dev: activation pending
    assert self._activationConditionsMet()  # dev: activation conditions

    aid: uint256 = timeLock._initiateAction()
    self.activationActionId = aid
    self.feedPending = True
    log OracleActivationPending(actionId=aid, confirmationBlock=timeLock._getActionConfirmationBlock(aid))
    return True


@external
def confirmNewPriceFeed(_asset: address) -> bool:
    if _asset != RIPE_TOKEN:
        return False
    assert gov._canGovern(msg.sender)  # dev: no perms
    assert not priceData.isPaused  # dev: contract paused

    aid: uint256 = self.activationActionId
    assert aid != 0  # dev: no pending activation
    assert self._activationConditionsMet()  # dev: activation conditions
    assert timeLock._confirmAction(aid)  # dev: time lock not reached

    config: OracleConfig = self.oracleConfig
    config.activated = True
    self.oracleConfig = config
    self.activationActionId = 0
    self.feedPending = False
    self.activationTimestamp = block.timestamp
    log OracleActivated(actionId=aid, activationTimestamp=block.timestamp)
    return True


@external
def cancelNewPendingPriceFeed(_asset: address) -> bool:
    if _asset != RIPE_TOKEN:
        return False
    assert gov._canGovern(msg.sender)  # dev: no perms
    assert not priceData.isPaused  # dev: contract paused

    aid: uint256 = self.activationActionId
    assert timeLock._cancelAction(aid)  # dev: cannot cancel action
    self.activationActionId = 0
    self.feedPending = False
    return True


@view
@internal
def _activationConditionsMet() -> bool:
    config: OracleConfig = self.oracleConfig
    if not self._isValidOracleConfig(config):
        return False
    if MODE == PROTOCOL_ACCOUNTING and SEQUENCER_UPTIME_FEED == empty(address):
        return False
    if not self._sequencerIsHealthy(config.sequencerRestartGraceSeconds):
        return False

    avg: Average = self.average
    cp: Checkpoint = self.checkpoint
    if avg.updatedAt == 0 or cp.localTimestamp == 0 or avg.averagingPeriodSeconds < config.twapWindowSeconds:
        return False
    if block.timestamp < avg.updatedAt or block.timestamp - avg.updatedAt > config.maxAverageStalenessSeconds:
        return False

    valid: bool = False
    p0: uint256 = 0
    p1: uint256 = 0
    timestamp: uint256 = 0
    reserve0: uint256 = 0
    reserve1: uint256 = 0
    valid, p0, p1, timestamp, reserve0, reserve1 = self._getCurrentCumulativePrices()
    if not valid:
        return False

    reserveRipe: uint256 = reserve0 if RIPE_IS_TOKEN0 else reserve1
    reserveQuote: uint256 = reserve1 if RIPE_IS_TOKEN0 else reserve0
    return reserveRipe >= config.minRipeReserve and reserveQuote >= config.minQuoteReserve


@external
def disablePriceFeed(_asset: address) -> bool:
    if _asset != RIPE_TOKEN:
        return False
    assert gov._canGovern(msg.sender)  # dev: no perms
    assert not priceData.isPaused  # dev: contract paused
    assert timeLock.actionTimeLock != 0  # dev: setup incomplete
    assert self.oracleConfig.activated  # dev: not active
    assert not timeLock._hasPendingAction(self.disableActionId)  # dev: disable pending

    aid: uint256 = timeLock._initiateAction()
    self.disableActionId = aid
    log OracleDisablePending(actionId=aid, confirmationBlock=timeLock._getActionConfirmationBlock(aid))
    return True


@external
def confirmDisablePriceFeed(_asset: address) -> bool:
    if _asset != RIPE_TOKEN:
        return False
    assert gov._canGovern(msg.sender)  # dev: no perms
    assert not priceData.isPaused  # dev: contract paused

    aid: uint256 = self.disableActionId
    assert aid != 0  # dev: no pending disable
    assert timeLock._confirmAction(aid)  # dev: time lock not reached

    config: OracleConfig = self.oracleConfig
    config.activated = False
    self.oracleConfig = config
    self.disableActionId = 0
    self.activationTimestamp = 0
    self.feedPending = True
    log OracleDeactivated(reasonCode=DEACTIVATED_BY_GOVERNANCE)
    return True


@external
def cancelDisablePriceFeed(_asset: address) -> bool:
    if _asset != RIPE_TOKEN:
        return False
    assert gov._canGovern(msg.sender)  # dev: no perms
    assert not priceData.isPaused  # dev: contract paused

    aid: uint256 = self.disableActionId
    assert timeLock._cancelAction(aid)  # dev: cannot cancel action
    self.disableActionId = 0
    return True


###############
# Diagnostics #
###############


@view
@external
def getTwapQuotePerRipe() -> (uint256, uint256, uint256):
    avg: Average = self.average
    if avg.updatedAt == 0:
        return 0, 0, 0
    ripeQuoteAverage: uint256 = avg.price0Average if RIPE_IS_TOKEN0 else avg.price1Average
    return self._normalizeUq(ripeQuoteAverage), avg.averagingPeriodSeconds, avg.updatedAt


@view
@external
def getCurrentCumulativePrices() -> (uint256, uint256, uint256):
    valid: bool = False
    price0Cumulative: uint256 = 0
    price1Cumulative: uint256 = 0
    timestamp: uint256 = 0
    reserve0: uint256 = 0
    reserve1: uint256 = 0
    valid, price0Cumulative, price1Cumulative, timestamp, reserve0, reserve1 = self._getCurrentCumulativePrices()
    if not valid:
        return 0, 0, 0
    return price0Cumulative, price1Cumulative, timestamp


@view
@external
def getCheckpoint() -> (uint256, uint256, uint256, uint256, uint256):
    cp: Checkpoint = self.checkpoint
    return cp.price0Cumulative, cp.price1Cumulative, cp.pairTimestamp, cp.reserve0, cp.reserve1


@view
@external
def getReserveHealth() -> (uint256, uint256, uint256, bool):
    reservesOk: bool = False
    reserve0: uint256 = 0
    reserve1: uint256 = 0
    pairTimestamp: uint256 = 0
    reservesOk, reserve0, reserve1, pairTimestamp = self._readReserves(PAIR)
    if not reservesOk:
        return 0, 0, 0, False

    reserveRipe: uint256 = reserve0 if RIPE_IS_TOKEN0 else reserve1
    reserveQuote: uint256 = reserve1 if RIPE_IS_TOKEN0 else reserve0
    averageAge: uint256 = 0
    if self.average.updatedAt != 0 and block.timestamp >= self.average.updatedAt:
        averageAge = block.timestamp - self.average.updatedAt

    updateDue: bool = False
    if self.checkpoint.localTimestamp != 0 and block.timestamp >= self.checkpoint.localTimestamp:
        updateDue = block.timestamp - self.checkpoint.localTimestamp >= self.oracleConfig.twapWindowSeconds
    return reserveRipe, reserveQuote, averageAge, updateDue


@view
@external
def getSafetyState(_oracleRegistry: address) -> (uint256, uint256, uint256, uint256, uint256, uint256, uint256):
    return self._getSafetyState(self.oracleConfig.maxQuoteStaleSeconds, _oracleRegistry)


@view
@external
def getSafetyStateAtStaleTime(
    _staleTime: uint256,
    _oracleRegistry: address,
) -> (uint256, uint256, uint256, uint256, uint256, uint256, uint256):
    return self._getSafetyState(_staleTime, _oracleRegistry)


@view
@external
def getModeConstants() -> (uint256, uint256):
    return MONITOR_BOUND, PROTOCOL_ACCOUNTING


########################
# Captured dependencies #
########################


@view
@internal
def _readUint(_target: address, _selector: Bytes[4]) -> (bool, uint256):
    if _target == empty(address) or not _target.is_contract:
        return False, 0
    success: bool = False
    response: Bytes[33] = b""
    success, response = raw_call(
        _target,
        _selector,
        max_outsize=33,
        gas=EXTERNAL_CALL_GAS,
        is_static_call=True,
        revert_on_failure=False,
    )
    if not success or len(response) != 32:
        return False, 0
    return True, abi_decode(response, uint256)


@view
@internal
def _readAddress(_target: address, _selector: Bytes[4]) -> (bool, address):
    valid: bool = False
    rawValue: uint256 = 0
    valid, rawValue = self._readUint(_target, _selector)
    if not valid or rawValue >= 2 ** 160:
        return False, empty(address)
    return True, convert(rawValue, address)


@view
@internal
def _readFactoryPair(_factory: address, _tokenA: address, _tokenB: address) -> (bool, address):
    if _factory == empty(address) or not _factory.is_contract:
        return False, empty(address)
    success: bool = False
    response: Bytes[33] = b""
    success, response = raw_call(
        _factory,
        concat(method_id("getPair(address,address)"), abi_encode(_tokenA, _tokenB)),
        max_outsize=33,
        gas=EXTERNAL_CALL_GAS,
        is_static_call=True,
        revert_on_failure=False,
    )
    if not success or len(response) != 32:
        return False, empty(address)
    rawValue: uint256 = abi_decode(response, uint256)
    if rawValue >= 2 ** 160:
        return False, empty(address)
    return True, convert(rawValue, address)


@view
@internal
def _readPairIdentity(_pair: address) -> (bool, address, address, address):
    factoryOk: bool = False
    pairFactory: address = empty(address)
    factoryOk, pairFactory = self._readAddress(_pair, method_id("factory()"))
    if not factoryOk:
        return False, empty(address), empty(address), empty(address)

    token0Ok: bool = False
    token0: address = empty(address)
    token0Ok, token0 = self._readAddress(_pair, method_id("token0()"))
    if not token0Ok:
        return False, empty(address), empty(address), empty(address)

    token1Ok: bool = False
    token1: address = empty(address)
    token1Ok, token1 = self._readAddress(_pair, method_id("token1()"))
    if not token1Ok:
        return False, empty(address), empty(address), empty(address)
    return True, pairFactory, token0, token1


@view
@internal
def _readReserves(_pair: address) -> (bool, uint256, uint256, uint256):
    if _pair == empty(address) or not _pair.is_contract:
        return False, 0, 0, 0
    success: bool = False
    response: Bytes[97] = b""
    success, response = raw_call(
        _pair,
        method_id("getReserves()"),
        max_outsize=97,
        gas=EXTERNAL_CALL_GAS,
        is_static_call=True,
        revert_on_failure=False,
    )
    if not success or len(response) != 96:
        return False, 0, 0, 0
    reserve0: uint256 = 0
    reserve1: uint256 = 0
    timestamp: uint256 = 0
    reserve0, reserve1, timestamp = abi_decode(response, (uint256, uint256, uint256))
    if reserve0 > MAX_UINT112 or reserve1 > MAX_UINT112 or timestamp >= UINT32_MODULUS:
        return False, 0, 0, 0
    return True, reserve0, reserve1, timestamp


@view
@internal
def _readQuoteUsd(_oracleRegistry: address) -> (bool, uint256):
    if _oracleRegistry == empty(address) or _oracleRegistry == self or not _oracleRegistry.is_contract:
        return False, 0
    success: bool = False
    response: Bytes[33] = b""
    success, response = raw_call(
        _oracleRegistry,
        concat(method_id("getPrice(address,bool)"), abi_encode(QUOTE_TOKEN, False)),
        max_outsize=33,
        gas=PRICE_DESK_CALL_GAS,
        is_static_call=True,
        revert_on_failure=False,
    )
    if not success or len(response) != 32:
        return False, 0
    return True, abi_decode(response, uint256)


@view
@internal
def _sequencerIsHealthy(_grace: uint256) -> bool:
    feed: address = SEQUENCER_UPTIME_FEED
    if feed == empty(address):
        return MODE == MONITOR_BOUND
    if not feed.is_contract:
        return False

    success: bool = False
    response: Bytes[161] = b""
    success, response = raw_call(
        feed,
        method_id("latestRoundData()"),
        max_outsize=161,
        gas=EXTERNAL_CALL_GAS,
        is_static_call=True,
        revert_on_failure=False,
    )
    if not success or len(response) != 160:
        return False

    roundId: uint256 = 0
    answer: int256 = 0
    startedAt: uint256 = 0
    updatedAt: uint256 = 0
    answeredInRound: uint256 = 0
    roundId, answer, startedAt, updatedAt, answeredInRound = abi_decode(
        response,
        (uint256, int256, uint256, uint256, uint256),
    )
    if answer != 0 or startedAt == 0 or updatedAt == 0:
        return False
    if startedAt > block.timestamp or updatedAt > block.timestamp or answeredInRound < roundId:
        return False
    return block.timestamp - startedAt >= _grace


########
# Math #
########


@view
@internal
def _uint32Elapsed(_current: uint256, _previous: uint256) -> uint256:
    if _current >= UINT32_MODULUS or _previous >= UINT32_MODULUS:
        return 0
    if _current >= _previous:
        return _current - _previous
    return UINT32_MODULUS - _previous + _current


@view
@internal
def _normalizeUq(_uq: uint256) -> uint256:
    exponent: uint256 = 18 + RIPE_DECIMALS - QUOTE_DECIMALS
    scale: uint256 = 10 ** exponent
    whole: uint256 = _uq // UQ112
    remainder: uint256 = _uq % UQ112
    if whole > max_value(uint256) // scale:
        return 0
    normalizedWhole: uint256 = whole * scale
    normalizedRemainder: uint256 = remainder * scale // UQ112
    if normalizedWhole > max_value(uint256) - normalizedRemainder:
        return 0
    return normalizedWhole + normalizedRemainder


@view
@internal
def _deviationBps(_spot: uint256, _twap: uint256) -> (bool, uint256):
    if _twap == 0:
        return False, 0
    difference: uint256 = _spot - _twap if _spot >= _twap else _twap - _spot
    whole: uint256 = difference // _twap
    remainder: uint256 = difference % _twap
    if whole > max_value(uint256) // BPS:
        return False, 0
    wholeBps: uint256 = whole * BPS
    if remainder > max_value(uint256) // BPS:
        return False, 0
    remainderBps: uint256 = remainder * BPS // _twap
    if wholeBps > max_value(uint256) - remainderBps:
        return False, 0
    return True, wholeBps + remainderBps


@view
@internal
def _mulDivOne(_a: uint256, _b: uint256) -> (bool, uint256):
    whole: uint256 = _a // ONE
    remainder: uint256 = _a % ONE
    if whole != 0 and _b > max_value(uint256) // whole:
        return False, 0
    wholeProduct: uint256 = whole * _b
    if remainder != 0 and _b > max_value(uint256) // remainder:
        return False, 0
    remainderProduct: uint256 = remainder * _b // ONE
    if wholeProduct > max_value(uint256) - remainderProduct:
        return False, 0
    return True, wholeProduct + remainderProduct
