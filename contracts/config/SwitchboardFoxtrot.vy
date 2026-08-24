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

interface InstantBondLane:
    def start(_genesisBlock: uint256, _epochLength: uint256): nonpayable
    def isValidRateOverride(_targetRate: uint256) -> bool: view
    def isValidConfig(_config: InstantBondConfig) -> bool: view
    def isValidEpochLength(_epochLength: uint256) -> bool: view
    def setConfig(_newConfig: InstantBondConfig): nonpayable
    def isValidPaymentToken(_token: address) -> bool: view
    def setRateOverride(_targetRate: uint256): nonpayable
    def setPaymentToken(_token: address): nonpayable
    def setCanBuyNow(_canBuyNow: bool): nonpayable
    def bondConfig() -> InstantBondConfig: view
    def canCancelRateOverride() -> bool: view
    def cancelRateOverride(): nonpayable
    def isRunning() -> bool: view
    def CLAIMS() -> address: view
    def stop(): nonpayable

interface InstantBondClaims:
    def setRemainingAllocationBudget(_amount: uint256): nonpayable

interface RipeHq:
    def getAddr(_regId: uint256) -> address: view

flag ActionType:
    INSTANT_BOND_CONFIG
    RATE_OVERRIDE_SET
    RATE_OVERRIDE_CANCEL
    REMAINING_ALLOCATION_BUDGET_SET

struct InstantBondConfig:
    canBuyNow: bool
    paymentCapPerEpoch: uint256
    minPaymentAmount: uint256
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
    maxVestingBonus: uint256
    minVestingLength: uint256
    maxVestingLength: uint256
    epochLength: uint256

event PendingInstantBondConfigSet:
    actionId: uint256
    confirmationBlock: uint256
    canBuyNow: bool
    paymentCapPerEpoch: uint256
    minPaymentAmount: uint256
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
    maxVestingBonus: uint256
    minVestingLength: uint256
    maxVestingLength: uint256
    epochLength: uint256

event InstantBondConfigExecuted:
    actionId: uint256

event PendingInstantBondRemainingAllocationBudgetSet:
    actionId: uint256
    confirmationBlock: uint256
    amount: uint256

event InstantBondRemainingAllocationBudgetExecuted:
    actionId: uint256

event PendingRateOverrideSet:
    actionId: uint256
    confirmationBlock: uint256
    targetRate: uint256

event PendingRateOverrideCancellationSet:
    actionId: uint256
    confirmationBlock: uint256

event RateOverrideExecuted:
    actionId: uint256

event RateOverrideCancellationExecuted:
    actionId: uint256

event InstantBondStarted:
    genesisBlock: uint256
    epochLength: uint256

event InstantBondPaymentTokenSet:
    token: indexed(address)

event InstantBondCanBuyNowSet:
    canBuyNow: bool

# pending actions
actionType: public(HashMap[uint256, ActionType]) # aid -> type
pendingConfig: public(HashMap[uint256, InstantBondConfig]) # aid -> config
pendingRemainingAllocationBudget: public(HashMap[uint256, uint256]) # aid -> amount
pendingRateOverride: public(HashMap[uint256, uint256]) # aid -> target rate

INSTANT_BOND_LANE_ID: constant(uint256) = 26


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
def _getInstantBondLaneAddr() -> address:
    lane: address = staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(INSTANT_BOND_LANE_ID)
    assert lane != empty(address) # dev: invalid lane
    return lane


#######################
# Instant Bond Config #
#######################


@external
def setInstantBondConfig(_config: InstantBondConfig) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    lane: address = self._getInstantBondLaneAddr()
    assert staticcall InstantBondLane(lane).isValidConfig(_config) # dev: invalid config

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.INSTANT_BOND_CONFIG
    self.pendingConfig[aid] = _config

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingInstantBondConfigSet(
        actionId=aid,
        confirmationBlock=confirmationBlock,
        canBuyNow=_config.canBuyNow,
        paymentCapPerEpoch=_config.paymentCapPerEpoch,
        minPaymentAmount=_config.minPaymentAmount,
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
        maxVestingBonus=_config.maxVestingBonus,
        minVestingLength=_config.minVestingLength,
        maxVestingLength=_config.maxVestingLength,
        epochLength=_config.epochLength,
    )
    return aid


# can buy now


@external
def setCanBuyNow(_canBuyNow: bool):
    assert gov._canGovern(msg.sender) # dev: no perms

    lane: address = self._getInstantBondLaneAddr()
    config: InstantBondConfig = staticcall InstantBondLane(lane).bondConfig()
    assert config.canBuyNow != _canBuyNow # dev: no change
    extcall InstantBondLane(lane).setCanBuyNow(_canBuyNow)
    log InstantBondCanBuyNowSet(canBuyNow=_canBuyNow)


#################
# Rate Override #
#################


@external
def setInstantBondRateOverride(_targetRate: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    lane: address = self._getInstantBondLaneAddr()
    assert staticcall InstantBondLane(lane).isValidRateOverride(_targetRate) # dev: invalid rate override

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.RATE_OVERRIDE_SET
    self.pendingRateOverride[aid] = _targetRate

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingRateOverrideSet(
        actionId=aid,
        confirmationBlock=confirmationBlock,
        targetRate=_targetRate,
    )
    return aid


@external
def cancelInstantBondRateOverride() -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    lane: address = self._getInstantBondLaneAddr()
    assert staticcall InstantBondLane(lane).canCancelRateOverride() # dev: no rate override

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.RATE_OVERRIDE_CANCEL

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingRateOverrideCancellationSet(
        actionId=aid,
        confirmationBlock=confirmationBlock,
    )
    return aid


#########
# Start #
#########


@external
def startInstantBond(_genesisBlock: uint256, _epochLength: uint256):
    assert gov._canGovern(msg.sender) # dev: no perms

    lane: address = self._getInstantBondLaneAddr()
    assert not staticcall InstantBondLane(lane).isRunning() # dev: already running
    assert staticcall InstantBondLane(lane).isValidEpochLength(_epochLength) # dev: invalid epoch length
    assert staticcall InstantBondLane(lane).isValidConfig(staticcall InstantBondLane(lane).bondConfig()) # dev: not configured
    extcall InstantBondLane(lane).start(_genesisBlock, _epochLength)
    log InstantBondStarted(genesisBlock=_genesisBlock, epochLength=_epochLength)


@external
def stopInstantBond():
    assert gov._canGovern(msg.sender) # dev: no perms

    lane: address = self._getInstantBondLaneAddr()
    assert staticcall InstantBondLane(lane).isRunning() # dev: not running
    extcall InstantBondLane(lane).stop()


#################
# Payment Token #
#################


@external
def setInstantBondPaymentToken(_token: address):
    assert gov._canGovern(msg.sender) # dev: no perms

    lane: address = self._getInstantBondLaneAddr()
    assert staticcall InstantBondLane(lane).isValidPaymentToken(_token) # dev: invalid payment token
    extcall InstantBondLane(lane).setPaymentToken(_token)
    log InstantBondPaymentTokenSet(token=_token)


#####################
# Allocation Budget #
#####################


@external
def setInstantBondRemainingAllocationBudget(_amount: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    lane: address = self._getInstantBondLaneAddr()
    assert staticcall InstantBondLane(lane).CLAIMS() != empty(address) # dev: invalid claims

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.REMAINING_ALLOCATION_BUDGET_SET
    self.pendingRemainingAllocationBudget[aid] = _amount

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingInstantBondRemainingAllocationBudgetSet(
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
    lane: address = self._getInstantBondLaneAddr()

    if actionType == ActionType.INSTANT_BOND_CONFIG:
        assert staticcall InstantBondLane(lane).isValidConfig(self.pendingConfig[_aid]) # dev: invalid config
        extcall InstantBondLane(lane).setConfig(self.pendingConfig[_aid])
        log InstantBondConfigExecuted(actionId=_aid)
    elif actionType == ActionType.RATE_OVERRIDE_SET:
        assert staticcall InstantBondLane(lane).isValidRateOverride(self.pendingRateOverride[_aid]) # dev: invalid rate override
        extcall InstantBondLane(lane).setRateOverride(self.pendingRateOverride[_aid])
        log RateOverrideExecuted(actionId=_aid)
    elif actionType == ActionType.RATE_OVERRIDE_CANCEL:
        assert staticcall InstantBondLane(lane).canCancelRateOverride() # dev: no rate override
        extcall InstantBondLane(lane).cancelRateOverride()
        log RateOverrideCancellationExecuted(actionId=_aid)
    else:
        claims: address = staticcall InstantBondLane(lane).CLAIMS()
        assert claims != empty(address) # dev: invalid claims
        extcall InstantBondClaims(claims).setRemainingAllocationBudget(self.pendingRemainingAllocationBudget[_aid])
        log InstantBondRemainingAllocationBudgetExecuted(actionId=_aid)

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
    assert timeLock._cancelAction(_aid) # dev: cannot cancel action
    self.actionType[_aid] = empty(ActionType)
