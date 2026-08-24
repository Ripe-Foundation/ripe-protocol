# RIPE Reserve Engine — implementation guide

Status: owner-approved architecture; Phase 1 contract-source and draft-PR handoff

Last revised: 24 August 2026

Source worktree: `/Users/wigglez/dev/ripe-protocol-instant-bond-lane`

Source branch: `instant-bond-lane`

Baseline commit: `7ae57fc72a8c45179a76ecd8328828effe2fea8e`

Baseline tree: `8af20f7667157279b9c6c7b7da9f6086601a7240`

This guide supersedes the earlier untracked **RIPE Direct Sale** proposal. It
incorporates the historical syntheses in
[`design-reviews/SYNTHESIS-claude.md`](design-reviews/SYNTHESIS-claude.md) and
[`design-reviews/SYNTHESIS.md`](design-reviews/SYNTHESIS.md), later reviewer
feedback, and the owner's subsequent decisions. The historical design reviews
remain evidence of the earlier debate; they are not the selected implementation.

For the Phase 1 implementation authorized here, this guide is controlling
wherever it conflicts with revision-24 `implementation-spec.md`, `README.md`,
`pricing-design.md`, `dynamic-controller-proposal.md`, or the current Instant
Bond source. Those materials remain historical controller, rationale, and
implementation evidence only. Do not edit them during Phase 1.

No production parameter value, deployment, registration, mint permission, or
activation is authorized by this guide.

## 1. Read this first: exact Phase 1 authorization

The fresh implementation agent must create its own branch and linked worktree.
Do not switch branches in the source worktree and do not work in
`/Users/wigglez/dev/ripe-protocol`.

Use these names unless they already exist:

```sh
SOURCE_WORKTREE=/Users/wigglez/dev/ripe-protocol-instant-bond-lane
IMPLEMENTATION_WORKTREE=/Users/wigglez/dev/ripe-protocol-ripe-reserve-engine-contracts-phase1
IMPLEMENTATION_BRANCH=codex/ripe-reserve-engine-contracts-phase1
BASE_COMMIT=7ae57fc72a8c45179a76ecd8328828effe2fea8e
BASE_TREE=8af20f7667157279b9c6c7b7da9f6086601a7240

git -C "$SOURCE_WORKTREE" rev-parse HEAD^{commit} HEAD^{tree}
git -C "$SOURCE_WORKTREE" status --short --branch
git -C "$SOURCE_WORKTREE" worktree add -b "$IMPLEMENTATION_BRANCH" \
  "$IMPLEMENTATION_WORKTREE" "$BASE_COMMIT"
```

Before creating the worktree, verify:

- the commit and tree exactly match the values above;
- the source worktree's only expected dirty path is this untracked guide;
- the proposed branch and worktree path do not already exist.

If any check differs, stop and report it. Do not reset, restore, stash, clean,
pull, fetch, delete, or reuse anything to force the expected state. Read this
guide from the source worktree, but do not copy, edit, stage, or commit it in the
implementation branch.

### Phase 1 writable paths

Only these five production-source Git pathnames may change, producing four
resulting source files:

1. Delete `contracts/core/InstantBondLane.vy` and replace it with
   `contracts/core/RipeReserveEngine.vy`.
2. Rewrite the feature-specific surface in
   `contracts/config/SwitchboardFoxtrot.vy`.
3. Rename the slot-26 symbols and getters in `contracts/modules/Addys.vy`.
4. Add `interfaces/RipeReserveEngine.vyi` as the shared Engine/Foxtrot ABI.

Phase 1 implements the complete selected contract semantics below, not a
rename-only checkpoint.

### Phase 1 hard exclusions

Do not create, edit, rename, generate, or run:

- tests or fixtures;
- Python tooling, simulations, deployment scripts, or activation files;
- ABI JSON, manifests, CI/workflow files, coverage configuration, or reports;
- documentation, including this guide;
- dependencies, lockfiles, formatting sweeps, or unrelated cleanup.

Do not modify `DeptBasics.vy`, `Department.vyi`, `SwitchboardCharlie.vy`,
`RipeHq.vy`, `RipeToken.vy`, Teller, RipeGov, MissionControl, Ledger, BondRoom,
Endaoment, or any other contract or interface.

Do not compile or run any test in Phase 1. Before the completion checks in
section 9 pass, do not commit, push, or open a PR. After they pass, the one
scoped commit, branch push, and source-review draft PR required by section 9 are
authorized. Do not merge, deploy, configure, register slot 26, grant mint
authority, fund, or activate anything. The user will review the smart-contract
source in that PR before authorizing tests.

## 2. Selected product

The feature becomes the **RIPE Reserve Engine**, the protocol's primary channel
for distributing larger amounts of RIPE in exchange for reserve assets. Block
rewards remain a separate distribution channel.

One Engine run accepts one approved payment/reserve asset. The payer receives a
RIPE allocation calculated from the epoch's base payout rate and the payer's
selected vesting duration. The exact allocation is minted into the Engine and
released from an isolated position over time.

The Engine is not debt. A position provides no principal repayment, interest,
maturity payment, ownership of reserve assets, or redemption claim against the
contributed asset. Public language must describe the actual payment, mint, vest,
claim, and governance-recovery mechanics; the product name is not a substitute
for legal review.

These decisions are fixed:

| Area | Selected behavior |
|---|---|
| Public name | **RIPE Reserve Engine** |
| Contract | `RipeReserveEngine` |
| Registry | `RIPE_RESERVE_ENGINE_ID`, retaining numeric slot `26` |
| Audience | Retail and institutional participants use the same mechanism |
| User methods | `previewAcquireRipe`, `acquireRipe`, `claimVestedRipe` |
| Buyer | Payer is the immutable beneficiary in v1 |
| Delivery | Mint exact RIPE to the Engine, never directly to the payer |
| Positions | One independent, nontransferable, never-merged position per acquisition |
| Minimum lock | Fixed, nonzero no-claim cliff in the Engine |
| Vesting | Linear after the cliff through a buyer-selected full-vesting duration |
| Incentive | Longer duration receives a bounded, weakly monotonic RIPE allocation adjustment; integer plateaus are accepted |
| Timing | Preserve the existing genesis, epoch, timing, and empty-time behavior |
| RipeGov | Remove from acquisition; a participant may use Teller after claiming |
| Claims | Pull-based, position-specific, beneficiary-only, and live after shutdown |
| Recovery | Exact-amount RIPE recovery to canonical governance, with position safeguards |
| Token scope | No blacklist-, burn-, or lost-key-verification machinery |
| BondRoom activation policy | Disabled by default while the Engine operates; coexistence needs separate approval |

Do not use active product or ABI terms containing `InstantBond`, `bond`, `sale`,
`buyNow`, `yield`, `interest`, `APY`, `maturity`, or `redemption`. Historical
review files are not renamed.

## 3. Definitions and decision record

- **Instance:** one deployed `RipeReserveEngine` contract.
- **Run:** one started campaign with a snapshotted payment asset, vesting terms,
  epoch cadence, and starting controller state.
- **Lineage:** this instance plus predecessor Engine instances whose cumulative
  allocations consume the same distribution authorization.
- **Base payout rate:** RIPE base units allocated per whole payment token before
  the duration adjustment. A higher rate means more RIPE for the same payment.
- **Total allocation:** base allocation plus the duration adjustment.
- **Outstanding RIPE:** allocated RIPE not yet claimed or recovered.
- **Escrow coverage deficit:** `totalOutstandingRipe` exceeds the Engine's pinned
  RIPE balance. Do not call this insolvency in the ABI, events, or documentation.
- **Time:** block numbers are canonical. References to 90 days are implemented as
  a deployment-calibrated block count; calendar dates are estimates only.

Recorded-decision treatment:

| Record | Treatment |
|---|---|
| Decision 2 | Superseded: isolated Engine positions now support a duration adjustment |
| Decisions 5, 9, and 16 | Superseded: Engine escrow and RIPE-safe recovery replace inherited recovery and purchase-time RipeGov custody |
| Decisions 21, 22, and 28 | Superseded by the bounded named-epoch override below |
| Decision 14 / revision-24 last-write-wins behavior | Superseded by explicit config, run-terms, closure, capacity, and rate identities |
| Decision 6 | Retained: acquisitions may remain available during protocol bad debt; proceeds do not repair RipeGov bad debt |
| Decisions 7 and 13 | Retained: payer equals beneficiary |
| Decision 23 | Retained: any currently registered switchboard is trusted by the Engine |
| Decision 24 | Retained: a quote is market information, not settlement readiness or a reservation |
| Decision 27 | Superseded by monotonic lineage allocation and live outstanding limits |
| New | Primary-channel role, one retail/institutional mechanism, position recovery, a 100% hard adjustment ceiling, no per-buyer cap, and no blacklist/burn machinery are accepted |

## 4. Preserve the useful controller; replace the settlement

Start from the current `InstantBondLane.vy` controller rather than rewriting its
economics from memory. Preserve:

- one fixed base payout rate per committed epoch;
- scheduled genesis and the wait before it;
- `genesisBlock == 0` meaning start at the execution block;
- the existing explicit-past-genesis and partial-first-epoch behavior;
- a new immutable bound on future genesis lead;
- lazy first-purchase initialization and rollover;
- cold start at the seed rate, without pre-first-purchase decay;
- high-utilization, dead-band, and low-utilization branches;
- payment-amount-weighted intra-epoch lateness in the high branch;
- capped empty/skipped-epoch decay, including the existing treatment of paused,
  disabled, and capacity-unavailable elapsed epochs;
- minimum payment, hard payment capacity, and full-fill-or-revert;
- no keeper and no on-chain fair-value oracle.

Only accepted payment and payment timing feed the controller. Selected vesting
duration, allocated RIPE, claims, and recoveries do not feed utilization or
timing. Preserve the current controller rounding and same-block split/order
semantics unless this guide expressly changes them.

Where an epoch has both an ordinary controller rate and a final rate, the final
rate is controller history. Every later ordinary transition starts from
`min(previousEpoch.basePayoutRate, current baseRateCeiling())`, never from
`previousEpoch.controllerBasePayoutRate`. Thus a one-shot override is one direct
rate substitution, but the substituted final rate still influences later
controller transitions exactly as the current override does.

Remove the entire purchase-time Teller/RipeGov path and the MissionControl,
Ledger, Teller, RipeGov-vault, requested-lock, exit, and bad-debt-quote
dependencies. The minimum-lock requirement is now the Engine's cliff. The old
account-wide governance-lock bonus becomes the isolated position's duration
adjustment.

## 5. `RipeReserveEngine.vy`

### 5.1 Department integration and constructor

Keep `implements: Department`, initialize `addys` and `deptBasics`, and export
only `deptBasics.canMintGreen` and `deptBasics.canMintRipe`. Follow the selective
export/manual Department pattern already used by `Endaoment.vy`:

- initialize paused;
- `canMintGreen == False`;
- `canMintRipe == True`;
- implement `isPaused`, `pause`, `recoverFunds`, and `recoverFundsMany` directly;
- use the existing `DepartmentPauseModified` and `DepartmentFundsRecovered`
  events;
- do not export the inherited recovery entrypoints, because they can sweep RIPE.

The constructor must pin the RIPE token used by the instance and verify it is the
current RipeHq RIPE address. Claims from this instance always use that pinned
token even if the registry later rotates. A retired instance remains a live
claim contract for its original token.

Use this constructor shape; field types are `uint256` except the two addresses
and the two structs:

```text
__init__(
    ripeHq,
    ripeToken,
    initialConfig: ReserveEngineConfig,
    initialRunTerms: ReserveEngineRunTerms,
    hardLineageAllocationCap,
    priorLineageAllocated,
    minClaimCliffBlocks,
    minLinearVestingBlocks,
    maxVestingHorizon,
    minBaseAllocation,
    minEpochLength,
    maxEpochLength,
    maxGenesisLeadBlocks,
    recoveryDormancyBlocks,
    recoveryNoticeBlocks,
    recoveryExecutionWindowBlocks,
)
```

Validate both initial structs and their cross-domain relationships atomically in
the constructor. This avoids a partially configured bootstrap. Store them as
the staged/current configuration for the first future run, set
`currentConfigVersion = 1` and `runTermsVersion = 1`, but keep `runId = 0` and
no active run. `activeRunTerms` and `epochState` start empty.

Use fail-closed initial state: paused, disabled, not running, lineage limit equal
to prior lineage allocation, and outstanding limit zero. Initialize position
and recovery action IDs to `1`; ID `0` is invalid and IDs are never reused.
Initialize `runId`, `runRegistryVersion`, `closureNonce`,
`capacityReductionNonce`, `rateNonce`, `overrideApplicationsThisRun`, and all
lifetime allocation/claim/recovery totals to `0`.

Constructor immutables are the scalar bounds listed above. Require:

```text
0 < MIN_CLAIM_CLIFF_BLOCKS
2 <= MIN_LINEAR_VESTING_BLOCKS
MIN_LINEAR_VESTING_BLOCKS <= MAX_VESTING_HORIZON <= 2**128 - 1
0 < MIN_BASE_ALLOCATION
0 < MIN_EPOCH_LENGTH < MAX_EPOCH_LENGTH
MAX_EPOCH_LENGTH <= max_value(uint256) // 10_000 + 1
0 < MAX_GENESIS_LEAD_BLOCKS
priorLineageAllocated <= HARD_LINEAGE_ALLOCATION_CAP
0 < RECOVERY_DORMANCY_BLOCKS
0 < RECOVERY_NOTICE_BLOCKS
0 < RECOVERY_EXECUTION_WINDOW_BLOCKS
```

The `2**128 - 1` vesting-horizon bound makes the required quotient/remainder
vesting multiplication full-width safe. The recovery execution window begins
after notice maturity.

The hard code-level duration-adjustment ceiling is:

```text
MAX_DURATION_ADJUSTMENT_BPS = 10_000  # 100% additional RIPE
MAX_DURATION_GRID_POINTS = 256
```

Production configuration is expected to be materially lower and remains an
owner-supplied calibration.

Both Engine and Foxtrot have material runtime-size pressure. Reuse narrow
internal helpers, avoid duplicate public wrappers, and use the repository's
codesize optimization pragma where appropriate. This is source guidance only;
compilation and exact EIP-170 measurement remain Phase 2.

### 5.2 Required types and state

Use one canonical definition for every shared type in
`interfaces/RipeReserveEngine.vyi`; do not maintain divergent Engine and
Foxtrot copies.

Represent rate source as `uint8` with fixed values:

```text
RATE_SOURCE_NONE = 0
RATE_SOURCE_SEED = 1
RATE_SOURCE_CONTROLLER = 2
RATE_SOURCE_OVERRIDE = 3
```

`ReserveEngineConfig` holds prospective controller economics:

```text
paymentCapPerEpoch
minPaymentAmount
maxAllInPayoutRate
seedBasePayoutRate
uHighBps
uLowBps
minPriceIncreaseBps
maxPriceIncreaseBps
minPriceDecreaseBps
maxPriceDecreaseBps
decayBps
maxDecayEpochs
maxOverrideDeviationBps
maxOverrideLeadEpochs
```

Every config field is `uint256` in the listed order.

`ReserveEngineRunTerms` holds stopped-only, next-run product terms:

```text
paymentToken
epochLength
claimCliffBlocks
minFullVestingBlocks
maxFullVestingBlocks
durationStepBlocks
maxDurationAdjustmentBps
maxOverrideApplicationsPerRun
```

`paymentToken` is `address`; every remaining run-term field is `uint256`, in the
listed order.

Store `stagedRunTerms` for the next start and an immutable-for-the-run
`activeRunTerms` snapshot. `getRunTerms()` returns the staged value;
`getActiveRunTerms()` returns the active snapshot or the empty struct when no run
has ever started. References below to the active run's override budget or
duration adjustment mean fields of `activeRunTerms`.

Keep `isEngineEnabled` outside both structs so a queued configuration can never
re-enable an Engine that was closed after queueing.

`EpochSnapshot` must retain the current controller fields and add enough
identity to make a committed epoch immutable:

```text
epoch
controllerBasePayoutRate
basePayoutRate
rateSource
rateNonce
epochConfigVersion
paymentCap
minPaymentAmount
acceptedPayment
paymentWeightedLateness
timingEligible
```

`rateSource` is `uint8`, `timingEligible` is `bool`, and every other epoch field
is `uint256`, in the listed order.

`VestingPosition` stores exactly:

```text
beneficiary
allocation
claimed
recovered
purchaseBlock
claimStartBlock
fullyVestedBlock
selectedFullVestingBlocks
durationAdjustmentBps
runId
epoch
epochConfigVersion
basePayoutRate
rateSource
rateNonce
positionVersion
```

`beneficiary` is `address`, `rateSource` is `uint8`, and every other position
field is `uint256`, in the listed order.

Do not add position transfer, beneficiary redesignation, merge, cancellation,
refund, acceleration, extension, receipt NFT/token, owner enumeration, or
`claimMany` in Phase 1. Positions are discoverable from indexed events and the
public position mapping. Initialize each position's `positionVersion` to `1`.
Claims are claim-all-at-the-current-block, so `lastClaimBlock` would not extend
the recovery dormancy of a still-outstanding fully vested position and must not
be stored.

Required aggregate state:

```text
totalAllocated
totalClaimed
totalRecovered
activeLineageAllocationLimit
activeOutstandingRipeLimit
runId
runRegistryVersion
currentConfigVersion
runTermsVersion
closureNonce
capacityReductionNonce
rateNonce
overrideApplicationsThisRun
```

Also store the exact `currentConfig`, `stagedRunTerms`, `activeRunTerms`,
`epochState`, and `installedRateOverride` structs, plus immutable `ripeHq` and
`pinnedRipe` addresses and the active run's payment decimals/scale. Do not create
parallel scalar copies unless required for an immutable or a public ABI getter.

Derive rather than separately mutate:

```text
lineageAllocated = priorLineageAllocated + totalAllocated

totalOutstandingRipe =
    totalAllocated - totalClaimed - totalRecovered

positionOutstanding =
    position.allocation - position.claimed - position.recovered
```

`totalAllocated` is lifetime-monotonic. Claims and either form of RIPE recovery
never reopen lineage allocation capacity. Every accepted controller-config
change increments `currentConfigVersion`. An already committed epoch retains
its `epochConfigVersion`; a newly projected epoch uses the then-current version.

### 5.3 Run and configuration validation

A run snapshots one payment asset, one duration grid, and one finite override
application budget. Changing the payment asset, epoch cadence, cliff, duration
range, step, maximum duration adjustment, or per-run override budget is
stopped-only and applies only to a later `start`. It never changes an existing
position. Each accepted staged change increments `runTermsVersion`.

The payment token must be a nonzero contract distinct from pinned RIPE, expose a
stable supported decimal count no greater than the existing
`MAX_PAYMENT_DECIMALS`, and pass the exact-transfer behavior at acquisition.
Snapshot its address, decimals, and scale into the run.

Preserve these code constants from the current controller:

```text
MAX_PRICE_STEP_BPS = 10_000
MAX_DECAY_EPOCHS = 32
MAX_PAYMENT_DECIMALS = 73
MIN_BASE_RATE = 10_000
```

The renamed controller fields describe the implied RIPE price, not the payout
rate. Do not invert them:

```text
minPriceIncreaseBps / maxPriceIncreaseBps
    = current minUpBps / maxUpBps
    = high-utilization branch: implied RIPE price rises, payout rate falls

minPriceDecreaseBps / maxPriceDecreaseBps
    = current minDownBps / maxDownBps
    = low-utilization branch: implied RIPE price falls, payout rate rises

maxAllInPayoutRate = current maxEffectiveRate
seedBasePayoutRate = current seedRate
```

Port the current controller validator under those names. Every accepted config
must satisfy, using overflow-safe comparisons:

```text
0 < uLowBps < uHighBps < 10_000
0 < minPriceIncreaseBps <= maxPriceIncreaseBps <= MAX_PRICE_STEP_BPS
0 < minPriceDecreaseBps <= maxPriceDecreaseBps <= decayBps < 10_000
maxPriceDecreaseBps < minPriceIncreaseBps

(10_000 + minPriceIncreaseBps) * (10_000 - decayBps)
    >= 10_000**2

0 < maxDecayEpochs <= MAX_DECAY_EPOCHS
0 < maxAllInPayoutRate <= max_value(uint256) // 10_000
paymentScale <= minPaymentAmount <= paymentCapPerEpoch
paymentCapPerEpoch <= max_value(uint256) // 10_000
maxAllInPayoutRate <= max_value(uint256) // paymentCapPerEpoch
0 <= maxOverrideDeviationBps <= 10_000
```

The last line is notation over a `uint256`: zero is valid and permits only an
exact controller-rate match. `maxOverrideLeadEpochs` is also a `uint256`; zero
means only the current projected, uncommitted epoch. At use sites compare
`targetEpoch - projectedEpoch <= maxOverrideLeadEpochs` after first proving
`targetEpoch >= projectedEpoch`; do not add and risk overflow.

Validate the current config against the applicable payment scale and duration
adjustment: the active run while running, otherwise the staged run terms. The
implied maximum base allocation, duration adjustment, total allocation, and all
payment/rate products must fit in `uint256`. Replace only the obsolete
mint-budget and RipeGov-lock predicates with the lineage, outstanding, and
duration rules in this guide; do not drop the controller's anti-oscillation,
anti-ratchet, or overflow guards.

Require `MIN_EPOCH_LENGTH <= epochLength <= MAX_EPOCH_LENGTH`. Preserve the
current `epochLength == 1` branch that defines payment lateness as zero rather
than dividing by `epochLength - 1`.

For cliff `C`, minimum duration `Dmin`, maximum duration `Dmax`, and step `S`,
require:

```text
C >= MIN_CLAIM_CLIFF_BLOCKS > 0
MIN_LINEAR_VESTING_BLOCKS >= 2
Dmin >= C + MIN_LINEAR_VESTING_BLOCKS
Dmax > Dmin
Dmax <= MAX_VESTING_HORIZON
S > 0
(Dmax - Dmin) % S == 0
0 < maxDurationAdjustmentBps <= 10_000

maxDurationAdjustmentBps * (Dmin - C)
    < 10_000 * (Dmax - Dmin)
```

Use overflow-safe comparisons. The strict final inequality prevents the
continuous duration curve from giving the longest choice both more RIPE and
faster release. It is necessary but not sufficient after integer flooring.

A valid buyer duration is exactly:

```text
Dmin <= D <= Dmax
(D - Dmin) % S == 0
```

Off-grid values revert; never round or clamp them. Require:

```text
gridPointCount = (Dmax - Dmin) / S + 1
gridPointCount <= MAX_DURATION_GRID_POINTS  # 256
```

`_isValidRunTerms` must loop over every adjacent grid pair. For `D1 < D2`, let:

```text
L1 = D1 - C
L2 = D2 - C
M1 = 10_000 + adjustmentBps(D1)
M2 = 10_000 + adjustmentBps(D2)
margin = M1 * L2 - M2 * L1
```

Require `margin > 0` and the following overflow-safe sufficient condition:

```text
MIN_BASE_ALLOCATION * margin >= 10_000 * L2
```

Together with `baseAllocation >= MIN_BASE_ALLOCATION` at acquisition, this
guarantees a strictly decreasing **average linear release rate** for every
adjacent duration and any valid acquisition. In exact allocation arithmetic,
require the equivalent cross-product relationship:

```text
totalAllocation(D1) * (D2 - C)
    > totalAllocation(D2) * (D1 - C)
```

This is not a promise that every individual block's floored vesting increment
is strictly smaller; quotient/remainder increments may tie. Plateaus in
adjustment bps or allocation remain acceptable, and weak allocation
monotonicity is deliberate. Implement the products with checked
decomposition/comparison rather than permitting overflow.

For a purchase included at block `P` with selected purchase-to-full-vest
duration `D`:

```text
claimStartBlock = P + C
fullyVestedBlock = P + D
linearVestingBlocks = D - C
```

Check both additions before storing them.

Preserve `MIN_BASE_RATE` and validate:

```text
baseRateCeiling >= MIN_BASE_RATE
MIN_BASE_RATE <= seedBasePayoutRate <= baseRateCeiling
```

The smallest legal payment at `MIN_BASE_RATE` must produce at least
`MIN_BASE_ALLOCATION` and never a zero-value position. Run the complete
controller and adjacent-pair duration-grid qualification in the constructor,
`setConfig`, `setRunTerms`, and `start` as applicable. Because active run terms
cannot mutate, preview and acquisition perform only O(1) checks for the selected
duration's on-grid membership, applicable snapshot/version identities,
allocation floor, payment decimals, live limits, token identities, mint
authorization, and coverage. Do not run the 256-point qualifier per purchase.

An accepted controller-config change is prospective. It governs only epochs
committed after the change. A committed epoch retains its snapshotted payment
cap, minimum payment, ordinary controller rate, final base rate, source, nonce,
and config version; acquisition must not compare that stored rate with a later
current `baseRateCeiling`. Pause, disable, stop, and live-limit reductions are
the immediate closure controls.

`start` is stopped-only, validates the complete staged configuration and run
terms, requires this instance to occupy RipeHq slot 26, and reads that slot's
`AddressInfo.version`. Snapshot the version as `runRegistryVersion`, snapshot the
exact `runTermsVersion`, increment `runId`, set the resolved genesis and active
run identity, leave `epochState` empty, reset the per-run override count, and
ensure no installed override remains. Do not eagerly store a seed epoch. The
first successful acquisition lazily commits either the seed result or a valid
target-epoch override, with no decay for pre-first-purchase elapsed epochs. A
queued start captures `currentConfigVersion`, `runTermsVersion`, `closureNonce`,
the current slot address, and current slot version so later staging, closure,
replacement, slot-26 registry disable, or A-to-B-to-A restoration makes it
stale. It must not implicitly unpause or enable the Engine.

At `start` execution, `genesisBlock == 0` resolves to the execution block. An
explicit past genesis remains valid and preserves the existing partial-first-
epoch behavior. An explicit future genesis is valid only when
`genesisBlock - block.number <= MAX_GENESIS_LEAD_BLOCKS`; this lead bound is a
new immutable, not behavior inherited from the current contract.

`stop` invalidates any installed override, sets `isRunning = False`, clears
`epochState`, and sets `genesisBlock = 0` while advancing `closureNonce` as
specified below. Retain the last `activeRunTerms`, active payment-token
address/decimals/scale, `runId`, and `runRegistryVersion` for historical
inspection. A later `start` overwrites those active-run snapshots and again
leaves `epochState` empty until its first successful acquisition.

### 5.4 Duration adjustment and all-in ceiling

All calculations round down:

```text
durationAdjustmentBps =
    floor(
        maxDurationAdjustmentBps
        * (D - Dmin)
        / (Dmax - Dmin)
    )

baseAllocation =
    floor(paymentAmount * basePayoutRate / paymentScale)

adjustmentAllocation =
    floor(baseAllocation * durationAdjustmentBps / 10_000)

totalAllocation = baseAllocation + adjustmentAllocation
```

Use checked bounds or quotient/remainder decomposition anywhere a product can
overflow. Adjustment monotonicity is weak because floors may create plateaus.

`maxAllInPayoutRate` caps the maximum-duration result. Derive:

```text
baseRateCeiling =
    floor(
        maxAllInPayoutRate * 10_000
        / (10_000 + maxDurationAdjustmentBps)
    )
```

The controller may ordinarily saturate at `baseRateCeiling`. Seed and override
rates outside the legal base-rate range are invalid. Never calculate an
excessive individual allocation and clamp it afterward; per-acquisition clamping
would distort the duration curve.

Payment capacity and controller utilization remain payment-denominated. The
adjusted `totalAllocation` consumes every RIPE-denominated lineage, active,
outstanding, escrow, and reporting rail. Worst-case issuance assumes every
participant chooses `Dmax`.

### 5.5 Quote and acquisition ABI

Use:

```text
previewAcquireRipe(paymentAmount, selectedFullVestingBlocks)
    -> ReserveEngineQuote

acquireRipe(
    paymentAmount,
    selectedFullVestingBlocks,
    constraints: AcquisitionConstraints,
) -> (positionId, totalAllocation)
```

The payer is `msg.sender` and is stored as the beneficiary. There is no recipient
argument.

Use this exact `ReserveEngineQuote` field order:

```text
available: bool
reasonFlags: uint256
runId: uint256
runRegistryVersion: uint256
epochConfigVersion: uint256
closureNonce: uint256
capacityReductionNonce: uint256
epoch: uint256
epochEndBlock: uint256
paymentToken: address
proceedsRecipient: address
paymentAmount: uint256
paymentScale: uint256
remainingPaymentCapacity: uint256
controllerBasePayoutRate: uint256
basePayoutRate: uint256
rateSource: uint8
rateNonce: uint256
selectedFullVestingBlocks: uint256
claimCliffBlocks: uint256
durationAdjustmentBps: uint256
baseAllocation: uint256
adjustmentAllocation: uint256
totalAllocation: uint256
projectedClaimStartBlock: uint256
projectedFullyVestedBlock: uint256
remainingLineageCapacity: uint256
remainingOutstandingCapacity: uint256
isEscrowCovered: bool
escrowCoverageDeficit: uint256
overrideTargetEpoch: uint256
overrideTargetBasePayoutRate: uint256
```

Do not add caller balance, allowance, blacklist, token-pause, or token-burn
probes. Current RipeHq mint authorization is a market-open reason.

Use a `uint256` reason bitmask with these exact bits:

```text
NOT_RUNNING             = 1 << 0
ENGINE_DISABLED         = 1 << 1
ENGINE_PAUSED           = 1 << 2
BEFORE_GENESIS          = 1 << 3
INVALID_CONFIGURATION   = 1 << 4
NOT_CURRENT_INSTANCE    = 1 << 5
NO_MINT_AUTHORIZATION   = 1 << 6
ESCROW_COVERAGE_DEFICIT = 1 << 7
INVALID_DURATION        = 1 << 8
BELOW_MINIMUM_PAYMENT   = 1 << 9
PAYMENT_CAP_EXCEEDED    = 1 << 10
LINEAGE_CAP_EXCEEDED    = 1 << 11
OUTSTANDING_CAP_EXCEEDED = 1 << 12
```

`available` is exactly `reasonFlags == 0`.

Resolve the canonical Endaoment Funds proceeds address in preview. A zero
address sets `INVALID_CONFIGURATION`; it is protocol settlement configuration,
not a caller balance/allowance probe. The quote remains market information and
not a reservation.

When the Engine is stopped, `getEpochSnapshot()` returns the empty
`EpochSnapshot`, and preview must not fabricate a staged-run or legacy-seed
projection. The quote is unavailable with `NOT_RUNNING`; its epoch-, payment-
asset-, rate-, vesting-, allocation-, schedule-, and override-derived output
fields are zero. It may still return the direct inputs (`paymentAmount` and
`selectedFullVestingBlocks`) plus live lifetime identity, closure/capacity,
remaining-capacity, and escrow-coverage diagnostics. A running Engine whose
first acquisition has not occurred is different: `epochState()` remains empty,
while `getEpochSnapshot()` and preview lazily project that run's seed or valid
target override.

`AcquisitionConstraints` binds the material quote fields:

```text
expectedRunId: uint256
expectedRunRegistryVersion: uint256
expectedEpochConfigVersion: uint256
expectedClosureNonce: uint256
expectedCapacityReductionNonce: uint256
expectedEpoch: uint256
expectedPaymentToken: address
expectedProceedsRecipient: address
expectedBasePayoutRate: uint256
expectedRateSource: uint8
expectedRateNonce: uint256
expectedDurationAdjustmentBps: uint256
expectedTotalAllocation: uint256
deadlineBlock: uint256
```

The payment amount and selected duration are direct arguments and therefore
already bound. Raises to capacity do not increment `capacityReductionNonce`;
only a reduction does. A quote is not a reservation. Any material mismatch
reverts and requires a fresh quote. Quote schedule blocks are projections from
the quote block; the actual position schedule starts at transaction inclusion,
and `deadlineBlock` bounds that drift. The deadline is inclusive:
`block.number <= deadlineBlock`.

`acquireRipe` must be nonreentrant and execute in this order:

1. Validate genesis, running/enabled/unpaused state, inclusive deadline, and
   `RipeHq.ripeToken() == pinnedRipe`. Require current slot-26 address and version
   to equal `(self, runRegistryVersion)`, validate the applicable run/config
   state, current `RipeHq.canMintRipe(self)` authorization, a nonzero current
   Endaoment Funds proceeds address, O(1) selected-duration membership, and
   pre-operation escrow coverage. Mint only the pinned token; claims continue to
   use it even if slot 3 rotates after acquisitions stop.
2. Project or load the epoch, apply the override state machine if relevant, and
   validate every acquisition constraint against the exact snapshot that will
   be committed.
3. Enforce minimum payment and full-fill payment capacity.
4. Calculate the base and adjusted allocation; enforce the minimum position
   allocation, active lineage limit, immutable hard lineage cap, and active
   outstanding-RIPE limit against the adjusted total.
5. Commit epoch/controller state, create a new position, and increment
   `totalAllocated` before external calls. Every failure later reverts all state.
6. Transfer the exact payment amount from the payer directly to the current
   canonical Endaoment Funds address and verify its exact balance increase.
   Fee-on-transfer or otherwise incompatible payment assets revert.
7. Mint the exact total allocation to the Engine and verify the Engine's pinned
   RIPE balance increased by exactly that amount.
8. Verify post-operation escrow coverage and emit `RipeAllocated`.

The position's purchase, claim-start, and full-vest blocks are based on the
actual inclusion block. The event indexes payer/beneficiary and position ID and
includes payment, base rate/source identity, duration adjustment, total
allocation, schedule, run, and epoch.

### 5.6 Vesting and claims

For position allocation `A`, recovered amount `R`, claim-start block `S`,
full-vest block `F`, and current block `b`:

```text
grossVested(b) = 0                         if b <= S
grossVested(b) = A                         if b >= F
grossVested(b) = floor(A * (b - S) / (F-S)) otherwise

remainingEntitlement = A - R

claimable =
    min(grossVested, remainingEntitlement)
    - claimed
```

Implement the middle vesting branch with quotient/remainder decomposition, not
an unchecked `A * elapsed` product. The terminal branch returns exactly `A`, so
rounding cannot strand final dust.

`claimVestedRipe(positionId)` claims all currently claimable RIPE. It must:

- accept only the stored beneficiary and always pay that beneficiary;
- reject nonexistent positions and a zero claimable amount;
- ignore acquisition pause, disabled, stopped, exhausted, and retired state;
- fail closed during an escrow coverage deficit;
- increment position claimed, `totalClaimed`, and `positionVersion` before
  transfer;
- invalidate and clear a pending recovery for that position, with an event;
- verify exact Engine-balance reduction and beneficiary-balance increase;
- verify post-operation escrow coverage and revert atomically on failure.

Claims never affect controller state or lifetime lineage allocation.

### 5.7 Escrow coverage

Expose:

```text
isEscrowCovered = RIPE.balanceOf(self) >= totalOutstandingRipe

escrowCoverageDeficit =
    max(totalOutstandingRipe - RIPE.balanceOf(self), 0)

escrowSurplus =
    max(RIPE.balanceOf(self) - totalOutstandingRipe, 0)
```

If a token-admin action or external balance change creates a deficit, all new
acquisitions, participant claims, position-specific RIPE recoveries, and
RIPE-surplus recoveries fail closed. This prevents transaction ordering from
selecting winners from an under-covered balance.

There is no stored deficit flag, administrator reset, blacklist branch, burn
branch, or remediation subsystem. A direct RIPE transfer to the Engine restores
coverage arithmetically; operations resume automatically once the balance is
sufficient. Overshoot becomes ordinary surplus. Non-RIPE recovery remains
available during a deficit.

Every successful Engine-controlled RIPE transition must end with:

```text
RIPE.balanceOf(self) >= totalOutstandingRipe
```

### 5.8 Non-RIPE and surplus RIPE recovery

Preserve the Department ABI exactly:

```text
recoverFunds(recipient, asset)
recoverFundsMany(recipient, assets[<=20])
```

These functions keep normal whole-live-balance recovery for non-RIPE assets,
including the existing caller-supplied recipient. Validate nonzero values and
reject the pinned RIPE address in both single and batch paths. They are
nonreentrant and callable by any currently registered switchboard. If a batch
contains pinned RIPE, revert the entire batch atomically.

Add a separate amount-specific function:

```text
recoverRipeSurplus(amount) -> bool
```

It has no recipient argument. Return `False` without mutation when:

```text
amount == 0
amount > live escrowSurplus
```

Otherwise resolve the canonical recipient from `RipeHq.governance()` at
execution, transfer exactly `amount`, verify exact balance changes, return
`True`, and leave all position and allocation accounting unchanged. It never requires
`totalOutstandingRipe == 0`. Foxtrot should use its ordinary timelock for this
route and consume an action as a stale no-op if live surplus is no longer
sufficient. The Engine still rechecks the bound atomically.

Claims, position-specific recovery, and surplus recovery are instance-local and
must not require the Engine to remain current in slot 26. This preserves custody
and recovery for retired instances; acquisition remains current-instance only.

### 5.9 Position-specific RIPE recovery

This is an explicit governance power to cancel and recover part or all of a
fully vested, inactive, unclaimed position. The contract does not determine
whether a key is actually lost. Do not add a lost-key oracle, beneficiary
rewrite, abandonment classification, blacklist logic, or burn logic.

Because the Engine trusts any registered switchboard, the mandatory recovery
notice must be enforced inside the Engine. A Foxtrot-only queue would be
bypassable by another registered switchboard.

Add:

```text
queueRipeRecovery(positionId, amount) -> recoveryActionId
executeRipeRecovery(recoveryActionId) -> bool
cancelRipeRecovery(recoveryActionId) -> bool
```

All three require a currently registered switchboard. Do not pin Foxtrot.

Queue only when:

```text
block.number >= fullyVestedBlock + RECOVERY_DORMANCY_BLOCKS
amount > 0
amount <= positionOutstanding
```

`RECOVERY_DORMANCY_BLOCKS` is the immutable target-chain block equivalent of
approximately 90 days. Permit only one live queued recovery per position.

The Engine stores this exact `PendingRipeRecovery` field order:

```text
actionId: uint256
positionId: uint256
beneficiary: address
amount: uint256
expectedPositionVersion: uint256
expectedPositionOutstanding: uint256
governanceRecipientSnapshot: address
governanceGenerationSnapshot: uint256
queuedBlock: uint256
executeAfterBlock: uint256
expiresAtBlock: uint256
```

Calculate the window as:

```text
executeAfterBlock = queuedBlock + RECOVERY_NOTICE_BLOCKS
expiresAtBlock = executeAfterBlock + RECOVERY_EXECUTION_WINDOW_BLOCKS
```

Both intervals are nonzero and both additions are checked.

The execution interval is exact:

```text
mature:  block.number >= executeAfterBlock
live:    block.number < expiresAtBlock
expired: block.number >= expiresAtBlock
```

Resolve both `RipeHq.governance()` and the already-exported
`RipeHq.numGovChanges()` at queue time and do not accept a recipient argument.
Emit `RipeRecoveryQueued`, indexed by position and beneficiary, with the exact
amount, recipient, governance generation, version, maturity, and expiry.

The beneficiary may claim during the notice period. A successful claim updates
activity/version and clears the queued recovery. Any governance rotation,
including an address sequence that later returns to the original address, a
prior recovery, position-version/accounting mismatch, cancellation, or expiry
also makes the action terminal without a transfer. Never clamp a stale amount or
redirect it to a new recipient.

At execution:

1. For an issued pending action, return `False` without clearing if the notice
   has not matured, even if governance has already rotated.
2. After maturity, clear and emit a terminal reason if the action is expired or
   objectively stale.
3. Recheck current canonical governance and `numGovChanges()` equal both queued
   snapshots, plus the exact position version/outstanding amount and
   `amount <= positionOutstanding`.
4. During a coverage deficit, return `False` without a RIPE transfer and leave
   the otherwise-live action available until coverage is restored or it expires.
5. Clear pending state and increment position recovered, `totalRecovered`, and
   `positionVersion` before transfer.
6. Transfer the exact amount to canonical governance, verify both balance deltas,
   verify post-operation coverage, and emit `RipeRecoveredForPosition`.

`executeRipeRecovery` and `cancelRipeRecovery` return `False` for a validly
issued ID that is already terminal or no longer pending. ID `0` and never-issued
IDs remain invalid. This lets a Foxtrot route close safely after a beneficiary
claim or another switchboard has already terminated the Engine action.

Recovery may be partial and repeated. It reduces position and global
outstanding RIPE but never reduces `totalAllocated` or lineage allocation. It
does not require unrelated positions or global outstanding RIPE to be zero.

### 5.10 Rate override

Replace the indefinite scalar override with one installed, one-shot, named-epoch
`RateOverride` using this exact field order:

```text
targetBasePayoutRate: uint256
targetEpoch: uint256
runId: uint256
runRegistryVersion: uint256
installedConfigVersion: uint256
closureNonce: uint256
installedRateNonce: uint256
```

The Foxtrot install is timelocked. At most one Foxtrot install action may be
pending. Engine installation requires running, enabled, unpaused state; current
slot-26 address/version equal to the active run identity; no installed override;
unused run override budget; current captured config/run/closure/rate identities;
and a target rate inside `[MIN_BASE_RATE, baseRateCeiling()]`. Do not require a
prior acquisition or nonzero committed epoch state.

`isValidRateOverride(targetBasePayoutRate, targetEpoch)` must include every
intrinsic live installation predicate: running, enabled, and unpaused state;
current slot-26 address/version equal to `(self, runRegistryVersion)`; no
installed override; a nonzero active run budget where
`overrideApplicationsThisRun` is less than
`activeRunTerms.maxOverrideApplicationsPerRun`; valid active config/run state;
legal target-rate and target-epoch bounds; and an uncommitted target. Foxtrot
separately compares the payload's captured run, registry, config, closure, and
rate identities. It must be able to use this view at step 4 to classify a mature
install action as stale without relying on a reverting Engine call.

Treat the current projected epoch as `0` before genesis. A target may be the
current projected, still-uncommitted epoch or a later epoch satisfying:

```text
targetEpoch >= projectedEpoch
targetEpoch - projectedEpoch <= maxOverrideLeadEpochs
```

Before genesis this permits targets `0..maxOverrideLeadEpochs`, not only epoch
zero. Foxtrot alone knows its timelock. At queue time it must require that its
earliest confirmation block is before the target epoch's end-exclusive block,
using checked genesis/epoch arithmetic; the Engine must not try to inspect
Foxtrot delay state. Revalidate live state at execution. An install remains
valid when projection equals the target and that epoch has not been committed.
It is missed after target commitment or projection beyond the target.

The queued Foxtrot action captures the current `rateNonce`. A successful install
requires that nonce to remain current, increments it once, and stores the
resulting value as `installedRateNonce`.

When the target epoch is first committed:

1. Calculate the ordinary controller base rate first.
2. Validate the target against `MIN_BASE_RATE` and the current
   `baseRateCeiling`.
3. Validate at application time:

   ```text
   abs(target - controller) * 10_000
       <= controller * maxOverrideDeviationBps
   ```

4. Use the exact target if valid.
5. Otherwise clear it as a terminal no-op and use the controller result without
   blocking an otherwise valid acquisition.

If an override replaces the seed result for the first committed epoch, store
`controllerBasePayoutRate = seedBasePayoutRate` and
`rateSource = RATE_SOURCE_OVERRIDE`.

For any later epoch, calculate the ordinary controller result from
`min(previousEpoch.basePayoutRate, current baseRateCeiling())`. Do not restart
from the previous epoch's `controllerBasePayoutRate`. A successful override is
one-shot only in the sense that it directly substitutes the named epoch; that
epoch's final `basePayoutRate` remains the starting history for the next
ordinary transition.

Use overflow-safe arithmetic. Never clamp the target or a buyer allocation.
The ordinary first commitment uses `RATE_SOURCE_SEED`; later ordinary
commitments use `RATE_SOURCE_CONTROLLER`; only a successfully applied target
uses `RATE_SOURCE_OVERRIDE`. A missed or deviation-invalid override does not
change the ordinary source.

Preview simulates override application, deviation failure, or a miss without
mutating storage. In all three terminal cases, the projected and then committed
epoch stores the pre-terminal observed global `rateNonce`. Acquisition first
commits that exact snapshot, then clears the override and increments the global
nonce exactly once. The quote constraints and `RipeAllocated` event therefore
bind the stored pre-terminal nonce even though the post-acquisition global nonce
has advanced. A preview of a later projected epoch with
`projectedEpoch > targetEpoch` follows this same ordering for a miss.

Applying, missing, invalidating, cancelling, or lifecycle-invalidating an
installed override clears it exactly once and advances the nonce. Cancellation
of an installed override is immediate. A stop, new run, payment-token/run-term
change, controller-config change, Engine pause, or Engine disable invalidates it.
Stale Foxtrot install actions consume their timelock and typed payload as a
terminal no-op rather than reverting and remaining wedged.

Installation requires:

```text
overrideApplicationsThisRun
    < activeRunTerms.maxOverrideApplicationsPerRun
```

A snapshotted maximum of zero disables override installation for that run. The
counter increments only when a committed epoch actually stores
`RATE_SOURCE_OVERRIDE`. A miss, deviation failure, cancellation, config or
lifecycle invalidation, and any other terminal no-op do not consume the budget.
Reset it only on a new run. An override affects the base rate only; the maximum-
duration outcome remains protected by the all-in ceiling.

### 5.11 Lifecycle, limits, and authority

Every Engine governance/admin mutator dynamically checks
`addys._isSwitchboardAddr(msg.sender)`. Foxtrot is the intended controller, but
the Engine does not cache or hardcode it. The Engine-side position-recovery queue
is the only extra notice mechanism required to make a participant-facing delay
unbypassable across registered switchboards.

Acquisition availability requires all of:

```text
not isPaused
isEngineEnabled
isRunning
block.number >= genesisBlock
valid current run/config
current slot-26 address/version == (self, runRegistryVersion)
current RipeHq RIPE token == pinnedRipe
current RipeHq mint authorization
escrow coverage
remaining payment, lineage, and outstanding capacity
```

Pause, disable, and stop block new acquisitions only. Claims remain callable.
Closing actions and live-limit reductions are de-escalatory. Increment
`closureNonce` exactly once on each successful `unpaused -> paused`,
`enabled -> disabled`, and `running -> stopped` transition. Reject lifecycle
no-ops. Enable, unpause, and start do not increment it. A limit reduction
increments `capacityReductionNonce`. Later reopening or raises never restore an
old nonce.

Address equality is not sufficient instance identity. Slot replacement,
slot-26 registry disable, or A-to-B-to-A restoration advances the registry
version and therefore cannot revive an old run, quote, acquisition, or ordinary
Foxtrot action. Engine disable instead advances `closureNonce`. Claims and
instance-local recovery ignore current slot occupancy. An intentionally restored
Engine may run again only after the old run is stopped and a fresh timelocked
`start` snapshots the new registry version and increments `runId`; it never
resumes the old run.

Enforce:

```text
priorLineageAllocated + totalAllocated + newAllocation
    <= activeLineageAllocationLimit
    <= HARD_LINEAGE_ALLOCATION_CAP

totalOutstandingRipe + newAllocation
    <= activeOutstandingRipeLimit
```

Active limits may be set below current use, in which case new acquisitions close
without underflow and claims continue. Claims and recovery lower outstanding
RIPE; neither restores lineage allocation room. Remove `setCumulativeMinted`
entirely.

Classify the two-limit update component-wise against the exact current pair:

- an immediate reduction requires both new values to be no greater than the
  current values and at least one to be lower;
- a queued raise requires both new values to be no less than the current values
  and at least one to be higher;
- reject mixed-direction and no-change updates.

A queued raise captures the exact current limit pair and
`capacityReductionNonce`. It becomes stale if either limit changes first. This
also serializes parallel raises even though a successful raise does not advance
the reduction nonce.

There is no calendar sunset and no per-buyer cap. The accepted tradeoff is that
an address cap is Sybil-sensitive; the payment cap is the maximum single-fill
exposure.

### 5.12 Required views and events

Expose compact views for:

- complete current config, staged/current run terms, and run/config versions;
- controller projection and committed epoch snapshot;
- duration validity, adjustment, and base-rate ceiling;
- quote and acquisition availability reasons;
- position, gross vested, claimable, and position outstanding;
- lineage allocated/remaining and active outstanding remaining;
- total outstanding RIPE, coverage status, deficit, and surplus;
- installed override status;
- queued RIPE recovery and recovery eligibility.

Required Engine event families:

- `RipeAllocated` and `VestedRipeClaimed`;
- epoch initialized/rolled with controller and final base-rate identity;
- Engine config, run terms, start, stop, enable, and limit changes;
- override installed, applied, cancelled, missed, invalid, and lifecycle-invalid;
- `RipeRecoveryQueued`, terminal recovery reason, and
  `RipeRecoveredForPosition`;
- `RipeSurplusRecovered`;
- standard Department pause and non-RIPE recovery events.

Events must carry enough indexed identity for a wallet or indexer to discover a
position and warn its beneficiary about a queued recovery. Do not retain legacy
Instant Bond event aliases.

The public user/accounting view ABI is:

```text
previewAcquireRipe(paymentAmount, selectedFullVestingBlocks)
    -> ReserveEngineQuote
positions(positionId) -> VestingPosition
grossVestedRipe(positionId) -> uint256
claimableRipe(positionId) -> uint256
positionOutstandingRipe(positionId) -> uint256
totalOutstandingRipe() -> uint256
lineageAllocated() -> uint256
remainingLineageCapacity() -> uint256
remainingOutstandingCapacity() -> uint256
isEscrowCovered() -> bool
escrowCoverageDeficit() -> uint256
escrowSurplus() -> uint256
isValidDuration(selectedFullVestingBlocks) -> bool
durationAdjustmentBps(selectedFullVestingBlocks) -> uint256
baseRateCeiling() -> uint256
epochState() -> EpochSnapshot             # stored committed snapshot
getEpochSnapshot() -> EpochSnapshot        # projection at the current block
installedRateOverride() -> RateOverride
pendingRipeRecoveries(recoveryActionId) -> PendingRipeRecovery
pendingRecoveryForPosition(positionId) -> uint256
recoveryEligibleBlock(positionId) -> uint256
genesisBlock() -> uint256
paymentToken() -> address
paymentDecimals() -> uint8
paymentScale() -> uint256
pinnedRipe() -> address
ripeHq() -> address
runRegistryVersion() -> uint256
```

While running, `baseRateCeiling()` uses the live prospective controller config
and `activeRunTerms.maxDurationAdjustmentBps`. While stopped, it uses the live
config and staged run terms. The committed epoch's stored rate remains
authoritative for that epoch even if this view later changes.

Use these exact business and state-transition event payloads; fields marked
`indexed` are indexed and field order is normative:

```text
RipeAllocated(
    beneficiary indexed, positionId indexed, paymentToken indexed,
    proceedsRecipient, paymentAmount, baseAllocation, adjustmentAllocation,
    totalAllocation, controllerBasePayoutRate, basePayoutRate,
    durationAdjustmentBps, claimStartBlock, fullyVestedBlock, runId,
    runRegistryVersion, epoch, epochConfigVersion, rateSource, rateNonce,
)

VestedRipeClaimed(
    beneficiary indexed, positionId indexed, amount,
    cumulativeClaimed, cumulativeRecovered, remainingOutstanding,
)

RipeRecoveryQueued(
    positionId indexed, beneficiary indexed, governanceRecipient indexed,
    recoveryActionId, amount, expectedPositionVersion,
    governanceGeneration, executeAfterBlock, expiresAtBlock,
)

RipeRecoveryTerminated(
    positionId indexed, beneficiary indexed, recoveryActionId,
    reason: uint8,
)

RipeRecoveredForPosition(
    positionId indexed, beneficiary indexed, governanceRecipient indexed,
    recoveryActionId, amount, cumulativeRecovered, remainingOutstanding,
)

RipeSurplusRecovered(
    governanceRecipient indexed, amount, remainingSurplus,
)

EpochInitialized(
    epoch indexed, controllerBasePayoutRate, basePayoutRate, paymentCap,
    minPaymentAmount, timingEligible, epochConfigVersion, rateSource, rateNonce,
)

EpochRolled(
    fromEpoch indexed, toEpoch indexed, oldBasePayoutRate,
    controllerBasePayoutRate, basePayoutRate, newPaymentCap,
    newMinPaymentAmount, previousAcceptedPayment, previousPaymentCap,
    previousPaymentWeightedLateness, previousTimingEligible, utilizationBps,
    effectivePriceAdjustmentBps, decaySteps, epochConfigVersion, rateSource,
    rateNonce,
)

ReserveEngineConfigSet(
    currentConfigVersion indexed, configHash,
)

ReserveEngineRunTermsSet(
    runTermsVersion indexed, runTermsHash,
)

ReserveEngineStarted(
    runId indexed, runRegistryVersion indexed, genesisBlock,
    currentConfigVersion, runTermsVersion,
)

ReserveEngineStopped(
    runId indexed, resultingClosureNonce,
)

ReserveEngineEnabledSet(
    isEngineEnabled, resultingClosureNonce,
)

ReserveEngineClosureAdvanced(
    operation indexed, resultingClosureNonce,
)

ReserveEngineLimitsSet(
    activeLineageAllocationLimit, activeOutstandingRipeLimit,
    resultingCapacityReductionNonce,
)

RateOverrideInstalled(
    targetEpoch indexed, targetBasePayoutRate, runId, runRegistryVersion,
    installedConfigVersion, closureNonce, installedRateNonce,
)

RateOverrideApplied(
    epoch indexed, controllerBasePayoutRate, basePayoutRate,
    observedRateNonce, resultingRateNonce, overrideApplicationsThisRun,
)

RateOverrideTerminated(
    targetEpoch indexed, targetBasePayoutRate, reason: uint8,
    observedRateNonce, resultingRateNonce,
)
```

Use fixed recovery terminal reasons: `1 = BENEFICIARY_ACTIVITY`,
`2 = CANCELLED`, `3 = EXPIRED`, `4 = POSITION_STALE`, and
`5 = GOVERNANCE_ROTATED`. Configuration and run-term events carry the new
version and `keccak256(_abi_encode(struct fields...))` in the declared field
order. Lifecycle and limit events carry the resulting nonce and exact new
values. Use closure operation values `1 = PAUSE`, `2 = DISABLE`, and `3 = STOP`.
Use override terminal reasons `1 = CANCELLED`, `2 = MISSED`,
`3 = DEVIATION_INVALID`, `4 = CONFIG_CHANGED`, `5 = PAUSED`, `6 = DISABLED`,
`7 = STOPPED`, and `8 = NEW_RUN`. Exactly one terminal event advances the nonce
for each installed override.

For the Engine events above, untyped numeric fields are `uint256` except
`rateSource`, `reason`, and `operation`, which are `uint8`. Fields named
`timingEligible`, `previousTimingEligible`, and `isEngineEnabled` are `bool`;
`beneficiary`, `paymentToken`, `proceedsRecipient`, and
`governanceRecipient` are `address`; and fields ending in `Hash` are `bytes32`.

Use this exact public user-mutator surface:

```text
acquireRipe(
    paymentAmount,
    selectedFullVestingBlocks,
    constraints: AcquisitionConstraints,
) -> (positionId, totalAllocation)
claimVestedRipe(positionId) -> uint256
```

Use this exact governance/admin mutator surface; omitted return values mean no
return:

```text
setConfig(newConfig, expectedCurrentConfigVersion)
setRunTerms(newRunTerms, expectedRunTermsVersion)
setEngineEnabled(shouldEnable, expectedClosureNonce)
setActiveLimits(
    newLineageLimit,
    newOutstandingLimit,
    expectedCurrentLineageLimit,
    expectedCurrentOutstandingLimit,
    expectedCapacityReductionNonce,
)
start(
    genesisBlock,
    expectedRegistryVersion,
    expectedCurrentConfigVersion,
    expectedRunTermsVersion,
    expectedClosureNonce,
)
stop()
installRateOverride(
    targetBasePayoutRate,
    targetEpoch,
    expectedRunId,
    expectedRunRegistryVersion,
    expectedCurrentConfigVersion,
    expectedClosureNonce,
    expectedRateNonce,
)
cancelRateOverride()
queueRipeRecovery(positionId, amount) -> uint256
executeRipeRecovery(recoveryActionId) -> bool
cancelRipeRecovery(recoveryActionId) -> bool
recoverRipeSurplus(amount) -> bool
pause(shouldPause)
recoverFunds(recipient, asset)
recoverFundsMany(recipient, assets: DynArray[address, 20])
```

Every untyped numeric argument above is `uint256`; booleans and addresses are
named by role. Do not add overlapping aliases for the same action.

The shared interface's callable declarations are closed. It must declare the
shared structs and exactly the Engine calls Foxtrot makes: the following
governance/admin mutators (with the signatures and returns above), followed by
the validation, evidence, and identity views in the next block. It must not
grow into a second public-user or generic Department interface.

```text
setConfig
setRunTerms
setEngineEnabled
setActiveLimits
start
stop
installRateOverride
cancelRateOverride
queueRipeRecovery
executeRipeRecovery
cancelRipeRecovery
recoverRipeSurplus
pause
```

The exact Foxtrot-facing views are:

```text
isValidConfig(config) -> bool
isValidRunTerms(runTerms) -> bool
isValidStart(genesisBlock) -> bool
isValidRateOverride(targetBasePayoutRate, targetEpoch) -> bool
canCancelRateOverride() -> bool
isValidActiveLimits(newLineageLimit, newOutstandingLimit) -> bool
getConfig() -> ReserveEngineConfig
getRunTerms() -> ReserveEngineRunTerms
getActiveRunTerms() -> ReserveEngineRunTerms
configHash() -> bytes32
runTermsHash() -> bytes32
currentConfigVersion() -> uint256
runTermsVersion() -> uint256
runId() -> uint256
runRegistryVersion() -> uint256
closureNonce() -> uint256
capacityReductionNonce() -> uint256
rateNonce() -> uint256
isPaused() -> bool
isEngineEnabled() -> bool
isRunning() -> bool
activeLineageAllocationLimit() -> uint256
activeOutstandingRipeLimit() -> uint256
escrowSurplus() -> uint256
installedRateOverride() -> RateOverride
epochState() -> EpochSnapshot
genesisBlock() -> uint256
paymentToken() -> address
paymentDecimals() -> uint8
paymentScale() -> uint256
pinnedRipe() -> address
ripeHq() -> address
pendingRipeRecoveries(recoveryActionId) -> PendingRipeRecovery
hasPendingRipeRecovery(recoveryActionId) -> bool
```

After `queueRipeRecovery`, Foxtrot reads the returned action's
`pendingRipeRecoveries` value to bind the route event's beneficiary and amount.
It does not need `positions()` in the shared interface.

## 6. `SwitchboardFoxtrot.vy`

Keep the contract name `SwitchboardFoxtrot`. Import the new Engine interface,
remove the duplicated Lane interface/structs, rename every feature-specific
method/action/storage field/event, and retain dynamic slot-26 resolution.

Preserve the existing four-argument constructor ABI. Initialize governance as
today, but remove the zero-delay setup window by calling:

```text
timeLock.__init__(
    _minConfigTimeLock,
    _maxConfigTimeLock,
    _minConfigTimeLock,
    _maxConfigTimeLock,
)
```

Production min/max values remain deployment calibration. Do not add a fifth
constructor argument or rely on `setActionTimeLockAfterSetup`.

Every ordinary queued Foxtrot action stores the exact target Engine resolved at
queue time and the current slot-26 registry version. At execution, require the
same address and version still occupy slot 26 and the payload-specific captured
run/config/run-terms/closure/capacity/rate identities remain valid. A
replacement, slot-26 registry disable, A-to-B-to-A restoration, or other
objective stale condition consumes and clears the mature action exactly once,
emits a reason, and returns `False`; it must not mutate the replacement Engine
or remain wedged.
Instance-local surplus and position recovery are the explicit exceptions below.

Ordinary pending actions do not snapshot local or RipeHq governance generations.
They cannot self-execute: a currently authorized governor must affirmatively
execute or cancel them. This preserves the repository's ordinary action-
inheritance policy without two extra nonce domains. Position recovery is
different because its Engine action freezes a transfer recipient and therefore
snapshots the RipeHq governance generation.

Use this action split:

| Operation | Foxtrot treatment |
|---|---|
| Full controller config | Timelocked, prospective |
| Payment token or run terms | Timelocked, stopped-only |
| Start or reopen/enable | Timelocked positive action |
| Raise lineage/outstanding limits | Timelocked positive action |
| Install named-epoch override | Timelocked; only one pending install |
| Recover RIPE surplus | Timelocked; Engine rechecks live surplus |
| Pause, disable, or stop | Immediate de-escalation |
| Lower live limits | Immediate de-escalation |
| Cancel pending action or installed override | Immediate de-escalation |
| Queue/execute/cancel position recovery | Direct wrapper; Engine notice supplies the mandatory delay |

Do not add a second Foxtrot delay on position recovery. The Engine queue is the
single mandatory notice and remains effective regardless of which registered
switchboard calls it.

Maintain `knownReserveEngines: HashMap[address, bool]` and
`knownEngineRegistryVersion: HashMap[address, uint256]`. Whenever a state-
changing Foxtrot method resolves an address as the current slot-26 Engine, mark
that address known and record the observed registry version. There is no
separate recognition workflow. An explicit recovery target is admissible only
if it was recorded while current and still reports this Foxtrot's RipeHq.

A retired Engine that Foxtrot never recorded while current is intentionally
ineligible for Foxtrot's retired-target path. It must instead be administered
through another currently registered switchboard capable of deliberately
targeting that instance. The Engine's applicable safeguards still apply:
dormancy and notice for position recovery, and the live-surplus bound plus
canonical-governance recipient for surplus recovery. Do not add retroactive
Foxtrot recognition. This is why the Phase 4 replacement procedure must make
the outgoing Engine known before changing slot 26.

Position-recovery queue and surplus-recovery methods accept an explicit known
Engine target. This allows newly matured positions and later surplus on a
retired instance to remain administrable. Neither operation requires that the
target still occupy slot 26. Surplus recovery remains timelocked; position
recovery relies on the Engine's dormancy and notice.

At surplus queue time require `amount > 0` and
`amount <= targetEngine.escrowSurplus()`. Recheck both after maturity; if the
live surplus has fallen below the amount, consume the action as stale without a
transfer.

When the position-recovery queue wrapper calls the explicit target, allocate a
Foxtrot recovery-route ID and store `(targetEngine,
engineRecoveryActionId)`. Execute and cancel wrappers take the Foxtrot route ID
and call the captured Engine even if slot 26 has since been replaced; they must
never resolve a new Engine and reuse the old numeric ID.

Before forwarding execute or cancel, query
`targetEngine.hasPendingRipeRecovery(engineRecoveryActionId)`. If a validly
issued route points to an already-cleared action, close the route without
calling the Engine. After an Engine `False` result, retain the route while the
action remains pending because it is immature or coverage-blocked; otherwise
clear it as terminal. This routing record is not a second timelock.

The Foxtrot interface must cover all Engine mutators and validation views. Clear
each `actionType` and its typed payload on execution, cancellation, expiry, or
stale no-op.

Use this exact `executePendingAction` order:

1. Load the action type and typed payload. Reject ID `0`; return `False` for an
   unknown or already-terminal ID.
2. If expired, cancel the TimeLock row, clear action type and payload, emit
   `EXPIRED`, and return `False`.
3. If not yet confirmable, return `False` without mutation.
4. Evaluate target address/version, captured identities, action direction, and
   live validity using views. For surplus, recheck the explicit known target and
   live amount. Treat an `ENABLE` whose target is already enabled, an `UNPAUSE`
   whose target is already unpaused, and a `START` whose target is already
   running as objectively stale lifecycle no-ops.
5. If objectively stale, consume the now-mature TimeLock row, clear action type
   and payload, emit `STALE`, and return `False`.
6. Otherwise confirm the TimeLock, clear action type and payload, and execute
   the Engine call. For every successful non-surplus call, and a surplus call
   returning `True`, emit `EXECUTED` and return `True`. If
   `recoverRipeSurplus` returns `False`, emit `STALE` and return `False`; never
   emit `EXECUTED` for that branch.
7. An unexpected Engine or token revert reverts the entire transaction,
   including the TimeLock/payload clearing, so the action remains available for
   retry, cancellation, or expiry. Do not claim that a post-confirm revert
   permanently deletes the TimeLock row.

Use this exact `cancelPendingAction` order:

1. Reject ID `0`; return `False` for an unknown or already-terminal ID.
2. Record whether the still-pending TimeLock row is expired, then cancel that
   row. Clear the action type and its exact typed payload in the same
   transaction.
3. If this is the action referenced by `pendingRateOverrideActionId`, clear that
   pointer too.
4. Emit `EXPIRED` when the row was already expired, otherwise emit `CANCELLED`.
   Return `True` because an issued pending action was closed in either case.

Cancellation does not call the Engine and does not require the target or any
captured identity to remain current. An unexpected TimeLock inconsistency
reverts the transaction rather than leaving half-cleared state.

Do not change ordinary Engine governance mutators into Boolean no-ops. Foxtrot
preclassifies objective staleness synchronously before calling their existing
reverting ABI.

Use this exact Foxtrot external surface in addition to the inherited governance
and timelock ABI:

```text
setReserveEngineConfig(config) -> uint256                    # Foxtrot action ID
setReserveEngineRunTerms(runTerms) -> uint256                # Foxtrot action ID
enableReserveEngine() -> uint256                             # Foxtrot action ID
disableReserveEngine()
startReserveEngine(genesisBlock) -> uint256                  # Foxtrot action ID
stopReserveEngine()
pauseReserveEngine()
unpauseReserveEngine() -> uint256                            # Foxtrot action ID
raiseReserveEngineLimits(newLineageLimit, newOutstandingLimit) -> uint256
lowerReserveEngineLimits(newLineageLimit, newOutstandingLimit)
setReserveEngineRateOverride(targetBasePayoutRate, targetEpoch) -> uint256
cancelReserveEngineRateOverride()
recoverReserveEngineRipeSurplus(targetEngine, amount) -> uint256 # action ID
queueReserveEngineRipeRecovery(targetEngine, positionId, amount) -> uint256
executeReserveEngineRipeRecovery(routeId) -> bool
cancelReserveEngineRipeRecovery(routeId) -> bool
executePendingAction(actionId) -> bool
cancelPendingAction(actionId) -> bool
knownReserveEngines(targetEngine) -> bool
knownEngineRegistryVersion(targetEngine) -> uint256
pendingRateOverrideActionId() -> uint256
ripeRecoveryRoutes(routeId) -> RipeRecoveryRoute
```

Arguments named `targetEngine` are `address`; every other untyped argument is
`uint256`. Required queued action types are
`CONFIG`, `RUN_TERMS`, `ENABLE`, `START`, `UNPAUSE`, `LIMIT_RAISE`,
`RATE_OVERRIDE_INSTALL`, and `RIPE_SURPLUS_RECOVERY`. Each typed payload stores
the target Engine and the exact current values/nonces its Engine call expects.

Represent the action type as `uint8` with fixed values in that order: `1`
through `8`; `0` means no action.

Store `pendingRateOverrideActionId: uint256`. A new install queue requires it to
be zero. Successful execution, cancellation, expiry, and stale termination clear
it; action IDs themselves remain never-reused. At queue time,
`raiseReserveEngineLimits` must require the component-wise raise predicate and
`lowerReserveEngineLimits` must require the component-wise reduction predicate.
Never allow a timelocked raise wrapper to carry a reduction tuple.

Use these exact typed queued-payload fields and order. A field named
`targetRegistryVersion` is the slot version observed when `targetEngine` was
current; ordinary actions recheck it against the live slot, while retired-
Engine surplus recovery uses it only as recorded identity evidence.
Store each payload type in its own public `HashMap[actionId, payload]` and clear
that exact row on every terminal path.

```text
ConfigAction:
    targetEngine: address
    targetRegistryVersion: uint256
    newConfig: ReserveEngineConfig
    expectedCurrentConfigVersion: uint256
    expectedRunTermsVersion: uint256
    expectedClosureNonce: uint256

RunTermsAction:
    targetEngine: address
    targetRegistryVersion: uint256
    newRunTerms: ReserveEngineRunTerms
    expectedCurrentConfigVersion: uint256
    expectedRunTermsVersion: uint256
    expectedClosureNonce: uint256

EnableAction:
    targetEngine: address
    targetRegistryVersion: uint256
    expectedClosureNonce: uint256

StartAction:
    targetEngine: address
    targetRegistryVersion: uint256
    genesisBlock: uint256
    expectedCurrentConfigVersion: uint256
    expectedRunTermsVersion: uint256
    expectedClosureNonce: uint256

UnpauseAction:
    targetEngine: address
    targetRegistryVersion: uint256
    expectedClosureNonce: uint256

LimitRaiseAction:
    targetEngine: address
    targetRegistryVersion: uint256
    newLineageLimit: uint256
    newOutstandingLimit: uint256
    expectedCurrentLineageLimit: uint256
    expectedCurrentOutstandingLimit: uint256
    expectedCapacityReductionNonce: uint256
    expectedClosureNonce: uint256

RateOverrideInstallAction:
    targetEngine: address
    targetRegistryVersion: uint256
    targetBasePayoutRate: uint256
    targetEpoch: uint256
    expectedRunId: uint256
    expectedRunRegistryVersion: uint256
    expectedCurrentConfigVersion: uint256
    expectedClosureNonce: uint256
    expectedRateNonce: uint256

RipeSurplusRecoveryAction:
    targetEngine: address
    targetRegistryVersion: uint256
    amount: uint256
```

The payload hash is exactly
`keccak256(_abi_encode(actionType, typed payload fields...))` in the field order
above. Do not hash packed or ad hoc encodings.

Use this exact position-recovery route shape:

```text
struct RipeRecoveryRoute:
    targetEngine: address
    engineRecoveryActionId: uint256
```

Route IDs start at `1`, are never reused, and are separate from Foxtrot timelock
action IDs. Do not preserve legacy method or event aliases.

Foxtrot must emit:

```text
ReserveEngineActionQueued(
    actionId indexed, targetEngine indexed, actionType: uint8 indexed,
    targetRegistryVersion, confirmationBlock, payloadHash,
)

ReserveEngineActionTerminated(
    actionId indexed, targetEngine indexed, actionType: uint8 indexed,
    outcome: uint8,
)

ReserveEngineRecoveryRouteCreated(
    routeId indexed, targetEngine indexed, positionId indexed,
    engineRecoveryActionId, beneficiary, amount,
)

ReserveEngineRecoveryRouteClosed(
    routeId indexed, targetEngine indexed, engineRecoveryActionId,
    outcome: uint8,
)

ReserveEngineConfigQueued(
    actionId indexed, expectedCurrentConfigVersion,
    expectedRunTermsVersion, expectedClosureNonce, configHash,
)

ReserveEngineRunTermsQueued(
    actionId indexed, expectedCurrentConfigVersion,
    expectedRunTermsVersion, expectedClosureNonce, runTermsHash,
)

ReserveEngineLifecycleQueued(
    actionId indexed, operation: uint8, genesisBlock,
    expectedCurrentConfigVersion, expectedRunTermsVersion,
    expectedClosureNonce,
)

ReserveEngineLimitRaiseQueued(
    actionId indexed, newLineageLimit, newOutstandingLimit,
    expectedCurrentLineageLimit, expectedCurrentOutstandingLimit,
    expectedCapacityReductionNonce, expectedClosureNonce,
)

ReserveEngineRateOverrideQueued(
    actionId indexed, targetEpoch indexed, targetBasePayoutRate,
    expectedRunId, expectedRunRegistryVersion,
    expectedCurrentConfigVersion, expectedClosureNonce, expectedRateNonce,
)

ReserveEngineRipeSurplusRecoveryQueued(
    actionId indexed, targetEngine indexed, amount,
)
```

Use `1 = EXECUTED`, `2 = CANCELLED`, `3 = EXPIRED`, and `4 = STALE` for
ordinary action outcomes; recovery routes may additionally use `5 = STILL_LIVE`
internally but must not emit a closure event until the route is actually clear.
Use lifecycle queue operations `1 = ENABLE`, `2 = START`, and `3 = UNPAUSE`.

For the Foxtrot events above, untyped numeric fields are `uint256`. Fields named
`targetEngine` and `beneficiary` are `address`; fields ending in `Hash` are
`bytes32`; and `actionType`, `outcome`, and `operation` are `uint8`.

The Engine's any-switchboard authorization is deliberate. Foxtrot's ordinary
timelocks are the supported governance route, not an assertion that other
registered switchboards are technically incapable of calling the same Engine
mutators. Position recovery is different only because its notice is enforced by
the Engine itself.

## 7. `Addys.vy` and `RipeReserveEngine.vyi`

In `Addys.vy` make only these semantic-preserving changes:

```text
INSTANT_BOND_LANE_ID       -> RIPE_RESERVE_ENGINE_ID
_getInstantBondLaneId     -> _getRipeReserveEngineId
_getInstantBondLaneAddr   -> _getRipeReserveEngineAddr
```

Retain numeric registry ID `26`. Do not keep deprecated aliases; the feature is
undeployed and this is an intentional ABI/source rename.

Do not widen `Addys.vy` merely to expose the registry version. Engine and
Foxtrot may each use a narrow local RipeHq interface for the already-exported
`getAddrInfo(26)` view with the existing exact return shape:

```text
AddressInfo:
    addr: address
    version: uint256
    lastModified: uint256
    description: String[64]
```

No `RipeHq.vy` or AddressRegistry change is required.

`interfaces/RipeReserveEngine.vyi` is the authoritative ABI used by Foxtrot. It
must define the shared config/action structs and only the Engine methods Foxtrot
calls or validates. Do not modify `Department.vyi` and do not add a speculative
interface hierarchy. Import it under an explicit alias such as `ire` wherever
the module name would otherwise clash with the implementing contract name.

## 8. Source-level invariants

The Phase 1 source must make these relationships apparent and enforce them at
every relevant transition:

```text
position.claimed + position.recovered <= position.allocation

totalClaimed + totalRecovered <= totalAllocated

totalOutstandingRipe =
    totalAllocated - totalClaimed - totalRecovered

positionOutstanding =
    position.allocation - position.claimed - position.recovered

lineageAllocated = priorLineageAllocated + totalAllocated

RIPE.balanceOf(engine) >= totalOutstandingRipe
    after every successful Engine-controlled RIPE transition
```

Transition effects:

| Transition | Engine RIPE balance | Outstanding RIPE | Lifetime allocation |
|---|---:|---:|---:|
| Acquisition | `+totalAllocation` | `+totalAllocation` | `+totalAllocation` |
| Claim | `-amount` | `-amount` | unchanged |
| Position recovery | `-amount` | `-amount` | unchanged |
| Surplus recovery | `-amount` | unchanged | unchanged |

Additional non-negotiable properties:

- every external state-changing user/token path is nonreentrant;
- internal effects precede external interactions and failures roll back atomically;
- all token amounts and schedule additions are overflow-safe;
- exact payment, mint, claim, and RIPE-recovery deltas are checked;
- no acquisition can create position ID zero or a zero/uneconomic allocation;
- no duration selection bypasses the all-in payout ceiling;
- no adjusted allocation bypasses a RIPE-denominated cap;
- no full config action re-enables a closed Engine;
- no stale run, quote, acquisition, or ordinary action survives a slot-version
  change or A-to-B-to-A restoration;
- every committed epoch preserves both its ordinary controller rate and final
  base rate;
- every successful pause, disable, and stop transition permanently advances
  `closureNonce`;
- no registered switchboard can bypass position-recovery dormancy or notice;
- no generic recovery path accepts pinned RIPE;
- known retired Engines remain available for claims and specialized recovery;
- no claim checks acquisition pause/enable/running state;
- no blacklist, burn, beneficiary rescue, token receipt, per-buyer cap, or oracle
  machinery is introduced.

## 9. Phase 1 completion, review PR, and mandatory stop

When the five allowed Git pathnames have produced the four resulting source
files:

1. Run `git diff --check` for tracked changes. Because the new Engine and
   interface remain untracked, also run a read-only trailing-whitespace search
   over all five allowed Git pathnames. Do not stage files merely to make Git
   inspect them.
2. Inspect `git status --short`, `git diff --stat`, the tracked source diff, and
   each new file in full. Remember that ordinary `git diff` and
   `git diff --stat` omit untracked files.
3. Confirm no path outside the Phase 1 allowlist changed.
4. Search active contract/interface source for stale `InstantBond`, `buyNow`, and
   old slot/getter names. Historical docs and untouched tests are intentionally
   stale and must not be edited.
5. If there is any source-level blocker, unexpected changed path, or failed
   check, stop without committing, pushing, or opening a PR and report it. Do
   not weaken the guide or expand scope to force publication.
6. Use this read-only query to verify the remote base:

   ```sh
   git ls-remote --exit-code --heads origin refs/heads/instant-bond-lane
   ```

   Its OID must equal `BASE_COMMIT`. If it differs or cannot be verified, stop
   before publication and report it. Do not fetch into, merge, rebase, or
   otherwise rewrite the implementation to follow a moved base without new
   owner direction.
7. If and only if the checks and remote-base pin pass, stage exactly these five
   Git pathnames:

   ```sh
   git add -- \
     contracts/core/InstantBondLane.vy \
     contracts/core/RipeReserveEngine.vy \
     contracts/config/SwitchboardFoxtrot.vy \
     contracts/modules/Addys.vy \
     interfaces/RipeReserveEngine.vyi
   ```

   Verify with `git diff --cached --name-status --no-renames` that the staged
   result is exactly one deletion, two modifications, and two additions across
   those paths, with no guide, test, artifact, or generated file. Run
   `git diff --cached --check` and inspect the complete staged diff. Then create
   one commit with subject:

   ```text
   feat: add RIPE Reserve Engine contracts
   ```

   Confirm the post-commit worktree is clean and the commit is the only commit
   after `BASE_COMMIT`.
8. Push only `codex/ripe-reserve-engine-contracts-phase1`, without force, and
   verify the remote head OID exactly equals the local commit. Then open one
   **draft pull request** with:

   ```text
   base:  instant-bond-lane
   head:  codex/ripe-reserve-engine-contracts-phase1
   title: feat: add RIPE Reserve Engine contracts
   ```

   The PR body must state the pinned baseline commit/tree, summarize the four
   resulting source files and principal invariants, list the five changed Git
   pathnames, request owner source review, and include this exact prominent
   statement: **“Source-only; not compiled or tested.”** It must also say that
   tests, ABI regeneration, size qualification, and integration remain deferred
   until owner approval.
9. Verify the created PR is open and draft; its base name is exactly
   `instant-bond-lane`; its base OID equals `BASE_COMMIT`; its head name is
   exactly `codex/ripe-reserve-engine-contracts-phase1`; and its head OID equals
   the local commit. Verify the union of each PR file's `filename` and optional
   `previous_filename` is exactly the five-path allowlist. GitHub may represent
   the Lane deletion plus Engine addition as one rename, yielding four file
   objects; that is valid only when the rename entry has
   `contracts/core/RipeReserveEngine.vy` as `filename` and
   `contracts/core/InstantBondLane.vy` as `previous_filename`, with the other
   three resulting files and no out-of-scope path.

   If an existing PR for that head is returned, do not create a duplicate;
   verify it satisfies the same requirements. Never retarget the PR to `master`,
   `main`, or another branch. Automatic PR CI may start, but do not wait for it,
   do not treat it as Phase 1 evidence, and do not change code in response to it.
10. Report:

   - implementation branch and worktree;
   - exact baseline commit and tree;
   - local commit hash and matching remote-head OID;
   - draft PR number, URL, state, base name/OID, and head name/OID;
   - changed paths;
   - concise behavior/invariant summary;
   - assumptions or source-level blockers;
   - tracked, staged, and all-five-path whitespace-check results;
   - the exact statement: **“Source-only; not compiled or tested.”**

Then stop for owner review with the PR left open as a draft. Do not repair
tests, compile failures, generated artifacts, CI, documentation, or deployment
files; do not add another commit, mark the PR ready, merge, or publish anything
else without new owner direction. The repository is not yet test-green,
ABI-synchronized, size-qualified, merge-ready, deployable, or activatable.

## 10. Later phases — not yet authorized

These phases exist so Phase 1 source does not make later requirements invisible.
They require new owner authorization.

### Phase 2: tests and contract validation

After the owner approves the Phase 1 source diff in the draft PR:

- rename/rewrite the focused contract and Foxtrot tests;
- add vesting boundary, grid, adjustment, all-in ceiling, quote-binding,
  controller, override, coverage, recovery-race, replacement-target, reentrancy,
  and exact-transfer cases;
- add stateful conservation checks over acquisition, claim, position recovery,
  surplus recovery, and recapitalization;
- test alternate registered switchboards cannot bypass the Engine recovery
  notice;
- distinguish address equality from slot-version identity, including an
  A-to-B-to-A restoration that cannot revive an old run, quote, or action;
- cover new recovery and surplus queues against known retired Engines;
- cover pause/unpause, disable/enable, and stop/start closure-nonce invalidation;
- cover immature, expired, objectively stale, successful, and unexpected-revert
  Foxtrot action paths, including current-governance adoption/cancellation after
  governance rotation;
- compile only the affected contracts, then measure both deployed runtime sizes
  against EIP-170 and report exact headroom;
- run focused tests first; do not broaden into the full suite without approval.

Production-grid tests must exercise the same on-chain adjacent-pair predicate,
every permitted duration, the minimum base allocation and larger allocations,
weak adjustment monotonicity, and strictly decreasing average linear release
velocity (while permitting tied individual-block increments). Re-run the exact
qualifier for the hash of every proposed production run terms before any initial
or later `start`; the continuous inequality alone is not sufficient.

Phase 2 may fix owner-approved defects in the five Phase 1 Git pathnames, but it
must not silently redesign the accepted mechanism.

### Phase 3: repository integration

Only after contract and test approval:

- regenerate ABI files after deleting the stale `InstantBondLane.json` artifact;
- update activation schema, qualifier, controller simulator, deployment inputs,
  CI/workflow coverage, SDK/indexer surfaces, and active documentation;
- preserve the historical design-review directory as historical evidence;
- add a normal lean CI shard for the Reserve Engine tests rather than relying
  only on a feature workflow.

### Phase 4: production qualification and activation

Deployment, slot registration, mint authorization, funding, configuration, and
activation remain separately authorized operations. Before them, require an
approved reference-price/liquidity method, worst-case max-adjustment issuance
analysis, combined Engine/block-reward issuance reporting, projected unlock
cohorts, and monitoring/close thresholds. BondRoom remains disabled by default;
coexistence requires a separately approved aggregate issuance, relative-pricing,
monitoring, and close-priority policy. A replacement must stop/disable the old
instance, remove its mint authority, preserve its RIPE balance, claims, and
specialized recovery, and record it as known in Foxtrot before slot replacement.
Re-registration never revives its old run.

## 11. Values intentionally left for calibration

The architecture is complete. These values are not:

- approved payment asset and its token qualification;
- exact claim cliff and the immutable minimum cliff floor;
- `Dmin`, `Dmax`, and duration step within the fixed 256-point maximum;
- configured duration adjustment below the 100% hard ceiling;
- target-chain block count representing the 90-day recovery dormancy;
- recovery notice and recovery-action expiry;
- minimum/maximum epoch length, production epoch length, and genesis lead;
- minimum payment, epoch payment cap, and `MIN_BASE_ALLOCATION`;
- seed/base/all-in payout rates;
- utilization bands, up/down steps, decay, and configured maximum decay epochs
  at or below the fixed code bound of `32`;
- override deviation, lead, and per-run application limit;
- hard lineage cap, truthful prior-lineage allocation, and live lineage and
  outstanding-RIPE limits;
- Foxtrot timelock and expiration;
- reference-price/liquidity evidence, maximum acceptable vest-adjusted economic
  incentive, and monitoring thresholds;
- production block-time assumptions used only for date estimates.

Keep these as explicit immutable, configuration, deployment, or activation
inputs as appropriate. Do not insert illustrative values and present them as
approved production settings.
