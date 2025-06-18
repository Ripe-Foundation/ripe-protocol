# @version 0.4.1
# pragma optimize codesize

implements: Department

exports: addys.__interface__
exports: deptBasics.__interface__

initializes: addys
initializes: deptBasics[addys := addys]

import contracts.modules.Addys as addys
import contracts.modules.DeptBasics as deptBasics
from interfaces import Department
from interfaces import Vault
import interfaces.ConfigStructs as cs

from ethereum.ercs import IERC20
from ethereum.ercs import IERC4626

interface CreditEngine:
    def redeemCollateralFromMany(_redemptions: DynArray[CollateralRedemption, MAX_COLLATERAL_REDEMPTIONS], _greenAmount: uint256, _recipient: address, _caller: address, _shouldTransferBalance: bool, _shouldRefundSavingsGreen: bool, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def redeemCollateral(_user: address, _vaultId: uint256, _asset: address, _greenAmount: uint256, _recipient: address, _caller: address, _shouldTransferBalance: bool, _shouldRefundSavingsGreen: bool, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def getMaxWithdrawableForAsset(_user: address, _vaultId: uint256, _asset: address, _vaultAddr: address = empty(address), _a: addys.Addys = empty(addys.Addys)) -> uint256: view
    def repayForUser(_user: address, _greenAmount: uint256, _shouldRefundSavingsGreen: bool, _caller: address, _a: addys.Addys = empty(addys.Addys)) -> bool: nonpayable
    def borrowForUser(_user: address, _greenAmount: uint256, _wantsSavingsGreen: bool, _shouldEnterStabPool: bool, _caller: address, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def updateDebtForUser(_user: address, _a: addys.Addys = empty(addys.Addys)) -> bool: nonpayable

interface MissionControl:
    def getTellerWithdrawConfig(_asset: address, _user: address, _caller: address) -> TellerWithdrawConfig: view
    def getTellerDepositConfig(_vaultId: uint256, _asset: address, _user: address) -> TellerDepositConfig: view
    def setUserDelegation(_user: address, _delegate: address, _config: cs.ActionDelegation): nonpayable
    def setUserConfig(_user: address, _config: cs.UserConfig): nonpayable
    def getFirstVaultIdForAsset(_asset: address) -> uint256: view
    def underscoreRegistry() -> address: view

interface AuctionHouse:
    def buyManyFungibleAuctions(_purchases: DynArray[FungAuctionPurchase, MAX_AUCTION_PURCHASES], _greenAmount: uint256, _recipient: address, _caller: address, _shouldTransferBalance: bool, _shouldRefundSavingsGreen: bool, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def buyFungibleAuction(_liqUser: address, _vaultId: uint256, _asset: address, _greenAmount: uint256, _recipient: address, _caller: address, _shouldTransferBalance: bool, _shouldRefundSavingsGreen: bool, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def liquidateManyUsers(_liqUsers: DynArray[address, MAX_LIQ_USERS], _keeper: address, _wantsSavingsGreen: bool, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def liquidateUser(_liqUser: address, _keeper: address, _wantsSavingsGreen: bool, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable

interface StabVault:
    def redeemManyFromStabilityPool(_redemptions: DynArray[StabPoolRedemption, MAX_STAB_REDEMPTIONS], _greenAmount: uint256, _redeemer: address, _shouldRefundSavingsGreen: bool, _shouldAutoDeposit: bool, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def claimFromStabilityPool(_claimer: address, _stabAsset: address, _claimAsset: address, _maxUsdValue: uint256, _caller: address, _shouldAutoDeposit: bool, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def redeemFromStabilityPool(_claimAsset: address, _greenAmount: uint256, _redeemer: address, _shouldRefundSavingsGreen: bool, _shouldAutoDeposit: bool, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def claimManyFromStabilityPool(_claimer: address, _claims: DynArray[StabPoolClaim, MAX_STAB_CLAIMS], _caller: address, _shouldAutoDeposit: bool, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable

interface Lootbox:
    def claimLootForManyUsers(_users: DynArray[address, MAX_CLAIM_USERS], _caller: address, _shouldStake: bool, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def updateDepositPoints(_user: address, _vaultId: uint256, _vaultAddr: address, _asset: address, _a: addys.Addys = empty(addys.Addys)): nonpayable
    def claimLootForUser(_user: address, _caller: address, _shouldStake: bool, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable

interface RipeGovVault:
    def depositTokensWithLockDuration(_user: address, _asset: address, _amount: uint256, _lockDuration: uint256, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def adjustLock(_user: address, _asset: address, _newLockDuration: uint256, _a: addys.Addys = empty(addys.Addys)): nonpayable
    def releaseLock(_user: address, _asset: address, _a: addys.Addys = empty(addys.Addys)): nonpayable

interface Ledger:
    def getDepositLedgerData(_user: address, _vaultId: uint256) -> DepositLedgerData: view
    def addVaultToUser(_user: address, _vaultId: uint256): nonpayable

interface AddressRegistry:
    def getRegId(_addr: address) -> uint256: view
    def getAddr(_regId: uint256) -> address: view

interface BondRoom:
    def purchaseRipeBond(_recipient: address, _paymentAsset: address, _paymentAmount: uint256, _lockDuration: uint256, _caller: address, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable

interface PriceDesk:
    def addGreenRefPoolSnapshot() -> bool: nonpayable

interface UnderscoreAgentFactory:
    def isUserWallet(_addr: address) -> bool: view

interface UnderscoreRegistry:
    def getAddy(_addyId: uint256) -> address: view

interface UnderscoreWallet:
    def walletConfig() -> address: view

interface UnderscoreWalletConfig:
    def owner() -> address: view

struct DepositLedgerData:
    isParticipatingInVault: bool
    numUserVaults: uint256

struct TellerDepositConfig:
    canDepositGeneral: bool
    canDepositAsset: bool
    doesVaultSupportAsset: bool
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

event UserConfigSet:
    user: indexed(address)
    canAnyoneDeposit: bool
    canAnyoneRepayDebt: bool
    canAnyoneBondForUser: bool
    caller: indexed(address)

event UserDelegationSet:
    user: indexed(address) 
    delegate: indexed(address)
    canWithdraw: bool
    canBorrow: bool
    canClaimFromStabPool: bool 
    canClaimLoot: bool
    caller: indexed(address)

MAX_BALANCE_ACTION: constant(uint256) = 20
MAX_CLAIM_USERS: constant(uint256) = 25
MAX_COLLATERAL_REDEMPTIONS: constant(uint256) = 20
MAX_AUCTION_PURCHASES: constant(uint256) = 20
MAX_LIQ_USERS: constant(uint256) = 50
MAX_STAB_CLAIMS: constant(uint256) = 15
MAX_STAB_REDEMPTIONS: constant(uint256) = 15
STABILITY_POOL_ID: constant(uint256) = 1
RIPE_GOV_VAULT_ID: constant(uint256) = 2
UNDERSCORE_AGENT_FACTORY_ID: constant(uint256) = 1


@deploy
def __init__(_ripeHq: address):
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, False, False) # no minting


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
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()
    return self._deposit(_asset, _amount, _user, _vaultAddr, _vaultId, msg.sender, 0, False, True, a)


@nonreentrant
@external
def depositMany(_user: address, _deposits: DynArray[DepositAction, MAX_BALANCE_ACTION]) -> uint256:
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()
    for d: DepositAction in _deposits:
        self._deposit(d.asset, d.amount, _user, d.vaultAddr, d.vaultId, msg.sender, 0, False, False, a)
    extcall PriceDesk(a.priceDesk).addGreenRefPoolSnapshot()
    extcall CreditEngine(a.creditEngine).updateDebtForUser(_user, a)
    return len(_deposits)


@external
def depositFromTrusted(
    _user: address,
    _vaultId: uint256,
    _asset: address,
    _amount: uint256,
    _lockDuration: uint256,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    assert addys._isValidRipeAddr(msg.sender) # dev: no perms
    a: addys.Addys = addys._getAddys(_a)
    return self._deposit(_asset, _amount, _user, empty(address), _vaultId, msg.sender, _lockDuration, False, False, a)


# core logic


@internal
def _deposit(
    _asset: address,
    _amount: uint256,
    _user: address,
    _vaultAddr: address,
    _vaultId: uint256,
    _depositor: address,
    _lockDuration: uint256,
    _areFundsHereAlready: bool,
    _shouldPerformHouseKeeping: bool,
    _a: addys.Addys,
) -> uint256:
    vaultAddr: address = empty(address)
    vaultId: uint256 = 0
    vaultAddr, vaultId = self._getVaultAddrAndId(_asset, _vaultAddr, _vaultId, _a.vaultBook, _a.missionControl)

    # get ledger data
    d: DepositLedgerData = staticcall Ledger(_a.ledger).getDepositLedgerData(_user, vaultId)
    amount: uint256 = self._validateOnDeposit(_asset, _amount, _user, vaultId, vaultAddr, _depositor, _areFundsHereAlready, d, _a.missionControl)

    # transfer tokens
    if _areFundsHereAlready:
        assert extcall IERC20(_asset).transfer(vaultAddr, amount, default_return_value=True) # dev: could not transfer
    else:
        assert extcall IERC20(_asset).transferFrom(_depositor, vaultAddr, amount, default_return_value=True) # dev: token transfer failed

    # deposit tokens
    if _lockDuration != 0:
        amount = extcall RipeGovVault(vaultAddr).depositTokensWithLockDuration(_user, _asset, amount, _lockDuration, _a)
    else:
        amount = extcall Vault(vaultAddr).depositTokensInVault(_user, _asset, amount, _a)

    # register vault participation
    if not d.isParticipatingInVault:
        extcall Ledger(_a.ledger).addVaultToUser(_user, vaultId)

    # update lootbox points
    extcall Lootbox(_a.lootbox).updateDepositPoints(_user, vaultId, vaultAddr, _asset, _a)

    # perform house keeping
    if _shouldPerformHouseKeeping:
        extcall PriceDesk(_a.priceDesk).addGreenRefPoolSnapshot()
        extcall CreditEngine(_a.creditEngine).updateDebtForUser(_user, _a)

    log TellerDeposit(user=_user, depositor=_depositor, asset=_asset, amount=amount, vaultAddr=vaultAddr, vaultId=vaultId)
    return amount


# validation


@view
@internal
def _validateOnDeposit(
    _asset: address,
    _amount: uint256,
    _user: address,
    _vaultId: uint256,
    _vaultAddr: address,
    _depositor: address,
    _areFundsHereAlready: bool,
    _d: DepositLedgerData,
    _missionControl: address,
) -> uint256:
    config: TellerDepositConfig = staticcall MissionControl(_missionControl).getTellerDepositConfig(_vaultId, _asset, _user)
    assert config.canDepositGeneral # dev: protocol deposits disabled
    assert config.canDepositAsset # dev: asset deposits disabled
    assert config.doesVaultSupportAsset # dev: vault does not support asset
    assert config.isUserAllowed # dev: user not on whitelist

    # trusted depositor
    isRipeDepartment: bool = addys._isValidRipeAddr(_depositor)

    # make sure depositor is allowed to deposit for user
    if _user != _depositor and not config.canAnyoneDeposit:
        assert isRipeDepartment or self._isUnderscoreWalletOwner(_user, _depositor, _missionControl) # dev: cannot deposit for user

    # avail amount
    holder: address = _depositor
    if _areFundsHereAlready:
        holder = self
    amount: uint256 = min(_amount, staticcall IERC20(_asset).balanceOf(holder))
    assert amount != 0 # dev: cannot deposit 0

    # if depositing from ripe dept, skip these limits
    if isRipeDepartment:
        return amount
    
    # vault data
    vd: Vault.VaultDataOnDeposit = staticcall Vault(_vaultAddr).getVaultDataOnDeposit(_user, _asset)

    # check max vaults, max assets per vault
    if not _d.isParticipatingInVault:
        assert _d.numUserVaults < config.perUserMaxVaults # dev: reached max vaults

    elif not vd.hasPosition:
        assert vd.numAssets < config.perUserMaxAssetsPerVault # dev: reached max assets per vault

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
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()
    amount: uint256 = self._withdraw(_asset, _amount, _user, _vaultAddr, _vaultId, msg.sender, a)
    extcall PriceDesk(a.priceDesk).addGreenRefPoolSnapshot()
    assert extcall CreditEngine(a.creditEngine).updateDebtForUser(_user, a) # dev: bad debt health
    return amount


@nonreentrant
@external
def withdrawMany(_user: address, _withdrawals: DynArray[WithdrawalAction, MAX_BALANCE_ACTION]) -> uint256:
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()
    for w: WithdrawalAction in _withdrawals:
        self._withdraw(w.asset, w.amount, _user, w.vaultAddr, w.vaultId, msg.sender, a)
    extcall PriceDesk(a.priceDesk).addGreenRefPoolSnapshot()
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
    vaultAddr, vaultId = self._getVaultAddrAndId(_asset, _vaultAddr, _vaultId, _a.vaultBook, _a.missionControl)

    # validation
    amount: uint256 = self._validateOnWithdrawal(_asset, _amount, _user, vaultAddr, vaultId, _caller, _a)

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

    config: TellerWithdrawConfig = staticcall MissionControl(_a.missionControl).getTellerWithdrawConfig(_asset, _user, _caller)
    assert config.canWithdrawGeneral # dev: protocol withdrawals disabled
    assert config.canWithdrawAsset # dev: asset withdrawals disabled
    assert config.isUserAllowed # dev: user not on whitelist

    # make sure caller is allowed to withdraw for user
    if _user != _caller and not config.canWithdrawForUser:
        assert self._isUnderscoreWalletOwner(_user, _caller, _a.missionControl) # dev: not allowed to withdraw for user

    # max withdrawable
    maxWithdrawable: uint256 = staticcall CreditEngine(_a.creditEngine).getMaxWithdrawableForAsset(_user, _vaultId, _asset, _vaultAddr, _a)
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
    _wantsSavingsGreen: bool = True,
    _shouldEnterStabPool: bool = False,
) -> uint256:
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()
    extcall PriceDesk(a.priceDesk).addGreenRefPoolSnapshot() # do before borrow
    return extcall CreditEngine(a.creditEngine).borrowForUser(_user, _greenAmount, _wantsSavingsGreen, _shouldEnterStabPool, msg.sender, a)


# repay


@nonreentrant
@external
def repay(
    _paymentAmount: uint256 = max_value(uint256),
    _user: address = msg.sender,
    _isPaymentSavingsGreen: bool = False,
    _shouldRefundSavingsGreen: bool = True,
) -> bool:
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()
    extcall PriceDesk(a.priceDesk).addGreenRefPoolSnapshot() # do before
    greenAmount: uint256 = self._handleGreenPayment(_isPaymentSavingsGreen, _paymentAmount, a.creditEngine, a.greenToken, a.savingsGreen)
    return extcall CreditEngine(a.creditEngine).repayForUser(_user, greenAmount, _shouldRefundSavingsGreen, msg.sender, a)


# redeem collateral


@nonreentrant
@external
def redeemCollateral(
    _user: address,
    _vaultId: uint256,
    _asset: address,
    _paymentAmount: uint256 = max_value(uint256),
    _isPaymentSavingsGreen: bool = False,
    _shouldTransferBalance: bool = False,
    _shouldRefundSavingsGreen: bool = True,
    _recipient: address = msg.sender,
) -> uint256:
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()
    greenAmount: uint256 = self._handleGreenPayment(_isPaymentSavingsGreen, _paymentAmount, a.creditEngine, a.greenToken, a.savingsGreen)
    greenSpent: uint256 = extcall CreditEngine(a.creditEngine).redeemCollateral(_user, _vaultId, _asset, greenAmount, _recipient, msg.sender, _shouldTransferBalance, _shouldRefundSavingsGreen, a)
    extcall PriceDesk(a.priceDesk).addGreenRefPoolSnapshot()
    extcall CreditEngine(a.creditEngine).updateDebtForUser(_recipient, a)
    return greenSpent


@nonreentrant
@external
def redeemCollateralFromMany(
    _redemptions: DynArray[CollateralRedemption, MAX_COLLATERAL_REDEMPTIONS],
    _paymentAmount: uint256 = max_value(uint256),
    _isPaymentSavingsGreen: bool = False,
    _shouldTransferBalance: bool = False,
    _shouldRefundSavingsGreen: bool = True,
    _recipient: address = msg.sender,
) -> uint256:
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()
    greenAmount: uint256 = self._handleGreenPayment(_isPaymentSavingsGreen, _paymentAmount, a.creditEngine, a.greenToken, a.savingsGreen)
    greenSpent: uint256 = extcall CreditEngine(a.creditEngine).redeemCollateralFromMany(_redemptions, greenAmount, _recipient, msg.sender, _shouldTransferBalance, _shouldRefundSavingsGreen, a)
    extcall PriceDesk(a.priceDesk).addGreenRefPoolSnapshot()
    extcall CreditEngine(a.creditEngine).updateDebtForUser(_recipient, a)
    return greenSpent


################
# Liquidations #
################


# liquidate users


@nonreentrant
@external
def liquidateUser(
    _liqUser: address,
    _wantsSavingsGreen: bool = True,
) -> uint256:
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()
    keeperRewards: uint256 = extcall AuctionHouse(a.auctionHouse).liquidateUser(_liqUser, msg.sender, _wantsSavingsGreen, a)
    extcall PriceDesk(a.priceDesk).addGreenRefPoolSnapshot()
    extcall CreditEngine(a.creditEngine).updateDebtForUser(msg.sender, a)
    return keeperRewards


@nonreentrant
@external
def liquidateManyUsers(
    _liqUsers: DynArray[address, MAX_LIQ_USERS],
    _wantsSavingsGreen: bool = True,
) -> uint256:
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()
    keeperRewards: uint256 = extcall AuctionHouse(a.auctionHouse).liquidateManyUsers(_liqUsers, msg.sender, _wantsSavingsGreen, a)
    extcall PriceDesk(a.priceDesk).addGreenRefPoolSnapshot()
    extcall CreditEngine(a.creditEngine).updateDebtForUser(msg.sender, a)
    return keeperRewards


# buy fungible auctions


@nonreentrant
@external
def buyFungibleAuction(
    _liqUser: address,
    _vaultId: uint256,
    _asset: address,
    _paymentAmount: uint256 = max_value(uint256),
    _isPaymentSavingsGreen: bool = False,
    _shouldTransferBalance: bool = False,
    _shouldRefundSavingsGreen: bool = True,
    _recipient: address = msg.sender,
) -> uint256:
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()
    greenAmount: uint256 = self._handleGreenPayment(_isPaymentSavingsGreen, _paymentAmount, a.auctionHouse, a.greenToken, a.savingsGreen)
    greenSpent: uint256 = extcall AuctionHouse(a.auctionHouse).buyFungibleAuction(_liqUser, _vaultId, _asset, greenAmount, _recipient, msg.sender, _shouldTransferBalance, _shouldRefundSavingsGreen, a)
    extcall PriceDesk(a.priceDesk).addGreenRefPoolSnapshot()
    extcall CreditEngine(a.creditEngine).updateDebtForUser(_recipient, a)
    return greenSpent


@nonreentrant
@external
def buyManyFungibleAuctions(
    _purchases: DynArray[FungAuctionPurchase, MAX_AUCTION_PURCHASES],
    _paymentAmount: uint256 = max_value(uint256),
    _isPaymentSavingsGreen: bool = False,
    _shouldTransferBalance: bool = False,
    _shouldRefundSavingsGreen: bool = True,
    _recipient: address = msg.sender,
) -> uint256:
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()
    greenAmount: uint256 = self._handleGreenPayment(_isPaymentSavingsGreen, _paymentAmount, a.auctionHouse, a.greenToken, a.savingsGreen)
    greenSpent: uint256 = extcall AuctionHouse(a.auctionHouse).buyManyFungibleAuctions(_purchases, greenAmount, _recipient, msg.sender, _shouldTransferBalance, _shouldRefundSavingsGreen, a)
    extcall CreditEngine(a.creditEngine).updateDebtForUser(_recipient, a)
    extcall PriceDesk(a.priceDesk).addGreenRefPoolSnapshot()
    return greenSpent


###################
# Stability Pools #
###################


# deposit green into stab pool


@nonreentrant
@external
def convertToSavingsGreenAndDepositIntoStabPool(_user: address = msg.sender, _greenAmount: uint256 = max_value(uint256)) -> uint256:
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()

    # transfer GREEN to this contract
    greenAmount: uint256 = min(_greenAmount, staticcall IERC20(a.greenToken).balanceOf(msg.sender))
    assert greenAmount != 0 # dev: cannot deposit 0 green
    assert extcall IERC20(a.greenToken).transferFrom(msg.sender, self, greenAmount, default_return_value=True) # dev: token transfer failed

    # put GREEN into sGREEN
    assert extcall IERC20(a.greenToken).approve(a.savingsGreen, greenAmount, default_return_value=True) # dev: green approval failed
    sGreenAmount: uint256 = extcall IERC4626(a.savingsGreen).deposit(greenAmount, self)
    assert extcall IERC20(a.greenToken).approve(a.savingsGreen, 0, default_return_value=True) # dev: green approval failed

    return self._deposit(a.savingsGreen, sGreenAmount, _user, empty(address), STABILITY_POOL_ID, msg.sender, 0, True, True, a)


# claims


@nonreentrant
@external
def claimFromStabilityPool(
    _vaultId: uint256,
    _stabAsset: address,
    _claimAsset: address,
    _maxUsdValue: uint256 = max_value(uint256),
    _user: address = msg.sender,
    _shouldAutoDeposit: bool = False,
) -> uint256:
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()
    vaultAddr: address = staticcall AddressRegistry(a.vaultBook).getAddr(_vaultId)
    claimUsdValue: uint256 = extcall StabVault(vaultAddr).claimFromStabilityPool(_user, _stabAsset, _claimAsset, _maxUsdValue, msg.sender, _shouldAutoDeposit, a)
    extcall PriceDesk(a.priceDesk).addGreenRefPoolSnapshot()
    assert extcall CreditEngine(a.creditEngine).updateDebtForUser(msg.sender, a) # dev: bad debt health
    return claimUsdValue


@nonreentrant
@external
def claimManyFromStabilityPool(
    _vaultId: uint256,
    _claims: DynArray[StabPoolClaim, MAX_STAB_CLAIMS],
    _user: address = msg.sender,
    _shouldAutoDeposit: bool = False,
) -> uint256:
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()
    vaultAddr: address = staticcall AddressRegistry(a.vaultBook).getAddr(_vaultId)
    claimUsdValue: uint256 = extcall StabVault(vaultAddr).claimManyFromStabilityPool(_user, _claims, msg.sender, _shouldAutoDeposit, a)
    extcall PriceDesk(a.priceDesk).addGreenRefPoolSnapshot()
    assert extcall CreditEngine(a.creditEngine).updateDebtForUser(msg.sender, a) # dev: bad debt health
    return claimUsdValue


# redemptions


@nonreentrant
@external
def redeemFromStabilityPool(
    _vaultId: uint256,
    _claimAsset: address,
    _paymentAmount: uint256 = max_value(uint256),
    _isPaymentSavingsGreen: bool = False,
    _shouldRefundSavingsGreen: bool = True,
    _shouldAutoDeposit: bool = False,
) -> uint256:
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()
    vaultAddr: address = staticcall AddressRegistry(a.vaultBook).getAddr(_vaultId)
    greenAmount: uint256 = self._handleGreenPayment(_isPaymentSavingsGreen, _paymentAmount, vaultAddr, a.greenToken, a.savingsGreen)
    greenSpent: uint256 = extcall StabVault(vaultAddr).redeemFromStabilityPool(_claimAsset, greenAmount, msg.sender, _shouldRefundSavingsGreen, _shouldAutoDeposit, a)
    extcall PriceDesk(a.priceDesk).addGreenRefPoolSnapshot()
    extcall CreditEngine(a.creditEngine).updateDebtForUser(msg.sender, a)
    return greenSpent


@nonreentrant
@external
def redeemManyFromStabilityPool(
    _vaultId: uint256,
    _redemptions: DynArray[StabPoolRedemption, MAX_STAB_REDEMPTIONS],
    _paymentAmount: uint256 = max_value(uint256),
    _isPaymentSavingsGreen: bool = False,
    _shouldRefundSavingsGreen: bool = True,
    _shouldAutoDeposit: bool = False,
) -> uint256:
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()
    vaultAddr: address = staticcall AddressRegistry(a.vaultBook).getAddr(_vaultId)
    greenAmount: uint256 = self._handleGreenPayment(_isPaymentSavingsGreen, _paymentAmount, vaultAddr, a.greenToken, a.savingsGreen)
    greenSpent: uint256 = extcall StabVault(vaultAddr).redeemManyFromStabilityPool(_redemptions, greenAmount, msg.sender, _shouldRefundSavingsGreen, _shouldAutoDeposit, a)
    extcall PriceDesk(a.priceDesk).addGreenRefPoolSnapshot()
    extcall CreditEngine(a.creditEngine).updateDebtForUser(msg.sender, a)
    return greenSpent


###########
# Rewards #
###########


# claim loot


@nonreentrant
@external
def claimLoot(_user: address = msg.sender, _shouldStake: bool = True) -> uint256:
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()
    totalRipe: uint256 = extcall Lootbox(a.lootbox).claimLootForUser(_user, msg.sender, _shouldStake, a)
    extcall PriceDesk(a.priceDesk).addGreenRefPoolSnapshot()
    extcall CreditEngine(a.creditEngine).updateDebtForUser(_user, a)
    return totalRipe


# claim for many users


@nonreentrant
@external
def claimLootForManyUsers(_users: DynArray[address, MAX_CLAIM_USERS], _shouldStake: bool = True) -> uint256:
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()
    totalRipe: uint256 = extcall Lootbox(a.lootbox).claimLootForManyUsers(_users, msg.sender, _shouldStake, a)
    extcall PriceDesk(a.priceDesk).addGreenRefPoolSnapshot()
    extcall CreditEngine(a.creditEngine).updateDebtForUser(msg.sender, a)
    return totalRipe


##################
# Ripe Gov Vault #
##################


@nonreentrant
@external
def adjustLock(_asset: address, _newLockDuration: uint256, _user: address = msg.sender):
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()
    vaultAddr: address = staticcall AddressRegistry(a.vaultBook).getAddr(RIPE_GOV_VAULT_ID)

    # validate underscore wallet
    if _user != msg.sender:
        assert self._isUnderscoreWalletOwner(_user, msg.sender, a.missionControl) # dev: not owner of underscore wallet

    extcall RipeGovVault(vaultAddr).adjustLock(_user, _asset, _newLockDuration, a)
    extcall PriceDesk(a.priceDesk).addGreenRefPoolSnapshot()
    extcall CreditEngine(a.creditEngine).updateDebtForUser(_user, a)


@nonreentrant
@external
def releaseLock(_asset: address, _user: address = msg.sender):
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()
    vaultAddr: address = staticcall AddressRegistry(a.vaultBook).getAddr(RIPE_GOV_VAULT_ID)

    # validate underscore wallet
    if _user != msg.sender:
        assert self._isUnderscoreWalletOwner(_user, msg.sender, a.missionControl) # dev: not owner of underscore wallet

    extcall RipeGovVault(vaultAddr).releaseLock(_user, _asset, a)
    extcall PriceDesk(a.priceDesk).addGreenRefPoolSnapshot()
    extcall CreditEngine(a.creditEngine).updateDebtForUser(_user, a)


##################
# Bond Purchases #
##################


@nonreentrant
@external
def purchaseRipeBond(
    _paymentAsset: address,
    _paymentAmount: uint256 = max_value(uint256),
    _lockDuration: uint256 = 0,
    _recipient: address = msg.sender,
) -> uint256:
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()
    paymentAmount: uint256 = min(_paymentAmount, staticcall IERC20(_paymentAsset).balanceOf(msg.sender))
    assert extcall IERC20(_paymentAsset).transferFrom(msg.sender, a.bondRoom, paymentAmount, default_return_value=True) # dev: token transfer failed
    ripePayout: uint256 = extcall BondRoom(a.bondRoom).purchaseRipeBond(_recipient, _paymentAsset, paymentAmount, _lockDuration, msg.sender, a)
    extcall PriceDesk(a.priceDesk).addGreenRefPoolSnapshot()
    extcall CreditEngine(a.creditEngine).updateDebtForUser(_recipient, a)
    return ripePayout


###############
# User Config #
###############


@external
def setUserConfig(
    _user: address = msg.sender,
    _canAnyoneDeposit: bool = True,
    _canAnyoneRepayDebt: bool = True,
    _canAnyoneBondForUser: bool = True,
) -> bool:
    assert not deptBasics.isPaused # dev: contract paused
    mc: address = addys._getMissionControlAddr()

    # validate underscore wallet
    if _user != msg.sender:
        assert self._isUnderscoreWalletOwner(_user, msg.sender, mc) # dev: not owner of underscore wallet

    return self._setUserConfig(_user, _canAnyoneDeposit, _canAnyoneRepayDebt, _canAnyoneBondForUser, mc)


@internal
def _setUserConfig(
    _user: address,
    _canAnyoneDeposit: bool,
    _canAnyoneRepayDebt: bool,
    _canAnyoneBondForUser: bool,
    _mc: address
) -> bool:
    userConfig: cs.UserConfig = cs.UserConfig(
        canAnyoneDeposit=_canAnyoneDeposit,
        canAnyoneRepayDebt=_canAnyoneRepayDebt,
        canAnyoneBondForUser=_canAnyoneBondForUser,
    )
    extcall MissionControl(_mc).setUserConfig(_user, userConfig)
    log UserConfigSet(user=_user, canAnyoneDeposit=_canAnyoneDeposit, canAnyoneRepayDebt=_canAnyoneRepayDebt, canAnyoneBondForUser=_canAnyoneBondForUser, caller=msg.sender)
    return True


# delegation


@external
def setUserDelegation(
    _delegate: address,
    _user: address = msg.sender,
    _canWithdraw: bool = True,
    _canBorrow: bool = True,
    _canClaimFromStabPool: bool = True,
    _canClaimLoot: bool = True,
) -> bool:
    assert not deptBasics.isPaused # dev: contract paused
    assert _delegate != empty(address) # dev: invalid delegate
    assert _delegate != _user # dev: cannot delegate to self

    # validate underscore wallet
    mc: address = addys._getMissionControlAddr()
    if _user != msg.sender:
        assert self._isUnderscoreWalletOwner(_user, msg.sender, mc) # dev: not owner of underscore wallet
        assert _delegate != msg.sender # dev: cannot delegate to owner

    return self._setUserDelegation(_delegate, _user, _canWithdraw, _canBorrow, _canClaimFromStabPool, _canClaimLoot, mc)


@internal
def _setUserDelegation(
    _delegate: address,
    _user: address,
    _canWithdraw: bool,
    _canBorrow: bool,
    _canClaimFromStabPool: bool,
    _canClaimLoot: bool,
    _mc: address
) -> bool:
    config: cs.ActionDelegation = cs.ActionDelegation(
        canWithdraw=_canWithdraw,
        canBorrow=_canBorrow,
        canClaimFromStabPool=_canClaimFromStabPool,
        canClaimLoot=_canClaimLoot,
    )
    extcall MissionControl(_mc).setUserDelegation(_user, _delegate, config)
    log UserDelegationSet(user=_user, delegate=_delegate, canWithdraw=_canWithdraw, canBorrow=_canBorrow, canClaimFromStabPool=_canClaimFromStabPool, canClaimLoot=_canClaimLoot, caller=msg.sender)
    return True


# underscore helpers


@external
def setUndyLegoAccess(_legoAddr: address) -> bool:
    # NOTE: failing gracefully here to not brick underscore wallets

    mc: address = addys._getMissionControlAddr()
    if mc == empty(address):
        return False

    if _legoAddr == empty(address):
        return False

    if not self._isUnderscoreWallet(msg.sender, mc):
        return False

    # set config
    self._setUserConfig(msg.sender, True, True, True, mc)
    self._setUserDelegation(_legoAddr, msg.sender, True, True, True, True, mc)
    return True


#############
# Utilities #
#############


# vault info 


@view
@internal
def _getVaultAddrAndId(
    _asset: address,
    _vaultAddr: address,
    _vaultId: uint256,
    _vaultBook: address,
    _missionControl: address,
) -> (address, uint256):
    vaultAddr: address = empty(address)
    vaultId: uint256 = 0

    # if no vault data specified, get first vault id for asset
    if _vaultAddr == empty(address) and _vaultId == 0:
        vaultId = staticcall MissionControl(_missionControl).getFirstVaultIdForAsset(_asset)
        assert vaultId != 0 # dev: invalid asset
        vaultAddr = staticcall AddressRegistry(_vaultBook).getAddr(vaultId)
        assert vaultAddr != empty(address) # dev: invalid vault id

    # vault id
    elif _vaultId != 0:
        vaultAddr = staticcall AddressRegistry(_vaultBook).getAddr(_vaultId)
        assert vaultAddr != empty(address) # dev: invalid vault id
        vaultId = _vaultId
        if _vaultAddr != empty(address):
            assert vaultAddr == _vaultAddr # dev: vault id and vault addr mismatch

    # vault addr
    elif _vaultAddr != empty(address):
        vaultId = staticcall AddressRegistry(_vaultBook).getRegId(_vaultAddr) # dev: invalid vault addr
        assert vaultId != 0 # dev: invalid vault addr
        vaultAddr = _vaultAddr

    return vaultAddr, vaultId


# green payments


@internal
def _handleGreenPayment(
    _isPaymentSavingsGreen: bool,
    _amount: uint256,
    _recipient: address,
    _greenToken: address,
    _savingsGreen: address,
) -> uint256:
    asset: address = _greenToken
    if _isPaymentSavingsGreen:
        asset = _savingsGreen

    amount: uint256 = min(_amount, staticcall IERC20(asset).balanceOf(msg.sender))
    assert amount != 0 # dev: cannot transfer 0 amount
    assert _recipient != empty(address) # dev: invalid recipient

    # savings green - unwrap it and transfer to recipient
    if _isPaymentSavingsGreen:
        assert extcall IERC20(_savingsGreen).transferFrom(msg.sender, self, amount, default_return_value=True) # dev: token transfer failed
        amount = extcall IERC4626(_savingsGreen).redeem(amount, _recipient, self) # dev: savings green redeem failed

    # normal green - transfer directly to recipient
    else:
        assert extcall IERC20(_greenToken).transferFrom(msg.sender, _recipient, amount, default_return_value=True) # dev: token transfer failed

    return amount


# underscore ownership check


@view
@external
def isUnderscoreWalletOwner(_user: address, _caller: address, _mc: address = empty(address)) -> bool:
    missionControl: address = _mc
    if _mc == empty(address):
        missionControl = addys._getMissionControlAddr()
    return self._isUnderscoreWalletOwner(_user, _caller, missionControl)


@view
@internal
def _isUnderscoreWallet(_user: address, _mc: address) -> bool:
    underscore: address = staticcall MissionControl(_mc).underscoreRegistry()
    if underscore == empty(address):
        return False

    agentFactory: address = staticcall UnderscoreRegistry(underscore).getAddy(UNDERSCORE_AGENT_FACTORY_ID)
    if agentFactory == empty(address):
        return False

    # check if user is underscore wallet
    return staticcall UnderscoreAgentFactory(agentFactory).isUserWallet(_user)


@view
@internal
def _isUnderscoreWalletOwner(_user: address, _caller: address, _mc: address) -> bool:
    if not self._isUnderscoreWallet(_user, _mc):
        return False

    walletConfig: address = staticcall UnderscoreWallet(_user).walletConfig()
    if walletConfig == empty(address):
        return False

    # check if caller is owner
    return staticcall UnderscoreWalletConfig(walletConfig).owner() == _caller