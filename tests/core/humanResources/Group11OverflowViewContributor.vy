# @version 0.4.3

# Test-only blueprint. Constructor ABI matches Contributor.
# Getters ignore constructor args so the aggregate views can saturate.

interface HumanResources:
    def refundAfterCancelPaycheck(_amount: uint256, _shouldBurnPosition: bool): nonpayable
    def canModifyHrContributor(_addr: address) -> bool: view

interface RipeHq:
    def getAddr(_regId: uint256) -> address: view


HUMAN_RESOURCES_ID: constant(uint256) = 15

ripeHq: address
storedComp: uint256
cancelled: bool


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
    self.ripeHq = _ripeHq
    self.storedComp = _compensation


@external
def cancelPaycheck():
    if self.cancelled:
        return
    hr: address = staticcall RipeHq(self.ripeHq).getAddr(HUMAN_RESOURCES_ID)
    assert staticcall HumanResources(hr).canModifyHrContributor(msg.sender)
    self.cancelled = True
    extcall HumanResources(hr).refundAfterCancelPaycheck(self.storedComp, True)


@external
@view
def compensation() -> uint256:
    if self.cancelled:
        return 0
    return max_value(uint256) // 2 + 1


@external
@view
def totalClaimed() -> uint256:
    if self.cancelled:
        return 0
    return max_value(uint256) // 2 + 1


@external
@view
def endTime() -> uint256:
    return max_value(uint256)


@external
@view
def cliffTime() -> uint256:
    return max_value(uint256)
