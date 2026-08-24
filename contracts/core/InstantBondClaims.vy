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

from ethereum.ercs import IERC20

interface RipeToken:
    def ripeHq() -> address: view
    def isPaused() -> bool: view

interface RipeHq:
    def ripeToken() -> address: view
    def canMintRipe(_addr: address) -> bool: view

interface InstantBondLane:
    def CLAIMS() -> address: view
    def settleVestedRipe(_beneficiary: address, _amount: uint256, _autoDeposit: bool, _lockDuration: uint256) -> bool: nonpayable

struct VestingPosition:
    ripePayout: uint256
    ripeClaimed: uint256
    creationBlock: uint256
    maturityBlock: uint256

event VestingPositionCreated:
    beneficiary: indexed(address)
    positionIndex: indexed(uint256)
    sourceLane: indexed(address)
    ripePayout: uint256
    creationBlock: uint256
    maturityBlock: uint256

event VestedRipeClaimed:
    beneficiary: indexed(address)
    positionIndex: indexed(uint256)
    amountClaimed: uint256
    totalClaimedForPosition: uint256
    ripePayout: uint256
    autoDeposited: bool
    lockDuration: uint256

positions: public(HashMap[address, HashMap[uint256, VestingPosition]])
positionCount: public(HashMap[address, uint256])
totalAllocatedRipe: public(uint256)
totalClaimedRipe: public(uint256)

RIPE_TOKEN: public(immutable(address))
MAX_VESTING_LENGTH: public(constant(uint256)) = 7_884_000


@deploy
def __init__(_ripeHq: address):
    addys.__init__(_ripeHq)
    deptBasics.__init__(True, False, False) # starts paused; no mint capability

    ripeToken: address = staticcall RipeHq(_ripeHq).ripeToken()
    assert ripeToken != empty(address) and ripeToken.is_contract # dev: invalid ripe token
    RIPE_TOKEN = ripeToken
    assert staticcall RipeHq(_ripeHq).ripeToken() == RIPE_TOKEN # dev: invalid ripe token
    assert staticcall RipeToken(RIPE_TOKEN).ripeHq() == _ripeHq # dev: invalid token hq


#############
# Positions #
#############


@nonreentrant
@external
def createVestingPosition(
    _beneficiary: address,
    _ripePayout: uint256,
    _vestingLength: uint256,
) -> uint256:
    assert not deptBasics.isPaused # dev: paused

    lane: address = addys._getInstantBondLaneAddr()
    assert msg.sender == lane # dev: invalid lane
    assert staticcall InstantBondLane(msg.sender).CLAIMS() == self # dev: incompatible lane

    ripeHq: address = addys._getRipeHq()
    assert staticcall RipeHq(ripeHq).ripeToken() == RIPE_TOKEN # dev: invalid ripe token
    assert staticcall RipeToken(RIPE_TOKEN).ripeHq() == ripeHq # dev: invalid token hq
    assert not staticcall RipeToken(RIPE_TOKEN).isPaused() # dev: ripe token paused
    assert staticcall RipeHq(ripeHq).canMintRipe(msg.sender) # dev: cannot mint ripe

    assert _beneficiary != empty(address) # dev: invalid beneficiary
    assert _ripePayout != 0 # dev: invalid payout
    assert _vestingLength != 0 and _vestingLength <= MAX_VESTING_LENGTH # dev: invalid vesting length
    assert _vestingLength <= max_value(uint256) - block.number # dev: maturity overflow

    positionIndex: uint256 = self.positionCount[_beneficiary] + 1
    creationBlock: uint256 = block.number
    maturityBlock: uint256 = creationBlock + _vestingLength

    self.positionCount[_beneficiary] = positionIndex
    self.positions[_beneficiary][positionIndex] = VestingPosition(
        ripePayout=_ripePayout,
        ripeClaimed=0,
        creationBlock=creationBlock,
        maturityBlock=maturityBlock,
    )
    self.totalAllocatedRipe += _ripePayout

    log VestingPositionCreated(
        beneficiary=_beneficiary,
        positionIndex=positionIndex,
        sourceLane=msg.sender,
        ripePayout=_ripePayout,
        creationBlock=creationBlock,
        maturityBlock=maturityBlock,
    )
    return positionIndex


##########
# Claims #
##########


@nonreentrant
@external
def claimVestedRipe(
    _positionIndex: uint256,
    _autoDeposit: bool,
    _lockDuration: uint256,
) -> uint256:
    assert not deptBasics.isPaused # dev: paused
    assert _positionIndex != 0 and _positionIndex <= self.positionCount[msg.sender] # dev: invalid position

    position: VestingPosition = self.positions[msg.sender][_positionIndex]
    vestedRipe: uint256 = self._getVestedRipe(position)
    claimableRipe: uint256 = vestedRipe - position.ripeClaimed
    assert claimableRipe != 0 # dev: nothing to claim

    if _autoDeposit:
        assert _lockDuration != 0 # dev: invalid lock duration
    else:
        assert _lockDuration == 0 # dev: invalid lock duration

    lane: address = addys._getInstantBondLaneAddr()
    assert lane != empty(address) # dev: invalid lane
    assert staticcall InstantBondLane(lane).CLAIMS() == self # dev: incompatible lane

    ripeHq: address = addys._getRipeHq()
    assert staticcall RipeHq(ripeHq).ripeToken() == RIPE_TOKEN # dev: invalid ripe token
    assert staticcall RipeToken(RIPE_TOKEN).ripeHq() == ripeHq # dev: invalid token hq
    assert not staticcall RipeToken(RIPE_TOKEN).isPaused() # dev: ripe token paused

    balanceBefore: uint256 = 0
    if not _autoDeposit:
        balanceBefore = staticcall IERC20(RIPE_TOKEN).balanceOf(msg.sender)

    position.ripeClaimed += claimableRipe
    self.positions[msg.sender][_positionIndex] = position
    self.totalClaimedRipe += claimableRipe

    assert extcall InstantBondLane(lane).settleVestedRipe(msg.sender, claimableRipe, _autoDeposit, _lockDuration) # dev: settlement failed

    if not _autoDeposit:
        balanceAfter: uint256 = staticcall IERC20(RIPE_TOKEN).balanceOf(msg.sender)
        assert balanceAfter >= balanceBefore # dev: ripe receipt mismatch
        assert balanceAfter - balanceBefore == claimableRipe # dev: ripe receipt mismatch

    log VestedRipeClaimed(
        beneficiary=msg.sender,
        positionIndex=_positionIndex,
        amountClaimed=claimableRipe,
        totalClaimedForPosition=position.ripeClaimed,
        ripePayout=position.ripePayout,
        autoDeposited=_autoDeposit,
        lockDuration=_lockDuration,
    )
    return claimableRipe


#################
# Vesting Views #
#################


@view
@external
def getVestedRipe(_beneficiary: address, _positionIndex: uint256) -> uint256:
    if _positionIndex == 0 or _positionIndex > self.positionCount[_beneficiary]:
        return 0
    return self._getVestedRipe(self.positions[_beneficiary][_positionIndex])


@view
@external
def getClaimableRipe(_beneficiary: address, _positionIndex: uint256) -> uint256:
    if _positionIndex == 0 or _positionIndex > self.positionCount[_beneficiary]:
        return 0
    position: VestingPosition = self.positions[_beneficiary][_positionIndex]
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
