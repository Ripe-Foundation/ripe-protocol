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
    def genesisBlock() -> uint256: view
    def isValidRateOverride(_targetBasePayoutRate: uint256, _targetEpoch: uint256) -> bool: view
    def isValidConfig(_config: InstantBondConfig) -> bool: view
    def isValidEpochLength(_epochLength: uint256) -> bool: view
    def setConfig(_newConfig: InstantBondConfig): nonpayable
    def isValidPaymentToken(_token: address) -> bool: view
    def setRateOverride(_targetBasePayoutRate: uint256, _targetEpoch: uint256) -> uint256: nonpayable
    def setPaymentToken(_token: address): nonpayable
    def setCanBuyNow(_canBuyNow: bool): nonpayable
    def canBuyNow() -> bool: view
    def bondConfig() -> InstantBondConfig: view
    def overrideTargetBasePayoutRate() -> uint256: view
    def overrideTargetEpoch() -> uint256: view
    def cancelRateOverride(): nonpayable
    def isRunning() -> bool: view
    def stop(): nonpayable

interface InstantBondClaims:
    def setRemainingAllocationBudget(_amount: uint256): nonpayable

interface RipeHq:
    def getAddr(_regId: uint256) -> address: view

flag ActionType:
    INSTANT_BOND_CONFIG
    REMAINING_ALLOCATION_BUDGET_SET

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

event PendingInstantBondConfigSet:
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

event InstantBondConfigExecuted:
    actionId: uint256

event PendingInstantBondRemainingAllocationBudgetSet:
    actionId: uint256
    confirmationBlock: uint256
    amount: uint256

event InstantBondRemainingAllocationBudgetExecuted:
    actionId: uint256

event InstantBondRateOverrideSet:
    targetEpoch: indexed(uint256)
    targetBasePayoutRate: uint256

event InstantBondRateOverrideCancelled:
    targetEpoch: indexed(uint256)
    targetBasePayoutRate: uint256

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

INSTANT_BOND_LANE_ID: constant(uint256) = 26
INSTANT_BOND_CLAIMS_ID: constant(uint256) = 27


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


@view
@internal
def _getInstantBondClaimsAddr() -> address:
    claims: address = staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(INSTANT_BOND_CLAIMS_ID)
    assert claims != empty(address) and claims.is_contract # dev: invalid claims
    return claims


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


# can buy now


@external
def setCanBuyNow(_canBuyNow: bool):
    assert gov._canGovern(msg.sender) # dev: no perms

    lane: address = self._getInstantBondLaneAddr()
    assert staticcall InstantBondLane(lane).canBuyNow() != _canBuyNow # dev: no change
    extcall InstantBondLane(lane).setCanBuyNow(_canBuyNow)
    log InstantBondCanBuyNowSet(canBuyNow=_canBuyNow)


#################
# Rate Override #
#################


@external
def setInstantBondRateOverride(_targetBasePayoutRate: uint256, _targetEpoch: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    lane: address = self._getInstantBondLaneAddr()
    assert staticcall InstantBondLane(lane).isValidRateOverride(_targetBasePayoutRate, _targetEpoch) # dev: invalid rate override
    resolvedEpoch: uint256 = extcall InstantBondLane(lane).setRateOverride(_targetBasePayoutRate, _targetEpoch)
    log InstantBondRateOverrideSet(
        targetEpoch=resolvedEpoch,
        targetBasePayoutRate=_targetBasePayoutRate,
    )
    return resolvedEpoch


@external
def cancelInstantBondRateOverride():
    assert gov._canGovern(msg.sender) # dev: no perms

    lane: address = self._getInstantBondLaneAddr()
    targetBasePayoutRate: uint256 = staticcall InstantBondLane(lane).overrideTargetBasePayoutRate()
    assert targetBasePayoutRate != 0 # dev: no rate override
    targetEpoch: uint256 = staticcall InstantBondLane(lane).overrideTargetEpoch()
    extcall InstantBondLane(lane).cancelRateOverride()
    log InstantBondRateOverrideCancelled(targetEpoch=targetEpoch, targetBasePayoutRate=targetBasePayoutRate)


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
    resolvedGenesisBlock: uint256 = staticcall InstantBondLane(lane).genesisBlock()
    log InstantBondStarted(genesisBlock=resolvedGenesisBlock, epochLength=_epochLength)


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

    self._getInstantBondClaimsAddr()

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

    if actionType == ActionType.INSTANT_BOND_CONFIG:
        lane: address = self._getInstantBondLaneAddr()
        config: InstantBondConfig = self.pendingConfig[_aid]
        assert staticcall InstantBondLane(lane).isValidConfig(config) # dev: invalid config
        extcall InstantBondLane(lane).setConfig(config)
        self.pendingConfig[_aid] = empty(InstantBondConfig)
        log InstantBondConfigExecuted(actionId=_aid)

    elif actionType == ActionType.REMAINING_ALLOCATION_BUDGET_SET:
        claims: address = self._getInstantBondClaimsAddr()
        amount: uint256 = self.pendingRemainingAllocationBudget[_aid]
        extcall InstantBondClaims(claims).setRemainingAllocationBudget(amount)
        self.pendingRemainingAllocationBudget[_aid] = 0
        log InstantBondRemainingAllocationBudgetExecuted(actionId=_aid)

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

    if actionType == ActionType.INSTANT_BOND_CONFIG:
        self.pendingConfig[_aid] = empty(InstantBondConfig)
    elif actionType == ActionType.REMAINING_ALLOCATION_BUDGET_SET:
        self.pendingRemainingAllocationBudget[_aid] = 0
    else:
        raise "invalid action"

    self.actionType[_aid] = empty(ActionType)
