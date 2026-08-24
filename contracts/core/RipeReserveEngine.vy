#     RIPE Reserve Engine
#     Reserve-asset acquisition, isolated vesting, claims, and recovery
#
#     Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
#     Ripe Foundation (C) 2026

# @version 0.4.3
# pragma optimize codesize

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
import interfaces.RipeReserveEngine as ire

from interfaces import Department
from ethereum.ercs import IERC20
from ethereum.ercs import IERC20Detailed


interface RipeToken:
    def mint(_recipient: address, _amount: uint256) -> bool: nonpayable


interface RipeHq:
    def ripeToken() -> address: view
    def canMintRipe(_addr: address) -> bool: view
    def governance() -> address: view
    def numGovChanges() -> uint256: view
    def getAddrInfo(_regId: uint256) -> AddressInfo: view


flag ActiveLimitDirection:
    REDUCTION
    RAISE


struct AddressInfo:
    addr: address
    version: uint256
    lastModified: uint256
    description: String[64]


struct VestingPosition:
    beneficiary: address
    allocation: uint256
    claimed: uint256
    recovered: uint256
    purchaseBlock: uint256
    claimStartBlock: uint256
    fullyVestedBlock: uint256
    selectedFullVestingBlocks: uint256
    durationAdjustmentBps: uint256
    runId: uint256
    epoch: uint256
    epochConfigVersion: uint256
    basePayoutRate: uint256
    rateSource: uint8
    rateNonce: uint256
    positionVersion: uint256


struct ReserveEngineQuote:
    available: bool
    reasonFlags: uint256
    runId: uint256
    runRegistryVersion: uint256
    epochConfigVersion: uint256
    closureNonce: uint256
    capacityReductionNonce: uint256
    epoch: uint256
    epochEndBlock: uint256
    paymentToken: address
    proceedsRecipient: address
    paymentAmount: uint256
    paymentScale: uint256
    remainingPaymentCapacity: uint256
    controllerBasePayoutRate: uint256
    basePayoutRate: uint256
    rateSource: uint8
    rateNonce: uint256
    selectedFullVestingBlocks: uint256
    claimCliffBlocks: uint256
    durationAdjustmentBps: uint256
    baseAllocation: uint256
    adjustmentAllocation: uint256
    totalAllocation: uint256
    projectedClaimStartBlock: uint256
    projectedFullyVestedBlock: uint256
    remainingLineageCapacity: uint256
    remainingOutstandingCapacity: uint256
    isEscrowCovered: bool
    escrowCoverageDeficit: uint256
    overrideTargetEpoch: uint256
    overrideTargetBasePayoutRate: uint256


struct AcquisitionConstraints:
    expectedRunId: uint256
    expectedRunRegistryVersion: uint256
    expectedEpochConfigVersion: uint256
    expectedClosureNonce: uint256
    expectedCapacityReductionNonce: uint256
    expectedEpoch: uint256
    expectedPaymentToken: address
    expectedProceedsRecipient: address
    expectedBasePayoutRate: uint256
    expectedRateSource: uint8
    expectedRateNonce: uint256
    expectedDurationAdjustmentBps: uint256
    expectedTotalAllocation: uint256
    deadlineBlock: uint256


struct RateTransition:
    controllerBasePayoutRate: uint256
    utilizationBps: uint256
    effectivePriceAdjustmentBps: uint256
    decaySteps: uint256


event RipeAllocated:
    beneficiary: indexed(address)
    positionId: indexed(uint256)
    paymentToken: indexed(address)
    proceedsRecipient: address
    paymentAmount: uint256
    baseAllocation: uint256
    adjustmentAllocation: uint256
    totalAllocation: uint256
    controllerBasePayoutRate: uint256
    basePayoutRate: uint256
    durationAdjustmentBps: uint256
    claimStartBlock: uint256
    fullyVestedBlock: uint256
    runId: uint256
    runRegistryVersion: uint256
    epoch: uint256
    epochConfigVersion: uint256
    rateSource: uint8
    rateNonce: uint256


event VestedRipeClaimed:
    beneficiary: indexed(address)
    positionId: indexed(uint256)
    amount: uint256
    cumulativeClaimed: uint256
    cumulativeRecovered: uint256
    remainingOutstanding: uint256


event RipeRecoveryQueued:
    positionId: indexed(uint256)
    beneficiary: indexed(address)
    governanceRecipient: indexed(address)
    recoveryActionId: uint256
    amount: uint256
    expectedPositionVersion: uint256
    governanceGeneration: uint256
    executeAfterBlock: uint256
    expiresAtBlock: uint256


event RipeRecoveryTerminated:
    positionId: indexed(uint256)
    beneficiary: indexed(address)
    recoveryActionId: uint256
    reason: uint8


event RipeRecoveredForPosition:
    positionId: indexed(uint256)
    beneficiary: indexed(address)
    governanceRecipient: indexed(address)
    recoveryActionId: uint256
    amount: uint256
    cumulativeRecovered: uint256
    remainingOutstanding: uint256


event RipeSurplusRecovered:
    governanceRecipient: indexed(address)
    amount: uint256
    remainingSurplus: uint256


event EpochInitialized:
    epoch: indexed(uint256)
    controllerBasePayoutRate: uint256
    basePayoutRate: uint256
    paymentCap: uint256
    minPaymentAmount: uint256
    timingEligible: bool
    epochConfigVersion: uint256
    rateSource: uint8
    rateNonce: uint256


event EpochRolled:
    fromEpoch: indexed(uint256)
    toEpoch: indexed(uint256)
    oldBasePayoutRate: uint256
    controllerBasePayoutRate: uint256
    basePayoutRate: uint256
    newPaymentCap: uint256
    newMinPaymentAmount: uint256
    previousAcceptedPayment: uint256
    previousPaymentCap: uint256
    previousPaymentWeightedLateness: uint256
    previousTimingEligible: bool
    utilizationBps: uint256
    effectivePriceAdjustmentBps: uint256
    decaySteps: uint256
    epochConfigVersion: uint256
    rateSource: uint8
    rateNonce: uint256


event ReserveEngineConfigSet:
    currentConfigVersion: indexed(uint256)
    configHash: bytes32


event ReserveEngineRunTermsSet:
    runTermsVersion: indexed(uint256)
    runTermsHash: bytes32


event ReserveEngineStarted:
    runId: indexed(uint256)
    runRegistryVersion: indexed(uint256)
    genesisBlock: uint256
    currentConfigVersion: uint256
    runTermsVersion: uint256


event ReserveEngineStopped:
    runId: indexed(uint256)
    resultingClosureNonce: uint256


event ReserveEngineEnabledSet:
    isEngineEnabled: bool
    resultingClosureNonce: uint256


event ReserveEngineClosureAdvanced:
    operation: indexed(uint8)
    resultingClosureNonce: uint256


event ReserveEngineLimitsSet:
    activeLineageAllocationLimit: uint256
    activeOutstandingRipeLimit: uint256
    resultingCapacityReductionNonce: uint256


event RateOverrideInstalled:
    targetEpoch: indexed(uint256)
    targetBasePayoutRate: uint256
    runId: uint256
    runRegistryVersion: uint256
    installedConfigVersion: uint256
    closureNonce: uint256
    installedRateNonce: uint256


event RateOverrideApplied:
    epoch: indexed(uint256)
    controllerBasePayoutRate: uint256
    basePayoutRate: uint256
    observedRateNonce: uint256
    resultingRateNonce: uint256
    overrideApplicationsThisRun: uint256


event RateOverrideTerminated:
    targetEpoch: indexed(uint256)
    targetBasePayoutRate: uint256
    reason: uint8
    observedRateNonce: uint256
    resultingRateNonce: uint256


# controller and staged run configuration
currentConfig: ire.ReserveEngineConfig
stagedRunTerms: ire.ReserveEngineRunTerms
activeRunTerms: ire.ReserveEngineRunTerms

# lifecycle and committed controller state
isEngineEnabled: public(bool)
isRunning: public(bool)
epochState: public(ire.EpochSnapshot)
installedRateOverride: public(ire.RateOverride)
genesisBlock: public(uint256)
paymentToken: public(address)
paymentDecimals: public(uint8)
paymentScale: public(uint256)

# identities and limits
runId: public(uint256)
runRegistryVersion: public(uint256)
currentConfigVersion: public(uint256)
runTermsVersion: public(uint256)
closureNonce: public(uint256)
capacityReductionNonce: public(uint256)
rateNonce: public(uint256)
overrideApplicationsThisRun: public(uint256)
activeLineageAllocationLimit: public(uint256)
activeOutstandingRipeLimit: public(uint256)

# lifetime accounting
totalAllocated: public(uint256)
totalClaimed: public(uint256)
totalRecovered: public(uint256)

# isolated positions and recovery actions
positions: public(HashMap[uint256, VestingPosition])
pendingRipeRecoveries: public(HashMap[uint256, ire.PendingRipeRecovery])
pendingRecoveryForPosition: public(HashMap[uint256, uint256])
nextPositionId: uint256
nextRecoveryActionId: uint256

# pinned instance identity
RIPE_HQ: immutable(address)
PINNED_RIPE: immutable(address)

# immutable bounds
HARD_LINEAGE_ALLOCATION_CAP: immutable(uint256)
PRIOR_LINEAGE_ALLOCATED: immutable(uint256)
MIN_CLAIM_CLIFF_BLOCKS: immutable(uint256)
MIN_LINEAR_VESTING_BLOCKS: immutable(uint256)
MAX_VESTING_HORIZON: immutable(uint256)
MIN_BASE_ALLOCATION: immutable(uint256)
MIN_EPOCH_LENGTH: immutable(uint256)
MAX_EPOCH_LENGTH: immutable(uint256)
MAX_GENESIS_LEAD_BLOCKS: immutable(uint256)
RECOVERY_DORMANCY_BLOCKS: immutable(uint256)
RECOVERY_NOTICE_BLOCKS: immutable(uint256)
RECOVERY_EXECUTION_WINDOW_BLOCKS: immutable(uint256)

HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%
MAX_DURATION_ADJUSTMENT_BPS: constant(uint256) = 100_00
MAX_DURATION_GRID_POINTS: constant(uint256) = 256
MAX_PRICE_STEP_BPS: constant(uint256) = 100_00
MAX_DECAY_EPOCHS: constant(uint256) = 32
MAX_PAYMENT_DECIMALS: constant(uint8) = 73
MIN_BASE_RATE: constant(uint256) = 10_000
RIPE_RESERVE_ENGINE_ID: constant(uint256) = 26
MAX_UINT128: constant(uint256) = 2 ** 128 - 1

# quote reason bits
NOT_RUNNING: constant(uint256) = 1
ENGINE_DISABLED: constant(uint256) = 2
ENGINE_PAUSED: constant(uint256) = 4
BEFORE_GENESIS: constant(uint256) = 8
INVALID_CONFIGURATION: constant(uint256) = 16
NOT_CURRENT_INSTANCE: constant(uint256) = 32
NO_MINT_AUTHORIZATION: constant(uint256) = 64
ESCROW_COVERAGE_DEFICIT: constant(uint256) = 128
INVALID_DURATION: constant(uint256) = 256
BELOW_MINIMUM_PAYMENT: constant(uint256) = 512
PAYMENT_CAP_EXCEEDED: constant(uint256) = 1024
LINEAGE_CAP_EXCEEDED: constant(uint256) = 2048
OUTSTANDING_CAP_EXCEEDED: constant(uint256) = 4096

# fixed rate sources
RATE_SOURCE_NONE: constant(uint8) = 0
RATE_SOURCE_SEED: constant(uint8) = 1
RATE_SOURCE_CONTROLLER: constant(uint8) = 2
RATE_SOURCE_OVERRIDE: constant(uint8) = 3

# fixed position-recovery terminal reasons
RECOVERY_BENEFICIARY_ACTIVITY: constant(uint8) = 1
RECOVERY_CANCELLED: constant(uint8) = 2
RECOVERY_EXPIRED: constant(uint8) = 3
RECOVERY_POSITION_STALE: constant(uint8) = 4
RECOVERY_GOVERNANCE_ROTATED: constant(uint8) = 5

# fixed closure operations
CLOSURE_PAUSE: constant(uint8) = 1
CLOSURE_DISABLE: constant(uint8) = 2
CLOSURE_STOP: constant(uint8) = 3

# fixed override terminal reasons
OVERRIDE_CANCELLED: constant(uint8) = 1
OVERRIDE_MISSED: constant(uint8) = 2
OVERRIDE_DEVIATION_INVALID: constant(uint8) = 3
OVERRIDE_CONFIG_CHANGED: constant(uint8) = 4
OVERRIDE_PAUSED: constant(uint8) = 5
OVERRIDE_DISABLED: constant(uint8) = 6
OVERRIDE_STOPPED: constant(uint8) = 7
OVERRIDE_NEW_RUN: constant(uint8) = 8


@deploy
def __init__(
    _ripeHq: address,
    _ripeToken: address,
    _initialConfig: ire.ReserveEngineConfig,
    _initialRunTerms: ire.ReserveEngineRunTerms,
    _hardLineageAllocationCap: uint256,
    _priorLineageAllocated: uint256,
    _minClaimCliffBlocks: uint256,
    _minLinearVestingBlocks: uint256,
    _maxVestingHorizon: uint256,
    _minBaseAllocation: uint256,
    _minEpochLength: uint256,
    _maxEpochLength: uint256,
    _maxGenesisLeadBlocks: uint256,
    _recoveryDormancyBlocks: uint256,
    _recoveryNoticeBlocks: uint256,
    _recoveryExecutionWindowBlocks: uint256,
):
    addys.__init__(_ripeHq)
    deptBasics.__init__(True, False, True) # starts paused; can mint ripe only

    assert _ripeHq != empty(address) and _ripeHq.is_contract # dev: invalid ripe hq
    assert _ripeToken != empty(address) and _ripeToken.is_contract # dev: invalid ripe token
    assert staticcall RipeHq(_ripeHq).ripeToken() == _ripeToken # dev: ripe token mismatch

    assert _minClaimCliffBlocks != 0 # dev: invalid claim cliff floor
    assert _minLinearVestingBlocks >= 2 # dev: invalid linear vesting floor
    assert _minLinearVestingBlocks <= _maxVestingHorizon # dev: invalid vesting bounds
    assert _maxVestingHorizon <= MAX_UINT128 # dev: invalid vesting horizon
    assert _minBaseAllocation != 0 # dev: invalid allocation floor
    assert _minEpochLength != 0 and _minEpochLength < _maxEpochLength # dev: invalid epoch bounds
    assert _maxEpochLength <= max_value(uint256) // HUNDRED_PERCENT + 1 # dev: unsafe epoch bound
    assert _maxGenesisLeadBlocks != 0 # dev: invalid genesis lead
    assert _priorLineageAllocated <= _hardLineageAllocationCap # dev: invalid lineage
    assert _recoveryDormancyBlocks != 0 # dev: invalid recovery dormancy
    assert _recoveryNoticeBlocks != 0 # dev: invalid recovery notice
    assert _recoveryExecutionWindowBlocks != 0 # dev: invalid recovery window

    RIPE_HQ = _ripeHq
    PINNED_RIPE = _ripeToken
    HARD_LINEAGE_ALLOCATION_CAP = _hardLineageAllocationCap
    PRIOR_LINEAGE_ALLOCATED = _priorLineageAllocated
    MIN_CLAIM_CLIFF_BLOCKS = _minClaimCliffBlocks
    MIN_LINEAR_VESTING_BLOCKS = _minLinearVestingBlocks
    MAX_VESTING_HORIZON = _maxVestingHorizon
    MIN_BASE_ALLOCATION = _minBaseAllocation
    MIN_EPOCH_LENGTH = _minEpochLength
    MAX_EPOCH_LENGTH = _maxEpochLength
    MAX_GENESIS_LEAD_BLOCKS = _maxGenesisLeadBlocks
    RECOVERY_DORMANCY_BLOCKS = _recoveryDormancyBlocks
    RECOVERY_NOTICE_BLOCKS = _recoveryNoticeBlocks
    RECOVERY_EXECUTION_WINDOW_BLOCKS = _recoveryExecutionWindowBlocks

    isValidPayment: bool = False
    initialDecimals: uint8 = 0
    initialScale: uint256 = 0
    isValidPayment, initialDecimals, initialScale = self._getPaymentDetails(_initialRunTerms.paymentToken)
    assert isValidPayment # dev: invalid payment token
    assert self._isValidRunTermsCore(_initialRunTerms) # dev: invalid run terms
    assert self._isValidConfigFor(_initialConfig, _initialRunTerms, initialScale) # dev: invalid config

    self.currentConfig = _initialConfig
    self.stagedRunTerms = _initialRunTerms
    self.currentConfigVersion = 1
    self.runTermsVersion = 1
    self.activeLineageAllocationLimit = _priorLineageAllocated
    self.activeOutstandingRipeLimit = 0
    self.nextPositionId = 1
    self.nextRecoveryActionId = 1

    log ReserveEngineConfigSet(currentConfigVersion=1, configHash=self._configHash(_initialConfig))
    log ReserveEngineRunTermsSet(runTermsVersion=1, runTermsHash=self._runTermsHash(_initialRunTerms))


###################
# Pinned Identity #
###################


@view
@external
def ripeHq() -> address:
    return RIPE_HQ


@view
@external
def pinnedRipe() -> address:
    return PINNED_RIPE


#######################
# Department Controls #
#######################


@view
@external
def isPaused() -> bool:
    return deptBasics.isPaused


@nonreentrant
@external
def pause(_shouldPause: bool):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert _shouldPause != deptBasics.isPaused # dev: no change

    if _shouldPause:
        self._terminateInstalledOverride(OVERRIDE_PAUSED)
        self.closureNonce += 1
        log ReserveEngineClosureAdvanced(operation=CLOSURE_PAUSE, resultingClosureNonce=self.closureNonce)

    deptBasics.isPaused = _shouldPause
    log deptBasics.DepartmentPauseModified(isPaused=_shouldPause)


@nonreentrant
@external
def recoverFunds(_recipient: address, _asset: address):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert _recipient != empty(address) and _asset != empty(address) # dev: invalid recovery
    assert _asset != PINNED_RIPE # dev: pinned ripe
    deptBasics._recoverFunds(_recipient, _asset)


@nonreentrant
@external
def recoverFundsMany(_recipient: address, _assets: DynArray[address, 20]):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert _recipient != empty(address) # dev: invalid recipient
    for asset: address in _assets:
        assert asset != empty(address) and asset != PINNED_RIPE # dev: invalid recovery asset
    for recoverAsset: address in _assets:
        deptBasics._recoverFunds(_recipient, recoverAsset)


#########################
# Config and Run Terms  #
#########################


@view
@external
def getConfig() -> ire.ReserveEngineConfig:
    return self.currentConfig


@view
@external
def getRunTerms() -> ire.ReserveEngineRunTerms:
    return self.stagedRunTerms


@view
@external
def getActiveRunTerms() -> ire.ReserveEngineRunTerms:
    return self.activeRunTerms


@view
@external
def configHash() -> bytes32:
    return self._configHash(self.currentConfig)


@view
@external
def runTermsHash() -> bytes32:
    return self._runTermsHash(self.stagedRunTerms)


@pure
@internal
def _configHash(_config: ire.ReserveEngineConfig) -> bytes32:
    return keccak256(_abi_encode(
        _config.paymentCapPerEpoch,
        _config.minPaymentAmount,
        _config.maxAllInPayoutRate,
        _config.seedBasePayoutRate,
        _config.uHighBps,
        _config.uLowBps,
        _config.minPriceIncreaseBps,
        _config.maxPriceIncreaseBps,
        _config.minPriceDecreaseBps,
        _config.maxPriceDecreaseBps,
        _config.decayBps,
        _config.maxDecayEpochs,
        _config.maxOverrideDeviationBps,
        _config.maxOverrideLeadEpochs,
    ))


@pure
@internal
def _runTermsHash(_runTerms: ire.ReserveEngineRunTerms) -> bytes32:
    return keccak256(_abi_encode(
        _runTerms.paymentToken,
        _runTerms.epochLength,
        _runTerms.claimCliffBlocks,
        _runTerms.minFullVestingBlocks,
        _runTerms.maxFullVestingBlocks,
        _runTerms.durationStepBlocks,
        _runTerms.maxDurationAdjustmentBps,
        _runTerms.maxOverrideApplicationsPerRun,
    ))


@view
@external
def isValidConfig(_config: ire.ReserveEngineConfig) -> bool:
    return self._isValidConfigWithApplicableTerms(_config)


@nonreentrant
@external
def setConfig(_newConfig: ire.ReserveEngineConfig, _expectedCurrentConfigVersion: uint256):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert _expectedCurrentConfigVersion == self.currentConfigVersion # dev: config moved
    assert self._isValidConfigWithApplicableTerms(_newConfig) # dev: invalid config

    self._terminateInstalledOverride(OVERRIDE_CONFIG_CHANGED)
    self.currentConfig = _newConfig
    self.currentConfigVersion += 1
    log ReserveEngineConfigSet(
        currentConfigVersion=self.currentConfigVersion,
        configHash=self._configHash(_newConfig),
    )


@view
@external
def isValidRunTerms(_runTerms: ire.ReserveEngineRunTerms) -> bool:
    if self.isRunning:
        return False
    isValidPayment: bool = False
    decimals: uint8 = 0
    scale: uint256 = 0
    isValidPayment, decimals, scale = self._getPaymentDetails(_runTerms.paymentToken)
    if not isValidPayment or not self._isValidRunTermsCore(_runTerms):
        return False
    return self._isValidConfigFor(self.currentConfig, _runTerms, scale)


@nonreentrant
@external
def setRunTerms(_newRunTerms: ire.ReserveEngineRunTerms, _expectedRunTermsVersion: uint256):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert not self.isRunning # dev: running
    assert _expectedRunTermsVersion == self.runTermsVersion # dev: run terms moved

    isValidPayment: bool = False
    decimals: uint8 = 0
    scale: uint256 = 0
    isValidPayment, decimals, scale = self._getPaymentDetails(_newRunTerms.paymentToken)
    assert isValidPayment # dev: invalid payment token
    assert self._isValidRunTermsCore(_newRunTerms) # dev: invalid run terms
    assert self._isValidConfigFor(self.currentConfig, _newRunTerms, scale) # dev: invalid config

    self._terminateInstalledOverride(OVERRIDE_CONFIG_CHANGED)
    self.stagedRunTerms = _newRunTerms
    self.runTermsVersion += 1
    log ReserveEngineRunTermsSet(
        runTermsVersion=self.runTermsVersion,
        runTermsHash=self._runTermsHash(_newRunTerms),
    )


########################
# Lifecycle and Limits #
########################


@nonreentrant
@external
def setEngineEnabled(_shouldEnable: bool, _expectedClosureNonce: uint256):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert _expectedClosureNonce == self.closureNonce # dev: closure moved
    assert _shouldEnable != self.isEngineEnabled # dev: no change

    if not _shouldEnable:
        self._terminateInstalledOverride(OVERRIDE_DISABLED)
        self.closureNonce += 1
        log ReserveEngineClosureAdvanced(operation=CLOSURE_DISABLE, resultingClosureNonce=self.closureNonce)

    self.isEngineEnabled = _shouldEnable
    log ReserveEngineEnabledSet(
        isEngineEnabled=_shouldEnable,
        resultingClosureNonce=self.closureNonce,
    )


@view
@external
def isValidActiveLimits(_newLineageLimit: uint256, _newOutstandingLimit: uint256) -> bool:
    return self._activeLimitDirection(_newLineageLimit, _newOutstandingLimit) != empty(ActiveLimitDirection)


@nonreentrant
@external
def setActiveLimits(
    _newLineageLimit: uint256,
    _newOutstandingLimit: uint256,
    _expectedCurrentLineageLimit: uint256,
    _expectedCurrentOutstandingLimit: uint256,
    _expectedCapacityReductionNonce: uint256,
):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert _expectedCurrentLineageLimit == self.activeLineageAllocationLimit # dev: lineage limit moved
    assert _expectedCurrentOutstandingLimit == self.activeOutstandingRipeLimit # dev: outstanding limit moved
    assert _expectedCapacityReductionNonce == self.capacityReductionNonce # dev: capacity moved

    direction: ActiveLimitDirection = self._activeLimitDirection(_newLineageLimit, _newOutstandingLimit)
    assert direction != empty(ActiveLimitDirection) # dev: invalid limit direction
    if direction == ActiveLimitDirection.REDUCTION:
        self.capacityReductionNonce += 1

    self.activeLineageAllocationLimit = _newLineageLimit
    self.activeOutstandingRipeLimit = _newOutstandingLimit
    log ReserveEngineLimitsSet(
        activeLineageAllocationLimit=_newLineageLimit,
        activeOutstandingRipeLimit=_newOutstandingLimit,
        resultingCapacityReductionNonce=self.capacityReductionNonce,
    )


@view
@internal
def _activeLimitDirection(_newLineageLimit: uint256, _newOutstandingLimit: uint256) -> ActiveLimitDirection:
    if _newLineageLimit > HARD_LINEAGE_ALLOCATION_CAP:
        return empty(ActiveLimitDirection)

    currentLineage: uint256 = self.activeLineageAllocationLimit
    currentOutstanding: uint256 = self.activeOutstandingRipeLimit
    isReduction: bool = (
        _newLineageLimit <= currentLineage
        and _newOutstandingLimit <= currentOutstanding
        and (_newLineageLimit < currentLineage or _newOutstandingLimit < currentOutstanding)
    )
    if isReduction:
        return ActiveLimitDirection.REDUCTION

    isRaise: bool = (
        _newLineageLimit >= currentLineage
        and _newOutstandingLimit >= currentOutstanding
        and (_newLineageLimit > currentLineage or _newOutstandingLimit > currentOutstanding)
    )
    return ActiveLimitDirection.RAISE if isRaise else empty(ActiveLimitDirection)


@view
@external
def isValidStart(_genesisBlock: uint256) -> bool:
    terms: ire.ReserveEngineRunTerms = self.stagedRunTerms
    isValidPayment: bool = False
    decimals: uint8 = 0
    scale: uint256 = 0
    isValidPayment, decimals, scale = self._getPaymentDetails(terms.paymentToken)
    slot: AddressInfo = staticcall RipeHq(RIPE_HQ).getAddrInfo(RIPE_RESERVE_ENGINE_ID)
    return self._isValidStart(_genesisBlock, terms, isValidPayment, scale, slot)


@nonreentrant
@external
def start(
    _genesisBlock: uint256,
    _expectedRegistryVersion: uint256,
    _expectedCurrentConfigVersion: uint256,
    _expectedRunTermsVersion: uint256,
    _expectedClosureNonce: uint256,
):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert not self.isRunning # dev: already running
    assert _expectedCurrentConfigVersion == self.currentConfigVersion # dev: config moved
    assert _expectedRunTermsVersion == self.runTermsVersion # dev: run terms moved
    assert _expectedClosureNonce == self.closureNonce # dev: closure moved

    terms: ire.ReserveEngineRunTerms = self.stagedRunTerms
    isValidPayment: bool = False
    decimals: uint8 = 0
    scale: uint256 = 0
    isValidPayment, decimals, scale = self._getPaymentDetails(terms.paymentToken)

    slot: AddressInfo = staticcall RipeHq(RIPE_HQ).getAddrInfo(RIPE_RESERVE_ENGINE_ID)
    assert slot.addr == self and slot.version == _expectedRegistryVersion # dev: engine identity moved
    assert self._isValidStart(_genesisBlock, terms, isValidPayment, scale, slot) # dev: invalid start

    self._terminateInstalledOverride(OVERRIDE_NEW_RUN)
    self.runId += 1
    self.runRegistryVersion = slot.version
    self.activeRunTerms = terms
    self.paymentToken = terms.paymentToken
    self.paymentDecimals = decimals
    self.paymentScale = scale
    self.genesisBlock = block.number if _genesisBlock == 0 else _genesisBlock
    self.isRunning = True
    self.epochState = empty(ire.EpochSnapshot)
    self.overrideApplicationsThisRun = 0

    log ReserveEngineStarted(
        runId=self.runId,
        runRegistryVersion=slot.version,
        genesisBlock=self.genesisBlock,
        currentConfigVersion=self.currentConfigVersion,
        runTermsVersion=self.runTermsVersion,
    )


@nonreentrant
@external
def stop():
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert self.isRunning # dev: not running

    self._terminateInstalledOverride(OVERRIDE_STOPPED)
    self.isRunning = False
    self.epochState = empty(ire.EpochSnapshot)
    self.genesisBlock = 0
    self.closureNonce += 1

    log ReserveEngineStopped(runId=self.runId, resultingClosureNonce=self.closureNonce)
    log ReserveEngineClosureAdvanced(operation=CLOSURE_STOP, resultingClosureNonce=self.closureNonce)


############################
# Configuration Validation #
############################


@view
@internal
def _getPaymentDetails(_token: address) -> (bool, uint8, uint256):
    if _token == empty(address) or not _token.is_contract or _token == PINNED_RIPE:
        return False, 0, 0
    decimals: uint8 = staticcall IERC20Detailed(_token).decimals()
    if decimals > MAX_PAYMENT_DECIMALS:
        return False, decimals, 0
    return True, decimals, 10 ** convert(decimals, uint256)


@view
@internal
def _isValidConfigWithApplicableTerms(_config: ire.ReserveEngineConfig) -> bool:
    terms: ire.ReserveEngineRunTerms = self.activeRunTerms if self.isRunning else self.stagedRunTerms
    isValidPayment: bool = False
    decimals: uint8 = 0
    scale: uint256 = 0
    isValidPayment, decimals, scale = self._getPaymentDetails(terms.paymentToken)
    if not isValidPayment or not self._isValidRunTermsCore(terms):
        return False
    if self.isRunning:
        if terms.paymentToken != self.paymentToken:
            return False
        if decimals != self.paymentDecimals or scale != self.paymentScale:
            return False
    return self._isValidConfigFor(_config, terms, scale)


@view
@internal
def _isValidConfigFor(
    _config: ire.ReserveEngineConfig,
    _runTerms: ire.ReserveEngineRunTerms,
    _paymentScale: uint256,
) -> bool:
    if _config.uLowBps == 0 or _config.uLowBps >= _config.uHighBps:
        return False
    if _config.uHighBps >= HUNDRED_PERCENT:
        return False

    if _config.minPriceIncreaseBps == 0 or _config.minPriceIncreaseBps > _config.maxPriceIncreaseBps:
        return False
    if _config.maxPriceIncreaseBps > MAX_PRICE_STEP_BPS:
        return False
    if _config.minPriceDecreaseBps == 0 or _config.minPriceDecreaseBps > _config.maxPriceDecreaseBps:
        return False

    if _config.decayBps == 0 or _config.decayBps >= HUNDRED_PERCENT:
        return False
    if _config.maxPriceDecreaseBps > _config.decayBps:
        return False
    if _config.maxPriceDecreaseBps >= _config.minPriceIncreaseBps:
        return False

    if (
        (HUNDRED_PERCENT + _config.minPriceIncreaseBps)
        * (HUNDRED_PERCENT - _config.decayBps)
        < HUNDRED_PERCENT * HUNDRED_PERCENT
    ):
        return False

    if _config.maxDecayEpochs == 0 or _config.maxDecayEpochs > MAX_DECAY_EPOCHS:
        return False
    if _config.maxAllInPayoutRate == 0:
        return False
    if _config.maxAllInPayoutRate > max_value(uint256) // HUNDRED_PERCENT:
        return False

    if _paymentScale == 0:
        return False
    if _config.paymentCapPerEpoch < _paymentScale:
        return False
    if _config.paymentCapPerEpoch > max_value(uint256) // HUNDRED_PERCENT:
        return False
    if _config.minPaymentAmount < _paymentScale or _config.minPaymentAmount > _config.paymentCapPerEpoch:
        return False
    if _config.maxAllInPayoutRate > max_value(uint256) // _config.paymentCapPerEpoch:
        return False
    if _config.maxOverrideDeviationBps > HUNDRED_PERCENT:
        return False

    ceiling: uint256 = self._baseRateCeilingFor(
        _config.maxAllInPayoutRate,
        _runTerms.maxDurationAdjustmentBps,
    )
    if ceiling < MIN_BASE_RATE:
        return False
    if _config.seedBasePayoutRate < MIN_BASE_RATE or _config.seedBasePayoutRate > ceiling:
        return False

    minimumBaseAllocation: uint256 = _config.minPaymentAmount * MIN_BASE_RATE // _paymentScale
    if minimumBaseAllocation < MIN_BASE_ALLOCATION:
        return False

    maximumBaseAllocation: uint256 = _config.paymentCapPerEpoch * ceiling // _paymentScale
    maximumAdjustment: uint256 = self._mulBps(
        maximumBaseAllocation,
        _runTerms.maxDurationAdjustmentBps,
    )
    if maximumBaseAllocation > max_value(uint256) - maximumAdjustment:
        return False
    maximumTotalAllocation: uint256 = maximumBaseAllocation + maximumAdjustment
    maximumAllInAllocation: uint256 = (
        _config.paymentCapPerEpoch * _config.maxAllInPayoutRate // _paymentScale
    )
    if maximumTotalAllocation > maximumAllInAllocation:
        return False

    return True


@view
@internal
def _isValidRunTermsCore(_runTerms: ire.ReserveEngineRunTerms) -> bool:
    if _runTerms.epochLength < MIN_EPOCH_LENGTH or _runTerms.epochLength > MAX_EPOCH_LENGTH:
        return False

    cliff: uint256 = _runTerms.claimCliffBlocks
    minimumDuration: uint256 = _runTerms.minFullVestingBlocks
    maximumDuration: uint256 = _runTerms.maxFullVestingBlocks
    step: uint256 = _runTerms.durationStepBlocks
    maximumAdjustment: uint256 = _runTerms.maxDurationAdjustmentBps

    if cliff < MIN_CLAIM_CLIFF_BLOCKS:
        return False
    if cliff > max_value(uint256) - MIN_LINEAR_VESTING_BLOCKS:
        return False
    if minimumDuration < cliff + MIN_LINEAR_VESTING_BLOCKS:
        return False
    if maximumDuration <= minimumDuration or maximumDuration > MAX_VESTING_HORIZON:
        return False
    if step == 0:
        return False

    durationRange: uint256 = maximumDuration - minimumDuration
    if durationRange % step != 0:
        return False
    if maximumAdjustment == 0 or maximumAdjustment > MAX_DURATION_ADJUSTMENT_BPS:
        return False

    minimumLinearBlocks: uint256 = minimumDuration - cliff
    if maximumAdjustment * minimumLinearBlocks >= HUNDRED_PERCENT * durationRange:
        return False

    gridPointCount: uint256 = durationRange // step + 1
    if gridPointCount > MAX_DURATION_GRID_POINTS:
        return False

    for i: uint256 in range(MAX_DURATION_GRID_POINTS):
        if i + 1 >= gridPointCount:
            break

        durationOne: uint256 = minimumDuration + i * step
        durationTwo: uint256 = durationOne + step
        linearOne: uint256 = durationOne - cliff
        linearTwo: uint256 = durationTwo - cliff
        multiplierOne: uint256 = HUNDRED_PERCENT + self._durationAdjustmentForTerms(durationOne, _runTerms)
        multiplierTwo: uint256 = HUNDRED_PERCENT + self._durationAdjustmentForTerms(durationTwo, _runTerms)

        left: uint256 = multiplierOne * linearTwo
        right: uint256 = multiplierTwo * linearOne
        if left <= right:
            return False
        margin: uint256 = left - right
        required: uint256 = HUNDRED_PERCENT * linearTwo
        # If MIN_BASE_ALLOCATION * margin would overflow, its mathematical value
        # already exceeds bounded `required`.
        if MIN_BASE_ALLOCATION <= max_value(uint256) // margin:
            if MIN_BASE_ALLOCATION * margin < required:
                return False

    return True


@view
@internal
def _isValidStart(
    _genesisBlock: uint256,
    _terms: ire.ReserveEngineRunTerms,
    _isValidPayment: bool,
    _paymentScale: uint256,
    _slot: AddressInfo,
) -> bool:
    if self.isRunning:
        return False
    if _genesisBlock > block.number and _genesisBlock - block.number > MAX_GENESIS_LEAD_BLOCKS:
        return False

    if _slot.addr != self or _slot.version == 0:
        return False
    if staticcall RipeHq(RIPE_HQ).ripeToken() != PINNED_RIPE:
        return False

    if not _isValidPayment or not self._isValidRunTermsCore(_terms):
        return False
    return self._isValidConfigFor(self.currentConfig, _terms, _paymentScale)


@view
@internal
def _hasCoherentActiveRunBinding() -> bool:
    # Full config and run qualification is maintained by constructor and governed transitions.
    if self.runId == 0 or self.runRegistryVersion == 0:
        return False
    if self.currentConfigVersion == 0 or self.runTermsVersion == 0:
        return False

    terms: ire.ReserveEngineRunTerms = self.activeRunTerms
    if terms.paymentToken == empty(address) or terms.paymentToken != self.paymentToken:
        return False

    isValidPayment: bool = False
    decimals: uint8 = 0
    scale: uint256 = 0
    isValidPayment, decimals, scale = self._getPaymentDetails(terms.paymentToken)
    if not isValidPayment:
        return False
    return decimals == self.paymentDecimals and scale == self.paymentScale


############################
# Duration and Rate Helpers #
############################


@view
@external
def isValidDuration(_selectedFullVestingBlocks: uint256) -> bool:
    terms: ire.ReserveEngineRunTerms = self.activeRunTerms if self.isRunning else self.stagedRunTerms
    return self._isValidDurationFor(_selectedFullVestingBlocks, terms)


@view
@external
def durationAdjustmentBps(_selectedFullVestingBlocks: uint256) -> uint256:
    terms: ire.ReserveEngineRunTerms = self.activeRunTerms if self.isRunning else self.stagedRunTerms
    if not self._isValidDurationFor(_selectedFullVestingBlocks, terms):
        return 0
    return self._durationAdjustmentForTerms(_selectedFullVestingBlocks, terms)


@pure
@internal
def _isValidDurationFor(
    _selectedFullVestingBlocks: uint256,
    _runTerms: ire.ReserveEngineRunTerms,
) -> bool:
    if _selectedFullVestingBlocks < _runTerms.minFullVestingBlocks:
        return False
    if _selectedFullVestingBlocks > _runTerms.maxFullVestingBlocks:
        return False
    if _runTerms.durationStepBlocks == 0:
        return False
    return (
        (_selectedFullVestingBlocks - _runTerms.minFullVestingBlocks)
        % _runTerms.durationStepBlocks
        == 0
    )


@pure
@internal
def _durationAdjustmentForTerms(
    _selectedFullVestingBlocks: uint256,
    _runTerms: ire.ReserveEngineRunTerms,
) -> uint256:
    return (
        _runTerms.maxDurationAdjustmentBps
        * (_selectedFullVestingBlocks - _runTerms.minFullVestingBlocks)
        // (_runTerms.maxFullVestingBlocks - _runTerms.minFullVestingBlocks)
    )


@view
@external
def baseRateCeiling() -> uint256:
    terms: ire.ReserveEngineRunTerms = self.activeRunTerms if self.isRunning else self.stagedRunTerms
    return self._baseRateCeilingFor(
        self.currentConfig.maxAllInPayoutRate,
        terms.maxDurationAdjustmentBps,
    )


@pure
@internal
def _baseRateCeilingFor(_maxAllInPayoutRate: uint256, _maxDurationAdjustmentBps: uint256) -> uint256:
    return (
        _maxAllInPayoutRate * HUNDRED_PERCENT
        // (HUNDRED_PERCENT + _maxDurationAdjustmentBps)
    )


@pure
@internal
def _mulBps(_amount: uint256, _bps: uint256) -> uint256:
    whole: uint256 = _amount // HUNDRED_PERCENT
    remainder: uint256 = _amount % HUNDRED_PERCENT
    return whole * _bps + remainder * _bps // HUNDRED_PERCENT


#################
# Rate Override #
#################


@view
@external
def isValidRateOverride(_targetBasePayoutRate: uint256, _targetEpoch: uint256) -> bool:
    return self._isValidRateOverride(_targetBasePayoutRate, _targetEpoch)


@view
@internal
def _isValidRateOverride(_targetBasePayoutRate: uint256, _targetEpoch: uint256) -> bool:
    if not self.isRunning or not self.isEngineEnabled or deptBasics.isPaused:
        return False
    if not self._hasCoherentActiveRunBinding():
        return False
    if self.installedRateOverride.targetBasePayoutRate != 0:
        return False

    slot: AddressInfo = staticcall RipeHq(RIPE_HQ).getAddrInfo(RIPE_RESERVE_ENGINE_ID)
    if slot.addr != self or slot.version != self.runRegistryVersion:
        return False

    overrideBudget: uint256 = self.activeRunTerms.maxOverrideApplicationsPerRun
    if overrideBudget == 0 or self.overrideApplicationsThisRun >= overrideBudget:
        return False

    ceiling: uint256 = self._baseRateCeilingFor(
        self.currentConfig.maxAllInPayoutRate,
        self.activeRunTerms.maxDurationAdjustmentBps,
    )
    if _targetBasePayoutRate < MIN_BASE_RATE or _targetBasePayoutRate > ceiling:
        return False

    projectedEpoch: uint256 = self._projectedEpoch()
    if _targetEpoch < projectedEpoch:
        return False
    if _targetEpoch - projectedEpoch > self.currentConfig.maxOverrideLeadEpochs:
        return False

    committed: ire.EpochSnapshot = self.epochState
    if committed.basePayoutRate != 0 and _targetEpoch <= committed.epoch:
        return False
    return True


@nonreentrant
@external
def installRateOverride(
    _targetBasePayoutRate: uint256,
    _targetEpoch: uint256,
    _expectedRunId: uint256,
    _expectedRunRegistryVersion: uint256,
    _expectedCurrentConfigVersion: uint256,
    _expectedClosureNonce: uint256,
    _expectedRateNonce: uint256,
):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert _expectedRunId == self.runId # dev: run moved
    assert _expectedRunRegistryVersion == self.runRegistryVersion # dev: registry identity moved
    assert _expectedCurrentConfigVersion == self.currentConfigVersion # dev: config moved
    assert _expectedClosureNonce == self.closureNonce # dev: closure moved
    assert _expectedRateNonce == self.rateNonce # dev: rate moved
    assert self._isValidRateOverride(_targetBasePayoutRate, _targetEpoch) # dev: invalid rate override

    self.rateNonce += 1
    self.installedRateOverride = ire.RateOverride(
        targetBasePayoutRate=_targetBasePayoutRate,
        targetEpoch=_targetEpoch,
        runId=self.runId,
        runRegistryVersion=self.runRegistryVersion,
        installedConfigVersion=self.currentConfigVersion,
        closureNonce=self.closureNonce,
        installedRateNonce=self.rateNonce,
    )
    log RateOverrideInstalled(
        targetEpoch=_targetEpoch,
        targetBasePayoutRate=_targetBasePayoutRate,
        runId=self.runId,
        runRegistryVersion=self.runRegistryVersion,
        installedConfigVersion=self.currentConfigVersion,
        closureNonce=self.closureNonce,
        installedRateNonce=self.rateNonce,
    )


@view
@external
def canCancelRateOverride() -> bool:
    return self.installedRateOverride.targetBasePayoutRate != 0


@nonreentrant
@external
def cancelRateOverride():
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert self.installedRateOverride.targetBasePayoutRate != 0 # dev: no override
    self._terminateInstalledOverride(OVERRIDE_CANCELLED)


@internal
def _terminateInstalledOverride(_reason: uint8):
    installed: ire.RateOverride = self.installedRateOverride
    if installed.targetBasePayoutRate == 0:
        return

    observedNonce: uint256 = self.rateNonce
    self.installedRateOverride = empty(ire.RateOverride)
    self.rateNonce = observedNonce + 1
    log RateOverrideTerminated(
        targetEpoch=installed.targetEpoch,
        targetBasePayoutRate=installed.targetBasePayoutRate,
        reason=_reason,
        observedRateNonce=observedNonce,
        resultingRateNonce=self.rateNonce,
    )


@internal
def _applyInstalledOverride(_snapshot: ire.EpochSnapshot):
    installed: ire.RateOverride = self.installedRateOverride
    assert installed.targetBasePayoutRate != 0 # dev: no override
    observedNonce: uint256 = self.rateNonce
    self.installedRateOverride = empty(ire.RateOverride)
    self.overrideApplicationsThisRun += 1
    self.rateNonce = observedNonce + 1
    log RateOverrideApplied(
        epoch=_snapshot.epoch,
        controllerBasePayoutRate=_snapshot.controllerBasePayoutRate,
        basePayoutRate=_snapshot.basePayoutRate,
        observedRateNonce=observedNonce,
        resultingRateNonce=self.rateNonce,
        overrideApplicationsThisRun=self.overrideApplicationsThisRun,
    )


####################
# Epoch Controller #
####################


@view
@external
def getEpochSnapshot() -> ire.EpochSnapshot:
    snapshot: ire.EpochSnapshot = empty(ire.EpochSnapshot)
    transition: RateTransition = empty(RateTransition)
    terminalReason: uint8 = 0
    appliesOverride: bool = False
    snapshot, transition, terminalReason, appliesOverride = self._projectEpoch(
        self.epochState,
        self.currentConfig,
    )
    return snapshot


@view
@internal
def _projectedEpoch() -> uint256:
    if not self.isRunning or block.number < self.genesisBlock:
        return 0
    return (block.number - self.genesisBlock) // self.activeRunTerms.epochLength


@view
@internal
def _projectEpoch(
    _previous: ire.EpochSnapshot,
    _config: ire.ReserveEngineConfig,
) -> (ire.EpochSnapshot, RateTransition, uint8, bool):
    if not self.isRunning or block.number < self.genesisBlock:
        return empty(ire.EpochSnapshot), empty(RateTransition), 0, False

    epoch: uint256 = self._projectedEpoch()
    if _previous.basePayoutRate != 0 and epoch <= _previous.epoch:
        return _previous, empty(RateTransition), 0, False

    transition: RateTransition = empty(RateTransition)
    controllerRate: uint256 = _config.seedBasePayoutRate
    source: uint8 = RATE_SOURCE_SEED
    timingEligible: bool = (
        (block.number - self.genesisBlock) % self.activeRunTerms.epochLength == 0
    )

    if _previous.basePayoutRate != 0:
        transition = self._nextBaseRate(_previous, epoch - _previous.epoch, _config)
        controllerRate = transition.controllerBasePayoutRate
        source = RATE_SOURCE_CONTROLLER
        timingEligible = True

    finalRate: uint256 = controllerRate
    terminalReason: uint8 = 0
    appliesOverride: bool = False
    installed: ire.RateOverride = self.installedRateOverride
    if installed.targetBasePayoutRate != 0:
        if epoch > installed.targetEpoch:
            terminalReason = OVERRIDE_MISSED
        elif epoch == installed.targetEpoch:
            if self._isApplicableOverrideRate(installed.targetBasePayoutRate, controllerRate, _config):
                finalRate = installed.targetBasePayoutRate
                source = RATE_SOURCE_OVERRIDE
                appliesOverride = True
            else:
                terminalReason = OVERRIDE_DEVIATION_INVALID

    snapshot: ire.EpochSnapshot = ire.EpochSnapshot(
        epoch=epoch,
        controllerBasePayoutRate=controllerRate,
        basePayoutRate=finalRate,
        rateSource=source,
        rateNonce=self.rateNonce,
        epochConfigVersion=self.currentConfigVersion,
        paymentCap=_config.paymentCapPerEpoch,
        minPaymentAmount=_config.minPaymentAmount,
        acceptedPayment=0,
        paymentWeightedLateness=0,
        timingEligible=timingEligible,
    )
    return snapshot, transition, terminalReason, appliesOverride


@view
@internal
def _isApplicableOverrideRate(
    _targetRate: uint256,
    _controllerRate: uint256,
    _config: ire.ReserveEngineConfig,
) -> bool:
    ceiling: uint256 = self._baseRateCeilingFor(
        _config.maxAllInPayoutRate,
        self.activeRunTerms.maxDurationAdjustmentBps,
    )
    if _targetRate < MIN_BASE_RATE or _targetRate > ceiling:
        return False

    difference: uint256 = (
        _targetRate - _controllerRate
        if _targetRate >= _controllerRate
        else _controllerRate - _targetRate
    )
    if difference > max_value(uint256) // HUNDRED_PERCENT:
        return False
    return (
        difference * HUNDRED_PERCENT
        <= _controllerRate * _config.maxOverrideDeviationBps
    )


@view
@internal
def _nextBaseRate(
    _previous: ire.EpochSnapshot,
    _elapsedEpochs: uint256,
    _config: ire.ReserveEngineConfig,
) -> RateTransition:
    ceiling: uint256 = self._baseRateCeilingFor(
        _config.maxAllInPayoutRate,
        self.activeRunTerms.maxDurationAdjustmentBps,
    )
    rate: uint256 = min(_previous.basePayoutRate, ceiling)
    utilizationBps: uint256 = 0
    adjustmentBps: uint256 = 0
    decaySteps: uint256 = 0

    if _previous.acceptedPayment == 0:
        decaySteps = min(_elapsedEpochs, _config.maxDecayEpochs)
    else:
        utilizationBps = _previous.acceptedPayment * HUNDRED_PERCENT // _previous.paymentCap

        if utilizationBps >= _config.uHighBps:
            strengthBps: uint256 = (
                (utilizationBps - _config.uHighBps)
                * HUNDRED_PERCENT
                // (HUNDRED_PERCENT - _config.uHighBps)
            )
            earlinessBps: uint256 = 0
            if _previous.timingEligible:
                earlinessBps = HUNDRED_PERCENT - (
                    _previous.paymentWeightedLateness // _previous.acceptedPayment
                )
            demandBps: uint256 = strengthBps * earlinessBps // HUNDRED_PERCENT
            adjustmentBps = _config.minPriceIncreaseBps + (
                (_config.maxPriceIncreaseBps - _config.minPriceIncreaseBps)
                * demandBps
                // HUNDRED_PERCENT
            )
            rate = max(
                rate * HUNDRED_PERCENT // (HUNDRED_PERCENT + adjustmentBps),
                MIN_BASE_RATE,
            )

        elif utilizationBps <= _config.uLowBps:
            weaknessBps: uint256 = (
                (_config.uLowBps - utilizationBps)
                * HUNDRED_PERCENT
                // _config.uLowBps
            )
            adjustmentBps = _config.minPriceDecreaseBps + (
                (_config.maxPriceDecreaseBps - _config.minPriceDecreaseBps)
                * weaknessBps
                // HUNDRED_PERCENT
            )
            rate = min(
                rate * HUNDRED_PERCENT // (HUNDRED_PERCENT - adjustmentBps),
                ceiling,
            )

        decaySteps = min(_elapsedEpochs - 1, _config.maxDecayEpochs)

    for _i: uint256 in range(decaySteps, bound=MAX_DECAY_EPOCHS):
        rate = min(
            rate * HUNDRED_PERCENT // (HUNDRED_PERCENT - _config.decayBps),
            ceiling,
        )

    return RateTransition(
        controllerBasePayoutRate=rate,
        utilizationBps=utilizationBps,
        effectivePriceAdjustmentBps=adjustmentBps,
        decaySteps=decaySteps,
    )


@internal
def _storeEpochState(
    _previous: ire.EpochSnapshot,
    _snapshot: ire.EpochSnapshot,
    _transition: RateTransition,
    _terminalReason: uint8,
    _appliesOverride: bool,
):
    if _previous.basePayoutRate != 0 and _snapshot.epoch <= _previous.epoch:
        return

    self.epochState = _snapshot
    if _previous.basePayoutRate == 0:
        log EpochInitialized(
            epoch=_snapshot.epoch,
            controllerBasePayoutRate=_snapshot.controllerBasePayoutRate,
            basePayoutRate=_snapshot.basePayoutRate,
            paymentCap=_snapshot.paymentCap,
            minPaymentAmount=_snapshot.minPaymentAmount,
            timingEligible=_snapshot.timingEligible,
            epochConfigVersion=_snapshot.epochConfigVersion,
            rateSource=_snapshot.rateSource,
            rateNonce=_snapshot.rateNonce,
        )
    else:
        log EpochRolled(
            fromEpoch=_previous.epoch,
            toEpoch=_snapshot.epoch,
            oldBasePayoutRate=_previous.basePayoutRate,
            controllerBasePayoutRate=_snapshot.controllerBasePayoutRate,
            basePayoutRate=_snapshot.basePayoutRate,
            newPaymentCap=_snapshot.paymentCap,
            newMinPaymentAmount=_snapshot.minPaymentAmount,
            previousAcceptedPayment=_previous.acceptedPayment,
            previousPaymentCap=_previous.paymentCap,
            previousPaymentWeightedLateness=_previous.paymentWeightedLateness,
            previousTimingEligible=_previous.timingEligible,
            utilizationBps=_transition.utilizationBps,
            effectivePriceAdjustmentBps=_transition.effectivePriceAdjustmentBps,
            decaySteps=_transition.decaySteps,
            epochConfigVersion=_snapshot.epochConfigVersion,
            rateSource=_snapshot.rateSource,
            rateNonce=_snapshot.rateNonce,
        )

    if _appliesOverride:
        self._applyInstalledOverride(_snapshot)
    elif _terminalReason != 0:
        self._terminateInstalledOverride(_terminalReason)


@view
@internal
def _getLatenessBps(_blockNumber: uint256) -> uint256:
    epochLength: uint256 = self.activeRunTerms.epochLength
    if epochLength == 1:
        return 0
    offset: uint256 = (_blockNumber - self.genesisBlock) % epochLength
    return offset * HUNDRED_PERCENT // (epochLength - 1)


###########################
# Accounting and Coverage #
###########################


@view
@external
def totalOutstandingRipe() -> uint256:
    return self._totalOutstandingRipe()


@view
@internal
def _totalOutstandingRipe() -> uint256:
    return self.totalAllocated - self.totalClaimed - self.totalRecovered


@view
@external
def lineageAllocated() -> uint256:
    return self._lineageAllocated()


@view
@internal
def _lineageAllocated() -> uint256:
    return PRIOR_LINEAGE_ALLOCATED + self.totalAllocated


@view
@external
def remainingLineageCapacity() -> uint256:
    return self._remainingLineageCapacity()


@view
@internal
def _remainingLineageCapacity() -> uint256:
    used: uint256 = self._lineageAllocated()
    activeRemaining: uint256 = 0
    hardRemaining: uint256 = 0
    if self.activeLineageAllocationLimit > used:
        activeRemaining = self.activeLineageAllocationLimit - used
    if HARD_LINEAGE_ALLOCATION_CAP > used:
        hardRemaining = HARD_LINEAGE_ALLOCATION_CAP - used
    return min(activeRemaining, hardRemaining)


@view
@external
def remainingOutstandingCapacity() -> uint256:
    return self._remainingOutstandingCapacity()


@view
@internal
def _remainingOutstandingCapacity() -> uint256:
    outstanding: uint256 = self._totalOutstandingRipe()
    if self.activeOutstandingRipeLimit <= outstanding:
        return 0
    return self.activeOutstandingRipeLimit - outstanding


@view
@external
def isEscrowCovered() -> bool:
    isCovered: bool = False
    deficit: uint256 = 0
    surplus: uint256 = 0
    isCovered, deficit, surplus = self._getEscrowData()
    return isCovered


@view
@external
def escrowCoverageDeficit() -> uint256:
    isCovered: bool = False
    deficit: uint256 = 0
    surplus: uint256 = 0
    isCovered, deficit, surplus = self._getEscrowData()
    return deficit


@view
@external
def escrowSurplus() -> uint256:
    isCovered: bool = False
    deficit: uint256 = 0
    surplus: uint256 = 0
    isCovered, deficit, surplus = self._getEscrowData()
    return surplus


@view
@internal
def _getEscrowData() -> (bool, uint256, uint256):
    outstanding: uint256 = self._totalOutstandingRipe()
    balance: uint256 = staticcall IERC20(PINNED_RIPE).balanceOf(self)
    if balance >= outstanding:
        return True, 0, balance - outstanding
    return False, outstanding - balance, 0


@view
@external
def positionOutstandingRipe(_positionId: uint256) -> uint256:
    return self._positionOutstanding(self.positions[_positionId])


@pure
@internal
def _positionOutstanding(_position: VestingPosition) -> uint256:
    return _position.allocation - _position.claimed - _position.recovered


#########
# Quote #
#########


@view
@external
def previewAcquireRipe(
    _paymentAmount: uint256,
    _selectedFullVestingBlocks: uint256,
) -> ReserveEngineQuote:
    return self._previewAcquireRipe(_paymentAmount, _selectedFullVestingBlocks)


@view
@internal
def _previewAcquireRipe(
    _paymentAmount: uint256,
    _selectedFullVestingBlocks: uint256,
) -> ReserveEngineQuote:
    quote: ReserveEngineQuote = empty(ReserveEngineQuote)
    quote.paymentAmount = _paymentAmount
    quote.selectedFullVestingBlocks = _selectedFullVestingBlocks
    quote.runId = self.runId
    quote.runRegistryVersion = self.runRegistryVersion
    quote.closureNonce = self.closureNonce
    quote.capacityReductionNonce = self.capacityReductionNonce
    quote.remainingLineageCapacity = self._remainingLineageCapacity()
    quote.remainingOutstandingCapacity = self._remainingOutstandingCapacity()

    isCovered: bool = False
    deficit: uint256 = 0
    surplus: uint256 = 0
    isCovered, deficit, surplus = self._getEscrowData()
    quote.isEscrowCovered = isCovered
    quote.escrowCoverageDeficit = deficit
    if not isCovered:
        quote.reasonFlags |= ESCROW_COVERAGE_DEFICIT

    if not self.isRunning:
        quote.reasonFlags |= NOT_RUNNING
    if not self.isEngineEnabled:
        quote.reasonFlags |= ENGINE_DISABLED
    if deptBasics.isPaused:
        quote.reasonFlags |= ENGINE_PAUSED

    if not self.isRunning:
        quote.available = False
        return quote

    terms: ire.ReserveEngineRunTerms = self.activeRunTerms
    quote.paymentToken = self.paymentToken
    quote.paymentScale = self.paymentScale
    quote.claimCliffBlocks = terms.claimCliffBlocks

    installed: ire.RateOverride = self.installedRateOverride
    if installed.targetBasePayoutRate != 0:
        quote.overrideTargetEpoch = installed.targetEpoch
        quote.overrideTargetBasePayoutRate = installed.targetBasePayoutRate

    if block.number < self.genesisBlock:
        quote.reasonFlags |= BEFORE_GENESIS

    if not self._hasCoherentActiveRunBinding():
        quote.reasonFlags |= INVALID_CONFIGURATION

    if staticcall RipeHq(RIPE_HQ).ripeToken() != PINNED_RIPE:
        quote.reasonFlags |= INVALID_CONFIGURATION

    slot: AddressInfo = staticcall RipeHq(RIPE_HQ).getAddrInfo(RIPE_RESERVE_ENGINE_ID)
    if slot.addr != self or slot.version != self.runRegistryVersion:
        quote.reasonFlags |= NOT_CURRENT_INSTANCE

    if not staticcall RipeHq(RIPE_HQ).canMintRipe(self):
        quote.reasonFlags |= NO_MINT_AUTHORIZATION

    proceedsRecipient: address = addys._getEndaomentFundsAddr()
    quote.proceedsRecipient = proceedsRecipient
    if proceedsRecipient == empty(address):
        quote.reasonFlags |= INVALID_CONFIGURATION

    isDurationValid: bool = self._isValidDurationFor(_selectedFullVestingBlocks, terms)
    if not isDurationValid:
        quote.reasonFlags |= INVALID_DURATION

    snapshot: ire.EpochSnapshot = empty(ire.EpochSnapshot)
    transition: RateTransition = empty(RateTransition)
    terminalReason: uint8 = 0
    appliesOverride: bool = False
    snapshot, transition, terminalReason, appliesOverride = self._projectEpoch(
        self.epochState,
        self.currentConfig,
    )

    if snapshot.basePayoutRate == 0:
        if block.number >= self.genesisBlock:
            quote.reasonFlags |= INVALID_CONFIGURATION
        quote.available = False
        return quote

    quote.epoch = snapshot.epoch
    quote.epochConfigVersion = snapshot.epochConfigVersion
    quote.controllerBasePayoutRate = snapshot.controllerBasePayoutRate
    quote.basePayoutRate = snapshot.basePayoutRate
    quote.rateSource = snapshot.rateSource
    quote.rateNonce = snapshot.rateNonce

    hasEpochEnd: bool = False
    epochEnd: uint256 = 0
    hasEpochEnd, epochEnd = self._epochEndBlock(snapshot.epoch)
    if not hasEpochEnd:
        quote.reasonFlags |= INVALID_CONFIGURATION
    else:
        quote.epochEndBlock = epochEnd

    if snapshot.acceptedPayment > snapshot.paymentCap:
        quote.reasonFlags |= INVALID_CONFIGURATION
    else:
        quote.remainingPaymentCapacity = snapshot.paymentCap - snapshot.acceptedPayment

    if _paymentAmount < snapshot.minPaymentAmount:
        quote.reasonFlags |= BELOW_MINIMUM_PAYMENT
    if _paymentAmount > quote.remainingPaymentCapacity:
        quote.reasonFlags |= PAYMENT_CAP_EXCEEDED

    if isDurationValid:
        quote.durationAdjustmentBps = self._durationAdjustmentForTerms(
            _selectedFullVestingBlocks,
            terms,
        )
        if block.number > max_value(uint256) - terms.claimCliffBlocks:
            quote.reasonFlags |= INVALID_CONFIGURATION
        else:
            quote.projectedClaimStartBlock = block.number + terms.claimCliffBlocks
        if block.number > max_value(uint256) - _selectedFullVestingBlocks:
            quote.reasonFlags |= INVALID_CONFIGURATION
        else:
            quote.projectedFullyVestedBlock = block.number + _selectedFullVestingBlocks

    canCalculate: bool = (
        isDurationValid
        and _paymentAmount >= snapshot.minPaymentAmount
        and _paymentAmount <= quote.remainingPaymentCapacity
    )
    if canCalculate:
        quote.baseAllocation, quote.adjustmentAllocation, quote.totalAllocation = self._calculateAllocation(
            _paymentAmount,
            snapshot.basePayoutRate,
            self.paymentScale,
            quote.durationAdjustmentBps,
        )
        if quote.baseAllocation < MIN_BASE_ALLOCATION or quote.totalAllocation == 0:
            quote.reasonFlags |= INVALID_CONFIGURATION
        if quote.totalAllocation > quote.remainingLineageCapacity:
            quote.reasonFlags |= LINEAGE_CAP_EXCEEDED
        if quote.totalAllocation > quote.remainingOutstandingCapacity:
            quote.reasonFlags |= OUTSTANDING_CAP_EXCEEDED

    quote.available = quote.reasonFlags == 0
    return quote


@view
@internal
def _epochEndBlock(_epoch: uint256) -> (bool, uint256):
    if _epoch == max_value(uint256):
        return False, 0
    epochCount: uint256 = _epoch + 1
    epochLength: uint256 = self.activeRunTerms.epochLength
    if epochLength == 0:
        return False, 0
    if epochCount > (max_value(uint256) - self.genesisBlock) // epochLength:
        return False, 0
    return True, self.genesisBlock + epochCount * epochLength


@view
@internal
def _calculateAllocation(
    _paymentAmount: uint256,
    _basePayoutRate: uint256,
    _paymentScale: uint256,
    _durationAdjustmentBps: uint256,
) -> (uint256, uint256, uint256):
    baseAllocation: uint256 = _paymentAmount * _basePayoutRate // _paymentScale
    adjustmentAllocation: uint256 = self._mulBps(baseAllocation, _durationAdjustmentBps)
    return baseAllocation, adjustmentAllocation, baseAllocation + adjustmentAllocation


########################
# Acquire and Allocate #
########################


@nonreentrant
@external
def acquireRipe(
    _paymentAmount: uint256,
    _selectedFullVestingBlocks: uint256,
    _constraints: AcquisitionConstraints,
) -> (uint256, uint256):
    assert self.isRunning # dev: acquisition unavailable
    assert self.isEngineEnabled # dev: acquisition unavailable
    assert not deptBasics.isPaused # dev: acquisition unavailable
    assert block.number >= self.genesisBlock # dev: acquisition unavailable
    assert block.number <= _constraints.deadlineBlock # dev: deadline passed
    assert staticcall RipeHq(RIPE_HQ).ripeToken() == PINNED_RIPE # dev: invalid configuration

    slot: AddressInfo = staticcall RipeHq(RIPE_HQ).getAddrInfo(RIPE_RESERVE_ENGINE_ID)
    assert slot.addr == self and slot.version == self.runRegistryVersion # dev: engine identity moved
    assert self._hasCoherentActiveRunBinding() # dev: invalid configuration
    assert staticcall RipeHq(RIPE_HQ).canMintRipe(self) # dev: no mint authorization

    proceedsRecipient: address = addys._getEndaomentFundsAddr()
    assert proceedsRecipient != empty(address) # dev: invalid configuration

    terms: ire.ReserveEngineRunTerms = self.activeRunTerms
    assert self._isValidDurationFor(_selectedFullVestingBlocks, terms) # dev: invalid duration

    isCovered: bool = False
    deficit: uint256 = 0
    surplus: uint256 = 0
    isCovered, deficit, surplus = self._getEscrowData()
    assert isCovered # dev: escrow coverage deficit

    previous: ire.EpochSnapshot = self.epochState
    snapshot: ire.EpochSnapshot = empty(ire.EpochSnapshot)
    transition: RateTransition = empty(RateTransition)
    terminalReason: uint8 = 0
    appliesOverride: bool = False
    snapshot, transition, terminalReason, appliesOverride = self._projectEpoch(
        previous,
        self.currentConfig,
    )
    assert snapshot.basePayoutRate != 0 # dev: invalid configuration
    assert snapshot.acceptedPayment <= snapshot.paymentCap # dev: invalid configuration
    hasEpochEnd: bool = False
    epochEndBlock: uint256 = 0
    hasEpochEnd, epochEndBlock = self._epochEndBlock(snapshot.epoch)
    assert hasEpochEnd and block.number < epochEndBlock # dev: invalid configuration

    # Build only the settlement fields bound by constraints or persisted below.
    quote: ReserveEngineQuote = empty(ReserveEngineQuote)
    quote.runId = self.runId
    quote.runRegistryVersion = self.runRegistryVersion
    quote.epochConfigVersion = snapshot.epochConfigVersion
    quote.closureNonce = self.closureNonce
    quote.capacityReductionNonce = self.capacityReductionNonce
    quote.epoch = snapshot.epoch
    quote.paymentToken = self.paymentToken
    quote.proceedsRecipient = proceedsRecipient
    quote.controllerBasePayoutRate = snapshot.controllerBasePayoutRate
    quote.basePayoutRate = snapshot.basePayoutRate
    quote.rateSource = snapshot.rateSource
    quote.rateNonce = snapshot.rateNonce
    quote.durationAdjustmentBps = self._durationAdjustmentForTerms(
        _selectedFullVestingBlocks,
        terms,
    )
    assert block.number <= max_value(uint256) - terms.claimCliffBlocks # dev: invalid configuration
    assert block.number <= max_value(uint256) - _selectedFullVestingBlocks # dev: invalid configuration
    quote.projectedClaimStartBlock = block.number + terms.claimCliffBlocks
    quote.projectedFullyVestedBlock = block.number + _selectedFullVestingBlocks
    quote.remainingPaymentCapacity = snapshot.paymentCap - snapshot.acceptedPayment

    # Preserve preview parity while binding expectedTotalAllocation before payment rails.
    if (
        _paymentAmount >= snapshot.minPaymentAmount
        and _paymentAmount <= quote.remainingPaymentCapacity
    ):
        quote.baseAllocation, quote.adjustmentAllocation, quote.totalAllocation = self._calculateAllocation(
            _paymentAmount,
            snapshot.basePayoutRate,
            self.paymentScale,
            quote.durationAdjustmentBps,
        )

    assert _constraints.expectedRunId == quote.runId # dev: run moved
    assert _constraints.expectedRunRegistryVersion == quote.runRegistryVersion # dev: registry identity moved
    assert _constraints.expectedEpochConfigVersion == quote.epochConfigVersion # dev: config moved
    assert _constraints.expectedClosureNonce == quote.closureNonce # dev: closure moved
    assert _constraints.expectedCapacityReductionNonce == quote.capacityReductionNonce # dev: capacity moved
    assert _constraints.expectedEpoch == quote.epoch # dev: epoch moved
    assert _constraints.expectedPaymentToken == quote.paymentToken # dev: payment token moved
    assert _constraints.expectedProceedsRecipient == quote.proceedsRecipient # dev: proceeds recipient moved
    assert _constraints.expectedBasePayoutRate == quote.basePayoutRate # dev: base payout rate moved
    assert _constraints.expectedRateSource == quote.rateSource # dev: rate source moved
    assert _constraints.expectedRateNonce == quote.rateNonce # dev: rate identity moved
    assert _constraints.expectedDurationAdjustmentBps == quote.durationAdjustmentBps # dev: duration terms moved
    assert _constraints.expectedTotalAllocation == quote.totalAllocation # dev: allocation moved

    assert _paymentAmount >= snapshot.minPaymentAmount # dev: below minimum payment
    assert _paymentAmount <= quote.remainingPaymentCapacity # dev: payment cap exceeded

    assert quote.baseAllocation >= MIN_BASE_ALLOCATION # dev: allocation below floor
    assert quote.totalAllocation != 0 # dev: invalid allocation
    quote.remainingLineageCapacity = self._remainingLineageCapacity()
    quote.remainingOutstandingCapacity = self._remainingOutstandingCapacity()
    assert quote.totalAllocation <= quote.remainingLineageCapacity # dev: lineage or hard cap exceeded
    assert quote.totalAllocation <= quote.remainingOutstandingCapacity # dev: outstanding cap exceeded

    self._storeEpochState(
        previous,
        snapshot,
        transition,
        terminalReason,
        appliesOverride,
    )

    positionId: uint256 = self.nextPositionId
    self.nextPositionId = positionId + 1
    self.epochState.acceptedPayment += _paymentAmount
    self.epochState.paymentWeightedLateness += (
        _paymentAmount * self._getLatenessBps(block.number)
    )
    self.totalAllocated += quote.totalAllocation

    self.positions[positionId] = VestingPosition(
        beneficiary=msg.sender,
        allocation=quote.totalAllocation,
        claimed=0,
        recovered=0,
        purchaseBlock=block.number,
        claimStartBlock=quote.projectedClaimStartBlock,
        fullyVestedBlock=quote.projectedFullyVestedBlock,
        selectedFullVestingBlocks=_selectedFullVestingBlocks,
        durationAdjustmentBps=quote.durationAdjustmentBps,
        runId=quote.runId,
        epoch=quote.epoch,
        epochConfigVersion=quote.epochConfigVersion,
        basePayoutRate=quote.basePayoutRate,
        rateSource=quote.rateSource,
        rateNonce=quote.rateNonce,
        positionVersion=1,
    )

    paymentBalanceBefore: uint256 = staticcall IERC20(quote.paymentToken).balanceOf(quote.proceedsRecipient)
    assert extcall IERC20(quote.paymentToken).transferFrom(
        msg.sender,
        quote.proceedsRecipient,
        _paymentAmount,
        default_return_value=True,
    ) # dev: payment failed
    paymentBalanceAfter: uint256 = staticcall IERC20(quote.paymentToken).balanceOf(quote.proceedsRecipient)
    assert paymentBalanceAfter >= paymentBalanceBefore # dev: payment receipt mismatch
    assert paymentBalanceAfter - paymentBalanceBefore == _paymentAmount # dev: payment receipt mismatch

    ripeBalanceBefore: uint256 = staticcall IERC20(PINNED_RIPE).balanceOf(self)
    assert extcall RipeToken(PINNED_RIPE).mint(self, quote.totalAllocation) # dev: ripe mint failed
    ripeBalanceAfter: uint256 = staticcall IERC20(PINNED_RIPE).balanceOf(self)
    assert ripeBalanceAfter >= ripeBalanceBefore # dev: ripe mint mismatch
    assert ripeBalanceAfter - ripeBalanceBefore == quote.totalAllocation # dev: ripe mint mismatch

    isCovered, deficit, surplus = self._getEscrowData()
    assert isCovered # dev: escrow coverage deficit

    log RipeAllocated(
        beneficiary=msg.sender,
        positionId=positionId,
        paymentToken=quote.paymentToken,
        proceedsRecipient=quote.proceedsRecipient,
        paymentAmount=_paymentAmount,
        baseAllocation=quote.baseAllocation,
        adjustmentAllocation=quote.adjustmentAllocation,
        totalAllocation=quote.totalAllocation,
        controllerBasePayoutRate=quote.controllerBasePayoutRate,
        basePayoutRate=quote.basePayoutRate,
        durationAdjustmentBps=quote.durationAdjustmentBps,
        claimStartBlock=quote.projectedClaimStartBlock,
        fullyVestedBlock=quote.projectedFullyVestedBlock,
        runId=quote.runId,
        runRegistryVersion=quote.runRegistryVersion,
        epoch=quote.epoch,
        epochConfigVersion=quote.epochConfigVersion,
        rateSource=quote.rateSource,
        rateNonce=quote.rateNonce,
    )
    return positionId, quote.totalAllocation


######################
# Vesting and Claims #
######################


@view
@external
def grossVestedRipe(_positionId: uint256) -> uint256:
    return self._grossVestedRipe(self.positions[_positionId])


@view
@internal
def _grossVestedRipe(_position: VestingPosition) -> uint256:
    if _position.beneficiary == empty(address) or block.number <= _position.claimStartBlock:
        return 0
    if block.number >= _position.fullyVestedBlock:
        return _position.allocation

    linearBlocks: uint256 = _position.fullyVestedBlock - _position.claimStartBlock
    elapsed: uint256 = block.number - _position.claimStartBlock
    wholePerBlock: uint256 = _position.allocation // linearBlocks
    remainder: uint256 = _position.allocation % linearBlocks
    return wholePerBlock * elapsed + remainder * elapsed // linearBlocks


@view
@external
def claimableRipe(_positionId: uint256) -> uint256:
    return self._claimableRipe(self.positions[_positionId])


@view
@internal
def _claimableRipe(_position: VestingPosition) -> uint256:
    if _position.beneficiary == empty(address):
        return 0
    grossVested: uint256 = self._grossVestedRipe(_position)
    remainingEntitlement: uint256 = _position.allocation - _position.recovered
    vestedEntitlement: uint256 = min(grossVested, remainingEntitlement)
    if vestedEntitlement <= _position.claimed:
        return 0
    return vestedEntitlement - _position.claimed


@nonreentrant
@external
def claimVestedRipe(_positionId: uint256) -> uint256:
    position: VestingPosition = self.positions[_positionId]
    assert position.beneficiary != empty(address) # dev: invalid position
    assert msg.sender == position.beneficiary # dev: not beneficiary

    amount: uint256 = self._claimableRipe(position)
    assert amount != 0 # dev: nothing claimable

    isCovered: bool = False
    deficit: uint256 = 0
    surplus: uint256 = 0
    isCovered, deficit, surplus = self._getEscrowData()
    assert isCovered # dev: escrow coverage deficit

    position.claimed += amount
    self.totalClaimed += amount
    position.positionVersion += 1
    self.positions[_positionId] = position
    self._terminateRecoveryForPosition(
        _positionId,
        RECOVERY_BENEFICIARY_ACTIVITY,
    )

    engineBalanceBefore: uint256 = staticcall IERC20(PINNED_RIPE).balanceOf(self)
    beneficiaryBalanceBefore: uint256 = staticcall IERC20(PINNED_RIPE).balanceOf(position.beneficiary)
    assert extcall IERC20(PINNED_RIPE).transfer(
        position.beneficiary,
        amount,
        default_return_value=True,
    ) # dev: ripe claim failed
    engineBalanceAfter: uint256 = staticcall IERC20(PINNED_RIPE).balanceOf(self)
    beneficiaryBalanceAfter: uint256 = staticcall IERC20(PINNED_RIPE).balanceOf(position.beneficiary)
    assert engineBalanceBefore >= engineBalanceAfter # dev: ripe claim mismatch
    assert engineBalanceBefore - engineBalanceAfter == amount # dev: ripe claim mismatch
    assert beneficiaryBalanceAfter >= beneficiaryBalanceBefore # dev: ripe claim mismatch
    assert beneficiaryBalanceAfter - beneficiaryBalanceBefore == amount # dev: ripe claim mismatch

    isCovered, deficit, surplus = self._getEscrowData()
    assert isCovered # dev: escrow coverage deficit

    remaining: uint256 = self._positionOutstanding(position)
    log VestedRipeClaimed(
        beneficiary=position.beneficiary,
        positionId=_positionId,
        amount=amount,
        cumulativeClaimed=position.claimed,
        cumulativeRecovered=position.recovered,
        remainingOutstanding=remaining,
    )
    return amount


##########################
# Position RIPE Recovery #
##########################


@view
@external
def recoveryEligibleBlock(_positionId: uint256) -> uint256:
    position: VestingPosition = self.positions[_positionId]
    if position.beneficiary == empty(address):
        return 0
    if position.fullyVestedBlock > max_value(uint256) - RECOVERY_DORMANCY_BLOCKS:
        return 0
    return position.fullyVestedBlock + RECOVERY_DORMANCY_BLOCKS


@view
@external
def hasPendingRipeRecovery(_recoveryActionId: uint256) -> bool:
    return self.pendingRipeRecoveries[_recoveryActionId].actionId != 0


@nonreentrant
@external
def queueRipeRecovery(_positionId: uint256, _amount: uint256) -> uint256:
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    position: VestingPosition = self.positions[_positionId]
    assert position.beneficiary != empty(address) # dev: invalid position

    assert position.fullyVestedBlock <= max_value(uint256) - RECOVERY_DORMANCY_BLOCKS # dev: recovery schedule overflow
    eligibleBlock: uint256 = position.fullyVestedBlock + RECOVERY_DORMANCY_BLOCKS
    assert block.number >= eligibleBlock # dev: recovery dormancy

    outstanding: uint256 = self._positionOutstanding(position)
    assert _amount != 0 and _amount <= outstanding # dev: invalid recovery amount
    assert self.pendingRecoveryForPosition[_positionId] == 0 # dev: recovery already pending

    assert block.number <= max_value(uint256) - RECOVERY_NOTICE_BLOCKS # dev: recovery schedule overflow
    executeAfterBlock: uint256 = block.number + RECOVERY_NOTICE_BLOCKS
    assert executeAfterBlock <= max_value(uint256) - RECOVERY_EXECUTION_WINDOW_BLOCKS # dev: recovery schedule overflow
    expiresAtBlock: uint256 = executeAfterBlock + RECOVERY_EXECUTION_WINDOW_BLOCKS

    governanceRecipient: address = staticcall RipeHq(RIPE_HQ).governance()
    assert governanceRecipient != empty(address) # dev: invalid governance
    governanceGeneration: uint256 = staticcall RipeHq(RIPE_HQ).numGovChanges()

    actionId: uint256 = self.nextRecoveryActionId
    self.nextRecoveryActionId = actionId + 1
    self.pendingRipeRecoveries[actionId] = ire.PendingRipeRecovery(
        actionId=actionId,
        positionId=_positionId,
        beneficiary=position.beneficiary,
        amount=_amount,
        expectedPositionVersion=position.positionVersion,
        expectedPositionOutstanding=outstanding,
        governanceRecipientSnapshot=governanceRecipient,
        governanceGenerationSnapshot=governanceGeneration,
        queuedBlock=block.number,
        executeAfterBlock=executeAfterBlock,
        expiresAtBlock=expiresAtBlock,
    )
    self.pendingRecoveryForPosition[_positionId] = actionId

    log RipeRecoveryQueued(
        positionId=_positionId,
        beneficiary=position.beneficiary,
        governanceRecipient=governanceRecipient,
        recoveryActionId=actionId,
        amount=_amount,
        expectedPositionVersion=position.positionVersion,
        governanceGeneration=governanceGeneration,
        executeAfterBlock=executeAfterBlock,
        expiresAtBlock=expiresAtBlock,
    )
    return actionId


@nonreentrant
@external
def executeRipeRecovery(_recoveryActionId: uint256) -> bool:
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert self._isIssuedRecoveryAction(_recoveryActionId) # dev: invalid recovery action

    pending: ire.PendingRipeRecovery = self.pendingRipeRecoveries[_recoveryActionId]
    if pending.actionId == 0:
        return False
    if block.number < pending.executeAfterBlock:
        return False
    if block.number >= pending.expiresAtBlock:
        self._terminatePendingRecovery(pending, RECOVERY_EXPIRED)
        return False

    governanceRecipient: address = staticcall RipeHq(RIPE_HQ).governance()
    governanceGeneration: uint256 = staticcall RipeHq(RIPE_HQ).numGovChanges()
    if (
        governanceRecipient != pending.governanceRecipientSnapshot
        or governanceGeneration != pending.governanceGenerationSnapshot
    ):
        self._terminatePendingRecovery(pending, RECOVERY_GOVERNANCE_ROTATED)
        return False

    position: VestingPosition = self.positions[pending.positionId]
    currentOutstanding: uint256 = 0
    if position.beneficiary != empty(address):
        currentOutstanding = self._positionOutstanding(position)
    if (
        position.beneficiary != pending.beneficiary
        or position.positionVersion != pending.expectedPositionVersion
        or currentOutstanding != pending.expectedPositionOutstanding
        or pending.amount > currentOutstanding
        or self.pendingRecoveryForPosition[pending.positionId] != _recoveryActionId
    ):
        self._terminatePendingRecovery(pending, RECOVERY_POSITION_STALE)
        return False

    isCovered: bool = False
    deficit: uint256 = 0
    surplus: uint256 = 0
    isCovered, deficit, surplus = self._getEscrowData()
    if not isCovered:
        return False

    self.pendingRipeRecoveries[_recoveryActionId] = empty(ire.PendingRipeRecovery)
    self.pendingRecoveryForPosition[pending.positionId] = 0
    position.recovered += pending.amount
    position.positionVersion += 1
    self.positions[pending.positionId] = position
    self.totalRecovered += pending.amount

    engineBalanceBefore: uint256 = staticcall IERC20(PINNED_RIPE).balanceOf(self)
    recipientBalanceBefore: uint256 = staticcall IERC20(PINNED_RIPE).balanceOf(governanceRecipient)
    assert extcall IERC20(PINNED_RIPE).transfer(
        governanceRecipient,
        pending.amount,
        default_return_value=True,
    ) # dev: ripe recovery failed
    engineBalanceAfter: uint256 = staticcall IERC20(PINNED_RIPE).balanceOf(self)
    recipientBalanceAfter: uint256 = staticcall IERC20(PINNED_RIPE).balanceOf(governanceRecipient)
    assert engineBalanceBefore >= engineBalanceAfter # dev: ripe recovery mismatch
    assert engineBalanceBefore - engineBalanceAfter == pending.amount # dev: ripe recovery mismatch
    assert recipientBalanceAfter >= recipientBalanceBefore # dev: ripe recovery mismatch
    assert recipientBalanceAfter - recipientBalanceBefore == pending.amount # dev: ripe recovery mismatch

    isCovered, deficit, surplus = self._getEscrowData()
    assert isCovered # dev: escrow coverage deficit

    remaining: uint256 = self._positionOutstanding(position)
    log RipeRecoveredForPosition(
        positionId=pending.positionId,
        beneficiary=pending.beneficiary,
        governanceRecipient=governanceRecipient,
        recoveryActionId=_recoveryActionId,
        amount=pending.amount,
        cumulativeRecovered=position.recovered,
        remainingOutstanding=remaining,
    )
    return True


@nonreentrant
@external
def cancelRipeRecovery(_recoveryActionId: uint256) -> bool:
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert self._isIssuedRecoveryAction(_recoveryActionId) # dev: invalid recovery action
    pending: ire.PendingRipeRecovery = self.pendingRipeRecoveries[_recoveryActionId]
    if pending.actionId == 0:
        return False
    self._terminatePendingRecovery(pending, RECOVERY_CANCELLED)
    return True


@view
@internal
def _isIssuedRecoveryAction(_recoveryActionId: uint256) -> bool:
    return _recoveryActionId != 0 and _recoveryActionId < self.nextRecoveryActionId


@internal
def _terminateRecoveryForPosition(_positionId: uint256, _reason: uint8):
    actionId: uint256 = self.pendingRecoveryForPosition[_positionId]
    if actionId == 0:
        return
    pending: ire.PendingRipeRecovery = self.pendingRipeRecoveries[actionId]
    if pending.actionId != 0:
        self._terminatePendingRecovery(pending, _reason)
    else:
        self.pendingRecoveryForPosition[_positionId] = 0


@internal
def _terminatePendingRecovery(_pending: ire.PendingRipeRecovery, _reason: uint8):
    self.pendingRipeRecoveries[_pending.actionId] = empty(ire.PendingRipeRecovery)
    if self.pendingRecoveryForPosition[_pending.positionId] == _pending.actionId:
        self.pendingRecoveryForPosition[_pending.positionId] = 0
    log RipeRecoveryTerminated(
        positionId=_pending.positionId,
        beneficiary=_pending.beneficiary,
        recoveryActionId=_pending.actionId,
        reason=_reason,
    )


#########################
# Surplus RIPE Recovery #
#########################


@nonreentrant
@external
def recoverRipeSurplus(_amount: uint256) -> bool:
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    if _amount == 0:
        return False

    isCovered: bool = False
    deficit: uint256 = 0
    surplus: uint256 = 0
    isCovered, deficit, surplus = self._getEscrowData()
    if not isCovered or _amount > surplus:
        return False

    governanceRecipient: address = staticcall RipeHq(RIPE_HQ).governance()
    assert governanceRecipient != empty(address) # dev: invalid governance

    engineBalanceBefore: uint256 = staticcall IERC20(PINNED_RIPE).balanceOf(self)
    recipientBalanceBefore: uint256 = staticcall IERC20(PINNED_RIPE).balanceOf(governanceRecipient)
    assert extcall IERC20(PINNED_RIPE).transfer(
        governanceRecipient,
        _amount,
        default_return_value=True,
    ) # dev: ripe recovery failed
    engineBalanceAfter: uint256 = staticcall IERC20(PINNED_RIPE).balanceOf(self)
    recipientBalanceAfter: uint256 = staticcall IERC20(PINNED_RIPE).balanceOf(governanceRecipient)
    assert engineBalanceBefore >= engineBalanceAfter # dev: ripe recovery mismatch
    assert engineBalanceBefore - engineBalanceAfter == _amount # dev: ripe recovery mismatch
    assert recipientBalanceAfter >= recipientBalanceBefore # dev: ripe recovery mismatch
    assert recipientBalanceAfter - recipientBalanceBefore == _amount # dev: ripe recovery mismatch

    isCovered, deficit, surplus = self._getEscrowData()
    assert isCovered # dev: escrow coverage deficit
    log RipeSurplusRecovered(
        governanceRecipient=governanceRecipient,
        amount=_amount,
        remainingSurplus=surplus,
    )
    return True
