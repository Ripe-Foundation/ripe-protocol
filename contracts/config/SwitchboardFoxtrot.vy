# Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
# Ripe Foundation (C) 2026

# @version 0.4.3
# pragma optimize codesize

exports: gov.__interface__
exports: timeLock.__interface__

initializes: gov
initializes: timeLock[gov := gov]

import contracts.modules.LocalGov as gov
import contracts.modules.TimeLock as timeLock
import interfaces.RipeReserveEngine as ire


struct AddressInfo:
    addr: address
    version: uint256
    lastModified: uint256
    description: String[64]


interface RipeHq:
    def getAddrInfo(_regId: uint256) -> AddressInfo: view


struct ConfigAction:
    targetEngine: address
    targetRegistryVersion: uint256
    newConfig: ire.ReserveEngineConfig
    expectedCurrentConfigVersion: uint256
    expectedRunTermsVersion: uint256
    expectedClosureNonce: uint256


struct RunTermsAction:
    targetEngine: address
    targetRegistryVersion: uint256
    newRunTerms: ire.ReserveEngineRunTerms
    expectedCurrentConfigVersion: uint256
    expectedRunTermsVersion: uint256
    expectedClosureNonce: uint256


struct EnableAction:
    targetEngine: address
    targetRegistryVersion: uint256
    expectedClosureNonce: uint256


struct StartAction:
    targetEngine: address
    targetRegistryVersion: uint256
    genesisBlock: uint256
    expectedCurrentConfigVersion: uint256
    expectedRunTermsVersion: uint256
    expectedClosureNonce: uint256


struct UnpauseAction:
    targetEngine: address
    targetRegistryVersion: uint256
    expectedClosureNonce: uint256


struct LimitRaiseAction:
    targetEngine: address
    targetRegistryVersion: uint256
    newLineageLimit: uint256
    newOutstandingLimit: uint256
    expectedCurrentLineageLimit: uint256
    expectedCurrentOutstandingLimit: uint256
    expectedCapacityReductionNonce: uint256
    expectedClosureNonce: uint256


struct RateOverrideInstallAction:
    targetEngine: address
    targetRegistryVersion: uint256
    targetBasePayoutRate: uint256
    targetEpoch: uint256
    expectedRunId: uint256
    expectedRunRegistryVersion: uint256
    expectedCurrentConfigVersion: uint256
    expectedClosureNonce: uint256
    expectedRateNonce: uint256


struct RipeSurplusRecoveryAction:
    targetEngine: address
    targetRegistryVersion: uint256
    amount: uint256


struct RipeRecoveryRoute:
    targetEngine: address
    engineRecoveryActionId: uint256


event ReserveEngineActionQueued:
    actionId: indexed(uint256)
    targetEngine: indexed(address)
    actionType: indexed(uint8)
    targetRegistryVersion: uint256
    confirmationBlock: uint256
    payloadHash: bytes32


event ReserveEngineActionTerminated:
    actionId: indexed(uint256)
    targetEngine: indexed(address)
    actionType: indexed(uint8)
    outcome: uint8


event ReserveEngineRecoveryRouteCreated:
    routeId: indexed(uint256)
    targetEngine: indexed(address)
    positionId: indexed(uint256)
    engineRecoveryActionId: uint256
    beneficiary: address
    amount: uint256


event ReserveEngineRecoveryRouteClosed:
    routeId: indexed(uint256)
    targetEngine: indexed(address)
    engineRecoveryActionId: uint256
    outcome: uint8


event ReserveEngineConfigQueued:
    actionId: indexed(uint256)
    expectedCurrentConfigVersion: uint256
    expectedRunTermsVersion: uint256
    expectedClosureNonce: uint256
    configHash: bytes32


event ReserveEngineRunTermsQueued:
    actionId: indexed(uint256)
    expectedCurrentConfigVersion: uint256
    expectedRunTermsVersion: uint256
    expectedClosureNonce: uint256
    runTermsHash: bytes32


event ReserveEngineLifecycleQueued:
    actionId: indexed(uint256)
    operation: uint8
    genesisBlock: uint256
    expectedCurrentConfigVersion: uint256
    expectedRunTermsVersion: uint256
    expectedClosureNonce: uint256


event ReserveEngineLimitRaiseQueued:
    actionId: indexed(uint256)
    newLineageLimit: uint256
    newOutstandingLimit: uint256
    expectedCurrentLineageLimit: uint256
    expectedCurrentOutstandingLimit: uint256
    expectedCapacityReductionNonce: uint256
    expectedClosureNonce: uint256


event ReserveEngineRateOverrideQueued:
    actionId: indexed(uint256)
    targetEpoch: indexed(uint256)
    targetBasePayoutRate: uint256
    expectedRunId: uint256
    expectedRunRegistryVersion: uint256
    expectedCurrentConfigVersion: uint256
    expectedClosureNonce: uint256
    expectedRateNonce: uint256


event ReserveEngineRipeSurplusRecoveryQueued:
    actionId: indexed(uint256)
    targetEngine: indexed(address)
    amount: uint256


RIPE_RESERVE_ENGINE_ID: constant(uint256) = 26

ACTION_CONFIG: constant(uint8) = 1
ACTION_RUN_TERMS: constant(uint8) = 2
ACTION_ENABLE: constant(uint8) = 3
ACTION_START: constant(uint8) = 4
ACTION_UNPAUSE: constant(uint8) = 5
ACTION_LIMIT_RAISE: constant(uint8) = 6
ACTION_RATE_OVERRIDE_INSTALL: constant(uint8) = 7
ACTION_RIPE_SURPLUS_RECOVERY: constant(uint8) = 8

OUTCOME_EXECUTED: constant(uint8) = 1
OUTCOME_CANCELLED: constant(uint8) = 2
OUTCOME_EXPIRED: constant(uint8) = 3
OUTCOME_STALE: constant(uint8) = 4

LIFECYCLE_ENABLE: constant(uint8) = 1
LIFECYCLE_START: constant(uint8) = 2
LIFECYCLE_UNPAUSE: constant(uint8) = 3

actionType: public(HashMap[uint256, uint8])
configActions: public(HashMap[uint256, ConfigAction])
runTermsActions: public(HashMap[uint256, RunTermsAction])
enableActions: public(HashMap[uint256, EnableAction])
startActions: public(HashMap[uint256, StartAction])
unpauseActions: public(HashMap[uint256, UnpauseAction])
limitRaiseActions: public(HashMap[uint256, LimitRaiseAction])
rateOverrideInstallActions: public(HashMap[uint256, RateOverrideInstallAction])
ripeSurplusRecoveryActions: public(HashMap[uint256, RipeSurplusRecoveryAction])

knownReserveEngines: public(HashMap[address, bool])
knownEngineRegistryVersion: public(HashMap[address, uint256])
pendingRateOverrideActionId: public(uint256)

ripeRecoveryRoutes: public(HashMap[uint256, RipeRecoveryRoute])
nextRipeRecoveryRouteId: uint256


@deploy
def __init__(
    _ripeHq: address,
    _tempGov: address,
    _minConfigTimeLock: uint256,
    _maxConfigTimeLock: uint256,
):
    gov.__init__(_ripeHq, _tempGov, 0, 0, 0)
    timeLock.__init__(
        _minConfigTimeLock,
        _maxConfigTimeLock,
        _minConfigTimeLock,
        _maxConfigTimeLock,
    )
    self.nextRipeRecoveryRouteId = 1


##################
# Engine identity #
##################


@internal
def _observeCurrentReserveEngine() -> AddressInfo:
    info: AddressInfo = staticcall RipeHq(gov._getRipeHqFromGov()).getAddrInfo(RIPE_RESERVE_ENGINE_ID)
    if info.addr != empty(address):
        self.knownReserveEngines[info.addr] = True
        self.knownEngineRegistryVersion[info.addr] = info.version
    return info


@internal
def _requireCurrentReserveEngine() -> AddressInfo:
    info: AddressInfo = self._observeCurrentReserveEngine()
    assert info.addr != empty(address) # dev: invalid reserve engine
    assert staticcall ire(info.addr).ripeHq() == gov._getRipeHqFromGov() # dev: invalid reserve engine
    return info


@view
@internal
def _isKnownReserveEngine(_targetEngine: address) -> bool:
    if _targetEngine == empty(address) or not self.knownReserveEngines[_targetEngine]:
        return False
    return staticcall ire(_targetEngine).ripeHq() == gov._getRipeHqFromGov()


@pure
@internal
def _isCurrentTarget(_info: AddressInfo, _targetEngine: address, _targetRegistryVersion: uint256) -> bool:
    return _info.addr == _targetEngine and _info.version == _targetRegistryVersion


##################
# Action helpers #
##################


@internal
def _initAction(_actionType: uint8) -> (uint256, uint256):
    actionId: uint256 = timeLock._initiateAction()
    self.actionType[actionId] = _actionType
    return actionId, timeLock._getActionConfirmationBlock(actionId)


@internal
def _emitActionQueued(
    _actionId: uint256,
    _targetEngine: address,
    _actionType: uint8,
    _targetRegistryVersion: uint256,
    _confirmationBlock: uint256,
    _payloadHash: bytes32,
):
    log ReserveEngineActionQueued(
        actionId=_actionId,
        targetEngine=_targetEngine,
        actionType=_actionType,
        targetRegistryVersion=_targetRegistryVersion,
        confirmationBlock=_confirmationBlock,
        payloadHash=_payloadHash,
    )


@view
@internal
def _targetForAction(_actionId: uint256, _actionType: uint8) -> address:
    if _actionType == ACTION_CONFIG:
        return self.configActions[_actionId].targetEngine
    elif _actionType == ACTION_RUN_TERMS:
        return self.runTermsActions[_actionId].targetEngine
    elif _actionType == ACTION_ENABLE:
        return self.enableActions[_actionId].targetEngine
    elif _actionType == ACTION_START:
        return self.startActions[_actionId].targetEngine
    elif _actionType == ACTION_UNPAUSE:
        return self.unpauseActions[_actionId].targetEngine
    elif _actionType == ACTION_LIMIT_RAISE:
        return self.limitRaiseActions[_actionId].targetEngine
    elif _actionType == ACTION_RATE_OVERRIDE_INSTALL:
        return self.rateOverrideInstallActions[_actionId].targetEngine
    elif _actionType == ACTION_RIPE_SURPLUS_RECOVERY:
        return self.ripeSurplusRecoveryActions[_actionId].targetEngine
    raise "invalid action type"


@internal
def _clearAction(_actionId: uint256, _actionType: uint8):
    if _actionType == ACTION_CONFIG:
        self.configActions[_actionId] = empty(ConfigAction)
    elif _actionType == ACTION_RUN_TERMS:
        self.runTermsActions[_actionId] = empty(RunTermsAction)
    elif _actionType == ACTION_ENABLE:
        self.enableActions[_actionId] = empty(EnableAction)
    elif _actionType == ACTION_START:
        self.startActions[_actionId] = empty(StartAction)
    elif _actionType == ACTION_UNPAUSE:
        self.unpauseActions[_actionId] = empty(UnpauseAction)
    elif _actionType == ACTION_LIMIT_RAISE:
        self.limitRaiseActions[_actionId] = empty(LimitRaiseAction)
    elif _actionType == ACTION_RATE_OVERRIDE_INSTALL:
        self.rateOverrideInstallActions[_actionId] = empty(RateOverrideInstallAction)
        if self.pendingRateOverrideActionId == _actionId:
            self.pendingRateOverrideActionId = 0
    elif _actionType == ACTION_RIPE_SURPLUS_RECOVERY:
        self.ripeSurplusRecoveryActions[_actionId] = empty(RipeSurplusRecoveryAction)
    else:
        raise "invalid action type"
    self.actionType[_actionId] = 0


@internal
def _consumeAction(_actionId: uint256, _actionType: uint8):
    assert timeLock._confirmAction(_actionId) # dev: cannot confirm action
    self._clearAction(_actionId, _actionType)


@pure
@internal
def _isRaise(
    _newLineageLimit: uint256,
    _newOutstandingLimit: uint256,
    _currentLineageLimit: uint256,
    _currentOutstandingLimit: uint256,
) -> bool:
    return (
        _newLineageLimit >= _currentLineageLimit
        and _newOutstandingLimit >= _currentOutstandingLimit
        and (
            _newLineageLimit > _currentLineageLimit
            or _newOutstandingLimit > _currentOutstandingLimit
        )
    )


@pure
@internal
def _isReduction(
    _newLineageLimit: uint256,
    _newOutstandingLimit: uint256,
    _currentLineageLimit: uint256,
    _currentOutstandingLimit: uint256,
) -> bool:
    return (
        _newLineageLimit <= _currentLineageLimit
        and _newOutstandingLimit <= _currentOutstandingLimit
        and (
            _newLineageLimit < _currentLineageLimit
            or _newOutstandingLimit < _currentOutstandingLimit
        )
    )


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
@internal
def _targetEpochEndBlock(_targetEngine: address, _targetEpoch: uint256) -> uint256:
    genesisBlock: uint256 = staticcall ire(_targetEngine).genesisBlock()
    runTerms: ire.ReserveEngineRunTerms = staticcall ire(_targetEngine).getActiveRunTerms()
    if runTerms.epochLength == 0 or _targetEpoch == max_value(uint256):
        return 0
    epochCount: uint256 = _targetEpoch + 1
    if epochCount > (max_value(uint256) - genesisBlock) // runTerms.epochLength:
        return 0
    return genesisBlock + epochCount * runTerms.epochLength


################
# Configuration #
################


@external
def setReserveEngineConfig(_config: ire.ReserveEngineConfig) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    info: AddressInfo = self._requireCurrentReserveEngine()
    assert staticcall ire(info.addr).isValidConfig(_config) # dev: invalid config

    expectedConfigVersion: uint256 = staticcall ire(info.addr).currentConfigVersion()
    expectedRunTermsVersion: uint256 = staticcall ire(info.addr).runTermsVersion()
    expectedClosureNonce: uint256 = staticcall ire(info.addr).closureNonce()
    actionId: uint256 = 0
    confirmationBlock: uint256 = 0
    actionId, confirmationBlock = self._initAction(ACTION_CONFIG)

    self.configActions[actionId] = ConfigAction(
        targetEngine=info.addr,
        targetRegistryVersion=info.version,
        newConfig=_config,
        expectedCurrentConfigVersion=expectedConfigVersion,
        expectedRunTermsVersion=expectedRunTermsVersion,
        expectedClosureNonce=expectedClosureNonce,
    )
    payloadHash: bytes32 = keccak256(_abi_encode(
        ACTION_CONFIG,
        info.addr,
        info.version,
        _config,
        expectedConfigVersion,
        expectedRunTermsVersion,
        expectedClosureNonce,
    ))
    self._emitActionQueued(
        actionId,
        info.addr,
        ACTION_CONFIG,
        info.version,
        confirmationBlock,
        payloadHash,
    )
    log ReserveEngineConfigQueued(
        actionId=actionId,
        expectedCurrentConfigVersion=expectedConfigVersion,
        expectedRunTermsVersion=expectedRunTermsVersion,
        expectedClosureNonce=expectedClosureNonce,
        configHash=self._configHash(_config),
    )
    return actionId


@external
def setReserveEngineRunTerms(_runTerms: ire.ReserveEngineRunTerms) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    info: AddressInfo = self._requireCurrentReserveEngine()
    assert not staticcall ire(info.addr).isRunning() # dev: engine running
    assert staticcall ire(info.addr).isValidRunTerms(_runTerms) # dev: invalid run terms

    expectedConfigVersion: uint256 = staticcall ire(info.addr).currentConfigVersion()
    expectedRunTermsVersion: uint256 = staticcall ire(info.addr).runTermsVersion()
    expectedClosureNonce: uint256 = staticcall ire(info.addr).closureNonce()
    actionId: uint256 = 0
    confirmationBlock: uint256 = 0
    actionId, confirmationBlock = self._initAction(ACTION_RUN_TERMS)

    self.runTermsActions[actionId] = RunTermsAction(
        targetEngine=info.addr,
        targetRegistryVersion=info.version,
        newRunTerms=_runTerms,
        expectedCurrentConfigVersion=expectedConfigVersion,
        expectedRunTermsVersion=expectedRunTermsVersion,
        expectedClosureNonce=expectedClosureNonce,
    )
    payloadHash: bytes32 = keccak256(_abi_encode(
        ACTION_RUN_TERMS,
        info.addr,
        info.version,
        _runTerms,
        expectedConfigVersion,
        expectedRunTermsVersion,
        expectedClosureNonce,
    ))
    self._emitActionQueued(
        actionId,
        info.addr,
        ACTION_RUN_TERMS,
        info.version,
        confirmationBlock,
        payloadHash,
    )
    log ReserveEngineRunTermsQueued(
        actionId=actionId,
        expectedCurrentConfigVersion=expectedConfigVersion,
        expectedRunTermsVersion=expectedRunTermsVersion,
        expectedClosureNonce=expectedClosureNonce,
        runTermsHash=self._runTermsHash(_runTerms),
    )
    return actionId


#############
# Lifecycle #
#############


@external
def enableReserveEngine() -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    info: AddressInfo = self._requireCurrentReserveEngine()
    assert not staticcall ire(info.addr).isEngineEnabled() # dev: already enabled

    expectedClosureNonce: uint256 = staticcall ire(info.addr).closureNonce()
    actionId: uint256 = 0
    confirmationBlock: uint256 = 0
    actionId, confirmationBlock = self._initAction(ACTION_ENABLE)
    self.enableActions[actionId] = EnableAction(
        targetEngine=info.addr,
        targetRegistryVersion=info.version,
        expectedClosureNonce=expectedClosureNonce,
    )
    payloadHash: bytes32 = keccak256(_abi_encode(
        ACTION_ENABLE,
        info.addr,
        info.version,
        expectedClosureNonce,
    ))
    self._emitActionQueued(
        actionId,
        info.addr,
        ACTION_ENABLE,
        info.version,
        confirmationBlock,
        payloadHash,
    )
    log ReserveEngineLifecycleQueued(
        actionId=actionId,
        operation=LIFECYCLE_ENABLE,
        genesisBlock=0,
        expectedCurrentConfigVersion=0,
        expectedRunTermsVersion=0,
        expectedClosureNonce=expectedClosureNonce,
    )
    return actionId


@external
def disableReserveEngine():
    assert gov._canGovern(msg.sender) # dev: no perms
    info: AddressInfo = self._requireCurrentReserveEngine()
    assert staticcall ire(info.addr).isEngineEnabled() # dev: already disabled
    closureNonce: uint256 = staticcall ire(info.addr).closureNonce()
    extcall ire(info.addr).setEngineEnabled(False, closureNonce)


@external
def startReserveEngine(_genesisBlock: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    info: AddressInfo = self._requireCurrentReserveEngine()
    assert staticcall ire(info.addr).isValidStart(_genesisBlock) # dev: invalid start

    expectedConfigVersion: uint256 = staticcall ire(info.addr).currentConfigVersion()
    expectedRunTermsVersion: uint256 = staticcall ire(info.addr).runTermsVersion()
    expectedClosureNonce: uint256 = staticcall ire(info.addr).closureNonce()
    actionId: uint256 = 0
    confirmationBlock: uint256 = 0
    actionId, confirmationBlock = self._initAction(ACTION_START)
    self.startActions[actionId] = StartAction(
        targetEngine=info.addr,
        targetRegistryVersion=info.version,
        genesisBlock=_genesisBlock,
        expectedCurrentConfigVersion=expectedConfigVersion,
        expectedRunTermsVersion=expectedRunTermsVersion,
        expectedClosureNonce=expectedClosureNonce,
    )
    payloadHash: bytes32 = keccak256(_abi_encode(
        ACTION_START,
        info.addr,
        info.version,
        _genesisBlock,
        expectedConfigVersion,
        expectedRunTermsVersion,
        expectedClosureNonce,
    ))
    self._emitActionQueued(
        actionId,
        info.addr,
        ACTION_START,
        info.version,
        confirmationBlock,
        payloadHash,
    )
    log ReserveEngineLifecycleQueued(
        actionId=actionId,
        operation=LIFECYCLE_START,
        genesisBlock=_genesisBlock,
        expectedCurrentConfigVersion=expectedConfigVersion,
        expectedRunTermsVersion=expectedRunTermsVersion,
        expectedClosureNonce=expectedClosureNonce,
    )
    return actionId


@external
def stopReserveEngine():
    assert gov._canGovern(msg.sender) # dev: no perms
    info: AddressInfo = self._requireCurrentReserveEngine()
    assert staticcall ire(info.addr).isRunning() # dev: not running
    extcall ire(info.addr).stop()


@external
def pauseReserveEngine():
    assert gov._canGovern(msg.sender) # dev: no perms
    info: AddressInfo = self._requireCurrentReserveEngine()
    assert not staticcall ire(info.addr).isPaused() # dev: already paused
    extcall ire(info.addr).pause(True)


@external
def unpauseReserveEngine() -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    info: AddressInfo = self._requireCurrentReserveEngine()
    assert staticcall ire(info.addr).isPaused() # dev: already unpaused

    expectedClosureNonce: uint256 = staticcall ire(info.addr).closureNonce()
    actionId: uint256 = 0
    confirmationBlock: uint256 = 0
    actionId, confirmationBlock = self._initAction(ACTION_UNPAUSE)
    self.unpauseActions[actionId] = UnpauseAction(
        targetEngine=info.addr,
        targetRegistryVersion=info.version,
        expectedClosureNonce=expectedClosureNonce,
    )
    payloadHash: bytes32 = keccak256(_abi_encode(
        ACTION_UNPAUSE,
        info.addr,
        info.version,
        expectedClosureNonce,
    ))
    self._emitActionQueued(
        actionId,
        info.addr,
        ACTION_UNPAUSE,
        info.version,
        confirmationBlock,
        payloadHash,
    )
    log ReserveEngineLifecycleQueued(
        actionId=actionId,
        operation=LIFECYCLE_UNPAUSE,
        genesisBlock=0,
        expectedCurrentConfigVersion=0,
        expectedRunTermsVersion=0,
        expectedClosureNonce=expectedClosureNonce,
    )
    return actionId


#################
# Active limits #
#################


@external
def raiseReserveEngineLimits(_newLineageLimit: uint256, _newOutstandingLimit: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    info: AddressInfo = self._requireCurrentReserveEngine()
    currentLineageLimit: uint256 = staticcall ire(info.addr).activeLineageAllocationLimit()
    currentOutstandingLimit: uint256 = staticcall ire(info.addr).activeOutstandingRipeLimit()
    assert self._isRaise(
        _newLineageLimit,
        _newOutstandingLimit,
        currentLineageLimit,
        currentOutstandingLimit,
    ) # dev: invalid limit raise
    assert staticcall ire(info.addr).isValidActiveLimits(
        _newLineageLimit,
        _newOutstandingLimit,
    ) # dev: invalid limits

    expectedReductionNonce: uint256 = staticcall ire(info.addr).capacityReductionNonce()
    expectedClosureNonce: uint256 = staticcall ire(info.addr).closureNonce()
    actionId: uint256 = 0
    confirmationBlock: uint256 = 0
    actionId, confirmationBlock = self._initAction(ACTION_LIMIT_RAISE)
    self.limitRaiseActions[actionId] = LimitRaiseAction(
        targetEngine=info.addr,
        targetRegistryVersion=info.version,
        newLineageLimit=_newLineageLimit,
        newOutstandingLimit=_newOutstandingLimit,
        expectedCurrentLineageLimit=currentLineageLimit,
        expectedCurrentOutstandingLimit=currentOutstandingLimit,
        expectedCapacityReductionNonce=expectedReductionNonce,
        expectedClosureNonce=expectedClosureNonce,
    )
    payloadHash: bytes32 = keccak256(_abi_encode(
        ACTION_LIMIT_RAISE,
        info.addr,
        info.version,
        _newLineageLimit,
        _newOutstandingLimit,
        currentLineageLimit,
        currentOutstandingLimit,
        expectedReductionNonce,
        expectedClosureNonce,
    ))
    self._emitActionQueued(
        actionId,
        info.addr,
        ACTION_LIMIT_RAISE,
        info.version,
        confirmationBlock,
        payloadHash,
    )
    log ReserveEngineLimitRaiseQueued(
        actionId=actionId,
        newLineageLimit=_newLineageLimit,
        newOutstandingLimit=_newOutstandingLimit,
        expectedCurrentLineageLimit=currentLineageLimit,
        expectedCurrentOutstandingLimit=currentOutstandingLimit,
        expectedCapacityReductionNonce=expectedReductionNonce,
        expectedClosureNonce=expectedClosureNonce,
    )
    return actionId


@external
def lowerReserveEngineLimits(_newLineageLimit: uint256, _newOutstandingLimit: uint256):
    assert gov._canGovern(msg.sender) # dev: no perms
    info: AddressInfo = self._requireCurrentReserveEngine()
    currentLineageLimit: uint256 = staticcall ire(info.addr).activeLineageAllocationLimit()
    currentOutstandingLimit: uint256 = staticcall ire(info.addr).activeOutstandingRipeLimit()
    assert self._isReduction(
        _newLineageLimit,
        _newOutstandingLimit,
        currentLineageLimit,
        currentOutstandingLimit,
    ) # dev: invalid limit reduction
    assert staticcall ire(info.addr).isValidActiveLimits(
        _newLineageLimit,
        _newOutstandingLimit,
    ) # dev: invalid limits
    reductionNonce: uint256 = staticcall ire(info.addr).capacityReductionNonce()
    extcall ire(info.addr).setActiveLimits(
        _newLineageLimit,
        _newOutstandingLimit,
        currentLineageLimit,
        currentOutstandingLimit,
        reductionNonce,
    )


#################
# Rate override #
#################


@external
def setReserveEngineRateOverride(_targetBasePayoutRate: uint256, _targetEpoch: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert self.pendingRateOverrideActionId == 0 # dev: override action pending
    info: AddressInfo = self._requireCurrentReserveEngine()
    assert staticcall ire(info.addr).isValidRateOverride(
        _targetBasePayoutRate,
        _targetEpoch,
    ) # dev: invalid rate override

    expectedRunId: uint256 = staticcall ire(info.addr).runId()
    expectedRunRegistryVersion: uint256 = staticcall ire(info.addr).runRegistryVersion()
    expectedConfigVersion: uint256 = staticcall ire(info.addr).currentConfigVersion()
    expectedClosureNonce: uint256 = staticcall ire(info.addr).closureNonce()
    expectedRateNonce: uint256 = staticcall ire(info.addr).rateNonce()
    actionId: uint256 = 0
    confirmationBlock: uint256 = 0
    actionId, confirmationBlock = self._initAction(ACTION_RATE_OVERRIDE_INSTALL)

    targetEpochEndBlock: uint256 = self._targetEpochEndBlock(info.addr, _targetEpoch)
    assert targetEpochEndBlock != 0 and confirmationBlock < targetEpochEndBlock # dev: override confirmation misses epoch

    self.rateOverrideInstallActions[actionId] = RateOverrideInstallAction(
        targetEngine=info.addr,
        targetRegistryVersion=info.version,
        targetBasePayoutRate=_targetBasePayoutRate,
        targetEpoch=_targetEpoch,
        expectedRunId=expectedRunId,
        expectedRunRegistryVersion=expectedRunRegistryVersion,
        expectedCurrentConfigVersion=expectedConfigVersion,
        expectedClosureNonce=expectedClosureNonce,
        expectedRateNonce=expectedRateNonce,
    )
    self.pendingRateOverrideActionId = actionId
    payloadHash: bytes32 = keccak256(_abi_encode(
        ACTION_RATE_OVERRIDE_INSTALL,
        info.addr,
        info.version,
        _targetBasePayoutRate,
        _targetEpoch,
        expectedRunId,
        expectedRunRegistryVersion,
        expectedConfigVersion,
        expectedClosureNonce,
        expectedRateNonce,
    ))
    self._emitActionQueued(
        actionId,
        info.addr,
        ACTION_RATE_OVERRIDE_INSTALL,
        info.version,
        confirmationBlock,
        payloadHash,
    )
    log ReserveEngineRateOverrideQueued(
        actionId=actionId,
        targetEpoch=_targetEpoch,
        targetBasePayoutRate=_targetBasePayoutRate,
        expectedRunId=expectedRunId,
        expectedRunRegistryVersion=expectedRunRegistryVersion,
        expectedCurrentConfigVersion=expectedConfigVersion,
        expectedClosureNonce=expectedClosureNonce,
        expectedRateNonce=expectedRateNonce,
    )
    return actionId


@external
def cancelReserveEngineRateOverride():
    assert gov._canGovern(msg.sender) # dev: no perms
    info: AddressInfo = self._requireCurrentReserveEngine()
    assert staticcall ire(info.addr).canCancelRateOverride() # dev: no rate override
    extcall ire(info.addr).cancelRateOverride()


#################
# RIPE recovery #
#################


@external
def recoverReserveEngineRipeSurplus(_targetEngine: address, _amount: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert self._isKnownReserveEngine(_targetEngine) # dev: unknown reserve engine
    assert _amount > 0 and _amount <= staticcall ire(_targetEngine).escrowSurplus() # dev: invalid surplus amount

    targetRegistryVersion: uint256 = self.knownEngineRegistryVersion[_targetEngine]
    actionId: uint256 = 0
    confirmationBlock: uint256 = 0
    actionId, confirmationBlock = self._initAction(ACTION_RIPE_SURPLUS_RECOVERY)
    self.ripeSurplusRecoveryActions[actionId] = RipeSurplusRecoveryAction(
        targetEngine=_targetEngine,
        targetRegistryVersion=targetRegistryVersion,
        amount=_amount,
    )
    payloadHash: bytes32 = keccak256(_abi_encode(
        ACTION_RIPE_SURPLUS_RECOVERY,
        _targetEngine,
        targetRegistryVersion,
        _amount,
    ))
    self._emitActionQueued(
        actionId,
        _targetEngine,
        ACTION_RIPE_SURPLUS_RECOVERY,
        targetRegistryVersion,
        confirmationBlock,
        payloadHash,
    )
    log ReserveEngineRipeSurplusRecoveryQueued(
        actionId=actionId,
        targetEngine=_targetEngine,
        amount=_amount,
    )
    return actionId


@external
def queueReserveEngineRipeRecovery(
    _targetEngine: address,
    _positionId: uint256,
    _amount: uint256,
) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert self._isKnownReserveEngine(_targetEngine) # dev: unknown reserve engine

    engineActionId: uint256 = extcall ire(_targetEngine).queueRipeRecovery(_positionId, _amount)
    recovery: ire.PendingRipeRecovery = staticcall ire(_targetEngine).pendingRipeRecoveries(engineActionId)
    assert recovery.actionId == engineActionId # dev: invalid recovery action
    assert recovery.positionId == _positionId and recovery.amount == _amount # dev: invalid recovery payload

    routeId: uint256 = self.nextRipeRecoveryRouteId
    assert routeId != 0 and routeId != max_value(uint256) # dev: recovery route overflow
    self.nextRipeRecoveryRouteId = routeId + 1
    self.ripeRecoveryRoutes[routeId] = RipeRecoveryRoute(
        targetEngine=_targetEngine,
        engineRecoveryActionId=engineActionId,
    )
    log ReserveEngineRecoveryRouteCreated(
        routeId=routeId,
        targetEngine=_targetEngine,
        positionId=_positionId,
        engineRecoveryActionId=engineActionId,
        beneficiary=recovery.beneficiary,
        amount=recovery.amount,
    )
    return routeId


@external
def executeReserveEngineRipeRecovery(_routeId: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _routeId != 0 # dev: invalid recovery route
    route: RipeRecoveryRoute = self.ripeRecoveryRoutes[_routeId]
    if route.targetEngine == empty(address):
        return False

    if not staticcall ire(route.targetEngine).hasPendingRipeRecovery(route.engineRecoveryActionId):
        self.ripeRecoveryRoutes[_routeId] = empty(RipeRecoveryRoute)
        log ReserveEngineRecoveryRouteClosed(
            routeId=_routeId,
            targetEngine=route.targetEngine,
            engineRecoveryActionId=route.engineRecoveryActionId,
            outcome=OUTCOME_STALE,
        )
        return False

    recovery: ire.PendingRipeRecovery = staticcall ire(route.targetEngine).pendingRipeRecoveries(route.engineRecoveryActionId)
    executed: bool = extcall ire(route.targetEngine).executeRipeRecovery(route.engineRecoveryActionId)
    if executed:
        self.ripeRecoveryRoutes[_routeId] = empty(RipeRecoveryRoute)
        log ReserveEngineRecoveryRouteClosed(
            routeId=_routeId,
            targetEngine=route.targetEngine,
            engineRecoveryActionId=route.engineRecoveryActionId,
            outcome=OUTCOME_EXECUTED,
        )
        return True

    if staticcall ire(route.targetEngine).hasPendingRipeRecovery(route.engineRecoveryActionId):
        return False

    self.ripeRecoveryRoutes[_routeId] = empty(RipeRecoveryRoute)
    outcome: uint8 = OUTCOME_STALE
    if block.number >= recovery.expiresAtBlock:
        outcome = OUTCOME_EXPIRED
    log ReserveEngineRecoveryRouteClosed(
        routeId=_routeId,
        targetEngine=route.targetEngine,
        engineRecoveryActionId=route.engineRecoveryActionId,
        outcome=outcome,
    )
    return False


@external
def cancelReserveEngineRipeRecovery(_routeId: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _routeId != 0 # dev: invalid recovery route
    route: RipeRecoveryRoute = self.ripeRecoveryRoutes[_routeId]
    if route.targetEngine == empty(address):
        return False

    if not staticcall ire(route.targetEngine).hasPendingRipeRecovery(route.engineRecoveryActionId):
        self.ripeRecoveryRoutes[_routeId] = empty(RipeRecoveryRoute)
        log ReserveEngineRecoveryRouteClosed(
            routeId=_routeId,
            targetEngine=route.targetEngine,
            engineRecoveryActionId=route.engineRecoveryActionId,
            outcome=OUTCOME_STALE,
        )
        return False

    cancelled: bool = extcall ire(route.targetEngine).cancelRipeRecovery(route.engineRecoveryActionId)
    if cancelled:
        self.ripeRecoveryRoutes[_routeId] = empty(RipeRecoveryRoute)
        log ReserveEngineRecoveryRouteClosed(
            routeId=_routeId,
            targetEngine=route.targetEngine,
            engineRecoveryActionId=route.engineRecoveryActionId,
            outcome=OUTCOME_CANCELLED,
        )
        return True

    if staticcall ire(route.targetEngine).hasPendingRipeRecovery(route.engineRecoveryActionId):
        return False

    self.ripeRecoveryRoutes[_routeId] = empty(RipeRecoveryRoute)
    log ReserveEngineRecoveryRouteClosed(
        routeId=_routeId,
        targetEngine=route.targetEngine,
        engineRecoveryActionId=route.engineRecoveryActionId,
        outcome=OUTCOME_STALE,
    )
    return False


####################
# Pending execution #
####################


@external
def executePendingAction(_actionId: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _actionId != 0 # dev: invalid action
    actionType: uint8 = self.actionType[_actionId]
    if actionType == 0:
        return False

    targetEngine: address = self._targetForAction(_actionId, actionType)
    if timeLock._isExpired(_actionId):
        assert timeLock._cancelAction(_actionId) # dev: cannot expire action
        self._clearAction(_actionId, actionType)
        log ReserveEngineActionTerminated(
            actionId=_actionId,
            targetEngine=targetEngine,
            actionType=actionType,
            outcome=OUTCOME_EXPIRED,
        )
        return False
    if not timeLock._canConfirmAction(_actionId):
        return False

    if actionType == ACTION_CONFIG:
        action: ConfigAction = self.configActions[_actionId]
        currentInfo: AddressInfo = self._observeCurrentReserveEngine()
        stale: bool = not self._isCurrentTarget(currentInfo, action.targetEngine, action.targetRegistryVersion)
        if not stale and staticcall ire(action.targetEngine).currentConfigVersion() != action.expectedCurrentConfigVersion:
            stale = True
        if not stale and staticcall ire(action.targetEngine).runTermsVersion() != action.expectedRunTermsVersion:
            stale = True
        if not stale and staticcall ire(action.targetEngine).closureNonce() != action.expectedClosureNonce:
            stale = True
        if not stale and not staticcall ire(action.targetEngine).isValidConfig(action.newConfig):
            stale = True
        if stale:
            self._consumeAction(_actionId, actionType)
            log ReserveEngineActionTerminated(
                actionId=_actionId,
                targetEngine=action.targetEngine,
                actionType=actionType,
                outcome=OUTCOME_STALE,
            )
            return False
        self._consumeAction(_actionId, actionType)
        extcall ire(action.targetEngine).setConfig(
            action.newConfig,
            action.expectedCurrentConfigVersion,
        )

    elif actionType == ACTION_RUN_TERMS:
        action: RunTermsAction = self.runTermsActions[_actionId]
        currentInfo: AddressInfo = self._observeCurrentReserveEngine()
        stale: bool = not self._isCurrentTarget(currentInfo, action.targetEngine, action.targetRegistryVersion)
        if not stale and staticcall ire(action.targetEngine).currentConfigVersion() != action.expectedCurrentConfigVersion:
            stale = True
        if not stale and staticcall ire(action.targetEngine).runTermsVersion() != action.expectedRunTermsVersion:
            stale = True
        if not stale and staticcall ire(action.targetEngine).closureNonce() != action.expectedClosureNonce:
            stale = True
        if not stale and staticcall ire(action.targetEngine).isRunning():
            stale = True
        if not stale and not staticcall ire(action.targetEngine).isValidRunTerms(action.newRunTerms):
            stale = True
        if stale:
            self._consumeAction(_actionId, actionType)
            log ReserveEngineActionTerminated(
                actionId=_actionId,
                targetEngine=action.targetEngine,
                actionType=actionType,
                outcome=OUTCOME_STALE,
            )
            return False
        self._consumeAction(_actionId, actionType)
        extcall ire(action.targetEngine).setRunTerms(
            action.newRunTerms,
            action.expectedRunTermsVersion,
        )

    elif actionType == ACTION_ENABLE:
        action: EnableAction = self.enableActions[_actionId]
        currentInfo: AddressInfo = self._observeCurrentReserveEngine()
        stale: bool = not self._isCurrentTarget(currentInfo, action.targetEngine, action.targetRegistryVersion)
        if not stale and staticcall ire(action.targetEngine).closureNonce() != action.expectedClosureNonce:
            stale = True
        if not stale and staticcall ire(action.targetEngine).isEngineEnabled():
            stale = True
        if stale:
            self._consumeAction(_actionId, actionType)
            log ReserveEngineActionTerminated(
                actionId=_actionId,
                targetEngine=action.targetEngine,
                actionType=actionType,
                outcome=OUTCOME_STALE,
            )
            return False
        self._consumeAction(_actionId, actionType)
        extcall ire(action.targetEngine).setEngineEnabled(True, action.expectedClosureNonce)

    elif actionType == ACTION_START:
        action: StartAction = self.startActions[_actionId]
        currentInfo: AddressInfo = self._observeCurrentReserveEngine()
        stale: bool = not self._isCurrentTarget(currentInfo, action.targetEngine, action.targetRegistryVersion)
        if not stale and staticcall ire(action.targetEngine).currentConfigVersion() != action.expectedCurrentConfigVersion:
            stale = True
        if not stale and staticcall ire(action.targetEngine).runTermsVersion() != action.expectedRunTermsVersion:
            stale = True
        if not stale and staticcall ire(action.targetEngine).closureNonce() != action.expectedClosureNonce:
            stale = True
        if not stale and staticcall ire(action.targetEngine).isRunning():
            stale = True
        if not stale and not staticcall ire(action.targetEngine).isValidStart(action.genesisBlock):
            stale = True
        if stale:
            self._consumeAction(_actionId, actionType)
            log ReserveEngineActionTerminated(
                actionId=_actionId,
                targetEngine=action.targetEngine,
                actionType=actionType,
                outcome=OUTCOME_STALE,
            )
            return False
        self._consumeAction(_actionId, actionType)
        extcall ire(action.targetEngine).start(
            action.genesisBlock,
            action.targetRegistryVersion,
            action.expectedCurrentConfigVersion,
            action.expectedRunTermsVersion,
            action.expectedClosureNonce,
        )

    elif actionType == ACTION_UNPAUSE:
        action: UnpauseAction = self.unpauseActions[_actionId]
        currentInfo: AddressInfo = self._observeCurrentReserveEngine()
        stale: bool = not self._isCurrentTarget(currentInfo, action.targetEngine, action.targetRegistryVersion)
        if not stale and staticcall ire(action.targetEngine).closureNonce() != action.expectedClosureNonce:
            stale = True
        if not stale and not staticcall ire(action.targetEngine).isPaused():
            stale = True
        if stale:
            self._consumeAction(_actionId, actionType)
            log ReserveEngineActionTerminated(
                actionId=_actionId,
                targetEngine=action.targetEngine,
                actionType=actionType,
                outcome=OUTCOME_STALE,
            )
            return False
        self._consumeAction(_actionId, actionType)
        extcall ire(action.targetEngine).pause(False)

    elif actionType == ACTION_LIMIT_RAISE:
        action: LimitRaiseAction = self.limitRaiseActions[_actionId]
        currentInfo: AddressInfo = self._observeCurrentReserveEngine()
        stale: bool = not self._isCurrentTarget(currentInfo, action.targetEngine, action.targetRegistryVersion)
        if not stale and staticcall ire(action.targetEngine).activeLineageAllocationLimit() != action.expectedCurrentLineageLimit:
            stale = True
        if not stale and staticcall ire(action.targetEngine).activeOutstandingRipeLimit() != action.expectedCurrentOutstandingLimit:
            stale = True
        if not stale and staticcall ire(action.targetEngine).capacityReductionNonce() != action.expectedCapacityReductionNonce:
            stale = True
        if not stale and staticcall ire(action.targetEngine).closureNonce() != action.expectedClosureNonce:
            stale = True
        if not stale and not self._isRaise(
            action.newLineageLimit,
            action.newOutstandingLimit,
            action.expectedCurrentLineageLimit,
            action.expectedCurrentOutstandingLimit,
        ):
            stale = True
        if not stale and not staticcall ire(action.targetEngine).isValidActiveLimits(
            action.newLineageLimit,
            action.newOutstandingLimit,
        ):
            stale = True
        if stale:
            self._consumeAction(_actionId, actionType)
            log ReserveEngineActionTerminated(
                actionId=_actionId,
                targetEngine=action.targetEngine,
                actionType=actionType,
                outcome=OUTCOME_STALE,
            )
            return False
        self._consumeAction(_actionId, actionType)
        extcall ire(action.targetEngine).setActiveLimits(
            action.newLineageLimit,
            action.newOutstandingLimit,
            action.expectedCurrentLineageLimit,
            action.expectedCurrentOutstandingLimit,
            action.expectedCapacityReductionNonce,
        )

    elif actionType == ACTION_RATE_OVERRIDE_INSTALL:
        action: RateOverrideInstallAction = self.rateOverrideInstallActions[_actionId]
        currentInfo: AddressInfo = self._observeCurrentReserveEngine()
        stale: bool = self.pendingRateOverrideActionId != _actionId
        if not stale and not self._isCurrentTarget(currentInfo, action.targetEngine, action.targetRegistryVersion):
            stale = True
        if not stale and staticcall ire(action.targetEngine).runId() != action.expectedRunId:
            stale = True
        if not stale and staticcall ire(action.targetEngine).runRegistryVersion() != action.expectedRunRegistryVersion:
            stale = True
        if not stale and staticcall ire(action.targetEngine).currentConfigVersion() != action.expectedCurrentConfigVersion:
            stale = True
        if not stale and staticcall ire(action.targetEngine).closureNonce() != action.expectedClosureNonce:
            stale = True
        if not stale and staticcall ire(action.targetEngine).rateNonce() != action.expectedRateNonce:
            stale = True
        if not stale and not staticcall ire(action.targetEngine).isValidRateOverride(
            action.targetBasePayoutRate,
            action.targetEpoch,
        ):
            stale = True
        if stale:
            self._consumeAction(_actionId, actionType)
            log ReserveEngineActionTerminated(
                actionId=_actionId,
                targetEngine=action.targetEngine,
                actionType=actionType,
                outcome=OUTCOME_STALE,
            )
            return False
        self._consumeAction(_actionId, actionType)
        extcall ire(action.targetEngine).installRateOverride(
            action.targetBasePayoutRate,
            action.targetEpoch,
            action.expectedRunId,
            action.expectedRunRegistryVersion,
            action.expectedCurrentConfigVersion,
            action.expectedClosureNonce,
            action.expectedRateNonce,
        )

    elif actionType == ACTION_RIPE_SURPLUS_RECOVERY:
        action: RipeSurplusRecoveryAction = self.ripeSurplusRecoveryActions[_actionId]
        stale: bool = not self._isKnownReserveEngine(action.targetEngine)
        if not stale and (action.amount == 0 or staticcall ire(action.targetEngine).escrowSurplus() < action.amount):
            stale = True
        if stale:
            self._consumeAction(_actionId, actionType)
            log ReserveEngineActionTerminated(
                actionId=_actionId,
                targetEngine=action.targetEngine,
                actionType=actionType,
                outcome=OUTCOME_STALE,
            )
            return False
        self._consumeAction(_actionId, actionType)
        recovered: bool = extcall ire(action.targetEngine).recoverRipeSurplus(action.amount)
        if not recovered:
            log ReserveEngineActionTerminated(
                actionId=_actionId,
                targetEngine=action.targetEngine,
                actionType=actionType,
                outcome=OUTCOME_STALE,
            )
            return False

    else:
        raise "invalid action type"

    log ReserveEngineActionTerminated(
        actionId=_actionId,
        targetEngine=targetEngine,
        actionType=actionType,
        outcome=OUTCOME_EXECUTED,
    )
    return True


#######################
# Pending cancellation #
#######################


@external
def cancelPendingAction(_actionId: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _actionId != 0 # dev: invalid action
    actionType: uint8 = self.actionType[_actionId]
    if actionType == 0:
        return False

    targetEngine: address = self._targetForAction(_actionId, actionType)
    wasExpired: bool = timeLock._isExpired(_actionId)
    assert timeLock._cancelAction(_actionId) # dev: cannot cancel action
    self._clearAction(_actionId, actionType)
    outcome: uint8 = OUTCOME_CANCELLED
    if wasExpired:
        outcome = OUTCOME_EXPIRED
    log ReserveEngineActionTerminated(
        actionId=_actionId,
        targetEngine=targetEngine,
        actionType=actionType,
        outcome=outcome,
    )
    return True
