# @version 0.4.1

from interfaces import Vault
from ethereum.ercs import IERC20

interface Ledger:
    def getDepositLedgerData(_user: address, _vaultId: uint256) -> DepositLedgerData: view
    def isParticipatingInVault(_user: address, _vaultId: uint256) -> bool: view
    def removeVaultFromUser(_user: address, _vaultId: uint256): nonpayable
    def addVaultToUser(_user: address, _vaultId: uint256): nonpayable

interface VaultBook:
    def getVaultAddr(_vaultId: uint256) -> address: view
    def getVaultId(_vaultAddr: address) -> uint256: view

interface ControlRoom:
    def getDepositConfig(_vaultId: uint256, _asset: address, _user: address) -> DepositConfig: view

interface Lootbox:
    def updatePoints(_user: address, _vaultId: uint256, _asset: address): nonpayable

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view

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

struct DepositAction:
    asset: address
    amount: uint256
    user: address
    vaultAddr: address
    vaultId: uint256

struct WithdrawalAction:
    asset: address
    amount: uint256
    user: address
    vaultAddr: address
    vaultId: uint256

event TellerAddCollateral:
    user: indexed(address)
    depositor: indexed(address)
    asset: indexed(address)
    amount: uint256
    vaultAddr: address
    vaultId: uint256

event TellerRemoveCollateral:
    user: indexed(address)
    asset: indexed(address)
    requester: indexed(address)
    amount: uint256
    vaultAddr: address
    vaultId: uint256
    isDepleted: bool

LEDGER_ID: constant(uint256) = 2 # TODO: make sure this is correct
VAULT_BOOK_ID: constant(uint256) = 3 # TODO: make sure this is correct
LOOTBOX_ID: constant(uint256) = 5 # TODO: make sure this is correct
CONTROL_ROOM_ID: constant(uint256) = 6 # TODO: make sure this is correct

MAX_BATCH_ACTION: constant(uint256) = 20

# config
isActivated: public(bool)
ADDY_REGISTRY: public(immutable(address))


@deploy
def __init__(_addyRegistry: address):
    assert _addyRegistry != empty(address) # dev: invalid addy registry
    ADDY_REGISTRY = _addyRegistry
    self.isActivated = True


@view
@internal
def _getAddys() -> address[4]:
    ar: address = ADDY_REGISTRY
    ledger: address = staticcall AddyRegistry(ar).getAddy(LEDGER_ID)
    vaultBook: address = staticcall AddyRegistry(ar).getAddy(VAULT_BOOK_ID)
    lootbox: address = staticcall AddyRegistry(ar).getAddy(LOOTBOX_ID)
    controlRoom: address = staticcall AddyRegistry(ar).getAddy(CONTROL_ROOM_ID)
    return [ledger, vaultBook, lootbox, controlRoom]


############
# Deposits #
############


@nonreentrant
@external
def addCollateral(
    _asset: address,
    _amount: uint256,
    _user: address = msg.sender,
    _vaultAddr: address = empty(address),
    _vaultId: uint256 = 0,
) -> uint256:
    assert self.isActivated # dev: not activated
    return self._addCollateral(_asset, _amount, _user, _vaultAddr, _vaultId, msg.sender, self._getAddys())


@nonreentrant
@external
def addManyCollaterals(_deposits: DynArray[DepositAction, MAX_BATCH_ACTION]) -> uint256:
    assert self.isActivated # dev: not activated
    addys: address[4] = self._getAddys()
    for d: DepositAction in _deposits:
        self._addCollateral(d.asset, d.amount, d.user, d.vaultAddr, d.vaultId, msg.sender, addys)
    return len(_deposits)


@internal
def _addCollateral(
    _asset: address,
    _amount: uint256,
    _user: address,
    _vaultAddr: address,
    _vaultId: uint256,
    _depositor: address,
    _addys: address[4],
) -> uint256:
    ledger: address = _addys[0]
    vaultBook: address = _addys[1]
    lootbox: address = _addys[2]

    # get vault addr and id
    vaultAddr: address = empty(address)
    vaultId: uint256 = 0
    vaultAddr, vaultId = self._getVaultAddrAndId(_vaultAddr, _vaultId, vaultBook)

    # get ledger data
    d: DepositLedgerData = staticcall Ledger(ledger).getDepositLedgerData(_user, vaultId)
    amount: uint256 = self._validateOnDeposit(_asset, _amount, _user, vaultAddr, vaultId, _depositor, d, _addys)

    # deposit tokens
    assert extcall IERC20(_asset).transferFrom(_depositor, vaultAddr, amount) # dev: token transfer failed
    amount = extcall Vault(vaultAddr).depositTokensInVault(_user, _asset, amount)

    # register vault participation
    if not d.isParticipatingInVault:
        extcall Ledger(ledger).addVaultToUser(_user, vaultId)

    # update lootbox points
    extcall Lootbox(lootbox).updatePoints(_user, vaultId, _asset)

    log TellerAddCollateral(user=_user, depositor=_depositor, asset=_asset, amount=amount, vaultAddr=vaultAddr, vaultId=vaultId)
    return amount


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
    _addys: address[4],
) -> uint256:
    controlRoom: address = _addys[3]
    config: DepositConfig = staticcall ControlRoom(controlRoom).getDepositConfig(_vaultId, _asset, _user)
    assert config.canDeposit # dev: cannot deposit
    assert config.isUserAllowed # dev: user not allowed

    # check max vaults, max assets per vault
    vd: Vault.VaultDataOnDeposit = staticcall Vault(_vaultAddr).getVaultDataOnDeposit(_user, _asset)
    if not _d.isParticipatingInVault:
        assert _d.numUserVaults < config.maxDepositVaults # dev: reached max vaults
    elif not vd.hasPosition:
        assert vd.numAssets < config.maxDepositAssetsPerVault # dev: reached max assets per vault

    amount: uint256 = _amount
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


# @nonreentrant
# @external
# def removeCollateral(
#     _asset: address,
#     _amount: uint256,
#     _user: address = msg.sender,
#     _vaultAddr: address = empty(address),
#     _vaultId: uint256 = 0,
# ) -> uint256:
#     assert self.isActivated # dev: not activated
#     return self._removeCollateral(_asset, _amount, _user, _vaultAddr, _vaultId, msg.sender, self._getAddys())


# @nonreentrant
# @external
# def removeManyCollaterals(_withdrawals: DynArray[WithdrawalAction, MAX_BATCH_ACTION]) -> uint256:
#     assert self.isActivated # dev: not activated
#     addys: address[4] = self._getAddys()
#     for w: WithdrawalAction in _withdrawals:
#         self._removeCollateral(w.asset, w.amount, w.user, w.vaultAddr, w.vaultId, msg.sender, addys)
#     return len(_withdrawals)


# @internal
# def _removeCollateral(
#     _asset: address,
#     _amount: uint256,
#     _user: address,
#     _vaultAddr: address,
#     _vaultId: uint256,
#     _requester: address,
#     _addys: address[4],
# ) -> uint256:
#     validator: address = _addys[0]
#     ledger: address = _addys[1]
#     lootbox: address = _addys[2]

#     # validation
#     amount: uint256 = 0
#     vaultAddr: address = empty(address)
#     vaultId: uint256 = 0
#     amount, vaultAddr, vaultId = staticcall Validator(validator).validateOnWithdrawal(_asset, _amount, _user, _vaultAddr, _vaultId, _requester)

#     # withdraw tokens
#     isDepleted: bool = False
#     amount, isDepleted = extcall Vault(vaultAddr).withdrawTokensFromVault(_user, _asset, amount, _user)

#     # deregister vault (if applicable)
#     if isDepleted and not staticcall Vault(vaultAddr).isUserInVault(_user):
#         extcall Ledger(ledger).removeVaultFromUser(_user, _vaultId)

#     # update lootbox points
#     extcall Lootbox(lootbox).updatePoints(_user, _vaultId, _asset)

#     # check debt health (invariant!)
#     assert staticcall Validator(validator).hasGoodHealth(_user) # dev: not healthy

#     log TellerRemoveCollateral(user=_user, asset=_asset, requester=_requester, amount=amount, vaultAddr=vaultAddr, vaultId=vaultId, isDepleted=isDepleted)
#     return amount


##############
# Borrowing #
##############


@nonreentrant
@external
def borrow(
    _amount: uint256,
    _user: address = msg.sender,
    _shouldStake: bool = True,
) -> uint256:
    assert self.isActivated # dev: not activated
    return 0


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