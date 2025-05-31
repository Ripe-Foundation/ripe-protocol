# @version 0.4.1
# pragma optimize codesize

implements: Department

exports: gov.__interface__
exports: addys.__interface__
exports: deptBasics.__interface__

initializes: gov
initializes: addys
initializes: deptBasics[addys := addys]

import contracts.modules.LocalGov as gov
import contracts.modules.Addys as addys
import contracts.modules.DeptBasics as deptBasics
from interfaces import Department

interface MissionControl:
    def setPriorityLiqAssetVaults(_priorityLiqAssetVaults: DynArray[VaultLite, PRIORITY_VAULT_DATA]): nonpayable
    def setPriorityStabVaults(_priorityStabVaults: DynArray[VaultLite, PRIORITY_VAULT_DATA]): nonpayable
    def setPriorityPriceSourceIds(_priorityIds: DynArray[uint256, MAX_PRIORITY_PRICE_SOURCES]): nonpayable
    def setAssetConfig(_asset: address, _assetConfig: AssetConfig): nonpayable
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

struct AssetConfig:
    vaultIds: DynArray[uint256, MAX_VAULTS_PER_ASSET]
    stakersPointsAlloc: uint256
    voterPointsAlloc: uint256
    perUserDepositLimit: uint256
    globalDepositLimit: uint256
    debtTerms: DebtTerms
    shouldBurnAsPayment: bool
    shouldTransferToEndaoment: bool
    shouldSwapInStabPools: bool
    shouldAuctionInstantly: bool
    canDeposit: bool
    canWithdraw: bool
    canRedeemCollateral: bool
    canRedeemInStabPool: bool
    canBuyInAuction: bool
    canClaimInStabPool: bool
    specialStabPoolId: uint256
    customAuctionParams: AuctionParams
    whitelist: address
    isNft: bool

struct RipeRewardsConfig:
    arePointsEnabled: bool
    ripePerBlock: uint256
    borrowersAlloc: uint256
    stakersAlloc: uint256
    votersAlloc: uint256
    genDepositorsAlloc: uint256

struct DebtTerms:
    ltv: uint256
    redemptionThreshold: uint256
    liqThreshold: uint256
    liqFee: uint256
    borrowRate: uint256
    daowry: uint256

struct AuctionParams:
    hasParams: bool
    startDiscount: uint256
    maxDiscount: uint256
    delay: uint256
    duration: uint256

struct VaultLite:
    vaultId: uint256
    asset: address

event PriorityLiqAssetVaultsSet:
    numVaults: uint256

event PriorityStabVaultsSet:
    numVaults: uint256

event RewardsPointsEnabledModified:
    arePointsEnabled: bool
    caller: indexed(address)

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

event IsDaowryEnabledSet:
    isDaowryEnabled: bool
    caller: indexed(address)

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
):
    gov.__init__(_ripeHq, empty(address), 0, 0, 0)
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, False, False) # no minting

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


@external
def setGeneralConfig(
    _perUserMaxVaults: uint256,
    _perUserMaxAssetsPerVault: uint256,
    _priceStaleTime: uint256,
    _canDeposit: bool,
    _canWithdraw: bool,
    _canBorrow: bool,
    _canRepay: bool,
    _canClaimLoot: bool,
    _canLiquidate: bool,
    _canRedeemCollateral: bool,
    _canRedeemInStabPool: bool,
    _canBuyInAuction: bool,
    _canClaimInStabPool: bool,
) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused

    # TODO: add time lock

    mc: address = addys._getMissionControlAddr()
    config: GenConfig = staticcall MissionControl(mc).genConfig()
    assert self._areValidVaultLimits(_perUserMaxVaults, _perUserMaxAssetsPerVault, max_value(uint256), max_value(uint256)) # dev: invalid vault limits
    assert self._isValidStaleTime(_priceStaleTime, max_value(uint256)) # dev: invalid stale time

    config.perUserMaxVaults = _perUserMaxVaults
    config.perUserMaxAssetsPerVault = _perUserMaxAssetsPerVault
    config.priceStaleTime = _priceStaleTime
    config.canDeposit = _canDeposit
    config.canWithdraw = _canWithdraw
    config.canBorrow = _canBorrow
    config.canRepay = _canRepay
    config.canClaimLoot = _canClaimLoot
    config.canLiquidate = _canLiquidate
    config.canRedeemCollateral = _canRedeemCollateral
    config.canRedeemInStabPool = _canRedeemInStabPool
    config.canBuyInAuction = _canBuyInAuction
    config.canClaimInStabPool = _canClaimInStabPool
    extcall MissionControl(mc).setGeneralConfig(config)
    return True


# vault limits


@external
def setVaultLimits(_perUserMaxVaults: uint256, _perUserMaxAssetsPerVault: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused

    # TODO: add time lock

    mc: address = addys._getMissionControlAddr()
    config: GenConfig = staticcall MissionControl(mc).genConfig()
    assert self._areValidVaultLimits(_perUserMaxVaults, _perUserMaxAssetsPerVault, config.perUserMaxVaults, config.perUserMaxAssetsPerVault) # dev: invalid vault limits
    config.perUserMaxVaults = _perUserMaxVaults
    config.perUserMaxAssetsPerVault = _perUserMaxAssetsPerVault
    extcall MissionControl(mc).setGeneralConfig(config)

    log VaultLimitsSet(perUserMaxVaults=_perUserMaxVaults, perUserMaxAssetsPerVault=_perUserMaxAssetsPerVault)
    return True


@view
@internal
def _areValidVaultLimits(
    _perUserMaxVaults: uint256,
    _perUserMaxAssetsPerVault: uint256,
    _prevPerUserMaxVaults: uint256,
    _prevPerUserMaxAssetsPerVault: uint256,
) -> bool:
    if _perUserMaxVaults == _prevPerUserMaxVaults and _perUserMaxAssetsPerVault == _prevPerUserMaxAssetsPerVault:
        return False
    if 0 in [_perUserMaxVaults, _perUserMaxAssetsPerVault]:
        return False
    if max_value(uint256) in [_perUserMaxVaults, _perUserMaxAssetsPerVault]:
        return False
    return True


# stale time for prices


@external
def setStaleTime(_staleTime: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: not activated

    mc: address = addys._getMissionControlAddr()
    config: GenConfig = staticcall MissionControl(mc).genConfig()
    assert self._isValidStaleTime(_staleTime, config.priceStaleTime) # dev: invalid stale time
    config.priceStaleTime = _staleTime
    extcall MissionControl(mc).setGeneralConfig(config)

    log StaleTimeSet(staleTime=_staleTime)
    return True


@view
@internal
def _isValidStaleTime(_staleTime: uint256, _prevStaleTime: uint256) -> bool:
    if _staleTime == _prevStaleTime:
        return False
    return _staleTime >= MIN_STALE_TIME and _staleTime <= MAX_STALE_TIME


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


@external
def setGeneralDebtConfig(
    _perUserDebtLimit: uint256,
    _globalDebtLimit: uint256,
    _minDebtAmount: uint256,
    _numAllowedBorrowers: uint256,
    _maxBorrowPerInterval: uint256,
    _numBlocksPerInterval: uint256,
    _keeperFeeRatio: uint256,
    _minKeeperFee: uint256,
    _isDaowryEnabled: bool,
    _ltvPaybackBuffer: uint256,
    _genAuctionParams: AuctionParams,
) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused

    # TODO: add time lock

    assert self._areValidDebtLimits(_perUserDebtLimit, _globalDebtLimit, _minDebtAmount, _numAllowedBorrowers) # dev: invalid debt limits
    assert self._areValidBorrowIntervalConfig(_maxBorrowPerInterval, _numBlocksPerInterval, _minDebtAmount) # dev: invalid borrow interval config
    assert self._isValidKeeperConfig(_keeperFeeRatio, _minKeeperFee) # dev: invalid keeper config
    assert self._isValidLtvPaybackBuffer(_ltvPaybackBuffer) # dev: invalid ltv payback buffer
    assert self._areValidAuctionParams(_genAuctionParams) # dev: invalid auction params

    genDebtConfig: GenDebtConfig = GenDebtConfig(
        perUserDebtLimit=_perUserDebtLimit,
        globalDebtLimit=_globalDebtLimit,
        minDebtAmount=_minDebtAmount,
        numAllowedBorrowers=_numAllowedBorrowers,
        maxBorrowPerInterval=_maxBorrowPerInterval,
        numBlocksPerInterval=_numBlocksPerInterval,
        keeperFeeRatio=_keeperFeeRatio,
        minKeeperFee=_minKeeperFee,
        isDaowryEnabled=_isDaowryEnabled,
        ltvPaybackBuffer=_ltvPaybackBuffer,
        genAuctionParams=_genAuctionParams,
    )
    extcall MissionControl(addys._getMissionControlAddr()).setGeneralDebtConfig(genDebtConfig)
    return True


# global debt limits


@external
def setGlobalDebtLimits(
    _perUserDebtLimit: uint256,
    _globalDebtLimit: uint256,
    _minDebtAmount: uint256,
    _numAllowedBorrowers: uint256,
) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused

    # TODO: add time lock

    assert self._areValidDebtLimits(_perUserDebtLimit, _globalDebtLimit, _minDebtAmount, _numAllowedBorrowers) # dev: invalid debt limits
    mc: address = addys._getMissionControlAddr()
    config: GenDebtConfig = staticcall MissionControl(mc).genDebtConfig()
    config.perUserDebtLimit = _perUserDebtLimit
    config.globalDebtLimit = _globalDebtLimit
    config.minDebtAmount = _minDebtAmount
    config.numAllowedBorrowers = _numAllowedBorrowers
    extcall MissionControl(mc).setGeneralDebtConfig(config)

    log GlobalDebtLimitsSet(perUserDebtLimit=_perUserDebtLimit, globalDebtLimit=_globalDebtLimit, minDebtAmount=_minDebtAmount, numAllowedBorrowers=_numAllowedBorrowers)
    return True


@view
@internal
def _areValidDebtLimits(
    _perUserDebtLimit: uint256,
    _globalDebtLimit: uint256,
    _minDebtAmount: uint256,
    _numAllowedBorrowers: uint256,
) -> bool:
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
def setBorrowIntervalConfig(
    _maxBorrowPerInterval: uint256,
    _numBlocksPerInterval: uint256,
) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused

    # TODO: add time lock

    mc: address = addys._getMissionControlAddr()
    config: GenDebtConfig = staticcall MissionControl(mc).genDebtConfig()
    assert self._areValidBorrowIntervalConfig(_maxBorrowPerInterval, _numBlocksPerInterval, config.minDebtAmount) # dev: invalid borrow interval config
    config.maxBorrowPerInterval = _maxBorrowPerInterval
    config.numBlocksPerInterval = _numBlocksPerInterval
    extcall MissionControl(mc).setGeneralDebtConfig(config)

    log BorrowIntervalConfigSet(maxBorrowPerInterval=_maxBorrowPerInterval, numBlocksPerInterval=_numBlocksPerInterval)
    return True


@view
@internal
def _areValidBorrowIntervalConfig(
    _maxBorrowPerInterval: uint256,
    _numBlocksPerInterval: uint256,
    _minDebtAmount: uint256,
) -> bool:
    if 0 in [_maxBorrowPerInterval, _numBlocksPerInterval]:
        return False
    if max_value(uint256) in [_maxBorrowPerInterval, _numBlocksPerInterval]:
        return False
    if _maxBorrowPerInterval < _minDebtAmount:
        return False
    return True


# keeper config


@external
def setKeeperConfig(
    _keeperFeeRatio: uint256,
    _minKeeperFee: uint256,
) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused

    # TODO: add time lock

    assert self._isValidKeeperConfig(_keeperFeeRatio, _minKeeperFee) # dev: invalid keeper config
    mc: address = addys._getMissionControlAddr()
    config: GenDebtConfig = staticcall MissionControl(mc).genDebtConfig()
    config.keeperFeeRatio = _keeperFeeRatio
    config.minKeeperFee = _minKeeperFee
    extcall MissionControl(mc).setGeneralDebtConfig(config)

    log KeeperConfigSet(keeperFeeRatio=_keeperFeeRatio, minKeeperFee=_minKeeperFee)
    return True


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


# ltv payback buffer


@external
def setLtvPaybackBuffer(_ltvPaybackBuffer: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused

    # TODO: add time lock

    assert self._isValidLtvPaybackBuffer(_ltvPaybackBuffer) # dev: invalid ltv payback buffer
    mc: address = addys._getMissionControlAddr()
    config: GenDebtConfig = staticcall MissionControl(mc).genDebtConfig()
    config.ltvPaybackBuffer = _ltvPaybackBuffer
    extcall MissionControl(mc).setGeneralDebtConfig(config)

    log LtvPaybackBufferSet(ltvPaybackBuffer=_ltvPaybackBuffer)
    return True


@view
@internal
def _isValidLtvPaybackBuffer(_ltvPaybackBuffer: uint256) -> bool:
    if _ltvPaybackBuffer == 0:
        return False
    if _ltvPaybackBuffer > 10_00: # 10% max
        return False
    return True


# gen auction params


@external
def setGenAuctionParams(
    _startDiscount: uint256,
    _maxDiscount: uint256,
    _delay: uint256,
    _duration: uint256,
) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused

    # TODO: add time lock

    params: AuctionParams= AuctionParams(
        hasParams=True,
        startDiscount=_startDiscount,
        maxDiscount=_maxDiscount,
        delay=_delay,
        duration=_duration,
    )
    assert self._areValidAuctionParams(params) # dev: invalid auction params

    mc: address = addys._getMissionControlAddr()
    config: GenDebtConfig = staticcall MissionControl(mc).genDebtConfig()
    config.genAuctionParams = params
    extcall MissionControl(mc).setGeneralDebtConfig(config)

    log GenAuctionParamsSet(startDiscount=_startDiscount, maxDiscount=_maxDiscount, delay=_delay, duration=_duration)
    return True


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


################
# Asset Config #
################


@external
def setAssetConfig(
    _asset: address,
    _vaultIds: DynArray[uint256, MAX_VAULTS_PER_ASSET],
    _stakersPointsAlloc: uint256,
    _voterPointsAlloc: uint256,
    _perUserDepositLimit: uint256,
    _globalDepositLimit: uint256,
    _debtTerms: DebtTerms,
    _shouldBurnAsPayment: bool,
    _shouldTransferToEndaoment: bool,
    _shouldSwapInStabPools: bool,
    _shouldAuctionInstantly: bool,
    _canDeposit: bool,
    _canWithdraw: bool,
    _canRedeemCollateral: bool,
    _canRedeemInStabPool: bool,
    _canBuyInAuction: bool,
    _canClaimInStabPool: bool,
    _specialStabPoolId: uint256,
    _customAuctionParams: AuctionParams,
    _whitelist: address,
    _isNft: bool,
) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused

    # TODO: add time lock, validation

    mc: address = addys._getMissionControlAddr()
    assetConfig: AssetConfig = AssetConfig(
        vaultIds=_vaultIds,
        stakersPointsAlloc=_stakersPointsAlloc,
        voterPointsAlloc=_voterPointsAlloc,
        perUserDepositLimit=_perUserDepositLimit,
        globalDepositLimit=_globalDepositLimit,
        debtTerms=_debtTerms,
        shouldBurnAsPayment=_shouldBurnAsPayment,
        shouldTransferToEndaoment=_shouldTransferToEndaoment,
        shouldSwapInStabPools=_shouldSwapInStabPools,
        shouldAuctionInstantly=_shouldAuctionInstantly,
        canDeposit=_canDeposit,
        canWithdraw=_canWithdraw,
        canRedeemCollateral=_canRedeemCollateral,
        canRedeemInStabPool=_canRedeemInStabPool,
        canBuyInAuction=_canBuyInAuction,
        canClaimInStabPool=_canClaimInStabPool,
        specialStabPoolId=_specialStabPoolId,
        customAuctionParams=_customAuctionParams,
        whitelist=_whitelist,
        isNft=_isNft,
    )
    extcall MissionControl(mc).setAssetConfig(_asset, assetConfig)
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
    for vault: VaultLite in _priorityVaults:
        if self.vaultDedupe[vault.vaultId][vault.asset]:
            continue
        if not staticcall VaultBook(vaultBook).isValidRegId(vault.vaultId):
            continue

        # TODO: once asset config is complete do a check here that asset is supported by vault

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


####################
# Rewards / Points #
####################


@external
def setRipeRewardsConfig(
    _arePointsEnabled: bool,
    _ripePerBlock: uint256,
    _borrowersAlloc: uint256,
    _stakersAlloc: uint256,
    _votersAlloc: uint256,
    _genDepositorsAlloc: uint256,
) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused

    # TODO: add time lock

    rewardsConfig: RipeRewardsConfig = RipeRewardsConfig(
        arePointsEnabled=_arePointsEnabled,
        ripePerBlock=_ripePerBlock,
        borrowersAlloc=_borrowersAlloc,
        stakersAlloc=_stakersAlloc,
        votersAlloc=_votersAlloc,
        genDepositorsAlloc=_genDepositorsAlloc,
    )
    extcall MissionControl(addys._getMissionControlAddr()).setRipeRewardsConfig(rewardsConfig)
    return True


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
