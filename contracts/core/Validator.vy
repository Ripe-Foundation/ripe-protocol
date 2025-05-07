# @version 0.4.1

from interfaces import Vault
from ethereum.ercs import IERC20

interface VaultBook:
    def getVaultAddr(_vaultId: uint256) -> address: view
    def getVaultId(_vaultAddr: address) -> uint256: view

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view

VAULT_BOOK_ID: constant(uint256) = 3 # TODO: make sure this is correct

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


@view
@external
def validateOnDeposit(
    _asset: address,
    _amount: uint256,
    _user: address,
    _vaultAddr: address,
    _vaultId: uint256,
    _depositor: address,
) -> (uint256, address, uint256):
    vaultAddr: address = empty(address)
    vaultId: uint256 = 0
    vaultAddr, vaultId = self._getVaultAddrAndId(_vaultAddr, _vaultId)

    # TODO: implement

    return _amount, vaultAddr, vaultId


###############
# Withdrawals #
###############


@view
@external
def validateOnWithdrawal(
    _asset: address,
    _amount: uint256,
    _user: address,
    _vaultAddr: address,
    _vaultId: uint256,
    _requester: address,
) -> (uint256, address, uint256):
    vaultAddr: address = empty(address)
    vaultId: uint256 = 0
    vaultAddr, vaultId = self._getVaultAddrAndId(_vaultAddr, _vaultId)

    # TODO: implement

    return _amount, vaultAddr, vaultId


########
# Debt #
########


@view
@external
def hasGoodHealth(_user: address) -> bool:

    # TODO: implement

    return True


#############
# Utilities #
#############


@view
@internal
def _getVaultAddrAndId(_vaultAddr: address, _vaultId: uint256) -> (address, uint256):
    vaultBook: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(VAULT_BOOK_ID)

    assert _vaultId != 0 or _vaultAddr != empty(address) # dev: invalid vault id or vault addr
    vaultAddr: address = empty(address)
    vaultId: uint256 = 0

    # validate vault id
    if _vaultId != 0:
        vaultAddr = staticcall VaultBook(vaultBook).getVaultAddr(_vaultId) # dev: invalid vault id
        assert vaultAddr != empty(address) # dev: invalid vault id
        vaultId = _vaultId
        if _vaultAddr != empty(address):
            assert vaultAddr == _vaultAddr # dev: vault id and vault addr mismatch

    # validate vault addr
    elif _vaultAddr != empty(address):
        vaultId = staticcall VaultBook(vaultBook).getVaultId(_vaultAddr) # dev: invalid vault addr
        assert vaultId != 0 # dev: invalid vault addr
        vaultAddr = _vaultAddr

    return vaultAddr, vaultId