# @version 0.4.1

implements: Department

exports: gov.__interface__
exports: registry.__interface__
exports: addys.__interface__
exports: deptBasics.__interface__

initializes: gov
initializes: registry[gov := gov]
initializes: addys
initializes: deptBasics[addys := addys]

import contracts.modules.LocalGov as gov
import contracts.modules.AddressRegistry as registry
import contracts.modules.Addys as addys
import contracts.modules.DeptBasics as deptBasics

from interfaces import Vault
from interfaces import Department

# # staked green
# stakedGreenVault: public(uint256) # vault id
# pendingStakedGreenVault: public(address)

# # staked ripe
# stakedRipeVault: public(uint256) # vault id
# pendingStakedRipeVault: public(address)

# # nft vaults
# isNftVault: public(HashMap[uint256, bool]) # vault id -> is nft vault
# pendingIsNftVault: public(HashMap[address, bool]) # addr -> pending is nft vault


@deploy
def __init__(
    _ripeHq: address,
    _minRegistryTimeLock: uint256,
    _maxRegistryTimeLock: uint256,
):
    gov.__init__(_ripeHq, empty(address), 0, 0, 0)
    registry.__init__(_minRegistryTimeLock, _maxRegistryTimeLock, 0, "VaultBook.vy")
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, False)
