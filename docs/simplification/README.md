# RH codebase simplification

- **Branch:** `codex/rh-codebase-simplification`
- **Worktree:** `/Users/wigglez/dev/ripe-protocol-rh-simplification`
- **Baseline:** `610b43f4508e85628a1362532a79d68d71ea902c` (`rh` / `origin/rh` at plan time)
- **Authorizing plan:** [`implementation-plan.md`](implementation-plan.md) — the exact
  bytes of `RH-CODEBASE-SIMPLIFICATION-PLAN.md` used to authorize this run
  (SHA-256 `52b9d33f2157b463a6cf26c8fe37783b4ce81bcd6157f5e841be73392ee13e4e`).
- **Extraction manifest:** [`extracted-files.tsv`](extracted-files.tsv)

Nothing was archived inside the repository. Every extracted path is recovered
from Git history at the baseline commit.

## Commit series

| Commit | Content |
| --- | --- |
| `56b6100` | Train 1 — bind the plan, verify the integrated speed foundation (no-change verification) |
| `51616b9` | Train 2 — extract deployment step manifests and the parked RH dashboard |
| `b4f2a95` | Record the step-manifest extraction in the live status authority |
| `61ec63d` | First implementation report |
| *(see [`validation-evidence.md`](validation-evidence.md))* | Review remediation: RH-D020 supersession, corrected metrics, evidence packet, complete retained-document list |

Train 3 produced no commit; every candidate was blocked by a retained consumer
or a committed authority. See **De-scopes** below.

The exact delivered tip, the tip each measurement is bound to, and every
evidence path with its SHA-256 are recorded in
[`validation-evidence.md`](validation-evidence.md). That document is the
authoritative evidence inventory; this one is the narrative report.

Commits are unsigned because the sandbox denies access to `~/.gnupg`. Signing was
not a plan requirement; the landing owner can re-sign at integration.

## Before / after

Tracked-line counts move by a few hundred with each report revision because this
document is itself tracked. [`validation-evidence.md`](validation-evidence.md)
records the exact figure for every commit in the series; the table below is bound
to the commits named in its header.

| Measure | Baseline `610b43f` | Delivered tip | Change |
| --- | ---: | ---: | ---: |
| Tracked files | 678 | 588 | −90 |
| Tracked lines | 3,445,736 | see `validation-evidence.md` (≈615,900) | ≈−82.1% |
| Working-tree bytes (excl. `.git`) | 162,472 KB | 26,688 KB | −83.6% |

The file count is stable across the series at 588. Only `docs/simplification/`
report text changes between the last commits, and no test, script, config, or
scanner reads that directory — proven in `validation-evidence.md`.

Per-area figures below are measured at `b4f2a95`, the last commit that changed
anything outside `docs/simplification/`; only this report's own line count moves
after it.

| Area | Baseline `610b43f` files / lines | At `b4f2a95` files / lines |
| --- | ---: | ---: |
| `migration_history/` | 68 / 2,957,627 | 2 / 146,579 |
| `tests/` | 170 / 149,889 | 170 / 149,894 |
| `docs/` | 149 / 129,519 | 126 / 110,493 |
| `scripts/` | 100 / 115,027 | 100 / 115,027 |
| `config/` | 8 / 49,242 | 8 / 49,242 |
| `contracts/` | 96 / 39,697 | 96 / 39,697 |
| `migrations/` | 72 / 3,412 | 72 / 3,412 |
| `interfaces/` | 6 / 758 | 6 / 758 |
| `.github/` | 2 / 148 | 1 / 92 |

Against the non-binding Section 10 projection (roughly 500,000–575,000 lines and
470–590 files): the file count lands inside the range at 588; the line count is
about 615,900, roughly 40,900 above the top of the projected zone. The gap is entirely
accounted for by two documented de-scopes — the block-clock process package
(23,184 projected lines) and the provisional 40,000–70,000 "other completed
docs" range, which the reverse-reference scan did not support. Section 10 states
that retention rules and evidence-based de-scopes win over every number in it.

## Recovery

`extracted-files.tsv` records one row per extracted path with its category,
original path, Git mode, baseline blob ID, byte length, SHA-256, and recovery
commit. All 93 rows were verified to recover **by path** from the recovery commit
with exact blob ID, byte length, and SHA-256 match, and to be absent from the
working tree.

Restore a single file:

```bash
git show 610b43f4508e85628a1362532a79d68d71ea902c:migration_history/base-mainnet/v1/1004-manifest.json > /tmp/1004-manifest.json
```

Restore an entire extracted category:

```bash
git checkout 610b43f4508e85628a1362532a79d68d71ea902c -- migration_history/base-mainnet/v1 migration_history/robinhood-mainnet/v1
git checkout 610b43f4508e85628a1362532a79d68d71ea902c -- docs/chains/rh/dashboard .github/workflows/rh-handoff-dashboard.yml
```

Verify every row recovers with matching bytes:

```bash
python - <<'EOF'
import csv, hashlib, subprocess
bad = []
for row in csv.DictReader(open("docs/simplification/extracted-files.tsv"), delimiter="\t"):
    blob = subprocess.run(
        ["git", "cat-file", "blob", f"{row['recovery_commit']}:{row['original_path']}"],
        capture_output=True, check=True,
    ).stdout
    if (len(blob) != int(row["byte_length"])
            or hashlib.sha256(blob).hexdigest() != row["sha256"]):
        bad.append(row["original_path"])
print("mismatches:", bad or "none")
EOF
```

## What was extracted

| Category | Files | Notes |
| --- | ---: | --- |
| `migration-history-step-manifest` | 66 | 59 Base + 7 Robinhood numeric step manifests. Both `current-manifest.json` files, both `v1` directories, and every `config/network_profiles.py` declaration are retained unchanged. |
| `dashboard-application` | 26 | The parked `docs/chains/rh/dashboard/` Next.js application. |
| `dashboard-workflow` | 1 | `.github/workflows/rh-handoff-dashboard.yml`. `.github/workflows/python-tests.yml` is retained. |

## Test and invariant disposition

**No test file was removed and no test identity disappeared.** `tests/` still holds
170 files, and both lanes collect exactly what they collected at baseline
(lean 3,244; comprehensive 4,539).

One test was adapted, the single change Section 4.1 permits:

| Test | Change | Invariant preserved |
| --- | --- | --- |
| `tests/deployment/test_manifest_schema.py::test_every_committed_base_json_parses_without_rewrite` | Base-history corpus count `60` → `1` | Both glob expressions, the top-level-key assertion, the record-shape assertion, and the read-does-not-rewrite byte comparison are unchanged and still run against the retained `current-manifest.json`. Passed at final. |

Directory-scanning consumers were re-run rather than weakened:

| Consumer | Outcome at final |
| --- | --- |
| `test_base_profile_regression.py::test_committed_base_history_inventory_is_unchanged` | PASS — `git status` over `migration_history/base-mainnet/v1` is clean because the deletions are committed |
| `test_base_profile_regression.py::test_base_mainnet_source_and_history_are_preserved` | PASS — `history_state` is still `EXISTING` |
| `test_robinhood_blueprint.py` three-directory path census | PASS (79 tests green) |
| `test_lootbox_deployment_profiles.py::test_x1_historical_call_site_inventory_is_complete` | Pre-existing FAIL, byte-identical message at baseline and final; it scans `migration_history` only for `*.py`, of which the directory contains none. Its failure is about `migrations/robinhood-mainnet/0005_Departments.py`. |
| `test_network_profiles.py`, `test_current_manifest_promotion.py` | PASS, unchanged |

## Mock-contract consumer inventory

All 34 `contracts/mock/` files are retained; every one has at least one retained
consumer. `scripts/export_abis.py` excludes `contracts/mock/` and
`contracts/testing/`, so the 52-output ABI census is unaffected either way.

| Mock | Retained consumers (primary) |
| --- | --- |
| `MockSGreenPrice.vy` | `config/block-clock-inventory.json` |
| `MockAuctionHouse.vy` | `tests/config/test_switchboard_charlie.py` |
| `MockBadERC1271.vy`, `MockERC1271.vy` | `tests/tokens/test_signatures.py` |
| `MockCurvePrices.vy`, `MockErc4626Vault.vy`, `MockErc4626VaultWithSafeGap.vy`, `MockUndyV2.vy`, `MockWhitelist.vy`, `MockRando.vy` | `tests/conf_mock.py` |
| `MockErc721.vy`, `MockRevertOnReceive.vy`, `MockReentrantErc20.vy`, `MockBlacklistErc20.vy` | `tests/core/endaoment/test_endaoment_funds.py` |
| `MockWithGov.vy` | `tests/modules/test_local_gov.py` |
| `MockWithTimeLock.vy` | `tests/modules/test_time_lock.py` |
| `MockPriceSource.vy` | `tests/priceSources/modules/test_price_source_data.py` |
| `MockRobinhoodCurveSystem.vy` | `tests/priceSources/curve/test_robinhood_launch_route.py` |
| `MockUniswapV2Pair.vy`, `MockUniswapV2QuotePriceDesk.vy`, `MockUniswapV2RipeHq.vy`, `MockUniswapV2Token.vy` | `tests/priceSources/uniswap/test_minimal_prices.py` (Uniswap retained by Section 3.6) |
| `MockDepartment.vy` | `tests/conf_mock.py` |
| `MockMorphoV2Vault.vy`, `MockMorphoV2Factory.vy`, `MockYieldRegistry.vy` | `tests/priceSources/blueChip/test_bluechip_morpho_v2.py` |
| `MockProbeErc20.vy`, `MockFeeOnTransferErc20.vy` | `tests/probes/test_stock_token_transfer_probe.py`, `tests/vaults/…` |
| `MockPyth.vy`, `MockStork.vy`, `MockChainlinkFeed.vy` | `tests/priceSources/test_{pyth,stork,chainlink}_prices.py` |
| `MockRegistry.vy` | `tests/registries/test_address_registry.py` |
| `MockErc20.vy` | `tests/conf_mock.py` and many behavior suites |
| `MockStockTokenControls.vy` | `tests/vaults/test_stock_token_vault_comparison.py`, `tests/vaults/test_basic_vault_safety.py` |

## Document disposition

149 baseline documents − 26 removed + 3 added = **126 retained**. All 26 removed
files are the dashboard application's own files; nothing else under `docs/` was
deleted. The 3 added are this report, the extraction manifest, and the tracked
plan copy. The complete retained list is in
[`validation-evidence.md`](validation-evidence.md).

**Runtime-read documents, all retained** (found by the required reverse-reference
scan over `tests/`, `scripts/`, `config/`, `migrations/`, `.github/` for literal
paths and computed `Path` joins):

| Document | Retained consumer |
| --- | --- |
| `evidence/dependency-security-gate.md` | `tests/deployment/test_dependency_gate.py` |
| `schemas/deployment-manifest-v2.schema.json` | `tests/deployment/test_manifest_schema.py` |
| `evidence/robinhood-manifest-phase-a.md` | `tests/deployment/test_manifest_schema.py` authorized-path set |
| `evidence/robinhood-defaults-parameters-phase-a.md` | `config/robinhood-parameters.json` citations |
| `reward-launch-qualification.md` | `config/robinhood-parameters.json` citation |
| `hardening/basic-vault-consumer-inventory.md` | `tests/vaults/test_basic_vault_consumer_inventory.py` |
| `hardening/creditengine-gas-measurements.md` | `tests/core/creditEngine/test_stock_backing.py` |
| `ledger-guard-implementation-record.md` | `tests/inventory/test_block_clock_inventory.py` |
| `examples/ExampleGreenCcipBurnMintPool.vy` | `scripts/check_block_clock_inventory.py`, `config/block-clock-inventory.json` |
| `block-number-inventory.md` | `config/block-clock-inventory.json` |

`status.yaml` is retained: every live operator document
(`deployment-owner-quickstart.md`, `deployment-owner-readiness.md`,
`START-HERE.md`, `AGENT-HANDOFF.md`, `decision-register.md`) names it as the sole
machine-readable current-status authority.

**Why no further documents were pruned.** A reference graph over all 149 documents
showed the corpus is densely interlinked: excluding the dashboard, only two
documents are referenced solely by a top-level authority hub, and the largest set
closed under "no code reference and every referrer is itself deletable" is six
files totalling 5,130 lines. Each of those six was then read directly and each is
either active work (`smart-contract-test-coverage-gap-plan.md` is bound to PR #67
at `7d8c76e5`; `canonical-launch-input-verification.md` is 2026-08-01
launch-qualification evidence recording 58 open blockers) or carries an explicit
in-document retention instruction (all three `stability-pool/` documents say to
retain them as design provenance, refreshed 2026-08-06). Deleting anything beyond
that would have required editing retained authority documents to remove inbound
links, which Section 4.3 does not authorize.

## Documentation edits

Only where a path reference would otherwise dangle or a statement would become
false:

- `smart-contract-changes/README.md` — the enforcement-boundary section linked to
  the deleted workflow and already misstated the workflow inventory;
- `smart-contract-changes/ccip-burn-mint-token-pools.md` — same stale claim;
- `status.yaml` — `dashboard_governance` and a new `migration_history_extraction`
  note record both extractions without altering the historical provenance lists;
- `decision-register.md` — an RH-D018 current overlay, in the register's own
  idiom, recording the extraction without revoking the ratification;
- `robinhood-deployment-support-specification.md` §3.6 — notes the extraction and
  that operator behavior is unchanged.

## De-scopes, with evidence

**Train 3 was fully de-scoped.** Every candidate had a retained consumer or a
committed authority that Section 0.4 says to respect.

| Candidate | Blocker |
| --- | --- |
| Block-clock process package (23,184 lines) | `tests/inventory/test_bluechip_yield_prices_artifacts.py`, which Section 4.5 retains by name, imports `scripts.check_block_clock_inventory` and asserts its exact `CURRENT_BINDINGS_STATE_SHA256`. The script reads `config/block-clock-inventory.json`. The package therefore cannot be removed atomically, and Section 2.3H forbids removing `tests/inventory/test_block_clock_inventory.py` on its own. |
| Probe package (`contracts/testing/`, `scripts/probes/`, `tests/probes/`) | Six of its nine files are pinned paths inside the retained `config/block-clock-inventory.json`, and `scripts/check_block_clock_inventory.py` names them in `S5_REVIEW_PATHS` and its review records. The inventory's session fixture copies every pinned path off disk. |
| `tests/deployment/fork/` (4,922 lines) | `tests/deployment/fork/offline/test_collection_contract.py` asserts `len(IMPLEMENTED_PATH_LEDGER) == 31` and that the ledger equals an `rglob` of the suite root, plus exact `ordered_node_sha256` and per-mode classification SHA-256 values. Removing any file requires refreshing committed authority hashes, which Section 7.3 forbids. The `offline/` tests are also the fail-closed net (`test_safe_default_blocks_socket_and_requests`, `test_default_mode_is_network_disabled`, `test_forbidden_environment_and_alias_drift_fail_closed`) that Section 7.4 relies on to run the comprehensive lane safely. |
| `tests/vaults/test_stock_token_vault_comparison.py` (2,043 lines) | 31 heavily parametrized direct contract-behavior and security tests covering liquidation, auction atomicity, blocklists, pause paths, loss accounting, and governance recovery. Section 1.1 retains direct behavior and security-invariant tests. |
| Parked CCIP examples | `examples/ExampleGreenCcipBurnMintPool.vy` is read by the retained checker and pinned in the retained inventory; the other two files in that directory are its README and reference source. |
| One-time scripts | None found without a consumer. All six `scripts/params/*.py` reports are invoked by `scripts/params/run_all.py`; `scripts/utils/log.py` is imported by `migrate.py` and the runner; `check_contract_artifacts.py`, `update_contract_artifact_expectations.py`, `export_abis.py`, and `verify_blockscout.py` are on the Section 3.4 retention list. `scripts/ledger_signing_smoke.py` has no textual consumer but is deployment-owner signing tooling protected by Section 0.5 precedence 3. |

## Validation

Interpreter `/Users/wigglez/dev/ripe-protocol-validation-envs/rh-wave2-py312/bin/python`
(Python 3.12.0, IPython 9.8.0, pytest 8.4.2, vyper 0.4.3), same machine and same
private-cache methodology for every baseline and final measurement.

### Suites

| Lane | Baseline `610b43f` | Final `b4f2a95` |
| --- | --- | --- |
| Lean (default) | 13 failed, 3,205 passed, 278 deselected, 1 xfailed, 25 errors — pytest 934.80s, wall 997.30s, exit 1 | 13 failed, 3,205 passed, 278 deselected, 1 xfailed, 25 errors — pytest 1003.49s, wall 1071.24s, exit 1 |
| Comprehensive | 34 failed, 4,303 passed, 143 deselected, 1 xfailed, 201 errors — pytest 1627.42s, wall 1780.94s, exit 1 | 34 failed, 4,303 passed, 143 deselected, 1 xfailed, 201 errors — pytest 1607.62s, wall 1749.66s, exit 1 |

**Normalized failure/error identity diff: zero new identities in both lanes, and
zero identities lost.** Lean 38 → 38, comprehensive 235 → 235. Both baseline sets
were cross-checked against their terminal `FAILED`/`ERROR` node IDs and reconcile
exactly (the comprehensive terminal writer truncates parametrized IDs containing
spaces; those reconcile by prefix).

Neither lane is green, at baseline or at final. The 38 lean identities are 13
pre-existing failures plus 25 `tests/priceSources/blueChip/test_bluechip_morpho_v2.py`
errors. This cleanup neither fixed nor introduced any of them.

### Gates at final, from the clean committed validation checkout

| Gate | Result |
| --- | --- |
| `scripts/check_contract_artifacts.py` | `CONTRACT_ARTIFACTS_OK` — no retained production-artifact drift |
| ABI export parity (`test_abi_export.py`) | GREEN, 9/9 — exactly 52 checked-in ABIs retained |
| Dependency-security gate | GREEN, 45/45 |
| Contract artifact inventory | GREEN, 41/41 |
| Current-manifest promotion | GREEN, 62/62 |
| Network profiles | GREEN, 31/31 |
| Base profile regression | GREEN, 19/19 |
| Robinhood blueprint census | GREEN, 79/79 |
| Manifest schema | 85/86, the single failure pre-existing |
| BluePrint stock M4 HEAD census | 29/37, all 8 failures pre-existing |
| `tests.constants` import smoke | Migrations and `scripts/params/params_utils.py` still resolve it |
| `git diff --check` | Clean |
| `python-tests.yml` YAML parse, retained paths, pinned actions | Valid; all four actions pinned to 40-hex SHAs |

The workflow was **not dispatched**. The branch is not pushed, so no GitHub
Actions run was observed and no CI result is claimed.

### Benchmarks (process wall time from `/usr/bin/time -p`, authoritative)

| Target | Baseline cold | Final cold | Baseline warm | Final warm | Warm change |
| --- | ---: | ---: | ---: | ---: | ---: |
| `tests/tokens` | 148.28s | 135.92s | 57.54s | 54.76s | −4.8% |
| `tests/data/test_mission_control.py` | 149.17s | 138.34s | 56.10s | 56.59s | +0.9% |

pytest-reported durations, same order: 126.38 → 115.93 and 36.15 → 35.05;
129.43 → 118.51 and 37.05 → 37.72. Both targets pass (82 and 83 tests). Each run
used a fresh private runtime root, so the first run is cold for both bytecode and
Boa artifacts and the immediate rerun measures both warm. No warm regression
exceeds the ±10% rule.

### Socket-purity gate (pass/fail, not a timing benchmark)

`tests/clock/test_clock_profiles.py` with `socket.socket` patched to raise:
**57 passed** at baseline and 57 passed at final. Lazy port allocation inside the
`anvil()` factory is preserved; the pure clock subtree binds no socket.

## Tests not run, and why

- Remote fork qualification. `RIPE_RH_FORK_MODE`, `RIPE_RH_FORK_MANIFEST`, and
  `RIPE_RH_FORK_IDENTITY_MANIFEST` were unset for every run, so
  `tests/deployment/fork/` collected in the comprehensive lane and ran only its
  offline, network-disabled paths. No RPC endpoint, signer, mnemonic, or cloud
  credential was used or present.
- Marker-gated lanes in the lean run: `release`, `artifact`, `fuzz`, `gas`, and
  `fork_qualification` are deselected by `pytest.ini`. All of them run in the
  comprehensive lane, which was executed.
- GitHub Actions. Not dispatched; the branch is not pushed.

## Residual risks and follow-ups

- **RH-D018 is resolved, not deferred.** The owner ratified superseding its
  repository-placement clause on 2026-08-07. `RH-D020 — The dashboard is
  extracted from the active tree` now carries that authority in the decision
  register, `status.yaml` mirrors it in the `decisions` list and in
  `dashboard_governance`, and register/`status.yaml` identifier-and-title parity
  was verified programmatically (23 = 23, no mismatches). The RH-D018
  dependency-scope boundary and the RH-D019 parked publication posture are
  unchanged, and no Sites action is authorized.
- **Deployment CLI defects** recorded in
  `robinhood-deployment-support-specification.md` are untouched and out of scope
  by Section 2.4. They remain a separate deployment-owner task.
- **Pre-existing broken links.** 97 relative markdown links across four documents
  point at `GuardedErc20` sources absent at the baseline commit. They pre-date
  this work and none is in the extraction manifest.
- **Pre-existing red gates.** The block-clock inventory checker already fails at
  the baseline with three codes, and three of its 160 pinned paths were already
  missing. This cleanup did not touch that; it is why the block-clock package
  could not be retired.
