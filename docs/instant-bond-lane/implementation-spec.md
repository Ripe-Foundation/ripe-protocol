# Instant Bond Lane — Implementation Specification

**Mechanism version:** v2 · **Specification revision:** 20

**Status:** Owner-approved implementation specification. Economic calibration remains
a deployment input. Revision-20 local commit and branch push are authorized as bounded
in §20; merge, pull-request publication, deployment, production configuration, RIPE
minting, and activation are not.

**Prepared:** 5 August 2026 · **Revised:** 11 August 2026 (dynamic demand controller,
next-successful-rollover rate override, implementation reconciliation, owner-approved
runtime ceilings, and final revision-20 local evidence)

**Companion:** pricing rationale in [`pricing-design.md`](pricing-design.md). This
specification is authoritative wherever the documents differ.

**Worktree:** `ripe-protocol-instant-bond-lane`, branch `instant-bond-lane`.
Revision 20 began from committed feature baseline
`ad782c80b2f4bfa73d7dcd8c9c4979903b767b96`, tree
`dc64aab1a63c48ab311b9539f3043df7c17d3788`, which incorporates RH baseline
`be6e4e9805e9b499b10f61cd219c555e62b43857`.

## Owner-confirmed product decisions

1. The lane has its own deterministic epoch clock; it does not follow Bond Room or
   Ledger epochs.
2. A buyer may receive RIPE unlocked or request a flexible lock with a linear bonus.
3. Fully empty epochs use bounded **DECAY**, including epochs in which the lane was
   paused, disabled, or out of mint budget.
4. Economic parameters are governed through a timelocked switchboard, like the bonds.
5. Fund recovery uses inherited `DeptBasics.recoverFunds` functions.
6. Purchases remain available during bad debt and do not participate in bad-debt
   repayment accounting.
7. The buyer is always the RIPE recipient; delegated purchases are out of scope.
8. `EPOCH_LENGTH` is immutable. All other economic parameters are governed.
9. Lock-duration boundaries come from the live RIPE gov-vault configuration. The
   lane owns only the bonus magnitude.
10. The lane has no hard sunset; governance disables it with `canBuyNow`, pause, or
    deregistration.
11. The payment asset is a canonical dollar-denominated ERC-20 selected at deployment
    and may not be the registered RIPE token; the lane derives and stores its immutable
    decimal scale rather than assuming USDC or a fixed decimal count.
12. Purchases have a governed, epoch-snapshotted minimum payment amount of at least one
    whole payment token.
13. Purchases are permissionless and always settle to `msg.sender`; the lane does not
    add a buyer allowlist.
14. The complete current epoch snapshot is exposed through public getters. Epoch
    identifiers and `pricingConfigVersion`—rather than `liveConfigVersion`—are indexed
    consistently in lifecycle and purchase events. The owner explicitly ratified that
    final topic allocation during the historical Phase 2 review; `liveConfigVersion`
    remains present as non-indexed purchase-event data.
15. RIPE is the sole hardcoded payment-token exclusion because accepting the minted
    asset would create a self-referential mint path. GREEN may be a legitimate
    dollar-stable payment asset. Savings GREEN and other yield-bearing or
    value-accruing wrappers are not assumed to remain worth one dollar per token and
    require explicit valuation-aware calibration and owner approval; v2 deliberately
    does not hardcode a chain-specific asset allowlist.
16. Locked settlement follows the live `MissionControl.coreRipeGovVaultId()` rather
    than a hardcoded vault number. Preview remains narrow and does not bind that
    governance-controlled destination into the quote ABI.
17. Payment settlement succeeds only when Endaoment Funds receives the exact requested
    amount. Nonexact transfer semantics fail closed and are not normalized or credited.
18. High-utilization price increases use governed minimum and maximum steps. The step
    is determined by both utilization above the high threshold and the
    payment-amount-weighted purchase timing within the epoch. A full first-block epoch
    receives the maximum step; a full last-block epoch receives the minimum step.
19. Low-utilization price decreases use governed minimum and maximum steps selected by
    utilization severity. Empty skipped epochs continue to use the single bounded
    `decayBps` step and do not invent a purchase-speed signal.
20. A partially elapsed first initialized epoch is timing-ineligible unless its first
    successful purchase occurs at deterministic epoch offset zero. Every later stored
    epoch is timing-eligible. The lane does not track pause-adjusted or availability-
    adjusted time.
21. Governance may install one exact base-rate override. It applies at the first later
    **successful** rollover, regardless of how many calendar epochs have elapsed, and
    is neither consumed by preview nor by a reverted purchase. There is no target
    epoch, execution window, maximum lead, or missed-target decay rule.
22. Installing or cancelling an override is independently timelocked through
    `SwitchboardFoxtrot`. Any successful full config replacement invalidates an
    installed override. Override operations use independent optimistic versioning.
23. The lane retains the protocol-standard trust boundary: any currently registered
    switchboard may call its governance mutators. Foxtrot is the intended timelocked
    route, not an immutable lane-side authorization pin. A Foxtrot-only binding would
    require a separate circular-deployment/bootstrap design.

## Final engineering decisions

- The price floor protects the **all-in payout after the maximum lock bonus**.
- Initialization is lazy and deterministic: the first successful `buyNow` at or
  after genesis initializes the current epoch. `previewBuyNow` simulates the same
  state read-only.
- There is no reactivation/rebaseline branch. An unavailable gap is ordinary empty
  time and receives at most `maxDecayEpochs` decay steps at the next rollover.
- Config staleness is enforced in the lane itself with `expectedVersion`.
- Every epoch snapshots the version that supplied its rate, cap, minimum payment, and
  maximum bonus.
- `MIN_BASE_RATE = 10_000` is an engineering liveness floor that prevents inverse-rate
  recovery from becoming an integer fixed point. It is not an economic calibration
  substitute or a complete defense against mis-scaled governance inputs.
- A low-utilization step may not exceed the empty-epoch decay step:
  `maxDownBps <= decayBps`.
- Dynamic up/down ranges satisfy the ordering and anti-round-trip constraints in
  §3.3. For configurations admitted by the stricter revision-20 validation, equal
  endpoints recover the revision-19 fixed-step arithmetic exactly.
- Purchase timing uses integer, amount-weighted lateness. Splitting, merging, or
  reordering same-block purchases cannot change the signal.
- The ordinary controller result is always computed at rollover. An installed rate
  override replaces only the final stored rate; the counterfactual controller rate is
  emitted for auditability.
- Override installation, application, installed cancellation, and config invalidation
  each advance `overrideVersion` exactly once. Queue cancellation and expiry do not.
- Config events emit all fields rather than only a hash.
- Rollover events emit the complete new epoch snapshot as well as the previous epoch's
  utilization inputs.
- Pricing config versions are indexed consistently across initialization, rollover,
  and purchase events for monitoring.
- Preview remains a lane-side quote with a boolean availability signal. It does not add
  a reason-code ABI or attempt to preflight every downstream dependency.
- Governance uses a small dedicated `SwitchboardFoxtrot`; no pre-existing protocol
  contract outside the two feature contracts is modified. `Foxtrot` follows the
  repository's NATO phonetic sequence after the already-existing `SwitchboardEcho`.
- Delivery remains owner-gated. The owner authorized revision-20 source, documentation,
  tests, generated ABI updates, local validation, commit, and push on the existing
  `instant-bond-lane` branch. That authority does not include merge, pull-request
  publication, Phase 3 fork/testnet work, deployment, configuration, or activation.
  The exact current scope and validation commands are recorded in §20.

---

## Historical Phase 1 execution contract

Phase 1 is complete and must not be restarted from this section. The following records
the original source-only execution boundary for provenance. Later owner-authorized
review, test, and RH-alignment work is governed by §20 and the revision history.

1. Work was limited to `/Users/wigglez/dev/ripe-protocol-instant-bond-lane`. The
   original Phase-1 baseline was branch `instant-bond-lane` at
   `91eda49ccd34a25090582aff0695075c4c806011`. That historical pin is not an instruction
   to reset or rebind the completed feature. Revision 20's starting baseline is
   recorded in the header above.
2. This specification was normative and `pricing-design.md` was optional rationale
   that could not override it.
3. Read-only inspection of the repository was allowed; the original ceiling restricted
   writes, not reads. The implementer was directed to the source families now recorded
   in §10.1 for lane and switchboard conventions.
4. Original writes were limited to the two contracts in §1 and an explicitly
   authorized normative revision. The contracts had to be complete, with no TODOs,
   placeholders, stubs, unapproved architecture/economic/API changes, or shared
   feature-interface file.
5. Any conflict with the bound source or inability to work within that ceiling
   required stopping and reporting the exact conflict.
6. Compilation and validation were forbidden at that historical source-only stage,
   which ended with an owner-review handoff. The later revision-20 authorization in
   §20 supersedes that old stop point without retroactively broadening it.

---

## 1. Scope and minimal architecture

Build exactly two contracts at these paths:

1. `contracts/core/InstantBondLane.vy` — a core Department that accepts a canonical
   dollar-denominated ERC-20 payment token, derives its immutable decimal scale,
   stores one fixed base payout rate per lane epoch, applies an optional lock bonus,
   enforces an epoch payment cap, minimum purchase, and cumulative mint budget,
   forwards proceeds to Endaoment Funds, and mints RIPE unlocked or into RipeGov
   through Teller.
2. `contracts/config/SwitchboardFoxtrot.vy` — a single-purpose LocalGov +
   TimeLock adapter that queues and executes complete lane-config replacements,
   exact rate-override installations, and installed-override cancellations.

These are the only production contracts changed by the feature. Revision-20's complete
source, documentation, model, and test file inventory is recorded in §20. The
implementation may import existing repository modules and interfaces, but it must not
modify them. Any new feature-specific structs, events, constants, or narrow interface
declarations needed by the lane must live inside these two contracts, even if that
requires a small amount of duplication between them.

Existing-system state changes are limited to registering the new switchboard,
registering the lane as a RIPE minter, and installing its configuration. There are
**no source changes** to MissionControl, Ledger, RipeToken, RipeGov, BondRoom,
SwitchboardAlpha, SwitchboardBravo, SwitchboardCharlie, SwitchboardDelta, or
SwitchboardEcho.

Out of scope for v2: external-price oracles, DEX guards, within-epoch price ramps or
tranche schedules, self-updating solvency floors, delegated purchases,
partial fills, bad-debt participation, historical on-chain epoch mappings, and a
special reactivation price reset.

The safety hierarchy is:

1. cumulative `mintBudget`;
2. per-epoch `paymentCapPerEpoch`, `minPaymentAmount`, and the all-in effective-rate
   ceiling;
3. global RipeHq `mintEnabled` and lane registration;
4. lane `canBuyNow` and Department pause;
5. the demand controller.

The controller is not an oracle and is not the primary supply-safety boundary.

---

## 2. Contract shape and constructor

The lane follows the Bond Room's module pattern on Vyper `0.4.3`:

```vyper
# @version 0.4.3
implements: Department
exports: addys.__interface__
exports: deptBasics.__interface__
initializes: addys
initializes: deptBasics[addys := addys]

import contracts.modules.Addys as addys
import contracts.modules.DeptBasics as deptBasics
from interfaces import Department
import interfaces.ConfigStructs as cs

from ethereum.ercs import IERC20
from ethereum.ercs import IERC20Detailed
```

Constructor shape:

```vyper
@deploy
def __init__(
    _ripeHq: address,
    _paymentToken: address,
    _genesisBlock: uint256,
    _epochLength: uint256,
):
    assert _paymentToken != empty(address) and _paymentToken.is_contract
                                                            # dev: invalid payment token
    assert _epochLength != 0 and _epochLength <= max_value(uint256) // HUNDRED_PERCENT + 1
                                                            # dev: invalid epoch length

    paymentDecimals: uint8 = staticcall IERC20Detailed(_paymentToken).decimals()
    assert paymentDecimals <= MAX_PAYMENT_DECIMALS          # dev: invalid payment decimals

    addys.__init__(_ripeHq)
    assert _paymentToken != addys._getRipeToken()           # dev: payment token is ripe
    deptBasics.__init__(True, False, True)  # starts paused, can mint ripe only

    PAYMENT_TOKEN = _paymentToken
    PAYMENT_DECIMALS = paymentDecimals
    PAYMENT_SCALE = 10 ** convert(paymentDecimals, uint256)
    GENESIS_BLOCK = _genesisBlock
    EPOCH_LENGTH = _epochLength
```

`PAYMENT_TOKEN`, `PAYMENT_DECIMALS`, `PAYMENT_SCALE`, `GENESIS_BLOCK`, and
`EPOCH_LENGTH` are immutable. The constructor reads `decimals()` once and supports
decimal counts from 0 through 73; the upper bound ensures the derived scale can
participate in the §3.3 arithmetic bounds. There is no recurring runtime decimals
dependency. Deployment tooling must still verify that `PAYMENT_TOKEN` is the intended
canonical dollar stablecoin on the target chain. The constructor rejects the registered
RIPE token, but otherwise establishes only contract code and a representable decimal
scale; it does not establish dollar denomination, intended stablecoin identity, stable
value, or absence of proxy risk. Runtime purchase settlement nevertheless measures the
Endaoment Funds balance delta and rejects any transfer that does not deliver the exact
requested amount.

Locked settlement resolves `MissionControl.coreRipeGovVaultId()` on every purchase and
rejects a zero pointer before payment or minting. This follows the protocol's rotatable
core-vault topology and ensures purchases after a RipeGov migration route to the current
core vault rather than a historical numeric ID. Fork and live preflight must verify that
the current pointer resolves to RipeGov and supports the RIPE token.

The lane deploys paused, unconfigured, and inert. The constructor installs no
economic values. `DeptBasics` supplies `isPaused`, `pause(bool)`, `canMintRipe`, and
the inherited recovery functions.

Resolved addresses use `Addys`:

- Endaoment Funds: id 21;
- MissionControl: id 5;
- Ledger: id 4;
- RIPE token: id 3 / `a.ripeToken`;
- Teller: id 17 / `a.teller`;
- switchboard registry: id 6.

---

## 3. Types, governed configuration, and hard constants

### 3.1 Config input

`version` is **not** caller-supplied. It is separate lane state.

```text
InstantBondConfig
    canBuyNow            # immediate master on/off

    paymentCapPerEpoch   # payment-token base units
    minPaymentAmount     # minimum purchase, payment-token base units
    mintBudget           # cumulative RIPE-wei ceiling; may be raised or lowered

    maxEffectiveRate     # maximum all-in RIPE-wei per whole USD
    seedRate             # initial base rate, used only before first initialization

    uHighBps             # high-utilization threshold
    uLowBps              # low-utilization threshold
    minUpBps             # minimum high-utilization price-up step
    maxUpBps             # maximum high-utilization price-up step
    minDownBps           # minimum low-utilization price-down step
    maxDownBps           # maximum low-utilization price-down step
    decayBps             # price-down step for a fully empty epoch
    maxDecayEpochs       # max empty steps applied by one rollover

    maxLockBonus         # maximum bonus on base payout, HUNDRED_PERCENT scale
```

Lane state holds:

```text
config                  # current governed config
configVersion           # starts 0; increments after every successful setConfig
isInitialized

currentEpoch
epochRate               # fixed base rate for currentEpoch
epochPaymentCap         # fixed cap for currentEpoch
epochMinPaymentAmount   # fixed minimum purchase for currentEpoch
epochMaxLockBonus       # fixed bonus magnitude for currentEpoch
epochPricingVersion     # config version that supplied the epoch pricing fields
epochAcceptedPayment
epochWeightedLateness   # sum(paymentAmount * latenessBps) for the stored epoch
epochTimingEligible     # whether timing may amplify the high-utilization step

rateOverride            # exact target rate; zero means no installed override
overrideVersion         # optimistic lifecycle version; starts at zero

cumulativeMinted        # all RIPE minted by the lane, including bonuses
```

No epoch-history mapping is stored. Events are the historical audit record.

Required read ABI exposes `PAYMENT_TOKEN`, `PAYMENT_DECIMALS`, `PAYMENT_SCALE`,
`GENESIS_BLOCK`, and `EPOCH_LENGTH` as public immutables; `config`, `configVersion`,
and `cumulativeMinted` are public. The complete stored epoch snapshot is also public:
`isInitialized`, `currentEpoch`, `epochRate`, `epochPaymentCap`,
`epochMinPaymentAmount`, `epochMaxLockBonus`, `epochPricingVersion`, and
`epochAcceptedPayment`, `epochWeightedLateness`, and `epochTimingEligible`. The
installed `rateOverride` and its independent `overrideVersion` are also public. The
switchboard depends on the lane validators and version getters, while operators
and indexers can compare live configuration, stored epoch state, cumulative issuance,
and the read-only projection returned by `previewBuyNow`. These getters are a stored
snapshot, lazily advanced only by a successful `buyNow`; after a block-clock boundary
they can describe the prior epoch until the next purchase. Integrations must use
`previewBuyNow` for current pricing and must never construct a quote directly from
`epochRate` or the other stored epoch getters.

### 3.2 Hard constants

```text
HUNDRED_PERCENT              = 100_00
MAX_LOCK_BONUS               = 1000_00  # 1000%, aligned with existing bond ceiling
MAX_PRICE_STEP_BPS           = 100_00   # at most a 100% price-up step
MAX_DECAY_EPOCHS             = 32       # hard gas/velocity bound
MAX_PAYMENT_DECIMALS         = 73       # PAYMENT_SCALE remains arithmetically usable
MIN_BASE_RATE                = 10_000   # engineering liveness floor
```

`maxDecayEpochs` may be governed below 32 but not above it. Thirty-two is an
engineering safety ceiling, not a recommended production value.

### 3.3 Required validation

The lane is the authority for config validity. `setConfig` must enforce all of the
following on every config, including the first:

```text
0 < uLowBps < uHighBps < 10_000
0 < minUpBps <= maxUpBps <= MAX_PRICE_STEP_BPS
0 < minDownBps <= maxDownBps <= decayBps < 10_000
maxDownBps < minUpBps
(10_000 + minUpBps) * (10_000 - maxDownBps) >= 10_000**2
0 < maxDecayEpochs <= MAX_DECAY_EPOCHS

0 < maxEffectiveRate <= max_value(uint256) / 10_000
PAYMENT_SCALE <= minPaymentAmount <= paymentCapPerEpoch
paymentCapPerEpoch <= max_value(uint256) / 10_000
paymentCapPerEpoch * maxEffectiveRate <= max_value(uint256)

maxLockBonus <= MAX_LOCK_BONUS
baseRateCeiling(maxEffectiveRate, maxLockBonus) >= MIN_BASE_RATE
maxBaseRipe = paymentCapPerEpoch * baseRateCeiling // PAYMENT_SCALE
maxLockBonus == 0 or maxBaseRipe <= max_value(uint256) / maxLockBonus
seedRate >= MIN_BASE_RATE
seedRate <= baseRateCeiling(maxEffectiveRate, maxLockBonus)

mintBudget >= cumulativeMinted
```

The one-whole-token minimum purchase prevents base-unit dust from selecting the sold
epoch controller branch. Governance may set a materially higher minimum, but never a
minimum above the epoch cap. The `10_000` minimum base rate prevents the inverse-rate
recovery formula from becoming an integer fixed point for any valid down step; it is
still economically tiny and does not replace calibrated operator bounds or unit-aware
tooling. The range ordering ensures that the strongest nonempty price-down step is no
larger than empty decay and is smaller than the weakest price-up step. The product
constraint prevents an unclamped minimum-up/maximum-down round trip from producing a
net price decrease; the engineering floor and ceiling can still dominate arithmetic at
their boundaries and are tested separately. The conservative
`paymentCapPerEpoch * maxEffectiveRate` bound makes the base
payout multiplication safe before division. Variable-decimal payment tokens require a
separate bound on `maxBaseRipe * maxLockBonus`, because the bonus multiplication occurs
before division by `HUNDRED_PERCENT`; without that bound, otherwise-valid configs for
low-decimal tokens could revert during payout calculation. Purchase code compares
`totalRipe` with `mintBudget - cumulativeMinted`; it does not use an unchecked
`cumulativeMinted + totalRipe` expression.

Expose `isValidConfig(config) -> bool` for tooling and the dedicated switchboard.
The lane repeats/asserts the validation during execution; a switchboard precheck is
not a security boundary.

The constructor separately requires:

```text
0 < EPOCH_LENGTH <= max_value(uint256) // 10_000 + 1
```

This is equivalent to `(EPOCH_LENGTH - 1) * 10_000 <= max_value(uint256)` and makes
the normalized block-offset calculation safe. Together with the existing
`paymentCapPerEpoch <= max_value(uint256) // 10_000` bound, it proves that both each
`paymentAmount * latenessBps` term and their epoch accumulator remain in `uint256`.

---

## 4. Payout math and the effective floor

`rate` is RIPE-wei per whole dollar-denominated payment token. The immutable
`PAYMENT_SCALE` normalizes its configured decimals:

```text
baseRipe = paymentAmount * epochRate // PAYMENT_SCALE
```

`maxEffectiveRate` limits the maximum **total** RIPE-wei per USD after the maximum
bonus. The base-rate ceiling for a pricing config is:

```text
baseRateCeiling =
    maxEffectiveRate * HUNDRED_PERCENT
    // (HUNDRED_PERCENT + maxLockBonus)
```

Initialization and every rollover enforce `epochRate <= baseRateCeiling` for the
epoch's snapshotted `epochMaxLockBonus`. Consequently every successful purchase must
satisfy the dimensionally exact cross-product invariant:

```text
totalRipe * PAYMENT_SCALE
    <= paymentAmount * epochMaxEffectiveRate
```

Here `epochMaxEffectiveRate` means the value in the config identified by
`epochPricingVersion`; it does not mean a newer live config installed mid-epoch.
Tests use cross multiplication, not truncating division.

A governance action that lowers `maxEffectiveRate` is **prospective**: the tighter
floor applies at the next rollover, not to the running epoch. If the current epoch's
older floor is unsafe, governance must pause the lane immediately and leave it paused
until the tighter config is active in a new epoch.

All rate, base-payout, and bonus calculations round down, protecting the treasury.

---

## 5. Lock bonus and live RipeGov terms

The lane reads `MissionControl.ripeGovVaultConfig(ripeToken)` once per quote or
purchase as `cs.RipeGovVaultConfig`. The exact baseline shape is nested:
`vaultConfig.lockTerms.minLockDuration`,
`vaultConfig.lockTerms.maxLockDuration`, `vaultConfig.lockTerms.canExit`, and
`vaultConfig.lockTerms.exitFee`; `shouldFreezeWhenBadDebt` is directly on
`vaultConfig`. Do not flatten or redefine the existing repository type.

Lock-duration boundaries deliberately remain live rather than epoch-snapshotted.
RipeGov reads the same config during settlement, so the bonus-bearing duration and
the deposited duration cannot diverge. A governance change to RipeGov terms can
therefore change the lock curve within a lane epoch, but cannot exceed the epoch's
snapshotted `epochMaxLockBonus` and cannot violate the all-in floor.

Exact bonus logic:

```text
(vMin, vMax) = live RIPE gov-vault min/max lock

if vMax == 0 or vMax < vMin:
    actualLock = 0
    bonusRatio = 0
elif requestedLock < vMin:
    actualLock = 0
    bonusRatio = 0
else:
    actualLock = min(requestedLock, vMax)
    if vMax == vMin:  # necessarily nonzero here
        bonusRatio = epochMaxLockBonus
    else:
        bonusRatio = (
            epochMaxLockBonus * (actualLock - vMin)
            // (vMax - vMin)
        )

baseRipe = paymentAmount * epochRate // PAYMENT_SCALE
bonusRipe = baseRipe * bonusRatio // HUNDRED_PERCENT
totalRipe = baseRipe + bonusRipe
```

Important properties:

- `actualLock` never exceeds `requestedLock`.
- A request below the live minimum settles unlocked and receives no bonus.
- A request exactly at a positive live minimum creates a real lock with zero bonus; UI
  must warn before submission rather than presenting it as an economically rewarded
  lock choice.
- `vMin == vMax > 0` gives the full bonus without division by zero.
- `vMin == vMax == 0` gives no bonus and settles unlocked.
- Invalid live terms with `vMax < vMin` fail safely to an unlocked, zero-bonus payout
  rather than underflowing the quote path.
- The value passed to Teller is the same `actualLock` used for the bonus.
- The lane's bonus magnitude is independent of RipeGov's governance-points boost.

`actualLock` is the **new-deposit duration passed to RipeGov**, not necessarily the
buyer's final account unlock. RipeGov combines a new deposit with any existing RIPE
gov-vault shares using its normalized-share-weighted, whole-block unlock calculation
(`RipeGov.vy:936-961`). The weighting approximately transfers the new deposit's
share-duration commitment across the combined position, but a dominant short-duration
existing position can make the final calendar unlock materially shorter than
`block.number + actualLock`. Integer normalization and final division can further
round down the incremental extension. Because RipeGov floors an expired prior position
to one block, a measured 100,000-RIPE expired position plus an approximately 15-RIPE
max-lock payout reduces a 1,000-block bonus-bearing duration to one effective account
block (0.1%). The UI must label `actualLock` as the deposit lock and must not present it as
the buyer's final position unlock. The economic treatment of this inherited behavior
is recorded in §16.

For a locked quote, the UI must also disclose the live early-exit terms:

```text
canExitEarly = lockTerms.canExit
exitFee       = lockTerms.exitFee
isExitFrozen  = (
    actualLock != 0
    and ripeGovVaultConfig.shouldFreezeWhenBadDebt
    and Ledger.badDebt() != 0
)
```

`RipeGov.releaseLock` blocks early exit during bad debt when the freeze flag is set.
Even without bad debt, `canExitEarly == false` means the position has no paid early
exit. These are disclosures, not purchase blockers. For an unlocked quote, return
`canExitEarly=false`, `exitFee=0`, and `isExitFrozen=false`.

---

## 6. Epoch clock and initialization

For `blockNumber >= GENESIS_BLOCK`:

```text
laneEpoch(blockNumber) =
    (blockNumber - GENESIS_BLOCK) // EPOCH_LENGTH
```

Before genesis, the epoch function is unavailable and must not subtract unsigned
values. Because `EPOCH_LENGTH` is immutable, historical epoch indices never remap.

### 6.1 Lazy initialization

The lane has one initialization path:

1. Deployment leaves `configVersion == 0` and `isInitialized == false`.
2. Timelocked `setConfig(config, expectedVersion=0)` installs the first validated
   config and sets `configVersion = 1`; the lane remains paused and `canBuyNow=false`.
3. Governance later installs an enabling config and unpauses the Department.
4. The first successful `buyNow` at or after genesis initializes state before quoting:

```text
currentEpoch         = laneEpoch(block.number)
epochRate            = config.seedRate
epochPaymentCap      = config.paymentCapPerEpoch
epochMinPaymentAmount = config.minPaymentAmount
epochMaxLockBonus    = config.maxLockBonus
epochPricingVersion  = configVersion
epochAcceptedPayment = 0
epochWeightedLateness = 0
epochTimingEligible  = ((block.number - GENESIS_BLOCK) % EPOCH_LENGTH == 0)
isInitialized        = True
```

`seedRate` is validated at or below its derived base-rate ceiling, so initialization
does not silently clamp a misconfigured seed.

Epochs between genesis and the first successful initialization are intentionally
ignored. This is cold-start behavior: the lane begins at `seedRate` in the then-current
epoch rather than decaying before it has ever been active.

The first stored epoch receives timing amplification only when initialization occurs
at deterministic epoch offset zero. A late cold start would otherwise treat demand
before the lane existed as unsold time and overstate the meaning of purchase speed.
`EPOCH_LENGTH == 1` has offset zero and is therefore eligible. Purchase lateness is
still accumulated for a timing-ineligible first epoch for monitoring, but its high-
utilization branch uses `minUpBps`. Every later stored epoch is timing-eligible.

If `buyNow` later reverts, initialization and every other state write revert
atomically. `previewBuyNow` simulates the above initialization read-only and can quote
the first successful purchase.

Before config or genesis, preview returns `available=false`; `buyNow` reverts with an
explicit unavailable reason.

---

## 7. Controller and rollover

Rollover is lazy. It runs inside `buyNow` when the current deterministic epoch is
greater than stored `currentEpoch`. Preview runs the same controller read-only.

The current live config supplies the **next epoch's** pricing fields and the
transition parameters used at that rollover. Multiple governed changes before a
rollover collapse to the latest successfully installed config.

Safe reference algorithm:

```text
def rollover():
    e = laneEpoch(block.number)
    if e == currentEpoch:
        return

    cfg = live config
    fromEpoch = currentEpoch
    oldRate = epochRate
    previousAcceptedPayment = epochAcceptedPayment
    previousPaymentCap = epochPaymentCap
    previousWeightedLateness = epochWeightedLateness
    previousTimingEligible = epochTimingEligible
    elapsed = e - currentEpoch
    newCeiling = baseRateCeiling(cfg.maxEffectiveRate, cfg.maxLockBonus)

    # Clamp before multiplication. Validation guarantees rate * 10_000 is safe.
    rate = min(epochRate, newCeiling)
    effectiveAdjustmentBps = 0

    if epochAcceptedPayment == 0:
        # Defensive only under the current atomic write sequence.
        decaySteps = min(elapsed, cfg.maxDecayEpochs)
        utilizationBps = 0
    else:
        utilizationBps = epochAcceptedPayment * 10_000 // epochPaymentCap

        if utilizationBps >= cfg.uHighBps:
            utilizationStrengthBps = (
                (utilizationBps - cfg.uHighBps)
                * 10_000
                // (10_000 - cfg.uHighBps)
            )
            averageLatenessBps = epochWeightedLateness // epochAcceptedPayment
            earlinessBps = 0
            if epochTimingEligible:
                earlinessBps = 10_000 - averageLatenessBps
            demandStrengthBps = utilizationStrengthBps * earlinessBps // 10_000
            effectiveAdjustmentBps = (
                cfg.minUpBps
                + (cfg.maxUpBps - cfg.minUpBps)
                * demandStrengthBps
                // 10_000
            )
            rate = max(
                rate * 10_000 // (10_000 + effectiveAdjustmentBps),
                MIN_BASE_RATE,
            )
        elif utilizationBps <= cfg.uLowBps:
            weaknessBps = (
                (cfg.uLowBps - utilizationBps)
                * 10_000
                // cfg.uLowBps
            )
            effectiveAdjustmentBps = (
                cfg.minDownBps
                + (cfg.maxDownBps - cfg.minDownBps)
                * weaknessBps
                // 10_000
            )
            rate = min(
                rate * 10_000 // (10_000 - effectiveAdjustmentBps),
                newCeiling,
            )

        # The sold stored epoch was handled once above. Only skipped epochs decay.
        decaySteps = min(elapsed - 1, cfg.maxDecayEpochs)

    for i: uint256 in range(decaySteps, bound=MAX_DECAY_EPOCHS):
        rate = min(
            rate * 10_000 // (10_000 - cfg.decayBps),
            newCeiling,
        )

    controllerRate = rate
    if rateOverride != 0:
        # Installation validation and config invalidation guarantee that this exact
        # target is still within the live floor/ceiling. Do not decay or clamp it.
        rate = rateOverride

    currentEpoch         = e
    epochRate            = rate
    epochPaymentCap      = cfg.paymentCapPerEpoch
    epochMinPaymentAmount = cfg.minPaymentAmount
    epochMaxLockBonus    = cfg.maxLockBonus
    epochPricingVersion  = configVersion
    epochAcceptedPayment = 0
    epochWeightedLateness = 0
    epochTimingEligible  = True

    if rateOverride != 0:
        appliedTarget = rateOverride
        rateOverride = 0
        overrideVersion += 1
        log RateOverrideApplied(
            newVersion=overrideVersion,
            fromEpoch=fromEpoch,
            toEpoch=e,
            targetRate=appliedTarget,
            controllerRate=controllerRate,
        )

    log EpochRolled(
        fromEpoch=fromEpoch,
        toEpoch=e,
        oldRate=oldRate,
        newRate=rate,
        newPaymentCap=cfg.paymentCapPerEpoch,
        newMinPaymentAmount=cfg.minPaymentAmount,
        newMaxLockBonus=cfg.maxLockBonus,
        previousAcceptedPayment=previousAcceptedPayment,
        previousPaymentCap=previousPaymentCap,
        previousWeightedLateness=previousWeightedLateness,
        previousTimingEligible=previousTimingEligible,
        utilizationBps=utilizationBps,
        effectiveAdjustmentBps=effectiveAdjustmentBps,
        decaySteps=decaySteps,
        controllerRate=controllerRate,
        pricingConfigVersion=configVersion,
    )
```

The pre-rollover event values must be captured into locals before any epoch state is
overwritten, as shown above.

The inverse-price formulas are exact. A naive `rate * (10_000 - stepBps) / 10_000`
must not replace the price-up formula. `MIN_BASE_RATE` prevents repeated price-up
steps from rounding the inverse rate permanently to zero and ensures every valid
low-utilization recovery step can increase a sub-ceiling rate. It is a liveness bound,
not the treasury price floor. The `maxDownBps <= decayBps` constraint prevents a
minimum-size low-utilization purchase from selecting a stronger individual price-down
step than a fully empty epoch, while the governed minimum payment makes selecting that
branch economically non-dust.

For each successful purchase, the lane computes:

```text
offset = (block.number - GENESIS_BLOCK) % EPOCH_LENGTH
latenessBps = 0                                      if EPOCH_LENGTH == 1
latenessBps = offset * 10_000 // (EPOCH_LENGTH - 1) otherwise
epochWeightedLateness += paymentAmount * latenessBps
```

Weighting by payment makes the signal invariant to splitting or merging purchases at
the same block and distinguishes early volume from a tiny early probe followed by late
volume. A full first-block epoch maps exactly to `maxUpBps`; a full last-block epoch
maps exactly to `minUpBps`. At exactly `uHighBps`, utilization strength is zero and the
step is `minUpBps` regardless of timing. At exactly `uLowBps`, the down step is
`minDownBps`; a positive-payment epoch whose floored utilization is zero receives
`maxDownBps`.

The override is deliberately outside the controller calculation. `controllerRate`
records the complete ordinary transition including skipped decay. The exact target
then replaces that final rate and becomes the base for the following epoch's ordinary
controller. Preview performs the same projection without clearing the override.

### 7.1 Empty and unavailable epochs

An empty epoch decays whether the absence of sales came from demand, pause,
`canBuyNow=false`, exhausted budget, frontend downtime, or any other cause. A single
rollover applies at most `maxDecayEpochs` decay steps.

There is no rebaseline function and no pause timestamp. This is deliberate: one rule
is easier to reason about and test, while the hard floor and decay cap bound a long
outage's effect.

An installed exact-rate override is the explicit exception to ordinary skipped-epoch
decay. It persists through unavailable time and applies without pre-application decay
on the first later successful rollover. Governance can invalidate it with any full
config replacement or cancel it through a separately timelocked Foxtrot action.

---

## 8. Preview ABI and parity

```text
previewBuyNow(paymentAmount, requestedLock) -> InstantBondQuote
```

Logical return structure:

```text
InstantBondQuote
    available
    epoch
    pricingConfigVersion
    liveConfigVersion
    rate
    remainingPayment
    minPaymentAmount
    budgetRemaining
    baseRipe
    bonusRatio
    bonusRipe
    actualLock
    totalRipe
    canExitEarly
    exitFee
    isExitFrozen
```

Preview behavior:

1. Before config or genesis: return a zeroed quote with `available=false`.
2. If uninitialized: simulate §6.1.
3. If initialized but stale: simulate §7 without writing, including an installed exact
   override, but do not clear the override or advance `overrideVersion`.
4. Populate the epoch, versions, rate, remaining-capacity, active minimum-payment, and
   remaining-budget fields.
5. If `paymentAmount < minPaymentAmount` or exceeds `remainingPayment`, return
   `available=false` with zero payout/lock fields. Do not multiply an unbounded caller
   input by the rate.
6. Otherwise read the live RipeGov lock terms and compute §5.
7. Return the metadata and safely computed payout fields even when the request is
   unavailable for another reason, such as insufficient mint budget.
8. Set `available=true` only when all conditions evaluated by preview hold:
   Department unpaused, `canBuyNow`, RipeHq currently authorizes the lane to mint
   RIPE, payment at or above the epoch minimum, nonzero base payout, payment within
   remaining epoch capacity, and total payout within remaining mint budget.

Preview deliberately does not inspect the caller's payment-token balance or allowance.
It also does not take `deadlineBlock`, `expectedEpoch`, or `minRipeOut`; those are
execution protections populated from the quote. `available` is not a guarantee that
every downstream dependency will accept settlement: token behavior, general deposit
policy, VaultBook topology, the destination vault, and an unregistered Endaoment Funds
address can still make the atomic purchase revert. Deployment monitoring and the smoke
tests cover those dependencies without adding them all to the lane's quote path. The
quote intentionally provides no reason code: integrations that need diagnostic detail
should inspect the exposed lane state and relevant protocol dependencies separately.

The controller, lock, and payout arithmetic must live in shared internal helpers used
by both preview and purchase. If no relevant state changes between calls, a purchase
using the quote's epoch and an adequate `minRipeOut` returns exactly `quote.totalRipe`.
When an override is projected, `quote.rate` is the exact target. The ordinary
counterfactual remains reconstructable from the stored epoch inputs, config events,
and §7 and is emitted as `controllerRate` only when the rollover actually commits.

---

## 9. `buyNow` ABI and purchase flow

```text
buyNow(
    paymentAmount,
    requestedLock,
    expectedEpoch,
    minRipeOut,
    deadlineBlock,
) -> uint256
```

The caller is always the recipient. The function is `@nonreentrant` and uses
checks-effects-interactions. It does not partially fill an oversized request.

Normative flow:

The line wrapping below is illustrative; operation order, local terminology, and
diagnostics are normative where shown.

```text
1.  assert configVersion != 0                                  # dev: not configured
2.  assert block.number >= GENESIS_BLOCK                       # dev: before genesis
3.  assert not deptBasics.isPaused                             # dev: paused
4.  cfg = live config; assert cfg.canBuyNow                    # dev: disabled
5.  assert block.number <= deadlineBlock                       # dev: expired
6.  a = addys._getAddys()
    assert RipeHq(a.hq).canMintRipe(self)                     # dev: mint unavailable
7.  endaoFunds = addys._getEndaomentFundsAddr()
    assert endaoFunds != empty(address)                        # dev: no destination

8.  initialize if needed; otherwise rollover if needed
9.  assert expectedEpoch == projected currentEpoch             # dev: epoch moved

10. remainingPayment = epochPaymentCap - epochAcceptedPayment
    assert paymentAmount >= epochMinPaymentAmount
                                                                  # dev: below minimum payment
    assert paymentAmount <= remainingPayment                      # dev: exceeds epoch cap

11. Read live RIPE gov-vault config once.
12. Compute baseRipe, bonusRatio, bonusRipe, actualLock, totalRipe.
    assert baseRipe != 0                                       # dev: zero payout
    assert totalRipe >= minRipeOut                             # dev: slippage

13. budgetRemaining = cfg.mintBudget - cumulativeMinted
    assert totalRipe <= budgetRemaining                        # dev: mint budget

14. coreRipeGovVaultId = 0
    if actualLock != 0:
        coreRipeGovVaultId = MissionControl(a.missionControl).coreRipeGovVaultId()
        assert coreRipeGovVaultId != 0                          # dev: invalid vault id

15. paymentBalanceBefore = IERC20(PAYMENT_TOKEN).balanceOf(endaoFunds)

16. store the complete pricing snapshot when initializing or rolling
    epochAcceptedPayment = pricing.acceptedPayment + paymentAmount  # effects
    epochWeightedLateness = (
        pricing.weightedLateness + paymentAmount * latenessBps(block.number)
    )
    cumulativeMinted += totalRipe
    if this store committed a rollover with an installed override:
        clear rateOverride
        increment overrideVersion exactly once
        emit RateOverrideApplied with target and controllerRate

17. assert IERC20(PAYMENT_TOKEN).transferFrom(
        msg.sender,
        endaoFunds,
        paymentAmount,
        default_return_value=True,
    )                                                          # dev: payment failed
    paymentBalanceAfter = IERC20(PAYMENT_TOKEN).balanceOf(endaoFunds)
    assert paymentBalanceAfter >= paymentBalanceBefore
    assert paymentBalanceAfter - paymentBalanceBefore == paymentAmount
                                                               # dev: payment receipt mismatch

18. if actualLock == 0:
        assert RipeToken(a.ripeToken).mint(msg.sender, totalRipe)
                                                                  # dev: mint failed
    else:
        assert RipeToken(a.ripeToken).mint(self, totalRipe)     # dev: mint failed
        assert IERC20(a.ripeToken).approve(
            a.teller,
            totalRipe,
            default_return_value=True,
        )                                                       # dev: ripe approval failed
        depositedAmount = Teller(a.teller).depositFromTrusted(
            msg.sender,
            coreRipeGovVaultId,
            a.ripeToken,
            totalRipe,
            actualLock,
            a,
        )
        assert depositedAmount == totalRipe                       # dev: deposit mismatch
        assert IERC20(a.ripeToken).approve(
            a.teller,
            0,
            default_return_value=True,
        )                                                       # dev: ripe approval failed

19. emit InstantBondPurchased(..., ripeGovVaultId=coreRipeGovVaultId)
20. return totalRipe
```

The snapshot helper is deliberately transition-only: on a purchase in the already
stored epoch it performs no write. Therefore `epochAcceptedPayment` must still be
assigned explicitly on every successful purchase, as must the weighted-lateness
accumulator. Folding either assignment into the snapshot helper would lose same-epoch
accumulation; the stateful differential model guards this distinction.

Any failed transfer, exact-receipt check, mint, approval, Teller deposit, or
deposited-amount equality check reverts the full transaction, including cap and budget
state, timing state, and any provisional override consumption/version increment.
Standard transfers and no-return transfers are supported when the observed
Endaoment Funds balance increase is exactly `paymentAmount`; short, fee-on-transfer,
zero, or excess receipt is rejected atomically.

---

## 10. Settlement and protocol integration

The settlement path mirrors `BondRoom.vy`:

- Proceeds go directly from the buyer to Endaoment Funds (id 21).
- Unlocked RIPE is minted directly to the buyer.
- Locked RIPE is minted to the lane, approved exactly to Teller, deposited into the
  current `MissionControl.coreRipeGovVaultId()` with `depositFromTrusted`, and the
  approval is reset to zero.
- The lane should normally retain no payment-token or RIPE balance.
- `depositFromTrusted` accepts the lane after its RipeHq registration because the lane
  becomes a valid Ripe address.
- The lane asserts that Teller reports a deposited amount exactly equal to `totalRipe`,
  preventing a future dependency change from silently leaving RIPE behind.

Declare narrow inline interfaces for:

- `RipeHq.canMintRipe`;
- `RipeToken.mint`, using the bound implementation's `-> bool` return and asserting
  success;
- `Teller.depositFromTrusted`;
- `MissionControl.ripeGovVaultConfig`, returning the existing
  `cs.RipeGovVaultConfig`, and `MissionControl.coreRipeGovVaultId`;
- `Ledger.badDebt`.

The lane does not call `Ledger.didClearBadDebt`, does not reduce RIPE delivery during
bad debt, and does not write Bond Room/Ledger epoch state.

### 10.1 Source anchors at the reviewed RH-integrated baseline

The following references were rebound and verified at revision 18's reviewed
`c4ae637`/RH-integrated source. Rebind them again after dependency changes:

- RipeGov clamps deposits to live min/max lock terms: `RipeGov.vy:211-214`.
- RipeGov early-exit permissions, bad-debt freeze, and fee: `RipeGov.vy:792-833`.
- RipeGov weighted unlock calculation: `RipeGov.vy:936-961`.
- Teller trusted-deposit authorization and signature: `Teller.vy:278-289`.
- RipeHq RIPE-minter checks: `RipeHq.vy:389-399`.
- Registered-switchboard authorization: `Addys.vy:183-189`.
- Department pause/recovery behavior: `DeptBasics.vy:63-93`.
- SwitchboardCharlie pause pass-through: `SwitchboardCharlie.vy:629-635`.
- Bond Room's locked mint/approve/deposit/reset pattern: `BondRoom.vy:219-226`.
- Shared TimeLock confirmation and expiration behavior: `TimeLock.vy:65-87` and
  `TimeLock.vy:117-123`.

---

## 11. Governed configuration semantics

```text
setConfig(newConfig, expectedVersion)
```

The lane function must:

1. require `addys._isSwitchboardAddr(msg.sender)`;
2. require `expectedVersion == configVersion`;
3. validate `newConfig` under §3.3;
4. store the complete new config;
5. increment `configVersion` exactly once;
6. if an override is installed, clear it, increment `overrideVersion` exactly once,
   and emit `RateOverrideInvalidated`;
7. emit every config field and the new version;
8. return the resulting config version.

`setConfig`, `setRateOverride`, and `cancelRateOverride` are `@nonreentrant` as
defense-in-depth even though only registered switchboards may call them and their
normal paths have no state-changing external interaction.

Initial configuration uses `expectedVersion=0`. Stale actions revert in the lane even
if they came from a registered switchboard. This preserves the protocol's standard
registered-switchboard authorization model while placing overwrite protection at the
actual state boundary.

Activation timing:

- `canBuyNow` changes immediately **when the timelocked config action executes**; it
  is not an untimelocked emergency switch. `DeptBasics.pause` is the emergency path.
- Any valid `mintBudget` change applies immediately. A decrease may halt purchases but
  may never set the budget below `cumulativeMinted`.
- Before initialization, the latest config supplies the seed and first epoch fields.
- After initialization, rate inputs, payment cap, minimum payment, and maximum bonus
  take effect together at the next rollover. They never rewrite the running epoch.
- `seedRate` never resets or directly changes an initialized `epochRate`.

Every action replaces the full config and increments `configVersion`, even when the
operator intends only to toggle `canBuyNow` or change `mintBudget`. There is no partial
config action. Operators must copy and verify every unchanged pricing field; the next
rollover snapshots the newly versioned full config even when those values are identical.
Because initiation pins `expectedVersion`, config actions cannot be safely pipelined:
each successful action changes the version and any later action prepared against the
old version will revert. Multi-step plans therefore require serial timelocks.

A purchase event therefore carries both:

- `pricingConfigVersion` — source of rate, cap, and max bonus; and
- `liveConfigVersion` — live source of availability and mint budget.

Lock-duration terms are separately live through SwitchboardAlpha and are not covered
by the lane config version.

Rate-override governance uses:

```text
isValidRateOverride(targetRate, expectedConfigVersion, expectedOverrideVersion) -> bool
setRateOverride(targetRate, expectedConfigVersion, expectedOverrideVersion) -> newVersion
canCancelRateOverride(expectedOverrideVersion) -> bool
cancelRateOverride(expectedOverrideVersion) -> newVersion
```

The two mutators require a registered switchboard. Installation additionally requires
an initialized lane, no installed override, exact config and override versions, and:

```text
MIN_BASE_RATE <= targetRate <= baseRateCeiling(live config)
```

An installed target has no calendar expiry and may be installed while the deterministic
clock is already ahead of stored `currentEpoch`. Transaction ordering is therefore
operationally significant: if governance needs to prevent an intervening buyer from
consuming the override, it must pause first. Same-epoch purchases do not consume it.
The first successful purchase with a projected epoch greater than `currentEpoch`
stores the target exactly and advances `overrideVersion`; a failed purchase reverts
both effects. Installed cancellation clears the target and advances the version.

The scalar `rateOverride == 0` sentinel is unambiguous because zero is outside every
valid target range. A separate stored bound-config field is unnecessary: every
successful full config write synchronously invalidates the installed target. The
installation event records the config version against which validation occurred.

---

## 12. Dedicated `SwitchboardFoxtrot`

The dedicated switchboard uses `LocalGov` and `TimeLock`, with the same constructor
and setup pattern as the existing configuration switchboards plus an immutable target:

```text
constructor(
    ripeHq,
    tempGov,
    minConfigTimeLock,
    maxConfigTimeLock,
    instantBondLane,
)
```

`instantBondLane` must be nonzero and a contract and is stored as public immutable
`LANE`. The switchboard exposes no arbitrary target parameter.

Constructor initialization follows the baseline switchboards exactly:

```text
gov.__init__(ripeHq, tempGov, 0, 0, 0)
timeLock.__init__(minConfigTimeLock, maxConfigTimeLock, 0, maxConfigTimeLock)
assert instantBondLane != empty(address) and instantBondLane.is_contract
LANE = instantBondLane
```

Action-tagged state:

```text
ActionType
    INSTANT_BOND_CONFIG
    RATE_OVERRIDE_SET
    RATE_OVERRIDE_CANCEL

PendingInstantBondConfig
    config
    expectedVersion

PendingRateOverride
    targetRate
    expectedConfigVersion
    expectedOverrideVersion

public actionType[aid] -> ActionType
public pendingConfig[aid] -> PendingInstantBondConfig
public pendingRateOverride[aid] -> PendingRateOverride
```

External workflow:

```text
setInstantBondConfig(config, expectedVersion) -> aid
setInstantBondRateOverride(
    targetRate,
    expectedConfigVersion,
    expectedOverrideVersion,
) -> aid
cancelInstantBondRateOverride(expectedOverrideVersion) -> aid
executePendingAction(aid) -> bool
cancelPendingAction(aid) -> bool
```

The workflow above omits source-level leading underscores for readability. The concrete
`executePendingAction` and `cancelPendingAction` ABI input name is `_aid`; event fields
remain the more descriptive `actionId`.

Every initiation requires LocalGov permission and a nonzero inherited
`actionTimeLock`. Config initiation requires `LANE.isValidConfig(config)` and exact
`LANE.configVersion()`. Override installation initiation requires
`LANE.isValidRateOverride(...)`; installed-override cancellation initiation requires
`LANE.canCancelRateOverride(...)`. A rejected precheck must not allocate an action ID.
The nonzero timelock assertion makes the required
`setActionTimeLockAfterSetup` deployment ordering self-enforcing.

Execution requires LocalGov permission and a confirmable, unexpired action. The action
type dispatches to `LANE.setConfig`, `LANE.setRateOverride`, or
`LANE.cancelRateOverride`. Each lane mutator repeats authorization and version/state
validation and returns the actual resulting version. Only after the external call
succeeds does Foxtrot clear `actionType`, `pendingConfig`, and `pendingRateOverride` and
emit the action-specific result.

If a target call reverts because an action became stale, transaction atomicity also
reverts TimeLock's provisional confirmation deletion. The action therefore remains
pending for retry, explicit queue cancellation, or expiry cleanup. At or after
TimeLock expiration, execution clears the tagged payload, emits the corresponding
config or override action-cancellation event, and returns `false`; before confirmation
it returns `false` without mutation.

`cancelPendingAction(aid)` cancels only a queued Foxtrot action. It never calls the
lane and cannot cancel an installed override. Cancelling an installed override uses
the separate, version-bound, timelocked `cancelInstantBondRateOverride` workflow.

Required switchboard events:

```text
PendingInstantBondConfigSet(
    actionId,
    confirmationBlock,
    expectedVersion,
    <all config fields in §3.1 order>,
)
InstantBondConfigExecuted(actionId, newVersion)
InstantBondConfigCancelled(actionId)

PendingRateOverrideSet(
    actionId,
    confirmationBlock,
    targetRate,
    expectedConfigVersion,
    expectedOverrideVersion,
)
PendingRateOverrideCancellationSet(
    actionId,
    confirmationBlock,
    expectedOverrideVersion,
)
RateOverrideExecuted(actionId, newVersion)
RateOverrideCancellationExecuted(actionId, newVersion)
RateOverrideActionCancelled(actionId, isCancellation)
```

No Foxtrot event field is indexed.

Multiple queued actions may coexist. Their deterministic races are:

- two installs against the same versions: first execution succeeds; the other reverts
  stale and remains pending;
- config executes before an install: the install is stale by config version;
- install executes before a previously queued config: the config succeeds and
  invalidates the installed target because config actions intentionally do not bind
  `overrideVersion`;
- application, config invalidation, or installed cancellation before a queued cancel:
  that cancel becomes stale and remains pending;
- a reverting config leaves the installed override and both versions unchanged.

Rationale: SwitchboardDelta is the closest semantic home because it already governs
Bond Room configuration, but it is nonupgradeable and the prior size review measured
it at approximately 23.1 KB against the 24,576-byte EIP-170 runtime limit. The full
lane-config action requires a target interface, complete pending-config storage,
detailed initiation event, initiation logic, execution logic, cancellation cleanup,
and stale-version handling. It must not be forced into the remaining approximate
1.5 KB of headroom. Modifying Delta would also require deploying and registering a
replacement and reopening regression risk across its unrelated bond, HR, reward,
loot, and deleverage actions.

SwitchboardEcho already exists and governs Endaoment and PSM operations. Adding this
lane to Echo would mix governance domains and would still require replacing a live,
nonupgradeable switchboard. A small `SwitchboardFoxtrot` is therefore the next
repository-consistent name and the lowest-blast-radius architecture. Historical
bytecode sizes are preserved in §20.3; current revision-20 size and project-ceiling
results are recorded in §20.4.

The lane intentionally uses the protocol-standard registered-switchboard check rather
than pinning config or override mutators to the dedicated switchboard address. Pinning
would require a predicted address, circular deployment, or a mutable one-time bootstrap
setter. The Switchboard registry remains the protocol trust boundary; the dedicated
switchboard's immutable `LANE` target and the lane-local version checks provide the
feature-specific containment. Every registered switchboard must therefore be treated
as capable of exercising these mutators.

---

## 13. Availability and recovery

Availability controls are intentionally layered:

- `config.canBuyNow` — timelocked economic on/off;
- `DeptBasics.pause` — operational circuit breaker; lite-action actors may pause,
  while full governance is required to unpause under SwitchboardCharlie;
- RipeHq `mintEnabled` — global mint circuit breaker;
- RipeHq registration/HqConfig — lane-specific RIPE mint authorization;
- RIPE token pause — blocks minting in both unlocked and locked paths;
- RIPE token recipient blacklist — blocks the unlocked buyer directly, while the locked
  path mints to the lane and therefore does not test the buyer as the token recipient;
- `mintBudget` — cumulative issuance ceiling;
- `paymentCapPerEpoch` — current epoch fundraising capacity;
- `minPaymentAmount` — current epoch minimum purchase size.

`SwitchboardCharlie.pause(lane, True)` is the complete operational circuit breaker.
Pausing Teller does not block `depositFromTrusted`, and pausing RipeGov affects only the
locked branch while unlocked purchases can otherwise continue. Unpausing the lane
requires full governance under the existing Charlie permission rule.

MissionControl/Teller deposit gates (`canDepositGeneral`, asset/vault support, and the
buyer's deposit allowlist) apply only to the locked path. The unlocked path mints RIPE
directly and does not consult those gates. Disabling general deposits can therefore
halt locked purchases while unlocked purchases remain available; it is not a complete
lane shutdown.

Inherited `recoverFunds` and `recoverFundsMany` remain switchboard-gated. Recovery is
not part of normal settlement and must never be used to extract buyer payments in
place of the direct Endaoment Funds transfer.

There is no rebaseline, restart, untimelocked direct admin-set-rate bypass, or
emergency mint function. The sole manual rate path is the exact, versioned,
timelocked override lifecycle in §11–§12.

---

## 14. Events

Core lane events:

```text
EpochInitialized(
    epoch indexed,
    rate,
    paymentCap,
    minPaymentAmount,
    maxLockBonus,
    timingEligible,
    pricingConfigVersion indexed,
)

EpochRolled(
    fromEpoch indexed,
    toEpoch indexed,
    oldRate,
    newRate,
    newPaymentCap,
    newMinPaymentAmount,
    newMaxLockBonus,
    previousAcceptedPayment,
    previousPaymentCap,
    previousWeightedLateness,
    previousTimingEligible,
    utilizationBps,
    effectiveAdjustmentBps,
    decaySteps,
    controllerRate,
    pricingConfigVersion indexed,
)

InstantBondPurchased(
    buyer indexed,
    paymentAmount,
    baseRipe,
    bonusRipe,
    bonusRatio,
    actualLock,
    totalRipe,
    epochRate,
    epoch indexed,
    pricingConfigVersion indexed,
    liveConfigVersion,
    ripeGovVaultId,
)

InstantBondConfigSet(
    newVersion,
    <all config fields in §3.1 order>,
)

RateOverrideInstalled(newVersion indexed, targetRate, boundConfigVersion indexed)
RateOverrideApplied(
    newVersion indexed,
    fromEpoch indexed,
    toEpoch indexed,
    targetRate,
    controllerRate,
)
RateOverrideCancelled(newVersion indexed, targetRate)
RateOverrideInvalidated(
    newVersion indexed,
    targetRate,
    newConfigVersion indexed,
)
```

`DeptBasics` already emits pause and recovery events. Switchboard events are specified
in §12. Initialization `epoch`, both rollover epoch endpoints, purchase `epoch`, and
each event's `pricingConfigVersion` are indexed as shown so indexers can filter by lane
epoch or pricing source without decoding every log. Events must be sufficient to
reconstruct every config and epoch transition without an on-chain history mapping.
`previousWeightedLateness`, `previousAcceptedPayment`, utilization, eligibility, the
historical config, and the deterministic formulas reconstruct the timing and severity
signals. `effectiveAdjustmentBps` records the final dynamic step directly, while
`controllerRate` distinguishes ordinary control from an exact override.
The purchase event has no remaining indexed slot: the signature plus `buyer`, `epoch`,
and `pricingConfigVersion` consume the EVM's four-topic maximum. The owner ratified
`pricingConfigVersion` over `liveConfigVersion` because it identifies the economic
terms used for the payout and aligns with initialization and rollover monitoring;
`liveConfigVersion` remains in event data for authorization and budget forensics.

The snapshot-field naming asymmetry is deliberate. `EpochInitialized` uses bare
`paymentCap`, `minPaymentAmount`, and `maxLockBonus` because there is no prior snapshot
to distinguish. `EpochRolled` prefixes the equivalent new snapshot fields with `new`
because that event also carries previous-epoch inputs.

---

## 15. Required invariants

Tests must prove:

1. **All-in floor:** for every successful purchase,
   `totalRipe * PAYMENT_SCALE <= paymentAmount * maxEffectiveRateFor(epochPricingVersion)`.
2. **Fixed epoch pricing:** rate, cap, minimum payment, max bonus, and pricing version
   do not change within a stored epoch.
3. **Controller direction and ranges:** high utilization increases price/decreases
   inverse rate by a step in `[minUpBps, maxUpBps]`; low utilization decreases price/
   increases inverse rate by a step in `[minDownBps, maxDownBps]`; the dead band applies
   no utilization step, subject to the live-ceiling pre-clamp.
4. **Skipped-epoch steps:** every committed initialized epoch currently contains a
   positive purchase. At its next rollover, the stored sold epoch applies its
   utilization transition once and one, two, or many skipped epochs apply exactly
   `min(elapsed - 1, maxDecayEpochs)` decay steps. The source retains a documented
   defensive fallback for a future committed zero-accepted epoch; under the current
   atomic write sequence that branch is unreachable and is not claimed as executable
   product behavior.
5. **Bounds:** `epochAcceptedPayment <= epochPaymentCap`, every accepted payment is at
   least `epochMinPaymentAmount`, and
   `cumulativeMinted <= mintBudget` after every successful call.
6. **Lock correctness:** zero terms give no bonus; equal positive terms give the full
   bonus; below-min requests are unlocked; intermediate bonuses are linear; the
   deposited lock equals the bonus-bearing lock and never exceeds the request.
7. **Settlement:** Endaoment Funds receives exactly `paymentAmount`; buyer receives or
   locks exactly `totalRipe` in the current MissionControl core RipeGov vault; the lane
   has no normal residual balance or allowance. The purchase event records that vault
   ID, or zero for an unlocked purchase.
8. **Recipient:** `msg.sender` is always the RIPE recipient.
9. **Atomicity:** any payment, mint, approval, or Teller failure reverts all cap,
   budget, timing, override, token, version, and event effects.
10. **Lifecycle:** before config/genesis purchase reverts and preview is unavailable;
    first preview simulates initialization; first successful buy stores the same quote;
    pre-initialization elapsed epochs do not decay.
11. **Prospective config:** live availability/budget changes are immediate; pricing
    changes are next-rollover; seed changes never reset an initialized rate.
12. **Versioning:** stale config and override actions revert at the lane; pricing and
    live config versions in purchase events identify their respective state;
    `overrideVersion` advances only on installation, application, installed
    cancellation, or config invalidation.
13. **Preview parity:** with unchanged relevant state, protective purchase inputs from
    a quote produce exactly the quoted payout and lock.
14. **No rebaseline:** pause/disable/budget gaps follow the same bounded decay rule.
15. **Rate liveness:** initialization and every rollover leave
    `epochRate >= MIN_BASE_RATE`; a sequence of high-utilization epochs cannot round the
    rate permanently to zero, and every valid low-utilization step strictly increases a
    sub-ceiling rate.
16. **Controller anti-dust:** the active minimum is at least one whole payment token,
    below-minimum purchases revert, and `maxDownBps <= decayBps` for every valid config.
17. **Bonus-intermediate safety:** every valid config keeps
    `maxBaseRipe * maxLockBonus` within `uint256` before bonus division, including for
    low-decimal payment tokens.
18. **Stored-state visibility:** public epoch getters expose the last stored snapshot;
    after an unpurchased boundary they remain unchanged while `previewBuyNow` projects
    the current epoch and pricing.
19. **Timing arithmetic:** weighted lateness never exceeds
    `epochAcceptedPayment * 10_000`; same-block split/merge and purchase-order
    permutations are exact invariants; first and last blocks map to exact endpoints.
20. **First-epoch eligibility:** an offset-zero initialization is timing-eligible,
    including `EPOCH_LENGTH == 1`; a later initialization is not. Every ordinary
    rolled epoch is eligible.
21. **Collapsed-range compatibility:** when each min/max pair is equal to its
    revision-19 fixed step, the controller produces byte-for-byte identical rate
    arithmetic for every utilization, timing, and elapsed-epoch input.
22. **Override lifecycle:** same-epoch purchase and preview retain an installed target;
    the first successful later rollover stores it exactly and consumes it once; the
    following rollover resumes ordinary control from that stored rate.
23. **Override governance:** a full config write invalidates an installed target;
    installed cancellation is timelocked and version-bound; queued action cancellation
    or expiry does not mutate Lane override state or versions.

---

## 16. Threat model and accepted trade-offs

### Supply and treasury

- `mintBudget` is the ultimate lane issuance cap but is governed and raisable after a
  timelock. Monitoring and governance-key security remain essential.
- Per-epoch worst-case issuance is bounded by
  `paymentCapPerEpoch * maxEffectiveRate // PAYMENT_SCALE`.
- Protocol RIPE issuance is governed by four distinct budgets: Ledger's
  `ripeAvailForRewards`, `ripeAvailForHr`, and `ripeAvailForBonds`, plus this lane's
  independent `mintBudget`. There is no aggregate on-chain ceiling or RIPE token-level
  maximum supply. Supply dashboards must add the lane's
  `mintBudget - cumulativeMinted` to the three Ledger remainders and expose the lane
  amount separately so operators do not undercount authorized issuance.
- Monitoring must also expose `configVersion`, `currentEpoch`, `cumulativeMinted`, the
  live `mintBudget`, worst-case issuance per epoch, and the deployment-approved
  rolling-day bound from §18. Crossing an approved warning or shutdown threshold is an
  operational halt condition even when the on-chain config remains valid.
- The global RipeHq mint switch can halt every protocol minter, including this lane.

### Pricing

- The controller discovers a cap-clearing price, not fair value.
- During a fast external price rise, the lane can temporarily sell below market and
  transfer value to fast buyers. A small epoch cap bounds the leak.
- DECAY gives patient buyers a free waiting option. The floor, decay cap, and mint
  budget bound that option.
- No automatic payment-token depeg or DEX-divergence guard exists in v2.
- `MIN_BASE_RATE` prevents integer fixed points but is economically tiny; deployment
  tooling and operator review must reject implausibly scaled `seedRate` and
  `maxEffectiveRate` values.
- A buyer can still deliberately make a minimum-size low-utilization purchase to select
  the sold-epoch branch. The governed minimum makes that non-dust,
  `maxDownBps <= decayBps`
  prevents a stronger individual step than emptiness, and the all-in floor remains the
  hard destination.
- Amount-weighted timing resists transaction splitting but is not manipulation-proof.
  A buyer or coordinated group can choose when to submit volume, and block producers
  can affect inclusion near boundaries. Timing only selects within governed bounds;
  the cap, budget, floor, and timelocked calibration remain the safety controls.
- An exact manual override is an explicit governance intervention, not oracle-backed
  fair value. Operators must document its unit conversion, target rationale, and
  expected divergence from `controllerRate`; pause before installation when an
  intervening rollover buyer would be unsafe.

### Lock-bonus commitment

- RipeGov stores one weighted unlock per user/asset rather than an isolated lock per
  deposit. A buyer with a sufficiently dominant short-duration RIPE position can
  receive the lane's long-lock bonus while the combined position's calendar unlock is
  much shorter than the new deposit's requested duration. Normalized-share and
  whole-block rounding can reduce the incremental extension further.
- The weighted calculation approximately moves the new deposit's duration commitment
  onto the buyer's existing shares, so this is not universally a cost-free bonus.
  Nevertheless, the individual lane deposit does not receive an isolated max-duration
  lock. The measured accepted boundary is concrete: with a 100,000-RIPE expired prior
  position, an approximately 15-RIPE max-lock payout received the full 5,000-bps lane
  bonus while the combined position was locked for one effective block, or 0.1% of the
  1,000-block bonus-bearing duration. This is not merely an extreme theoretical ratio.
- Bond Room inherits the same behavior through the identical Teller-to-RipeGov path;
  the lane does not create it. The lane can increase the available bonus budget,
  however, so v2 consciously accepts the inherited exposure rather than describing it
  only as a UI concern.
- Full closure requires isolated positions or a RipeGov-level lock-accounting change,
  both out of scope for this minimal lane. Launch bounds are a modest
  `paymentCapPerEpoch`, modest `maxLockBonus`, the cumulative `mintBudget`, and monitoring
  purchases that combine a maximum deposit lock with a large, short-duration or expired
  prior RipeGov position. Calibration must use the measured one-block/0.1% case rather
  than assuming the new deposit's requested duration becomes the account duration.
- The purchase event identifies the buyer and deposit `actualLock`, but deliberately
  does not duplicate pre-existing RipeGov shares or unlock state. Monitoring must join
  the event with RipeGov state/history; those cross-contract values are live position
  context, not a stable statement of the final post-deposit unlock.

### Governance

- All registered switchboards are trusted under the existing protocol authorization
  model. The dedicated switchboard is the only intended config/override entry point
  and has an immutable lane target.
- Registration and upgrade review must verify that no other switchboard exposes a
  generic executor capable of calling config or override mutators; the lane
  intentionally relies on the protocol-wide registered-switchboard trust boundary.
- Lane-local expected-version checks prevent stale queued actions from overwriting a
  newer config or override lifecycle state. Config writes deliberately invalidate any
  installed override.
- Live RipeGov lock terms are governed on a different switchboard and can change
  within an epoch. Buyer `minRipeOut`, the no-longer-than-requested rule, and the
  all-in bonus ceiling bound the effect.
- Operations must monitor changes to RIPE gov-vault min/max duration, early-exit terms,
  and bad-debt freeze behavior because those live values affect quotes within an epoch.

### Execution and UX

- Exact-amount, revert-on-cap-exceed purchases permit cap front-running. `expectedEpoch`,
  `minRipeOut`, and `deadlineBlock` protect price and timing but do not reserve capacity.
- A locked buyer may have no early exit or may temporarily lose early exit during bad
  debt. Preview and UI disclosure are mandatory.
- The lane is permissionless and has no lane-level buyer allowlist or per-buyer terms.
  Locked purchases inherit MissionControl's deposit allowlist; unlocked purchases do
  not. This is distinct from Bond Room's Teller-only and bond-allowlist workflow.
- On the locked path RIPE is minted to the lane and deposited for the buyer. The RIPE
  token therefore checks the lane/vault transfer path rather than the buyer as a token
  recipient; a RIPE-blacklisted buyer can still acquire RipeGov vault exposure if the
  MissionControl deposit allowlist permits them. Bond Room inherits the same pattern.
- `available=true` is lane-side only. A locked quote can still revert because general
  deposits are disabled, the buyer is not deposit-allowlisted, the current core-vault
  pointer is zero or does not support RIPE, RipeGov is paused, or the RIPE token is
  paused. An unlocked quote can still revert because the RIPE token is paused or the
  buyer is token-blacklisted. Any quote can also precede a purchase revert if Endaoment
  Funds id 21 resolves to the zero
  address; preview intentionally does not add that registry lookup.
- Preview itself may revert if required registry, MissionControl, RipeHq, or Ledger
  calls revert or resolve to unusable addresses. Before configuration or genesis it
  returns a zeroed unavailable quote without making those calls; after that point it is
  a dependency-aware view, not a guaranteed no-revert health endpoint.
- A quote does not include or bind the live core RipeGov vault ID. A timelocked pointer
  rotation between quote and execution may change the canonical destination; this is
  deliberate because it remains protocol-governed, while the purchase event records
  the actual vault ID. v2 does not add `expectedVaultId`.
- The mechanism assumes a canonical, dollar-denominated ERC-20 whose successful
  transfer delivers the exact requested amount. Its decimal count may vary and is
  snapshotted immutably at construction. The lane enforces exact receipt but has no
  oracle and cannot verify the token's dollar value or detect a depeg.
- Revision 18 added `ripeGovVaultId` to the then-predeployment
  `InstantBondPurchased` signature and topic. Revision 20 additionally changes config,
  rollover, override, and Foxtrot ABI surfaces. Final ABI and indexer artifacts must be
  regenerated from the revision-20 source; `ripeGovVaultId` remains data-only because
  the purchase event already uses the EVM's four-topic maximum.

### Complexity controls

- no historical storage arrays or mappings;
- no oracle or DEX interfaces;
- no partial fills;
- a governed minimum payment of at least one whole payment token;
- no delegated recipient;
- no rebaseline state machine;
- no target-epoch/window scheduler or automatic override expiry;
- one installed exact-rate override at a time;
- three explicitly tagged action types in the dedicated switchboard.

---

## 17. Test plan

> **Revision-20 local validation is complete and its evidence is recorded in §20.4.**
> This section remains the acceptance checklist for the current implementation. It
> does not authorize the deployment rehearsal subsection, remote-fork execution,
> testnet work, merge, pull-request publication, deployment, configuration, or
> activation. The separately authorized commit-and-push boundary is recorded in §20.

**Framework:** pytest + titanoboa + Vyper `0.4.3`. Tests live under
`tests/core/instantBondLane/` with dedicated switchboard tests under the appropriate
`tests/config/` path. Reuse shared token fixtures and add payment-token coverage across
multiple decimal counts.

### Constructor and configuration

- zero/non-contract payment token, missing/reverting `decimals()`, decimal counts above
  73, the registered RIPE token as payment, and zero epoch length reject;
- 0-, 6-, and 18-decimal payment tokens derive the correct immutable scale;
- every §3.3 boundary and invalid combination;
- invalid min/max ordering, `maxDownBps > decayBps`, anti-round-trip failure,
  denominator boundaries, oversized decay cap, unsafe epoch-length/payment/timing
  multiplication bounds, minimum payment outside `[PAYMENT_SCALE, cap]`,
  ceiling below `MIN_BASE_RATE`, and seed outside `[MIN_BASE_RATE, ceiling]` reject;
- first config expects version 0; version increments once; stale and out-of-order
  actions reject at execution;
- budget cannot fall below minted; valid budget reduction/raise is immediate.

### Initialization and preview

- before config, before genesis, at genesis, and after genesis;
- first call in epoch zero and first call many epochs after genesis;
- preview of uninitialized state equals first successful purchase;
- failed first purchase does not leave initialization state;
- seed change before initialization applies; after initialization it does not reset;
- after an unpurchased epoch boundary, public epoch getters retain the prior stored
  snapshot while `previewBuyNow` projects the new epoch; the next successful purchase
  advances the getters to the projected snapshot.

### Controller

- high, low, exact-threshold, and dead-band utilization;
- exact first/middle/last-block timing, amount-weighted mixed timing, and monotonic
  min/max interpolation;
- split/merge and same-block purchase-order invariance;
- offset-zero, partially elapsed first initialization, and `EPOCH_LENGTH == 1` timing
  eligibility;
- high-utilization severity endpoints, low-utilization severity endpoints, rounded
  zero utilization from a positive payment, and equal-endpoint revision-19 arithmetic
  parity for configurations admitted by revision 20;
- one sold epoch followed by one, two, and many skipped epochs, including more skipped
  epochs than the governed cap; the defensive zero-accepted stored-epoch branch is
  documented as unreachable under the current atomic write sequence rather than
  represented as a constructible test state;
- paused, disabled, and exhausted-budget gaps use identical bounded decay;
- exact inverse-price arithmetic and rounding;
- repeated high-utilization steps saturate at `MIN_BASE_RATE`, never zero;
- every valid low-utilization step strictly increases a sub-ceiling rate;
- below-minimum purchases revert; the active minimum is fixed within an epoch; a
  minimum-size low-utilization purchase cannot select a stronger individual step than
  an empty epoch;
- new tighter/looser effective floor at rollover;
- property/reference-model tests over randomized elapsed epochs and configs.

### Floor and arithmetic

- cross-product floor invariant for zero, intermediate, and maximum bonus;
- rates at and below the derived ceiling, including the `MIN_BASE_RATE` boundary;
- minimum nonzero payout and large safe boundary values;
- cap, budget, rate, base, bonus, and cumulative arithmetic cannot overflow;
- low-decimal adversarial configs that satisfy the base multiplication bound but would
  overflow `baseRipe * bonusRatio` reject in `isValidConfig`;
- conversely, fuzz valid configs across supported decimal counts at the worst-case
  purchase boundary (`paymentAmount = paymentCapPerEpoch`, base rate at the derived
  ceiling, and maximum bonus) and prove payout arithmetic never reverts and the all-in
  floor always holds.

### Lock and disclosure

- live `vMin/vMax`: zero/zero, equal positive, invalid max-below-min, below min, min,
  intermediate, max, and above max;
- RipeGov settlement event lock equals lane `actualLock`;
- change RipeGov terms within an epoch and verify live alignment plus floor safety;
- buyer with an existing RIPE gov-vault position follows RipeGov's weighted-unlock
  behavior; the quote does not misstate `actualLock` as the final account unlock;
- economic adversarial case: a large short-duration prior position followed by one or
  many maximum-lock lane purchases; measure the resulting weighted unlock, normalized
  share rounding, bonus captured, and incremental share-block commitment;
- pin the accepted expired-position case at a one-block effective duration for a
  100,000-RIPE prior position and approximately 15-RIPE max-lock payout;
- `canExit`, exit fee, no-exit, and bad-debt-freeze quote fields.

### Settlement and atomicity

- unlocked mint and current-core-vault locked settlement;
- real SwitchboardCharlie timelocked pointer rotation and post-migration locked
  settlement, including a mutation-sensitive zero-pointer fail-closed case and unusable
  target-vault rejection;
- exact Endaoment Funds receipt for standard and no-return tokens plus atomic rejection
  of false-return, zero, short/fee-on-transfer, and excess receipt on both unlocked and
  locked paths at representative 6- and 18-decimal scales;
- payment, mint, approval, Teller failure, and Teller deposited-amount mismatch roll
  back epoch/cap/budget/timing/override state and versions atomically;
- zero normal residual payment-token/RIPE and zero Teller allowance.

### Authorization and availability

- unregistered lane, HqConfig mint disabled, global mint disabled, lane disabled,
  paused, expired deadline, wrong epoch, cap exceed, budget exceed, and slippage;
- zero Endaoment Funds address rejects before payment transfer;
- preview remains narrowly scoped when Endaoment Funds is unset: it may quote available,
  while `buyNow` rejects the missing destination before transferring payment;
- anyone may buy only for self;
- inherited recovery and pause permissions retain existing behavior.

### Events and governance

- reconstruct full config history and epoch transitions from events;
- read the complete stored epoch snapshot through its public getters and reconcile it
  with initialization and rollover events;
- filter initialization, rollover, and purchase logs by indexed epoch identifiers and
  `pricingConfigVersion`;
- prove rollover events include `newPaymentCap`, `newMinPaymentAmount`, and
  `newMaxLockBonus`, alongside weighted lateness, eligibility, adjustment,
  counterfactual controller rate, and the distinctly named prior-epoch inputs;
- purchase events distinguish pricing and live config versions;
- dedicated switchboard config/override initiate, confirm, dispatch, stale execute,
  cancel, and expiration with complete action-type/payload cleanup;
- configuration initiation rejects while `actionTimeLock == 0`;
- override installation rejects before initialization, outside floor/ceiling, with an
  occupied slot, or against stale config/override versions without advancing action ID;
- same-epoch retention, preview non-consumption, exact next-successful-rollover
  application after short and long gaps, failed-settlement rollback, exactly-once
  consumption, following-epoch controller resumption, installed cancellation, and
  config invalidation;
- parallel install/cancel actions and every config/override ordering race in §12;
- a unique sentinel round trip through Foxtrot proves every duplicated
  `InstantBondConfig` field position, and CI compares the two source struct blocks to
  catch same-type field reordering that leaves the ABI selector unchanged;
- switchboard immutable target and deployed-bytecode-size checks; measure both Boa
  deployments independently, enforce EIP-170, and report whether the existing project
  anti-creep ceilings still pass. Any ceiling change requires an explicit owner
  decision and final evidence in §20.

### Coverage and validation environment

- run Vyper line and branch coverage for both contracts through the installed
  `boa.coverage` plugin, report missing lines/arcs, and enforce at least 85% combined
  branch-aware coverage across the two feature contracts;
- the source may mark only a proven defensive-only branch with `pragma: no branch`,
  accompanied by an explanation of why no committed state can reach it;
- run the focused suite and complete local suite in the repository environment, then
  repeat the focused suite in the pinned Python 3.12 validation environment before
  Phase 3 review;
- when `boa.coverage` instrumentation is active through the explicitly selected
  `.coveragerc-instant-bond`, the root test configuration rebinds Boa to a unique,
  platform-default, self-cleaning temporary compiler cache before contracts are
  loaded. Coverage therefore retains Boa's required source-map materialization while
  remaining a cold-compile measurement even if the runner has a populated default or
  explicitly configured cache. Other repository coverage runs do not activate this
  feature gate or inherit its include list and threshold;
- the root hook must fail loudly if Titanoboa removes or renames the private coverage
  state it relies on. It remains at repository root because a feature-directory
  conftest is discovered after `pytest_sessionstart`, too late to rebind compilation;
- use the combined and per-contract percentages as gates, but do not treat Boa's
  per-line `Missing` attribution as proof of an untested branch. Multi-line structs and
  chained guards are known to report phantom misses even when discriminating tests
  execute them; confirm any proposed gap with a direct or mutation-sensitive test;
- the coverage gate is serial. If a future runner opts into pytest-xdist, each worker
  receives its own unique self-cleaning compiler cache; this deliberately favors
  instrumentation correctness over cross-worker cache reuse and must be budgeted as a
  cold compile per worker. The feature-specific slowdown does not apply to unrelated
  coverage invocations;
- keep artifacts from final Python, pytest, Hypothesis, Boa, and coverage commands
  outside the worktree. Pre-existing ignored caches are not part of the exact 19-path
  candidate and are neither evidence nor authorization to delete unrelated user state.

### Deployment rehearsal

> **Phase 3 only — not authorized.** These cases remain specified and are not part of
> revision-20 local validation.

- rehearse every registry/config timelock phase on a pinned target-chain fork;
- capture dynamic `regId` values;
- verify launch remains unavailable until both config enablement and unpause;
- execute one unlocked and one locked smoke purchase with a deliberately small budget.

---

## 18. Deployment and activation

> **Deferred — Phase 3/4 not authorized.** No deployment scripts, deployment or
> configuration artifacts, fork rehearsals, testnet actions, production actions, or
> activation work may occur until a later phase is explicitly authorized by the
> owner. This does not prohibit the owner-authorized local ABI and deterministic model
> artifacts listed in §20.

Deployment is multi-phase and must honor live timelocks:

1. Finalize and record immutable inputs: canonical dollar-stablecoin payment token,
   expected token decimals/scale, `GENESIS_BLOCK`, and `EPOCH_LENGTH`; verify
   `GENESIS_BLOCK % EPOCH_LENGTH == 0`. Independently call `decimals()` and compare it
   with the deployed lane's immutable `PAYMENT_DECIMALS` and `PAYMENT_SCALE`. Read
   `MissionControl.coreRipeGovVaultId()`, require it to be nonzero, resolve it through
   VaultBook, identify the result as RipeGov, and verify that it supports RIPE. Never
   substitute a hardcoded numeric vault ID for this pointer check.
2. Determine whether the payment token is upgradeable. If it is, record its proxy and
   implementation identity/code hash and establish implementation-slot monitoring.
   Re-verify exact transfer receipt after any implementation change.
3. Deploy `InstantBondLane` paused and unconfigured.
4. Deploy `SwitchboardFoxtrot` with the lane as immutable target and action
   timelock unset during setup.
5. Before the switchboard is registered or can call the lane, call
   `setActionTimeLockAfterSetup`, verify the nonzero production timelock, and relinquish
   the temporary local governor if one was installed. This avoids any registered
   zero-timelock window; Foxtrot also rejects every action initiation while the action
   timelock remains zero.
6. Initiate registration of the dedicated switchboard in the existing Switchboard
   registry; wait; confirm.
7. Initiate lane registration in RipeHq; wait the registry timelock; confirm and
   capture the returned `regId`. Never hardcode a guessed id.
8. Initiate `HqConfig(regId, canMintGreen=false, canMintRipe=true,
   canSetTokenBlacklist=false)`; wait; confirm.
9. Queue the initial lane config with `expectedVersion=0`, `canBuyNow=false`, and a
   deliberately small calibrated cap/budget; wait; execute. Verify version 1 and all
   emitted fields. Keep the Department paused.
10. Verify preview remains unavailable while paused/disabled and that RipeHq recognizes
   the lane as an authorized RIPE minter.
11. Queue a full config with `expectedVersion=1` and `canBuyNow=true`; wait; execute.
   While still paused, verify `previewBuyNow` shows the intended rate and
   `pricingConfigVersion == liveConfigVersion`; this proves any prospective floor
   tightening is active at the simulated rollover. Unpause through the established
   SwitchboardCharlie governance path only after the enabling config is confirmed.
12. Execute small unlocked and locked smoke purchases. Verify exact Endaoment receipt,
    cumulative mint accounting, event versions, the actual `ripeGovVaultId`, lock
    disclosure, and settlement. Regenerate and verify the final event ABI/topic before
    configuring indexers.
13. While paused, rehearse an exact override at both valid endpoints: queue, wait,
    install, preview the next rollover without consumption, execute a purchase that
    commits the exact target, and verify the following ordinary controller transition.
    Separately rehearse installed cancellation and config invalidation.

Before any initial or replacement lane config is queued, the proposal must calculate
and record, using arbitrary-precision off-chain arithmetic:

```text
worstCaseEpochMint = paymentCapPerEpoch * maxEffectiveRate // PAYMENT_SCALE
targetBlocksPerDay = ceil(86_400 / targetChainBlockSeconds)
maxEpochsTouchedPerDay = ceil(targetBlocksPerDay / EPOCH_LENGTH) + 1
worstCaseRollingDayMint = worstCaseEpochMint * maxEpochsTouchedPerDay
remainingLaneBudget = mintBudget - cumulativeMinted
```

The extra epoch in the rolling-day bound conservatively covers a 24-hour window that
begins and ends inside different lane epochs. The proposal must compare all four values,
the underlying decimal scale, and the proposed lifetime `mintBudget` with separately
recorded owner-approved limits. No action may be queued or executed if a value is
missing, implausibly scaled, above its approved limit, or not independently reviewed.
This is the owner-selected hard deployment/reconfiguration gate; v2 deliberately does
not hard-code an arbitrary epoch-to-budget ratio in contract validation.

A config that was valid when queued can become invalid before execution if purchases
raise `cumulativeMinted` above its proposed `mintBudget`. The execution must fail
closed. Operators must re-read the live version and cumulative minted amount, update
the full config, and queue a fresh action; an execution revert in this case is expected
behavior, not a reason to bypass lane validation.

The first successful purchase initializes at the current deterministic epoch and uses
the latest seed. A manual override is unavailable before initialization. After
initialization, an override is an optional, separately timelocked recovery tool and is
not part of ordinary activation.

Decommission with `canBuyNow=false`, pause, or lane deregistration. Recover only truly
stranded assets through the inherited governed recovery path.

Operations must treat widespread `payment receipt mismatch` failures as a payment-token
incident, not merely a lane-config problem. Investigate proxy implementation changes,
blocklist/no-op behavior, fees, transfer-side rebasing, or other semantic drift before
reenabling purchases. Exact receipt intentionally fails closed.

---

## 19. Remaining inputs: calibration only

> **Deferred outside revision-20 delivery.** Calibration is not required to complete
> local contract verification. The current authorization does not include production
> deployment datasets or configuration artifacts.

All product and engineering semantics are settled in this specification. The only
remaining inputs are economic calibration and final live-state discovery:

- `EPOCH_LENGTH`;
- canonical dollar-stablecoin `PAYMENT_TOKEN` and its expected decimals;
- `paymentCapPerEpoch`;
- `minPaymentAmount`;
- initial and maximum planned `mintBudget`;
- `uLowBps` / `uHighBps`;
- `minUpBps` / `maxUpBps` / `minDownBps` / `maxDownBps` / `decayBps`;
- governed `maxDecayEpochs` (hard ceiling 32);
- `maxEffectiveRate` and `seedRate`;
- `maxLockBonus` (hard ceiling 1000%);
- live RipeGov min/max lock durations and their arithmetic plausibility; and
- live registry identities and the dynamic core-vault pointer as nonbinding preflight
  assertions, never hardcoded execution inputs.

Calibration values must satisfy §3.3 and should be selected with the simulation work
described in `pricing-design.md`. Placeholder values may be used in unit tests, but no
placeholder value may enter a deployment artifact or activation proposal.
The deterministic `controller-simulation-v2.json` artifact validates integer mechanism
behavior but remains explicitly `calibration_status: not_approved`; its fixture and
paths are not production recommendations. Production review must pin acceptable fast-
demand catch-up, weak-demand decline, empty decay, oscillation, and override-deviation
bounds before choosing the five adjustment parameters.
Initial `maxLockBonus` and `paymentCapPerEpoch` must also bound the accepted weighted-lock
exposure in §16; scaling either requires monitoring evidence from the limited launch.
Governance validation does not impose a useful upper bound on RipeGov
`maxLockDuration`; deployment review must reject values large enough to threaten the
lane's lock-bonus multiplication even though such nonsense input fails closed.
Choose `paymentCapPerEpoch` as a clean multiple of `minPaymentAmount` when practical;
otherwise up to `minPaymentAmount - 1` base units of epoch capacity can be stranded and
unpurchaseable. Calibrate `EPOCH_LENGTH` against target-chain block time and expected
transaction latency because `expectedEpoch` is an exact execution-time match and
transactions crossing a boundary revert. Deployment review must independently sanity
check the immutable genesis block and epoch length; the constructor rejects zero and
arithmetically unsafe epoch lengths but deliberately does not embed chain-specific
timing windows. The
effective issuance bound is not the epoch cap alone: it is
`paymentCapPerEpoch * maxEffectiveRate // PAYMENT_SCALE` per `EPOCH_LENGTH` blocks.
Those three economic inputs and the target-chain block time must be calibrated and
approved together using the rolling-day gate in §18; a very short epoch converts an
otherwise modest cap into a high-frequency issuance allowance.

---

## 20. Revision-20 authorization, changed-file scope, and evidence

### 20.1 Current owner authorization and prohibited actions

The owner authorized revision-20 implementation, documentation/model reconciliation,
tests, deterministic ABI regeneration, local validation, one commit on the existing
`instant-bond-lane` branch, and push of that branch. Commit and push are explicit
authorizations; neither implies authorization for any later lifecycle step.

The current owner authorization does **not** include:

- merging into another branch;
- opening or publishing a pull request;
- remote-fork execution, testnet rehearsal, or production-chain interaction;
- deployment, registry changes, configuration, RIPE minting, or activation;
- production calibration datasets or operator proposals; or
- publication beyond the authorized branch push.

At this specification pass, the concrete revision-20 changed-file inventory is:

Production contracts:

1. `contracts/core/InstantBondLane.vy`
2. `contracts/config/SwitchboardFoxtrot.vy`

Normative, rationale, deterministic model, and generated ABI artifacts:

1. `docs/instant-bond-lane/implementation-spec.md`
2. `docs/instant-bond-lane/pricing-design.md`
3. `docs/instant-bond-lane/dynamic-controller-proposal.md`
4. `docs/instant-bond-lane/controller-simulation-v2.json`
5. `scripts/simulations/instant_bond_lane_controller.py`
6. `scripts/abis/InstantBondLane.json`
7. `scripts/abis/SwitchboardFoxtrot.json`

Feature tests and fixtures:

1. `tests/config/test_switchboard_foxtrot.py`
2. `tests/core/instantBondLane/conftest.py`
3. `tests/core/instantBondLane/test_constructor_config.py`
4. `tests/core/instantBondLane/test_controller.py`
5. `tests/core/instantBondLane/test_lifecycle_purchase.py`
6. `tests/core/instantBondLane/test_lock_settlement.py`
7. `tests/core/instantBondLane/test_properties_abi.py`
8. `tests/core/instantBondLane/test_robinhood_mainnet_fork.py`
9. `tests/core/instantBondLane/test_simulation.py`
10. `tests/core/instantBondLane/test_stateful_fuzz.py`

The generated ABI deltas above are the owner-authorized deterministic regeneration,
not a separate API-design surface. No unrelated file is implicitly writable merely
because it would be convenient for validation.

### 20.2 Required revision-20 local validation

Validation must bind the final candidate, use private temporary caches/data paths, and
include:

- focused pytest over `tests/core/instantBondLane/` and
  `tests/config/test_switchboard_foxtrot.py`, including the stateful model;
- the deterministic simulator's `--check` against
  `docs/instant-bond-lane/controller-simulation-v2.json`;
- directly affected BondRoom, RipeGov, SwitchboardDelta, and TimeLock regressions;
- the complete default-local `tests/` suite, or an exact failure/deselection record if
  repository baseline debt prevents a green claim;
- cold-cache Vyper line and branch coverage for both feature contracts through
  `.coveragerc-instant-bond`;
- focused-suite repetition in the pinned Python 3.12 validation environment;
- Boa deployed-runtime measurement for both contracts, EIP-170 enforcement, and an
  explicit result against the owner-approved revision-20 project anti-creep ceilings;
- ABI export, event signature/indexing, method identifier, public getter, and storage
  layout reconciliation against the exact revision-20 source;
- deterministic ABI export inventory checks;
- `git diff --check`, stale-term checks for superseded controller/override semantics,
  and pinned-environment `pip check`; and
- a final changed-file manifest before commit and a remote-ref identity check after
  the authorized push.

Any production source change after a validation run invalidates that run's source
hashes, bytecode, ABI/layout, coverage, and test evidence until regenerated. Preview or
model-only checks do not substitute for contract tests.

### 20.3 Historical evidence — revisions 18 and 19 only

The following measurements are preserved for provenance. They are bound to their
historical source and **must not** be presented as revision-20 evidence: revision 20
changes controller economics, config tuples, storage, selectors, events, Foxtrot
dispatch, tests, and runtime.

Historical revision-18 evidence recorded on 7 August 2026:

- 102 focused feature/configuration tests passed and two explicitly opt-in fork cases
  skipped in both the active and pinned environments;
- the state machine passed 50 examples with 20 generated actions per example;
- the revision-17 complete default-local suite reported 2,605 passed and 142
  fork-dependent tests deselected. A revision-18 attempt stopped at 77% after 2,557
  passed, 2 skipped, and 278 deselected because the RH-integrated baseline produced 12
  failures and 25 cascading errors outside that correction pass. This was recorded as
  baseline test debt, not a green complete-suite claim;
- combined branch-aware Boa coverage was 87.1% (`InstantBondLane.vy`: 85.8%;
  `SwitchboardFoxtrot.vy`: 96.2%), with the cold-cache safety hook reproducing the
  result and cleaning its temporary compiler cache;
- pinned runtime bytecode measured 8,669 bytes for the Lane and 5,069 bytes for
  Foxtrot, against the then-current 9,000-byte and 5,500-byte project ceilings; and
- the pinned environment reported no broken Python requirements.

Historical revision-19 evidence recorded on 11 August 2026:

- Vyper `0.4.3+commit.bff19ea2` compiled both contracts; active and pinned Python 3.12
  environments each reported 102 focused tests passed and two opt-in fork tests
  skipped, including the 50-example, 20-action stateful model;
- directly affected BondRoom, RipeGov, SwitchboardDelta, and TimeLock regressions
  reported 379 passed; the complete suite was not rerun;
- fresh cold-cache branch-aware coverage reported 86.31% combined. The Lane reported
  288 statements, 19 missed, 68 branches, 35 partial branches, and 84.8%; Foxtrot
  reported 50 statements, none missed, four branches, two partial branches, and 96.3%;
- the change from revision 18's 313 Lane statement locations to 288 was attributed to
  repository-standard one-line call formatting, with the same misses and partial
  branches, rather than to less executed behavior;
- compiled runtime bytecode measured 8,669 bytes for the Lane with binary SHA-256
  `37c046ecf03ecc046892dd0c46d40eab4d23d3243a1fb33e6019fda8d1b4c15e` and
  5,068 bytes for Foxtrot with binary SHA-256
  `c7036ba870f0320e54aa5865515bc33aa09d83f8239be47c093be0e7b4bd262f`;
- method identifiers and storage layout matched `c1e9718`; the Lane ABI matched and
  Foxtrot's only ABI metadata delta was `_actionId` to `_aid` on its two pending-action
  functions;
- the ABI exporter reported 54 outputs, with `InstantBondLane.json` SHA-256
  `c89b70b189b99680d6454562fbba0e39b2d6a978277c50b81861c7ceb6d098d9` and
  `SwitchboardFoxtrot.json` SHA-256
  `82d212307993f7e2d78df258b7c4f90f126634ef3f372ad16f080b659d49f1a7`;
- `git diff --check` and pinned-environment `pip check` passed; the Lane source was
  bound to SHA-256
  `fea86d2c072bf06eb8bbffed6a6be5289abe778cb29a22594f527b29ce7254c3`
  and Foxtrot to
  `25178dd5e07e04a8be7a8952b8244cbef28d0588cc027192f504b649c285c4c0`.

The earlier local wrap-up commit
`020a4f1da397ad9ac9c617000053609eb44fa209` and patch SHA-256
`9bcf1e43549733ea08f5f6db3eaa81a1f4a6e26a64fbbe2175113ea4dad6ef33`
are also historical provenance, not the revision-20 candidate or current Git
authorization boundary.

### 20.4 Final revision-20 local evidence

The final local candidate is bound to starting commit
`ad782c80b2f4bfa73d7dcd8c9c4979903b767b96` and the exact 19 paths listed in §20.1.
The production source hashes are:

- Lane: `39cb6ac4df0870f224c84b97b93521b9f565d0a7842c0f5c500c03315c560d7b`;
- Foxtrot: `42d33168684e0e5fd16c4c2591fc2534ceb6036fc24e63dc65c11e13b79109aa`.

Fresh revision-20 validation produced the following evidence:

- active and pinned environments both used Python 3.12.0. The active environment used
  pytest 8.4.2 and Vyper import version 0.4.3; both Vyper CLIs reported
  `0.4.3+commit.bff19ea2`. Pinned `pip check` reported no broken requirements;
- the complete focused Lane/Foxtrot selection, including deployed-runtime and stateful
  tests, reported 145 passed and two expected opt-in fork skips in both environments.
  The active run completed in 334.69 seconds with three benign assertion-rewrite
  warnings caused by early cache-isolation imports; the pinned run completed in 330.91
  seconds with the same three warnings;
- the stateful differential model separately passed one Hypothesis test with 50
  examples and 20 mixed lifecycle steps per example; directly affected BondRoom,
  RipeGov, SwitchboardDelta, and TimeLock regressions reported 379 passed;
- the default-local suite reported 3,349 passed, 13 failed, two skipped, 278 deselected,
  one expected failure, and 25 setup errors. No Lane or Foxtrot test failed. Twelve
  failures and all 25 errors reproduce the existing pointer/oracle, Teller block-clock,
  Deleverage, and BlueChip constructor-fixture baseline. The thirteenth failure is the
  pre-existing stale basic-vault consumer inventory; that inventory, its test, and all
  seven scanned source files are byte-identical to `HEAD` and absent from this diff;
- cold-cache branch-aware coverage over the complete focused selection reported 145
  passed and two skipped. Lane reported 391 statements, 27 missed, 88 branches, 45
  partial branches, and 85.0%; Foxtrot reported 110 statements, none missed, 14
  branches, seven partial branches, and 94.4%; combined coverage was 86.90% from 501
  statements, 27 missed, 102 branches, and 52 partial branches, above the 85% gate;
- Boa deployed runtime measured 10,564 bytes for Lane and 6,051 bytes for Foxtrot. The
  owner explicitly approved revision-20 project ceilings of 11,000 and 6,500 bytes,
  leaving 436 and 449 bytes of project-gate headroom. EIP-170 headroom is 14,012 and
  18,525 bytes respectively;
- `scripts/export_abis.py --check` reported all 54 ABI outputs current, with 45 Vyper
  sources intentionally excluded; the ABI test suite reported nine passed. The Lane
  ABI SHA-256 is
  `6dd92faa586b6ff3ca9d9e88ed40ccf37d5b802db26d74769a9b4793ca34582b`
  and the Foxtrot ABI SHA-256 is
  `00c831a45f751c1af458b4de3e75916b508279e7fbb22d48f117320b10f37963`;
- the canonical compact-JSON method-identifier hashes are
  `9a7a1ec490a6353d5a1a66848ef83d5b801d0211d623f74a4b70c10b1b867cbe`
  for Lane and
  `ab6a154a88c5ba9981c0656dcab620cf3aa63894b81d0e7ef2abe699eac191c7`
  for Foxtrot. The corresponding storage-layout hashes are
  `20d6ee775ce7f7d6d3e139c38296ff2ddc471928e8e2a1b7db6804d7baecf14c`
  and `fa76a8aaab85abaa26d9fd5d1c314b4a9e415dad81f474b83cf205b1f0b3727a`;
  focused ABI tests also passed exact struct order, selectors, event signatures and
  indexing, public getter shapes, and mirrored Lane/Foxtrot config fields;
- the deterministic simulator `--check` passed, its 12-test suite passed, and the
  canonical artifact SHA-256 is
  `f8a528bf61d1605d4f90b3a5fa8806d139b783ce2c7c22e918299073998cbde4`;
- scoped stale-term checks found no superseded revision-19 config field, override-window,
  constant-suffix, action-ID, or `# dev:` notation in the current contracts and
  generated interfaces; `git diff --check` passed and no validation cache or output
  entered the 19-file candidate.

The repository's separately scoped frozen-contract inventory remains red for a
pre-existing `MissionControl.vy` expectation mismatch: its 37 passing and four failing
inventory tests are not caused by either revision-20 contract, and the frozen Robinhood
inventory intentionally does not include this feature. That baseline debt and the
default-suite limitations above are recorded rather than concealed or modified outside
the authorized scope.

The commit containing this paragraph cannot include its own Git identity. The
authorized commit ID, tree, pushed branch name, and local/remote equality therefore
belong in the external final handoff after the push. That Git publication does not
authorize merge, pull-request publication, deployment, configuration, or activation.

### 20.5 Later phases remain unauthorized

Remote-fork execution, testnet rehearsal, deployment, configuration, and activation
remain outside revision-20 authorization. A later explicit owner instruction is
required before following §17's deployment rehearsal or §18's production sequence.
Merge and pull-request publication likewise require separate authorization even after
the branch is committed and pushed.

---

## 21. Revision history

This in-document history starts prospectively at revision 13. Revisions 9, 11, and 12
below are reconstructed from the observable reviewer snapshots and feedback artifacts,
not from committed document baselines. No durable document state is claimed for
revision 8 or 10, so those numbers are intentionally omitted. This table is not a
substitute for establishing a Git baseline when the owner separately authorizes Git
actions.

| Revision | Date | Summary |
|---:|:---|:---|
| 9 | 5 August 2026 | Generalized the payment asset and decimal scale; added the epoch minimum, controller bounds, lock-term fallback, deposit equality check, and timelock setup guard. |
| 11 | 5 August 2026 | Corrected compiler mutability and low-decimal bonus bounds; added defensive reentrancy and version handling; expanded threat-model guidance; exposed stored epoch state; completed and indexed epoch events; recorded permissionless access and the narrow preview scope. |
| 12 | 5 August 2026 | Clarified lazy getter semantics and preview limitations; disambiguated and indexed rollover fields; restored Foxtrot's version read-back; expanded Phase 2 event and arithmetic properties. |
| 13 | 5 August 2026 | Removed incorrect borrowed banner art; added Foxtrot-specific sub-art; indexed pricing config versions consistently; documented deliberate event-name asymmetry; corrected revision provenance. |
| 14 | 5 August 2026 | Recorded Phase 2 authorization and exact scope; explicitly ratified pricing-version topic allocation; corrected the defensive-only empty-state specification; added contract-backed controller properties, branch coverage, settlement safety-net, event-topic, boundary, and pinned-environment requirements. |
| 15 | 6 August 2026 | Added owner-authorized rule-based stateful differential fuzzing over mixed lifecycle, governance, settlement, and rollback sequences; reconciled the focused, coverage, and complete-suite evidence without changing contract code. |
| 16 | 6 August 2026 | Rejected RIPE as the immutable payment token; made coverage cold-cache-safe; recorded owner-selected non-hard-coded issuance gates, epoch-frequency calibration, four-budget supply monitoring, and the pre-merge baseline requirement. |
| 17 | 6 August 2026 | Recorded the owner-authorized local commit and pricing-rationale reconciliation; made the dedicated coverage gate platform-neutral, self-cleaning, fail-safe, and inert for unrelated coverage runs; added coverage-data ignores and a distinct RIPE-payment diagnostic. |
| 18 | 7 August 2026 | Aligned locked settlement with RH's dynamic core-vault pointer; enforced exact Endaoment receipt; disclosed the actual settlement vault; reconciled migration/fork/adversarial tests; quantified the owner-accepted weighted-lock dilution; rebound RH source anchors; refreshed runbook, coverage, runtime, and authorization evidence; and incorporated the independent mutation/security review. |
| 19 | 11 August 2026 | Normalized both feature contracts to repository Vyper conventions; reconciled constant, local, action-ID, invariant, and diagnostic notation; added canonical ABI exports; documented the Foxtrot ABI-metadata rename and Boa source-location coverage shift; and refreshed focused, coverage, runtime, ABI/layout, export, regression, and environment evidence without changing successful-path semantics or storage. |
| 20 | 11 August 2026 | Added bounded utilization-and-timing controller ranges, first-partial-epoch eligibility, exact next-successful-rollover overrides with independent optimistic versioning, three-action Foxtrot dispatch, revised config/state/events/APIs, deterministic model artifacts, and expanded tests; recorded the exact owner-authorized source/document/model/test/ABI/commit/push scope while reserving merge, pull-request, deployment, configuration, and activation; owner-approved the revision-20 runtime ceilings; and recorded fresh focused, coverage, runtime, ABI/layout, simulator, regression, environment, and exact baseline-limitation evidence while preserving revisions 18/19 measurements as historical. |
