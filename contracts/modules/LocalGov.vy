# Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
# Ripe Foundation (C) 2025

# @version 0.4.3

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
    prevTimeLock: uint256
    newTimeLock: uint256

event RipeHqSetupFinished:
    prevGov: indexed(address)
    newGov: indexed(address)
    timeLock: uint256

# governance
governance: public(address)
pendingGov: public(PendingGovernance)
numGovChanges: public(uint256)

# time lock
govChangeTimeLock: public(uint256)

# config
RIPE_HQ_FOR_GOV: immutable(address)
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

    # ripe hq
    if _ripeHq == empty(address):
        assert _initialGov != empty(address) # dev: ripe hq must have gov

    # local gov (department, other smart contracts)
    else:
        hqGov: address = staticcall RipeHq(_ripeHq).governance()
        assert hqGov != empty(address) # dev: ripe hq must have gov
        assert _initialGov != hqGov # dev: ripe hq cannot set same gov

    # time locks
    minTimeLock: uint256 = _minTimeLock
    maxTimeLock: uint256 = _maxTimeLock
    if minTimeLock == 0 or maxTimeLock == 0:
        assert _ripeHq != empty(address) # dev: need ripe hq if no time locks
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
    assert self._setGovTimeLock(initialTimeLock) # dev: invalid time lock


@view
@external
def getRipeHqFromGov() -> address:
    return self._getRipeHqFromGov()


@view
@internal
def _getRipeHqFromGov() -> address:
    return RIPE_HQ_FOR_GOV


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
@external
def getGovernors() -> DynArray[address, 2]:
    return self._getGovernors()


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
    self.numGovChanges += 1
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


# set time lock


@external
def setGovTimeLock(_numBlocks: uint256) -> bool:
    assert self._canGovern(msg.sender) # dev: no perms
    return self._setGovTimeLock(_numBlocks)


@internal
def _setGovTimeLock(_numBlocks: uint256) -> bool:
    prevTimeLock: uint256 = self.govChangeTimeLock
    assert self._isValidGovTimeLock(_numBlocks, prevTimeLock) # dev: invalid time lock
    self.govChangeTimeLock = _numBlocks
    log GovChangeTimeLockModified(prevTimeLock=prevTimeLock, newTimeLock=_numBlocks)
    return True


# validation


@view
@external
def isValidGovTimeLock(_newTimeLock: uint256) -> bool:
    return self._isValidGovTimeLock(_newTimeLock, self.govChangeTimeLock)


@view
@internal
def _isValidGovTimeLock(_newTimeLock: uint256, _prevTimeLock: uint256) -> bool:
    if _newTimeLock == _prevTimeLock:
        return False # no change
    if self.pendingGov.confirmBlock != 0:
        return False # cannot change while pending gov change
    return _newTimeLock >= MIN_GOV_TIME_LOCK and _newTimeLock <= MAX_GOV_TIME_LOCK


# utils


@view
@external
def minGovChangeTimeLock() -> uint256:
    return MIN_GOV_TIME_LOCK


@view
@external
def maxGovChangeTimeLock() -> uint256:
    return MAX_GOV_TIME_LOCK


#################
# Ripe Hq Setup #
#################


@external
def finishRipeHqSetup(_newGov: address, _timeLock: uint256 = 0) -> bool:
    assert self._isRipeHqGov() # dev: only ripe hq
    assert msg.sender == self.governance # dev: no perms
    assert self.numGovChanges == 0 # dev: already changed gov

    # validation
    assert _newGov != empty(address) and _newGov.is_contract # dev: invalid _newGov
    prevGov: address = self.governance

    # set new gov
    self.governance = _newGov
    self.numGovChanges += 1

    # set time lock
    timeLock: uint256 = _timeLock
    if timeLock == 0:
        timeLock = MIN_GOV_TIME_LOCK
    assert self._setGovTimeLock(timeLock) # dev: invalid time lock

    log RipeHqSetupFinished(prevGov=prevGov, newGov=_newGov, timeLock=timeLock)
    return True