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
# pragma optimize codesize

exports: gov.__interface__
exports: timeLock.__interface__

initializes: gov
initializes: timeLock[gov := gov]

import contracts.modules.LocalGov as gov
import contracts.modules.TimeLock as timeLock

interface InstantBondLane:
    def setConfig(_newConfig: InstantBondConfig, _expectedVersion: uint256) -> uint256: nonpayable
    def setRateOverride(_targetRate: uint256, _expectedConfigVersion: uint256, _expectedOverrideVersion: uint256) -> uint256: nonpayable
    def cancelRateOverride(_expectedOverrideVersion: uint256) -> uint256: nonpayable
    def isValidConfig(_config: InstantBondConfig) -> bool: view
    def isValidRateOverride(_targetRate: uint256, _expectedConfigVersion: uint256, _expectedOverrideVersion: uint256) -> bool: view
    def canCancelRateOverride(_expectedOverrideVersion: uint256) -> bool: view
    def configVersion() -> uint256: view
    def overrideVersion() -> uint256: view
    def getRipeHq() -> address: view
    def EPOCH_LENGTH() -> uint256: view

flag ActionType:
    INSTANT_BOND_CONFIG
    RATE_OVERRIDE_SET
    RATE_OVERRIDE_CANCEL

# NOTE: Keep this struct byte-for-byte aligned with InstantBondLane.InstantBondConfig.
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

struct PendingInstantBondConfig:
    config: InstantBondConfig
    expectedVersion: uint256

struct PendingRateOverride:
    targetRate: uint256
    expectedConfigVersion: uint256
    expectedOverrideVersion: uint256

event PendingInstantBondConfigSet:
    actionId: uint256
    confirmationBlock: uint256
    expectedVersion: uint256
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

event InstantBondConfigExecuted:
    actionId: uint256
    newVersion: uint256

event InstantBondConfigCancelled:
    actionId: uint256

event PendingRateOverrideSet:
    actionId: uint256
    confirmationBlock: uint256
    targetRate: uint256
    expectedConfigVersion: uint256
    expectedOverrideVersion: uint256

event PendingRateOverrideCancellationSet:
    actionId: uint256
    confirmationBlock: uint256
    expectedOverrideVersion: uint256

event RateOverrideExecuted:
    actionId: uint256
    newVersion: uint256

event RateOverrideCancellationExecuted:
    actionId: uint256
    newVersion: uint256

event RateOverrideActionCancelled:
    actionId: uint256
    isCancellation: bool

LANE: public(immutable(address))

# pending actions
actionType: public(HashMap[uint256, ActionType]) # aid -> type
pendingConfig: public(HashMap[uint256, PendingInstantBondConfig]) # aid -> config
pendingRateOverride: public(HashMap[uint256, PendingRateOverride]) # aid -> override


@deploy
def __init__(
    _ripeHq: address,
    _tempGov: address,
    _minConfigTimeLock: uint256,
    _maxConfigTimeLock: uint256,
    _instantBondLane: address,
):
    gov.__init__(_ripeHq, _tempGov, 0, 0, 0)
    timeLock.__init__(_minConfigTimeLock, _maxConfigTimeLock, 0, _maxConfigTimeLock)
    assert _instantBondLane != empty(address) and _instantBondLane.is_contract # dev: invalid lane
    assert staticcall InstantBondLane(_instantBondLane).getRipeHq() == _ripeHq # dev: invalid lane
    assert staticcall InstantBondLane(_instantBondLane).EPOCH_LENGTH() != 0 # dev: invalid lane
    configVersion: uint256 = staticcall InstantBondLane(_instantBondLane).configVersion()
    overrideVersion: uint256 = staticcall InstantBondLane(_instantBondLane).overrideVersion()
    assert not staticcall InstantBondLane(_instantBondLane).isValidConfig(empty(InstantBondConfig)) # dev: invalid lane
    assert not staticcall InstantBondLane(_instantBondLane).isValidRateOverride(0, configVersion, overrideVersion) # dev: invalid lane
    LANE = _instantBondLane


#######################
# Instant Bond Config #
#######################


@external
def setInstantBondConfig(_config: InstantBondConfig, _expectedVersion: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert timeLock.actionTimeLock != 0 # dev: action time lock not set

    lane: address = LANE
    assert staticcall InstantBondLane(lane).isValidConfig(_config) # dev: invalid config
    assert _expectedVersion == staticcall InstantBondLane(lane).configVersion() # dev: stale config version

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.INSTANT_BOND_CONFIG
    self.pendingConfig[aid] = PendingInstantBondConfig(
        config=_config,
        expectedVersion=_expectedVersion,
    )

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingInstantBondConfigSet(
        actionId=aid,
        confirmationBlock=confirmationBlock,
        expectedVersion=_expectedVersion,
        canBuyNow=_config.canBuyNow,
        paymentCapPerEpoch=_config.paymentCapPerEpoch,
        minPaymentAmount=_config.minPaymentAmount,
        mintBudget=_config.mintBudget,
        maxEffectiveRate=_config.maxEffectiveRate,
        seedRate=_config.seedRate,
        uHighBps=_config.uHighBps,
        uLowBps=_config.uLowBps,
        minUpBps=_config.minUpBps,
        maxUpBps=_config.maxUpBps,
        minDownBps=_config.minDownBps,
        maxDownBps=_config.maxDownBps,
        decayBps=_config.decayBps,
        maxDecayEpochs=_config.maxDecayEpochs,
        maxLockBonus=_config.maxLockBonus,
    )
    return aid


#################
# Rate Override #
#################


@external
def setInstantBondRateOverride(
    _targetRate: uint256,
    _expectedConfigVersion: uint256,
    _expectedOverrideVersion: uint256,
) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert timeLock.actionTimeLock != 0 # dev: action time lock not set

    lane: address = LANE
    assert staticcall InstantBondLane(lane).isValidRateOverride(_targetRate, _expectedConfigVersion, _expectedOverrideVersion) # dev: invalid rate override

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.RATE_OVERRIDE_SET
    self.pendingRateOverride[aid] = PendingRateOverride(
        targetRate=_targetRate,
        expectedConfigVersion=_expectedConfigVersion,
        expectedOverrideVersion=_expectedOverrideVersion,
    )

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingRateOverrideSet(
        actionId=aid,
        confirmationBlock=confirmationBlock,
        targetRate=_targetRate,
        expectedConfigVersion=_expectedConfigVersion,
        expectedOverrideVersion=_expectedOverrideVersion,
    )
    return aid


@external
def cancelInstantBondRateOverride(_expectedOverrideVersion: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert timeLock.actionTimeLock != 0 # dev: action time lock not set

    lane: address = LANE
    assert staticcall InstantBondLane(lane).canCancelRateOverride(_expectedOverrideVersion) # dev: no rate override

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.RATE_OVERRIDE_CANCEL
    self.pendingRateOverride[aid] = PendingRateOverride(
        targetRate=0,
        expectedConfigVersion=0,
        expectedOverrideVersion=_expectedOverrideVersion,
    )

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingRateOverrideCancellationSet(
        actionId=aid,
        confirmationBlock=confirmationBlock,
        expectedOverrideVersion=_expectedOverrideVersion,
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
    lane: address = LANE
    newVersion: uint256 = 0
    if actionType == ActionType.INSTANT_BOND_CONFIG:
        p: PendingInstantBondConfig = self.pendingConfig[_aid]
        newVersion = extcall InstantBondLane(lane).setConfig(p.config, p.expectedVersion)
    elif actionType == ActionType.RATE_OVERRIDE_SET:
        o: PendingRateOverride = self.pendingRateOverride[_aid]
        newVersion = extcall InstantBondLane(lane).setRateOverride(
            o.targetRate,
            o.expectedConfigVersion,
            o.expectedOverrideVersion,
        )
    else:
        c: PendingRateOverride = self.pendingRateOverride[_aid]
        newVersion = extcall InstantBondLane(lane).cancelRateOverride(c.expectedOverrideVersion)

    self._clearPending(_aid, actionType)
    if actionType == ActionType.INSTANT_BOND_CONFIG:
        log InstantBondConfigExecuted(actionId=_aid, newVersion=newVersion)
    elif actionType == ActionType.RATE_OVERRIDE_SET:
        log RateOverrideExecuted(actionId=_aid, newVersion=newVersion)
    else:
        log RateOverrideCancellationExecuted(actionId=_aid, newVersion=newVersion)
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
    assert timeLock._cancelAction(_aid) # dev: cannot cancel action
    self._clearPending(_aid, actionType)
    if actionType == ActionType.INSTANT_BOND_CONFIG:
        log InstantBondConfigCancelled(actionId=_aid)
    else:
        log RateOverrideActionCancelled(
            actionId=_aid,
            isCancellation=actionType == ActionType.RATE_OVERRIDE_CANCEL,
        )


@internal
def _clearPending(_aid: uint256, _actionType: ActionType):
    if _actionType == ActionType.INSTANT_BOND_CONFIG:
        self.pendingConfig[_aid] = empty(PendingInstantBondConfig)
    else:
        self.pendingRateOverride[_aid] = empty(PendingRateOverride)
    self.actionType[_aid] = empty(ActionType)
