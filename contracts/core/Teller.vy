# @version 0.4.1

initializes: addys
exports: addys.__interface__
import contracts.modules.Addys as addys

from interfaces import Vault
from ethereum.ercs import IERC20

interface CreditEngine:
    def repayForUser(_user: address, _amount: uint256, _shouldStakeRefund: bool, _caller: address, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def borrowForUser(_user: address, _amount: uint256, _shouldStake: bool, _caller: address, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def getMaxWithdrawableForAsset(_user: address, _asset: address, _a: addys.Addys = empty(addys.Addys)) -> uint256: view
    def hasGoodDebtHealth(_user: address, _a: addys.Addys = empty(addys.Addys)) -> bool: view

interface Lootbox:
    def updateDepositPoints(_user: address, _vaultId: uint256, _vaultAddr: address, _asset: address, _a: addys.Addys = empty(addys.Addys)): nonpayable
    def claimLootForUser(_user: address, _shouldStake: bool, _caller: address, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable

interface ControlRoom:
    def getWithdrawConfig(_vaultId: uint256, _asset: address, _user: address, _caller: address) -> WithdrawConfig: view
    def getDepositConfig(_vaultId: uint256, _asset: address, _user: address) -> DepositConfig: view

interface Ledger:
    def getDepositLedgerData(_user: address, _vaultId: uint256) -> DepositLedgerData: view
    def addVaultToUser(_user: address, _vaultId: uint256): nonpayable

interface VaultBook:
    def getVaultAddr(_vaultId: uint256) -> address: view
    def getVaultId(_vaultAddr: address) -> uint256: view

struct DepositLedgerData:
    isParticipatingInVault: bool
    numUserVaults: uint256

struct DepositConfig:
    canDeposit: bool
    isUserAllowed: bool
    perUserDepositLimit: uint256
    globalDepositLimit: uint256
    maxDepositAssetsPerVault: uint256
    maxDepositVaults: uint256
    canOthersDepositForUser: bool

struct DepositAction:
    asset: address
    amount: uint256
    vaultAddr: address
    vaultId: uint256

struct WithdrawConfig:
    canWithdraw: bool
    isUserAllowed: bool
    canWithdrawForUser: bool

struct WithdrawalAction:
    asset: address
    amount: uint256
    vaultAddr: address
    vaultId: uint256

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

MAX_BATCH_ACTION: constant(uint256) = 20

# config
isActivated: public(bool)


@deploy
def __init__(_hq: address):
    addys.__init__(_hq)
    self.isActivated = True


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
    assert self.isActivated # dev: not activated
    return self._deposit(_asset, _amount, _user, _vaultAddr, _vaultId, msg.sender, addys._getAddys())


@nonreentrant
@external
def depositMany(_user: address, _deposits: DynArray[DepositAction, MAX_BATCH_ACTION]) -> uint256:
    assert self.isActivated # dev: not activated
    a: addys.Addys = addys._getAddys()
    for d: DepositAction in _deposits:
        self._deposit(d.asset, d.amount, _user, d.vaultAddr, d.vaultId, msg.sender, a)
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
    assert extcall IERC20(_asset).transferFrom(_depositor, vaultAddr, amount) # dev: token transfer failed
    amount = extcall Vault(vaultAddr).depositTokensInVault(_user, _asset, amount)

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
    config: DepositConfig = staticcall ControlRoom(_controlRoom).getDepositConfig(_vaultId, _asset, _user)
    assert config.canDeposit # dev: cannot deposit
    assert config.isUserAllowed # dev: user not allowed

    # make sure depositor is allowed to deposit for user
    if _user != _depositor:
        assert config.canOthersDepositForUser # dev: others cannot deposit for user

    # check max vaults, max assets per vault
    vd: Vault.VaultDataOnDeposit = staticcall Vault(_vaultAddr).getVaultDataOnDeposit(_user, _asset)
    if not _d.isParticipatingInVault:
        assert _d.numUserVaults < config.maxDepositVaults # dev: reached max vaults
    elif not vd.hasPosition:
        assert vd.numAssets < config.maxDepositAssetsPerVault # dev: reached max assets per vault

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
    assert self.isActivated # dev: not activated
    a: addys.Addys = addys._getAddys()
    amount: uint256 = self._withdraw(_asset, _amount, _user, _vaultAddr, _vaultId, msg.sender, a)
    assert staticcall CreditEngine(a.creditEngine).hasGoodDebtHealth(_user, a) # dev: cannot withdraw, bad debt health
    return amount


@nonreentrant
@external
def withdrawMany(_user: address, _withdrawals: DynArray[WithdrawalAction, MAX_BATCH_ACTION]) -> uint256:
    assert self.isActivated # dev: not activated
    a: addys.Addys = addys._getAddys()
    for w: WithdrawalAction in _withdrawals:
        self._withdraw(w.asset, w.amount, _user, w.vaultAddr, w.vaultId, msg.sender, a)
    assert staticcall CreditEngine(a.creditEngine).hasGoodDebtHealth(_user, a) # dev: cannot withdraw, bad debt health
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
    amount, isDepleted = extcall Vault(vaultAddr).withdrawTokensFromVault(_user, _asset, amount, _user)

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

    config: WithdrawConfig = staticcall ControlRoom(_a.controlRoom).getWithdrawConfig(_vaultId, _asset, _user, _caller)
    assert config.canWithdraw # dev: cannot withdraw
    assert config.isUserAllowed # dev: user not allowed

    # make sure caller is allowed to withdraw for user
    if _user != _caller:
        assert config.canWithdrawForUser # dev: invalid caller

    # max withdrawable
    maxWithdrawable: uint256 = staticcall CreditEngine(_a.creditEngine).getMaxWithdrawableForAsset(_user, _asset, _a)
    assert maxWithdrawable != 0 # dev: cannot withdraw anything

    return min(_amount, maxWithdrawable)


########
# Debt #
########


@nonreentrant
@external
def borrow(
    _amount: uint256 = max_value(uint256),
    _user: address = msg.sender,
    _shouldStake: bool = True,
) -> uint256:
    assert self.isActivated # dev: not activated
    a: addys.Addys = addys._getAddys()
    return extcall CreditEngine(a.creditEngine).borrowForUser(_user, _amount, _shouldStake, msg.sender, a)


@nonreentrant
@external
def repay(
    _amount: uint256 = max_value(uint256),
    _user: address = msg.sender,
    _shouldStakeRefund: bool = True,
) -> uint256:
    assert self.isActivated # dev: not activated
    a: addys.Addys = addys._getAddys()
    amount: uint256 = min(_amount, staticcall IERC20(a.greenToken).balanceOf(msg.sender))
    assert extcall IERC20(a.greenToken).transferFrom(msg.sender, a.creditEngine, amount) # dev: token transfer failed
    return extcall CreditEngine(a.creditEngine).repayForUser(_user, amount, _shouldStakeRefund, msg.sender, a)


###########
# Rewards #
###########


@nonreentrant
@external
def claimLoot(_user: address = msg.sender, _shouldStake: bool = True) -> uint256:
    assert self.isActivated # dev: not activated
    a: addys.Addys = addys._getAddys()
    return extcall Lootbox(a.lootbox).claimLootForUser(_user, _shouldStake, msg.sender, a)


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
        vaultAddr = staticcall VaultBook(_vaultBook).getVaultAddr(_vaultId) # dev: invalid vault id
        assert vaultAddr != empty(address) # dev: invalid vault id
        vaultId = _vaultId
        if _vaultAddr != empty(address):
            assert vaultAddr == _vaultAddr # dev: vault id and vault addr mismatch

    # validate vault addr
    elif _vaultAddr != empty(address):
        vaultId = staticcall VaultBook(_vaultBook).getVaultId(_vaultAddr) # dev: invalid vault addr
        assert vaultId != 0 # dev: invalid vault addr
        vaultAddr = _vaultAddr

    return vaultAddr, vaultId


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