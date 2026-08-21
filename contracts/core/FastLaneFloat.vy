#     ╔══════════════════════════════════════════════════════════════╗
#     ║  ** Fast Lane Float **                                       ║
#     ║  Holds destination-chain inventory and pays a fast-lane fill  ║
#     ║  against a solver-signed order. Holds no mint authority.      ║
#     ╚══════════════════════════════════════════════════════════════╝
#
#     Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
#     Ripe Foundation (C) 2025

# @version 0.4.3

# UNAUDITED. Not authorized for real funds. See
# docs/chains/rh/relay-fast-lane.md for what this is and what blocks it, and
# docs/chains/rh/bridge-integration-security-review.md for the open findings.
#
# This contract CANNOT verify that the origin-chain deposit asserted by an order
# actually happened. It pays against a signature. The caps below - not the
# signature - are the security boundary: they bound total loss if the solver key
# is compromised. Every other check narrows the blast radius; only the caps
# bound it.

exports: gov.__interface__
exports: timeLock.__interface__

initializes: gov
initializes: timeLock[gov := gov]

import contracts.modules.LocalGov as gov
import contracts.modules.TimeLock as timeLock

from ethereum.ercs import IERC20

interface RipeHq:
    def mintEnabled() -> bool: view

interface RipeErc20:
    def blacklisted(_addr: address) -> bool: view
    def isPaused() -> bool: view
    def ripeHq() -> address: view

struct FillOrder:
    relayOrderId: bytes32
    recipient: address
    inputAmount: uint256
    outputAmount: uint256
    originChainId: uint256
    issuedAt: uint256
    deadline: uint256
    salt: bytes32

# One entry per outstanding fill. `paidAt` is set once, at fill, and is NEVER
# reset by a stage transition: age always means "time since we paid the user",
# which is the exposure that matters and which makes the list chronological by
# construction. That is what allows an O(1) oldest lookup without a heap - the
# list order never depends on the order in which settlements are observed.
struct Entry:
    amount: uint256
    paidAt: uint256
    stage: uint8
    prev: bytes32
    next: bytes32

struct PendingChange:
    epoch: uint256
    actionType: uint8
    addrVal: address
    numVal: uint256
    maxFill: uint256
    maxExposure: uint256
    maxEntries: uint256
    maxAge: uint256
    shortfallOrderId: bytes32

event FastLaneFilled:
    orderId: indexed(bytes32)
    recipient: indexed(address)
    outputAmount: uint256
    inputAmount: uint256

event StageAdvanced:
    orderId: indexed(bytes32)
    fromStage: uint8
    toStage: uint8

event ExposureCleared:
    orderId: indexed(bytes32)
    amount: uint256
    ageSeconds: uint256

event LanePauseSet:
    isPaused: bool
    caller: indexed(address)

event SolverSignerCleared:
    prevSigner: indexed(address)
    caller: indexed(address)

event GuardianSet:
    guardian: indexed(address)
    isGuardian: bool

event CapsLowered:
    maxFill: uint256
    maxExposure: uint256
    maxEntries: uint256
    maxAge: uint256

event ChangeInitiated:
    actionId: indexed(uint256)
    actionType: uint8

event ChangeConfirmed:
    actionId: indexed(uint256)
    actionType: uint8

event Retired:
    caller: indexed(address)
    retiredAt: uint256

event FloatFloorSet:
    newFloor: uint256
    caller: indexed(address)

event FloatFunded:
    funder: indexed(address)
    amount: uint256

event ShortfallRecorded:
    orderId: indexed(bytes32)
    amount: uint256
    caller: indexed(address)

# config
lanePaused: public(bool)
solverSigner: public(address)
isGuardian: public(HashMap[address, bool])

# A signer dropped in an incident can never be reinstated. Without this,
# rotating back to the same address serves a full timelock, carries a current
# configEpoch, and revives every order ever signed under it - the pre-signed
# backlog is dormant rather than dead. Burning forces rotation to a NEW key,
# which is the only rotation that actually retires the old signatures.
isBurnedSigner: public(HashMap[address, bool])

# hard caps - the security boundary
maxFillAmount: public(uint256)
maxAggregateExposure: public(uint256)
maxOutstandingEntries: public(uint256)
maxEntryAge: public(uint256)

# advisory only: read by the quoting layer, never enforced here
quoteThreshold: public(uint256)

# Inventory reserve invariant. This is NOT the control that detects stalled
# replenishment: if restoration stops, exposure cannot clear, outstandingNotional
# climbs and `maxAggregateExposure` closes admission. That ledger bound is the
# cause-agnostic refill-failure control, and it predates this floor.
#
# The floor enforces only `postFillBalance >= minFloatBalance`, so it binds only
# when `balance - floor` is tighter than the remaining aggregate capacity. Under
# a float much larger than the exposure cap it never fires.
#
# It is kept because it is the ONLY cap with an independent data source. Every
# other bound - aggregate notional, entry count, entry age - is computed from
# counters this contract maintains, so all three fail together if that
# accounting is ever wrong. The floor reads balanceOf from the token, so it
# still holds tokens back when the ledger does not.
minFloatBalance: public(uint256)

# Tokens this contract believes it holds. Restoration must be matched by real
# balance, not merely asserted by a governor, so clearing exposure requires the
# balance to have risen. Direct transfers only ever create slack, which is safe:
# the tokens are genuinely present however they arrived.
accountedBalance: public(uint256)

# One-way. Retirement pauses, drops the signer, and permanently blocks every
# reactivation path, so a superseded instance cannot be rekeyed back into use.
isRetired: public(bool)
retiredAt: public(uint256)

# Bumped by every emergency or tightening action. A timelocked action confirms
# only in the epoch it was queued in, so a matured unpause cannot undo a
# guardian pause that happened after it was queued.
configEpoch: public(uint256)

# ledger
entries: public(HashMap[bytes32, Entry])
oldestEntry: public(bytes32)
newestEntry: public(bytes32)
isFilled: public(HashMap[bytes32, bool])

# aggregate - hard invariants
outstandingNotional: public(uint256)
outstandingEntries: public(uint256)

# per-stage - health signal only, never blocking (a verified transition must
# always be recordable; a remote fact cannot be refused because a local counter
# is full)
stageANotional: public(uint256)
stageAEntries: public(uint256)
stageBNotional: public(uint256)
stageBEntries: public(uint256)

pendingChanges: public(HashMap[uint256, PendingChange])

TOKEN: public(immutable(address))
RIPE_HQ: public(immutable(address))
FLOAT_RECIPIENT: public(immutable(address))

STAGE_A: constant(uint8) = 1
STAGE_B: constant(uint8) = 2

ACTION_SET_SOLVER: constant(uint8) = 1
ACTION_RAISE_CAPS: constant(uint8) = 2
ACTION_UNPAUSE: constant(uint8) = 3
ACTION_WITHDRAW: constant(uint8) = 4
ACTION_LOWER_FLOOR: constant(uint8) = 5
ACTION_RECORD_SHORTFALL: constant(uint8) = 6

MAX_ORDER_HORIZON: constant(uint256) = 15 * 60
RETIREMENT_DELAY: constant(uint256) = 7 * 24 * 3600
MIN_RESTORE_BPS: constant(uint256) = 9_500
HUNDRED_PCT: constant(uint256) = 10_000

MAX_BATCH: constant(uint256) = 50
ENTRY_CEILING: constant(uint256) = 1000

EIP712_TYPEHASH: constant(bytes32) = keccak256("EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)")
ORDER_TYPEHASH: constant(bytes32) = keccak256("FillOrder(bytes32 relayOrderId,address recipient,uint256 inputAmount,uint256 outputAmount,uint256 originChainId,uint256 issuedAt,uint256 deadline,bytes32 salt)")
NAME_HASH: constant(bytes32) = keccak256("RipeFastLaneFloat")
VERSION_HASH: constant(bytes32) = keccak256("1")
ECRECOVER_PRECOMPILE: constant(address) = 0x0000000000000000000000000000000000000001


@deploy
def __init__(
    _ripeHq: address,
    _token: address,
    _floatRecipient: address,
    _tempGov: address,
    _minTimeLock: uint256,
    _maxTimeLock: uint256,
    _maxFillAmount: uint256,
    _maxAggregateExposure: uint256,
    _maxOutstandingEntries: uint256,
    _maxEntryAge: uint256,
    _minFloatBalance: uint256,
):
    assert empty(address) not in [_ripeHq, _token, _floatRecipient] # dev: invalid addr
    assert _maxOutstandingEntries != 0 and _maxOutstandingEntries <= ENTRY_CEILING # dev: invalid entry cap
    assert _maxFillAmount != 0 and _maxAggregateExposure != 0 and _maxEntryAge != 0 # dev: invalid caps
    # the floor is a cap like any other: a zero floor deploys it inert, which is
    # the failure mode of a gate whose condition can be satisfied vacuously
    assert _minFloatBalance != 0 # dev: invalid floor
    assert _maxFillAmount <= _maxAggregateExposure # dev: fill cap above exposure cap

    gov.__init__(_ripeHq, _tempGov, 0, 0, 0)
    # initial timelock is the MINIMUM, not zero: with 0 the confirm block equals
    # the initiate block and every slow lever would confirm in the same transaction
    timeLock.__init__(_minTimeLock, _maxTimeLock, _minTimeLock, _maxTimeLock)

    RIPE_HQ = _ripeHq
    TOKEN = _token
    FLOAT_RECIPIENT = _floatRecipient

    self.maxFillAmount = _maxFillAmount
    self.maxAggregateExposure = _maxAggregateExposure
    self.maxOutstandingEntries = _maxOutstandingEntries
    self.maxEntryAge = _maxEntryAge
    self.minFloatBalance = _minFloatBalance

    # starts halted: no fill can occur before governance sets a solver and unpauses
    self.lanePaused = True


###############
# Fill (hot)  #
###############


@external
@nonreentrant
def fill(_order: FillOrder, _signature: Bytes[65]) -> bytes32:
    """
    @notice Pay a fast-lane fill from the float against a solver-signed order
    @dev Checks, then effects, then interactions. The order id is recomputed from
         every canonical field and is never accepted as an input.
    @param _order The solver-signed order terms
    @param _signature EIP-712 signature over `_order` by the configured solver
    @return The derived order id
    """
    signer: address = self.solverSigner

    # 1. caller gate - the solver signature is visible at quote time, so without
    #    this anyone holding a quote could claim the payout before depositing
    assert msg.sender == signer # dev: not solver

    # 2. liveness gates. mintEnabled is read because the refill leg is a CCIP
    #    burn/mint that mintEnabled blocks, while this fill is a plain transfer
    #    that it does not - so without this clause disabling minting would stop
    #    the float being replenished while leaving it draining at full rate
    assert not self.lanePaused # dev: lane paused
    assert not self.isRetired # dev: retired
    # the token's HQ is mutable; if it migrates, this instance's refill
    # authority is obsolete while the old HQ may still report enabled
    assert staticcall RipeErc20(TOKEN).ripeHq() == RIPE_HQ # dev: hq migrated
    assert staticcall RipeHq(RIPE_HQ).mintEnabled() # dev: minting disabled
    assert not staticcall RipeErc20(TOKEN).isPaused() # dev: token paused

    # 3. verify the signature over the local authorization, then replay-guard on
    #    the SETTLEMENT identity.
    #
    #    These are two different hashes and the distinction is load-bearing. The
    #    authorization hash covers salt and issuedAt, so one origin deposit can
    #    be authorized many times over. Relay settles per canonical order id and
    #    is idempotent on it, so a second authorization carrying the same
    #    relayOrderId would pay again against a deposit that only ever funded one
    #    fill. v1 therefore allows exactly ONE fill per canonical order;
    #    duplicate deposits sharing an order id are an off-chain refund, never a
    #    second payout.
    authHash: bytes32 = self._orderId(_order)
    self._validateSignature(authHash, _signature, signer)
    orderId: bytes32 = _order.relayOrderId
    assert not self.isFilled[orderId] # dev: already filled

    # 4. order terms
    # Freshness is bounded against a SIGNED issuance time, not against the
    # deadline. An unbounded deadline admits an order priced arbitrarily long
    # ago, which bites in this contract's OWN threat model rather than only the
    # adversarial one: the outputAmount <= inputAmount check exists to catch a
    # buggy solver overpaying against a real deposit, and an order built,
    # signed, dropped by a retry queue and replayed later against a deposit that
    # no longer corresponds is exactly that bug.
    #
    # `deadline <= block.timestamp + MAX_ORDER_HORIZON` does NOT close that, and
    # was the first attempt: it bounds time-to-expiry at fill, not order age, so
    # a year-long order is merely inadmissible until its final horizon and then
    # becomes fillable for fifteen minutes at a moment the signer picked. Age is
    # only knowable from a value inside the signature.
    assert _order.issuedAt <= block.timestamp # dev: order from the future
    assert block.timestamp <= _order.deadline # dev: order expired
    assert _order.issuedAt <= _order.deadline # dev: deadline before issuance
    assert _order.deadline - _order.issuedAt <= MAX_ORDER_HORIZON # dev: quote window too long
    # implied by the three above, and stated anyway because it is the property
    # that actually matters and the one the previous check only appeared to give
    assert block.timestamp - _order.issuedAt <= MAX_ORDER_HORIZON # dev: order too old
    # Relay's attestor requires the canonical order id as the terminal calldata
    # suffix (`transaction.input.endsWith(orderId)`), so a fill without it is
    # unattestable. Vyper accepts trailing calldata, but tolerance is not
    # binding: read it back and require it to equal the id the solver signed,
    # otherwise the suffix is decorative and any bytes would pass.
    assert _order.relayOrderId != empty(bytes32) # dev: no relay order id
    assert convert(slice(msg.data, len(msg.data) - 32, 32), bytes32) == _order.relayOrderId # dev: order id suffix

    assert _order.originChainId != chain.id # dev: same chain
    assert _order.recipient != empty(address) # dev: invalid recipient
    assert _order.recipient != self # dev: self recipient
    assert not staticcall RipeErc20(TOKEN).blacklisted(_order.recipient) # dev: blacklisted recipient
    assert _order.outputAmount != 0 # dev: zero output

    # NOT a solvency invariant: inputAmount is an assertion inside the order,
    # not an observation of a deposit. Under key compromise both numbers are
    # attacker-chosen. This catches a buggy solver overpaying against a real
    # deposit; the caps are what bound a malicious one.
    assert _order.outputAmount <= _order.inputAmount # dev: overpay

    # 5. hard caps
    assert _order.inputAmount <= self.maxFillAmount # dev: fill too large
    newNotional: uint256 = self.outstandingNotional + _order.inputAmount
    newEntries: uint256 = self.outstandingEntries + 1
    assert newNotional <= self.maxAggregateExposure # dev: exposure cap
    assert newEntries <= self.maxOutstandingEntries # dev: entry cap
    self._assertOldestWithinAge()

    # drain floor - cause-agnostic, see minFloatBalance
    balance: uint256 = staticcall IERC20(TOKEN).balanceOf(self)
    assert balance >= _order.outputAmount # dev: insufficient float
    assert balance - _order.outputAmount >= self.minFloatBalance # dev: float floor

    # effects - exposure is reserved before the transfer, never after
    self.isFilled[orderId] = True
    self.outstandingNotional = newNotional
    self.outstandingEntries = newEntries
    self.stageANotional += _order.inputAmount
    self.stageAEntries += 1
    self._appendEntry(orderId, _order.inputAmount)
    accounted: uint256 = self.accountedBalance
    self.accountedBalance = accounted - min(accounted, _order.outputAmount)

    # interaction
    assert extcall IERC20(TOKEN).transfer(_order.recipient, _order.outputAmount, default_return_value=True) # dev: transfer failed

    log FastLaneFilled(orderId=orderId, recipient=_order.recipient, outputAmount=_order.outputAmount, inputAmount=_order.inputAmount)
    return orderId


@view
@internal
def _assertOldestWithinAge():
    oldest: bytes32 = self.oldestEntry
    if oldest == empty(bytes32):
        return
    assert block.timestamp - self.entries[oldest].paidAt <= self.maxEntryAge # dev: exposure too old


###############
# Order id    #
###############


@view
@external
def getOrderId(_order: FillOrder) -> bytes32:
    return self._orderId(_order)


@view
@internal
def _orderId(_order: FillOrder) -> bytes32:
    return keccak256(
        abi_encode(
            ORDER_TYPEHASH,
            _order.relayOrderId,
            _order.recipient,
            _order.inputAmount,
            _order.outputAmount,
            _order.originChainId,
            _order.issuedAt,
            _order.deadline,
            _order.salt,
        )
    )


@view
@external
def getDigest(_order: FillOrder) -> bytes32:
    return self._digest(self._orderId(_order))


@view
@internal
def _digest(_orderId: bytes32) -> bytes32:
    # chain.id and self are both bound here. If two instances are ever deployed
    # at the same address on different chains, chain.id is the only thing
    # preventing a cross-chain replay of the same order.
    domainSeparator: bytes32 = keccak256(abi_encode(EIP712_TYPEHASH, NAME_HASH, VERSION_HASH, chain.id, self))
    return keccak256(concat(b"\x19\x01", domainSeparator, _orderId))


@view
@internal
def _validateSignature(_orderId: bytes32, _signature: Bytes[65], _signer: address):
    assert _signer != empty(address) # dev: no solver signer
    assert len(_signature) == 65 # dev: invalid sig length
    digest: bytes32 = self._digest(_orderId)

    r: bytes32 = convert(slice(_signature, 0, 32), bytes32)
    s: bytes32 = convert(slice(_signature, 32, 32), bytes32)
    v: uint8 = convert(slice(_signature, 64, 1), uint8)
    if v < 27:
        v = v + 27
    assert v == 27 or v == 28 # dev: invalid v parameter

    s_uint: uint256 = convert(s, uint256)
    assert s_uint != 0 # dev: invalid s value (zero)
    assert s_uint <= convert(0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF5D576E7357A4501DDFE92F46681B20A0, uint256) # dev: invalid s value

    response: Bytes[32] = raw_call(
        ECRECOVER_PRECOMPILE,
        abi_encode(digest, v, r, s),
        max_outsize = 32,
        is_static_call = True,
    )
    assert len(response) == 32 # dev: invalid ecrecover response length
    assert abi_decode(response, address) == _signer # dev: invalid signature


###############
# Ledger      #
###############


@internal
def _appendEntry(_orderId: bytes32, _amount: uint256):
    prevTail: bytes32 = self.newestEntry
    self.entries[_orderId] = Entry(
        amount=_amount,
        paidAt=block.timestamp,
        stage=STAGE_A,
        prev=prevTail,
        next=empty(bytes32),
    )
    if prevTail == empty(bytes32):
        self.oldestEntry = _orderId
    else:
        self.entries[prevTail].next = _orderId
    self.newestEntry = _orderId


@internal
def _unlinkEntry(_orderId: bytes32):
    entry: Entry = self.entries[_orderId]
    if entry.prev == empty(bytes32):
        self.oldestEntry = entry.next
    else:
        self.entries[entry.prev].next = entry.next
    if entry.next == empty(bytes32):
        self.newestEntry = entry.prev
    else:
        self.entries[entry.next].prev = entry.prev
    self.entries[_orderId] = empty(Entry)


@external
def recordWithdrawn(_orderIds: DynArray[bytes32, MAX_BATCH]) -> uint256:
    """
    @notice Move entries from stage A to stage B after the origin receivable is withdrawn
    @dev Governance only. This must never be assertable by the solver or a keeper:
         a key that can free capacity can drain the float regardless of the caps.
         Aggregate exposure and count are deliberately unchanged - a transition is
         not a reduction.
    """
    assert gov._canGovern(msg.sender) # dev: no perms
    count: uint256 = 0
    for orderId: bytes32 in _orderIds:
        entry: Entry = self.entries[orderId]
        if entry.stage != STAGE_A:
            continue
        self.entries[orderId].stage = STAGE_B
        self.stageANotional -= entry.amount
        self.stageAEntries -= 1
        self.stageBNotional += entry.amount
        self.stageBEntries += 1
        count += 1
        log StageAdvanced(orderId=orderId, fromStage=STAGE_A, toStage=STAGE_B)
    return count


@external
def recordRestored(_orderIds: DynArray[bytes32, MAX_BATCH], _receivedAmount: uint256) -> uint256:
    """
    @notice Clear entries once destination inventory is back on this contract
    @dev Governance authorises WHICH entries clear, but it cannot assert THAT
         inventory returned: the balance must actually have risen by
         `_receivedAmount` above what this contract already accounted for. A
         mistaken or compromised governor therefore cannot recycle the aggregate
         cap without real tokens arriving. This is a balance proof, not a CCIP
         receipt proof - it binds amount but not origin, so it does not remove
         the need for an authenticated receiver.
    """
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _receivedAmount != 0 # dev: zero received

    accounted: uint256 = self.accountedBalance
    balance: uint256 = staticcall IERC20(TOKEN).balanceOf(self)
    assert balance >= accounted + _receivedAmount # dev: inventory not restored

    count: uint256 = 0
    clearedTotal: uint256 = 0
    for orderId: bytes32 in _orderIds:
        entry: Entry = self.entries[orderId]
        if entry.stage != STAGE_B:
            continue
        self.stageBNotional -= entry.amount
        self.stageBEntries -= 1
        self.outstandingNotional -= entry.amount
        self.outstandingEntries -= 1
        clearedTotal += entry.amount
        self._unlinkEntry(orderId)
        count += 1
        log ExposureCleared(orderId=orderId, amount=entry.amount, ageSeconds=block.timestamp - entry.paidAt)

    assert clearedTotal != 0 # dev: nothing cleared
    # tolerate bridge fees, but not an arbitrary shortfall
    assert _receivedAmount >= clearedTotal * MIN_RESTORE_BPS // HUNDRED_PCT # dev: restored short
    self.accountedBalance = accounted + _receivedAmount
    return count


###############
# Views       #
###############


@view
@external
def floatBalance() -> uint256:
    return staticcall IERC20(TOKEN).balanceOf(self)


@view
@external
def oldestEntryAge() -> uint256:
    oldest: bytes32 = self.oldestEntry
    if oldest == empty(bytes32):
        return 0
    return block.timestamp - self.entries[oldest].paidAt


@view
@external
def isHealthy() -> bool:
    oldest: bytes32 = self.oldestEntry
    if oldest != empty(bytes32) and block.timestamp - self.entries[oldest].paidAt > self.maxEntryAge:
        return False
    if self.outstandingNotional > self.maxAggregateExposure:
        return False
    if self.outstandingEntries > self.maxOutstandingEntries:
        return False
    return True


@view
@external
def canFill(_inputAmount: uint256) -> bool:
    """
    @notice Advisory pre-check for the quoting layer. Reserves nothing: two
            concurrent quotes can both pass and only one may fit.
    """
    if self.lanePaused or self.isRetired or _inputAmount == 0 or _inputAmount > self.maxFillAmount:
        return False
    if staticcall RipeErc20(TOKEN).ripeHq() != RIPE_HQ:
        return False
    if not staticcall RipeHq(RIPE_HQ).mintEnabled():
        return False
    if self.outstandingNotional + _inputAmount > self.quoteThreshold:
        return False
    if self.outstandingEntries + 1 > self.maxOutstandingEntries:
        return False
    balance: uint256 = staticcall IERC20(TOKEN).balanceOf(self)
    if balance < _inputAmount or balance - _inputAmount < self.minFloatBalance:
        return False
    oldest: bytes32 = self.oldestEntry
    if oldest != empty(bytes32) and block.timestamp - self.entries[oldest].paidAt > self.maxEntryAge:
        return False
    return True


###############
# Fast levers #
###############


@external
def pauseLane():
    """
    @notice Halt the lane immediately. Any guardian or governance may call.
    """
    assert self.isGuardian[msg.sender] or gov._canGovern(msg.sender) # dev: no perms
    assert not self.lanePaused # dev: already paused
    self.lanePaused = True
    self.configEpoch += 1
    log LanePauseSet(isPaused=True, caller=msg.sender)


@external
def clearSolverSigner():
    """
    @notice Drop the solver signer immediately. Any guardian or governance may call.
    """
    assert self.isGuardian[msg.sender] or gov._canGovern(msg.sender) # dev: no perms
    prev: address = self.solverSigner
    assert prev != empty(address) # dev: no signer
    self.solverSigner = empty(address)
    self.isBurnedSigner[prev] = True
    self.configEpoch += 1
    log SolverSignerCleared(prevSigner=prev, caller=msg.sender)


@external
def lowerCaps(_maxFill: uint256, _maxExposure: uint256, _maxEntries: uint256, _maxAge: uint256):
    """
    @notice Tighten caps immediately. Governance only. Never raises.
    @dev A cap may not be set below current live exposure, which would brick
         `recordRestored` and strand entries the contract must still reconcile.
    """
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _maxFill <= self.maxFillAmount # dev: not a reduction
    assert _maxExposure <= self.maxAggregateExposure # dev: not a reduction
    assert _maxEntries <= self.maxOutstandingEntries # dev: not a reduction
    assert _maxAge <= self.maxEntryAge # dev: not a reduction
    assert _maxExposure >= self.outstandingNotional # dev: below live exposure
    assert _maxEntries >= self.outstandingEntries # dev: below live entries
    assert _maxFill != 0 and _maxExposure != 0 and _maxEntries != 0 and _maxAge != 0 # dev: zero cap
    assert _maxFill <= _maxExposure # dev: fill cap above exposure cap

    # the advisory threshold must never advertise headroom the hard cap refuses
    if self.quoteThreshold > _maxExposure:
        self.quoteThreshold = _maxExposure

    self.maxFillAmount = _maxFill
    self.maxAggregateExposure = _maxExposure
    self.maxOutstandingEntries = _maxEntries
    self.maxEntryAge = _maxAge
    self.configEpoch += 1
    log CapsLowered(maxFill=_maxFill, maxExposure=_maxExposure, maxEntries=_maxEntries, maxAge=_maxAge)


@external
def retire():
    """
    @notice Permanently retire this instance. Governance only, irreversible.
    @dev Atomically pauses and drops the signer, and blocks every reactivation
         path thereafter. This is what makes an HQ migration or a redeploy safe:
         the superseded instance cannot be rekeyed back into service.
    """
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not self.isRetired # dev: already retired
    self.isRetired = True
    self.retiredAt = block.timestamp
    self.lanePaused = True
    self.solverSigner = empty(address)
    self.configEpoch += 1
    log Retired(caller=msg.sender, retiredAt=block.timestamp)


@external
def raiseFloatFloor(_newFloor: uint256):
    """
    @notice Raise the drain floor immediately. Governance only.
    @dev Raising halts the lane sooner, so it is the safe direction and is not
         timelocked. Lowering the floor allows more of the float to drain and
         goes through `initiateChange(ACTION_LOWER_FLOOR, ...)`.
    """
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _newFloor > self.minFloatBalance # dev: not a raise
    self.minFloatBalance = _newFloor
    self.configEpoch += 1
    log FloatFloorSet(newFloor=_newFloor, caller=msg.sender)


@external
def setQuoteThreshold(_threshold: uint256):
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _threshold <= self.maxAggregateExposure # dev: above hard cap
    self.quoteThreshold = _threshold


@external
def setGuardian(_guardian: address, _isGuardian: bool):
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _guardian != empty(address) # dev: invalid guardian
    self.isGuardian[_guardian] = _isGuardian
    log GuardianSet(guardian=_guardian, isGuardian=_isGuardian)


@external
def fundFloat(_amount: uint256):
    """
    @notice Pull float in from the caller. Permissionless by design - adding
            inventory can only improve solvency and creates no claim.
    """
    assert _amount != 0 # dev: zero amount
    assert extcall IERC20(TOKEN).transferFrom(msg.sender, self, _amount, default_return_value=True) # dev: transfer failed
    self.accountedBalance += _amount
    log FloatFunded(funder=msg.sender, amount=_amount)


@external
def syncAccountedBalance():
    """
    @notice Account for float that arrived by direct transfer
    @dev Only ever raises `accountedBalance`, which makes restoration strictly
         harder to claim. It can never be used to manufacture restoration room.
    """
    assert gov._canGovern(msg.sender) # dev: no perms
    balance: uint256 = staticcall IERC20(TOKEN).balanceOf(self)
    assert balance > self.accountedBalance # dev: nothing to sync
    self.accountedBalance = balance


###############
# Slow levers #
###############


@external
def initiateChange(_actionType: uint8, _addrVal: address, _numVal: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _actionType in [ACTION_SET_SOLVER, ACTION_RAISE_CAPS, ACTION_UNPAUSE, ACTION_WITHDRAW, ACTION_LOWER_FLOOR, ACTION_RECORD_SHORTFALL] # dev: invalid action

    # a retired instance may only ever pay its float out; nothing may bring it back
    if self.isRetired:
        assert _actionType == ACTION_WITHDRAW # dev: retired

    if _actionType == ACTION_SET_SOLVER:
        assert _addrVal != empty(address) and not _addrVal.is_contract # dev: solver must be eoa
        assert not self.isBurnedSigner[_addrVal] # dev: signer burned
    elif _actionType == ACTION_UNPAUSE:
        # queueing an unpause while already unpaused would let it sit matured
        # and instantly undo a later guardian pause
        assert self.lanePaused # dev: not paused
    elif _actionType == ACTION_WITHDRAW:
        # every precondition is checked here AND revalidated at confirmation.
        # Checking at initiation matters because RETIREMENT_DELAY is longer than
        # the timelock expiration window: an action queued before the delay
        # elapsed could never be confirmed before expiring.
        assert _numVal != 0 # dev: zero amount
        assert self.isRetired # dev: not retired
        assert block.timestamp >= self.retiredAt + RETIREMENT_DELAY # dev: retirement delay
        assert self.outstandingEntries == 0 # dev: live exposure
    elif _actionType == ACTION_LOWER_FLOOR:
        assert _numVal < self.minFloatBalance # dev: not a reduction
        assert _numVal != 0 # dev: zero floor

    assert _actionType != ACTION_RAISE_CAPS # dev: use initiateCapRaise
    assert _actionType != ACTION_RECORD_SHORTFALL # dev: use initiateRecordShortfall

    aid: uint256 = timeLock._initiateAction()
    self.pendingChanges[aid] = PendingChange(
        epoch=self.configEpoch,
        actionType=_actionType, addrVal=_addrVal, numVal=_numVal,
        maxFill=0, maxExposure=0, maxEntries=0, maxAge=0,
        shortfallOrderId=empty(bytes32),
    )
    log ChangeInitiated(actionId=aid, actionType=_actionType)
    return aid


@external
def initiateCapRaise(_maxFill: uint256, _maxExposure: uint256, _maxEntries: uint256, _maxAge: uint256) -> uint256:
    """
    @notice Raise any cap, behind the timelock. Every cap is raisable so that a
            mis-set cap is recoverable without redeploying, and no cap can be
            raised quickly.
    """
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not self.isRetired # dev: retired
    assert _maxFill >= self.maxFillAmount # dev: not a raise
    assert _maxExposure >= self.maxAggregateExposure # dev: not a raise
    assert _maxEntries >= self.maxOutstandingEntries # dev: not a raise
    assert _maxAge >= self.maxEntryAge # dev: not a raise
    assert _maxFill <= _maxExposure # dev: fill cap above exposure cap
    assert _maxEntries <= ENTRY_CEILING # dev: above entry ceiling

    aid: uint256 = timeLock._initiateAction()
    self.pendingChanges[aid] = PendingChange(
        epoch=self.configEpoch,
        actionType=ACTION_RAISE_CAPS, addrVal=empty(address), numVal=0,
        maxFill=_maxFill, maxExposure=_maxExposure, maxEntries=_maxEntries, maxAge=_maxAge,
        shortfallOrderId=empty(bytes32),
    )
    log ChangeInitiated(actionId=aid, actionType=ACTION_RAISE_CAPS)
    return aid


@external
def initiateRecordShortfall(_orderId: bytes32, _amount: uint256) -> uint256:
    """
    @notice Queue a write-off of an entry that has no real inventory behind it -
            e.g. a phantom entry left over from the pre-fix replay-identity gap,
            or any entry a governor determines will never be restored. Behind
            the timelock, since unlike `recordRestored` this clears exposure on
            assertion alone, with no balance proof possible: there is nothing
            to prove for a loss that already happened.
    @dev Deliberately NOT blocked while retired. A stuck phantom entry is
         exactly what would keep `outstandingEntries` above zero forever,
         which blocks `ACTION_WITHDRAW` on a retired instance that otherwise
         has nothing left to reconcile - writing it off is the only way such
         an instance ever finishes sweeping.
    """
    assert gov._canGovern(msg.sender) # dev: no perms
    entry: Entry = self.entries[_orderId]
    assert entry.stage != 0 # dev: no such entry
    assert entry.amount == _amount # dev: amount mismatch
    assert _amount != 0 # dev: zero amount

    aid: uint256 = timeLock._initiateAction()
    self.pendingChanges[aid] = PendingChange(
        epoch=self.configEpoch,
        actionType=ACTION_RECORD_SHORTFALL, addrVal=empty(address), numVal=_amount,
        maxFill=0, maxExposure=0, maxEntries=0, maxAge=0,
        shortfallOrderId=_orderId,
    )
    log ChangeInitiated(actionId=aid, actionType=ACTION_RECORD_SHORTFALL)
    return aid


@external
def confirmChange(_actionId: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert timeLock._confirmAction(_actionId) # dev: time lock not reached
    p: PendingChange = self.pendingChanges[_actionId]
    self.pendingChanges[_actionId] = empty(PendingChange)

    # a queued action is void if anything was paused, tightened or retired after
    # it was queued - it must be re-queued against the current configuration
    assert p.epoch == self.configEpoch # dev: stale action

    if p.actionType == ACTION_SET_SOLVER:
        self.solverSigner = p.addrVal
    elif p.actionType == ACTION_RAISE_CAPS:
        self.maxFillAmount = p.maxFill
        self.maxAggregateExposure = p.maxExposure
        self.maxOutstandingEntries = p.maxEntries
        self.maxEntryAge = p.maxAge
    elif p.actionType == ACTION_UNPAUSE:
        self.lanePaused = False
        log LanePauseSet(isPaused=False, caller=msg.sender)
    elif p.actionType == ACTION_LOWER_FLOOR:
        self.minFloatBalance = p.numVal
        log FloatFloorSet(newFloor=p.numVal, caller=msg.sender)
    elif p.actionType == ACTION_WITHDRAW:
        # float only ever leaves to a fixed address chosen at deploy - no
        # caller-supplied recipient and no arbitrary calldata anywhere in this
        # contract - and only from a quiesced, retired instance whose entries
        # have all been reconciled
        assert self.isRetired # dev: not retired
        assert block.timestamp >= self.retiredAt + RETIREMENT_DELAY # dev: retirement delay
        assert self.outstandingEntries == 0 # dev: live exposure
        before: uint256 = staticcall IERC20(TOKEN).balanceOf(self)
        assert extcall IERC20(TOKEN).transfer(FLOAT_RECIPIENT, p.numVal, default_return_value=True) # dev: transfer failed
        after: uint256 = staticcall IERC20(TOKEN).balanceOf(self)
        assert before - after == p.numVal # dev: unexpected balance delta
        accounted: uint256 = self.accountedBalance
        self.accountedBalance = accounted - min(accounted, p.numVal)
    elif p.actionType == ACTION_RECORD_SHORTFALL:
        # revalidated here, not just at initiation: a batched recordWithdrawn
        # /recordRestored covering this same order id in the meantime would
        # have already cleared it, and this must not double-clear or clear a
        # now-mismatched amount
        entry: Entry = self.entries[p.shortfallOrderId]
        assert entry.stage != 0 # dev: already cleared
        assert entry.amount == p.numVal # dev: amount mismatch
        if entry.stage == STAGE_A:
            self.stageANotional -= entry.amount
            self.stageAEntries -= 1
        else:
            self.stageBNotional -= entry.amount
            self.stageBEntries -= 1
        self.outstandingNotional -= entry.amount
        self.outstandingEntries -= 1
        self._unlinkEntry(p.shortfallOrderId)
        log ShortfallRecorded(orderId=p.shortfallOrderId, amount=entry.amount, caller=msg.sender)

    log ChangeConfirmed(actionId=_actionId, actionType=p.actionType)
    return True


@external
def cancelChange(_actionId: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert timeLock._cancelAction(_actionId) # dev: cannot cancel
    self.pendingChanges[_actionId] = empty(PendingChange)
    return True
