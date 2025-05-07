# @version 0.4.1

struct PendingAction:
    initiatedBlock: uint256
    confirmBlock: uint256

# data
actionDelay: public(uint256)
pendingActions: public(HashMap[uint256, PendingAction])
nextActionId: public(uint256)

MIN_ACTION_DELAY: public(immutable(uint256))
MAX_ACTION_DELAY: public(immutable(uint256))


@deploy
def __init__(
    _minActionDelay: uint256,
    _maxActionDelay: uint256,
    _shouldSetDelay: bool,
):
    self.nextActionId = 1

    assert _minActionDelay < _maxActionDelay # dev: invalid delay
    MIN_ACTION_DELAY = _minActionDelay
    MAX_ACTION_DELAY = _maxActionDelay

    if _shouldSetDelay:
        self.actionDelay = _minActionDelay


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
def getConfirmationBlock(_actionId: uint256) -> uint256:
    return self._getConfirmationBlock(_actionId)


@view
@internal
def _getConfirmationBlock(_actionId: uint256) -> uint256:
    return self.pendingActions[_actionId].confirmBlock


########
# Core #
########


# initiate


@internal
def _initiateAction() -> uint256:
    actionId: uint256 = self.nextActionId
    confirmBlock: uint256 = block.number + self.actionDelay
    self.pendingActions[actionId] = PendingAction(
        initiatedBlock= block.number,
        confirmBlock= confirmBlock,
    )
    self.nextActionId += 1
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


##########
# Config #
##########


@internal
def _setActionDelay(_numBlocks: uint256) -> bool:
    if _numBlocks < MIN_ACTION_DELAY or _numBlocks > MAX_ACTION_DELAY:
        return False
    self.actionDelay = _numBlocks
    return True