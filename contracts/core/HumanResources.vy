#               ___          ___     
#              /__/\        /  /\    
#              \  \:\      /  /::\   
#               \__\:\    /  /:/\:\  
#           ___ /  /::\  /  /:/~/:/  
#          /__/\  /:/\:\/__/:/ /:/___
#          \  \:\/:/__\/\  \:\/:::::/
#           \  \::/      \  \::/~~~~ 
#            \  \:\       \  \:\     
#             \  \:\       \  \:\    
#              \__\/        \__\/    

#     ╔═══════════════════════════════════════════════╗
#     ║  ** Human Resources **                        ║
#     ║  Handles compensation for human contributors  ║
#     ╚═══════════════════════════════════════════════╝
#
#     Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
#     Ripe Foundation (C) 2025

# @version 0.4.3

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
import interfaces.ConfigStructs as cs

from interfaces import Vault
from interfaces import Department
from ethereum.ercs import IERC20

interface Ledger:
    def addHrContributor(_contributor: address, _compensation: uint256): nonpayable
    def addVaultToUser(_user: address, _vaultId: uint256): nonpayable
    def consumeHrContributorCash(_mintableReduction: uint256, _liabilityReduction: uint256): nonpayable
    def applyHrContributorSettlement(_budgetCredit: uint256, _mintableRelease: uint256, _liabilityRelease: uint256): nonpayable
    def isHrContributor(_contributor: address) -> bool: view
    def contributors(i: uint256) -> address: view
    def numContributors() -> uint256: view
    def ripeAvailForHr() -> uint256: view

interface RipeGovVault:
    def transferContributorRipeTokens(_contributor: address, _toUser: address, _lockDuration: uint256, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def withdrawContributorTokensToBurn(_user: address, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable

interface RipeToken:
    def mint(_to: address, _amount: uint256): nonpayable
    def burn(_amount: uint256) -> bool: nonpayable

interface MissionControl:
    def coreRipeGovVaultId() -> uint256: view
    def hrConfig() -> cs.HrConfig: view

interface HrContributor:
    def totalClaimed() -> uint256: view
    def compensation() -> uint256: view

interface Teller:
    def depositFromTrusted(_user: address, _vaultId: uint256, _asset: address, _amount: uint256, _lockDuration: uint256, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable

interface Lootbox:
    def updateDepositPoints(_user: address, _vaultId: uint256, _vaultAddr: address, _asset: address, _a: addys.Addys = empty(addys.Addys)): nonpayable

interface VaultBook:
    def getAddr(_vaultId: uint256) -> address: view

struct ContributorTerms:
    owner: address
    manager: address
    compensation: uint256
    startDelay: uint256
    vestingLength: uint256
    cliffLength: uint256
    unlockLength: uint256
    depositLockDuration: uint256

struct HrGrant:
    initialized: bool
    remainingMintable: uint256
    cancelCreditLiability: uint256
    mintedPaycheck: uint256
    cliffTime: uint256
    settled: bool

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
# Fresh HR/Ledger deploy only. Pre-existing Ledger contributors have
# initialized=False and cannot cash or refund until a separate migration.
hrGrant: public(HashMap[address, HrGrant])


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
    hrConfig: cs.HrConfig = staticcall MissionControl(a.missionControl).hrConfig()
    assert self._areValidContributorTerms(terms, hrConfig, a.ledger) # dev: invalid terms

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

    hrConfig: cs.HrConfig = staticcall MissionControl(a.missionControl).hrConfig()
    if not self._areValidContributorTerms(terms, hrConfig, a.ledger):
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

    self.hrGrant[contributorAddr] = HrGrant(
        initialized=True,
        remainingMintable=terms.compensation,
        cancelCreditLiability=terms.compensation,
        mintedPaycheck=0,
        cliffTime=block.timestamp + terms.startDelay + terms.cliffLength,
        settled=False,
    )

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

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(_aid)
    self._cancelNewPendingContributor(_aid)

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
    hrConfig: cs.HrConfig = staticcall MissionControl(a.missionControl).hrConfig()
    return self._areValidContributorTerms(terms, hrConfig, a.ledger)


@view
@internal
def _areValidContributorTerms(_terms: ContributorTerms, _hrConfig: cs.HrConfig, _ledger: address) -> bool:

    # must have a template
    if _hrConfig.contribTemplate == empty(address):
        return False

    # compensation check
    if _terms.compensation == 0:
        return False

    # check what's available for HR
    if _terms.compensation > staticcall Ledger(_ledger).ripeAvailForHr():
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

    if _terms.compensation > max_value(uint256) // 2:
        return False
    if _terms.vestingLength > 2 ** 128:
        return False
    if _terms.depositLockDuration > max_value(uint256) - 2 ** 64:
        return False
    if _terms.startDelay > max_value(uint256) - block.timestamp:
        return False
    startTime: uint256 = block.timestamp + _terms.startDelay
    if _terms.vestingLength > max_value(uint256) - startTime:
        return False
    if _terms.cliffLength > max_value(uint256) - startTime:
        return False
    if _terms.unlockLength > max_value(uint256) - startTime:
        return False

    return True


####################
# From Contributor #
####################


# views


@view
@external
def canModifyHrContributor(_addr: address) -> bool:
    return addys._isSwitchboardAddr(_addr)


@view
@external
def hasRipeBalance(_contributor: address) -> bool:
    a: addys.Addys = addys._getAddys()
    vaultId: uint256 = self._getCoreRipeGovVaultId(a.missionControl)
    ripeGovVaultAddr: address = staticcall VaultBook(a.vaultBook).getAddr(vaultId)
    return staticcall Vault(ripeGovVaultAddr).doesUserHaveBalance(_contributor, a.ripeToken)


# transfer ripe tokens


@external
def transferContributorRipeTokens(_owner: address, _lockDuration: uint256) -> uint256:
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()
    assert staticcall Ledger(a.ledger).isHrContributor(msg.sender) # dev: not a contributor

    # transfer tokens in ripe gov vault
    vaultId: uint256 = self._getCoreRipeGovVaultId(a.missionControl)
    ripeGovVaultAddr: address = staticcall VaultBook(a.vaultBook).getAddr(vaultId) 
    amount: uint256 = extcall RipeGovVault(ripeGovVaultAddr).transferContributorRipeTokens(msg.sender, _owner, _lockDuration, a)

    extcall Ledger(a.ledger).addVaultToUser(_owner, vaultId)
    extcall Lootbox(a.lootbox).updateDepositPoints(msg.sender, vaultId, ripeGovVaultAddr, a.ripeToken, a)
    extcall Lootbox(a.lootbox).updateDepositPoints(_owner, vaultId, ripeGovVaultAddr, a.ripeToken, a)
    return amount


# cash ripe check


@external
def cashRipeCheck(_amount: uint256, _lockDuration: uint256) -> bool:
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()
    assert staticcall Ledger(a.ledger).isHrContributor(msg.sender) # dev: not a contributor

    g: HrGrant = self.hrGrant[msg.sender]
    assert g.initialized # dev: hr grant not initialized
    assert not g.settled # dev: hr grant settled
    assert _amount <= g.remainingMintable # dev: hr reserve underflow
    g.remainingMintable -= _amount
    g.mintedPaycheck += _amount
    liabilityReduce: uint256 = 0
    if block.timestamp >= g.cliffTime:
        if g.cancelCreditLiability > g.remainingMintable:
            liabilityReduce = g.cancelCreditLiability - g.remainingMintable
            g.cancelCreditLiability = g.remainingMintable
    if g.remainingMintable == 0 and g.cancelCreditLiability == 0:
        g.settled = True
    self.hrGrant[msg.sender] = g
    extcall Ledger(a.ledger).consumeHrContributorCash(_amount, liabilityReduce)

    # mint ripe tokens here
    extcall RipeToken(a.ripeToken).mint(self, _amount)

    # deposit into gov vault
    assert extcall IERC20(a.ripeToken).approve(a.teller, _amount, default_return_value=True) # dev: ripe approval failed
    vaultId: uint256 = self._getCoreRipeGovVaultId(a.missionControl)
    extcall Teller(a.teller).depositFromTrusted(msg.sender, vaultId, a.ripeToken, _amount, _lockDuration, a)
    assert extcall IERC20(a.ripeToken).approve(a.teller, 0, default_return_value=True) # dev: ripe approval failed
    return True


# refund after cancel paycheck


@external
def refundAfterCancelPaycheck(_amount: uint256, _shouldBurnPosition: bool):
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()
    assert staticcall Ledger(a.ledger).isHrContributor(msg.sender) # dev: not a contributor

    g: HrGrant = self.hrGrant[msg.sender]
    assert g.initialized # dev: hr grant not initialized
    assert not g.settled # dev: hr grant settled

    actualBurned: uint256 = 0
    if _shouldBurnPosition:
        vaultId: uint256 = self._getCoreRipeGovVaultId(a.missionControl)
        ripeGovVaultAddr: address = staticcall VaultBook(a.vaultBook).getAddr(vaultId)
        withdrawalAmount: uint256 = extcall RipeGovVault(ripeGovVaultAddr).withdrawContributorTokensToBurn(msg.sender, a)
        extcall Lootbox(a.lootbox).updateDepositPoints(msg.sender, vaultId, ripeGovVaultAddr, a.ripeToken, a)
        burnAmount: uint256 = min(withdrawalAmount, staticcall IERC20(a.ripeToken).balanceOf(self))
        if burnAmount != 0:
            assert extcall RipeToken(a.ripeToken).burn(burnAmount) # dev: ripe burn failed
            actualBurned = burnAmount

    mintableRelease: uint256 = min(_amount, g.remainingMintable)
    extraWanted: uint256 = _amount - mintableRelease
    maxExtra: uint256 = min(g.mintedPaycheck, actualBurned)
    assert extraWanted <= maxExtra # dev: hr reserve underflow
    budgetCredit: uint256 = _amount

    g.remainingMintable -= mintableRelease
    liabilityRelease: uint256 = 0
    if g.remainingMintable == 0:
        liabilityRelease = g.cancelCreditLiability
        g.cancelCreditLiability = 0
        g.settled = True
    else:
        liabilityRelease = mintableRelease
        assert g.cancelCreditLiability >= liabilityRelease
        g.cancelCreditLiability -= liabilityRelease

    self.hrGrant[msg.sender] = g
    extcall Ledger(a.ledger).applyHrContributorSettlement(
        budgetCredit,
        mintableRelease,
        liabilityRelease,
    )


#########
# Other #
#########


@view
@internal
def _getCoreRipeGovVaultId(_missionControl: address) -> uint256:
    vaultId: uint256 = staticcall MissionControl(_missionControl).coreRipeGovVaultId()
    assert vaultId != 0 # dev: invalid vault id
    return vaultId


@view
@external
def getTotalClaimed() -> uint256:
    ledger: address = addys._getLedgerAddr()

    numContributors: uint256 = staticcall Ledger(ledger).numContributors()
    if numContributors == 0:
        return 0

    totalClaimed: uint256 = 0
    for i: uint256 in range(1, numContributors, bound=max_value(uint256)):
        contributorAddr: address = staticcall Ledger(ledger).contributors(i)
        if contributorAddr == empty(address):
            continue
        claimed: uint256 = staticcall HrContributor(contributorAddr).totalClaimed()
        if totalClaimed > max_value(uint256) - claimed:
            return max_value(uint256)
        totalClaimed += claimed

    return totalClaimed


@view
@external
def getTotalCompensation() -> uint256:
    ledger: address = addys._getLedgerAddr()

    numContributors: uint256 = staticcall Ledger(ledger).numContributors()
    if numContributors == 0:
        return 0

    totalCompensation: uint256 = 0
    for i: uint256 in range(1, numContributors, bound=max_value(uint256)):
        contributorAddr: address = staticcall Ledger(ledger).contributors(i)
        if contributorAddr == empty(address):
            continue
        compensation: uint256 = staticcall HrContributor(contributorAddr).compensation()
        if totalCompensation > max_value(uint256) - compensation:
            return max_value(uint256)
        totalCompensation += compensation

    return totalCompensation