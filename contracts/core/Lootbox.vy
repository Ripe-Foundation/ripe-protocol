# @version 0.4.1

from interfaces import Vault
from ethereum.ercs import IERC20

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view

# config
isActivated: public(bool)
ADDY_REGISTRY: public(immutable(address))


@deploy
def __init__(_addyRegistry: address):
    assert _addyRegistry != empty(address) # dev: invalid addy registry
    ADDY_REGISTRY = _addyRegistry
    self.isActivated = True


@external
def updatePoints(_user: address, _vaultId: uint256, _asset: address):

    # TODO: implement

    pass
