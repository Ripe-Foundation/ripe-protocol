# @version 0.4.1

interface RipeHq:
    def minGovChangeTimeLock() -> uint256: view
    def maxGovChangeTimeLock() -> uint256: view
    def governance() -> address: view

struct PendingGovernance:
    newGov: address
    initiatedBlock: uint256
    confirmBlock: uint256

event GovChangeStarted:
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

event GovChangeTimeLockModified:
    numBlocks: uint256

event HqGovernanceSetup:
    deployer: indexed(address)
    newGov: indexed(address)

# time lock
govChangeTimeLock: public(uint256)

# governance
governance: public(address)
pendingGov: public(PendingGovernance)

# config
RIPE_HQ_FOR_GOV: immutable(address)
didFinishSetup: public(bool)

# time lock boundaries
MIN_GOV_TIME_LOCK: immutable(uint256)
MAX_GOV_TIME_LOCK: immutable(uint256)


@deploy
def __init__(
    _ripeHq: address,
    _initialGov: address,
    _minTimeLock: uint256,
    _maxTimeLock: uint256,
    _initialTimeLock: uint256,
):
    RIPE_HQ_FOR_GOV = _ripeHq
    self.governance = _initialGov

    # ripe hq gov must have gov
    if _ripeHq == empty(address):
        assert _initialGov != empty(address) # dev: ripe hq must have gov

    # local gov (department, other smart contracts)
    minTimeLock: uint256 = _minTimeLock
    maxTimeLock: uint256 = _maxTimeLock
    if minTimeLock == 0 or maxTimeLock == 0:
        assert _ripeHq != empty(address) # dev: need ripe hq for local gov
        minTimeLock = staticcall RipeHq(_ripeHq).minGovChangeTimeLock()
        maxTimeLock = staticcall RipeHq(_ripeHq).maxGovChangeTimeLock()

    # set min and max time locks
    assert minTimeLock < maxTimeLock # dev: invalid time lock
    assert minTimeLock != 0 and maxTimeLock != max_value(uint256) # dev: invalid time lock
    MIN_GOV_TIME_LOCK = minTimeLock
    MAX_GOV_TIME_LOCK = maxTimeLock

    # this contract is top level governance from Ripe HQ -- not setting initial time lock during setup
    if _ripeHq == empty(address):
        return

    # set initial time lock (for local gov)
    initialTimeLock: uint256 = max(minTimeLock, _initialTimeLock)
    assert self._isValidGovTimeLock(initialTimeLock) # dev: invalid time lock
    self.govChangeTimeLock = initialTimeLock


##############
# Gov Access #
##############


@view
@external
def canGovern(_addr: address) -> bool:
    return self._canGovern(_addr)


@view
@internal
def _canGovern(_addr: address) -> bool:
    if _addr == empty(address):
        return False
    return _addr in self._getGovernors()


@view
@internal
def _getGovernors() -> DynArray[address, 2]:
    governors: DynArray[address, 2] = []

    # local governance
    localGov: address = self.governance
    if localGov != empty(address):
        governors.append(localGov)

    # ripe hq governance
    ripeHq: address = RIPE_HQ_FOR_GOV
    if ripeHq == empty(address):
        return governors

    hqGov: address = staticcall RipeHq(ripeHq).governance()
    if hqGov != empty(address):
        governors.append(hqGov)

    return governors


######################
# Governance Changes #
######################


@view
@external
def hasPendingGovChange() -> bool:
    return self.pendingGov.confirmBlock != 0


@view
@internal
def _isRipeHqGov() -> bool:
    return RIPE_HQ_FOR_GOV == empty(address)


# start gov change


@external
def startGovernanceChange(_newGov: address):
    governors: DynArray[address, 2] = self._getGovernors()
    assert msg.sender in governors # dev: no perms

    # validation
    if _newGov != empty(address):
        assert _newGov not in governors # dev: invalid _newGov
        assert _newGov.is_contract # dev: _newGov must be a contract
    else:
        assert not self._isRipeHqGov() # dev: ripe hq cannot set 0x0

    confirmBlock: uint256 = block.number + self.govChangeTimeLock
    self.pendingGov = PendingGovernance(
        newGov= _newGov,
        initiatedBlock= block.number,
        confirmBlock= confirmBlock,
    )
    log GovChangeStarted(prevGov=self.governance, newGov=_newGov, confirmBlock=confirmBlock)


# confirm gov change


@external
def confirmGovernanceChange():
    data: PendingGovernance = self.pendingGov
    assert data.confirmBlock != 0 and block.number >= data.confirmBlock # dev: time lock not reached

    # check permissions
    if data.newGov != empty(address):
        assert msg.sender == data.newGov # dev: only new gov can confirm
    else:
        assert self._canGovern(msg.sender) # dev: no perms
        assert not self._isRipeHqGov() # dev: ripe hq cannot set 0x0

    # set new governance
    prevGov: address = self.governance
    self.governance = data.newGov
    self.pendingGov = empty(PendingGovernance)
    log GovChangeConfirmed(prevGov=prevGov, newGov=data.newGov, initiatedBlock=data.initiatedBlock, confirmBlock=data.confirmBlock)


# cancel gov change


@external
def cancelGovernanceChange():
    assert self._canGovern(msg.sender) # dev: no perms
    data: PendingGovernance = self.pendingGov
    assert data.confirmBlock != 0 # dev: no pending change
    self.pendingGov = empty(PendingGovernance)
    log GovChangeCancelled(cancelledGov=data.newGov, initiatedBlock=data.initiatedBlock, confirmBlock=data.confirmBlock)


####################
# Time Lock Config #
####################


# validation


@view
@external
def isValidGovTimeLock(_numBlocks: uint256) -> bool:
    return self._isValidGovTimeLock(_numBlocks)


@view
@internal
def _isValidGovTimeLock(_numBlocks: uint256) -> bool:
    if self.pendingGov.confirmBlock != 0:
        return False # cannot change while pending gov change
    return _numBlocks >= MIN_GOV_TIME_LOCK and _numBlocks <= MAX_GOV_TIME_LOCK


# set time lock


@external
def setGovTimeLock(_numBlocks: uint256):
    assert self._canGovern(msg.sender) # dev: no perms
    self._setGovTimeLock(_numBlocks)


@internal
def _setGovTimeLock(_numBlocks: uint256):
    assert self._isValidGovTimeLock(_numBlocks) # dev: invalid time lock
    self.govChangeTimeLock = _numBlocks
    log GovChangeTimeLockModified(numBlocks=_numBlocks)


# utils


@view
@external
def minGovChangeTimeLock() -> uint256:
    return MIN_GOV_TIME_LOCK


@view
@external
def maxGovChangeTimeLock() -> uint256:
    return MAX_GOV_TIME_LOCK


############
# Hq Setup #
############


@external
def finishHqSetup(_newGov: address):
    assert self._isRipeHqGov() # dev: only ripe hq
    assert msg.sender == self.governance # dev: no perms
    assert not self.didFinishSetup # dev: already finished setup

    # set new gov
    assert _newGov != empty(address) and _newGov.is_contract # dev: invalid _newGov
    prevGov: address = self.governance
    self.governance = _newGov

    # set time lock
    self._setGovTimeLock(MIN_GOV_TIME_LOCK)

    self.didFinishSetup = True
    log HqGovernanceSetup(deployer=prevGov, newGov=_newGov)