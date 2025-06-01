# @version 0.4.1
# pragma optimize codesize

implements: Department

exports: gov.__interface__
exports: addys.__interface__
exports: deptBasics.__interface__
exports: timeLock.__interface__

initializes: gov
initializes: addys
initializes: deptBasics[addys := addys]
initializes: timeLock[gov := gov]

import contracts.modules.LocalGov as gov
import contracts.modules.Addys as addys
import contracts.modules.DeptBasics as deptBasics
import contracts.modules.TimeLock as timeLock
from interfaces import Department

interface MissionControl:
    def setPriorityLiqAssetVaults(_priorityLiqAssetVaults: DynArray[VaultLite, PRIORITY_VAULT_DATA]): nonpayable
    def setPriorityPriceSourceIds(_priorityIds: DynArray[uint256, MAX_PRIORITY_PRICE_SOURCES]): nonpayable
    def setPriorityStabVaults(_priorityStabVaults: DynArray[VaultLite, PRIORITY_VAULT_DATA]): nonpayable
    def isSupportedAssetInVault(_vaultId: uint256, _asset: address) -> bool: view
    def setRipeRewardsConfig(_rewardsConfig: RipeRewardsConfig): nonpayable
    def setGeneralDebtConfig(_genDebtConfig: GenDebtConfig): nonpayable
    def setUnderscoreRegistry(_underscoreRegistry: address): nonpayable
    def setCanDisable(_user: address, _canDisable: bool): nonpayable
    def setGeneralConfig(_genConfig: GenConfig): nonpayable
    def rewardsConfig() -> RipeRewardsConfig: view
    def canDisable(_user: address) -> bool: view
    def genDebtConfig() -> GenDebtConfig: view
    def underscoreRegistry() -> address: view
    def genConfig() -> GenConfig: view

interface VaultBook:
    def isValidRegId(_regId: uint256) -> bool: view

interface PriceDesk:
    def isValidRegId(_regId: uint256) -> bool: view

interface UnderscoreAgentFactory:
    def isUserWallet(_addr: address) -> bool: view

interface UnderscoreRegistry:
    def getAddy(_addyId: uint256) -> address: view

flag ActionType:
    RIPE_REWARDS_BLOCK
    RIPE_REWARDS_ALLOCS
    GEN_CONFIG_VAULT_LIMITS
    GEN_CONFIG_STALE_TIME
    DEBT_GLOBAL_LIMITS
    DEBT_BORROW_INTERVAL
    DEBT_KEEPER_CONFIG
    DEBT_LTV_PAYBACK_BUFFER
    DEBT_AUCTION_PARAMS

struct GenConfig:
    perUserMaxVaults: uint256
    perUserMaxAssetsPerVault: uint256
    priceStaleTime: uint256
    canDeposit: bool
    canWithdraw: bool
    canBorrow: bool
    canRepay: bool
    canClaimLoot: bool
    canLiquidate: bool
    canRedeemCollateral: bool
    canRedeemInStabPool: bool
    canBuyInAuction: bool
    canClaimInStabPool: bool

struct GenConfigLite:
    perUserMaxVaults: uint256
    perUserMaxAssetsPerVault: uint256
    priceStaleTime: uint256

struct GenDebtConfig:
    perUserDebtLimit: uint256
    globalDebtLimit: uint256
    minDebtAmount: uint256
    numAllowedBorrowers: uint256
    maxBorrowPerInterval: uint256
    numBlocksPerInterval: uint256
    keeperFeeRatio: uint256
    minKeeperFee: uint256
    isDaowryEnabled: bool
    ltvPaybackBuffer: uint256
    genAuctionParams: AuctionParams

struct RipeRewardsConfig:
    arePointsEnabled: bool
    ripePerBlock: uint256
    borrowersAlloc: uint256
    stakersAlloc: uint256
    votersAlloc: uint256
    genDepositorsAlloc: uint256

struct AuctionParams:
    hasParams: bool
    startDiscount: uint256
    maxDiscount: uint256
    delay: uint256
    duration: uint256

struct VaultLite:
    vaultId: uint256
    asset: address

event PendingVaultLimitsChange:
    perUserMaxVaults: uint256
    perUserMaxAssetsPerVault: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingStaleTimeChange:
    priceStaleTime: uint256
    confirmationBlock: uint256
    actionId: uint256

event CanDepositSet:
    canDeposit: bool
    caller: indexed(address)

event CanWithdrawSet:
    canWithdraw: bool
    caller: indexed(address)

event CanBorrowSet:
    canBorrow: bool
    caller: indexed(address)

event CanRepaySet:
    canRepay: bool
    caller: indexed(address)

event CanClaimLootSet:
    canClaimLoot: bool
    caller: indexed(address)

event CanLiquidateSet:
    canLiquidate: bool
    caller: indexed(address)

event CanRedeemCollateralSet:
    canRedeemCollateral: bool
    caller: indexed(address)

event CanRedeemInStabPoolSet:
    canRedeemInStabPool: bool
    caller: indexed(address)

event CanBuyInAuctionSet:
    canBuyInAuction: bool
    caller: indexed(address)

event CanClaimInStabPoolSet:
    canClaimInStabPool: bool
    caller: indexed(address)

event PendingGlobalDebtLimitsChange:
    perUserDebtLimit: uint256
    globalDebtLimit: uint256
    minDebtAmount: uint256
    numAllowedBorrowers: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingBorrowIntervalConfigChange:
    maxBorrowPerInterval: uint256
    numBlocksPerInterval: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingKeeperConfigChange:
    keeperFeeRatio: uint256
    minKeeperFee: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingLtvPaybackBufferChange:
    ltvPaybackBuffer: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingDefaultAuctionParamsChange:
    startDiscount: uint256
    maxDiscount: uint256
    delay: uint256
    duration: uint256
    confirmationBlock: uint256
    actionId: uint256

event IsDaowryEnabledSet:
    isDaowryEnabled: bool
    caller: indexed(address)

event PendingRipeRewardsPerBlockChange:
    ripePerBlock: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingRipeRewardsAllocsChange:
    borrowersAlloc: uint256
    stakersAlloc: uint256
    votersAlloc: uint256
    genDepositorsAlloc: uint256
    confirmationBlock: uint256
    actionId: uint256

event RewardsPointsEnabledModified:
    arePointsEnabled: bool
    caller: indexed(address)


#########


event PriorityLiqAssetVaultsSet:
    numVaults: uint256

event PriorityStabVaultsSet:
    numVaults: uint256

event RipeRewardsConfigSet:
    arePointsEnabled: bool
    ripePerBlock: uint256
    borrowersAlloc: uint256
    stakersAlloc: uint256
    votersAlloc: uint256
    genDepositorsAlloc: uint256

event PendingRipeRewardsConfigChange:
    arePointsEnabled: bool
    ripePerBlock: uint256
    borrowersAlloc: uint256
    stakersAlloc: uint256
    votersAlloc: uint256
    genDepositorsAlloc: uint256
    confirmationBlock: uint256
    actionId: uint256

event RipeRewardsPerBlockSet:
    ripePerBlock: uint256

event RipeRewardsAllocsSet:
    borrowersAlloc: uint256
    stakersAlloc: uint256
    votersAlloc: uint256
    genDepositorsAlloc: uint256

event GeneralConfigSet:
    perUserMaxVaults: uint256
    perUserMaxAssetsPerVault: uint256
    priceStaleTime: uint256
    canDeposit: bool
    canWithdraw: bool
    canBorrow: bool
    canRepay: bool
    canClaimLoot: bool
    canLiquidate: bool
    canRedeemCollateral: bool
    canRedeemInStabPool: bool
    canBuyInAuction: bool
    canClaimInStabPool: bool

event UnderscoreRegistrySet:
    addr: indexed(address)

event CanDisableSet:
    user: indexed(address)
    canDisable: bool

event PriorityPriceSourceIdsModified:
    numIds: uint256

event StaleTimeSet:
    staleTime: uint256

event VaultLimitsSet:
    perUserMaxVaults: uint256
    perUserMaxAssetsPerVault: uint256

event GlobalDebtLimitsSet:
    perUserDebtLimit: uint256
    globalDebtLimit: uint256
    minDebtAmount: uint256
    numAllowedBorrowers: uint256

event BorrowIntervalConfigSet:
    maxBorrowPerInterval: uint256
    numBlocksPerInterval: uint256

event KeeperConfigSet:
    keeperFeeRatio: uint256
    minKeeperFee: uint256

event LtvPaybackBufferSet:
    ltvPaybackBuffer: uint256

event GenAuctionParamsSet:
    startDiscount: uint256
    maxDiscount: uint256
    delay: uint256
    duration: uint256

# pending changes
actionType: public(HashMap[uint256, ActionType]) # aid -> type
pendingRipeRewardsConfig: public(HashMap[uint256, RipeRewardsConfig]) # aid -> config
pendingGeneralConfig: public(HashMap[uint256, GenConfigLite]) # aid -> config
pendingDebtConfig: public(HashMap[uint256, GenDebtConfig]) # aid -> config

# temp data
vaultDedupe: transient(HashMap[uint256, HashMap[address, bool]]) # vault id -> asset

MIN_STALE_TIME: public(immutable(uint256))
MAX_STALE_TIME: public(immutable(uint256))

MAX_VAULTS_PER_ASSET: constant(uint256) = 10
MAX_PRIORITY_PRICE_SOURCES: constant(uint256) = 10
PRIORITY_VAULT_DATA: constant(uint256) = 20
UNDERSCORE_AGENT_FACTORY_ID: constant(uint256) = 1
HUNDRED_PERCENT: constant(uint256) = 100_00 # 100%


@deploy
def __init__(
    _ripeHq: address,
    _minStaleTime: uint256,
    _maxStaleTime: uint256,
    _minConfigTimeLock: uint256,
    _maxConfigTimeLock: uint256,
):
    gov.__init__(_ripeHq, empty(address), 0, 0, 0)
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, False, False) # no minting
    timeLock.__init__(_minConfigTimeLock, _maxConfigTimeLock, 0)

    assert _minStaleTime < _maxStaleTime # dev: invalid stale time range
    MIN_STALE_TIME = _minStaleTime
    MAX_STALE_TIME = _maxStaleTime


# access control


@view
@internal
def _hasPermsToEnable(_caller: address, _shouldEnable: bool) -> bool:
    if gov._canGovern(_caller):
        return True
    if not _shouldEnable:
        return staticcall MissionControl(addys._getMissionControlAddr()).canDisable(_caller)
    return False


##################
# General Config #
##################


# vault limits


@external
def setVaultLimits(_perUserMaxVaults: uint256, _perUserMaxAssetsPerVault: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused

    assert self._areValidVaultLimits(_perUserMaxVaults, _perUserMaxAssetsPerVault) # dev: invalid vault limits
    return self._setPendingGenConfig(ActionType.GEN_CONFIG_VAULT_LIMITS, _perUserMaxVaults, _perUserMaxAssetsPerVault)


@view
@internal
def _areValidVaultLimits(_perUserMaxVaults: uint256, _perUserMaxAssetsPerVault: uint256) -> bool:
    if 0 in [_perUserMaxVaults, _perUserMaxAssetsPerVault]:
        return False
    if max_value(uint256) in [_perUserMaxVaults, _perUserMaxAssetsPerVault]:
        return False
    return True


# stale time for prices


@external
def setStaleTime(_staleTime: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: not activated

    assert self._isValidStaleTime(_staleTime) # dev: invalid stale time
    return self._setPendingGenConfig(ActionType.GEN_CONFIG_STALE_TIME, 0, 0, _staleTime)


@view
@internal
def _isValidStaleTime(_staleTime: uint256) -> bool:
    return _staleTime >= MIN_STALE_TIME and _staleTime <= MAX_STALE_TIME


# set pending general config


@internal
def _setPendingGenConfig(
    _actionType: ActionType,
    _perUserMaxVaults: uint256 = 0,
    _perUserMaxAssetsPerVault: uint256 = 0,
    _priceStaleTime: uint256 = 0,
) -> uint256:
    aid: uint256 = timeLock._initiateAction()

    self.actionType[aid] = _actionType
    self.pendingGeneralConfig[aid] = GenConfigLite(
        perUserMaxVaults=_perUserMaxVaults,
        perUserMaxAssetsPerVault=_perUserMaxAssetsPerVault,
        priceStaleTime=_priceStaleTime,
    )

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    if _actionType == ActionType.GEN_CONFIG_VAULT_LIMITS:
        log PendingVaultLimitsChange(
            perUserMaxVaults=_perUserMaxVaults,
            perUserMaxAssetsPerVault=_perUserMaxAssetsPerVault,
            confirmationBlock=confirmationBlock,
            actionId=aid,
        )
    elif _actionType == ActionType.GEN_CONFIG_STALE_TIME:
        log PendingStaleTimeChange(
            priceStaleTime=_priceStaleTime,
            confirmationBlock=confirmationBlock,
            actionId=aid,
        )
    return aid


# enable / disable


@external
def setCanDeposit(_shouldEnable: bool) -> bool:
    assert not deptBasics.isPaused # dev: contract paused
    assert self._hasPermsToEnable(msg.sender, _shouldEnable) # dev: no perms

    mc: address = addys._getMissionControlAddr()
    config: GenConfig = staticcall MissionControl(mc).genConfig()
    assert config.canDeposit != _shouldEnable # dev: already set
    config.canDeposit = _shouldEnable
    extcall MissionControl(mc).setGeneralConfig(config)

    log CanDepositSet(canDeposit=_shouldEnable, caller=msg.sender)
    return True


@external
def setCanWithdraw(_shouldEnable: bool) -> bool:
    assert not deptBasics.isPaused # dev: contract paused
    assert self._hasPermsToEnable(msg.sender, _shouldEnable) # dev: no perms

    mc: address = addys._getMissionControlAddr()
    config: GenConfig = staticcall MissionControl(mc).genConfig()
    assert config.canWithdraw != _shouldEnable # dev: already set
    config.canWithdraw = _shouldEnable
    extcall MissionControl(mc).setGeneralConfig(config)

    log CanWithdrawSet(canWithdraw=_shouldEnable, caller=msg.sender)
    return True


@external
def setCanBorrow(_shouldEnable: bool) -> bool:
    assert not deptBasics.isPaused # dev: contract paused
    assert self._hasPermsToEnable(msg.sender, _shouldEnable) # dev: no perms

    mc: address = addys._getMissionControlAddr()
    config: GenConfig = staticcall MissionControl(mc).genConfig()
    assert config.canBorrow != _shouldEnable # dev: already set
    config.canBorrow = _shouldEnable
    extcall MissionControl(mc).setGeneralConfig(config)

    log CanBorrowSet(canBorrow=_shouldEnable, caller=msg.sender)
    return True


@external
def setCanRepay(_shouldEnable: bool) -> bool:
    assert not deptBasics.isPaused # dev: contract paused
    assert self._hasPermsToEnable(msg.sender, _shouldEnable) # dev: no perms

    mc: address = addys._getMissionControlAddr()
    config: GenConfig = staticcall MissionControl(mc).genConfig()
    assert config.canRepay != _shouldEnable # dev: already set
    config.canRepay = _shouldEnable
    extcall MissionControl(mc).setGeneralConfig(config)

    log CanRepaySet(canRepay=_shouldEnable, caller=msg.sender)
    return True


@external
def setCanClaimLoot(_shouldEnable: bool) -> bool:
    assert not deptBasics.isPaused # dev: contract paused
    assert self._hasPermsToEnable(msg.sender, _shouldEnable) # dev: no perms

    mc: address = addys._getMissionControlAddr()
    config: GenConfig = staticcall MissionControl(mc).genConfig()
    assert config.canClaimLoot != _shouldEnable # dev: already set
    config.canClaimLoot = _shouldEnable
    extcall MissionControl(mc).setGeneralConfig(config)

    log CanClaimLootSet(canClaimLoot=_shouldEnable, caller=msg.sender)
    return True


@external
def setCanLiquidate(_shouldEnable: bool) -> bool:
    assert not deptBasics.isPaused # dev: contract paused
    assert self._hasPermsToEnable(msg.sender, _shouldEnable) # dev: no perms

    mc: address = addys._getMissionControlAddr()
    config: GenConfig = staticcall MissionControl(mc).genConfig()
    assert config.canLiquidate != _shouldEnable # dev: already set
    config.canLiquidate = _shouldEnable
    extcall MissionControl(mc).setGeneralConfig(config)

    log CanLiquidateSet(canLiquidate=_shouldEnable, caller=msg.sender)
    return True


@external
def setCanRedeemCollateral(_shouldEnable: bool) -> bool:
    assert not deptBasics.isPaused # dev: contract paused
    assert self._hasPermsToEnable(msg.sender, _shouldEnable) # dev: no perms

    mc: address = addys._getMissionControlAddr()
    config: GenConfig = staticcall MissionControl(mc).genConfig()
    assert config.canRedeemCollateral != _shouldEnable # dev: already set
    config.canRedeemCollateral = _shouldEnable
    extcall MissionControl(mc).setGeneralConfig(config)

    log CanRedeemCollateralSet(canRedeemCollateral=_shouldEnable, caller=msg.sender)
    return True


@external
def setCanRedeemInStabPool(_shouldEnable: bool) -> bool:
    assert not deptBasics.isPaused # dev: contract paused
    assert self._hasPermsToEnable(msg.sender, _shouldEnable) # dev: no perms

    mc: address = addys._getMissionControlAddr()
    config: GenConfig = staticcall MissionControl(mc).genConfig()
    assert config.canRedeemInStabPool != _shouldEnable # dev: already set
    config.canRedeemInStabPool = _shouldEnable
    extcall MissionControl(mc).setGeneralConfig(config)

    log CanRedeemInStabPoolSet(canRedeemInStabPool=_shouldEnable, caller=msg.sender)
    return True


@external
def setCanBuyInAuction(_shouldEnable: bool) -> bool:
    assert not deptBasics.isPaused # dev: contract paused
    assert self._hasPermsToEnable(msg.sender, _shouldEnable) # dev: no perms

    mc: address = addys._getMissionControlAddr()
    config: GenConfig = staticcall MissionControl(mc).genConfig()
    assert config.canBuyInAuction != _shouldEnable # dev: already set
    config.canBuyInAuction = _shouldEnable
    extcall MissionControl(mc).setGeneralConfig(config)

    log CanBuyInAuctionSet(canBuyInAuction=_shouldEnable, caller=msg.sender)
    return True


@external
def setCanClaimInStabPool(_shouldEnable: bool) -> bool:
    assert not deptBasics.isPaused # dev: contract paused
    assert self._hasPermsToEnable(msg.sender, _shouldEnable) # dev: no perms

    mc: address = addys._getMissionControlAddr()
    config: GenConfig = staticcall MissionControl(mc).genConfig()
    assert config.canClaimInStabPool != _shouldEnable # dev: already set
    config.canClaimInStabPool = _shouldEnable
    extcall MissionControl(mc).setGeneralConfig(config)

    log CanClaimInStabPoolSet(canClaimInStabPool=_shouldEnable, caller=msg.sender)
    return True


###############
# Debt Config #
###############


# global debt limits


@external
def setGlobalDebtLimits(_perUserDebtLimit: uint256, _globalDebtLimit: uint256, _minDebtAmount: uint256, _numAllowedBorrowers: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused

    assert self._areValidDebtLimits(_perUserDebtLimit, _globalDebtLimit, _minDebtAmount, _numAllowedBorrowers) # dev: invalid debt limits
    return self._setPendingDebtConfig(ActionType.DEBT_GLOBAL_LIMITS, _perUserDebtLimit, _globalDebtLimit, _minDebtAmount, _numAllowedBorrowers)


@view
@internal
def _areValidDebtLimits(_perUserDebtLimit: uint256, _globalDebtLimit: uint256, _minDebtAmount: uint256, _numAllowedBorrowers: uint256) -> bool:
    if 0 in [_perUserDebtLimit, _globalDebtLimit, _numAllowedBorrowers]:
        return False
    if max_value(uint256) in [_perUserDebtLimit, _globalDebtLimit, _minDebtAmount, _numAllowedBorrowers]:
        return False
    if _perUserDebtLimit > _globalDebtLimit:
        return False
    if _minDebtAmount > _perUserDebtLimit:
        return False
    return True


# borrow intervals


@external
def setBorrowIntervalConfig(_maxBorrowPerInterval: uint256, _numBlocksPerInterval: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused

    assert self._areValidBorrowIntervalConfig(_maxBorrowPerInterval, _numBlocksPerInterval) # dev: invalid borrow interval config
    return self._setPendingDebtConfig(ActionType.DEBT_BORROW_INTERVAL, 0, 0, 0, 0, _maxBorrowPerInterval, _numBlocksPerInterval)


@view
@internal
def _areValidBorrowIntervalConfig(_maxBorrowPerInterval: uint256, _numBlocksPerInterval: uint256) -> bool:
    if 0 in [_maxBorrowPerInterval, _numBlocksPerInterval]:
        return False
    if max_value(uint256) in [_maxBorrowPerInterval, _numBlocksPerInterval]:
        return False
    config: GenDebtConfig = staticcall MissionControl(addys._getMissionControlAddr()).genDebtConfig()
    if _maxBorrowPerInterval < config.minDebtAmount:
        return False
    return True


# keeper config


@external
def setKeeperConfig(_keeperFeeRatio: uint256, _minKeeperFee: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused

    assert self._isValidKeeperConfig(_keeperFeeRatio, _minKeeperFee) # dev: invalid keeper config
    return self._setPendingDebtConfig(ActionType.DEBT_KEEPER_CONFIG, 0, 0, 0, 0, 0, 0, _keeperFeeRatio, _minKeeperFee)


@view
@internal
def _isValidKeeperConfig(_keeperFeeRatio: uint256, _minKeeperFee: uint256) -> bool:
    if max_value(uint256) in [_keeperFeeRatio, _minKeeperFee]:
        return False
    if _keeperFeeRatio > 10_00: # 10% max
        return False
    if _minKeeperFee > 100 * (10 ** 18): # $100 max
        return False
    return True


# ltv payback buffer


@external
def setLtvPaybackBuffer(_ltvPaybackBuffer: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused

    assert self._isValidLtvPaybackBuffer(_ltvPaybackBuffer) # dev: invalid ltv payback buffer
    return self._setPendingDebtConfig(ActionType.DEBT_LTV_PAYBACK_BUFFER, 0, 0, 0, 0, 0, 0, 0, 0, _ltvPaybackBuffer)


@view
@internal
def _isValidLtvPaybackBuffer(_ltvPaybackBuffer: uint256) -> bool:
    if _ltvPaybackBuffer == 0 or _ltvPaybackBuffer > 10_00: # 10% max
        return False
    return True


# gen auction params


@external
def setGenAuctionParams(
    _startDiscount: uint256,
    _maxDiscount: uint256,
    _delay: uint256,
    _duration: uint256,
) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused

    params: AuctionParams= AuctionParams(
        hasParams=True,
        startDiscount=_startDiscount,
        maxDiscount=_maxDiscount,
        delay=_delay,
        duration=_duration,
    )
    assert self._areValidAuctionParams(params) # dev: invalid auction params
    return self._setPendingDebtConfig(ActionType.DEBT_AUCTION_PARAMS, 0, 0, 0, 0, 0, 0, 0, 0, 0, params)


@view
@internal
def _areValidAuctionParams(_params: AuctionParams) -> bool:
    if not _params.hasParams:
        return False
    if _params.startDiscount >= HUNDRED_PERCENT:
        return False
    if _params.maxDiscount >= HUNDRED_PERCENT:
        return False
    if _params.startDiscount >= _params.maxDiscount:
        return False
    if _params.delay >= _params.duration:
        return False
    if _params.duration == 0 or _params.duration == max_value(uint256):
        return False
    return True


# set pending debt config


@internal
def _setPendingDebtConfig(
    _actionType: ActionType,
    _perUserDebtLimit: uint256 = 0,
    _globalDebtLimit: uint256 = 0,
    _minDebtAmount: uint256 = 0,
    _numAllowedBorrowers: uint256 = 0,
    _maxBorrowPerInterval: uint256 = 0,
    _numBlocksPerInterval: uint256 = 0,
    _keeperFeeRatio: uint256 = 0,
    _minKeeperFee: uint256 = 0,
    _ltvPaybackBuffer: uint256 = 0,
    _genAuctionParams: AuctionParams = empty(AuctionParams),
) -> uint256:
    aid: uint256 = timeLock._initiateAction()

    self.actionType[aid] = _actionType
    self.pendingDebtConfig[aid] = GenDebtConfig(
        perUserDebtLimit=_perUserDebtLimit,
        globalDebtLimit=_globalDebtLimit,
        minDebtAmount=_minDebtAmount,
        numAllowedBorrowers=_numAllowedBorrowers,
        maxBorrowPerInterval=_maxBorrowPerInterval,
        numBlocksPerInterval=_numBlocksPerInterval,
        keeperFeeRatio=_keeperFeeRatio,
        minKeeperFee=_minKeeperFee,
        isDaowryEnabled=False,
        ltvPaybackBuffer=_ltvPaybackBuffer,
        genAuctionParams=_genAuctionParams,
    )

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    if _actionType == ActionType.DEBT_GLOBAL_LIMITS:
        log PendingGlobalDebtLimitsChange(
            perUserDebtLimit=_perUserDebtLimit,
            globalDebtLimit=_globalDebtLimit,
            minDebtAmount=_minDebtAmount,
            numAllowedBorrowers=_numAllowedBorrowers,
            confirmationBlock=confirmationBlock,
            actionId=aid,
        )
    elif _actionType == ActionType.DEBT_BORROW_INTERVAL:
        log PendingBorrowIntervalConfigChange(
            maxBorrowPerInterval=_maxBorrowPerInterval,
            numBlocksPerInterval=_numBlocksPerInterval,
            confirmationBlock=confirmationBlock,
            actionId=aid,
        )
    elif _actionType == ActionType.DEBT_KEEPER_CONFIG:
        log PendingKeeperConfigChange(
            keeperFeeRatio=_keeperFeeRatio,
            minKeeperFee=_minKeeperFee,
            confirmationBlock=confirmationBlock,
            actionId=aid,
        )
    elif _actionType == ActionType.DEBT_LTV_PAYBACK_BUFFER:
        log PendingLtvPaybackBufferChange(
            ltvPaybackBuffer=_ltvPaybackBuffer,
            confirmationBlock=confirmationBlock,
            actionId=aid,
        )
    elif _actionType == ActionType.DEBT_AUCTION_PARAMS:
        log PendingDefaultAuctionParamsChange(
            startDiscount=_genAuctionParams.startDiscount,
            maxDiscount=_genAuctionParams.maxDiscount,
            delay=_genAuctionParams.delay,
            duration=_genAuctionParams.duration,
            confirmationBlock=confirmationBlock,
            actionId=aid,
        )
    return aid


# daowry


@external
def setIsDaowryEnabled(_shouldEnable: bool) -> bool:
    assert not deptBasics.isPaused # dev: contract paused
    assert self._hasPermsToEnable(msg.sender, _shouldEnable) # dev: no perms

    mc: address = addys._getMissionControlAddr()
    config: GenDebtConfig = staticcall MissionControl(mc).genDebtConfig()
    assert config.isDaowryEnabled != _shouldEnable # dev: already set
    config.isDaowryEnabled = _shouldEnable
    extcall MissionControl(mc).setGeneralDebtConfig(config)

    log IsDaowryEnabledSet(isDaowryEnabled=_shouldEnable, caller=msg.sender)
    return True


####################
# Rewards / Points #
####################


# ripe per block


@external
def setRipePerBlock(_ripePerBlock: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused
    return self._setPendingRipeRewardsConfig(ActionType.RIPE_REWARDS_BLOCK, _ripePerBlock)


# allocs


@external
def setRipeRewardsAllocs(
    _borrowersAlloc: uint256,
    _stakersAlloc: uint256,
    _votersAlloc: uint256,
    _genDepositorsAlloc: uint256,
) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused
    return self._setPendingRipeRewardsConfig(ActionType.RIPE_REWARDS_ALLOCS, 0, _borrowersAlloc, _stakersAlloc, _votersAlloc, _genDepositorsAlloc)


# set pending ripe rewards config


@internal
def _setPendingRipeRewardsConfig(
    _actionType: ActionType,
    _ripePerBlock: uint256 = 0,
    _borrowersAlloc: uint256 = 0,
    _stakersAlloc: uint256 = 0,
    _votersAlloc: uint256 = 0,
    _genDepositorsAlloc: uint256 = 0,
) -> uint256:
    aid: uint256 = timeLock._initiateAction()

    self.actionType[aid] = _actionType
    self.pendingRipeRewardsConfig[aid] = RipeRewardsConfig(
        arePointsEnabled=False,
        ripePerBlock=_ripePerBlock,
        borrowersAlloc=_borrowersAlloc,
        stakersAlloc=_stakersAlloc,
        votersAlloc=_votersAlloc,
        genDepositorsAlloc=_genDepositorsAlloc,
    )

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    if _actionType == ActionType.RIPE_REWARDS_BLOCK:
        log PendingRipeRewardsPerBlockChange(
            ripePerBlock=_ripePerBlock,
            confirmationBlock=confirmationBlock,
            actionId=aid,
        )

    elif _actionType == ActionType.RIPE_REWARDS_ALLOCS:
        log PendingRipeRewardsAllocsChange(
            borrowersAlloc=_borrowersAlloc,
            stakersAlloc=_stakersAlloc,
            votersAlloc=_votersAlloc,
            genDepositorsAlloc=_genDepositorsAlloc,
            confirmationBlock=confirmationBlock,
            actionId=aid,
        )

    return aid


# enable points


@external
def setRewardsPointsEnabled(_shouldEnable: bool) -> bool:
    assert not deptBasics.isPaused # dev: contract paused
    assert self._hasPermsToEnable(msg.sender, _shouldEnable) # dev: no perms

    mc: address = addys._getMissionControlAddr()
    rewardsConfig: RipeRewardsConfig = staticcall MissionControl(mc).rewardsConfig()
    assert rewardsConfig.arePointsEnabled != _shouldEnable # dev: already set
    rewardsConfig.arePointsEnabled = _shouldEnable
    extcall MissionControl(mc).setRipeRewardsConfig(rewardsConfig)

    log RewardsPointsEnabledModified(arePointsEnabled=_shouldEnable, caller=msg.sender)
    return True


#######################
# Priority Vault Data #
#######################


# priority liquidation


@external
def setPriorityLiqAssetVaults(_priorityLiqAssetVaults: DynArray[VaultLite, PRIORITY_VAULT_DATA]) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused

    # TODO: add time lock

    priorityVaults: DynArray[VaultLite, PRIORITY_VAULT_DATA] = self._sanitizePriorityVaults(_priorityLiqAssetVaults)
    assert len(priorityVaults) != 0 # dev: invalid priority vaults
    extcall MissionControl(addys._getMissionControlAddr()).setPriorityLiqAssetVaults(priorityVaults)

    log PriorityLiqAssetVaultsSet(numVaults=len(priorityVaults))
    return True


# priority stability pools


@external
def setPriorityStabVaults(_priorityStabVaults: DynArray[VaultLite, PRIORITY_VAULT_DATA]) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused

    # TODO: add time lock

    priorityVaults: DynArray[VaultLite, PRIORITY_VAULT_DATA] = self._sanitizePriorityVaults(_priorityStabVaults)
    assert len(priorityVaults) != 0 # dev: invalid priority vaults
    extcall MissionControl(addys._getMissionControlAddr()).setPriorityStabVaults(priorityVaults)

    log PriorityStabVaultsSet(numVaults=len(priorityVaults))
    return True


# sanitize


@internal
def _sanitizePriorityVaults(_priorityVaults: DynArray[VaultLite, PRIORITY_VAULT_DATA]) -> DynArray[VaultLite, PRIORITY_VAULT_DATA]:
    sanitizedVaults: DynArray[VaultLite, PRIORITY_VAULT_DATA] = []
    vaultBook: address = addys._getVaultBookAddr()
    mc: address = addys._getMissionControlAddr()
    for vault: VaultLite in _priorityVaults:
        if self.vaultDedupe[vault.vaultId][vault.asset]:
            continue
        if not staticcall VaultBook(vaultBook).isValidRegId(vault.vaultId):
            continue
        if not staticcall MissionControl(mc).isSupportedAssetInVault(vault.vaultId, vault.asset):
            continue
        sanitizedVaults.append(vault)
        self.vaultDedupe[vault.vaultId][vault.asset] = True
    return sanitizedVaults


#############################
# Prices - Priority Sources #
#############################


@external
def setPriorityPriceSourceIds(_priorityIds: DynArray[uint256, MAX_PRIORITY_PRICE_SOURCES]) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused

    # TODO: add time lock

    priorityIds: DynArray[uint256, MAX_PRIORITY_PRICE_SOURCES] = self._sanitizePrioritySources(_priorityIds)
    assert len(priorityIds) != 0 # dev: invalid priority sources
    extcall MissionControl(addys._getMissionControlAddr()).setPriorityPriceSourceIds(priorityIds)

    log PriorityPriceSourceIdsModified(numIds=len(priorityIds))
    return True


@view
@internal
def _sanitizePrioritySources(_priorityIds: DynArray[uint256, MAX_PRIORITY_PRICE_SOURCES]) -> DynArray[uint256, MAX_PRIORITY_PRICE_SOURCES]:
    sanitizedIds: DynArray[uint256, MAX_PRIORITY_PRICE_SOURCES] = []
    priceDesk: address = addys._getPriceDeskAddr()
    for pid: uint256 in _priorityIds:
        if not staticcall PriceDesk(priceDesk).isValidRegId(pid):
            continue
        if pid in sanitizedIds:
            continue
        sanitizedIds.append(pid)
    return sanitizedIds


#######################
# Underscore Registry #
#######################


@external
def setUnderscoreRegistry(_underscoreRegistry: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused

    # TODO: add time lock

    mc: address = addys._getMissionControlAddr()
    assert staticcall MissionControl(mc).underscoreRegistry() != _underscoreRegistry # dev: already set
    assert self._isValidUnderscoreAddr(_underscoreRegistry) # dev: invalid underscore registry
    extcall MissionControl(mc).setUnderscoreRegistry(_underscoreRegistry)

    log UnderscoreRegistrySet(addr=_underscoreRegistry)
    return True


@view
@internal
def _isValidUnderscoreAddr(_addr: address) -> bool:
    agentFactory: address = staticcall UnderscoreRegistry(_addr).getAddy(UNDERSCORE_AGENT_FACTORY_ID)
    if agentFactory == empty(address):
        return False

    # make sure has interface
    return not staticcall UnderscoreAgentFactory(agentFactory).isUserWallet(empty(address))


###############
# Can Disable #
###############


@external
def setCanDisable(_user: address, _canDisable: bool) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused

    # TODO: add time lock

    mc: address = addys._getMissionControlAddr()
    assert _user != empty(address) # dev: invalid user
    assert staticcall MissionControl(mc).canDisable(_user) != _canDisable # dev: already set
    extcall MissionControl(mc).setCanDisable(_user, _canDisable)

    log CanDisableSet(user=_user, canDisable=_canDisable)
    return True


#############
# Execution #
#############


@external
def executePendingAction(_aid: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused
    assert timeLock._confirmAction(_aid) # dev: time lock not reached

    actionType: ActionType = self.actionType[_aid]
    mc: address = addys._getMissionControlAddr()

    if actionType == ActionType.RIPE_REWARDS_BLOCK:
        config: RipeRewardsConfig = staticcall MissionControl(mc).rewardsConfig()
        config.ripePerBlock = self.pendingRipeRewardsConfig[_aid].ripePerBlock
        extcall MissionControl(mc).setRipeRewardsConfig(config)
        log RipeRewardsPerBlockSet(ripePerBlock=config.ripePerBlock)

    elif actionType == ActionType.RIPE_REWARDS_ALLOCS:
        config: RipeRewardsConfig = staticcall MissionControl(mc).rewardsConfig()
        pending: RipeRewardsConfig = self.pendingRipeRewardsConfig[_aid]
        config.borrowersAlloc = pending.borrowersAlloc
        config.stakersAlloc = pending.stakersAlloc
        config.votersAlloc = pending.votersAlloc
        config.genDepositorsAlloc = pending.genDepositorsAlloc
        extcall MissionControl(mc).setRipeRewardsConfig(config)
        log RipeRewardsAllocsSet(borrowersAlloc=pending.borrowersAlloc, stakersAlloc=pending.stakersAlloc, votersAlloc=pending.votersAlloc, genDepositorsAlloc=pending.genDepositorsAlloc)

    elif actionType == ActionType.GEN_CONFIG_VAULT_LIMITS:
        config: GenConfig = staticcall MissionControl(mc).genConfig()
        pending: GenConfigLite = self.pendingGeneralConfig[_aid]
        config.perUserMaxVaults = pending.perUserMaxVaults
        config.perUserMaxAssetsPerVault = pending.perUserMaxAssetsPerVault
        extcall MissionControl(mc).setGeneralConfig(config)
        log VaultLimitsSet(perUserMaxVaults=pending.perUserMaxVaults, perUserMaxAssetsPerVault=pending.perUserMaxAssetsPerVault)

    elif actionType == ActionType.GEN_CONFIG_STALE_TIME:
        config: GenConfig = staticcall MissionControl(mc).genConfig()
        pending: GenConfigLite = self.pendingGeneralConfig[_aid]
        config.priceStaleTime = pending.priceStaleTime
        extcall MissionControl(mc).setGeneralConfig(config)
        log StaleTimeSet(staleTime=pending.priceStaleTime)

    self.actionType[_aid] = empty(ActionType)
    return True