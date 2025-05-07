# @version 0.4.1

from interfaces import Vault
from ethereum.ercs import IERC20

interface Validator:
    def validateOnWithdrawal(_asset: address, _amount: uint256, _user: address, _vaultAddr: address, _vaultId: uint256, _requester: address) -> (uint256, address, uint256): view
    def validateOnDeposit(_asset: address, _amount: uint256, _user: address, _vaultAddr: address, _vaultId: uint256, _depositor: address) -> (uint256, address, uint256): view
    def hasGoodHealth(_user: address) -> bool: view

interface Ledger:
    def isVaultRegistered(_user: address, _vaultId: uint256) -> bool: view
    def removeVaultFromUser(_user: address, _vaultId: uint256): nonpayable
    def addVaultToUser(_user: address, _vaultId: uint256): nonpayable

interface Lootbox:
    def updatePoints(_user: address, _vaultId: uint256, _asset: address): nonpayable

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view

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
VALIDATOR_ID: constant(uint256) = 4 # TODO: make sure this is correct
LOOTBOX_ID: constant(uint256) = 5 # TODO: make sure this is correct

MAX_BATCH_ACTION: constant(uint256) = 20

# config
isActivated: public(bool)
ADDY_REGISTRY: public(immutable(address))


@deploy
def __init__(_addyRegistry: address):
    assert _addyRegistry != empty(address) # dev: invalid addy registry
    ADDY_REGISTRY = _addyRegistry
    self.isActivated = True


@internal
def getAddys() -> address[3]:
    ar: address = ADDY_REGISTRY
    validator: address = staticcall AddyRegistry(ar).getAddy(VALIDATOR_ID)
    ledger: address = staticcall AddyRegistry(ar).getAddy(LEDGER_ID)
    lootbox: address = staticcall AddyRegistry(ar).getAddy(LOOTBOX_ID)
    return [validator, ledger, lootbox]


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
    return self._addCollateral(_asset, _amount, _user, _vaultAddr, _vaultId, msg.sender, self.getAddys())


@nonreentrant
@external
def addManyCollaterals(_deposits: DynArray[DepositAction, MAX_BATCH_ACTION]) -> uint256:
    assert self.isActivated # dev: not activated
    addys: address[3] = self.getAddys()
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
    _addys: address[3],
) -> uint256:
    validator: address = _addys[0]
    ledger: address = _addys[1]
    lootbox: address = _addys[2]

    # validation
    amount: uint256 = 0
    vaultAddr: address = empty(address)
    vaultId: uint256 = 0
    amount, vaultAddr, vaultId = staticcall Validator(validator).validateOnDeposit(_asset, _amount, _user, _vaultAddr, _vaultId, _depositor)

    # deposit tokens
    assert extcall IERC20(_asset).transferFrom(_depositor, vaultAddr, amount) # dev: token transfer failed
    amount = extcall Vault(vaultAddr).depositTokensInVault(_user, _asset, amount)

    # register vault participation
    if not staticcall Ledger(ledger).isVaultRegistered(_user, vaultId):
        extcall Ledger(ledger).addVaultToUser(_user, vaultId)

    # update lootbox points
    extcall Lootbox(lootbox).updatePoints(_user, _vaultId, _asset)

    log TellerAddCollateral(user=_user, depositor=_depositor, asset=_asset, amount=amount, vaultAddr=vaultAddr, vaultId=vaultId)
    return amount


###############
# Withdrawals #
###############


@nonreentrant
@external
def removeCollateral(
    _asset: address,
    _amount: uint256,
    _user: address = msg.sender,
    _vaultAddr: address = empty(address),
    _vaultId: uint256 = 0,
) -> uint256:
    assert self.isActivated # dev: not activated
    return self._removeCollateral(_asset, _amount, _user, _vaultAddr, _vaultId, msg.sender, self.getAddys())


@nonreentrant
@external
def removeManyCollaterals(_withdrawals: DynArray[WithdrawalAction, MAX_BATCH_ACTION]) -> uint256:
    assert self.isActivated # dev: not activated
    addys: address[3] = self.getAddys()
    for w: WithdrawalAction in _withdrawals:
        self._removeCollateral(w.asset, w.amount, w.user, w.vaultAddr, w.vaultId, msg.sender, addys)
    return len(_withdrawals)


@internal
def _removeCollateral(
    _asset: address,
    _amount: uint256,
    _user: address,
    _vaultAddr: address,
    _vaultId: uint256,
    _requester: address,
    _addys: address[3],
) -> uint256:
    validator: address = _addys[0]
    ledger: address = _addys[1]
    lootbox: address = _addys[2]

    # validation
    amount: uint256 = 0
    vaultAddr: address = empty(address)
    vaultId: uint256 = 0
    amount, vaultAddr, vaultId = staticcall Validator(validator).validateOnWithdrawal(_asset, _amount, _user, _vaultAddr, _vaultId, _requester)

    # withdraw tokens
    isDepleted: bool = False
    amount, isDepleted = extcall Vault(vaultAddr).withdrawTokensFromVault(_user, _asset, amount, _user)

    # deregister vault (if applicable)
    if isDepleted and not staticcall Vault(vaultAddr).isUserInVault(_user):
        extcall Ledger(ledger).removeVaultFromUser(_user, _vaultId)

    # update lootbox points
    extcall Lootbox(lootbox).updatePoints(_user, _vaultId, _asset)

    # check debt health (invariant!)
    assert staticcall Validator(validator).hasGoodHealth(_user) # dev: not healthy

    log TellerRemoveCollateral(user=_user, asset=_asset, requester=_requester, amount=amount, vaultAddr=vaultAddr, vaultId=vaultId, isDepleted=isDepleted)
    return amount
