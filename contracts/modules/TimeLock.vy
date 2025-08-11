# Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
# Ripe Foundation (C) 2025

# @version 0.4.3

uses: gov
from . import LocalGov as gov

struct PendingAction:
    initiatedBlock: uint256
    confirmBlock: uint256
    expiration: uint256

event ActionTimeLockSet:
    newTimeLock: uint256
    prevTimeLock: uint256

event ExpirationSet:
    expiration: uint256

# core data
pendingActions: public(HashMap[uint256, PendingAction])
actionId: public(uint256)

# config
actionTimeLock: public(uint256)
expiration: public(uint256)

MIN_ACTION_TIMELOCK: immutable(uint256)
MAX_ACTION_TIMELOCK: immutable(uint256)


@deploy
def __init__(
    _minActionTimeLock: uint256,
    _maxActionTimeLock: uint256,
    _initialTimeLock: uint256,
    _expiration: uint256,
):
    # start at 1 index
    self.actionId = 1

    # set time lock boundaries
    assert _minActionTimeLock < _maxActionTimeLock # dev: invalid time lock boundaries
    assert _minActionTimeLock != 0 and _maxActionTimeLock != max_value(uint256) # dev: invalid time lock boundaries
    MIN_ACTION_TIMELOCK = _minActionTimeLock
    MAX_ACTION_TIMELOCK = _maxActionTimeLock

    # set expiration time
    self._setExpiration(_expiration, _initialTimeLock)

    # set initial time lock
    if _initialTimeLock != 0:
        assert self._setActionTimeLock(_initialTimeLock, 0) # dev: failed to set initial time lock


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
        expiration= confirmBlock + self.expiration,
    )
    self.actionId += 1
    return actionId


# confirm


@internal
def _confirmAction(_actionId: uint256) -> bool:
    if not self._canConfirmAction(_actionId):
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


# can confirm


@view
@external
def canConfirmAction(_actionId: uint256) -> bool:
    return self._canConfirmAction(_actionId)


@view
@internal
def _canConfirmAction(_actionId: uint256) -> bool:
    data: PendingAction = self.pendingActions[_actionId]
    if data.confirmBlock == 0 or block.number < data.confirmBlock:
        return False
    if block.number >= data.expiration:
        return False
    return True


# is expired


@view
@external
def isExpired(_actionId: uint256) -> bool:
    return self._isExpired(_actionId)


@view
@internal
def _isExpired(_actionId: uint256) -> bool:
    data: PendingAction = self.pendingActions[_actionId]
    if data.confirmBlock == 0:
        return False
    return block.number >= data.expiration


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


######################
# Config - Time Lock #
######################


@external
def setActionTimeLock(_newTimeLock: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return self._setActionTimeLock(_newTimeLock, self.actionTimeLock)


@internal
def _setActionTimeLock(_newTimeLock: uint256, _prevTimeLock: uint256) -> bool:
    assert self._isValidActionTimeLock(_newTimeLock, _prevTimeLock) # dev: invalid time lock
    self.actionTimeLock = _newTimeLock
    log ActionTimeLockSet(newTimeLock=_newTimeLock, prevTimeLock=_prevTimeLock)
    return True


# validation


@view
@external
def isValidActionTimeLock(_newTimeLock: uint256) -> bool:
    return self._isValidActionTimeLock(_newTimeLock, self.actionTimeLock)


@view
@internal
def _isValidActionTimeLock(_newTimeLock: uint256, _prevTimeLock: uint256) -> bool:
    if _newTimeLock == _prevTimeLock:
        return False # no change
    return _newTimeLock >= MIN_ACTION_TIMELOCK and _newTimeLock <= MAX_ACTION_TIMELOCK


# utils


@view
@external
def minActionTimeLock() -> uint256:
    return MIN_ACTION_TIMELOCK


@view
@external
def maxActionTimeLock() -> uint256:
    return MAX_ACTION_TIMELOCK


#######################
# Config - Expiration #
#######################


@external
def setExpiration(_expiration: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return self._setExpiration(_expiration, self.actionTimeLock)


@internal
def _setExpiration(_expiration: uint256, _timeLock: uint256) -> bool:
    assert self._isValidExpiration(_expiration, _timeLock) # dev: invalid expiration
    self.expiration = _expiration
    log ExpirationSet(expiration=_expiration)
    return True


# validation


@view
@internal
def _isValidExpiration(_expiration: uint256, _timeLock: uint256) -> bool:
    if _expiration == 0 or _expiration == max_value(uint256):
        return False
    if _expiration < _timeLock:
        return False
    return True


################
# Finish Setup #
################


@external
def setActionTimeLockAfterSetup(_newTimeLock: uint256 = 0) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms

    prevTimeLock: uint256 = self.actionTimeLock
    assert prevTimeLock == 0 # dev: already set

    timeLock: uint256 = _newTimeLock
    if timeLock == 0:
        timeLock = MIN_ACTION_TIMELOCK
    return self._setActionTimeLock(timeLock, prevTimeLock)
