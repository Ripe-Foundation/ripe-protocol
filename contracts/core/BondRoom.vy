# @version 0.4.1

implements: Department

exports: addys.__interface__
exports: deptBasics.__interface__

initializes: addys
initializes: deptBasics[addys := addys]

import contracts.modules.Addys as addys
import contracts.modules.DeptBasics as deptBasics
from interfaces import Department

from ethereum.ercs import IERC20
from ethereum.ercs import IERC20Detailed

interface Ledger:
    def setEpochData(_epochStart: uint256, _epochEnd: uint256, _amountAvailInEpoch: uint256): nonpayable
    def didPurchaseRipeBond(_amountPaid: uint256, _ripePayout: uint256): nonpayable
    def didClearBadDebt(_amount: uint256, _ripeAmount: uint256): nonpayable
    def getEpochData() -> (uint256, uint256): view
    def getRipeBondData() -> RipeBondData: view

interface Teller:
    def depositIntoGovVaultFromTrusted(_user: address, _asset: address, _amount: uint256, _lockDuration: uint256, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable

interface PriceDesk:
    def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool = False) -> uint256: view

interface MissionControl:
    def getPurchaseRipeBondConfig(_user: address) -> PurchaseRipeBondConfig: view

interface RipeToken:
    def mint(_to: address, _amount: uint256): nonpayable

struct PurchaseRipeBondConfig:
    asset: address
    amountPerEpoch: uint256
    canBond: bool
    minRipePerUnit: uint256
    maxRipePerUnit: uint256
    maxRipePerUnitLockBonus: uint256
    epochLength: uint256
    shouldAutoRestart: bool
    restartDelayBlocks: uint256
    minLockDuration: uint256
    maxLockDuration: uint256
    canAnyoneBondForUser: bool

struct RipeBondData:
    paymentAmountAvailInEpoch: uint256
    ripeAvailForBonds: uint256
    badDebt: uint256

event RipeBondPurchased:
    user: indexed(address)
    paymentAsset: indexed(address)
    paymentAmount: uint256
    lockDuration: uint256
    ripePayout: uint256
    ripeForBadDebt: uint256
    baseRipePerUnit: uint256
    ripePerUnitBonus: uint256
    epochProgress: uint256
    refundAmount: uint256
    caller: indexed(address)

HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%


@deploy
def __init__(_ripeHq: address):
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, False, True) # can mint ripe only


##############
# Ripe Bonds #
##############


@external
def purchaseRipeBond(
    _user: address,
    _paymentAsset: address,
    _paymentAmount: uint256,
    _lockDuration: uint256,
    _caller: address,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    assert msg.sender == addys._getTellerAddr() # dev: only Teller allowed
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)
    return self._purchaseRipeBond(_user, _paymentAsset, _paymentAmount, _lockDuration, _caller, a)


@internal
def _purchaseRipeBond(
    _user: address,
    _paymentAsset: address,
    _paymentAmount: uint256,
    _lockDuration: uint256,
    _caller: address,
    _a: addys.Addys,
) -> uint256:
    assert _user != empty(address) # dev: invalid user
    maxUserAmount: uint256 = min(_paymentAmount, staticcall IERC20(_paymentAsset).balanceOf(self))
    assert maxUserAmount != 0 # dev: user has no asset balance (or zero specified)

    config: PurchaseRipeBondConfig = staticcall MissionControl(_a.missionControl).getPurchaseRipeBondConfig(_user)
    assert config.asset == _paymentAsset # dev: asset mismatch
    assert config.canBond # dev: bonds disabled
    if _user != _caller:
        assert config.canAnyoneBondForUser # dev: cannot bond for user

    # refresh epoch if necessary
    epochStart: uint256 = 0
    epochEnd: uint256 = 0
    epochStart, epochEnd = self._refreshBondEpoch(_a.ledger, config.amountPerEpoch, config.epochLength)
    assert block.number >= epochStart and block.number < epochEnd # dev: not within epoch window

    # check availability - do after epoch refresh!
    data: RipeBondData = staticcall Ledger(_a.ledger).getRipeBondData()
    assert data.paymentAmountAvailInEpoch != 0 # dev: no more available in epoch
    paymentAmount: uint256 = min(maxUserAmount, data.paymentAmountAvailInEpoch)

    # base ripe payout
    epochProgress: uint256 = (block.number - epochStart) * HUNDRED_PERCENT // (epochEnd - epochStart)
    baseRipePerUnit: uint256 = self._calcRipePerUnit(epochProgress, config.minRipePerUnit, config.maxRipePerUnit)

    # bonus for lock duration
    ripePerUnitBonus: uint256 = 0
    lockDuration: uint256 = min(_lockDuration, config.maxLockDuration)
    if lockDuration >= config.minLockDuration:
        ripePerUnitBonus = config.maxRipePerUnitLockBonus * (lockDuration - config.minLockDuration) // (config.maxLockDuration - config.minLockDuration)
    else:
        lockDuration = 0

    # finalize ripe payout
    ripePerUnit: uint256 = baseRipePerUnit + ripePerUnitBonus
    ripePayout: uint256 = ripePerUnit * paymentAmount // (10 ** convert(staticcall IERC20Detailed(_paymentAsset).decimals(), uint256))
    assert ripePayout != 0 # dev: bad deal, user is not getting fair amount of Ripe
    assert ripePayout <= data.ripeAvailForBonds # dev: not enough ripe avail

    # handle bad debt (if applicable)
    ripeForBadDebt: uint256 = 0
    if data.badDebt != 0:
        paymentUsdValue: uint256 = staticcall PriceDesk(_a.priceDesk).getUsdValue(_paymentAsset, paymentAmount, False)
        if paymentUsdValue != 0:
            ripeForBadDebt = ripePayout
            debtRepaymentValue: uint256 = min(paymentUsdValue, data.badDebt)
            if debtRepaymentValue < paymentUsdValue:
                ripeForBadDebt = ripePayout * debtRepaymentValue // paymentUsdValue
            extcall Ledger(_a.ledger).didClearBadDebt(debtRepaymentValue, ripeForBadDebt)

    # update bond data -- amount avail in epoch is reduced even if bad debt is repaid
    extcall Ledger(_a.ledger).didPurchaseRipeBond(paymentAmount, ripePayout - ripeForBadDebt)

    # transfer payment proceeds to endaoment
    assert extcall IERC20(_paymentAsset).transfer(_a.endaoment, paymentAmount, default_return_value=True) # dev: asset transfer failed

    # mint ripe tokens, deposit into gov vault or transfer tokens to user
    if lockDuration != 0:
        extcall RipeToken(_a.ripeToken).mint(self, ripePayout)
        assert extcall IERC20(_a.ripeToken).approve(_a.teller, ripePayout, default_return_value=True) # dev: ripe approval failed
        extcall Teller(_a.teller).depositIntoGovVaultFromTrusted(_user, _a.ripeToken, ripePayout, lockDuration, _a)
        assert extcall IERC20(_a.ripeToken).approve(_a.teller, 0, default_return_value=True) # dev: ripe approval failed
    else:
        extcall RipeToken(_a.ripeToken).mint(_user, ripePayout)

    # refund user any extra payment amount
    refundAmount: uint256 = 0
    if _paymentAmount > paymentAmount:
        refundAmount = min(_paymentAmount - paymentAmount, staticcall IERC20(_paymentAsset).balanceOf(self))
        assert extcall IERC20(_paymentAsset).transfer(_caller, refundAmount, default_return_value=True) # dev: asset transfer failed

    # start next epoch (if applicable)
    if paymentAmount == data.paymentAmountAvailInEpoch and config.shouldAutoRestart:
        newStartBlock: uint256 = block.number + config.restartDelayBlocks
        extcall Ledger(_a.ledger).setEpochData(newStartBlock, newStartBlock + config.epochLength, config.amountPerEpoch)

    log RipeBondPurchased(user=_user, paymentAsset=_paymentAsset, paymentAmount=paymentAmount, lockDuration=lockDuration, ripePayout=ripePayout, ripeForBadDebt=ripeForBadDebt, baseRipePerUnit=baseRipePerUnit, ripePerUnitBonus=ripePerUnitBonus, epochProgress=epochProgress, refundAmount=refundAmount, caller=_caller)
    return ripePayout


@pure
@internal
def _calcRipePerUnit(_ratio: uint256, _minRipePerUnit: uint256, _maxRipePerUnit: uint256) -> uint256:
    if _ratio == 0 or _minRipePerUnit == _maxRipePerUnit:
        return _minRipePerUnit
    valRange: uint256 = _maxRipePerUnit - _minRipePerUnit
    adjustment: uint256 =  _ratio * valRange // HUNDRED_PERCENT
    return _minRipePerUnit + adjustment


##########
# Epochs #
##########


# start at block


@external
def startBondEpochAtBlock(_block: uint256):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()

    config: PurchaseRipeBondConfig = staticcall MissionControl(a.missionControl).getPurchaseRipeBondConfig(empty(address))
    startBlock: uint256 = max(_block, block.number)
    extcall Ledger(a.ledger).setEpochData(startBlock, startBlock + config.epochLength, config.amountPerEpoch)


# refresh epoch


@external 
def refreshBondEpoch() -> (uint256, uint256):
    assert addys._isValidRipeAddr(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()

    config: PurchaseRipeBondConfig = staticcall MissionControl(a.missionControl).getPurchaseRipeBondConfig(empty(address))
    return self._refreshBondEpoch(a.ledger, config.amountPerEpoch, config.epochLength)


@internal
def _refreshBondEpoch(
    _ledger: address,
    _amountPerEpoch: uint256,
    _epochLength: uint256,
) -> (uint256, uint256):
    startBlock: uint256 = 0
    endBlock: uint256 = 0
    startBlock, endBlock = staticcall Ledger(_ledger).getEpochData()

    didChange: bool = False
    startBlock, endBlock, didChange = self._getLatestEpochBlockTimes(startBlock, endBlock, _epochLength)
    if didChange:
        extcall Ledger(_ledger).setEpochData(startBlock, endBlock, _amountPerEpoch)

    return startBlock, endBlock


# get epoch blocks


@view
@external
def getLatestEpochBlockTimes(_prevStartBlock: uint256, _prevEndBlock: uint256, _epochLength: uint256) -> (uint256, uint256, bool):
    return self._getLatestEpochBlockTimes(_prevStartBlock, _prevEndBlock, _epochLength)


@view
@internal
def _getLatestEpochBlockTimes(
    _prevStartBlock: uint256,
    _prevEndBlock: uint256,
    _epochLength: uint256,
) -> (uint256, uint256, bool):
    startBlock: uint256 = _prevStartBlock
    endBlock: uint256 = _prevEndBlock

    # nothing to do here (start block is in future, or current block is before end block)
    if block.number < startBlock or block.number < endBlock:
        return startBlock, endBlock, False

    # nothing has been set yet, start now
    if startBlock == 0 or endBlock == 0:
        return block.number, block.number + _epochLength, True

    # past existing end block, still within next epoch window -- this could set start time in past
    newStartBlock: uint256 = 0
    if block.number < (endBlock + _epochLength):
        newStartBlock = endBlock

    # past next window, past everything
    else:
        epochsAhead: uint256 = (block.number - endBlock) // _epochLength
        newStartBlock = _epochLength * epochsAhead + endBlock

    return newStartBlock, newStartBlock + _epochLength, True
