# Base legacy-vault compatibility release notes

This change lets new departments read retained Stability Pool 1 through VaultBook while preserving direct, authorized settlement calls. Retained RipeGov 2 remains usable through the new Teller, Lootbox and HumanResources. Ordinary tests compile both retained vaults from their authenticated historical sources; their provenance is recorded in `tests/fixtures/legacy_pool/provenance.json`.

## Shared-source deployment dependency

The updated AuctionHouse, Deleverage, SwitchboardAlpha and SwitchboardCharlie require the active VaultBook to expose `canAcceptLiquidationAsset`, `getDeleverageTraversalAsset` and `hasStabilityPoolInterface`. SwitchboardGolf also requires its public `LEGACY_POOL()` getter when validating a nonzero special stability-pool ID. This applies on **Robinhood as well as Base**, even when every vault uses the modern interface. On modern-only chains, configure the new VaultBook with a zero `_legacyPool` binding and verify the getter and three helper methods before activating updated callers. A zero binding disables legacy dispatch; it does not remove the callers' dependency on the helper ABI. VaultBook explicitly implements `VaultBookCompatibility`, so signature drift fails compilation.

Golf deliberately prohibits retained Pool 1 as a **special** stability pool: that route relies on modern active-claim accounting which the retained pool lacks. Both proposal and execution reject the configuration through normal policy validation before calling the unsupported selector. This restriction does not disable Pool 1's existing priority-pool liquidation route. Current Base configurations with `specialStabPoolId == 0` remain supported.

## Optional traversal and strict settlement

Broad deleverage traversal skips an unusable retained-pool position: it returns `(asset, 0)` if optional NAV or user-value reads revert, return malformed data or yield zero. It also checks the historical maximum-withdrawal calculation and skips virtual-share residues whose executable withdrawal or its forward USD value rounds to zero. Each optional getter has an 8,000,000-gas allowance. **Before every optional call**, VaultBook unconditionally requires at least **8,176,985 remaining gas**: the full 8M allowance, the EIP-150 forwarding reserve (rounded up), and 50,000 for Vyper setup, memory expansion and a cold call. An underfunded transaction reverts atomically; it cannot succeed with a gas-starved user omitted. The check precedes even successful returns, including a nested PriceDesk call that would otherwise return zero after an underfunded source failure. Only a call that received the complete allowance may fail soft. Consumed gas is therefore not a sufficient transaction-limit estimate. Gas-exhaustion regressions use a 16M outer budget and prove that the healthy user still repays; callers must budget the whole transaction, including multiple users and reads. Paused pools and cohorts with no spendable stabilization-token custody are skipped before valuation. A healthy retained position returns its full, uncapped NAV. The helper's second return value is a token/NAV amount for stability vaults and a `0`/`1` balance-presence sentinel for ordinary vaults.

`Deleverage.getDeleverageInfo` excludes those skipped positions; it is therefore an estimate of usable positions, not an inventory of every recorded share. Broad keeper batches continue to healthy users before or after an unpriceable position. Direct historical Pool-1 NAV, withdrawal, claim and settlement calls remain strict. Explicit owner-selected operations do not gain a general fail-soft settlement path. Tests reset transient storage between composed scenarios, including owner repayments at $1.007, $0.999 and $0.40 with minimum deposit balance 10**16. The latter two leave a nonzero raw withdrawal with zero forward USD value.

Liquidation readiness examines only the selected payment path and does not enumerate unrelated claims or certify their prices. A pool can be ready for a liquidation swap while strict NAV-dependent user flows cannot complete. Optional traversal cannot replace oracle qualification.

## Pricing and claim-inventory activation gates

The saved Base readback at block **51,532,106** records eleven non-GREEN claims in the LP cohort. Both active and staged PriceDesk observations record unit prices of **1 USD wei** for VVV (`0xacfe6019ed1a7dc6f7b508c02d1b04ec88cc21bf`, 18 decimals) and mcbETH (`0x3bf93770f2d4a794c3d9ebefbaebae2a8f09a5e5`, 8 decimals). Each has one raw claim unit. Their unrounded dollar values are zero; PriceDesk's positive-price floor gives each a one-USD-wei quote. The evidence establishes those values, not the intent behind setting them.

The committed `DefaultsBaseLive.vy` snapshot at block **51,479,022** does not include mcbETH. Replaying only MissionControl's asset list is insufficient to preserve the LP cohort's pricing dependencies. Before activation, the release owner must verify usable, nonzero quote paths for **all retained claim assets**, including VVV and mcbETH, in the selected PriceDesk. These notes do not prescribe retaining economically incorrect prices. Changing prices or resolving residual claims remains a release decision. The pinned fork evidence below reads these routes without changing live configuration. Economic price qualification remains open.

Monitor `max(numClaimableAssets(cohort) - 1, 0)` and enumerate nonzero claim balances for both LP and sGREEN cohorts. Index zero is unused: a getter value of 27 means **26 real claim assets**, beyond the modern pool's active-claim cap of 20. Historical Pool 1 removes depleted claims, so this is an outstanding-inventory cost, not necessarily permanent growth. Each outstanding claim still lengthens the legacy NAV walks, including the optional reads used by traversal.

Local regression measurements with priced mock routes (execution gas, excluding transaction intrinsic gas) are:

| Real claims | VaultBook traversal | Deleverage info | One-user broad batch |
| --- | ---: | ---: | ---: |
| 11 | 525,046 | 578,159 | 1,329,127 |
| 26 | 1,113,826 | 1,166,939 | 2,506,687 |

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

This is an operator command for separately authorized staging. The pinned production-runner rehearsal below uses disposable history and a read-only upstream transport; no transaction was broadcast. The normal history guard must pass. Historical migrations and deployment records remain frozen; do not resume the old four-argument VaultBook constructors from this source revision.

The step deploys seven candidates under fresh `<Contract>BaseLegacyCompatCandidate20260919` labels: VaultBook, AuctionHouse, Deleverage, SwitchboardAlpha, SwitchboardCharlie, SwitchboardGolf and Switchboard. VaultBook receives the fifth constructor argument binding retained Pool 1. The registry contains only retained rows 1–5. The replacement Switchboard registers the new Alpha, Charlie and Golf and preserves the staged Bravo, Delta, Echo and setup Foxtrot addresses. Deleverage reads `minDeleverageBps`, `deleverageBuffer`, `deleverageCooldown` and `underscoreSafeSpreadBps` freshly from active HQ slot 18. It binds the newer full-payoff buffer, overage, dust threshold and dust BPS to `10**15`, `100`, `0`, `0` respectively, then reads back all eight exactly. Before any deployment, each reused Bravo, Delta, Echo and FoxtrotSetup must match its recorded label, authenticated source/ABI/constructor/runtime, Base HQ, action-delay bounds, zero local governance and empty pending governance. FoxtrotSetup must also bind the reviewed MissionControl and Defaults, with `initStep == 1`, `nextAssetIndex == 0`, and `rewardsInitialized == False`, both before and after staging. Zero local governance still permits HQ governance; it is not immutability. Final Switchboard row readbacks independently resolve those manifest labels. Both registries relinquish temporary governance and restore their delays. Post-deployment checks enforce the public binding, independent registry identities, helper ABI and deployed-runtime limits, and reauthenticate all source state after the final transaction: active HQ pointers; active VaultBook forward/reverse/valid rows; inherited Deleverage parameters; reused controllers' runtime, HQ, governance and bounds; Foxtrot binding/progress; every affected HQ pending update/disable; and both candidate registries' pending actions. Any drift fails completion.

The standard migration journal records candidate addresses and constructor inputs under `migration_history/base-mainnet/v1/2026091900-pending-manifest.json` while incomplete and `2026091900-manifest.json` on completion. While incomplete, preserve the accompanying `2026091900-log.json` for authenticated resume; the runner removes the temporary journal and pending manifest after successful completion. Do not overwrite canonical labels or bypass the runner guard.

All five earlier compatibility-sensitive candidates are **superseded**: **VaultBook, AuctionHouse, Deleverage, SwitchboardAlpha and SwitchboardCharlie** with the `BaseUpgradeCandidate20260914` suffix, including `VaultBookPopulatedBaseUpgradeCandidate20260914`. The new Golf restriction also supersedes the staged **SwitchboardGolf**, and the new controller addresses require replacing **SwitchboardPopulatedBaseUpgradeCandidate20260914** (the empty Stage-1 Switchboard is not a final registry either). Existing staging and Safe material cannot be used as the final compatibility candidate set. Rebuild and review cutover proposals from the fresh manifest; no activation batch is authorized by this change.

The recorded Base material identifies an older pending HQ slot-8 VaultBook proposal and includes an unexecuted [cancellation batch](cancel-pending-vaultbook.safe.json). Before activation, governance must re-read `pendingAddrUpdate(8)` and resolve any conflicting proposal rather than confirm the old candidate. The final handoff refreshes that state read-only; cancellation, replacement or confirmation remains an owner decision. A confirmable pending proposal is not approval to execute it. The [read-only finalized refresh](legacy-vault-rehearsal/pending-slot-8.json) at block **51,549,300** still records `0x09f45F56b218756ab092f7470F8199db56849867`, initiated at 49,890,175 and confirmable since **49,911,775**. The active book remains `0xB758e30C14825519b895Fd9928d5d8748A71a944`. Re-read at the actual cutover; this snapshot does not resolve the conflict.

## Rehearsal and Contributor boundaries

`scripts/base_full_update_fork.py` appends retained Pool 1 to the historical VaultBook constructor calls through its local deployment adapter. That existing full-update diagnostic still populates **rows 1–10**: retained vaults at 1–5 and future vaults at 6–10 (`numAddrs() == 11`). It is not a phase-1 cutover qualification. The new production step enforces retained-only **rows 1–5** (`numAddrs() == 6`); the final phase-1 fork rehearsal must use that exact topology and candidate set.

The `current_contributor_legacy_gov_env` fixture exercises a newly deployed blueprint compiled from the **current Contributor source** against authenticated historical RipeGov. It covers contributor transfer, cancellation/burn, authorization failures and paused-Ledger rollback. It does **not** authenticate or exercise already-deployed historical Contributor bytecode. Staging retains those deployed contributor contracts. Before relying on them at release, the release owner must inventory and authenticate their runtime/source versions and qualify the relevant flows against those versions and the final departments. Track this release gate in [historical Contributor qualification #235](https://github.com/Ripe-Foundation/ripe-protocol/issues/235); the local current-blueprint tests are not evidence that it is closed.

## Deferred shared rounding correction

The modern StabilityPool shares the underlying virtual-share rounding mismatch. Changing its accounting or direct settlement is outside this retained-Pool-1 compatibility correction and would require separate economic and migration review. The modern condition has already been reproduced during review. [Accounting follow-up #234](https://github.com/Ripe-Foundation/ripe-protocol/issues/234) requires preserving/reconfirming that reproduction, choosing an accounting/dust policy, and testing withdrawals, asset/share/debt conservation and keeper composition before changing that source. This PR contains the required retained-pool batch protection and leaves modern direct settlement unchanged.

## Repeatable read-only cutover verification

Capture an immutable **pre-stage** baseline using `scripts.capture_legacy_vault_baseline`, independently review its addresses/runtime hashes, active rows, inherited policy and pending-action dispositions, and record its SHA-256 outside the candidate manifest. The committed baseline under `legacy-vault-rehearsal/re-review/` is pinned to block 51,575,411. Capturing a baseline is not approval.

Run the standalone verifier immediately after separately authorized staging and again at the pinned pre-activation block. Pass the **full authenticated current manifest**, not the slim numbered step file, and independently reviewed original stager authority:

```sh
# An archive-capable Base RPC is required for the selected historical block.
BASE_RPC_URL=<archive-capable-read-only-endpoint> python -m scripts.verify_legacy_vault_cutover \
  --manifest <final-current-manifest.json> --stager <original-stager-address> \
  --baseline-manifest <reviewed-pre-stage-baseline.json> \
  --baseline-sha256 <independently-reviewed-sha256> --expected-phase staged \
  --block <pinned-base-block> --output <new-cutover-evidence.json>
```

The command authenticates candidate source/ABI/constructors/runtime against local reviewed source, retained Pool/RipeGov runtime pins, exact HQ and candidate/controller addresses, row-1 forward/reverse/valid identity, all retained rows 1–5, absent/invalid rows 6–10, helper probes, registry delays, zero local and pending governance, and the eight Deleverage values. The `staged` lifecycle requires HQ slots 5/6/8/9/18 to remain at the independently authenticated old addresses and rejects every partial or unrelated activation. It compares actual active rows 1–5, including forward/reverse/valid identity, with the candidate. All pending HQ updates/disables require the reviewed baseline disposition; populated candidate rows must have no pending update/disable. It records block/hash, source commit/tree and per-input hashes, both manifest paths/hashes, runtime sizes/hashes, active and candidate rows separately, Foxtrot state and all pending actions. Same files, resolved aliases and hardlinks are rejected before verification; a candidate manifest cannot redefine canonical retained/reused addresses. Failed checks raise and leave a failure report. The normal mode only reads chain state. For candidates that exist only in a fork, `--replay-staging` replaces `--manifest`/`--stager`: the standalone command independently replays the production runner in a clean disposable fork at the same baseline block, then verifies its output. That mode performs local simulated deployments only. Neither mode has a wallet or broadcast path; the upstream transport rejects write RPC methods. Re-run if the source, manifest, inherited policy, registry state or local governance changes.

## Executable monitoring and keeper integration gate

`scripts.legacy_vault_preflight` implements strict pinned-block diagnostics, a fully reconciled local batch simulation, and read-only receipt reconciliation. Integration remains **open**, owned by **@mickhagen** in [#236](https://github.com/Ripe-Foundation/ripe-protocol/issues/236), pending identification of the production keeper repository/service and its integration PR. The exact hook points are cohort selection (complete indexed inventory), immediately before constructing/submitting `Teller.deleverageManyUsers` (exact ordered batch and funded simulation), and after final receipt before acknowledging completion or advancing the work cursor (every intended user reconciled). Shipping this tool alone does not complete that integration.

The inventory JSON is `{ "complete_at_block": 51575411, "attested_by": "<indexer/review reference>", "users": ["0x..."] }`; it must include every user with nonzero recorded Pool-1 shares. Historical sample censuses do not establish current completeness. Intended JSON is an array of `{ "user": "0x...", "target": 1000000000000000000 }`; optional `minimum_credit` may require a stricter amount. The tool uses an 8M strict read limit, a diagnostic-only 12M retry after exhaustion, and a 12.8M batch execution limit within a 16M submission budget.

```sh
# Archive-capable Base RPC; read-only upstream and disposable simulation only.
BASE_RPC_URL=<archive-capable-RPC> python -m scripts.legacy_vault_preflight \
  --manifest <current-manifest.json> --users-json <complete-users.json> \
  --block <pinned-block> --intended-json <batch.json> --keeper <actual-caller> \
  --output <new-preflight.json>
BASE_RPC_URL=<read-only-RPC> python -m scripts.legacy_vault_preflight \
  --preflight <saved-preflight.json> --receipt-tx-hash <finalized-hash> \
  --output <new-reconciliation.json>
```

Both commands write durable JSON and exit nonzero on failure. Missing, duplicate, unexpected, wrong-emitter, zero-credit or insufficient-credit user events reject completion. A positive 1-wei quote requires review and prevents `keeper_ready`; a whole-cohort failure cannot be hidden by excluding its users from a batch. Enumerate all users with **nonzero recorded Pool-1 shares**, then compare `getDeleverageTraversalAsset` with strict raw getter probes using the same asset and block. A zero result is a classification event, not automatically an incident:

| Classification | Evidence and action |
| --- | --- |
| Expected residue | Both strict getters decode exactly 32 bytes; prices succeed; reproduce the helper's inverse withdrawal and forward USD calculation. Log per-user dust, exclude from repayment targets; no cohort alarm. |
| Paused | `isPaused()` true. Suppress dust/pricing alerts, stop cohort scheduling, retain the existing pause incident/owner state. |
| No spendable custody | Stabilization custody is zero, or GREEN reservations prevent spending. Record balances/reservations and wait for usable custody; no generic getter alarm. |
| Missing/failing price | Enumerate every nonzero claim and stabilization-token route; strict price/value call fails or is zero. Quarantine the whole cohort and page the oracle owner with asset, route, block and error. A positive 1-wei floor is separately flagged for economic review. |
| Malformed getter | Raw response is not exactly one uint256, even if the call reports success. Quarantine the cohort and alert with selector, runtime hash and raw return length. |
| Read gas exhausted/expensive | The 8M probe fails but a bounded diagnostic-only 12M strict probe succeeds, or a successful read exceeds 80% of the allowance. Quarantine/requalify the route and inventory; preserve trace/consumed-gas evidence. Never silently increase the production cap. |
| Other strict-read failure | Strict getters fail after price/shape/gas checks. Quarantine and report the exact failing selector; do not classify an unexplained failure as dust. |

Run one strict valuation probe per funded cohort even if no user currently needs deleverage. A cohort-wide failure or unexpected disappearance of previously executable positions produces **one actionable cohort incident**, listing affected users/shares and failing claim/selector. Intentional per-user dust zeros do not produce repeated incidents. Reset the classification after pause, custody, claim-list or oracle-route changes. Every keeper batch must use current successful strict probes and an exact-batch gas estimate; a stale estimate is not a guarantee if nested routes change before execution. No monitor may alter prices, dust balances, governance or candidate activation.

## Pinned production-runner and gas evidence

The executable rehearsal uses the real `MigrationRunner`, the normal frontier guard and unchanged `Migration.deploy`/`execute` methods. It copies history into a disposable directory and records journal counts, candidate addresses, gas, readbacks, source hashes and the exact source commit. Reproduce with:

```sh
# An archive-capable Base RPC is required for this historical block.
BASE_RPC_URL=<archive-capable-read-only-endpoint> python -m scripts.base_legacy_compat_fork \
  --block 51575411 --baseline-manifest <reviewed-pre-stage-baseline.json> \
  --baseline-sha256 <independently-reviewed-sha256> \
  --output <new-rehearsal.json> --measure-gas
```

The current round requires a clean detached checkout (tracked and untracked), records commit/tree plus per-input hashes, and compares the separately supplied baseline hash before local staging. `--development` explicitly marks dirty debugging output as non-qualification evidence. The standalone verifier can reproduce fork-only staging with `--replay-staging` at the same pin. Current qualification uses **bridge PriceDesk `0xad70893E2F51076b0e9bA18fC593e924593a073F`**, actual Foxtrot Defaults initialization, candidate MissionControl, source ordering and candidate departments. Minimum funded limits are scanned separately from consumed gas, with all intended users reconciled and an actual retained-pool withdrawal traced at every successful point. At block 51,575,411, bridge pricing of `0x99e65176F7FA8743E3fbaEF277d1Da448e361367` exhausts the immutable 1.5M per-source allowance. This rejects the exact historical 26-claim stress inventory and strict collateral valuation for every sampled current mixed holder. [Bridge qualification #237](https://github.com/Ripe-Foundation/ripe-protocol/issues/237), owned by @mickhagen, must close before those cases are supported. Successful strict cohort probes alone do not certify the borrower's other collateral. The runner preserves a complete denial report and exits nonzero when this gas qualification is blocked; `staging_passed` remains a separate result. No source allowance, price or custody override is used to manufacture mixed-holder success. See the current signed-code evidence and resolution handoff in `legacy-vault-rehearsal/re-review/`.

### Historical evidence, superseded for operational capacity

The following results predate the unconditional pre-call reserve. They remain preserved provenance and are **not current supported batch limits**. In particular, the existing 26-claim result still supports no keeper batch within the 16M budget.

The [recorded production-runner report](legacy-vault-rehearsal/review-qualification.json) pins Base block **51,532,106**, hash **`0xfafa2ee560c34e532d9c54c5921fbd14a5be9c213cf380d77040ae762aadee32`**. It records **7 deployments, 35 simulated transactions and 29,959,148 aggregate execution gas**, with all staging and independent verifier checks passing and **zero live transactions**. Candidate addresses, eight Deleverage parameters, registry/controller identities, runtime hashes and transaction journal are included. The saved run was made before committing this review round, so its source commit is the prior `11f854f5…` and its dirty flag is true; its per-input hashes bind the actual implementation tested. Only a trailing blank line in the shared Python verifier helper was removed after that run; contract, interface and migration inputs are unchanged. The final signed-head rerun and input-hash comparison are published in PR #233's validation evidence. Do not mistake the pre-commit report's parent SHA for the final PR head.

Live-fork execution gas (excluding transaction intrinsic gas) is separate from the local mock table above:

| Claim inventory | NAV cold / warm | User value cold / warm | Traversal cold / warm | Deleverage info | Settlement: 1 / 2 / 4 users |
| --- | ---: | ---: | ---: | ---: | ---: |
| Current 11, active MissionControl | 1,281,852 / 336,352 | 1,226,018 / 280,518 | 1,640,677 / 680,677 | — | — |
| Current 11, candidate diagnostic | 1,115,223 / 294,223 | 1,068,377 / 247,377 | 1,431,919 / 596,419 | 1,622,621 | 9,041,379 / 12,020,360 / 17,348,094 |
| Stress 26, candidate diagnostic | 5,689,916 / 1,853,416 | 5,643,070 / 1,806,570 | 7,565,805 / 3,714,805 | 7,756,507 | 17,215,151 / 25,918,404 / 37,482,910 |

The active-MissionControl 26-claim cold NAV/user-value reads are **5,735,863 / 5,680,029**. Thus the **8M allowance** leaves **2,264,137 gas (28.3% of the allowance)** above the measured worst read; both legitimate getters fit at 11 and 26 claims. An earlier 5M trial failed this real-route stress qualification and was rejected. This is a measured allowance, not a guarantee for arbitrary future oracle graphs.

Cold runs clear Boa access warmth and transient caches; warm runs repeat without clearing them. The candidate diagnostic retains the real active PriceDesk/oracles, copies active asset policy into staged MissionControl, substitutes the reported department pointers and opens staging pause flags only inside the disposable fork. MissionControl's price-source priority ordering differs between the active and candidate cases. Those controls explain why cold figures differ from other transaction contexts, including earlier reviewer observations around 1.28–1.43M. All 11 current claim assets, balances, quotes and observed oracle call routes are in the report; the 26 distinct priced assets are recorded separately. No oracle or token-custody override is used.

Each sampled borrower repays 1 GREEN. Trace counts confirm **two NAV getter calls, one user-value getter and one withdrawal per user**: traversal walks the claims twice, settlement reads NAV again, and withdrawal values the position again internally. The full transaction also performs CreditEngine, Ledger, rewards and transfer work. A traversal-only number is not a keeper transaction estimate.

The prior diagnostic reported a provisional ceiling of **2 users for its measured 11-claim configuration**; that consumed-gas ceiling is superseded by the funded-limit qualification above, with mandatory exact-batch preflight at **no more than 12.8M estimated gas in a 16M budget**. The measured two-user batch leaves **3,979,640 gas (24.9%)** below that budget; four users exceed it. Reserve at least 20% for transaction overhead and state/route variance. The **26-claim stress configuration supports no keeper batch under this budget**: even one user exceeds 16M. Disable that cohort's keeper settlement and requalify or separately review a cost reduction; do not use the ABI's 25-user capacity as a supported batch size. A 64M outer limit was used only to measure otherwise unsupported batches to completion. These sampled limits do not authorize activation or replace final current-state qualification.

The staging result and gas diagnostic are separate report fields. Gas diagnostics explicitly record local candidate-pointer/pause changes and additional claim-ledger entries; these are experiments in the disposable fork, not a final activation or historical Contributor qualification. The real 11-claim inventory is unchanged. The 26-claim stress case uses distinct assets and configured real oracle routes with one-unit added claim entries; it does not assert that those added claims are in current custody. All live release gates remain open: final retained claim prices, final live gas and supported keeper batch qualification, pending HQ slot 8 resolution, rows 1–5 rehearsal using the exact final candidate set, deployed historical Contributor qualification, and separate modern rounding review.

## Merge coordination and regression placement

This PR is stacked on [PR #231](https://github.com/Ripe-Foundation/ripe-protocol/pull/231) and merges into it or after it. Preserve the verified **18,278-byte** Foxtrot pin and **60-output** ABI count, with `SwitchboardFoxtrotSetup.json` as the added named ABI anchor. The reserve-activation validator now audits both Foxtrot source variants while retaining seven registered controller roles. Preserve that distinction if #231 changes the inventory independently. Remeasure or recount if combined sources change.

The composed compatibility tests live in the existing AuctionHouse CI shard; registry tests remain in `tests/registries/test_vault_book_legacy_compat.py`. The shard-coverage check guards that placement; the manifest-consumer census separately checks recorded deployment consumers. The workflow now includes the stacked base `codex/base-upgrade-fork-rehearsal` for pull-request and merge-group events. The aggregate `rh-pr-gate` must succeed with all validation jobs on the exact final head before merge; preserve the run URL and check attachment. Branch-protection settings are a separate repository-owner control. Keep this PR draft through re-review. Issues #234 and #235 remain open, assigned to @mickhagen and labeled `activation-blocker`.

Authenticated historical fixture whitespace is intentional and must remain byte-for-byte unchanged. Check this round normally; for the complete stacked diff, narrowly exclude only `tests/fixtures/legacy_pool/contracts/vaults/StabilityPool.vy`, `tests/fixtures/legacy_pool/contracts/modules/Addys.vy` and `tests/fixtures/legacy_pool/contracts/vaults/RipeGov.vy` if their authenticated source bytes trigger `git diff --check`. Verify provenance hashes instead; do not normalize those files.
