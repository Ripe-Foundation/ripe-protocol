# PR #95 Smart-Contract Change Rationale

Status: explanatory review document for draft PR #95. This document does not
authorize merge, deployment, activation, a Safe transaction, or any other live
mutation.

## Purpose and comparison basis

PR #95 contains a broad remediation of issues found while reviewing PR #67.
This document explains every production smart-contract source file changed by
the draft, why the change exists, the behavior it is intended to enforce, and
the important limitations that remain.

The source inventory below was taken from the three-dot diff between:

- target branch: `rh` at `3a4cac429a860ffc95bd85612d9e345108332833`;
- remediated source head before this document: `304019c4be7b7fad8da4b355c28e9e0c56dd1c45`.

There are 13 changed production contract files:

| Contract source | Nature of change | Primary reason |
| --- | --- | --- |
| `contracts/config/SwitchboardAlpha.vy` | Executable validation | Prevent governance from installing a priority Stability Pool that lacks the runtime capabilities liquidation requires. |
| `contracts/config/SwitchboardBravo.vy` | Executable validation | Validate a special Stability Pool against its real populated/empty state, downstream selectors, and paused state. |
| `contracts/config/SwitchboardCharlie.vy` | Executable validation | Prevent the preferred Stability Pool pointer from accepting a partial or incompatible implementation. |
| `contracts/core/AuctionHouse.vy` | Liquidation accounting and code-size refactor | Make liquidation retries safe, prevent no-progress fees, and prove exact collateral receipt by the pool. |
| `contracts/core/CreditEngine.vy` | Liquidation eligibility and code-size refactor | Keep an unhealthy account frozen while allowing another liquidation pass only after its auctions are gone. |
| `contracts/core/Teller.vy` | Reentrancy/composition guard | Prevent housekeeping callbacks from corrupting an in-progress token receipt measurement. |
| `contracts/core/VaultMigrator.vy` | Migration route and state preservation | Keep historical RipeGov vaults out of generic migration while preserving balances, points, and lock terms. |
| `contracts/modules/Addys.vy` | Registry constants | Match the immutable live RipeHq order: RIPE CCIP pool ID 23 and GREEN CCIP pool ID 24. |
| `contracts/priceSources/UniswapV2Prices.vy` | Price-authority boundary | Keep manipulable Uniswap V2 observations available for monitoring but impossible to consume as a protocol price feed. |
| `contracts/vaults/RipeGov.vy` | Lock, points, and migration behavior | Preserve original migration terms and constrain privileged contributor locks. |
| `contracts/vaults/modules/StabVault.vy` | NAV, custody, claims, and delivery accounting | Keep claim liabilities reserved, fail closed on missing prices/custody, and reject short user deliveries. |
| `solidity/src/RipeCcipBurnMintTokenPools.sol` | Comments/provenance clarification only | Remove false claims that the repository candidate proves the source used for already-live pools. |
| `solidity/src/RipeTokenPool.sol` | Comments/provenance clarification only | Classify this configurable-capability pool as retained legacy/testnet history, not the selected mainnet candidate. |

## Why the changes span multiple contracts

Several findings were compositional rather than isolated:

1. AuctionHouse sends collateral to a Stability Pool.
2. StabVault records the received collateral as a claim liability.
3. Switchboards decide which Stability Pool implementations are allowed into
   those paths.

A check in only one layer is not sufficient. For example, a correct StabVault
cannot protect liquidation if governance points MissionControl at an older
contract without `canAcceptLiquidationAsset`, and a selector probe cannot prove
that the amount AuctionHouse just sent was actually received. PR #95 therefore
uses defense in depth:

| Risk | Admission/configuration defense | Caller defense | Accounting defense |
| --- | --- | --- | --- |
| Partial Stability Pool implementation | Alpha, Bravo, and Charlie probe the selectors that downstream code calls. | AuctionHouse calls `canAcceptLiquidationAsset` before moving collateral. | StabVault validates supported asset roles and claim accounting. |
| Donation-masked short receipt | Not applicable. | AuctionHouse measures the pool's balance delta around the exact transfer. | StabVault still checks aggregate custody against aggregate liabilities. |
| Claim liability reused as pool backing | Bravo validates the configured pool/asset relationship. | AuctionHouse uses the pool's reported admissibility. | StabVault subtracts all reserved claims from spendable backing and forbids role overlap. |
| RipeGov migration loses special state | Dedicated migration routes and pause requirements. | VaultMigrator selects the route and carries state. | RipeGov preserves stored terms and accepts only authorized migration state transitions. |

This is the main reason the contract diff is broader than a one-file patch.

## 1. `SwitchboardAlpha.vy`

### What changed

- Added a minimal Stability Pool read interface containing:
  `claimableBalances`, `canAcceptLiquidationAsset`, and `isPaused`.
- `setPriorityStabVaults` now validates the sanitized priority list before
  storing a pending governance action.
- The pending action is validated again immediately before execution.
- Validation now requires each referenced VaultBook ID to resolve to a real
  contract, requires MissionControl to support the configured vault/asset pair,
  probes the downstream Stability Pool selectors, and rejects a paused pool.

### Why this is required

The old configuration path could accept a registered contract based on shallow
identity checks even though AuctionHouse now calls
`canAcceptLiquidationAsset` before every Stability Pool liquidation swap. An
older pool or purpose-built partial contract could therefore pass governance
configuration and later make liquidation revert at runtime.

Checking both when the action is proposed and when it is executed matters
because governance actions are timelocked. A registry binding, supported asset,
pause state, or implementation can change during the delay.

### Important behavior detail

The calls using the zero address are capability probes, not a claim that the
zero address is a valid claim asset. Their return values are deliberately not
required to be true/nonzero. A revert or malformed response rejects the
candidate because it proves the selector is unavailable or incompatible.

### Interface, storage, and risk impact

- No new external SwitchboardAlpha selector is introduced.
- No persistent storage variable is added.
- Existing governance actions become more restrictive: a partial, paused, or
  incompatible pool that was previously accepted is now rejected.
- The second validation is intentionally fail closed; a pool becoming invalid
  during the timelock prevents confirmation.

### Representative validation

- `test_priority_stab_vault_rejects_legacy_partial_interface`
- `test_priority_stab_vault_revalidates_interface_at_confirmation`
- priority-list filtering and edge-case coverage in
  `tests/config/test_switchboard_alpha.py`

## 2. `SwitchboardBravo.vy`

### What changed

The validator for an asset's `specialStabPoolId` now probes:

- `getNumVaultAssets`;
- `vaultAssets(1)` when the pool is populated;
- `canAcceptLiquidationAsset`;
- pair-specific `claimableBalances`;
- aggregate `totalClaimableBalances`;
- `isPaused`.

It also rejects a zero/non-contract registry result, a populated pool whose
first asset slot is empty, an incompatible populated pair, and a paused pool.

### Why this is required

A VaultBook ID proves registration, not that the registered contract implements
the Stability Pool ABI used by liquidation. Without these probes, an asset
could be configured to swap through a pool that reverts as soon as
AuctionHouse reaches it.

The validator uses `getNumVaultAssets`, rather than treating a nonzero raw
`vaultAssets(1)` slot as proof of a live asset. Vault deregistration does not
necessarily erase the old mapping slot. A pool that once had an asset but is
currently empty must remain reusable instead of being permanently rejected by
stale storage.

### Empty-pool behavior

A freshly deployed or legitimately emptied pool is allowed before its first
deposit. The code still probes the selector, but it requires a true
`canAcceptLiquidationAsset` result only after the pool has a current Stability
Pool asset. This avoids turning safe interface validation into an accidental
"must already have deposits" deployment requirement.

### Interface, storage, and risk impact

- No new external SwitchboardBravo selector is introduced.
- No persistent storage variable is added.
- Configuration becomes fail closed for partial and paused pools.
- A populated pool must affirm the exact Stability-asset/liquidation-asset
  pair; an empty pool is checked for ABI compatibility without pretending a
  nonexistent first asset is active.

### Representative validation

- `test_special_stab_pool_rejects_legacy_partial_interface`
- `test_special_stab_pool_rejects_paused_pool`
- `test_special_stab_pool_accepts_reusable_pool_with_stale_removed_slot`
- existing special-pool ID and whitelist validation coverage in
  `tests/config/test_switchboard_bravo.py`

## 3. `SwitchboardCharlie.vy`

### What changed

The preferred Stability Pool pointer validator now probes the pool's:

- first asset view;
- pair claim balance view;
- liquidation-asset acceptance view;
- aggregate claim balance view;
- pause state.

It continues to require a valid VaultBook contract, a different pointer, and
support for sGREEN, and it rejects a paused pool.

### Why this is required

The preferred pool is a protocol routing pointer. Previously, a contract could
provide the two shallow views used by the validator but omit a selector that a
later deposit, claim, or liquidation path needs. The pointer would be accepted,
and the failure would be deferred until a user or keeper exercised the route.

The probes intentionally permit a valid empty pre-deposit pool. They verify ABI
shape, not preexisting liquidity.

### Interface, storage, and risk impact

- No external ABI or storage-layout change.
- Pointer changes are more restrictive and fail at proposal/confirmation time
  instead of failing in a user or liquidation transaction later.

### Representative validation

- `test_preferred_stability_pool_rejects_legacy_partial_interface`
- preferred-pool paused/unsupported/binding revalidation coverage in
  `tests/config/test_switchboard_charlie.py`

## 4. `AuctionHouse.vy`

### What changed

#### A. Liquidation state is an account-wide unhealthy freeze

Once a user reaches the liquidation threshold, `userDebt.inLiquidation` stays
set until debt health is restored. The freeze applies to the whole account,
including protocol-held RIPE/GREEN-like zero-LTV assets and positive-LTV
collateral that policy does not permit AuctionHouse to sell, such as a
tokenized security awaiting a governance-controlled recovery route.

Auction existence now has a separate job: an outstanding auction blocks a
competing liquidation pass, while a frozen unhealthy user with no auction may
be retried permissionlessly. `CreditEngine.canLiquidateUser` mirrors this
distinction. Health restoration still clears the flag through the existing
CreditEngine/Ledger path, which also removes outstanding auctions.

#### B. No-progress liquidation calls are economically inert

If no debt was repaid and no asset was queued, the call clears liquidation fees
and the keeper fee before updating debt. The call can be retried after the
underlying problem is repaired, but repeated calls cannot grow debt or mint
keeper compensation without liquidation progress.

#### C. Stability Pool collateral receipt is measured per call

AuctionHouse records the pool's liquidation-asset balance immediately before
and after `_transferCollateral` and requires the exact increase reported by the
source vault. This prevents a preexisting donation from masking a short or
fee-on-transfer receipt.

#### D. Single-item wrappers share the batch implementations

`liquidateUser` routes a one-user array through the shared multi-user internal
path, and `buyFungibleAuction` routes one purchase through the shared batch
purchase path. Both public selectors remain present. Several arithmetic helper
expressions were also shortened without changing their formulas.

### Why these changes are required

The old code used one boolean for two different concerns: freezing an unhealthy
account and proving that an auction already owned the liquidation workflow.
Clearing the flag when no auction was queued made deficient collateral
retryable, but it also removed the explicit account-wide freeze requested for
zero-LTV and non-auctionable collateral. Keeping the flag while continuing to
reject every retry had the opposite failure: a healthy asset could be consumed
by direct Stability Pool settlement, leave a deficient remainder with no
auction, and permanently block a later retry after backing was repaired.

Separating the two concerns preserves both invariants. The debt flag freezes
the account; `Ledger.hasFungibleAuctions(user)` determines whether another
liquidation pass may run. A no-progress retry must also be economically inert,
or repeated calls could charge fees without repaying debt or creating an
auction.

The old aggregate pool receipt check could be satisfied by tokens already in
the pool. Measuring the caller-local balance delta is what proves that this
specific transfer delivered what its source vault reported.

The wrapper consolidation was needed to pay for the security checks without
removing public selectors or exceeding EIP-170. It is a code-size refactor, not
an intentional change to caller-facing single-vs-batch semantics.

### Interface, storage, and risk impact

- Public AuctionHouse selectors are preserved.
- No persistent storage variable is added; existing transient liquidation
  bookkeeping remains transaction-scoped on the EVM.
- No-progress calls emit a liquidation result but charge no fee. The account
  remains frozen while unhealthy and is retryable only when no auction exists.
- Positive-LTV collateral that is not burnable, transferable, Stability-Pool
  eligible, or auctionable remains frozen but requires an explicit recovery
  route; the flag by itself does not repay the debt.
- The pool balance-delta assertion means fee-on-transfer or otherwise short
  incoming liquidation assets are unsupported and revert atomically.
- Final measured deployed runtime: 23,863 bytes, leaving 713 bytes below the
  EIP-170 limit.

### Representative validation

- `test_direct_settlement_keeps_unhealthy_remainder_frozen_and_retryable_without_auction`
- nonzero-fee no-progress retry coverage in
  `tests/core/auctionHouse/test_ah_liquidation.py`
- non-auctionable positive-LTV collateral plus zero-LTV account-freeze coverage
  in `tests/core/auctionHouse/test_ah_liquidation.py`
- final-auction depletion with unhealthy residual debt remains frozen and
  retryable in `tests/core/auctionHouse/test_ah_auctions.py`
- `test_stability_swap_rejects_donation_masked_short_receipt_from_shares_vault`
- existing single/many liquidation and single/many auction-purchase behavior

## 5. `CreditEngine.vy`

### What changed

Debt-health checks now distinguish an account-wide liquidation freeze from an
outstanding auction. `hasGoodDebtHealth` and redemption remain false while the
flag is set. `canLiquidateUser` may become true for a frozen user only when no
auction exists and the live collateral/debt values are at the liquidation
threshold.

Equivalent liquidation/redemption threshold calculations now share one helper.
Two existing arithmetic paths were also expressed more compactly: repayment
refund is `available - repaid` after `repaid = min(available, debt)`, and dynamic
rate boost arithmetic is inlined. The subtraction uses `unsafe_sub` only after
the preceding `min` proves `repaid <= available`.

### Why these changes are required

Without the auction-aware view, the public eligibility check would say a frozen
no-auction account cannot be liquidated even though AuctionHouse intentionally
allows that retry. Keepers and operational tooling would receive the opposite
answer from the action they are meant to evaluate.

The first correct implementation fell below the repository's ratified 200-byte
EIP-170 headroom floor. Consolidating equivalent arithmetic brought the final
deployed runtime back above the floor without removing selectors or weakening
the liquidation policy. This self-retires the prior RH-D026 exact waiver rather
than extending it to a new contract version.

### Interface, storage, and risk impact

- Public selectors and persistent storage are unchanged.
- A frozen account with an outstanding auction still reports non-liquidatable.
- A frozen account without an auction reports liquidatable only after the live
  position reaches its liquidation threshold; being above ordinary LTV alone
  is not enough.
- Final measured deployed runtime: 24,367 bytes, leaving 209 bytes of EIP-170
  headroom.

### Representative validation

- the direct CreditEngine state matrix in
  `tests/core/creditEngine/test_credit_liquidation_state.py`, covering healthy,
  redemption-only, and liquidatable positions across frozen/unfrozen and
  auction/no-auction states;
- exact inclusive redemption/liquidation boundaries, zero thresholds, zero
  debt, and last-auction removal in the same CreditEngine-owned suite;
- active-auction rejection in `test_ah_liquidation_auction_creation`
- no-auction direct-settlement retry coverage
- non-auctionable collateral and final-auction-depletion retry coverage
- repayment/refund caps against both declared input and actual CreditEngine
  balance, plus the existing dynamic-borrow-rate CreditEngine regressions
- exact constructor-bound runtime and default headroom-floor checks

## 6. `Teller.vy`

### What changed

`_performHousekeeping` now reverts while `receiptMeasurementActive` is true.

### Why this is required

Teller measures custody before and after a vault deposit to prove the exact
token receipt. During that measurement window, a callback into another Teller
route must not be allowed to move custody in the opposite direction and make a
short outer receipt appear exact.

Housekeeping is not just bookkeeping: it can call Ledger, Curve pricing, and
CreditEngine. Those external calls create compositional callback surfaces.
Blocking housekeeping during the receipt window closes the remaining nested
route under the same mutex already used by direct deposits.

### Interface, storage, and risk impact

- No external ABI or storage-layout change.
- Normal housekeeping outside a receipt window is unchanged.
- A nested protocol callback that attempts housekeeping during an active
  receipt measurement now fails atomically by design.
- Teller is close to EIP-170 after all changes: measured deployed runtime is
  24,532 bytes, leaving 44 bytes of headroom. The shared artifact ledger binds
  the full deployed runtime, including immutable data.

### Representative validation

- receipt-window callback and housekeeping coverage in
  `tests/core/teller/test_teller_deposit.py`, including:
  `test_receipt_window_blocks_every_custody_changing_nested_route` and
  `test_after_credit_callback_cannot_corrupt_the_measured_receipt`

## 7. `VaultMigrator.vy`

### What changed

#### A. Generic migration excludes every historical RipeGov ID

`migrateVaultPositions` now consults MissionControl's monotonic
`isRipeGovVaultId` classifier for both source and target. It no longer excludes
only whichever vault is the current core pointer at the time of the call.

#### B. RipeGov routes require an explicit migration freeze

Both exporter-capable and legacy RipeGov migration require Teller to be paused.
The exporter-capable route also requires the source ID to be classified as a
historical RipeGov and rejects the constructor-bound immutable Base legacy
source, which must use its dedicated legacy route.

### Why these changes are required

A former core RipeGov vault does not become a basic shares vault when the core
pointer rotates. Sending it through generic migration would discard lock,
governance-point, and tombstone semantics. Historical classification must be
monotonic.

Requiring Teller to be paused prevents ordinary user activity and most
Teller-routed mutation during the administrator-controlled migration window.

Governance-point disable settings are intentionally not migration state. They
are emergency, vault-local controls used when a particular vault approaches a
points-overflow risk. Migration preserves the points recorded by the source,
while the target starts under its own independently administered disable
policy and may resume accrual.

### Approved batch and lock-term design retained

This change does **not** convert migration into one-user or one-asset calls.
The approved ABI remains a bounded batch of up to 25 users. For each user, all
supported governance assets are migrated atomically.

For the Base legacy wind-down:

1. pause Teller;
2. lower `minLockDuration` for every participating asset under the approved,
   censused configuration plan;
3. keep the legacy source unpaused and the target paused;
4. snapshot all supported assets for a user before the first withdrawal;
5. migrate the user batch atomically;
6. restore configuration and verify it before unpausing the target/Teller.

The one-block reduction works only if the census proves the new minimum is
below every migrating position's stored historical minimum. Lowering only a
maximum duration does not provide the same unlock behavior.

### Interface, storage, and risk impact

- Existing public migration selectors and the multi-user/all-assets behavior
  are preserved.
- No new persistent storage variable is added.
- Generic migration becomes intentionally stricter.
- Target user/asset rows must still satisfy the import contract's virginity or
  explicitly allowed stale-zero preconditions; a dirty target makes the batch
  revert atomically.
- A late user failure still rolls back earlier users in the same transaction.
- Measured deployed runtime: 12,464 bytes.

### Representative validation

- `test_core_pointer_rotation_preserves_the_historical_exclusion_boundary`
- `test_migration_does_not_carry_source_point_disable_policy`
- `test_exporter_migration_preserves_pre_wind_down_terms_unlock_and_points`
- `test_teller_migration_requires_teller_and_both_vaults_paused`
- `test_active_legacy_locks_migrate_for_many_users_and_all_assets_after_one_block_min_reduction`
- late-user rollback, same-action-block rollback, 25-user limit, and gas
  characterization in `tests/vaults/test_vault_migrator_legacy.py`

## 8. `Addys.vy`

### What changed

The two CCIP registry constants were corrected from:

- GREEN = 23 / RIPE = 24

to the immutable live registry order:

- RIPE = 23 / GREEN = 24.

### Why this is required

The live pools were registered RIPE first and GREEN second. Repository
constants, test fixtures, and reporting tools had retained the planned order
instead of the actual onchain order. That could cause operator output—and any
future contract code that begins consuming these constants—to label or resolve
the opposite pool.

### Interface, storage, and risk impact

- No storage or public ABI change.
- The current `Addys` struct does not expose either CCIP pool, and the review
  found no existing runtime consumer of these two constant names. The active
  bridge itself resolves pools through Chainlink's TokenAdminRegistry and is
  not rerouted by this edit.
- This is still important preventive correctness: future code must not compile
  the opposite live topology into a contract.

## 9. `UniswapV2Prices.vy`

### What changed

- Standard PriceSource `getPrice` now returns zero.
- `getPriceAndHasFeed` now returns `(0, false)`.
- `hasPriceFeed` now returns false.
- Added `getMonitoringPrice`, which exposes the existing weighted/spot
  monitoring calculation to direct callers.
- Direct reserve-price and snapshot/configuration views remain available.

### Why this is required

Uniswap V2 reserve ratios are manipulable spot observations. Repeated
manipulated snapshots can also suppress the weighted monitoring result for an
extended period. The owner decision was to retain this data for monitoring,
not to promote it into a collateral-grade or value-bearing oracle.

The boundary must be enforced in the contract, not only in a runbook. Returning
`hasFeed = false` means an accidental PriceDesk registration cannot silently
turn the adapter into protocol pricing authority.

### Interface, storage, and risk impact

- The new direct monitoring getter is an intentional ABI addition.
- Standard PriceSource calls are intentionally disabled even though direct
  monitoring calls can return a value.
- Snapshot storage/configuration is retained.
- Monitoring values remain manipulable and may return zero; no caller should
  treat them as liquidation, borrowing, collateral, or accounting authority.
- Measured deployed runtime: 14,028 bytes.

### Representative validation

- `test_protocol_feed_stays_disabled_while_monitoring_starts_after_first_snapshot`
- `test_repeated_manipulated_snapshots_can_suppress_monitoring_value`
- reserve, decimal, stale-snapshot, timelock, malformed-response, and pause
  coverage in `tests/priceSources/uniswap/test_minimal_prices.py`

## 10. `RipeGov.vy`

### What changed

#### A. Contributor lock duration is constrained

The HumanResources contributor transfer duration is clamped to the current
governance-configured minimum and maximum. If the recipient already has a later
lock after normal terms refresh, the transfer cannot shorten it.

#### B. Migration export accrues without rewriting stored terms

`_updateGovPointsForUserAsset` now takes an internal refresh flag. Normal point
updates still refresh to current MissionControl terms. Migration export uses
the stored `lastTerms` to accrue through the current block and deliberately
does not replace `unlock` or `lastTerms` with the temporary wind-down config.

#### C. Public point refresh is closed while the vault is paused

`updateUserGovPoints` now rejects calls while paused. This prevents an unrelated
registered protocol caller from rewriting imported or not-yet-exported lock
metadata during the migration window.

### Why these changes are required

HumanResources is privileged to move contributor RIPE, but the supplied lock
duration should not bypass the same current min/max policy imposed on normal
governance deposits or shorten a recipient's stronger existing lock.

For migration, the administrator intentionally lowers minimum lock terms to
make the legacy withdrawal possible. If export first refreshed the stored row
to those temporary terms, the target would preserve the wind-down terms rather
than the user's original terms—the opposite of the migration objective.

### Interface, storage, and risk impact

- No public selector is removed or added by these changes.
- No persistent storage variable is added.
- Governance-point disable setters remain Switchboard-only; VaultMigrator has
  no authority to apply them.
- Paused migration state becomes intentionally more restrictive.
- Measured deployed runtime: 23,667 bytes, leaving 909 bytes of EIP-170
  headroom.

### Representative validation

- `test_contributor_transfer_cannot_shorten_existing_lock`
- contributor min/max clamp and existing-lock coverage in
  `tests/vaults/test_ripe_gov_controls_and_migration.py`
- exporter term preservation and source-disable non-carryover tests
- paused/unpaused point and lock mutation matrix

## 11. `StabVault.vy`

`StabVault` is the shared module compiled into StabilityPool. These changes are
the largest accounting portion of the smart-contract remediation.

### What changed

#### A. All claim liabilities are reserved from Stability-asset backing

`_getUnreservedBalance` reads custody, requires custody to cover the asset's
aggregate claim liability, and returns only `custody - reserved`. NAV,
withdrawal, and liquidation-spend calculations now use this unreserved amount.

The aggregate `totalClaimableBalances` value is used because one token can be a
claim liability owed to multiple Stability-asset cohorts. A pair-local
subtraction would still let one cohort spend another cohort's reserve.

#### B. An asset cannot be both Stability backing and a claim liability

- Depositing a Stability asset is rejected while that token has any claim
  liability.
- Adding a claim liability is rejected if the token is already a supported
  Stability asset.

This prevents the same custody from being classified and valued in two roles.

#### C. Active claim valuation fails closed

Every active, nonzero claim included in NAV must have:

- aggregate custody covering aggregate liability; and
- a nonzero, nonreverting current price.

If either is unavailable, deposits, withdrawals, and other NAV-dependent value
movement revert instead of silently omitting the claim and redistributing its
future value to a different share cohort.

#### D. User-facing outbound transfers must be exact

Direct Stability-asset withdrawals and direct (non-auto-deposit) claim payouts
measure the recipient balance delta and require it to equal the nominal amount.
A fee-on-transfer token therefore cannot burn the user's full shares or claim
liability while delivering less than the accounting amount.

#### E. Liquidation spending cannot consume claim reserves

`swapForLiquidatedCollateral` caps the spendable Stability asset at the
unreserved balance rather than raw custody.

#### F. Single claim calls share the batch implementation

The single-claim wrapper constructs one row and routes through the shared batch
internal function. This preserves the external selectors while reclaiming code
space for the accounting checks.

### Why these changes are required

The prior implementation could treat an unpriced active claim as zero in NAV.
Users could deposit or fully exit during the outage, transferring the claim's
eventual restored value between cohorts or abandoning it after the last shares
left.

It also valued claims without globally proving custody and used raw custody as
spendable Stability backing. A claim token that was also admitted as a
Stability asset could be counted twice. Finally, an ERC-20 returning success
while charging an outbound fee could reduce internal liability/shares by the
full nominal amount although the user received less.

### Dormant sub-threshold claims: approved workflow

Claims below the activation threshold remain dormant rather than entering the
active NAV iteration. They are still reserved from raw custody by
`totalClaimableBalances`, but they are not automatically redistributed after a
cohort's final shares exit.

The approved operational rule is to claim dormant residuals before the final
share exit. PR #95 deliberately does not add a governance recovery/redistribution
ABI because that would require a separate ownership and economic policy.

### Important remaining token-admission constraint

The exact recipient-delta helper covers user withdrawals and direct claim
payouts. The non-GREEN Stability-asset transfer to Endaoment during
`swapForLiquidatedCollateral` still uses the token's normal `transfer` result.
Operational admission must therefore continue to require exact-transfer tokens
for that path. PR #95 does not claim general fee-on-transfer token support.

### Interface, storage, and risk impact

- Existing single and batch claim selectors are preserved.
- No new persistent storage variable is added; the new logic uses existing
  aggregate claim-liability mappings.
- Missing price or custody becomes a temporary fail-closed availability event
  rather than a value redistribution event. Normal operations resume after the
  price/custody is restored.
- Measured deployed StabilityPool runtime: 24,313 bytes, leaving 263 bytes of
  EIP-170 headroom.

### Representative validation

- `test_active_claim_custody_deficit_fails_closed_for_value_extracting_actions`
- `test_claim_reserve_cannot_be_reclassified_as_stability_backing`
- `test_outbound_fee_on_transfer_short_delivery_reverts_atomically`
- `test_outbound_fee_on_transfer_stability_asset_does_not_burn_shares`
- `test_unavailable_claim_price_blocks_deposits_and_withdrawals`
- `test_withdrawal_during_zero_price_outage_reverts_without_abandoning_claims`
- price/custody restoration, dormant dust, exact settlement, active-claim cap,
  and EIP-170/gas-bound coverage in
  `tests/vaults/modules/test_stab_vault_hardening.py`

## 12. `RipeCcipBurnMintTokenPools.sol`

### What changed

Only comments and provenance claims changed. The GREEN and RIPE capability
functions and constructor code are unchanged.

The revised comments now state accurately that:

- token-specific bytecode prevents GREEN/RIPE capability **flags** from being
  passed in the wrong order;
- the inherited constructor still accepts a token address, so deployment
  tooling must bind and revalidate `getToken()`;
- this file is the repository candidate/reference implementation using the
  vendored `BurnMintTokenPool 1.5.1`;
- observed live topology, runtime hash, capabilities, and type/version do not
  by themselves prove that already-live pools were created from this exact
  source/compiler/settings/constructor artifact.

### Why this is required

The old comments made two stronger claims than the evidence supported: that a
pool could not be deployed for the wrong token, and that the live pools were
built from this source. The first ignored the inherited token constructor
argument. The second conflated runtime/topology observations with creation
provenance.

This clarification is security relevant because operators and reviewers use
source comments to decide which checks can be omitted. The corrected text keeps
token binding and creation provenance as explicit gates.

### Interface, storage, and runtime impact

- No executable Solidity statement, ABI, or storage layout changed.
- Solidity metadata may change when comments/source hashes change, so this
  repository candidate must still be rebuilt and identified from the final
  source. That is not evidence about already-live creation provenance.

### Representative validation

Foundry tests prove the candidate's compiled capability answers, token binding,
inherited owner controls, and pinned `BurnMintTokenPool 1.5.1` type/version.
They do not claim to prove historical live deployment provenance.

## 13. `RipeTokenPool.sol`

### What changed

Only the contract-level documentation changed. Executable code, constructor
arguments, immutable capability flags, ABI, and storage are unchanged.

The comments now classify this configurable-capability pool as legacy/testnet
migration history. The token-specific
`RipeCcipBurnMintTokenPools.sol` implementation is the current repository
candidate for mainnet use, while neither source file is represented as proof of
the already-live pools' creation artifact.

### Why this is required

Keeping two pool implementations without an explicit status distinction makes
it easy for a future migration or reviewer to select the wrong architecture.
The configurable version can accept contradictory capability flags at
construction; the token-specific candidate removes that particular flag-order
risk. Historical/testnet scripts can still refer to the legacy contract, but
the repository no longer presents both as interchangeable mainnet choices.

### Interface, storage, and runtime impact

- No executable behavior changed.
- As with the other Solidity source, source-metadata identity can change even
  when executable statements do not.

## ABI and storage summary

The remediation intentionally avoids broad ABI/storage churn:

- Uniswap adds `getMonitoringPrice` and changes the standard PriceSource views
  to report no protocol feed.
- AuctionHouse and StabVault retain their single-item public wrappers by
  routing them through shared batch internals.
- RipeGov, VaultMigrator, Teller, Alpha, Bravo, and Charlie add no new public
  remediation selectors.
- The Solidity changes are comments only.
- No changed Vyper contract adds a persistent storage variable in this
  remediation. Existing mappings and transient liquidation bookkeeping are
  reused.

The checked-in ABI export and the governed artifact ledger are generated from
the final integrated source. The artifact ledger binds the full deployed
runtime, including immutable data, for the governed contract set.

## What these contract changes deliberately do not claim

1. **Uniswap monitoring is not manipulation resistant.** The contract boundary
   prevents protocol price authority; it does not make reserve observations
   safe for collateral.
2. **Migration is not permissionless.** It is an administrator-run, paused,
   preflighted batch process with atomic rollback.
3. **A migration target is not a merge destination for arbitrary prior user
   history.** Target eligibility/virginity remains a precondition.
4. **StabilityPool does not support arbitrary ERC-20 transfer semantics.** Exact
   user deliveries are enforced, while admission policy must still exclude
   problematic tokens on paths without a recipient-delta measurement.
5. **Repository CCIP source is not historical creation proof.** Exact live
   source/compiler/constructor provenance remains an explicit unresolved gate.
6. **No contract change authorizes a live action.** Deployment migrations,
   Safe calldata, rate-limit policy, signer binding, destination-gas evidence,
   receiver-control evidence, and merge approval are separate decisions.

## Reviewer-oriented conclusion

The contract changes are not one undifferentiated rewrite. They fall into five
specific groups:

1. preserve RipeGov lock/point semantics during controlled migration;
2. make Stability Pool claims, custody, and liquidations value-conserving and
   retry-safe;
3. reject incompatible runtime implementations before governance activates
   them;
4. enforce the owner-approved monitoring-only boundary for Uniswap V2;
5. reconcile live CCIP identity/provenance claims without pretending repository
   source proves historical deployment origin.

The most behaviorally significant files are `RipeGov.vy`,
`VaultMigrator.vy`, `StabVault.vy`, and `AuctionHouse.vy`. The Switchboard
changes are the configuration-side enforcement required to make those runtime
assumptions safe. `Teller.vy` closes a composition/reentrancy edge. `Addys.vy`
corrects a live registry fact. The two Solidity files only correct explanatory
claims and do not change their executable statements.
