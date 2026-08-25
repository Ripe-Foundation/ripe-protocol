#        ______   __     __   __   ______  ______   __  __   ______   ______   ______   ______   _____
#       /\  ___\ /\ \  _ \ \ /\ \ /\__  _\/\  ___\ /\ \_\ \ /\  == \ /\  __ \ /\  __ \ /\  == \ /\  __-.
#       \ \___  \\ \ \/ ".\ \\ \ \\/_/\ \/\ \ \____\ \  __ \\ \  __< \ \ \/\ \\ \  __ \\ \  __< \ \ \/\ \
#        \/\_____\\ \__/".~\_\\ \_\  \ \_\ \ \_____\\ \_\ \_\\ \_____\\ \_____\\ \_\ \_\\ \_\ \_\\ \____-
#         \/_____/ \/_/   \/_/ \/_/   \/_/  \/_____/ \/_/\/_/ \/_____/ \/_____/ \/_/\/_/ \/_/ /_/ \/____/
#                                    ╔═╗┌─┐─┐ ┬┌┬┐┬─┐┌─┐┌┬┐
#                                    ╠╣ │ │┌┴┬┘ │ ├┬┘│ │ │
#                                    ╚  └─┘┴ └─ ┴ ┴└─└─┘ ┴
#
#      Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
#      Ripe Foundation (C) 2025

# @version 0.4.3

exports: gov.__interface__
exports: timeLock.__interface__

initializes: gov
initializes: timeLock[gov := gov]

import contracts.modules.LocalGov as gov
import contracts.modules.TimeLock as timeLock

interface RipeReserveEngine:
    def start(_genesisBlock: uint256, _epochLength: uint256): nonpayable
    def genesisBlock() -> uint256: view
    def isValidRateOverride(_targetBasePayoutRate: uint256, _targetEpoch: uint256) -> bool: view
    def isValidConfig(_config: ReserveEngineConfig) -> bool: view
    def isValidEpochLength(_epochLength: uint256) -> bool: view
    def setConfig(_newConfig: ReserveEngineConfig): nonpayable
    def isValidPaymentToken(_token: address) -> bool: view
    def setRateOverride(_targetBasePayoutRate: uint256, _targetEpoch: uint256) -> uint256: nonpayable
    def setPaymentToken(_token: address): nonpayable
    def setCanAcquireRipe(_canAcquireRipe: bool): nonpayable
    def canAcquireRipe() -> bool: view
    def engineConfig() -> ReserveEngineConfig: view
    def overrideTargetBasePayoutRate() -> uint256: view
    def overrideTargetEpoch() -> uint256: view
    def cancelRateOverride(): nonpayable
    def isRunning() -> bool: view
    def stop(): nonpayable

interface RipeReserveVesting:
    def setRemainingAllocationBudget(_amount: uint256): nonpayable

interface RipeHq:
    def getAddr(_regId: uint256) -> address: view

flag ActionType:
    RESERVE_ENGINE_CONFIG
    RESERVE_VESTING_ALLOCATION_BUDGET_SET

struct ReserveEngineConfig:
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

event PendingReserveEngineConfigSet:
    actionId: uint256
    confirmationBlock: uint256
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

event ReserveEngineConfigExecuted:
    actionId: uint256

event PendingReserveVestingAllocationBudgetSet:
    actionId: uint256
    confirmationBlock: uint256
    amount: uint256

event ReserveVestingAllocationBudgetExecuted:
    actionId: uint256

event ReserveEngineRateOverrideSet:
    targetEpoch: indexed(uint256)
    targetBasePayoutRate: uint256

event ReserveEngineRateOverrideCancelled:
    targetEpoch: indexed(uint256)
    targetBasePayoutRate: uint256

event ReserveEngineStarted:
    genesisBlock: uint256
    epochLength: uint256

event ReserveEnginePaymentTokenSet:
    token: indexed(address)

event ReserveEngineCanAcquireRipeSet:
    canAcquireRipe: bool

# pending actions
actionType: public(HashMap[uint256, ActionType]) # aid -> type
pendingEngineConfig: public(HashMap[uint256, ReserveEngineConfig]) # aid -> config
pendingVestingAllocationBudget: public(HashMap[uint256, uint256]) # aid -> amount

RIPE_RESERVE_ENGINE_ID: constant(uint256) = 26
RIPE_RESERVE_VESTING_ID: constant(uint256) = 27


@deploy
def __init__(
    _ripeHq: address,
    _tempGov: address,
    _minConfigTimeLock: uint256,
    _maxConfigTimeLock: uint256,
):
    gov.__init__(_ripeHq, _tempGov, 0, 0, 0)
    timeLock.__init__(_minConfigTimeLock, _maxConfigTimeLock, 0, _maxConfigTimeLock)


# address getters


@view
@internal
def _getRipeReserveEngineAddr() -> address:
    engine: address = staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(RIPE_RESERVE_ENGINE_ID)
    assert engine != empty(address) # dev: invalid engine
    return engine


@view
@internal
def _getRipeReserveVestingAddr() -> address:
    vesting: address = staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(RIPE_RESERVE_VESTING_ID)
    assert vesting != empty(address) and vesting.is_contract # dev: invalid vesting
    return vesting


#########################
# reserve engine config #
#########################


@external
def setReserveEngineConfig(_config: ReserveEngineConfig) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    engine: address = self._getRipeReserveEngineAddr()
    assert staticcall RipeReserveEngine(engine).isValidConfig(_config) # dev: invalid config

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.RESERVE_ENGINE_CONFIG
    self.pendingEngineConfig[aid] = _config

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingReserveEngineConfigSet(
        actionId=aid,
        confirmationBlock=confirmationBlock,
        paymentCapPerEpoch=_config.paymentCapPerEpoch,
        minPaymentAmount=_config.minPaymentAmount,
        maxAllInPayoutRate=_config.maxAllInPayoutRate,
        seedBasePayoutRate=_config.seedBasePayoutRate,
        uHighBps=_config.uHighBps,
        uLowBps=_config.uLowBps,
        minUpBps=_config.minUpBps,
        maxUpBps=_config.maxUpBps,
        minDownBps=_config.minDownBps,
        maxDownBps=_config.maxDownBps,
        decayBps=_config.decayBps,
        maxDecayEpochs=_config.maxDecayEpochs,
        maxVestingBonus=_config.maxVestingBonus,
        minVestingLength=_config.minVestingLength,
        maxVestingLength=_config.maxVestingLength,
        epochLength=_config.epochLength,
    )
    return aid


# can acquire ripe


@external
def setCanAcquireRipe(_canAcquireRipe: bool):
    assert gov._canGovern(msg.sender) # dev: no perms

    engine: address = self._getRipeReserveEngineAddr()
    assert staticcall RipeReserveEngine(engine).canAcquireRipe() != _canAcquireRipe # dev: no change
    extcall RipeReserveEngine(engine).setCanAcquireRipe(_canAcquireRipe)
    log ReserveEngineCanAcquireRipeSet(canAcquireRipe=_canAcquireRipe)


#################
# Rate Override #
#################


@external
def setReserveEngineRateOverride(_targetBasePayoutRate: uint256, _targetEpoch: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    engine: address = self._getRipeReserveEngineAddr()
    assert staticcall RipeReserveEngine(engine).isValidRateOverride(_targetBasePayoutRate, _targetEpoch) # dev: invalid rate override
    resolvedEpoch: uint256 = extcall RipeReserveEngine(engine).setRateOverride(_targetBasePayoutRate, _targetEpoch)
    log ReserveEngineRateOverrideSet(
        targetEpoch=resolvedEpoch,
        targetBasePayoutRate=_targetBasePayoutRate,
    )
    return resolvedEpoch


@external
def cancelReserveEngineRateOverride():
    assert gov._canGovern(msg.sender) # dev: no perms

    engine: address = self._getRipeReserveEngineAddr()
    targetBasePayoutRate: uint256 = staticcall RipeReserveEngine(engine).overrideTargetBasePayoutRate()
    assert targetBasePayoutRate != 0 # dev: no rate override
    targetEpoch: uint256 = staticcall RipeReserveEngine(engine).overrideTargetEpoch()
    extcall RipeReserveEngine(engine).cancelRateOverride()
    log ReserveEngineRateOverrideCancelled(targetEpoch=targetEpoch, targetBasePayoutRate=targetBasePayoutRate)


#########
# Start #
#########


@external
def startReserveEngine(_genesisBlock: uint256, _epochLength: uint256):
    assert gov._canGovern(msg.sender) # dev: no perms

    engine: address = self._getRipeReserveEngineAddr()
    assert not staticcall RipeReserveEngine(engine).isRunning() # dev: already running
    assert staticcall RipeReserveEngine(engine).isValidEpochLength(_epochLength) # dev: invalid epoch length
    assert staticcall RipeReserveEngine(engine).isValidConfig(staticcall RipeReserveEngine(engine).engineConfig()) # dev: not configured
    extcall RipeReserveEngine(engine).start(_genesisBlock, _epochLength)
    resolvedGenesisBlock: uint256 = staticcall RipeReserveEngine(engine).genesisBlock()
    log ReserveEngineStarted(genesisBlock=resolvedGenesisBlock, epochLength=_epochLength)


@external
def stopReserveEngine():
    assert gov._canGovern(msg.sender) # dev: no perms

    engine: address = self._getRipeReserveEngineAddr()
    assert staticcall RipeReserveEngine(engine).isRunning() # dev: not running
    extcall RipeReserveEngine(engine).stop()


#################
# Payment Token #
#################


@external
def setReserveEnginePaymentToken(_token: address):
    assert gov._canGovern(msg.sender) # dev: no perms

    engine: address = self._getRipeReserveEngineAddr()
    assert staticcall RipeReserveEngine(engine).isValidPaymentToken(_token) # dev: invalid payment token
    extcall RipeReserveEngine(engine).setPaymentToken(_token)
    log ReserveEnginePaymentTokenSet(token=_token)


#####################
# Allocation Budget #
#####################


@external
def setReserveVestingRemainingAllocationBudget(_amount: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    self._getRipeReserveVestingAddr()

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.RESERVE_VESTING_ALLOCATION_BUDGET_SET
    self.pendingVestingAllocationBudget[aid] = _amount

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingReserveVestingAllocationBudgetSet(
        actionId=aid,
        confirmationBlock=confirmationBlock,
        amount=_amount,
    )
    return aid


#############
# Execution #
#############


@external
def executePendingAction(_aid: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms

    # check time lock
    if not timeLock._confirmAction(_aid):
        if timeLock._isExpired(_aid):
            self._cancelPendingAction(_aid)
        return False

    actionType: ActionType = self.actionType[_aid]
    assert actionType != empty(ActionType) # dev: invalid action

    if actionType == ActionType.RESERVE_ENGINE_CONFIG:
        engine: address = self._getRipeReserveEngineAddr()
        config: ReserveEngineConfig = self.pendingEngineConfig[_aid]
        assert staticcall RipeReserveEngine(engine).isValidConfig(config) # dev: invalid config
        extcall RipeReserveEngine(engine).setConfig(config)
        self.pendingEngineConfig[_aid] = empty(ReserveEngineConfig)
        log ReserveEngineConfigExecuted(actionId=_aid)

    elif actionType == ActionType.RESERVE_VESTING_ALLOCATION_BUDGET_SET:
        vesting: address = self._getRipeReserveVestingAddr()
        amount: uint256 = self.pendingVestingAllocationBudget[_aid]
        extcall RipeReserveVesting(vesting).setRemainingAllocationBudget(amount)
        self.pendingVestingAllocationBudget[_aid] = 0
        log ReserveVestingAllocationBudgetExecuted(actionId=_aid)

    else:
        raise "invalid action"

    self.actionType[_aid] = empty(ActionType)
    return True


#################
# Cancel Action #
#################


@external
def cancelPendingAction(_aid: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    self._cancelPendingAction(_aid)
    return True


@internal
def _cancelPendingAction(_aid: uint256):
    actionType: ActionType = self.actionType[_aid]
    assert actionType != empty(ActionType) # dev: invalid action
    assert timeLock._cancelAction(_aid) # dev: cannot cancel action

    if actionType == ActionType.RESERVE_ENGINE_CONFIG:
        self.pendingEngineConfig[_aid] = empty(ReserveEngineConfig)
    elif actionType == ActionType.RESERVE_VESTING_ALLOCATION_BUDGET_SET:
        self.pendingVestingAllocationBudget[_aid] = 0
    else:
        raise "invalid action"

    self.actionType[_aid] = empty(ActionType)
