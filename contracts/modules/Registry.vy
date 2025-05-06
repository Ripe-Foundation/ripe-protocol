# @version 0.4.1

struct AddyInfo:
    addr: address
    version: uint256
    lastModified: uint256
    description: String[64]

struct PendingNewAddy:
    description: String[64]
    initiatedBlock: uint256
    confirmBlock: uint256

struct PendingAddyUpdate:
    newAddr: address
    initiatedBlock: uint256
    confirmBlock: uint256

struct PendingAddyDisable:
    initiatedBlock: uint256
    confirmBlock: uint256

event NewAddyPending:
    addr: indexed(address)
    description: String[64]
    confirmBlock: uint256
    registry: String[28]

event NewAddyConfirmed:
    addr: indexed(address)
    addyId: uint256
    description: String[64]
    registry: String[28]

event NewPendingAddyCancelled:
    description: String[64]
    addr: indexed(address)
    initiatedBlock: uint256
    confirmBlock: uint256
    registry: String[28]

event AddyUpdatePending:
    addyId: uint256
    description: String[64]
    newAddr: indexed(address)
    prevAddr: indexed(address)
    version: uint256
    confirmBlock: uint256
    registry: String[28]

event AddyUpdateConfirmed:
    addyId: uint256
    description: String[64]
    newAddr: indexed(address)
    prevAddr: indexed(address)
    version: uint256
    registry: String[28]

event AddyUpdateCancelled:
    addyId: uint256
    description: String[64]
    newAddr: indexed(address)
    prevAddr: indexed(address)
    initiatedBlock: uint256
    confirmBlock: uint256
    registry: String[28]

event AddyDisablePending:
    addyId: uint256
    description: String[64]
    addr: indexed(address)
    version: uint256
    confirmBlock: uint256
    registry: String[28]

event AddyDisableConfirmed:
    addyId: uint256
    description: String[64]
    addr: indexed(address)
    version: uint256
    registry: String[28]

event AddyDisableCancelled:
    addyId: uint256
    description: String[64]
    addr: indexed(address)
    initiatedBlock: uint256
    confirmBlock: uint256
    registry: String[28]

event AddyChangeDelaySet:
    delayBlocks: uint256
    registry: String[28]

# core registry
addyInfo: public(HashMap[uint256, AddyInfo])
addyToId: public(HashMap[address, uint256])
numAddys: public(uint256)

# pending changes
pendingNewAddy: public(HashMap[address, PendingNewAddy]) # addr -> pending new addy
pendingAddyUpdate: public(HashMap[uint256, PendingAddyUpdate]) # addyId -> pending addy update
pendingAddyDisable: public(HashMap[uint256, PendingAddyDisable]) # addyId -> pending addy disable
addyChangeDelay: public(uint256)

MIN_ADDY_CHANGE_DELAY: public(immutable(uint256))
MAX_ADDY_CHANGE_DELAY: public(immutable(uint256))
REGISTRY_STR: public(immutable(String[28]))


@deploy
def __init__(_minAddyChangeDelay: uint256, _maxAddyChangeDelay: uint256, _registryStr: String[28]):
    assert _minAddyChangeDelay < _maxAddyChangeDelay # dev: invalid delay
    MIN_ADDY_CHANGE_DELAY = _minAddyChangeDelay
    MAX_ADDY_CHANGE_DELAY = _maxAddyChangeDelay

    REGISTRY_STR = _registryStr

    # start at 1 index
    self.numAddys = 1


############
# New Addy #
############


@view
@external
def isValidNewAddy(_addr: address) -> bool:
    return self._isValidNewAddy(_addr)


@view
@internal
def _isValidNewAddy(_addr: address) -> bool:
    if _addr == empty(address) or not _addr.is_contract:
        return False
    return self.addyToId[_addr] == 0


@internal
def _registerNewAddy(_addr: address, _description: String[64]) -> bool:
    """
    @notice Initiates the registration process for a new address in the registry
    @dev This function sets up a pending registration that requires confirmation after a delay period
    @param _addr The address to be registered
    @param _description A short description of the address (max 64 characters)
    @return True if the registration was successfully initiated, False if the address is invalid
    """
    if not self._isValidNewAddy(_addr):
        return False

    # set pending
    confirmBlock: uint256 = block.number + self.addyChangeDelay
    self.pendingNewAddy[_addr] = PendingNewAddy(
        description=_description,
        initiatedBlock=block.number,
        confirmBlock=confirmBlock,
    )

    log NewAddyPending(addr=_addr, description=_description, confirmBlock=confirmBlock, registry=REGISTRY_STR)
    return True


@internal
def _confirmNewAddy(_addr: address) -> uint256:
    """
    @notice Confirms a pending address registration after the required delay period
    @dev This function finalizes the registration by assigning an ID and storing the address info
    @param _addr The address to confirm registration for
    @return The assigned ID for the registered address, or 0 if confirmation fails
    """
    data: PendingNewAddy = self.pendingNewAddy[_addr]
    assert data.confirmBlock != 0 and block.number >= data.confirmBlock # dev: time delay not reached
    if not self._isValidNewAddy(_addr):
        self.pendingNewAddy[_addr] = empty(PendingNewAddy) # clear pending
        return 0

    # register new addy
    addyId: uint256 = self.numAddys
    self.addyToId[_addr] = addyId
    self.numAddys = addyId + 1
    self.addyInfo[addyId] = AddyInfo(
        addr=_addr,
        version=1,
        lastModified=block.timestamp,
        description=data.description,
    )

    # clear pending
    self.pendingNewAddy[_addr] = empty(PendingNewAddy)

    log NewAddyConfirmed(addr=_addr, addyId=addyId, description=data.description, registry=REGISTRY_STR)
    return addyId


@internal
def _cancelPendingNewAddy(_addr: address) -> bool:
    """
    @notice Cancels a pending address registration
    @dev This function removes the pending registration and emits a cancellation event
    @param _addr The address whose pending registration should be cancelled
    @return True if the cancellation was successful, reverts if no pending registration exists
    """
    data: PendingNewAddy = self.pendingNewAddy[_addr]
    assert data.confirmBlock != 0 # dev: no pending

    self.pendingNewAddy[_addr] = empty(PendingNewAddy)
    log NewPendingAddyCancelled(description=data.description, addr=_addr, initiatedBlock=data.initiatedBlock, confirmBlock=data.confirmBlock, registry=REGISTRY_STR)
    return True


###############
# Update Addy #
###############


@view
@external
def isValidAddyUpdate(_addyId: uint256, _newAddr: address) -> bool:
    return self._isValidAddyUpdate(_addyId, _newAddr, self.addyInfo[_addyId].addr)


@view
@internal
def _isValidAddyUpdate(_addyId: uint256, _newAddr: address, _prevAddr: address) -> bool:
    if not self._isValidAddyId(_addyId):
        return False
    if not self._isValidNewAddy(_newAddr):
        return False
    return _newAddr != _prevAddr


@internal
def _updateAddyAddr(_addyId: uint256, _newAddr: address) -> bool:
    """
    @notice Initiates an address update for an existing registered address
    @dev This function sets up a pending update that requires confirmation after a delay period
    @param _addyId The ID of the address to update
    @param _newAddr The new address to set
    @return True if the update was successfully initiated, False if the update is invalid
    """
    data: AddyInfo = self.addyInfo[_addyId]
    if not self._isValidAddyUpdate(_addyId, _newAddr, data.addr):
        return False

    # set pending
    confirmBlock: uint256 = block.number + self.addyChangeDelay
    self.pendingAddyUpdate[_addyId] = PendingAddyUpdate(
        newAddr=_newAddr,
        initiatedBlock=block.number,
        confirmBlock=confirmBlock,
    )

    log AddyUpdatePending(addyId=_addyId, description=data.description, newAddr=_newAddr, prevAddr=data.addr, version=data.version, confirmBlock=confirmBlock, registry=REGISTRY_STR)
    return True


@internal
def _confirmAddyUpdate(_addyId: uint256) -> bool:
    """
    @notice Confirms a pending address update after the required delay period
    @dev This function finalizes the update by updating the address info and version
    @param _addyId The ID of the address to confirm update for
    @return True if the update was successfully confirmed, False if confirmation fails
    """
    pendingData: PendingAddyUpdate = self.pendingAddyUpdate[_addyId]
    assert pendingData.confirmBlock != 0 and block.number >= pendingData.confirmBlock # dev: time delay not reached
    data: AddyInfo = self.addyInfo[_addyId]
    prevAddr: address = data.addr # needed for later
    if not self._isValidAddyUpdate(_addyId, pendingData.newAddr, prevAddr):
        self.pendingAddyUpdate[_addyId] = empty(PendingAddyUpdate) # clear pending
        return False

    # update addy data
    data.addr = pendingData.newAddr
    data.lastModified = block.timestamp
    data.version += 1
    self.addyInfo[_addyId] = data
    self.addyToId[pendingData.newAddr] = _addyId

    # handle previous addr
    if prevAddr != empty(address):
        self.addyToId[prevAddr] = 0

    # clear pending
    self.pendingAddyUpdate[_addyId] = empty(PendingAddyUpdate)

    log AddyUpdateConfirmed(addyId=_addyId, description=data.description, newAddr=pendingData.newAddr, prevAddr=prevAddr, version=data.version, registry=REGISTRY_STR)
    return True


@internal
def _cancelPendingAddyUpdate(_addyId: uint256) -> bool:
    """
    @notice Cancels a pending address update
    @dev This function removes the pending update and emits a cancellation event
    @param _addyId The ID of the address whose pending update should be cancelled
    @return True if the cancellation was successful, reverts if no pending update exists
    """
    pendingData: PendingAddyUpdate = self.pendingAddyUpdate[_addyId]
    assert pendingData.confirmBlock != 0 # dev: no pending

    self.pendingAddyUpdate[_addyId] = empty(PendingAddyUpdate)
    prevData: AddyInfo = self.addyInfo[_addyId]
    log AddyUpdateCancelled(addyId=_addyId, description=prevData.description, newAddr=pendingData.newAddr, prevAddr=prevData.addr, initiatedBlock=pendingData.initiatedBlock, confirmBlock=pendingData.confirmBlock, registry=REGISTRY_STR)
    return True


################
# Disable Addy #
################


@view
@external
def isValidAddyDisable(_addyId: uint256) -> bool:
    return self._isValidAddyDisable(_addyId, self.addyInfo[_addyId].addr)


@view
@internal
def _isValidAddyDisable(_addyId: uint256, _prevAddr: address) -> bool:
    if not self._isValidAddyId(_addyId):
        return False
    return _prevAddr != empty(address)


@internal
def _disableAddyAddr(_addyId: uint256) -> bool:
    """
    @notice Initiates the disable process for an existing registered address
    @dev This function sets up a pending disable that requires confirmation after a delay period
    @param _addyId The ID of the address to disable
    @return True if the disable was successfully initiated, False if the disable is invalid
    """
    data: AddyInfo = self.addyInfo[_addyId]
    if not self._isValidAddyDisable(_addyId, data.addr):
        return False

    # set pending
    confirmBlock: uint256 = block.number + self.addyChangeDelay
    self.pendingAddyDisable[_addyId] = PendingAddyDisable(
        initiatedBlock=block.number,
        confirmBlock=confirmBlock,
    )

    log AddyDisablePending(addyId=_addyId, description=data.description, addr=data.addr, version=data.version, confirmBlock=confirmBlock, registry=REGISTRY_STR)
    return True


@internal
def _confirmAddyDisable(_addyId: uint256) -> bool:
    """
    @notice Confirms a pending address disable after the required delay period
    @dev This function finalizes the disable by clearing the address and updating version
    @param _addyId The ID of the address to confirm disable for
    @return True if the disable was successfully confirmed, False if confirmation fails
    """
    pendingData: PendingAddyDisable = self.pendingAddyDisable[_addyId]
    assert pendingData.confirmBlock != 0 and block.number >= pendingData.confirmBlock # dev: time delay not reached
    data: AddyInfo = self.addyInfo[_addyId]
    prevAddr: address = data.addr # needed for later
    if not self._isValidAddyDisable(_addyId, prevAddr):
        self.pendingAddyDisable[_addyId] = empty(PendingAddyDisable) # clear pending
        return False

    # disable addy
    data.addr = empty(address)
    data.lastModified = block.timestamp
    data.version += 1
    self.addyInfo[_addyId] = data
    self.addyToId[prevAddr] = 0

    # clear pending
    self.pendingAddyDisable[_addyId] = empty(PendingAddyDisable)

    log AddyDisableConfirmed(addyId=_addyId, description=data.description, addr=prevAddr, version=data.version, registry=REGISTRY_STR)
    return True


@internal
def _cancelPendingAddyDisable(_addyId: uint256) -> bool:
    """
    @notice Cancels a pending address disable
    @dev This function removes the pending disable and emits a cancellation event
    @param _addyId The ID of the address whose pending disable should be cancelled
    @return True if the cancellation was successful, reverts if no pending disable exists
    """
    data: PendingAddyDisable = self.pendingAddyDisable[_addyId]
    assert data.confirmBlock != 0 # dev: no pending

    self.pendingAddyDisable[_addyId] = empty(PendingAddyDisable)
    prevData: AddyInfo = self.addyInfo[_addyId]
    log AddyDisableCancelled(addyId=_addyId, description=prevData.description, addr=prevData.addr, initiatedBlock=data.initiatedBlock, confirmBlock=data.confirmBlock, registry=REGISTRY_STR)
    return True


################
# Change Delay #
################


@internal
def _setAddyChangeDelay(_numBlocks: uint256) -> bool:
    """
    @notice Sets the delay period required for address changes
    @dev The delay must be between MIN_ADDY_CHANGE_DELAY and MAX_ADDY_CHANGE_DELAY
    @param _numBlocks The number of blocks to set as the delay period
    @return True if the delay was successfully set, reverts if delay is invalid
    """
    assert _numBlocks >= MIN_ADDY_CHANGE_DELAY and _numBlocks <= MAX_ADDY_CHANGE_DELAY # dev: invalid delay
    self.addyChangeDelay = _numBlocks
    log AddyChangeDelaySet(delayBlocks=_numBlocks, registry=REGISTRY_STR)
    return True


#################
# Views / Utils #
#################


# is valid


@view
@external
def isValidAddyAddr(_addr: address) -> bool:
    return self._isValidAddyAddr(_addr)


@view
@internal
def _isValidAddyAddr(_addr: address) -> bool:
    return self.addyToId[_addr] != 0


@view
@external
def isValidAddyId(_addyId: uint256) -> bool:
    return self._isValidAddyId(_addyId)


@view
@internal
def _isValidAddyId(_addyId: uint256) -> bool:
    return _addyId != 0 and _addyId < self.numAddys


# addy getters


@view
@external
def getAddyId(_addr: address) -> uint256:
    return self._getAddyId(_addr)


@view
@internal
def _getAddyId(_addr: address) -> uint256:
    return self.addyToId[_addr]


@view
@external
def getAddy(_addyId: uint256) -> address:
    return self._getAddy(_addyId)


@view
@internal
def _getAddy(_addyId: uint256) -> address:
    return self.addyInfo[_addyId].addr


@view
@external
def getAddyInfo(_addyId: uint256) -> AddyInfo:
    return self._getAddyInfo(_addyId)


@view
@internal
def _getAddyInfo(_addyId: uint256) -> AddyInfo:
    return self.addyInfo[_addyId]


@view
@external
def getAddyDescription(_addyId: uint256) -> String[64]:
    return self._getAddyDescription(_addyId)


@view
@internal
def _getAddyDescription(_addyId: uint256) -> String[64]:
    return self.addyInfo[_addyId].description


# high level


@view
@external
def getNumAddys() -> uint256:
    return self._getNumAddys()


@view
@internal
def _getNumAddys() -> uint256:
    return self.numAddys - 1


@view
@external
def getLastAddyAddr() -> address:
    return self._getLastAddyAddr()


@view
@internal
def _getLastAddyAddr() -> address:
    lastIndex: uint256 = self.numAddys - 1
    return self.addyInfo[lastIndex].addr


@view
@external
def getLastAddyId() -> uint256:
    return self._getLastAddyId()


@view
@internal
def _getLastAddyId() -> uint256:
    return self.numAddys - 1
