# @version 0.4.1

uses: gov
import contracts.modules.LocalGov as gov

interface RegistryItem:
    def setRegistryId(_regId: uint256) -> bool: nonpayable

struct AddressInfo:
    addr: address
    version: uint256
    lastModified: uint256
    description: String[64]

struct PendingNewAddress:
    description: String[64]
    initiatedBlock: uint256
    confirmBlock: uint256

struct PendingAddressUpdate:
    newAddr: address
    initiatedBlock: uint256
    confirmBlock: uint256

struct PendingAddressDisable:
    initiatedBlock: uint256
    confirmBlock: uint256

event NewAddressPending:
    addr: indexed(address)
    description: String[64]
    confirmBlock: uint256
    registry: String[28]

event NewAddressConfirmed:
    addr: indexed(address)
    regId: uint256
    description: String[64]
    registry: String[28]

event NewAddressCancelled:
    description: String[64]
    addr: indexed(address)
    initiatedBlock: uint256
    confirmBlock: uint256
    registry: String[28]

event AddressUpdatePending:
    regId: uint256
    description: String[64]
    newAddr: indexed(address)
    prevAddr: indexed(address)
    version: uint256
    confirmBlock: uint256
    registry: String[28]

event AddressUpdateConfirmed:
    regId: uint256
    description: String[64]
    newAddr: indexed(address)
    prevAddr: indexed(address)
    version: uint256
    registry: String[28]

event AddressUpdateCancelled:
    regId: uint256
    description: String[64]
    newAddr: indexed(address)
    prevAddr: indexed(address)
    initiatedBlock: uint256
    confirmBlock: uint256
    registry: String[28]

event AddressDisablePending:
    regId: uint256
    description: String[64]
    addr: indexed(address)
    version: uint256
    confirmBlock: uint256
    registry: String[28]

event AddressDisableConfirmed:
    regId: uint256
    description: String[64]
    addr: indexed(address)
    version: uint256
    registry: String[28]

event AddressDisableCancelled:
    regId: uint256
    description: String[64]
    addr: indexed(address)
    initiatedBlock: uint256
    confirmBlock: uint256
    registry: String[28]

event RegistryTimeLockModified:
    numBlocks: uint256
    registry: String[28]

# config
registryChangeTimeLock: public(uint256)

# core registry
addrInfo: public(HashMap[uint256, AddressInfo])
addrToRegId: public(HashMap[address, uint256])
numAddrs: public(uint256)

# pending changes
pendingNewAddr: public(HashMap[address, PendingNewAddress]) # addr -> pending new addr
pendingAddrUpdate: public(HashMap[uint256, PendingAddressUpdate]) # regId -> pending addr update
pendingAddrDisable: public(HashMap[uint256, PendingAddressDisable]) # regId -> pending addr disable

REGISTRY_STR: immutable(String[28])
MIN_REG_TIME_LOCK: immutable(uint256)
MAX_REG_TIME_LOCK: immutable(uint256)


@deploy
def __init__(
    _minTimeLock: uint256,
    _maxTimeLock: uint256,
    _initialTimeLock: uint256,
    _registryStr: String[28],
):
    REGISTRY_STR = _registryStr

    assert _minTimeLock < _maxTimeLock # dev: invalid time lock
    assert _minTimeLock != 0 and _maxTimeLock != max_value(uint256) # dev: invalid time lock
    MIN_REG_TIME_LOCK = _minTimeLock
    MAX_REG_TIME_LOCK = _maxTimeLock

    # set initial time lock -- this may be zero during inital setup of registry
    if _initialTimeLock != 0:
        assert self._isValidRegistryTimeLock(_initialTimeLock) # dev: invalid time lock
        self.registryChangeTimeLock = _initialTimeLock

    # start at 1 index
    self.numAddrs = 1


@view
@external
def getRegistryDescription() -> String[28]:
    return REGISTRY_STR


###############
# New Address #
###############


# register new address


@external
def startAddNewAddressToRegistry(_addr: address, _description: String[64]) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return self._startAddNewAddressToRegistry(_addr, _description)


@internal
def _startAddNewAddressToRegistry(_addr: address, _description: String[64]) -> bool:
    assert self._isValidNewAddress(_addr) # dev: invalid addy

    confirmBlock: uint256 = block.number + self.registryChangeTimeLock
    self.pendingNewAddr[_addr] = PendingNewAddress(
        description=_description,
        initiatedBlock=block.number,
        confirmBlock=confirmBlock,
    )

    log NewAddressPending(addr=_addr, description=_description, confirmBlock=confirmBlock, registry=REGISTRY_STR)
    return True


# confirm new address


@external
def confirmNewAddressToRegistry(_addr: address) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    return self._confirmNewAddressToRegistry(_addr)


@internal
def _confirmNewAddressToRegistry(_addr: address) -> uint256:
    data: PendingNewAddress = self.pendingNewAddr[_addr]
    assert data.confirmBlock != 0 and block.number >= data.confirmBlock # dev: time lock not reached

    if not self._isValidNewAddress(_addr):
        self.pendingNewAddr[_addr] = empty(PendingNewAddress) # clear pending
        return 0

    # register new addy
    regId: uint256 = self.numAddrs
    self.addrToRegId[_addr] = regId
    self.numAddrs = regId + 1
    self.addrInfo[regId] = AddressInfo(
        addr=_addr,
        version=1,
        lastModified=block.timestamp,
        description=data.description,
    )
    assert extcall RegistryItem(_addr).setRegistryId(regId) # dev: failed to set registry id

    # clear pending
    self.pendingNewAddr[_addr] = empty(PendingNewAddress)

    log NewAddressConfirmed(addr=_addr, regId=regId, description=data.description, registry=REGISTRY_STR)
    return regId


# cancel new address


@external
def cancelNewAddressToRegistry(_addr: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return self._cancelNewAddressToRegistry(_addr)


@internal
def _cancelNewAddressToRegistry(_addr: address) -> bool:
    data: PendingNewAddress = self.pendingNewAddr[_addr]
    assert data.confirmBlock != 0 # dev: no pending

    self.pendingNewAddr[_addr] = empty(PendingNewAddress)
    log NewAddressCancelled(description=data.description, addr=_addr, initiatedBlock=data.initiatedBlock, confirmBlock=data.confirmBlock, registry=REGISTRY_STR)
    return True


# validation


@view
@external
def isValidNewAddress(_addr: address) -> bool:
    return self._isValidNewAddress(_addr)


@view
@internal
def _isValidNewAddress(_addr: address) -> bool:
    if _addr == empty(address) or not _addr.is_contract:
        return False
    return self.addrToRegId[_addr] == 0


###################
# Address Updates #
###################


# update address


@external
def startAddressUpdateToRegistry(_regId: uint256, _newAddr: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return self._startAddressUpdateToRegistry(_regId, _newAddr)


@internal
def _startAddressUpdateToRegistry(_regId: uint256, _newAddr: address) -> bool:
    data: AddressInfo = self.addrInfo[_regId]
    assert self._isValidAddressUpdate(_regId, _newAddr, data.addr) # dev: invalid update

    # set pending
    confirmBlock: uint256 = block.number + self.registryChangeTimeLock
    self.pendingAddrUpdate[_regId] = PendingAddressUpdate(
        newAddr=_newAddr,
        initiatedBlock=block.number,
        confirmBlock=confirmBlock,
    )

    log AddressUpdatePending(regId=_regId, description=data.description, newAddr=_newAddr, prevAddr=data.addr, version=data.version, confirmBlock=confirmBlock, registry=REGISTRY_STR)
    return True


# confirm update address


@external
def confirmAddressUpdateToRegistry(_regId: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return self._confirmAddressUpdateToRegistry(_regId)


@internal
def _confirmAddressUpdateToRegistry(_regId: uint256) -> bool:
    newData: PendingAddressUpdate = self.pendingAddrUpdate[_regId]
    assert newData.confirmBlock != 0 and block.number >= newData.confirmBlock # dev: time lock not reached

    data: AddressInfo = self.addrInfo[_regId]
    prevAddr: address = data.addr # needed for later
    if not self._isValidAddressUpdate(_regId, newData.newAddr, prevAddr):
        self.pendingAddrUpdate[_regId] = empty(PendingAddressUpdate) # clear pending
        return False

    # update addy data
    data.addr = newData.newAddr
    data.lastModified = block.timestamp
    data.version += 1
    self.addrInfo[_regId] = data
    self.addrToRegId[newData.newAddr] = _regId
    assert extcall RegistryItem(newData.newAddr).setRegistryId(_regId) # dev: failed to set registry id

    # handle previous addr
    if prevAddr != empty(address):
        self.addrToRegId[prevAddr] = 0

    # clear pending
    self.pendingAddrUpdate[_regId] = empty(PendingAddressUpdate)

    log AddressUpdateConfirmed(regId=_regId, description=data.description, newAddr=newData.newAddr, prevAddr=prevAddr, version=data.version, registry=REGISTRY_STR)
    return True


# cancel update address


@external
def cancelAddressUpdateToRegistry(_regId: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return self._cancelAddressUpdateToRegistry(_regId)


@internal
def _cancelAddressUpdateToRegistry(_regId: uint256) -> bool:
    data: PendingAddressUpdate = self.pendingAddrUpdate[_regId]
    assert data.confirmBlock != 0 # dev: no pending

    self.pendingAddrUpdate[_regId] = empty(PendingAddressUpdate)
    prevData: AddressInfo = self.addrInfo[_regId]
    log AddressUpdateCancelled(regId=_regId, description=prevData.description, newAddr=data.newAddr, prevAddr=prevData.addr, initiatedBlock=data.initiatedBlock, confirmBlock=data.confirmBlock, registry=REGISTRY_STR)
    return True


# validation


@view
@external
def isValidAddressUpdate(_regId: uint256, _newAddr: address) -> bool:
    return self._isValidAddressUpdate(_regId, _newAddr, self.addrInfo[_regId].addr)


@view
@internal
def _isValidAddressUpdate(_regId: uint256, _newAddr: address, _prevAddr: address) -> bool:
    if not self._isValidRegId(_regId):
        return False
    if not self._isValidNewAddress(_newAddr):
        return False
    return _newAddr != _prevAddr


###################
# Disable Address #
###################


# start disable address


@external
def startAddressDisableInRegistry(_regId: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return self._startAddressDisableInRegistry(_regId)


@internal
def _startAddressDisableInRegistry(_regId: uint256) -> bool:
    data: AddressInfo = self.addrInfo[_regId]
    assert self._isValidAddressDisable(_regId, data.addr) # dev: invalid disable

    # set pending
    confirmBlock: uint256 = block.number + self.registryChangeTimeLock
    self.pendingAddrDisable[_regId] = PendingAddressDisable(
        initiatedBlock=block.number,
        confirmBlock=confirmBlock,
    )

    log AddressDisablePending(regId=_regId, description=data.description, addr=data.addr, version=data.version, confirmBlock=confirmBlock, registry=REGISTRY_STR)
    return True


# confirm disable address


@external
def confirmAddressDisableInRegistry(_regId: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return self._confirmAddressDisableInRegistry(_regId)


@internal
def _confirmAddressDisableInRegistry(_regId: uint256) -> bool:
    newData: PendingAddressDisable = self.pendingAddrDisable[_regId]
    assert newData.confirmBlock != 0 and block.number >= newData.confirmBlock # dev: time lock not reached

    data: AddressInfo = self.addrInfo[_regId]
    prevAddr: address = data.addr # needed for later
    if not self._isValidAddressDisable(_regId, prevAddr):
        self.pendingAddrDisable[_regId] = empty(PendingAddressDisable) # clear pending
        return False

    # disable addy
    data.addr = empty(address)
    data.lastModified = block.timestamp
    data.version += 1
    self.addrInfo[_regId] = data
    self.addrToRegId[prevAddr] = 0

    # clear pending
    self.pendingAddrDisable[_regId] = empty(PendingAddressDisable)

    log AddressDisableConfirmed(regId=_regId, description=data.description, addr=prevAddr, version=data.version, registry=REGISTRY_STR)
    return True


# cancel disable address


@external
def cancelAddressDisableInRegistry(_regId: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return self._cancelAddressDisableInRegistry(_regId)


@internal
def _cancelAddressDisableInRegistry(_regId: uint256) -> bool:
    data: PendingAddressDisable = self.pendingAddrDisable[_regId]
    assert data.confirmBlock != 0 # dev: no pending

    self.pendingAddrDisable[_regId] = empty(PendingAddressDisable)
    prevData: AddressInfo = self.addrInfo[_regId]
    log AddressDisableCancelled(regId=_regId, description=prevData.description, addr=prevData.addr, initiatedBlock=data.initiatedBlock, confirmBlock=data.confirmBlock, registry=REGISTRY_STR)
    return True


# validation


@view
@external
def isValidAddressDisable(_regId: uint256) -> bool:
    return self._isValidAddressDisable(_regId, self.addrInfo[_regId].addr)


@view
@internal
def _isValidAddressDisable(_regId: uint256, _prevAddr: address) -> bool:
    if not self._isValidRegId(_regId):
        return False
    return _prevAddr != empty(address)


####################
# Time Lock Config #
####################


@external
def setRegistryTimeLock(_numBlocks: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return self._setRegistryTimeLock(_numBlocks)


@external
def setRegistryTimeLockAfterSetup():
    assert gov._canGovern(msg.sender) # dev: no perms
    assert self.registryChangeTimeLock == 0 # dev: already set
    self._setRegistryTimeLock(MIN_REG_TIME_LOCK)


@internal
def _setRegistryTimeLock(_numBlocks: uint256) -> bool:
    assert self._isValidRegistryTimeLock(_numBlocks) # dev: invalid time lock
    self.registryChangeTimeLock = _numBlocks
    log RegistryTimeLockModified(numBlocks=_numBlocks, registry=REGISTRY_STR)
    return True


# validation


@view
@external
def isValidRegistryTimeLock(_numBlocks: uint256) -> bool:
    return self._isValidRegistryTimeLock(_numBlocks)


@view
@internal
def _isValidRegistryTimeLock(_numBlocks: uint256) -> bool:
    return _numBlocks >= MIN_REG_TIME_LOCK and _numBlocks <= MAX_REG_TIME_LOCK


#################
# Views / Utils #
#################


# is valid addr


@view
@external
def isValidAddr(_addr: address) -> bool:
    return self._isValidAddr(_addr)


@view
@internal
def _isValidAddr(_addr: address) -> bool:
    return self.addrToRegId[_addr] != 0


# is valid addr id


@view
@external
def isValidRegId(_regId: uint256) -> bool:
    return self._isValidRegId(_regId)


@view
@internal
def _isValidRegId(_regId: uint256) -> bool:
    return _regId != 0 and _regId < self.numAddrs


# get reg id


@view
@external
def getRegId(_addr: address) -> uint256:
    return self._getRegId(_addr)


@view
@internal
def _getRegId(_addr: address) -> uint256:
    return self.addrToRegId[_addr]


# get addr


@view
@external
def getAddr(_regId: uint256) -> address:
    return self._getAddr(_regId)


@view
@internal
def _getAddr(_regId: uint256) -> address:
    return self.addrInfo[_regId].addr


# get addr info


@view
@external
def getAddrInfo(_regId: uint256) -> AddressInfo:
    return self._getAddrInfo(_regId)


@view
@internal
def _getAddrInfo(_regId: uint256) -> AddressInfo:
    return self.addrInfo[_regId]


# get addr description


@view
@external
def getAddrDescription(_regId: uint256) -> String[64]:
    return self._getAddrDescription(_regId)


@view
@internal
def _getAddrDescription(_regId: uint256) -> String[64]:
    return self.addrInfo[_regId].description


# get num addrs


@view
@external
def getNumAddrs() -> uint256:
    return self._getNumAddrs()


@view
@internal
def _getNumAddrs() -> uint256:
    return self.numAddrs - 1


# get last addr


@view
@external
def getLastAddr() -> address:
    return self._getLastAddr()


@view
@internal
def _getLastAddr() -> address:
    lastRegId: uint256 = self.numAddrs - 1
    return self.addrInfo[lastRegId].addr


# get last reg id


@view
@external
def getLastRegId() -> uint256:
    return self._getLastRegId()


@view
@internal
def _getLastRegId() -> uint256:
    return self.numAddrs - 1
