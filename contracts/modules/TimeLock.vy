# @version 0.4.1

uses: gov
import contracts.modules.LocalGov as gov

struct PendingAction:
    initiatedBlock: uint256
    confirmBlock: uint256

event ActionTimeLockSet:
    timeLock: uint256
# core data
pendingActions: public(HashMap[uint256, PendingAction])
actionId: public(uint256)

# config
actionTimeLock: public(uint256)

MIN_ACTION_TIMELOCK: public(immutable(uint256))
MAX_ACTION_TIMELOCK: public(immutable(uint256))


@deploy
def __init__(
    _minActionTimeLock: uint256,
    _maxActionTimeLock: uint256,
    _initialTimeLock: uint256,
):
    # start at 1 index
    self.actionId = 1

    # set time lock boundaries
    assert _minActionTimeLock < _maxActionTimeLock # dev: invalid delay
    assert _minActionTimeLock != 0 and _maxActionTimeLock != max_value(uint256) # dev: invalid time lock
    MIN_ACTION_TIMELOCK = _minActionTimeLock
    MAX_ACTION_TIMELOCK = _maxActionTimeLock

    # set initial time lock
    if _initialTimeLock != 0:
        assert self._setActionTimeLock(_initialTimeLock) # dev: failed to set initial time lock


########
# Core #
########


# initiate


@internal
def _initiateAction() -> uint256:
    actionId: uint256 = self.actionId
    confirmBlock: uint256 = block.number + self.actionTimeLock
    self.pendingActions[actionId] = PendingAction(
        initiatedBlock= block.number,
        confirmBlock= confirmBlock,
    )
    self.actionId += 1
    return actionId


# confirm


@internal
def _confirmAction(_actionId: uint256) -> bool:
    data: PendingAction = self.pendingActions[_actionId]
    if data.confirmBlock == 0 or block.number < data.confirmBlock:
        return False
    self.pendingActions[_actionId] = empty(PendingAction)
    return True


# cancel


@internal
def _cancelAction(_actionId: uint256) -> bool:
    data: PendingAction = self.pendingActions[_actionId]
    if data.confirmBlock == 0:
        return False
    self.pendingActions[_actionId] = empty(PendingAction)
    return True


#########
# Utils #
#########


# pending action


@view
@external
def hasPendingAction(_actionId: uint256) -> bool:
    return self._hasPendingAction(_actionId)


@view
@internal
def _hasPendingAction(_actionId: uint256) -> bool:
    return self.pendingActions[_actionId].confirmBlock != 0


# confirmation block


@view
@external
def getActionConfirmationBlock(_actionId: uint256) -> uint256:
    return self._getActionConfirmationBlock(_actionId)


@view
@internal
def _getActionConfirmationBlock(_actionId: uint256) -> uint256:
    return self.pendingActions[_actionId].confirmBlock


##########
# Config #
##########


@external
def setActionTimeLock(_numBlocks: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return self._setActionTimeLock(_numBlocks)


@internal
def _setActionTimeLock(_numBlocks: uint256) -> bool:
    assert self._isValidActionTimeLock(_numBlocks) # dev: invalid time lock
    self.actionTimeLock = _numBlocks
    log ActionTimeLockSet(timeLock=_numBlocks)
    return True


# validation


@view
@external
def isValidActionTimeLock(_numBlocks: uint256) -> bool:
    return self._isValidActionTimeLock(_numBlocks)


@view
@internal
def _isValidActionTimeLock(_numBlocks: uint256) -> bool:
    return _numBlocks >= MIN_ACTION_TIMELOCK and _numBlocks <= MAX_ACTION_TIMELOCK


# utils


@view
@external
def minActionTimeLock() -> uint256:
    return MIN_ACTION_TIMELOCK


@view
@external
def maxActionTimeLock() -> uint256:
    return MAX_ACTION_TIMELOCK


# finish setup


@external
def setActionTimeLockAfterSetup(_numBlocks: uint256 = 0) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert self.actionTimeLock == 0 # dev: already set

    timeLock: uint256 = _numBlocks
    if timeLock == 0:
        timeLock = MIN_ACTION_TIMELOCK
    return self._setActionTimeLock(timeLock)