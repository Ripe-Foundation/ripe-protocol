# @version 0.4.3

# Test-only blueprint used to separate aggregate-view arithmetic from the
# standard Contributor cash path.  It preserves HR's required constructor
# shape, reports the supplied compensation, and initializes totalClaimed to
# that value so the aggregate view's checked addition is directly exercised.

compensation: public(uint256)
totalClaimed: public(uint256)


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
    self.totalClaimed = _compensation
