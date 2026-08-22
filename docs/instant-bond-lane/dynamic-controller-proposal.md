# Instant Bond Lane Dynamic Controller and Manual Rate Override Design Record

**Status:** Current Instant Bond controller and override design record (specification
revision 24) under the dated
[owner decision](https://github.com/Ripe-Foundation/ripe-protocol/pull/156#issuecomment-5304274427).
Economic calibration is explicitly **not approved**. This document is not merge,
deployment, configuration, minting, or activation authority.

> **New to the feature?** Start with [`README.md`](README.md). This design record is
> the detailed controller and manual-override derivation, not the onboarding entry
> point.

**Starting baselines:** revision 20 began at
`ad782c80b2f4bfa73d7dcd8c9c4979903b767b96`; revision 21 begins from the
committed and pushed `instant-bond-lane` checkpoint
`79917dd8ca1abc5fc915777fd80e95d4005b4747`. Revision 22 integrates current
`origin/rh` commit `36ee0db42482c3e7d6c43d045fc02655b90bebf4`. Revision 23
begins from reviewed PR head `55a2ef9ec25412d2f7bf7a9e8547a6ccc414e0ae`.

The revision-24 [`implementation-spec.md`](implementation-spec.md) is authoritative.
This document records the controller rationale and the implemented design at
`contracts/core/InstantBondLane.vy` and
`contracts/config/SwitchboardFoxtrot.vy`; it does not replace the normative source or
the final evidence block in the implementation specification.

## 1. Conclusions

The implemented controller preserves the utilization-based direction decision while
making the adjustment magnitude responsive to demand strength:

- high utilization moves price up by a governed value in `minUpBps..maxUpBps`;
- low-utilization positive-payment epochs move price down by a governed value in
  `minDownBps..maxDownBps`;
- the dead band applies no utilization-driven step, while a newly lowered ceiling may
  still clamp the base rate;
- fully empty or skipped epochs retain the existing fixed `decayBps` step;
- every committed epoch still has one fixed base payout rate; and
- all effective adjustments remain bounded before exact inverse-rate arithmetic.

"Fixed base payout rate" does not mean every buyer receives the same effective
locked quote. MissionControl lock terms remain live, and buyer-selected lock duration
can change the bonus within the snapshotted epoch maximum. Before the first successful
purchase commits a lazily projected epoch, a newly executed config can also change
that uncommitted projection.

Purchase timing must be amount-weighted. Using only the final sellout block lets a
buyer acquire almost the entire cap immediately and delay a marginal tail purchase to
force the minimum upward adjustment.

Timing is strategically selectable: a buyer can wait until the last block without
paying a different active-epoch rate and select the weakest valid upward response.
Production activation therefore remains blocked until signed calibration proves the
approved `minUpBps..maxUpBps` spread—including repeated last-block full-cap paths—is
safe. The mechanism does not claim that timing is costly or manipulation-proof.

Governance can install one timelocked, one-shot exact rate for the next successful
rollover. There is no direct or untimelocked admin setter, and an override never
rewrites the active stored epoch. There is no target calendar epoch, execution window
tied to an epoch boundary, or maximum lead in epochs.

## 2. Implemented authority model

The Lane exposes `setConfig`, `setCanBuyNow`, `setRateOverride`, `cancelRateOverride`,
`start`, `stop`, `setPaymentToken`, and `setCumulativeMinted` to any address that
satisfies the protocol's existing registered-switchboard check. Those mutators are
`@nonreentrant` defense-in-depth. `SwitchboardFoxtrot` is the intended route and
resolves the lane through RipeHq id 26. It does not store a lane address. The Lane
does not pin authority to Foxtrot. Registry-wide trust is the resolved protocol
boundary, not a future design decision.

The exact manual-rate workflow is deliberately separate from ordinary configuration:

- `seedRate` supplies the first initialized epoch only;
- `setConfig` replaces persistent controller inputs but never writes the active
  epoch rate directly, and cannot change an already-installed `epochLength`;
- `setRateOverride` last-write-wins one exact target for the first later successful
  rollover;
- `cancelRateOverride` removes an installed target through the same registered-
  switchboard boundary;
- `canBuyNow`, Department pause, mint authorization, and `mintBudget` can stop sales
  but do not assign price; and
- Foxtrot independently timelocks config replacement, override installation, and
  installed-override cancellation as three tagged action types. Start, stop,
  payment-token, minted, and `canBuyNow` are immediate.

## 3. Terminology and units

The contract stores a base payout rate:

```text
R = RIPE-wei per whole payment token
```

`R` is the inverse of price. A lower rate is a higher RIPE price. Governance and UI
tooling may display a human price, but every on-chain controller and override input
must use the exact integer `rate` to avoid ambiguous decimal conversion.

Let:

```text
B = 10_000
C = snapshotted epoch payment cap
A = total accepted payment in the epoch
U = floor(A * B / C)
L = installed epoch length in blocks
```

## 4. Amount-weighted timing signal

For a purchase `i` at zero-based block offset `o_i` within an epoch:

```text
if L == 1:
    lateness_i = 0
else:
    lateness_i = floor(o_i * B / (L - 1))

weightedLateness += paymentAmount_i * lateness_i
```

At rollover after a positive epoch:

```text
averageLateness = floor(weightedLateness / A)
earliness = B - averageLateness
```

This maps all first-block demand to `earliness=B`, all last-block demand to zero, and
mixed demand according to the amount arriving at each time. Splitting or merging
purchases in the same block does not alter the signal.

For `L=1`, the epoch's only block is both its first and last. The implementation
assigns full earliness (`B`) because all observed demand necessarily arrives in the
sole available block. For `L>1`, the first and last offsets map exactly to `B` and
zero.

The config bound `paymentCapPerEpoch <= max_value(uint256) / B` makes
`weightedLateness <= C * B` safe. `isValidEpochLength` additionally enforces
`epochLength <= max_value(uint256) / B + 1`, which makes `o_i * B` safe. The
deterministic Python model uses unbounded integers and therefore remains supporting
mechanism evidence rather than proof of these Vyper bounds.

The first initialized epoch is only partially exposed when initialization occurs after
its deterministic start. The implemented rule sets `epochTimingEligible` only when
initialization occurs at deterministic offset zero. Timing is still recorded, but an
ineligible first epoch forces its upward timing multiplier to zero and therefore uses
`minUpBps`. `epochLength == 1` is offset-zero and eligible. Every later stored epoch
is timing-eligible.

## 5. Dynamic upward adjustment

Final utilization still chooses the branch. For `U >= uHighBps`, normalize both the
amount above the threshold and the timing signal:

```text
utilizationStrength = floor(
    (U - uHighBps) * B / (B - uHighBps)
)

demandStrength = floor(utilizationStrength * earliness / B)

effectiveUpBps = minUpBps + floor(
    (maxUpBps - minUpBps) * demandStrength / B
)
```

Consequences:

- exact `uHighBps` receives `minUpBps` regardless of timing;
- a full first-block epoch receives `maxUpBps`;
- a full last-block epoch receives `minUpBps`;
- a full epoch sold uniformly receives an intermediate adjustment;
- high but partially filled epochs receive a bounded intermediate adjustment; and
- a late tail purchase affects timing only in proportion to its amount.

As the historical revision-19 controller did, first apply the latest base-rate ceiling
before selecting any branch:

```text
boundedOldRate = min(oldRate, newBaseRateCeiling)
```

Apply the effective price increase using the current exact inverse-rate formula:

```text
newRate = max(
    floor(boundedOldRate * B / (B + effectiveUpBps)),
    MIN_BASE_RATE,
)
```

Do not interpolate `rate` directly and do not replace the formula with
`oldRate * (B - effectiveUpBps) / B`.

## 6. Dynamic downward adjustment

Purchase timing is not the primary weakness signal when an epoch fails to reach the
target. For a positive-payment epoch with `U <= uLowBps`, including a utilization that
rounds down to `U=0`, use utilization shortfall:

```text
weakness = floor((uLowBps - U) * B / uLowBps)

effectiveDownBps = minDownBps + floor(
    (maxDownBps - minDownBps) * weakness / B
)

newRate = min(
    floor(boundedOldRate * B / (B - effectiveDownBps)),
    newBaseRateCeiling,
)
```

Thus utilization exactly at `uLowBps` receives `minDownBps`, and a positive-payment
epoch whose floored utilization is zero receives `maxDownBps`.

The dead band `uLowBps < U < uHighBps` applies no controller step, but a newly
lowered ceiling still clamps the old rate to `boundedOldRate`.

## 7. Empty and skipped epochs

Keep `decayBps` fixed. Empty epochs have no purchase-timing observation, and skipped
epochs already express duration by applying one decay step per epoch up to
`maxDecayEpochs`. Giving decay another time-dependent range would count the same
duration twice.

The existing lazy rules remain:

- after one positive stored epoch, apply its utilization transition once and then
  `min(elapsed - 1, maxDecayEpochs)` fixed decay steps;
- keep the defensive zero-accepted stored branch;
- ignore elapsed epochs before first initialization; and
- treat pause, disablement, budget exhaustion, and operational outages like other
  unavailable empty time.

Availability does not pause or rebaseline the lateness clock. Demand released after a
mid-epoch unpause is therefore measured at its wall-clock offset and can select a
weaker upward step than equal demand available from the epoch start. Calibration must
include that deliberately accepted distortion.

## 8. Implemented configuration

Revision 20 replaced the historical fixed fields:

```text
upBps
downBps
```

with:

```text
minUpBps
maxUpBps
minDownBps
maxDownBps
```

Retain `uLowBps`, `uHighBps`, `decayBps`, and `maxDecayEpochs`.

The complete mirrored config order is:

```text
canBuyNow
paymentCapPerEpoch
minPaymentAmount
mintBudget
maxEffectiveRate
seedRate
uHighBps
uLowBps
minUpBps
maxUpBps
minDownBps
maxDownBps
decayBps
maxDecayEpochs
maxLockBonus
minLockDuration
epochLength
```

Controller-specific hard validation (the implementation specification contains the
remaining payment, rate, bonus, budget, and arithmetic bounds):

```text
0 < uLowBps < uHighBps < B
0 < minUpBps <= maxUpBps <= MAX_PRICE_STEP_BPS
0 < minDownBps <= maxDownBps <= decayBps < B
maxDownBps < minUpBps
(B + minUpBps) * (B - maxDownBps) >= B * B
(B + minUpBps) * (B - decayBps) >= B * B
0 < maxDecayEpochs <= 32
```

The two factor inequalities ensure that, away from rate bounds and integer saturation,
neither the strongest configured positive low-utilization price-down factor nor one
empty-decay factor can erase the weakest configured high-utilization price-up factor.
This is not an unconditional state-level monotonicity guarantee: if the price-up
transition saturates at `MIN_BASE_RATE`, a later price-down or decay step can and should
move the rate up from that floor. The model tests the interior factors and documents
the bound exception.

Collapsing each range (`min==max`) reproduces the revision-19 positive-epoch
transition for configs that satisfy the stricter v2 validation, including exact rate
arithmetic, ceiling pre-clamp, floor, and bounded skipped decay. It does not preserve
config acceptance: revision 19 permits `uLowBps=0`, `uHighBps=B`, and some asymmetric
step pairs that the nondegenerate dynamic formulas or round-trip inequality reject.

The 17-field config is mirrored byte-for-byte in `InstantBondLane` and
`SwitchboardFoxtrot`, with a source-identity guard test. Lane and Foxtrot config events
emit every field in that same order. `epochLength` is on the struct so start can
install cadence, but `setConfig` rejects a different length once one is installed.

## 9. Implemented epoch state and observability

The dynamic controller adds and publicly exposes:

```text
epochWeightedLateness
epochTimingEligible       # false only for a late first initialized epoch
```

The timing accumulator resets on rollover, and the current purchase contribution is
added only after projected epoch state has been selected. Failed purchases and reverted
settlement do not persist timing.

`EpochRolled` reports the implemented reconstructable inputs and results:

```text
previousWeightedLateness
previousTimingEligible
effectiveAdjustmentBps
controllerRate
```

The event also carries both epoch endpoints, old/new rate, the complete new pricing
snapshot, prior accepted payment/cap, utilization, and decay steps. Average lateness,
strength intermediates, and adjustment direction are deterministically reconstructable
and are not separate event fields. There is no pricing-config version field.

## 10. Timelocked one-shot manual rate override

### 10.1 Authority

There is no direct Lane admin. The intended workflow queues, confirms, executes,
expires, and cancels override actions through `SwitchboardFoxtrot` and the existing
`LocalGov`/`TimeLock` model.

The Lane's mutators use the existing registered-switchboard authorization check.
Registry-wide switchboard trust is accepted; Foxtrot is the intended route, not a
Lane-side immutable authorization pin.

### 10.2 Installed state

The Lane stores one public scalar:

```text
rateOverride       # exact target; zero means none installed
```

`rateOverride == 0` represents no installed override because every valid rate is
strictly positive. There is no `overrideVersion` and no stored bound-config-version
field. Foxtrot queues the target only. Every full config write, plus `start` and
`stop`, synchronously invalidates an installed target.

Last write wins. A later `setRateOverride` replaces the pending target without a
cancel-first step. Preview, same-epoch purchases, failed execution, expired queue
cleanup, and reverted settlement leave it unchanged.

The ordinary Foxtrot TimeLock confirmation and expiration rules bound a queued action.
A zero time lock is allowed and makes confirmation immediate. There is no target epoch,
target-boundary execution window, minimum pre-target window, or maximum lead in epochs.
Once successfully installed in the Lane, the override persists until application,
timelocked cancellation, or invalidation by `setConfig` / `start` / `stop`.

Before initialization (`epochState.rate == 0` or the lane is not running), governance
changes `seedRate` instead. Installation requires:

```text
isRunning
epochState.rate != 0
MIN_BASE_RATE <= targetRate <= currentBaseRateCeiling
```

The contract rejects an invalid rate and never silently clamps a requested manual
target.

### 10.3 Owner-selected next-successful-rollover semantics

Let `S` be the Lane's stored `epochState.epoch` and `E` the deterministic epoch
projected for a purchase or preview:

```text
E == S: retain the override; use the already committed stored epoch rate
E > S:  use targetRate exactly for the newly projected epoch
```

The `E > S` result is identical whether one or many deterministic epochs elapsed.
The target replaces the ordinary utilization transition and every skipped-epoch decay
effect for that rollover. The implementation still calculates the ordinary result as
`controllerRate` and emits it as counterfactual telemetry, but does not clamp or decay
the valid installed target. The next ordinary rollover starts from the committed
target rate.

Preview projects the override without consuming it. A successful purchase in the
already stored epoch leaves it pending. The first successful purchase that commits any later epoch clears it atomically. A
settlement failure after projection reverts consumption together with the epoch,
timing, cap, and mint accounting writes.

Installation is valid even when the stored epoch is already stale relative to the
wall-clock lane epoch. In that case the next successful purchase can apply the target
immediately to the current uncommitted deterministic epoch. This matches the existing
lazy rule under which governance can change an uncommitted projection while never
rewriting an already committed epoch.

### 10.4 Config changes and cancellation

Executing any full config, `start`, or `stop` while an override is installed clears
and invalidates the override and emits `RateOverrideInvalidated`. `setCanBuyNow` does
not. A stale override cannot survive a successful config write and make ordinary
purchases revert.

Cancellation of a queued Foxtrot action follows Echo: `timeLock._cancelAction` plus
clear `actionType`. It does not wipe leftover pending payloads and has no per-action
cancel event. Cancellation of an override already installed in the Lane changes a
committed future economic rule and is itself timelocked.

### 10.5 Events and views

The implemented Foxtrot events are:

- `PendingRateOverrideSet(actionId, confirmationBlock, targetRate)`;
- `PendingRateOverrideCancellationSet(actionId, confirmationBlock)`;
- `RateOverrideExecuted(actionId)`; and
- `RateOverrideCancellationExecuted(actionId)`.

The implemented Lane events are:

- `RateOverrideInstalled(targetRate)`;
- `RateOverrideApplied(fromEpoch indexed, toEpoch indexed, targetRate,
  controllerRate)`;
- `RateOverrideCancelled(targetRate)`; and
- `RateOverrideInvalidated(targetRate)`.

The public override views are the scalar `rateOverride()` getter plus
`isValidRateOverride(targetRate)` and `canCancelRateOverride()`. There is no
separate detailed override tuple. `previewBuyNow.rate` is authoritative for the
projected purchase rate and does not consume an installed target.

### 10.6 Emergency operator flow

If pricing is wildly wrong:

1. pause the Lane through the established emergency path;
2. queue any required full config change;
3. wait and execute it;
4. queue the exact one-shot next-rollover rate;
5. wait and install it;
6. verify preview, override state, ceiling, cap, and budget;
7. unpause only when the target rate and operational checks are aligned.

The global mint switch remains the broader protocol circuit breaker. Manual pricing
does not bypass the all-in rate ceiling, epoch cap, mint budget, pause, or mint
authorization.

If the Lane remains paused across one or many deterministic epochs after installation,
the target remains exact and pending. The first successful rollover after unpause uses
it without calendar decay. This paused-recovery behavior is a deliberate consequence
of the owner-selected semantics.

## 11. Simulation and acceptance gates

The deterministic model is
`scripts/simulations/instant_bond_lane_controller.py`; its canonical output is
`controller-simulation-v2.json` in this directory.

Canonical artifact SHA-256:
`b021bb113202bd0407023db910651a8364ed336f689ce41942919b9bde16cbb7`.

The checked-in pure Python companion model demonstrates:

- exact first/last timing endpoints;
- monotone upward adjustment in both utilization strength and amount-weighted
  earliness;
- monotone downward adjustment in utilization weakness;
- same-block split/merge and purchase-order invariance;
- conditional collapsed-range positive-transition parity with revision 19, including
  final integer rates for configs admitted by v2;
- fixed, capped, dynamic-range-independent decay;
- exact next-successful-rollover projection after one or many elapsed epochs, plus a
  pure versioned install, same-epoch retention, repeat preview, failed commit,
  successful one-shot consumption, last-write-wins replacement, cancellation, and
  config-invalidation lifecycle;
- floor, ceiling pre-clamp, and maximum-decay preservation; and
- byte-identical canonical JSON across repeated runs.

This model is not a Lane, Foxtrot, Boa, EVM, authorization, storage, event, or
settlement simulator. Revision-23 contract and test sources implement the related
paths, including stale Foxtrot actions, TimeLock boundaries, failed-settlement rollback,
the partially exposed first initialization, pause/disable/budget intervals, config
execution, ABI/event reconstruction, and stateful reference-model parity. Their final
run results are recorded in §20.7 of `implementation-spec.md`; that normative evidence,
not this design record, governs validation claims.

The illustrative fixture intentionally exposes calibration risk:

- full first/mid/last-block demand selects `800/500/200` bps;
- +30% price catch-up takes `4/6/14` such epochs;
- 2x takes `10/15/36`, and 10x takes `30/48/117`;
- one fast-full 8% price-up epoch followed by one 1.5% empty decay epoch nets a
  `1.0638x` price multiplier per pair;
- sixteen such alternating pairs reach a `2.6900x` price index;
- one late-full 2% price-up epoch followed by one 1.5% empty decay epoch still nets
  `1.0047x` per pair, with sixteen alternating pairs reaching `1.0779x`; and
- 32 consecutive fast-full epochs reach `11.7370x`.

Those figures are mechanism evidence and a warning, not a parameter recommendation.

Simulation values are illustrative. The artifact must remain marked
`calibration_status: not_approved` until the owner pins acceptable catch-up time,
half-life, oscillation, leakage, capacity, and override-deviation limits.

## 12. Implemented revision-20 impact

Revision 20 changes economics and is not behavior-preserving relative to revision 19.
The working candidate includes:

- expanded mirrored config tuples and config events;
- changed function selectors and generated ABIs;
- new Lane timing and override storage fields;
- new Foxtrot pending-action storage and action/event paths;
- revised rollover, preview, and state-commit logic;
- new override installation/cancel/invalidation logic;
- updated controller, property, lifecycle, Foxtrot, ABI, and stateful models;
- a reconciled normative specification revision; and
- regenerated canonical ABI artifacts.

Historical revision 19 measured 8,669 bytes for Lane against its 9,000-byte project
regression ceiling and 5,068 bytes for Foxtrot against 5,500 bytes. Revision 20
measured 10,564 bytes for Lane and 6,051 bytes for Foxtrot. Revision-22 Boa
deployments measured 10,758 and 6,051 bytes. On 15 August 2026, the owner raised only
the Lane project ceiling to 13,000 bytes; Foxtrot remained 6,500 and EIP-170 remained
24,576. Those local ceilings were later dropped. The only current size limit is
EIP-170. Revision-23 measurements in §20.7 of `implementation-spec.md` are
historical. Recompile and remeasure after every production-source change. The
rebaseline is a source-size policy decision, not deployment or economic-calibration
approval.

## 13. Execution status and authority boundary

Completed in the working candidate:

1. owner selection of the dynamic controller and next-successful-rollover semantics;
2. authoritative specification reconciliation through revision 24;
3. atomic Lane and Foxtrot implementation;
4. controller, lifecycle, governance, ABI, simulation, and stateful test/model updates;
5. deterministic ABI regeneration;
6. current-RH integration and a permanent feature gate for branch, PR, merge-queue,
   and manual validation; and
7. the later EIP-170-only size policy plus a fail-closed activation manifest.

Revision 20's bounded branch commit and push completed at `79917dd`, and revision 21's
reviewer-remediation checkpoint was committed and pushed as `d13203d`. The owner
authorized revision 23 remediation, commit, push, and substantive replies on the
existing draft PR. Exact final Git and PR identities belong in the external handoff
because a commit cannot include itself.

Economic calibration remains `not_approved` and is required before any deployment or
configuration proposal, not before completing source validation or review. Deployment,
configuration, RIPE minting, and activation remain outside the current authorization.
