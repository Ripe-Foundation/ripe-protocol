# Instant Bond Lane

This is the **start-here guide** for the Instant Bond Lane feature. It explains what
the mechanism does, how a purchase moves through the protocol, how the epoch
controller changes the next rate, how governance intervenes, and which production
decisions are still deliberately blocked.

> **Current status — contract candidate, not an active product.** The contracts,
> tests, generated ABIs, and deterministic controller model are implemented and
> validated. They are **not deployed, configured, economically calibrated, or
> authorized for activation**. The activation manifest remains fail-closed.

This README is an onboarding map, not the normative specification. If it ever
conflicts with [`implementation-spec.md`](implementation-spec.md), the implementation
specification and contract source control.

## Fast reading path

For a quick ramp-up, read in this order:

1. This README for the system and transaction model.
2. [`contracts/core/InstantBondLane.vy`](../../contracts/core/InstantBondLane.vy) for
   purchase, preview, pricing, settlement, and stored state.
3. [`contracts/config/SwitchboardFoxtrot.vy`](../../contracts/config/SwitchboardFoxtrot.vy)
   for governance.
4. [`pricing-design.md`](pricing-design.md) for the economic rationale and risks.
5. [`dynamic-controller-proposal.md`](dynamic-controller-proposal.md) for exact
   controller and override derivation.
6. [`implementation-spec.md`](implementation-spec.md) for the normative ABI,
   invariants, threat model, tests, and historical evidence.
7. [`../../config/instant-bond-lane-activation.json`](../../config/instant-bond-lane-activation.json)
   for the machine-checked list of inputs still required before activation.

## What the mechanism is

The Instant Bond Lane is a dedicated, permissionless **Buy Now lane for newly minted
RIPE**:

- a buyer pays a configured dollar-denominated ERC-20 (swappable only while the lane
  is stopped);
- payment goes directly to Endaoment Funds;
- the Lane mints RIPE for that purchase;
- the buyer receives RIPE unlocked, or the Lane deposits it into the current core
  RipeGov vault with a lock; and
- the next epoch's base payout rate responds to how much of the prior epoch sold and
  when that payment volume arrived.

It is not BondRoom, a Dutch auction, an order book, or a fair-value oracle. It is a
bounded **cap-clearing demand controller**. Its question is: “At this rate, how much
of the governed epoch capacity cleared?” It does not independently know what RIPE is
worth on external markets.

Every successful purchase mints new RIPE. The main economic safety boundaries are the
per-epoch payment cap, all-in rate ceiling, cumulative mint budget, pause/mint
controls, exact payment settlement, and conservative production calibration.

## System map

```mermaid
flowchart LR
    Buyer["Buyer / msg.sender"]
    Lane["InstantBondLane"]
    Payment["Configured payment token"]
    Endao["Endaoment Funds"]
    Ripe["RIPE token"]
    Teller["Teller"]
    GovVault["Current core RipeGov vault"]
    MC["MissionControl + registries"]
    HQ["RipeHq mint controls"]
    Gov["Local governance"]
    Fox["SwitchboardFoxtrot + TimeLock"]

    Buyer -->|"previewBuyNow / buyNow"| Lane
    Lane -->|"transferFrom, exact receipt"| Payment
    Payment --> Endao
    Lane -->|"unlocked mint"| Ripe
    Ripe --> Buyer
    Lane -->|"locked mint + trusted deposit"| Teller
    Teller --> GovVault
    GovVault -->|"shares / position for buyer"| Buyer
    Lane -.->|live topology and lock terms| MC
    Lane -.->|mint authorization| HQ
    Gov -->|"config, override, start/stop, token"| Fox
    Fox -->|"HQ id 26 lookup"| Lane
```

The Lane and Foxtrot are nonupgradeable Vyper contracts. Foxtrot does not store the
lane address. It looks up `INSTANT_BOND_LANE_ID = 26` from RipeHq, the same way the
other switchboards resolve Mission Control and Endaoment. The Lane follows the
protocol's Department trust model: any registered switchboard may call its mutators.
Foxtrot is the intended semantic route. Deployment qualification must prove no other
registered switchboard exposes an unintended generic call path to the Lane mutators.

## Lifecycle

The constructor is `__init__(ripeHq, paymentToken, config)`. Deploy is paused, not
running, `genesisBlock = 0`, and `epochState.rate = 0`. The installed config must
already be valid, including `epochLength`.

`start(genesisBlock, epochLength)` is switchboard-gated. `genesisBlock = 0` means
`block.number`. Past and future genesis are allowed. Start writes the resolved genesis
and `bondConfig.epochLength`, then re-validates the live config (so a payment-token
swap with a stale cap/min fails here), sets `isRunning`, and wipes the epoch snapshot
and any installed override.

`stop()` sets `isRunning = false`, `genesisBlock = 0`, wipes `epochState`, and clears
an installed override. It does not touch the payment token, the rest of config, or
`cumulativeMinted`.

The asset-change flow is `stop()` → `setPaymentToken` / `setConfig` → `start(0,
length)`. Pause is a short incident switch: same genesis, same snapshot, token stays
locked. Charlie wraps `pause` / `recoverFunds` for any department.

## A purchase from start to finish

### 1. Preview from the buyer address

The buyer calls:

```text
previewBuyNow(paymentAmount, requestedLock)
```

The returned `InstantBondQuote` includes:

- whether the lane currently looks available;
- projected epoch, rate, remaining epoch capacity, minimum payment, and remaining mint
  budget;
- base RIPE, bonus, actual lock, and total RIPE;
- the current core RipeGov vault ID for a locked purchase; and
- live early-exit, exit-fee, and bad-debt-freeze disclosure.

`available` is a market-readiness flag, not a wallet or vault preflight. It is true
only when the lane is unpaused, running, `canBuyNow`, the payment sits in the current
cap/min window, the mint budget covers the payout, and RipeHq currently authorizes the
lane to mint. Preview still fills rate and payout math when unavailable.

It does **not** inspect wallet balance or allowance, Endaoment liveness, vault/Teller
admission, or RIPE pause/blacklist. Those can still make `buyNow` revert.

It is still a quote, not a reservation. Another transaction can consume capacity,
change a live control, rotate a vault, update lock terms, or advance the epoch before
the purchase lands.

### 2. Bind the transaction

The complete purchase call is:

```text
buyNow(
    paymentAmount,
    requestedLock,
    expectedEpoch,
    minRipeOut,
    deadlineBlock,
)
```

There is no `_minActualLock` or `_expectedCoreVaultId`. The caller should bind:

- `expectedEpoch` to the previewed epoch;
- `minRipeOut` to an acceptable payout floor; and
- `deadlineBlock` to a short validity window.

Unlocked settlement happens when the buyer asked for `0` **and**
`config.minLockDuration == 0`, or when there is no live vault range. The vault
minimum does not force a lock on a zero request when the lane min is `0`. Instant Bond
then mints RIPE to the wallet and never calls Teller/RipeGov. An impossible vault
range or zero vault max is a valid unlocked buy.

Purchases are full-fill-only. The Lane never silently reduces `paymentAmount`; if
another buyer consumes capacity first, the transaction reverts and the client must
preview again and retry.

### 3. Update state and settle atomically

The Lane projects initialization or rollover, records the new accounting, and then:

1. transfers the exact payment amount directly to Endaoment Funds;
2. verifies the destination balance increased by exactly that amount;
3. mints the quoted RIPE; and
4. either sends it to the buyer or deposits it through Teller into the current core
   RipeGov vault for the buyer.

For locked settlement, the Lane dynamically resolves `coreRipeGovVaultId()` at
execution time, verifies the Teller-reported deposited amount, restores its preexisting
RIPE balance, and clears the Teller allowance. Any downstream failure reverts the
entire transaction, including projected rollover, accepted-payment accounting,
weighted timing, mint-budget use, and one-shot override consumption.

The production activation policy supports a specifically qualified, non-callback
payment token. Exact-receipt checks reject fee-on-transfer, short, zero, excess, and
false-return settlement behavior. Callback behavior is tested for atomicity but is not
qualified for production by default.

## Epochs and fixed pricing

The lane clock is storage, not constructor immutables:

```text
epoch = (block.number - genesisBlock) // bondConfig.epochLength
```

`start` installs genesis and cadence. `setConfig` cannot change a live
`epochLength`; a different length is invalid once one is installed. A new cadence
requires `stop()` then `start(..., newLength)`.

There is no keeper-only initialization or rollover transaction:

- cold start versus rollover is `epochState.rate == 0` (`MIN_BASE_RATE` is 10_000);
- before the first successful purchase after start, `previewBuyNow` projects
  `seedRate` and a successful `buyNow` initializes the epoch;
- all successful purchases in one stored epoch use the same snapshotted base rate,
  payment cap, minimum payment, and maximum lock bonus;
- `previewBuyNow` projects a later epoch without writing state; and
- the first successful purchase in that later epoch commits the rollover.

Epoch state is therefore **lazy**. Public `epochState()` is the last committed
snapshot and goes stale until the next buy. `getEpochSnapshot()` is the live
projection. Consumers must use `previewBuyNow` or `getEpochSnapshot()`, not
reconstruct a current quote from stale stored getters.

Epochs before first initialization do not create historical decay. A first
initialization is timing-eligible only at deterministic offset zero; a partial cold-
start epoch uses the weakest upward step if its utilization is high. Every later
stored epoch is timing-eligible.

## How the controller moves the next rate

The Lane stores an inverse payout rate:

```text
rate = RIPE-wei paid per one whole payment token
baseRipe = paymentAmount * rate // paymentScale
```

Amounts stay in native payment-token units. The lane does not PriceDesk-normalize.

This direction is easy to misread:

- **higher rate** → the buyer receives more RIPE → RIPE's implied price is lower;
- **lower rate** → the buyer receives less RIPE → RIPE's implied price is higher.

For the prior stored epoch:

```text
utilizationBps = acceptedPayment * 10_000 // paymentCap
```

Thresholds are inclusive. The next successful rollover applies one of four behaviors:

| Prior result | Signal | Next-rate behavior |
|---|---|---|
| High utilization | `utilization >= uHighBps` | Lower the payout rate, raising implied RIPE price by `minUpBps..maxUpBps`. |
| Dead band | `uLowBps < utilization < uHighBps` | Apply no utilization step; a newly lowered ceiling may still clamp the rate. |
| Low positive utilization | `utilization <= uLowBps` | Raise the payout rate, lowering implied RIPE price by `minDownBps..maxDownBps`. |
| Skipped empty time | No committed purchases in intervening epochs | Apply fixed `decayBps`, capped by `maxDecayEpochs`. |

### High utilization: amount-weighted timing

The high branch uses both utilization strength and amount-weighted purchase timing.
For each purchase, the Lane computes its normalized block lateness and accumulates:

```text
lateness = offset * 10_000 // (epochLength - 1)
epochWeightedLateness += paymentAmount * lateness
averageLateness = epochWeightedLateness // acceptedPayment
earliness = 10_000 - averageLateness
```

Weighting makes same-block split, merge, and order permutations equivalent. A small
late tail cannot erase a large early purchase, and a small early probe cannot make
large late demand appear early.

Exactly `uHighBps` receives `minUpBps` regardless of timing. At full utilization, a
first-block eligible epoch can reach `maxUpBps`, while a final-block fill receives
`minUpBps`. Intermediate demand interpolates between them.

Timing is nevertheless strategically selectable because the epoch price is fixed. A
buyer can wait for the final block without paying a worse same-epoch rate. Production
activation therefore requires `minUpBps` and the entire range to remain safe under
repeated final-block full-cap purchases; the current simulator values are not approved
calibration.

### Low utilization and skipped epochs

The low branch ignores timing and scales the downward adjustment by how far utilization
falls below `uLowBps`. A positive-payment epoch exactly at the low threshold receives
`minDownBps`; near-zero utilization can reach `maxDownBps`.

After applying the prior positive epoch's utilization transition once, a multi-epoch
gap applies:

```text
min(elapsedEpochs - 1, maxDecayEpochs)
```

fixed decay steps. Pause, disablement, budget exhaustion, or lack of buyers does not
stop the deterministic clock or create a separate rebaseline. The controller's bounds
ensure the weakest upward response is not undone by a stronger positive-payment or
empty-epoch downward response away from explicit floor/ceiling saturation.

For exact staged integer formulas and rounding direction, use
[`dynamic-controller-proposal.md`](dynamic-controller-proposal.md), not a reimplementation
from this summary.

## Snapshot fields versus live fields

A full config write replaces every field last-write-wins. There is no `configVersion`
or compare-and-swap. It does not rewrite the already committed epoch snapshot, except
that `setConfig` cannot change a live `epochLength`.

| Snapshotted on first buy of an epoch | Always live |
|---|---|
| Base payout rate | `canBuyNow` |
| Epoch payment cap | Remaining cumulative `mintBudget` |
| Epoch minimum payment | `minLockDuration` |
| Epoch maximum lock bonus | Department, RIPE, and global mint availability |
| | MissionControl lock terms and core vault ID |
| | Address-registry destinations and Teller/vault admission |
| | Payment token (only writable while stopped) |

Changing a pricing field mid-epoch is prospective. Even lowering
`maxEffectiveRate` does not rewrite the running epoch's rate; the new ceiling is applied
at rollover. Emergency operators must pause or disable purchases when immediate effect
is required. A full config change also invalidates any installed rate override.
`setCanBuyNow` does not.

## Locking and bonus behavior

Effective lock floor is `max(vault.lockTerms.minLockDuration, config.minLockDuration)`.
Vault `maxLockDuration` is the only ceiling.

- `requestedLock = 0` and `config.minLockDuration = 0` → unlocked, even if the vault
  has a min;
- `config.minLockDuration > 0` → a buy that can lock is clamped up to the effective
  min;
- no live vault range, or `maxLock < minLock`, or vault max is `0` → unlocked.

For a locked purchase:

- the epoch's `maxLockBonus` bounds a linear duration bonus;
- the all-in `maxEffectiveRate` ceiling reserves room for the maximum possible bonus;
  and
- Teller deposits the complete RIPE amount into the current core RipeGov vault for
  `msg.sender`.

RipeGov blends new deposits into an account-level weighted position. A dominant active
or expired position can dilute the effective new commitment. For that reason, the
approved production activation policy requires `maxLockBonus=0` until isolated lock
lots exist. Nonzero-bonus code and model cases remain tested dormant arithmetic, not an
approved launch configuration.

Live exit permission, exit fee, and bad-debt freeze status are disclosed by preview but
are not transaction-bound.

## Governance and the manual rate override

`SwitchboardFoxtrot` combines LocalGov and TimeLock. It resolves the lane through
RipeHq id 26. Constructor is `(ripeHq, tempGov, minConfigTimeLock,
maxConfigTimeLock)` — no lane address.

Timelocked (once `setActionTimeLockAfterSetup` has been called; a zero time lock is
allowed and makes confirmation immediate):

1. replace the complete Instant Bond config;
2. install one exact rate override; or
3. cancel an override already installed in the Lane.

Immediate (governance only):

- `startInstantBond` / `stopInstantBond`
- `setInstantBondPaymentToken`
- `setInstantBondCumulativeMinted`
- `setCanBuyNow`

Foxtrot pre-validates with the lane views (`isValidConfig`, `isValidRateOverride`,
`canCancelRateOverride`, `isValidEpochLength`, `isValidPaymentToken`,
`isValidCumulativeMinted`) and keeps the same `# dev:` strings. Execute re-validates
before the lane call. Foxtrot does not wipe leftover pending config/override payloads
after execute or cancel; it only clears `actionType`, matching Echo. There are no
per-action cancel events.

The override is last-write-wins. There is no `overrideVersion`. It is valid only while
the lane is running **and** `epochState.rate != 0`. Last write wins. It is consumed on
the next successful rollover. `setConfig`, `start`, and `stop` clear an installed
override. `setCanBuyNow` does not.

Its lifecycle:

- same-epoch purchases leave it pending;
- preview projects it without consuming it;
- the first later successful rollover stores it exactly and consumes it once;
- no skipped-epoch decay is applied to the target before use;
- a failed downstream purchase restores it through transaction rollback;
- a successful full config write invalidates it; and
- the following epoch resumes normal control from the overridden stored rate.

There is no target epoch, expiry, or maximum lead. Operators must revalidate or cancel
an installed override before reopening after a long pause or disablement. The ordinary
counterfactual `controllerRate` is emitted when an override applies.

`setCanPurchaseRipeBond` stays on SwitchboardDelta for BondRoom. It is not on Foxtrot.

## Configuration at a glance

The ABI-locked config struct is duplicated byte-for-byte in both contracts:

| Field group | Fields | Purpose |
|---|---|---|
| Availability | `canBuyNow` | Live purchase switch. Also has a dedicated immediate Foxtrot setter. |
| Capacity | `paymentCapPerEpoch`, `minPaymentAmount` | Snapshotted epoch capacity and minimum full-fill size. |
| Supply | `mintBudget` | Instance-local cumulative RIPE issuance ceiling. |
| Rates | `maxEffectiveRate`, `seedRate` | All-in payout ceiling and cold-start base rate. |
| Utilization | `uHighBps`, `uLowBps` | Inclusive high, dead-band, and low branch thresholds. |
| Price up | `minUpBps`, `maxUpBps` | High-demand implied-price increase range. |
| Price down | `minDownBps`, `maxDownBps` | Low-demand implied-price decrease range. |
| Empty time | `decayBps`, `maxDecayEpochs` | Fixed skipped-epoch response and loop cap. |
| Locking | `maxLockBonus`, `minLockDuration` | Snapshotted max bonus (production policy is zero); live extra lock floor. |
| Clock | `epochLength` | Cadence. Writable only through `start`, not `setConfig` once installed. |

`mintBudget` is local to one Lane deployment. A replacement or concurrent Lane would
start with separate `cumulativeMinted` state, so activation requires an external
aggregate issuance ledger and may allocate only the approved remaining program budget.

No values in the simulator fixture are production recommendations.

## Main APIs and events

### InstantBondLane

User entry points:

```text
previewBuyNow(paymentAmount, requestedLock) -> InstantBondQuote
buyNow(paymentAmount, requestedLock, expectedEpoch, minRipeOut, deadlineBlock)
    -> totalRipe
```

Governance validation and mutation (registered switchboard):

```text
start(genesisBlock, epochLength)
stop()
setConfig(config)
setCanBuyNow(canBuyNow)
setRateOverride(targetRate)
cancelRateOverride()
setPaymentToken(token)
setCumulativeMinted(amount)

isValidConfig(config)
isValidRateOverride(targetRate)
canCancelRateOverride()
isValidEpochLength(epochLength)
isValidPaymentToken(token)
isValidCumulativeMinted(amount)
```

Important public state (camelCase):

```text
bondConfig()
epochState()
getEpochSnapshot()
isRunning()
genesisBlock()
epochLength()
paymentToken() / paymentDecimals() / paymentScale()
rateOverride()
cumulativeMinted()
```

Events:

```text
EpochInitialized
EpochRolled
InstantBondPurchased
InstantBondConfigSet
CanBuyNowSet
InstantBondStarted
InstantBondStopped
PaymentTokenSet
CumulativeMintedSet
RateOverrideInstalled
RateOverrideApplied
RateOverrideCancelled
RateOverrideInvalidated
```

### SwitchboardFoxtrot

```text
setInstantBondConfig(config) -> aid
setInstantBondRateOverride(targetRate) -> aid
cancelInstantBondRateOverride() -> aid
executePendingAction(actionId)
cancelPendingAction(actionId)
startInstantBond(genesisBlock, epochLength)
stopInstantBond()
setInstantBondPaymentToken(token)
setInstantBondCumulativeMinted(amount)
setCanBuyNow(canBuyNow)
```

Foxtrot `InstantBondStarted` logs the raw `_genesisBlock` argument, so `0` stays `0`.
The lane event logs the resolved block.

Use the generated ABIs for exact tuple layout, overloads, output names, event field
order, and indexing:

- [`../../scripts/abis/InstantBondLane.json`](../../scripts/abis/InstantBondLane.json)
- [`../../scripts/abis/SwitchboardFoxtrot.json`](../../scripts/abis/SwitchboardFoxtrot.json)

## Security properties to preserve

Anyone changing this feature should treat these as hard boundaries:

- exact payment receipt at Endaoment Funds;
- exact RIPE mint/Teller settlement and restoration of the Lane's preexisting RIPE
  balance;
- dynamic `coreRipeGovVaultId()` resolution at execution time;
- no forced lock when the buyer asked for `0` and the lane min is `0`;
- fixed same-epoch snapshot and correct accepted-payment/weighted-lateness
  accumulation;
- preview purity and full transaction rollback after every downstream failure;
- last-write-wins config and override; one-shot override consumption;
- weakest-up versus downward/empty anti-ratchet bounds;
- byte-identical Lane/Foxtrot config structs and ABI field order;
- Foxtrot validation on the same lane views, including execute-time revalidation; and
- the registered-switchboard authority model plus deployment-time route inventory.

The only deploy size limit is EIP-170 (24,576 bytes). There is no local Lane/Foxtrot
byte ceiling. Contracts compile without `# pragma optimize codesize` so call gas stays
on the default gas optimizer. Recompile and remeasure after every production-source or
imported-module change; do not weaken a safety check merely to recover bytes.

## What is deliberately not implemented

The current design excludes:

- an external fair-value, solvency, or payment-token depeg oracle;
- automatic DEX-based price changes;
- within-epoch price ramps or tranches;
- partial fills or capacity reservations;
- delegated recipients;
- automatic override expiry, target-epoch scheduling, or override versions;
- buyer-bound vault ID / minimum-lock transaction fields;
- per-epoch historical mappings; and
- an automatic pause-clock or rebaseline after unavailable time.

These are explicit scope decisions, not accidental omissions.

## Activation is still blocked

The branch is implementation-ready for review, not deployment-ready. Run:

```bash
python scripts/qualify_instant_bond_lane_activation.py \
  --manifest config/instant-bond-lane-activation.json \
  --check-draft

python scripts/qualify_instant_bond_lane_activation.py \
  --manifest config/instant-bond-lane-activation.json \
  --require-ready
```

The first command must confirm that the blocked draft is structurally valid. The
second command is expected to fail until every production input is supplied and
approved. Missing categories currently include:

- economic calibration and safe final-block sellout constraints;
- aggregate issuance accounting and replacement-Lane budget reconciliation;
- payment-token identity, code hash, depeg monitoring, pause, and reopening policy;
- full-fill retry and override-reopening runbooks;
- constructor parameters, realistic epoch/genesis bounds, deployed code hashes, and
  post-deployment assertions;
- registered-switchboard selector/code-hash inventory;
- credentialed archive-fork topology and locked/unlocked purchase qualification; and
- indexer owner and event-schema approval.

`activation_approved` must remain false until a separately authorized activation
phase closes all of those gates. Passing contract tests does not satisfy them.

## Validation commands

Generated and machine-checked surfaces:

```bash
python scripts/export_abis.py --check
python scripts/simulations/instant_bond_lane_controller.py \
  --check docs/instant-bond-lane/controller-simulation-v2.json
python scripts/qualify_instant_bond_lane_activation.py --check-draft
python -m pip check
git diff --check
```

Complete feature selection, including artifact, fuzz, gas, runtime, workflow, and
activation tests:

```bash
python -m pytest \
  -q \
  -p no:cacheprovider \
  -o addopts='' \
  tests/core/instantBondLane \
  tests/config/test_switchboard_foxtrot.py \
  tests/deployment/test_instant_bond_lane_activation.py \
  tests/deployment/test_abi_export.py \
  tests/test_instant_bond_lane_workflow.py
```

The repository workflow additionally runs branch-aware coverage and enforces separate
85% thresholds for Lane and Foxtrot. Keep Boa, Hypothesis, Python, pytest, XDG, and
coverage caches outside the worktree when reproducing final evidence.

## Agent change checklist

Before modifying this feature:

1. Rebind the live branch, PR head, RH base, Vyper `0.4.3`, and clean worktree.
2. Read this README, then the exact normative sections affected by the change.
3. Preserve the config field order in both contracts.
4. Add a regression or independent-model case before changing mechanism behavior.
5. Recompile and confirm both deployed runtimes stay under EIP-170.
6. Regenerate the Lane/Foxtrot ABIs after any ABI or event change.
7. Regenerate the controller JSON after either production source file changes; its
   artifact binds exact source hashes.
8. Run the complete feature gate with normally excluded markers enabled.
9. Keep economic calibration, deployment, configuration, minting, and activation as
   separate owner-authorized phases.
10. Never call the feature production-ready while `--require-ready` fails.

## Frequently asked questions

### Is an “instant bond” a normal bond or a claim on existing RIPE?

No. It is a direct primary-market RIPE purchase with optional RipeGov locking. The
Lane mints new RIPE within governed capacity and budget limits.

### Does an early sellout affect the next epoch more than a late sellout?

Yes. On a high-utilization, timing-eligible epoch, payment-weighted earliness can move
the adjustment from `minUpBps` toward `maxUpBps`. A final-block full-cap purchase still
receives the minimum upward response, which is why production calibration must make
that minimum safe on its own.

### Can governance manually set the next rate?

Yes, through a timelocked, last-write-wins, one-shot exact rate override. It applies
only at the next successful rollover, preview does not consume it, and a full config
change invalidates it.

### Can governance change the current epoch's price immediately?

No. Pricing fields are prospective and the committed epoch snapshot stays fixed.
Pause or `canBuyNow=false` is the immediate emergency control.

### Does the Lane use a market oracle?

No. It responds only to its own realized demand and elapsed epochs. External depeg and
fair-value risks are managed through conservative bounds and the still-unfilled
operational activation gates.

### Is the feature ready to deploy because the tests pass?

No. The code candidate and activation qualification are intentionally separate. The
manifest's failing `--require-ready` result is the authoritative deployment/activation
blocker.
