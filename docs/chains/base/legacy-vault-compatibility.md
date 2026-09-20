# Base legacy-vault compatibility release notes

This change lets new departments read retained Stability Pool 1 through VaultBook while preserving direct, authorized settlement calls. Retained RipeGov 2 remains usable through the new Teller, Lootbox and HumanResources. Ordinary tests compile both retained vaults from their authenticated historical sources; their provenance is recorded in `tests/fixtures/legacy_pool/provenance.json`.

## Shared-source deployment dependency

The updated AuctionHouse, Deleverage, SwitchboardAlpha and SwitchboardCharlie require the active VaultBook to expose `canAcceptLiquidationAsset`, `getDeleverageTraversalAsset` and `hasStabilityPoolInterface`. SwitchboardGolf also requires its public `LEGACY_POOL()` getter when validating a nonzero special stability-pool ID. This applies on **Robinhood as well as Base**, even when every vault uses the modern interface. On modern-only chains, configure the new VaultBook with a zero `_legacyPool` binding and verify the getter and three helper methods before activating updated callers. A zero binding disables legacy dispatch; it does not remove the callers' dependency on the helper ABI. VaultBook explicitly implements `VaultBookCompatibility`, so signature drift fails compilation.

Golf deliberately prohibits retained Pool 1 as a **special** stability pool: that route relies on modern active-claim accounting which the retained pool lacks. Both proposal and execution reject the configuration through normal policy validation before calling the unsupported selector. This restriction does not disable Pool 1's existing priority-pool liquidation route. Current Base configurations with `specialStabPoolId == 0` remain supported.

## Optional traversal and strict settlement

Broad deleverage traversal skips an unusable retained-pool position: it returns `(asset, 0)` if optional NAV or user-value reads revert, return malformed data or yield zero. It also checks the historical maximum-withdrawal calculation and skips virtual-share residues whose executable withdrawal rounds to zero. Paused pools and cohorts with no spendable stabilization-token custody are skipped before valuation. A healthy retained position returns its full, uncapped NAV. The helper's second return value is a token/NAV amount for stability vaults and a `0`/`1` balance-presence sentinel for ordinary vaults.

`Deleverage.getDeleverageInfo` excludes those skipped positions; it is therefore an estimate of usable positions, not an inventory of every recorded share. Broad keeper batches continue to healthy users before or after an unpriceable position. Direct historical Pool-1 NAV, withdrawal, claim and settlement calls remain strict. Explicit owner-selected operations do not gain a general fail-soft settlement path. Tests reset transient storage between composed scenarios, including after an owner repayment at a constant $1.007 quote leaves a one-raw-unit LP residue with zero executable withdrawal.

Liquidation readiness examines only the selected payment path and does not enumerate unrelated claims or certify their prices. A pool can be ready for a liquidation swap while strict NAV-dependent user flows cannot complete. Optional traversal cannot replace oracle qualification.

## Pricing and claim-inventory activation gates

The saved Base readback at block **51,532,106** records eleven non-GREEN claims in the LP cohort. Both active and staged PriceDesk observations record unit prices of **1 USD wei** for VVV (`0xacfe6019ed1a7dc6f7b508c02d1b04ec88cc21bf`, 18 decimals) and mcbETH (`0x3bf93770f2d4a794c3d9ebefbaebae2a8f09a5e5`, 8 decimals). Each has one raw claim unit. Their unrounded dollar values are zero; PriceDesk's positive-price floor gives each a one-USD-wei quote. The evidence establishes those values, not the intent behind setting them.

The committed `DefaultsBaseLive.vy` snapshot at block **51,479,022** does not include mcbETH. Replaying only MissionControl's asset list is insufficient to preserve the LP cohort's pricing dependencies. Before activation, the release owner must verify usable, nonzero quote paths for **all retained claim assets**, including VVV and mcbETH, in the selected PriceDesk. These notes do not prescribe retaining economically incorrect prices. Changing prices or resolving residual claims remains a release decision. No live readback or oracle configuration was performed for this follow-up.

Monitor `max(numClaimableAssets(cohort) - 1, 0)` and enumerate nonzero claim balances for both LP and sGREEN cohorts. Index zero is unused: a getter value of 27 means **26 real claim assets**, beyond the modern pool's active-claim cap of 20. Historical Pool 1 removes depleted claims, so this is an outstanding-inventory cost, not necessarily permanent growth. Each outstanding claim still lengthens the legacy NAV walks, including the optional reads used by traversal.

Local regression measurements with priced mock routes (execution gas, excluding transaction intrinsic gas) are:

| Real claims | VaultBook traversal | Deleverage info | One-user broad batch |
| --- | ---: | ---: | ---: |
| 11 | 524,920 | 578,033 | 1,329,001 |
| 26 | 1,113,700 | 1,166,813 | 2,506,561 |

The corresponding regression ceilings are 660,000 / 730,000 / 1,670,000 and 1,400,000 / 1,500,000 / 3,200,000. These tests supplement the separate readiness-cost test, whose selected-payment-path cost does not grow with unrelated claims. They do not qualify live nested oracle costs. Before activation, rehearse traversal, `getDeleverageInfo` and representative keeper batches against the final candidate set, actual oracle routes and current claim inventory at a pinned Base block. Include larger-inventory and batch-size stress cases; record gas headroom and the supported operational batch size. Requalify after material inventory or oracle-route changes.

## Constructor and post-deployment checks

VaultBook validates Base chain identity, HQ identity and the non-valuing legacy getter shapes. Its constructor probe enforces successful selector calls and decoding and has an explicit `invalid legacy interface` assertion reason. It does not invoke `getTotalAmountForUser` during construction: a zero user still triggers historical cohort valuation, a zero asset fails its ERC20 balance read, and an existing cohort can fail on an unavailable claim price. Tests cover empty, populated, paused and unpriceable cases. The full historical ABI/runtime must be authenticated before choosing the immutable binding; constructor probes alone do not authenticate arbitrary supplied code.

Read back each final candidate, and repeat against the active VaultBook at cutover:

1. `LEGACY_POOL()` equals retained Pool 1, `0x2a157096af6337b2b4bd47de435520572ed5a439`.
2. `getRegId(pool) == 1`, `getAddr(1) == pool`, and `isValidRegId(1)` is true. These three independent storage relationships must all hold.
3. `hasStabilityPoolInterface(pool, probeAsset, probeClaim)` succeeds with an actual cohort asset and the chosen claim probe. The migration uses `vaultAssets(1)` and the zero claim address for non-valuing structural validation.
4. All retained addresses are unchanged at rows 1–5, `numAddrs() == 6`, and rows 6–10 are absent and invalid.
5. Registry delays are restored, temporary governance is relinquished, and the caller/registry candidate addresses match the newly recorded deployment manifest.

## Executable phase-1 staging path

Use [2026091900_StageLegacyVaultCompatibility.py](../../../migrations/base-mainnet/2026091900_StageLegacyVaultCompatibility.py), through the normal runner:

```sh
python -m scripts.migrate --profile base-mainnet --start-timestamp 2026091900 --single
```

This is an operator command for separately authorized staging; it was exercised locally against real contracts, not broadcast. The normal history guard must pass. Historical migrations and deployment records remain frozen; do not resume the old four-argument VaultBook constructors from this source revision.

The step deploys seven candidates under fresh `<Contract>BaseLegacyCompatCandidate20260919` labels: VaultBook, AuctionHouse, Deleverage, SwitchboardAlpha, SwitchboardCharlie, SwitchboardGolf and Switchboard. VaultBook receives the fifth constructor argument binding retained Pool 1. The registry contains only retained rows 1–5. The replacement Switchboard registers the new Alpha, Charlie and Golf and preserves the staged Bravo, Delta, Echo and setup Foxtrot addresses. Deleverage retains all eight staged economic parameters. Both registries relinquish temporary governance and restore their delays. Post-deployment checks enforce the public binding, independent registry identities, helper ABI and deployed-runtime limits, and verify that active HQ pointers and the pending HQ slot-8 proposal did not change.

The standard migration journal records candidate addresses and constructor inputs under `migration_history/base-mainnet/v1/2026091900-pending-manifest.json` while incomplete and `2026091900-manifest.json` on completion. While incomplete, preserve the accompanying `2026091900-log.json` for authenticated resume; the runner removes the temporary journal and pending manifest after successful completion. Do not overwrite canonical labels or bypass the runner guard.

All five earlier compatibility-sensitive candidates are **superseded**: **VaultBook, AuctionHouse, Deleverage, SwitchboardAlpha and SwitchboardCharlie** with the `BaseUpgradeCandidate20260914` suffix, including `VaultBookPopulatedBaseUpgradeCandidate20260914`. The new Golf restriction also supersedes the staged **SwitchboardGolf**, and the new controller addresses require replacing **SwitchboardPopulatedBaseUpgradeCandidate20260914** (the empty Stage-1 Switchboard is not a final registry either). Existing staging and Safe material cannot be used as the final compatibility candidate set. Rebuild and review cutover proposals from the fresh manifest; no activation batch is authorized by this change.

The recorded Base material identifies an older pending HQ slot-8 VaultBook proposal and includes an unexecuted [cancellation batch](cancel-pending-vaultbook.safe.json). Before activation, governance must re-read `pendingAddrUpdate(8)` and resolve any conflicting proposal rather than confirm the old candidate. Its current live status was not refreshed here; cancellation or replacement remains an owner decision.

## Rehearsal and Contributor boundaries

`scripts/base_full_update_fork.py` appends retained Pool 1 to the historical VaultBook constructor calls through its local deployment adapter. That existing full-update diagnostic still populates **rows 1–10**: retained vaults at 1–5 and future vaults at 6–10 (`numAddrs() == 11`). It is not a phase-1 cutover qualification. The new production step enforces retained-only **rows 1–5** (`numAddrs() == 6`); the final phase-1 fork rehearsal must use that exact topology and candidate set.

The `current_contributor_legacy_gov_env` fixture exercises a newly deployed blueprint compiled from the **current Contributor source** against authenticated historical RipeGov. It covers contributor transfer, cancellation/burn, authorization failures and paused-Ledger rollback. It does **not** authenticate or exercise already-deployed historical Contributor bytecode. Staging retains those deployed contributor contracts. Before relying on them at release, the release owner must inventory and authenticate their runtime/source versions and qualify the relevant flows against those versions and the final departments. This section tracks that release gate; the local current-blueprint tests are not evidence that it is closed.

## Deferred shared rounding correction

The modern StabilityPool shares the underlying virtual-share rounding mismatch. Changing its accounting or direct settlement is outside this retained-Pool-1 compatibility correction and would require separate economic and migration review. This section tracks a follow-up to reproduce the same partial-repayment residue on the modern pool, choose an accounting/dust policy, and test withdrawals, share conservation and keeper composition before changing that source. This PR contains the required retained-pool batch protection and leaves modern direct settlement unchanged.

## Merge coordination and regression placement

This PR is stacked on [PR #231](https://github.com/Ripe-Foundation/ripe-protocol/pull/231) and merges into it or after it. Preserve the verified **18,278-byte** Foxtrot pin and **60-output** ABI count, with `SwitchboardFoxtrotSetup.json` as the added named ABI anchor. The reserve-activation validator now audits both Foxtrot source variants while retaining seven registered controller roles. Preserve that distinction if #231 changes the inventory independently. Remeasure or recount if combined sources change.

The composed compatibility tests live in the existing AuctionHouse CI shard; registry tests remain in `tests/registries/test_vault_book_legacy_compat.py`. The shard-coverage check guards that placement; the manifest-consumer census separately checks recorded deployment consumers. The stacked PR base does not trigger the master/rh pull-request workflow automatically; dispatch `python-tests.yml` with `lane=lean` on the final branch head and attach all job results before re-review.
