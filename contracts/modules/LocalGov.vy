# @version 0.4.1

interface AddyRegistry:
    def MIN_GOV_CHANGE_DELAY() -> uint256: view
    def MAX_GOV_CHANGE_DELAY() -> uint256: view
    def governance() -> address: view

struct PendingGovernance:
    newGov: address
    initiatedBlock: uint256
    confirmBlock: uint256

event GovChangeInitiated:
    prevGov: indexed(address)
    newGov: indexed(address)
    confirmBlock: uint256

event GovChangeConfirmed:
    prevGov: indexed(address)
    newGov: indexed(address)
    initiatedBlock: uint256
    confirmBlock: uint256

event GovChangeCancelled:
    cancelledGov: indexed(address)
    initiatedBlock: uint256
    confirmBlock: uint256

event GovChangeDelaySet:
    delayBlocks: uint256

# governance
governance: public(address)
pendingGov: public(PendingGovernance) # pending governance change
govChangeDelay: public(uint256) # num blocks to wait before governance can be changed

# immutable
MIN_GOV_CHANGE_DELAY: public(immutable(uint256))
MAX_GOV_CHANGE_DELAY: public(immutable(uint256))
_addyRegistry: address # ish


@deploy
def __init__(
    _initialGov: address,
    _addyRegistry: address,
    _minGovChangeDelay: uint256,
    _maxGovChangeDelay: uint256,
):
    # need to have one of the two for this to be valid
    assert _initialGov != empty(address) or _addyRegistry != empty(address) # dev: invalid gov config

    # set initial governance
    if _initialGov != empty(address):
        self.governance = _initialGov

    # if local governance, set addy registry
    if _addyRegistry != empty(address):
        self._addyRegistry = _addyRegistry

    # set min and max delay
    minDelay: uint256 = _minGovChangeDelay
    maxDelay: uint256 = _maxGovChangeDelay
    if minDelay == 0 or maxDelay == 0:
        assert _addyRegistry != empty(address) # dev: need addy registry for local gov
        minDelay = staticcall AddyRegistry(_addyRegistry).MIN_GOV_CHANGE_DELAY()
        maxDelay = staticcall AddyRegistry(_addyRegistry).MAX_GOV_CHANGE_DELAY()

    assert minDelay < maxDelay # dev: invalid delay
    MIN_GOV_CHANGE_DELAY = minDelay
    MAX_GOV_CHANGE_DELAY = maxDelay

    # Top-level registry (AddyRegistry.vy) has no delay initially during setup
    if _addyRegistry != empty(address):
        self.govChangeDelay = minDelay  


#############
# Utilities #
#############


@view
@external
def canGovern(_address: address) -> bool:
    """
    @notice Check if an address has governance permissions
    @dev Checks if the address is either the local governance or the AddyRegistry governance
    @param _address The address to check for governance permissions
    @return True if the address has governance permissions, False otherwise
    """
    return self._canGovern(_address)


@view
@internal
def _canGovern(_address: address) -> bool:
    return _address in self._getGovernors()


@view
@external
def hasPendingGovChange() -> bool:
    """
    @notice Checks if there is a pending governance change
    @return bool True if there is a pending governance change, false otherwise
    """
    return self.pendingGov.confirmBlock != 0


@view
@internal
def _getGovernors() -> DynArray[address, 2]:
    """
    @notice Internal function to get all valid governance addresses
    @dev Returns a list containing both local governance and AddyRegistry governance (if set)
    @return Array of addresses that have governance permissions
    """
    governors: DynArray[address, 2] = []

    # local governance
    localGov: address = self.governance
    if localGov != empty(address):
        governors.append(localGov)

    # addy registry governance
    addyRegistry: address = self._addyRegistry
    if addyRegistry != empty(address):
        globalGovernance: address = staticcall AddyRegistry(addyRegistry).governance()
        if globalGovernance != empty(address):
            governors.append(globalGovernance)

    return governors


@view
@internal
def _isAddyRegistryGov() -> bool:
    """
    @notice Internal function to check if this contract is the AddyRegistry
    @dev Returns true if _addyRegistry is not set (empty address)
    @return True if this contract is the AddyRegistry, False otherwise
    """
    return self._addyRegistry == empty(address)


##################
# Set Governance #
##################


@external
def changeGovernance(_newGov: address):
    """
    @notice Initiates a new governance change
    @dev Can only be called by current governance
    @param _newGov The address of new governance
    """
    governors: DynArray[address, 2] = self._getGovernors()
    assert msg.sender in governors # dev: no perms

    # validation
    assert _newGov not in governors # dev: invalid new governance
    assert _newGov.is_contract # dev: new governance must be a contract
    if self._isAddyRegistryGov():
        assert _newGov != empty(address) # dev: addy registry cannot set 0x0

    confirmBlock: uint256 = block.number + self.govChangeDelay
    self.pendingGov = PendingGovernance(
        newGov= _newGov,
        initiatedBlock= block.number,
        confirmBlock= confirmBlock,
    )
    log GovChangeInitiated(prevGov=self.governance, newGov=_newGov, confirmBlock=confirmBlock)


@external
def confirmGovernanceChange():
    """
    @notice Confirms the governance change
    @dev Can only be called by the new governance
    """
    data: PendingGovernance = self.pendingGov
    assert data.newGov != empty(address) # dev: no pending governance
    assert data.confirmBlock != 0 and block.number >= data.confirmBlock # dev: time delay not reached
    assert msg.sender == data.newGov # dev: only new governance can confirm

    prevGov: address = self.governance
    self.governance = data.newGov
    self.pendingGov = empty(PendingGovernance)
    log GovChangeConfirmed(prevGov=prevGov, newGov=data.newGov, initiatedBlock=data.initiatedBlock, confirmBlock=data.confirmBlock)


@external
def cancelGovernanceChange():
    """
    @notice Cancels the governance change
    @dev Can only be called by the current governance
    """
    assert self._canGovern(msg.sender) # dev: no perms
    data: PendingGovernance = self.pendingGov
    assert data.confirmBlock != 0 # dev: no pending change
    self.pendingGov = empty(PendingGovernance)
    log GovChangeCancelled(cancelledGov=data.newGov, initiatedBlock=data.initiatedBlock, confirmBlock=data.confirmBlock)


@external
def setGovernanceChangeDelay(_numBlocks: uint256):
    """
    @notice Sets the governance change delay
    @dev Can only be called by current governance
    @param _numBlocks The number of blocks to wait before governance can be changed
    """
    assert self.pendingGov.confirmBlock == 0 # dev: cannot set delay if there is a pending change
    assert self._canGovern(msg.sender) # dev: no perms
    assert _numBlocks >= MIN_GOV_CHANGE_DELAY and _numBlocks <= MAX_GOV_CHANGE_DELAY # dev: invalid delay
    self.govChangeDelay = _numBlocks
    log GovChangeDelaySet(delayBlocks=_numBlocks)