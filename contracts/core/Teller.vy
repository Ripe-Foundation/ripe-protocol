# @version 0.4.1

implements: Department

exports: addys.__interface__
exports: deptBasics.__interface__

initializes: addys
initializes: deptBasics[addys := addys]

import contracts.modules.Addys as addys
import contracts.modules.DeptBasics as deptBasics
from interfaces import Department
from interfaces import Vault
from ethereum.ercs import IERC20

interface CreditEngine:
    def redeemCollateralFromMany(_redemptions: DynArray[CollateralRedemption, MAX_COLLATERAL_REDEMPTIONS], _greenAmount: uint256, _redeemer: address, _shouldStakeRefund: bool, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def redeemCollateral(_user: address, _vaultId: uint256, _asset: address, _greenAmount: uint256, _redeemer: address, _shouldStakeRefund: bool, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def repayForUser(_user: address, _greenAmount: uint256, _shouldStakeRefund: bool, _caller: address, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def borrowForUser(_user: address, _greenAmount: uint256, _shouldStake: bool, _caller: address, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def getMaxWithdrawableForAsset(_user: address, _asset: address, _a: addys.Addys = empty(addys.Addys)) -> uint256: view
    def updateDebtForUser(_user: address, _a: addys.Addys = empty(addys.Addys)) -> bool: nonpayable

interface AuctionHouse:
    def buyManyFungibleAuctions(_purchases: DynArray[FungAuctionPurchase, MAX_AUCTION_PURCHASES], _greenAmount: uint256, _buyer: address, _shouldStakeRefund: bool, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def buyFungibleAuction(_liqUser: address, _vaultId: uint256, _asset: address, _greenAmount: uint256, _buyer: address, _shouldStakeRefund: bool, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def liquidateManyUsers(_liqUsers: DynArray[address, MAX_LIQ_USERS], _keeper: address, _shouldStakeRewards: bool, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def liquidateUser(_liqUser: address, _keeper: address, _shouldStakeRewards: bool, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable

interface StabVault:
    def redeemManyFromStabilityPool(_redemptions: DynArray[StabPoolRedemption, MAX_STAB_REDEMPTIONS], _greenAmount: uint256, _redeemer: address, _shouldStakeRefund: bool, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def redeemFromStabilityPool(_claimAsset: address, _greenAmount: uint256, _redeemer: address, _shouldStakeRefund: bool, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def claimFromStabilityPool(_claimer: address, _stabAsset: address, _claimAsset: address, _maxUsdValue: uint256, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def claimManyFromStabilityPool(_claimer: address, _claims: DynArray[StabPoolClaim, MAX_STAB_CLAIMS], _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable

interface Lootbox:
    def claimLootForManyUsers(_users: DynArray[address, MAX_CLAIM_USERS], _caller: address, _shouldStake: bool, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def updateDepositPoints(_user: address, _vaultId: uint256, _vaultAddr: address, _asset: address, _a: addys.Addys = empty(addys.Addys)): nonpayable
    def claimLootForUser(_user: address, _caller: address, _shouldStake: bool, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable

interface ControlRoom:
    def getTellerWithdrawConfig(_asset: address, _user: address, _caller: address) -> TellerWithdrawConfig: view
    def getTellerDepositConfig(_asset: address, _user: address) -> TellerDepositConfig: view

interface Ledger:
    def getDepositLedgerData(_user: address, _vaultId: uint256) -> DepositLedgerData: view
    def addVaultToUser(_user: address, _vaultId: uint256): nonpayable

interface VaultBook:
    def getRegId(_vaultAddr: address) -> uint256: view
    def getAddr(_vaultId: uint256) -> address: view

struct DepositLedgerData:
    isParticipatingInVault: bool
    numUserVaults: uint256

struct TellerDepositConfig:
    canDepositGeneral: bool
    canDepositAsset: bool
    isUserAllowed: bool
    perUserDepositLimit: uint256
    globalDepositLimit: uint256
    perUserMaxAssetsPerVault: uint256
    perUserMaxVaults: uint256
    canAnyoneDeposit: bool

struct DepositAction:
    asset: address
    amount: uint256
    vaultAddr: address
    vaultId: uint256

struct TellerWithdrawConfig:
    canWithdrawGeneral: bool
    canWithdrawAsset: bool
    isUserAllowed: bool
    canWithdrawForUser: bool

struct WithdrawalAction:
    asset: address
    amount: uint256
    vaultAddr: address
    vaultId: uint256

struct CollateralRedemption:
    user: address
    vaultId: uint256
    asset: address
    maxGreenAmount: uint256

struct FungAuctionPurchase:
    liqUser: address
    vaultId: uint256
    asset: address
    maxGreenAmount: uint256

struct StabPoolClaim:
    stabAsset: address
    claimAsset: address
    maxUsdValue: uint256

struct StabPoolRedemption:
    claimAsset: address
    maxGreenAmount: uint256

event TellerDeposit:
    user: indexed(address)
    depositor: indexed(address)
    asset: indexed(address)
    amount: uint256
    vaultAddr: address
    vaultId: uint256

event TellerWithdrawal:
    user: indexed(address)
    asset: indexed(address)
    caller: indexed(address)
    amount: uint256
    vaultAddr: address
    vaultId: uint256
    isDepleted: bool

MAX_BALANCE_ACTION: constant(uint256) = 20
MAX_CLAIM_USERS: constant(uint256) = 25
MAX_COLLATERAL_REDEMPTIONS: constant(uint256) = 20
MAX_AUCTION_PURCHASES: constant(uint256) = 20
MAX_LIQ_USERS: constant(uint256) = 50
MAX_STAB_CLAIMS: constant(uint256) = 15
MAX_STAB_REDEMPTIONS: constant(uint256) = 15


@deploy
def __init__(_ripeHq: address):
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, False) # no minting


############
# Deposits #
############


@nonreentrant
@external
def deposit(
    _asset: address,
    _amount: uint256 = max_value(uint256),
    _user: address = msg.sender,
    _vaultAddr: address = empty(address),
    _vaultId: uint256 = 0,
) -> uint256:
    assert deptBasics.isActivated # dev: contract paused
    a: addys.Addys = addys._getAddys()
    amount: uint256 = self._deposit(_asset, _amount, _user, _vaultAddr, _vaultId, msg.sender, a)
    extcall CreditEngine(a.creditEngine).updateDebtForUser(_user, a)
    return amount


@nonreentrant
@external
def depositMany(_user: address, _deposits: DynArray[DepositAction, MAX_BALANCE_ACTION]) -> uint256:
    assert deptBasics.isActivated # dev: contract paused
    a: addys.Addys = addys._getAddys()
    for d: DepositAction in _deposits:
        self._deposit(d.asset, d.amount, _user, d.vaultAddr, d.vaultId, msg.sender, a)
    extcall CreditEngine(a.creditEngine).updateDebtForUser(_user, a)
    return len(_deposits)


# core logic


@internal
def _deposit(
    _asset: address,
    _amount: uint256,
    _user: address,
    _vaultAddr: address,
    _vaultId: uint256,
    _depositor: address,
    _a: addys.Addys,
) -> uint256:
    vaultAddr: address = empty(address)
    vaultId: uint256 = 0
    vaultAddr, vaultId = self._getVaultAddrAndId(_vaultAddr, _vaultId, _a.vaultBook)

    # get ledger data
    d: DepositLedgerData = staticcall Ledger(_a.ledger).getDepositLedgerData(_user, vaultId)
    amount: uint256 = self._validateOnDeposit(_asset, _amount, _user, vaultAddr, vaultId, _depositor, d, _a.controlRoom)

    # deposit tokens
    assert extcall IERC20(_asset).transferFrom(_depositor, vaultAddr, amount, default_return_value=True) # dev: token transfer failed
    amount = extcall Vault(vaultAddr).depositTokensInVault(_user, _asset, amount, _a)

    # register vault participation
    if not d.isParticipatingInVault:
        extcall Ledger(_a.ledger).addVaultToUser(_user, vaultId)

    # update lootbox points
    extcall Lootbox(_a.lootbox).updateDepositPoints(_user, vaultId, vaultAddr, _asset, _a)

    log TellerDeposit(user=_user, depositor=_depositor, asset=_asset, amount=amount, vaultAddr=vaultAddr, vaultId=vaultId)
    return amount


# validation


@view
@internal
def _validateOnDeposit(
    _asset: address,
    _amount: uint256,
    _user: address,
    _vaultAddr: address,
    _vaultId: uint256,
    _depositor: address,
    _d: DepositLedgerData,
    _controlRoom: address,
) -> uint256:
    config: TellerDepositConfig = staticcall ControlRoom(_controlRoom).getTellerDepositConfig(_asset, _user)
    assert config.canDepositGeneral # dev: protocol deposits disabled
    assert config.canDepositAsset # dev: asset deposits disabled
    assert config.isUserAllowed # dev: user not on whitelist

    # make sure depositor is allowed to deposit for user
    if _user != _depositor:
        assert config.canAnyoneDeposit # dev: others cannot deposit for user

    # check max vaults, max assets per vault
    vd: Vault.VaultDataOnDeposit = staticcall Vault(_vaultAddr).getVaultDataOnDeposit(_user, _asset)
    if not _d.isParticipatingInVault:
        assert _d.numUserVaults < config.perUserMaxVaults # dev: reached max vaults
    elif not vd.hasPosition:
        assert vd.numAssets < config.perUserMaxAssetsPerVault # dev: reached max assets per vault

    # avail amount
    amount: uint256 = min(_amount, staticcall IERC20(_asset).balanceOf(_depositor))
    assert amount != 0 # dev: cannot deposit 0

    # per user deposit limit
    availPerUserDeposit: uint256 = self._getAvailPerUserDepositLimit(vd.userBalance, config.perUserDepositLimit)
    assert availPerUserDeposit != 0 # dev: cannot deposit, reached user limit
    amount = min(amount, availPerUserDeposit)

    # global deposit limit
    availGlobalDeposit: uint256 = self._getAvailGlobalDepositLimit(vd.totalBalance, config.globalDepositLimit)
    assert availGlobalDeposit != 0 # dev: cannot deposit, reached global limit
    amount = min(amount, availGlobalDeposit)

    return amount


# per user deposit limit


@view 
@internal 
def _getAvailPerUserDepositLimit(_userDepositBal: uint256, _perUserDepositLimit: uint256) -> uint256:
    if _perUserDepositLimit == max_value(uint256):
        return max_value(uint256)
    availDeposits: uint256 = 0
    if _perUserDepositLimit > _userDepositBal:
        availDeposits = _perUserDepositLimit - _userDepositBal
    return availDeposits


# global deposit limit


@view 
@internal 
def _getAvailGlobalDepositLimit(_totalDepositBal: uint256, _globalDepositLimit: uint256) -> uint256:
    availDeposits: uint256 = 0
    if _globalDepositLimit > _totalDepositBal:
        availDeposits = _globalDepositLimit - _totalDepositBal
    return availDeposits


###############
# Withdrawals #
###############


@nonreentrant
@external
def withdraw(
    _asset: address,
    _amount: uint256 = max_value(uint256),
    _user: address = msg.sender,
    _vaultAddr: address = empty(address),
    _vaultId: uint256 = 0,
) -> uint256:
    assert deptBasics.isActivated # dev: contract paused
    a: addys.Addys = addys._getAddys()
    amount: uint256 = self._withdraw(_asset, _amount, _user, _vaultAddr, _vaultId, msg.sender, a)
    assert extcall CreditEngine(a.creditEngine).updateDebtForUser(_user, a) # dev: bad debt health
    return amount


@nonreentrant
@external
def withdrawMany(_user: address, _withdrawals: DynArray[WithdrawalAction, MAX_BALANCE_ACTION]) -> uint256:
    assert deptBasics.isActivated # dev: contract paused
    a: addys.Addys = addys._getAddys()
    for w: WithdrawalAction in _withdrawals:
        self._withdraw(w.asset, w.amount, _user, w.vaultAddr, w.vaultId, msg.sender, a)
    assert extcall CreditEngine(a.creditEngine).updateDebtForUser(_user, a) # dev: bad debt health
    return len(_withdrawals)


@internal
def _withdraw(
    _asset: address,
    _amount: uint256,
    _user: address,
    _vaultAddr: address,
    _vaultId: uint256,
    _caller: address,
    _a: addys.Addys,
) -> uint256:
    vaultAddr: address = empty(address)
    vaultId: uint256 = 0
    vaultAddr, vaultId = self._getVaultAddrAndId(_vaultAddr, _vaultId, _a.vaultBook)

    # validation
    amount: uint256 = self._validateOnWithdrawal(_asset, _amount, _user, _vaultAddr, _vaultId, _caller, _a)

    # withdraw tokens
    isDepleted: bool = False
    amount, isDepleted = extcall Vault(vaultAddr).withdrawTokensFromVault(_user, _asset, amount, _user, _a)

    # update lootbox points
    extcall Lootbox(_a.lootbox).updateDepositPoints(_user, vaultId, vaultAddr, _asset, _a)

    log TellerWithdrawal(user=_user, asset=_asset, caller=_caller, amount=amount, vaultAddr=vaultAddr, vaultId=vaultId, isDepleted=isDepleted)
    return amount


# validation


@view
@internal
def _validateOnWithdrawal(
    _asset: address,
    _amount: uint256,
    _user: address,
    _vaultAddr: address,
    _vaultId: uint256,
    _caller: address,
    _a: addys.Addys,
) -> uint256:
    assert _amount != 0 # dev: cannot withdraw 0

    config: TellerWithdrawConfig = staticcall ControlRoom(_a.controlRoom).getTellerWithdrawConfig(_asset, _user, _caller)
    assert config.canWithdrawGeneral # dev: protocol withdrawals disabled
    assert config.canWithdrawAsset # dev: asset withdrawals disabled
    assert config.isUserAllowed # dev: user not on whitelist

    # make sure caller is allowed to withdraw for user
    if _user != _caller:
        assert config.canWithdrawForUser # dev: caller not allowed to withdraw for user

    # max withdrawable
    maxWithdrawable: uint256 = staticcall CreditEngine(_a.creditEngine).getMaxWithdrawableForAsset(_user, _asset, _a)
    assert maxWithdrawable != 0 # dev: cannot withdraw anything

    return min(_amount, maxWithdrawable)


########
# Debt #
########


# borrow


@nonreentrant
@external
def borrow(
    _greenAmount: uint256 = max_value(uint256),
    _user: address = msg.sender,
    _shouldStake: bool = True,
) -> uint256:
    assert deptBasics.isActivated # dev: contract paused
    a: addys.Addys = addys._getAddys()
    return extcall CreditEngine(a.creditEngine).borrowForUser(_user, _greenAmount, _shouldStake, msg.sender, a)


# repay


@nonreentrant
@external
def repay(
    _greenAmount: uint256 = max_value(uint256),
    _user: address = msg.sender,
    _shouldStakeRefund: bool = True,
) -> uint256:
    assert deptBasics.isActivated # dev: contract paused
    a: addys.Addys = addys._getAddys()
    greenAmount: uint256 = self._transferTokensToDepartment(_greenAmount, a.greenToken, a.creditEngine)
    return extcall CreditEngine(a.creditEngine).repayForUser(_user, greenAmount, _shouldStakeRefund, msg.sender, a)


# redeem collateral


@nonreentrant
@external
def redeemCollateral(
    _user: address,
    _vaultId: uint256,
    _asset: address,
    _greenAmount: uint256 = max_value(uint256),
    _shouldStakeRefund: bool = True,
) -> uint256:
    assert deptBasics.isActivated # dev: contract paused
    a: addys.Addys = addys._getAddys()
    greenAmount: uint256 = self._transferTokensToDepartment(_greenAmount, a.greenToken, a.creditEngine)
    greenSpent: uint256 = extcall CreditEngine(a.creditEngine).redeemCollateral(_user, _vaultId, _asset, greenAmount, msg.sender, _shouldStakeRefund, a)
    extcall CreditEngine(a.creditEngine).updateDebtForUser(msg.sender, a)
    return greenSpent


@nonreentrant
@external
def redeemCollateralFromMany(
    _redemptions: DynArray[CollateralRedemption, MAX_COLLATERAL_REDEMPTIONS],
    _greenAmount: uint256 = max_value(uint256),
    _shouldStakeRefund: bool = True,
) -> uint256:
    assert deptBasics.isActivated # dev: contract paused
    a: addys.Addys = addys._getAddys()
    greenAmount: uint256 = self._transferTokensToDepartment(_greenAmount, a.greenToken, a.creditEngine)
    greenSpent: uint256 = extcall CreditEngine(a.creditEngine).redeemCollateralFromMany(_redemptions, greenAmount, msg.sender, _shouldStakeRefund, a)
    extcall CreditEngine(a.creditEngine).updateDebtForUser(msg.sender, a)
    return greenSpent


################
# Liquidations #
################


# buy fungible auctions


@nonreentrant
@external
def buyFungibleAuction(
    _liqUser: address,
    _vaultId: uint256,
    _asset: address,
    _greenAmount: uint256 = max_value(uint256),
    _shouldStakeRefund: bool = True,
) -> uint256:
    assert deptBasics.isActivated # dev: contract paused
    a: addys.Addys = addys._getAddys()
    greenAmount: uint256 = self._transferTokensToDepartment(_greenAmount, a.greenToken, a.auctionHouse)
    greenSpent: uint256 = extcall AuctionHouse(a.auctionHouse).buyFungibleAuction(_liqUser, _vaultId, _asset, greenAmount, msg.sender, _shouldStakeRefund, a)
    extcall CreditEngine(a.creditEngine).updateDebtForUser(msg.sender, a)
    return greenSpent


@nonreentrant
@external
def buyManyFungibleAuctions(
    _purchases: DynArray[FungAuctionPurchase, MAX_AUCTION_PURCHASES],
    _greenAmount: uint256 = max_value(uint256),
    _shouldStakeRefund: bool = True,
) -> uint256:
    assert deptBasics.isActivated # dev: contract paused
    a: addys.Addys = addys._getAddys()
    greenAmount: uint256 = self._transferTokensToDepartment(_greenAmount, a.greenToken, a.auctionHouse)
    greenSpent: uint256 = extcall AuctionHouse(a.auctionHouse).buyManyFungibleAuctions(_purchases, greenAmount, msg.sender, _shouldStakeRefund, a)
    extcall CreditEngine(a.creditEngine).updateDebtForUser(msg.sender, a)
    return greenSpent


# liquidate users


@nonreentrant
@external
def liquidateUser(
    _liqUser: address,
    _shouldStakeRewards: bool = True,
) -> uint256:
    assert deptBasics.isActivated # dev: contract paused
    a: addys.Addys = addys._getAddys()
    keeperRewards: uint256 = extcall AuctionHouse(a.auctionHouse).liquidateUser(_liqUser, msg.sender, _shouldStakeRewards, a)
    extcall CreditEngine(a.creditEngine).updateDebtForUser(msg.sender, a)
    return keeperRewards


@nonreentrant
@external
def liquidateManyUsers(
    _liqUsers: DynArray[address, MAX_LIQ_USERS],
    _shouldStakeRewards: bool = True,
) -> uint256:
    assert deptBasics.isActivated # dev: contract paused
    a: addys.Addys = addys._getAddys()
    keeperRewards: uint256 = extcall AuctionHouse(a.auctionHouse).liquidateManyUsers(_liqUsers, msg.sender, _shouldStakeRewards, a)
    extcall CreditEngine(a.creditEngine).updateDebtForUser(msg.sender, a)
    return keeperRewards


###################
# Stability Pools #
###################


# claims


@nonreentrant
@external
def claimFromStabilityPool(
    _vaultId: uint256,
    _stabAsset: address,
    _claimAsset: address,
    _maxUsdValue: uint256 = max_value(uint256),
) -> uint256:
    assert deptBasics.isActivated # dev: contract paused
    a: addys.Addys = addys._getAddys()
    vaultAddr: address = staticcall VaultBook(a.vaultBook).getAddr(_vaultId) # dev: invalid vault id
    claimUsdValue: uint256 = extcall StabVault(vaultAddr).claimFromStabilityPool(msg.sender, _stabAsset, _claimAsset, _maxUsdValue, a)
    assert extcall CreditEngine(a.creditEngine).updateDebtForUser(msg.sender, a) # dev: bad debt health
    return claimUsdValue


@nonreentrant
@external
def claimManyFromStabilityPool(
    _vaultId: uint256,
    _claims: DynArray[StabPoolClaim, MAX_STAB_CLAIMS],
) -> uint256:
    assert deptBasics.isActivated # dev: contract paused
    a: addys.Addys = addys._getAddys()
    vaultAddr: address = staticcall VaultBook(a.vaultBook).getAddr(_vaultId) # dev: invalid vault id
    claimUsdValue: uint256 = extcall StabVault(vaultAddr).claimManyFromStabilityPool(msg.sender, _claims, a)
    assert extcall CreditEngine(a.creditEngine).updateDebtForUser(msg.sender, a) # dev: bad debt health
    return claimUsdValue


# redemptions


@nonreentrant
@external
def redeemFromStabilityPool(
    _vaultId: uint256,
    _claimAsset: address,
    _greenAmount: uint256 = max_value(uint256),
    _shouldStakeRefund: bool = True,
) -> uint256:
    assert deptBasics.isActivated # dev: contract paused
    a: addys.Addys = addys._getAddys()
    vaultAddr: address = staticcall VaultBook(a.vaultBook).getAddr(_vaultId) # dev: invalid vault id
    assert vaultAddr != empty(address) # dev: invalid vault id
    greenAmount: uint256 = self._transferTokensToDepartment(_greenAmount, a.greenToken, vaultAddr)
    greenSpent: uint256 = extcall StabVault(vaultAddr).redeemFromStabilityPool(_claimAsset, greenAmount, msg.sender, _shouldStakeRefund, a)
    extcall CreditEngine(a.creditEngine).updateDebtForUser(msg.sender, a)
    return greenSpent


@nonreentrant
@external
def redeemManyFromStabilityPool(
    _vaultId: uint256,
    _redemptions: DynArray[StabPoolRedemption, MAX_STAB_REDEMPTIONS],
    _greenAmount: uint256 = max_value(uint256),
    _shouldStakeRefund: bool = True,
) -> uint256:
    assert deptBasics.isActivated # dev: contract paused
    a: addys.Addys = addys._getAddys()
    vaultAddr: address = staticcall VaultBook(a.vaultBook).getAddr(_vaultId) # dev: invalid vault id
    assert vaultAddr != empty(address) # dev: invalid vault id
    greenAmount: uint256 = self._transferTokensToDepartment(_greenAmount, a.greenToken, vaultAddr)
    greenSpent: uint256 = extcall StabVault(vaultAddr).redeemManyFromStabilityPool(_redemptions, greenAmount, msg.sender, _shouldStakeRefund, a)
    extcall CreditEngine(a.creditEngine).updateDebtForUser(msg.sender, a)
    return greenSpent


###########
# Rewards #
###########


# claim loot


@nonreentrant
@external
def claimLoot(_user: address = msg.sender, _shouldStake: bool = True) -> uint256:
    assert deptBasics.isActivated # dev: contract paused
    a: addys.Addys = addys._getAddys()
    totalRipe: uint256 = extcall Lootbox(a.lootbox).claimLootForUser(_user, msg.sender, _shouldStake, a)
    extcall CreditEngine(a.creditEngine).updateDebtForUser(_user, a)
    return totalRipe


# claim for many users


@nonreentrant
@external
def claimLootForManyUsers(_users: DynArray[address, MAX_CLAIM_USERS], _shouldStake: bool = True) -> uint256:
    assert deptBasics.isActivated # dev: contract paused
    a: addys.Addys = addys._getAddys()
    totalRipe: uint256 = extcall Lootbox(a.lootbox).claimLootForManyUsers(_users, msg.sender, _shouldStake, a)
    extcall CreditEngine(a.creditEngine).updateDebtForUser(msg.sender, a)
    return totalRipe


#############
# Utilities #
#############


@view
@internal
def _getVaultAddrAndId(
    _vaultAddr: address,
    _vaultId: uint256,
    _vaultBook: address,
) -> (address, uint256):
    assert _vaultId != 0 or _vaultAddr != empty(address) # dev: invalid vault id or vault addr
    vaultAddr: address = empty(address)
    vaultId: uint256 = 0

    # validate vault id
    if _vaultId != 0:
        vaultAddr = staticcall VaultBook(_vaultBook).getAddr(_vaultId) # dev: invalid vault id
        assert vaultAddr != empty(address) # dev: invalid vault id
        vaultId = _vaultId
        if _vaultAddr != empty(address):
            assert vaultAddr == _vaultAddr # dev: vault id and vault addr mismatch

    # validate vault addr
    elif _vaultAddr != empty(address):
        vaultId = staticcall VaultBook(_vaultBook).getRegId(_vaultAddr) # dev: invalid vault addr
        assert vaultId != 0 # dev: invalid vault addr
        vaultAddr = _vaultAddr

    return vaultAddr, vaultId


@internal
def _transferTokensToDepartment(
    _amount: uint256,
    _asset: address,
    _recipient: address,
) -> uint256:
    tokenAmount: uint256 = min(_amount, staticcall IERC20(_asset).balanceOf(msg.sender))
    assert tokenAmount != 0 # dev: cannot transfer 0 amount
    assert extcall IERC20(_asset).transferFrom(msg.sender, _recipient, tokenAmount, default_return_value=True) # dev: token transfer failed
    return tokenAmount