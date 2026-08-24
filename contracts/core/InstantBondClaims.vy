#    ___  ________   ________  _________  ________  ________   _________        ________  ________  ________   ________  ________
#   |\  \|\   ___  \|\   ____\|\___   ___\\   __  \|\   ___  \|\___   ___\     |\   __  \|\   __  \|\   ___  \|\   ___ \|\   ____\
#   \ \  \ \  \\ \  \ \  \___|\|___ \  \_\ \  \|\  \ \  \\ \  \|___ \  \_|     \ \  \|\ /\ \  \|\  \ \  \\ \  \ \  \_|\ \ \  \___|_
#    \ \  \ \  \\ \  \ \_____  \   \ \  \ \ \   __  \ \  \\ \  \   \ \  \       \ \   __  \ \  \\\  \ \  \\ \  \ \  \ \\ \ \_____  \
#     \ \  \ \  \\ \  \|____|\  \   \ \  \ \ \  \ \  \ \  \\ \  \   \ \  \       \ \  \|\  \ \  \\\  \ \  \\ \  \ \  \_\\ \|____|\  \
#      \ \__\ \__\\ \__\____\_\  \   \ \__\ \ \__\ \__\ \__\\ \__\   \ \__\       \ \_______\ \_______\ \__\\ \__\ \_______\____\_\  \
#       \|__|\|__| \|__|\_________\   \|__|  \|__|\|__|\|__| \|__|    \|__|        \|_______|\|_______|\|__| \|__|\|_______|\_________\
#                      \|_________|                                                                                        \|_________|
#
#     Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
#     Ripe Foundation (C) 2026

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
    ripePayout: uint256
    ripeClaimed: uint256
    creationBlock: uint256
    maturityBlock: uint256

event VestingPositionCreated:
    user: indexed(address)
    positionIndex: indexed(uint256)
    sourceLane: indexed(address)
    ripePayout: uint256
    creationBlock: uint256
    maturityBlock: uint256

event RemainingAllocationBudgetSet:
    amount: uint256

# claim positions
positions: public(HashMap[address, HashMap[uint256, VestingPosition]]) # user -> index -> position
indexOfPosition: public(HashMap[address, HashMap[uint256, uint256]]) # user -> position id -> index
numUserPositions: public(HashMap[address, uint256]) # user -> num positions
nextPositionId: public(uint256)

# global state
totalAllocatedRipe: public(uint256)
totalClaimedRipe: public(uint256)
remainingAllocationBudget: public(uint256)


@deploy
def __init__(_ripeHq: address):
    addys.__init__(_ripeHq)
    deptBasics.__init__(True, False, False) # starts paused; no mint capability


#####################
# Allocation Budget #
#####################


@nonreentrant
@external
def setRemainingAllocationBudget(_amount: uint256):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    self.remainingAllocationBudget = _amount
    log RemainingAllocationBudgetSet(amount=_amount)


#############
# Positions #
#############


@nonreentrant
@external
def createVestingPosition(
    _user: address,
    _ripePayout: uint256,
    _vestingLength: uint256,
) -> uint256:
    assert not deptBasics.isPaused # dev: paused
    assert msg.sender == addys._getInstantBondLaneAddr() # dev: invalid lane

    # basic validation
    assert _user != empty(address) # dev: invalid user
    assert _ripePayout != 0 # dev: invalid payout
    assert _ripePayout <= self.remainingAllocationBudget # dev: allocation budget

    # create position
    creationBlock: uint256 = block.number
    maturityBlock: uint256 = creationBlock + _vestingLength
    position: VestingPosition = VestingPosition(
        id=self.nextPositionId + 1,
        ripePayout=_ripePayout,
        ripeClaimed=0,
        creationBlock=creationBlock,
        maturityBlock=maturityBlock,
    )
    self._addPositionToUser(_user, position)

    # global state
    self.remainingAllocationBudget -= _ripePayout
    self.totalAllocatedRipe += _ripePayout
    self.nextPositionId = position.id

    log VestingPositionCreated(
        user=_user,
        positionIndex=position.id,
        sourceLane=msg.sender,
        ripePayout=_ripePayout,
        creationBlock=creationBlock,
        maturityBlock=maturityBlock,
    )
    return position.id


# add position


@internal
def _addPositionToUser(_user: address, _position: VestingPosition):
    if self.indexOfPosition[_user][_position.id] != 0:
        return

    pid: uint256 = self.numUserPositions[_user]
    if pid == 0:
        pid = 1 # not using 0 index

    self.positions[_user][pid] = _position
    self.indexOfPosition[_user][_position.id] = pid
    self.numUserPositions[_user] = pid + 1


# remove position


@internal
def _removePositionFromUser(_user: address, _positionId: uint256):
    numUserPositions: uint256 = self.numUserPositions[_user]
    if numUserPositions == 0:
        return

    targetIndex: uint256 = self.indexOfPosition[_user][_positionId]
    if targetIndex == 0:
        return

    lastIndex: uint256 = numUserPositions - 1
    self.numUserPositions[_user] = lastIndex
    self.indexOfPosition[_user][_positionId] = 0

    if targetIndex != lastIndex:
        lastPosition: VestingPosition = self.positions[_user][lastIndex]
        self.positions[_user][targetIndex] = lastPosition
        self.indexOfPosition[_user][lastPosition.id] = targetIndex


#################
# Record Claims #
#################


@nonreentrant
@external
def recordClaim(_user: address, _positionId: uint256) -> (uint256, uint256, uint256):
    assert not deptBasics.isPaused # dev: paused
    assert msg.sender == addys._getInstantBondLaneAddr() # dev: invalid lane
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
    if position.ripeClaimed == position.ripePayout:
        self._removePositionFromUser(_user, position.id)

    # global state
    self.totalClaimedRipe += claimableRipe
    return claimableRipe, position.ripeClaimed, position.ripePayout


#################
# Vesting Views #
#################


@view
@external
def getNumUserPositions(_user: address) -> uint256:
    numPositions: uint256 = self.numUserPositions[_user]
    if numPositions == 0:
        return 0
    return numPositions - 1


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
def getVestedRipe(_user: address, _positionId: uint256) -> uint256:
    index: uint256 = self.indexOfPosition[_user][_positionId]
    if index == 0:
        return 0
    return self._getVestedRipe(self.positions[_user][index])


@view
@internal
def _getVestedRipe(_position: VestingPosition) -> uint256:
    if block.number <= _position.creationBlock:
        return 0
    if block.number >= _position.maturityBlock:
        return _position.ripePayout

    elapsed: uint256 = block.number - _position.creationBlock
    duration: uint256 = _position.maturityBlock - _position.creationBlock
    quotient: uint256 = _position.ripePayout // duration
    remainder: uint256 = _position.ripePayout % duration
    return quotient * elapsed + remainder * elapsed // duration
