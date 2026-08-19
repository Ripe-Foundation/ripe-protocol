# Fast-lane payout contract — specification

Status: **Specification only. Not authorized, not implemented, not audited. No
funds may reach this contract before an independent audit.**

Date: 2026-08-19

Scope: the destination-side contract required by the conditional Relay fast lane
described in [`bridge-integration-synthesis.md`](bridge-integration-synthesis.md).
It is written as the build plan so the controls established in
[`bridge-integration-security-review.md`](bridge-integration-security-review.md)
live in the artifact a builder reads, not only in the review that found them.

This document specifies one component. It does not authorize the lane, resolve
H-1/H-2/H-4, or substitute for the venue-first sequencing recorded in the
synthesis.

## What the contract is

One immutable instance per chain, per token. It holds Ripe's destination float
and pays a user when presented with a solver-signed order asserting that the
user deposited on the origin chain. It then tracks the resulting exposure until
the origin receivable is withdrawn and the destination float is restored.

RIPE and GREEN across Base and Robinhood is therefore four deployments. A
multi-token variant halves that; a fixed `immutable token` is preferred because
it removes a hot-path validation and makes the review statement "this contract
can only ever move RIPE" checkable by inspection.

## What the contract cannot do

**It cannot verify that the origin deposit happened.** There is no proof of the
origin deposit on this chain. The contract pays against a *signature* asserting
one exists.

Everything else in this document is hygiene around that fact. If the solver key
is compromised, the attacker signs orders for deposits that never happened and
the float pays out. Therefore:

> **The caps are the security boundary. The signature is not.**

Adding Relay's own attestation (`includeProtocolData=true`) as a second required
signature is a real improvement and should be done, but two signatures are still
not a proof. The only construction that yields a proof is a cross-chain message,
and that message is CCIP — the latency the lane exists to avoid. Fast means
paying before proof. The contract's job is to bound that, not to eliminate it.

## State

```solidity
IERC20  immutable token;          // fixed at construction, never a parameter
address immutable hq;             // RipeHq on this chain (H-6)
address solverSigner;             // EOA whose signature authorizes a fill
bool    lanePaused;               // lane-scoped gate

mapping(bytes32 => bool) filled;  // replay guard, keyed by canonical order id

// Two-stage exposure ledger. Three caps per stage.
//   A: paid here, origin receivable not yet withdrawn
//   B: origin withdrawn, destination float not yet restored
uint256 stageANotional;  uint256 maxStageANotional;  // soft/hard pair, below
uint64  maxStageAAge;    uint32  maxStageAEntries;
uint256 stageBNotional;  uint256 maxStageBNotional;
uint64  maxStageBAge;    uint32  maxStageBEntries;
// per-entry {orderId, amount, timestamp}
```

## `fill(Order, bytes solverSig)`

Checks, then effects, then interactions. No exception.

**Checks**

1. `!lanePaused && IRipeHq(hq).mintEnabled()` — **both**, per H-6. See
   "Why the fill reads `mintEnabled`" below. One staticcall on the hot path.
2. `!filled[orderId]`, where `orderId` is **recomputed from every canonical
   order field**, never accepted as a supplied value.
3. EIP-712 signature recovers to `solverSigner`, with `chainid` **and**
   `address(this)` in the domain separator.
4. `order.deadline > block.timestamp`.
5. `order.destinationChainId == block.chainid`.
6. `order.outputToken == token`.
7. `order.recipient != 0 && !IErc20Token(token).blacklisted(order.recipient)`.
8. `order.outputAmount <= order.inputAmount`.
9. All three stage-A caps, and all three stage-B caps: notional, age, entry
   count. Any breach reverts.

**Effects**

10. `filled[orderId] = true`; append the stage-A entry; **reserve exposure
    before the transfer**, not after.

**Interactions**

11. `token.safeTransfer(order.recipient, order.outputAmount)`

`nonReentrant` throughout. RIPE and GREEN are Vyper ERC-20s with no transfer
hooks, so reentrancy is not reachable today; the guarantee should not depend on
the token staying hook-free.

### Check 8 is not a solvency invariant

`order.inputAmount` is an assertion inside a solver-signed order, not an
observation of a deposit. Under solver-key compromise both amounts are
attacker-chosen and the check passes trivially at `inputAmount == outputAmount`.

Keep the check — it catches a *buggy* solver overpaying against a real deposit,
which is a live failure mode. Do not describe it as protecting the float. The
caps do that, and only the caps do that.

### Why the fill reads `mintEnabled` (H-6)

A fill is a `safeTransfer`, which never consults `mintEnabled`. A refill is a
CCIP burn/mint whose destination leg enters `RipeHq.canMintRipe` and returns
`False` on `mintEnabled` alone (`RipeHq.vy:392`). Left uncoupled,
`setMintingEnabled(false)` therefore **disables the safe leg and leaves the
risky one running**: fills drain the float at full rate while every replenishment
strands, already burned on the origin.

Gating the fill on `mintEnabled` restores that lever to being a complete stop.
`lanePaused` remains separate so a lane-specific incident does not require
halting protocol issuance.

**Consequence to state explicitly, because the fix relocates the harm rather
than removing it.** Coupling the fill to `mintEnabled` means a protocol-wide
incident unrelated to bridging now rejects fills for users whose origin deposit
is already irreversible. That is the correct trade — the alternative is a fully
drained float — but it moves the loss from Ripe's balance sheet onto in-flight
users' deposits, and it should be a chosen position with a runbook, not
something discovered during an incident. See "Pre-fill exposure" below.

## Ledger transitions

`recordWithdrawn` (A→B) and `recordRestored` (B→cleared) **must not free
capacity or reset age on a solver or keeper assertion.** A compromised key that
can clear the cap repeatedly can drain the float regardless of how the cap is
sized — the cap would bound a single fill rather than the position.

Exposure may be reduced only against verifiable destination restoration.
Practically that means the contract observes the CCIP delivery itself, or the
transition is governance/multisig-authorized. It must never be a role the solver
holds.

Separate **in-flight** from **known-failed** in stage B and alarm on the latter
immediately. Otherwise a stranded CCIP message ages silently into a cap breach,
and the halt reports "exposure too old" when the true condition is "a CCIP
message failed" — the same signal for a solvency problem and an operational one.

## The three caps, and why the third exists

**Notional** bounds the balance sheet. **Age** is the control that matters most,
because Relay's withdrawal is gated on a vendor signature with no timeout, so
elapsed time is the real signal.

**Entry count** (M-4) exists to protect the contract's own liveness. Enforcing
"no entry older than `maxAge`" needs the oldest outstanding entry, and the naive
implementation iterates on every `fill` — O(n) on the hot path, growing with
volume, and adversarially reachable: a compromised key that cannot exceed the
notional cap can still emit many minimum-size fills until `fill` is too
expensive to call. The most-relied-upon control has a naive implementation that
is a self-DoS. A FIFO head pointer is O(1) but assumes in-order settlement,
which is not established for Relay; one out-of-order settlement stalls it.

The entry-count cap bounds iteration directly, is O(1) to enforce, and also
bounds the batch size the ledger transitions must handle.

### Sizing `maxStageBAge`

Do **not** size it off the happy path. The four measured CCIP transfers span
18m52s–24m46s per hop, 44m11s round trip, but two of those were sent 96 seconds
apart on the same lane and landed 6m24s apart — so the variance is intra-lane,
consistent with commit batching, and **24m46s is the maximum of four samples,
not an upper bound.** The true tail is source finality plus one full round
interval, which has not been measured.

A stranded message is also not a slow message: recovery needs the destination
condition cleared *and* a manual re-execution, unbounded in wall-clock and
dependent on a runbook that does not exist. Size `maxStageBAge` from finality
plus one measured round interval plus margin. Measure the round interval before
fixing any number.

## Pre-fill exposure, and the soft/hard cap

Every fail-closed check in `fill` is a way for a user who has **already
deposited** to be rejected. Deposits into the Relay Depository are
permissionless and Ripe cannot prevent them, and the Depository has no
permissionless timeout refund — recovery is Relay-authorized. So a rejection
after deposit leaves the user's origin tokens locked pending a path Ripe does
not control.

The lifecycle is therefore asymmetric and must be documented as such:

- **Before fill:** the user bears non-delivery and escrow risk.
- **After fill:** the user is done; Relay attestation and withdrawal risk is
  entirely Ripe's.

The UI must never present "deposit accepted" as a guaranteed fill.

**Mechanism for the cap case: enforce two thresholds.** Quote and UI gate on
`softCap`; `fill` enforces `hardCap`, with `softCap < hardCap`. The gap absorbs
deposits that were already in flight when the soft cap was reached, sized to
peak in-flight notional over the deposit→fill window. A user quoted below the
soft cap then cannot be rejected for cap reasons unless the gap itself is
exhausted, which is an incident rather than ordinary operation. The cost is that
the gap is reserved rather than usable — a deliberate reserve, not lost capital.

**This does not help for `lanePaused` or `mintEnabled`.** Those are step
functions, not gradual thresholds; there is no headroom to reserve. For those,
the only mitigations are minimizing the deposit→fill window, disclosure at
deposit time, and a written recovery runbook for reaching Relay. That residual
is not engineerable away and belongs in the owner decision.

## Roles — asymmetric by construction

| Action | Who | Timing |
| --- | --- | --- |
| Pause lane | any guardian | immediate |
| Unpause | governance | timelocked |
| Lower any cap | governance | immediate |
| Raise any cap | governance | timelocked |
| Remove solver signer | any guardian | immediate |
| Add/rotate solver signer | governance | timelocked |
| Fund float | treasury | — |
| Withdraw float | governance | timelocked |

Every safe direction is fast; every dangerous direction is slow.

## Prohibited

- **No RipeHq registration and no mint capability.** There is no per-department
  mint cap in the protocol and department removal is timelocked, so a
  mint-authorized filler has no proportionate kill switch — the only in-timelock
  lever is `setMintingEnabled(false)`, which is protocol-wide. Do not site the
  float in `Endaoment`, which already holds `canMintGreen`.
- **No upgradeability.** One immutable instance per chain/token.
- **No `execute(to, data, value)` escape hatch.** That is precisely the pattern
  that makes Relay's own Depository a single-key total-loss risk. A rescue path,
  if any, is `sweep(token)` to a **fixed** governance address with no arbitrary
  calldata and no caller-chosen recipient.

## Invariants

1. `stageANotional + stageBNotional <= fundedCapital` at all times.
2. No `orderId` is filled twice, on this chain or any other.
3. No token leaves while `lanePaused` or while `mintEnabled == False`.
4. No cap is ever exceeded, including within a single block.
5. Exposure never decreases, and no entry age resets, without verified
   destination restoration.
6. `fill` gas is bounded independent of outstanding entry count.

## Test obligations

Red-before-green, failure paths first. Beyond obligations 15–17 already recorded
in the security review (H-6 gating, drain ordering, gas bounding):

- Every check at its boundary: cap at exactly max, deadline at exactly
  `block.timestamp`, `outputAmount == inputAmount + 1`, entry count at cap.
- Replay: same order twice; the same order on the paired chain — the test that
  matters if the contracts are CREATE2'd to a shared address, since
  `address(this)` then stops distinguishing them and `chainid` in the domain
  separator becomes the sole defense.
- **Valid signature, no corresponding origin deposit.** Assert the loss is
  bounded by the caps. If this test does not exist, the caps are decorative.
- Forged ledger transition: a solver-signed or keeper-signed `recordWithdrawn` /
  `recordRestored` cannot free capacity or reset age.
- Soft/hard cap: a fill quoted below `softCap` succeeds when `stageANotional`
  has since risen above `softCap` but below `hardCap`.
- Fuzz: arbitrary interleavings of fill / withdraw / restore never violate
  invariant 1.
- Invariant run: no path transfers a single token while paused or while
  destination minting is disabled.

## Open items

1. `maxStageBAge` cannot be fixed until the CCIP commit round interval is
   measured. Four samples are not a distribution.
2. Whether Relay settles withdrawals in order is unestablished, and it
   determines whether the ledger can use a FIFO head pointer or must rely on the
   entry-count cap alone.
3. Relay's production attestor behaviour is not provable from source; the
   absence of a solver allowlist in the repository does not establish its
   absence in the running service.
4. The residual pre-fill stranding risk under `lanePaused` / `mintEnabled` is an
   owner acceptance, not an engineering item.
