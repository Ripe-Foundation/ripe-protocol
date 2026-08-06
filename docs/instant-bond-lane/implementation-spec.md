# Instant Bond Lane — Implementation Specification

**Mechanism version:** v1 · **Specification revision:** 17

**Status:** Implementation-ready specification. Economic calibration remains a
deployment input. This document does **not** authorize deployment, production
configuration, RIPE minting, activation, or publication.

**Prepared:** 5 August 2026 · **Revised:** 6 August 2026 (committed-candidate
portability, coverage isolation, and authorization reconciliation)

**Companion:** pricing rationale in [`pricing-design.md`](pricing-design.md). This
specification is authoritative wherever the documents differ.

**Worktree:** `ripe-protocol-instant-bond-lane`, branch `instant-bond-lane`, from
`master` at `91eda49`.

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
    final topic allocation after Phase 2 review; `liveConfigVersion` remains present as
    non-indexed purchase-event data.
15. RIPE is the sole hardcoded payment-token exclusion because accepting the minted
    asset would create a self-referential mint path. GREEN may be a legitimate
    dollar-stable payment asset. Savings GREEN and other yield-bearing or
    value-accruing wrappers are not assumed to remain worth one dollar per token and
    require explicit valuation-aware calibration and owner approval; v1 deliberately
    does not hardcode a chain-specific asset allowlist.

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
  `downBps <= decayBps`.
- Config events emit all fields rather than only a hash.
- Rollover events emit the complete new epoch snapshot as well as the previous epoch's
  utilization inputs.
- Pricing config versions are indexed consistently across initialization, rollover,
  and purchase events for monitoring.
- Preview remains a lane-side quote with a boolean availability signal. It does not add
  a reason-code ABI or attempt to preflight every downstream dependency.
- Governance uses a small dedicated `SwitchboardFoxtrot`; no existing contract is
  modified. `Foxtrot` follows the repository's NATO phonetic sequence after the
  already-existing `SwitchboardEcho`.
- Delivery is owner-gated. Phase 1 source work is complete and Phase 2 tests and local
  validation were separately authorized. The owner later authorized local wrap-up and
  commits on the existing `instant-bond-lane` branch; that authority does not include
  merge, push, pull-request publication, Phase 3 fork/testnet work, deployment, or
  activation. The exact current scope and validation commands are recorded in §20.

---

## Fresh-agent Phase 1 execution contract

This document contains all product and engineering context required for Phase 1. A
fresh implementer must follow this start contract before editing:

1. Work only in `/Users/wigglez/dev/ripe-protocol-instant-bond-lane`. The bound
   baseline is branch `instant-bond-lane` at commit
   `91eda49ccd34a25090582aff0695075c4c806011`. If either fact differs, stop without
   editing and report the drift.
2. Read this specification completely. It is normative. `pricing-design.md` is
   optional economic rationale and cannot override this file.
3. Read-only inspection of any repository file is allowed and expected; the Phase 1
   ceiling restricts writes, not reads. Use §10.1 for exact source anchors. In
   particular, use `BondRoom.vy`, `Addys.vy`, `DeptBasics.vy`, `ConfigStructs.vyi`,
   `RipeGov.vy`, `Teller.vy`, `RipeHq.vy`, and `RipeToken.vy` for the lane, and use
   `SwitchboardDelta.vy`, `LocalGov.vy`, and `TimeLock.vy` for the switchboard's
   structural conventions.
4. Implement the two contracts in §1 completely, with no TODOs, placeholders, stubs,
   or omitted normative behavior. Do not change the architecture, economics, public
   workflows, or names without explicit owner authorization. Do not create a shared
   interface file; duplicate the small feature-specific ABI structs in the two
   contracts when required.
5. If the specification conflicts with the bound source or cannot be implemented
   within the contract-source ceiling, stop and report the exact conflict instead of
   guessing, broadening scope, or modifying an existing contract.
6. Obey the prohibited-action list in §20. After writing the two source files and any
   explicitly authorized normative revision, provide a concise source-only handoff that
   names the changed files and identifies any uncertainty left solely because
   compilation and validation are forbidden, then stop for owner review.

---

## 1. Scope and minimal architecture

Build exactly two contracts at these paths:

1. `contracts/core/InstantBondLane.vy` — a core Department that accepts a canonical
   dollar-denominated ERC-20 payment token, derives its immutable decimal scale,
   computes a fixed base payout rate per lane epoch, applies an optional lock bonus,
   enforces an epoch payment cap, minimum purchase, and cumulative mint budget,
   forwards proceeds to Endaoment Funds, and mints RIPE unlocked or into RipeGov
   through Teller.
2. `contracts/config/SwitchboardFoxtrot.vy` — a single-purpose LocalGov +
   TimeLock adapter that queues and executes complete lane-config replacements.

For Phase 1 contract implementation, these are the only contracts that may be created
or edited. The current owner-review pass additionally authorizes the normative
specification update recorded in §20. The implementation may import existing repository
modules and interfaces, but it must not modify them. Any new feature-specific structs,
events, constants, or narrow interface declarations needed by the lane must live inside
these two contracts, even if that requires a small amount of duplication between them.

Existing-system state changes are limited to registering the new switchboard,
registering the lane as a RIPE minter, and installing its configuration. There are
**no source changes** to MissionControl, Ledger, RipeToken, RipeGov, BondRoom,
SwitchboardAlpha, SwitchboardBravo, SwitchboardCharlie, SwitchboardDelta, or
SwitchboardEcho.

Out of scope for v1: external-price oracles, DEX guards, tranche schedules,
sellout-time acceleration, self-updating solvency floors, delegated purchases,
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
import interfaces.ConfigStructs as cs
from interfaces import Department
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
    assert _epochLength != 0                                # dev: invalid epoch length

    paymentDecimals = IERC20Detailed(_paymentToken).decimals()
    assert paymentDecimals <= MAX_PAYMENT_DECIMALS_CONST    # dev: invalid payment decimals

    addys.__init__(_ripeHq)
    assert _paymentToken != addys._getRipeToken()           # dev: payment token is ripe
    deptBasics.__init__(True, False, True)  # paused, no GREEN mint, RIPE mint

    PAYMENT_TOKEN = _paymentToken
    PAYMENT_DECIMALS = paymentDecimals
    PAYMENT_SCALE = 10 ** paymentDecimals
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
scale; it does not establish dollar denomination, intended stablecoin identity, transfer
semantics, stable value, or absence of proxy risk.

`RIPE_GOV_VAULT_ID = 2` follows the existing protocol assumption. Fork and live
preflight must verify that id 2 still resolves to RipeGov and supports the RIPE token;
the lane must not deploy against a topology where that assumption is false.

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
    upBps                # price-up step; stored inverse rate moves down
    downBps              # price-down step; stored inverse rate moves up
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

cumulativeMinted        # all RIPE minted by the lane, including bonuses
```

No epoch-history mapping is stored. Events are the historical audit record.

Required read ABI exposes `PAYMENT_TOKEN`, `PAYMENT_DECIMALS`, `PAYMENT_SCALE`,
`GENESIS_BLOCK`, and `EPOCH_LENGTH` as public immutables; `config`, `configVersion`,
and `cumulativeMinted` are public. The complete stored epoch snapshot is also public:
`isInitialized`, `currentEpoch`, `epochRate`, `epochPaymentCap`,
`epochMinPaymentAmount`, `epochMaxLockBonus`, `epochPricingVersion`, and
`epochAcceptedPayment`. The switchboard depends on `configVersion()`, while operators
and indexers can compare live configuration, stored epoch state, cumulative issuance,
and the read-only projection returned by `previewBuyNow`. These getters are a stored
snapshot, lazily advanced only by a successful `buyNow`; after a block-clock boundary
they can describe the prior epoch until the next purchase. Integrations must use
`previewBuyNow` for current pricing and must never construct a quote directly from
`epochRate` or the other stored epoch getters.

### 3.2 Hard constants

```text
HUNDRED_PERCENT              = 10_000
RIPE_GOV_VAULT_ID            = 2
MAX_LOCK_BONUS_CONST         = 100_000  # 1000%, aligned with existing bond ceiling
MAX_PRICE_STEP_BPS_CONST     = 10_000   # at most a 100% price-up step
MAX_DECAY_EPOCHS_CONST       = 32       # hard gas/velocity bound
MAX_PAYMENT_DECIMALS_CONST   = 73       # PAYMENT_SCALE remains arithmetically usable
MIN_BASE_RATE                = 10_000   # engineering liveness floor
```

`maxDecayEpochs` may be governed below 32 but not above it. Thirty-two is an
engineering safety ceiling, not a recommended production value.

### 3.3 Required validation

The lane is the authority for config validity. `setConfig` must enforce all of the
following on every config, including the first:

```text
0 <= uLowBps < uHighBps <= 10_000
0 < downBps < upBps <= MAX_PRICE_STEP_BPS_CONST
downBps <= decayBps < 10_000
0 < maxDecayEpochs <= MAX_DECAY_EPOCHS_CONST

0 < maxEffectiveRate <= max_value(uint256) / 10_000
PAYMENT_SCALE <= minPaymentAmount <= paymentCapPerEpoch
paymentCapPerEpoch <= max_value(uint256) / 10_000
paymentCapPerEpoch * maxEffectiveRate <= max_value(uint256)

maxLockBonus <= MAX_LOCK_BONUS_CONST
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
recovery formula from becoming an integer fixed point for any valid `downBps`; it is
still economically tiny and does not replace calibrated operator bounds or unit-aware
tooling. The conservative `paymentCapPerEpoch * maxEffectiveRate` bound makes the base
payout multiplication safe before division. Variable-decimal payment tokens require a
separate bound on `maxBaseRipe * maxLockBonus`, because the bonus multiplication occurs
before division by `HUNDRED_PERCENT`; without that bound, otherwise-valid configs for
low-decimal tokens could revert during payout calculation. Purchase code compares
`totalRipe` with `mintBudget - cumulativeMinted`; it does not use an unchecked
`cumulativeMinted + totalRipe` expression.

Expose `isValidConfig(config) -> bool` for tooling and the dedicated switchboard.
The lane repeats/asserts the validation during execution; a switchboard precheck is
not a security boundary.

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
- `vMin == vMax > 0` gives the full bonus without division by zero.
- `vMin == vMax == 0` gives no bonus and settles unlocked.
- Invalid live terms with `vMax < vMin` fail safely to an unlocked, zero-bonus payout
  rather than underflowing the quote path.
- The value passed to Teller is the same `actualLock` used for the bonus.
- The lane's bonus magnitude is independent of RipeGov's governance-points boost.

`actualLock` is the **new-deposit duration passed to RipeGov**, not necessarily the
buyer's final account unlock. RipeGov combines a new deposit with any existing RIPE
gov-vault shares using its normalized-share-weighted, whole-block unlock calculation
(`RipeGov.vy:696-721`). The weighting approximately transfers the new deposit's
share-duration commitment across the combined position, but a dominant short-duration
existing position can make the final calendar unlock materially shorter than
`block.number + actualLock`. Integer normalization and final division can further
round down the incremental extension, including to zero blocks in an extreme share
ratio. The UI must label `actualLock` as the deposit lock and must not present it as
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
isInitialized        = True
```

`seedRate` is validated at or below its derived base-rate ceiling, so initialization
does not silently clamp a misconfigured seed.

Epochs between genesis and the first successful initialization are intentionally
ignored. This is cold-start behavior: the lane begins at `seedRate` in the then-current
epoch rather than decaying before it has ever been active.

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
    elapsed = e - currentEpoch
    newCeiling = baseRateCeiling(cfg.maxEffectiveRate, cfg.maxLockBonus)

    # Clamp before multiplication. Validation guarantees rate * 10_000 is safe.
    rate = min(epochRate, newCeiling)

    if epochAcceptedPayment == 0:
        # Includes the stored epoch that just completed.
        decaySteps = min(elapsed, cfg.maxDecayEpochs)
        utilizationBps = 0
    else:
        utilizationBps = epochAcceptedPayment * 10_000 // epochPaymentCap

        if utilizationBps >= cfg.uHighBps:
            # Price up, inverse rate down.
            rate = max(
                rate * 10_000 // (10_000 + cfg.upBps),
                MIN_BASE_RATE,
            )
        elif utilizationBps <= cfg.uLowBps:
            # Price down, inverse rate up.
            rate = min(
                rate * 10_000 // (10_000 - cfg.downBps),
                newCeiling,
            )

        # The sold stored epoch was handled once above. Only skipped epochs decay.
        decaySteps = min(elapsed - 1, cfg.maxDecayEpochs)

    for i: uint256 in range(decaySteps, bound=MAX_DECAY_EPOCHS_CONST):
        rate = min(
            rate * 10_000 // (10_000 - cfg.decayBps),
            newCeiling,
        )

    currentEpoch         = e
    epochRate            = rate
    epochPaymentCap      = cfg.paymentCapPerEpoch
    epochMinPaymentAmount = cfg.minPaymentAmount
    epochMaxLockBonus    = cfg.maxLockBonus
    epochPricingVersion  = configVersion
    epochAcceptedPayment = 0

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
        utilizationBps=utilizationBps,
        decaySteps=decaySteps,
        pricingConfigVersion=configVersion,
    )
```

The pre-rollover event values must be captured into locals before any epoch state is
overwritten, as shown above.

The inverse-price formulas are exact. A naive `rate * (10_000 - upBps) / 10_000`
must not replace the price-up formula. `MIN_BASE_RATE` prevents repeated price-up
steps from rounding the inverse rate permanently to zero and ensures every valid
low-utilization recovery step can increase a sub-ceiling rate. It is a liveness bound,
not the treasury price floor. The `downBps <= decayBps` constraint prevents a
minimum-size low-utilization purchase from selecting a stronger individual price-down
step than a fully empty epoch, while the governed minimum payment makes selecting that
branch economically non-dust.

### 7.1 Empty and unavailable epochs

An empty epoch decays whether the absence of sales came from demand, pause,
`canBuyNow=false`, exhausted budget, frontend downtime, or any other cause. A single
rollover applies at most `maxDecayEpochs` decay steps.

There is no rebaseline function and no pause timestamp. This is deliberate: one rule
is easier to reason about and test, while the hard floor and decay cap bound a long
outage's effect.

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
3. If initialized but stale: simulate §7 without writing.
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

```text
1.  assert configVersion != 0                                  # dev: not configured
2.  assert block.number >= GENESIS_BLOCK                       # dev: before genesis
3.  assert not deptBasics.isPaused                             # dev: paused
4.  cfg = live config; assert cfg.canBuyNow                    # dev: disabled
5.  a = addys._getAddys()
    assert RipeHq(a.hq).canMintRipe(self)                     # dev: mint unavailable
6.  endaomentFunds = addys._getEndaomentFundsAddr()
    assert endaomentFunds != empty(address)                    # dev: no destination
7.  assert block.number <= deadlineBlock                       # dev: expired

8.  initialize if needed; otherwise rollover if needed
9.  assert expectedEpoch == currentEpoch                       # dev: epoch moved

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

14. epochAcceptedPayment += paymentAmount                      # effects
    cumulativeMinted   += totalRipe

15. assert IERC20(PAYMENT_TOKEN).transferFrom(
        msg.sender,
        endaomentFunds,
        paymentAmount,
        default_return_value=True,
    )                                                          # dev: payment failed

16. if actualLock == 0:
        assert RipeToken(a.ripeToken).mint(msg.sender, totalRipe)
                                                                  # dev: mint failed
    else:
        assert RipeToken(a.ripeToken).mint(self, totalRipe)     # dev: mint failed
        assert IERC20(a.ripeToken).approve(
            a.teller,
            totalRipe,
            default_return_value=True,
        )                                                       # dev: approval failed
        depositedAmount = Teller(a.teller).depositFromTrusted(
            msg.sender,
            RIPE_GOV_VAULT_ID,
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
        )                                                       # dev: approval failed

17. emit InstantBondPurchased(...)
18. return totalRipe
```

Any failed transfer, mint, approval, Teller deposit, or deposited-amount equality check
reverts the full transaction, including cap and budget state. The canonical payment
token is assumed non-fee-on-transfer; the lane credits the exact requested
`paymentAmount`.

---

## 10. Settlement and protocol integration

The settlement path mirrors `BondRoom.vy`:

- Proceeds go directly from the buyer to Endaoment Funds (id 21).
- Unlocked RIPE is minted directly to the buyer.
- Locked RIPE is minted to the lane, approved exactly to Teller, deposited into vault
  id 2 with `depositFromTrusted`, and the approval is reset to zero.
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
  `cs.RipeGovVaultConfig`;
- `Ledger.badDebt`.

The lane does not call `Ledger.didClearBadDebt`, does not reduce RIPE delivery during
bad debt, and does not write Bond Room/Ledger epoch state.

### 10.1 Source anchors at the bound baseline

The following references were verified at `91eda49`. Rebind them if the implementation
baseline changes:

- RipeGov clamps deposits to live min/max lock terms: `RipeGov.vy:172-175`.
- RipeGov early-exit permissions, bad-debt freeze, and fee: `RipeGov.vy:552-585`.
- Teller trusted-deposit authorization and signature: `Teller.vy:254-265`.
- RipeHq RIPE-minter checks: `RipeHq.vy:389-399`.
- Registered-switchboard authorization: `Addys.vy:183-189`.
- Department pause/recovery behavior: `DeptBasics.vy:63-93`.
- SwitchboardCharlie pause pass-through: `SwitchboardCharlie.vy:490-496`.
- Bond Room's locked mint/approve/deposit/reset pattern: `BondRoom.vy:219-224`.
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
6. emit every config field and the new version.

`setConfig` is `@nonreentrant` as defense-in-depth even though only registered
switchboards may call it and its normal path has no state-changing external interaction.

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

- `epochPricingVersion` — source of rate, cap, and max bonus; and
- `configVersion` — live source of availability and mint budget.

Lock-duration terms are separately live through SwitchboardAlpha and are not covered
by the lane config version.

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

Minimal state:

```text
PendingInstantBondConfig
    config
    expectedVersion

public pendingConfig[actionId] -> PendingInstantBondConfig
```

Minimal external workflow:

```text
setInstantBondConfig(config, expectedVersion) -> actionId
executePendingAction(actionId) -> bool
cancelPendingAction(actionId) -> bool
```

Initiation requires LocalGov permission, requires the inherited `actionTimeLock` to be
nonzero, requires `LANE.isValidConfig(config)`, requires
`expectedVersion == LANE.configVersion()` at initiation, creates a TimeLock action,
stores the complete pending input, and emits it with the confirmation block. The
nonzero assertion makes the required `setActionTimeLockAfterSetup` deployment ordering
self-enforcing rather than relying only on procedure.

Execution requires LocalGov permission and a confirmable, unexpired action. It calls
`LANE.setConfig(config, expectedVersion)`. The lane repeats the version and config
checks. If another config executed first, the stale action reverts and cannot overwrite
state; governance may cancel it or let it expire. A successful execution deletes the
dedicated `pendingConfig[actionId]` entry after the lane call. Before emitting the
execution event, Foxtrot reads `LANE.configVersion()` and reports the actual resulting
lane version rather than deriving it from the pending input.

Cancellation and automatic expired-action cleanup must delete the pending config.
Because this switchboard has one action type, it needs no action-type flag or dispatch
tree.

Required switchboard events:

```text
PendingInstantBondConfigSet(
    actionId,
    confirmationBlock,
    expectedVersion,
    <all config fields>,
)
InstantBondConfigExecuted(actionId, newVersion)
InstantBondConfigCancelled(actionId)
```

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
repository-consistent name and the lowest-blast-radius architecture. Exact bytecode
sizes remain a Phase 2 verification item; Phase 1 does not compile either contract.

The lane intentionally uses the protocol-standard registered-switchboard check rather
than pinning `setConfig` to the dedicated switchboard address. Pinning would require a
predicted address, circular deployment, or a mutable one-time bootstrap setter. The
Switchboard registry remains the protocol trust boundary; the dedicated switchboard's
immutable `LANE` target and the lane-local version check provide the feature-specific
containment.

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

There is no rebaseline, restart, admin-set-rate, or emergency mint function.

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
    utilizationBps,
    decaySteps,
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
)

InstantBondConfigSet(
    newVersion,
    <all config fields>,
)
```

`DeptBasics` already emits pause and recovery events. Switchboard events are specified
in §12. Initialization `epoch`, both rollover epoch endpoints, purchase `epoch`, and
each event's `pricingConfigVersion` are indexed as shown so indexers can filter by lane
epoch or pricing source without decoding every log. Events must be sufficient to
reconstruct every config and epoch transition without an on-chain history mapping.
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
3. **Controller direction:** high utilization increases price/decreases inverse rate;
   low nonzero utilization decreases price/increases inverse rate; the dead band holds.
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
   locks exactly `totalRipe`; the lane has no normal residual balance or allowance.
8. **Recipient:** `msg.sender` is always the RIPE recipient.
9. **Atomicity:** any payment, mint, approval, or Teller failure reverts all cap,
   budget, token, and event effects.
10. **Lifecycle:** before config/genesis purchase reverts and preview is unavailable;
    first preview simulates initialization; first successful buy stores the same quote;
    pre-initialization elapsed epochs do not decay.
11. **Prospective config:** live availability/budget changes are immediate; pricing
    changes are next-rollover; seed changes never reset an initialized rate.
12. **Versioning:** stale config actions revert at the lane; pricing and live versions
    in purchase events identify their respective state.
13. **Preview parity:** with unchanged relevant state, protective purchase inputs from
    a quote produce exactly the quoted payout and lock.
14. **No rebaseline:** pause/disable/budget gaps follow the same bounded decay rule.
15. **Rate liveness:** initialization and every rollover leave
    `epochRate >= MIN_BASE_RATE`; a sequence of high-utilization epochs cannot round the
    rate permanently to zero, and every valid low-utilization step strictly increases a
    sub-ceiling rate.
16. **Controller anti-dust:** the active minimum is at least one whole payment token,
    below-minimum purchases revert, and `downBps <= decayBps` for every valid config.
17. **Bonus-intermediate safety:** every valid config keeps
    `maxBaseRipe * maxLockBonus` within `uint256` before bonus division, including for
    low-decimal payment tokens.
18. **Stored-state visibility:** public epoch getters expose the last stored snapshot;
    after an unpurchased boundary they remain unchanged while `previewBuyNow` projects
    the current epoch and pricing.

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
- No automatic payment-token depeg or DEX-divergence guard exists in v1.
- `MIN_BASE_RATE` prevents integer fixed points but is economically tiny; deployment
  tooling and operator review must reject implausibly scaled `seedRate` and
  `maxEffectiveRate` values.
- A buyer can still deliberately make a minimum-size low-utilization purchase to select
  the sold-epoch branch. The governed minimum makes that non-dust, `downBps <= decayBps`
  prevents a stronger individual step than emptiness, and the all-in floor remains the
  hard destination.

### Lock-bonus commitment

- RipeGov stores one weighted unlock per user/asset rather than an isolated lock per
  deposit. A buyer with a sufficiently dominant short-duration RIPE position can
  receive the lane's long-lock bonus while the combined position's calendar unlock is
  much shorter than the new deposit's requested duration. Normalized-share and
  whole-block rounding can reduce the incremental extension further.
- The weighted calculation approximately moves the new deposit's duration commitment
  onto the buyer's existing shares, so this is not universally a cost-free bonus.
  Nevertheless, the individual lane deposit does not receive an isolated max-duration
  lock, and extreme ratios can create a real incentive leak.
- Bond Room inherits the same behavior through the identical Teller-to-RipeGov path;
  the lane does not create it. The lane can increase the available bonus budget,
  however, so v1 consciously accepts the inherited exposure rather than describing it
  only as a UI concern.
- Full closure requires isolated positions or a RipeGov-level lock-accounting change,
  both out of scope for this minimal lane. Launch bounds are a modest
  `paymentCapPerEpoch`, modest `maxLockBonus`, the cumulative `mintBudget`, and monitoring
  purchases that combine a maximum deposit lock with a large, short-duration prior
  RipeGov position.
- The purchase event identifies the buyer and deposit `actualLock`, but deliberately
  does not duplicate pre-existing RipeGov shares or unlock state. Monitoring must join
  the event with RipeGov state/history; those cross-contract values are live position
  context, not a stable statement of the final post-deposit unlock.

### Governance

- All registered switchboards are trusted under the existing protocol authorization
  model. The dedicated switchboard is the only intended config entry point and has an
  immutable lane target.
- Lane-local expected-version checks prevent stale queued actions from overwriting a
  newer config.
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
  deposits are disabled, the buyer is not deposit-allowlisted, vault id 2 does not
  support RIPE, RipeGov is paused, or the RIPE token is paused. An unlocked quote can
  still revert because the RIPE token is paused or the buyer is token-blacklisted. Any
  quote can also precede a purchase revert if Endaoment Funds id 21 resolves to the zero
  address; preview intentionally does not add that registry lookup.
- Preview itself may revert if required registry, MissionControl, RipeHq, or Ledger
  calls revert or resolve to unusable addresses. Before configuration or genesis it
  returns a zeroed unavailable quote without making those calls; after that point it is
  a dependency-aware view, not a guaranteed no-revert health endpoint.
- The mechanism assumes a canonical, dollar-denominated, non-fee-on-transfer ERC-20.
  Its decimal count may vary and is snapshotted immutably at construction. The lane has
  no oracle and cannot verify the token's dollar value or detect a depeg.

### Complexity controls

- no historical storage arrays or mappings;
- no oracle or DEX interfaces;
- no partial fills;
- a governed minimum payment of at least one whole payment token;
- no delegated recipient;
- no rebaseline state machine;
- no direct rate setter;
- one action type in the dedicated switchboard.

---

## 17. Test plan

> **Phase 2 authorized and executed.** This section is the acceptance checklist for
> the owner-authorized local test and validation phase. It does not authorize the
> deployment rehearsal subsection, remote-fork execution, testnet work, deployment,
> activation, publication, or Git actions; those remain separately gated in §20.

**Framework:** pytest + titanoboa + Vyper `0.4.3`. Tests live under
`tests/core/instantBondLane/` with dedicated switchboard tests under the appropriate
`tests/config/` path. Reuse shared token fixtures and add payment-token coverage across
multiple decimal counts.

### Constructor and configuration

- zero/non-contract payment token, missing/reverting `decimals()`, decimal counts above
  73, the registered RIPE token as payment, and zero epoch length reject;
- 0-, 6-, and 18-decimal payment tokens derive the correct immutable scale;
- every §3.3 boundary and invalid combination;
- `upBps <= downBps`, `downBps > decayBps`, denominator boundaries, oversized decay
  cap, unsafe multiplication bounds, minimum payment outside `[PAYMENT_SCALE, cap]`,
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
- `canExit`, exit fee, no-exit, and bad-debt-freeze quote fields.

### Settlement and atomicity

- unlocked mint and vault-2 locked settlement;
- exact Endaoment Funds receipt;
- payment, mint, approval, Teller failure, and Teller deposited-amount mismatch rollback;
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
  `newMaxLockBonus`, alongside the distinctly named prior-epoch inputs;
- purchase events distinguish pricing and live config versions;
- dedicated switchboard initiate, confirm, stale execute, cancel, and expiration;
- configuration initiation rejects while `actionTimeLock == 0`;
- a unique sentinel round trip through Foxtrot proves every duplicated
  `InstantBondConfig` field position, and CI compares the two source struct blocks to
  catch same-type field reordering that leaves the ABI selector unchanged;
- switchboard immutable target and bytecode-size checks; measure both runtimes
  independently in Phase 2 rather than importing reviewer numbers, and add a
  source-level EIP-170 headroom comment only if the measured margin warrants one.

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
- the coverage gate is serial. If a future runner opts into pytest-xdist, each worker
  receives its own unique self-cleaning compiler cache; this deliberately favors
  instrumentation correctness over cross-worker cache reuse and must be budgeted as a
  cold compile per worker. The feature-specific slowdown does not apply to unrelated
  coverage invocations;
- keep Python, pytest, Hypothesis, Boa, and coverage artifacts outside the worktree.

### Deployment rehearsal

> **Phase 3 only — not authorized.** These cases remain specified but were not run in
> Phase 2.

- rehearse every registry/config timelock phase on a pinned target-chain fork;
- capture dynamic `regId` values;
- verify launch remains unavailable until both config enablement and unpause;
- execute one unlocked and one locked smoke purchase with a deliberately small budget.

---

## 18. Deployment and activation

> **Deferred — Phase 3/4 not authorized.** No deployment scripts, configuration
> changes, generated artifacts, fork rehearsals, testnet actions, production
> actions, or activation work may occur until a later phase is explicitly authorized
> by the owner.

Deployment is multi-phase and must honor live timelocks:

1. Finalize and record immutable inputs: canonical dollar-stablecoin payment token,
   expected token decimals/scale, `GENESIS_BLOCK`, and `EPOCH_LENGTH`; verify vault id
   2 is RipeGov and supports RIPE. Independently call `decimals()` and compare it with
   the deployed lane's immutable `PAYMENT_DECIMALS` and `PAYMENT_SCALE`.
2. Deploy `InstantBondLane` paused and unconfigured.
3. Deploy `SwitchboardFoxtrot` with the lane as immutable target and action
   timelock unset during setup.
4. Before the switchboard is registered or can call the lane, call
   `setActionTimeLockAfterSetup`, verify the nonzero production timelock, and relinquish
   the temporary local governor if one was installed. This avoids any registered
   zero-timelock window; Foxtrot also rejects configuration initiation while the action
   timelock remains zero.
5. Initiate registration of the dedicated switchboard in the existing Switchboard
   registry; wait; confirm.
6. Initiate lane registration in RipeHq; wait the registry timelock; confirm and
   capture the returned `regId`. Never hardcode a guessed id.
7. Initiate `HqConfig(regId, canMintGreen=false, canMintRipe=true,
   canSetTokenBlacklist=false)`; wait; confirm.
8. Queue the initial lane config with `expectedVersion=0`, `canBuyNow=false`, and a
   deliberately small calibrated cap/budget; wait; execute. Verify version 1 and all
   emitted fields. Keep the Department paused.
9. Verify preview remains unavailable while paused/disabled and that RipeHq recognizes
   the lane as an authorized RIPE minter.
10. Queue a full config with `expectedVersion=1` and `canBuyNow=true`; wait; execute.
   While still paused, verify `previewBuyNow` shows the intended rate and
   `pricingConfigVersion == liveConfigVersion`; this proves any prospective floor
   tightening is active at the simulated rollover. Unpause through the established
   SwitchboardCharlie governance path only after the enabling config is confirmed.
11. Execute small unlocked and locked smoke purchases. Verify Endaoment receipt,
    cumulative mint accounting, event versions, lock disclosure, and settlement.

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
This is the owner-selected hard deployment/reconfiguration gate; v1 deliberately does
not hard-code an arbitrary epoch-to-budget ratio in contract validation.

A config that was valid when queued can become invalid before execution if purchases
raise `cumulativeMinted` above its proposed `mintBudget`. The execution must fail
closed. Operators must re-read the live version and cumulative minted amount, update
the full config, and queue a fresh action; an execution revert in this case is expected
behavior, not a reason to bypass lane validation.

The first successful purchase initializes at the current deterministic epoch and uses
the latest seed. Activation does not require or permit a manual rate write.

Decommission with `canBuyNow=false`, pause, or lane deregistration. Recover only truly
stranded assets through the inherited governed recovery path.

---

## 19. Remaining inputs: calibration only

> **Deferred — not authorized in Phase 2.** Calibration is not required to complete
> local contract verification. Phase 2 must not create deployment datasets or
> configuration artifacts for this work.

All product and engineering semantics are settled in this specification. The only
remaining inputs are economic calibration and final live-state discovery:

- `EPOCH_LENGTH`;
- canonical dollar-stablecoin `PAYMENT_TOKEN` and its expected decimals;
- `paymentCapPerEpoch`;
- `minPaymentAmount`;
- initial and maximum planned `mintBudget`;
- `uLowBps` / `uHighBps`;
- `upBps` / `downBps` / `decayBps`;
- governed `maxDecayEpochs` (hard ceiling 32);
- `maxEffectiveRate` and `seedRate`;
- `maxLockBonus` (hard ceiling 1000%);
- live expected registry ids as nonbinding preflight assertions.

Calibration values must satisfy §3.3 and should be selected with the simulation work
described in `pricing-design.md`. Placeholder values may be used in unit tests, but no
placeholder value may enter a deployment artifact or activation proposal.
Initial `maxLockBonus` and `paymentCapPerEpoch` must also bound the accepted weighted-lock
exposure in §16; scaling either requires monitoring evidence from the limited launch.
Choose `paymentCapPerEpoch` as a clean multiple of `minPaymentAmount` when practical;
otherwise up to `minPaymentAmount - 1` base units of epoch capacity can be stranded and
unpurchaseable. Calibrate `EPOCH_LENGTH` against target-chain block time and expected
transaction latency because `expectedEpoch` is an exact execution-time match and
transactions crossing a boundary revert. Deployment review must independently sanity
check the immutable genesis block and epoch length; the constructor rejects only a zero
epoch length and deliberately does not embed chain-specific timing windows. The
effective issuance bound is not the epoch cap alone: it is
`paymentCapPerEpoch * maxEffectiveRate // PAYMENT_SCALE` per `EPOCH_LENGTH` blocks.
Those three economic inputs and the target-chain block time must be calibrated and
approved together using the rolling-day gate in §18; a very short epoch converts an
otherwise modest cap into a high-frequency issuance allowance.

---

## 20. Owner-controlled delivery phases

Each phase requires separate owner authorization. Completing one phase does not
authorize the next.

### Phase 1 — contract source and normative-spec revision (completed)

Authorized work is limited to creating or editing exactly:

1. `contracts/core/InstantBondLane.vy`
2. `contracts/config/SwitchboardFoxtrot.vy`
3. `docs/instant-bond-lane/implementation-spec.md`

The two contracts must implement the complete behavior defined by this specification,
including all required on-chain authorization checks, input validation, bounds,
accounting protections, and execution-time revalidation. The specification may be
edited only to record the owner-approved Phase 1 review decisions. The instruction to
perform “no validation” in Phase 1 means no external validation activity; it does not
permit omitting defensive checks from the contract source.

Phase 1 does **not** authorize:

- creating or editing any other file, including tests, fixtures, mocks, interfaces,
  scripts, deployment/configuration files, other documentation, or generated artifacts;
- compiling the contracts;
- running tests, linters, formatters, static analyzers, bytecode-size checks,
  coverage tools, simulations, or any other validation command;
- running fork rehearsals or interacting with testnet or production;
- staging, committing, pushing, opening a pull request, deploying, or activating the
  feature unless the owner separately authorizes that action.

After the two contract source files and this normative revision are written, the
implementer must stop and hand the changes to the owner for review. Owner feedback may
require another source/spec-only Phase 1 revision. Phase 2 may begin only after the
owner explicitly authorizes it.

### Phase 2 — tests and local validation (authorized; current review phase)

The owner explicitly authorized comprehensive local tests and validation on 5 August
2026, then authorized the reviewer-driven corrections in specification revision 14,
local stateful differential fuzzing, and the revision 16 RIPE-payment guard and
reproducibility corrections on 6 August 2026.
The agreed editable scope is limited to:

1. the owner-approved RIPE-payment constructor guard and defensive-only reachability
   comment in `contracts/core/InstantBondLane.vy`;
2. this normative specification;
3. `.coveragerc-instant-bond`;
4. the cache-safety hook in `tests/conftest.py`;
5. `tests/core/instantBondLane/conftest.py` and the feature tests in that directory;
6. `tests/config/test_switchboard_foxtrot.py`.

The agreed validation commands use the active or pinned Python interpreter with all
caches, coverage data, and pytest temporary files redirected to private temporary
paths. They comprise:

- focused pytest over `tests/core/instantBondLane/` and
  `tests/config/test_switchboard_foxtrot.py`;
- directly affected BondRoom, RipeGov, SwitchboardDelta, and timelock regressions;
- the complete default-local `tests/` suite;
- Vyper line/branch coverage for `InstantBondLane.vy` and `SwitchboardFoxtrot.vy`
  through `boa.coverage`, invoked with
  `--cov-config=.coveragerc-instant-bond`;
- Hypothesis rule-based stateful differential fuzzing against an independent model of
  lazy epoch transitions, controller arithmetic, versioned pricing snapshots, payout
  math, availability, settlement accounting, and transaction rollback;
- independent runtime-bytecode measurement;
- a focused-suite repeat with the pinned
  `ripe-protocol-validation-envs/rh-wave2-py312` interpreter.

The reconciled local evidence through specification revision 17 on 6 August 2026 is:

- 78 focused feature/configuration tests passed with the pinned interpreter;
- the state machine passed a clean direct run configured for 50 examples and 20
  generated actions per example, interleaving purchases, epoch jumps, configuration
  and lock-term changes, pause and mint transitions, and deliberate rollback paths;
- the complete default-local suite reported 2,605 passed and 142 fork-dependent
  tests deselected;
- combined Boa coverage for the two feature contracts was 86.9% with branch
  coverage enabled (`InstantBondLane.vy`: 85.6%; `SwitchboardFoxtrot.vy`: 96.2%),
  satisfying the configured 85% minimum while retaining a missing-branch report;
- a `pytest --cov --cov-config=.coveragerc-instant-bond` run deliberately pointed at
  an already-populated Boa cache reproduced the same 86.9% result because the root
  coverage hook rebound compilation to a unique empty temporary cache;
- that dedicated run left no `ripe-boa-coverage.*` directory after pytest exited,
  while an unrelated targeted BondRoom test invoked with plain `--cov` passed without
  inheriting the Instant Bond Lane include list or 85% threshold;
- pinned runtime bytecode measured 8,398 bytes for `InstantBondLane.vy` and 5,069
  bytes for `SwitchboardFoxtrot.vy`, below the respective 9,000-byte and 5,500-byte
  regression ceilings and the 24,576-byte EIP-170 limit; and
- the pinned environment reported no broken Python requirements.

Phase 2 does **not** authorize remote-fork tests, the deployment rehearsal in §17,
testnet or production interaction, calibration artifacts, staging, committing,
pushing, pull requests, deployment, activation, or publication. After local evidence
is reconciled, work stops for owner review.

### Post-Phase 2 local wrap-up and Git authorization

After reviewing the reconciled Phase 2 evidence, the owner explicitly authorized the
agent to finish this specific feature workflow in the same worktree and commit it on
the existing `instant-bond-lane` branch, without merging it into another branch. That
authorization covered the two contracts, normative specification, feature tests,
feature-scoped coverage configuration, shared test-cache hook, and the optional
`pricing-design.md` terminology reconciliation. The owner subsequently instructed the
agent to incorporate the committed-candidate review findings, including the narrow
`.gitignore` coverage-data entries and related test/config corrections, as part of the
same local wrap-up.

The resulting baseline commit was
`020a4f1da397ad9ac9c617000053609eb44fa209` with tree
`3b0399c997427e454ef4ef5d8ca636abdf6154c6`; its parent was the original bound
baseline `91eda49ccd34a25090582aff0695075c4c806011`. The commit patch was recorded as
SHA-256 `9bcf1e43549733ea08f5f6db3eaa81a1f4a6e26a64fbbe2175113ea4dad6ef33`, computed
from the exact bytes emitted by `git diff HEAD^1 HEAD --binary`.

This local authorization does **not** authorize merging, pushing, opening a pull
request, fork or testnet work, production configuration, deployment, activation, or
publication. Phases 3 and 4 still require fresh, explicit owner authorization.

The local Git authorization above establishes committed source baselines covering both
contracts, the normative specification, coverage configuration, root cache hook,
feature tests, and the explicitly recorded supporting files. Before any merge, the
owner must separately authorize the merge action. The final merge review must compare
the latest committed baseline byte-for-byte with the merge candidate; any later source
change invalidates prior hash, bytecode, coverage, and test evidence until it is
regenerated.

### Phase 3 — fork and testnet rehearsal (not authorized)

After Phase 2 review and explicit owner authorization, perform fork settlement,
rollover, governance, switchboard, emergency-shutdown, surplus, and zero-balance
scenarios, followed by testnet epoch-boundary and operator-runbook rehearsal.

### Phase 4 — limited production and activation (not authorized)

After Phase 3 review and explicit owner authorization, follow §18 with conservative
reserve, daily-limit, and epoch-cap settings. Activation additionally requires live
monitoring, verified emergency roles, and no unresolved invariant failures.

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
