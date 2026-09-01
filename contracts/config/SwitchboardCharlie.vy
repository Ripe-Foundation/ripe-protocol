#        ______   __     __   __   ______  ______   __  __   ______   ______   ______   ______   _____    
#       /\  ___\ /\ \  _ \ \ /\ \ /\__  _\/\  ___\ /\ \_\ \ /\  == \ /\  __ \ /\  __ \ /\  == \ /\  __-.  
#       \ \___  \\ \ \/ ".\ \\ \ \\/_/\ \/\ \ \____\ \  __ \\ \  __< \ \ \/\ \\ \  __ \\ \  __< \ \ \/\ \ 
#        \/\_____\\ \__/".~\_\\ \_\  \ \_\ \ \_____\\ \_\ \_\\ \_____\\ \_____\\ \_\ \_\\ \_\ \_\\ \____- 
#         \/_____/ \/_/   \/_/ \/_/   \/_/  \/_____/ \/_/\/_/ \/_____/ \/_____/ \/_/\/_/ \/_/ /_/ \/____/ 
#                                                    ┏┓┓     ┓•  
#                                                    ┃ ┣┓┏┓┏┓┃┓┏┓
#                                                    ┗┛┛┗┗┻┛ ┗┗┗ 
#
#      Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
#      Ripe Foundation (C) 2026 

# @version 0.4.3
# pragma optimize codesize

exports: gov.__interface__
exports: timeLock.__interface__

initializes: gov
initializes: timeLock[gov := gov]

import contracts.modules.LocalGov as gov
import contracts.modules.TimeLock as timeLock
import contracts.modules.Addys as addys
import interfaces.ConfigStructs as cs

struct AssetRetirementConfig:
    isSupported: bool
    hasPointsAlloc: bool
    hasWhitelist: bool
    ltv: uint256
    canWithdraw: bool
    canRedeemCollateral: bool
    canBuyInAuction: bool
    canClaimInStabPool: bool
    shouldTransferToEndaoment: bool
    isNft: bool

interface Lootbox:
    def claimLootForManyUsers(_users: DynArray[address, MAX_CLAIM_USERS], _caller: address, _shouldStake: bool, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def updateDepositPoints(_user: address, _vaultId: uint256, _vaultAddr: address, _asset: address, _a: addys.Addys = empty(addys.Addys)): nonpayable
    def claimLootForUser(_user: address, _caller: address, _shouldStake: bool, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def claimDepositLootForAsset(_user: address, _vaultId: uint256, _asset: address) -> uint256: nonpayable
    def updateRipeRewards(_a: addys.Addys = empty(addys.Addys)): nonpayable
    def distributeUnderscoreRewards() -> (uint256, uint256): nonpayable
    def setUnderscoreSendInterval(_interval: uint256): nonpayable
    def setUndyDepositRewardsAmount(_amount: uint256): nonpayable
    def setHasUnderscoreRewards(_hasRewards: bool): nonpayable
    def setUndyYieldBonusAmount(_amount: uint256): nonpayable

interface MissionControl:
    def setUserDelegation(_user: address, _delegate: address, _config: cs.ActionDelegation): nonpayable
    def setAssetConfig(_asset: address, _assetConfig: cs.AssetConfig): nonpayable
    def setRewardVaultId(_asset: address, _vaultId: uint256): nonpayable
    def isSupportedAssetInVault(_vaultId: uint256, _asset: address) -> bool: view
    def getAssetRetirementConfig(_asset: address) -> AssetRetirementConfig: view
    def setUserConfig(_user: address, _config: cs.UserConfig): nonpayable
    def setTrainingWheels(_trainingWheels: address): nonpayable
    def setPreferredStabVaultId(_vaultId: uint256): nonpayable
    def setCoreRipeGovVaultId(_vaultId: uint256): nonpayable
    def deregisterAsset(_asset: address) -> bool: nonpayable
    def assetConfig(_asset: address) -> cs.AssetConfig: view
    def canPerformLiteAction(_user: address) -> bool: view
    def isSupportedAsset(_asset: address) -> bool: view
    def preferredStabVaultId() -> uint256: view
    def coreRipeGovVaultId() -> uint256: view
    def assetStakersPointsAlloc(_asset: address) -> uint256: view
    def isStabVaultId(_vaultId: uint256) -> bool: view
    def isRipeGovVaultId(_vaultId: uint256) -> bool: view
    def rewardVaultId(_asset: address) -> uint256: view
    def accrualStartBlock(_asset: address, _vaultId: uint256) -> uint256: view

interface StabilityPool:
    def canAcceptLiquidationAsset(_stabAsset: address, _claimAsset: address) -> bool: view
    def claimableBalances(_stabAsset: address, _claimAsset: address) -> uint256: view
    def totalClaimableBalances(_asset: address) -> uint256: view
    def vaultAssets(_index: uint256) -> address: view
    def isPaused() -> bool: view

interface RipeEcoContract:
    def recoverFundsMany(_recipient: address, _assets: DynArray[address, MAX_RECOVER_ASSETS]): nonpayable
    def recoverFunds(_recipient: address, _asset: address): nonpayable
    def pause(_shouldPause: bool): nonpayable

interface VaultBook:
    def isValidRegId(_regId: uint256) -> bool: view
    def getAddr(_vaultId: uint256) -> address: view

interface RipeGovVault:
    def totalGovPoints() -> uint256: view
    def isPaused() -> bool: view

interface Switchboard:
    def setBlacklist(_tokenAddr: address, _addr: address, _shouldBlacklist: bool) -> bool: nonpayable

interface CreditEngine:
    def updateDebtForUser(_user: address, _a: addys.Addys = empty(addys.Addys)) -> bool: nonpayable

interface Ledger:
    def setLockedAccount(_wallet: address, _shouldLock: bool): nonpayable

interface TrainingWheels:
    def setAllowed(_user: address, _shouldAllow: bool): nonpayable

interface VaultData:
    def deregisterVaultAsset(_asset: address) -> bool: nonpayable

interface RipeHq:
    def getAddr(_regId: uint256) -> address: view

flag ActionType:
    RECOVER_FUNDS
    RECOVER_FUNDS_MANY
    TRAINING_WHEELS
    SET_UNDERSCORE_SEND_INTERVAL
    SET_UNDY_DEPOSIT_REWARDS_AMOUNT
    SET_UNDY_YIELD_BONUS_AMOUNT
    DEREGISTER_ASSET
    DEREGISTER_VAULT_ASSET
    SET_USER_CONFIG
    SET_USER_DELEGATION
    CORE_RIPE_GOV_VAULT
    PREFERRED_STAB_VAULT
    REWARD_VAULT_ID

flag AssetFlag:
    CAN_DEPOSIT
    CAN_WITHDRAW
    CAN_REDEEM_IN_STAB_POOL
    CAN_BUY_IN_AUCTION
    CAN_CLAIM_IN_STAB_POOL
    CAN_REDEEM_COLLATERAL

struct RecoverFundsAction:
    contractAddr: address
    recipient: address
    asset: address

struct RecoverFundsManyAction:
    contractAddr: address
    recipient: address
    assets: DynArray[address, MAX_RECOVER_ASSETS]

struct TrainingWheelAccess:
    user: address
    isAllowed: bool

struct DeregisterVaultAssetAction:
    vaultAddr: address
    asset: address

struct UserConfigAction:
    user: address
    config: cs.UserConfig

struct UserDelegationAction:
    user: address
    delegate: address
    config: cs.ActionDelegation

struct RewardVaultUpdate:
    asset: address
    oldVaultId: uint256
    newVaultId: uint256

event PendingRecoverFundsAction:
    contractAddr: indexed(address)
    recipient: indexed(address)
    asset: indexed(address)
    confirmationBlock: uint256
    actionId: uint256

event PendingRecoverFundsManyAction:
    contractAddr: indexed(address)
    recipient: indexed(address)
    numAssets: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingTrainingWheelsChange:
    trainingWheels: indexed(address)
    confirmationBlock: uint256
    actionId: uint256

event PauseExecuted:
    contractAddr: indexed(address)
    shouldPause: bool

event RecoverFundsExecuted:
    contractAddr: indexed(address)
    recipient: indexed(address)
    asset: indexed(address)

event RecoverFundsManyExecuted:
    contractAddr: indexed(address)
    recipient: indexed(address)
    numAssets: uint256

event BlacklistSet:
    tokenAddr: indexed(address)
    addr: indexed(address)
    isBlacklisted: bool
    caller: indexed(address)

event LockedAccountSet:
    wallet: indexed(address)
    isLocked: bool
    caller: indexed(address)

event DebtUpdatedForUser:
    user: indexed(address)
    success: bool
    caller: indexed(address)

event DebtUpdatedForManyUsers:
    numUsers: uint256
    caller: indexed(address)

event LootClaimedForUser:
    user: indexed(address)
    caller: indexed(address)
    shouldStake: bool
    ripeAmount: uint256

event LootClaimedForManyUsers:
    numUsers: uint256
    caller: indexed(address)
    shouldStake: bool
    totalRipeAmount: uint256

event RipeRewardsUpdated:
    caller: indexed(address)
    success: bool

event DepositLootClaimedForAsset:
    user: indexed(address)
    vaultId: uint256
    asset: indexed(address)
    ripeAmount: uint256
    caller: indexed(address)

event DepositPointsUpdated:
    user: indexed(address)
    vaultId: uint256
    asset: indexed(address)
    caller: indexed(address)

event DepositPointsUpdatedMany:
    numUsers: uint256
    vaultId: uint256
    asset: indexed(address)
    caller: indexed(address)

event AssetDepositPointsCheckpointedAt:
    asset: indexed(address)
    vaultId: uint256
    vaultAddr: indexed(address)
    caller: indexed(address)

event TrainingWheelsSet:
    trainingWheels: indexed(address)

event TrainingWheelsAccessSet:
    trainingWheels: indexed(address)
    user: indexed(address)
    isAllowed: bool

event UnderscoreRewardsDistributed:
    caller: indexed(address)
    success: bool

event UnderscoreSendIntervalSet:
    interval: uint256
    caller: indexed(address)

event UndyDepositRewardsAmountSet:
    amount: uint256
    caller: indexed(address)

event UndyYieldBonusAmountSet:
    amount: uint256
    caller: indexed(address)

event HasUnderscoreRewardsSet:
    hasRewards: bool
    caller: indexed(address)

event PendingUnderscoreSendIntervalAction:
    interval: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingUndyDepositRewardsAmountAction:
    amount: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingUndyYieldBonusAmountAction:
    amount: uint256
    confirmationBlock: uint256
    actionId: uint256

event CanDepositAssetSet:
    asset: indexed(address)
    canDeposit: bool
    caller: indexed(address)

event CanWithdrawAssetSet:
    asset: indexed(address)
    canWithdraw: bool
    caller: indexed(address)

event CanRedeemInStabPoolAssetSet:
    asset: indexed(address)
    canRedeemInStabPool: bool
    caller: indexed(address)

event CanBuyInAuctionAssetSet:
    asset: indexed(address)
    canBuyInAuction: bool
    caller: indexed(address)

event CanClaimInStabPoolAssetSet:
    asset: indexed(address)
    canClaimInStabPool: bool
    caller: indexed(address)

event CanRedeemCollateralAssetSet:
    asset: indexed(address)
    canRedeemCollateral: bool
    caller: indexed(address)

event PendingDeregisterAssetAction:
    asset: indexed(address)
    confirmationBlock: uint256
    actionId: uint256

event AssetDeregistered:
    asset: indexed(address)

event PendingDeregisterVaultAssetAction:
    vaultAddr: indexed(address)
    asset: indexed(address)
    confirmationBlock: uint256
    actionId: uint256

event PendingUserConfigAction:
    user: indexed(address)
    confirmationBlock: uint256
    actionId: uint256

event PendingUserDelegationAction:
    user: indexed(address)
    delegate: indexed(address)
    confirmationBlock: uint256
    actionId: uint256

event VaultAssetDeregistered:
    vaultAddr: indexed(address)
    asset: indexed(address)

event UserConfigSet:
    user: indexed(address)
    caller: indexed(address)

event UserDelegationSet:
    user: indexed(address)
    delegate: indexed(address)
    caller: indexed(address)

event PendingCoreRipeGovVaultIdChange:
    previousVaultId: uint256
    newVaultId: uint256
    newVaultAddr: address
    confirmationBlock: uint256
    actionId: uint256

event CoreRipeGovVaultIdSet:
    previousVaultId: uint256
    newVaultId: uint256
    newVaultAddr: address

event PendingPreferredStabVaultIdChange:
    previousVaultId: uint256
    newVaultId: uint256
    newVaultAddr: address
    confirmationBlock: uint256
    actionId: uint256

event PreferredStabVaultIdSet:
    previousVaultId: uint256
    newVaultId: uint256
    newVaultAddr: address

event RewardVaultIdSet:
    asset: indexed(address)
    oldVaultId: uint256
    newVaultId: uint256
    caller: indexed(address)

# pending actions storage
actionType: public(HashMap[uint256, ActionType])
pendingRecoverFundsActions: public(HashMap[uint256, RecoverFundsAction])
pendingRecoverFundsManyActions: public(HashMap[uint256, RecoverFundsManyAction])
pendingTrainingWheels: public(HashMap[uint256, address])
pendingUnderscoreSendInterval: public(HashMap[uint256, uint256])
pendingUndyDepositRewardsAmount: public(HashMap[uint256, uint256])
pendingUndyYieldBonusAmount: public(HashMap[uint256, uint256])
pendingMissionControl: public(HashMap[uint256, address])
pendingDeregisterAsset: public(HashMap[uint256, address])
pendingDeregisterVaultAsset: public(HashMap[uint256, DeregisterVaultAssetAction])
pendingUserConfig: public(HashMap[uint256, UserConfigAction])
pendingUserDelegation: public(HashMap[uint256, UserDelegationAction])
pendingCoreRipeGovVaultId: public(HashMap[uint256, uint256])
pendingPreferredStabVaultId: public(HashMap[uint256, uint256])
pendingRewardVault: public(HashMap[uint256, RewardVaultUpdate])

MAX_RECOVER_ASSETS: constant(uint256) = 20
MAX_TRAINING_WHEEL_ACCESS: constant(uint256) = 25
MAX_DEBT_UPDATES: constant(uint256) = 50
MAX_CLAIM_USERS: constant(uint256) = 50

SAVINGS_GREEN_ID: constant(uint256) = 2
RIPE_TOKEN_ID: constant(uint256) = 3
LEDGER_ID: constant(uint256) = 4
MISSION_CONTROL_ID: constant(uint256) = 5
SWITCHBOARD_ID: constant(uint256) = 6
VAULT_BOOK_ID: constant(uint256) = 8
CREDIT_ENGINE_ID: constant(uint256) = 13
LOOTBOX_ID: constant(uint256) = 16


@deploy
def __init__(
    _ripeHq: address,
    _tempGov: address,
    _minConfigTimeLock: uint256,
    _maxConfigTimeLock: uint256,
):
    gov.__init__(_ripeHq, _tempGov, 0, 0, 0)
    timeLock.__init__(_minConfigTimeLock, _maxConfigTimeLock, 0, _maxConfigTimeLock)


# access control


@view
@internal
def _hasPermsForLiteAction(_caller: address, _hasLiteAccess: bool) -> bool:
    if gov._canGovern(_caller):
        return True
    if _hasLiteAccess:
        return staticcall MissionControl(self._getMissionControlAddr()).canPerformLiteAction(_caller)
    return False


# addys lite


@view
@internal
def _getMissionControlAddr() -> address:
    return staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(MISSION_CONTROL_ID)


@view
@internal
def _resolveMissionControl(_missionControl: address) -> address:
    mc: address = self._getMissionControlAddr()
    if _missionControl == empty(address):
        return mc
    assert _missionControl != mc # dev: use empty for current mission control
    return _missionControl


@view
@internal
def _getCreditEngineAddr() -> address:
    return staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(CREDIT_ENGINE_ID)


@view
@internal
def _getLootboxAddr() -> address:
    return staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(LOOTBOX_ID)


@view
@internal
def _getVaultBookAddr() -> address:
    return staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(VAULT_BOOK_ID)


@view
@internal
def _getLedgerAddr() -> address:
    return staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(LEDGER_ID)


###################
# Reward Vault Id #
###################


@view
@internal
def _assertValidRewardVaultId(_asset: address, _vaultId: uint256, _oldVaultId: uint256, _missionControl: address):
    if _oldVaultId != 0 and _vaultId != _oldVaultId:
        # A live promotional clock and its points history share this row identity.
        # Retargeting requires an explicit checkpointed points/clock migration.
        assert staticcall MissionControl(_missionControl).accrualStartBlock(_asset, _oldVaultId) == 0 # dev: promotional reward row migration required
    checkVaultId: uint256 = _oldVaultId if _vaultId == 0 else _vaultId
    assert staticcall MissionControl(_missionControl).isSupportedAssetInVault(checkVaultId, _asset) # dev: unsupported reward vault
    if _vaultId != 0:
        if staticcall MissionControl(_missionControl).assetStakersPointsAlloc(_asset) != 0:
            assert staticcall MissionControl(_missionControl).isRipeGovVaultId(_vaultId) or staticcall MissionControl(_missionControl).isStabVaultId(_vaultId) # dev: staker vault class


# Operator retirement / migration:
# 1. setRewardVaultId(asset, 0) — checkpoints, clears, and zeros allocs on the MC write.
# 2. Move balances / change vaultIds.
# 3. setRewardVaultId(asset, newVault); new vault must already be in vaultIds.
# 4. Bravo sets allocs if needed, or leave both 0 for gen only.
# Execute fences the new row's lastUpdate under the old/zero policy before the write,
# so a stale Ledger row cannot eat the old earner's interval.
# Clear and zero are atomic in MissionControl, so there is no orphan-allocation gap.
@external
def setRewardVaultId(_asset: address, _vaultId: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    mc: address = self._getMissionControlAddr()
    oldVaultId: uint256 = staticcall MissionControl(mc).rewardVaultId(_asset)
    self._assertValidRewardVaultId(_asset, _vaultId, oldVaultId, mc)
    assert _vaultId != oldVaultId # dev: reward vault unchanged
    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.REWARD_VAULT_ID
    self.pendingMissionControl[aid] = mc
    self.pendingRewardVault[aid] = RewardVaultUpdate(asset=_asset, oldVaultId=oldVaultId, newVaultId=_vaultId)
    return aid


##########################
# Core Vault ID Pointers #
##########################


# core ripe gov vault id


@external
def setCoreRipeGovVaultId(_newVaultId: uint256, _missionControl: address = empty(address)) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    mc: address = self._resolveMissionControl(_missionControl)
    newVaultAddr: address = empty(address)
    previousVaultId: uint256 = 0
    newVaultAddr, previousVaultId = self._validateCoreRipeGovVaultId(_newVaultId, mc)

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.CORE_RIPE_GOV_VAULT
    self.pendingCoreRipeGovVaultId[aid] = _newVaultId
    self.pendingMissionControl[aid] = mc
    log PendingCoreRipeGovVaultIdChange(
        previousVaultId=previousVaultId,
        newVaultId=_newVaultId,
        newVaultAddr=newVaultAddr,
        confirmationBlock=timeLock._getActionConfirmationBlock(aid),
        actionId=aid,
    )
    return aid


@view
@internal
def _validateCoreRipeGovVaultId(_vaultId: uint256, _missionControl: address) -> (address, uint256):
    assert _vaultId != 0 # dev: invalid vault id

    vaultBook: address = self._getVaultBookAddr()
    assert staticcall VaultBook(vaultBook).isValidRegId(_vaultId) # dev: invalid vault id
    vaultAddr: address = staticcall VaultBook(vaultBook).getAddr(_vaultId)
    assert vaultAddr != empty(address) and vaultAddr.is_contract # dev: invalid vault
    previousVaultId: uint256 = staticcall MissionControl(_missionControl).coreRipeGovVaultId()
    assert _vaultId != previousVaultId # dev: already set

    ripeToken: address = staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(RIPE_TOKEN_ID)
    assert staticcall MissionControl(_missionControl).isSupportedAssetInVault(_vaultId, ripeToken) # dev: unsupported asset
    na: uint256 = staticcall RipeGovVault(vaultAddr).totalGovPoints()
    assert not staticcall RipeGovVault(vaultAddr).isPaused() # dev: vault paused
    return vaultAddr, previousVaultId


# preferred stab vault id


@external
def setPreferredStabVaultId(_newVaultId: uint256, _missionControl: address = empty(address)) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    mc: address = self._resolveMissionControl(_missionControl)
    newVaultAddr: address = empty(address)
    previousVaultId: uint256 = 0
    newVaultAddr, previousVaultId = self._validatePreferredStabVaultId(_newVaultId, mc)

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.PREFERRED_STAB_VAULT
    self.pendingPreferredStabVaultId[aid] = _newVaultId
    self.pendingMissionControl[aid] = mc
    log PendingPreferredStabVaultIdChange(
        previousVaultId=previousVaultId,
        newVaultId=_newVaultId,
        newVaultAddr=newVaultAddr,
        confirmationBlock=timeLock._getActionConfirmationBlock(aid),
        actionId=aid,
    )
    return aid


@view
@internal
def _validatePreferredStabVaultId(_vaultId: uint256, _missionControl: address) -> (address, uint256):
    assert _vaultId != 0 # dev: invalid vault id

    vaultBook: address = self._getVaultBookAddr()
    assert staticcall VaultBook(vaultBook).isValidRegId(_vaultId) # dev: invalid vault id
    vaultAddr: address = staticcall VaultBook(vaultBook).getAddr(_vaultId)
    assert vaultAddr != empty(address) and vaultAddr.is_contract # dev: invalid vault
    previousVaultId: uint256 = staticcall MissionControl(_missionControl).preferredStabVaultId()
    assert _vaultId != previousVaultId # dev: already set

    savingsGreen: address = staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(SAVINGS_GREEN_ID)
    assert staticcall MissionControl(_missionControl).isSupportedAssetInVault(_vaultId, savingsGreen) # dev: unsupported asset

    # verify has correct interface
    naStabAsset: address = staticcall StabilityPool(vaultAddr).vaultAssets(1)
    naPair: uint256 = staticcall StabilityPool(vaultAddr).claimableBalances(savingsGreen, savingsGreen)
    naCanAccept: bool = staticcall StabilityPool(vaultAddr).canAcceptLiquidationAsset(savingsGreen, savingsGreen)
    assert staticcall StabilityPool(vaultAddr).totalClaimableBalances(savingsGreen) == 0 # dev: asset reserved for claims
    assert not staticcall StabilityPool(vaultAddr).isPaused() # dev: vault paused

    return vaultAddr, previousVaultId


#################
# Pause Actions #
#################


@external
def pause(_contractAddr: address, _shouldPause: bool) -> bool:
    assert self._hasPermsForLiteAction(msg.sender, _shouldPause) # dev: no perms

    extcall RipeEcoContract(_contractAddr).pause(_shouldPause)
    log PauseExecuted(contractAddr=_contractAddr, shouldPause=_shouldPause)
    return True


#########################
# Fund Recovery Actions #
#########################


@external
def recoverFunds(_contractAddr: address, _recipient: address, _asset: address) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert empty(address) not in [_contractAddr, _recipient, _asset] # dev: invalid parameters
    
    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.RECOVER_FUNDS
    self.pendingRecoverFundsActions[aid] = RecoverFundsAction(
        contractAddr=_contractAddr,
        recipient=_recipient,
        asset=_asset
    )
    
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingRecoverFundsAction(
        contractAddr=_contractAddr,
        recipient=_recipient,
        asset=_asset,
        confirmationBlock=confirmationBlock,
        actionId=aid
    )
    return aid


@external
def recoverFundsMany(_contractAddr: address, _recipient: address, _assets: DynArray[address, MAX_RECOVER_ASSETS]) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert empty(address) not in [_contractAddr, _recipient] # dev: invalid parameters
    assert len(_assets) != 0 # dev: no assets provided
    
    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.RECOVER_FUNDS_MANY
    self.pendingRecoverFundsManyActions[aid] = RecoverFundsManyAction(
        contractAddr=_contractAddr,
        recipient=_recipient,
        assets=_assets
    )
    
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingRecoverFundsManyAction(
        contractAddr=_contractAddr,
        recipient=_recipient,
        numAssets=len(_assets),
        confirmationBlock=confirmationBlock,
        actionId=aid
    )
    return aid


####################
# Blacklist / Lock #
####################


@external
def setBlacklist(_tokenAddr: address, _addr: address, _shouldBlacklist: bool) -> bool:
    assert self._hasPermsForLiteAction(msg.sender, _shouldBlacklist) # dev: no perms
    assert empty(address) not in [_tokenAddr, _addr] # dev: invalid parameters

    switchboard: address = staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(SWITCHBOARD_ID)
    extcall Switchboard(switchboard).setBlacklist(_tokenAddr, _addr, _shouldBlacklist)
    log BlacklistSet(tokenAddr=_tokenAddr, addr=_addr, isBlacklisted=_shouldBlacklist, caller=msg.sender)
    return True


@external
def setLockedAccount(_wallet: address, _shouldLock: bool) -> bool:
    assert self._hasPermsForLiteAction(msg.sender, _shouldLock) # dev: no perms
    assert _wallet != empty(address) # dev: invalid wallet

    extcall Ledger(self._getLedgerAddr()).setLockedAccount(_wallet, _shouldLock)
    log LockedAccountSet(wallet=_wallet, isLocked=_shouldLock, caller=msg.sender)
    return True


################
# Debt Updates #
################


@external
def updateDebtForUser(_user: address) -> bool:
    assert self._hasPermsForLiteAction(msg.sender, True) # dev: no perms
    assert _user != empty(address) # dev: invalid user

    success: bool = extcall CreditEngine(self._getCreditEngineAddr()).updateDebtForUser(_user)
    log DebtUpdatedForUser(user=_user, success=success, caller=msg.sender)
    return success


@external
def updateDebtForManyUsers(_users: DynArray[address, MAX_DEBT_UPDATES]) -> bool:
    assert self._hasPermsForLiteAction(msg.sender, True) # dev: no perms
    assert len(_users) != 0 # dev: no users provided

    creditEngineAddr: address = self._getCreditEngineAddr()
    for u: address in _users:
        extcall CreditEngine(creditEngineAddr).updateDebtForUser(u)

    log DebtUpdatedForManyUsers(numUsers=len(_users), caller=msg.sender)
    return True


###############
# Loot Claims #
###############


@external
def claimLootForUser(_user: address, _shouldStake: bool) -> uint256:
    assert self._hasPermsForLiteAction(msg.sender, True) # dev: no perms
    assert _user != empty(address) # dev: invalid user

    ripeAmount: uint256 = extcall Lootbox(self._getLootboxAddr()).claimLootForUser(_user, msg.sender, _shouldStake)
    log LootClaimedForUser(user=_user, caller=msg.sender, shouldStake=_shouldStake, ripeAmount=ripeAmount)
    return ripeAmount


@external
def claimLootForManyUsers(_users: DynArray[address, MAX_CLAIM_USERS], _shouldStake: bool) -> uint256:
    assert self._hasPermsForLiteAction(msg.sender, True) # dev: no perms
    assert len(_users) != 0 # dev: no users provided

    totalRipeAmount: uint256 = extcall Lootbox(self._getLootboxAddr()).claimLootForManyUsers(_users, msg.sender, _shouldStake)
    log LootClaimedForManyUsers(numUsers=len(_users), caller=msg.sender, shouldStake=_shouldStake, totalRipeAmount=totalRipeAmount)
    return totalRipeAmount


@external
def updateRipeRewards() -> bool:
    assert self._hasPermsForLiteAction(msg.sender, True) # dev: no perms

    extcall Lootbox(self._getLootboxAddr()).updateRipeRewards()
    log RipeRewardsUpdated(caller=msg.sender, success=True)
    return True


@external
def distributeUnderscoreRewards() -> bool:
    assert self._hasPermsForLiteAction(msg.sender, True) # dev: no perms

    extcall Lootbox(self._getLootboxAddr()).distributeUnderscoreRewards()
    log UnderscoreRewardsDistributed(caller=msg.sender, success=True)
    return True


@external
def setHasUnderscoreRewards(_hasRewards: bool) -> bool:
    # Allow lite action to disable (False), but only governance can enable (True)
    assert self._hasPermsForLiteAction(msg.sender, not _hasRewards) # dev: no perms

    extcall Lootbox(self._getLootboxAddr()).setHasUnderscoreRewards(_hasRewards)
    log HasUnderscoreRewardsSet(hasRewards=_hasRewards, caller=msg.sender)
    return True


@external
def setUnderscoreSendInterval(_interval: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.SET_UNDERSCORE_SEND_INTERVAL
    self.pendingUnderscoreSendInterval[aid] = _interval
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingUnderscoreSendIntervalAction(
        interval=_interval,
        confirmationBlock=confirmationBlock,
        actionId=aid
    )
    return aid


@external
def setUndyDepositRewardsAmount(_amount: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.SET_UNDY_DEPOSIT_REWARDS_AMOUNT
    self.pendingUndyDepositRewardsAmount[aid] = _amount
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingUndyDepositRewardsAmountAction(
        amount=_amount,
        confirmationBlock=confirmationBlock,
        actionId=aid
    )
    return aid


@external
def setUndyYieldBonusAmount(_amount: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.SET_UNDY_YIELD_BONUS_AMOUNT
    self.pendingUndyYieldBonusAmount[aid] = _amount
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingUndyYieldBonusAmountAction(
        amount=_amount,
        confirmationBlock=confirmationBlock,
        actionId=aid
    )
    return aid


@external
def claimDepositLootForAsset(_user: address, _vaultId: uint256, _asset: address) -> uint256:
    assert self._hasPermsForLiteAction(msg.sender, True) # dev: no perms
    assert empty(address) not in [_user, _asset] # dev: invalid parameters

    ripeAmount: uint256 = extcall Lootbox(self._getLootboxAddr()).claimDepositLootForAsset(_user, _vaultId, _asset)
    log DepositLootClaimedForAsset(user=_user, vaultId=_vaultId, asset=_asset, ripeAmount=ripeAmount, caller=msg.sender)
    return ripeAmount


@external
def updateDepositPoints(_user: address, _vaultId: uint256, _asset: address) -> bool:
    assert self._hasPermsForLiteAction(msg.sender, True) # dev: no perms
    assert empty(address) not in [_user, _asset] # dev: invalid parameters

    vaultAddr: address = staticcall VaultBook(self._getVaultBookAddr()).getAddr(_vaultId)
    assert vaultAddr != empty(address) # dev: invalid vault

    extcall Lootbox(self._getLootboxAddr()).updateDepositPoints(_user, _vaultId, vaultAddr, _asset)
    log DepositPointsUpdated(user=_user, vaultId=_vaultId, asset=_asset, caller=msg.sender)
    return True


@external
def checkpointAssetDepositPointsAt(_asset: address, _vaultId: uint256, _vaultAddr: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert empty(address) not in [_asset, _vaultAddr] # dev: invalid parameters
    assert _vaultAddr.is_contract # dev: invalid vault

    vaultBook: address = self._getVaultBookAddr()
    assert staticcall VaultBook(vaultBook).isValidRegId(_vaultId) # dev: invalid vault id
    bookAddr: address = staticcall VaultBook(vaultBook).getAddr(_vaultId)
    assert bookAddr == _vaultAddr # dev: vault addr mismatch

    mc: address = self._getMissionControlAddr()
    if staticcall MissionControl(mc).rewardVaultId(_asset) == _vaultId:
        assert staticcall MissionControl(mc).accrualStartBlock(_asset, _vaultId) != max_value(uint256) # dev: cannot checkpoint armed promotional row

    extcall Lootbox(self._getLootboxAddr()).updateDepositPoints(empty(address), _vaultId, _vaultAddr, _asset)
    log AssetDepositPointsCheckpointedAt(asset=_asset, vaultId=_vaultId, vaultAddr=_vaultAddr, caller=msg.sender)
    return True


@external
def updateManyDepositPoints(_users: DynArray[address, MAX_CLAIM_USERS], _vaultId: uint256, _asset: address) -> bool:
    assert self._hasPermsForLiteAction(msg.sender, True) # dev: no perms

    assert empty(address) not in _users # dev: invalid user
    vaultAddr: address = staticcall VaultBook(self._getVaultBookAddr()).getAddr(_vaultId)
    assert vaultAddr != empty(address) # dev: invalid vault

    for u: address in _users:
        extcall Lootbox(self._getLootboxAddr()).updateDepositPoints(u, _vaultId, vaultAddr, _asset)

    log DepositPointsUpdatedMany(numUsers=len(_users), vaultId=_vaultId, asset=_asset, caller=msg.sender)
    return True


###################
# Training Wheels #
###################


# set training wheels address (does not set access)


@external
def setTrainingWheels(_trainingWheels: address, _missionControl: address = empty(address)) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.TRAINING_WHEELS
    self.pendingTrainingWheels[aid] = _trainingWheels
    self.pendingMissionControl[aid] = self._resolveMissionControl(_missionControl)
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingTrainingWheelsChange(
        trainingWheels=_trainingWheels,
        confirmationBlock=confirmationBlock,
        actionId=aid,
    )
    return aid


# sets access to training wheels


@external
def setManyTrainingWheelsAccess(_addr: address, _trainingWheels: DynArray[TrainingWheelAccess, MAX_TRAINING_WHEEL_ACCESS]):
    assert gov._canGovern(msg.sender) # dev: no perms
    assert len(_trainingWheels) != 0 # dev: no training wheels provided
    assert _addr != empty(address) # dev: invalid address

    for tw: TrainingWheelAccess in _trainingWheels:
        extcall TrainingWheels(_addr).setAllowed(tw.user, tw.isAllowed)
        log TrainingWheelsAccessSet(trainingWheels=_addr, user=tw.user, isAllowed=tw.isAllowed)


##################
# Random Actions #
##################


# deregister asset


@external
def deregisterAsset(_asset: address, _missionControl: address = empty(address)) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _asset != empty(address) # dev: invalid asset

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.DEREGISTER_ASSET
    self.pendingDeregisterAsset[aid] = _asset
    self.pendingMissionControl[aid] = self._resolveMissionControl(_missionControl)
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingDeregisterAssetAction(
        asset=_asset,
        confirmationBlock=confirmationBlock,
        actionId=aid,
    )
    return aid


# validate


@view
@internal
def _validateAssetDeregistration(_asset: address, _missionControl: address):
    rewardVault: uint256 = staticcall MissionControl(_missionControl).rewardVaultId(_asset)
    if rewardVault != 0:
        assert staticcall MissionControl(_missionControl).accrualStartBlock(_asset, rewardVault) == 0 # dev: promotional campaign cannot deregister
    config: AssetRetirementConfig = staticcall MissionControl(_missionControl).getAssetRetirementConfig(_asset)
    assert config.isSupported # dev: invalid asset
    assert (
        not config.hasPointsAlloc
        and not config.hasWhitelist
        and config.canWithdraw
        and config.canClaimInStabPool
        and (
            config.ltv == 0
            or (
                not config.isNft
                and config.canBuyInAuction
                and (
                    config.shouldTransferToEndaoment
                    or config.canRedeemCollateral
                )
            )
        )
    ) # dev: invalid retirement config


# deregister vault asset


@external
def deregisterVaultAsset(_vaultAddr: address, _asset: address) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _vaultAddr != empty(address) # dev: invalid vault
    assert _asset != empty(address) # dev: invalid asset

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.DEREGISTER_VAULT_ASSET
    self.pendingDeregisterVaultAsset[aid] = DeregisterVaultAssetAction(vaultAddr=_vaultAddr, asset=_asset)
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingDeregisterVaultAssetAction(
        vaultAddr=_vaultAddr,
        asset=_asset,
        confirmationBlock=confirmationBlock,
        actionId=aid,
    )
    return aid


# set user config


@external
def setUserConfig(_user: address, _config: cs.UserConfig, _missionControl: address = empty(address)) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _user != empty(address) # dev: invalid user

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.SET_USER_CONFIG
    self.pendingUserConfig[aid] = UserConfigAction(user=_user, config=_config)
    self.pendingMissionControl[aid] = self._resolveMissionControl(_missionControl)
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingUserConfigAction(
        user=_user,
        confirmationBlock=confirmationBlock,
        actionId=aid,
    )
    return aid


# set user delegation


@external
def setUserDelegation(
    _user: address,
    _delegate: address,
    _config: cs.ActionDelegation,
    _missionControl: address = empty(address),
) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _user != empty(address) # dev: invalid user

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.SET_USER_DELEGATION
    self.pendingUserDelegation[aid] = UserDelegationAction(user=_user, delegate=_delegate, config=_config)
    self.pendingMissionControl[aid] = self._resolveMissionControl(_missionControl)
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingUserDelegationAction(
        user=_user,
        delegate=_delegate,
        confirmationBlock=confirmationBlock,
        actionId=aid,
    )
    return aid


@view
@internal
def _getRequiredVaultAddr(_vaultBook: address, _vaultId: uint256) -> address:
    if _vaultId == 0:
        return empty(address)
    vaultAddr: address = staticcall VaultBook(_vaultBook).getAddr(_vaultId)
    assert vaultAddr != empty(address) # dev: missing reward vault
    return vaultAddr


@internal
def _checkpointRewardVault(_lootbox: address, _asset: address, _vaultId: uint256, _vaultAddr: address):
    extcall Lootbox(_lootbox).updateDepositPoints(empty(address), _vaultId, _vaultAddr, _asset)


@internal
def _executeRewardVaultId(_missionControl: address, _update: RewardVaultUpdate):
    assert _missionControl == self._getMissionControlAddr() # dev: not current mission control
    self._assertValidRewardVaultId(_update.asset, _update.newVaultId, _update.oldVaultId, _missionControl)
    assert staticcall MissionControl(_missionControl).rewardVaultId(_update.asset) == _update.oldVaultId # dev: reward vault changed

    vaultBook: address = self._getVaultBookAddr()
    oldVaultAddr: address = self._getRequiredVaultAddr(vaultBook, _update.oldVaultId)
    newVaultAddr: address = self._getRequiredVaultAddr(vaultBook, _update.newVaultId)

    lootbox: address = self._getLootboxAddr()
    for i: uint256 in range(2):
        if _update.oldVaultId != 0:
            self._checkpointRewardVault(lootbox, _update.asset, _update.oldVaultId, oldVaultAddr)
        if _update.newVaultId != 0:
            self._checkpointRewardVault(lootbox, _update.asset, _update.newVaultId, newVaultAddr)
        if i == 0:
            extcall MissionControl(_missionControl).setRewardVaultId(_update.asset, _update.newVaultId)
    log RewardVaultIdSet(asset=_update.asset, oldVaultId=_update.oldVaultId, newVaultId=_update.newVaultId, caller=msg.sender)


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

    if actionType == ActionType.RECOVER_FUNDS:
        p: RecoverFundsAction = self.pendingRecoverFundsActions[_aid]
        extcall RipeEcoContract(p.contractAddr).recoverFunds(p.recipient, p.asset)
        log RecoverFundsExecuted(contractAddr=p.contractAddr, recipient=p.recipient, asset=p.asset)

    elif actionType == ActionType.RECOVER_FUNDS_MANY:
        p: RecoverFundsManyAction = self.pendingRecoverFundsManyActions[_aid]
        extcall RipeEcoContract(p.contractAddr).recoverFundsMany(p.recipient, p.assets)
        log RecoverFundsManyExecuted(contractAddr=p.contractAddr, recipient=p.recipient, numAssets=len(p.assets))

    elif actionType == ActionType.TRAINING_WHEELS:
        p: address = self.pendingTrainingWheels[_aid]
        mc: address = self.pendingMissionControl[_aid]
        if mc == empty(address):
            mc = self._getMissionControlAddr()
        extcall MissionControl(mc).setTrainingWheels(p)
        log TrainingWheelsSet(trainingWheels=p)

    elif actionType == ActionType.CORE_RIPE_GOV_VAULT:
        newVaultId: uint256 = self.pendingCoreRipeGovVaultId[_aid]
        mc: address = self.pendingMissionControl[_aid]
        if mc == empty(address):
            mc = self._getMissionControlAddr()
        newVaultAddr: address = empty(address)
        previousVaultId: uint256 = 0
        newVaultAddr, previousVaultId = self._validateCoreRipeGovVaultId(newVaultId, mc)
        extcall MissionControl(mc).setCoreRipeGovVaultId(newVaultId)
        log CoreRipeGovVaultIdSet(previousVaultId=previousVaultId, newVaultId=newVaultId, newVaultAddr=newVaultAddr)

    elif actionType == ActionType.PREFERRED_STAB_VAULT:
        newVaultId: uint256 = self.pendingPreferredStabVaultId[_aid]
        mc: address = self.pendingMissionControl[_aid]
        if mc == empty(address):
            mc = self._getMissionControlAddr()
        newVaultAddr: address = empty(address)
        previousVaultId: uint256 = 0
        newVaultAddr, previousVaultId = self._validatePreferredStabVaultId(newVaultId, mc)
        extcall MissionControl(mc).setPreferredStabVaultId(newVaultId)
        log PreferredStabVaultIdSet(previousVaultId=previousVaultId, newVaultId=newVaultId, newVaultAddr=newVaultAddr)

    elif actionType == ActionType.REWARD_VAULT_ID:
        self._executeRewardVaultId(self.pendingMissionControl[_aid], self.pendingRewardVault[_aid])

    elif actionType == ActionType.DEREGISTER_ASSET:
        asset: address = self.pendingDeregisterAsset[_aid]
        mc: address = self.pendingMissionControl[_aid]
        if mc == empty(address):
            mc = self._getMissionControlAddr()
        assert mc == self._getMissionControlAddr() # dev: not current mission control
        self._validateAssetDeregistration(asset, mc)
        success: bool = extcall MissionControl(mc).deregisterAsset(asset)
        assert success # dev: invalid asset
        log AssetDeregistered(asset=asset)

    elif actionType == ActionType.DEREGISTER_VAULT_ASSET:
        p: DeregisterVaultAssetAction = self.pendingDeregisterVaultAsset[_aid]
        success: bool = extcall VaultData(p.vaultAddr).deregisterVaultAsset(p.asset)
        assert success # dev: invalid vault asset
        log VaultAssetDeregistered(vaultAddr=p.vaultAddr, asset=p.asset)

    elif actionType == ActionType.SET_UNDERSCORE_SEND_INTERVAL:
        interval: uint256 = self.pendingUnderscoreSendInterval[_aid]
        extcall Lootbox(self._getLootboxAddr()).setUnderscoreSendInterval(interval)
        log UnderscoreSendIntervalSet(interval=interval, caller=msg.sender)

    elif actionType == ActionType.SET_UNDY_DEPOSIT_REWARDS_AMOUNT:
        amount: uint256 = self.pendingUndyDepositRewardsAmount[_aid]
        extcall Lootbox(self._getLootboxAddr()).setUndyDepositRewardsAmount(amount)
        log UndyDepositRewardsAmountSet(amount=amount, caller=msg.sender)

    elif actionType == ActionType.SET_UNDY_YIELD_BONUS_AMOUNT:
        amount: uint256 = self.pendingUndyYieldBonusAmount[_aid]
        extcall Lootbox(self._getLootboxAddr()).setUndyYieldBonusAmount(amount)
        log UndyYieldBonusAmountSet(amount=amount, caller=msg.sender)

    elif actionType == ActionType.SET_USER_CONFIG:
        p: UserConfigAction = self.pendingUserConfig[_aid]
        mc: address = self.pendingMissionControl[_aid]
        if mc == empty(address):
            mc = self._getMissionControlAddr()
        extcall MissionControl(mc).setUserConfig(p.user, p.config)
        log UserConfigSet(user=p.user, caller=msg.sender)

    elif actionType == ActionType.SET_USER_DELEGATION:
        p: UserDelegationAction = self.pendingUserDelegation[_aid]
        mc: address = self.pendingMissionControl[_aid]
        if mc == empty(address):
            mc = self._getMissionControlAddr()
        extcall MissionControl(mc).setUserDelegation(p.user, p.delegate, p.config)
        log UserDelegationSet(user=p.user, delegate=p.delegate, caller=msg.sender)

    self.actionType[_aid] = empty(ActionType)
    return True


#################
# Cancel Action #
#################


@external
def cancelPendingAction(_aid: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    self._cancelPendingAction(_aid)
    return True


@internal
def _cancelPendingAction(_aid: uint256):
    assert timeLock._cancelAction(_aid) # dev: cannot cancel action
    self.actionType[_aid] = empty(ActionType)


###############
# Asset Flags #
###############


@view
@internal
def _isValidRedeemCollateralConfig(
    _asset: address,
    _shouldEnable: bool,
    _isNft: bool,
    _debtTermsLtv: uint256,
    _shouldTransferToEndaoment: bool,
) -> bool:
    if not _shouldEnable:
        return True

    # cannot redeem collateral if nft
    if _isNft:
        return False

    # must have ltv
    if _debtTermsLtv == 0:
        return False

    # any stable-ish assets cannot be redeemed
    if _shouldTransferToEndaoment:
        return False

    return True


@internal
def _setAssetFlag(_asset: address, _flag: AssetFlag, _shouldEnable: bool, _missionControl: address, _caller: address) -> bool:
    assert self._hasPermsForLiteAction(_caller, not _shouldEnable) # dev: no perms

    mc: address = self._resolveMissionControl(_missionControl)
    assert staticcall MissionControl(mc).isSupportedAsset(_asset) # dev: invalid asset
    assetConfig: cs.AssetConfig = staticcall MissionControl(mc).assetConfig(_asset)

    # get current value and validate
    if _flag == AssetFlag.CAN_DEPOSIT:
        assert assetConfig.canDeposit != _shouldEnable # dev: already set
        assetConfig.canDeposit = _shouldEnable
        log CanDepositAssetSet(asset=_asset, canDeposit=_shouldEnable, caller=_caller)

    elif _flag == AssetFlag.CAN_WITHDRAW:
        assert assetConfig.canWithdraw != _shouldEnable # dev: already set
        assetConfig.canWithdraw = _shouldEnable
        log CanWithdrawAssetSet(asset=_asset, canWithdraw=_shouldEnable, caller=_caller)

    elif _flag == AssetFlag.CAN_REDEEM_IN_STAB_POOL:
        assert assetConfig.canRedeemInStabPool != _shouldEnable # dev: already set
        assetConfig.canRedeemInStabPool = _shouldEnable
        log CanRedeemInStabPoolAssetSet(asset=_asset, canRedeemInStabPool=_shouldEnable, caller=_caller)

    elif _flag == AssetFlag.CAN_BUY_IN_AUCTION:
        assert assetConfig.canBuyInAuction != _shouldEnable # dev: already set
        assetConfig.canBuyInAuction = _shouldEnable
        log CanBuyInAuctionAssetSet(asset=_asset, canBuyInAuction=_shouldEnable, caller=_caller)

    elif _flag == AssetFlag.CAN_CLAIM_IN_STAB_POOL:
        assert assetConfig.canClaimInStabPool != _shouldEnable # dev: already set
        assetConfig.canClaimInStabPool = _shouldEnable
        log CanClaimInStabPoolAssetSet(asset=_asset, canClaimInStabPool=_shouldEnable, caller=_caller)

    elif _flag == AssetFlag.CAN_REDEEM_COLLATERAL:
        assert assetConfig.canRedeemCollateral != _shouldEnable # dev: already set
        assert self._isValidRedeemCollateralConfig(_asset, _shouldEnable, assetConfig.isNft, assetConfig.debtTerms.ltv, assetConfig.shouldTransferToEndaoment) # dev: invalid redeem collateral config
        assetConfig.canRedeemCollateral = _shouldEnable
        log CanRedeemCollateralAssetSet(asset=_asset, canRedeemCollateral=_shouldEnable, caller=_caller)

    extcall MissionControl(mc).setAssetConfig(_asset, assetConfig)
    return True


@external
def setCanDepositAsset(_asset: address, _shouldEnable: bool, _missionControl: address = empty(address)) -> bool:
    return self._setAssetFlag(_asset, AssetFlag.CAN_DEPOSIT, _shouldEnable, _missionControl, msg.sender)


@external
def setCanWithdrawAsset(_asset: address, _shouldEnable: bool, _missionControl: address = empty(address)) -> bool:
    return self._setAssetFlag(_asset, AssetFlag.CAN_WITHDRAW, _shouldEnable, _missionControl, msg.sender)


@external
def setCanRedeemInStabPoolAsset(_asset: address, _shouldEnable: bool, _missionControl: address = empty(address)) -> bool:
    return self._setAssetFlag(_asset, AssetFlag.CAN_REDEEM_IN_STAB_POOL, _shouldEnable, _missionControl, msg.sender)


@external
def setCanBuyInAuctionAsset(_asset: address, _shouldEnable: bool, _missionControl: address = empty(address)) -> bool:
    return self._setAssetFlag(_asset, AssetFlag.CAN_BUY_IN_AUCTION, _shouldEnable, _missionControl, msg.sender)


@external
def setCanClaimInStabPoolAsset(_asset: address, _shouldEnable: bool, _missionControl: address = empty(address)) -> bool:
    return self._setAssetFlag(_asset, AssetFlag.CAN_CLAIM_IN_STAB_POOL, _shouldEnable, _missionControl, msg.sender)


@external
def setCanRedeemCollateralAsset(_asset: address, _shouldEnable: bool, _missionControl: address = empty(address)) -> bool:
    return self._setAssetFlag(_asset, AssetFlag.CAN_REDEEM_COLLATERAL, _shouldEnable, _missionControl, msg.sender)
