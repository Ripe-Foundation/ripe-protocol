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
#      Ripe Foundation (C) 2025 

# @version 0.4.3

exports: gov.__interface__
exports: timeLock.__interface__

initializes: gov
initializes: timeLock[gov := gov]

import contracts.modules.LocalGov as gov
import contracts.modules.TimeLock as timeLock
import contracts.modules.Addys as addys
import interfaces.ConfigStructs as cs

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
    def setUserConfig(_user: address, _config: cs.UserConfig): nonpayable
    def setTrainingWheels(_trainingWheels: address): nonpayable
    def deregisterAsset(_asset: address) -> bool: nonpayable
    def assetConfig(_asset: address) -> cs.AssetConfig: view
    def canPerformLiteAction(_user: address) -> bool: view
    def isSupportedAsset(_asset: address) -> bool: view

interface AuctionHouse:
    def startManyAuctions(_auctions: DynArray[FungAuctionConfig, MAX_AUCTIONS], _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def pauseManyAuctions(_auctions: DynArray[FungAuctionConfig, MAX_AUCTIONS], _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def pauseAuction(_liqUser: address, _liqVaultId: uint256, _liqAsset: address, _a: addys.Addys = empty(addys.Addys)) -> bool: nonpayable
    def startAuction(_liqUser: address, _liqVaultId: uint256, _liqAsset: address, _a: addys.Addys = empty(addys.Addys)) -> bool: nonpayable
    def canStartAuction(_liqUser: address, _liqVaultId: uint256, _liqAsset: address) -> bool: view

interface RipeEcoContract:
    def recoverFundsMany(_recipient: address, _assets: DynArray[address, MAX_RECOVER_ASSETS]): nonpayable
    def recoverFunds(_recipient: address, _asset: address): nonpayable
    def pause(_shouldPause: bool): nonpayable

interface CreditEngine:
    def updateDebtForManyUsers(_users: DynArray[address, MAX_DEBT_UPDATES], _a: addys.Addys = empty(addys.Addys)) -> bool: nonpayable
    def updateDebtForUser(_user: address, _a: addys.Addys = empty(addys.Addys)) -> bool: nonpayable

interface Switchboard:
    def setBlacklist(_tokenAddr: address, _addr: address, _shouldBlacklist: bool) -> bool: nonpayable

interface Ledger:
    def setLockedAccount(_wallet: address, _shouldLock: bool): nonpayable

interface TrainingWheels:
    def setAllowed(_user: address, _shouldAllow: bool): nonpayable

interface VaultData:
    def deregisterVaultAsset(_asset: address) -> bool: nonpayable

interface VaultBook:
    def getAddr(_vaultId: uint256) -> address: view

interface RipeHq:
    def getAddr(_regId: uint256) -> address: view

flag ActionType:
    RECOVER_FUNDS
    RECOVER_FUNDS_MANY
    START_AUCTION
    START_MANY_AUCTIONS
    PAUSE_AUCTION
    PAUSE_MANY_AUCTIONS
    TRAINING_WHEELS
    SET_UNDERSCORE_SEND_INTERVAL
    SET_UNDY_DEPOSIT_REWARDS_AMOUNT
    SET_UNDY_YIELD_BONUS_AMOUNT
    DEREGISTER_ASSET
    DEREGISTER_VAULT_ASSET
    SET_USER_CONFIG
    SET_USER_DELEGATION

flag AssetFlag:
    CAN_DEPOSIT
    CAN_WITHDRAW
    CAN_REDEEM_IN_STAB_POOL
    CAN_BUY_IN_AUCTION
    CAN_CLAIM_IN_STAB_POOL
    CAN_REDEEM_COLLATERAL

struct PauseAction:
    contractAddr: address
    shouldPause: bool

struct RecoverFundsAction:
    contractAddr: address
    recipient: address
    asset: address

struct RecoverFundsManyAction:
    contractAddr: address
    recipient: address
    assets: DynArray[address, MAX_RECOVER_ASSETS]

struct FungAuctionConfig:
    liqUser: address
    vaultId: uint256
    asset: address

struct TrainingWheelBundle:
    addr: address
    trainingWheels: DynArray[TrainingWheelAccess, MAX_TRAINING_WHEEL_ACCESS]

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

event PendingStartAuctionAction:
    liqUser: indexed(address)
    vaultId: uint256
    asset: indexed(address)
    confirmationBlock: uint256
    actionId: uint256

event PendingStartManyAuctionsAction:
    numAuctions: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingPauseAuctionAction:
    liqUser: indexed(address)
    vaultId: uint256
    asset: indexed(address)
    confirmationBlock: uint256
    actionId: uint256

event PendingPauseManyAuctionsAction:
    numAuctions: uint256
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

event StartAuctionExecuted:
    liqUser: indexed(address)
    vaultId: uint256
    asset: indexed(address)
    success: bool

event StartManyAuctionsExecuted:
    numAuctionsStarted: uint256

event PauseAuctionExecuted:
    liqUser: indexed(address)
    vaultId: uint256
    asset: indexed(address)
    success: bool

event PauseManyAuctionsExecuted:
    numAuctionsPaused: uint256

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

# pending actions storage
actionType: public(HashMap[uint256, ActionType])
pendingPauseActions: public(HashMap[uint256, PauseAction])
pendingRecoverFundsActions: public(HashMap[uint256, RecoverFundsAction])
pendingRecoverFundsManyActions: public(HashMap[uint256, RecoverFundsManyAction])
pendingStartAuctionActions: public(HashMap[uint256, FungAuctionConfig])
pendingStartManyAuctionsActions: public(HashMap[uint256, DynArray[FungAuctionConfig, MAX_AUCTIONS]])
pendingPauseAuctionActions: public(HashMap[uint256, FungAuctionConfig])
pendingPauseManyAuctionsActions: public(HashMap[uint256, DynArray[FungAuctionConfig, MAX_AUCTIONS]])
pendingTrainingWheels: public(HashMap[uint256, address])
pendingUnderscoreSendInterval: public(HashMap[uint256, uint256])
pendingUndyDepositRewardsAmount: public(HashMap[uint256, uint256])
pendingUndyYieldBonusAmount: public(HashMap[uint256, uint256])
pendingMissionControl: public(HashMap[uint256, address])
pendingDeregisterAsset: public(HashMap[uint256, address])
pendingDeregisterVaultAsset: public(HashMap[uint256, DeregisterVaultAssetAction])
pendingUserConfig: public(HashMap[uint256, UserConfigAction])
pendingUserDelegation: public(HashMap[uint256, UserDelegationAction])

MAX_RECOVER_ASSETS: constant(uint256) = 20
MAX_AUCTIONS: constant(uint256) = 20
MAX_TRAINING_WHEEL_ACCESS: constant(uint256) = 25
MAX_DEBT_UPDATES: constant(uint256) = 50
MAX_CLAIM_USERS: constant(uint256) = 50

LEDGER_ID: constant(uint256) = 4
MISSION_CONTROL_ID: constant(uint256) = 5
SWITCHBOARD_ID: constant(uint256) = 6
VAULT_BOOK_ID: constant(uint256) = 8
AUCTION_HOUSE_ID: constant(uint256) = 9
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
def _getAuctionHouseAddr() -> address:
    return staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(AUCTION_HOUSE_ID)


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

    # Get vault address from vault book
    vaultAddr: address = staticcall VaultBook(self._getVaultBookAddr()).getAddr(_vaultId)
    assert vaultAddr != empty(address) # dev: invalid vault

    extcall Lootbox(self._getLootboxAddr()).updateDepositPoints(_user, _vaultId, vaultAddr, _asset)
    log DepositPointsUpdated(user=_user, vaultId=_vaultId, asset=_asset, caller=msg.sender)
    return True


@external
def updateManyDepositPoints(_users: DynArray[address, MAX_CLAIM_USERS], _vaultId: uint256, _asset: address) -> bool:
    assert self._hasPermsForLiteAction(msg.sender, True) # dev: no perms

    # Get vault address from vault book
    vaultAddr: address = staticcall VaultBook(self._getVaultBookAddr()).getAddr(_vaultId)
    assert vaultAddr != empty(address) # dev: invalid vault

    for u: address in _users:
        extcall Lootbox(self._getLootboxAddr()).updateDepositPoints(u, _vaultId, vaultAddr, _asset)

    log DepositPointsUpdatedMany(numUsers=len(_users), vaultId=_vaultId, asset=_asset, caller=msg.sender)
    return True


###################
# Auction Actions #
###################


# start auctions


@external
def startAuction(_liqUser: address, _vaultId: uint256, _asset: address) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert empty(address) not in [_liqUser, _asset] # dev: invalid parameters
    
    # validate auction can be started
    auctionHouseAddr: address = self._getAuctionHouseAddr()
    assert staticcall AuctionHouse(auctionHouseAddr).canStartAuction(_liqUser, _vaultId, _asset) # dev: cannot start auction
    
    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.START_AUCTION
    self.pendingStartAuctionActions[aid] = FungAuctionConfig(
        liqUser=_liqUser,
        vaultId=_vaultId,
        asset=_asset
    )
    
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingStartAuctionAction(
        liqUser=_liqUser,
        vaultId=_vaultId,
        asset=_asset,
        confirmationBlock=confirmationBlock,
        actionId=aid
    )
    return aid


@external
def startManyAuctions(_auctions: DynArray[FungAuctionConfig, MAX_AUCTIONS]) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert len(_auctions) != 0 # dev: no auctions provided
    
    # validate all auctions can be started
    auctionHouseAddr: address = self._getAuctionHouseAddr()
    for auction: FungAuctionConfig in _auctions:
        assert staticcall AuctionHouse(auctionHouseAddr).canStartAuction(auction.liqUser, auction.vaultId, auction.asset) # dev: cannot start auction
    
    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.START_MANY_AUCTIONS
    self.pendingStartManyAuctionsActions[aid] = _auctions
    
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingStartManyAuctionsAction(
        numAuctions=len(_auctions),
        confirmationBlock=confirmationBlock,
        actionId=aid
    )
    return aid


# pause auctions


@external
def pauseAuction(_liqUser: address, _vaultId: uint256, _asset: address) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert empty(address) not in [_liqUser, _asset] # dev: invalid parameters
    
    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.PAUSE_AUCTION
    self.pendingPauseAuctionActions[aid] = FungAuctionConfig(
        liqUser=_liqUser,
        vaultId=_vaultId,
        asset=_asset
    )
    
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingPauseAuctionAction(
        liqUser=_liqUser,
        vaultId=_vaultId,
        asset=_asset,
        confirmationBlock=confirmationBlock,
        actionId=aid
    )
    return aid


@external
def pauseManyAuctions(_auctions: DynArray[FungAuctionConfig, MAX_AUCTIONS]) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert len(_auctions) != 0 # dev: no auctions provided
    
    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.PAUSE_MANY_AUCTIONS
    self.pendingPauseManyAuctionsActions[aid] = _auctions
    
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingPauseManyAuctionsAction(
        numAuctions=len(_auctions),
        confirmationBlock=confirmationBlock,
        actionId=aid
    )
    return aid


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

    elif actionType == ActionType.START_AUCTION:
        p: FungAuctionConfig = self.pendingStartAuctionActions[_aid]
        success: bool = extcall AuctionHouse(self._getAuctionHouseAddr()).startAuction(p.liqUser, p.vaultId, p.asset)
        log StartAuctionExecuted(liqUser=p.liqUser, vaultId=p.vaultId, asset=p.asset, success=success)

    elif actionType == ActionType.START_MANY_AUCTIONS:
        auctions: DynArray[FungAuctionConfig, MAX_AUCTIONS] = self.pendingStartManyAuctionsActions[_aid]
        numStarted: uint256 = extcall AuctionHouse(self._getAuctionHouseAddr()).startManyAuctions(auctions)
        log StartManyAuctionsExecuted(numAuctionsStarted=numStarted)

    elif actionType == ActionType.PAUSE_AUCTION:
        p: FungAuctionConfig = self.pendingPauseAuctionActions[_aid]
        success: bool = extcall AuctionHouse(self._getAuctionHouseAddr()).pauseAuction(p.liqUser, p.vaultId, p.asset)
        log PauseAuctionExecuted(liqUser=p.liqUser, vaultId=p.vaultId, asset=p.asset, success=success)

    elif actionType == ActionType.PAUSE_MANY_AUCTIONS:
        auctions: DynArray[FungAuctionConfig, MAX_AUCTIONS] = self.pendingPauseManyAuctionsActions[_aid]
        numPaused: uint256 = extcall AuctionHouse(self._getAuctionHouseAddr()).pauseManyAuctions(auctions)
        log PauseManyAuctionsExecuted(numAuctionsPaused=numPaused)

    elif actionType == ActionType.TRAINING_WHEELS:
        p: address = self.pendingTrainingWheels[_aid]
        mc: address = self.pendingMissionControl[_aid]
        if mc == empty(address):
            mc = self._getMissionControlAddr()
        extcall MissionControl(mc).setTrainingWheels(p)
        log TrainingWheelsSet(trainingWheels=p)

    elif actionType == ActionType.DEREGISTER_ASSET:
        asset: address = self.pendingDeregisterAsset[_aid]
        mc: address = self.pendingMissionControl[_aid]
        if mc == empty(address):
            mc = self._getMissionControlAddr()
        extcall MissionControl(mc).deregisterAsset(asset)
        log AssetDeregistered(asset=asset)

    elif actionType == ActionType.DEREGISTER_VAULT_ASSET:
        p: DeregisterVaultAssetAction = self.pendingDeregisterVaultAsset[_aid]
        extcall VaultData(p.vaultAddr).deregisterVaultAsset(p.asset)
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
