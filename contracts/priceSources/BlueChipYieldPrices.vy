# @version 0.4.1

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
from ethereum.ercs import IERC4626
from ethereum.ercs import IERC20

interface EulerRegistry:
    def isValidDeployment(_vault: address) -> bool: view
    def isProxy(_vault: address) -> bool: view

interface AaveRegistry:
    def getAllATokens() -> DynArray[TokenData, MAX_MARKETS]: view
    def getPoolDataProvider() -> address: view

interface Moonwell:
    def exchangeRateStored() -> uint256: view
    def underlying() -> address: view

interface PriceDesk:
    def getPrice(_asset: address, _shouldRaise: bool = False) -> uint256: view

interface FluidRegistry:
    def getAllFTokens() -> DynArray[address, MAX_MARKETS]: view

interface MoonwellRegistry:
    def getAllMarkets() -> DynArray[address, MAX_MARKETS]: view

interface CompoundV3Registry:
    def factory(_cometAsset: address) -> address: view

interface MorphoRegistry:
    def isMetaMorpho(_vault: address) -> bool: view

interface AaveToken:
    def UNDERLYING_ASSET_ADDRESS() -> address: view

interface CompoundV3:
    def baseToken() -> address: view

flag Protocol:
    MORPHO
    EULER
    MOONWELL
    SKY
    FLUID
    AAVE_V3
    COMPOUND_V3

struct PriceConfig:
    protocol: Protocol
    underlyingAsset: address
    underlyingDecimals: uint256
    vaultTokenDecimals: uint256
    minSnapshotDelay: uint256
    maxNumSnapshots: uint256
    maxUpsideDeviation: uint256
    staleTime: uint256
    lastSnapshot: PriceSnapshot
    nextIndex: uint256

struct PriceSnapshot:
    totalSupply: uint256
    pricePerShare: uint256
    lastUpdate: uint256

struct PendingPriceConfig:
    actionId: uint256
    config: PriceConfig

struct TokenData:
    symbol: String[32]
    tokenAddress: address

event NewPriceConfigPending:
    asset: indexed(address)
    protocol: Protocol
    underlyingAsset: indexed(address)
    minSnapshotDelay: uint256
    maxNumSnapshots: uint256
    maxUpsideDeviation: uint256
    staleTime: uint256
    confirmationBlock: uint256
    actionId: uint256

event NewPriceConfigAdded:
    asset: indexed(address)
    protocol: Protocol
    underlyingAsset: indexed(address)
    minSnapshotDelay: uint256
    maxNumSnapshots: uint256
    maxUpsideDeviation: uint256
    staleTime: uint256

event NewPriceConfigCancelled:
    asset: indexed(address)
    protocol: Protocol
    underlyingAsset: indexed(address)

event PriceConfigUpdatePending:
    asset: indexed(address)
    protocol: Protocol
    underlyingAsset: indexed(address)
    minSnapshotDelay: uint256
    maxNumSnapshots: uint256
    maxUpsideDeviation: uint256
    staleTime: uint256
    confirmationBlock: uint256
    actionId: uint256

event PriceConfigUpdated:
    asset: indexed(address)
    protocol: Protocol
    underlyingAsset: indexed(address)
    minSnapshotDelay: uint256
    maxNumSnapshots: uint256
    maxUpsideDeviation: uint256
    staleTime: uint256

event PriceConfigUpdateCancelled:
    asset: indexed(address)
    protocol: Protocol
    underlyingAsset: indexed(address)

event DisablePriceConfigPending:
    asset: indexed(address)
    protocol: Protocol
    underlyingAsset: indexed(address)
    confirmationBlock: uint256
    actionId: uint256

event DisablePriceConfigConfirmed:
    asset: indexed(address)
    protocol: Protocol
    underlyingAsset: indexed(address)

event DisablePriceConfigCancelled:
    asset: indexed(address)
    protocol: Protocol
    underlyingAsset: indexed(address)

event PricePerShareSnapshotAdded:
    asset: indexed(address)
    protocol: Protocol
    underlyingAsset: indexed(address)
    totalSupply: uint256
    pricePerShare: uint256

# data 
priceConfigs: public(HashMap[address, PriceConfig]) # asset -> config
snapShots: public(HashMap[address, HashMap[uint256, PriceSnapshot]]) # asset -> index -> snapshot
pendingPriceConfigs: public(HashMap[address, PendingPriceConfig]) # asset -> pending config

HUNDRED_PERCENT: constant(uint256) = 100_00 # 100%
MAX_MARKETS: constant(uint256) = 50

# registries
MORPHO_ADDRS: public(immutable(address[2]))
EULER_ADDRS: public(immutable(address[2]))
FLUID_ADDR: public(immutable(address))
COMPOUND_V3_ADDR: public(immutable(address))
MOONWELL_ADDR: public(immutable(address))
AAVE_V3_ADDR: public(immutable(address))


@deploy
def __init__(
    _ripeHq: address,
    _minPriceChangeTimeLock: uint256,
    _maxPriceChangeTimeLock: uint256,
    _morphoAddrs: address[2],
    _eulerAddrs: address[2],
    _fluidAddr: address,
    _compoundV3Addr: address,
    _moonwellAddr: address,
    _aaveV3Addr: address,
):
    gov.__init__(_ripeHq, empty(address), 0, 0, 0)
    addys.__init__(_ripeHq)
    priceData.__init__(False, False)
    timeLock.__init__(_minPriceChangeTimeLock, _maxPriceChangeTimeLock, 0, _maxPriceChangeTimeLock)

    # factories / registries
    MORPHO_ADDRS = _morphoAddrs
    EULER_ADDRS = _eulerAddrs
    FLUID_ADDR = _fluidAddr
    COMPOUND_V3_ADDR = _compoundV3Addr
    MOONWELL_ADDR = _moonwellAddr
    AAVE_V3_ADDR = _aaveV3Addr


###############
# Core Prices #
###############


# get price


@view
@external
def getPrice(_asset: address, _staleTime: uint256 = 0, _priceDesk: address = empty(address)) -> uint256:
    config: PriceConfig = self.priceConfigs[_asset]
    if config.underlyingAsset == empty(address):
        return 0
    return self._getPrice(_asset, config, _priceDesk)


@view
@external
def getPriceAndHasFeed(_asset: address, _staleTime: uint256 = 0, _priceDesk: address = empty(address)) -> (uint256, bool):
    config: PriceConfig = self.priceConfigs[_asset]
    if config.underlyingAsset == empty(address):
        return 0, False
    return self._getPrice(_asset, config, _priceDesk), True


@view
@internal
def _getPrice(
    _asset: address,
    _config: PriceConfig,
    _priceDesk: address,
) -> uint256:
    # NOTE: not using Mission Control `_staleTime` in this contract.
    # These vault tokens are different/unique. Each config has its own stale time.

    priceDesk: address = _priceDesk
    if priceDesk == empty(address):
        priceDesk = addys._getPriceDeskAddr()

    # undelrying price
    underlyingPrice: uint256 = staticcall PriceDesk(priceDesk).getPrice(_config.underlyingAsset, False)

    # aave v3 and compound v3 -- just use underlying price
    if _config.protocol == Protocol.COMPOUND_V3 or _config.protocol == Protocol.AAVE_V3:
        return underlyingPrice

    # weighted price per share
    weightedPricePerShare: uint256 = self._getWeightedPrice(_asset, _config)

    # erc4626 vaults
    price: uint256 = 0
    if _config.protocol == Protocol.MORPHO or _config.protocol == Protocol.EULER or _config.protocol == Protocol.FLUID:
        price = self._getErc4626Price(_asset, _config, weightedPricePerShare, underlyingPrice)

    # moonwell
    elif _config.protocol == Protocol.MOONWELL:
        price = self._getMoonwellPrice(_asset, _config, weightedPricePerShare, underlyingPrice)

    # TODO: implement rest of protocols

    return price


# utilities


@view
@external
def hasPriceFeed(_asset: address) -> bool:
    return self.priceConfigs[_asset].underlyingAsset != empty(address)


@view
@external
def hasPendingPriceFeedUpdate(_asset: address) -> bool:
    return timeLock._hasPendingAction(self.pendingPriceConfigs[_asset].actionId)


################
# Add New Feed #
################


# initiate new feed


@external
def addNewPriceFeed(
    _asset: address,
    _protocol: Protocol,
    _minSnapshotDelay: uint256 = 60 * 5, # 5 minutes
    _maxNumSnapshots: uint256 = 20,
    _maxUpsideDeviation: uint256 = 10_00, # 10%
    _staleTime: uint256 = 0,
) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    p: PriceConfig = self._getPriceConfig(_asset, _protocol, _minSnapshotDelay, _maxNumSnapshots, _maxUpsideDeviation, _staleTime)
    assert self._isValidNewPriceConfig(_asset, p) # dev: invalid feed

    # set to pending state
    aid: uint256 = timeLock._initiateAction()
    self.pendingPriceConfigs[_asset] = PendingPriceConfig(actionId=aid, config=p)
    log NewPriceConfigPending(
        asset=_asset,
        protocol=p.protocol,
        underlyingAsset=p.underlyingAsset,
        minSnapshotDelay=p.minSnapshotDelay,
        maxNumSnapshots=p.maxNumSnapshots,
        maxUpsideDeviation=p.maxUpsideDeviation,
        staleTime=p.staleTime,
        confirmationBlock=timeLock._getActionConfirmationBlock(aid),
        actionId=aid,
    )
    return True


# confirm new feed


@external
def confirmNewPriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validate again
    d: PendingPriceConfig = self.pendingPriceConfigs[_asset]
    assert d.config.underlyingAsset != empty(address) # dev: no pending config
    if not self._isValidNewPriceConfig(_asset, d.config):
        self._cancelNewPendingPriceFeed(_asset, d.actionId)
        return False

    # check time lock
    assert timeLock._confirmAction(d.actionId) # dev: time lock not reached

    # save new feed config
    self.priceConfigs[_asset] = d.config
    self.pendingPriceConfigs[_asset] = empty(PendingPriceConfig)
    priceData._addPricedAsset(_asset)

    # add snapshot
    self._addPriceSnapshot(_asset, d.config)

    log NewPriceConfigAdded(
        asset=_asset,
        protocol=d.config.protocol,
        underlyingAsset=d.config.underlyingAsset,
        minSnapshotDelay=d.config.minSnapshotDelay,
        maxNumSnapshots=d.config.maxNumSnapshots,
        maxUpsideDeviation=d.config.maxUpsideDeviation,
        staleTime=d.config.staleTime,
    )
    return True


# cancel new feed


@external
def cancelNewPendingPriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    d: PendingPriceConfig = self.pendingPriceConfigs[_asset]
    self._cancelNewPendingPriceFeed(_asset, d.actionId)
    log NewPriceConfigCancelled(
        asset=_asset,
        protocol=d.config.protocol,
        underlyingAsset=d.config.underlyingAsset,
    )
    return True


@internal
def _cancelNewPendingPriceFeed(_asset: address, _aid: uint256):
    assert timeLock._cancelAction(_aid) # dev: cannot cancel action
    self.pendingPriceConfigs[_asset] = empty(PendingPriceConfig)


# validation


@view
@external
def isValidNewFeed(
    _asset: address,
    _protocol: Protocol,
    _minSnapshotDelay: uint256,
    _maxNumSnapshots: uint256,
    _maxUpsideDeviation: uint256,
    _staleTime: uint256,
) -> bool:
    config: PriceConfig = self._getPriceConfig(_asset, _protocol, _minSnapshotDelay, _maxNumSnapshots, _maxUpsideDeviation, _staleTime)
    return self._isValidNewPriceConfig(_asset, config)


@view
@internal
def _isValidNewPriceConfig(_asset: address, _config: PriceConfig) -> bool:
    if priceData.indexOfAsset[_asset] != 0 or self.priceConfigs[_asset].underlyingAsset != empty(address): # use the `updatePriceConfig` function instead
        return False
    return self._isValidFeedConfig(_asset, _config)


@view
@internal
def _isValidFeedConfig(_asset: address, _config: PriceConfig) -> bool:
    if empty(address) in [_asset, _config.underlyingAsset]:
        return False
    if _config.minSnapshotDelay > (60 * 60 * 24 * 7): # 1 week
        return False
    if _config.maxNumSnapshots == 0 or _config.maxNumSnapshots > 25:
        return False
    if _config.maxUpsideDeviation > HUNDRED_PERCENT:
        return False
    if 0 in [_config.underlyingDecimals, _config.vaultTokenDecimals]:
        return False
    return staticcall PriceDesk(addys._getPriceDeskAddr()).getPrice(_config.underlyingAsset, False) != 0


# create price config


@view
@internal
def _getPriceConfig(
    _asset: address,
    _protocol: Protocol,
    _minSnapshotDelay: uint256,
    _maxNumSnapshots: uint256,
    _maxUpsideDeviation: uint256,
    _staleTime: uint256,
) -> PriceConfig:

    # underlying asset
    underlyingAsset: address = empty(address)
    if _protocol == Protocol.MORPHO:
        underlyingAsset = self._getMorphoUnderlyingAsset(_asset)

    elif _protocol == Protocol.EULER:
        underlyingAsset = self._getEulerUnderlyingAsset(_asset)

    elif _protocol == Protocol.FLUID:
        underlyingAsset = self._getFluidUnderlyingAsset(_asset)

    elif _protocol == Protocol.COMPOUND_V3:
        underlyingAsset = self._getCompoundV3UnderlyingAsset(_asset)

    elif _protocol == Protocol.MOONWELL:
        underlyingAsset = self._getMoonwellUnderlyingAsset(_asset)

    elif _protocol == Protocol.AAVE_V3:
        underlyingAsset = self._getAaveV3UnderlyingAsset(_asset)

    # TODO: implement rest of protocols

    underlyingDecimals: uint256 = 0
    if underlyingAsset != empty(address):
        underlyingDecimals = convert(staticcall IERC20Detailed(underlyingAsset).decimals(), uint256)

    # vault token decimals
    vaultTokenDecimals: uint256 = 0
    if _asset != empty(address):
        vaultTokenDecimals = convert(staticcall IERC20Detailed(_asset).decimals(), uint256)

    return PriceConfig(
        protocol=_protocol,
        underlyingAsset=underlyingAsset,
        underlyingDecimals=underlyingDecimals,
        vaultTokenDecimals=vaultTokenDecimals,
        minSnapshotDelay=_minSnapshotDelay,
        maxNumSnapshots=_maxNumSnapshots,
        maxUpsideDeviation=_maxUpsideDeviation,
        staleTime=_staleTime,
        lastSnapshot=empty(PriceSnapshot),
        nextIndex=0,
    )


#################
# Update Config #
#################


@external
def updatePriceConfig(
    _asset: address,
    _minSnapshotDelay: uint256 = 60 * 5, # 5 minutes
    _maxNumSnapshots: uint256 = 20,
    _maxUpsideDeviation: uint256 = 10_00, # 10%
    _staleTime: uint256 = 0,
) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    p: PriceConfig = self.priceConfigs[_asset]
    p.minSnapshotDelay = _minSnapshotDelay
    p.maxNumSnapshots = _maxNumSnapshots
    p.maxUpsideDeviation = _maxUpsideDeviation
    p.staleTime = _staleTime
    assert self._isValidUpdateConfig(_asset, p) # dev: invalid config

    # set to pending state
    aid: uint256 = timeLock._initiateAction()
    self.pendingPriceConfigs[_asset] = PendingPriceConfig(actionId=aid, config=p)
    log PriceConfigUpdatePending(
        asset=_asset,
        protocol=p.protocol,
        underlyingAsset=p.underlyingAsset,
        minSnapshotDelay=p.minSnapshotDelay,
        maxNumSnapshots=p.maxNumSnapshots,
        maxUpsideDeviation=p.maxUpsideDeviation,
        staleTime=p.staleTime,
        confirmationBlock=timeLock._getActionConfirmationBlock(aid),
        actionId=aid,
    )
    return True


# confirm new feed


@external
def confirmPriceFeedUpdate(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validate again
    d: PendingPriceConfig = self.pendingPriceConfigs[_asset]
    assert d.config.underlyingAsset != empty(address) # dev: no pending config
    if not self._isValidUpdateConfig(_asset, d.config):
        self._cancelPriceFeedUpdate(_asset, d.actionId)
        return False

    # check time lock
    assert timeLock._confirmAction(d.actionId) # dev: time lock not reached

    # save new feed config
    self.priceConfigs[_asset] = d.config
    self.pendingPriceConfigs[_asset] = empty(PendingPriceConfig)

    # add snapshot
    self._addPriceSnapshot(_asset, d.config)

    log PriceConfigUpdated(
        asset=_asset,
        protocol=d.config.protocol,
        underlyingAsset=d.config.underlyingAsset,
        minSnapshotDelay=d.config.minSnapshotDelay,
        maxNumSnapshots=d.config.maxNumSnapshots,
        maxUpsideDeviation=d.config.maxUpsideDeviation,
        staleTime=d.config.staleTime,
    )
    return True


# cancel new feed


@external
def cancelPriceFeedUpdate(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    d: PendingPriceConfig = self.pendingPriceConfigs[_asset]
    self._cancelPriceFeedUpdate(_asset, d.actionId)
    log PriceConfigUpdateCancelled(
        asset=_asset,
        protocol=d.config.protocol,
        underlyingAsset=d.config.underlyingAsset,
    )
    return True


@internal
def _cancelPriceFeedUpdate(_asset: address, _aid: uint256):
    assert timeLock._cancelAction(_aid) # dev: cannot cancel action
    self.pendingPriceConfigs[_asset] = empty(PendingPriceConfig)


# validation


@view
@external
def isValidUpdateConfig(_asset: address, _maxNumSnapshots: uint256, _staleTime: uint256) -> bool:
    p: PriceConfig = self.priceConfigs[_asset]
    p.maxNumSnapshots = _maxNumSnapshots
    p.staleTime = _staleTime
    return self._isValidUpdateConfig(_asset, p)


@view
@internal
def _isValidUpdateConfig(_asset: address, _config: PriceConfig) -> bool:
    if priceData.indexOfAsset[_asset] == 0 or _config.underlyingAsset == empty(address): # must add new feed first
        return False
    return self._isValidFeedConfig(_asset, _config)


################
# Disable Feed #
################


# initiate disable feed


@external
def disablePriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validation
    prevConfig: PriceConfig = self.priceConfigs[_asset]
    assert self._isValidDisablePriceFeed(_asset, prevConfig.underlyingAsset) # dev: invalid asset

    # set to pending state
    aid: uint256 = timeLock._initiateAction()
    self.pendingPriceConfigs[_asset] = PendingPriceConfig(actionId=aid, config=empty(PriceConfig))

    log DisablePriceConfigPending(
        asset=_asset,
        protocol=prevConfig.protocol,
        underlyingAsset=prevConfig.underlyingAsset,
        confirmationBlock=timeLock._getActionConfirmationBlock(aid),
        actionId=aid,
    )
    return True


# confirm disable feed


@external
def confirmDisablePriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    # validate again
    prevConfig: PriceConfig = self.priceConfigs[_asset]
    d: PendingPriceConfig = self.pendingPriceConfigs[_asset]
    assert d.actionId != 0 # dev: no pending disable feed
    if not self._isValidDisablePriceFeed(_asset, prevConfig.underlyingAsset):
        self._cancelDisablePriceFeed(_asset, d.actionId)
        return False

    # check time lock
    assert timeLock._confirmAction(d.actionId) # dev: time lock not reached

    # disable feed
    self.priceConfigs[_asset] = empty(PriceConfig)
    self.pendingPriceConfigs[_asset] = empty(PendingPriceConfig)
    priceData._removePricedAsset(_asset)

    log DisablePriceConfigConfirmed(
        asset=_asset,
        protocol=prevConfig.protocol,
        underlyingAsset=prevConfig.underlyingAsset,
    )
    return True


# cancel disable feed


@external
def cancelDisablePriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused

    self._cancelDisablePriceFeed(_asset, self.pendingPriceConfigs[_asset].actionId)
    prevConfig: PriceConfig = self.priceConfigs[_asset]
    log DisablePriceConfigCancelled(
        asset=_asset,
        protocol=prevConfig.protocol,
        underlyingAsset=prevConfig.underlyingAsset,
    )
    return True


@internal
def _cancelDisablePriceFeed(_asset: address, _aid: uint256):
    assert timeLock._cancelAction(_aid) # dev: cannot cancel action
    self.pendingPriceConfigs[_asset] = empty(PendingPriceConfig)


# validation


@view
@external
def isValidDisablePriceFeed(_asset: address) -> bool:
    return self._isValidDisablePriceFeed(_asset, self.priceConfigs[_asset].underlyingAsset)


@view
@internal
def _isValidDisablePriceFeed(_asset: address, _underlyingAsset: address) -> bool:
    if priceData.indexOfAsset[_asset] == 0:
        return False
    return _underlyingAsset != empty(address)


###################
# Price Snapshots #
###################


# get weighted price


@view
@external
def getWeightedPrice(_asset: address) -> uint256:
    config: PriceConfig = self.priceConfigs[_asset]
    return self._getWeightedPrice(_asset, config)


@view
@internal
def _getWeightedPrice(_asset: address, _config: PriceConfig) -> uint256:
    if _config.underlyingAsset == empty(address) or _config.maxNumSnapshots == 0:
        return 0

    # calculate weighted average price using all valid snapshots
    numerator: uint256 = 0
    denominator: uint256 = 0
    for i: uint256 in range(_config.maxNumSnapshots, bound=max_value(uint256)):

        snapShot: PriceSnapshot = self.snapShots[_asset][i]
        if snapShot.pricePerShare == 0 or snapShot.totalSupply == 0 or snapShot.lastUpdate == 0:
            continue

        # too stale, skip
        if _config.staleTime != 0 and block.timestamp > snapShot.lastUpdate + _config.staleTime:
            continue

        numerator += (snapShot.totalSupply * snapShot.pricePerShare)
        denominator += snapShot.totalSupply

    # weighted price per share
    weightedPricePerShare: uint256 = 0
    if numerator != 0:
        weightedPricePerShare = numerator // denominator
    else:
        weightedPricePerShare = _config.lastSnapshot.pricePerShare

    return weightedPricePerShare


# add price snapshot


@external 
def addPriceSnapshot(_asset: address) -> bool:
    assert addys._isValidRipeAddr(msg.sender) # dev: no perms
    assert not priceData.isPaused # dev: contract paused
    return self._addPriceSnapshot(_asset, self.priceConfigs[_asset])


@internal 
def _addPriceSnapshot(_asset: address, _config: PriceConfig) -> bool:
    config: PriceConfig = _config
    if config.underlyingAsset == empty(address):
        return False

    # aave v3 and compound v3 - not using snapshots
    if _config.protocol == Protocol.COMPOUND_V3 or _config.protocol == Protocol.AAVE_V3:
        return False

    # already have snapshot for this time
    if config.lastSnapshot.lastUpdate == block.timestamp:
        return False

    # check if snapshot is too recent
    if config.lastSnapshot.lastUpdate + config.minSnapshotDelay > block.timestamp:
        return False

    # create and store new snapshot
    newSnapshot: PriceSnapshot = self._getLatestSnapshot(_asset, config)
    config.lastSnapshot = newSnapshot
    self.snapShots[_asset][config.nextIndex] = newSnapshot

    # update index
    config.nextIndex += 1
    if config.nextIndex >= config.maxNumSnapshots:
        config.nextIndex = 0

    # save config data
    self.priceConfigs[_asset] = config

    log PricePerShareSnapshotAdded(
        asset=_asset,
        protocol=config.protocol,
        underlyingAsset=config.underlyingAsset,
        totalSupply=newSnapshot.totalSupply,
        pricePerShare=newSnapshot.pricePerShare,
    )
    return True


# latest snapshot


@view
@external
def getLatestSnapshot(_asset: address) -> PriceSnapshot:
    return self._getLatestSnapshot(_asset, self.priceConfigs[_asset])


@view
@internal
def _getLatestSnapshot(_asset: address, _config: PriceConfig) -> PriceSnapshot:
    totalSupply: uint256 = staticcall IERC20(_asset).totalSupply() // (10 ** _config.vaultTokenDecimals)
    pricePerShare: uint256 = 0

    # erc4626 vaults
    if _config.protocol == Protocol.MORPHO or _config.protocol == Protocol.EULER or _config.protocol == Protocol.FLUID:
        pricePerShare = self._getCurrentErc4626PricePerShare(_asset, _config.vaultTokenDecimals)

    # moonwell
    elif _config.protocol == Protocol.MOONWELL:
        pricePerShare = self._getCurrentMoonwellPricePerShare(_asset, _config.vaultTokenDecimals)

    # TODO: implement rest of protocols

    # throttle upside (extra safety check)
    pricePerShare = self._throttleUpside(pricePerShare, _config.lastSnapshot.pricePerShare, _config.maxUpsideDeviation)

    return PriceSnapshot(
        totalSupply=totalSupply,
        pricePerShare=pricePerShare,
        lastUpdate=block.timestamp,
    )


@view
@internal
def _throttleUpside(_newValue: uint256, _prevValue: uint256, _maxUpside: uint256) -> uint256:
    if _maxUpside == 0 or _prevValue == 0 or _newValue == 0:
        return _newValue
    maxPricePerShare: uint256 = _prevValue + (_prevValue * _maxUpside // HUNDRED_PERCENT)
    return min(_newValue, maxPricePerShare)


##################
# Erc4626 Vaults #
##################


@view
@internal
def _getErc4626Price(
    _asset: address,
    _config: PriceConfig,
    _weightedPricePerShare: uint256,
    _underlyingPrice: uint256,
) -> uint256:
    pricePerShare: uint256 = _weightedPricePerShare
    if pricePerShare == 0 or _underlyingPrice == 0:
        return 0

    # allow downside if current price per share is lower
    currentPricePerShare: uint256 = self._getCurrentErc4626PricePerShare(_asset, _config.vaultTokenDecimals)
    if currentPricePerShare != 0:
        pricePerShare = min(pricePerShare, currentPricePerShare)

    return _underlyingPrice * pricePerShare // (10 ** _config.underlyingDecimals)


@view
@internal
def _getCurrentErc4626PricePerShare(_asset: address, _decimals: uint256) -> uint256:
    return staticcall IERC4626(_asset).convertToAssets(10 ** _decimals)


##########
# Morpho #
##########


@view
@internal
def _getMorphoUnderlyingAsset(_asset: address) -> address:
    if not staticcall MorphoRegistry(MORPHO_ADDRS[0]).isMetaMorpho(_asset) and not staticcall MorphoRegistry(MORPHO_ADDRS[1]).isMetaMorpho(_asset):
        return empty(address)
    return staticcall IERC4626(_asset).asset()


#########
# Euler #
#########


@view
@internal
def _getEulerUnderlyingAsset(_asset: address) -> address:
    if not staticcall EulerRegistry(EULER_ADDRS[0]).isProxy(_asset) and not staticcall EulerRegistry(EULER_ADDRS[1]).isValidDeployment(_asset):
        return empty(address)
    return staticcall IERC4626(_asset).asset()


#########
# Fluid #
#########


@view
@internal
def _getFluidUnderlyingAsset(_asset: address) -> address:
    fTokens: DynArray[address, MAX_MARKETS] = staticcall FluidRegistry(FLUID_ADDR).getAllFTokens()
    if _asset not in fTokens:
        return empty(address)
    return staticcall IERC4626(_asset).asset()


###############
# Compound v3 #
###############


@view
@internal
def _getCompoundV3UnderlyingAsset(_asset: address) -> address:
    if staticcall CompoundV3Registry(COMPOUND_V3_ADDR).factory(_asset) == empty(address):
        return empty(address)
    return staticcall CompoundV3(_asset).baseToken()


###########
# Aave v3 #
###########


@view
@internal
def _getAaveV3UnderlyingAsset(_asset: address) -> address:
    dataProvider: address = staticcall AaveRegistry(AAVE_V3_ADDR).getPoolDataProvider()
    aTokens: DynArray[TokenData, MAX_MARKETS] = staticcall AaveRegistry(dataProvider).getAllATokens()
    for a: TokenData in aTokens:
        if a.tokenAddress == _asset:
            return staticcall AaveToken(_asset).UNDERLYING_ASSET_ADDRESS()
    return empty(address)


############
# Moonwell #
############


@view
@internal
def _getMoonwellPrice(
    _asset: address,
    _config: PriceConfig,
    _weightedPricePerShare: uint256,
    _underlyingPrice: uint256,
) -> uint256:
    pricePerShare: uint256 = _weightedPricePerShare
    if pricePerShare == 0 or _underlyingPrice == 0:
        return 0

    # allow downside if current price per share is lower
    currentPricePerShare: uint256 = self._getCurrentMoonwellPricePerShare(_asset, _config.vaultTokenDecimals)
    if currentPricePerShare != 0:
        pricePerShare = min(pricePerShare, currentPricePerShare)

    return _underlyingPrice * pricePerShare // (10 ** _config.underlyingDecimals)


@view
@internal
def _getCurrentMoonwellPricePerShare(_asset: address, _decimals: uint256) -> uint256:
    return (10 ** _decimals) * staticcall Moonwell(_asset).exchangeRateStored() // (10 ** 18)


@view
@internal
def _getMoonwellUnderlyingAsset(_asset: address) -> address:
    compMarkets: DynArray[address, MAX_MARKETS] = staticcall MoonwellRegistry(MOONWELL_ADDR).getAllMarkets()
    if _asset not in compMarkets:
        return empty(address)
    return staticcall Moonwell(_asset).underlying()