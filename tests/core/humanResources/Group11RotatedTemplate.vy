# @version 0.4.3

# Test-only replacement Contributor blueprint.  It has HR's required
# constructor ABI and a marker so a proof can distinguish confirm-time
# template selection without changing production bytecode.

compensation: public(uint256)


@deploy
def __init__(
    _ripeHq: address,
    _owner: address,
    _manager: address,
    _compensation: uint256,
    _startDelay: uint256,
    _vestingLength: uint256,
    _cliffLength: uint256,
    _unlockLength: uint256,
    _depositLockDuration: uint256,
    _minKeyActionDelay: uint256,
    _maxKeyActionDelay: uint256,
):
    self.compensation = _compensation


@view
@external
def templateMarker() -> uint256:
    return 11
