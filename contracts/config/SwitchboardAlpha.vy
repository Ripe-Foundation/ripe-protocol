#        ______   __     __   __   ______  ______   __  __   ______   ______   ______   ______   _____    
#       /\  ___\ /\ \  _ \ \ /\ \ /\__  _\/\  ___\ /\ \_\ \ /\  == \ /\  __ \ /\  __ \ /\  == \ /\  __-.  
#       \ \___  \\ \ \/ ".\ \\ \ \\/_/\ \/\ \ \____\ \  __ \\ \  __< \ \ \/\ \\ \  __ \\ \  __< \ \ \/\ \ 
#        \/\_____\\ \__/".~\_\\ \_\  \ \_\ \ \_____\\ \_\ \_\\ \_____\\ \_____\\ \_\ \_\\ \_\ \_\\ \____- 
#         \/_____/ \/_/   \/_/ \/_/   \/_/  \/_____/ \/_/\/_/ \/_____/ \/_____/ \/_/\/_/ \/_/ /_/ \/____/ 
#                                                  ┏┓┓  ┓   
#                                                  ┣┫┃┏┓┣┓┏┓
#                                                  ┛┗┗┣┛┛┗┗┻
#                                                     ┛     
#      Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
#      Ripe Foundation (C) 2025 

# @version 0.4.3
# pragma optimize codesize

exports: gov.__interface__
exports: timeLock.__interface__

initializes: gov
initializes: timeLock[gov := gov]

import contracts.modules.LocalGov as gov
import contracts.modules.TimeLock as timeLock
from interfaces import Vault
import interfaces.ConfigStructs as cs

interface MissionControl:
    def setRipeGovVaultConfig(_asset: address, _assetWeight: uint256, _shouldFreezeWhenBadDebt: bool, _lockTerms: cs.LockTerms): nonpayable
    def setPriorityLiqAssetVaults(_priorityLiqAssetVaults: DynArray[cs.VaultLite, PRIORITY_VAULT_DATA]): nonpayable
    def setPriorityStabVaults(_priorityStabVaults: DynArray[cs.VaultLite, PRIORITY_VAULT_DATA]): nonpayable
    def setPriorityPriceSourceIds(_priorityIds: DynArray[uint256, MAX_PRIORITY_PRICE_SOURCES]): nonpayable
    def isSupportedAssetInVault(_vaultId: uint256, _asset: address) -> bool: view
    def setRipeRewardsConfig(_rewardsConfig: cs.RipeRewardsConfig): nonpayable
    def setCanPerformLiteAction(_user: address, _canDisable: bool): nonpayable
    def setGeneralDebtConfig(_genDebtConfig: cs.GenDebtConfig): nonpayable
    def setUnderscoreRegistry(_underscoreRegistry: address): nonpayable
    def setShouldCheckLastTouch(_shouldCheck: bool): nonpayable
    def setGeneralConfig(_genConfig: cs.GenConfig): nonpayable
    def canPerformLiteAction(_user: address) -> bool: view
    def isSupportedAsset(_asset: address) -> bool: view
    def rewardsConfig() -> cs.RipeRewardsConfig: view
    def genDebtConfig() -> cs.GenDebtConfig: view
    def underscoreRegistry() -> address: view
    def shouldCheckLastTouch() -> bool: view
    def genConfig() -> cs.GenConfig: view

interface Ledger:
    def setRipeAvailForRewards(_amount: uint256): nonpayable
    def setRipeAvailForBonds(_amount: uint256): nonpayable
    def setRipeAvailForHr(_amount: uint256): nonpayable

interface VaultBook:
    def isValidRegId(_regId: uint256) -> bool: view
    def getAddr(_regId: uint256) -> address: view

interface CreditEngine:
    def setUnderscoreVaultDiscount(_discount: uint256): nonpayable
    def setBuybackRatio(_ratio: uint256): nonpayable

interface PriceDesk:
    def isValidRegId(_regId: uint256) -> bool: view

interface UnderscoreLedger:
    def isUserWallet(_addr: address) -> bool: view

interface UnderscoreRegistry:
    def getAddr(_addyId: uint256) -> address: view

interface RipeHq:
    def getAddr(_regId: uint256) -> address: view

flag ActionType:
    GEN_CONFIG_VAULT_LIMITS
    GEN_CONFIG_STALE_TIME
    DEBT_GLOBAL_LIMITS
    DEBT_BORROW_INTERVAL
    DEBT_DYNAMIC_RATE_CONFIG
    DEBT_MAX_LTV_DEVIATION
    DEBT_KEEPER_CONFIG
    DEBT_LTV_PAYBACK_BUFFER
    DEBT_AUCTION_PARAMS
    RIPE_REWARDS_BLOCK
    RIPE_REWARDS_ALLOCS
    RIPE_REWARDS_AUTO_STAKE_PARAMS
    RIPE_AVAIL_REWARDS
    RIPE_AVAIL_HR
    RIPE_AVAIL_BONDS
    OTHER_PRIORITY_LIQ_ASSET_VAULTS
    OTHER_PRIORITY_STAB_VAULTS
    OTHER_PRIORITY_PRICE_SOURCE_IDS
    OTHER_UNDERSCORE_REGISTRY
    OTHER_CAN_PERFORM_LITE_ACTION
    OTHER_SHOULD_CHECK_LAST_TOUCH
    RIPE_VAULT_CONFIG
    DEBT_UNDY_VAULT_DISCOUNT
    DEBT_BUYBACK_RATIO

flag GenConfigFlag:
    CAN_DEPOSIT
    CAN_WITHDRAW
    CAN_BORROW
    CAN_REPAY
    CAN_CLAIM_LOOT
    CAN_LIQUIDATE
    CAN_REDEEM_COLLATERAL
    CAN_REDEEM_IN_STAB_POOL
    CAN_BUY_IN_AUCTION
    CAN_CLAIM_IN_STAB_POOL

struct GenConfigLite:
    perUserMaxVaults: uint256
    perUserMaxAssetsPerVault: uint256
    priceStaleTime: uint256

struct CanPerform:
    user: address
    canDo: bool

struct PendingRipeGovVaultConfig:
    asset: address
    assetWeight: uint256
    shouldFreezeWhenBadDebt: bool
    lockTerms: cs.LockTerms

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

event PendingDynamicRateConfigChange:
    minDynamicRateBoost: uint256
    maxDynamicRateBoost: uint256
    increasePerDangerBlock: uint256
    maxBorrowRate: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingKeeperConfigChange:
    keeperFeeRatio: uint256
    minKeeperFee: uint256
    maxKeeperFee: uint256
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

event PendingUndyVaultDiscountChange:
    discount: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingBuybackRatioChange:
    ratio: uint256
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

event PendingRipeRewardsAutoStakeParamsChange:
    autoStakeRatio: uint256
    autoStakeDurationRatio: uint256
    stabPoolRipePerDollarClaimed: uint256
    confirmationBlock: uint256
    actionId: uint256

event RewardsPointsEnabledModified:
    arePointsEnabled: bool
    caller: indexed(address)

event PendingRipeAvailableForRewardsChange:
    amount: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingRipeAvailableForHrChange:
    amount: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingRipeAvailableForBondsChange:
    amount: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingPriorityLiqAssetVaultsChange:
    numPriorityLiqAssetVaults: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingPriorityStabVaultsChange:
    numPriorityStabVaults: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingPriorityPriceSourceIdsChange:
    numPriorityPriceSourceIds: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingUnderscoreRegistryChange:
    underscoreRegistry: address
    confirmationBlock: uint256
    actionId: uint256

event PendingCanPerformLiteAction:
    user: address
    canDo: bool
    confirmationBlock: uint256
    actionId: uint256

event PendingShouldCheckLastTouchChange:
    shouldCheck: bool
    confirmationBlock: uint256
    actionId: uint256

event PendingMaxLtvDeviationChange:
    newDeviation: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingRipeGovVaultConfigChange:
    asset: address
    assetWeight: uint256
    shouldFreezeWhenBadDebt: bool
    minLockDuration: uint256
    maxLockDuration: uint256
    maxLockBoost: uint256
    canExit: bool
    exitFee: uint256
    confirmationBlock: uint256
    actionId: uint256

event VaultLimitsSet:
    perUserMaxVaults: uint256
    perUserMaxAssetsPerVault: uint256

event StaleTimeSet:
    staleTime: uint256

event GlobalDebtLimitsSet:
    perUserDebtLimit: uint256
    globalDebtLimit: uint256
    minDebtAmount: uint256
    numAllowedBorrowers: uint256

event BorrowIntervalConfigSet:
    maxBorrowPerInterval: uint256
    numBlocksPerInterval: uint256

event DynamicRateConfigSet:
    minDynamicRateBoost: uint256
    maxDynamicRateBoost: uint256
    increasePerDangerBlock: uint256
    maxBorrowRate: uint256

event KeeperConfigSet:
    keeperFeeRatio: uint256
    minKeeperFee: uint256
    maxKeeperFee: uint256

event LtvPaybackBufferSet:
    ltvPaybackBuffer: uint256

event GenAuctionParamsSet:
    startDiscount: uint256
    maxDiscount: uint256
    delay: uint256
    duration: uint256

event UndyVaultDiscountSet:
    discount: uint256

event BuybackRatioSet:
    ratio: uint256

event RipeRewardsPerBlockSet:
    ripePerBlock: uint256

event RipeRewardsAllocsSet:
    borrowersAlloc: uint256
    stakersAlloc: uint256
    votersAlloc: uint256
    genDepositorsAlloc: uint256

event RipeRewardsAutoStakeParamsSet:
    autoStakeRatio: uint256
    autoStakeDurationRatio: uint256
    stabPoolRipePerDollarClaimed: uint256

event RipeAvailableForRewardsSet:
    amount: uint256

event RipeAvailableForHrSet:
    amount: uint256

event RipeAvailableForBondsSet:
    amount: uint256

event PriorityLiqAssetVaultsSet:
    numVaults: uint256

event PriorityStabVaultsSet:
    numVaults: uint256

event PriorityPriceSourceIdsModified:
    numIds: uint256

event UnderscoreRegistrySet:
    addr: indexed(address)

event CanPerformLiteAction:
    user: indexed(address)
    canDo: bool

event ShouldCheckLastTouchSet:
    shouldCheck: bool

event MaxLtvDeviationSet:
    newDeviation: uint256

event RipeGovVaultConfigSet:
    asset: address
    assetWeight: uint256
    shouldFreezeWhenBadDebt: bool
    minLockDuration: uint256
    maxLockDuration: uint256
    maxLockBoost: uint256
    canExit: bool
    exitFee: uint256

# pending config changes
actionType: public(HashMap[uint256, ActionType]) # aid -> type
pendingRipeRewardsConfig: public(HashMap[uint256, cs.RipeRewardsConfig]) # aid -> config
pendingGeneralConfig: public(HashMap[uint256, GenConfigLite]) # aid -> config
pendingDebtConfig: public(HashMap[uint256, cs.GenDebtConfig]) # aid -> config
pendingUndyVaultDiscount: public(HashMap[uint256, uint256]) # aid -> discount
pendingBuybackRatio: public(HashMap[uint256, uint256]) # aid -> ratio
pendingPriorityLiqAssetVaults: public(HashMap[uint256, DynArray[cs.VaultLite, PRIORITY_VAULT_DATA]])
pendingPriorityStabVaults: public(HashMap[uint256, DynArray[cs.VaultLite, PRIORITY_VAULT_DATA]])
pendingPriorityPriceSourceIds: public(HashMap[uint256, DynArray[uint256, MAX_PRIORITY_PRICE_SOURCES]])
pendingUnderscoreRegistry: public(HashMap[uint256, address])
pendingCanPerformLiteAction: public(HashMap[uint256, CanPerform])
pendingShouldCheckLastTouch: public(HashMap[uint256, bool])
pendingRipeGovVaultConfig: public(HashMap[uint256, PendingRipeGovVaultConfig]) # aid -> config
pendingRipeAvailable: public(HashMap[uint256, uint256]) # aid -> amount

# temp data
vaultDedupe: transient(HashMap[uint256, HashMap[address, bool]]) # vault id -> asset

MIN_STALE_TIME: public(immutable(uint256))
MAX_STALE_TIME: public(immutable(uint256))

MAX_PRIORITY_PRICE_SOURCES: constant(uint256) = 10
PRIORITY_VAULT_DATA: constant(uint256) = 20
UNDERSCORE_LEDGER_ID: constant(uint256) = 1
HUNDRED_PERCENT: constant(uint256) = 100_00 # 100%
EIGHTEEN_DECIMALS: constant(uint256) = 10 ** 18

LEDGER_ID: constant(uint256) = 4
MISSION_CONTROL_ID: constant(uint256) = 5
PRICE_DESK_ID: constant(uint256) = 7
VAULT_BOOK_ID: constant(uint256) = 8
CREDIT_ENGINE_ID: constant(uint256) = 13


@deploy
def __init__(
    _ripeHq: address,
    _tempGov: address,
    _minStaleTime: uint256,
    _maxStaleTime: uint256,
    _minConfigTimeLock: uint256,
    _maxConfigTimeLock: uint256,
):
    gov.__init__(_ripeHq, _tempGov, 0, 0, 0)
    timeLock.__init__(_minConfigTimeLock, _maxConfigTimeLock, 0, _maxConfigTimeLock)

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
        return staticcall MissionControl(self._getMissionControlAddr()).canPerformLiteAction(_caller)
    return False


# addys lite


@view
@internal
def _getMissionControlAddr() -> address:
    return staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(MISSION_CONTROL_ID)


@view
@internal
def _getPriceDeskAddr() -> address:
    return staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(PRICE_DESK_ID)


@view
@internal
def _getVaultBookAddr() -> address:
    return staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(VAULT_BOOK_ID)


@view
@internal
def _getLedgerAddr() -> address:
    return staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(LEDGER_ID)


@view
@internal
def _getCreditEngineAddr() -> address:
    return staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(CREDIT_ENGINE_ID)


##################
# General Config #
##################


# vault limits


@external
def setVaultLimits(_perUserMaxVaults: uint256, _perUserMaxAssetsPerVault: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

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
    return self._setGenConfigFlag(GenConfigFlag.CAN_DEPOSIT, _shouldEnable)


@external
def setCanWithdraw(_shouldEnable: bool) -> bool:
    return self._setGenConfigFlag(GenConfigFlag.CAN_WITHDRAW, _shouldEnable)


@external
def setCanBorrow(_shouldEnable: bool) -> bool:
    return self._setGenConfigFlag(GenConfigFlag.CAN_BORROW, _shouldEnable)


@external
def setCanRepay(_shouldEnable: bool) -> bool:
    return self._setGenConfigFlag(GenConfigFlag.CAN_REPAY, _shouldEnable)


@external
def setCanClaimLoot(_shouldEnable: bool) -> bool:
    return self._setGenConfigFlag(GenConfigFlag.CAN_CLAIM_LOOT, _shouldEnable)


@external
def setCanLiquidate(_shouldEnable: bool) -> bool:
    return self._setGenConfigFlag(GenConfigFlag.CAN_LIQUIDATE, _shouldEnable)


@external
def setCanRedeemCollateral(_shouldEnable: bool) -> bool:
    return self._setGenConfigFlag(GenConfigFlag.CAN_REDEEM_COLLATERAL, _shouldEnable)


@external
def setCanRedeemInStabPool(_shouldEnable: bool) -> bool:
    return self._setGenConfigFlag(GenConfigFlag.CAN_REDEEM_IN_STAB_POOL, _shouldEnable)


@external
def setCanBuyInAuction(_shouldEnable: bool) -> bool:
    return self._setGenConfigFlag(GenConfigFlag.CAN_BUY_IN_AUCTION, _shouldEnable)


@external
def setCanClaimInStabPool(_shouldEnable: bool) -> bool:
    return self._setGenConfigFlag(GenConfigFlag.CAN_CLAIM_IN_STAB_POOL, _shouldEnable)


@internal
def _setGenConfigFlag(_flag: GenConfigFlag, _shouldEnable: bool) -> bool:
    assert self._hasPermsToEnable(msg.sender, _shouldEnable) # dev: no perms

    mc: address = self._getMissionControlAddr()
    config: cs.GenConfig = staticcall MissionControl(mc).genConfig()
    
    # get current value and validate
    if _flag == GenConfigFlag.CAN_DEPOSIT:
        assert config.canDeposit != _shouldEnable # dev: already set
        config.canDeposit = _shouldEnable
        log CanDepositSet(canDeposit=_shouldEnable, caller=msg.sender)

    elif _flag == GenConfigFlag.CAN_WITHDRAW:
        assert config.canWithdraw != _shouldEnable # dev: already set
        config.canWithdraw = _shouldEnable
        log CanWithdrawSet(canWithdraw=_shouldEnable, caller=msg.sender)

    elif _flag == GenConfigFlag.CAN_BORROW:
        assert config.canBorrow != _shouldEnable # dev: already set
        config.canBorrow = _shouldEnable
        log CanBorrowSet(canBorrow=_shouldEnable, caller=msg.sender)

    elif _flag == GenConfigFlag.CAN_REPAY:
        assert config.canRepay != _shouldEnable # dev: already set
        config.canRepay = _shouldEnable
        log CanRepaySet(canRepay=_shouldEnable, caller=msg.sender)

    elif _flag == GenConfigFlag.CAN_CLAIM_LOOT:
        assert config.canClaimLoot != _shouldEnable # dev: already set
        config.canClaimLoot = _shouldEnable
        log CanClaimLootSet(canClaimLoot=_shouldEnable, caller=msg.sender)

    elif _flag == GenConfigFlag.CAN_LIQUIDATE:
        assert config.canLiquidate != _shouldEnable # dev: already set
        config.canLiquidate = _shouldEnable
        log CanLiquidateSet(canLiquidate=_shouldEnable, caller=msg.sender)

    elif _flag == GenConfigFlag.CAN_REDEEM_COLLATERAL:
        assert config.canRedeemCollateral != _shouldEnable # dev: already set
        config.canRedeemCollateral = _shouldEnable
        log CanRedeemCollateralSet(canRedeemCollateral=_shouldEnable, caller=msg.sender)

    elif _flag == GenConfigFlag.CAN_REDEEM_IN_STAB_POOL:
        assert config.canRedeemInStabPool != _shouldEnable # dev: already set
        config.canRedeemInStabPool = _shouldEnable
        log CanRedeemInStabPoolSet(canRedeemInStabPool=_shouldEnable, caller=msg.sender)

    elif _flag == GenConfigFlag.CAN_BUY_IN_AUCTION:
        assert config.canBuyInAuction != _shouldEnable # dev: already set
        config.canBuyInAuction = _shouldEnable
        log CanBuyInAuctionSet(canBuyInAuction=_shouldEnable, caller=msg.sender)

    elif _flag == GenConfigFlag.CAN_CLAIM_IN_STAB_POOL:
        assert config.canClaimInStabPool != _shouldEnable # dev: already set
        config.canClaimInStabPool = _shouldEnable
        log CanClaimInStabPoolSet(canClaimInStabPool=_shouldEnable, caller=msg.sender)
    
    extcall MissionControl(mc).setGeneralConfig(config)
    return True


###############
# Debt Config #
###############


# global debt limits


@external
def setGlobalDebtLimits(_perUserDebtLimit: uint256, _globalDebtLimit: uint256, _minDebtAmount: uint256, _numAllowedBorrowers: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

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

    assert self._areValidBorrowIntervalConfig(_maxBorrowPerInterval, _numBlocksPerInterval) # dev: invalid borrow interval config
    return self._setPendingDebtConfig(ActionType.DEBT_BORROW_INTERVAL, 0, 0, 0, 0, _maxBorrowPerInterval, _numBlocksPerInterval)


@view
@internal
def _areValidBorrowIntervalConfig(_maxBorrowPerInterval: uint256, _numBlocksPerInterval: uint256) -> bool:
    if 0 in [_maxBorrowPerInterval, _numBlocksPerInterval]:
        return False
    if max_value(uint256) in [_maxBorrowPerInterval, _numBlocksPerInterval]:
        return False
    config: cs.GenDebtConfig = staticcall MissionControl(self._getMissionControlAddr()).genDebtConfig()
    if _maxBorrowPerInterval < config.minDebtAmount:
        return False
    return True


# dynamic rate config


@external
def setDynamicRateConfig(_minDynamicRateBoost: uint256, _maxDynamicRateBoost: uint256, _increasePerDangerBlock: uint256, _maxBorrowRate: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert self._isValidDynamicRateConfig(_minDynamicRateBoost, _maxDynamicRateBoost, _increasePerDangerBlock, _maxBorrowRate) # dev: invalid dynamic rate config
    return self._setPendingDebtConfig(ActionType.DEBT_DYNAMIC_RATE_CONFIG, 0, 0, 0, 0, 0, 0, _minDynamicRateBoost, _maxDynamicRateBoost, _increasePerDangerBlock, _maxBorrowRate)


@view
@internal
def _isValidDynamicRateConfig(_minDynamicRateBoost: uint256, _maxDynamicRateBoost: uint256, _increasePerDangerBlock: uint256, _maxBorrowRate: uint256) -> bool:
    # NOTE: denominator for `_increasePerDangerBlock` is 100_0000 (100.0000%)

    if 0 in [_minDynamicRateBoost, _maxDynamicRateBoost, _increasePerDangerBlock, _maxBorrowRate]:
        return False
    if max_value(uint256) in [_minDynamicRateBoost, _maxDynamicRateBoost, _increasePerDangerBlock, _maxBorrowRate]:
        return False
    if _minDynamicRateBoost > _maxDynamicRateBoost:
        return False
    if _maxDynamicRateBoost > 1000_00: # 1000% max
        return False
    if _maxBorrowRate > 200_00: # 200% max
        return False
    return True


# max ltv deviation


@external
def setMaxLtvDeviation(_newDeviation: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    assert self._isValidMaxDeviation(_newDeviation) # dev: invalid max deviation
    return self._setPendingDebtConfig(ActionType.DEBT_MAX_LTV_DEVIATION, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, _newDeviation)


@view
@internal
def _isValidMaxDeviation(_newDeviation: uint256) -> bool:
    if _newDeviation == 0:
        return False
    return _newDeviation <= HUNDRED_PERCENT


# keeper config


@external
def setKeeperConfig(
    _keeperFeeRatio: uint256,
    _minKeeperFee: uint256,
    _maxKeeperFee: uint256,
) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    assert self._isValidKeeperConfig(_keeperFeeRatio, _minKeeperFee, _maxKeeperFee) # dev: invalid keeper config
    return self._setPendingDebtConfig(ActionType.DEBT_KEEPER_CONFIG, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, _keeperFeeRatio, _minKeeperFee, _maxKeeperFee)


@view
@internal
def _isValidKeeperConfig(_keeperFeeRatio: uint256, _minKeeperFee: uint256, _maxKeeperFee: uint256) -> bool:
    if max_value(uint256) in [_keeperFeeRatio, _minKeeperFee, _maxKeeperFee]:
        return False
    if _keeperFeeRatio > 10_00: # 10% max
        return False
    if _minKeeperFee > _maxKeeperFee:
        return False
    if _minKeeperFee > 200 * EIGHTEEN_DECIMALS: # $200 max
        return False
    if _maxKeeperFee > 100_000 * EIGHTEEN_DECIMALS: # 100k max
        return False
    return True


# ltv payback buffer


@external
def setLtvPaybackBuffer(_ltvPaybackBuffer: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    assert self._isValidLtvPaybackBuffer(_ltvPaybackBuffer) # dev: invalid ltv payback buffer
    return self._setPendingDebtConfig(ActionType.DEBT_LTV_PAYBACK_BUFFER, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, _ltvPaybackBuffer)


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

    params: cs.AuctionParams= cs.AuctionParams(
        hasParams=True,
        startDiscount=_startDiscount,
        maxDiscount=_maxDiscount,
        delay=_delay,
        duration=_duration,
    )
    assert self._areValidAuctionParams(params) # dev: invalid auction params
    return self._setPendingDebtConfig(ActionType.DEBT_AUCTION_PARAMS, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, params)


@view
@external
def areValidAuctionParams(_params: cs.AuctionParams) -> bool:
    return self._areValidAuctionParams(_params)


@view
@internal
def _areValidAuctionParams(_params: cs.AuctionParams) -> bool:
    if not _params.hasParams:
        return False
    if _params.startDiscount > HUNDRED_PERCENT:
        return False
    if _params.maxDiscount > HUNDRED_PERCENT:
        return False
    if _params.startDiscount >= _params.maxDiscount:
        return False
    if _params.delay == max_value(uint256):
        return False
    if _params.duration == 0 or _params.duration == max_value(uint256):
        return False
    return True


# underscore vault discount


@external
def setUndyVaultDiscount(_discount: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _discount <= HUNDRED_PERCENT # dev: invalid discount

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.DEBT_UNDY_VAULT_DISCOUNT
    self.pendingUndyVaultDiscount[aid] = _discount
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingUndyVaultDiscountChange(
        discount=_discount,
        confirmationBlock=confirmationBlock,
        actionId=aid,
    )
    return aid


# buyback ratio


@external
def setBuybackRatio(_ratio: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _ratio <= HUNDRED_PERCENT # dev: invalid ratio

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.DEBT_BUYBACK_RATIO
    self.pendingBuybackRatio[aid] = _ratio
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingBuybackRatioChange(
        ratio=_ratio,
        confirmationBlock=confirmationBlock,
        actionId=aid,
    )
    return aid


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
    _minDynamicRateBoost: uint256 = 0,
    _maxDynamicRateBoost: uint256 = 0,
    _increasePerDangerBlock: uint256 = 0,
    _maxBorrowRate: uint256 = 0,
    _maxLtvDeviation: uint256 = 0,
    _keeperFeeRatio: uint256 = 0,
    _minKeeperFee: uint256 = 0,
    _maxKeeperFee: uint256 = 0,
    _ltvPaybackBuffer: uint256 = 0,
    _genAuctionParams: cs.AuctionParams = empty(cs.AuctionParams),
) -> uint256:
    aid: uint256 = timeLock._initiateAction()

    self.actionType[aid] = _actionType
    self.pendingDebtConfig[aid] = cs.GenDebtConfig(
        perUserDebtLimit=_perUserDebtLimit,
        globalDebtLimit=_globalDebtLimit,
        minDebtAmount=_minDebtAmount,
        numAllowedBorrowers=_numAllowedBorrowers,
        maxBorrowPerInterval=_maxBorrowPerInterval,
        numBlocksPerInterval=_numBlocksPerInterval,
        minDynamicRateBoost=_minDynamicRateBoost,
        maxDynamicRateBoost=_maxDynamicRateBoost,
        increasePerDangerBlock=_increasePerDangerBlock,
        maxBorrowRate=_maxBorrowRate,
        maxLtvDeviation=_maxLtvDeviation,
        keeperFeeRatio=_keeperFeeRatio,
        minKeeperFee=_minKeeperFee,
        maxKeeperFee=_maxKeeperFee,
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
    elif _actionType == ActionType.DEBT_DYNAMIC_RATE_CONFIG:
        log PendingDynamicRateConfigChange(
            minDynamicRateBoost=_minDynamicRateBoost,
            maxDynamicRateBoost=_maxDynamicRateBoost,
            increasePerDangerBlock=_increasePerDangerBlock,
            maxBorrowRate=_maxBorrowRate,
            confirmationBlock=confirmationBlock,
            actionId=aid,
        )
    elif _actionType == ActionType.DEBT_MAX_LTV_DEVIATION:
        log PendingMaxLtvDeviationChange(
            newDeviation=_maxLtvDeviation,
            confirmationBlock=confirmationBlock,
            actionId=aid,
        )
    elif _actionType == ActionType.DEBT_KEEPER_CONFIG:
        log PendingKeeperConfigChange(
            keeperFeeRatio=_keeperFeeRatio,
            minKeeperFee=_minKeeperFee,
            maxKeeperFee=_maxKeeperFee,
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
    assert self._hasPermsToEnable(msg.sender, _shouldEnable) # dev: no perms

    mc: address = self._getMissionControlAddr()
    config: cs.GenDebtConfig = staticcall MissionControl(mc).genDebtConfig()
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
    assert _ripePerBlock != max_value(uint256) # dev: invalid ripe per block
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
    assert self._areValidRipeRewardsAllocs(_borrowersAlloc, _stakersAlloc, _votersAlloc, _genDepositorsAlloc) # dev: invalid rewards allocs
    return self._setPendingRipeRewardsConfig(ActionType.RIPE_REWARDS_ALLOCS, 0, _borrowersAlloc, _stakersAlloc, _votersAlloc, _genDepositorsAlloc)


@view
@internal
def _areValidRipeRewardsAllocs(_borrowersAlloc: uint256, _stakersAlloc: uint256, _votersAlloc: uint256, _genDepositorsAlloc: uint256) -> bool:
    if _borrowersAlloc + _stakersAlloc + _votersAlloc + _genDepositorsAlloc > HUNDRED_PERCENT:
        return False
    return True


# auto stake ratios


@external
def setAutoStakeParams(_autoStakeRatio: uint256, _autoStakeDurationRatio: uint256, _stabPoolRipePerDollarClaimed: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert self._areValidAutoStakeParams(_autoStakeRatio, _autoStakeDurationRatio) # dev: invalid auto stake params
    return self._setPendingRipeRewardsConfig(ActionType.RIPE_REWARDS_AUTO_STAKE_PARAMS, 0, 0, 0, 0, 0, _autoStakeRatio, _autoStakeDurationRatio, _stabPoolRipePerDollarClaimed)


@view
@internal
def _areValidAutoStakeParams(_autoStakeRatio: uint256, _autoStakeDurationRatio: uint256) -> bool:
    if _autoStakeRatio > HUNDRED_PERCENT:
        return False
    if _autoStakeDurationRatio > HUNDRED_PERCENT:
        return False
    return True


# set pending ripe rewards config


@internal
def _setPendingRipeRewardsConfig(
    _actionType: ActionType,
    _ripePerBlock: uint256 = 0,
    _borrowersAlloc: uint256 = 0,
    _stakersAlloc: uint256 = 0,
    _votersAlloc: uint256 = 0,
    _genDepositorsAlloc: uint256 = 0,
    _autoStakeRatio: uint256 = 0,
    _autoStakeDurationRatio: uint256 = 0,
    _stabPoolRipePerDollarClaimed: uint256 = 0,
) -> uint256:
    aid: uint256 = timeLock._initiateAction()

    self.actionType[aid] = _actionType
    self.pendingRipeRewardsConfig[aid] = cs.RipeRewardsConfig(
        arePointsEnabled=False,
        ripePerBlock=_ripePerBlock,
        borrowersAlloc=_borrowersAlloc,
        stakersAlloc=_stakersAlloc,
        votersAlloc=_votersAlloc,
        genDepositorsAlloc=_genDepositorsAlloc,
        autoStakeRatio=_autoStakeRatio,
        autoStakeDurationRatio=_autoStakeDurationRatio,
        stabPoolRipePerDollarClaimed=_stabPoolRipePerDollarClaimed,
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
    elif _actionType == ActionType.RIPE_REWARDS_AUTO_STAKE_PARAMS:
        log PendingRipeRewardsAutoStakeParamsChange(
            autoStakeRatio=_autoStakeRatio,
            autoStakeDurationRatio=_autoStakeDurationRatio,
            stabPoolRipePerDollarClaimed=_stabPoolRipePerDollarClaimed,
            confirmationBlock=confirmationBlock,
            actionId=aid,
        )
    return aid


# enable points


@external
def setRewardsPointsEnabled(_shouldEnable: bool) -> bool:
    assert self._hasPermsToEnable(msg.sender, _shouldEnable) # dev: no perms

    mc: address = self._getMissionControlAddr()
    rewardsConfig: cs.RipeRewardsConfig = staticcall MissionControl(mc).rewardsConfig()
    assert rewardsConfig.arePointsEnabled != _shouldEnable # dev: already set
    rewardsConfig.arePointsEnabled = _shouldEnable
    extcall MissionControl(mc).setRipeRewardsConfig(rewardsConfig)

    log RewardsPointsEnabledModified(arePointsEnabled=_shouldEnable, caller=msg.sender)
    return True


##################
# Ripe Available #
##################


@external
def setRipeAvailableForRewards(_amount: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.RIPE_AVAIL_REWARDS
    self.pendingRipeAvailable[aid] = _amount
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingRipeAvailableForRewardsChange(
        amount=_amount,
        confirmationBlock=confirmationBlock,
        actionId=aid,
    )
    return aid


@external
def setRipeAvailableForHr(_amount: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.RIPE_AVAIL_HR
    self.pendingRipeAvailable[aid] = _amount
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingRipeAvailableForHrChange(
        amount=_amount,
        confirmationBlock=confirmationBlock,
        actionId=aid,
    )
    return aid


@external
def setRipeAvailableForBonds(_amount: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.RIPE_AVAIL_BONDS
    self.pendingRipeAvailable[aid] = _amount
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingRipeAvailableForBondsChange(
        amount=_amount,
        confirmationBlock=confirmationBlock,
        actionId=aid,
    )
    return aid


#######################
# Priority Vault Data #
#######################


# priority liquidation


@external
def setPriorityLiqAssetVaults(_priorityLiqAssetVaults: DynArray[cs.VaultLite, PRIORITY_VAULT_DATA]) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    priorityVaults: DynArray[cs.VaultLite, PRIORITY_VAULT_DATA] = self._sanitizePriorityVaults(_priorityLiqAssetVaults)
    assert len(priorityVaults) == len(_priorityLiqAssetVaults) # dev: invalid priority vaults

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.OTHER_PRIORITY_LIQ_ASSET_VAULTS
    self.pendingPriorityLiqAssetVaults[aid] = priorityVaults
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingPriorityLiqAssetVaultsChange(
        numPriorityLiqAssetVaults=len(priorityVaults),
        confirmationBlock=confirmationBlock,
        actionId=aid,
    )
    return aid


# priority stability pools


@external
def setPriorityStabVaults(_priorityStabVaults: DynArray[cs.VaultLite, PRIORITY_VAULT_DATA]) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    priorityVaults: DynArray[cs.VaultLite, PRIORITY_VAULT_DATA] = self._sanitizePriorityVaults(_priorityStabVaults)
    assert len(priorityVaults) == len(_priorityStabVaults) # dev: invalid priority vaults

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.OTHER_PRIORITY_STAB_VAULTS
    self.pendingPriorityStabVaults[aid] = priorityVaults
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingPriorityStabVaultsChange(
        numPriorityStabVaults=len(priorityVaults),
        confirmationBlock=confirmationBlock,
        actionId=aid,
    )
    return aid


# sanitize


@internal
def _sanitizePriorityVaults(_priorityVaults: DynArray[cs.VaultLite, PRIORITY_VAULT_DATA]) -> DynArray[cs.VaultLite, PRIORITY_VAULT_DATA]:
    sanitizedVaults: DynArray[cs.VaultLite, PRIORITY_VAULT_DATA] = []
    vaultBook: address = self._getVaultBookAddr()
    mc: address = self._getMissionControlAddr()
    for vault: cs.VaultLite in _priorityVaults:
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
def setPriorityPriceSourceIds(_priorityIds: DynArray[uint256, MAX_PRIORITY_PRICE_SOURCES]) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    priorityIds: DynArray[uint256, MAX_PRIORITY_PRICE_SOURCES] = self._sanitizePrioritySources(_priorityIds)
    assert len(priorityIds) != 0 # dev: invalid priority sources

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.OTHER_PRIORITY_PRICE_SOURCE_IDS
    self.pendingPriorityPriceSourceIds[aid] = priorityIds
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingPriorityPriceSourceIdsChange(
        numPriorityPriceSourceIds=len(priorityIds),
        confirmationBlock=confirmationBlock,
        actionId=aid,
    )
    return aid


@view
@internal
def _sanitizePrioritySources(_priorityIds: DynArray[uint256, MAX_PRIORITY_PRICE_SOURCES]) -> DynArray[uint256, MAX_PRIORITY_PRICE_SOURCES]:
    sanitizedIds: DynArray[uint256, MAX_PRIORITY_PRICE_SOURCES] = []
    priceDesk: address = self._getPriceDeskAddr()
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
def setUnderscoreRegistry(_underscoreRegistry: address) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    assert self._isValidUnderscoreAddr(_underscoreRegistry) # dev: invalid underscore registry

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.OTHER_UNDERSCORE_REGISTRY
    self.pendingUnderscoreRegistry[aid] = _underscoreRegistry
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingUnderscoreRegistryChange(
        underscoreRegistry=_underscoreRegistry,
        confirmationBlock=confirmationBlock,
        actionId=aid,
    )
    return aid


@view
@internal
def _isValidUnderscoreAddr(_addr: address) -> bool:
    if _addr == empty(address):
        return True # allowing setting to empty address

    undyLedger: address = staticcall UnderscoreRegistry(_addr).getAddr(UNDERSCORE_LEDGER_ID)
    if undyLedger == empty(address):
        return False

    # make sure has interface
    return not staticcall UnderscoreLedger(undyLedger).isUserWallet(empty(address))


###########################
# Can Perform Lite Action #
###########################


@external
def setCanPerformLiteAction(_user: address, _canDo: bool) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    # when removing, allow to do immediately
    if not _canDo:
        extcall MissionControl(self._getMissionControlAddr()).setCanPerformLiteAction(_user, _canDo)
        log CanPerformLiteAction(user=_user, canDo=_canDo)
        return 0

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.OTHER_CAN_PERFORM_LITE_ACTION
    self.pendingCanPerformLiteAction[aid] = CanPerform(user=_user, canDo=_canDo)
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingCanPerformLiteAction(user=_user, canDo=_canDo, confirmationBlock=confirmationBlock, actionId=aid)
    return aid


###########################
# Should Check Last Touch #
###########################


@external
def setShouldCheckLastTouch(_shouldCheck: bool) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.OTHER_SHOULD_CHECK_LAST_TOUCH
    self.pendingShouldCheckLastTouch[aid] = _shouldCheck
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingShouldCheckLastTouchChange(shouldCheck=_shouldCheck, confirmationBlock=confirmationBlock, actionId=aid)
    return aid


#########################
# Ripe Gov Vault Config #
#########################


@external
def setRipeGovVaultConfig(
    _asset: address,
    _assetWeight: uint256,
    _shouldFreezeWhenBadDebt: bool,
    _minLockDuration: uint256,
    _maxLockDuration: uint256,
    _maxLockBoost: uint256,
    _exitFee: uint256,
    _canExit: bool,
) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    lockTerms: cs.LockTerms = cs.LockTerms(
        minLockDuration=_minLockDuration,
        maxLockDuration=_maxLockDuration,
        maxLockBoost=_maxLockBoost,
        canExit=_canExit,
        exitFee=_exitFee,
    )
    assert self._isValidRipeVaultConfig(_asset, _assetWeight, lockTerms) # dev: invalid ripe vault config

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.RIPE_VAULT_CONFIG
    self.pendingRipeGovVaultConfig[aid] = PendingRipeGovVaultConfig(
        asset=_asset,
        assetWeight=_assetWeight,
        shouldFreezeWhenBadDebt=_shouldFreezeWhenBadDebt,
        lockTerms=lockTerms,
    )

    log PendingRipeGovVaultConfigChange(
        asset=_asset,
        assetWeight=_assetWeight,
        shouldFreezeWhenBadDebt=_shouldFreezeWhenBadDebt,
        minLockDuration=_minLockDuration,
        maxLockDuration=_maxLockDuration,
        maxLockBoost=_maxLockBoost,
        canExit=_canExit,
        exitFee=_exitFee,
        confirmationBlock=timeLock._getActionConfirmationBlock(aid),
        actionId=aid,
    )
    return aid


@view
@internal
def _isValidRipeVaultConfig(_asset: address, _assetWeight: uint256, _lockTerms: cs.LockTerms) -> bool:
    if _asset == empty(address):
        return False

    mc: address = self._getMissionControlAddr()
    if not staticcall MissionControl(mc).isSupportedAsset(_asset):
        return False

    # NOTE: this assumes that vault id 2 is ripe gov vault !!
    if not staticcall MissionControl(mc).isSupportedAssetInVault(2, _asset):
        return False

    if _assetWeight > 500_00: # max 500%
        return False

    if _lockTerms.minLockDuration > _lockTerms.maxLockDuration:
        return False

    if _lockTerms.maxLockBoost > 1000_00: # max 1000%
        return False

    if _lockTerms.exitFee > HUNDRED_PERCENT:
        return False

    if _lockTerms.canExit and _lockTerms.exitFee == 0:
        return False

    if not _lockTerms.canExit and _lockTerms.exitFee != 0:
        return False

    return True


#############
# Execution #
#############


@external
def executePendingAction(_aid: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms

    # check time lock
    if not timeLock._confirmAction(_aid):
        if timeLock._isExpired(_aid):
            self._cancelPendingAction(_aid)
        return False

    actionType: ActionType = self.actionType[_aid]
    mc: address = self._getMissionControlAddr()

    if actionType == ActionType.GEN_CONFIG_VAULT_LIMITS:
        config: cs.GenConfig = staticcall MissionControl(mc).genConfig()
        p: GenConfigLite = self.pendingGeneralConfig[_aid]
        config.perUserMaxVaults = p.perUserMaxVaults
        config.perUserMaxAssetsPerVault = p.perUserMaxAssetsPerVault
        extcall MissionControl(mc).setGeneralConfig(config)
        log VaultLimitsSet(perUserMaxVaults=p.perUserMaxVaults, perUserMaxAssetsPerVault=p.perUserMaxAssetsPerVault)

    elif actionType == ActionType.GEN_CONFIG_STALE_TIME:
        config: cs.GenConfig = staticcall MissionControl(mc).genConfig()
        config.priceStaleTime = self.pendingGeneralConfig[_aid].priceStaleTime
        extcall MissionControl(mc).setGeneralConfig(config)
        log StaleTimeSet(staleTime=config.priceStaleTime)

    elif actionType == ActionType.DEBT_GLOBAL_LIMITS:
        config: cs.GenDebtConfig = staticcall MissionControl(mc).genDebtConfig()
        p: cs.GenDebtConfig = self.pendingDebtConfig[_aid]
        config.perUserDebtLimit = p.perUserDebtLimit
        config.globalDebtLimit = p.globalDebtLimit
        config.minDebtAmount = p.minDebtAmount
        config.numAllowedBorrowers = p.numAllowedBorrowers
        extcall MissionControl(mc).setGeneralDebtConfig(config)
        log GlobalDebtLimitsSet(perUserDebtLimit=p.perUserDebtLimit, globalDebtLimit=p.globalDebtLimit, minDebtAmount=p.minDebtAmount, numAllowedBorrowers=p.numAllowedBorrowers)

    elif actionType == ActionType.DEBT_BORROW_INTERVAL:
        config: cs.GenDebtConfig = staticcall MissionControl(mc).genDebtConfig()
        p: cs.GenDebtConfig = self.pendingDebtConfig[_aid]
        config.maxBorrowPerInterval = p.maxBorrowPerInterval
        config.numBlocksPerInterval = p.numBlocksPerInterval
        extcall MissionControl(mc).setGeneralDebtConfig(config)
        log BorrowIntervalConfigSet(maxBorrowPerInterval=p.maxBorrowPerInterval, numBlocksPerInterval=p.numBlocksPerInterval)

    elif actionType == ActionType.DEBT_DYNAMIC_RATE_CONFIG:
        config: cs.GenDebtConfig = staticcall MissionControl(mc).genDebtConfig()
        p: cs.GenDebtConfig = self.pendingDebtConfig[_aid]
        config.minDynamicRateBoost = p.minDynamicRateBoost
        config.maxDynamicRateBoost = p.maxDynamicRateBoost
        config.increasePerDangerBlock = p.increasePerDangerBlock
        config.maxBorrowRate = p.maxBorrowRate
        extcall MissionControl(mc).setGeneralDebtConfig(config)
        log DynamicRateConfigSet(minDynamicRateBoost=p.minDynamicRateBoost, maxDynamicRateBoost=p.maxDynamicRateBoost, increasePerDangerBlock=p.increasePerDangerBlock, maxBorrowRate=p.maxBorrowRate)

    elif actionType == ActionType.DEBT_MAX_LTV_DEVIATION:
        config: cs.GenDebtConfig = staticcall MissionControl(mc).genDebtConfig()
        config.maxLtvDeviation = self.pendingDebtConfig[_aid].maxLtvDeviation
        extcall MissionControl(mc).setGeneralDebtConfig(config)
        log MaxLtvDeviationSet(newDeviation=config.maxLtvDeviation)

    elif actionType == ActionType.DEBT_KEEPER_CONFIG:
        config: cs.GenDebtConfig = staticcall MissionControl(mc).genDebtConfig()
        p: cs.GenDebtConfig = self.pendingDebtConfig[_aid]
        config.keeperFeeRatio = p.keeperFeeRatio
        config.minKeeperFee = p.minKeeperFee
        config.maxKeeperFee = p.maxKeeperFee
        extcall MissionControl(mc).setGeneralDebtConfig(config)
        log KeeperConfigSet(keeperFeeRatio=p.keeperFeeRatio, minKeeperFee=p.minKeeperFee, maxKeeperFee=p.maxKeeperFee)

    elif actionType == ActionType.DEBT_LTV_PAYBACK_BUFFER:
        config: cs.GenDebtConfig = staticcall MissionControl(mc).genDebtConfig()
        config.ltvPaybackBuffer = self.pendingDebtConfig[_aid].ltvPaybackBuffer
        extcall MissionControl(mc).setGeneralDebtConfig(config)
        log LtvPaybackBufferSet(ltvPaybackBuffer=config.ltvPaybackBuffer)

    elif actionType == ActionType.DEBT_AUCTION_PARAMS:
        config: cs.GenDebtConfig = staticcall MissionControl(mc).genDebtConfig()
        p: cs.GenDebtConfig = self.pendingDebtConfig[_aid]
        config.genAuctionParams = p.genAuctionParams
        extcall MissionControl(mc).setGeneralDebtConfig(config)
        log GenAuctionParamsSet(startDiscount=p.genAuctionParams.startDiscount, maxDiscount=p.genAuctionParams.maxDiscount, delay=p.genAuctionParams.delay, duration=p.genAuctionParams.duration)

    elif actionType == ActionType.DEBT_UNDY_VAULT_DISCOUNT:
        discount: uint256 = self.pendingUndyVaultDiscount[_aid]
        extcall CreditEngine(self._getCreditEngineAddr()).setUnderscoreVaultDiscount(discount)
        log UndyVaultDiscountSet(discount=discount)

    elif actionType == ActionType.DEBT_BUYBACK_RATIO:
        ratio: uint256 = self.pendingBuybackRatio[_aid]
        extcall CreditEngine(self._getCreditEngineAddr()).setBuybackRatio(ratio)
        log BuybackRatioSet(ratio=ratio)

    elif actionType == ActionType.RIPE_REWARDS_BLOCK:
        config: cs.RipeRewardsConfig = staticcall MissionControl(mc).rewardsConfig()
        config.ripePerBlock = self.pendingRipeRewardsConfig[_aid].ripePerBlock
        extcall MissionControl(mc).setRipeRewardsConfig(config)
        log RipeRewardsPerBlockSet(ripePerBlock=config.ripePerBlock)

    elif actionType == ActionType.RIPE_REWARDS_ALLOCS:
        config: cs.RipeRewardsConfig = staticcall MissionControl(mc).rewardsConfig()
        p: cs.RipeRewardsConfig = self.pendingRipeRewardsConfig[_aid]
        config.borrowersAlloc = p.borrowersAlloc
        config.stakersAlloc = p.stakersAlloc
        config.votersAlloc = p.votersAlloc
        config.genDepositorsAlloc = p.genDepositorsAlloc
        extcall MissionControl(mc).setRipeRewardsConfig(config)
        log RipeRewardsAllocsSet(borrowersAlloc=p.borrowersAlloc, stakersAlloc=p.stakersAlloc, votersAlloc=p.votersAlloc, genDepositorsAlloc=p.genDepositorsAlloc)

    elif actionType == ActionType.RIPE_REWARDS_AUTO_STAKE_PARAMS:
        config: cs.RipeRewardsConfig = staticcall MissionControl(mc).rewardsConfig()
        p: cs.RipeRewardsConfig = self.pendingRipeRewardsConfig[_aid]
        config.autoStakeRatio = p.autoStakeRatio
        config.autoStakeDurationRatio = p.autoStakeDurationRatio
        config.stabPoolRipePerDollarClaimed = p.stabPoolRipePerDollarClaimed
        extcall MissionControl(mc).setRipeRewardsConfig(config)
        log RipeRewardsAutoStakeParamsSet(autoStakeRatio=p.autoStakeRatio, autoStakeDurationRatio=p.autoStakeDurationRatio, stabPoolRipePerDollarClaimed=p.stabPoolRipePerDollarClaimed)

    elif actionType == ActionType.RIPE_AVAIL_REWARDS:
        amount: uint256 = self.pendingRipeAvailable[_aid]
        extcall Ledger(self._getLedgerAddr()).setRipeAvailForRewards(amount)
        log RipeAvailableForRewardsSet(amount=amount)

    elif actionType == ActionType.RIPE_AVAIL_HR:
        amount: uint256 = self.pendingRipeAvailable[_aid]
        extcall Ledger(self._getLedgerAddr()).setRipeAvailForHr(amount)
        log RipeAvailableForHrSet(amount=amount)

    elif actionType == ActionType.RIPE_AVAIL_BONDS:
        amount: uint256 = self.pendingRipeAvailable[_aid]
        extcall Ledger(self._getLedgerAddr()).setRipeAvailForBonds(amount)
        log RipeAvailableForBondsSet(amount=amount)

    elif actionType == ActionType.OTHER_PRIORITY_LIQ_ASSET_VAULTS:
        priorityVaults: DynArray[cs.VaultLite, PRIORITY_VAULT_DATA] = self.pendingPriorityLiqAssetVaults[_aid]
        extcall MissionControl(mc).setPriorityLiqAssetVaults(priorityVaults)
        log PriorityLiqAssetVaultsSet(numVaults=len(priorityVaults))

    elif actionType == ActionType.OTHER_PRIORITY_STAB_VAULTS:
        priorityVaults: DynArray[cs.VaultLite, PRIORITY_VAULT_DATA] = self.pendingPriorityStabVaults[_aid]
        extcall MissionControl(mc).setPriorityStabVaults(priorityVaults)
        log PriorityStabVaultsSet(numVaults=len(priorityVaults))

    elif actionType == ActionType.OTHER_PRIORITY_PRICE_SOURCE_IDS:
        priorityIds: DynArray[uint256, MAX_PRIORITY_PRICE_SOURCES] = self.pendingPriorityPriceSourceIds[_aid]
        extcall MissionControl(mc).setPriorityPriceSourceIds(priorityIds)
        log PriorityPriceSourceIdsModified(numIds=len(priorityIds))

    elif actionType == ActionType.OTHER_UNDERSCORE_REGISTRY:
        underscoreRegistry: address = self.pendingUnderscoreRegistry[_aid]
        extcall MissionControl(mc).setUnderscoreRegistry(underscoreRegistry)
        log UnderscoreRegistrySet(addr=underscoreRegistry)

    elif actionType == ActionType.OTHER_CAN_PERFORM_LITE_ACTION:
        data: CanPerform = self.pendingCanPerformLiteAction[_aid]
        extcall MissionControl(mc).setCanPerformLiteAction(data.user, data.canDo)
        log CanPerformLiteAction(user=data.user, canDo=data.canDo)

    elif actionType == ActionType.OTHER_SHOULD_CHECK_LAST_TOUCH:
        shouldCheck: bool = self.pendingShouldCheckLastTouch[_aid]
        extcall MissionControl(mc).setShouldCheckLastTouch(shouldCheck)
        log ShouldCheckLastTouchSet(shouldCheck=shouldCheck)

    elif actionType == ActionType.RIPE_VAULT_CONFIG:
        p: PendingRipeGovVaultConfig = self.pendingRipeGovVaultConfig[_aid]
        extcall MissionControl(mc).setRipeGovVaultConfig(p.asset, p.assetWeight, p.shouldFreezeWhenBadDebt, p.lockTerms)
        log RipeGovVaultConfigSet(asset=p.asset, assetWeight=p.assetWeight, shouldFreezeWhenBadDebt=p.shouldFreezeWhenBadDebt, minLockDuration=p.lockTerms.minLockDuration, maxLockDuration=p.lockTerms.maxLockDuration, maxLockBoost=p.lockTerms.maxLockBoost, canExit=p.lockTerms.canExit, exitFee=p.lockTerms.exitFee)

    self.actionType[_aid] = empty(ActionType)
    return True


# cancel action


@external
def cancelPendingAction(_aid: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    self._cancelPendingAction(_aid)
    return True


@internal
def _cancelPendingAction(_aid: uint256):
    assert timeLock._cancelAction(_aid) # dev: cannot cancel action
    self.actionType[_aid] = empty(ActionType)