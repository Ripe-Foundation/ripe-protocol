# @version 0.4.1

implements: Department

exports: addys.__interface__
exports: deptBasics.__interface__
exports: gov.__interface__
exports: timeLock.__interface__

initializes: addys
initializes: deptBasics[addys := addys]
initializes: gov
initializes: timeLock[gov := gov]

import contracts.modules.Addys as addys
import contracts.modules.DeptBasics as deptBasics
import contracts.modules.LocalGov as gov
import contracts.modules.TimeLock as timeLock

from interfaces import Department

interface Ledger:
    def addHrContributor(_contributor: address, _compensation: uint256): nonpayable
    def ripeAvailForHr() -> uint256: view

interface MissionControl:
    def getHrConfig() -> HrConfig: view

struct ContributorTerms:
    owner: address
    manager: address
    compensation: uint256
    startDelay: uint256
    vestingLength: uint256
    cliffLength: uint256
    unlockLength: uint256
    depositLockDuration: uint256

struct HrConfig:
    contribTemplate: address
    maxCompensation: uint256
    minCliffLength: uint256
    maxStartDelay: uint256
    minVestingLength: uint256
    maxVestingLength: uint256
    ripeAvailForHr: uint256

event NewContributorInitiated:
    owner: indexed(address)
    manager: indexed(address)
    compensation: uint256
    startDelay: uint256
    vestingLength: uint256
    cliffLength: uint256
    unlockLength: uint256
    depositLockDuration: uint256
    confirmationBlock: uint256
    actionId: uint256

event NewContributorConfirmed:
    contributorAddr: indexed(address)
    owner: indexed(address)
    manager: indexed(address)
    compensation: uint256
    startDelay: uint256
    vestingLength: uint256
    cliffLength: uint256
    unlockLength: uint256
    depositLockDuration: uint256
    actionId: uint256

event NewContributorCancelled:
    owner: indexed(address)
    manager: indexed(address)
    compensation: uint256
    startDelay: uint256
    vestingLength: uint256
    cliffLength: uint256
    unlockLength: uint256
    depositLockDuration: uint256
    confirmationBlock: uint256
    actionId: uint256

# pending
pendingContributor: public(HashMap[uint256, ContributorTerms]) # aid -> terms


@deploy
def __init__(
    _ripeHq: address,
    _minConfigTimeLock: uint256,
    _maxConfigTimeLock: uint256,
):
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, False, True) # can mint ripe only
    gov.__init__(_ripeHq, empty(address), 0, 0, 0)
    timeLock.__init__(_minConfigTimeLock, _maxConfigTimeLock, 0, _maxConfigTimeLock)


@view
@internal
def _getHrConfig(_missionControl: address, _ledger: address) -> HrConfig:
    hrConfig: HrConfig = staticcall MissionControl(_missionControl).getHrConfig()
    hrConfig.ripeAvailForHr = staticcall Ledger(_ledger).ripeAvailForHr()
    return hrConfig


####################
# New Contributors #
####################


# initiate new contributor


@external
def initiateNewContributor(
    _owner: address,
    _manager: address,
    _compensation: uint256,
    _startDelay: uint256,
    _vestingLength: uint256,
    _cliffLength: uint256,
    _unlockLength: uint256,
    _depositLockDuration: uint256,
) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()

    terms: ContributorTerms = ContributorTerms(
        owner=_owner,
        manager=_manager,
        compensation=_compensation,
        startDelay=_startDelay,
        vestingLength=_vestingLength,
        cliffLength=_cliffLength,
        unlockLength=_unlockLength,
        depositLockDuration=_depositLockDuration,
    )
    hrConfig: HrConfig = self._getHrConfig(a.missionControl, a.ledger)
    assert self._areValidContributorTerms(terms, hrConfig) # dev: invalid terms

    aid: uint256 = timeLock._initiateAction()
    self.pendingContributor[aid] = terms
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log NewContributorInitiated(
        owner=_owner,
        manager=_manager,
        compensation=_compensation,
        startDelay=_startDelay,
        vestingLength=_vestingLength,
        cliffLength=_cliffLength,
        unlockLength=_unlockLength,
        depositLockDuration=_depositLockDuration,
        confirmationBlock=confirmationBlock,
        actionId=aid,
    )
    return aid


# confirm new contributor


@external
def confirmNewContributor(_aid: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()

    terms: ContributorTerms = self.pendingContributor[_aid]
    assert terms.owner != empty(address) # dev: no pending contributor

    hrConfig: HrConfig = self._getHrConfig(a.missionControl, a.ledger)
    if not self._areValidContributorTerms(terms, hrConfig):
        self._cancelNewPendingContributor(_aid)
        return False

    # check time lock
    assert timeLock._confirmAction(_aid) # dev: time lock not reached

    # deploy new contributor
    contributorAddr: address = create_from_blueprint(
        hrConfig.contribTemplate,
        a.hq,
        terms.owner,
        terms.manager,
        terms.compensation,
        terms.startDelay,
        terms.vestingLength,
        terms.cliffLength,
        terms.unlockLength,
        terms.depositLockDuration,
        timeLock.MIN_ACTION_TIMELOCK,
        timeLock.MAX_ACTION_TIMELOCK,
    )
    assert contributorAddr != empty(address) # dev: could not deploy

    # update ledger
    extcall Ledger(a.ledger).addHrContributor(contributorAddr, terms.compensation)

    self.pendingContributor[_aid] = empty(ContributorTerms)
    log NewContributorConfirmed(
        contributorAddr=contributorAddr,
        owner=terms.owner,
        manager=terms.manager,
        compensation=terms.compensation,
        startDelay=terms.startDelay,
        vestingLength=terms.vestingLength,
        cliffLength=terms.cliffLength,
        unlockLength=terms.unlockLength,
        depositLockDuration=terms.depositLockDuration,
        actionId=_aid,
    )
    return True


# cancel contributor


@external
def cancelNewContributor(_aid: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused

    terms: ContributorTerms = self.pendingContributor[_aid]
    assert terms.owner != empty(address) # dev: no pending contributor
    self._cancelNewPendingContributor(_aid)

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(_aid)
    log NewContributorCancelled(
        owner=terms.owner,
        manager=terms.manager,
        compensation=terms.compensation,
        startDelay=terms.startDelay,
        vestingLength=terms.vestingLength,
        cliffLength=terms.cliffLength,
        unlockLength=terms.unlockLength,
        depositLockDuration=terms.depositLockDuration,
        confirmationBlock=confirmationBlock,
        actionId=_aid,
    )
    return True


@internal
def _cancelNewPendingContributor(_aid: uint256):
    assert timeLock._cancelAction(_aid) # dev: cannot cancel action
    self.pendingContributor[_aid] = empty(ContributorTerms)


####################
# Terms Validation #
####################


@view
@external
def areValidContributorTerms(
    _owner: address,
    _manager: address,
    _compensation: uint256,
    _startDelay: uint256,
    _vestingLength: uint256,
    _cliffLength: uint256,
    _unlockLength: uint256,
    _depositLockDuration: uint256,
) -> bool:
    a: addys.Addys = addys._getAddys()
    terms: ContributorTerms = ContributorTerms(
        owner=_owner,
        manager=_manager,
        compensation=_compensation,
        startDelay=_startDelay,
        vestingLength=_vestingLength,
        cliffLength=_cliffLength,
        unlockLength=_unlockLength,
        depositLockDuration=_depositLockDuration,
    )
    hrConfig: HrConfig = self._getHrConfig(a.missionControl, a.ledger)
    return self._areValidContributorTerms(terms, hrConfig)


@view
@internal
def _areValidContributorTerms(_terms: ContributorTerms, _hrConfig: HrConfig) -> bool:

    # must have a template
    if _hrConfig.contribTemplate == empty(address):
        return False

    # compensation check
    if _terms.compensation == 0:
        return False

    # check what's available for HR
    if _terms.compensation > _hrConfig.ripeAvailForHr:
        return False

    if _hrConfig.maxCompensation != 0 and _terms.compensation > _hrConfig.maxCompensation:
        return False

    # cliff check
    if _terms.cliffLength == 0:
        return False

    if _hrConfig.minCliffLength != 0 and _terms.cliffLength < _hrConfig.minCliffLength:
        return False

    # vesting check
    if _terms.vestingLength == 0:
        return False

    if _hrConfig.minVestingLength != 0 and _terms.vestingLength < _hrConfig.minVestingLength:
        return False

    if _hrConfig.maxVestingLength != 0 and _terms.vestingLength > _hrConfig.maxVestingLength:
        return False

    if _hrConfig.maxStartDelay != 0 and _terms.startDelay > _hrConfig.maxStartDelay:
        return False

    # unlock cannot be greater than vesting
    if _terms.unlockLength > _terms.vestingLength:
        return False

    # cliff can never be greater than unlock
    if _terms.cliffLength > _terms.unlockLength:
        return False

    if empty(address) in [_terms.owner, _terms.manager]:
        return False

    return True


#####################
# TO DO TO DO TO DO #
#####################


@external
def transferContributorRipeTokens(_owner: address, _lockDuration: uint256) -> uint256:
    # TODO: add vault to ledger, update deposit points, do all the things teller would do
    return 0


@external
def cashRipeCheck(_amount: uint256, _lockDuration: uint256) -> bool:
    # mint, deposit (similar to lootbox deposit)
    return True


@external
def refundAfterCancelPaycheck(_amount: uint256, _shouldBurnPosition: bool):
    # TODO: refund after cancel paycheck
    # burn position in ripe gov vault if _shouldBurnPosition
    pass


@view
@external
def hasRipeBalance(_contributor: address) -> bool:
    # TODO: get balance from vault
    return True


# THINGS TO ADD TO SWITCHBOARD FOUR

# OTHER CONTRIBUTOR THINGS
# cashRipeCheck for contributor
# cancelRipeTransfer for contributor
# cancelOwnershipChange for contributor
# setManager for contributor

# THINGS ONLY HR CAN DO
# setIsFrozen
# cancelPaycheck