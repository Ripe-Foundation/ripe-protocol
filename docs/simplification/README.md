# RH codebase simplification

> **8 August 2026 — Train 3 de-scope superseded.** A later pass on this branch
> removed the block-clock inventory
> (`scripts/check_block_clock_inventory.py`, `config/block-clock-inventory.json`,
> `tests/inventory/test_block_clock_inventory.py`) and the probe package
> (`contracts/testing/`, `scripts/probes/`, `tests/probes/`), which the
> "De-scopes, with evidence" section below records as retained. The blocker
> that section describes was real at the time: those paths were pinned by the
> inventory's own file census, so nothing could be removed without it. Removing
> the census removed the blocker.
>
> The sections below are kept as the record of the original two trains. For what
> the branch removes now, see [`REMOVED.md`](REMOVED.md) — a single index of all
> 171 removed paths — and Section 14 of
> [`validation-evidence.md`](validation-evidence.md) for the binding test
> evidence. No production contract was modified in either pass.

- **Branch:** `codex/rh-codebase-simplification`
- **Worktree:** `/Users/wigglez/dev/ripe-protocol-rh-simplification`
- **Baseline:** `610b43f4508e85628a1362532a79d68d71ea902c` (`rh` / `origin/rh` at plan time)
- **Authorizing plan:** [`implementation-plan.md`](implementation-plan.md) — the exact
  bytes of `RH-CODEBASE-SIMPLIFICATION-PLAN.md` used to authorize this run
  (SHA-256 `52b9d33f2157b463a6cf26c8fe37783b4ce81bcd6157f5e841be73392ee13e4e`).
- **Extraction manifest:** [`extracted-files.tsv`](extracted-files.tsv)

Nothing was archived inside the repository. Every extracted path is recovered
from Git history at the baseline commit.

## Status and authority

**This branch is the owner-rebound implementation candidate.** It is open as
[PR #77](https://github.com/Ripe-Foundation/ripe-protocol/pull/77) against `rh`,
and is still in **draft**. The post-merge validation matrix is complete and
recorded in [`validation-evidence.md`](validation-evidence.md) section 14; an
earlier revision of this line said the draft was pending that matrix, which
stopped being true once section 14 landed. What the draft status now reflects is
that marking the PR ready is an owner action, not a missing artifact.

`implementation-plan.md` in this directory is the byte-exact copy of the plan
that authorized this work (SHA-256
`52b9d33f2157b463a6cf26c8fe37783b4ce81bcd6157f5e841be73392ee13e4e`, baseline
`610b43f`). The root `RH-CODEBASE-SIMPLIFICATION-PLAN.md` was subsequently
replaced with a revised plan (SHA-256
`a20a4a53d953a3c3120462bee186e81e092fc2a90d0d407edfdda5f5151a4990`, baseline
`be6e4e9`) that called for a fresh `-v2` branch and forbade opening a PR. **On
2026-08-07 the owner explicitly rebound to this branch**, superseding that
plan's branch, baseline, and no-PR clauses. The tracked copy here is
deliberately the plan that authorized the work, not the later revision.

The substance is unaffected: the revised plan mandates the same removals — 66
numeric step manifests, 26 dashboard files, one workflow — and records the same
Train 3 no-change retention outcome this branch reached independently.

For the commit series, exact per-commit tree sizes, and the commit each
measurement is bound to, see [`validation-evidence.md`](validation-evidence.md).

**Commit signatures, stated accurately.** An earlier revision of this line claimed
"commits on this branch are GPG-signed and verify as good." A review checked the
raw commit objects and refuted it.

The durable facts, which no later commit changes:

- **11 commits on this branch carry no signature at all**, including the first,
  `56b6100`. Any branch-wide "all commits are signed" claim is therefore false
  and cannot be repaired by signing later work.
- **No commit reports `G` (good) in this checkout.** Signed ones report `E` —
  signature present, public key not in this keyring — so "verifies as good" is
  not something a local clone can assert either way.

The signed count necessarily moves with every commit, so it is not printed here.
Recount both from the raw objects rather than trusting a number in a document:

```bash
for c in $(git rev-list origin/rh..HEAD); do
  git cat-file commit "$c" | sed -n '1,30p' | grep -q '^gpgsig' && echo signed || echo unsigned
done | sort | uniq -c
```

At the time of writing that returns 24 signed and 11 unsigned over 35 commits. A
review found the previously printed figures (20 and 11 over 31) stale for exactly
the reason this section now avoids: a printed count of a moving quantity is wrong
the moment the next commit lands. Signature policy for this branch remains an
open question for the owner, not a claim this document should be making.

## Before / after

The extraction itself is fixed and does not move: **93 files removed**, all
recoverable from `610b43f`. What moves with each rebase or report revision is
the absolute tree size, so exact per-commit counts live in
[`validation-evidence.md`](validation-evidence.md) rather than here.

| Removed | Files | Lines |
| --- | ---: | ---: |
| Numeric deployment step manifests | 66 | 2,811,048 |
| Parked RH dashboard | 26 | 20,277 |
| Dashboard workflow | 1 | 56 |
| **Total** | **93** | **2,831,381** |

Measured against the original baseline `610b43f`, the active tree went from
678 files / 3,445,736 lines to 588 files / 615,919 lines — a **−82.1%** line
reduction, and 162,472 KB → 26,688 KB on disk. After merging rh the absolute
figures are larger on both sides because rh added work; the extraction delta is
unchanged.

Against the non-binding Section 10 projection (500,000–575,000 lines,
470–590 files) the file count landed inside the range and the line count about
40,900 above it, entirely accounted for by the documented block-clock and
document-pruning de-scopes.

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

**This no longer holds, and the original wording is corrected here.** Trains 1
and 2 removed no test file: at that baseline `tests/` held 170 files on both
sides and both lanes collected identically (lean 3,244; comprehensive 4,539).

The later pass on this branch **does** remove test files — the block-clock
inventory suite and the probe package — and 339 comprehensive node identities
disappear with them. Of those, 79 were failing before removal. None of the
removals is a passing test that was deleted to make a lane greener; the exact
per-node accounting is in
[`validation-evidence.md`](validation-evidence.md) section 14, and the removed
paths are indexed in [`REMOVED.md`](REMOVED.md).

Five test files are adapted. This is more than the single change Section 4.1
anticipated, and each is listed so a reviewer can read the whole surface:

| Test file | Change | What still holds |
| --- | --- | --- |
| `test_manifest_schema.py` | Base-history corpus count assertion removed entirely (it had been `60` → `1`) | Both globs, the top-level-key assertion, the record-shape assertion, and the read-does-not-rewrite byte comparison are unchanged and run against whatever is committed. |
| `test_vault_pointer_runtime_sizes.py` | Exact runtime-size dict equality replaced by EIP-170 ceiling plus a per-contract headroom floor | The ratified 200-byte floor applies by default. Two exact-version exceptions are recorded after the VaultMigrator integration: CreditEngine at 184 bytes (RH-D026) and Teller at 51 bytes (RH-D027). Each waived contract is pinned by source sha256, immutable-free runtime-template sha256 and size, exact deployed size, and the sha256 of the complete deployed runtime at declared constructor inputs. Any identity change reopens its decision rather than silently extending the waiver. |
| `test_ledger_action_block.py` | Frozen mutant sha256 replaced by an exact ordered-diff comparison, plus a negative regression | A mutant must differ from `Ledger.vy` by exactly the declared edit; a second change, even on the same line, fails. |
| `test_collection_contract.py` | `len(ledger) == 31` census removed | Sortedness, uniqueness, prefix, ceiling, and filesystem-match all remain. |
| `test_bluechip_yield_prices_artifacts.py` | Block-clock integration assertion removed | Nothing replaces it; the coverage loss is recorded as RH-D025. |

Directory-scanning consumers were re-run rather than weakened:

| Consumer | Outcome at final |
| --- | --- |
| `test_base_profile_regression.py::test_committed_base_history_inventory_is_unchanged` | PASS — `git status` over `migration_history/base-mainnet/v1` is clean because the deletions are committed |
| `test_base_profile_regression.py::test_base_mainnet_source_and_history_are_preserved` | PASS — `history_state` is still `EXISTING` |
| `test_robinhood_blueprint.py` three-directory path census | PASS (79 tests green) |
| `test_lootbox_deployment_profiles.py::test_x1_historical_call_site_inventory_is_complete` | Pre-existing FAIL, byte-identical message at baseline and final; it scans `migration_history` only for `*.py`, of which the directory contains none. Its failure is about `migrations/robinhood-mainnet/0005_Departments.py`. |
| `test_network_profiles.py`, `test_current_manifest_promotion.py` | PASS, unchanged |

## Mock-contract consumer inventory

**All 34 `contracts/mock/` files are retained.** 33 have at least one consumer in
the retained tree; `MockSGreenPrice.vy` has none, and is kept deliberately — see
the note below this table, which also records how this inventory was wrong twice.
`scripts/export_abis.py` excludes `contracts/mock/` and `contracts/testing/`
(`DEFAULT_EXCLUDE_DIRS = ("mock", "testing")`), so the historical 52-output ABI
census at the simplification candidate was unaffected either way. The merged RH
tree later added `DefaultsRobinhoodLive`; the current post-merge ABI census is
53 outputs.

| Mock | Retained consumers (primary) |
| --- | --- |
| `MockSGreenPrice.vy` | **None in the retained tree.** Deployed on Base Sepolia v1 — see below |
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

### `MockSGreenPrice.vy` has no *current* consumer, but it was deployed

This entry has been wrong twice, in opposite directions, and the second error was
worse than the first. Both are recorded because the second one procured an owner
decision.

**First error.** The table above listed `config/block-clock-inventory.json` as
this mock's consumer and concluded all 34 were covered. That file is deleted by
this branch, so the row named a consumer that no longer exists. A review caught
it.

**Second error, and the one that matters.** The correction claimed *"No test,
script, migration, or contract has ever referenced it."* **That is false.** It was
produced by running `git grep -l MockSGreenPrice 5a664cd` — a search of one
commit's tree — and then stating the result as a fact about history. A tree at a
commit is not a history. On that false premise the owner was asked to choose
between retaining an unused orphan and deleting something never deployed, and
chose deletion.

**What is actually true**, from `git log --all -S` over `migrations/` and
`migration_history/`:

| | |
| --- | --- |
| Deployed to | Base Sepolia v1, `0xD10eD35EEcA84beEDC3e61d76db06857Aeb98Bb6` |
| Deployed by | `migrations/base-sepolia/1006_PriceDesk.py` at `385ceae` |
| Registered as | `"Mock SavingsGreen Price"` in PriceDesk, via `startAddNewAddressToRegistry` + `confirmNewAddressToRegistry` |
| Constructor arg | `SavingsGreen` at `0xA7a5bD6fAc4AfB87908Add345c5baD82FB1A2e97` |
| Appears in | 10 historical `base-sepolia/v1` step manifests (`0000`, `0001`, `1004`–`1011`) |
| Size | 87 lines |

Context that does *not* excuse the error but bounds it: `rh` itself had already
dropped both `1006_PriceDesk.py` and the `MockSGreenPrice` entry from
`base-sepolia/v1/current-manifest.json` before this branch existed — neither
removal is this branch's doing — and `v1` is superseded by `v2`. Whether
`0xD10e…Bb6` still holds code or is still registered in PriceDesk has **not**
been checked; that needs an RPC query nobody has run.

**Disposition: retained.** Presented with the corrected history on 9 August 2026,
the owner reversed the deletion. The file is restored byte-identically. It is
carried as source for a real, if obsolete, testnet deployment.

What remains true, and is all the table above should ever have claimed: **no
retained file in the current tree references it.** That is a statement about the
tree, and it is the only kind of statement a tree search can support.
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

## Artifact gates: post-merge remediation

The simplification PR deliberately left three pre-existing RH integrity
failures untouched while deployment-owned artifacts were in flight. The
follow-up repository-health remediation resolves them without changing live
state or granting deployment authority:

| Check | Condition inherited from RH | Follow-up resolution |
| --- | --- | --- |
| ABI export | `DefaultsRobinhoodLive.vy` had no committed ABI and the census still expected 52 outputs. | Regenerate the committed ABI set and bind the test to all 53 current outputs. |
| Governed contract artifacts | Source, compiler-input, creation, and runtime expectations drifted for merged contracts. | Regenerate governed expectations for Ledger, Lootbox, MissionControl, and Teller, and bind the Ledger/Lootbox profile manifests to those expectations. |
| Migration manifest safety | The retained runner lacked the in-memory typed handoff action required by the manifest safety test. | Layer the reviewed H-06 typed handoff and fail-closed guards onto the current runner while retaining the CCIP helpers used by eight migration files. Add a call-graph regression gate for every retained `migration.<method>(...)` call. |

The earlier red state and its baseline/candidate parity remain historical facts
for the cleanup PR. Generated ABIs, hashes, profiles, and migration-runner code
are repository evidence only; they do not select production constructor values,
sign a transaction, register a contract, or authorize deployment.

An initial health-remediation commit restored the historical H-06 runner blob
verbatim. That blob predated the August 7 CCIP additions and therefore removed
`deploy_solidity`, `get_solidity_contract`, `get_address_on_chain`, and
`timestamp` even though retained migrations still call them. Independent review
caught the compatibility regression before publication. This follow-up restores
all four methods, blocks `deploy_solidity` before any Foundry side effect when
H-06 manifest-v2 mode is active, and binds the live migration call graph in a
root-level lean/comprehensive test.

## Validation

Interpreter `/Users/wigglez/dev/ripe-protocol-validation-envs/rh-wave2-py312/bin/python`
(Python 3.12.0, IPython 9.8.0, pytest 8.4.2, vyper 0.4.3) on
Wigglez-MacStudio-2025, same private-cache methodology for every measurement.
Exact paths, SHA-256 values, timing metadata, and the complete failure
inventories are in [`validation-evidence.md`](validation-evidence.md).

The authoritative baseline/candidate pair ran in two **`git clone` checkouts**
rather than worktrees. A concurrent `git worktree remove`/`prune` in the source
repository cannot reach a clone, which removes the interference that damaged an
earlier attempt. Each clone's `HEAD` was re-read after every lane and recorded.

### Suites

| Lane | Baseline `610b43f` | Candidate `e74f184` |
| --- | --- | --- |
| Lean | 13 failed, 3,205 passed, 278 deselected, 1 xfailed, 25 errors — pytest 987.23s, wall 1052.96s, exit 1 | 13 failed, 3,205 passed, 278 deselected, 1 xfailed, 25 errors — pytest 962.67s, wall 1027.77s, exit 1 |
| Comprehensive | 36 failed, 4,301 passed, 143 deselected, 1 xfailed, 201 errors — pytest 1650.20s, wall 1791.01s, exit 1 | 36 failed, 4,301 passed, 143 deselected, 1 xfailed, 201 errors — pytest 1622.63s, wall 1768.99s, exit 1 |

**Normalized failure/error identity diff: zero new identities in both lanes, and
zero lost.** Lean 38 → 38, comprehensive 237 → 237, collection identical
(3,244 lean / 4,539 comprehensive).

Four independent comprehensive runs across two checkout mechanisms, three
candidate commits, and five checkouts all agree; every pair measured with a
consistent mechanism yields zero drift. The 235-vs-237 difference between
worktree and clone runs is fully diagnosed in `validation-evidence.md`: two
`test_defaults_robinhood` tests shell out to Git for historical commits that a
clone does not copy, and both pass at both commits once those objects are
restored.

Neither lane is green, at baseline or candidate. The 176 comprehensive
`test_block_clock_inventory` errors are one pre-existing cause — its session
fixture copies every path pinned by `config/block-clock-inventory.json`, and
three pinned paths do not exist at the baseline commit. This cleanup neither
fixed nor introduced any of them.

Terminal `FAILED`/`ERROR` node IDs were cross-checked against the JUnit sets. The
lean lane matches exactly, 38 = 38. The comprehensive terminal writer truncates
parametrized IDs containing spaces, so six JUnit identities map onto four
truncated terminal prefixes; those four were reconciled by prefix match rather
than exact equality, which is weaker evidence than the lean lane's exact match.

### Gates at the candidate tip and after merge

At the historical simplification candidate, every cleanup-owned gate was green
while the inherited artifact failures above remained red; the exact table is in
`validation-evidence.md`. The post-merge remediation advances ABI export parity
to 53 outputs and repairs the governed contract-artifact and in-memory migration
handoff gates. Historical candidate counts remain historical rather than being
silently rewritten as current results.

The Python workflow was **not dispatched for PR #77** because the workflow at
that time was `workflow_dispatch` only. The post-merge remediation changes the
workflow to run both lean and comprehensive lanes automatically for pull
requests and for pushes to `master` or `rh`, while preserving manual
single-lane dispatch. It checks out full history for commit-bound gates, gives
the comprehensive lane a 180-minute limit, cancels superseded PR/branch runs,
and adds a focused macOS job for the platform-gated H-06 promotion suite. No
remote CI result is claimed until the remediation PR exists and GitHub actually
runs it; macOS-local and Ubuntu CI pass/skip totals are not expected to match.

### Benchmarks (process wall time from `/usr/bin/time -p`, authoritative)

Matched pair, both sets measured in clone checkouts on an otherwise idle machine:

| Target | Baseline warm | Candidate warm | Change |
| --- | ---: | ---: | ---: |
| `tests/tokens` | 55.41s | 55.78s | +0.7% |
| `tests/data/test_mission_control.py` | 57.18s | 54.05s | −5.5% |

Cold times moved −2.0% and −1.9%. No warm regression approaches the ±10% rule.
Per-run `user`/`sys`, pytest durations, exit codes, runtime-root paths, and log
hashes are in `validation-evidence.md`.

An earlier candidate benchmark set was **discarded**: a stray retry loop that a
`pkill` failed to stop was running full suites concurrently, so it did not match
the quiet-machine baseline methodology.

### Socket-purity gate (pass/fail, not a timing benchmark)

`tests/clock/test_clock_profiles.py` with `socket.socket` patched to raise:
**57 passed** at both `610b43f` and `e74f184`. Lazy port allocation inside the
`anvil()` factory is preserved.

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
  repository-placement clause on 2026-08-07. `RH-D024 — The dashboard is
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
- **Tests depending on unreachable Git objects.** Two `test_defaults_robinhood`
  tests shell out for commits `0f79b626…` (reachable only from
  `refs/remotes/origin/rh-deploy`) and `74c4120f…` (unreachable from any ref,
  surviving on gc grace). Both fail on any fresh clone and would fail after a
  `git gc`. Pre-existing, unrelated to this cleanup, and worth a separate fix.
- **Concurrent repository activity.** The owner was working in this repository
  throughout: `rh` moved `610b43f` → `be6e4e9` and several worktrees were created
  and swept, one of which destroyed an early reference checkout mid-run. Per plan
  Section 14.2 the branch stayed bound to the exact baseline and was not rebased.
  A landing decision should account for `rh` having advanced.
