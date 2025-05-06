# @version 0.4.1

from interfaces import Vault
from ethereum.ercs import IERC20

interface RipeCodex:
    def validateCollateralDetails(_asset: address, _amount: uint256, _forUser: address, _vaultAddr: address, _vaultId: uint256, _depositor: address) -> (uint256, address, uint256): view

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view

struct Deposit:
    asset: address
    amount: uint256
    forUser: address
    vaultAddr: address
    vaultId: uint256

MAX_DEPOSIT_COUNT: constant(uint256) = 10
VAULT_BOOK_ID: constant(uint256) = 3 # TODO: make sure this is correct
RIPE_CODEX_ID: constant(uint256) = 4 # TODO: make sure this is correct

# config
isActivated: public(bool)
ADDY_REGISTRY: public(immutable(address))


@deploy
def __init__(_addyRegistry: address):
    assert _addyRegistry != empty(address) # dev: invalid addy registry
    ADDY_REGISTRY = _addyRegistry
    self.isActivated = True


############
# Deposits #
############


@nonreentrant
@external
def addCollateral(
    _asset: address,
    _amount: uint256,
    _forUser: address = msg.sender,
    _vaultAddr: address = empty(address),
    _vaultId: uint256 = 0,
) -> uint256:
    assert self.isActivated # dev: not activated
    ripeCodex: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(RIPE_CODEX_ID)
    return self._addCollateral(_asset, _amount, _forUser, _vaultAddr, _vaultId, msg.sender, ripeCodex)


@nonreentrant
@external
def addManyCollaterals(_deposits: DynArray[Deposit, MAX_DEPOSIT_COUNT]) -> uint256:
    assert self.isActivated # dev: not activated
    ripeCodex: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(RIPE_CODEX_ID)
    for d: Deposit in _deposits:
        self._addCollateral(d.asset, d.amount, d.forUser, d.vaultAddr, d.vaultId, msg.sender, ripeCodex)
    return len(_deposits)


@internal
def _addCollateral(
    _asset: address,
    _amount: uint256,
    _forUser: address,
    _vaultAddr: address,
    _vaultId: uint256,
    _depositor: address,
    _ripeCodex: address,
) -> uint256:
    amount: uint256 = 0
    vaultAddr: address = empty(address)
    vaultId: uint256 = 0
    amount, vaultAddr, vaultId = staticcall RipeCodex(_ripeCodex).validateCollateralDetails(_asset, _amount, _forUser, _vaultAddr, _vaultId, _depositor)
    assert extcall IERC20(_asset).transferFrom(_depositor, vaultAddr, amount) # dev: token transfer failed
    return extcall Vault(vaultAddr).depositTokensInVault(_forUser, _asset, amount)