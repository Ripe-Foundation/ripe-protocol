# PR #233 re-review implementation and qualification

The contract, staging, verifier, executable monitor and test changes are implemented. **This is not release approval.** The exact proposed bridge configuration fails strict pricing for one route and therefore does not qualify the sampled current mixed holders or the preserved 26-claim stress set. The qualification command deliberately exits nonzero and retains its complete evidence; staging and standalone staged verification are separate results.

PR base remains `codex/base-upgrade-fork-rehearsal` at `bdf7f3da7113aabde60ab8eceab6a960a841bb88`. This work stacks on PR #231 and remains draft. Code commits are signed; clean evidence below is from `c56bce6a09e372540cf4dd7158d165a71f520a8e`, tree `c343bf98bd0520cbfdacb3cd7e603d499d43759d`. The following commit adds only documentation and evidence. Its own final-head rerun and full payload are published on PR #233, avoiding a self-referential report/commit cycle.

## Resolution of the 13 requested items

1. **Underfunded optional reads fail closed.** Before every NAV, user-value, conversion or price read, VaultBook requires 8,176,985 gas: 8M plus the rounded EIP-150 reserve and 50k setup/memory/cold-call reserve. The check is unconditional, including nested PriceDesk successful-zero behavior. Gas scans cover both user orders, LP, sGREEN, mixed cohorts and every optional branch. Every accepted optional call receives exactly 8M. Genuine early reverts, malformed/zero results and full-allowance exhaustion remain fail-soft; direct settlement stays strict. VaultBook is 18,382 bytes. The 60 ABIs were regenerated and checked; the public ABI is unchanged by this internal check.
2. **Independent baseline enforced.** The command requires an immutable baseline plus an independently supplied SHA-256, rejects identical resolved files, symlinks and hardlinks, and derives canonical retained/reused addresses from that baseline. Both paths and hashes are recorded. The baseline is separately committed; no historical manifest was rewritten.
3. **Staged lifecycle enforced.** HQ slots 5, 6, 8, 9 and 18 must match authenticated pre-stage addresses. Partial activation, unrelated addresses and an already-active candidate fail. Deleverage inheritance comes from the pinned old slot 18. Only `staged` is supported; there is no permissive active-mode fallback.
4. **Actual active book compared.** Authenticate slot 8, read all five forward/reverse/valid row identities, compare them with the candidate, and report both sets separately. Drift in either book fails.
5. **FoxtrotSetup mutable state checked.** Expected MissionControl and Defaults, init step 1, next asset index 0 and uninitialized rewards are checked before/after staging and by the verifier. Each field has a negative test. Constructor-authority provenance names the precise current-manifest label/argument and numbered deployment record.
6. **Pending actions covered.** HQ update and disable states for slots 5/6/8/9/18 must match explicit reviewed dispositions. Only the exact known slot-8 conflict is preserved under `hold_no_activation`; other slots must be empty. Every populated critical candidate book/board row must have empty pending update/disable state.
7. **Final staging state reauthenticated.** After all 35 simulated transactions, retained rows, inherited policy, reused-controller code/HQ/governance/bounds, Foxtrot state and HQ/candidate pending actions are re-read. A changed source state prevents completion. Adversarial staging tests mutate state after the final setup transaction.
8. **Direct verifier suite added.** 41 network-independent composition tests exercise successful staging, independent inputs, lifecycle/row/policy drift, every relevant pending action, Foxtrot fields and durable failure reports with exact reasons. Authentication checks are not bypassed. Only deterministic compiler results are cached in these tests.
9. **Executable monitor supplied; integration remains gated.** Strict pinned-block cohort diagnosis, classified zeros/failures, complete-inventory attestation, exact-batch local simulation, and finalized-receipt reconciliation are executable. Every intended user must have the expected event, target and sufficient credited/cleared debt. Caller/calldata, emitter, duplicates, omissions and finality are checked. The external keeper repository/service has not been identified. Owner @mickhagen must wire the exact cohort-selection, pre-submission and post-finality completion hooks in [#236](https://github.com/Ripe-Foundation/ripe-protocol/issues/236). Do not describe production monitoring as complete until that integration is qualified.
10. **Expanded qualification executed; mixed-holder release qualification remains blocked.** Actual LP-only and sGREEN-only borrowers, conversion traces, both mixed-user orders, multiple batch sizes, current mixed holders and the exact prior 26-claim set are exercised against the bridge/defaults/candidate configuration. Full settlement is proven for eligible LP and sGREEN representatives. Strict collateral valuation blocks all four sampled current mixed holders, so their successful full settlement is not claimed. [#237](https://github.com/Ripe-Foundation/ripe-protocol/issues/237) records the exact failing route, 1.5M source cap and owner. No oracle, price, custody or debt override manufactures success. No keeper batch is supported for the 26-claim configuration.
11. **Clean provenance produced.** Detached checkout, clean tracked/untracked status, signed code commit/tree, per-input hashes, independent baseline hash and source-after checks are recorded. Reports are generated outside the checkout. Cross-checkout Boa cache contamination was reproduced and fixed with temporary scoped caches; success/failure tests verify exact caller-cache restoration. Both pinned command examples require an archive-capable Base RPC. Standalone `--replay-staging` independently reconstructs fork-only candidates using the unchanged production runner and then verifies them.
12. **Test/process cleanup complete, release gates retained.** The residue test pins its two exact revert reasons. #234 and #235 remain open, assigned to @mickhagen with `activation-blocker` metadata. The workflow now includes the stacked base and exposes `rh-pr-gate` on PR/merge-group events. Require its final-head success before merge; branch protection remains a repository-owner setting. Historical fixture whitespace is preserved. No authenticated historical migration or manifest was edited.
13. **Prior behavior retained.** Sub-dollar forward rounding, healthy-user progress past genuinely unusable positions, strict settlement, 8M read cap, public binding, retained rows 1–5, Golf's Pool-1 prohibition, search-path restoration, historical source authentication, 60 ABI outputs and the 18,278-byte Foxtrot pin remain covered. Modern rounding and historical Contributor gates remain open.

## Files changed in this round

| File | Purpose |
| --- | --- |
| `contracts/registries/VaultBook.vy` | Unconditional full-allowance admission before each optional read. |
| `migrations/base-mainnet/2026091900_StageLegacyVaultCompatibility.py` | Before/after source authentication and candidate pending-action checks. |
| `scripts/utils/legacy_vault_compat.py` | Shared row, pending, lifecycle/Foxtrot and source-state invariants; exact constructor provenance. |
| `scripts/capture_legacy_vault_baseline.py` | Read-only capture of independently reviewable pre-stage addresses, runtime hashes, policy and pending dispositions. |
| `scripts/verify_legacy_vault_cutover.py` | Independent baseline inputs; enforced staged phase; full state comparison; durable failures; standalone local replay. |
| `scripts/base_legacy_compat_fork.py` | Clean production-runner replay, separate staging/gas results, fail-closed qualification exit, scoped compiler cache. |
| `scripts/utils/legacy_vault_gas.py` | Actual Foxtrot Defaults/bridge configuration, both cohorts/orders, funded-limit scan, all-user and withdrawal trace reconciliation, explicit rejected samples. |
| `scripts/legacy_vault_preflight.py` | Strict diagnostic, local preflight and finalized-receipt reconciliation without a broadcast path. |
| `scripts/utils/fork_reports.py` | Source tree and complete historical/fixture/gas-input fingerprints. |
| `tests/core/auctionHouse/test_base_legacy_vault_compat.py` | Exact residue reverts, all four optional branch starvation checks and ordered cohort gas-limit scans. |
| `tests/test_base_review_safety.py` | Foxtrot field negatives and adversarial final-transaction source/pending drift. |
| `tests/test_legacy_cutover_verifier.py` | Direct offline verifier composition and input/failure-report regressions. |
| `tests/test_legacy_vault_preflight.py` | Classification, real retained-cohort simulation, all-user reconciliation, finality/intent and error-report tests. |
| `tests/test_legacy_rehearsal_cache.py` | Cross-checkout cache contamination reproduction and exact restoration on both exits. |
| `tests/test_vault_pointer_runtime_sizes.py` | Intentional VaultBook runtime update to 18,382 bytes. |
| `.github/workflows/python-tests.yml` | PR/merge-group routing for the stacked base. |
| `tests/test_lean_shard_coverage.py` | Guard the additional workflow route. |
| `docs/chains/base/legacy-vault-compatibility.md` | Commands, gas-admission semantics, baseline/lifecycle requirements, monitor hooks and release gates. |
| `docs/chains/base/legacy-vault-rehearsal/re-review/pre-stage-baseline.json` | Frozen pre-stage evidence with separate expected hash. |
| `docs/chains/base/legacy-vault-rehearsal/re-review/qualification.json` | Full clean production-runner/gas artifact; qualification intentionally blocked. |
| `docs/chains/base/legacy-vault-rehearsal/re-review/verifier.json` | Independent clean standalone staged-verifier artifact. |
| `docs/chains/base/legacy-vault-rehearsal/re-review/validation.json` | Exact local commands, counts and artifact hashes. |
| This handoff | Numbered resolution, file summary, capacity, provenance and remaining gates. |

## Pinned configuration and operational capacity

Base block **51,575,411**, hash **`0x3bd7415ea242fb3bae7f9ceb46747fa5b22f7504d5e442a362153fd7d6378acd`**. Independent baseline SHA-256: **`495b2075514d1345a2df0274705791d5a511cdda963a3039288ac65498531043`**.

Bridge PriceDesk **`0xad70893E2F51076b0e9bA18fC593e924593a073F`**; MissionControl **`0xD2c97549F4D44ca8Eb000d2AB2f3c5da8623D1D7`**; Defaults **`0x249c4798C49Fc8Ad86a43dC425D80396971E7AcC`**. Foxtrot configuration/rewards initialization is simulated through its actual methods after staged-state verification. Source order `[1,8,2,9,4,5]`, stale time 86,400 seconds, price/snapshot source allowances 1.5M each. All source addresses, validity and runtime hashes are in the report.

Use a **16M transaction budget**, with **12.8M maximum execution limit** and remaining headroom for intrinsic gas and state variance. The table shows tested funded upper bounds, not merely consumed gas; the binary-search interval is at most 10,000 gas. Every successful sample has full intended-user reconciliation and a positive retained-pool withdrawal trace.

| Current inventory/sample | Funded upper bound | Consumed execution gas | Supported within 12.8M? |
| --- | ---: | ---: | --- |
| LP-only, 11 claims, 1 user | 11,418,750 | 4,796,915 | Yes, conditional on release gates |
| LP-only, 11 claims, 2 users | 14,375,000 | 7,405,229 | No |
| sGREEN-only, 0 claims, 1 user | 9,050,000 | 1,180,025 | Yes, conditional |
| sGREEN-only, 0 claims, 2 users | 9,775,000 | 1,612,232 | Yes, conditional |
| sGREEN-only, 0 claims, 4 users | 10,900,000 | 2,736,103 | Yes, conditional; largest measured sample |
| Separate LP then sGREEN users | 13,493,750 | 5,440,133 | No |
| Separate sGREEN then LP users | 12,181,250 | 5,440,133 | Yes, conditional |
| Current mixed holder / mixed holder with healthy user, both orders | Strict collateral valuation fails | — | No; #237 |
| Preserved 26-claim stress set, either cohort and all tested batches | Strict price/getter/settlement qualification fails | — | No supported batch |

Thus measured conditional capacity is **1 LP-only user**, **up to the tested 4 sGREEN-only users**, and **2 separately funded users only in the tested sGREEN-then-LP ordering**. No universal mixed-holder allowance is qualified. No operational ceiling is inferred from the ABI's 25-user bound. Qualification used a trusted registered caller; a real keeper must separately pass the exact caller/eligibility simulation. The 64M outer limit is diagnostic only and does not change the nested source cap.

The 26-claim experiment retains the exact historical asset list, adding one raw claim-ledger unit for missing entries in each cohort. It does not change oracle code, feeds, prices or token custody. These entries model read cost and failure behavior, not new backed claims. Actual LP inventory has 11 claims and actual sGREEN inventory has none. VVV and mcbETH still require economic review of their one-wei prices.

## Runtime sizes

| Contract | Runtime bytes |
| --- | ---: |
| VaultBook | 18,382 |
| AuctionHouse | 24,565 |
| Deleverage | 24,430 |
| SwitchboardAlpha | 23,982 |
| SwitchboardCharlie | 22,326 |
| SwitchboardGolf | 21,035 |
| Switchboard | 12,595 |
| SwitchboardFoxtrot (existing pin) | 18,278 |

All runtime pins remain below 24,576. The full inventory remains in `tests/test_vault_pointer_runtime_sizes.py`; no production contract besides VaultBook changed in this review round.

## Validation and preservation

Exact commands and pass/fail counts are in `validation.json`. Local contract/monitor/controls/artifact/snapshot suites are green. The full exact-final-head CI run, attached PR checks and final-head artifact hashes are linked from the PR handoff. The clean standalone staged verifier passes; the gas-inclusive rehearsal deliberately fails `BASE_LEGACY_COMPAT_GAS_QUALIFICATION_BLOCKED` after preserving its completed matrix and successful staging evidence.

Historical migrations, recorded deployment manifests and authenticated historical fixtures remain byte-for-byte unchanged from `4291fc48`. `git diff --check` passes for this round. For the complete stacked diff, narrowly exclude only intentional authenticated fixture whitespace in `tests/fixtures/legacy_pool/contracts/vaults/StabilityPool.vy`, `tests/fixtures/legacy_pool/contracts/modules/Addys.vy` and `tests/fixtures/legacy_pool/contracts/vaults/RipeGov.vy`; verify their provenance hashes instead. The normal checkout was not edited. The implementation worktree retains its two pre-existing untracked handoff/planning inputs; the index and tracked worktree are clean after commits.

**Zero live transactions, proposals, deployments or activations occurred.** Outstanding release work is fresh candidate staging/authorization, all retained claim-price qualification, pending HQ slot-8 resolution, modern rounding #234, historical Contributors #235, external keeper integration #236, and bridge/mixed-holder qualification #237. All four issues have accountable owner @mickhagen and activation-blocker labels. Nothing in these reports authorizes release.
