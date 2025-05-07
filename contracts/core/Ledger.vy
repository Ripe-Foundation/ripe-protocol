# @version 0.4.1

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view

# user vault participation
userVaults: public(HashMap[address, HashMap[uint256, uint256]]) # user -> index -> vault id
indexOfVault: public(HashMap[address, HashMap[uint256, uint256]]) # user -> vault id -> index
numUserVaults: public(HashMap[address, uint256]) # user -> num vaults

TELLER_ID: constant(uint256) = 1 # TODO: make sure this is correct

# config
ADDY_REGISTRY: public(immutable(address))


@deploy
def __init__(_addyRegistry: address):
    assert _addyRegistry != empty(address) # dev: invalid addy registry
    ADDY_REGISTRY = _addyRegistry


###############
# User Vaults #
###############


@view
@external
def isVaultRegistered(_user: address, _vaultId: uint256) -> bool:
    return self.indexOfVault[_user][_vaultId] != 0


@external
def addVaultToUser(_user: address, _vaultId: uint256):
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).getAddy(TELLER_ID) # dev: only Teller allowed

    # already participating - fail gracefully
    if self.indexOfVault[_user][_vaultId] != 0:
        return

    # register vault
    vid: uint256 = self.numUserVaults[_user]
    if vid == 0:
        vid = 1 # not using 0 index

    self.userVaults[_user][vid] = _vaultId
    self.indexOfVault[_user][_vaultId] = vid
    self.numUserVaults[_user] = vid + 1


@external
def removeVaultFromUser(_user: address, _vaultId: uint256):
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).getAddy(TELLER_ID) # dev: only Teller allowed

    numUserVaults: uint256 = self.numUserVaults[_user]
    if numUserVaults == 0:
        return

    targetIndex: uint256 = self.indexOfVault[_user][_vaultId]
    if targetIndex == 0:
        return

    # update data
    lastIndex: uint256 = numUserVaults - 1
    self.numUserVaults[_user] = lastIndex
    self.indexOfVault[_user][_vaultId] = 0

    # have last vault replace the target vault
    if targetIndex != lastIndex:
        lastVaultId: uint256 = self.userVaults[_user][lastIndex]
        self.userVaults[_user][targetIndex] = lastVaultId
        self.indexOfVault[_user][lastVaultId] = targetIndex