# @version 0.4.1
# pragma optimize codesize

exports: gov.__interface__
exports: timeLock.__interface__

initializes: gov
initializes: timeLock[gov := gov]

import contracts.modules.LocalGov as gov
import contracts.modules.TimeLock as timeLock
import contracts.modules.Addys as addys

interface AuctionHouse:
    def startManyAuctions(_auctions: DynArray[FungAuctionConfig, MAX_AUCTIONS], _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def pauseManyAuctions(_auctions: DynArray[FungAuctionConfig, MAX_AUCTIONS], _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def pauseAuction(_liqUser: address, _liqVaultId: uint256, _liqAsset: address, _a: addys.Addys = empty(addys.Addys)) -> bool: nonpayable
    def startAuction(_liqUser: address, _liqVaultId: uint256, _liqAsset: address, _a: addys.Addys = empty(addys.Addys)) -> bool: nonpayable
    def canStartAuction(_liqUser: address, _liqVaultId: uint256, _liqAsset: address) -> bool: view

interface Lootbox:
    def claimLootForUser(_user: address, _caller: address, _shouldStake: bool, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def claimLootForManyUsers(_users: DynArray[address, MAX_CLAIM_USERS], _caller: address, _shouldStake: bool, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def updateRipeRewards(_a: addys.Addys = empty(addys.Addys)): nonpayable
    def claimDepositLootForAsset(_user: address, _vaultId: uint256, _asset: address) -> uint256: nonpayable
    def updateDepositPoints(_user: address, _vaultId: uint256, _vaultAddr: address, _asset: address, _a: addys.Addys = empty(addys.Addys)): nonpayable

interface RipeEcoContract:
    def recoverFundsMany(_recipient: address, _assets: DynArray[address, MAX_RECOVER_ASSETS]): nonpayable
    def recoverFunds(_recipient: address, _asset: address): nonpayable
    def pause(_shouldPause: bool): nonpayable

interface CreditEngine:
    def updateDebtForManyUsers(_users: DynArray[address, MAX_DEBT_UPDATES], _a: addys.Addys = empty(addys.Addys)) -> bool: nonpayable
    def updateDebtForUser(_user: address, _a: addys.Addys = empty(addys.Addys)) -> bool: nonpayable

interface TokenContract:
    def setBlacklist(_addr: address, _shouldBlacklist: bool) -> bool: nonpayable

interface MissionControl:
    def canPerformLiteAction(_user: address) -> bool: view

interface VaultBook:
    def getAddr(_vaultId: uint256) -> address: view

interface RipeHq:
    def getAddr(_regId: uint256) -> address: view

flag ActionType:
    PAUSE
    RECOVER_FUNDS
    RECOVER_FUNDS_MANY
    START_AUCTION
    START_MANY_AUCTIONS
    PAUSE_AUCTION
    PAUSE_MANY_AUCTIONS

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

event PendingPauseAction:
    contractAddr: indexed(address)
    shouldPause: bool
    confirmationBlock: uint256
    actionId: uint256

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

event DebtUpdatedForUser:
    user: indexed(address)
    success: bool
    caller: indexed(address)

event DebtUpdatedForManyUsers:
    numUsers: uint256
    success: bool
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

# pending actions storage
actionType: public(HashMap[uint256, ActionType])
pendingPauseActions: public(HashMap[uint256, PauseAction])
pendingRecoverFundsActions: public(HashMap[uint256, RecoverFundsAction])
pendingRecoverFundsManyActions: public(HashMap[uint256, RecoverFundsManyAction])
pendingStartAuctionActions: public(HashMap[uint256, FungAuctionConfig])
pendingStartManyAuctionsActions: public(HashMap[uint256, DynArray[FungAuctionConfig, MAX_AUCTIONS]])
pendingPauseAuctionActions: public(HashMap[uint256, FungAuctionConfig])
pendingPauseManyAuctionsActions: public(HashMap[uint256, DynArray[FungAuctionConfig, MAX_AUCTIONS]])

MAX_RECOVER_ASSETS: constant(uint256) = 20
MAX_AUCTIONS: constant(uint256) = 20
MAX_DEBT_UPDATES: constant(uint256) = 50
MAX_CLAIM_USERS: constant(uint256) = 50

MISSION_CONTROL_ID: constant(uint256) = 5
VAULT_BOOK_ID: constant(uint256) = 7
AUCTION_HOUSE_ID: constant(uint256) = 8
CREDIT_ENGINE_ID: constant(uint256) = 9
LOOTBOX_ID: constant(uint256) = 10


@deploy
def __init__(
    _ripeHq: address,
    _minConfigTimeLock: uint256,
    _maxConfigTimeLock: uint256,
):
    gov.__init__(_ripeHq, empty(address), 0, 0, 0)
    timeLock.__init__(_minConfigTimeLock, _maxConfigTimeLock, 0, _maxConfigTimeLock)


# access control


@view
@internal
def hasPermsForLiteAction(_caller: address, _hasLiteAccess: bool) -> bool:
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


#################
# Pause Actions #
#################


@external
def pause(_contractAddr: address, _shouldPause: bool) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _contractAddr != empty(address) # dev: invalid contract address
    
    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.PAUSE
    self.pendingPauseActions[aid] = PauseAction(
        contractAddr=_contractAddr,
        shouldPause=_shouldPause
    )
    
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingPauseAction(
        contractAddr=_contractAddr,
        shouldPause=_shouldPause,
        confirmationBlock=confirmationBlock,
        actionId=aid
    )
    return aid


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


#############
# Blacklist #
#############


@external
def setBlacklist(_tokenAddr: address, _addr: address, _shouldBlacklist: bool) -> bool:
    assert self.hasPermsForLiteAction(msg.sender, _shouldBlacklist) # dev: no perms
    assert empty(address) not in [_tokenAddr, _addr] # dev: invalid parameters

    extcall TokenContract(_tokenAddr).setBlacklist(_addr, _shouldBlacklist)
    log BlacklistSet(tokenAddr=_tokenAddr, addr=_addr, isBlacklisted=_shouldBlacklist, caller=msg.sender)
    return True


################
# Debt Updates #
################


@external
def updateDebtForUser(_user: address) -> bool:
    assert self.hasPermsForLiteAction(msg.sender, True) # dev: no perms
    assert _user != empty(address) # dev: invalid user

    success: bool = extcall CreditEngine(self._getCreditEngineAddr()).updateDebtForUser(_user)
    log DebtUpdatedForUser(user=_user, success=success, caller=msg.sender)
    return success


@external
def updateDebtForManyUsers(_users: DynArray[address, MAX_DEBT_UPDATES]) -> bool:
    assert self.hasPermsForLiteAction(msg.sender, True) # dev: no perms
    assert len(_users) != 0 # dev: no users provided

    success: bool = extcall CreditEngine(self._getCreditEngineAddr()).updateDebtForManyUsers(_users)
    log DebtUpdatedForManyUsers(numUsers=len(_users), success=success, caller=msg.sender)
    return success


###############
# Loot Claims #
###############


@external
def claimLootForUser(_user: address, _shouldStake: bool) -> uint256:
    assert self.hasPermsForLiteAction(msg.sender, True) # dev: no perms
    assert _user != empty(address) # dev: invalid user

    ripeAmount: uint256 = extcall Lootbox(self._getLootboxAddr()).claimLootForUser(_user, msg.sender, _shouldStake)
    log LootClaimedForUser(user=_user, caller=msg.sender, shouldStake=_shouldStake, ripeAmount=ripeAmount)
    return ripeAmount


@external
def claimLootForManyUsers(_users: DynArray[address, MAX_CLAIM_USERS], _shouldStake: bool) -> uint256:
    assert self.hasPermsForLiteAction(msg.sender, True) # dev: no perms
    assert len(_users) != 0 # dev: no users provided

    totalRipeAmount: uint256 = extcall Lootbox(self._getLootboxAddr()).claimLootForManyUsers(_users, msg.sender, _shouldStake)
    log LootClaimedForManyUsers(numUsers=len(_users), caller=msg.sender, shouldStake=_shouldStake, totalRipeAmount=totalRipeAmount)
    return totalRipeAmount


@external
def updateRipeRewards() -> bool:
    assert self.hasPermsForLiteAction(msg.sender, True) # dev: no perms

    extcall Lootbox(self._getLootboxAddr()).updateRipeRewards()
    log RipeRewardsUpdated(caller=msg.sender, success=True)
    return True


@external
def claimDepositLootForAsset(_user: address, _vaultId: uint256, _asset: address) -> uint256:
    assert self.hasPermsForLiteAction(msg.sender, True) # dev: no perms
    assert empty(address) not in [_user, _asset] # dev: invalid parameters

    ripeAmount: uint256 = extcall Lootbox(self._getLootboxAddr()).claimDepositLootForAsset(_user, _vaultId, _asset)
    log DepositLootClaimedForAsset(user=_user, vaultId=_vaultId, asset=_asset, ripeAmount=ripeAmount, caller=msg.sender)
    return ripeAmount


@external
def updateDepositPoints(_user: address, _vaultId: uint256, _asset: address) -> bool:
    assert self.hasPermsForLiteAction(msg.sender, True) # dev: no perms
    assert empty(address) not in [_user, _asset] # dev: invalid parameters

    # Get vault address from vault book
    vaultAddr: address = staticcall VaultBook(self._getVaultBookAddr()).getAddr(_vaultId)
    assert vaultAddr != empty(address) # dev: invalid vault

    extcall Lootbox(self._getLootboxAddr()).updateDepositPoints(_user, _vaultId, vaultAddr, _asset)
    log DepositPointsUpdated(user=_user, vaultId=_vaultId, asset=_asset, caller=msg.sender)
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

    if actionType == ActionType.PAUSE:
        p: PauseAction = self.pendingPauseActions[_aid]
        extcall RipeEcoContract(p.contractAddr).pause(p.shouldPause)
        log PauseExecuted(contractAddr=p.contractAddr, shouldPause=p.shouldPause)

    elif actionType == ActionType.RECOVER_FUNDS:
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
