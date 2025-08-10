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
# pragma optimize codesize

exports: gov.__interface__
exports: timeLock.__interface__

initializes: gov
initializes: timeLock[gov := gov]

import contracts.modules.LocalGov as gov
import contracts.modules.TimeLock as timeLock
import contracts.modules.Addys as addys
from interfaces import UndyLego as ul

interface Endaoment:
    def addLiquidity(_legoId: uint256, _pool: address, _tokenA: address, _tokenB: address, _amountA: uint256 = max_value(uint256), _amountB: uint256 = max_value(uint256), _minAmountA: uint256 = 0, _minAmountB: uint256 = 0, _minLpAmount: uint256 = 0, _extraData: bytes32 = empty(bytes32)) -> (uint256, uint256, uint256, uint256): nonpayable
    def removeLiquidity(_legoId: uint256, _pool: address, _tokenA: address, _tokenB: address, _lpToken: address, _lpAmount: uint256 = max_value(uint256), _minAmountA: uint256 = 0, _minAmountB: uint256 = 0, _extraData: bytes32 = empty(bytes32)) -> (uint256, uint256, uint256, uint256): nonpayable
    def rebalanceYieldPosition(_fromLegoId: uint256, _fromVaultToken: address, _toLegoId: uint256, _toVaultAddr: address = empty(address), _fromVaultAmount: uint256 = max_value(uint256), _extraData: bytes32 = empty(bytes32)) -> (uint256, address, uint256, uint256): nonpayable
    def depositForYield(_legoId: uint256, _asset: address, _vaultAddr: address = empty(address), _amount: uint256 = max_value(uint256), _extraData: bytes32 = empty(bytes32)) -> (uint256, address, uint256, uint256): nonpayable
    def claimRewards(_legoId: uint256, _rewardToken: address = empty(address), _rewardAmount: uint256 = max_value(uint256), _extraData: bytes32 = empty(bytes32)) -> (uint256, uint256): nonpayable
    def withdrawFromYield(_legoId: uint256, _vaultToken: address, _amount: uint256 = max_value(uint256), _extraData: bytes32 = empty(bytes32)) -> (uint256, address, uint256, uint256): nonpayable
    def addPartnerLiquidity(_legoId: uint256, _pool: address, _partner: address, _asset: address, _amount: uint256, _minLpAmount: uint256) -> (uint256, uint256, uint256): nonpayable
    def swapTokens(_instructions: DynArray[ul.SwapInstruction, MAX_SWAP_INSTRUCTIONS]) -> (address, uint256, address, uint256, uint256): nonpayable
    def mintPartnerLiquidity(_partner: address, _asset: address, _amount: uint256 = max_value(uint256)) -> uint256: nonpayable
    def recoverNft(_collection: address, _nftTokenId: uint256, _recipient: address) -> bool: nonpayable
    def convertWethToEth(_amount: uint256 = max_value(uint256)) -> (uint256, uint256): nonpayable
    def convertEthToWeth(_amount: uint256 = max_value(uint256)) -> (uint256, uint256): payable
    def repayPoolDebt(_pool: address, _amount: uint256) -> bool: nonpayable
    def stabilizeGreenRefPool() -> bool: nonpayable

interface AuctionHouse:
    def startManyAuctions(_auctions: DynArray[FungAuctionConfig, MAX_AUCTIONS], _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def pauseManyAuctions(_auctions: DynArray[FungAuctionConfig, MAX_AUCTIONS], _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def pauseAuction(_liqUser: address, _liqVaultId: uint256, _liqAsset: address, _a: addys.Addys = empty(addys.Addys)) -> bool: nonpayable
    def startAuction(_liqUser: address, _liqVaultId: uint256, _liqAsset: address, _a: addys.Addys = empty(addys.Addys)) -> bool: nonpayable
    def canStartAuction(_liqUser: address, _liqVaultId: uint256, _liqAsset: address) -> bool: view

interface Lootbox:
    def claimLootForManyUsers(_users: DynArray[address, MAX_CLAIM_USERS], _caller: address, _shouldStake: bool, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def updateDepositPoints(_user: address, _vaultId: uint256, _vaultAddr: address, _asset: address, _a: addys.Addys = empty(addys.Addys)): nonpayable
    def claimLootForUser(_user: address, _caller: address, _shouldStake: bool, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def claimDepositLootForAsset(_user: address, _vaultId: uint256, _asset: address) -> uint256: nonpayable
    def updateRipeRewards(_a: addys.Addys = empty(addys.Addys)): nonpayable

interface RipeEcoContract:
    def recoverFundsMany(_recipient: address, _assets: DynArray[address, MAX_RECOVER_ASSETS]): nonpayable
    def recoverFunds(_recipient: address, _asset: address): nonpayable
    def pause(_shouldPause: bool): nonpayable

interface CreditEngine:
    def updateDebtForManyUsers(_users: DynArray[address, MAX_DEBT_UPDATES], _a: addys.Addys = empty(addys.Addys)) -> bool: nonpayable
    def updateDebtForUser(_user: address, _a: addys.Addys = empty(addys.Addys)) -> bool: nonpayable

interface MissionControl:
    def setTrainingWheels(_trainingWheels: address): nonpayable
    def canPerformLiteAction(_user: address) -> bool: view

interface Switchboard:
    def setBlacklist(_tokenAddr: address, _addr: address, _shouldBlacklist: bool) -> bool: nonpayable

interface TrainingWheels:
    def setAllowed(_user: address, _shouldAllow: bool): nonpayable

interface Ledger:
    def setLockedAccount(_wallet: address, _shouldLock: bool): nonpayable

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
    ENDAO_SWAP
    ENDAO_ADD_LIQUIDITY
    ENDAO_REMOVE_LIQUIDITY
    ENDAO_PARTNER_MINT
    ENDAO_PARTNER_POOL
    ENDAO_REPAY
    ENDOA_RECOVER_NFT
    TRAINING_WHEELS

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

struct EndaoLiquidityAction:
    legoId: uint256
    pool: address
    tokenA: address
    tokenB: address
    amountA: uint256
    amountB: uint256
    minAmountA: uint256
    minAmountB: uint256
    minLpAmount: uint256
    extraData: bytes32
    lpToken: address
    lpAmount: uint256

struct EndaoPartnerMintAction:
    partner: address
    asset: address
    amount: uint256

struct EndaoPartnerPoolAction:
    legoId: uint256
    pool: address
    partner: address
    asset: address
    amount: uint256
    minLpAmount: uint256

struct EndaoRepayAction:
    pool: address
    amount: uint256

struct EndaoRecoverNftAction:
    collection: address
    nftTokenId: uint256
    recipient: address

struct TrainingWheelBundle:
    addr: address
    trainingWheels: DynArray[TrainingWheelAccess, MAX_TRAINING_WHEEL_ACCESS]

struct TrainingWheelAccess:
    user: address
    isAllowed: bool

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

event PendingEndaoSwapAction:
    numSwapInstructions: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingEndaoAddLiquidityAction:
    legoId: uint256
    pool: indexed(address)
    tokenA: indexed(address)
    tokenB: indexed(address)
    confirmationBlock: uint256
    actionId: uint256

event PendingEndaoRemoveLiquidityAction:
    legoId: uint256
    pool: indexed(address)
    tokenA: indexed(address)
    tokenB: indexed(address)
    confirmationBlock: uint256
    actionId: uint256

event PendingEndaoPartnerMintAction:
    partner: indexed(address)
    asset: indexed(address)
    amount: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingEndaoPartnerPoolAction:
    legoId: uint256
    pool: indexed(address)
    partner: indexed(address)
    asset: indexed(address)
    confirmationBlock: uint256
    actionId: uint256

event PendingEndaoRepayAction:
    pool: indexed(address)
    amount: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingTrainingWheelsChange:
    trainingWheels: indexed(address)
    confirmationBlock: uint256
    actionId: uint256

event PendingEndaoRecoverNftAction:
    collection: indexed(address)
    nftTokenId: uint256
    recipient: indexed(address)
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

event EndaomentDepositPerformed:
    legoId: uint256
    asset: indexed(address)
    vault: indexed(address)
    amount: uint256
    caller: indexed(address)

event EndaomentWithdrawalPerformed:
    legoId: uint256
    asset: indexed(address)
    vaultAddr: indexed(address)
    withdrawAmount: uint256
    caller: indexed(address)

event EndaomentReblanacePerformed:
    fromLegoId: uint256
    fromAsset: indexed(address)
    fromVaultAddr: address
    toLegoId: uint256
    toVaultAddr: indexed(address)
    caller: indexed(address)

event EndaomentEthToWethPerformed:
    amount: uint256
    caller: indexed(address)

event EndaomentWethToEthPerformed:
    amount: uint256
    caller: indexed(address)

event EndaomentClaimPerformed:
    legoId: uint256
    rewardToken: indexed(address)
    rewardAmount: uint256
    usdValue: uint256
    caller: indexed(address)

event EndaomentStabilizerPerformed:
    success: bool
    caller: indexed(address)

event EndaoSwapExecuted:
    numSwapInstructions: uint256

event EndaoAddLiquidityExecuted:
    legoId: uint256
    pool: indexed(address)
    tokenA: indexed(address)
    tokenB: indexed(address)

event EndaoRemoveLiquidityExecuted:
    legoId: uint256
    pool: indexed(address)
    tokenA: indexed(address)
    tokenB: indexed(address)

event EndaoPartnerMintExecuted:
    partner: indexed(address)
    asset: indexed(address)
    greenMinted: uint256

event EndaoPartnerPoolExecuted:
    legoId: uint256
    pool: indexed(address)
    partner: indexed(address)
    asset: indexed(address)

event EndaoRepayExecuted:
    pool: indexed(address)
    success: bool

event EndaoRecoverNftExecuted:
    collection: indexed(address)
    nftTokenId: uint256
    recipient: indexed(address)
    success: bool

event TrainingWheelsSet:
    trainingWheels: indexed(address)

event TrainingWheelsAccessSet:
    trainingWheels: indexed(address)
    user: indexed(address)
    isAllowed: bool

# pending actions storage
actionType: public(HashMap[uint256, ActionType])
pendingPauseActions: public(HashMap[uint256, PauseAction])
pendingRecoverFundsActions: public(HashMap[uint256, RecoverFundsAction])
pendingRecoverFundsManyActions: public(HashMap[uint256, RecoverFundsManyAction])
pendingStartAuctionActions: public(HashMap[uint256, FungAuctionConfig])
pendingStartManyAuctionsActions: public(HashMap[uint256, DynArray[FungAuctionConfig, MAX_AUCTIONS]])
pendingPauseAuctionActions: public(HashMap[uint256, FungAuctionConfig])
pendingPauseManyAuctionsActions: public(HashMap[uint256, DynArray[FungAuctionConfig, MAX_AUCTIONS]])
pendingEndaoSwapActions: public(HashMap[uint256, DynArray[ul.SwapInstruction, MAX_SWAP_INSTRUCTIONS]])
pendingEndaoAddLiquidityActions: public(HashMap[uint256, EndaoLiquidityAction])
pendingEndaoRemoveLiquidityActions: public(HashMap[uint256, EndaoLiquidityAction])
pendingEndaoPartnerMintActions: public(HashMap[uint256, EndaoPartnerMintAction])
pendingEndaoPartnerPoolActions: public(HashMap[uint256, EndaoPartnerPoolAction])
pendingEndaoRepayActions: public(HashMap[uint256, EndaoRepayAction])
pendingEndaoRecoverNftActions: public(HashMap[uint256, EndaoRecoverNftAction])
pendingTrainingWheels: public(HashMap[uint256, address])

MAX_RECOVER_ASSETS: constant(uint256) = 20
MAX_AUCTIONS: constant(uint256) = 20
MAX_TRAINING_WHEEL_ACCESS: constant(uint256) = 25
MAX_DEBT_UPDATES: constant(uint256) = 50
MAX_CLAIM_USERS: constant(uint256) = 50
MAX_SWAP_INSTRUCTIONS: constant(uint256) = 5
MAX_TOKEN_PATH: constant(uint256) = 5

LEDGER_ID: constant(uint256) = 4
MISSION_CONTROL_ID: constant(uint256) = 5
SWITCHBOARD_ID: constant(uint256) = 6
VAULT_BOOK_ID: constant(uint256) = 8
AUCTION_HOUSE_ID: constant(uint256) = 9
CREDIT_ENGINE_ID: constant(uint256) = 13
ENDAOMENT_ID: constant(uint256) = 14
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


@view
@internal
def _getEndaomentAddr() -> address:
    return staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(ENDAOMENT_ID)


@view
@internal
def _getLedgerAddr() -> address:
    return staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(LEDGER_ID)


#################
# Pause Actions #
#################


@external
def pause(_contractAddr: address, _shouldPause: bool) -> bool:
    assert self.hasPermsForLiteAction(msg.sender, _shouldPause) # dev: no perms

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
    assert self.hasPermsForLiteAction(msg.sender, _shouldBlacklist) # dev: no perms
    assert empty(address) not in [_tokenAddr, _addr] # dev: invalid parameters

    switchboard: address = staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(SWITCHBOARD_ID)
    extcall Switchboard(switchboard).setBlacklist(_tokenAddr, _addr, _shouldBlacklist)
    log BlacklistSet(tokenAddr=_tokenAddr, addr=_addr, isBlacklisted=_shouldBlacklist, caller=msg.sender)
    return True


@external
def setLockedAccount(_wallet: address, _shouldLock: bool) -> bool:
    assert self.hasPermsForLiteAction(msg.sender, _shouldLock) # dev: no perms
    assert _wallet != empty(address) # dev: invalid wallet

    extcall Ledger(self._getLedgerAddr()).setLockedAccount(_wallet, _shouldLock)
    log LockedAccountSet(wallet=_wallet, isLocked=_shouldLock, caller=msg.sender)
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


@external
def updateManyDepositPoints(_users: DynArray[address, MAX_CLAIM_USERS], _vaultId: uint256, _asset: address) -> bool:
    assert self.hasPermsForLiteAction(msg.sender, True) # dev: no perms

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


#############
# Endaoment #
#############


# no timelock required


@external
def performEndaomentDeposit(
    _legoId: uint256,
    _asset: address,
    _vaultAddr: address = empty(address),
    _amount: uint256 = max_value(uint256),
    _extraData: bytes32 = empty(bytes32),
) -> (uint256, address, uint256, uint256):
    assert self.hasPermsForLiteAction(msg.sender, True) # dev: no perms
    assert empty(address) not in [_asset, _vaultAddr] # dev: invalid parameters
    assert _legoId != 0 # dev: invalid lego id

    result: (uint256, address, uint256, uint256) = extcall Endaoment(self._getEndaomentAddr()).depositForYield(_legoId, _asset, _vaultAddr, _amount, _extraData)
    log EndaomentDepositPerformed(legoId=_legoId, asset=_asset, vault=_vaultAddr, amount=_amount, caller=msg.sender)
    return result


@external
def performEndaomentWithdraw(
    _legoId: uint256,
    _vaultToken: address,
    _amount: uint256 = max_value(uint256),
    _extraData: bytes32 = empty(bytes32),
) -> (uint256, address, uint256, uint256):
    assert self.hasPermsForLiteAction(msg.sender, True) # dev: no perms
    assert empty(address) not in [_vaultToken] # dev: invalid parameters
    assert _legoId != 0 # dev: invalid lego id

    result: (uint256, address, uint256, uint256) = extcall Endaoment(self._getEndaomentAddr()).withdrawFromYield(_legoId, _vaultToken, _amount, _extraData)
    log EndaomentWithdrawalPerformed(legoId=_legoId, asset=result[1], vaultAddr=_vaultToken, withdrawAmount=result[0], caller=msg.sender)
    return result


@external
def performEndaomentRebalance(
    _fromLegoId: uint256,
    _fromVaultToken: address,
    _toLegoId: uint256,
    _toVaultAddr: address = empty(address),
    _fromVaultAmount: uint256 = max_value(uint256),
    _extraData: bytes32 = empty(bytes32),
) -> (uint256, address, uint256, uint256):
    assert self.hasPermsForLiteAction(msg.sender, True) # dev: no perms
    assert empty(address) not in [_fromVaultToken, _toVaultAddr] # dev: invalid parameters
    assert _fromLegoId != 0 and _toLegoId != 0 # dev: invalid lego ids

    result: (uint256, address, uint256, uint256) = extcall Endaoment(self._getEndaomentAddr()).rebalanceYieldPosition(_fromLegoId, _fromVaultToken, _toLegoId, _toVaultAddr, _fromVaultAmount, _extraData)
    log EndaomentReblanacePerformed(fromLegoId=_fromLegoId, fromAsset=_fromVaultToken, fromVaultAddr=_fromVaultToken, toLegoId=_toLegoId, toVaultAddr=_toVaultAddr, caller=msg.sender)
    return result


@payable
@external
def performEndaomentEthToWeth(_amount: uint256 = max_value(uint256)) -> (uint256, uint256):
    assert self.hasPermsForLiteAction(msg.sender, True) # dev: no perms

    result: (uint256, uint256) = extcall Endaoment(self._getEndaomentAddr()).convertEthToWeth(_amount, value=msg.value)
    log EndaomentEthToWethPerformed(amount=_amount, caller=msg.sender)
    return result


@external
def performEndaomentWethToEth(_amount: uint256 = max_value(uint256)) -> (uint256, uint256):
    assert self.hasPermsForLiteAction(msg.sender, True) # dev: no perms

    result: (uint256, uint256) = extcall Endaoment(self._getEndaomentAddr()).convertWethToEth(_amount)
    log EndaomentWethToEthPerformed(amount=_amount, caller=msg.sender)
    return result


@external
def performEndaomentClaim(
    _legoId: uint256,
    _rewardToken: address = empty(address),
    _rewardAmount: uint256 = max_value(uint256),
    _extraData: bytes32 = empty(bytes32),
) -> (uint256, uint256):
    assert self.hasPermsForLiteAction(msg.sender, True) # dev: no perms
    assert _legoId != 0 # dev: invalid lego id

    result: (uint256, uint256) = extcall Endaoment(self._getEndaomentAddr()).claimRewards(_legoId, _rewardToken, _rewardAmount, _extraData)
    log EndaomentClaimPerformed(legoId=_legoId, rewardToken=_rewardToken, rewardAmount=result[0], usdValue=result[1], caller=msg.sender)
    return result


@external
def performEndaomentStabilizer() -> bool:
    assert self.hasPermsForLiteAction(msg.sender, True) # dev: no perms

    success: bool = extcall Endaoment(self._getEndaomentAddr()).stabilizeGreenRefPool()
    log EndaomentStabilizerPerformed(success=success, caller=msg.sender)
    return success


# timelock actions


@external
def performEndaomentSwap(_instructions: DynArray[ul.SwapInstruction, MAX_SWAP_INSTRUCTIONS]) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert len(_instructions) != 0 # dev: no swap instructions provided
    
    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.ENDAO_SWAP
    self.pendingEndaoSwapActions[aid] = _instructions
    
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingEndaoSwapAction(
        numSwapInstructions=len(_instructions),
        confirmationBlock=confirmationBlock,
        actionId=aid
    )
    return aid


@external
def addLiquidityInEndaoment(
    _legoId: uint256,
    _pool: address,
    _tokenA: address,
    _tokenB: address,
    _amountA: uint256 = max_value(uint256),
    _amountB: uint256 = max_value(uint256),
    _minAmountA: uint256 = 0,
    _minAmountB: uint256 = 0,
    _minLpAmount: uint256 = 0,
    _extraData: bytes32 = empty(bytes32),
) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _legoId != 0 # dev: invalid lego id
    
    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.ENDAO_ADD_LIQUIDITY
    self.pendingEndaoAddLiquidityActions[aid] = EndaoLiquidityAction(
        legoId=_legoId,
        pool=_pool,
        tokenA=_tokenA,
        tokenB=_tokenB,
        amountA=_amountA,
        amountB=_amountB,
        minAmountA=_minAmountA,
        minAmountB=_minAmountB,
        minLpAmount=_minLpAmount,
        extraData=_extraData,
        lpToken=empty(address),
        lpAmount=0
    )
    
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingEndaoAddLiquidityAction(
        legoId=_legoId,
        pool=_pool,
        tokenA=_tokenA,
        tokenB=_tokenB,
        confirmationBlock=confirmationBlock,
        actionId=aid
    )
    return aid


@external
def removeLiquidityInEndaoment(
    _legoId: uint256,
    _pool: address,
    _tokenA: address,
    _tokenB: address,
    _lpToken: address,
    _lpAmount: uint256 = max_value(uint256),
    _minAmountA: uint256 = 0,
    _minAmountB: uint256 = 0,
    _extraData: bytes32 = empty(bytes32),
) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _legoId != 0 # dev: invalid lego id
    
    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.ENDAO_REMOVE_LIQUIDITY
    self.pendingEndaoRemoveLiquidityActions[aid] = EndaoLiquidityAction(
        legoId=_legoId,
        pool=_pool,
        tokenA=_tokenA,
        tokenB=_tokenB,
        amountA=0,
        amountB=0,
        minAmountA=_minAmountA,
        minAmountB=_minAmountB,
        minLpAmount=0,
        extraData=_extraData,
        lpToken=_lpToken,
        lpAmount=_lpAmount
    )
    
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingEndaoRemoveLiquidityAction(
        legoId=_legoId,
        pool=_pool,
        tokenA=_tokenA,
        tokenB=_tokenB,
        confirmationBlock=confirmationBlock,
        actionId=aid
    )
    return aid


@external
def mintPartnerLiquidityInEndaoment(_partner: address, _asset: address, _amount: uint256 = max_value(uint256)) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert empty(address) not in [_partner, _asset] # dev: invalid parameters
    
    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.ENDAO_PARTNER_MINT
    self.pendingEndaoPartnerMintActions[aid] = EndaoPartnerMintAction(
        partner=_partner,
        asset=_asset,
        amount=_amount
    )
    
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingEndaoPartnerMintAction(
        partner=_partner,
        asset=_asset,
        amount=_amount,
        confirmationBlock=confirmationBlock,
        actionId=aid
    )
    return aid


@external
def addPartnerLiquidityInEndaoment(
    _legoId: uint256,
    _pool: address,
    _partner: address,
    _asset: address,
    _amount: uint256 = max_value(uint256),
    _minLpAmount: uint256 = 0,
) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert empty(address) not in [_pool, _partner, _asset] # dev: invalid parameters
    assert _legoId != 0 # dev: invalid lego id
    
    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.ENDAO_PARTNER_POOL
    self.pendingEndaoPartnerPoolActions[aid] = EndaoPartnerPoolAction(
        legoId=_legoId,
        pool=_pool,
        partner=_partner,
        asset=_asset,
        amount=_amount,
        minLpAmount=_minLpAmount
    )
    
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingEndaoPartnerPoolAction(
        legoId=_legoId,
        pool=_pool,
        partner=_partner,
        asset=_asset,
        confirmationBlock=confirmationBlock,
        actionId=aid
    )
    return aid


@external
def repayPoolDebtInEndaoment(_pool: address, _amount: uint256 = max_value(uint256)) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _pool != empty(address) # dev: invalid pool
    
    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.ENDAO_REPAY
    self.pendingEndaoRepayActions[aid] = EndaoRepayAction(
        pool=_pool,
        amount=_amount
    )
    
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingEndaoRepayAction(
        pool=_pool,
        amount=_amount,
        confirmationBlock=confirmationBlock,
        actionId=aid
    )
    return aid


@external
def recoverNftInEndaoment(_collection: address, _nftTokenId: uint256, _recipient: address) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert empty(address) not in [_collection, _recipient] # dev: invalid parameters
    
    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.ENDOA_RECOVER_NFT
    self.pendingEndaoRecoverNftActions[aid] = EndaoRecoverNftAction(
        collection=_collection,
        nftTokenId=_nftTokenId,
        recipient=_recipient
    )
    
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingEndaoRecoverNftAction(
        collection=_collection,
        nftTokenId=_nftTokenId,
        recipient=_recipient,
        confirmationBlock=confirmationBlock,
        actionId=aid
    )
    return aid


###################
# Training Wheels #
###################


# set training wheels address (does not set access)


@external
def setTrainingWheels(_trainingWheels: address) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.TRAINING_WHEELS
    self.pendingTrainingWheels[aid] = _trainingWheels
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

    elif actionType == ActionType.ENDAO_SWAP:
        swapInstructions: DynArray[ul.SwapInstruction, MAX_SWAP_INSTRUCTIONS] = self.pendingEndaoSwapActions[_aid]
        extcall Endaoment(self._getEndaomentAddr()).swapTokens(swapInstructions)
        log EndaoSwapExecuted(numSwapInstructions=len(swapInstructions))

    elif actionType == ActionType.ENDAO_ADD_LIQUIDITY:
        p: EndaoLiquidityAction = self.pendingEndaoAddLiquidityActions[_aid]
        extcall Endaoment(self._getEndaomentAddr()).addLiquidity(p.legoId, p.pool, p.tokenA, p.tokenB, p.amountA, p.amountB, p.minAmountA, p.minAmountB, p.minLpAmount, p.extraData)
        log EndaoAddLiquidityExecuted(legoId=p.legoId, pool=p.pool, tokenA=p.tokenA, tokenB=p.tokenB)

    elif actionType == ActionType.ENDAO_REMOVE_LIQUIDITY:
        p: EndaoLiquidityAction = self.pendingEndaoRemoveLiquidityActions[_aid]
        extcall Endaoment(self._getEndaomentAddr()).removeLiquidity(p.legoId, p.pool, p.tokenA, p.tokenB, p.lpToken, p.lpAmount, p.minAmountA, p.minAmountB, p.extraData)
        log EndaoRemoveLiquidityExecuted(legoId=p.legoId, pool=p.pool, tokenA=p.tokenA, tokenB=p.tokenB)

    elif actionType == ActionType.ENDAO_PARTNER_MINT:
        p: EndaoPartnerMintAction = self.pendingEndaoPartnerMintActions[_aid]
        greenMinted: uint256 = extcall Endaoment(self._getEndaomentAddr()).mintPartnerLiquidity(p.partner, p.asset, p.amount)
        log EndaoPartnerMintExecuted(partner=p.partner, asset=p.asset, greenMinted=greenMinted)

    elif actionType == ActionType.ENDAO_PARTNER_POOL:
        p: EndaoPartnerPoolAction = self.pendingEndaoPartnerPoolActions[_aid]
        extcall Endaoment(self._getEndaomentAddr()).addPartnerLiquidity(p.legoId, p.pool, p.partner, p.asset, p.amount, p.minLpAmount)
        log EndaoPartnerPoolExecuted(legoId=p.legoId, pool=p.pool, partner=p.partner, asset=p.asset)

    elif actionType == ActionType.ENDAO_REPAY:
        p: EndaoRepayAction = self.pendingEndaoRepayActions[_aid]
        success: bool = extcall Endaoment(self._getEndaomentAddr()).repayPoolDebt(p.pool, p.amount)
        log EndaoRepayExecuted(pool=p.pool, success=success)

    elif actionType == ActionType.ENDOA_RECOVER_NFT:
        p: EndaoRecoverNftAction = self.pendingEndaoRecoverNftActions[_aid]
        success: bool = extcall Endaoment(self._getEndaomentAddr()).recoverNft(p.collection, p.nftTokenId, p.recipient)
        log EndaoRecoverNftExecuted(collection=p.collection, nftTokenId=p.nftTokenId, recipient=p.recipient, success=success)

    elif actionType == ActionType.TRAINING_WHEELS:
        p: address = self.pendingTrainingWheels[_aid]
        extcall MissionControl(self._getMissionControlAddr()).setTrainingWheels(p)
        log TrainingWheelsSet(trainingWheels=p)

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
