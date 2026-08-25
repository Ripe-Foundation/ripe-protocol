#    ___  ________   ________  _________  ________  ________   _________        ________  ________  ________   ________  ________
#   |\  \|\   ___  \|\   ____\|\___   ___\\   __  \|\   ___  \|\___   ___\     |\   __  \|\   __  \|\   ___  \|\   ___ \|\   ____\
#   \ \  \ \  \\ \  \ \  \___|\|___ \  \_\ \  \|\  \ \  \\ \  \|___ \  \_|     \ \  \|\ /\ \  \|\  \ \  \\ \  \ \  \_|\ \ \  \___|_
#    \ \  \ \  \\ \  \ \_____  \   \ \  \ \ \   __  \ \  \\ \  \   \ \  \       \ \   __  \ \  \\\  \ \  \\ \  \ \  \ \\ \ \_____  \
#     \ \  \ \  \\ \  \|____|\  \   \ \  \ \ \  \ \  \ \  \\ \  \   \ \  \       \ \  \|\  \ \  \\\  \ \  \\ \  \ \  \_\\ \|____|\  \
#      \ \__\ \__\\ \__\____\_\  \   \ \__\ \ \__\ \__\ \__\\ \__\   \ \__\       \ \_______\ \_______\ \__\\ \__\ \_______\____\_\  \
#       \|__|\|__| \|__|\_________\   \|__|  \|__|\|__|\|__| \|__|    \|__|        \|_______|\|_______|\|__| \|__|\|_______|\_________\
#                      \|_________|                                                                                        \|_________|
#
#     ripe protocol license: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
#     ripe foundation (C) 2026

# @version 0.4.3

implements: Department

exports: addys.__interface__
exports: deptBasics.__interface__

initializes: addys
initializes: deptBasics[addys := addys]

import contracts.modules.Addys as addys
import contracts.modules.DeptBasics as deptBasics
from interfaces import Department

struct VestingPosition:
    id: uint256
    ripeAllocation: uint256
    ripeClaimed: uint256
    creationBlock: uint256
    claimStartBlock: uint256
    maturityBlock: uint256

event VestingPositionCreated:
    user: indexed(address)
    positionId: indexed(uint256)
    sourceEngine: indexed(address)
    ripeAllocation: uint256
    creationBlock: uint256
    claimStartBlock: uint256
    maturityBlock: uint256

event ClaimRecorded:
    user: indexed(address)
    positionId: indexed(uint256)
    amountClaimed: uint256
    totalClaimedForPosition: uint256
    ripeAllocation: uint256
    fullyClaimed: bool

event RemainingAllocationBudgetSet:
    amount: uint256

# claim positions
positions: public(HashMap[address, HashMap[uint256, VestingPosition]]) # user -> index -> position
indexOfPosition: public(HashMap[address, HashMap[uint256, uint256]]) # user -> position id -> index
numUserPositions: public(HashMap[address, uint256]) # user -> active position count
nextPositionId: public(uint256)

# global state
totalAllocatedRipe: public(uint256)
totalClaimedRipe: public(uint256)
remainingAllocationBudget: public(uint256)


@deploy
def __init__(_ripeHq: address):
    addys.__init__(_ripeHq)
    deptBasics.__init__(True, False, False) # starts paused; no mint capability

    self.nextPositionId = 1


#############
# positions #
#############


@nonreentrant
@external
def createVestingPosition(
    _user: address,
    _ripeAllocation: uint256,
    _vestingLength: uint256,
    _minVestingLength: uint256,
) -> uint256:
    assert not deptBasics.isPaused # dev: paused
    assert msg.sender == addys._getRipeReserveEngineAddr() # dev: invalid engine

    # basic validation
    assert _user != empty(address) # dev: invalid user
    assert _ripeAllocation != 0 # dev: invalid allocation
    assert _ripeAllocation <= self.remainingAllocationBudget # dev: allocation budget
    assert _minVestingLength != 0 # dev: invalid minimum vesting
    assert _vestingLength >= _minVestingLength # dev: invalid vesting length

    # create position
    creationBlock: uint256 = block.number
    assert _minVestingLength <= max_value(uint256) - creationBlock # dev: claim start overflow
    assert _vestingLength <= max_value(uint256) - creationBlock # dev: maturity overflow
    claimStartBlock: uint256 = creationBlock + _minVestingLength
    maturityBlock: uint256 = creationBlock + _vestingLength
    nextPositionId: uint256 = self.nextPositionId
    position: VestingPosition = VestingPosition(
        id=nextPositionId,
        ripeAllocation=_ripeAllocation,
        ripeClaimed=0,
        creationBlock=creationBlock,
        claimStartBlock=claimStartBlock,
        maturityBlock=maturityBlock,
    )
    self._addPositionToUser(_user, position)

    # global state
    self.remainingAllocationBudget -= _ripeAllocation
    self.totalAllocatedRipe += _ripeAllocation
    self.nextPositionId = nextPositionId + 1

    log VestingPositionCreated(
        user=_user,
        positionId=position.id,
        sourceEngine=msg.sender,
        ripeAllocation=_ripeAllocation,
        creationBlock=creationBlock,
        claimStartBlock=claimStartBlock,
        maturityBlock=maturityBlock,
    )
    return position.id


# add position


@internal
def _addPositionToUser(_user: address, _position: VestingPosition):
    assert self.indexOfPosition[_user][_position.id] == 0 # dev: duplicate position

    positionIndex: uint256 = self.numUserPositions[_user] + 1 # not using 0 index
    assert self.positions[_user][positionIndex].id == 0 # dev: occupied position

    self.positions[_user][positionIndex] = _position
    self.indexOfPosition[_user][_position.id] = positionIndex
    self.numUserPositions[_user] = positionIndex


# remove position


@internal
def _removePositionFromUser(_user: address, _positionId: uint256):
    numUserPositions: uint256 = self.numUserPositions[_user]
    assert numUserPositions != 0 # dev: no positions

    targetIndex: uint256 = self.indexOfPosition[_user][_positionId]
    assert targetIndex != 0 and targetIndex <= numUserPositions # dev: invalid position

    lastIndex: uint256 = numUserPositions

    if targetIndex != lastIndex:
        lastPosition: VestingPosition = self.positions[_user][lastIndex]
        assert lastPosition.id != 0 # dev: invalid last position
        self.positions[_user][targetIndex] = lastPosition
        self.indexOfPosition[_user][lastPosition.id] = targetIndex

    self.positions[_user][lastIndex] = empty(VestingPosition)
    self.indexOfPosition[_user][_positionId] = 0
    self.numUserPositions[_user] = numUserPositions - 1


#################
# record claims #
#################


@nonreentrant
@external
def recordClaim(_user: address, _positionId: uint256) -> (uint256, uint256, uint256):
    assert not deptBasics.isPaused # dev: paused
    assert msg.sender == addys._getRipeReserveEngineAddr() # dev: invalid engine
    assert _user != empty(address) # dev: invalid user

    # validate position exists
    index: uint256 = self.indexOfPosition[_user][_positionId]
    assert index != 0 # dev: invalid position

    # check claimable ripe
    position: VestingPosition = self.positions[_user][index]
    claimableRipe: uint256 = self._getVestedRipe(position) - position.ripeClaimed
    assert claimableRipe != 0 # dev: nothing to claim

    # update position
    position.ripeClaimed += claimableRipe
    self.positions[_user][index] = position

    # remove position if fully claimed
    fullyClaimed: bool = position.ripeClaimed == position.ripeAllocation
    if fullyClaimed:
        self._removePositionFromUser(_user, position.id)

    # global state
    self.totalClaimedRipe += claimableRipe
    log ClaimRecorded(
        user=_user,
        positionId=position.id,
        amountClaimed=claimableRipe,
        totalClaimedForPosition=position.ripeClaimed,
        ripeAllocation=position.ripeAllocation,
        fullyClaimed=fullyClaimed,
    )
    return claimableRipe, position.ripeClaimed, position.ripeAllocation


#################
# vesting views #
#################


@view
@external
def getNumUserPositions(_user: address) -> uint256:
    return self.numUserPositions[_user]


@view
@external
def getClaimableRipe(_user: address, _positionId: uint256) -> uint256:
    index: uint256 = self.indexOfPosition[_user][_positionId]
    if index == 0:
        return 0
    position: VestingPosition = self.positions[_user][index]
    return self._getVestedRipe(position) - position.ripeClaimed


@view
@external
def totalOutstandingRipe() -> uint256:
    return self.totalAllocatedRipe - self.totalClaimedRipe


@view
@external
def canRetire() -> bool:
    return deptBasics.isPaused and self.totalAllocatedRipe - self.totalClaimedRipe == 0


@view
@external
def getVestedRipe(_user: address, _positionId: uint256) -> uint256:
    index: uint256 = self.indexOfPosition[_user][_positionId]
    if index == 0:
        return 0
    return self._getVestedRipe(self.positions[_user][index])


@view
@internal
def _getVestedRipe(_position: VestingPosition) -> uint256:
    if block.number < _position.claimStartBlock:
        return 0
    if block.number >= _position.maturityBlock:
        return _position.ripeAllocation

    elapsed: uint256 = block.number - _position.creationBlock
    duration: uint256 = _position.maturityBlock - _position.creationBlock
    return self._mulDivFloor(_position.ripeAllocation, elapsed, duration)


# safe math


@pure
@internal
def _mulDivFloor(_x: uint256, _y: uint256, _d: uint256) -> uint256:
    assert _d != 0 # dev: zero denominator

    lo: uint256 = unsafe_mul(_x, _y)
    mm: uint256 = uint256_mulmod(_x, _y, max_value(uint256))
    hi: uint256 = unsafe_sub(
        unsafe_sub(mm, lo),
        convert(mm < lo, uint256),
    )

    # fast path: the product fits in 256 bits.
    if hi == 0:
        return lo // _d

    # the full-precision result must fit in uint256.
    assert _d > hi # dev: result overflows

    # make the 512-bit product exactly divisible by the denominator.
    rem: uint256 = uint256_mulmod(_x, _y, _d)
    hi = unsafe_sub(hi, convert(rem > lo, uint256))
    lo = unsafe_sub(lo, rem)

    # factor powers of two out of the denominator and shift the
    # high product bits into the low product word.
    tz: uint256 = unsafe_sub(0, _d) & _d
    d2: uint256 = _d // tz
    lo = lo // tz
    lo |= unsafe_mul(
        hi,
        unsafe_add(
            unsafe_div(unsafe_sub(0, tz), tz),
            1,
        ),
    )

    # compute the modular inverse of the now-odd denominator.
    inv: uint256 = unsafe_mul(3, d2) ^ 2
    for i: uint256 in range(6):
        inv = unsafe_mul(
            inv,
            unsafe_sub(2, unsafe_mul(d2, inv)),
        )

    return unsafe_mul(lo, inv)


#####################
# allocation budget #
#####################


@nonreentrant
@external
def setRemainingAllocationBudget(_amount: uint256):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    self.remainingAllocationBudget = _amount
    log RemainingAllocationBudgetSet(amount=_amount)
