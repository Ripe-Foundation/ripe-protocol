# Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
# Ripe Foundation (C) 2025

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
from ethereum.ercs import IERC20Detailed

interface CurveMetaRegistry:
    def get_registry_handlers_from_pool(_pool: address) -> address[10]: view
    def get_underlying_coins(_pool: address) -> address[8]: view
    def get_n_underlying_coins(_pool: address) -> uint256: view 
    def get_base_registry(_addr: address) -> address: view
    def get_lp_token(_pool: address) -> address: view
    def is_registered(_pool: address) -> bool: view

interface CurvePool:
    def balances(_index: uint256) -> uint256: view
    def get_virtual_price() -> uint256: view
    def price_oracle() -> uint256: view
    def totalSupply() -> uint256: view
    def lp_price() -> uint256: view

interface PriceDesk:
    def getPrice(_asset: address, _shouldRaise: bool = False) -> uint256: view

interface CurvePoolNg:
    def price_oracle(_index: uint256) -> uint256: view

interface CurveAddressProvider:
    def get_address(_id: uint256) -> address: view

flag PoolType:
    STABLESWAP_NG
    TWO_CRYPTO_NG
    TRICRYPTO_NG
    TWO_CRYPTO
    METAPOOL
    CRYPTO

struct CurvePriceConfig:
    pool: address
    lpToken: address
    numUnderlying: uint256
    underlying: address[4]
    poolType: PoolType
    hasEcoToken: bool

struct PendingCurvePrice:
    actionId: uint256
    config: CurvePriceConfig

struct CurveRegistries:
    StableSwapNg: address
    TwoCryptoNg: address
    TricryptoNg: address
    TwoCrypto: address
    MetaPool: address

struct GreenRefPoolConfig:
    pool: address
    lpToken: address
    greenIndex: uint256
    altAsset: address
    altAssetDecimals: uint256
    maxNumSnapshots: uint256
    dangerTrigger: uint256
    staleBlocks: uint256
    stabilizerAdjustWeight: uint256
    stabilizerMaxPoolDebt: uint256

struct RefPoolSnapshot:
    greenBalance: uint256
    ratio: uint256
    update: uint256
    inDanger: bool

struct GreenRefPoolData:
    lastSnapshot: RefPoolSnapshot
    numBlocksInDanger: uint256
    nextIndex: uint256

struct CurrentGreenPoolStatus:
    weightedRatio: uint256
    dangerTrigger: uint256
    numBlocksInDanger: uint256

struct StabilizerConfig:
    pool: address
    lpToken: address
    greenBalance: uint256
    greenRatio: uint256
    greenIndex: uint256
    stabilizerAdjustWeight: uint256
    stabilizerMaxPoolDebt: uint256

event NewCurvePricePending:
    asset: indexed(address)
    pool: indexed(address)
    confirmationBlock: uint256
    actionId: uint256

event NewCurvePriceAdded:
    asset: indexed(address)
    pool: indexed(address)

event NewCurvePriceCancelled:
    asset: indexed(address)
    pool: indexed(address)

event CurvePriceConfigUpdatePending:
    asset: indexed(address)
    pool: indexed(address)
    prevPool: indexed(address)
    confirmationBlock: uint256
    actionId: uint256

event CurvePriceConfigUpdated:
    asset: indexed(address)
    pool: indexed(address)
    prevPool: indexed(address)

event CurvePriceConfigUpdateCancelled:
    asset: indexed(address)
    pool: indexed(address)
    prevPool: indexed(address)

event DisableCurvePricePending:
    asset: indexed(address)
    prevPool: indexed(address)
    confirmationBlock: uint256
    actionId: uint256

event CurvePriceDisabled:
    asset: indexed(address)
    prevPool: indexed(address)

event DisableCurvePriceCancelled:
    asset: indexed(address)
    prevPool: indexed(address)

event GreenRefPoolConfigPending:
    pool: indexed(address)
    maxNumSnapshots: uint256
    dangerTrigger: uint256
    staleBlocks: uint256
    stabilizerAdjustWeight: uint256
    stabilizerMaxPoolDebt: uint256
    confirmationBlock: uint256
    actionId: uint256

event GreenRefPoolConfigUpdated:
    pool: indexed(address)
    maxNumSnapshots: uint256
    dangerTrigger: uint256
    staleBlocks: uint256
    stabilizerAdjustWeight: uint256
    stabilizerMaxPoolDebt: uint256

event GreenRefPoolConfigUpdateCancelled:
    pool: indexed(address)
    maxNumSnapshots: uint256
    dangerTrigger: uint256
    staleBlocks: uint256
    stabilizerAdjustWeight: uint256
    stabilizerMaxPoolDebt: uint256

event GreenRefPoolSnapshotAdded:
    pool: indexed(address)
    greenBalance: uint256
    greenRatio: uint256
    inDanger: bool

# config
curveConfig: public(HashMap[address, CurvePriceConfig]) # asset -> config
pendingUpdates: public(HashMap[address, PendingCurvePrice]) # asset -> config

# green reference pool
greenRefPoolConfig: public(GreenRefPoolConfig)
greenRefPoolData: public(GreenRefPoolData)
snapShots: public(HashMap[uint256, RefPoolSnapshot]) # index -> snapshot
pendingGreenRefPoolConfig: public(HashMap[uint256, GreenRefPoolConfig]) # actionId -> config

# curve
CURVE_META_REGISTRY: public(immutable(address))
CURVE_REGISTRIES: public(immutable(CurveRegistries))

# curve address provider ids
METAPOOL_FACTORY_ID: constant(uint256) = 3
TWO_CRYPTO_FACTORY_ID: constant(uint256) = 6
META_REGISTRY_ID: constant(uint256) = 7
TRICRYPTO_NG_FACTORY_ID: constant(uint256) = 11
STABLESWAP_NG_FACTORY_ID: constant(uint256) = 12
TWO_CRYPTO_NG_FACTORY_ID: constant(uint256) = 13

MAX_POOLS: constant(uint256) = 50
EIGHTEEN_DECIMALS: constant(uint256) = 10 ** 18
HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%


@deploy
def __init__(
    _ripeHq: address,
    _curveAddressProvider: address,
    _minPriceChangeTimeLock: uint256,
    _maxPriceChangeTimeLock: uint256,
):
    gov.__init__(_ripeHq, empty(address), 0, 0, 0)
    addys.__init__(_ripeHq)
    priceData.__init__(False)
    timeLock.__init__(_minPriceChangeTimeLock, _maxPriceChangeTimeLock, 0, _maxPriceChangeTimeLock)

    # set curve address provider
    if _curveAddressProvider != empty(address):
        CURVE_META_REGISTRY = staticcall CurveAddressProvider(_curveAddressProvider).get_address(META_REGISTRY_ID)
        CURVE_REGISTRIES = CurveRegistries(
            StableSwapNg= staticcall CurveAddressProvider(_curveAddressProvider).get_address(STABLESWAP_NG_FACTORY_ID),
            TwoCryptoNg= staticcall CurveAddressProvider(_curveAddressProvider).get_address(TWO_CRYPTO_NG_FACTORY_ID),
            TricryptoNg= staticcall CurveAddressProvider(_curveAddressProvider).get_address(TRICRYPTO_NG_FACTORY_ID),
            TwoCrypto= staticcall CurveAddressProvider(_curveAddressProvider).get_address(TWO_CRYPTO_FACTORY_ID),
            MetaPool= staticcall CurveAddressProvider(_curveAddressProvider).get_address(METAPOOL_FACTORY_ID),
        )


###############
# Core Prices #
###############


# get price


@view
@external
def getPrice(_asset: address, _staleTime: uint256 = 0, _priceDesk: address = empty(address)) -> uint256:
    config: CurvePriceConfig = self.curveConfig[_asset]
    if config.pool == empty(address):
        return 0
    return self._getCurvePrice(_asset, config, _priceDesk)


@view
@external
def getPriceAndHasFeed(_asset: address, _staleTime: uint256 = 0, _priceDesk: address = empty(address)) -> (uint256, bool):
    config: CurvePriceConfig = self.curveConfig[_asset]
    if config.pool == empty(address):
        return 0, False
    return self._getCurvePrice(_asset, config, _priceDesk), True


# utilities


@view
@external
def hasPriceFeed(_asset: address) -> bool:
    return self.curveConfig[_asset].pool != empty(address)


@view
@external
def hasPendingPriceFeedUpdate(_asset: address) -> bool:
    return timeLock._hasPendingAction(self.pendingUpdates[_asset].actionId)


@external 
def addPriceSnapshot(_asset: address) -> bool:
    return False


###############
# Curve Price #
###############


@view
@internal
def _getCurvePrice(_asset: address, _config: CurvePriceConfig, _priceDesk: address) -> uint256:
    price: uint256 = 0

    priceDesk: address = _priceDesk
    if _priceDesk == empty(address):
        priceDesk = addys._getPriceDeskAddr()

    # lp tokens
    if _asset == _config.lpToken:

        # stable lp tokens
        if _config.poolType == PoolType.STABLESWAP_NG or _config.poolType == PoolType.METAPOOL:
            price = self._getStableLpPrice(_config.pool, _config.underlying, priceDesk)

        # crypto lp tokens
        else:
            price = self._getCryptoLpPrice(_config.pool, _config.underlying[0], priceDesk)

    # single asset (only supporting pools with 2 assets)
    elif _config.numUnderlying == 2:
        price = self._getSingleTokenPrice(_config.pool, _asset, [_config.underlying[0], _config.underlying[1]], _config.poolType, priceDesk)

    return price


# stable lp tokens


@view 
@internal 
def _getStableLpPrice(_pool: address, _coins: address[4], _priceDesk: address) -> uint256: 

    # REQUIREMENTS:
    # all assets must be stable-ish to each other
    # each underlying asset must have price feed (Price Desk)
    # Note: see this article: https://news.curve.fi/chainlink-oracles-and-curve-pools/

    lowestPrice: uint256 = max_value(uint256)
    for c: address in _coins:
        if c == empty(address):
            break

        underlyingPrice: uint256 = staticcall PriceDesk(_priceDesk).getPrice(c, False)
        if underlyingPrice < lowestPrice:
            lowestPrice = underlyingPrice 

    # if no price feed, return 0
    if lowestPrice == 0 or lowestPrice == max_value(uint256):
        return 0

    # curve virtual price
    virtualPrice: uint256 = staticcall CurvePool(_pool).get_virtual_price()
    if virtualPrice == 0:
        return 0
    
    return lowestPrice * virtualPrice // EIGHTEEN_DECIMALS


@view 
@external 
def getStableLpPrice(_pool: address, _coins: address[4]) -> uint256: 
    # mostly for testing
    return self._getStableLpPrice(_pool, _coins, addys._getPriceDeskAddr())


# crypto lp token price


@view
@internal 
def _getCryptoLpPrice(_pool: address, _firstAsset: address, _priceDesk: address) -> uint256:

    # REQUIREMENTS:
    # pool must have `lp_price()`
    # 0 index asset must have price feed (Price Desk)

    lpPrice: uint256 = staticcall CurvePool(_pool).lp_price()
    if lpPrice == 0:
        return 0

    assetPrice: uint256 = staticcall PriceDesk(_priceDesk).getPrice(_firstAsset)
    if assetPrice == 0:
        return 0

    return assetPrice * lpPrice // EIGHTEEN_DECIMALS


@view
@external 
def getCryptoLpPrice(_pool: address, _firstAsset: address) -> uint256:
    # mostly for testing
    return self._getCryptoLpPrice(_pool, _firstAsset, addys._getPriceDeskAddr())


# single asset price


@view
@internal 
def _getSingleTokenPrice(
    _pool: address,
    _targetAsset: address,
    _coins: address[2],
    _poolType: PoolType,
    _priceDesk: address,
) -> uint256:
    price: uint256 = 0

    # REQUIREMENTS:
    # pool must have `price_oracle()`
    # can only have 2 assets in pool
    # alt asset must have price feed (Price Desk)

    # curve price oracle
    priceOracle: uint256 = 0
    if _poolType == PoolType.STABLESWAP_NG:
        priceOracle = staticcall CurvePoolNg(_pool).price_oracle(0)
    else:
        priceOracle = staticcall CurvePool(_pool).price_oracle()

    if priceOracle == 0:
        return 0

    # in relation to alt asset
    altPrice: uint256 = 0
    if _targetAsset == _coins[0]:
        altPrice = staticcall PriceDesk(_priceDesk).getPrice(_coins[1], False)
        price = altPrice * EIGHTEEN_DECIMALS // priceOracle
    else:
        altPrice = staticcall PriceDesk(_priceDesk).getPrice(_coins[0], False)
        price = altPrice * priceOracle // EIGHTEEN_DECIMALS

    return price


@view
@external
def getSingleTokenPrice(_pool: address, _targetAsset: address, _coins: address[2], _poolType: PoolType = empty(PoolType)) -> uint256:
    # mostly for testing
    return self._getSingleTokenPrice(_pool, _targetAsset, _coins, _poolType, addys._getPriceDeskAddr())


################
# Add New Feed #
################


# initiate new feed


@external
def addNewPriceFeed(_asset: address, _pool: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validation
    config: CurvePriceConfig = self._getCurvePoolConfig(_pool)
    assert self._isValidNewFeed(_asset, config) # dev: invalid pool

    # set to pending state
    aid: uint256 = timeLock._initiateAction()
    self.pendingUpdates[_asset] = PendingCurvePrice(
        actionId=aid,
        config=config,
    )

    log NewCurvePricePending(asset=_asset, pool=_pool, confirmationBlock=timeLock._getActionConfirmationBlock(aid), actionId=aid)
    return True


# confirm new feed


@external
def confirmNewPriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validate again
    d: PendingCurvePrice = self.pendingUpdates[_asset]
    assert d.config.pool != empty(address) # dev: no pending new feed
    if not self._isValidNewFeed(_asset, d.config):
        self._cancelNewPendingPriceFeed(_asset, d.actionId)
        return False

    # check time lock
    assert timeLock._confirmAction(d.actionId) # dev: time lock not reached

    # save new feed config
    self.curveConfig[_asset] = d.config
    self.pendingUpdates[_asset] = empty(PendingCurvePrice)
    priceData._addPricedAsset(_asset)

    log NewCurvePriceAdded(asset=_asset, pool=d.config.pool)
    return True


# cancel new feed


@external
def cancelNewPendingPriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    d: PendingCurvePrice = self.pendingUpdates[_asset]
    self._cancelNewPendingPriceFeed(_asset, d.actionId)
    log NewCurvePriceCancelled(asset=_asset, pool=d.config.pool)
    return True


@internal
def _cancelNewPendingPriceFeed(_asset: address, _aid: uint256):
    assert timeLock._cancelAction(_aid) # dev: cannot cancel action
    self.pendingUpdates[_asset] = empty(PendingCurvePrice)


# validation


@view
@external
def isValidNewFeed(_asset: address, _pool: address) -> bool:
    config: CurvePriceConfig = self._getCurvePoolConfig(_pool)
    return self._isValidNewFeed(_asset, config)


@view
@internal
def _isValidNewFeed(_asset: address, _config: CurvePriceConfig) -> bool:
    if priceData.indexOfAsset[_asset] != 0 or self.curveConfig[_asset].pool != empty(address): # use the `updatePriceFeed` function instead
        return False
    return self._isValidFeedConfig(_asset, _config)


###############
# Update Feed #
###############


# initiate update feed


@external
def updatePriceFeed(_asset: address, _pool: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validation
    prevPool: address = self.curveConfig[_asset].pool
    config: CurvePriceConfig = self._getCurvePoolConfig(_pool)
    assert self._isValidUpdateFeed(_asset, config, prevPool) # dev: invalid feed

    # set to pending state
    aid: uint256 = timeLock._initiateAction()
    self.pendingUpdates[_asset] = PendingCurvePrice(
        actionId=aid,
        config=config,
    )
    log CurvePriceConfigUpdatePending(asset=_asset, pool=_pool, prevPool=prevPool, confirmationBlock=timeLock._getActionConfirmationBlock(aid), actionId=aid)
    return True


# confirm update feed


@external
def confirmPriceFeedUpdate(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validate again
    d: PendingCurvePrice = self.pendingUpdates[_asset]
    assert d.config.pool != empty(address) # dev: no pending update feed
    prevPool: address = self.curveConfig[_asset].pool
    if not self._isValidUpdateFeed(_asset, d.config, prevPool):
        self._cancelPriceFeedUpdate(_asset, d.actionId)
        return False

    # check time lock
    assert timeLock._confirmAction(d.actionId) # dev: time lock not reached

    # save new feed config
    self.curveConfig[_asset] = d.config
    self.pendingUpdates[_asset] = empty(PendingCurvePrice)

    log CurvePriceConfigUpdated(asset=_asset, pool=d.config.pool, prevPool=prevPool)
    return True


# cancel update feed


@external
def cancelPriceFeedUpdate(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    d: PendingCurvePrice = self.pendingUpdates[_asset]
    self._cancelPriceFeedUpdate(_asset, d.actionId)
    log CurvePriceConfigUpdateCancelled(asset=_asset, pool=d.config.pool, prevPool=self.curveConfig[_asset].pool)
    return True


@internal
def _cancelPriceFeedUpdate(_asset: address, _aid: uint256):
    assert timeLock._cancelAction(_aid) # dev: cannot cancel action
    self.pendingUpdates[_asset] = empty(PendingCurvePrice)


# validation


@view
@external
def isValidUpdateFeed(_asset: address, _newPool: address) -> bool:
    config: CurvePriceConfig = self._getCurvePoolConfig(_newPool)
    return self._isValidUpdateFeed(_asset, config, self.curveConfig[_asset].pool)


@view
@internal
def _isValidUpdateFeed(_asset: address, _config: CurvePriceConfig, _prevPool: address) -> bool:
    if _config.pool == _prevPool:
        return False
    if priceData.indexOfAsset[_asset] == 0 or _prevPool == empty(address): # use the `addNewPriceFeed` function instead
        return False
    return self._isValidFeedConfig(_asset, _config)


@view
@internal
def _isValidFeedConfig(_asset: address, _config: CurvePriceConfig) -> bool:
    if empty(address) in [_asset, _config.pool, _config.lpToken]:
        return False

    if _asset not in _config.underlying and _asset != _config.lpToken:
        return False

    # for initial ripe/green lp deployment, need to skip checking price -- when totalSupply is zero, the `get_virtual_price()` will fail
    if _config.hasEcoToken and _asset == _config.pool and staticcall CurvePool(_config.pool).totalSupply() == 0:
        return True

    return self._getCurvePrice(_asset, _config, empty(address)) != 0


################
# Disable Feed #
################


# initiate disable feed


@external
def disablePriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validation
    prevPool: address = self.curveConfig[_asset].pool
    assert self._isValidDisablePriceFeed(_asset, prevPool) # dev: invalid asset

    # set to pending state
    aid: uint256 = timeLock._initiateAction()
    self.pendingUpdates[_asset] = PendingCurvePrice(
        actionId=aid,
        config=empty(CurvePriceConfig),
    )

    log DisableCurvePricePending(asset=_asset, prevPool=prevPool, confirmationBlock=timeLock._getActionConfirmationBlock(aid), actionId=aid)
    return True


# confirm disable feed


@external
def confirmDisablePriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validate again
    prevPool: address = self.curveConfig[_asset].pool
    d: PendingCurvePrice = self.pendingUpdates[_asset]
    assert d.actionId != 0 # dev: no pending disable feed
    if not self._isValidDisablePriceFeed(_asset, prevPool):
        self._cancelDisablePriceFeed(_asset, d.actionId)
        return False

    # check time lock
    assert timeLock._confirmAction(d.actionId) # dev: time lock not reached

    # disable feed
    self.curveConfig[_asset] = empty(CurvePriceConfig)
    self.pendingUpdates[_asset] = empty(PendingCurvePrice)
    priceData._removePricedAsset(_asset)
    
    log CurvePriceDisabled(asset=_asset, prevPool=prevPool)
    return True


# cancel disable feed


@external
def cancelDisablePriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    self._cancelDisablePriceFeed(_asset, self.pendingUpdates[_asset].actionId)
    log DisableCurvePriceCancelled(asset=_asset, prevPool=self.curveConfig[_asset].pool)
    return True


@internal
def _cancelDisablePriceFeed(_asset: address, _aid: uint256):
    assert timeLock._cancelAction(_aid) # dev: cannot cancel action
    self.pendingUpdates[_asset] = empty(PendingCurvePrice)


# validation


@view
@external
def isValidDisablePriceFeed(_asset: address) -> bool:
    return self._isValidDisablePriceFeed(_asset, self.curveConfig[_asset].pool)


@view
@internal
def _isValidDisablePriceFeed(_asset: address, _prevPool: address) -> bool:
    if priceData.indexOfAsset[_asset] == 0:
        return False
    return _prevPool != empty(address)


##############
# Curve Data #
##############


@view
@external
def getCurvePoolConfig(_pool: address) -> CurvePriceConfig:
    return self._getCurvePoolConfig(_pool)


@view
@internal
def _getCurvePoolConfig(_pool: address) -> CurvePriceConfig:
    mr: address = CURVE_META_REGISTRY
    if not staticcall CurveMetaRegistry(mr).is_registered(_pool):
        return empty(CurvePriceConfig)

    lpToken: address = staticcall CurveMetaRegistry(mr).get_lp_token(_pool)
    underlying: address[8] = staticcall CurveMetaRegistry(mr).get_underlying_coins(_pool)

    # check if ripe ecosystem token
    hasEcoToken: bool = False
    for token: address in [addys._getGreenToken(), addys._getSavingsGreen(), addys._getRipeToken()]:
        if token in underlying:
            hasEcoToken = True
            break

    return CurvePriceConfig(
        pool = _pool,
        lpToken = lpToken,
        numUnderlying = staticcall CurveMetaRegistry(mr).get_n_underlying_coins(_pool),
        underlying = [underlying[0], underlying[1], underlying[2], underlying[3]],
        poolType = self._getPoolType(_pool, mr),
        hasEcoToken = hasEcoToken,
    )


@view
@internal
def _getPoolType(_pool: address, _mr: address) -> PoolType:
    # check what type of pool this is based on where it's registered on Curve
    registryHandlers: address[10] = staticcall CurveMetaRegistry(_mr).get_registry_handlers_from_pool(_pool)
    baseRegistry: address = staticcall CurveMetaRegistry(_mr).get_base_registry(registryHandlers[0])

    curveRegistries: CurveRegistries = CURVE_REGISTRIES
    poolType: PoolType = empty(PoolType)
    if baseRegistry == curveRegistries.StableSwapNg:
        poolType = PoolType.STABLESWAP_NG
    elif baseRegistry == curveRegistries.TwoCryptoNg:
        poolType = PoolType.TWO_CRYPTO_NG
    elif baseRegistry == curveRegistries.TricryptoNg:
        poolType = PoolType.TRICRYPTO_NG
    elif baseRegistry == curveRegistries.TwoCrypto:
        poolType = PoolType.TWO_CRYPTO
    elif baseRegistry == curveRegistries.MetaPool:
        poolType = PoolType.METAPOOL
    else:
        poolType = PoolType.CRYPTO
    return poolType


#########################
# Green Ref Pool Config #
#########################


@external
def setGreenRefPoolConfig(
    _pool: address,
    _maxNumSnapshots: uint256,
    _dangerTrigger: uint256,
    _staleBlocks: uint256,
    _stabilizerAdjustWeight: uint256,
    _stabilizerMaxPoolDebt: uint256,
) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # pool data
    poolConfig: CurvePriceConfig = self._getCurvePoolConfig(_pool)
    greenToken: address = addys._getGreenToken()
    greenIndex: uint256 = 0
    if greenToken == poolConfig.underlying[1]:
        greenIndex = 1
    altAsset: address = poolConfig.underlying[1 - greenIndex]

    refConfig: GreenRefPoolConfig = GreenRefPoolConfig(
        pool=_pool,
        lpToken=poolConfig.lpToken,
        greenIndex=greenIndex,
        altAsset=altAsset,
        altAssetDecimals=convert(staticcall IERC20Detailed(altAsset).decimals(), uint256),
        maxNumSnapshots=_maxNumSnapshots,
        dangerTrigger=_dangerTrigger,
        staleBlocks=_staleBlocks,
        stabilizerAdjustWeight=_stabilizerAdjustWeight,
        stabilizerMaxPoolDebt=_stabilizerMaxPoolDebt,
    )
    assert self._isValidGreenRefPoolConfig(poolConfig, refConfig, _maxNumSnapshots, _dangerTrigger, _staleBlocks, _stabilizerAdjustWeight, _stabilizerMaxPoolDebt, greenToken) # dev: invalid ref pool config

    # set to pending state
    aid: uint256 = timeLock._initiateAction()
    self.pendingGreenRefPoolConfig[aid] = refConfig
    log GreenRefPoolConfigPending(pool=_pool, maxNumSnapshots=_maxNumSnapshots, dangerTrigger=_dangerTrigger, staleBlocks=_staleBlocks, stabilizerAdjustWeight=_stabilizerAdjustWeight, stabilizerMaxPoolDebt=_stabilizerMaxPoolDebt, confirmationBlock=timeLock._getActionConfirmationBlock(aid), actionId=aid)
    return aid


# confirm green ref pool config


@external
def confirmGreenRefPoolConfig(_aid: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validate again
    d: GreenRefPoolConfig = self.pendingGreenRefPoolConfig[_aid]
    assert d.pool != empty(address) # dev: no pending update

    # check time lock
    assert timeLock._confirmAction(_aid) # dev: time lock not reached

    # save new ref pool config
    self.greenRefPoolConfig = d
    self.pendingGreenRefPoolConfig[_aid] = empty(GreenRefPoolConfig)
    log GreenRefPoolConfigUpdated(pool=d.pool, maxNumSnapshots=d.maxNumSnapshots, dangerTrigger=d.dangerTrigger, staleBlocks=d.staleBlocks, stabilizerAdjustWeight=d.stabilizerAdjustWeight, stabilizerMaxPoolDebt=d.stabilizerMaxPoolDebt)

    # add snapshot
    self._addGreenRefPoolSnapshot()
    return True


# cancel update feed


@external
def cancelGreenRefPoolConfig(_aid: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    d: GreenRefPoolConfig = self.pendingGreenRefPoolConfig[_aid]
    assert d.pool != empty(address) # dev: no pending update
    
    assert timeLock._cancelAction(_aid) # dev: cannot cancel action
    self.pendingGreenRefPoolConfig[_aid] = empty(GreenRefPoolConfig)

    log GreenRefPoolConfigUpdateCancelled(pool=d.pool, maxNumSnapshots=d.maxNumSnapshots, dangerTrigger=d.dangerTrigger, staleBlocks=d.staleBlocks, stabilizerAdjustWeight=d.stabilizerAdjustWeight, stabilizerMaxPoolDebt=d.stabilizerMaxPoolDebt)
    return True


# validation


@view
@internal
def _isValidGreenRefPoolConfig(
    _poolConfig: CurvePriceConfig,
    _refConfig: GreenRefPoolConfig,
    _maxNumSnapshots: uint256,
    _dangerTrigger: uint256,
    _staleBlocks: uint256,
    _stabilizerAdjustWeight: uint256,
    _stabilizerMaxPoolDebt: uint256,
    _greenToken: address,
) -> bool:
    if _greenToken not in _poolConfig.underlying:
        return False

    if _poolConfig.numUnderlying != 2: # only 2 underlying tokens
        return False

    if _maxNumSnapshots == 0 or _maxNumSnapshots > 100: # 100 max
        return False

    if _dangerTrigger < 50_00 or _dangerTrigger >= HUNDRED_PERCENT: # 50% - 99.99%
        return False

    if _stabilizerAdjustWeight == 0 or _stabilizerAdjustWeight > HUNDRED_PERCENT:
        return False

    if _stabilizerMaxPoolDebt == 0 or _stabilizerMaxPoolDebt > 1_000_000 * EIGHTEEN_DECIMALS: # 1 million
        return False

    # make sure this curve integration works
    greenBalance: uint256 = 0
    greenRatio: uint256 = 0
    greenBalance, greenRatio = self._getCurvePoolData(_refConfig.pool, _refConfig.greenIndex, _refConfig.altAssetDecimals)
    if greenRatio == 0:
        return False

    return True


########################
# Green Ref Pool Utils #
########################


# get ref pool data


@view
@external
def getCurrentGreenPoolStatus() -> CurrentGreenPoolStatus:
    config: GreenRefPoolConfig = self.greenRefPoolConfig
    if config.pool == empty(address) or config.maxNumSnapshots == 0:
        return empty(CurrentGreenPoolStatus)

    data: GreenRefPoolData = self.greenRefPoolData

    # calculate weighted ratio using all valid snapshots
    numerator: uint256 = 0
    denominator: uint256 = 0
    for i: uint256 in range(config.maxNumSnapshots, bound=max_value(uint256)):

        snapShot: RefPoolSnapshot = self.snapShots[i]
        if snapShot.greenBalance == 0 or snapShot.ratio == 0 or snapShot.update == 0:
            continue

        # too stale, skip
        if config.staleBlocks != 0 and block.number > snapShot.update + config.staleBlocks:
            continue

        numerator += (snapShot.greenBalance * snapShot.ratio)
        denominator += snapShot.greenBalance

    # weighted ratio
    weightedRatio: uint256 = 0
    if numerator != 0:
        weightedRatio = numerator // denominator
    else:
        weightedRatio = data.lastSnapshot.ratio

    return CurrentGreenPoolStatus(
        weightedRatio=weightedRatio,
        dangerTrigger=config.dangerTrigger,
        numBlocksInDanger=data.numBlocksInDanger,
    )


# add snapshot


@external 
def addGreenRefPoolSnapshot() -> bool:
    assert addys._isValidRipeAddr(msg.sender) # dev: no perms
    if priceData.isPaused:
        return False # fail gracefully
    return self._addGreenRefPoolSnapshot()


@internal 
def _addGreenRefPoolSnapshot() -> bool:
    data: GreenRefPoolData = self.greenRefPoolData
    if data.lastSnapshot.update == block.number:
        return False

    # balance data
    config: GreenRefPoolConfig = self.greenRefPoolConfig
    if config.pool == empty(address):
        return False

    # curve pool data
    greenBalance: uint256 = 0
    greenRatio: uint256 = 0
    greenBalance, greenRatio = self._getCurvePoolData(config.pool, config.greenIndex, config.altAssetDecimals)
    if greenBalance == 0 or greenRatio == 0:
        return False

    inDanger: bool = greenRatio >= config.dangerTrigger
    
    # update danger data (using OLD snapshot before overwriting)
    if not inDanger:
        data.numBlocksInDanger = 0
    elif data.lastSnapshot.inDanger and data.lastSnapshot.update != 0:
        elapsedBlocks: uint256 = block.number - data.lastSnapshot.update
        data.numBlocksInDanger += elapsedBlocks

    # create and store new snapshot
    newSnapshot: RefPoolSnapshot = RefPoolSnapshot(
        greenBalance=greenBalance,
        ratio=greenRatio,
        update=block.number,
        inDanger=inDanger,
    )
    data.lastSnapshot = newSnapshot
    self.snapShots[data.nextIndex] = newSnapshot

    # update index
    data.nextIndex += 1
    if data.nextIndex >= config.maxNumSnapshots:
        data.nextIndex = 0

    # save data
    self.greenRefPoolData = data

    log GreenRefPoolSnapshotAdded(pool=config.pool, greenBalance=greenBalance, greenRatio=greenRatio, inDanger=inDanger)
    return True


# curve pool balance


@view
@external 
def getCurvePoolData() -> (uint256, uint256):
    config: GreenRefPoolConfig = self.greenRefPoolConfig
    return self._getCurvePoolData(config.pool, config.greenIndex, config.altAssetDecimals)


@view
@internal 
def _getCurvePoolData(
    _pool: address,
    _greenIndex: uint256,
    _altAssetDecimals: uint256,
) -> (uint256, uint256):
    normalize: uint256 = 10 ** (18 - _altAssetDecimals)

    # get balances
    greenBalance: uint256 = staticcall CurvePool(_pool).balances(_greenIndex)
    altAssetBalance: uint256 = staticcall CurvePool(_pool).balances(1 - _greenIndex) * normalize

    totalSupply: uint256 = greenBalance + altAssetBalance
    ratio: uint256 = 50_00 # 50%
    if totalSupply != 0:
        ratio = greenBalance * HUNDRED_PERCENT // totalSupply

    return greenBalance, ratio


# stabilizer data / config


@view
@external
def getGreenStabilizerConfig() -> StabilizerConfig:
    config: GreenRefPoolConfig = self.greenRefPoolConfig
    if config.pool == empty(address):
        return empty(StabilizerConfig)

    # green pool data
    greenBalance: uint256 = 0
    greenRatio: uint256 = 0
    greenBalance, greenRatio = self._getCurvePoolData(config.pool, config.greenIndex, config.altAssetDecimals)

    return StabilizerConfig(
        pool=config.pool,
        lpToken=config.lpToken,
        greenBalance=greenBalance,
        greenRatio=greenRatio,
        greenIndex=config.greenIndex,
        stabilizerAdjustWeight=config.stabilizerAdjustWeight,
        stabilizerMaxPoolDebt=config.stabilizerMaxPoolDebt,
    )
