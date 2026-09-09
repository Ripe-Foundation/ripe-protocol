# Historical proposal — superseded

This document records an earlier pricing proposal. The implemented controller is
documented in [README.md](README.md) and bound to source by
`controller-simulation-v2.json`.

# Instant Bond Lane — On-Chain Pricing via a Demand Controller

**Historical status at revision 24:** Economic rationale for the then-current
Instant Bond Lane candidate. The dated
[owner decision](https://github.com/Ripe-Foundation/ripe-protocol/pull/156#issuecomment-5304274427)
selected its operational policies at that checkpoint. Later owner decisions
superseded parts of that record. Economic calibration remains explicitly **not
approved**.

> **New to the feature?** Start with [`README.md`](README.md) for the architecture,
> transaction flow, governance model, safety boundaries, and reading path.
>
> **Historical authority:** [`implementation-spec.md`](implementation-spec.md) was
> the normative source for this proposal. The companion
> [`dynamic-controller-proposal.md`](dynamic-controller-proposal.md) records the
> controller and override derivation in more detail. The owner separately authorized
> revision-23 remediation commit/push and continued draft review; this rationale does
> not authorize merge, deployment, configuration, RIPE minting, or activation.

**Prepared:** 5 August 2026 · **Revised:** 22 August 2026 for the then-implemented
start/stop clock, last-write-wins override, HQ-resolved Foxtrot, 17-field config,
and EIP-170-only size policy.

**Purpose:** Explain how the Instant Bond Lane sets its Buy Now rate, why the mechanism
uses these signals, and which economic risks remain for calibration and operations.

**What this mechanism is, stated plainly:** a **cap-clearing controller**, not a
fair-value oracle. It finds a rate at which a bounded sale capacity clears near a
target level of demand. It does not read external venues or claim to know RIPE's fair
value. Arbitrage can tether its price to external value, but the tether is indirect,
lagged, and safest when capacity and the lifetime mint budget are conservative.

---

## 1. Implemented mechanism in one page

Each deterministic Lane epoch has one fixed base payout rate. At the first successful
purchase in a later epoch, the Lane lazily computes a new rate from the prior stored
epoch's payment utilization, amount-weighted purchase timing, and any skipped epochs:

- high utilization raises RIPE's implied price by a governed step in
  `minUpBps..maxUpBps`;
- low-utilization positive-payment epochs lower price by a governed step in
  `minDownBps..maxDownBps`;
- the dead band applies no utilization step;
- empty and skipped epochs apply fixed `decayBps`, capped by `maxDecayEpochs`;
- every result is bounded by `MIN_BASE_RATE` and the live config's all-in effective-rate
  ceiling; and
- one timelocked exact-rate override may replace the final result at the first later
  **successful** rollover.

The override has no target epoch, execution window, expiry, or maximum lead. Preview
does not consume it, same-epoch purchases retain it, failed settlement rolls back its
provisional application, and any successful full config write invalidates it. The
following rollover resumes ordinary control from the committed target.

The fixed base rate does not make every locked quote identical. The epoch snapshots
`maxLockBonus`, while live MissionControl lock terms and the buyer's requested duration
determine the bonus within that ceiling. Production activation fixes the ceiling at
zero until isolated lock lots exist. The buyer is always `msg.sender`.

---

## 2. Controller arithmetic

The Lane stores an inverse rate:

```text
R = RIPE-wei per whole dollar-denominated payment token
B = 10_000
C = snapshotted epoch payment cap
A = accepted payment in the stored epoch
U = floor(A * B / C)
```

A lower `R` means a higher RIPE price. The contract therefore uses exact inverse-price
arithmetic rather than approximating a price increase as a same-percentage rate
decrease.

### 2.1 Amount-weighted timing

For a purchase at zero-based deterministic epoch offset `o` and installed epoch length
`L`:

```text
lateness = 0                              if L == 1
lateness = floor(o * B / (L - 1))         otherwise

epochWeightedLateness += paymentAmount * lateness
averageLateness = floor(epochWeightedLateness / A)
earliness = B - averageLateness
```

Weighting by payment makes same-block splitting, merging, and reordering invariant. A
tiny early probe cannot make a large late purchase appear early, and delaying only a
marginal tail cannot control the signal as a final-sellout timestamp would.

A first initialized epoch is timing-eligible only when initialization occurs at its
deterministic offset zero. A later cold start still records timing for observability but
uses zero earliness at its first rollover, producing `minUpBps` if utilization is high.
`epochLength == 1` is offset-zero and eligible. Every later stored epoch is eligible.

### 2.2 High-utilization adjustment

For `U >= uHighBps`:

```text
utilizationStrength = floor(
    (U - uHighBps) * B / (B - uHighBps)
)
demandStrength = floor(utilizationStrength * earliness / B)

effectiveAdjustmentBps = minUpBps + floor(
    (maxUpBps - minUpBps) * demandStrength / B
)

boundedOldRate = min(oldRate, newBaseRateCeiling)
newRate = max(
    floor(boundedOldRate * B / (B + effectiveAdjustmentBps)),
    MIN_BASE_RATE,
)
```

Exactly `uHighBps` receives `minUpBps`. A full first-block eligible epoch receives
`maxUpBps`; a full last-block epoch receives `minUpBps`. Intermediate utilization and
timing interpolate monotonically within the governed range.

### 2.3 Low-utilization adjustment

For a positive-payment epoch with `U <= uLowBps`:

```text
weakness = floor((uLowBps - U) * B / uLowBps)

effectiveAdjustmentBps = minDownBps + floor(
    (maxDownBps - minDownBps) * weakness / B
)

newRate = min(
    floor(boundedOldRate * B / (B - effectiveAdjustmentBps)),
    newBaseRateCeiling,
)
```

Exactly `uLowBps` receives `minDownBps`. A positive payment whose floored utilization
is zero receives `maxDownBps`. Timing is not used for this branch because utilization
shortfall is the direct weakness signal.

### 2.4 Dead band, empty epochs, and skipped time

For `uLowBps < U < uHighBps`, the utilization controller applies no step, although a
newly lowered effective-rate ceiling may still clamp the old rate.

Fully empty time uses fixed decay:

```text
rate = min(
    floor(rate * B / (B - decayBps)),
    newBaseRateCeiling,
)
```

After a positive stored epoch, its utilization transition runs once and
`min(elapsed - 1, maxDecayEpochs)` skipped-epoch steps follow. The source retains a
defensive zero-accepted stored-epoch branch that applies `min(elapsed,
maxDecayEpochs)` steps, although current atomic purchase sequencing cannot commit such
a stored epoch. Epochs before first initialization are ignored.

Configuration validation requires both a weakest-up/strongest-positive-down factor
and a weakest-up/empty-decay factor to be non-ratcheting away from explicit rate bounds:

```text
(B + minUpBps) * (B - maxDownBps) >= B * B
(B + minUpBps) * (B - decayBps) >= B * B
```

Thus an alternating high-demand/empty pattern cannot make RIPE progressively cheaper
merely because empty decay was configured slightly stronger than the weakest upward
response. `MIN_BASE_RATE` saturation remains an intentional exception.

Pause, `canBuyNow=false`, exhausted budget, frontend failure, and other unavailable
time are not separately clocked. They decay like other empty time. This gives patient
buyers a waiting option, bounded by the rate ceiling, decay cap, per-epoch capacity,
and lifetime mint budget. Demand released after a mid-epoch unpause is measured at its
wall-clock lateness, so it may select a weaker upward step than equal volume available
from the epoch start.

---

## 3. Exact manual override

The Lane stores one public scalar:

```text
rateOverride       # exact target; zero means none installed
```

There is no `overrideVersion` and no stored config-version binding. Last write wins:
a later `setRateOverride` replaces the pending target without a cancel-first step.
Every subsequent full config write, plus `start` and `stop`, synchronously
invalidates an installed target. Preview, same-epoch purchases, failed execution,
expired queued-action cleanup, and reverted settlement leave it unchanged.

Installation is valid only while the lane is running **and** `epochState.rate != 0`.
The target must sit between `MIN_BASE_RATE` and the live derived base-rate ceiling.
Invalid targets revert rather than being clamped.

For stored epoch `S` and projected deterministic epoch `E`:

```text
E == S: retain the target and use the committed stored rate
E > S:  calculate the ordinary controllerRate, then store target exactly
```

The result is identical whether one or many calendar epochs elapsed. The target is not
clamped or decayed after installation; config invalidation prevents it from surviving
a ceiling change. `RateOverrideApplied` emits the exact target and the ordinary
counterfactual `controllerRate` for auditability.

Authority uses the protocol's existing registered-switchboard trust boundary.
`SwitchboardFoxtrot` is the intended timelocked route and looks up the lane through
RipeHq id 26. The Lane is not immutably pinned to Foxtrot. Foxtrot separately queues
full config replacement, exact override installation, and installed-override
cancellation.

---

## 4. Safety boundaries

The controller is not the primary supply boundary. Revision 20 relies on layered
controls:

1. governed cumulative `mintBudget`, which may never be set below
   `cumulativeMinted`;
2. snapshotted `paymentCapPerEpoch` and `minPaymentAmount`;
3. `maxEffectiveRate`, which limits total RIPE after the maximum lock bonus;
4. `MIN_BASE_RATE` and bounded controller adjustments;
5. Lane `canBuyNow` and Department pause;
6. Lane-specific and global RipeHq mint authorization; and
7. the exact-payment settlement requirement.

The base-rate ceiling is derived from the all-in effective ceiling:

```text
baseRateCeiling =
    maxEffectiveRate * B
    // (B + maxLockBonus)
```

Every successful purchase therefore satisfies the treasury-protective cross-product
bound specified in `implementation-spec.md`. A governed payment cap alone would not
bound dilution at a low price; the all-in ceiling and lifetime mint budget provide the
second and third boundaries.

Neither the budget nor the rate ceiling is immutable. Changes are full, last-write-wins,
timelocked config replacements through Foxtrot's intended route. A budget increase is
an explicit governance action and economic decision, never an automatic post-sellout
replenishment. Live `canBuyNow` and `mintBudget` changes apply immediately; rate, cap,
minimum-payment, and maximum-bonus fields are snapshotted only at initialization or the
next successful rollover and never rewrite the running epoch. `setCanBuyNow` is also
an immediate Foxtrot setter and does not invalidate an installed override.

`cumulativeMinted` is local to one Lane deployment. A replacement therefore needs an
external program ledger of retired Lane issuance and must configure its new
`mintBudget` to no more than the previously approved program remainder. Reusing the
retired deployment's nominal budget would double-count issuance authority.

---

## 5. What the controller does and does not provide

**It provides an admin-light, oracle-free rate.** Direction follows realized Lane
utilization, while bounded severity responds to utilization and, on the high branch,
amount-weighted timing.

**It does not provide fair value.** The equilibrium depends on capacity, epoch length,
buyer concentration, live lock terms, demand elasticity, and external arbitrage.

**It remains lagged.** A sellout proves demand was at least the cap, not whether it was
slightly or massively above it. Timing extracts more information than a binary
sellout, but it does not reveal the full demand curve.

**Lag transfers value to fast buyers.** A constant-step approximation gives the useful
historical intuition:

```text
leak ≈ capacity * gap² / (2 * priceUpStep)
```

This is a heuristic, not revision-20 calibration. The dynamic controller reduces some
lag by assigning stronger increases to earlier, higher utilization, but all concrete
catch-up, oscillation, and leakage limits remain unapproved until the owner selects
production parameters.

**Waiting can lower price.** Empty-epoch decay deliberately gives patient buyers a
free waiting option. The honest protection is bounded exposure, not a claim that
waiting is costly.

### 5.1 Mechanism precedent

The Lane is not a copy of another auction. Its design draws on a family of mechanisms
that support the underlying primitives:

- Bond Protocol's Sequential Dutch Auctioneer demonstrates oracle-free pricing from
  realized sales against a target, with asymmetric movement;
- Paradigm's GDA/VRGDA work demonstrates schedule-versus-sales feedback, although its
  signal differs from prior-epoch utilization;
- Frax FXB demonstrates a gradual Dutch auction bounded by a governed floor; and
- Olympus's Emissions Manager is a conceptual reference for admin-light issuance with
  an explicit governance path, not a template for a solvency oracle.

The shared lesson is limited but useful: bounded capacity, explicit rate bounds, and
conservative issuance controls protect the treasury more directly than pricing
sophistication does.

---

## 6. Supporting design choices

### 6.1 Independent deterministic Lane epoch

The Lane does not follow Bond Room or Ledger epochs:

```text
laneEpoch = (block.number - genesisBlock) // bondConfig.epochLength
```

`start` installs genesis and cadence. `setConfig` cannot change an already-installed
`epochLength`; a new cadence requires `stop()` then `start(..., newLength)`.
This removes cross-contract epoch handshakes and preserves deterministic history
while the clock is running. Rollover is lazy inside `buyNow`; `previewBuyNow` and
`getEpochSnapshot()` project the same state read-only. There is no external
initialization or rollover transaction.

### 6.2 Flexible lock bonus

The buyer may take RIPE unlocked or request a lock. Effective min lock is
`max(vault.minLockDuration, config.minLockDuration)`. Vault `maxLockDuration` is the
only ceiling. Unlocked settlement happens when the buyer asked for `0` **and** the
lane min is `0`, or when there is no live vault range. The vault minimum does not
force a lock on a zero request when the lane min is `0`. The epoch's `maxLockBonus`
bounds a linear bonus on a locked purchase. The all-in rate ceiling includes that
maximum bonus. Preview discloses the current core RipeGov vault ID; the purchase
event does not.

RipeGov combines deposits into an account-level weighted unlock. The requested deposit
duration is not necessarily the final position unlock; this inherited behavior and its
accepted economic exposure are detailed in the implementation specification. For an
expired prior position, normalized prior shares `P`, normalized new shares `N`, and
requested lock `L` produce `floor((P + N * L) / (P + N))`; the result stays at one
block while `N * (L - 2) < P`. Calibration must therefore model chunked purchases
through the whole epoch cap, not only one deposit.

### 6.3 Buyer is the recipient

`buyNow` has no recipient argument. `msg.sender` receives unlocked RIPE or the RipeGov
deposit. Delegated purchases and gifting remain out of scope.

### 6.4 Configured payment-token settlement

The payment token is dollar-denominated and may use any supported decimal count.
It is stored, not immutable, and may be swapped only while the lane is stopped.
`paymentScale` is derived from `decimals()` at each store; the contract does not
assume USDC or six decimals.

Payment transfers directly from the buyer to Endaoment Funds. The Lane compares the
destination balance before and after transfer and requires an exact increase, rejecting
false-return, zero, short, fee-on-transfer, and excess-receipt behavior atomically.

### 6.5 Isolation limits code risk, not economic risk

Production-contract changes are limited to `InstantBondLane` and its dedicated
`SwitchboardFoxtrot`; the exact document, model, ABI, and test scope is listed in
§20.1 of `implementation-spec.md`. The feature does not modify BondRoom, Ledger,
RipeToken, or RipeGov.
Isolation reduces regression risk but does not isolate RIPE supply. The Lane remains a
registered minter subject to protocol-wide mint controls, and monitoring must account
for its budget alongside the Ledger's reward, HR, and bond allowances.

### 6.6 Bad debt and shutdown

Purchases remain available during bad debt and do not participate in debt repayment
accounting. Locked-position early exit can still be frozen by live RipeGov terms, which
preview discloses.

There is no hard sunset or reactivation reset. Governance disables the Lane with
`canBuyNow`, Department pause, or deregistration. The global mint switch is the broader
protocol circuit breaker.

### 6.7 Deferred mechanisms

The implemented revision deliberately excludes:

- external fair-value or solvency oracles;
- DEX guards;
- within-epoch ramps or tranche schedules;
- automatic target-epoch override scheduling or expiry;
- delegated recipients;
- partial fills; and
- historical on-chain epoch mappings.

Each would add a new signal, authority path, or state machine and requires a separate
owner-approved design.

---

## 7. Implemented contract shape

The feature uses two nonupgradeable Vyper contracts:

1. `contracts/core/InstantBondLane.vy` — purchase, preview, controller, settlement,
   state, and registered-switchboard mutators.
2. `contracts/config/SwitchboardFoxtrot.vy` — LocalGov/TimeLock adapter for three
   tagged action types plus immediate start/stop, payment-token, minted, and
   `canBuyNow` setters. It resolves the lane through RipeHq id 26.

The 17-field config is:

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

Key Lane views and entry points are:

```text
isValidConfig(config)
setConfig(config)
setCanBuyNow(canBuyNow)
isValidRateOverride(targetRate)
setRateOverride(targetRate)
canCancelRateOverride()
cancelRateOverride()
start(genesisBlock, epochLength)
stop()
setPaymentToken(token)
setCumulativeMinted(amount)
buyNow(paymentAmount, requestedLock, expectedEpoch, minRipeOut, deadlineBlock)
previewBuyNow(paymentAmount, requestedLock)
getEpochSnapshot()
```

There are no public immutables for the clock or payment token. Public stored state is
`bondConfig`, `isRunning`, `epochState`, `paymentToken` / `paymentDecimals` /
`paymentScale`, `genesisBlock`, `rateOverride`, and `cumulativeMinted`. Cold start
versus rollover is `epochState.rate == 0`. There is no `isInitialized` or
`overrideVersion`.

Key Foxtrot workflows are:

```text
setInstantBondConfig(config)
setInstantBondRateOverride(targetRate)
cancelInstantBondRateOverride()
executePendingAction(aid)
cancelPendingAction(aid)
startInstantBond(genesisBlock, epochLength)
stopInstantBond()
setInstantBondPaymentToken(token)
setInstantBondCumulativeMinted(amount)
setCanBuyNow(canBuyNow)
```

Foxtrot does not store a lane address. It looks up `INSTANT_BOND_LANE_ID = 26` and
exposes the tagged action maps `actionType`, `pendingConfig`, and
`pendingRateOverride`. Execute and cancel clear `actionType` only.

`EpochRolled` exposes the prior accepted payment, cap, weighted lateness, timing
eligibility, utilization, applied adjustment, decay steps, ordinary `controllerRate`,
and complete new epoch snapshot. Override installation, application, installed
cancellation, and config invalidation have distinct Lane events with no version
fields. Foxtrot has no per-action cancel events.

The Lane event set is `EpochInitialized`, `EpochRolled`, `InstantBondPurchased`,
`InstantBondConfigSet`, `CanBuyNowSet`, `InstantBondStarted`, `InstantBondStopped`,
`PaymentTokenSet`, `CumulativeMintedSet`, `RateOverrideInstalled`,
`RateOverrideApplied`, `RateOverrideCancelled`, and `RateOverrideInvalidated`. The
Foxtrot event set is `PendingInstantBondConfigSet`, `InstantBondConfigExecuted`,
`PendingRateOverrideSet`, `PendingRateOverrideCancellationSet`,
`RateOverrideExecuted`, `RateOverrideCancellationExecuted`, `InstantBondStarted`,
`InstantBondCumulativeMintedSet`, `InstantBondPaymentTokenSet`, and
`InstantBondCanBuyNowSet`. Exact field order and indexing are normative only in
`implementation-spec.md` and the generated ABIs.

---

## 8. Economic calibration remains open

The deterministic model and canonical
[`controller-simulation-v2.json`](controller-simulation-v2.json) exercise integer
mechanism behavior. Their fixture remains marked `calibration_status: not_approved`.
It is not a recommendation for production step ranges, thresholds, caps, budgets,
epoch duration, rate ceiling, or seed rate. The current production lock-bonus policy is
zero; nonzero simulator cases are dormant arithmetic evidence only.

Before deployment or any configuration proposal, the owner must approve limits for:

- fast-demand catch-up time and maximum tolerated leakage;
- weak-demand decline and empty-epoch half-life;
- alternating-demand oscillation;
- per-epoch and rolling-day issuance;
- lifetime Lane budget across active and retired deployments;
- confirmation that lock bonus remains zero until isolated lock lots exist; and
- acceptable manual-target deviation from the ordinary controller.

Calibration must use the configured token's actual decimal scale and target-chain
block time. A short epoch can turn a modest-looking cap into a large rolling-day
issuance allowance.

---

## 9. Execution status and remaining gates

Completed in the working candidate:

- owner approval of revision-20 controller and next-successful-rollover semantics;
- Lane and Foxtrot implementation;
- normative specification reconciliation;
- controller, lifecycle, governance, ABI, simulation, and stateful test/model updates;
- deterministic ABI regeneration;
- current-RH integration and a permanent branch/PR/merge-queue/manual feature gate;
- a fail-closed activation manifest for calibration, issuance, payment/depeg,
  constructor, switchboard, fork, override, retry, and indexer inputs; and
- the later drop of those local ceilings in favor of EIP-170 only.

Revision 20's bounded branch commit and push completed at `79917dd`, and revision 21's
reviewer-remediation checkpoint was committed and pushed as `d13203d`. The owner
authorized revision 23 remediation, commit, branch push, and continued draft review.
Revision 24 is the current contract candidate. Economic calibration remains pending
before any deployment or configuration proposal.

Historical revision-18 through 23 measurements are preserved only in
`implementation-spec.md` and must not be presented as current evidence. Use the
generated ABIs, `test_properties_abi.py` EIP-170 check, and a fresh compile for
current runtime size.

The completed local checks satisfy the current integration and draft-review
prerequisites. Deployment, configuration, RIPE minting, and activation remain
separately unauthorized.

---

## 10. Summary

The current Lane is a bounded, oracle-free cap-clearing controller. It raises price
when payment utilization is high, uses amount-weighted timing to distinguish early from
late demand, lowers price on weak or empty demand, and keeps one base rate fixed within
each stored epoch. A last-write-wins, timelocked exact target gives governance a narrow
recovery tool without rewriting the active epoch or creating a calendar scheduler.

Its safety does not come from claiming fair-value discovery. It comes from the all-in
rate ceiling, per-epoch cap, cumulative mint budget, pause and mint controls, exact
payment settlement, and the requirement for conservative owner-approved calibration
before deployment. That calibration is still open; the mechanism implementation is
not.
