# Track 5: Stock Token Vault Comparison

**Status:** Draft for owner review

**Prepared:** 23 July 2026

**Planning baseline:** `d6efb34b5c28741fb25b053ea9b10af084fe7e53`

## Fresh-agent instruction

Treat this document as the task contract. Produce a code-grounded and behaviorally tested comparison of the two existing deployable vault paths for Robinhood Stock Token collateral:

1. nominal-balance `SimpleErc20`; and
2. share-based `RebaseErc20`, which initializes and uses the `SharesVault` module.

This track may add focused test-only mocks, tests, and documentation. Do not modify production contracts, defaults, migrations, or `docs/chains/rh-summary.md`. If neither existing vault is acceptable unchanged, stop at a documented `vault change specification required` conclusion rather than implementing custody changes.

Use a dedicated branch or worktree named `rh-track-5-stock-token-vault`. Do not edit files owned by the other Robinhood tracks. Commit deliverables to the track branch with clear messages; never push directly to or merge into the shared `rh` or `master` branch. The owner reviews and integrates the work.

## Worktree bootstrap

The owner must commit this approved brief to the `rh` integration branch before kickoff. The fresh agent is responsible for creating its own worktree:

1. Start from `/Users/wigglez/dev/ripe-protocol`.
2. Verify that the integration worktree is clean, `rh` resolves to the approved integration commit, and this brief exists in that commit.
3. Confirm that branch `rh-track-5-stock-token-vault` and path `/Users/wigglez/dev/ripe-protocol-track-5-stock-token-vault` do not already exist. If either exists, stop and ask the owner; do not reuse, delete, reset, or overwrite it.
4. Create the isolated worktree from the committed `rh` baseline:

   ```bash
   git -C /Users/wigglez/dev/ripe-protocol worktree add \
     -b rh-track-5-stock-token-vault \
     /Users/wigglez/dev/ripe-protocol-track-5-stock-token-vault \
     rh
   ```

5. Verify the new worktree's branch, commit, and clean status. Record the full starting commit in the deliverables.
6. Run every subsequent command and make every edit inside `/Users/wigglez/dev/ripe-protocol-track-5-stock-token-vault`.

Do not modify or commit from the integration worktree. Leave the track worktree and branch in place for owner review; do not remove or merge them yourself.

## Objective

Produce:

1. a reproducible, parametrized behavioral test suite that runs equivalent scenarios against both existing vaults;
2. `docs/chains/rh/stock-token-vault-comparison.md`; and
3. `docs/chains/rh/stock-token-vault-decision.md`.

Together, the work must answer:

- How does each vault measure deposits and represent user and total balances?
- What happens after a donation or an issuer-controlled partial or total custody loss?
- Does borrowing power immediately reflect the remaining live collateral?
- Is loss shared pro rata, or can an early withdrawer receive more than a later withdrawer?
- What happens when the live token balance reaches zero and later receives tokens again?
- How do pause and blocklist controls affect deposits, withdrawals, internal balance transfers, auctions, and deleveraging?
- Can a liquidator pay GREEN for collateral that the vault no longer holds?
- How do rounding, dust, share conversions, reward accounting, and vault registry behavior differ?
- Can either existing implementation be selected unchanged under the accepted-risk posture?

This track does not list a Stock Token, select production risk parameters, or authorize deployment. It creates the behavioral record and explicit owner decision needed before those actions.

## Controlling constraints

- Follow [`../rh-summary.md`](../rh-summary.md) and the selected Hightop Notes architecture.
- Preserve one canonical, chain-portable production contract source.
- Prefer an existing vault unchanged. Do not create a Robinhood-only vault or add `chain.id` branches.
- Compare the deployable `SimpleErc20` and `RebaseErc20` contracts. `SharesVault` is a module used by `RebaseErc20`, not an independently deployable vault choice.
- Do not build issuer-aware reconciliation, frozen claims, special recovery receipts, batch isolation, or session-aware liquidation behavior in this track.
- Treat issuer pause, blocklist, administrative burn, forced-transfer or redemption, and upgrade powers as accepted architecture inputs whose technical consequences must still be made explicit.
- Do not mistake a successful ordinary ERC-20 transfer for proof that vault accounting and liquidation remain safe after an issuer action.
- Keep Stock Token `CreditRedeem` disabled regardless of the selected vault.
- Keep `shouldSwapInStabPools = false` unless a separate owner decision accepts Stability Pool custody of issuer-controlled Stock Tokens.
- Recommendations are not approvals. The owner must select the vault and accept its documented failure behavior.

The controlling Hightop Notes source is:

`/Users/wigglez/dev/hightop-notes/random/hood/hood-chain-executive-summary.md`

If the local checkout is unavailable, use the [GitHub copy](https://github.com/mickhagen/hightop-notes/blob/main/random/hood/hood-chain-executive-summary.md). If neither source is accessible, stop rather than silently skipping the required architecture. Do not import the superseded federated design from `random/hood/hood-chain.md`.

## Required repository reading

Read and verify the current versions of:

- `docs/chains/rh-summary.md`
- `docs/chains/rh/track-2-stock-token-transferability.md`
- `docs/chains/rh/track-3-phase-0-inventory.md`
- `contracts/vaults/SimpleErc20.vy`
- `contracts/vaults/RebaseErc20.vy`
- `contracts/vaults/modules/BasicVault.vy`
- `contracts/vaults/modules/SharesVault.vy`
- `contracts/vaults/modules/VaultData.vy`
- `interfaces/Vault.vyi`
- `contracts/core/Teller.vy`
- `contracts/core/TellerUtils.vy`
- `contracts/core/CreditEngine.vy`
- `contracts/core/AuctionHouse.vy`
- `contracts/core/Deleverage.vy`
- `contracts/core/Lootbox.vy`
- `contracts/core/CreditRedeem.vy`
- `contracts/data/Ledger.vy`
- `contracts/data/MissionControl.vy`
- `contracts/registries/VaultBook.vy`
- `contracts/registries/PriceDesk.vy`
- `contracts/config/SwitchboardAlpha.vy`
- `contracts/config/SwitchboardBravo.vy`
- `contracts/config/SwitchboardCharlie.vy`
- `contracts/config/DefaultsBase.vy`
- `contracts/mock/MockBlacklistErc20.vy`
- `contracts/mock/MockFeeOnTransferErc20.vy`
- `contracts/mock/MockErc20.vy`
- `tests/conf_core.py`
- `tests/vaults/modules/test_basic_vault.py`
- `tests/vaults/modules/test_shares_vault.py`
- `tests/vaults/modules/test_vault_data.py`
- relevant Teller, CreditEngine, AuctionHouse, Deleverage, Lootbox, CreditRedeem, and Switchboard tests; and
- current deployment manifests and defaults-generation scripts that register or select vaults.

Use repository search to find every consumer of the common `Vault` interface and every use of:

- `getVaultDataOnDeposit`;
- `getUserLootBoxShare`;
- `getUserAssetAndAmountAtIndex`;
- `getTotalAmountForUser`;
- `getTotalAmountForVault`;
- `transferBalanceWithinVault`; and
- `withdrawTokensFromVault`.

Record the actual starting commit. If relevant contract code has changed since the planning baseline, document the delta before relying on this brief's code observations.

If Track 3's component matrix is available in the integration baseline, use its stable component IDs for `SimpleErc20`, `RebaseErc20`/`SharesVault`, `VaultBook`, `AuctionHouse`, `CreditEngine`, and `CreditRedeem`. Otherwise, mark those references `pending Track 3` and provide a reconciliation list.

## Phase A: Map the accounting and integration invariants

Create a side-by-side code map before writing new tests.

### Deposit and custody accounting

- [ ] Trace the complete deposit call path from `Teller` transfer through the selected vault's returned deposit amount.
- [ ] Distinguish the requested transfer amount, actual token balance delta, amount credited to the user, stored total balance or shares, and emitted amount.
- [ ] Determine whether each vault measures a per-call balance delta or relies on the requested amount and aggregate post-transfer balance.
- [ ] Trace fee-on-transfer, rebasing, donation-before-deposit, donation-between-deposits, and pre-existing-unaccounted-balance behavior.
- [ ] Explain `SharesVault.DECIMAL_OFFSET`, the virtual `+1` balance, rounding direction, and the intended donation-attack protection.
- [ ] Identify conditions under which a deposit can mint zero, excessive, or unexpectedly diluted shares.

### Loss and solvency accounting

- [ ] Compare each vault's stored user balances, stored total balances or shares, live ERC-20 balance, user-facing amount views, and vault-total views after a partial loss.
- [ ] Trace how `CreditEngine` converts those views into collateral value and borrowing power.
- [ ] Prove or disprove phantom collateral after an administrative burn or forced transfer.
- [ ] Prove or disprove first-withdrawer advantage with at least two users and multiple withdrawal orderings.
- [ ] Trace a total live-balance loss with outstanding nominal balances or shares.
- [ ] Trace what happens when new tokens arrive after the live balance reached zero.
- [ ] Determine whether the asset and user can be deregistered and whether governance recovery functions remain usable in each state.

### Downstream protocol behavior

- [ ] Trace both AuctionHouse settlement modes:
  - an internal `transferBalanceWithinVault`; and
  - an external token withdrawal to the liquidator.
- [ ] Determine whether the amount returned to AuctionHouse always represents economically deliverable collateral.
- [ ] Verify atomicity when the token transfer reverts: the liquidator must not lose GREEN and the borrower debt must not be reduced unless the collateral movement succeeds.
- [ ] Trace Deleverage's withdrawal and internal-transfer paths with live-balance loss.
- [ ] Trace `Lootbox.getUserLootBoxShare` behavior after donations and losses, including the share scaling used by `RebaseErc20`.
- [ ] Trace Teller's price snapshots, minimum-balance checks, global/per-user deposit limits, and housekeeping against each vault's reported values.
- [ ] Identify any monitoring or manifest field whose meaning changes from nominal token amounts to shares.

Record every claim with the exact contract, function, and line or stable source reference from the pinned commit.

## Phase B: Build the comparison harness

Add focused tests under:

`tests/vaults/test_stock_token_vault_comparison.py`

The tests must run equivalent scenarios against both `SimpleErc20` and `RebaseErc20` wherever their interfaces permit. Use named fixtures and scenario tables so behavioral differences are intentional and reviewable rather than duplicated test code.

### Issuer-control mock

The existing `MockBlacklistErc20` does not model the complete Stock Token control surface. Reuse or extend existing mocks where doing so remains clear, or add a dedicated test-only mock under `contracts/mock/` that can model:

- ordinary ERC-20 transfers and `transferFrom`;
- global token pause and resume;
- sender, recipient, and operator blocklisting;
- privileged balance reduction or burn from an arbitrary holder;
- privileged forced transfer or forced redemption from an arbitrary holder; and
- an administrator-controlled behavior change representing a token implementation upgrade.

If the upgrade test uses a behavior-switching mock instead of an actual proxy upgrade, label that limitation precisely. Do not present it as proof of proxy-storage or implementation-compatibility behavior.

Use existing fee-on-transfer and reentrancy mocks where relevant instead of adding duplicate token behaviors.

The existing share-vault test that transfers tokens out while impersonating the vault demonstrates live-balance loss, but it is not by itself a faithful test of issuer authority. Add a test that invokes the loss through the issuer-control surface.

### Test levels

Use both:

1. focused vault-level tests for accounting and rounding; and
2. integration tests through the real Teller, CreditEngine, AuctionHouse, Deleverage, Ledger, Lootbox, PriceDesk, MissionControl, and VaultBook paths needed to prove economic consequences.

Do not rely only on direct calls made with a fixture impersonating Teller or AuctionHouse.

No production contract change is authorized. Test-only mocks, fixtures, and comparison tests are within this track's scope.

## Phase C: Execute the behavioral matrix

Run each relevant scenario against both vaults and record the exact observed state transitions.

### Normal and accounting scenarios

- [ ] First deposit and withdrawal.
- [ ] Multiple users depositing before and after one another.
- [ ] Partial and complete withdrawals in both user orderings.
- [ ] Internal balance transfer between users.
- [ ] Exact candidate-token decimals plus at least one contrasting decimal configuration.
- [ ] Tiny amounts, rounding boundaries, and residual dust.
- [ ] Donation before the first deposit.
- [ ] Donation between user deposits.
- [ ] Donation after all current deposits.
- [ ] Requested deposit larger than the amount actually received.
- [ ] Fee-on-transfer or otherwise short-received deposit.
- [ ] Unexpected balance increase without a deposit.
- [ ] Partial live-balance reduction without an ordinary withdrawal.
- [ ] Total live-balance reduction to zero.
- [ ] New deposit or donation after a zero live balance while old balances or shares remain.
- [ ] Final withdrawal, user deregistration, asset deregistration, and permitted recovery behavior.

### Issuer-control scenarios

- [ ] Pause before deposit.
- [ ] Pause before ordinary withdrawal.
- [ ] Pause before liquidation through internal balance transfer.
- [ ] Pause before liquidation through external token transfer.
- [ ] Blocklist the borrower only.
- [ ] Blocklist the vault only.
- [ ] Blocklist the liquidator or withdrawal recipient only.
- [ ] Blocklist the Teller or applicable operator only.
- [ ] Unblock or unpause and retry the failed path.
- [ ] Partially burn the vault's balance.
- [ ] Burn the vault's entire balance.
- [ ] Force-transfer or force-redeem part of the vault's balance.
- [ ] Change token behavior through the approved upgrade test fixture.

For borrower, vault, liquidator, and operator blocklisting, state why a path succeeds or fails. Do not infer the outcome solely from the address label; identify whether that address is the ERC-20 sender, recipient, or operator for the exact call.

### Borrowing and liquidation scenarios

- [ ] Deposit collateral, borrow GREEN, then reduce the live vault balance and recompute debt health.
- [ ] Verify whether new borrowing remains possible against missing collateral.
- [ ] Start an auction before and after the issuer action.
- [ ] Purchase collateral through internal vault-balance transfer after a partial loss.
- [ ] Purchase collateral through external token withdrawal after a partial loss.
- [ ] Repeat both modes after total loss.
- [ ] Verify the GREEN spent, debt repaid, collateral amount returned, internal balance or shares transferred, actual token balance received, and auction state.
- [ ] Reverse the ordering of two liquidators or withdrawers to expose or disprove first-mover advantage.
- [ ] Exercise the relevant Deleverage path after partial and total loss.
- [ ] Confirm that a blocked or paused external transfer reverts atomically.
- [ ] Confirm that an internal balance transfer does not falsely prove the recipient can later withdraw the issuer-controlled token.

Do not add special liquidation recovery behavior. The purpose is to document the current contracts.

### Reward and view scenarios

- [ ] Compare all common Vault interface views before and after donation, partial loss, and total loss.
- [ ] Compare Lootbox deposit-share and reward inputs before and after those changes.
- [ ] Verify event amounts and share fields against resulting state.
- [ ] Record whether frontends or monitoring must distinguish nominal balance, raw shares, live claim amount, and actual vault token balance.

## Required result table

In `stock-token-vault-comparison.md`, include one row per scenario with:

- stable scenario ID;
- setup and actors;
- issuer action;
- expected invariant;
- `SimpleErc20` result;
- `RebaseErc20`/`SharesVault` result;
- actual token balance;
- stored nominal balance or shares;
- user-visible claim;
- borrowing-power effect;
- withdrawal effect;
- internal-liquidation effect;
- external-liquidation effect;
- rounding or dust;
- implementation-conformance result;
- safety-invariant result;
- owner-acceptance status;
- test name and commit;
- evidence notes; and
- owner decision implication.

Do not use `pass` to mean merely that a test reproduced known-dangerous behavior. Separate:

- implementation conformance;
- protocol safety invariant;
- accepted-risk posture; and
- owner approval.

## Phase D: Compare the choices and recommend a decision

Evaluate the existing vaults against:

- phantom collateral and stale borrowing power;
- first-withdrawer advantage;
- pro-rata custody-loss treatment;
- donation allocation and donation-attack resistance;
- deposit measurement and short-received tokens;
- zero-balance recovery;
- rounding and dust;
- pause and blocklist behavior;
- internal and external liquidation integrity;
- deleveraging behavior;
- reward and view consistency;
- registry, defaults, migration, ABI, and monitoring complexity;
- existing production history and test coverage; and
- user and operator comprehensibility.

The recommendation must use one of:

- `select SimpleErc20 unchanged`;
- `select RebaseErc20/SharesVault unchanged`;
- `conditional — additional evidence required`;
- `conditional — shared vault change specification required`;
- `do not list Stock Tokens under the current vault designs`; or
- `blocked — owner or cross-track decision missing`.

Do not recommend a new issuer-aware vault unless the owner explicitly reopens that non-goal. If a shared change to an existing vault is necessary, identify the failing invariants and required follow-on specification without designing or implementing the change here.

## Deliverable A: Comparison and test record

Create:

`docs/chains/rh/stock-token-vault-comparison.md`

It must include:

- repository branch and full starting commit;
- tested contract source hashes or exact pinned paths;
- test environment and commands;
- mock capabilities and limitations;
- Track 2 evidence consumed, if available;
- accounting and integration maps;
- the complete scenario result table;
- reproducible test names and outputs;
- unexplained failures or deviations;
- observed behavior versus accepted behavior; and
- remaining evidence gaps.

## Deliverable B: Vault decision record

Create:

`docs/chains/rh/stock-token-vault-decision.md`

It must include:

- decision status and recommended outcome;
- owner approval status;
- selected deployable contract and module path;
- rejected alternatives and reasons;
- accepted donation, deposit-measurement, burn, forced-transfer, pause, blocklist, zero-balance, withdrawal, liquidation, and upgrade behavior;
- phantom-collateral and first-withdrawer conclusions;
- borrowing-power and debt-health consequences;
- internal-versus-external liquidation consequences;
- reward, view, ABI, event, and monitoring implications;
- exact VaultBook registration and `DefaultsRobinhood` implications;
- required asset configuration, including disabled CreditRedeem and Stability Pool swap posture;
- shared-source and live-version implications;
- required follow-on tests, migrations, manifests, smoke checks, or specifications;
- unresolved Track 2 or Track 3 dependencies;
- explicit launch blockers; and
- exact `rh-summary.md` checklist items eligible for owner review.

The record must say whether the chosen vault is accepted unchanged. Silence is not approval to modify it.

## Cross-track interface

- Track 2 owns canonical Stock Token identity and the live third-party-contract transferability probe. Consume its evidence when available; do not duplicate its live transaction or make legal-eligibility determinations.
- If this track adds a dedicated issuer-control mock, name it `MockStockTokenControls.vy`; record any overlap with a Track 2 mock for consolidation during owner integration rather than duplicating or editing Track 2's work.
- This track may use an exact candidate token on a pinned fork for normal integration behavior after Track 2 identifies it. Fork impersonation is not live-transfer proof and must be labeled accordingly.
- Track 3 owns the component matrix and stable component IDs. This track supplies the tested decision for its deferred vault rows; do not edit Track 3's worktree.
- Track 4 owns USDG and PSM pricing and does not block the vault comparison.
- The later Stock Token oracle/configuration specification owns feed addresses, collateral factors, exposure caps, and production defaults. This track supplies the selected vault ID and behavioral constraints.
- Oracle pause and price-feed failure behavior belong to that later Stock Token oracle/configuration specification, not this vault-comparison track.
- If another track remains pending, continue with test mocks and explicit `pending Track N` fields rather than guessing or blocking all work.

## Approval gates

Stop and obtain owner approval before:

- selecting the production vault as an approved architecture decision;
- accepting a documented custody-loss, first-mover, liquidation, or monitoring risk;
- modifying any production vault or shared protocol contract;
- writing a production vault-change implementation;
- changing defaults, migrations, or asset configuration;
- deploying a contract or broadcasting a transaction;
- using a signing key or moving a live Stock Token; or
- making an external, legal, custody, or commercial commitment.

Repository analysis, test-only mocks, local tests, and fork tests may proceed without separate approval.

## Stop conditions

Stop and involve the owner if:

- neither existing vault satisfies the minimum agreed invariants;
- the comparison reveals that a liquidator can pay for economically nonexistent collateral;
- the selected behavior requires a new issuer-aware custody or recovery design;
- a proposed fix would create Robinhood-only production code;
- exact candidate-token behavior contradicts the mock assumptions materially;
- an issuer action creates an unrecognized mint, custody, debt, governance, or recovery authority boundary;
- a live transaction or legally eligible token holder is required to continue;
- Track 2 evidence contradicts the assumed transfer model; or
- the selected architecture conflicts with current code in a way that materially expands scope.

Otherwise, record the uncertainty and complete every unaffected comparison scenario.

## Validation

- [ ] Every relevant common Vault interface consumer is mapped.
- [ ] Equivalent scenarios run against both deployable vault contracts.
- [ ] Tests distinguish actual token balance, nominal accounting, raw shares, and live user claims.
- [ ] Donations, short-received deposits, partial loss, total loss, and zero-balance recovery are covered.
- [ ] Pause and borrower/vault/liquidator/operator blocklists are covered separately.
- [ ] Both internal-transfer and external-withdrawal liquidation modes are covered.
- [ ] Borrowing power, debt health, GREEN payment, debt repayment, and token receipt are reconciled.
- [ ] Reward and monitoring implications are tested or explicitly bounded.
- [ ] Mock issuer powers and upgrade limitations are documented.
- [ ] No production contract or deployment configuration was changed.
- [ ] Existing relevant tests still pass.
- [ ] File paths, function names, events, fields, and component IDs are verified against the starting commit.
- [ ] Markdown and whitespace checks pass.

## Completion criteria

This track is complete only when:

- the comparison tests are reproducible and reviewable;
- the complete scenario matrix has evidence for both existing vaults;
- normal, issuer-controlled, and liquidation behavior are distinguished;
- the decision record recommends one existing path unchanged or clearly identifies why a separate shared-vault specification is required;
- recommendations, accepted risks, and owner approvals are not conflated;
- Track 2 and Track 3 reconciliation items are explicit;
- no production custody code was changed; and
- the completion report identifies the exact `rh-summary.md` checkboxes eligible for owner review and closure.

Do not mark any checkbox in `rh-summary.md` yourself.
