# Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
# Ripe Foundation (C) 2026
# @version 0.4.3
# Imported UniswapV3TwapMath retains its separate MIT notice and provenance.

implements: PriceSource

exports: gov.__interface__
exports: addys.__interface__
exports: priceData.__interface__
exports: timeLock.__interface__
initializes: gov
initializes: addys
initializes: priceData[addys := addys]
initializes: timeLock[gov := gov]

from interfaces import PriceSource

import contracts.modules.LocalGov as gov
import contracts.modules.Addys as addys
import contracts.priceSources.modules.PriceSourceData as priceData
import contracts.modules.TimeLock as timeLock
import contracts.priceSources.modules.UniswapV3TwapMath as math

struct FeedParams:
    pool: address
    twapWindowSeconds: uint32
    minCurrentLiquidity: uint128
    minHarmonicLiquidity: uint128
    maxObservationAgeSeconds: uint32
    quoteStaleTime: uint256

struct UniV3FeedConfig:
    params: FeedParams
    assetIsToken0: bool
    assetDecimals: uint8
    fee: uint24

struct PendingUniV3Feed:
    actionId: uint256
    kind: uint256
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

configs: HashMap[address, UniV3FeedConfig]
pending: HashMap[address, PendingUniV3Feed]
decimalsBound: HashMap[address, bool]
boundDecimals: HashMap[address, uint8]

FACTORY: immutable(address)
WETH: immutable(address)
ETH_USD_FEED: immutable(address)
ANCHOR_DECIMALS: immutable(uint8)

MIN_TWAP_WINDOW: constant(uint32) = 1800
MAX_TWAP_WINDOW: constant(uint32) = 14400
MAX_OBSERVATION_AGE: constant(uint32) = 86400
MIN_LOCAL_STALE_TIME: constant(uint256) = 300
MAX_EFFECTIVE_STALE_TIME: constant(uint256) = 604800
ETH: constant(address) = 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE
# Preserve decoding/return gas even when earlier dependencies consume their caps.
FAILURE_RESERVE: constant(uint256) = 20000


@deploy
def __init__(
    ripeHq: address, tempGov: address,
    minActionTimeLock: uint256, maxActionTimeLock: uint256,
    factory: address, weth: address, ethUsdFeed: address,
):
    assert ripeHq.is_contract and factory.is_contract and weth.is_contract and ethUsdFeed.is_contract # dev: invalid dependencies
    valid: bool = False
    decimals: uint256 = 0
    valid, decimals = self._scalar(weth, method_id("decimals()"), 30000)
    assert valid and decimals == 18 # dev: invalid dependencies
    valid, decimals = self._scalar(ethUsdFeed, method_id("decimals()"), 30000)
    assert valid and decimals <= 18 # dev: invalid dependencies
    ANCHOR_DECIMALS = convert(decimals, uint8)
    FACTORY = factory
    WETH = weth
    ETH_USD_FEED = ethUsdFeed
    gov.__init__(ripeHq, tempGov, 0, 0, 0)
    addys.__init__(ripeHq)
    priceData.__init__(False)
    # Exclude this source from FinishSetup setActionTimeLockAfterSetup sweeps.
    timeLock.__init__(minActionTimeLock, maxActionTimeLock, minActionTimeLock, maxActionTimeLock)


@view
@internal
def _callGas(cap: uint256) -> uint256:
    available: uint256 = msg.gas
    if available <= FAILURE_RESERVE:
        return 0
    return min(cap, available - FAILURE_RESERVE)


@view
@internal
def _scalar(target: address, data: Bytes[132], cap: uint256) -> (bool, uint256):
    success: bool = False
    response: Bytes[33] = b""
    success, response = raw_call(target, data, gas=self._callGas(cap), max_outsize=33, is_static_call=True, revert_on_failure=False)
    if not success or len(response) != 32:
        return False, 0
    return True, abi_decode(response, uint256)


@view
@internal
def _identity(regId: uint256) -> address:
    valid: bool = False
    word: uint256 = 0
    valid, word = self._scalar(addys._getRipeHq(), abi_encode(regId, method_id=method_id("getAddr(uint256)")), 15000)
    if not valid or word == 0 or word >= 2**160:
        return empty(address)
    addr: address = convert(word, address)
    return addr if addr.is_contract else empty(address)


@view
@internal
def _deskScale(asset: address, decimals: uint8) -> (address, uint256):
    # 0: unreadable identity/scale; 1: compatible; 2: nonzero mismatch.
    desk: address = self._identity(7)
    if desk == empty(address):
        return desk, 0
    valid: bool = False
    scale: uint256 = 0
    valid, scale = self._scalar(desk, abi_encode(asset, method_id=method_id("tokenScale(address)")), 15000)
    if not valid:
        return desk, 0
    if scale != 0 and scale != 10**convert(decimals, uint256):
        return desk, 2
    return desk, 1


@view
@internal
def _effectiveAge(local: uint256, forwarded: uint256) -> uint256:
    age: uint256 = local
    if age != 0:
        if age < MIN_LOCAL_STALE_TIME or age > MAX_EFFECTIVE_STALE_TIME:
            return 0
        return age
    age = forwarded
    if age == 0:
        mc: address = self._identity(5)
        if mc == empty(address):
            return 0
        valid: bool = False
        valid, age = self._scalar(mc, method_id("getPriceStaleTime()"), 15000)
        if not valid:
            return 0
    return age if age > 0 and age <= MAX_EFFECTIVE_STALE_TIME else 0


@view
@external
def getPrice(asset: address, _staleTime: uint256 = 0, _oracleRegistry: address = empty(address)) -> uint256:
    config: UniV3FeedConfig = self.configs[asset]
    if config.params.pool == empty(address):
        return 0
    return self._price(asset, config, _staleTime, _oracleRegistry)


@view
@external
def getPriceAndHasFeed(asset: address, _staleTime: uint256 = 0, _oracleRegistry: address = empty(address)) -> (uint256, bool):
    config: UniV3FeedConfig = self.configs[asset]
    if config.params.pool == empty(address):
        return 0, False
    return self._price(asset, config, _staleTime, _oracleRegistry), True


@view
@internal
def _price(asset: address, config: UniV3FeedConfig, forwarded: uint256, registry: address) -> uint256:
    desk: address = empty(address)
    status: uint256 = 0
    desk, status = self._deskScale(asset, config.assetDecimals)
    if status != 1:
        return 0
    if forwarded != 0 and (msg.sender != desk or registry != desk):
        return 0
    age: uint256 = self._effectiveAge(config.params.quoteStaleTime, forwarded)
    if age == 0:
        return 0
    valid: bool = False
    decimals: uint256 = 0
    valid, decimals = self._scalar(asset, method_id("decimals()"), 15000)
    if not valid or decimals != convert(config.assetDecimals, uint256):
        return 0
    valid, decimals = self._scalar(ETH_USD_FEED, method_id("decimals()"), 15000)
    if not valid or decimals != convert(ANCHOR_DECIMALS, uint256):
        return 0
    quote: uint256 = self._poolQuote(config)
    if quote == 0:
        return 0
    usd: uint256 = self._anchorPrice(age)
    if usd == 0:
        return 0
    result: uint256 = 0
    valid, result = math.mulDiv(quote, usd, 10**18)
    return result if valid else 0


@view
@internal
def _poolQuote(config: UniV3FeedConfig) -> uint256:
    pool: address = config.params.pool
    success: bool = False
    slot: Bytes[225] = b""
    success, slot = raw_call(pool, method_id("slot0()"), max_outsize=225, gas=self._callGas(15000), is_static_call=True, revert_on_failure=False)
    if not success or len(slot) != 224:
        return 0
    words: uint256[7] = abi_decode(slot, uint256[7])
    tick: int256 = convert(convert(words[1], bytes32), int256)
    if words[0] < math.MIN_SQRT_RATIO or words[0] >= math.MAX_SQRT_RATIO or tick < math.MIN_TICK or tick > math.MAX_TICK:
        return 0
    if words[3] == 0 or words[3] > 65535 or words[2] >= words[3] or words[4] < words[3] or words[4] > 65535 or words[5] > 255 or words[6] != 1:
        return 0
    liquid: uint256 = 0
    success, liquid = self._scalar(pool, method_id("liquidity()"), 15000)
    if not success or liquid > 2**128 - 1 or liquid < convert(config.params.minCurrentLiquidity, uint256) or liquid == 0:
        return 0
    observation: Bytes[129] = b""
    success, observation = raw_call(pool, abi_encode(words[2], method_id=method_id("observations(uint256)")), max_outsize=129, gas=self._callGas(15000), is_static_call=True, revert_on_failure=False)
    if not success or len(observation) != 128:
        return 0
    obs: uint256[4] = abi_decode(observation, uint256[4])
    cumulative: int256 = convert(convert(obs[1], bytes32), int256)
    if obs[0] >= 2**32 or cumulative < -2**55 or cumulative >= 2**55 or obs[2] >= 2**160 or obs[3] != 1:
        return 0
    now32: uint32 = convert(block.timestamp % 2**32, uint32)
    age: uint32 = unsafe_sub(now32, convert(obs[0], uint32))
    if age > config.params.maxObservationAgeSeconds:
        return 0
    history: Bytes[257] = b""
    secondsAgos: DynArray[uint32, 2] = [config.params.twapWindowSeconds, 0]
    success, history = raw_call(pool, abi_encode(secondsAgos, method_id=method_id("observe(uint32[])")), max_outsize=257, gas=self._callGas(120000), is_static_call=True, revert_on_failure=False)
    if not success or len(history) != 256:
        return 0
    values: uint256[8] = abi_decode(history, uint256[8])
    if values[0] != 64 or values[1] != 160 or values[2] != 2 or values[5] != 2 or values[6] >= 2**160 or values[7] >= 2**160:
        return 0
    past: int256 = convert(convert(values[3], bytes32), int256)
    current: int256 = convert(convert(values[4], bytes32), int256)
    if past < -2**55 or past >= 2**55 or current < -2**55 or current >= 2**55:
        return 0
    mean: int256 = 0
    success, mean = math.meanTick(convert(past, int56), convert(current, int56), config.params.twapWindowSeconds)
    if not success:
        return 0
    harmonic: uint256 = math.harmonicLiquidity(convert(values[6], uint160), convert(values[7], uint160), config.params.twapWindowSeconds)
    if harmonic == 0 or harmonic < convert(config.params.minHarmonicLiquidity, uint256):
        return 0
    return math.quoteAtTick(mean, 10**convert(config.assetDecimals, uint256), config.assetIsToken0)


@view
@internal
def _anchorPrice(age: uint256) -> uint256:
    success: bool = False
    response: Bytes[161] = b""
    success, response = raw_call(ETH_USD_FEED, method_id("latestRoundData()"), max_outsize=161, gas=self._callGas(30000), is_static_call=True, revert_on_failure=False)
    if not success or len(response) != 160:
        return 0
    words: uint256[5] = abi_decode(response, uint256[5])
    if words[0] == 0 or words[0] >= 2**80 or words[4] >= 2**80 or words[4] < words[0] or words[1] == 0 or words[1] >= 2**255:
        return 0
    if words[3] == 0 or words[3] > block.timestamp or block.timestamp - words[3] > age:
        return 0
    scale: uint256 = 10**(18 - convert(ANCHOR_DECIMALS, uint256))
    if words[1] > max_value(uint256) // scale:
        return 0
    return words[1] * scale


@view
@external
def hasPriceFeed(asset: address) -> bool:
    return self.configs[asset].params.pool != empty(address)


@view
@external
def hasPendingPriceFeedUpdate(asset: address) -> bool:
    # Pending remains visible during qualification, after TimeLock consumption.
    return self.pending[asset].actionId != 0


@view
@external
def getFeedConfig(asset: address) -> UniV3FeedConfig:
    return self.configs[asset]


@view
@external
def getPendingFeed(asset: address) -> PendingUniV3Feed:
    return self.pending[asset]


@view
@external
def getBoundAssetDecimals(asset: address) -> (bool, uint8):
    return self.decimalsBound[asset], self.boundDecimals[asset]


@external
def addPriceSnapshot(_asset: address) -> bool:
    return False


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


@view
@internal
def _govern():
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused


@pure
@internal
def _validParams(p: FeedParams) -> bool:
    return (
        p.twapWindowSeconds >= MIN_TWAP_WINDOW and p.twapWindowSeconds <= MAX_TWAP_WINDOW
        and p.minCurrentLiquidity > 0 and p.minHarmonicLiquidity > 0
        and p.maxObservationAgeSeconds > 0 and p.maxObservationAgeSeconds <= MAX_OBSERVATION_AGE
        and (p.quoteStaleTime == 0 or (p.quoteStaleTime >= MIN_LOCAL_STALE_TIME and p.quoteStaleTime <= MAX_EFFECTIVE_STALE_TIME))
    )


@view
@internal
def _metadata(asset: address, p: FeedParams) -> (bool, UniV3FeedConfig):
    config: UniV3FeedConfig = empty(UniV3FeedConfig)
    if not self._validParams(p) or not p.pool.is_contract:
        return False, config
    valid: bool = False
    value: uint256 = 0
    valid, value = self._scalar(asset, method_id("decimals()"), 30000)
    if not valid or value > 18:
        return False, config
    config.params = p
    config.assetDecimals = convert(value, uint8)
    valid, value = self._scalar(ETH_USD_FEED, method_id("decimals()"), 30000)
    if not valid or value != convert(ANCHOR_DECIMALS, uint256):
        return False, config
    valid, value = self._scalar(p.pool, method_id("factory()"), 30000)
    if not valid or value != convert(FACTORY, uint256):
        return False, config
    config.assetIsToken0 = convert(asset, uint256) < convert(WETH, uint256)
    token0: address = asset if config.assetIsToken0 else WETH
    token1: address = WETH if config.assetIsToken0 else asset
    valid, value = self._scalar(p.pool, method_id("token0()"), 30000)
    if not valid or value != convert(token0, uint256):
        return False, config
    valid, value = self._scalar(p.pool, method_id("token1()"), 30000)
    if not valid or value != convert(token1, uint256):
        return False, config
    valid, value = self._scalar(p.pool, method_id("fee()"), 30000)
    if not valid or value >= 2**24:
        return False, config
    config.fee = convert(value, uint24)
    valid, value = self._scalar(FACTORY, abi_encode(asset, WETH, config.fee, method_id=method_id("getPool(address,address,uint24)")), 30000)
    if not valid or value != convert(p.pool, uint256):
        return False, config
    return True, config


@external
def addNewPriceFeed(asset: address, params: FeedParams) -> bool:
    return self._propose(asset, params, 1)


@external
def updatePriceFeed(asset: address, params: FeedParams) -> bool:
    return self._propose(asset, params, 2)


@external
def disablePriceFeed(asset: address) -> bool:
    return self._propose(asset, empty(FeedParams), 3)


@internal
def _propose(asset: address, params: FeedParams, kind: uint256) -> bool:
    self._govern()
    assert asset not in [empty(address), ETH, WETH] # dev: invalid asset
    active: UniV3FeedConfig = self.configs[asset]
    if kind == 1:
        assert active.params.pool == empty(address) # dev: feed already exists
    else:
        assert active.params.pool != empty(address) # dev: no active feed
    assert self.pending[asset].actionId == 0 # dev: pending feed action
    if kind == 1:
        assert priceData.numAssets <= 50 # dev: too many assets
    candidate: UniV3FeedConfig = active
    if kind != 3:
        valid: bool = False
        valid, candidate = self._metadata(asset, params)
        assert valid # dev: invalid feed
        assert not self.decimalsBound[asset] or candidate.assetDecimals == self.boundDecimals[asset] # dev: asset decimals changed
        if kind == 2:
            assert keccak256(abi_encode(candidate)) != keccak256(abi_encode(active)) # dev: no change
        assert self._price(asset, candidate, 0, empty(address)) != 0 # dev: invalid feed
    aid: uint256 = timeLock._initiateAction()
    self.pending[asset] = PendingUniV3Feed(actionId=aid, kind=kind, config=candidate)
    action: timeLock.PendingAction = timeLock.pendingActions[aid]
    log UniV3FeedProposed(asset=asset, actionId=aid, kind=kind, confirmationBlock=action.confirmBlock, expirationBlock=action.expiration, pool=candidate.params.pool, twapWindowSeconds=candidate.params.twapWindowSeconds, minCurrentLiquidity=candidate.params.minCurrentLiquidity, minHarmonicLiquidity=candidate.params.minHarmonicLiquidity, maxObservationAgeSeconds=candidate.params.maxObservationAgeSeconds, quoteStaleTime=candidate.params.quoteStaleTime, assetIsToken0=candidate.assetIsToken0, assetDecimals=candidate.assetDecimals, fee=candidate.fee)
    return True


@external
def confirmNewPriceFeed(asset: address) -> bool:
    return self._confirm(asset, 1)


@external
def confirmPriceFeedUpdate(asset: address) -> bool:
    return self._confirm(asset, 2)


@external
def confirmDisablePriceFeed(asset: address) -> bool:
    return self._confirm(asset, 3)


@internal
def _confirm(asset: address, kind: uint256) -> bool:
    self._govern()
    proposal: PendingUniV3Feed = self.pending[asset]
    aid: uint256 = proposal.actionId
    assert aid != 0 # dev: no pending feed action
    assert proposal.kind == kind # dev: wrong feed operation
    if kind == 1:
        assert self.configs[asset].params.pool == empty(address) # dev: feed already exists
        assert priceData.numAssets <= 50 # dev: too many assets
    else:
        assert self.configs[asset].params.pool != empty(address) # dev: no active feed
    assert timeLock._canConfirmAction(aid) # dev: time lock not reached
    action: timeLock.PendingAction = timeLock.pendingActions[aid]
    candidate: UniV3FeedConfig = proposal.config
    desk: address = empty(address)
    if kind != 3:
        valid: bool = False
        live: UniV3FeedConfig = empty(UniV3FeedConfig)
        valid, live = self._metadata(asset, candidate.params)
        # Existing bindings precede the pending metadata comparison. A first ADD
        # has no binding, so metadata drift is reported by the following check.
        if valid:
            assert not self.decimalsBound[asset] or live.assetDecimals == self.boundDecimals[asset] # dev: asset decimals changed
        assert valid and keccak256(abi_encode(live)) == keccak256(abi_encode(candidate)) # dev: feed metadata changed
        status: uint256 = 0
        desk, status = self._deskScale(asset, candidate.assetDecimals)
        assert status != 0 # dev: invalid price desk
        assert status == 1 # dev: token scale mismatch
        assert self._price(asset, candidate, 0, empty(address)) != 0 # dev: invalid feed
    assert timeLock._confirmAction(aid) # dev: time lock not reached
    if kind == 3:
        self.configs[asset] = empty(UniV3FeedConfig)
        priceData._removePricedAsset(asset)
    else:
        # The static callback sees the complete candidate and first-ADD binding,
        # the still-readable proposal, and the consumed TimeLock action. All
        # provisional writes and logs roll back if qualification fails.
        self.configs[asset] = candidate
        if kind == 1 and not self.decimalsBound[asset]:
            self.decimalsBound[asset] = True
            self.boundDecimals[asset] = candidate.assetDecimals
        success: bool = False
        response: Bytes[65] = b""
        success, response = raw_call(desk, abi_encode(asset, method_id=method_id("qualifyCallerPriceSource(address)")), gas=self._callGas(400000), max_outsize=65, is_static_call=True, revert_on_failure=False)
        assert success and len(response) == 64 # dev: price source not executable
        result: uint256[2] = abi_decode(response, uint256[2])
        assert result[0] != 0 and result[1] == 1 # dev: price source not executable
        if kind == 1:
            priceData._addPricedAsset(asset)
    self.pending[asset] = empty(PendingUniV3Feed)
    log UniV3FeedConfirmed(asset=asset, actionId=aid, kind=kind, confirmationBlock=action.confirmBlock, expirationBlock=action.expiration, pool=candidate.params.pool, twapWindowSeconds=candidate.params.twapWindowSeconds, minCurrentLiquidity=candidate.params.minCurrentLiquidity, minHarmonicLiquidity=candidate.params.minHarmonicLiquidity, maxObservationAgeSeconds=candidate.params.maxObservationAgeSeconds, quoteStaleTime=candidate.params.quoteStaleTime, assetIsToken0=candidate.assetIsToken0, assetDecimals=candidate.assetDecimals, fee=candidate.fee)
    return True


@external
def cancelNewPendingPriceFeed(asset: address) -> bool:
    return self._cancel(asset, 1)


@external
def cancelPriceFeedUpdate(asset: address) -> bool:
    return self._cancel(asset, 2)


@external
def cancelDisablePriceFeed(asset: address) -> bool:
    return self._cancel(asset, 3)


@internal
def _cancel(asset: address, kind: uint256) -> bool:
    self._govern()
    proposal: PendingUniV3Feed = self.pending[asset]
    assert proposal.actionId != 0 # dev: no pending feed action
    assert proposal.kind == kind # dev: wrong feed operation
    # Existence, not confirmability: expired proposals can still be cancelled.
    assert timeLock._cancelAction(proposal.actionId) # dev: no pending feed action
    self.pending[asset] = empty(PendingUniV3Feed)
    log UniV3FeedCancelled(asset=asset, actionId=proposal.actionId, kind=kind)
    return True
