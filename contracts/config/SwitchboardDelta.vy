# @version 0.4.1
# pragma optimize codesize

exports: gov.__interface__
exports: timeLock.__interface__

initializes: gov
initializes: timeLock[gov := gov]

import contracts.modules.LocalGov as gov
import contracts.modules.TimeLock as timeLock
from interfaces import Vault

interface HrContributor:
    def setIsFrozen(_shouldFreeze: bool) -> bool: nonpayable
    def setManager(_manager: address) -> bool: nonpayable
    def cancelOwnershipChange() -> bool: nonpayable
    def cancelRipeTransfer() -> bool: nonpayable
    def cashRipeCheck() -> uint256: nonpayable
    def cancelPaycheck() -> bool: nonpayable

interface MissionControl:
    def canPerformLiteAction(_user: address) -> bool: view
    def setHrConfig(_config: HrConfig): nonpayable
    def hrConfig() -> HrConfig: view

interface Ledger:
    def isHrContributor(_contributor: address) -> bool: view

interface RipeHq:
    def getAddr(_regId: uint256) -> address: view

flag ActionType:
    HR_CONFIG_TEMPLATE
    HR_CONFIG_MAX_COMP
    HR_CONFIG_MIN_CLIFF
    HR_CONFIG_MAX_START_DELAY
    HR_CONFIG_VESTING
    HR_MANAGER
    HR_CANCEL_PAYCHECK

struct HrConfig:
    contribTemplate: address
    maxCompensation: uint256
    minCliffLength: uint256
    maxStartDelay: uint256
    minVestingLength: uint256
    maxVestingLength: uint256

struct PendingManager:
    contributor: address
    pendingManager: address

struct PendingCancelPaycheck:
    contributor: address
    pendingShouldCancel: bool

event PendingHrContribTemplateChange:
    contribTemplate: indexed(address)
    confirmationBlock: uint256
    actionId: uint256

event PendingHrMaxCompensationChange:
    maxCompensation: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingHrMinCliffLengthChange:
    minCliffLength: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingHrMaxStartDelayChange:
    maxStartDelay: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingHrVestingLengthBoundariesChange:
    minVestingLength: uint256
    maxVestingLength: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingManagerSet:
    contributor: indexed(address)
    manager: indexed(address)
    confirmationBlock: uint256
    actionId: uint256

event PendingCancelPaycheckSet:
    contributor: indexed(address)
    confirmationBlock: uint256
    actionId: uint256

event RipeCheckCashedFromSwitchboard:
    contributor: indexed(address)
    cashedBy: indexed(address)
    amount: uint256

event RipeTransferCancelledFromSwitchboard:
    contributor: indexed(address)
    cancelledBy: indexed(address)

event OwnershipChangeCancelledFromSwitchboard:
    contributor: indexed(address)
    cancelledBy: indexed(address)

event ContributorFrozenFromSwitchboard:
    contributor: indexed(address)
    frozenBy: indexed(address)
    shouldFreeze: bool

event HrContribTemplateSet:
    contribTemplate: indexed(address)

event HrMaxCompensationSet:
    maxCompensation: uint256

event HrMinCliffLengthSet:
    minCliffLength: uint256

event HrMaxStartDelaySet:
    maxStartDelay: uint256

event HrVestingLengthBoundariesSet:
    minVestingLength: uint256
    maxVestingLength: uint256

event HrContributorManagerSet:
    contributor: indexed(address)
    manager: indexed(address)

event HrContributorCancelPaycheckSet:
    contributor: indexed(address)

# pending config changes
actionType: public(HashMap[uint256, ActionType]) # aid -> type
pendingHrConfig: public(HashMap[uint256, HrConfig]) # aid -> config
pendingManager: public(HashMap[uint256, PendingManager]) # aid -> pending manager
pendingCancelPaycheck: public(HashMap[uint256, address]) # aid -> contributor

LEDGER_ID: constant(uint256) = 4
MISSION_CONTROL_ID: constant(uint256) = 5
EIGHTEEN_DECIMALS: constant(uint256) = 10 ** 18

# timestamp units (not blocks!)
DAY_IN_SECONDS: constant(uint256) = 60 * 60 * 24
WEEK_IN_SECONDS: constant(uint256) = 7 * DAY_IN_SECONDS
MONTH_IN_SECONDS: constant(uint256) = 30 * DAY_IN_SECONDS
YEAR_IN_SECONDS: constant(uint256) = 365 * DAY_IN_SECONDS



@deploy
def __init__(
    _ripeHq: address,
    _minConfigTimeLock: uint256,
    _maxConfigTimeLock: uint256,
):
    gov.__init__(_ripeHq, empty(address), 0, 0, 0)
    timeLock.__init__(_minConfigTimeLock, _maxConfigTimeLock, 0, _maxConfigTimeLock)


# access control


@view
@internal
def _hasPermsToEnable(_caller: address, _isLite: bool) -> bool:
    if gov._canGovern(_caller):
        return True
    if _isLite:
        return staticcall MissionControl(self._getMissionControlAddr()).canPerformLiteAction(_caller)
    return False


# addys lite


@view
@internal
def _getMissionControlAddr() -> address:
    return staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(MISSION_CONTROL_ID)


@view
@internal
def _getLedgerAddr() -> address:
    return staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(LEDGER_ID)


#############
# HR Config #
#############


# contrib template


@external
def setContributorTemplate(_contribTemplate: address) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _contribTemplate.is_contract and _contribTemplate != empty(address) # dev: invalid contrib template
    return self._setPendingHrConfig(ActionType.HR_CONFIG_TEMPLATE, _contribTemplate)


# max compensation


@external
def setMaxCompensation(_maxComp: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _maxComp != 0 and _maxComp <= 20_000_000 * EIGHTEEN_DECIMALS # dev: invalid max compensation
    return self._setPendingHrConfig(ActionType.HR_CONFIG_MAX_COMP, empty(address), _maxComp)


# min cliff length


@external
def setMinCliffLength(_minCliffLength: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _minCliffLength > WEEK_IN_SECONDS # dev: invalid min cliff length
    return self._setPendingHrConfig(ActionType.HR_CONFIG_MIN_CLIFF, empty(address), 0, _minCliffLength)


# max start delay


@external
def setMaxStartDelay(_maxStartDelay: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _maxStartDelay <= 3 * MONTH_IN_SECONDS # dev: invalid max start delay
    return self._setPendingHrConfig(ActionType.HR_CONFIG_MAX_START_DELAY, empty(address), 0, 0, _maxStartDelay)


# min vesting length


@external
def setVestingLengthBoundaries(_minVestingLength: uint256, _maxVestingLength: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _minVestingLength < _maxVestingLength # dev: invalid vesting length boundaries
    assert _minVestingLength > MONTH_IN_SECONDS # dev: invalid min vesting length
    assert _maxVestingLength <= 5 * YEAR_IN_SECONDS # dev: invalid max vesting length
    return self._setPendingHrConfig(ActionType.HR_CONFIG_VESTING, empty(address), 0, 0, 0, _minVestingLength, _maxVestingLength)


# set pending hr config


@internal
def _setPendingHrConfig(
    _actionType: ActionType,
    _contribTemplate: address = empty(address),
    _maxCompensation: uint256 = 0,
    _minCliffLength: uint256 = 0,
    _maxStartDelay: uint256 = 0,
    _minVestingLength: uint256 = 0,
    _maxVestingLength: uint256 = 0,
) -> uint256:
    aid: uint256 = timeLock._initiateAction()

    self.actionType[aid] = _actionType
    self.pendingHrConfig[aid] = HrConfig(
        contribTemplate=_contribTemplate,
        maxCompensation=_maxCompensation,
        minCliffLength=_minCliffLength,
        maxStartDelay=_maxStartDelay,
        minVestingLength=_minVestingLength,
        maxVestingLength=_maxVestingLength,
    )

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    if _actionType == ActionType.HR_CONFIG_TEMPLATE:
        log PendingHrContribTemplateChange(
            contribTemplate=_contribTemplate,
            confirmationBlock=confirmationBlock,
            actionId=aid,
        )
    elif _actionType == ActionType.HR_CONFIG_MAX_COMP:
        log PendingHrMaxCompensationChange(
            maxCompensation=_maxCompensation,
            confirmationBlock=confirmationBlock,
            actionId=aid,
        )
    elif _actionType == ActionType.HR_CONFIG_MIN_CLIFF:
        log PendingHrMinCliffLengthChange(
            minCliffLength=_minCliffLength,
            confirmationBlock=confirmationBlock,
            actionId=aid,
        )
    elif _actionType == ActionType.HR_CONFIG_MAX_START_DELAY:
        log PendingHrMaxStartDelayChange(
            maxStartDelay=_maxStartDelay,
            confirmationBlock=confirmationBlock,
            actionId=aid,
        )
    elif _actionType == ActionType.HR_CONFIG_VESTING:
        log PendingHrVestingLengthBoundariesChange(
            minVestingLength=_minVestingLength,
            maxVestingLength=_maxVestingLength,
            confirmationBlock=confirmationBlock,
            actionId=aid,
        )
    return aid


#######################
# Contributor Options #
#######################


# cancel paycheck


@external
def cancelPaycheckForContributor(_contributor: address) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert staticcall Ledger(self._getLedgerAddr()).isHrContributor(_contributor) # dev: not a contributor
    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.HR_CANCEL_PAYCHECK
    self.pendingCancelPaycheck[aid] = _contributor
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingCancelPaycheckSet(contributor=_contributor, confirmationBlock=confirmationBlock, actionId=aid)
    return aid


# set manager


@external
def setManagerForContributor(_contributor: address, _manager: address) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _manager != empty(address) # dev: invalid manager
    assert staticcall Ledger(self._getLedgerAddr()).isHrContributor(_contributor) # dev: not a contributor
    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.HR_MANAGER
    self.pendingManager[aid] = PendingManager(contributor=_contributor, pendingManager=_manager)
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingManagerSet(contributor=_contributor, manager=_manager, confirmationBlock=confirmationBlock, actionId=aid)
    return aid


# lite actions


@external
def cashRipeCheckForContributor(_contributor: address) -> bool:
    assert self._hasPermsToEnable(msg.sender, True) # dev: no perms
    amount: uint256 = extcall HrContributor(_contributor).cashRipeCheck()
    log RipeCheckCashedFromSwitchboard(contributor=_contributor, cashedBy=msg.sender, amount=amount)
    return True


@external
def cancelRipeTransferForContributor(_contributor: address) -> bool:
    assert self._hasPermsToEnable(msg.sender, True) # dev: no perms
    extcall HrContributor(_contributor).cancelRipeTransfer()
    log RipeTransferCancelledFromSwitchboard(contributor=_contributor, cancelledBy=msg.sender)
    return True


@external
def cancelOwnershipChangeForContributor(_contributor: address) -> bool:
    assert self._hasPermsToEnable(msg.sender, True) # dev: no perms
    extcall HrContributor(_contributor).cancelOwnershipChange()
    log OwnershipChangeCancelledFromSwitchboard(contributor=_contributor, cancelledBy=msg.sender)
    return True


@external
def freezeContributor(_contributor: address, _shouldFreeze: bool) -> bool:
    assert self._hasPermsToEnable(msg.sender, _shouldFreeze) # dev: no perms
    extcall HrContributor(_contributor).setIsFrozen(_shouldFreeze)
    log ContributorFrozenFromSwitchboard(contributor=_contributor, frozenBy=msg.sender, shouldFreeze=_shouldFreeze)
    return True


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
    mc: address = self._getMissionControlAddr()

    if actionType == ActionType.HR_CONFIG_TEMPLATE:
        config: HrConfig = staticcall MissionControl(mc).hrConfig()
        config.contribTemplate = self.pendingHrConfig[_aid].contribTemplate
        extcall MissionControl(mc).setHrConfig(config)
        log HrContribTemplateSet(contribTemplate=config.contribTemplate)

    elif actionType == ActionType.HR_CONFIG_MAX_COMP:
        config: HrConfig = staticcall MissionControl(mc).hrConfig()
        p: HrConfig = self.pendingHrConfig[_aid]
        config.maxCompensation = p.maxCompensation
        extcall MissionControl(mc).setHrConfig(config)
        log HrMaxCompensationSet(maxCompensation=p.maxCompensation)

    elif actionType == ActionType.HR_CONFIG_MIN_CLIFF:
        config: HrConfig = staticcall MissionControl(mc).hrConfig()
        p: HrConfig = self.pendingHrConfig[_aid]
        config.minCliffLength = p.minCliffLength
        extcall MissionControl(mc).setHrConfig(config)
        log HrMinCliffLengthSet(minCliffLength=p.minCliffLength)

    elif actionType == ActionType.HR_CONFIG_MAX_START_DELAY:
        config: HrConfig = staticcall MissionControl(mc).hrConfig()
        p: HrConfig = self.pendingHrConfig[_aid]
        config.maxStartDelay = p.maxStartDelay
        extcall MissionControl(mc).setHrConfig(config)
        log HrMaxStartDelaySet(maxStartDelay=p.maxStartDelay)

    elif actionType == ActionType.HR_CONFIG_VESTING:
        config: HrConfig = staticcall MissionControl(mc).hrConfig()
        p: HrConfig = self.pendingHrConfig[_aid]
        config.minVestingLength = p.minVestingLength
        config.maxVestingLength = p.maxVestingLength
        extcall MissionControl(mc).setHrConfig(config)
        log HrVestingLengthBoundariesSet(minVestingLength=p.minVestingLength, maxVestingLength=p.maxVestingLength)

    elif actionType == ActionType.HR_MANAGER:
        p: PendingManager = self.pendingManager[_aid]
        extcall HrContributor(p.contributor).setManager(p.pendingManager)
        log HrContributorManagerSet(contributor=p.contributor, manager=p.pendingManager)

    elif actionType == ActionType.HR_CANCEL_PAYCHECK:
        p: address = self.pendingCancelPaycheck[_aid]
        extcall HrContributor(p).cancelPaycheck()
        log HrContributorCancelPaycheckSet(contributor=p)

    self.actionType[_aid] = empty(ActionType)
    return True


# cancel action


@external
def cancelPendingAction(_aid: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    self._cancelPendingAction(_aid)
    return True


@internal
def _cancelPendingAction(_aid: uint256):
    assert timeLock._cancelAction(_aid) # dev: cannot cancel action
    self.actionType[_aid] = empty(ActionType)


