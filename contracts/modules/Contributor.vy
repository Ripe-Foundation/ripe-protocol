# Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
# Ripe Foundation (C) 2025

# @version 0.4.1

interface HumanResources:
    def transferContributorRipeTokens(_owner: address, _lockDuration: uint256) -> uint256: nonpayable
    def refundAfterCancelPaycheck(_amount: uint256, _shouldBurnPosition: bool): nonpayable
    def cashRipeCheck(_amount: uint256, _lockDuration: uint256) -> bool: nonpayable
    def canModifyHrContributor(_addr: address) -> bool: view
    def hasRipeBalance(_contributor: address) -> bool: view

interface RipeGovernance:
    def removeDelegationFor(_recipient: address = empty(address)): nonpayable
    def delegateTo(_recipient: address, _ratio: uint256): nonpayable

interface RipeHq:
    def getAddr(_regId: uint256) -> address: view

struct PendingRipeTransfer:
    recipient: address
    initiatedBlock: uint256
    confirmBlock: uint256

struct PendingOwnerChange:
    newOwner: address
    initiatedBlock: uint256
    confirmBlock: uint256

event RipeCheckCashed:
    owner: indexed(address)
    cashedBy: indexed(address)
    amount: uint256

event RipeTransferInitiated:
    owner: indexed(address)
    confirmBlock: uint256
    initiatedBy: indexed(address)

event RipeTransferConfirmed:
    recipient: indexed(address)
    amount: uint256
    confirmedBy: indexed(address)
    initiatedBlock: uint256

event RipeTransferCancelled:
    recipient: indexed(address)
    cancelledBy: indexed(address)
    initiatedBlock: uint256
    confirmBlock: uint256

event OwnershipChangeInitiated:
    prevOwner: indexed(address)
    newOwner: indexed(address)
    confirmBlock: uint256

event OwnershipChangeConfirmed:
    prevOwner: indexed(address)
    newOwner: indexed(address)
    initiatedBlock: uint256
    confirmBlock: uint256

event OwnershipChangeCancelled:
    cancelledOwner: indexed(address)
    cancelledBy: indexed(address)
    initiatedBlock: uint256
    confirmBlock: uint256

event ManagerModified:
    newManager: indexed(address)
    changedBy: indexed(address)

event KeyActionDelaySet:
    numBlocks: uint256

event DelegationModified:
    govAddr: indexed(address)
    recipient: indexed(address)
    ratio: uint256

event DelegationRemoved:
    govAddr: indexed(address)
    recipient: indexed(address)

event FreezeModified:
    isFrozen: bool

event RipePaycheckCancelled:
    owner: indexed(address)
    forfeitedAmount: uint256
    didReachCliff: bool

# contributor terms
compensation: public(uint256)
startTime: public(uint256)
endTime: public(uint256)
cliffTime: public(uint256)
unlockTime: public(uint256)
depositLockDuration: public(uint256) # num blocks!

# admin
owner: public(address)
manager: public(address)

# important data!
totalClaimed: public(uint256)

# config
keyActionDelay: public(uint256) # num blocks!
isFrozen: public(bool)

# pending changes
pendingOwner: public(PendingOwnerChange)
pendingRipeTransfer: public(PendingRipeTransfer)

HUMAN_RESOURCES_ID: constant(uint256) = 15

RIPE_HQ: immutable(address)
MIN_KEY_ACTION_DELAY: immutable(uint256)
MAX_KEY_ACTION_DELAY: immutable(uint256)


@deploy
def __init__(
    _ripeHq: address,
    _owner: address,
    _manager: address,
    _compensation: uint256,
    _startDelay: uint256,
    _vestingLength: uint256,
    _cliffLength: uint256,
    _unlockLength: uint256,
    _depositLockDuration: uint256,
    _minKeyActionDelay: uint256,
    _maxKeyActionDelay: uint256,
):
    assert _ripeHq != empty(address) # dev: invalid ripe hq
    RIPE_HQ = _ripeHq

    # key terms validation
    assert empty(address) not in [_owner, _manager] # dev: invalid owner / manager
    assert _compensation != 0 # dev: invalid compensation
    assert _vestingLength != 0 # dev: invalid vesting length
    assert _unlockLength <= _vestingLength # dev: unlock must be <= vesting
    assert _cliffLength <= _unlockLength # dev: cliff must be <= unlock

    # set terms
    self.owner = _owner
    self.manager = _manager
    self.compensation = _compensation
    startTime: uint256 = block.timestamp + _startDelay
    self.startTime = startTime
    self.endTime = startTime + _vestingLength
    self.cliffTime = startTime + _cliffLength
    self.unlockTime = startTime + _unlockLength
    self.depositLockDuration = _depositLockDuration

    # key action delays
    assert _minKeyActionDelay < _maxKeyActionDelay # dev: invalid delay
    MIN_KEY_ACTION_DELAY = _minKeyActionDelay
    MAX_KEY_ACTION_DELAY = _maxKeyActionDelay
    self.keyActionDelay = _minKeyActionDelay


# addys


@view
@internal
def _getHrAddr() -> address:
    return staticcall RipeHq(RIPE_HQ).getAddr(HUMAN_RESOURCES_ID)


###################
# Cash Ripe Check #
###################


@external
def cashRipeCheck() -> uint256:
    hr: address = self._getHrAddr()
    owner: address = self.owner
    if msg.sender not in [owner, self.manager]:
        assert staticcall HumanResources(hr).canModifyHrContributor(msg.sender) # dev: no perms
    return self._cashRipeCheck(owner, msg.sender, hr)


@internal
def _cashRipeCheck(
    _owner: address,
    _caller: address,
    _hr: address,
) -> uint256:
    amount: uint256 = self._getClaimable()
    if amount == 0 or self.isFrozen:
        return 0 # can fail gracefully

    # mint ripe, stake in Ripe Gov Vault
    assert extcall HumanResources(_hr).cashRipeCheck(amount, self.depositLockDuration) # dev: could not cash check
    self.totalClaimed += amount

    log RipeCheckCashed(owner=_owner, cashedBy=_caller, amount=amount)
    return amount


#########################
# Transfer Ripe Balance #
#########################


@nonreentrant
@external
def initiateRipeTransfer(_shouldCashCheck: bool = True):
    assert not self.isFrozen # dev: contract frozen

    owner: address = self.owner
    assert msg.sender in [owner, self.manager] # dev: no perms

    # cash latest paycheck (doing this first)
    hr: address = self._getHrAddr()
    if _shouldCashCheck:
        self._cashRipeCheck(owner, msg.sender, hr)

    # important validation
    assert not self._hasPendingOwnerChange() # dev: cannot do with pending ownership change
    assert block.timestamp > self.unlockTime # dev: time not past unlock
    assert staticcall HumanResources(hr).hasRipeBalance(self) # dev: no balance

    # set transfer data
    confirmBlock: uint256 = block.number + self.keyActionDelay
    self.pendingRipeTransfer = PendingRipeTransfer(
        recipient = owner,
        initiatedBlock = block.number,
        confirmBlock = confirmBlock,
    )
    log RipeTransferInitiated(owner=owner, confirmBlock=confirmBlock, initiatedBy=msg.sender)


@nonreentrant
@external
def confirmRipeTransfer(_shouldCashCheck: bool = True):
    assert not self.isFrozen # dev: contract frozen

    owner: address = self.owner
    assert msg.sender in [owner, self.manager] # dev: no perms

    # validation
    assert not self._hasPendingOwnerChange() # dev: cannot do with pending ownership change
    pending: PendingRipeTransfer = self.pendingRipeTransfer
    assert pending.confirmBlock != 0 and block.number >= pending.confirmBlock # dev: time delay not reached

    # cash latest paycheck
    hr: address = self._getHrAddr()
    if _shouldCashCheck:
        self._cashRipeCheck(owner, msg.sender, hr)

    # transfer Ripe position
    amount: uint256 = extcall HumanResources(hr).transferContributorRipeTokens(pending.recipient, self.depositLockDuration) # dev: could not transfer

    # reset pending transfer
    self.pendingRipeTransfer = empty(PendingRipeTransfer)
    log RipeTransferConfirmed(recipient=pending.recipient, amount=amount, confirmedBy=msg.sender, initiatedBlock=pending.initiatedBlock)


@nonreentrant
@external
def cancelRipeTransfer():
    if msg.sender not in [self.owner, self.manager]:
        assert staticcall HumanResources(self._getHrAddr()).canModifyHrContributor(msg.sender) # dev: no perms

    pending: PendingRipeTransfer = self.pendingRipeTransfer
    assert pending.confirmBlock != 0 # dev: no pending transfer
    self.pendingRipeTransfer = empty(PendingRipeTransfer)

    log RipeTransferCancelled(recipient=pending.recipient, cancelledBy=msg.sender, initiatedBlock=pending.initiatedBlock, confirmBlock=pending.confirmBlock)


# utils


@view
@external
def hasPendingRipeTransfer() -> bool:
    return self._hasPendingRipeTransfer()


@view
@internal
def _hasPendingRipeTransfer() -> bool:
    return self.pendingRipeTransfer.confirmBlock != 0


#############
# Ownership #
#############


@external
def changeOwnership(_newOwner: address):
    currentOwner: address = self.owner
    assert msg.sender == currentOwner # dev: no perms
    assert _newOwner not in [empty(address), currentOwner] # dev: invalid new owner

    confirmBlock: uint256 = block.number + self.keyActionDelay
    self.pendingOwner = PendingOwnerChange(
        newOwner = _newOwner,
        initiatedBlock = block.number,
        confirmBlock = confirmBlock,
    )
    log OwnershipChangeInitiated(prevOwner=currentOwner, newOwner=_newOwner, confirmBlock=confirmBlock)


@external
def confirmOwnershipChange():
    data: PendingOwnerChange = self.pendingOwner
    assert data.newOwner != empty(address) # dev: no pending owner
    assert data.confirmBlock != 0 and block.number >= data.confirmBlock # dev: time delay not reached
    assert msg.sender == data.newOwner # dev: only new owner can confirm

    prevOwner: address = self.owner
    self.owner = data.newOwner
    self.pendingOwner = empty(PendingOwnerChange)
    log OwnershipChangeConfirmed(prevOwner=prevOwner, newOwner=data.newOwner, initiatedBlock=data.initiatedBlock, confirmBlock=data.confirmBlock)


@external
def cancelOwnershipChange():
    if msg.sender not in [self.owner, self.manager]:
        assert staticcall HumanResources(self._getHrAddr()).canModifyHrContributor(msg.sender) # dev: no perms

    data: PendingOwnerChange = self.pendingOwner
    assert data.confirmBlock != 0 # dev: no pending change
    self.pendingOwner = empty(PendingOwnerChange)
    log OwnershipChangeCancelled(cancelledOwner=data.newOwner, cancelledBy=msg.sender, initiatedBlock=data.initiatedBlock, confirmBlock=data.confirmBlock)


# utils


@view
@external
def hasPendingOwnerChange() -> bool:
    return self._hasPendingOwnerChange()


@view
@internal
def _hasPendingOwnerChange() -> bool:
    return self.pendingOwner.confirmBlock != 0


###############
# Other Admin #
###############


# manager


@external 
def setManager(_newManager: address):
    if msg.sender != self.owner:
        assert staticcall HumanResources(self._getHrAddr()).canModifyHrContributor(msg.sender) # dev: no perms

    assert not self._hasPendingOwnerChange() # dev: cannot do with pending ownership change
    assert _newManager != empty(address) # dev: cannot be 0x0
    self.manager = _newManager
    log ManagerModified(newManager=_newManager, changedBy=msg.sender)


# key action delay


@external
def setKeyActionDelay(_numBlocks: uint256):
    assert msg.sender == self.owner # dev: no perms
    assert _numBlocks >= MIN_KEY_ACTION_DELAY and _numBlocks <= MAX_KEY_ACTION_DELAY # dev: invalid delay
    self.keyActionDelay = _numBlocks
    log KeyActionDelaySet(numBlocks=_numBlocks)


# governance actions


@nonreentrant
@external
def delegateTo(_govAddr: address, _recipient: address, _ratio: uint256):
    assert not self.isFrozen # dev: contract frozen
    assert msg.sender == self.owner # dev: no perms
    extcall RipeGovernance(_govAddr).delegateTo(_recipient, _ratio) # dev: could not delegate
    log DelegationModified(govAddr=_govAddr, recipient=_recipient, ratio=_ratio)


@nonreentrant
@external
def removeDelegationFor(_govAddr: address, _recipient: address = empty(address)):
    assert not self.isFrozen # dev: contract frozen
    assert msg.sender in [self.manager, self.owner] # dev: no perms
    extcall RipeGovernance(_govAddr).removeDelegationFor(_recipient) # 0x0 will remove all delegations
    log DelegationRemoved(govAddr=_govAddr, recipient=_recipient)


############
# HR Admin #
############


# freeze


@external 
def setIsFrozen(_shouldFreeze: bool) -> bool:
    assert staticcall HumanResources(self._getHrAddr()).canModifyHrContributor(msg.sender) # dev: no perms
    self.isFrozen = _shouldFreeze
    log FreezeModified(isFrozen=_shouldFreeze)
    return True


# cancel pay check


@external
def cancelPaycheck():
    hr: address = self._getHrAddr()
    assert staticcall HumanResources(hr).canModifyHrContributor(msg.sender) # dev: no perms

    owner: address = self.owner
    totalComp: uint256 = self.compensation

    # important validation !
    assert block.timestamp < self.endTime # dev: cannot cancel

    # check cliff (if reached, cash check)
    forfeitedAmount: uint256 = totalComp
    didReachCliff: bool = (block.timestamp >= self.cliffTime)
    if didReachCliff:
        self._cashRipeCheck(owner, hr, hr)
        forfeitedAmount = totalComp - self.totalClaimed # get latest after `_cashRipeCheck()`
    assert forfeitedAmount != 0 # dev: nothing to cancel

    # reset comp amount + end time
    self.compensation = totalComp - forfeitedAmount
    self.endTime = block.timestamp

    # tell HR forfeited amount
    extcall HumanResources(hr).refundAfterCancelPaycheck(forfeitedAmount, not didReachCliff)

    log RipePaycheckCancelled(owner=owner, forfeitedAmount=forfeitedAmount, didReachCliff=didReachCliff)


######################
# Compensation Utils #
######################


 # claimable


@view
@external
def getClaimable() -> uint256:
    return self._getClaimable()


@view
@internal
def _getClaimable() -> uint256:
    vested: uint256 = self._getTotalVested()
    claimed: uint256 = self.totalClaimed
    claimable: uint256 = 0
    if vested > claimed:
        claimable = vested - claimed
    return claimable


# vested


@view
@external
def getTotalVested() -> uint256:
    return self._getTotalVested()


@view
@internal
def _getTotalVested() -> uint256:   
    startTime: uint256 = self.startTime
    if block.timestamp <= startTime:
        return 0 # has future start time
    compensation: uint256 = self.compensation
    return min(compensation, compensation * (block.timestamp - startTime) // (self.endTime - startTime))


# unvested


@view
@external
def getUnvestedComp() -> uint256:
    return self._getUnvestedComp()


@view
@internal
def _getUnvestedComp() -> uint256:
    remainingComp: uint256 = 0
    compTaken: uint256 = max(self._getTotalVested(), self.totalClaimed)
    totalComp: uint256 = self.compensation
    if totalComp > compTaken:
        remainingComp = totalComp - compTaken
    return remainingComp


# vesting length


@view
@external
def getRemainingVestingLength() -> uint256:
    return self._getRemainingVestingLength()


@view
@internal
def _getRemainingVestingLength() -> uint256:
    remainingVestingLength: uint256 = 0
    endTime: uint256 = self.endTime
    if endTime > block.timestamp:
        remainingVestingLength = endTime - block.timestamp
    return remainingVestingLength


# unlock length


@view
@external
def getRemainingUnlockLength() -> uint256:
    return self._getRemainingUnlockLength()


@view
@internal
def _getRemainingUnlockLength() -> uint256:
    remainingUnlockLength: uint256 = 0
    unlockTime: uint256 = self.unlockTime
    if unlockTime > block.timestamp:
        remainingUnlockLength = unlockTime - block.timestamp
    return remainingUnlockLength