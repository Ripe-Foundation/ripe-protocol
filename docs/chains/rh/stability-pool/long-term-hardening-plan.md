# Robinhood Stability Pool long-term hardening plan

> [!IMPORTANT]
> **Planning artifact only.** This document proposes source, configuration, and
> validation work for a new Robinhood Stability Pool. It does not authorize a
> contract edit, deployment, configuration, activation, signer use, transaction,
> or release. Each lifecycle phase retains its own approval gate.

> [!NOTE]
> **Implementation status added 2026-08-05.** Tier A+B was selected and
> implemented for the isolated candidate at
> `e603dcee4a22c1c5100191c72ea1a23de1b40c22`. The forward-looking plan below
> remains preserved as historical design context. The
> [implementation specification's as-built outcome](implementation-specification.md#as-built-outcome-2026-08-05)
> records the final code, bytecode, validation evidence, and owner-approved
> deviations. No deployment or later lifecycle phase is authorized here.

## Implemented outcome (2026-08-05)

Tier A+B is complete in the isolated candidate; Tier C remains deferred. The
final implementation:

- bounds each Stability asset to `12` active claim assets;
- keeps sub-threshold, unpriced, or over-cap receipts in dormant mapping
  accounting without losing claim or redemption rights;
- enforces aggregate custody against active and dormant claim liabilities;
- keeps permissionless pruning available and restricts permissionless manual
  activation to the paused state;
- rejects GREEN as a Stability asset using the current `Addys` value on the
  deposit path;
- retains Stability-specific recovery guards;
- retains `getTotalValue` and `getTotalUserValue` for off-chain use while not
  exporting `valueToShares`, `sharesToValue`, or `canActivateClaimAsset`; and
- deploys at `24,568` bytes, leaving `8` bytes below EIP-170.

The original plan's broader ABI-removal and always-available manual activation
language is therefore superseded as a description of the final candidate. The
zero-raw-Stability-balance plus dormant-only claim exit remains an explicit
deferred residual, and the repository-wide suite remains blocked by the
unrelated ten-versus-eleven-argument BlueChipYieldPrices source/fixture drift.

## 1. Scope and bound baseline

This plan is forward-looking. It covers a new Stability Pool for Robinhood
Chain. It intentionally excludes Base state, migration, and replacement steps.

| Field | Bound value |
| --- | --- |
| Branch | `rh` |
| Commit | `0e093e2c23eaf6cc931fe7ff15c903a99ea36738` |
| Tree | `8b6028eed43695e13c5192d079f04dd941f0d74f` |
| Wrapper | `contracts/vaults/StabilityPool.vy` |
| Accounting module | `contracts/vaults/modules/StabVault.vy` |
| Shared vault module | `contracts/vaults/modules/VaultData.vy` |

Rebind the then-authoritative `rh` commit and tree before implementation and
stop on unexplained drift.

The current Robinhood launch posture is deliberately narrow:

- sGREEN is the only priority Stability asset;
- WETH is the only collateral with `shouldSwapInStabPools=True`;
- Stock Token Stability routing remains disabled; and
- the expected initial active claim set for sGREEN is `{WETH}`.

This makes the immediate probability of list growth low. It does not remove the
need for a contract bound in a contract intended to be non-upgradeable.

## 2. Recommendation and implementation tiers

The iterable claim-asset registry is used for NAV, not as the source of truth
for claims or redemptions. A nonzero mapping balance can already exist without
an iterable index and remains claimable, redeemable, and cumulative on later
receipts. The smallest robust design should formalize that existing mechanical
property instead of introducing a large new accounting system.

### Tier 0 — configuration-only option

This is a valid Gate 0 outcome if the owner accepts the residual immutability
risk:

- generated configuration assertion limiting the cumulative lifetime set of
  Stability-routable claim assets;
- launch with WETH as the sole routed claim asset;
- active-count, gas, oracle-health, and custody/liability monitoring; and
- a documented pause response.

Tier 0 minimizes code risk, but it does not place a persistent contract ceiling
on future governance mistakes and does not stop one-base-unit registrations.
It is therefore not the recommended final posture for a new immutable pool.

### Tier A — minimum launch hardening

Recommended even if Tier B is deferred:

1. Add-time registration gate based on cumulative claim balance value.
2. A hard per-Stability-asset active-count ceiling.
3. Capacity exhaustion and unavailable pricing fail to **dormant accounting**,
   never to a liquidation revert.
4. Shadow-liability receipt credit so existing custody cannot support a new
   over-credit.
5. Stability-specific `recoverFunds` protection for all claim liabilities.
6. Clear the vacated last array slot during swap-and-pop.
7. Guard or permanently prohibit GREEN as a Stability asset.

Expected source size is approximately 40–70 lines in `StabVault.vy`, plus the
smallest wrapper-specific recovery surface that compilation requires. This is
an estimate, not a code ceiling.

### Tier B — bounded lifecycle maintenance

Recommended before deployment if size and gas evidence remain acceptable:

- permissionless bounded pruning/deactivation;
- permissionless bounded activation of accumulated dormant balances;
- activation/deactivation/capacity events;
- active-count and dormancy views; and
- a generated configuration-to-capacity assertion.

Expected additional source size is approximately 60–120 lines, subject to the
compiled-byte and regression evidence.

### Tier C — defer unless Gate 0 identifies a concrete requirement

Do not add a five-state enum, automatic oracle quarantine, per-asset native
floors, health aggregation, governance retirement, or sweeping in the first
candidate. Those features require a larger state/event transition design and
introduce new failure windows. Existing no-timelock pause authority plus
monitoring is the safer launch response to a material oracle failure.

This deferral leaves a known residual: while a configured active feed is
unusable, the pool and affected AuctionHouse borrower traversal remain
unavailable until the feed is restored/reconfigured or a later quarantine
design is deployed in a new pool. Pause contains value movement; it does not
restore liveness.

**Recommended candidate: Tier A + Tier B.** Tier 0 should still be documented
as the explicit lower-change alternative at Gate 0; Tier C should remain
deferred.

## 3. Corrected analysis of the current contract

### 3.1 The active list is unbounded and add-time dust is admitted

`claimableAssets[stabAsset]` has no persistent length ceiling.
`MAX_STAB_CLAIMS` and `MAX_STAB_REDEMPTIONS` limit user batches, not the stored
active set. `_addClaimableBalance` registers a first receipt even if it is one
base unit.

The existing `$0.10` check only runs after a reduction. The reduction triggers
are:

1. `claimFromStabilityPool`;
2. `redeemFromStabilityPool`; and
3. `swapWithClaimableGreen`.

When the residual is nonzero and below the threshold, only the iterable index
is removed. The balance mapping, aggregate liability, and custody remain. A
later receipt re-adds the asset and includes the whole accumulated balance in
NAV. This is useful prior functionality, but it is not an add-time gate, cap,
or complete lifecycle.

### 3.2 Claims and redemptions do not need an active index

Claims address `claimableBalances[stabAsset][claimAsset]` directly. Redemptions
also use the mapping directly. Removing an asset from the NAV index therefore
does not confiscate it or prevent it from being claimed/redeemed.

Dormant balances should remain redeemable. Redemption pays for and removes
dust custody and can self-clean the liability. Excluding dormant balances from
redemption would make cleanup harder and is not recommended.

### 3.3 NAV and value-moving paths scale with active claims

`_getValueOfClaimableAssets` traverses every active claim asset and normally
makes one external pricing path per non-GREEN/sGREEN asset. Rough planning
estimates are 25–40k gas for a cold priced asset and 3–4k for a warm one, but
the exact result depends on price-source count and source behavior and must be
measured on compiled Robinhood artifacts.

The active-claim dimension affects:

| Consumer/path | NAV traversals | Failure effect |
| --- | ---: | --- |
| Stability deposit | one or more through Teller composition | Deposit reverts |
| Stability withdrawal | at least one | Withdrawal reverts |
| Internal Stability transfer | at least one | Transfer reverts |
| Single claim | at least one | Claim reverts |
| `claimMany` | up to 15 repeated claim valuations | Batch reverts; worst case is batch size × active count |
| Stability value/share views | at least one | View reverts |
| AuctionHouse phase-2 borrower inventory | via `getUserAssetAndAmountAtIndex` and vault valuation | Liquidation can revert for a borrower holding Stability shares |

Teller deposit composition can repeat valuation two or three times depending
on the path. Redemption cost primarily scales with the number of Stability
assets processed, not the active claim count, because redemption reads the
selected claim-token mapping directly.

CreditEngine excludes Stability vault ID 1 in its relevant traversal, but
AuctionHouse does not. The bound and oracle policy are therefore liquidation
safety properties, not just user-experience improvements.

A no-feed asset can also be unusually expensive: PriceDesk may traverse every
configured price source before returning zero. Gas evidence must therefore vary
source count and cannot assume that an unpriced entry is a cheap skipped row.

### 3.4 Oracle behavior: stale configured feeds revert NAV

For non-GREEN/sGREEN claim assets, `StabVault._getUsdValue` calls PriceDesk with
`_shouldRaise=True`. PriceDesk distinguishes these cases:

| Price condition | PriceDesk result in Stability NAV | Current behavior |
| --- | --- | --- |
| Valid configured source | Positive price/value | Included in NAV |
| Configured source(s), none return a usable price | Revert: `has price config, no price` | Entire caller reverts |
| No feed configured | Zero | Asset is iterated but skipped |

Therefore the existing `claimValue == 0: continue` is not a stale-feed
quarantine. It only makes the no-feed case fail open. A configured stale,
dead, or otherwise unusable feed can deny deposits, withdrawals, transfers,
claims, views, and AuctionHouse liquidation inventory traversal.

Tier A/B should not pretend to solve this with an automatic quarantine. At
launch:

- require a manipulation-resistant primary source for every routable claim
  asset; spot-AMM-only sources are prohibited;
- monitor every admitted source and the relevant NAV calls;
- pause promptly on a material price failure using the existing no-timelock
  lite action; and
- document which exits remain available while paused.

WETH's accepted Chainlink setup is the launch reference case. Any future asset
needs separate price-source admission evidence.

If automatic quarantine is reconsidered, Gate 0 must first specify a complete
states × events transition matrix, whether quarantine is keyed by claim token
or `(stabAsset, claimAsset)`, who can mark/restore it, how failure is proven,
what happens before marking, and how claims work while pricing is unavailable.

### 3.5 Receipt accounting must use unaccounted custody

AuctionHouse transfers liquidation collateral before it calls
`swapWithClaimableGreen`. Stability Pool therefore cannot take a pre-transfer
snapshot, and AuctionHouse has only minimal EIP-170 headroom. An exact custody
delta inside `StabVault` is not implementable without changing the upstream
interface/ordering.

The current code credits up to the contract's entire token balance. Existing
donated or other unaccounted custody can mask a short current receipt. Tier A
should instead use the global shadow liability:

```text
custody = IERC20(claimAsset).balanceOf(self)
liability = totalClaimableBalances[claimAsset]
assert custody >= liability
availableUnaccounted = custody - liability
credited = min(reportedReceipt, availableUnaccounted)
```

The operation must then update pair and total liabilities by exactly
`credited`. Whether to require `credited == reportedReceipt` is an explicit
design choice. Strict equality fails closed for supported standard tokens but
can deny a liquidation when a token transfers short. Partial credit preserves
liquidation availability but makes the pool pay against less collateral than
AuctionHouse reported. The recommendation is strict equality together with
standard-token admission, unless Gate 1 deliberately accepts the economic loss
and monitoring requirements of partial credit. Existing surplus can still mask
a transfer-time shortfall, which is why exact transfer equality remains an
end-to-end oracle rather than a locally proven fact.

Exact equality between actual transfer delta and reported receipt remains an
end-to-end test oracle even though it cannot be established locally from a
post-transfer-only snapshot.

### 3.6 Generic recovery can orphan claim liabilities

`VaultData.recoverFunds` rejects a registered vault asset with a nonzero vault
balance, but it does not inspect Stability claim liabilities. Stability Pool
exports the shared `VaultData` interface wholesale, so a claim token could be
transferred without reducing `claimableBalances` or
`totalClaimableBalances`.

Do not change shared `VaultData` for all four vault types unless unavoidable.
First test whether Vyper supports replacing the wholesale recovery exports in
`StabilityPool.vy` with guarded wrapper functions while preserving the needed
ABI. Both single and many variants must require:

```text
totalClaimableBalances[asset] == 0
```

Monitor all pending and executed recovery actions targeting the Stability
Pool, even after the guard exists.

### 3.7 GREEN and post-crash edge cases

If GREEN is ever configured as a Stability asset, a non-sGREEN redemption can
add GREEN as a claim against GREEN itself. Raw GREEN balance and
`claimableBalances[GREEN][GREEN]` can then be counted twice. Select one launch
rule:

- recommended: add a cheap explicit code guard prohibiting GREEN as a
  Stability asset; or
- permanently assert the same exclusion in generated configuration and every
  governance path.

GREEN can still be a claim asset created by redemptions for a non-GREEN
Stability asset. Capacity must count actual active occupancy, not merely assets
currently marked routable. Reserve one slot for GREEN or exempt that precisely
defined special slot from the ordinary collateral capacity calculation while
still bounding total NAV iterations.

A large liquidation can also reduce a Stability asset's raw token balance to
zero while shares remain outstanding. Withdrawal and internal-transfer paths
assert a nonzero Stability-asset balance. The launch suite must prove a
deterministic post-crash user exit using the intended claim/redemption path.
If that exit depends on claims or redemptions, their launch flags must be
enabled and verified. Monitor:

```text
stabAssetBalance == 0 && totalShares != 0
```

## 4. Tier A/B target behavior

### 4.1 Minimal states

Do not add a stored enum for Tier A/B. Define state from existing accounting:

| State | Pair balance | Active index | NAV iteration | Claim/redeem |
| --- | ---: | ---: | --- | --- |
| Absent | `0` | `0` | No | No balance |
| Dormant | `> 0` | `0` | No | Available |
| Active | `> 0` | `> 0` | Yes | Available |

The only iterative set is Active. Dormant value is an intentionally bounded,
temporarily unrecognized NAV component.

### 4.2 USD activation and retention thresholds

Use Stability-specific hardcoded USD constants for the first candidate:

- provisional activation floor: `$0.25` cumulative value;
- provisional retention floor: existing `$0.10` residual value; and
- require retention floor `<` activation floor to provide hysteresis.

This avoids a MissionControl/configuration expansion and decimal-specific
native floors. On receipt, PriceDesk should be called with `_shouldRaise=False`
only for the activation decision. A returned zero means **no usable value is
available for this decision**—which can mean no feed or configured-but-currently
unusable sources—not that one particular oracle failure was proven. The receipt
remains accounted and dormant; it must not revert liquidation.

On reduction, the residual USD value is already being computed. Preserve the
existing `$0.10` deactivation behavior through a centralized helper.

Thresholds are provisional until gas/economic tests quantify the maximum
aggregate hidden value and MEV/value-transfer bound. They are hardcoded to make
the deployed contract's bound immutable and reviewable.

### 4.3 Bounded add-time registration

After shadow-liability credit:

1. If the pair is already active, add the credit and keep it active.
2. If cumulative USD value is zero or less than the activation floor, keep it
   dormant.
3. If value is at least the floor and a slot is available, activate atomically.
4. If capacity is full, keep the full credited balance dormant and emit a
   capacity event; never revert the liquidation solely for lack of a slot.

The contract maximum is provisional until measured. Start measurement at
active sizes `0, 1, 2, 4, 8, 12, 15`; 12 is a candidate, not a conclusion.
Document whether the GREEN reserve is inside that maximum.

### 4.4 Permissionless bounded maintenance

Tier B adds candidate-driven arrays bounded by a small compile-time maximum:

```text
pruneClaimableAssets(stabAsset, claimAssets[])
activateClaimAssets(stabAsset, claimAssets[])
```

`pruneClaimableAssets` must be idempotent and, per supplied candidate:

- clear an exact-zero active entry;
- deactivate a nonzero active residual below the retention floor;
- leave above-floor active balances unchanged;
- never sweep custody, delete accounting, alter shares, or scan the full set;
  and
- clear the vacated last array slot after swap-and-pop.

`activateClaimAssets` must be idempotent and, per supplied candidate:

- do nothing for absent or already-active pairs;
- value the cumulative dormant balance without raising on unavailable price;
- activate only at or above the activation floor and with capacity available;
- otherwise leave the complete liability dormant; and
- never make unrelated candidates fail because one price is unavailable.

No keeper reward is needed initially. Monitoring can supply eligible
candidates, and any account can execute bounded maintenance.

### 4.5 Dormant-value bound

The hidden-value ceiling must be stated, enforced where possible, and tested.
For `D` dormant pairs under one Stability asset and activation floor `A`, the
ordinary dust bound immediately after a successful price evaluation is:

```text
aggregate recognized-price dormant value <= D * A
```

Price appreciation or a full active set can later move a dormant pair above
`A`; permissionless activation and monitoring close that interval but do not
make the bound instantaneous. That is incomplete unless `D` is also bounded.
Enforce both:

- generated limit on the **cumulative lifetime set** of distinct claim tokens
  that can route into each Stability Pool, not merely the simultaneously
  enabled set; configuration churn must not reset the count;
- hard active-count ceiling in the contract;
- permissionless activation so a now-valuable dormant pair cannot remain
  hidden merely because nobody sends another receipt; and
- alerting on dormant pair count, individually valued dormant balances, and
  aggregate valued dormant exposure.

An unavailable-price balance cannot be assigned a USD bound at that moment.
It is governed by admission limits, custody/liability alarms, oracle alarms,
and pause response. The configuration ceiling is part of the mechanism, not a
substitute for it.

Reactivation creates a bounded NAV jump. An atomic deposit → dormant
activation/redemption → withdrawal sequence could capture part of that jump.
This is accepted only within the approved dormant-value ceiling and must be in
the fuzz model. Do not prevent dormant redemption merely to address this low
bounded risk.

### 4.6 Events and views

Minimum Tier A/B observability:

- `ClaimAssetActivated(stabAsset, claimAsset, balance, activeCount)`;
- `ClaimAssetDeactivated(stabAsset, claimAsset, balance, activeCount, reason)`;
- `ClaimAssetCapacityReached(stabAsset, claimAsset, balance, activeCount)`; and
- `ClaimAssetReceiptRecorded(stabAsset, claimAsset, reported, credited,
  resultingBalance, isActive)`.

Minimum views:

- `getNumActiveClaimAssets(stabAsset)`;
- `getClaimAssetState(stabAsset, claimAsset)` derived as absent/dormant/active;
- `canActivateClaimAsset(stabAsset, claimAsset)`; and
- activation/retention constants exposed through public constant getters or
  an equivalent ABI-stable view.

Do not add an unbounded aggregate-dormant view. Indexers compute aggregates
from events and targeted reads.

## 5. Literal accounting and safety invariants

1. For each claim token, `totalClaimableBalances[token]` equals the sum of pair
   liabilities across all registered Stability assets.
2. `IERC20(token).balanceOf(pool) >= totalClaimableBalances[token]` for every
   claim token; if violated, every affected value-moving path fails closed.
3. A receipt credit never exceeds post-transfer unaccounted custody:
   `credit <= custody - priorTotalLiability`. Exact transfer delta equality is
   an end-to-end test oracle, not a locally available pre/post invariant.
4. Every active pair has exactly one nonzero index and every in-range array
   entry points back to that index.
5. Every dormant pair has a nonzero balance and zero active index.
6. Every absent pair has zero balance and zero active index.
7. Active count and total NAV iteration never exceed the contract maximum,
   including any reserved GREEN slot.
8. Swap-and-pop clears the vacated last slot and cannot alter another pair's
   balance.
9. Capacity or unavailable activation price never causes a received
   liquidation asset to be unaccounted or causes liquidation to revert solely
   because registration failed.
10. Recovery cannot transfer a token with any Stability claim liability.
11. Maintenance never changes user shares, custody, or claim liabilities.
12. A reverted receipt, claim, redemption, activation, deactivation, deposit,
    withdrawal, or transfer rolls back all related state.
13. New share minting cannot use a knowingly false price or exceed the active
    iteration bound.
14. Full user exit remains possible after Stability-asset depletion under the
    exact launch flags and pause policy.

## 6. Phased work and gates

### Phase 0 — bind, measure, and choose the tier

No production edits.

- Rebind authoritative source, compiler, ABI, runtime size, and clean tree.
- Inventory every Stability selector and consumer, including Teller,
  AuctionHouse, CreditEngine, Lootbox, Switchboard, and generated interfaces.
- Confirm selective wrapper exports are feasible before choosing the recovery
  implementation.
- Measure the real matrix, not only active-count views:

| Variable | Required cases |
| --- | --- |
| Active claims | `0, 1, 2, 4, 8, 12, 15` |
| Price-source count | `0, 1`, and the admitted maximum |
| Source state | cold-valid, warm-valid, no feed, stale/dead configured feed |
| Claim batch | `1` and `15`, crossed with the active ceiling |
| Teller deposit | each composition causing one, two, or three NAV traversals |
| Stability-asset count | redemption/redeem-many at launch and maximum config |
| Auction path | swap receipt and phase-2 borrower inventory traversal |

- Record transaction gas, failure mode, and creation/runtime EIP-170 headroom.
- Produce the complete Tier A/B states × events transition table.
- Quantify dormant value/MEV bounds for proposed `$0.25/$0.10` thresholds.

**Gate 0 owner decisions:**

1. Tier 0 only, Tier A, or Tier A + B. Recommendation: Tier A + B.
2. Provisional hard maximum and whether one GREEN slot is reserved within it.
3. `$0.25` activation and `$0.10` retention, or different hardcoded USD values.
4. Code prohibition of GREEN as a Stability asset versus permanent generated
   configuration prohibition. Recommendation: code prohibition.
5. Launch claim/redemption enablement and the post-crash exit policy.
6. Strict short-receipt rejection versus partial credit. Recommendation:
   strict rejection plus standard-token admission.

### Phase 1 — exact specification

No production edits.

- Specify all transition preconditions, no-op outcomes, events, and reverts.
- Decide shared `StabVault.vy` behavior versus a Robinhood-specific fork.
  Shared code is preferable only if the rules are valid for every future
  deployment and all shared regression evidence passes; otherwise isolate the
  Robinhood behavior.
- Specify shadow-liability credit and strict-versus-partial short receipt.
- Specify GREEN reserve/exclusion behavior.
- Specify pause behavior for deposits, withdrawals, claims, redemptions,
  liquidation receipts, and recovery.
- Bind exact ABI changes and shared-module impact.

**Gate 1:** independent design review. Approval authorizes only an isolated
implementation candidate.

### Phase 2 — isolated Tier A/B candidate

Expected primary surface:

- `contracts/vaults/modules/StabVault.vy`;
- `contracts/vaults/StabilityPool.vy` for Stability-specific recovery and
  externally exposed maintenance/views;
- generated ABI/inventory expectations; and
- Stability-specific tests and token/oracle mocks.

Avoid MissionControl, shared `VaultData`, and AuctionHouse changes unless Phase
0 proves they are necessary and Gate 1 explicitly approves their blast radius.

Implementation order:

1. centralize count/index activation and swap-and-pop deactivation;
2. clear vacated slots and expose count/state views;
3. add shadow-liability receipt credit;
4. add USD add-time gate and fail-to-dormant capacity behavior;
5. add recovery guards and GREEN protection;
6. add bounded prune and activate entry points;
7. add events and mechanically regenerate ABI/inventories.

**Gate 2:** independent review of the complete source delta, shared behavior,
compiled bytes, and threat model.

### Phase 3 — validation

Deterministic tests must cover:

- below-floor first receipt, cumulative crossing, above-floor first receipt;
- zero/unavailable activation price remaining dormant without receipt revert;
- capacity at max minus one, max, and max plus one, including liquidation;
- active accumulation while capacity is full;
- permissionless activation without a new receipt;
- exact-zero and below-retention pruning;
- hysteresis and repeated activate/deactivate cycles;
- first/middle/last swap-and-pop with vacated-slot clearing;
- absent, dormant, active, and above-floor candidates; idempotency;
- 6-, 8-, and 18-decimal claim tokens;
- valid, no-feed, stale, dead, reverting, restored, and manipulated prices;
- source-count and cold/warm gas cases from Phase 0;
- custody below liability, exact receipt, short receipt, excess receipt, and
  pre-existing donation;
- fee-on-transfer, rebasing, false/malformed/reverting token behavior;
- claim, `claimMany(15)`, redemption, `swapWithClaimableGreen`, sGREEN
  conversion, and dormant redemption;
- recovery single/many rejection for any nonzero liability and pending-action
  monitoring;
- GREEN-as-Stability prohibition and GREEN claim-slot accounting;
- full post-crash exit with zero raw Stability asset and nonzero shares;
- exact launch pause and claim/redemption flags; and
- event fields, no-op outcomes, rollback, and no share changes from maintenance.

Stateful/fuzz action alphabet must include receipt, deposit, withdrawal,
internal transfer, claim, batched claim, redemption, pruning, permissionless
activation, donation, price failure/restoration, capacity exhaustion, and
re-addition. It must prove every Section 5 invariant, the dormant-value bound,
the maximum iteration bound, and the maximum allowed value captured around a
dormant NAV jump.

Gas/size evidence must include incremental gas per active asset, composed
Teller/AuctionHouse transactions, batch-15 × active-ceiling claims, all admitted
source counts/states, and creation/runtime bytecode for every changed contract.

**Gate 3:** complete deterministic, stateful, invariant, mutation, gas,
bytecode, ABI, and inventory evidence. A green suite does not authorize
integration or deployment.

### Phase 4 — Robinhood configuration qualification

- Keep sGREEN as the sole priority Stability asset unless separately changed.
- Keep WETH as the sole initially routed collateral unless separately admitted.
- Preserve Stock Token Stability exclusion.
- Assert generated routable-asset count plus reserved GREEN occupancy does not
  exceed contract capacity.
- Require a manipulation-resistant primary source for every routable asset;
  reject spot-AMM-only admission.
- Bind monitoring below the contract maximum and verify launch pause,
  claim, and redemption flags.

**Gate 4:** owner/security/risk approval of exact configuration and generated
proof. Deployment, activation, and release remain separate decisions.

## 7. Monitoring and operating response

The deployment packet must name monitor owner, response owner, pause authority,
and thresholds for:

- active occupancy at 50%, 75%, and 90% of maximum;
- capacity-reached events and dormant activation candidates;
- dormant pair count and valued aggregate exposure;
- unavailable/stale/manipulable prices and failed NAV calls;
- custody below total liability or unexplained surplus growth;
- `stabAssetBalance == 0 && totalShares != 0`;
- repeated activation/deactivation churn;
- deposit, withdrawal, claim, and AuctionHouse gas regression; and
- pending or executed Stability Pool recovery actions.

The oracle runbook must state which operations pause, which exits remain
available, and how the owner validates recovery before unpausing. Monitoring is
not a replacement for the contract active-count cap.

## 8. Explicit exclusions and follow-up audits

This plan does not:

- analyze Base or a legacy migration;
- authorize implementation, deployment, configuration, activation, or release;
- add automatic quarantine, governance retirement, or a dust sweep;
- add keeper rewards or an upgradeable proxy;
- redesign the pool as a per-asset accumulator; or
- reopen Deleverage, CCIP, Uniswap, LP, PSM, or Stock Stability work.

The following deserve separate audits before treating the whole Stability
system as comprehensively hardened, but they are not silently expanded into
this dust/index task:

- Stability-asset share math under direct donation/raw-balance changes;
- `DECIMAL_OFFSET`, rounding, and final-share economics;
- Deleverage burn-as-payment correctness;
- exact launch claim/redemption enablement and pause composition;
- the premise and governance consequences of non-upgradeability; and
- composition with the separate Gov Vault escape-hatch plan.

## 9. Definition of ready

A new Robinhood Stability Pool is ready to enter a separately authorized
deployment candidate only when:

- the owner has selected Tier 0/A/A+B and resolved every Gate 0 decision;
- below-floor and unavailable-price receipts are safely accounted dormant;
- active NAV iteration has a measured, enforced maximum;
- capacity exhaustion does not deny liquidation solely to register an asset;
- dormant balances can be permissionlessly activated and eligible active dust
  can be permissionlessly pruned if Tier B is selected;
- custody, liability, index, recovery, GREEN, and post-crash exit invariants
  pass deterministic and stateful testing;
- gas is proven for actual source states and composed worst-case paths;
- Robinhood admits only bounded assets with manipulation-resistant pricing;
- ABI/inventories match compiled bytes; and
- independent reviewers approve the exact source, tree, artifacts, and
  residual-risk statement.

Passing this definition establishes candidate readiness only. Integration,
deployment, configuration, activation, and release remain owner-controlled
phases.
