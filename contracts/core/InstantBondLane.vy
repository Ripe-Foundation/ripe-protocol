#    _____           _              _       ___                 _     
#    \_   \_ __  ___| |_ __ _ _ __ | |_    / __\ ___  _ __   __| |___ 
#     / /\/ '_ \/ __| __/ _` | '_ \| __|  /__\/// _ \| '_ \ / _` / __|
#  /\/ /_ | | | \__ \ || (_| | | | | |_  / \/  \ (_) | | | | (_| \__ \
#  \____/ |_| |_|___/\__\__,_|_| |_|\__| \_____/\___/|_| |_|\__,_|___/
#                                                                   
#     ╔════════════════════════════════════════╗
#     ║  ** Instant Bonds **                   ║
#     ║  Fixed-price direct RIPE purchases     ║
#     ╚════════════════════════════════════════╝
#
#     Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
#     Ripe Foundation (C) 2025

# @version 0.4.3
# pragma optimize codesize

implements: Department

exports: addys.__interface__
exports: deptBasics.__interface__

initializes: addys
initializes: deptBasics[addys := addys]

import contracts.modules.Addys as addys
import contracts.modules.DeptBasics as deptBasics
from interfaces import Department
import interfaces.ConfigStructs as cs

from ethereum.ercs import IERC20
from ethereum.ercs import IERC20Detailed

interface RipeToken:
    def mint(_recipient: address, _amount: uint256) -> bool: nonpayable

interface MissionControl:
    def ripeGovVaultConfig(_asset: address) -> cs.RipeGovVaultConfig: view
    def coreRipeGovVaultId() -> uint256: view

interface Teller:
    def depositFromTrusted(_user: address, _vaultId: uint256, _asset: address, _amount: uint256, _lockDuration: uint256, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable

interface RipeHq:
    def canMintRipe(_addr: address) -> bool: view

interface Ledger:
    def badDebt() -> uint256: view

struct InstantBondConfig:
    canBuyNow: bool
    paymentCapPerEpoch: uint256
    minPaymentAmount: uint256
    mintBudget: uint256
    maxEffectiveRate: uint256
    seedRate: uint256
    uHighBps: uint256
    uLowBps: uint256
    minUpBps: uint256
    maxUpBps: uint256
    minDownBps: uint256
    maxDownBps: uint256
    decayBps: uint256
    maxDecayEpochs: uint256
    maxLockBonus: uint256
    minLockDuration: uint256
    epochLength: uint256

struct InstantBondQuote:
    available: bool
    epoch: uint256
    rate: uint256
    remainingPayment: uint256
    minPaymentAmount: uint256
    budgetRemaining: uint256
    baseRipe: uint256
    bonusRatio: uint256
    bonusRipe: uint256
    actualLock: uint256
    ripeGovVaultId: uint256
    totalRipe: uint256
    canExitEarly: bool
    exitFee: uint256
    isExitFrozen: bool

struct RateTransition:
    controllerRate: uint256
    utilizationBps: uint256
    effectiveAdjustmentBps: uint256
    decaySteps: uint256

struct EpochSnapshot:
    epoch: uint256
    rate: uint256
    paymentCap: uint256
    minPaymentAmount: uint256
    maxLockBonus: uint256
    acceptedPayment: uint256
    weightedLateness: uint256
    timingEligible: bool

struct PayoutData:
    baseRipe: uint256
    bonusRatio: uint256
    bonusRipe: uint256
    actualLock: uint256
    totalRipe: uint256

event EpochInitialized:
    epoch: indexed(uint256)
    rate: uint256
    paymentCap: uint256
    minPaymentAmount: uint256
    maxLockBonus: uint256
    timingEligible: bool

event EpochRolled:
    fromEpoch: indexed(uint256)
    toEpoch: indexed(uint256)
    oldRate: uint256
    newRate: uint256
    newPaymentCap: uint256
    newMinPaymentAmount: uint256
    newMaxLockBonus: uint256
    previousAcceptedPayment: uint256
    previousPaymentCap: uint256
    previousWeightedLateness: uint256
    previousTimingEligible: bool
    utilizationBps: uint256
    effectiveAdjustmentBps: uint256
    decaySteps: uint256
    controllerRate: uint256

event InstantBondPurchased:
    buyer: indexed(address)
    paymentAmount: uint256
    baseRipe: uint256
    bonusRipe: uint256
    bonusRatio: uint256
    actualLock: uint256
    totalRipe: uint256
    epochRate: uint256
    epoch: indexed(uint256)

event InstantBondConfigSet:
    canBuyNow: bool
    paymentCapPerEpoch: uint256
    minPaymentAmount: uint256
    mintBudget: uint256
    maxEffectiveRate: uint256
    seedRate: uint256
    uHighBps: uint256
    uLowBps: uint256
    minUpBps: uint256
    maxUpBps: uint256
    minDownBps: uint256
    maxDownBps: uint256
    decayBps: uint256
    maxDecayEpochs: uint256
    maxLockBonus: uint256
    minLockDuration: uint256
    epochLength: uint256

event InstantBondStarted:
    genesisBlock: uint256
    epochLength: uint256

event InstantBondStopped:
    epochLength: uint256

event PaymentTokenSet:
    token: indexed(address)
    decimals: uint8
    scale: uint256

event CumulativeMintedSet:
    amount: uint256

event RateOverrideInstalled:
    targetRate: uint256

event RateOverrideApplied:
    fromEpoch: indexed(uint256)
    toEpoch: indexed(uint256)
    targetRate: uint256
    controllerRate: uint256

event RateOverrideCancelled:
    targetRate: uint256

event RateOverrideInvalidated:
    targetRate: uint256

# config
bondConfig: public(InstantBondConfig)
rateOverride: public(uint256)

# state
isRunning: public(bool)
epochState: public(EpochSnapshot)

paymentToken: public(address)
paymentDecimals: public(uint8)
paymentScale: public(uint256)
genesisBlock: public(uint256)

# overall
cumulativeMinted: public(uint256)

HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%
MAX_LOCK_BONUS: constant(uint256) = 1000_00 # 1000.00%
MAX_PRICE_STEP_BPS: constant(uint256) = 100_00 # 100.00%
MAX_DECAY_EPOCHS: constant(uint256) = 32
MAX_PAYMENT_DECIMALS: constant(uint8) = 73
MIN_BASE_RATE: constant(uint256) = 10_000


@deploy
def __init__(
    _ripeHq: address,
    _paymentToken: address,
    _config: InstantBondConfig,
):
    addys.__init__(_ripeHq)
    deptBasics.__init__(True, False, True) # starts paused, can mint ripe only

    self._storePaymentToken(_paymentToken)
    assert self._isValidConfig(_config) # dev: invalid config
    self.bondConfig = _config


#################
# Purchase Bond #
#################


@nonreentrant
@external
def buyNow(
    _paymentAmount: uint256,
    _requestedLock: uint256,
    _expectedEpoch: uint256,
    _minRipeOut: uint256,
    _deadlineBlock: uint256,
) -> uint256:
    assert block.number >= self.genesisBlock # dev: before genesis
    assert not deptBasics.isPaused # dev: paused
    assert self.isRunning # dev: not running

    config: InstantBondConfig = self.bondConfig
    assert self._isValidConfig(config) # dev: not configured
    assert config.canBuyNow # dev: disabled
    assert block.number <= _deadlineBlock # dev: expired

    # refresh epoch if necessary
    prev: EpochSnapshot = self.epochState
    snap: EpochSnapshot = empty(EpochSnapshot)
    transition: RateTransition = empty(RateTransition)
    snap, transition = self._getEpochSnapshot(prev, config)
    assert _expectedEpoch == snap.epoch # dev: epoch moved
    self._storeEpochState(prev, snap, transition)

    # check availability - do AFTER epoch refresh
    availAmount: uint256 = snap.paymentCap - snap.acceptedPayment
    assert _paymentAmount >= snap.minPaymentAmount # dev: below minimum payment
    assert _paymentAmount <= availAmount # dev: exceeds available amount

    # calculate payout and enforce mint budget
    a: addys.Addys = addys._getAddys()
    vaultConfig: cs.RipeGovVaultConfig = staticcall MissionControl(a.missionControl).ripeGovVaultConfig(a.ripeToken)
    payout: PayoutData = self._calculatePayout(_paymentAmount, snap.rate, snap.maxLockBonus, _requestedLock, config.minLockDuration, vaultConfig)

    assert payout.totalRipe >= _minRipeOut # dev: slippage
    budgetRemaining: uint256 = config.mintBudget - self.cumulativeMinted
    assert payout.totalRipe <= budgetRemaining # dev: mint budget

    # consume against this epoch before the state-changing external calls below
    self.epochState.acceptedPayment += _paymentAmount
    self.epochState.weightedLateness += _paymentAmount * self._getLatenessBps(block.number)
    self.cumulativeMinted += payout.totalRipe

    # collect payment amount, move to endaoment funds
    endaoFunds: address = addys._getEndaomentFundsAddr()
    paymentToken: address = self.paymentToken
    paymentBalanceBefore: uint256 = staticcall IERC20(paymentToken).balanceOf(endaoFunds)
    assert extcall IERC20(paymentToken).transferFrom(msg.sender, endaoFunds, _paymentAmount, default_return_value=True) # dev: payment failed
    paymentBalanceAfter: uint256 = staticcall IERC20(paymentToken).balanceOf(endaoFunds)
    assert paymentBalanceAfter >= paymentBalanceBefore # dev: payment receipt mismatch
    assert paymentBalanceAfter - paymentBalanceBefore == _paymentAmount # dev: payment receipt mismatch

    # mint ripe to user
    if payout.actualLock == 0:
        assert extcall RipeToken(a.ripeToken).mint(msg.sender, payout.totalRipe) # dev: mint failed
    
    # deposit into core ripe gov vault
    else:
        ripeBalanceBefore: uint256 = staticcall IERC20(a.ripeToken).balanceOf(self)

        # mint
        assert extcall RipeToken(a.ripeToken).mint(self, payout.totalRipe) # dev: mint failed

        # deposit
        coreRipeGovVaultId: uint256 = staticcall MissionControl(a.missionControl).coreRipeGovVaultId()
        assert extcall IERC20(a.ripeToken).approve(a.teller, payout.totalRipe, default_return_value=True) # dev: ripe approval failed
        depositedAmount: uint256 = extcall Teller(a.teller).depositFromTrusted(msg.sender, coreRipeGovVaultId, a.ripeToken, payout.totalRipe, payout.actualLock, a)
        assert extcall IERC20(a.ripeToken).approve(a.teller, 0, default_return_value=True) # dev: ripe approval failed

        # validation
        assert depositedAmount == payout.totalRipe # dev: deposit mismatch
        assert staticcall IERC20(a.ripeToken).balanceOf(self) == ripeBalanceBefore # dev: ripe settlement mismatch

    log InstantBondPurchased(
        buyer=msg.sender,
        paymentAmount=_paymentAmount,
        baseRipe=payout.baseRipe,
        bonusRipe=payout.bonusRipe,
        bonusRatio=payout.bonusRatio,
        actualLock=payout.actualLock,
        totalRipe=payout.totalRipe,
        epochRate=snap.rate,
        epoch=snap.epoch,
    )
    return payout.totalRipe


# calc payout


@view
@internal
def _calculatePayout(
    _paymentAmount: uint256,
    _rate: uint256,
    _maxLockBonus: uint256,
    _requestedLock: uint256,
    _minLockDuration: uint256,
    _vaultConfig: cs.RipeGovVaultConfig,
) -> PayoutData:
    baseRipe: uint256 = _paymentAmount * _rate // self.paymentScale
    minLock: uint256 = max(_vaultConfig.lockTerms.minLockDuration, _minLockDuration)
    maxLock: uint256 = _vaultConfig.lockTerms.maxLockDuration

    # unlocked if they asked for it and the lane has no floor, or there is no live range
    actualLock: uint256 = 0
    if (_requestedLock != 0 or _minLockDuration != 0) and maxLock != 0 and maxLock >= minLock:
        actualLock = min(max(_requestedLock, minLock), maxLock)

    bonusRatio: uint256 = 0
    if actualLock != 0:
        bonusRatio = _maxLockBonus
        if maxLock != minLock:
            bonusRatio = _maxLockBonus * (actualLock - minLock) // (maxLock - minLock)

    bonusRipe: uint256 = baseRipe * bonusRatio // HUNDRED_PERCENT
    return PayoutData(
        baseRipe=baseRipe,
        bonusRatio=bonusRatio,
        bonusRipe=bonusRipe,
        actualLock=actualLock,
        totalRipe=baseRipe + bonusRipe,
    )


# next rate


@pure
@internal
def _nextRate(
    _prev: EpochSnapshot,
    _elapsed: uint256,
    _config: InstantBondConfig,
) -> RateTransition:
    ceiling: uint256 = self._baseRateCeiling(_config.maxEffectiveRate, _config.maxLockBonus)
    rate: uint256 = min(_prev.rate, ceiling)
    utilizationBps: uint256 = 0
    adjustmentBps: uint256 = 0
    decaySteps: uint256 = 0

    # Stored empty epochs have no fill signal; decay the whole gap.
    # A committed buy always records a positive payment, so this is defensive.
    if _prev.acceptedPayment == 0: # pragma: no branch
        decaySteps = min(_elapsed, _config.maxDecayEpochs)
    else:
        utilizationBps = _prev.acceptedPayment * HUNDRED_PERCENT // _prev.paymentCap

        if utilizationBps >= _config.uHighBps:
            strengthBps: uint256 = (utilizationBps - _config.uHighBps) * HUNDRED_PERCENT // (HUNDRED_PERCENT - _config.uHighBps)
            earlinessBps: uint256 = 0
            if _prev.timingEligible:
                earlinessBps = HUNDRED_PERCENT - (_prev.weightedLateness // _prev.acceptedPayment)
            demandBps: uint256 = strengthBps * earlinessBps // HUNDRED_PERCENT
            adjustmentBps = _config.minUpBps + (_config.maxUpBps - _config.minUpBps) * demandBps // HUNDRED_PERCENT
            rate = max(rate * HUNDRED_PERCENT // (HUNDRED_PERCENT + adjustmentBps), MIN_BASE_RATE)

        elif utilizationBps <= _config.uLowBps:
            weaknessBps: uint256 = (_config.uLowBps - utilizationBps) * HUNDRED_PERCENT // _config.uLowBps
            adjustmentBps = _config.minDownBps + (_config.maxDownBps - _config.minDownBps) * weaknessBps // HUNDRED_PERCENT
            rate = min(rate * HUNDRED_PERCENT // (HUNDRED_PERCENT - adjustmentBps), ceiling)

        decaySteps = min(_elapsed - 1, _config.maxDecayEpochs)

    for i: uint256 in range(decaySteps, bound=MAX_DECAY_EPOCHS):
        rate = min(rate * HUNDRED_PERCENT // (HUNDRED_PERCENT - _config.decayBps), ceiling)

    return RateTransition(
        controllerRate=rate,
        utilizationBps=utilizationBps,
        effectiveAdjustmentBps=adjustmentBps,
        decaySteps=decaySteps,
    )


##########
# Epochs #
##########


# epoch snapshot


@view
@external
def getEpochSnapshot() -> EpochSnapshot:
    snap: EpochSnapshot = empty(EpochSnapshot)
    transition: RateTransition = empty(RateTransition)
    snap, transition = self._getEpochSnapshot(self.epochState, self.bondConfig)
    return snap


@view
@internal
def _getEpochSnapshot(_prev: EpochSnapshot, _config: InstantBondConfig) -> (EpochSnapshot, RateTransition):
    if block.number < self.genesisBlock:
        return empty(EpochSnapshot), empty(RateTransition)

    epoch: uint256 = (block.number - self.genesisBlock) // _config.epochLength

    # already committed this epoch
    if _prev.rate != 0 and epoch <= _prev.epoch:
        return _prev, empty(RateTransition)

    # first buy after start
    if _prev.rate == 0:
        onBoundary: bool = (block.number - self.genesisBlock) % _config.epochLength == 0
        return self._openEpoch(epoch, _config.seedRate, _config, onBoundary), empty(RateTransition)

    # later epoch: roll the controller, then optional override
    transition: RateTransition = self._nextRate(_prev, epoch - _prev.epoch, _config)
    rate: uint256 = transition.controllerRate
    overrideRate: uint256 = self.rateOverride
    if overrideRate != 0:
        rate = overrideRate

    return self._openEpoch(epoch, rate, _config, True), transition


# open epoch


@pure
@internal
def _openEpoch(
    _epoch: uint256,
    _rate: uint256,
    _config: InstantBondConfig,
    _timingEligible: bool,
) -> EpochSnapshot:
    return EpochSnapshot(
        epoch=_epoch,
        rate=_rate,
        paymentCap=_config.paymentCapPerEpoch,
        minPaymentAmount=_config.minPaymentAmount,
        maxLockBonus=_config.maxLockBonus,
        acceptedPayment=0,
        weightedLateness=0,
        timingEligible=_timingEligible,
    )


# store state


@internal
def _storeEpochState(_prev: EpochSnapshot, _snap: EpochSnapshot, _transition: RateTransition):

    # already committed this epoch
    if _prev.rate != 0 and _snap.epoch <= _prev.epoch:
        return

    # store the new epoch
    self.epochState = _snap

    # starting over
    if _prev.rate == 0:
        log EpochInitialized(
            epoch=_snap.epoch,
            rate=_snap.rate,
            paymentCap=_snap.paymentCap,
            minPaymentAmount=_snap.minPaymentAmount,
            maxLockBonus=_snap.maxLockBonus,
            timingEligible=_snap.timingEligible,
        )
        return

    # rolling to a new epoch
    overrideRate: uint256 = self.rateOverride
    if overrideRate != 0:
        self.rateOverride = 0
        log RateOverrideApplied(
            fromEpoch=_prev.epoch,
            toEpoch=_snap.epoch,
            targetRate=overrideRate,
            controllerRate=_transition.controllerRate,
        )

    log EpochRolled(
        fromEpoch=_prev.epoch,
        toEpoch=_snap.epoch,
        oldRate=_prev.rate,
        newRate=_snap.rate,
        newPaymentCap=_snap.paymentCap,
        newMinPaymentAmount=_snap.minPaymentAmount,
        newMaxLockBonus=_snap.maxLockBonus,
        previousAcceptedPayment=_prev.acceptedPayment,
        previousPaymentCap=_prev.paymentCap,
        previousWeightedLateness=_prev.weightedLateness,
        previousTimingEligible=_prev.timingEligible,
        utilizationBps=_transition.utilizationBps,
        effectiveAdjustmentBps=_transition.effectiveAdjustmentBps,
        decaySteps=_transition.decaySteps,
        controllerRate=_transition.controllerRate,
    )


# epoch length


@view
@external
def epochLength() -> uint256:
    return self.bondConfig.epochLength


@view
@external
def isValidEpochLength(_epochLength: uint256) -> bool:
    return self._isValidEpochLength(_epochLength)


@pure
@internal
def _isValidEpochLength(_epochLength: uint256) -> bool:
    return _epochLength != 0 and _epochLength <= max_value(uint256) // HUNDRED_PERCENT + 1


# utils


@view
@internal
def _getLatenessBps(_blockNumber: uint256) -> uint256:
    epochLength: uint256 = self.bondConfig.epochLength
    if epochLength == 1:
        return 0
    offset: uint256 = (_blockNumber - self.genesisBlock) % epochLength
    return offset * HUNDRED_PERCENT // (epochLength - 1)


###############
# Core Config #
###############


# start 


@nonreentrant
@external
def start(_genesisBlock: uint256, _epochLength: uint256):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert not self.isRunning # dev: already running
    assert self._isValidEpochLength(_epochLength) # dev: invalid epoch length

    config: InstantBondConfig = self.bondConfig
    config.epochLength = _epochLength
    self.bondConfig = config
    assert self._isValidConfig(config) # dev: not configured

    self.genesisBlock = block.number if _genesisBlock == 0 else _genesisBlock
    self.isRunning = True
    self._resetEpoch()
    log InstantBondStarted(genesisBlock=self.genesisBlock, epochLength=_epochLength)


# stop


@nonreentrant
@external
def stop():
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert self.isRunning # dev: not running
    self.isRunning = False
    self.genesisBlock = 0
    self._resetEpoch()
    log InstantBondStopped(epochLength=self.bondConfig.epochLength)


# set config


@nonreentrant
@external
def setConfig(_newConfig: InstantBondConfig):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert self._isValidConfig(_newConfig) # dev: invalid config

    self.bondConfig = _newConfig
    self._invalidateInstalledOverride()

    log InstantBondConfigSet(
        canBuyNow=_newConfig.canBuyNow,
        paymentCapPerEpoch=_newConfig.paymentCapPerEpoch,
        minPaymentAmount=_newConfig.minPaymentAmount,
        mintBudget=_newConfig.mintBudget,
        maxEffectiveRate=_newConfig.maxEffectiveRate,
        seedRate=_newConfig.seedRate,
        uHighBps=_newConfig.uHighBps,
        uLowBps=_newConfig.uLowBps,
        minUpBps=_newConfig.minUpBps,
        maxUpBps=_newConfig.maxUpBps,
        minDownBps=_newConfig.minDownBps,
        maxDownBps=_newConfig.maxDownBps,
        decayBps=_newConfig.decayBps,
        maxDecayEpochs=_newConfig.maxDecayEpochs,
        maxLockBonus=_newConfig.maxLockBonus,
        minLockDuration=_newConfig.minLockDuration,
        epochLength=_newConfig.epochLength,
    )


# utils


@internal
def _resetEpoch():
    self.epochState = empty(EpochSnapshot)
    self._invalidateInstalledOverride()


@internal
def _invalidateInstalledOverride():
    overrideRate: uint256 = self.rateOverride
    if overrideRate != 0:
        self.rateOverride = 0
        log RateOverrideInvalidated(targetRate=overrideRate)


#################
# Rate Override #
#################


# set rate override


@nonreentrant
@external
def setRateOverride(_targetRate: uint256):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert self._isValidRateOverride(_targetRate) # dev: invalid rate override
    self.rateOverride = _targetRate
    log RateOverrideInstalled(targetRate=_targetRate)


# cancel rate override


@view
@external
def canCancelRateOverride() -> bool:
    return self.rateOverride != 0


@nonreentrant
@external
def cancelRateOverride():
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    targetRate: uint256 = self.rateOverride
    assert targetRate != 0 # dev: no override
    self.rateOverride = 0
    log RateOverrideCancelled(targetRate=targetRate)


# validate rate override


@view
@external
def isValidRateOverride(_targetRate: uint256) -> bool:
    return self._isValidRateOverride(_targetRate)


@view
@internal
def _isValidRateOverride(_targetRate: uint256) -> bool:
    if not self.isRunning or self.epochState.rate == 0:
        return False
    config: InstantBondConfig = self.bondConfig
    ceiling: uint256 = self._baseRateCeiling(config.maxEffectiveRate, config.maxLockBonus)
    return _targetRate >= MIN_BASE_RATE and _targetRate <= ceiling


#################
# Payment Token #
#################


# set payment token


@nonreentrant
@external
def setPaymentToken(_token: address):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert not self.isRunning # dev: running
    self._storePaymentToken(_token)
    log PaymentTokenSet(token=_token, decimals=self.paymentDecimals, scale=self.paymentScale)


@internal
def _storePaymentToken(_token: address):
    assert self._isValidPaymentToken(_token) # dev: invalid payment token
    paymentDecimals: uint8 = staticcall IERC20Detailed(_token).decimals()
    self.paymentToken = _token
    self.paymentDecimals = paymentDecimals
    self.paymentScale = 10 ** convert(paymentDecimals, uint256)


# validation


@view
@external
def isValidPaymentToken(_token: address) -> bool:
    return not self.isRunning and self._isValidPaymentToken(_token)


@view
@internal
def _isValidPaymentToken(_token: address) -> bool:
    if _token == empty(address) or not _token.is_contract:
        return False
    if _token == addys._getRipeToken():
        return False
    paymentDecimals: uint8 = staticcall IERC20Detailed(_token).decimals()
    return paymentDecimals <= MAX_PAYMENT_DECIMALS


###############
# Mint Budget #
###############


@nonreentrant
@external
def setCumulativeMinted(_amount: uint256):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert self._isValidCumulativeMinted(_amount) # dev: exceeds mint budget
    self.cumulativeMinted = _amount
    log CumulativeMintedSet(amount=_amount)


# validation


@view
@external
def isValidCumulativeMinted(_amount: uint256) -> bool:
    return self._isValidCumulativeMinted(_amount)


@view
@internal
def _isValidCumulativeMinted(_amount: uint256) -> bool:
    return _amount <= self.bondConfig.mintBudget


##############
# Validation #
##############


@view
@external
def isValidConfig(_config: InstantBondConfig) -> bool:
    return self._isValidConfig(_config)


@view
@internal
def _isValidConfig(_config: InstantBondConfig) -> bool:
    # utilization bands must be 0 < low < high < 100%
    if _config.uLowBps == 0 or _config.uLowBps >= _config.uHighBps:
        return False
    if _config.uHighBps >= HUNDRED_PERCENT:
        return False

    # up/down steps must be positive and min <= max
    if _config.minUpBps == 0 or _config.minUpBps > _config.maxUpBps:
        return False
    if _config.minDownBps == 0 or _config.minDownBps > _config.maxDownBps:
        return False

    # a single up step cannot exceed the hard price-step cap
    if _config.maxUpBps > MAX_PRICE_STEP_BPS:
        return False

    # decay must be a real fraction (0% does nothing; 100%+ divides by zero)
    if _config.decayBps == 0 or _config.decayBps >= HUNDRED_PERCENT:
        return False

    # fill-based down cannot exceed idle decay, and cannot reach min up (no oscillation)
    if _config.maxDownBps > _config.decayBps or _config.maxDownBps >= _config.minUpBps:
        return False

    # one min-up then one decay cannot net higher (no ratchet)
    if (HUNDRED_PERCENT + _config.minUpBps) * (HUNDRED_PERCENT - _config.decayBps) < HUNDRED_PERCENT * HUNDRED_PERCENT:
        return False

    # idle decay needs a non-zero, bounded number of steps
    if _config.maxDecayEpochs == 0 or _config.maxDecayEpochs > MAX_DECAY_EPOCHS:
        return False

    # effective-rate ceiling must be real and safe to scale by 100%
    if _config.maxEffectiveRate == 0 or _config.maxEffectiveRate > max_value(uint256) // HUNDRED_PERCENT:
        return False

    # epoch cap is at least one token unit and safe to scale by 100%
    paymentScale: uint256 = self.paymentScale
    if _config.paymentCapPerEpoch < paymentScale or _config.paymentCapPerEpoch > max_value(uint256) // HUNDRED_PERCENT:
        return False

    # min payment is at least one unit and cannot exceed the cap
    if _config.minPaymentAmount < paymentScale or _config.minPaymentAmount > _config.paymentCapPerEpoch:
        return False

    # payment × rate at the cap cannot overflow
    if _config.maxEffectiveRate > max_value(uint256) // _config.paymentCapPerEpoch:
        return False

    # lock bonus stays inside the hard cap
    if _config.maxLockBonus > MAX_LOCK_BONUS:
        return False

    # implied max base rate must still be a legal rate
    baseRateCeiling: uint256 = self._baseRateCeiling(_config.maxEffectiveRate, _config.maxLockBonus)
    if baseRateCeiling < MIN_BASE_RATE:
        return False

    # full-cap bonus ripe cannot overflow
    maxBaseRipe: uint256 = _config.paymentCapPerEpoch * baseRateCeiling // paymentScale
    if _config.maxLockBonus != 0 and maxBaseRipe > max_value(uint256) // _config.maxLockBonus:
        return False

    # seed must sit in [min base rate, implied ceiling]
    if _config.seedRate < MIN_BASE_RATE or _config.seedRate > baseRateCeiling:
        return False

    # cannot cut the mint budget below RIPE already issued
    if _config.mintBudget < self.cumulativeMinted:
        return False

    # epoch length must be a valid clock
    if not self._isValidEpochLength(_config.epochLength):
        return False

    # setConfig cannot change the live clock; only start() can
    installedLength: uint256 = self.bondConfig.epochLength
    if installedLength != 0 and _config.epochLength != installedLength:
        return False

    return True


# base rate ceiling


@pure
@internal
def _baseRateCeiling(_maxEffectiveRate: uint256, _maxLockBonus: uint256) -> uint256:
    return _maxEffectiveRate * HUNDRED_PERCENT // (HUNDRED_PERCENT + _maxLockBonus)


###########
# Preview #
###########


@view
@external
def previewBuyNow(_paymentAmount: uint256, _requestedLock: uint256) -> InstantBondQuote:
    quote: InstantBondQuote = empty(InstantBondQuote)
    if block.number < self.genesisBlock:
        return quote

    config: InstantBondConfig = self.bondConfig
    if not self._isValidConfig(config):
        return quote

    # market
    snap: EpochSnapshot = empty(EpochSnapshot)
    transition: RateTransition = empty(RateTransition)
    snap, transition = self._getEpochSnapshot(self.epochState, config)
    remainingPayment: uint256 = snap.paymentCap - snap.acceptedPayment
    budgetRemaining: uint256 = config.mintBudget - self.cumulativeMinted

    quote.epoch = snap.epoch
    quote.rate = snap.rate
    quote.remainingPayment = remainingPayment
    quote.minPaymentAmount = snap.minPaymentAmount
    quote.budgetRemaining = budgetRemaining

    if _paymentAmount < snap.minPaymentAmount or _paymentAmount > remainingPayment:
        return quote

    # payout
    a: addys.Addys = addys._getAddys()
    vaultConfig: cs.RipeGovVaultConfig = staticcall MissionControl(a.missionControl).ripeGovVaultConfig(a.ripeToken)
    payout: PayoutData = self._calculatePayout(_paymentAmount, snap.rate, snap.maxLockBonus, _requestedLock, config.minLockDuration, vaultConfig)

    quote.baseRipe = payout.baseRipe
    quote.bonusRatio = payout.bonusRatio
    quote.bonusRipe = payout.bonusRipe
    quote.actualLock = payout.actualLock
    quote.totalRipe = payout.totalRipe

    # lock terms (disclosure only)
    if payout.actualLock != 0:
        quote.ripeGovVaultId = staticcall MissionControl(a.missionControl).coreRipeGovVaultId()
        quote.canExitEarly = vaultConfig.lockTerms.canExit
        quote.exitFee = vaultConfig.lockTerms.exitFee
        if vaultConfig.shouldFreezeWhenBadDebt:
            quote.isExitFrozen = staticcall Ledger(a.ledger).badDebt() != 0

    # same gates as buyNow, minus deadline / expectedEpoch / slippage
    if deptBasics.isPaused or not self.isRunning or not config.canBuyNow:
        return quote
    if payout.totalRipe > budgetRemaining:
        return quote
    if not staticcall RipeHq(addys._getRipeHq()).canMintRipe(self):
        return quote

    quote.available = True
    return quote

