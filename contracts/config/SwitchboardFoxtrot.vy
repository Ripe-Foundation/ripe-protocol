#        ______   __     __   __   ______  ______   __  __   ______   ______   ______   ______   _____
#       /\  ___\ /\ \  _ \ \ /\ \ /\__  _\/\  ___\ /\ \_\ \ /\  == \ /\  __ \ /\  __ \ /\  == \ /\  __-.
#       \ \___  \\ \ \/ ".\ \\ \ \\/_/\ \/\ \ \____\ \  __ \\ \  __< \ \ \/\ \\ \  __ \\ \  __< \ \ \/\ \
#        \/\_____\\ \__/".~\_\\ \_\  \ \_\ \ \_____\\ \_\ \_\\ \_____\\ \_____\\ \_\ \_\\ \_\ \_\\ \____-
#         \/_____/ \/_/   \/_/ \/_/   \/_/  \/_____/ \/_/\/_/ \/_____/ \/_____/ \/_/\/_/ \/_/ /_/ \/____/
#                                    ╔═╗┌─┐─┐ ┬┌┬┐┬─┐┌─┐┌┬┐
#                                    ╠╣ │ │┌┴┬┘ │ ├┬┘│ │ │
#                                    ╚  └─┘┴ └─ ┴ ┴└─└─┘ ┴
#
#     ╔════════════════════════════════════════╗
#     ║  ** Switchboard Foxtrot **             ║
#     ║  Instant Bond Lane configuration       ║
#     ╚════════════════════════════════════════╝
#
#     Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
#     Ripe Foundation (C) 2025

# @version 0.4.3

exports: gov.__interface__
exports: timeLock.__interface__

initializes: gov
initializes: timeLock[gov := gov]

import contracts.modules.LocalGov as gov
import contracts.modules.TimeLock as timeLock


# ABI ORDER LOCK: keep byte-for-byte aligned with InstantBondLane.InstantBondConfig.
struct InstantBondConfig:
    canBuyNow: bool
    paymentCapPerEpoch: uint256
    minPaymentAmount: uint256
    mintBudget: uint256
    maxEffectiveRate: uint256
    seedRate: uint256
    uHighBps: uint256
    uLowBps: uint256
    upBps: uint256
    downBps: uint256
    decayBps: uint256
    maxDecayEpochs: uint256
    maxLockBonus: uint256

struct PendingInstantBondConfig:
    config: InstantBondConfig
    expectedVersion: uint256


interface InstantBondLane:
    def isValidConfig(_config: InstantBondConfig) -> bool: view
    def configVersion() -> uint256: view
    def setConfig(_newConfig: InstantBondConfig, _expectedVersion: uint256): nonpayable


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
    upBps: uint256
    downBps: uint256
    decayBps: uint256
    maxDecayEpochs: uint256
    maxLockBonus: uint256

event InstantBondConfigExecuted:
    actionId: uint256
    newVersion: uint256

event InstantBondConfigCancelled:
    actionId: uint256


LANE: public(immutable(address))
pendingConfig: public(HashMap[uint256, PendingInstantBondConfig])


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
    assert _instantBondLane != empty(address) and _instantBondLane.is_contract  # dev: invalid lane
    LANE = _instantBondLane


#################
# Configuration #
#################


@external
def setInstantBondConfig(_config: InstantBondConfig, _expectedVersion: uint256) -> uint256:
    assert gov._canGovern(msg.sender)  # dev: no perms
    assert timeLock.actionTimeLock != 0  # dev: action time lock not set

    lane: address = LANE
    assert staticcall InstantBondLane(lane).isValidConfig(_config)  # dev: invalid config
    assert _expectedVersion == staticcall InstantBondLane(lane).configVersion()  # dev: stale config version

    actionId: uint256 = timeLock._initiateAction()
    self.pendingConfig[actionId] = PendingInstantBondConfig(
        config=_config,
        expectedVersion=_expectedVersion,
    )

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(actionId)
    log PendingInstantBondConfigSet(
        actionId=actionId,
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
        upBps=_config.upBps,
        downBps=_config.downBps,
        decayBps=_config.decayBps,
        maxDecayEpochs=_config.maxDecayEpochs,
        maxLockBonus=_config.maxLockBonus,
    )
    return actionId


#############
# Execution #
#############


@external
def executePendingAction(_actionId: uint256) -> bool:
    assert gov._canGovern(msg.sender)  # dev: no perms

    if not timeLock._confirmAction(_actionId):
        if timeLock._isExpired(_actionId):
            self._cancelPendingAction(_actionId)
        return False

    pending: PendingInstantBondConfig = self.pendingConfig[_actionId]
    extcall InstantBondLane(LANE).setConfig(pending.config, pending.expectedVersion)
    newVersion: uint256 = staticcall InstantBondLane(LANE).configVersion()

    self.pendingConfig[_actionId] = empty(PendingInstantBondConfig)
    log InstantBondConfigExecuted(actionId=_actionId, newVersion=newVersion)
    return True


################
# Cancellation #
################


@external
def cancelPendingAction(_actionId: uint256) -> bool:
    assert gov._canGovern(msg.sender)  # dev: no perms
    self._cancelPendingAction(_actionId)
    return True


@internal
def _cancelPendingAction(_actionId: uint256):
    assert timeLock._cancelAction(_actionId)  # dev: cannot cancel action
    self.pendingConfig[_actionId] = empty(PendingInstantBondConfig)
    log InstantBondConfigCancelled(actionId=_actionId)
