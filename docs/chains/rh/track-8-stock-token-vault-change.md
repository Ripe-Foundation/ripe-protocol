# Track 8: Shared Stock Token Vault-Change Specification

**Status:** Draft for owner review; specification-only

**Prepared:** 23 July 2026

**Planning baseline:** `68a76dcd5ea9b95b9148d3e6ebdd12107d5cc88e`

## Fresh-agent instruction

Treat this document as the task contract. Convert the integrated Track 5 vault evidence and fix recommendations into an implementation-ready, chain-portable specification and validation plan for safely supporting issuer-controlled ERC-20 collateral.

This track is documentation-only. Do not modify production contracts, interfaces, tests, mocks, defaults, parameter reports, migrations, manifests, ABI exports, dependencies, CI, or `docs/chains/rh-summary.md`. Do not select a production vault, accept a loss-allocation policy, authorize a Base upgrade, or implement a containment patch.

Use branch `rh-track-8-stock-token-vault-change`. Commit only the owner-approved specification deliverables to that branch with clear messages. Never push directly to or merge into `rh` or `master`; the owner reviews and integrates the work.

## Worktree bootstrap

The owner must first commit this approved brief to `rh`. The fresh agent is responsible for creating its own worktree:

1. Start from `/Users/wigglez/dev/ripe-protocol`.
2. Verify that:
   - the integration worktree is clean;
   - `rh` resolves to the approved integration commit;
   - this brief exists in that commit; and
   - the integrated Track 2, Track 3, and Track 5 artifacts listed below exist in that commit.
3. Record:
   - the full starting commit;
   - the commits and SHA-256 hashes for the Track 5 comparison, decision, fix-recommendation, mock, and test files;
   - the current component-matrix hash; and
   - the latest integrated versions of relevant vault, Teller, CreditEngine, AuctionHouse, Deleverage, Lootbox, MissionControl, and interface sources.
4. Confirm that branch `rh-track-8-stock-token-vault-change` and path `/Users/wigglez/dev/ripe-protocol-track-8-stock-token-vault-change` do not already exist. If either exists, stop and ask the owner; do not reuse, delete, reset, or overwrite it.
5. Create the isolated worktree:

   ```bash
   git -C /Users/wigglez/dev/ripe-protocol worktree add \
     -b rh-track-8-stock-token-vault-change \
     /Users/wigglez/dev/ripe-protocol-track-8-stock-token-vault-change \
     rh
   ```

6. Verify the new worktree's branch, commit, clean status, and recorded hashes.
7. Run every subsequent command and make every edit inside `/Users/wigglez/dev/ripe-protocol-track-8-stock-token-vault-change`.

Do not modify or commit from the integration worktree. Leave the Track 8 branch and worktree in place for owner review; do not remove or merge them yourself.

## Hard evidence precondition

The integration baseline must contain:

- `docs/chains/rh/stock-token-vault-comparison.md`;
- `docs/chains/rh/stock-token-vault-decision.md`;
- `docs/chains/rh/stock-token-vault-fix-recommendations.md`;
- `contracts/mock/MockStockTokenControls.vy`;
- `tests/vaults/test_stock_token_vault_comparison.py`;
- `docs/chains/rh/stock-token-transferability-evidence.md`;
- `docs/chains/rh/component-matrix.md`; and
- `docs/chains/rh/block-number-inventory.md`.

The Track 5 decision must still be:

```text
conditional — shared vault change specification required
```

If a later integrated decision has already approved a production vault or materially changed the Track 5 conclusion, stop and reconcile this brief before creating a competing specification.

Do not use a floating Track 2, Track 5, Track 6, or Track 7 worktree as authoritative evidence. Integrated `rh` files control. Parallel S1, S2, and Track 7 results may be recorded as `pending` and reconciled after owner review.

## Objective

Produce:

1. `docs/chains/rh/stock-token-vault-change-specification.md`; and
2. `docs/chains/rh/stock-token-vault-change-validation-plan.md`.

Together, the documents must:

- formalize custody, accounting, borrowing, settlement, liquidation, and bad-debt invariants;
- specify actual per-call deposit measurement for every affected shared vault path;
- compare the minimum shared containment release with the corrected share-based permanent path and the `do not list` outcome;
- define partial-loss, total-loss, post-zero, recovery, donation, and rounding behavior without silently choosing user property allocation;
- prevent positive borrowing value and paid settlement for undeliverable collateral;
- define an explicit per-asset collateral-use safety control and its governance semantics;
- preserve atomic GREEN payment and debt reduction;
- define total-loss progress into the existing bad-debt accounting exactly once;
- define rewards, events, getters, and monitoring units for nominal amounts, raw shares, live claims, live custody, and deficits;
- identify every shared contract, interface, ABI, default, migration, and live Base deployment implication;
- produce a complete adversarial test and exact-token fork plan;
- split implementation into reviewable changes while preserving atomic release requirements; and
- leave every owner, risk, security, loss-allocation, and live-version decision explicit.

The output must be detailed enough that implementation agents do not rediscover Track 5 behavior or make custody-policy decisions while editing code.

## Controlling constraints

- Follow [`../rh-summary.md`](../rh-summary.md), especially Section 4 and the one-canonical-source rule.
- Treat the integrated Track 5 comparison, decision, and fix recommendations as the controlling behavioral evidence.
- Track 5 supersedes the executive summary's earlier interim acceptance of passive phantom overstatement because it proved an active zero-backed settlement that charges GREEN and reduces borrower debt.
- Neither `SimpleErc20` nor `RebaseErc20`/`SharesVault` is approved unchanged for Stock Token collateral.
- `RebaseErc20`/`SharesVault` is the preferred accounting direction, not an owner-approved production selection.
- Keep Stock Token deposits, borrowing, and auction purchases disabled until the selected shared behavior, exact-token tests, live transferability gate, migration, and owner approvals close.
- Keep `AssetConfig.canRedeemCollateral = false` for Stock Tokens.
- Keep `shouldSwapInStabPools = false` unless governance separately accepts Stability Pool custody of issuer-controlled assets.
- Do not route Stock Tokens through Base treasury, Endaoment partner liquidity, Curve, Aerodrome, Underscore, yield, or unsupported integrations.
- Preserve one canonical Base/Robinhood/future-EVM source. Do not create a Robinhood-only vault, Stock-Token-specific vault implementation, or `chain.id` branch.
- Express issuer-controlled treatment through generic backing invariants and reviewed per-asset configuration, not token-name or chain checks.
- Do not assume monitoring is an onchain fix. Borrowing and settlement must fail closed without operator intervention.
- Do not treat atomic transfer failure as complete debt-resolution behavior.
- Recommendations are not approvals. The owner must approve the architecture, loss allocation, migration, and release grouping before production implementation.

The controlling Hightop Notes source is:

`/Users/wigglez/dev/hightop-notes/random/hood/hood-chain-executive-summary.md`

If the local checkout is unavailable, use the [GitHub copy](https://github.com/mickhagen/hightop-notes/blob/main/random/hood/hood-chain-executive-summary.md). If neither source is accessible, stop rather than silently skipping the selected architecture. Do not import the superseded federated design from `random/hood/hood-chain.md`.

## Required repository reading

Read and verify the current integrated versions of:

### Evidence and program documents

- `docs/chains/rh-summary.md`
- `docs/chains/rh/component-matrix.md`
- `docs/chains/rh/block-number-inventory.md`
- `docs/chains/rh/stock-token-transferability-evidence.md`
- `docs/chains/rh/stock-token-vault-comparison.md`
- `docs/chains/rh/stock-token-vault-decision.md`
- `docs/chains/rh/stock-token-vault-fix-recommendations.md`
- `docs/chains/rh/shared-block-clock-specification.md`
- `docs/chains/rh/block-clock-validation-plan.md`
- `docs/chains/rh/track-2-stock-token-transferability.md`
- `docs/chains/rh/track-5-stock-token-vault-comparison.md`
- the approved S1, S2, and Track 7 briefs; and
- any integrated S1, S2, or Track 7 output available at kickoff.

### Vault and protocol sources

- `contracts/vaults/SimpleErc20.vy`
- `contracts/vaults/RebaseErc20.vy`
- `contracts/vaults/modules/BasicVault.vy`
- `contracts/vaults/modules/SharesVault.vy`
- `contracts/vaults/modules/StabVault.vy`
- `contracts/vaults/modules/VaultData.vy`
- `contracts/vaults/StabilityPool.vy`
- `contracts/vaults/RipeGov.vy`
- `interfaces/Vault.vyi`
- `interfaces/ConfigStructs.vyi`
- `contracts/core/Teller.vy`
- `contracts/core/TellerUtils.vy`
- `contracts/core/CreditEngine.vy`
- `contracts/core/AuctionHouse.vy`
- `contracts/core/AuctionHouseNFT.vy`
- `contracts/core/Deleverage.vy`
- `contracts/core/Lootbox.vy`
- `contracts/core/CreditRedeem.vy`
- `contracts/data/Ledger.vy`
- `contracts/data/MissionControl.vy`
- `contracts/registries/VaultBook.vy`
- `contracts/registries/RipeHq.vy`
- `contracts/config/SwitchboardAlpha.vy`
- `contracts/config/SwitchboardBravo.vy`
- `contracts/config/SwitchboardCharlie.vy`
- `contracts/config/SwitchboardDelta.vy`
- `contracts/config/DefaultsBase.vy`; and
- relevant interfaces used by those sources.

### Tests, mocks, deployment, and generated surfaces

- `contracts/mock/MockStockTokenControls.vy`
- `contracts/mock/MockBlacklistErc20.vy`
- `contracts/mock/MockFeeOnTransferErc20.vy`
- `contracts/mock/MockReentrantErc20.vy`
- `contracts/mock/MockErc20.vy`
- `tests/vaults/test_stock_token_vault_comparison.py`
- `tests/vaults/modules/test_basic_vault.py`
- `tests/vaults/modules/test_shares_vault.py`
- `tests/vaults/modules/test_stab_vault.py`
- `tests/vaults/modules/test_vault_data.py`
- `tests/vaults/test_ripe_gov_vault.py`
- relevant Teller, CreditEngine, AuctionHouse, Deleverage, Lootbox, MissionControl, VaultBook, and Switchboard test files;
- `tests/conf_core.py`
- Base migrations and manifests that deploy/register vaults or replace custody-bearing components;
- current vault and component ABI exports;
- defaults/parameter-generation scripts; and
- Track 2's probe script and recorded exact-token fork inputs.

Use repository search to identify every consumer of:

- `getVaultDataOnDeposit`;
- `getUserLootBoxShare`;
- `getUserAssetAndAmountAtIndex`;
- `getTotalAmountForUser`;
- `getTotalAmountForVault`;
- `transferBalanceWithinVault`;
- `withdrawTokensFromVault`;
- raw nominal balances or share supply;
- `canBorrow`;
- `canBuyInAuctionAsset`; and
- debt-health, liquidation-threshold, auction-settlement, and bad-debt state.

Record exact source references from the starting commit. If relevant code changed after Track 5's evidence commit, classify each delta as evidence-preserving, evidence-invalidating, or unrelated before relying on an old test conclusion.

## Phase A: Reconcile evidence and current source

Build an authoritative delta and consumer map.

- [ ] Verify the hashes and commit ledger recorded by Track 5.
- [ ] Re-run or inspect the integrated comparison suite without modifying it, and record the actual collected case count from `PYTHONPATH=. pytest --collect-only -q tests/vaults/test_stock_token_vault_comparison.py` rather than inheriting a point-in-time parametrized count.
- [ ] Confirm the current code still reproduces the critical zero-backed Simple internal-auction settlement.
- [ ] Confirm the current Rebase behavior for partial loss, total loss, old nonzero shares at zero custody, and fresh deposits after zero.
- [ ] Confirm the short-received later-deposit mismeasurement in both paths.
- [ ] Trace exact caller/callee ordering for Teller transfer, vault credit, event emission, limits, housekeeping, and returned amount.
- [ ] Trace both AuctionHouse settlement modes and the point at which GREEN payment and debt reduction become committed.
- [ ] Trace CreditEngine amount collection, zero-amount skipping, weighted debt terms, liquidation eligibility, and bad-debt transitions.
- [ ] Trace Deleverage's applicable external-delivery behavior and its zero-custody dead end.
- [ ] Trace Lootbox raw-share and global live-value inputs.
- [ ] Trace VaultBook live-funds checks, address replacement, deregistration, and recovery constraints.
- [ ] Confirm the current lack of a per-asset collateral-use/borrow-value flag rather than inferring it from LTV.
- [ ] Quantify current Base exposure: enumerate every asset presently registered to a live Base `SimpleErc20`-path vault using committed manifests plus dated read-only onchain verification, then assess whether each token can reduce in-vault custody without matching Ripe accounting through administrative burn/confiscation, negative rebase, fee-on-transfer or short receipt, upgradeable behavior, or another control. Distinguish verified live facts from repository defaults and unknowns, and state whether Release 1 is an urgent live Base hardening requirement or only a Robinhood-listing prerequisite.

Do not expand Track 5's claim beyond what its test or source evidence proves. Distinguish tested, source-traced, derived, and pending claims.

## Phase B: Define the formal state and invariant model

The specification must define, for each `(vault, asset)`:

- actual ERC-20 live custody;
- requested transfer amount;
- actual per-call received amount;
- aggregate accounted amount;
- raw nominal user balance;
- raw share supply and user shares;
- live converted user claim;
- borrowing amount exposed to CreditEngine;
- current safely deliverable amount;
- deficit amount and deficit status;
- pause/blocklist/upgrade state when observable;
- debt attributable to users holding the asset;
- active auction claims; and
- protocol bad debt.

At minimum, formalize these invariants:

```text
sum of amounts credited for borrowing <= live custody

GREEN paid for collateral <= value of collateral actually and safely delivered

user claim aggregation and settlement cannot allocate more than live custody

a liability cannot remain both as user debt and Ledger bad debt

failed token delivery cannot commit GREEN payment, debt reduction, buyer claim,
or partial auction settlement
```

Define exact expected behavior in these states:

1. solvent ordinary operation;
2. pre-existing donation;
3. donation between deposits;
4. short-received or fee-on-transfer deposit;
5. partial issuer-controlled custody reduction;
6. aggregate nominal deficit;
7. total live-custody loss with outstanding claims;
8. zero custody with nonzero raw shares;
9. donation or issuer restoration after zero;
10. attempted new deposit after zero;
11. paused transfer;
12. sender, recipient, or operator blocklist;
13. active auction before an issuer action;
14. liquidation initiated after an issuer action;
15. implementation/beacon behavior change; and
16. recovery or migration with live users and debt.

Separate safety, liveness, allocation policy, and operator response. A revert can preserve funds while leaving unresolved debt; label both facts.

## Phase C: Compare architecture outcomes

The working specification must compare at least:

### Outcome 1: Do not list Stock Tokens

- no custody-source change;
- no Stock Token deposits, borrowing, or auctions;
- existing shared-vault defects remain a separate Base hardening concern; and
- Robinhood launch proceeds without Stock Token collateral only if the owner accepts the product-scope change.

### Outcome 2: Minimum shared containment release

Evaluate the Track 5 Release 1 proposal as one atomic deployable safety release:

- actual per-call received deposit delta;
- fail-closed Simple borrowing value during aggregate deficit;
- explicit deficit signal carried into debt health;
- no zero-threshold false-health or non-liquidatable outcome;
- internal-transfer deficit guard;
- generic per-asset collateral-use safety flag;
- repayment remains available; and
- no manufactured zero-backed auction.

State clearly that changing only the amount view is unsafe if existing debt can disappear from weighted debt terms.

### Outcome 3: Corrected share-based permanent path

Evaluate a shared `RebaseErc20`/`SharesVault` direction with:

- pro-rata live claims after partial loss;
- exact deposit delta;
- live claims, never raw shares, used for credit and settlement;
- explicit total-loss debt resolution;
- post-zero deposit freeze;
- owner-approved recovery/donation allocation;
- external-only settlement policy for issuer-controlled assets;
- bounded rounding/dust;
- explicit rewards and monitoring units; and
- migration from any existing vault version.

### Outcome 4: Another generic shared design

Only include another design if current interfaces cannot meet the invariants. It must remain generic and chain-portable. Do not propose an issuer-branded or Robinhood-only vault simply because Stock Tokens exposed the defect.

For every outcome record:

- invariant coverage;
- unresolved policy choices;
- contracts/interfaces affected;
- Base behavior and migration;
- custody risk;
- implementation/audit scope;
- rollback reality;
- testing burden;
- operational burden; and
- whether Robinhood Stock Token listing becomes technically eligible.

## Mandatory early owner checkpoint

After Phases A–C, pause and present:

- the evidence/source delta report;
- the formal invariant and state model;
- the architecture comparison;
- rejected shortcuts;
- unresolved owner/security/risk choices; and
- a recommendation.

Do not finalize Phases D–K until the owner decides whether to specify:

1. no Stock Token listing;
2. the containment release only;
3. the corrected share-based permanent path;
4. containment followed by the corrected share path; or
5. another explicitly approved generic design.

The checkpoint must also request direction on:

- whether a per-asset collateral-use flag is approved in principle;
- whether issuer-controlled collateral is always external-settlement-only;
- the total-loss transition into bad debt;
- post-zero freeze versus an explicit recapitalization/allocation procedure;
- treatment of later donations or issuer restoration;
- raw-share reward attribution;
- Base live-version and migration posture; and
- whether Release 1 is a Base hardening requirement even if Robinhood ultimately uses the share path.

If the owner does not approve a production direction, the valid Track 8 conclusion is `do not list Stock Tokens under the current vault designs`. Do not continue by selecting the recommendation yourself.

## Phase D: Specify exact deposit accounting

After the owner checkpoint, define:

- where the before/after balance measurement occurs;
- transfer ordering and reentrancy assumptions;
- how a token upgrade or callback affects the measurement;
- `requested`, `received`, `credited`, and emitted amounts;
- zero receipt, short receipt, fee-on-transfer, negative/rebasing delta, and excess receipt behavior;
- per-user/global deposit-limit accounting;
- price snapshot and housekeeping inputs;
- share minting input and conversion direction;
- event and ABI compatibility;
- rounding and minimum-positive-deposit behavior; and
- how a prior donation is prevented from becoming a later user's receipt.

Compare measuring in Teller versus inside the vault. Select one shared boundary only after tracing every caller and failure mode. The chosen design must not require an asset-name or chain branch.

Disposition every Teller/Vault deposit consumer, including Stability Pool, RipeGov, BasicVault, and SharesVault paths. A fix for Stock Token accounting must not silently change GREEN Stability Pool or RIPE governance-vault deposit semantics.

Tests must prove a later short-received transfer cannot overcredit either the nominal or share path and cannot create an undetected accounted deficit.

## Phase E: Specify backing, collateral-use, and debt-health behavior

Define:

- automatic onchain backing checks;
- the generic per-asset collateral-use flag and its storage/config interface;
- fast disable and stronger re-enable permissions;
- getter/view behavior for previews, maximum borrow, borrow validation, account health, and liquidation;
- explicit deficit propagation even when borrowing value becomes zero;
- treatment of other solvent collateral in the same account;
- behavior for existing debt;
- interaction with LTV and why LTV is not the custody safety switch;
- stale/missing price independence;
- event/getter evidence for monitoring; and
- no double counting of the same live custody across users.

For a nominal path, reject `min(userNominal, liveTotal)` as a multi-user allocation unless the specification mathematically proves aggregate safety. Do not silently pro-rate a nominal ledger without an owner-approved loss-allocation policy.

The specification must prove that:

- a one-unit aggregate deficit cannot support new GREEN debt;
- unrelated solvent collateral retains its correct value;
- a deficit cannot make existing debt appear healthy merely because a zero amount was skipped; and
- the same values drive previews and state-changing validation.

## Phase F: Specify settlement, liquidation, and bad-debt progress

Define a generic asset-level settlement policy.

- Stock Tokens must not allow a buyer-selected internal-settlement override.
- If external delivery is required, the token transfer must succeed before GREEN payment and debt reduction commit.
- Any retained internal settlement for other assets must return no more than demonstrably live-backed, safely allocable collateral.
- Partial-loss settlement cannot allocate the same remaining custody twice.
- Active auctions must define behavior when custody changes after auction creation.
- A new liquidation after total loss must not create a paid auction for missing tokens.
- Transfer pause/blocklist failures must remain atomic and retryable.
- Deleverage must not repay debt beyond delivered collateral.

Define the total-loss transition:

1. how debt with zero or deficit-backed collateral becomes resolution-eligible;
2. how deliverable remaining collateral is exhausted;
3. when no auction is created;
4. how the unrepaid amount leaves user debt;
5. how it enters existing protocol bad-debt accounting exactly once;
6. how duplicate settlement or liability retention is prevented;
7. how repayment remains available before transition; and
8. which governance/emergency controls can pause or resume the process.

Do not invent a new insurer, Stability Pool custody route, or recovery token in this track. If existing accounting cannot express the required transition safely, identify the exact separate shared-contract specification needed.

## Phase G: Specify corrected share-vault behavior

If the owner selects the share direction, define:

- partial-loss pro-rata conversion;
- conversion formulas and round-up/down rules;
- `DECIMAL_OFFSET`, virtual assets/shares, minimum deposit, and dust bounds;
- total live balance zero with nonzero shares;
- post-zero deposit freeze condition;
- old-share treatment;
- donation or issuer-restoration allocation;
- explicit recapitalization, if approved;
- user/asset deregistration and governance recovery;
- reward weight and global value units;
- raw shares versus live claim in events, views, reports, and manifests;
- maximum aggregate withdrawal/settlement amount;
- behavior across 6- and 18-decimal tokens; and
- storage/ABI compatibility.

The default recommendation from Track 5 is to freeze new deposits when `totalShares > 0` and live balance is zero. Any alternative must state who receives restored or newly deposited assets and prove that a new depositor cannot recapitalize or erase old claims unintentionally.

## Phase H: Specify controls, governance, and operational evidence

Map current and proposed controls for:

- global borrowing;
- per-asset collateral use;
- per-asset deposits;
- per-asset auction purchases;
- internal versus external settlement;
- withdrawals;
- repayment;
- liquidation initiation;
- bad-debt transition;
- vault/asset registration;
- vault replacement/migration; and
- emergency disable/re-enable.

For each control specify:

- contract and storage owner;
- caller/role;
- immediate or timelocked action;
- disable versus re-enable asymmetry;
- exact event and getter;
- Base and Robinhood default;
- interaction with repeated/jumping EVM `NUMBER`; and
- failure behavior if the integration or address is absent.

Hosted monitoring and incident staffing are outside this repository track. The specification must still define the onchain getters/events and a repository-side validation/runbook interface needed to observe:

- live custody;
- nominal accounted amount;
- raw shares;
- live claims;
- deficit;
- flags;
- affected users/debt/auctions; and
- the first observed divergence.

Monitoring cannot automatically rewrite balances, infer entitlement from a later donation, or re-enable an asset.

## Phase I: Specify interfaces, storage, artifacts, and migration

Produce a source-impact table covering, where applicable:

- `BasicVault`;
- `SharesVault`;
- `SimpleErc20`;
- `RebaseErc20`;
- `Teller`;
- `CreditEngine`;
- `AuctionHouse`;
- `Deleverage`;
- `Lootbox`;
- `MissionControl`;
- `SwitchboardAlpha`, `SwitchboardBravo`, and `SwitchboardCharlie`;
- `ConfigStructs`;
- `Vault` and other interfaces;
- `VaultBook`;
- defaults and parameter generation;
- ABIs and events;
- Base and Robinhood migrations/manifests; and
- post-deployment verification.

For every proposed change state:

- storage addition/order and upgrade/redeployment consequence;
- function/event/struct compatibility;
- all callers and readers;
- creation/runtime artifact change;
- Base live bytecode implication;
- source status versus live-version status;
- migration prerequisite;
- rollback limitation; and
- security/audit boundary.

Existing funds mean a VaultBook address cannot be replaced casually. Specify:

- old-vault deposit disablement;
- user/asset reconciliation;
- live-funds checks;
- debt and auction handling during migration;
- raw nominal/share cleanup;
- movement or re-registration of custody;
- atomicity and partial-failure behavior;
- old-address retirement;
- new-address permissions; and
- post-migration reconciliation.

Track 7 owns exact Robinhood migration IDs, namespaces, manifests, and deployment tooling. Track 8 defines vault-specific sequencing and requirements but must not improvise migration IDs. Record `pending Track 7` until integrated reservations exist.

## Phase J: Produce the validation plan

`stock-token-vault-change-validation-plan.md` must map every invariant and state to a named future test.

### Required test layers

1. **Math/property:** conservation, rounding, pro-rata loss, dust, and no aggregate over-allocation.
2. **Vault unit:** deposit delta, shares/nominal views, partial/total loss, post-zero state, donations, recovery, and controls.
3. **CreditEngine:** previews, borrow, existing debt, mixed collateral, deficit propagation, liquidation eligibility, and bad debt.
4. **AuctionHouse:** internal/external policy, active-auction loss, partial/total loss, payment/debt atomicity, and two-buyer ordering.
5. **Teller/Deleverage:** transfer ordering, limits, withdrawal, repayment, and actual delivery.
6. **Rewards/monitoring:** raw shares, live claims, global value, points, events, and getter units.
7. **Governance/config:** emergency disable, timelocked re-enable, permissions, defaults, and missing-address failure.
8. **Migration:** live users/funds/debt/auctions, partial failure, reconciliation, old-address retirement, and Base/RH version policy.
9. **Exact-token fork:** the integrated AAPL proxy at a pinned block, including issuer-control surfaces known from Track 2.
10. **Dual-clock/cross-chain regression:** identical artifacts under S1 Base/Robinhood profiles and S2 inventory enforcement once those tracks are integrated.

### Required scenarios

At minimum include:

- 6- and 18-decimal ordinary lifecycle;
- one-base-unit and minimum deposit;
- donation before first deposit;
- donation between deposits;
- later short-received transfer;
- fee-on-transfer;
- partial administrative burn/forced reduction;
- total loss;
- two users and both withdrawal orders;
- two auction buyers and both withdrawal orders;
- active internal and external auction before loss;
- auction initiated after partial and total loss;
- pause;
- vault/sender, recipient, and operator blocklists;
- implementation behavior switch;
- donation/restoration after zero;
- attempted fresh deposit after zero;
- mixed solvent and deficit collateral;
- existing debt at deficit/zero;
- repayment before bad-debt transition;
- exactly-once bad-debt transition;
- failed settlement leaves all relevant state unchanged;
- migration with live funds and debt; and
- unsupported Stock Token features remain disabled.

The integrated Track 5 suite remains regression evidence. New tests should fail against the unsafe current behavior where appropriate and pass only against the approved shared design. Do not delete or rewrite the evidence suite to make a new implementation look safe.

For every future test record:

- proposed file;
- stable component IDs;
- prerequisite owner decision;
- setup and actors;
- token behavior;
- expected state transition;
- clock profile if applicable;
- exact invariant;
- diagnostics;
- runtime tier; and
- reviewer/approver.

## Phase K: Split implementation and release gates

Define small review units, but preserve atomic deployment groups.

At minimum separate:

1. deposit-delta accounting and event/interface behavior;
2. per-asset collateral-use control and governance;
3. deficit detection and CreditEngine debt-health propagation;
4. internal-transfer backing guard and settlement policy;
5. total-loss liquidation and exactly-once bad-debt transition;
6. corrected share-vault post-zero, donation, and rounding behavior;
7. rewards/getters/events/monitoring semantics;
8. Base and Robinhood defaults/configuration;
9. vault migration, registry, manifests, and post-deployment verification; and
10. exact-token fork, dual-clock, lifecycle, and adversarial validation.

For each unit specify:

- exact expected files;
- component IDs;
- dependency and owner decisions;
- whether it is independently deployable;
- storage/ABI/artifact changes;
- targeted tests;
- required S1/S2 gates;
- Base regression;
- audit boundary;
- migration/rollback boundary;
- downstream consumer; and
- stop conditions.

Do not present an individually reviewable PR as independently deployable if safety requires an atomic release. In particular, a fail-closed zero amount, deficit-aware debt health, internal-settlement guard, and existing-debt transition must not be partially activated in a combination that makes debt falsely healthy, non-liquidatable, or chargeable against missing collateral.

Preserve the Track 5 release framing:

- **Release 0:** operations/runbook readiness; no production code or Stock Token enablement.
- **Release 1:** minimum shared containment, only if the owner approves the complete atomic safety group and Base migration.
- **Release 2:** corrected issuer-controlled collateral completion, only after loss-allocation, vault selection, bad-debt, migration, audit, and exact-token gates.

## Required decision register

The specification must include:

| Decision area | Required disposition |
| --- | --- |
| Product outcome | do not list, containment only, corrected share path, or staged containment then share path |
| Custody invariant | live/accounted/claim/borrow/deliverable definitions and fail-closed rule |
| Deposit measurement | measurement boundary, requested/received semantics, zero/short/excess behavior |
| Per-asset collateral use | storage, fast disable, re-enable governance, views/events |
| Nominal deficit policy | zero value, internal-transfer behavior, existing debt |
| Partial loss | pro-rata or other explicit allocation |
| Total loss | liquidation eligibility, no zero-backed auction, bad-debt transition |
| Post-zero state | freeze, recapitalization, restoration, new deposits, old claims |
| Donation allocation | before first deposit, between deposits, after zero |
| Settlement policy | external-only issuer-controlled assets and retained internal backing rule |
| Rounding | share offset, direction, minimum deposit, maximum dust |
| Rewards/monitoring | raw shares versus live claims and global value |
| Emergency controls | global/per-asset actions, disable/re-enable permissions and clocks |
| Vault selection | Simple containment, corrected Rebase, another generic design, or none |
| Base live version | parity, bounded temporary drift/convergence, custody-bearing migration |
| Migration | live users/funds/debt/auctions, registry replacement, rollback reality |
| Exact-token evidence | fork lifecycle, live Track 2 gate, proxy/upgrade behavior |
| Audit/release | atomic release group, reviewer, audit, testnet and smoke gates |

Each row must include options, evidence, recommendation, owner, affected components, prerequisite, needed-before milestone, and status. Recommendations are not approvals.

## Deliverable A: Shared vault-change specification

`docs/chains/rh/stock-token-vault-change-specification.md` must contain:

- starting commit, evidence hashes, and source-delta report;
- formal terms, state machine, and invariants;
- architecture comparison and owner checkpoint record;
- owner-selected or explicitly unselected direction;
- deposit accounting;
- backing/collateral/debt-health behavior;
- settlement/liquidation/bad-debt behavior;
- share-vault behavior if selected;
- controls and governance;
- interface/storage/source-impact table;
- Base/Robinhood live-version and migration implications;
- implementation/release split;
- decision register;
- open blockers; and
- exact `rh-summary.md` handoff.

## Deliverable B: Vault-change validation plan

`docs/chains/rh/stock-token-vault-change-validation-plan.md` must contain:

- invariant-to-test map;
- proposed test paths and fixtures;
- normal, issuer-control, loss, post-zero, and migration matrices;
- property and conservation tests;
- exact-token fork plan;
- S1/S2 integration;
- Base regression and identical-artifact checks;
- atomicity and exactly-once bad-debt assertions;
- diagnostics and evidence requirements;
- test tiers and commands;
- audit/review gates; and
- checklist/launch-gate mapping.

## Cross-track interface

- **Track 2:** consume the exact-token proxy/fork evidence. Live sender/recipient eligibility, acquisition, signing, gas, and broadcast remain owner/counsel gates outside this track.
- **Track 3:** use primary stable IDs `CM-021`, `CM-024`, `CM-025`, `CM-026`, `CM-030`, and `CM-043`. Reconcile known secondary surfaces including `CM-007`–`CM-013`, `CM-033`, `CM-034`, `CM-044`, `CM-045`, and `CM-049` when the proposed design affects defaults, configuration, rewards, Teller, Deleverage, helpers, or Robinhood values. Add every other actually affected component; do not renumber matrix IDs.
- **Track 5:** preserve its comparison suite and evidence classifications. Do not reinterpret “preferred direction” as owner approval.
- **Track 6 S1/S2:** consume the integrated harness and inventory only after review/merge. Until then, specify exact future integration points as `pending`.
- **Track 6 S3:** coordinate any Lootbox reward-unit implications. Track 8 does not own the Lootbox interval-floor change.
- **Track 6 S6:** coordinate `DefaultsRobinhood` and approved asset/default fields; Track 8 owns behavior requirements, not the defaults artifact.
- **Track 7:** consume migration namespace, manifest, verification, and dependency-security decisions. Track 8 supplies vault-specific requirements and does not reserve IDs.
- **Oracle/configuration follow-on:** oracle pause, feed staleness, market gaps, and final risk parameters remain separate from custody accounting, except where a price failure must be proven independent of backing controls.

If another track proposes the same interface, config field, test file, migration, or ABI change, record the collision and route integration to the owner. Do not edit another track's branch.

## Approval and safety boundaries

The agent may:

- inspect repository code, tests, history, manifests, and integrated evidence;
- run existing local tests without changing them;
- perform read-only public-source or RPC verification when already authorized by the evidence plan;
- draft the two owned documents;
- recommend architecture, invariants, implementation units, and test cases;
- pause at the mandatory checkpoint for owner direction; and
- commit owner-reviewed documentation to the Track 8 branch.

The agent must obtain fresh owner approval before:

- selecting a production vault or loss-allocation policy;
- continuing beyond the mandatory architecture checkpoint;
- editing production code, interfaces, tests, mocks, defaults, migrations, manifests, ABIs, dependencies, CI, generated files, or `rh-summary.md`;
- adding a dependency or tool;
- accepting a live-version or Base migration policy;
- changing a production flag or role;
- accessing a secret;
- signing or broadcasting a transaction;
- deploying or verifying a live contract;
- contacting Robinhood, an issuer, Chainlink, counsel, or another external party; or
- treating a recommendation as implementation authorization.

## Stop conditions

Stop and report evidence if:

- a required integrated Track 5 artifact is absent or materially superseded;
- current code invalidates a load-bearing Track 5 conclusion;
- an invariant cannot be achieved without a Robinhood-only or issuer-branded production contract;
- the design cannot prevent GREEN payment for undelivered collateral;
- fail-closed valuation makes existing debt falsely healthy or permanently invisible;
- total loss cannot transition without duplicating or losing liability;
- a post-zero design silently transfers value between old and new users;
- deposit measurement cannot distinguish the current call from prior donations;
- aggregate user claims or borrowing value can exceed live custody;
- implementation would require a custody migration without an owner-approved atomicity/rollback analysis;
- another active track owns a required file or decision and no disjoint specification is possible;
- the owner does not select a direction at the mandatory checkpoint; or
- proceeding would require a state-changing external action.

The safe valid outcome is `do not list Stock Tokens under the current vault designs`. Do not weaken an invariant merely to produce an implementation path.

## Validation

Before handoff:

- [ ] Verify every cited existing repository path exists at the starting commit.
- [ ] Label proposed future paths explicitly.
- [ ] Verify Track 5 hashes, evidence ledger, and current-source delta.
- [ ] Trace every common Vault interface consumer and every affected component ID.
- [ ] Confirm every Track 5 unsafe/blocked scenario has a disposition and future test.
- [ ] Confirm every fix recommendation is accepted, rejected, deferred, or returned for owner decision.
- [ ] Confirm the two deliverables agree on states, invariants, interfaces, and release grouping.
- [ ] Confirm no production, interface, test, mock, default, migration, manifest, ABI, dependency, CI, generated, or summary file changed.
- [ ] Confirm recommendations and approvals are visibly distinct.
- [ ] Run existing targeted tests only if the starting environment supports them without dependency changes.
- [ ] Run `git diff --check`.
- [ ] Record commands, results, starting commit, input hashes, source dates, checkpoint outcome, and final commit.

If an existing test fails, reproduce it on the untouched starting commit and separate it from Track 8. Do not change or skip a test in this documentation-only track.

## Completion criteria

Track 8 is complete when:

- both deliverables exist;
- the owner checkpoint is recorded;
- every custody/credit/settlement/bad-debt invariant is explicit;
- the selected direction is implementation-ready or the conclusion is `do not list`;
- every source/interface/storage/event/migration implication is mapped;
- implementation PRs and atomic release groups are clear;
- exact-token, Base, Robinhood, issuer-control, and migration validation are complete as plans;
- unresolved legal, live-probe, owner, security, risk, audit, and deployment gates remain explicit; and
- reviewer and owner approve the documents.

The completion report must state which Section 4 and Phase 0 checklist items are **eligible for owner review**. It must not edit or tick `docs/chains/rh-summary.md`; the owner closes checklist items only after the specification, implementation, validation, and production-behavior approvals they require.
