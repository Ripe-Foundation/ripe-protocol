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


@view
@external
def getSpecificRipeAllocs(_vaultId: uint256, _asset: address) -> (uint256, uint256):
    # TODO: implement

    return 0, 0


@view
@external
def getTotalRipeAllocs() -> (uint256, uint256):
    # TODO: implement

    return 0, 0