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
    deptBasics.pause,
    deptBasics.recoverFunds,
    deptBasics.recoverFundsMany,
    deptBasics.isPaused,
)

initializes: addys
initializes: deptBasics[addys := addys]

import contracts.modules.Addys as addys
import contracts.modules.DeptBasics as deptBasics
from interfaces import Department

from ethereum.ercs import IERC20
from ethereum.ercs import IERC20Detailed

interface InstantBondClaims:
    def createVestingPosition(_beneficiary: address, _ripePayout: uint256, _vestingLength: uint256) -> uint256: nonpayable
    def recordClaim(_beneficiary: address, _positionId: uint256) -> (uint256, uint256, uint256): nonpayable
    def remainingAllocationBudget() -> uint256: view
    def getRipeHq() -> address: view
    def isPaused() -> bool: view

interface RipeToken:
    def mint(_recipient: address, _amount: uint256) -> bool: nonpayable
    def ripeHq() -> address: view
    def isPaused() -> bool: view

interface MissionControl:
    def coreRipeGovVaultId() -> uint256: view

interface RipeHq:
    def canMintRipe(_addr: address) -> bool: view

interface Teller:
    def depositFromTrusted(_user: address, _vaultId: uint256, _asset: address, _amount: uint256, _lockDuration: uint256, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable

# High utilization reduces RIPE per payment unit; low utilization increases it.
# Idle decay also increases RIPE per payment unit toward the configured ceiling.
# The vesting bonus is applied after the epoch's base payout rate.
# One-shot rate overrides replace a derived epoch rate without changing these terms.
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
    timingEligible: bool # first epoch is eligible only when opened on its boundary

struct CalculatedPayout:
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

event InstantBondClaimed:
    beneficiary: indexed(address)
    positionIndex: indexed(uint256)
    amountClaimed: uint256
    totalClaimedForPosition: uint256
    ripePayout: uint256
    autoDeposited: bool
    lockDuration: uint256

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
# Current committed epoch while running; getEpochSnapshot() may project a later one.
epochState: public(EpochSnapshot)

paymentToken: public(address)
paymentScale: public(uint256)
genesisBlock: public(uint256)

HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%
MAX_VESTING_BONUS: constant(uint256) = 1000_00 # 1000.00%
MAX_VESTING_LENGTH: public(constant(uint256)) = 7_884_000
MAX_BATCH_CLAIMS: public(constant(uint256)) = 20
MAX_PRICE_STEP_BPS: constant(uint256) = 100_00 # 100.00%
MAX_DECAY_EPOCHS: constant(uint256) = 32
MAX_PAYMENT_DECIMALS: constant(uint8) = 73
# Numerically equals the BPS denominator, but represents the base-rate policy floor.
MIN_BASE_PAYOUT_RATE: constant(uint256) = 10_000
RATE_SOURCE_SEED: public(constant(uint256)) = 1
RATE_SOURCE_CONTROLLER: public(constant(uint256)) = 2
RATE_SOURCE_OVERRIDE: public(constant(uint256)) = 3


@deploy
def __init__(
    _ripeHq: address,
    _paymentToken: address,
    _config: InstantBondConfig,
):
    addys.__init__(_ripeHq)
    deptBasics.__init__(True, False, True) # starts paused, can mint ripe only

    paymentDecimals: uint8 = self._getValidatedPaymentDecimals(_paymentToken)
    self._storePaymentToken(_paymentToken, paymentDecimals)
    assert self._isValidConfig(_config) # dev: invalid config
    self.bondConfig = _config


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
    assert self.canBuyNow # dev: disabled
    assert block.number <= _deadlineBlock # dev: expired
    assert self._isPurchaseReady() # dev: mint not ready

    config: InstantBondConfig = self.bondConfig
    previousSnapshot: EpochSnapshot = self.epochState
    candidateSnapshot: EpochSnapshot = empty(EpochSnapshot)
    transition: RateTransition = empty(RateTransition)
    quote: InstantBondQuote = empty(InstantBondQuote)
    quote, candidateSnapshot, transition = self._quote(
        _paymentAmount,
        _requestedVestingLength,
        previousSnapshot,
        config,
    )

    assert _expectedEpoch == quote.epoch # dev: epoch moved
    assert quote.vestingLength == _expectedVestingLength # dev: vesting length moved
    assert quote.totalRipe >= _minRipeOut # dev: slippage
    assert _paymentAmount >= quote.minPaymentAmount # dev: below minimum payment
    assert _paymentAmount <= quote.remainingPayment # dev: exceeds available amount
    assert quote.totalRipe <= quote.budgetRemaining # dev: allocation budget

    self._commitEpochIfNeeded(previousSnapshot, candidateSnapshot, transition)
    self.epochState.acceptedPayment += _paymentAmount
    self.epochState.weightedLateness += _paymentAmount * self._getCurrentLatenessBps()

    # collect payment amount, move to endaoment funds
    endaoFunds: address = addys._getEndaomentFundsAddr()
    paymentToken: address = self.paymentToken
    paymentBalanceBefore: uint256 = staticcall IERC20(paymentToken).balanceOf(endaoFunds)
    assert extcall IERC20(paymentToken).transferFrom(msg.sender, endaoFunds, _paymentAmount, default_return_value=True) # dev: payment failed
    paymentBalanceAfter: uint256 = staticcall IERC20(paymentToken).balanceOf(endaoFunds)
    assert paymentBalanceAfter >= paymentBalanceBefore # dev: payment receipt mismatch
    assert paymentBalanceAfter - paymentBalanceBefore == _paymentAmount # dev: payment receipt mismatch

    positionIndex: uint256 = extcall InstantBondClaims(addys._getInstantBondClaimsAddr()).createVestingPosition(msg.sender, quote.totalRipe, quote.vestingLength)

    log InstantBondPurchased(
        buyer=msg.sender,
        positionIndex=positionIndex,
        paymentAmount=_paymentAmount,
        baseRipe=quote.baseRipe,
        bonusRipe=quote.bonusRipe,
        bonusRatio=quote.bonusRatio,
        vestingLength=quote.vestingLength,
        creationBlock=quote.creationBlock,
        maturityBlock=quote.maturityBlock,
        totalRipe=quote.totalRipe,
        controllerBasePayoutRate=quote.controllerBasePayoutRate,
        basePayoutRate=quote.basePayoutRate,
        rateSource=quote.rateSource,
        epoch=quote.epoch,
    )
    return quote.totalRipe


# preview


@view
@external
def previewBuyNow(_paymentAmount: uint256, _requestedVestingLength: uint256) -> InstantBondQuote:
    quote: InstantBondQuote = empty(InstantBondQuote)
    if not self.isRunning or block.number < self.genesisBlock:
        return quote

    # Vyper requires binding every returned value; only the quote is used in this view.
    candidateSnapshot: EpochSnapshot = empty(EpochSnapshot)
    transition: RateTransition = empty(RateTransition)
    quote, candidateSnapshot, transition = self._quote(
        _paymentAmount,
        _requestedVestingLength,
        self.epochState,
        self.bondConfig,
    )

    if _paymentAmount < quote.minPaymentAmount or _paymentAmount > quote.remainingPayment:
        return quote
    if deptBasics.isPaused or not self.canBuyNow:
        return quote
    if quote.totalRipe > quote.budgetRemaining:
        return quote
    if not self._isPurchaseReady():
        return quote

    quote.available = True
    return quote


# quote


@view
@internal
def _quote(
    _paymentAmount: uint256,
    _requestedVestingLength: uint256,
    _previousSnapshot: EpochSnapshot,
    _config: InstantBondConfig,
) -> (InstantBondQuote, EpochSnapshot, RateTransition):
    candidateSnapshot: EpochSnapshot = empty(EpochSnapshot)
    transition: RateTransition = empty(RateTransition)
    candidateSnapshot, transition = self._deriveEpochSnapshot(_previousSnapshot, _config)
    payout: CalculatedPayout = self._calculatePayout(
        _paymentAmount,
        _requestedVestingLength,
        candidateSnapshot,
    )
    budgetRemaining: uint256 = 0
    claims: address = addys._getInstantBondClaimsAddr()
    if claims != empty(address) and claims.is_contract:
        budgetRemaining = staticcall InstantBondClaims(claims).remainingAllocationBudget()

    quote: InstantBondQuote = empty(InstantBondQuote)
    quote.epoch = candidateSnapshot.epoch
    quote.controllerBasePayoutRate = candidateSnapshot.controllerBasePayoutRate
    quote.basePayoutRate = candidateSnapshot.basePayoutRate
    quote.rateSource = candidateSnapshot.rateSource
    quote.remainingPayment = candidateSnapshot.paymentCap - candidateSnapshot.acceptedPayment
    quote.minPaymentAmount = candidateSnapshot.minPaymentAmount
    quote.budgetRemaining = budgetRemaining
    quote.baseRipe = payout.baseRipe
    quote.bonusRatio = payout.bonusRatio
    quote.bonusRipe = payout.bonusRipe
    quote.vestingLength = payout.vestingLength
    quote.creationBlock = block.number
    quote.maturityBlock = block.number + payout.vestingLength
    quote.totalRipe = payout.totalRipe
    return quote, candidateSnapshot, transition


# calc payout


@view
@internal
def _calculatePayout(
    _paymentAmount: uint256,
    _requestedVestingLength: uint256,
    _snapshot: EpochSnapshot,
) -> CalculatedPayout:
    # the epoch snapshot binds the rate and vesting terms to one configuration.
    baseRipe: uint256 = _paymentAmount * _snapshot.basePayoutRate // self.paymentScale
    vestingLength: uint256 = _snapshot.minVestingLength
    if _requestedVestingLength != 0:
        vestingLength = min(max(_requestedVestingLength, _snapshot.minVestingLength), _snapshot.maxVestingLength)

    bonusRatio: uint256 = _snapshot.maxVestingBonus
    if _snapshot.maxVestingLength != _snapshot.minVestingLength:
        bonusRatio = _snapshot.maxVestingBonus * (vestingLength - _snapshot.minVestingLength) // (_snapshot.maxVestingLength - _snapshot.minVestingLength)

    bonusRipe: uint256 = baseRipe * bonusRatio // HUNDRED_PERCENT
    return CalculatedPayout(
        baseRipe=baseRipe,
        bonusRatio=bonusRatio,
        bonusRipe=bonusRipe,
        vestingLength=vestingLength,
        totalRipe=baseRipe + bonusRipe,
    )


##########
# Claims #
##########


@nonreentrant
@external
def claimVestedRipe(
    _positionId: uint256,
    _autoDeposit: bool,
    _lockDuration: uint256,
) -> uint256:
    return self._claimVestedRipe([_positionId], _autoDeposit, _lockDuration)


@nonreentrant
@external
def claimVestedRipeMany(
    _positionIds: DynArray[uint256, MAX_BATCH_CLAIMS],
    _autoDeposit: bool,
    _lockDuration: uint256,
) -> uint256:
    return self._claimVestedRipe(_positionIds, _autoDeposit, _lockDuration)


@internal
def _claimVestedRipe(
    _positionIds: DynArray[uint256, MAX_BATCH_CLAIMS],
    _autoDeposit: bool,
    _lockDuration: uint256,
) -> uint256:
    assert len(_positionIds) != 0 # dev: empty positions
    assert self._isMintReady() # dev: claim not ready

    claims: address = addys._getInstantBondClaimsAddr()
    totalClaimedRipe: uint256 = 0
    for i: uint256 in range(len(_positionIds), bound=MAX_BATCH_CLAIMS):
        amountClaimed: uint256 = 0
        totalClaimedForPosition: uint256 = 0
        ripePayout: uint256 = 0
        amountClaimed, totalClaimedForPosition, ripePayout = extcall InstantBondClaims(claims).recordClaim(msg.sender, _positionIds[i])
        totalClaimedRipe += amountClaimed
        log InstantBondClaimed(
            beneficiary=msg.sender,
            positionIndex=_positionIds[i],
            amountClaimed=amountClaimed,
            totalClaimedForPosition=totalClaimedForPosition,
            ripePayout=ripePayout,
            autoDeposited=_autoDeposit,
            lockDuration=_lockDuration,
        )

    self._settleVestedRipe(msg.sender, totalClaimedRipe, _autoDeposit, _lockDuration)
    return totalClaimedRipe


@internal
def _settleVestedRipe(
    _beneficiary: address,
    _amount: uint256,
    _autoDeposit: bool,
    _lockDuration: uint256,
):
    ripeToken: address = addys._getRipeToken()
    if not _autoDeposit:
        balanceBefore: uint256 = staticcall IERC20(ripeToken).balanceOf(_beneficiary)
        assert extcall RipeToken(ripeToken).mint(_beneficiary, _amount) # dev: mint failed
        balanceAfter: uint256 = staticcall IERC20(ripeToken).balanceOf(_beneficiary)
        assert balanceAfter >= balanceBefore # dev: ripe receipt mismatch
        assert balanceAfter - balanceBefore == _amount # dev: ripe receipt mismatch
        return

    a: addys.Addys = addys._getAddys()
    coreRipeGovVaultId: uint256 = staticcall MissionControl(a.missionControl).coreRipeGovVaultId()
    assert coreRipeGovVaultId != 0 # dev: invalid ripe gov vault

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


@view
@internal
def _isMintReady() -> bool:
    if addys._getInstantBondLaneAddr() != self:
        return False

    claims: address = addys._getInstantBondClaimsAddr()
    if claims == empty(address) or not claims.is_contract:
        return False
    if staticcall InstantBondClaims(claims).isPaused():
        return False

    ripeHq: address = addys._getRipeHq()
    if staticcall InstantBondClaims(claims).getRipeHq() != ripeHq:
        return False
    if not staticcall RipeHq(ripeHq).canMintRipe(self):
        return False

    ripeToken: address = addys._getRipeToken()
    if ripeToken == empty(address) or not ripeToken.is_contract:
        return False
    if staticcall RipeToken(ripeToken).ripeHq() != ripeHq:
        return False
    if staticcall RipeToken(ripeToken).isPaused():
        return False
    return True


@view
@internal
def _isPurchaseReady() -> bool:
    endaoFunds: address = addys._getEndaomentFundsAddr()
    if endaoFunds == empty(address) or not endaoFunds.is_contract:
        return False
    return self._isMintReady()


##########
# Epochs #
##########


# controller transition


@pure
@internal
def _calculateControllerTransition(
    _previousSnapshot: EpochSnapshot,
    _elapsed: uint256,
    _config: InstantBondConfig,
) -> RateTransition:
    ceiling: uint256 = self._basePayoutRateCeiling(_config.maxAllInPayoutRate, _config.maxVestingBonus)
    basePayoutRate: uint256 = min(_previousSnapshot.basePayoutRate, ceiling)
    utilizationBps: uint256 = 0
    adjustmentBps: uint256 = 0
    decaySteps: uint256 = 0

    # stored empty epochs have no fill signal; decay the whole gap.
    # a committed buy always records a positive payment, so this is defensive.
    if _previousSnapshot.acceptedPayment == 0: # pragma: no branch
        decaySteps = min(_elapsed, _config.maxDecayEpochs)

    else:
        utilizationBps = _previousSnapshot.acceptedPayment * HUNDRED_PERCENT // _previousSnapshot.paymentCap

        # Strong demand lowers RIPE per payment unit, increasing RIPE's effective price.
        if utilizationBps >= _config.uHighBps:
            strengthBps: uint256 = (utilizationBps - _config.uHighBps) * HUNDRED_PERCENT // (HUNDRED_PERCENT - _config.uHighBps)
            earlinessBps: uint256 = 0
            if _previousSnapshot.timingEligible:
                earlinessBps = HUNDRED_PERCENT - (_previousSnapshot.weightedLateness // _previousSnapshot.acceptedPayment)
            demandBps: uint256 = strengthBps * earlinessBps // HUNDRED_PERCENT
            adjustmentBps = _config.minUpBps + (_config.maxUpBps - _config.minUpBps) * demandBps // HUNDRED_PERCENT
            basePayoutRate = max(basePayoutRate * HUNDRED_PERCENT // (HUNDRED_PERCENT + adjustmentBps), MIN_BASE_PAYOUT_RATE)

        # Weak demand raises RIPE per payment unit, decreasing RIPE's effective price.
        elif utilizationBps <= _config.uLowBps:
            weaknessBps: uint256 = (_config.uLowBps - utilizationBps) * HUNDRED_PERCENT // _config.uLowBps
            adjustmentBps = _config.minDownBps + (_config.maxDownBps - _config.minDownBps) * weaknessBps // HUNDRED_PERCENT
            basePayoutRate = min(basePayoutRate * HUNDRED_PERCENT // (HUNDRED_PERCENT - adjustmentBps), ceiling)

        # the previous filled epoch provides the controller signal; only later epochs count as idle decay steps.
        decaySteps = min(_elapsed - 1, _config.maxDecayEpochs)

    for i: uint256 in range(decaySteps, bound=MAX_DECAY_EPOCHS):
        basePayoutRate = min(basePayoutRate * HUNDRED_PERCENT // (HUNDRED_PERCENT - _config.decayBps), ceiling)

    return RateTransition(
        controllerBasePayoutRate=basePayoutRate,
        utilizationBps=utilizationBps,
        effectiveAdjustmentBps=adjustmentBps,
        decaySteps=decaySteps,
    )

# epoch snapshot


@view
@external
def getEpochSnapshot() -> EpochSnapshot:
    if not self.isRunning:
        return empty(EpochSnapshot)
    # Vyper requires binding every returned value; only the snapshot is used here.
    candidateSnapshot: EpochSnapshot = empty(EpochSnapshot)
    transition: RateTransition = empty(RateTransition)
    candidateSnapshot, transition = self._deriveEpochSnapshot(self.epochState, self.bondConfig)
    return candidateSnapshot


@view
@internal
def _deriveEpochSnapshot(_previousSnapshot: EpochSnapshot, _config: InstantBondConfig) -> (EpochSnapshot, RateTransition):
    if block.number < self.genesisBlock:
        return empty(EpochSnapshot), empty(RateTransition)

    epoch: uint256 = (block.number - self.genesisBlock) // _config.epochLength

    # already committed this epoch
    if self._isEpochAlreadyCommitted(_previousSnapshot, epoch):
        return _previousSnapshot, empty(RateTransition)

    transition: RateTransition = empty(RateTransition)
    defaultRateSource: uint256 = RATE_SOURCE_SEED
    timingEligible: bool = True
    if not self._hasCommittedEpoch(_previousSnapshot):
        transition.controllerBasePayoutRate = _config.seedBasePayoutRate
        timingEligible = (block.number - self.genesisBlock) % _config.epochLength == 0
    else:
        # Later epochs roll the controller and always have meaningful timing data.
        transition = self._calculateControllerTransition(
            _previousSnapshot,
            epoch - _previousSnapshot.epoch,
            _config,
        )
        defaultRateSource = RATE_SOURCE_CONTROLLER

    # Apply an override only after deriving the normal rate for this epoch.
    basePayoutRate: uint256 = 0
    rateSource: uint256 = 0
    basePayoutRate, rateSource = self._applyScheduledRateOverride(epoch, transition.controllerBasePayoutRate, defaultRateSource)
    return self._buildEpochSnapshot(
        epoch,
        transition.controllerBasePayoutRate,
        basePayoutRate,
        rateSource,
        _config,
        timingEligible,
    ), transition


@pure
@internal
def _hasCommittedEpoch(_snapshot: EpochSnapshot) -> bool:
    # a legal base payout rate is always non-zero, so zero denotes no committed epoch.
    return _snapshot.basePayoutRate != 0


@pure
@internal
def _isEpochAlreadyCommitted(_snapshot: EpochSnapshot, _epoch: uint256) -> bool:
    return self._hasCommittedEpoch(_snapshot) and _epoch <= _snapshot.epoch


@view
@internal
def _applyScheduledRateOverride(_epoch: uint256, _basePayoutRate: uint256, _rateSource: uint256) -> (uint256, uint256):
    if self.overrideTargetBasePayoutRate != 0 and self.overrideTargetEpoch == _epoch:
        return self.overrideTargetBasePayoutRate, RATE_SOURCE_OVERRIDE
    return _basePayoutRate, _rateSource


# open epoch


@pure
@internal
def _buildEpochSnapshot(
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


# commit epoch


@internal
def _commitEpochIfNeeded(
    _previousSnapshot: EpochSnapshot,
    _candidateSnapshot: EpochSnapshot,
    _transition: RateTransition,
):

    # already committed this epoch
    if self._isEpochAlreadyCommitted(_previousSnapshot, _candidateSnapshot.epoch):
        return

    # store the new epoch
    self.epochState = _candidateSnapshot
    self._consumeInstalledOverride(_previousSnapshot, _candidateSnapshot)

    # starting over
    if not self._hasCommittedEpoch(_previousSnapshot):
        log EpochInitialized(
            epoch=_candidateSnapshot.epoch,
            controllerBasePayoutRate=_candidateSnapshot.controllerBasePayoutRate,
            basePayoutRate=_candidateSnapshot.basePayoutRate,
            rateSource=_candidateSnapshot.rateSource,
            paymentCap=_candidateSnapshot.paymentCap,
            minPaymentAmount=_candidateSnapshot.minPaymentAmount,
            maxVestingBonus=_candidateSnapshot.maxVestingBonus,
            minVestingLength=_candidateSnapshot.minVestingLength,
            maxVestingLength=_candidateSnapshot.maxVestingLength,
            timingEligible=_candidateSnapshot.timingEligible,
        )
        return

    # rolling to a new epoch
    log EpochRolled(
        fromEpoch=_previousSnapshot.epoch,
        toEpoch=_candidateSnapshot.epoch,
        oldBasePayoutRate=_previousSnapshot.basePayoutRate,
        controllerBasePayoutRate=_candidateSnapshot.controllerBasePayoutRate,
        newBasePayoutRate=_candidateSnapshot.basePayoutRate,
        rateSource=_candidateSnapshot.rateSource,
        newPaymentCap=_candidateSnapshot.paymentCap,
        newMinPaymentAmount=_candidateSnapshot.minPaymentAmount,
        newMaxVestingBonus=_candidateSnapshot.maxVestingBonus,
        newMinVestingLength=_candidateSnapshot.minVestingLength,
        newMaxVestingLength=_candidateSnapshot.maxVestingLength,
        previousAcceptedPayment=_previousSnapshot.acceptedPayment,
        previousPaymentCap=_previousSnapshot.paymentCap,
        previousWeightedLateness=_previousSnapshot.weightedLateness,
        previousTimingEligible=_previousSnapshot.timingEligible,
        utilizationBps=_transition.utilizationBps,
        effectiveAdjustmentBps=_transition.effectiveAdjustmentBps,
        decaySteps=_transition.decaySteps,
    )


@internal
def _consumeInstalledOverride(_previousSnapshot: EpochSnapshot, _candidateSnapshot: EpochSnapshot):
    targetBasePayoutRate: uint256 = self.overrideTargetBasePayoutRate
    if targetBasePayoutRate == 0:
        return

    targetEpoch: uint256 = self.overrideTargetEpoch
    if targetEpoch > _candidateSnapshot.epoch:
        return

    self._clearInstalledOverride()
    if targetEpoch == _candidateSnapshot.epoch:
        log RateOverrideApplied(
            fromEpoch=_previousSnapshot.epoch,
            toEpoch=_candidateSnapshot.epoch,
            targetBasePayoutRate=targetBasePayoutRate,
            controllerBasePayoutRate=_candidateSnapshot.controllerBasePayoutRate,
        )
    else:
        log RateOverrideMissed(
            targetEpoch=targetEpoch,
            committedEpoch=_candidateSnapshot.epoch,
            targetBasePayoutRate=targetBasePayoutRate,
            controllerBasePayoutRate=_candidateSnapshot.controllerBasePayoutRate,
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
def _getCurrentLatenessBps() -> uint256:
    epochLength: uint256 = self.bondConfig.epochLength
    if epochLength == 1:
        return 0
    offset: uint256 = (block.number - self.genesisBlock) % epochLength
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
    assert self._isValidConfigValues(config) # dev: not configured
    self.bondConfig = config

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
    log CanBuyNowSet(canBuyNow=_canBuyNow)


# lifecycle helpers


@internal
def _resetEpoch():
    self.epochState = empty(EpochSnapshot)
    self._invalidateInstalledOverride()


@internal
def _clearInstalledOverride():
    self.overrideTargetBasePayoutRate = 0
    self.overrideTargetEpoch = 0


@internal
def _invalidateInstalledOverride():
    targetBasePayoutRate: uint256 = self.overrideTargetBasePayoutRate
    if targetBasePayoutRate != 0:
        targetEpoch: uint256 = self.overrideTargetEpoch
        self._clearInstalledOverride()
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


@nonreentrant
@external
def cancelRateOverride():
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    targetBasePayoutRate: uint256 = self.overrideTargetBasePayoutRate
    assert targetBasePayoutRate != 0 # dev: no override
    targetEpoch: uint256 = self.overrideTargetEpoch
    self._clearInstalledOverride()
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

    earliestApplicableEpoch: uint256 = currentEpoch
    previousSnapshot: EpochSnapshot = self.epochState
    if self._hasCommittedEpoch(previousSnapshot) and previousSnapshot.epoch >= currentEpoch:
        if previousSnapshot.epoch == max_value(uint256): # pragma: no branch
            return False, 0
        earliestApplicableEpoch = previousSnapshot.epoch + 1

    # Zero means the earliest epoch that has not already accepted a purchase.
    if _targetEpoch == 0:
        return True, earliestApplicableEpoch
    if _targetEpoch < earliestApplicableEpoch:
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
    paymentDecimals: uint8 = self._getValidatedPaymentDecimals(_token)
    self._storePaymentToken(_token, paymentDecimals)
    log PaymentTokenSet(token=_token, decimals=paymentDecimals, scale=self.paymentScale)


@internal
def _storePaymentToken(_token: address, _paymentDecimals: uint8):
    self.paymentToken = _token
    self.paymentScale = 10 ** convert(_paymentDecimals, uint256)


@view
@internal
def _getValidatedPaymentDecimals(_token: address) -> uint8:
    assert self._isValidPaymentToken(_token) # dev: invalid payment token
    return staticcall IERC20Detailed(_token).decimals()


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
    if not self._isValidConfigValues(_config):
        return False

    # setConfig cannot change the live clock; only start() can
    installedLength: uint256 = self.bondConfig.epochLength
    return installedLength == 0 or _config.epochLength == installedLength


@view
@internal
def _isValidConfigValues(_config: InstantBondConfig) -> bool:
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

    return True


# base rate ceiling


@pure
@internal
def _basePayoutRateCeiling(_maxAllInPayoutRate: uint256, _maxVestingBonus: uint256) -> uint256:
    return _maxAllInPayoutRate * HUNDRED_PERCENT // (HUNDRED_PERCENT + _maxVestingBonus)
