#    ___  ________   ________  _________  ________  ________   _________        ________  ________  ________   ________  ________      
#   |\  \|\   ___  \|\   ____\|\___   ___\\   __  \|\   ___  \|\___   ___\     |\   __  \|\   __  \|\   ___  \|\   ___ \|\   ____\     
#   \ \  \ \  \\ \  \ \  \___|\|___ \  \_\ \  \|\  \ \  \\ \  \|___ \  \_|     \ \  \|\ /\ \  \|\  \ \  \\ \  \ \  \_|\ \ \  \___|_    
#    \ \  \ \  \\ \  \ \_____  \   \ \  \ \ \   __  \ \  \\ \  \   \ \  \       \ \   __  \ \  \\\  \ \  \\ \  \ \  \ \\ \ \_____  \   
#     \ \  \ \  \\ \  \|____|\  \   \ \  \ \ \  \ \  \ \  \\ \  \   \ \  \       \ \  \|\  \ \  \\\  \ \  \\ \  \ \  \_\\ \|____|\  \  
#      \ \__\ \__\\ \__\____\_\  \   \ \__\ \ \__\ \__\ \__\\ \__\   \ \__\       \ \_______\ \_______\ \__\\ \__\ \_______\____\_\  \ 
#       \|__|\|__| \|__|\_________\   \|__|  \|__|\|__|\|__| \|__|    \|__|        \|_______|\|_______|\|__| \|__|\|_______|\_________\
#                      \|_________|                                                                                        \|_________|
#                                                                                                                                   
#     ╔════════════════════════════════════════╗
#     ║  ** Instant Bonds **                   ║
#     ║  Fixed-price direct RIPE purchases     ║
#     ╚════════════════════════════════════════╝
#
#     Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
#     Ripe Foundation (C) 2025

# @version 0.4.3

implements: Department

exports: addys.__interface__
exports: (
    deptBasics.canMintGreen,
    deptBasics.canMintRipe,
)

initializes: addys
initializes: deptBasics[addys := addys]

import contracts.modules.Addys as addys
import contracts.modules.DeptBasics as deptBasics
from interfaces import Department
import interfaces.ConfigStructs as cs

from ethereum.ercs import IERC20
from ethereum.ercs import IERC20Detailed

interface MissionControl:
    def ripeGovVaultConfig(_asset: address) -> cs.RipeGovVaultConfig: view
    def coreRipeGovVaultId() -> uint256: view

interface Teller:
    def depositFromTrusted(_user: address, _vaultId: uint256, _asset: address, _amount: uint256, _lockDuration: uint256, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable

interface InstantBondClaims:
    def getRipeHq() -> address: view
    def isPaused() -> bool: view
    def remainingAllocationBudget() -> uint256: view
    def createVestingPosition(_beneficiary: address, _ripePayout: uint256, _vestingLength: uint256) -> uint256: nonpayable

interface RipeToken:
    def mint(_recipient: address, _amount: uint256) -> bool: nonpayable
    def ripeHq() -> address: view
    def isPaused() -> bool: view
    def blacklisted(_addr: address) -> bool: view

interface RipeHq:
    def getAddr(_regId: uint256) -> address: view
    def canMintRipe(_addr: address) -> bool: view

struct InstantBondConfig:
    paymentCapPerEpoch: uint256
    minPaymentAmount: uint256
    maxAllInPayoutRate: uint256
    seedBasePayoutRate: uint256
    uHighBps: uint256
    uLowBps: uint256
    minUpBps: uint256
    maxUpBps: uint256
    minDownBps: uint256
    maxDownBps: uint256
    decayBps: uint256
    maxDecayEpochs: uint256
    maxVestingBonus: uint256
    minVestingLength: uint256
    maxVestingLength: uint256
    epochLength: uint256

struct InstantBondQuote:
    available: bool
    epoch: uint256
    controllerBasePayoutRate: uint256
    basePayoutRate: uint256
    rateSource: uint256
    remainingPayment: uint256
    minPaymentAmount: uint256
    budgetRemaining: uint256
    baseRipe: uint256
    bonusRatio: uint256
    bonusRipe: uint256
    vestingLength: uint256
    creationBlock: uint256
    maturityBlock: uint256
    totalRipe: uint256

struct RateTransition:
    controllerBasePayoutRate: uint256
    utilizationBps: uint256
    effectiveAdjustmentBps: uint256
    decaySteps: uint256

struct EpochSnapshot:
    epoch: uint256
    controllerBasePayoutRate: uint256
    basePayoutRate: uint256
    rateSource: uint256
    paymentCap: uint256
    minPaymentAmount: uint256
    maxVestingBonus: uint256
    minVestingLength: uint256
    maxVestingLength: uint256
    acceptedPayment: uint256
    weightedLateness: uint256
    timingEligible: bool

struct PayoutData:
    baseRipe: uint256
    bonusRatio: uint256
    bonusRipe: uint256
    vestingLength: uint256
    totalRipe: uint256

event EpochInitialized:
    epoch: indexed(uint256)
    controllerBasePayoutRate: uint256
    basePayoutRate: uint256
    rateSource: uint256
    paymentCap: uint256
    minPaymentAmount: uint256
    maxVestingBonus: uint256
    minVestingLength: uint256
    maxVestingLength: uint256
    timingEligible: bool

event EpochRolled:
    fromEpoch: indexed(uint256)
    toEpoch: indexed(uint256)
    oldBasePayoutRate: uint256
    controllerBasePayoutRate: uint256
    newBasePayoutRate: uint256
    rateSource: uint256
    newPaymentCap: uint256
    newMinPaymentAmount: uint256
    newMaxVestingBonus: uint256
    newMinVestingLength: uint256
    newMaxVestingLength: uint256
    previousAcceptedPayment: uint256
    previousPaymentCap: uint256
    previousWeightedLateness: uint256
    previousTimingEligible: bool
    utilizationBps: uint256
    effectiveAdjustmentBps: uint256
    decaySteps: uint256

event InstantBondPurchased:
    buyer: indexed(address)
    positionIndex: indexed(uint256)
    paymentAmount: uint256
    baseRipe: uint256
    bonusRipe: uint256
    bonusRatio: uint256
    vestingLength: uint256
    creationBlock: uint256
    maturityBlock: uint256
    totalRipe: uint256
    controllerBasePayoutRate: uint256
    basePayoutRate: uint256
    rateSource: uint256
    epoch: indexed(uint256)

event InstantBondConfigSet:
    paymentCapPerEpoch: uint256
    minPaymentAmount: uint256
    maxAllInPayoutRate: uint256
    seedBasePayoutRate: uint256
    uHighBps: uint256
    uLowBps: uint256
    minUpBps: uint256
    maxUpBps: uint256
    minDownBps: uint256
    maxDownBps: uint256
    decayBps: uint256
    maxDecayEpochs: uint256
    maxVestingBonus: uint256
    minVestingLength: uint256
    maxVestingLength: uint256
    epochLength: uint256

event CanBuyNowSet:
    canBuyNow: bool

event InstantBondStarted:
    genesisBlock: uint256
    epochLength: uint256

event InstantBondStopped:
    epochLength: uint256

event PaymentTokenSet:
    token: indexed(address)
    decimals: uint8
    scale: uint256

event RateOverrideInstalled:
    targetEpoch: indexed(uint256)
    targetBasePayoutRate: uint256

event RateOverrideApplied:
    fromEpoch: indexed(uint256)
    toEpoch: indexed(uint256)
    targetBasePayoutRate: uint256
    controllerBasePayoutRate: uint256

event RateOverrideMissed:
    targetEpoch: indexed(uint256)
    committedEpoch: indexed(uint256)
    targetBasePayoutRate: uint256
    controllerBasePayoutRate: uint256

event RateOverrideCancelled:
    targetEpoch: indexed(uint256)
    targetBasePayoutRate: uint256

event RateOverrideInvalidated:
    targetEpoch: indexed(uint256)
    targetBasePayoutRate: uint256

# config
bondConfig: public(InstantBondConfig)
overrideTargetBasePayoutRate: public(uint256)
overrideTargetEpoch: public(uint256)
canBuyNow: public(bool)

# state
isRunning: public(bool)
epochState: public(EpochSnapshot)

paymentToken: public(address)
paymentDecimals: public(uint8)
paymentScale: public(uint256)
genesisBlock: public(uint256)

HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%
MAX_VESTING_BONUS: constant(uint256) = 1000_00 # 1000.00%
MAX_VESTING_LENGTH: public(constant(uint256)) = 7_884_000
MAX_PRICE_STEP_BPS: constant(uint256) = 100_00 # 100.00%
MAX_DECAY_EPOCHS: constant(uint256) = 32
MAX_PAYMENT_DECIMALS: constant(uint8) = 73
MIN_BASE_PAYOUT_RATE: constant(uint256) = 10_000
RATE_SOURCE_SEED: public(constant(uint256)) = 1
RATE_SOURCE_CONTROLLER: public(constant(uint256)) = 2
RATE_SOURCE_OVERRIDE: public(constant(uint256)) = 3
RIPE_TOKEN_ID: constant(uint256) = 3
INSTANT_BOND_CLAIMS_ID: constant(uint256) = 27


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


#######################
# Department Controls #
#######################


@nonreentrant
@external
def pause(_shouldPause: bool):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert _shouldPause != deptBasics.isPaused # dev: no change
    deptBasics.isPaused = _shouldPause
    if _shouldPause:
        self._invalidateInstalledOverride()
    log deptBasics.DepartmentPauseModified(isPaused=_shouldPause)


@nonreentrant
@external
def recoverFunds(_recipient: address, _asset: address):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    deptBasics._recoverFunds(_recipient, _asset)


@nonreentrant
@external
def recoverFundsMany(_recipient: address, _assets: DynArray[address, 20]):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    for asset: address in _assets:
        deptBasics._recoverFunds(_recipient, asset)


@view
@external
def isPaused() -> bool:
    return deptBasics.isPaused


#################
# Purchase Bond #
#################


@nonreentrant
@external
def buyNow(
    _paymentAmount: uint256,
    _requestedVestingLength: uint256,
    _expectedVestingLength: uint256,
    _expectedEpoch: uint256,
    _minRipeOut: uint256,
    _deadlineBlock: uint256,
) -> uint256:
    assert block.number >= self.genesisBlock # dev: before genesis
    assert not deptBasics.isPaused # dev: paused
    assert self.isRunning # dev: not running

    config: InstantBondConfig = self.bondConfig
    assert self._isValidConfig(config) # dev: not configured
    assert self.canBuyNow # dev: disabled
    assert block.number <= _deadlineBlock # dev: expired
    assert self._isPurchaseReady() # dev: mint not ready

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

    # calculate payout and enforce allocation budget
    payout: PayoutData = self._calculatePayout(
        _paymentAmount,
        snap.basePayoutRate,
        snap.maxVestingBonus,
        _requestedVestingLength,
        snap.minVestingLength,
        snap.maxVestingLength,
    )
    assert payout.vestingLength == _expectedVestingLength # dev: vesting length moved
    assert self._isWithinMaxAllInPayoutRate(_paymentAmount, payout.totalRipe, config.maxAllInPayoutRate) # dev: all-in payout rate ceiling

    assert payout.totalRipe >= _minRipeOut # dev: slippage
    claims: address = self._getClaimsAddr()
    budgetRemaining: uint256 = staticcall InstantBondClaims(claims).remainingAllocationBudget()
    assert payout.totalRipe <= budgetRemaining # dev: allocation budget

    # consume against this epoch before the state-changing external calls below
    self.epochState.acceptedPayment += _paymentAmount
    self.epochState.weightedLateness += _paymentAmount * self._getLatenessBps(block.number)

    # collect payment amount, move to endaoment funds
    endaoFunds: address = addys._getEndaomentFundsAddr()
    paymentToken: address = self.paymentToken
    paymentBalanceBefore: uint256 = staticcall IERC20(paymentToken).balanceOf(endaoFunds)
    assert extcall IERC20(paymentToken).transferFrom(msg.sender, endaoFunds, _paymentAmount, default_return_value=True) # dev: payment failed
    paymentBalanceAfter: uint256 = staticcall IERC20(paymentToken).balanceOf(endaoFunds)
    assert paymentBalanceAfter >= paymentBalanceBefore # dev: payment receipt mismatch
    assert paymentBalanceAfter - paymentBalanceBefore == _paymentAmount # dev: payment receipt mismatch

    # record one persistent vesting position; no ripe is minted at purchase
    positionIndex: uint256 = extcall InstantBondClaims(claims).createVestingPosition(msg.sender, payout.totalRipe, payout.vestingLength)
    assert positionIndex != 0 # dev: invalid position

    log InstantBondPurchased(
        buyer=msg.sender,
        positionIndex=positionIndex,
        paymentAmount=_paymentAmount,
        baseRipe=payout.baseRipe,
        bonusRipe=payout.bonusRipe,
        bonusRatio=payout.bonusRatio,
        vestingLength=payout.vestingLength,
        creationBlock=block.number,
        maturityBlock=block.number + payout.vestingLength,
        totalRipe=payout.totalRipe,
        controllerBasePayoutRate=snap.controllerBasePayoutRate,
        basePayoutRate=snap.basePayoutRate,
        rateSource=snap.rateSource,
        epoch=snap.epoch,
    )
    return payout.totalRipe


# calc payout


@view
@internal
def _calculatePayout(
    _paymentAmount: uint256,
    _basePayoutRate: uint256,
    _maxVestingBonus: uint256,
    _requestedVestingLength: uint256,
    _minVestingLength: uint256,
    _maxVestingLength: uint256,
) -> PayoutData:
    baseRipe: uint256 = _paymentAmount * _basePayoutRate // self.paymentScale
    vestingLength: uint256 = _minVestingLength
    if _requestedVestingLength != 0:
        vestingLength = min(max(_requestedVestingLength, _minVestingLength), _maxVestingLength)

    bonusRatio: uint256 = _maxVestingBonus
    if _maxVestingLength != _minVestingLength:
        bonusRatio = _maxVestingBonus * (vestingLength - _minVestingLength) // (_maxVestingLength - _minVestingLength)

    bonusRipe: uint256 = baseRipe * bonusRatio // HUNDRED_PERCENT
    return PayoutData(
        baseRipe=baseRipe,
        bonusRatio=bonusRatio,
        bonusRipe=bonusRipe,
        vestingLength=vestingLength,
        totalRipe=baseRipe + bonusRipe,
    )


@view
@internal
def _isWithinMaxAllInPayoutRate(_paymentAmount: uint256, _totalRipe: uint256, _maxAllInPayoutRate: uint256) -> bool:
    return _totalRipe <= _paymentAmount * _maxAllInPayoutRate // self.paymentScale


####################
# Claim Settlement #
####################


@nonreentrant
@external
def settleVestedRipe(
    _beneficiary: address,
    _amount: uint256,
    _autoDeposit: bool,
    _lockDuration: uint256,
) -> bool:
    assert self._isClaimsSettlementCompatible(msg.sender) # dev: invalid claims
    assert _beneficiary != empty(address) and _amount != 0 # dev: invalid settlement

    if _autoDeposit:
        assert _lockDuration != 0 # dev: invalid lock duration
    else:
        assert _lockDuration == 0 # dev: invalid lock duration

    ripeHq: address = addys._getRipeHq()
    ripeToken: address = self._getRipeTokenAddr()
    assert ripeToken != empty(address) and ripeToken.is_contract # dev: invalid ripe token
    assert staticcall RipeToken(ripeToken).ripeHq() == ripeHq # dev: invalid token hq
    assert not staticcall RipeToken(ripeToken).isPaused() # dev: ripe token paused
    assert not staticcall RipeToken(ripeToken).blacklisted(_beneficiary) # dev: blacklisted

    if not _autoDeposit:
        balanceBefore: uint256 = staticcall IERC20(ripeToken).balanceOf(_beneficiary)
        assert extcall RipeToken(ripeToken).mint(_beneficiary, _amount) # dev: mint failed
        balanceAfter: uint256 = staticcall IERC20(ripeToken).balanceOf(_beneficiary)
        assert balanceAfter >= balanceBefore # dev: ripe receipt mismatch
        assert balanceAfter - balanceBefore == _amount # dev: ripe receipt mismatch

    else:
        a: addys.Addys = addys._getAddys()
        coreRipeGovVaultId: uint256 = staticcall MissionControl(a.missionControl).coreRipeGovVaultId()
        assert coreRipeGovVaultId != 0 # dev: invalid ripe gov vault

        vaultConfig: cs.RipeGovVaultConfig = staticcall MissionControl(a.missionControl).ripeGovVaultConfig(ripeToken)
        minLockDuration: uint256 = vaultConfig.lockTerms.minLockDuration
        maxLockDuration: uint256 = vaultConfig.lockTerms.maxLockDuration
        assert maxLockDuration != 0 and maxLockDuration >= minLockDuration # dev: no lock terms
        assert _lockDuration >= minLockDuration and _lockDuration <= maxLockDuration # dev: invalid lock duration

        ripeBalanceBefore: uint256 = staticcall IERC20(ripeToken).balanceOf(self)
        assert extcall RipeToken(ripeToken).mint(self, _amount) # dev: mint failed
        ripeBalanceAfter: uint256 = staticcall IERC20(ripeToken).balanceOf(self)
        assert ripeBalanceAfter >= ripeBalanceBefore # dev: ripe receipt mismatch
        assert ripeBalanceAfter - ripeBalanceBefore == _amount # dev: ripe receipt mismatch

        assert extcall IERC20(ripeToken).approve(a.teller, _amount, default_return_value=True) # dev: ripe approval failed
        depositedAmount: uint256 = extcall Teller(a.teller).depositFromTrusted(_beneficiary, coreRipeGovVaultId, ripeToken, _amount, _lockDuration, a)
        assert depositedAmount == _amount # dev: deposit mismatch
        assert extcall IERC20(ripeToken).approve(a.teller, 0, default_return_value=True) # dev: ripe approval failed
        assert staticcall IERC20(ripeToken).balanceOf(self) == ripeBalanceBefore # dev: ripe settlement mismatch

    return True


@view
@internal
def _isPurchaseReady() -> bool:
    endaoFunds: address = addys._getEndaomentFundsAddr()
    if endaoFunds == empty(address) or not endaoFunds.is_contract:
        return False

    claims: address = self._getClaimsAddr()
    if claims == empty(address) or not claims.is_contract:
        return False
    if staticcall InstantBondClaims(claims).isPaused():
        return False
    if not self._isClaimsSettlementCompatible(claims):
        return False

    ripeHq: address = addys._getRipeHq()
    ripeToken: address = self._getRipeTokenAddr()
    if ripeToken == empty(address) or not ripeToken.is_contract:
        return False
    if staticcall RipeToken(ripeToken).ripeHq() != ripeHq:
        return False
    if staticcall RipeToken(ripeToken).isPaused():
        return False
    return True


@view
@external
def getInstantBondClaimsAddr() -> address:
    return self._getClaimsAddr()


@view
@external
def isClaimsSettlementCompatible(_claims: address) -> bool:
    return self._isClaimsSettlementCompatible(_claims)


@view
@internal
def _isClaimsSettlementCompatible(_claims: address) -> bool:
    if addys._getInstantBondLaneAddr() != self:
        return False
    if _claims == empty(address) or not _claims.is_contract:
        return False
    if _claims != self._getClaimsAddr():
        return False

    ripeHq: address = addys._getRipeHq()
    if staticcall InstantBondClaims(_claims).getRipeHq() != ripeHq:
        return False
    return staticcall RipeHq(ripeHq).canMintRipe(self)


@view
@internal
def _getClaimsAddr() -> address:
    return staticcall RipeHq(addys._getRipeHq()).getAddr(INSTANT_BOND_CLAIMS_ID)


@view
@internal
def _getRipeTokenAddr() -> address:
    return staticcall RipeHq(addys._getRipeHq()).getAddr(RIPE_TOKEN_ID)


# next rate


@pure
@internal
def _nextRate(
    _prev: EpochSnapshot,
    _elapsed: uint256,
    _config: InstantBondConfig,
) -> RateTransition:
    ceiling: uint256 = self._basePayoutRateCeiling(_config.maxAllInPayoutRate, _config.maxVestingBonus)
    basePayoutRate: uint256 = min(_prev.basePayoutRate, ceiling)
    utilizationBps: uint256 = 0
    adjustmentBps: uint256 = 0
    decaySteps: uint256 = 0

    # stored empty epochs have no fill signal; decay the whole gap.
    # a committed buy always records a positive payment, so this is defensive.
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
            basePayoutRate = max(basePayoutRate * HUNDRED_PERCENT // (HUNDRED_PERCENT + adjustmentBps), MIN_BASE_PAYOUT_RATE)

        elif utilizationBps <= _config.uLowBps:
            weaknessBps: uint256 = (_config.uLowBps - utilizationBps) * HUNDRED_PERCENT // _config.uLowBps
            adjustmentBps = _config.minDownBps + (_config.maxDownBps - _config.minDownBps) * weaknessBps // HUNDRED_PERCENT
            basePayoutRate = min(basePayoutRate * HUNDRED_PERCENT // (HUNDRED_PERCENT - adjustmentBps), ceiling)

        decaySteps = min(_elapsed - 1, _config.maxDecayEpochs)

    for i: uint256 in range(decaySteps, bound=MAX_DECAY_EPOCHS):
        basePayoutRate = min(basePayoutRate * HUNDRED_PERCENT // (HUNDRED_PERCENT - _config.decayBps), ceiling)

    return RateTransition(
        controllerBasePayoutRate=basePayoutRate,
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
    if not self.isRunning:
        return empty(EpochSnapshot)
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
    if _prev.basePayoutRate != 0 and epoch <= _prev.epoch:
        return _prev, empty(RateTransition)

    # first buy after start
    if _prev.basePayoutRate == 0:
        onBoundary: bool = (block.number - self.genesisBlock) % _config.epochLength == 0
        firstTransition: RateTransition = empty(RateTransition)
        firstTransition.controllerBasePayoutRate = _config.seedBasePayoutRate
        firstBasePayoutRate: uint256 = _config.seedBasePayoutRate
        rateSource: uint256 = RATE_SOURCE_SEED
        if self.overrideTargetBasePayoutRate != 0 and self.overrideTargetEpoch == epoch:
            firstBasePayoutRate = self.overrideTargetBasePayoutRate
            rateSource = RATE_SOURCE_OVERRIDE
        return self._openEpoch(
            epoch,
            firstTransition.controllerBasePayoutRate,
            firstBasePayoutRate,
            rateSource,
            _config,
            onBoundary,
        ), firstTransition

    # later epoch: roll the controller, then apply only an exact-epoch override
    transition: RateTransition = self._nextRate(_prev, epoch - _prev.epoch, _config)
    basePayoutRate: uint256 = transition.controllerBasePayoutRate
    rateSource: uint256 = RATE_SOURCE_CONTROLLER
    if self.overrideTargetBasePayoutRate != 0 and self.overrideTargetEpoch == epoch:
        basePayoutRate = self.overrideTargetBasePayoutRate
        rateSource = RATE_SOURCE_OVERRIDE

    return self._openEpoch(
        epoch,
        transition.controllerBasePayoutRate,
        basePayoutRate,
        rateSource,
        _config,
        True,
    ), transition


# open epoch


@pure
@internal
def _openEpoch(
    _epoch: uint256,
    _controllerBasePayoutRate: uint256,
    _basePayoutRate: uint256,
    _rateSource: uint256,
    _config: InstantBondConfig,
    _timingEligible: bool,
) -> EpochSnapshot:
    return EpochSnapshot(
        epoch=_epoch,
        controllerBasePayoutRate=_controllerBasePayoutRate,
        basePayoutRate=_basePayoutRate,
        rateSource=_rateSource,
        paymentCap=_config.paymentCapPerEpoch,
        minPaymentAmount=_config.minPaymentAmount,
        maxVestingBonus=_config.maxVestingBonus,
        minVestingLength=_config.minVestingLength,
        maxVestingLength=_config.maxVestingLength,
        acceptedPayment=0,
        weightedLateness=0,
        timingEligible=_timingEligible,
    )


# store state


@internal
def _storeEpochState(_prev: EpochSnapshot, _snap: EpochSnapshot, _transition: RateTransition):

    # already committed this epoch
    if _prev.basePayoutRate != 0 and _snap.epoch <= _prev.epoch:
        return

    # store the new epoch
    self.epochState = _snap

    # consume only an exact target, or clear an override whose target was missed
    overrideTargetBasePayoutRate: uint256 = self.overrideTargetBasePayoutRate
    if overrideTargetBasePayoutRate != 0:
        targetEpoch: uint256 = self.overrideTargetEpoch
        if targetEpoch <= _snap.epoch:
            self.overrideTargetBasePayoutRate = 0
            self.overrideTargetEpoch = 0
            if targetEpoch == _snap.epoch:
                log RateOverrideApplied(
                    fromEpoch=_prev.epoch,
                    toEpoch=_snap.epoch,
                    targetBasePayoutRate=overrideTargetBasePayoutRate,
                    controllerBasePayoutRate=_snap.controllerBasePayoutRate,
                )
            else:
                log RateOverrideMissed(
                    targetEpoch=targetEpoch,
                    committedEpoch=_snap.epoch,
                    targetBasePayoutRate=overrideTargetBasePayoutRate,
                    controllerBasePayoutRate=_snap.controllerBasePayoutRate,
                )

    # starting over
    if _prev.basePayoutRate == 0:
        log EpochInitialized(
            epoch=_snap.epoch,
            controllerBasePayoutRate=_snap.controllerBasePayoutRate,
            basePayoutRate=_snap.basePayoutRate,
            rateSource=_snap.rateSource,
            paymentCap=_snap.paymentCap,
            minPaymentAmount=_snap.minPaymentAmount,
            maxVestingBonus=_snap.maxVestingBonus,
            minVestingLength=_snap.minVestingLength,
            maxVestingLength=_snap.maxVestingLength,
            timingEligible=_snap.timingEligible,
        )
        return

    # rolling to a new epoch
    log EpochRolled(
        fromEpoch=_prev.epoch,
        toEpoch=_snap.epoch,
        oldBasePayoutRate=_prev.basePayoutRate,
        controllerBasePayoutRate=_snap.controllerBasePayoutRate,
        newBasePayoutRate=_snap.basePayoutRate,
        rateSource=_snap.rateSource,
        newPaymentCap=_snap.paymentCap,
        newMinPaymentAmount=_snap.minPaymentAmount,
        newMaxVestingBonus=_snap.maxVestingBonus,
        newMinVestingLength=_snap.minVestingLength,
        newMaxVestingLength=_snap.maxVestingLength,
        previousAcceptedPayment=_prev.acceptedPayment,
        previousPaymentCap=_prev.paymentCap,
        previousWeightedLateness=_prev.weightedLateness,
        previousTimingEligible=_prev.timingEligible,
        utilizationBps=_transition.utilizationBps,
        effectiveAdjustmentBps=_transition.effectiveAdjustmentBps,
        decaySteps=_transition.decaySteps,
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
        paymentCapPerEpoch=_newConfig.paymentCapPerEpoch,
        minPaymentAmount=_newConfig.minPaymentAmount,
        maxAllInPayoutRate=_newConfig.maxAllInPayoutRate,
        seedBasePayoutRate=_newConfig.seedBasePayoutRate,
        uHighBps=_newConfig.uHighBps,
        uLowBps=_newConfig.uLowBps,
        minUpBps=_newConfig.minUpBps,
        maxUpBps=_newConfig.maxUpBps,
        minDownBps=_newConfig.minDownBps,
        maxDownBps=_newConfig.maxDownBps,
        decayBps=_newConfig.decayBps,
        maxDecayEpochs=_newConfig.maxDecayEpochs,
        maxVestingBonus=_newConfig.maxVestingBonus,
        minVestingLength=_newConfig.minVestingLength,
        maxVestingLength=_newConfig.maxVestingLength,
        epochLength=_newConfig.epochLength,
    )


# can buy now


@nonreentrant
@external
def setCanBuyNow(_canBuyNow: bool):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert self.canBuyNow != _canBuyNow # dev: no change
    self.canBuyNow = _canBuyNow
    if not _canBuyNow:
        self._invalidateInstalledOverride()
    log CanBuyNowSet(canBuyNow=_canBuyNow)


# utils


@internal
def _resetEpoch():
    self.epochState = empty(EpochSnapshot)
    self._invalidateInstalledOverride()


@internal
def _invalidateInstalledOverride():
    targetBasePayoutRate: uint256 = self.overrideTargetBasePayoutRate
    if targetBasePayoutRate != 0:
        targetEpoch: uint256 = self.overrideTargetEpoch
        self.overrideTargetBasePayoutRate = 0
        self.overrideTargetEpoch = 0
        log RateOverrideInvalidated(targetEpoch=targetEpoch, targetBasePayoutRate=targetBasePayoutRate)


#################
# Rate Override #
#################


# set rate override


@nonreentrant
@external
def setRateOverride(_targetBasePayoutRate: uint256, _targetEpoch: uint256) -> uint256:
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    isValid: bool = False
    resolvedEpoch: uint256 = 0
    isValid, resolvedEpoch = self._isValidRateOverride(_targetBasePayoutRate, _targetEpoch)
    assert isValid # dev: invalid rate override
    self.overrideTargetBasePayoutRate = _targetBasePayoutRate
    self.overrideTargetEpoch = resolvedEpoch
    log RateOverrideInstalled(targetEpoch=resolvedEpoch, targetBasePayoutRate=_targetBasePayoutRate)
    return resolvedEpoch


# cancel rate override


@view
@external
def canCancelRateOverride() -> bool:
    return self.overrideTargetBasePayoutRate != 0


@nonreentrant
@external
def cancelRateOverride():
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    targetBasePayoutRate: uint256 = self.overrideTargetBasePayoutRate
    assert targetBasePayoutRate != 0 # dev: no override
    targetEpoch: uint256 = self.overrideTargetEpoch
    self.overrideTargetBasePayoutRate = 0
    self.overrideTargetEpoch = 0
    log RateOverrideCancelled(targetEpoch=targetEpoch, targetBasePayoutRate=targetBasePayoutRate)


# validate rate override


@view
@external
def isValidRateOverride(_targetBasePayoutRate: uint256, _targetEpoch: uint256) -> bool:
    isValid: bool = False
    resolvedEpoch: uint256 = 0
    isValid, resolvedEpoch = self._isValidRateOverride(_targetBasePayoutRate, _targetEpoch)
    return isValid


@view
@internal
def _isValidRateOverride(_targetBasePayoutRate: uint256, _targetEpoch: uint256) -> (bool, uint256):
    if not self.isRunning or self.overrideTargetBasePayoutRate != 0:
        return False, 0

    config: InstantBondConfig = self.bondConfig
    ceiling: uint256 = self._basePayoutRateCeiling(config.maxAllInPayoutRate, config.maxVestingBonus)
    if _targetBasePayoutRate < MIN_BASE_PAYOUT_RATE or _targetBasePayoutRate > ceiling:
        return False, 0

    return self._resolveRateOverrideEpoch(_targetEpoch)


@view
@internal
def _resolveRateOverrideEpoch(_targetEpoch: uint256) -> (bool, uint256):
    epochLength: uint256 = self.bondConfig.epochLength
    if epochLength == 0:
        return False, 0

    currentEpoch: uint256 = 0
    if block.number >= self.genesisBlock:
        currentEpoch = (block.number - self.genesisBlock) // epochLength

    prev: EpochSnapshot = self.epochState
    if _targetEpoch == 0:
        if prev.basePayoutRate != 0 and prev.epoch == currentEpoch:
            if currentEpoch == max_value(uint256): # pragma: no branch
                return False, 0
            return True, currentEpoch + 1
        return True, currentEpoch

    if _targetEpoch < currentEpoch:
        return False, 0
    if prev.basePayoutRate != 0 and _targetEpoch <= prev.epoch:
        return False, 0
    return True, _targetEpoch


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

    # all-in payout-rate ceiling must be real and safe to scale by 100%
    if _config.maxAllInPayoutRate == 0 or _config.maxAllInPayoutRate > max_value(uint256) // HUNDRED_PERCENT:
        return False

    # epoch cap is at least one token unit and safe to scale by 100%
    paymentScale: uint256 = self.paymentScale
    if _config.paymentCapPerEpoch < paymentScale or _config.paymentCapPerEpoch > max_value(uint256) // HUNDRED_PERCENT:
        return False

    # min payment is at least one unit and cannot exceed the cap
    if _config.minPaymentAmount < paymentScale or _config.minPaymentAmount > _config.paymentCapPerEpoch:
        return False

    # live ceiling must be safe against both the new cap and a committed epoch's cap
    effectivePaymentCap: uint256 = max(_config.paymentCapPerEpoch, self.epochState.paymentCap)
    if _config.maxAllInPayoutRate > max_value(uint256) // effectivePaymentCap:
        return False

    # vesting bonus stays inside the hard cap
    if _config.maxVestingBonus > MAX_VESTING_BONUS:
        return False

    # every purchase has a positive, bounded vesting duration
    if _config.minVestingLength == 0 or _config.maxVestingLength < _config.minVestingLength:
        return False
    if _config.maxVestingLength > MAX_VESTING_LENGTH:
        return False

    # implied max base rate must still be a legal rate
    basePayoutRateCeiling: uint256 = self._basePayoutRateCeiling(_config.maxAllInPayoutRate, _config.maxVestingBonus)
    if basePayoutRateCeiling < MIN_BASE_PAYOUT_RATE:
        return False

    # full-cap bonus ripe cannot overflow
    maxBaseRipe: uint256 = _config.paymentCapPerEpoch * basePayoutRateCeiling // paymentScale
    if _config.maxVestingBonus != 0 and maxBaseRipe > max_value(uint256) // _config.maxVestingBonus:
        return False

    # seed must sit in [min base rate, implied ceiling]
    if _config.seedBasePayoutRate < MIN_BASE_PAYOUT_RATE or _config.seedBasePayoutRate > basePayoutRateCeiling:
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
def _basePayoutRateCeiling(_maxAllInPayoutRate: uint256, _maxVestingBonus: uint256) -> uint256:
    return _maxAllInPayoutRate * HUNDRED_PERCENT // (HUNDRED_PERCENT + _maxVestingBonus)


###########
# Preview #
###########


@view
@external
def previewBuyNow(_paymentAmount: uint256, _requestedVestingLength: uint256) -> InstantBondQuote:
    quote: InstantBondQuote = empty(InstantBondQuote)
    if not self.isRunning or block.number < self.genesisBlock:
        return quote

    config: InstantBondConfig = self.bondConfig
    if not self._isValidConfig(config):
        return quote

    # market
    snap: EpochSnapshot = empty(EpochSnapshot)
    transition: RateTransition = empty(RateTransition)
    snap, transition = self._getEpochSnapshot(self.epochState, config)
    remainingPayment: uint256 = snap.paymentCap - snap.acceptedPayment
    claims: address = self._getClaimsAddr()
    budgetRemaining: uint256 = 0
    if claims != empty(address) and claims.is_contract:
        budgetRemaining = staticcall InstantBondClaims(claims).remainingAllocationBudget()

    quote.epoch = snap.epoch
    quote.controllerBasePayoutRate = snap.controllerBasePayoutRate
    quote.basePayoutRate = snap.basePayoutRate
    quote.rateSource = snap.rateSource
    quote.remainingPayment = remainingPayment
    quote.minPaymentAmount = snap.minPaymentAmount
    quote.budgetRemaining = budgetRemaining

    if _paymentAmount < snap.minPaymentAmount or _paymentAmount > remainingPayment:
        return quote

    # payout
    payout: PayoutData = self._calculatePayout(
        _paymentAmount,
        snap.basePayoutRate,
        snap.maxVestingBonus,
        _requestedVestingLength,
        snap.minVestingLength,
        snap.maxVestingLength,
    )

    quote.baseRipe = payout.baseRipe
    quote.bonusRatio = payout.bonusRatio
    quote.bonusRipe = payout.bonusRipe
    quote.vestingLength = payout.vestingLength
    quote.creationBlock = block.number
    quote.maturityBlock = block.number + payout.vestingLength
    quote.totalRipe = payout.totalRipe

    # same gates as buyNow, minus deadline / expectedEpoch / slippage
    if deptBasics.isPaused or not self.canBuyNow:
        return quote
    if not self._isWithinMaxAllInPayoutRate(_paymentAmount, payout.totalRipe, config.maxAllInPayoutRate):
        return quote
    if payout.totalRipe > budgetRemaining:
        return quote
    if not self._isPurchaseReady():
        return quote

    quote.available = True
    return quote
