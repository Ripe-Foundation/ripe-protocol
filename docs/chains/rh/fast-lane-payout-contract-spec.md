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
H-1/H-2/H-4, choose the provider economics, or replace any owner decision in
the synthesis.

## What the contract is

One immutable instance per chain, per token. It holds Ripe's destination float
and lets the configured solver EOA pay a user against a solver-signed Relay
order after the solver's off-chain service observes the deposit. That signature
commits to the quoted order terms; it does **not** assert or prove that the user
deposited on the origin chain. The contract then tracks the resulting exposure
until the origin receivable is withdrawn and the destination float is restored.

RIPE and GREEN across Base and Robinhood is therefore four deployments. A
multi-token variant halves that; a fixed `immutable token` is preferred because
it removes a hot-path validation and makes the review statement "this contract
can only ever move RIPE" checkable by inspection.

## What the contract cannot do

**It cannot verify that the origin deposit happened.** There is no proof of the
origin deposit on this chain. The canonical Relay order signature exists before
the deposit and attests only to the order fields.

Everything else in this document is hygiene around that fact. If the solver key
is compromised, the attacker signs orders for deposits that never happened and
the float pays out. Therefore:

> **Against solver/service compromise, the aggregate and per-fill caps are the
> loss boundary. The signature does not prove a deposit.**

Requesting `includeProtocolData=true` returns the canonical order, order id, and
the **solver's** ECDSA signature. It does not return a second Relay
Oracle/attestor signature. The payout must recompute and bind that material, but
it remains one Ripe solver trust root and no deposit proof. A separate custom
Ripe authorization signed by the same key could improve serialization or replay
hygiene; it would not improve signer-compromise resistance.

That signature is returned to the quote recipient before deposit, so it cannot
authorize `fill` by itself. Otherwise any quoted user could call `fill` without
depositing and consume the full aggregate cap without compromising a key. The
minimum topology therefore also requires a direct transaction from the
configured solver EOA after its service accepts the observed deposit. A future
permissionless-submit design instead needs a distinct post-deposit Ripe
authorization that is unavailable at quote time and a separate review.

This API meaning is pinned in `relay-docs@94bf717`
`references/api/changelog.mdx:83-87` and `relay-kit@a5f6cb5`
`packages/sdk/src/types/api.ts:2957-2979`; both call `orderSignature` the solver's
signature over `orderId`.

The only way to prove the remote deposit on this chain is an authenticated
cross-chain proof. Waiting for that proof removes the speed advantage. Fast
means paying before proof. The contract's job is to bound that risk, not claim
to eliminate it.

## State

```solidity
IERC20  immutable token;          // destination token; never a fill parameter
address immutable hq;             // expected destination RipeHq (H-6)
address immutable treasury;       // sole payout-token withdrawal recipient
address immutable originToken;    // paired token admitted by Relay on origin
address immutable relayDepository;
address immutable ccipRouter;
address immutable originRebalancer;
uint64  immutable originCcipSelector;
bytes32 immutable originChainIdHash;
bytes32 immutable destinationChainIdHash;
bytes32 immutable solverChainIdHash;
uint256 immutable deploymentChainId; // constructor captures block.chainid
uint64  maxQuoteLifetime;
uint64  maxRefundLifetime;
uint64  immutable originFinalityMargin;
uint64  immutable retirementDelay;
address solverSigner;             // Relay-required EOA; zero means disabled
bool    lanePaused;               // lane-scoped gate
bool    retired;                  // irreversible: no new fills/reactivation
uint64  retiredAt;

mapping(bytes32 => bool) filled;  // replay guard, keyed by canonical order id

// The aggregate caps are the hard loss/storage boundary. A stage transition
// never changes either aggregate.
uint256 outstandingNotional;  uint256 maxAggregateExposure;
uint32  outstandingEntries;   uint32  maxOutstandingEntries;
uint256 maxFillAmount;         // independent per-transfer hard ceiling

// Two-stage exposure ledger. Stage thresholds gate new fills and trip health;
// truthful reconciliation is still recorded if a threshold is crossed.
//   A: paid here, origin receivable not yet withdrawn
//   B: origin withdrawn, destination float not yet restored
uint256 stageANotional;  uint256 maxStageANotional;
uint256 stageAQuoteThreshold; // advisory API/UI admission; no reservation
uint64  maxStageAAge;    uint32  stageAEntries;  uint32 maxStageAEntries;
uint256 stageBNotional;  uint256 maxStageBNotional;
uint64  maxStageBAge;    uint32  stageBEntries;  uint32 maxStageBEntries;
// per-entry {orderId, amount, filledAt, withdrawnAt, stage, index links}
mapping(bytes32 => bool) consumedCcipMessage;
```

`maxAggregateExposure` is the chain-local, token-local full-loss allocation
approved by governance. It is independent of the token balance and cannot grow
merely because treasury adds more float. The governance manifest must ensure
the allocations across all deployments sum to no more than the approved
common-mode budget; isolated contracts cannot enforce that cross-chain sum.

Deploy paused with a zero signer. Unpause is impossible until every immutable
address/chain identifier, non-zero threshold, route-health dependency, and
solver policy is configured and readable. Enforce in the contract or the
governance deployment manifest, as appropriate:

- `stageAQuoteThreshold <= maxStageANotional <= maxAggregateExposure`;
- `maxFillAmount <= maxStageANotional` and
  `maxFillAmount <= maxAggregateExposure`;
- when token-pool rate limiting is enabled, `maxFillAmount` fits one refill
  message under the configured origin outbound and destination inbound
  capacities; it also fits every applicable per-message limit;
- `maxStageBNotional <= maxAggregateExposure`;
- both per-stage entry thresholds are no greater than
  `maxOutstandingEntries`; and
- quote/refund/age limits fit their timestamp types and cannot be raised except
  through the timelocked authority; and
- `retirementDelay >= max(maxQuoteLifetime, maxRefundLifetime) +
  originFinalityMargin`, with overflow-safe setters preserving that relation.

Use battle-tested non-upgradeable libraries for safe ERC-20 calls, ECDSA
recovery, reentrancy protection, and role administration. Timelocked actions
must be callable only by the actual on-chain timelock/governance executor; a
comment saying "timelocked" is not enforcement.

## `fill(OrderV1, bytes orderSignature, bytes32[] orderIdSuffix)`

The implementation must reproduce Relay's pinned canonical order format, not a
locally invented approximation. The one-element dynamic `orderIdSuffix` is
intentional: Relay's EVM attestor requires the raw fill transaction calldata to
end with the canonical order id. This must be the **top-level transaction**
calldata, not the calldata of an inner payout call. Require a direct call from
the configured solver EOA, `orderIdSuffix.length == 1`, its value equal to the
recomputed id, and the final 32 bytes of `msg.data` equal to that id. A different
ABI is acceptable only if it preserves and tests the same suffix property.

Pinned behavior: `relay-settlement@98ad1a0` defines the `v1` order and computes
the id with `hashStruct` in `packages/sdk/src/order/index.ts:19-192`;
`relay-protocol-oracle@55b22de` verifies `personal_sign(orderId)` and then
separately attests the deposit in
`src/services/attestation/index.ts:299-327`. Its EVM fill verifier requires the
transaction input suffix in
`src/services/attestation/vm/ethereum-vm/index.ts:407-468`. Port those semantics
and lock them with shared test vectors.

Provider-onboarding facts remain blockers, not implementation details. The
captured standard Relay orders encode Relay's Router, rather than a custom Ripe
payout, in `output.extraData.fillContract`; Relay must demonstrate a supported
quote/deposit path that signs this payout instance. Captured exact-input examples
also have `minimumAmount != expectedAmount`; this lane requires a demonstrated
exact-output or custom quote policy that makes the equality below intentional
and denominates its fees so `input == output + feeSum`. Until a live per-token
quote proves every property, the lane remains paused.

### Solver broadcast authorization

The direct-caller gate makes the solver service's second transaction signature
authorization-critical. Before the HSM/MPC may sign and broadcast `fill`, the
service must observe a successful origin transaction finalized under the
configured policy and independently verify the emitted deposit against the
quote/order:

- exact origin chain and configured Relay Depository log address;
- canonical order id, configured origin token, and effective depositor expected
  for that quote;
- actual deposited amount and the exact fee-aware economics
  `input == output + feeSum`;
- destination chain, payout instance, token, and user recipient; and
- uniqueness of `(originChain, transactionHash, logIndex)` and `orderId` in a
  durable idempotency store before signing.

The HSM/MPC transaction policy also allowlists the payout address, `fill`
selector, recomputed order id/calldata suffix, and maximum value/gas policy. A
pending, reverted, wrong-contract, wrong-token, dust, wrong-depositor,
wrong-amount, duplicate, or pre-finality event authorizes nothing. A reorg before
the required finality invalidates the observation and must never race a
broadcast. This service is not a deposit proof available to the payout contract;
service/HSM compromise remains bounded by the on-chain caps.

Checks, then effects, then the interaction and its exact balance-delta
postcondition. All ledger state changes happen before the external transfer.

**Checks**

1. `msg.sender == tx.origin == solverSigner`, `!retired`, and
   `solverSigner.code.length == 0`. This intentionally excludes wrappers,
   account abstraction, and EIP-7702 delegated code: Relay checks the top-level
   transaction input suffix, and the current topology requires its solver to be
   an EOA. Then require `!lanePaused`, `token.ripeHq() == hq`, and
   `RipeHq(hq).mintEnabled() == true`; destination token `isPaused() == false`;
   and neither `address(this)` nor the recipient is blacklisted. Every external
   getter is read with a fail-closed staticcall: revert, malformed return data,
   a changed HQ, or `false` rejects the fill. Because the token HQ is mutable,
   an HQ migration retires this immutable instance and requires a new deployment.
2. The order is the supported Relay `v1` shape and every dynamic collection is
   structurally bounded: exactly one input, input weight `1`, exactly one output
   payment, no output calls, and only the explicitly approved refund and fee
   shapes. Each direct address-valued `bytes` field for the EVM lane has the
   canonical 20-byte form. `output.extraData` instead has the exact canonical
   32-byte ABI encoding of `(address fillContract)`. Unknown versions,
   non-canonical encodings, trailing bytes, or extra fields fail closed.
3. Recompute Relay's canonical `orderId` from **all** normalized fields using the
   pinned SDK's EIP-712 `hashStruct` types. Relay does not domain-separate this
   struct hash with this payout contract. Verify the supplied signature as the
   EIP-191 `personal_sign` of that `orderId`, and require the recovered address
   to equal both `order.solver` and the configured `solverSigner`.
4. The one-element suffix and the final calldata word equal the recomputed id,
   and `filled[orderId] == false`.
5. Require `block.chainid == deploymentChainId`, then bind every order term:
   configured solver-chain identity; configured origin chain and origin token;
   exact input amount; each approved refund's `chainId`, recipient, currency,
   `minimumAmount`, deadline, and extra data; destination chain; exactly one
   non-zero recipient that is not `address(this)`; destination `token`; every
   fee's `recipientChainId`, recipient, `currencyChainId`, currency, and amount;
   empty calls; and the
   canonically decoded `output.extraData.fillContract == address(this)`.
   The fill-contract binding prevents the same canonical order from authorizing
   a second payout instance on the same chain.
6. `block.timestamp <= order.output.deadline <= block.timestamp +
   maxQuoteLifetime`. Apply `maxRefundLifetime` to every refund deadline as well.
7. Let `payment = order.output.payments[0]`. For this fixed-token lane, require
   `payment.minimumAmount == payment.expectedAmount > 0` and transfer that exact
   value. Require every fill fee's `currencyChainId`/currency to be the
   configured origin chain/token, sum all fee amounts with checked arithmetic,
   and require `feeSum == inputAmount - payment` after first proving
   `payment <= inputAmount`. This accounts for Relay debiting signed fill fees
   from the solver's Hub balance and makes the net origin receivable equal the
   exact payout/restoration ledger amount, with no untracked surplus or shortfall
   (`relay-protocol-oracle@55b22de`,
   `src/services/attestation/index.ts:1917-1975`). Also require
   `payment <= maxFillAmount`. If a live Relay
   schema cannot satisfy exact minimum/expected equality or the fee-denomination
   policy, stop and review an explicit treasury-subsidy/accounting alternative;
   do not silently choose one amount or ignore the shortfall.
8. Snapshot the contract token balance and require it covers the exact payout.
   The existing stage-A and stage-B health thresholds are not breached, and
   adding the payout stays
   within stage-A notional/count plus the aggregate notional/count hard caps.
   Use subtraction-form comparisons (`amount <= max - current` after checking
   `current <= max`) so the proof does not depend only on overflow reverts.

**Effects**

9. Set `filled[orderId] = true`; append the stage-A entry; increment stage-A and
   aggregate notional/count; and reserve exposure **before the transfer**, not
   after.

**Interactions**

10. `token.safeTransfer(recipient, payment.minimumAmount)`, then require the
    contract's balance decreased by exactly that amount. This fixed-token
    postcondition rejects self-transfer/no-delta behavior that can still emit a
    `Transfer` log and be misclassified as a Relay fill
    (`relay-protocol-oracle@55b22de ethereum-vm/index.ts:494-507`).

`nonReentrant` throughout. RIPE and GREEN are Vyper ERC-20s with no transfer
hooks, so reentrancy is not reachable today; the guarantee should not depend on
the token staying hook-free.

The origin withdrawal receiver and rebalancing settlement addresses are remote
state and cannot be checked by these local token getters. H-2 therefore remains
an implementation gate: the lane stays paused until a separately reviewed,
fail-closed settlement-health mechanism binds those addresses. An API status is
not an on-chain substitute.

### The amount comparison is not a solvency invariant

The signed input amount and fees are order terms, not observations of a deposit.
Under solver-key compromise they are attacker-chosen and the net-receivable
comparison passes trivially when the attacker makes them internally consistent.

Keep the check — it catches a *buggy* solver whose payout plus Relay-deducted
fees exceeds a genuine input. Without it, even an honest deposit can leave less
origin receivable than the exact Stage-B restoration amount. Do not describe it
as proving solvency. Against a compromised solver, the aggregate and per-fill
caps bound the float loss.

### Why the fill reads `mintEnabled` (H-6)

A fill is a `safeTransfer`, which never consults `mintEnabled`. A refill is a
CCIP burn/mint whose destination leg enters `RipeHq.canMintRipe` or
`RipeHq.canMintGreen`; both return `False` on `mintEnabled` before consulting
the caller's token-specific capability (`RipeHq.vy:377-399`). Left uncoupled,
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

Neither transition is authorized by the caller's role. Proof submission can be
permissionless; proof validation is the authority.

`recordWithdrawn` must verify finalized origin evidence binding the origin
chain, Relay Depository, token, canonical order id, amount, withdrawal receiver,
remote timestamp, and a replay-protected proof id. It moves exactly that entry
from A to B, leaves `outstandingNotional` and `outstandingEntries` unchanged,
preserves `filledAt`, and records the verified `withdrawnAt`. A late proof must
not make the entry younger. Until this proof/coordinator is designed and
reviewed, entries remain reserved in A and the production lane remains blocked.

`recordRestored` may decrease aggregate exposure only by destination inventory
received and credited exactly once. The selected construction is an
authenticated CCIP receiver callback, not a balance poll or privileged
assertion. The payout must implement and advertise
`IAny2EVMMessageReceiver` through ERC-165, using the version-pinned official
receiver base or an exact reviewed interface/ERC-165 implementation. Otherwise
the OffRamp can transfer the token while skipping the callback. The callback
must verify:

- `msg.sender` is the immutable CCIP Router;
- the source selector and decoded source sender are the configured origin lane
  and rebalancer;
- the message contains the one expected token and an exact received amount;
- every payload entry id is unique, is live in stage B, has the exact encoded
  amount, and the encoded amounts sum exactly to the received amount; and
- the CCIP `messageId` has not been consumed.

The current wallet-style CCIP transfers use empty data and callback gas `0`, so
they only transfer tokens; they cannot satisfy this proof. The refill design
therefore needs a separately reviewed origin rebalancer, a data-bearing message,
and separate worst-case gas measurements plus margin for (a) the token-pool
`releaseOrMint` path and (b) `ccipReceive`. The message `gasLimit` covers only
the callback; it cannot repair an undersized token-pool `destGasAmount`. A direct
token transfer, an unallocated balance increase, an API status, or a
governance/multisig signature does not clear exposure. Governance can pause or
retire the instance, but an accounting write-off must not reopen capacity.

The origin rebalancer must request out-of-order execution for every refill,
subject to explicit support on the configured lane. The deliberate failed-message
path below must not head-of-line block unrelated later refills. Treat
`allowOutOfOrderExecution == true` as a version-pinned message invariant and
negative-test any encoding that clears it.

Proof ordering is deliberately fail-closed rather than another credit ledger.
If an authenticated refill arrives while any referenced entry is still in stage
A, the callback reverts. That revert atomically unwinds the token transfer and
leaves the CCIP message eligible for manual re-execution after the finalized
A→B proof has been recorded. The runbook must detect this state and retry; no
stage-A entry, unknown id, residual amount, or unrelated balance increase may be
allocated. A message and each entry amount can be consumed exactly once.

The current construction has no authenticated destination-side proof that a
CCIP attempt failed, and the reverting callback cannot persist a failure flag.
Therefore `known-failed` is an **operational monitoring classification**, not
writable payout state: the watcher alerts, a guardian uses its existing pause
power, and no exposure is cleared. Do not add an on-chain failure flag until its
bounded storage, evidence authority, and clear-on-authenticated-success semantics
are separately specified.

Truthful reconciliation is always recordable while the lane is paused or a
stage threshold is already breached. A verified A→B transition does not revert
because B is full; it records the external fact and atomically marks the lane
unhealthy. Aggregate notional and entry count do not increase on a transition,
so the hard loss/storage boundary remains intact.

Operationally separate **in-flight** from **known-failed** stage-B entries and
alarm/pause on the latter immediately. Otherwise a stranded CCIP message ages
silently into a threshold breach, and the halt reports "exposure too old" when
the true condition is "a CCIP message failed" — the same signal for a solvency
problem and an operational one.

## The three stage thresholds, and why the third exists

Per-stage notional, age, and entry-count values are admission/health thresholds,
not all hard state invariants. A new fill must fit stage A and both stages must be
healthy, but a truthful A→B transition can cross a stage-B threshold and then
atomically pause the lane. Only `maxFillAmount`, `maxAggregateExposure`, and
`maxOutstandingEntries` are hard payout/storage invariants across transitions.

**Notional** bounds the balance sheet. **Age** is the control that matters most,
because Relay's withdrawal is gated on a vendor signature with no timeout, so
elapsed time is the real signal.

**Entry count** (M-4) exists to protect the contract's own liveness. Enforcing
"no entry older than `maxAge`" needs the oldest outstanding entry, and the naive
implementation iterates on every `fill` — O(n) on the hot path, growing with
volume, and adversarially reachable: a compromised key that cannot exceed the
notional cap can still emit many minimum-size fills until `fill` is too
expensive to call. The most-relied-upon control has a naive implementation that
is a self-DoS.

The entry-count cap is O(1) to check and bounds live storage and reconciliation
batch size. It does **not** turn a scan into O(1). `fill` must not scan. A
chronological doubly linked list permits O(1) append, arbitrary O(1) unlink, and
O(1) oldest lookup for stage A. Stage-B timestamps come from authenticated
remote facts that may be submitted out of order; use an indexed min-heap or an
equivalent explicitly bounded structure for O(1) oldest lookup and O(log
`maxOutstandingEntries`) insert/removal. Do not use a FIFO assumption unless
Relay ordering is first proven and made an invariant.

A reverting `fill` also cannot persist a pause. Expose a permissionless
`tripStaleExposure()` that reads the oldest structures, sets `lanePaused`, and
emits the offending stage/order id. Independently, every `fill` still rejects
when an age threshold is reached even if nobody has called the trip function.
Define the boundary once: an entry is healthy only while
`block.timestamp - startedAt < maxAge`; equality is stale. Reject authenticated
timestamps in the future before doing the subtraction.

### Sizing `maxStageBAge`

Do **not** size it from the four-point sample. Base→Robinhood sequences 1806 and
1807 were sent 96 seconds apart but arrived 384 seconds apart; their delivery
times differ by 288 seconds (19m58s versus 24m46s). This proves that the observed
variance is intra-lane. It does not identify the mechanism. Commit batching is
a hypothesis to test with consecutive sequence numbers and commit/execution
timestamps, not a conclusion.

`24m46s` is the maximum of four observations, not an upper bound or SLA. The
two-direction `44m11s` sum is also not a stage-B input: one refill is one
relevant CCIP hop. Those four observations measure only `ccipSend` inclusion to
destination receipt, while stage B begins at the authenticated origin
`withdrawnAt`. Its ordinary end-to-end budget must also measure withdrawal
finalization/detection; origin-proof generation, delivery, and destination
inclusion; rebalancer queue or batch cadence; nonce management; and source
transaction submission/inclusion before `ccipSend`.

If measurements establish that healthy messages are included by the next commit
round, add the source-finality policy, a full measured time-to-next-round bound,
destination execution, and explicit margin to that pre-send operational delay.
Include destination confirmation time too only if the accounting policy waits
for it before clearing exposure. Until every applicable segment is measured,
fix no numeric cap.

A stranded message is also not a slow message: recovery needs the destination
condition cleared *and* a manual re-execution, unbounded in wall-clock and
dependent on a runbook that does not exist. Missed rounds, known failures, and
manual re-execution are incident paths; even a confirmed batching model would
not prove that every message is bounded by one round.

## Pre-fill exposure, and the advisory quote threshold

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

`stageAQuoteThreshold` is an advisory API/UI admission threshold below the
`maxStageANotional` fill ceiling. The gap reduces ordinary post-deposit rejection risk, but
it reserves nothing. Two concurrent quotes can both observe the same headroom;
after the first fill consumes it, the second can still hit the hard cap. A
permissionless direct depositor can bypass quoting entirely. Gap exhaustion is
a capacity race, not necessarily an incident, and the UI must disclose it.

If a contractual fill guarantee is required, the destination contract must
create an order-bound reservation **before** the origin deposit, count it against
the aggregate hard cap, atomically convert it on fill, and permit expiry cleanup.
That is a separate state machine and audit surface. An API quote or off-chain
reservation cannot provide the same guarantee.

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
| Lower `maxFillAmount` or a stage threshold | governance | immediate |
| Lower an aggregate hard cap no lower than current exposure/count | governance | immediate |
| Raise any cap or threshold | governance | timelocked |
| Remove solver signer | any guardian | immediate |
| Add/rotate solver signer | governance | timelocked |
| Fund float | treasury | — |
| Submit reconciliation proof | anyone | proof-validated |
| Trip a breached health threshold | anyone | immediate |
| Irreversibly retire instance | governance | timelocked; atomically pause/disable signer |
| Withdraw retired float | governance | timelocked and quiescent |

Every safe direction is fast; every dangerous direction is slow.

Lowering a stage threshold below current exposure records the lower target and
pauses the lane; it never deletes entries or rewrites history to make the new
setting appear satisfied. An aggregate hard cap cannot be set below its current
outstanding value: governance may immediately lower it to the current value and
lower it again after authenticated restoration reduces exposure. Raising a
cap/threshold or unpausing remains timelocked and still requires every external
health check to pass at execution.

`retire()` is one-way. It atomically sets `retired = true`, records `retiredAt`,
sets `lanePaused = true`, and clears `solverSigner`. Once retired, unpause,
signer add/rotation, and every new fill/config reactivation revert forever;
proof-validated reconciliation and authenticated CCIP restoration remain
callable so existing exposure can drain.

`maxFillAmount` governs new fills only. Lowering it never makes an existing
larger entry ineligible for exact restoration. Because the payout cannot enforce
remote pool configuration, pool admins must pause and drain all entries larger
than a proposed origin-outbound/destination-inbound capacity or per-message
limit before lowering that remote limit. A cross-chain monitor revalidates both
pools and trips the guardian pause on drift. If that coordination cannot be
made enforceable, the exact-entry design must be replaced with separately
reviewed partial-restoration accounting.

## Prohibited

- **No RipeHq registration and no mint capability.** There is no per-department
  mint cap in the protocol and department removal is timelocked, so a
  mint-authorized filler has no proportionate kill switch — the only in-timelock
  lever is `setMintingEnabled(false)`, which is protocol-wide. Do not site the
  float in `Endaoment`, which already holds `canMintGreen`.
- **No upgradeability.** One immutable instance per chain/token.
- **No `execute(to, data, value)` escape hatch.** That is precisely the pattern
  that makes Relay's own Depository a single-key total-loss risk. A rescue path,
  if any, has no arbitrary calldata and no caller-chosen recipient.
- **No live-instance payout-token sweep.** `withdrawFloat(amount)` can send only
  the immutable payout token to the immutable treasury. It requires a paused,
  retired instance, a disabled solver, zero outstanding entries, and
  `block.timestamp >= uint256(retiredAt) + retirementDelay`. The immutable delay is no
  shorter than every permitted order/refund lifetime plus origin finality.
  Measure the actual balance delta. Recovering an
  unrelated token is a separate function that requires `asset != token`.

## Invariants

1. `outstandingNotional == stageANotional + stageBNotional ==` the sum of all
   active entry amounts. It also equals cumulative exact payouts minus
   cumulative authenticated, allocated destination restoration.
2. `outstandingEntries == stageAEntries + stageBEntries` and equals the number
   of active entries. A→B changes neither aggregate.
3. Every payout is at most `maxFillAmount`, and a successful fill's post-state
   never exceeds `maxAggregateExposure` or `maxOutstandingEntries`, including
   for concurrent fills in one block.
4. Within one deployment, `filled[orderId]` changes from false to true at most
   once. The validated destination chain, token, and
   `output.extraData.fillContract` make that exact signed order invalid at the
   paired chain or a second payout instance. Independent deployments cannot
   prevent a compromised signer from signing two different orders for one
   economic deposit; partitioned aggregate loss budgets bound that case.
5. No payout token leaves through `fill` while the lane or token is paused, the
   token's current HQ differs from the expected HQ, destination minting is
   disabled/unreadable, the signer is disabled, or a required address is
   blacklisted/unhealthy.
6. A→B preserves amount and `filledAt`; only verified origin evidence may add
   `withdrawnAt`. Aggregate exposure decreases only with exact, replay-protected
   destination restoration.
7. `fill` performs no linear scan. Its work is constant except for an explicitly
   bounded logarithmic age-index update.
8. A truthful reconciliation remains recordable when paused or unhealthy; a
   stage-threshold breach trips the lane rather than erasing the remote fact.

## Test obligations

Red-before-green, failure paths first. Beyond obligations 15–18 already recorded
in the security review (H-6 gating, drain ordering, gas bounding):

- Hash/signature parity against pinned Relay SDK fixtures: every canonical field
  changes the id; EIP-191 recovery succeeds; a custom EIP-712-domain signature
  does not masquerade as Relay's order signature.
- Relay EVM fill compatibility: valid calldata ends in the recomputed order id;
  a missing, duplicated, wrong, or non-terminal suffix reverts. A solver call
  through a wrapper and an EIP-7702-delegated solver both revert, because their
  top-level transaction input is not the direct payout call Relay will inspect.
- Every order-shape and amount check at its boundary: zero/multiple inputs,
  weight other than `1`, zero/multiple output payments, any call, unknown
  version, unapproved fee/refund, wrong fill contract, exact deadline, output one
  unit above net input, one unit above `maxFillAmount`, and minimum differing
  from expected. Exercise zero/multiple fees, wrong fee currency/chain, exact
  `output + feeSum == input`, one unit below/above, and fee-sum overflow. A
  self-recipient reverts, and every successful fill decreases the payout balance
  by the exact payment.
- Every liveness getter fails closed on `false`, revert, empty data, short data,
  and malformed boolean; include token pause plus contract/recipient blacklist.
  After `token.confirmHqChange`, the old payout instance rejects every fill even
  when its old HQ still reports `mintEnabled == true`.
- Cap arithmetic at exactly max, one unit above, `type(uint256).max`, entry count
  at max, and multiple fills in one block.
- Replay: same order twice; same order on the paired chain; same-chain second
  payout instance. Also demonstrate that a separately signed second order is
  not global replay protection and remains bounded by the aggregate cap.
- **Valid pre-deposit quote signature, no corresponding origin deposit.** The
  quoted user cannot call `fill`; no balance or ledger state changes. The paired
  threat test calls the same order directly from the configured solver and
  demonstrates that solver service/key compromise is bounded by the aggregate
  and per-fill caps. If this test does not exist, the caps are decorative.
- Solver release gate: a finalized exact configured-Depository event permits one
  direct broadcast. Pending/reverted/reorged, wrong chain/contract/token/order
  id/depositor/recipient, dust/wrong amount/net economics, and duplicate
  transaction-log/order ids never reach the HSM signing call.
- Forged ledger transition: solver, keeper, guardian, and governance assertions
  cannot move or clear exposure. Exercise wrong origin/depository/token/order/
  amount/receiver, non-final proof, replayed proof, and late proof timestamps.
- CCIP callback: advertise the pinned receiver interface and prove the OffRamp
  invokes it. Wrong router/source/sender/token/amount/id, duplicate entry,
  residual amount, direct token donation, and replay cannot clear exposure. A
  stage-A payload atomically reverts the token receipt; after verified A→B, a
  manual re-execution succeeds exactly once. Measure and bound token-pool gas and
  callback gas independently. A refill with out-of-order execution disabled is
  rejected before send, and one failed refill cannot block a later message.
- Refill sizing: when live pool rate limiting is enabled, `maxFillAmount` fits a
  single origin outbound and destination inbound message. The fork test fails if
  either enabled capacity or any applicable per-message limit is below it.
  Lowering `maxFillAmount` does not block restoration of an existing larger
  entry; a remote pool-limit reduction is rejected by the operational change
  procedure until all larger entries drain, and config drift pauses new fills.
- Quote-threshold race: two quotes can share headroom; after one consumes the
  hard capacity, the second reverts. A fill is not rejected merely because the
  advisory threshold was crossed if all hard caps still have room.
- Age structures: empty, exactly `maxAge`, `maxAge + 1`, arbitrary out-of-order
  reconciliation, persistent `tripStaleExposure`, and gas at one versus
  `maxOutstandingEntries`.
- Fuzz: arbitrary interleavings of fill / verified withdraw / authenticated
  restore preserve invariants 1–3 and never double-allocate restoration.
- Invariant run: no `fill` transfers payout tokens out while paused or while
  destination minting is disabled/unreadable; a valid authenticated restoration
  remains recordable while paused; retirement cannot withdraw the payout token
  with any outstanding entry. Retirement is irreversible; early sweep,
  unpause/signer re-add, and config reactivation all revert, while reconciliation
  continues.

## Open items

1. `maxStageBAge` cannot be fixed from four send→receipt samples. Also measure
   withdrawal finalization/detection, origin-proof generation/delivery and
   destination inclusion, and withdrawal→`ccipSend` queue, nonce, submission,
   and inclusion delay. Measure source-finality and commit/execution timing
   across consecutive sequence numbers and multiple rounds; only use a
   round-based model if that evidence confirms it.
2. The finalized origin-withdrawal proof/coordinator, proof finality, replay
   rules, and out-of-order handling are unresolved implementation blockers.
3. The authenticated CCIP refill requires an origin rebalancer, exact callback
   schema, a pinned ERC-165 receiver implementation, source binding,
   out-of-order execution support, failure/retry runbook, and independent
   token-pool/callback gas measurements; today's empty-data, gas-`0` transfer is
   not that mechanism.
4. Capture a live `v1` quote and freeze the exact Relay order/refund/fee policy,
   hash test vectors, chain-id normalization, and maximum array lengths before
   implementing the decoder. `includeProtocolData` is not a Relay attestation.
5. Relay's production attestor behaviour is not provable from source; the
   absence of a solver allowlist in the repository does not establish its
   absence in the running service.
6. The residual pre-fill stranding risk under `lanePaused` / `mintEnabled` is an
   owner acceptance, not an engineering item.
7. H-2's remote settlement-address and lane-health proof remains unresolved; an
   API check alone cannot satisfy the payout contract's fail-closed gate.
