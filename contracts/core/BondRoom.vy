#                      _,.---._     .-._                                             _,.---._        _,.---._            ___   
#          _..---.   ,-.' , -  `.  /==/ \  .-._   _,..---._           .-.,.---.    ,-.' , -  `.    ,-.' , -  `.   .-._ .'=.'\  
#        .' .'.-. \ /==/_,  ,  - \ |==|, \/ /, //==/,   -  \         /==/  `   \  /==/_,  ,  - \  /==/_,  ,  - \ /==/ \|==|  | 
#       /==/- '=' /|==|   .=.     ||==|-  \|  | |==|   _   _\       |==|-, .=., ||==|   .=.     ||==|   .=.     ||==|,|  / - | 
#       |==|-,   ' |==|_ : ;=:  - ||==| ,  | -| |==|  .=.   |       |==|   '='  /|==|_ : ;=:  - ||==|_ : ;=:  - ||==|  \/  , | 
#       |==|  .=. \|==| , '='     ||==| -   _ | |==|,|   | -|       |==|- ,   .' |==| , '='     ||==| , '='     ||==|- ,   _ | 
#       /==/- '=' ,|\==\ -    ,_ / |==|  /\ , | |==|  '='   /       |==|_  . ,'.  \==\ -    ,_ /  \==\ -    ,_ / |==| _ /\   | 
#      |==|   -   /  '.='. -   .'  /==/, | |- | |==|-,   _`/        /==/  /\ ,  )  '.='. -   .'    '.='. -   .'  /==/  / / , / 
#      `-._`.___,'     `--`--''    `--`./  `--` `-.`.____.'         `--`-`--`--'     `--`--''        `--`--''    `--`./  `--`  
#
#     ╔════════════════════════════════════════╗
#     ║  ** Bond Room **                       ║
#     ║  Where users can purhcase Ripe bonds   ║
#     ╚════════════════════════════════════════╝
#
#     Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
#     Ripe Foundation (C) 2025

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
from ethereum.ercs import IERC20Detailed

interface Ledger:
    def setEpochData(_epochStart: uint256, _epochEnd: uint256, _amountAvailInEpoch: uint256): nonpayable
    def didPurchaseRipeBond(_amountPaid: uint256, _ripePayout: uint256): nonpayable
    def didClearBadDebt(_amount: uint256, _ripeAmount: uint256): nonpayable
    def getEpochData() -> (uint256, uint256): view
    def getRipeBondData() -> RipeBondData: view

interface Teller:
    def depositFromTrusted(_user: address, _vaultId: uint256, _asset: address, _amount: uint256, _lockDuration: uint256, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def isUnderscoreWalletOwner(_user: address, _caller: address, _mc: address = empty(address)) -> bool: view

interface BondBooster:
    def getBoostRatio(_user: address, _units: uint256) -> uint256: view
    def addNewUnitsUsed(_user: address, _newUnits: uint256): nonpayable

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
    isUserAllowed: bool

struct RipeBondData:
    paymentAmountAvailInEpoch: uint256
    ripeAvailForBonds: uint256
    badDebt: uint256

event RipeBondPurchased:
    recipient: indexed(address)
    paymentAsset: indexed(address)
    paymentAmount: uint256
    lockDuration: uint256
    ripePerUnit: uint256
    totalRipePayout: uint256
    baseRipePayout: uint256
    ripeLockBonus: uint256
    ripeBoostBonus: uint256
    ripeForBadDebt: uint256
    epochProgress: uint256
    refundAmount: uint256
    caller: indexed(address)

event BondBoosterSet:
    bondBooster: address

HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%
RIPE_GOV_VAULT_ID: constant(uint256) = 2

bondBooster: public(address)


@deploy
def __init__(_ripeHq: address, _bondBooster: address):
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, False, True) # can mint ripe only

    self.bondBooster = _bondBooster


##############
# Ripe Bonds #
##############


@external
def purchaseRipeBond(
    _recipient: address,
    _paymentAsset: address,
    _paymentAmount: uint256,
    _lockDuration: uint256,
    _caller: address,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    assert msg.sender == addys._getTellerAddr() # dev: only Teller allowed
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)

    assert _recipient != empty(address) # dev: invalid user
    maxUserAmount: uint256 = min(_paymentAmount, staticcall IERC20(_paymentAsset).balanceOf(self))
    assert maxUserAmount != 0 # dev: user has no asset balance (or zero specified)

    config: PurchaseRipeBondConfig = staticcall MissionControl(a.missionControl).getPurchaseRipeBondConfig(_recipient)
    assert config.asset == _paymentAsset # dev: asset mismatch
    assert config.maxRipePerUnit != 0 # dev: max ripe per unit is zero
    assert config.canBond # dev: bonds disabled
    assert config.isUserAllowed # dev: user not on whitelist

    # can others bond for user
    if _recipient != _caller and not config.canAnyoneBondForUser:
        assert staticcall Teller(a.teller).isUnderscoreWalletOwner(_recipient, _caller, a.missionControl) # dev: cannot bond for user

    # refresh epoch if necessary
    epochStart: uint256 = 0
    epochEnd: uint256 = 0
    epochStart, epochEnd = self._refreshBondEpoch(a.ledger, config.amountPerEpoch, config.epochLength)
    assert block.number >= epochStart and block.number < epochEnd # dev: not within epoch window

    # check availability - do AFTER epoch refresh!
    data: RipeBondData = staticcall Ledger(a.ledger).getRipeBondData()
    assert data.paymentAmountAvailInEpoch != 0 # dev: no more available in epoch
    paymentAmount: uint256 = min(maxUserAmount, data.paymentAmountAvailInEpoch)

    # base ripe payout
    epochProgress: uint256 = (block.number - epochStart) * HUNDRED_PERCENT // (epochEnd - epochStart)
    ripePerUnit: uint256 = self._calcRipePerUnit(epochProgress, config.minRipePerUnit, config.maxRipePerUnit)

    # main ripe payout
    units: uint256 = paymentAmount // (10 ** convert(staticcall IERC20Detailed(_paymentAsset).decimals(), uint256))
    baseRipePayout: uint256 = ripePerUnit * units
    assert baseRipePayout != 0 # dev: must have base ripe payout
    totalRipePayout: uint256 = baseRipePayout

    # bonus for lock duration
    ripeLockBonus: uint256 = 0
    lockDuration: uint256 = min(_lockDuration, config.maxLockDuration)
    if lockDuration >= config.minLockDuration:
        maxLockBonusRatio: uint256 = min(config.maxRipePerUnitLockBonus, 10 * HUNDRED_PERCENT) # extra sanity check 
        lockBonusRatio: uint256 = maxLockBonusRatio * (lockDuration - config.minLockDuration) // (config.maxLockDuration - config.minLockDuration)
        ripeLockBonus = baseRipePayout * lockBonusRatio // HUNDRED_PERCENT
        totalRipePayout += ripeLockBonus
    else:
        lockDuration = 0

    # bonus from bond booster (if applicable)
    ripeBoostBonus: uint256 = 0
    bondBooster: address = self.bondBooster
    if bondBooster != empty(address):
        boostRatio: uint256 = min(staticcall BondBooster(bondBooster).getBoostRatio(_recipient, units), 10 * HUNDRED_PERCENT) # extra sanity check 
        ripeBoostBonus = baseRipePayout * boostRatio // HUNDRED_PERCENT
        if ripeBoostBonus != 0:
            totalRipePayout += ripeBoostBonus
            extcall BondBooster(bondBooster).addNewUnitsUsed(_recipient, units)

    assert totalRipePayout <= data.ripeAvailForBonds # dev: not enough ripe avail

    # handle bad debt (if applicable)
    ripeForBadDebt: uint256 = 0
    if data.badDebt != 0:
        paymentUsdValue: uint256 = staticcall PriceDesk(a.priceDesk).getUsdValue(_paymentAsset, paymentAmount, False)
        if paymentUsdValue != 0:
            ripeForBadDebt = totalRipePayout
            debtRepaymentValue: uint256 = min(paymentUsdValue, data.badDebt)
            if debtRepaymentValue < paymentUsdValue:
                ripeForBadDebt = totalRipePayout * debtRepaymentValue // paymentUsdValue
            extcall Ledger(a.ledger).didClearBadDebt(debtRepaymentValue, ripeForBadDebt)

    # update bond data -- amount avail in epoch is reduced even if bad debt is repaid
    extcall Ledger(a.ledger).didPurchaseRipeBond(paymentAmount, totalRipePayout - ripeForBadDebt)

    # transfer payment proceeds to endaoment
    assert extcall IERC20(_paymentAsset).transfer(a.endaoment, paymentAmount, default_return_value=True) # dev: asset transfer failed

    # mint ripe tokens, deposit into gov vault or transfer tokens to user
    if lockDuration != 0:
        extcall RipeToken(a.ripeToken).mint(self, totalRipePayout)
        assert extcall IERC20(a.ripeToken).approve(a.teller, totalRipePayout, default_return_value=True) # dev: ripe approval failed
        extcall Teller(a.teller).depositFromTrusted(_recipient, RIPE_GOV_VAULT_ID, a.ripeToken, totalRipePayout, lockDuration, a)
        assert extcall IERC20(a.ripeToken).approve(a.teller, 0, default_return_value=True) # dev: ripe approval failed
    else:
        extcall RipeToken(a.ripeToken).mint(_recipient, totalRipePayout)

    # refund user any extra payment amount
    refundAmount: uint256 = 0
    if _paymentAmount > paymentAmount:
        refundAmount = min(_paymentAmount - paymentAmount, staticcall IERC20(_paymentAsset).balanceOf(self))
        assert extcall IERC20(_paymentAsset).transfer(_caller, refundAmount, default_return_value=True) # dev: asset transfer failed

    # start next epoch (if applicable)
    if paymentAmount == data.paymentAmountAvailInEpoch and config.shouldAutoRestart:
        newStartBlock: uint256 = block.number + config.restartDelayBlocks
        extcall Ledger(a.ledger).setEpochData(newStartBlock, newStartBlock + config.epochLength, config.amountPerEpoch)

    log RipeBondPurchased(
        recipient=_recipient,
        paymentAsset=_paymentAsset,
        paymentAmount=paymentAmount,
        lockDuration=lockDuration,
        ripePerUnit=ripePerUnit,
        totalRipePayout=totalRipePayout,
        baseRipePayout=baseRipePayout,
        ripeLockBonus=ripeLockBonus,
        ripeBoostBonus=ripeBoostBonus,
        ripeForBadDebt=ripeForBadDebt,
        epochProgress=epochProgress,
        refundAmount=refundAmount,
        caller=_caller,
    )
    return totalRipePayout


@pure
@internal
def _calcRipePerUnit(_ratio: uint256, _minRipePerUnit: uint256, _maxRipePerUnit: uint256) -> uint256:
    if _ratio == 0 or _minRipePerUnit == _maxRipePerUnit:
        return _minRipePerUnit
    valRange: uint256 = _maxRipePerUnit - _minRipePerUnit
    adjustment: uint256 =  _ratio * valRange // HUNDRED_PERCENT
    return _minRipePerUnit + adjustment


# views / helpers

 
@view
@external
def previewRipeBondPayout(_recipient: address, _lockDuration: uint256 = 0, _paymentAmount: uint256 = max_value(uint256)) -> uint256:
    config: PurchaseRipeBondConfig = staticcall MissionControl(addys._getMissionControlAddr()).getPurchaseRipeBondConfig(empty(address))
    if config.maxRipePerUnit == 0 or not config.canBond:
        return 0

    # get epoch data
    ledger: address = addys._getLedgerAddr()
    epochStart: uint256 = 0
    epochEnd: uint256 = 0
    epochStart, epochEnd = staticcall Ledger(ledger).getEpochData()
    didChange: bool = False
    epochStart, epochEnd, didChange = self._getLatestEpochBlockTimes(epochStart, epochEnd, config.epochLength)

    # check availability
    data: RipeBondData = staticcall Ledger(ledger).getRipeBondData()
    paymentAmountAvailInEpoch: uint256 = data.paymentAmountAvailInEpoch
    if didChange:
        paymentAmountAvailInEpoch = config.amountPerEpoch

    paymentAmount: uint256 = min(_paymentAmount, paymentAmountAvailInEpoch)
    if paymentAmount == 0:
        return 0

    # base ripe payout
    epochProgress: uint256 = (block.number - epochStart) * HUNDRED_PERCENT // (epochEnd - epochStart)
    ripePerUnit: uint256 = self._calcRipePerUnit(epochProgress, config.minRipePerUnit, config.maxRipePerUnit)
    units: uint256 = paymentAmount // (10 ** convert(staticcall IERC20Detailed(config.asset).decimals(), uint256))
    baseRipePayout: uint256 = ripePerUnit * units
    if baseRipePayout == 0:
        return 0

    totalRipePayout: uint256 = baseRipePayout

    # bonus for lock duration
    lockDuration: uint256 = min(_lockDuration, config.maxLockDuration)
    if lockDuration >= config.minLockDuration:
        maxLockBonusRatio: uint256 = min(config.maxRipePerUnitLockBonus, 10 * HUNDRED_PERCENT) # extra sanity check 
        lockBonusRatio: uint256 = maxLockBonusRatio * (lockDuration - config.minLockDuration) // (config.maxLockDuration - config.minLockDuration)
        totalRipePayout += baseRipePayout * lockBonusRatio // HUNDRED_PERCENT

    # bonus from bond booster (if applicable)
    bondBooster: address = self.bondBooster
    if bondBooster != empty(address):
        boostRatio: uint256 = min(staticcall BondBooster(bondBooster).getBoostRatio(_recipient, units), 10 * HUNDRED_PERCENT) # extra sanity check 
        totalRipePayout += baseRipePayout * boostRatio // HUNDRED_PERCENT

    return totalRipePayout


@view
@external
def previewNextEpoch() -> (uint256, uint256):
    config: PurchaseRipeBondConfig = staticcall MissionControl(addys._getMissionControlAddr()).getPurchaseRipeBondConfig(empty(address))
    epochStart: uint256 = 0
    epochEnd: uint256 = 0
    epochStart, epochEnd = staticcall Ledger(addys._getLedgerAddr()).getEpochData()
    na: bool = False
    epochStart, epochEnd, na = self._getLatestEpochBlockTimes(epochStart, epochEnd, config.epochLength)
    return epochStart, epochEnd


################
# Bond Booster #
################


@external
def setBondBooster(_bondBooster: address):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    self.bondBooster = _bondBooster
    log BondBoosterSet(bondBooster=_bondBooster)


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


########   #######  ##    ## ########  
##     ## ##     ## ###   ## ##     ## 
##     ## ##     ## ####  ## ##     ## 
########  ##     ## ## ## ## ##     ## 
##     ## ##     ## ##  #### ##     ## 
##     ## ##     ## ##   ### ##     ## 
########   #######  ##    ## ######## 