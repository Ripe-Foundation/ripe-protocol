#  ___ _  _ ___ _____ _   _  _ _____   ___  ___  _  _ ___    _      _   _  _ ___
# |_ _| \| / __|_   _/_\ | \| |_   _| | _ )/ _ \| \| |   \  | |    /_\ | \| | __|
#  | || .` \__ \ | |/ _ \| .` | | |   | _ \ (_) | .` | |) | | |__ / _ \| .` | _|
# |___|_|\_|___/ |_/_/ \_\_|\_| |_|   |___/ \___/|_|\_|___/  |____/_/ \_\_|\_|___|
#
#     ╔════════════════════════════════════════╗
#     ║  ** Instant Bond Lane **               ║
#     ║  Fixed-epoch direct RIPE purchases     ║
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

interface MissionControl:
    def ripeGovVaultConfig(_asset: address) -> cs.RipeGovVaultConfig: view
    def coreRipeGovVaultId() -> uint256: view

interface RipeHq:
    def canMintRipe(_addr: address) -> bool: view

interface RipeToken:
    def mint(_recipient: address, _amount: uint256) -> bool: nonpayable

interface Teller:
    def depositFromTrusted(_user: address, _vaultId: uint256, _asset: address, _amount: uint256, _lockDuration: uint256, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable

interface Ledger:
    def badDebt() -> uint256: view

# NOTE: Keep this struct byte-for-byte aligned with SwitchboardFoxtrot.InstantBondConfig.
# Guarded by test_instant_bond_config_struct_bodies_are_byte_for_byte_identical.
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

struct InstantBondQuote:
    available: bool
    epoch: uint256
    pricingConfigVersion: uint256
    liveConfigVersion: uint256
    rate: uint256
    remainingPayment: uint256
    minPaymentAmount: uint256
    budgetRemaining: uint256
    baseRipe: uint256
    bonusRatio: uint256
    bonusRipe: uint256
    actualLock: uint256
    totalRipe: uint256
    canExitEarly: bool
    exitFee: uint256
    isExitFrozen: bool

struct PricingState:
    epoch: uint256
    rate: uint256
    paymentCap: uint256
    minPaymentAmount: uint256
    maxLockBonus: uint256
    pricingConfigVersion: uint256
    acceptedPayment: uint256
    weightedLateness: uint256
    timingEligible: bool
    didInitialize: bool
    didRollover: bool
    fromEpoch: uint256
    oldRate: uint256
    previousAcceptedPayment: uint256
    previousPaymentCap: uint256
    previousWeightedLateness: uint256
    previousTimingEligible: bool
    utilizationBps: uint256
    effectiveAdjustmentBps: uint256
    decaySteps: uint256
    controllerRate: uint256

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
    pricingConfigVersion: indexed(uint256)

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
    pricingConfigVersion: indexed(uint256)

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
    pricingConfigVersion: indexed(uint256)
    liveConfigVersion: uint256
    ripeGovVaultId: uint256

event InstantBondConfigSet:
    newVersion: indexed(uint256)
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

event RateOverrideInstalled:
    newVersion: indexed(uint256)
    targetRate: uint256
    boundConfigVersion: indexed(uint256)

event RateOverrideApplied:
    newVersion: indexed(uint256)
    fromEpoch: indexed(uint256)
    toEpoch: indexed(uint256)
    targetRate: uint256
    controllerRate: uint256

event RateOverrideCancelled:
    newVersion: indexed(uint256)
    targetRate: uint256

event RateOverrideInvalidated:
    newVersion: indexed(uint256)
    targetRate: uint256
    newConfigVersion: indexed(uint256)

HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%
MAX_LOCK_BONUS: constant(uint256) = 1000_00 # 1000.00%
MAX_PRICE_STEP_BPS: constant(uint256) = 100_00 # 100.00%
MAX_DECAY_EPOCHS: constant(uint256) = 32
MAX_PAYMENT_DECIMALS: constant(uint8) = 73
MIN_BASE_RATE: constant(uint256) = 10_000

PAYMENT_TOKEN: public(immutable(address))
PAYMENT_DECIMALS: public(immutable(uint8))
PAYMENT_SCALE: public(immutable(uint256))
GENESIS_BLOCK: public(immutable(uint256))
EPOCH_LENGTH: public(immutable(uint256))

config: public(InstantBondConfig)
configVersion: public(uint256)

# Stored snapshot, lazily advanced by buyNow. Use previewBuyNow for current pricing;
# never construct a quote directly from epochRate or the other stored epoch getters.
isInitialized: public(bool)
currentEpoch: public(uint256)
epochRate: public(uint256)
epochPaymentCap: public(uint256)
epochMinPaymentAmount: public(uint256)
epochMaxLockBonus: public(uint256)
epochPricingVersion: public(uint256)
epochAcceptedPayment: public(uint256)
epochWeightedLateness: public(uint256)
epochTimingEligible: public(bool)

# zero means no installed target; every config replacement invalidates it
rateOverride: public(uint256)
overrideVersion: public(uint256)

cumulativeMinted: public(uint256)


@deploy
def __init__(
    _ripeHq: address,
    _paymentToken: address,
    _genesisBlock: uint256,
    _epochLength: uint256,
):
    assert _paymentToken != empty(address) and _paymentToken.is_contract # dev: invalid payment token
    assert _epochLength != 0 and _epochLength <= max_value(uint256) // HUNDRED_PERCENT + 1 # dev: invalid epoch length

    paymentDecimals: uint8 = staticcall IERC20Detailed(_paymentToken).decimals()
    assert paymentDecimals <= MAX_PAYMENT_DECIMALS # dev: invalid payment decimals

    addys.__init__(_ripeHq)
    assert _paymentToken != addys._getRipeToken() # dev: payment token is ripe
    deptBasics.__init__(True, False, True) # starts paused, can mint ripe only

    PAYMENT_TOKEN = _paymentToken
    PAYMENT_DECIMALS = paymentDecimals
    PAYMENT_SCALE = 10 ** convert(paymentDecimals, uint256)
    GENESIS_BLOCK = _genesisBlock
    EPOCH_LENGTH = _epochLength


#################
# Configuration #
#################


@view
@external
def isValidConfig(_config: InstantBondConfig) -> bool:
    return self._isValidConfig(_config)


@view
@internal
def _isValidConfig(_config: InstantBondConfig) -> bool:
    # utilization and controller bounds
    if _config.uLowBps == 0 or _config.uLowBps >= _config.uHighBps:
        return False
    if _config.uHighBps >= HUNDRED_PERCENT:
        return False

    if _config.minUpBps == 0 or _config.minUpBps > _config.maxUpBps:
        return False
    if _config.maxUpBps > MAX_PRICE_STEP_BPS:
        return False
    if _config.minDownBps == 0 or _config.minDownBps > _config.maxDownBps:
        return False
    if _config.decayBps == 0 or _config.decayBps >= HUNDRED_PERCENT:
        return False
    if _config.maxDownBps > _config.decayBps or _config.maxDownBps >= _config.minUpBps:
        return False
    if (HUNDRED_PERCENT + _config.minUpBps) * (HUNDRED_PERCENT - _config.maxDownBps) < HUNDRED_PERCENT * HUNDRED_PERCENT:
        return False
    if _config.maxDecayEpochs == 0 or _config.maxDecayEpochs > MAX_DECAY_EPOCHS:
        return False

    # rate and payment arithmetic bounds
    if _config.maxEffectiveRate == 0 or _config.maxEffectiveRate > max_value(uint256) // HUNDRED_PERCENT:
        return False
    if _config.paymentCapPerEpoch < PAYMENT_SCALE or _config.paymentCapPerEpoch > max_value(uint256) // HUNDRED_PERCENT:
        return False
    if _config.minPaymentAmount < PAYMENT_SCALE or _config.minPaymentAmount > _config.paymentCapPerEpoch:
        return False
    if _config.maxEffectiveRate > max_value(uint256) // _config.paymentCapPerEpoch:
        return False

    # lock bonus and payout arithmetic bounds
    if _config.maxLockBonus > MAX_LOCK_BONUS:
        return False
    baseRateCeiling: uint256 = self._baseRateCeiling(_config.maxEffectiveRate, _config.maxLockBonus)
    if baseRateCeiling < MIN_BASE_RATE:
        return False
    maxBaseRipe: uint256 = _config.paymentCapPerEpoch * baseRateCeiling // PAYMENT_SCALE
    if _config.maxLockBonus != 0 and maxBaseRipe > max_value(uint256) // _config.maxLockBonus:
        return False
    if _config.seedRate < MIN_BASE_RATE or _config.seedRate > baseRateCeiling:
        return False

    # issuance budget cannot fall below prior minting
    if _config.mintBudget < self.cumulativeMinted:
        return False

    return True


@nonreentrant
@external
def setConfig(_newConfig: InstantBondConfig, _expectedVersion: uint256) -> uint256:
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert _expectedVersion == self.configVersion # dev: stale config version
    assert self._isValidConfig(_newConfig) # dev: invalid config

    newVersion: uint256 = self.configVersion + 1
    self.config = _newConfig
    self.configVersion = newVersion

    overrideRate: uint256 = self.rateOverride
    if overrideRate != 0:
        newOverrideVersion: uint256 = self.overrideVersion + 1
        self.rateOverride = 0
        self.overrideVersion = newOverrideVersion
        log RateOverrideInvalidated(
            newVersion=newOverrideVersion,
            targetRate=overrideRate,
            newConfigVersion=newVersion,
        )

    log InstantBondConfigSet(
        newVersion=newVersion,
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
    )
    return newVersion


#################
# Rate Override #
#################


@view
@external
def isValidRateOverride(
    _targetRate: uint256,
    _expectedConfigVersion: uint256,
    _expectedOverrideVersion: uint256,
) -> bool:
    if _expectedConfigVersion != self.configVersion:
        return False
    if _expectedOverrideVersion != self.overrideVersion:
        return False
    return self._isValidRateOverride(_targetRate)


@view
@internal
def _isValidRateOverride(_targetRate: uint256) -> bool:
    if not self.isInitialized or self.rateOverride != 0:
        return False
    config: InstantBondConfig = self.config
    ceiling: uint256 = self._baseRateCeiling(config.maxEffectiveRate, config.maxLockBonus)
    return _targetRate >= MIN_BASE_RATE and _targetRate <= ceiling


@nonreentrant
@external
def setRateOverride(
    _targetRate: uint256,
    _expectedConfigVersion: uint256,
    _expectedOverrideVersion: uint256,
) -> uint256:
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert _expectedConfigVersion == self.configVersion # dev: stale config version
    assert _expectedOverrideVersion == self.overrideVersion # dev: stale override version
    assert self._isValidRateOverride(_targetRate) # dev: invalid rate override

    newVersion: uint256 = self.overrideVersion + 1
    self.rateOverride = _targetRate
    self.overrideVersion = newVersion
    log RateOverrideInstalled(
        newVersion=newVersion,
        targetRate=_targetRate,
        boundConfigVersion=_expectedConfigVersion,
    )
    return newVersion


@view
@external
def canCancelRateOverride(_expectedOverrideVersion: uint256) -> bool:
    return self.rateOverride != 0 and _expectedOverrideVersion == self.overrideVersion


@nonreentrant
@external
def cancelRateOverride(_expectedOverrideVersion: uint256) -> uint256:
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert _expectedOverrideVersion == self.overrideVersion # dev: stale override version
    targetRate: uint256 = self.rateOverride
    assert targetRate != 0 # dev: no override

    newVersion: uint256 = self.overrideVersion + 1
    self.rateOverride = 0
    self.overrideVersion = newVersion
    log RateOverrideCancelled(newVersion=newVersion, targetRate=targetRate)
    return newVersion


############
# Purchase #
############


@nonreentrant
@external
def buyNow(
    _paymentAmount: uint256,
    _requestedLock: uint256,
    _expectedEpoch: uint256,
    _minRipeOut: uint256,
    _deadlineBlock: uint256,
) -> uint256:
    # validate availability
    configVersion: uint256 = self.configVersion
    assert configVersion != 0 # dev: not configured
    assert block.number >= GENESIS_BLOCK # dev: before genesis
    assert not deptBasics.isPaused # dev: paused

    config: InstantBondConfig = self.config
    assert config.canBuyNow # dev: disabled
    assert block.number <= _deadlineBlock # dev: expired

    a: addys.Addys = addys._getAddys()
    assert staticcall RipeHq(a.hq).canMintRipe(self) # dev: mint unavailable

    endaoFunds: address = addys._getEndaomentFundsAddr()
    assert endaoFunds != empty(address) # dev: no destination

    # project current epoch and validate payment
    pricing: PricingState = self._getPricingState(config, configVersion)
    assert _expectedEpoch == pricing.epoch # dev: epoch moved

    remainingPayment: uint256 = pricing.paymentCap - pricing.acceptedPayment
    assert _paymentAmount >= pricing.minPaymentAmount # dev: below minimum payment
    assert _paymentAmount <= remainingPayment # dev: exceeds epoch cap

    # calculate payout and enforce mint budget
    vaultConfig: cs.RipeGovVaultConfig = staticcall MissionControl(a.missionControl).ripeGovVaultConfig(a.ripeToken)
    payout: PayoutData = self._calculatePayout(
        _paymentAmount,
        pricing.rate,
        pricing.maxLockBonus,
        _requestedLock,
        vaultConfig,
    )

    assert payout.baseRipe != 0 # dev: zero payout
    assert payout.totalRipe >= _minRipeOut # dev: slippage

    budgetRemaining: uint256 = config.mintBudget - self.cumulativeMinted
    assert payout.totalRipe <= budgetRemaining # dev: mint budget

    # resolve lock destination
    coreRipeGovVaultId: uint256 = 0
    if payout.actualLock != 0:
        coreRipeGovVaultId = staticcall MissionControl(a.missionControl).coreRipeGovVaultId()
        assert coreRipeGovVaultId != 0 # dev: invalid vault id

    paymentBalanceBefore: uint256 = staticcall IERC20(PAYMENT_TOKEN).balanceOf(endaoFunds)

    # update accounting before the state-changing external calls below
    self._storePricingState(pricing)
    self.epochAcceptedPayment = pricing.acceptedPayment + _paymentAmount
    self.epochWeightedLateness = pricing.weightedLateness + _paymentAmount * self._getLatenessBps(block.number)
    self.cumulativeMinted += payout.totalRipe

    # collect exact payment amount
    assert extcall IERC20(PAYMENT_TOKEN).transferFrom(msg.sender, endaoFunds, _paymentAmount, default_return_value=True) # dev: payment failed
    paymentBalanceAfter: uint256 = staticcall IERC20(PAYMENT_TOKEN).balanceOf(endaoFunds)
    assert paymentBalanceAfter >= paymentBalanceBefore # dev: payment receipt mismatch
    assert paymentBalanceAfter - paymentBalanceBefore == _paymentAmount # dev: payment receipt mismatch

    # mint ripe and settle lock
    if payout.actualLock == 0:
        assert extcall RipeToken(a.ripeToken).mint(msg.sender, payout.totalRipe) # dev: mint failed
    else:
        ripeBalanceBefore: uint256 = staticcall IERC20(a.ripeToken).balanceOf(self)
        assert extcall RipeToken(a.ripeToken).mint(self, payout.totalRipe) # dev: mint failed
        assert extcall IERC20(a.ripeToken).approve(a.teller, payout.totalRipe, default_return_value=True) # dev: ripe approval failed
        depositedAmount: uint256 = extcall Teller(a.teller).depositFromTrusted(msg.sender, coreRipeGovVaultId, a.ripeToken, payout.totalRipe, payout.actualLock, a)
        assert depositedAmount == payout.totalRipe # dev: deposit mismatch
        assert staticcall IERC20(a.ripeToken).balanceOf(self) == ripeBalanceBefore # dev: ripe settlement mismatch
        assert extcall IERC20(a.ripeToken).approve(a.teller, 0, default_return_value=True) # dev: ripe approval failed

    log InstantBondPurchased(
        buyer=msg.sender,
        paymentAmount=_paymentAmount,
        baseRipe=payout.baseRipe,
        bonusRipe=payout.bonusRipe,
        bonusRatio=payout.bonusRatio,
        actualLock=payout.actualLock,
        totalRipe=payout.totalRipe,
        epochRate=pricing.rate,
        epoch=pricing.epoch,
        pricingConfigVersion=pricing.pricingConfigVersion,
        liveConfigVersion=configVersion,
        ripeGovVaultId=coreRipeGovVaultId,
    )
    return payout.totalRipe


###########
# Preview #
###########


@view
@external
def previewBuyNow(_paymentAmount: uint256, _requestedLock: uint256) -> InstantBondQuote:
    quote: InstantBondQuote = empty(InstantBondQuote)
    configVersion: uint256 = self.configVersion
    if configVersion == 0 or block.number < GENESIS_BLOCK:
        return quote

    config: InstantBondConfig = self.config
    pricing: PricingState = self._getPricingState(config, configVersion)
    remainingPayment: uint256 = pricing.paymentCap - pricing.acceptedPayment
    budgetRemaining: uint256 = config.mintBudget - self.cumulativeMinted

    quote.epoch = pricing.epoch
    quote.pricingConfigVersion = pricing.pricingConfigVersion
    quote.liveConfigVersion = configVersion
    quote.rate = pricing.rate
    quote.remainingPayment = remainingPayment
    quote.minPaymentAmount = pricing.minPaymentAmount
    quote.budgetRemaining = budgetRemaining

    if _paymentAmount < pricing.minPaymentAmount or _paymentAmount > remainingPayment:
        return quote

    a: addys.Addys = addys._getAddys()
    vaultConfig: cs.RipeGovVaultConfig = staticcall MissionControl(a.missionControl).ripeGovVaultConfig(a.ripeToken)
    payout: PayoutData = self._calculatePayout(
        _paymentAmount,
        pricing.rate,
        pricing.maxLockBonus,
        _requestedLock,
        vaultConfig,
    )

    quote.baseRipe = payout.baseRipe
    quote.bonusRatio = payout.bonusRatio
    quote.bonusRipe = payout.bonusRipe
    quote.actualLock = payout.actualLock
    quote.totalRipe = payout.totalRipe

    if payout.actualLock != 0:
        quote.canExitEarly = vaultConfig.lockTerms.canExit
        quote.exitFee = vaultConfig.lockTerms.exitFee
        if vaultConfig.shouldFreezeWhenBadDebt:
            quote.isExitFrozen = staticcall Ledger(a.ledger).badDebt() != 0

    if deptBasics.isPaused or not config.canBuyNow:
        return quote
    if not staticcall RipeHq(a.hq).canMintRipe(self):
        return quote
    if payout.baseRipe == 0 or payout.totalRipe > budgetRemaining:
        return quote

    quote.available = True
    return quote


###################
# Pricing Helpers #
###################


@pure
@internal
def _baseRateCeiling(_maxEffectiveRate: uint256, _maxLockBonus: uint256) -> uint256:
    return _maxEffectiveRate * HUNDRED_PERCENT // (HUNDRED_PERCENT + _maxLockBonus)


@view
@internal
def _getLaneEpoch(_blockNumber: uint256) -> uint256:
    return (_blockNumber - GENESIS_BLOCK) // EPOCH_LENGTH


@view
@internal
def _getLatenessBps(_blockNumber: uint256) -> uint256:
    if EPOCH_LENGTH == 1:
        return 0
    offset: uint256 = (_blockNumber - GENESIS_BLOCK) % EPOCH_LENGTH
    return offset * HUNDRED_PERCENT // (EPOCH_LENGTH - 1)


@view
@internal
def _getPricingState(_config: InstantBondConfig, _configVersion: uint256) -> PricingState:
    epoch: uint256 = self._getLaneEpoch(block.number)

    if not self.isInitialized:
        return PricingState(
            epoch=epoch,
            rate=_config.seedRate,
            paymentCap=_config.paymentCapPerEpoch,
            minPaymentAmount=_config.minPaymentAmount,
            maxLockBonus=_config.maxLockBonus,
            pricingConfigVersion=_configVersion,
            acceptedPayment=0,
            weightedLateness=0,
            timingEligible=(block.number - GENESIS_BLOCK) % EPOCH_LENGTH == 0,
            didInitialize=True,
            didRollover=False,
            fromEpoch=0,
            oldRate=0,
            previousAcceptedPayment=0,
            previousPaymentCap=0,
            previousWeightedLateness=0,
            previousTimingEligible=False,
            utilizationBps=0,
            effectiveAdjustmentBps=0,
            decaySteps=0,
            controllerRate=_config.seedRate,
        )

    pricing: PricingState = PricingState(
        epoch=self.currentEpoch,
        rate=self.epochRate,
        paymentCap=self.epochPaymentCap,
        minPaymentAmount=self.epochMinPaymentAmount,
        maxLockBonus=self.epochMaxLockBonus,
        pricingConfigVersion=self.epochPricingVersion,
        acceptedPayment=self.epochAcceptedPayment,
        weightedLateness=self.epochWeightedLateness,
        timingEligible=self.epochTimingEligible,
        didInitialize=False,
        didRollover=False,
        fromEpoch=0,
        oldRate=0,
        previousAcceptedPayment=0,
        previousPaymentCap=0,
        previousWeightedLateness=0,
        previousTimingEligible=False,
        utilizationBps=0,
        effectiveAdjustmentBps=0,
        decaySteps=0,
        controllerRate=self.epochRate,
    )
    if epoch <= self.currentEpoch:
        return pricing

    elapsed: uint256 = epoch - self.currentEpoch
    newCeiling: uint256 = self._baseRateCeiling(_config.maxEffectiveRate, _config.maxLockBonus)
    rate: uint256 = min(self.epochRate, newCeiling)
    utilizationBps: uint256 = 0
    effectiveAdjustmentBps: uint256 = 0
    decaySteps: uint256 = 0

    # Defensive-only under the current write sequence: a rollover is stored only
    # inside buyNow, which atomically records a positive minimum-sized purchase.
    # Keep this safe fallback in case future storage sequencing permits a committed
    # initialized epoch with zero accepted payment.
    if self.epochAcceptedPayment == 0: # pragma: no branch
        decaySteps = min(elapsed, _config.maxDecayEpochs)
    else:
        utilizationBps = self.epochAcceptedPayment * HUNDRED_PERCENT // self.epochPaymentCap

        if utilizationBps >= _config.uHighBps:
            utilizationStrength: uint256 = (utilizationBps - _config.uHighBps) * HUNDRED_PERCENT // (HUNDRED_PERCENT - _config.uHighBps)
            earlinessBps: uint256 = 0
            if self.epochTimingEligible:
                averageLatenessBps: uint256 = self.epochWeightedLateness // self.epochAcceptedPayment
                earlinessBps = HUNDRED_PERCENT - averageLatenessBps
            demandStrength: uint256 = utilizationStrength * earlinessBps // HUNDRED_PERCENT
            effectiveAdjustmentBps = _config.minUpBps + (_config.maxUpBps - _config.minUpBps) * demandStrength // HUNDRED_PERCENT
            rate = max(rate * HUNDRED_PERCENT // (HUNDRED_PERCENT + effectiveAdjustmentBps), MIN_BASE_RATE)
        elif utilizationBps <= _config.uLowBps:
            weaknessBps: uint256 = (_config.uLowBps - utilizationBps) * HUNDRED_PERCENT // _config.uLowBps
            effectiveAdjustmentBps = _config.minDownBps + (_config.maxDownBps - _config.minDownBps) * weaknessBps // HUNDRED_PERCENT
            rate = min(rate * HUNDRED_PERCENT // (HUNDRED_PERCENT - effectiveAdjustmentBps), newCeiling)

        decaySteps = min(elapsed - 1, _config.maxDecayEpochs)

    for i: uint256 in range(decaySteps, bound=MAX_DECAY_EPOCHS):
        rate = min(rate * HUNDRED_PERCENT // (HUNDRED_PERCENT - _config.decayBps), newCeiling)

    # preserve the ordinary result for auditability before applying an exact target
    controllerRate: uint256 = rate
    overrideRate: uint256 = self.rateOverride
    if overrideRate != 0:
        rate = overrideRate

    pricing.epoch = epoch
    pricing.rate = rate
    pricing.paymentCap = _config.paymentCapPerEpoch
    pricing.minPaymentAmount = _config.minPaymentAmount
    pricing.maxLockBonus = _config.maxLockBonus
    pricing.pricingConfigVersion = _configVersion
    pricing.acceptedPayment = 0
    pricing.weightedLateness = 0
    pricing.timingEligible = True
    pricing.didRollover = True
    pricing.fromEpoch = self.currentEpoch
    pricing.oldRate = self.epochRate
    pricing.previousAcceptedPayment = self.epochAcceptedPayment
    pricing.previousPaymentCap = self.epochPaymentCap
    pricing.previousWeightedLateness = self.epochWeightedLateness
    pricing.previousTimingEligible = self.epochTimingEligible
    pricing.utilizationBps = utilizationBps
    pricing.effectiveAdjustmentBps = effectiveAdjustmentBps
    pricing.decaySteps = decaySteps
    pricing.controllerRate = controllerRate
    return pricing


@internal
def _storePricingState(_pricing: PricingState):
    if not _pricing.didInitialize and not _pricing.didRollover:
        return

    self.currentEpoch = _pricing.epoch
    self.epochRate = _pricing.rate
    self.epochPaymentCap = _pricing.paymentCap
    self.epochMinPaymentAmount = _pricing.minPaymentAmount
    self.epochMaxLockBonus = _pricing.maxLockBonus
    self.epochPricingVersion = _pricing.pricingConfigVersion
    self.epochAcceptedPayment = _pricing.acceptedPayment
    self.epochWeightedLateness = _pricing.weightedLateness
    self.epochTimingEligible = _pricing.timingEligible

    # preview never reaches this stateful path; downstream failure reverts consumption
    if _pricing.didRollover and self.rateOverride != 0:
        targetRate: uint256 = self.rateOverride
        newOverrideVersion: uint256 = self.overrideVersion + 1
        self.rateOverride = 0
        self.overrideVersion = newOverrideVersion
        log RateOverrideApplied(
            newVersion=newOverrideVersion,
            fromEpoch=_pricing.fromEpoch,
            toEpoch=_pricing.epoch,
            targetRate=targetRate,
            controllerRate=_pricing.controllerRate,
        )

    if _pricing.didInitialize:
        self.isInitialized = True
        log EpochInitialized(
            epoch=_pricing.epoch,
            rate=_pricing.rate,
            paymentCap=_pricing.paymentCap,
            minPaymentAmount=_pricing.minPaymentAmount,
            maxLockBonus=_pricing.maxLockBonus,
            timingEligible=_pricing.timingEligible,
            pricingConfigVersion=_pricing.pricingConfigVersion,
        )
    else:
        log EpochRolled(
            fromEpoch=_pricing.fromEpoch,
            toEpoch=_pricing.epoch,
            oldRate=_pricing.oldRate,
            newRate=_pricing.rate,
            newPaymentCap=_pricing.paymentCap,
            newMinPaymentAmount=_pricing.minPaymentAmount,
            newMaxLockBonus=_pricing.maxLockBonus,
            previousAcceptedPayment=_pricing.previousAcceptedPayment,
            previousPaymentCap=_pricing.previousPaymentCap,
            previousWeightedLateness=_pricing.previousWeightedLateness,
            previousTimingEligible=_pricing.previousTimingEligible,
            utilizationBps=_pricing.utilizationBps,
            effectiveAdjustmentBps=_pricing.effectiveAdjustmentBps,
            decaySteps=_pricing.decaySteps,
            controllerRate=_pricing.controllerRate,
            pricingConfigVersion=_pricing.pricingConfigVersion,
        )


##################
# Payout Helpers #
##################


@view
@internal
def _calculatePayout(
    _paymentAmount: uint256,
    _rate: uint256,
    _maxLockBonus: uint256,
    _requestedLock: uint256,
    _vaultConfig: cs.RipeGovVaultConfig,
) -> PayoutData:
    actualLock: uint256 = 0
    bonusRatio: uint256 = 0
    minLock: uint256 = _vaultConfig.lockTerms.minLockDuration
    maxLock: uint256 = _vaultConfig.lockTerms.maxLockDuration

    if maxLock != 0 and maxLock >= minLock and _requestedLock >= minLock:
        actualLock = min(_requestedLock, maxLock)
        if maxLock == minLock:
            bonusRatio = _maxLockBonus
        else:
            bonusRatio = _maxLockBonus * (actualLock - minLock) // (maxLock - minLock)

    baseRipe: uint256 = _paymentAmount * _rate // PAYMENT_SCALE
    bonusRipe: uint256 = baseRipe * bonusRatio // HUNDRED_PERCENT
    return PayoutData(
        baseRipe=baseRipe,
        bonusRatio=bonusRatio,
        bonusRipe=bonusRipe,
        actualLock=actualLock,
        totalRipe=baseRipe + bonusRipe,
    )
