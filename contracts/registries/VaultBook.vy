# @version 0.4.1

initializes: gov
initializes: registry

exports: gov.__interface__

import contracts.modules.LocalGov as gov
import contracts.modules.Registry as registry
from interfaces import Vault

# staked green
stakedGreenVault: public(uint256) # vault id
pendingStakedGreenVault: public(address)

# nft vaults
isNftVault: public(HashMap[uint256, bool]) # vault id -> is nft vault
pendingIsNftVault: public(HashMap[address, bool]) # addr -> pending is nft vault


@deploy
def __init__(
    _addyRegistry: address,
    _minVaultChangeDelay: uint256,
    _maxVaultChangeDelay: uint256,
):
    assert _addyRegistry != empty(address) # dev: invalid addy registry

    # initialize gov
    gov.__init__(empty(address), _addyRegistry, 0, 0)

    # initialize registry
    registry.__init__(_minVaultChangeDelay, _maxVaultChangeDelay, "VaultBook.vy")


##################
# Register Vault #
##################


@view
@external
def isValidNewVaultAddr(_addr: address) -> bool:
    return registry._isValidNewAddy(_addr)


# initiate


@external
def registerNewVault(
    _addr: address,
    _description: String[64],
    _isStakedGreenVault: bool = False,
    _isNftVault: bool = False,
) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    
    # cannot be both
    assert not (_isStakedGreenVault and _isNftVault) # dev: invalid vault type

    isPending: bool = registry._registerNewAddy(_addr, _description)
    if isPending:
        if _isStakedGreenVault:
            self.pendingStakedGreenVault = _addr
        elif _isNftVault:
            self.pendingIsNftVault[_addr] = True

    return isPending


# confirm


@external
def confirmNewVaultRegistration(_addr: address) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    vaultId: uint256 = registry._confirmNewAddy(_addr)
    if vaultId == 0:
        self._cancelPendingVault(_addr)
        return 0

    # set vault id
    assert extcall Vault(_addr).setVaultId(vaultId) # dev: set id failed

    # set staked green vault
    if self.pendingStakedGreenVault == _addr:
        self.stakedGreenVault = vaultId
        self.pendingStakedGreenVault = empty(address)

    # set nft vault
    elif self.pendingIsNftVault[_addr]:
        self.isNftVault[vaultId] = True
        self.pendingIsNftVault[_addr] = False

    return vaultId


# cancel


@external
def cancelPendingNewVault(_addr: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    self._cancelPendingVault(_addr)
    return registry._cancelPendingNewAddy(_addr)


@internal
def _cancelPendingVault(_addr: address):
    if self.pendingIsNftVault[_addr]:
        self.pendingIsNftVault[_addr] = False
    elif self.pendingStakedGreenVault == _addr:
        self.pendingStakedGreenVault = empty(address)


################
# Update Vault #
################


@view
@external
def isValidVaultUpdate(_vaultId: uint256, _newAddr: address) -> bool:
    if self._hasAnyFunds(_vaultId):
        return False
    return registry._isValidAddyUpdate(_vaultId, _newAddr, registry.addyInfo[_vaultId].addr)


@external
def updateVaultAddr(_vaultId: uint256, _newAddr: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    if self._hasAnyFunds(_vaultId):
        return False
    return registry._updateAddyAddr(_vaultId, _newAddr)


@external
def confirmVaultUpdate(_vaultId: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    if self._hasAnyFunds(_vaultId):
        return False
    didUpdate: bool = registry._confirmAddyUpdate(_vaultId)
    if didUpdate:
        vaultAddr: address = registry.addyInfo[_vaultId].addr
        assert extcall Vault(vaultAddr).setVaultId(_vaultId) # dev: set id failed
    return didUpdate


@external
def cancelPendingVaultUpdate(_vaultId: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._cancelPendingAddyUpdate(_vaultId)


#################
# Disable Vault #
#################


@view
@external
def isValidVaultDisable(_vaultId: uint256) -> bool:
    if self._hasAnyFunds(_vaultId):
        return False
    return registry._isValidAddyDisable(_vaultId, registry.addyInfo[_vaultId].addr)


@external
def disableVaultAddr(_vaultId: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    if self._hasAnyFunds(_vaultId):
        return False
    return registry._disableAddyAddr(_vaultId)


@external
def confirmVaultDisable(_vaultId: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    if self._hasAnyFunds(_vaultId):
        return False
    return registry._confirmAddyDisable(_vaultId)


@external
def cancelPendingVaultDisable(_vaultId: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._cancelPendingAddyDisable(_vaultId)


######################
# Vault Change Delay #
######################


@external
def setVaultChangeDelay(_numBlocks: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._setAddyChangeDelay(_numBlocks)


@view
@external
def vaultChangeDelay() -> uint256:
    return registry.addyChangeDelay


@external
def setVaultChangeDelayToMin() -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._setAddyChangeDelay(registry.MIN_ADDY_CHANGE_DELAY)


#################
# Views / Utils #
#################


@view
@external
def numVaultsRaw() -> uint256:
    return registry.numAddys


# is valid


@view
@external
def isValidVaultAddr(_addr: address) -> bool:
    return registry._isValidAddyAddr(_addr)


@view
@external
def isValidVaultId(_vaultId: uint256) -> bool:
    return registry._isValidAddyId(_vaultId)


# lego getters


@view
@external
def getVaultId(_addr: address) -> uint256:
    return registry._getAddyId(_addr)


@view
@external
def getVaultAddr(_vaultId: uint256) -> address:
    return registry._getAddy(_vaultId)


@view
@external
def getVaultInfo(_vaultId: uint256) -> registry.AddyInfo:
    return registry.addyInfo[_vaultId]


@view
@external
def getVaultDescription(_vaultId: uint256) -> String[64]:
    return registry.addyInfo[_vaultId].description


# high level


@view
@external
def getNumVaults() -> uint256:
    return registry._getNumAddys()


@view
@external
def getLastVaultAddr() -> address:
    return registry._getLastAddyAddr()


@view
@external
def getLastVaultId() -> uint256:
    return registry._getLastAddyId()


# other utils


@view
@external
def hasAnyFunds(_vaultId: uint256) -> bool:
    return self._hasAnyFunds(_vaultId)


@view
@internal
def _hasAnyFunds(_vaultId: uint256) -> bool:
    vaultAddr: address = registry._getAddy(_vaultId)
    return staticcall Vault(vaultAddr).hasAnyFunds()


@view
@external
def getStakedGreenVault() -> address:
    return registry._getAddy(self.stakedGreenVault)