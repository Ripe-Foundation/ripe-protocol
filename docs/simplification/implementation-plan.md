# RH Codebase Simplification Implementation Plan

> **Path note (8 August 2026):** some paths cited below no longer exist in the
> active tree — the block-clock inventory, the `contracts/testing/` probes, and
> the extracted deploy manifests and review records were removed. The citations
> were accurate when written and are left intact. See
> [`REMOVED.md`](REMOVED.md) for the full index; everything is
> recoverable from git history. No production contract was modified.

- **Status:** Fresh-agent autonomous implementation handoff
- **Prepared:** 2026-08-07
- **Implementation baseline:** `rh` and `origin/rh` at `610b43f4508e85628a1362532a79d68d71ea902c`
- **Comparison baseline:** `master` at `91eda49ccd34a25090582aff0695075c4c806011`
- **Repository:** `/Users/wigglez/dev/ripe-protocol`
- **Primary objective:** Make the active contract-development tree smaller and keep the already-integrated fast test workflow intact, without changing production Vyper, live deployment tooling, deployment-record formats, or security intent.

> This is one long-running implementation task with one consolidated validation and review at the end. The three implementation trains are independently revertible recovery units, not micro-gates or review pauses.

## 0. Fresh-agent operating contract

### 0.1 Execution cadence

When the user says **“Implement `RH-CODEBASE-SIMPLIFICATION-PLAN.md` end to end”**, the implementing agent must:

1. Read this entire file before editing.
2. Create a new isolated worktree from the exact bound commit.
3. Capture the Phase 0 reference JUnit identities, representative wall-clock benchmarks, and socket-purity evidence defined in Section 5.
4. Execute Trains 1–3 continuously, lowest risk first.
5. Use cheap targeted checks while editing, but do not run the full suites or request reviews between trains.
6. Locally commit each broad train so it can be reverted independently.
7. If one train becomes unsafe, revert or omit that train, complete the others, and report it as de-scoped.
8. After all implementation is complete and locally committed, run the complete final validation matrix once.
9. Fix final-run findings, rerun affected top-level gates, and deliver one complete end-of-task review packet.

The task must not become a chain of small PRs, approval requests, or repeated full-suite runs. The one reference lean/comprehensive pair at Phase 0 exists only to bind the pre-existing failure identities; it is not a review gate. Targeted debugging during implementation is expected; candidate comprehensive tests, artifact parity, benchmarks, recovery checks, and review happen together at the end.

### 0.2 Authorized local actions

The implementation handoff authorizes the agent to:

- create an isolated `codex/` branch and worktree from the exact baseline;
- create two temporary detached validation/reference worktrees and private out-of-tree evidence/runtime directories for this task;
- edit, move, and remove files within that worktree according to this plan;
- use `git mv` for any retained file that changes location;
- generate a compact extraction manifest and final report;
- run local, credential-free tests and static checks;
- make a small number of broad local commits for the three trains and final fixes;
- make evidence-based low-risk decisions inside the explicit retention rules.

It does **not** authorize the agent to:

- push, open a PR, publish a tag, merge, deploy, or write to any remote system;
- use live secrets, production signers, or remote fork credentials;
- modify `master`, `rh`, another existing branch, or another existing worktree;
- inspect for cleanup, edit, restore, clean, stage, or commit any tracked or untracked material in the existing dirty RH worktree, including `docs/chains/rh/vault-migration/`;
- merge or cherry-pick in-flight feature/remediation branches;
- edit production Vyper or accept retained production-artifact drift;
- change `scripts/migrate.py`, `scripts/utils/migration_runner.py`, `scripts/utils/manifest_schema.py`, deployment manifest semantics, or operator CLI behavior;
- change `requirements.in`, `requirements.txt`, or the frozen dependency-security evidence;
- rewrite Git history or garbage-collect historical objects.

### 0.3 Exact starting procedure

Current controlling refs:

```text
rh/origin-rh: 610b43f4508e85628a1362532a79d68d71ea902c
master:       91eda49ccd34a25090582aff0695075c4c806011
```

Create a new worktree; do not use the dirty reference RH worktree:

```bash
git -C /Users/wigglez/dev/ripe-protocol rev-parse rh^{commit} origin/rh^{commit}
git -C /Users/wigglez/dev/ripe-protocol cat-file -e 610b43f4508e85628a1362532a79d68d71ea902c^{commit}
git -C /Users/wigglez/dev/ripe-protocol worktree add -b codex/rh-codebase-simplification /Users/wigglez/dev/ripe-protocol-rh-simplification 610b43f4508e85628a1362532a79d68d71ea902c
git -C /Users/wigglez/dev/ripe-protocol-rh-simplification status --short --branch
```

Expected new-worktree status: clean, on `codex/rh-codebase-simplification`, at the exact commit above.

The root handoff file is intentionally outside the bound RH commit. Before implementation edits, add an exact tracked copy to the new branch at `docs/simplification/implementation-plan.md` using `apply_patch`. Preserve that copy as the implementation authority; record any execution-time de-scope in the final report rather than silently rewriting the plan.

Create a separate temporary detached reference worktree at the same baseline under a task-specific `/private/tmp/rh-simplification-reference.XXXXXX` parent for Phase 0 evidence. Keep that clean reference worktree registered through final validation so Section 7 can compare the same checkout; do not use or modify the existing dirty RH worktree.

If the proposed branch/path already exists, inspect it rather than overwriting it. If unrelated, use a clear `-v2` suffix. Never delete, reset, clean, or reuse an unexpected worktree.

Do not fetch, rebase, or silently bind to a newer RH tip. If the exact baseline is unavailable, stop. Landing onto later RH is a separate integration action described in Section 14.

### 0.4 Continuation, de-scope, and hard-stop rules

Ordinary ambiguity does not stop the long run:

- If a deletion candidate has an unresolved retained consumer, retain it and continue.
- If a test’s security intent is unclear, retain the test and continue.
- If a low-value cleanup requires changing frozen requirements, production artifacts, live deployment tooling, or committed authority hashes, omit that cleanup and continue.
- If a train cannot be completed safely, revert its complete local commit train, finish the remaining trains, and describe the de-scope in the final report.

Stop and ask the user only if:

1. The exact baseline is missing or corrupt.
2. No isolated clean worktree can be created without overwriting user work.
3. A required retained test can pass only through a production Vyper or retained-artifact change.
4. Removed material cannot be recovered and hash-verified from the baseline.
5. Required validation needs a secret, deployment, remote write, or unapproved network access.
6. The task encounters an actual semantic conflict in the live operator path despite that path being out of scope.

Sandbox cache or loopback failures are environmental diagnostics, not protocol failures. The already-integrated lazy-port change should allow local Boa tests that do not request Anvil to run without binding a socket; proving that is an acceptance item.

### 0.5 Source-of-truth precedence

When goals conflict, use this order:

1. Preserve supported production behavior and retained production artifacts.
2. Preserve security invariants and committed authority/hash gates.
3. Preserve the deployment coworker’s documented commands and live operator files.
4. Preserve current test-lane behavior and dependency reproducibility.
5. Remove active-tree bulk and cruft.
6. Report achieved file/line reduction.

No numeric file or line target may override a retention rule. This plan intentionally contains no hard post-cleanup file-count or line-count gate.

### 0.6 Environment and toolchain

Use one named environment for every baseline and final measurement:

```text
Interpreter: /Users/wigglez/dev/ripe-protocol-validation-envs/rh-wave2-py312/bin/python
Python:      3.12.0
IPython:     9.8.0
Machine:     the current local Mac running this task
```

The locked environment already exists. Do not modify it during the implementation unless a missing pinned package prevents validation and the user approves the mutation.

Canonical clean-environment provisioning, if the locked environment is unavailable:

```bash
/Users/wigglez/.pyenv/versions/3.12.0/bin/python -m venv /private/tmp/ripe-rh-simplification-venv
/private/tmp/ripe-rh-simplification-venv/bin/python -m pip install -r requirements.txt
```

Dependency installation may require network approval. Do not alter requirement files to make installation easier.

For tests and benchmarks, create private task-specific runtime directories. Keep Python bytecode enabled for representative developer-performance measurements; forced `PYTHONDONTWRITEBYTECODE=1` distorts repeat-run timing. A fresh runtime root per representative target intentionally gives the first run a cold bytecode and Boa cache, while the immediate rerun measures both caches warm.

Required environment values:

```text
ETHERSCAN_API_KEY=local-placeholder
RIPE_BOA_CACHE_DIR=<private mode-0700 directory>
PYTHONPYCACHEPREFIX=<private mode-0700 directory>
XDG_CACHE_HOME=<private mode-0700 directory>
HYPOTHESIS_STORAGE_DIRECTORY=<private mode-0700 directory>
TMPDIR=<private mode-0700 directory>
```

Use a private pytest cache and basetemp. Unset RPC, private-key, mnemonic, cloud-secret, `RIPE_RH_FORK_MODE`, `RIPE_RH_FORK_MANIFEST`, and `RIPE_RH_FORK_IDENTITY_MANIFEST` environment variables for local validation. Record the interpreter version, environment path, machine identity, commit, command, cache state, pytest duration, and process wall time in every benchmark result.

### 0.7 Required final artifacts

The completed branch must contain:

- `docs/simplification/implementation-plan.md` — the exact plan used to authorize the run;
- `docs/simplification/README.md` — implementation summary, recovery instructions, before/after metrics, validation outcomes, de-scopes, and retained exceptions;
- `docs/simplification/extracted-files.tsv` — category, original path, Git mode, baseline blob ID, byte length, SHA-256, recovery commit;
- a test/invariant disposition section in the report;
- a mock-contract consumer inventory in the report;
- a retained-doc list and deleted-doc reverse-reference result;
- a migration-history retention/extraction inventory;
- a small, independently revertible local commit series for Trains 1–3 and final fixes;
- a clean committed worktree before the final validation checkout is created.

The final handoff must also provide an out-of-worktree evidence bundle containing the baseline and final lean/comprehensive JUnit XML, terminal logs, exit codes, `/usr/bin/time` results, representative benchmark logs, and socket-purity logs. Do not add those bulky raw logs/XML files back to the repository; record their absolute paths and SHA-256 values in `docs/simplification/README.md` and the final response.

No push, PR, deployment, tag, or external archive is part of this task.

## 1. Scope and outcome

The test-speed work requested by the owner is already integrated into `rh` at this baseline. This plan protects that work and delivers active-tree size and comprehension reduction; it does not promise a further speedup.

### 1.1 Target active tree

Retain:

- all supported production contracts and interfaces;
- direct contract-behavior, regression, and security-invariant tests;
- the integrated lean/comprehensive pytest lanes;
- the minimum test harness, configuration authorities, artifact checks, and operator tooling those tests require;
- all Base and Robinhood migration source files;
- current deployment manifests required by retained operator tools;
- live operator, security-gate, configuration, and test-lane documentation.

Extract from the active tip when dependency tracing permits:

- old numeric deployment-history snapshots while retaining required current manifests;
- the parked RH dashboard and dashboard workflow;
- completed evidence/plans not read by retained code or required by operators;
- fork qualification and one-time probe packages;
- the superseded vault comparison after selected invariants are retained;
- parked CCIP examples/evidence, without touching production CCIP behavior;
- the block-clock inventory/process package only if it can be removed atomically without losing direct dual-clock behavior tests.

### 1.2 Explicitly out of scope

The following are separate future tasks:

- migration-runner reduction or redesign;
- any change to `scripts/migrate.py` defaults, resume behavior, network selection, secret handling, or logging;
- manifest-schema or current-manifest format changes;
- requirement-group splitting or dependency upgrades;
- Git-history rewriting or clone-size compaction;
- production Vyper cleanup or behavior changes;
- Uniswap V2 price-source removal;
- live CI execution, CI status observation, or required-check configuration;
- integration of `instant-bond-lane`, vault-migration work, or any other active branch.

The deployment runner/schema work is excluded because it touches a live mainnet-adjacent operator path and provides little leverage against the immediate goal of a fast, understandable contract-development repository.

## 2. Current baseline and dependency trace

### 2.1 Current tree census

At `610b43f4508e85628a1362532a79d68d71ea902c`:

- RH is 336 commits ahead of `master`.
- The RH delta changes 373 files with 385,991 insertions and 2,376 deletions.
- The active tree contains 678 tracked files and 3,445,736 tracked lines.
- Fewer than 1% of RH additions are under `contracts/`.

| Area | Files | Lines | Disposition |
| --- | ---: | ---: | --- |
| `migration_history/` | 68 | 2,957,627 | Remove old step snapshots; retain current manifests required by live paths |
| `tests/` | 170 | 149,889 | Retain core behavior; extract qualification/process/one-time surfaces selectively |
| `docs/` | 149 | 129,519 | Keep explicit operator/runtime list; remove only after reverse-reference scan |
| `scripts/` | 100 | 115,027 | Retain live deployment/artifact paths; remove only proven one-time tooling |
| `config/` | 8 | 49,242 | Mostly load-bearing; do not apply a bulk generated-file rule |
| `contracts/` | 96 | 39,697 | Production plus 34 mocks and 2 testing probes |
| `migrations/` | 72 | 3,412 | Retain all; multiple files import `tests.constants` |
| `interfaces/` | 6 | 758 | Retain |
| `.github/` | 2 | 148 | Keep Python tests workflow; remove dashboard workflow with dashboard |

`scripts/abis/` contains 52 JSON files and 83,895 lines and is retained wholesale because repository ABI parity requires exactly those 52 outputs. `contracts/mock/` contains 34 files and 3,199 lines and still requires a reverse-consumer inventory.

### 2.2 Test-speed work is already integrated

`codex/rh-test-speed-integration` is not a competing branch: it is exactly current `rh`/`origin/rh` at `610b43f4508e85628a1362532a79d68d71ea902c`.

Current RH already contains:

- root `pytest.ini` with lean/comprehensive lane definitions;
- `-p no:unraisableexception` in the lean default;
- `RIPE_BOA_CACHE_DIR` support in `tests/conftest.py`;
- lazy port allocation inside the Anvil context rather than an eager `free_port` fixture;
- scoped fixture overrides for clock, deployment, deployment-profile, inventory, and probe tests;
- `.github/workflows/python-tests.yml` with manual lean/comprehensive dispatch;
- optimized Uniswap behavior tests and explicit fuzz/release/artifact/gas markers.

Do not recreate this work, invent `tests/unit`, or add a second `-m core`/`-m integration` taxonomy.

The existing selection stack is:

1. `tests/conftest.py` registers `conf_core`, `conf_mock`, `conf_utils`, `conf_env`, and `utils.clock_profiles` as root plugins.
2. `tests/conf_env.py` defines `--fork`, `--rpc`, `--anvil`, the `fork` markers, and `pytest_collection_modifyitems` with the `always` escape.
3. Root `pytest.ini` applies lean/comprehensive marker and directory selection.

Pytest 8 requires plugin/addoption registration to remain at an allowed root location. Extend the existing mechanism only when necessary; do not move plugin registration into a subtree.

The local default path does **not** start Anvil. It uses `boa.set_env(Env())` plus fast mode unless `--anvil`, a remote fork, or an RPC override is explicitly requested. The historical problem was eager socket binding; the integrated lazy-port change should now make sandboxed local tests possible.

The integrated speed evidence records a known-red default reference, not a green suite: the final reference run reported 3,205 passed, 13 failed, 25 errors, and 1 xfailed. That comparison was measured on pristine RH `2c026b0` and the rebound candidate `25b9220`; `25b9220..610b43f` is exactly one documentation-only commit modifying `docs/chains/rh/rh-test-speed-implementation-plan.md`, so the test tree at the bound baseline is identical. The aggregate counts remain useful context, but they are not a failure-identity baseline; Phase 0 must capture fresh JUnit identities at `610b43f` before editing.

### 2.3 Load-bearing couplings

These couplings control cleanup decisions.

#### A. `BluePrint.py` committed-HEAD census

`config/BluePrint.py` validates committed `HEAD` blobs and worktree bytes for:

- `tests/core/auctionHouse/test_ah_auctions.py`;
- `tests/core/auctionHouse/test_auctionhouse_stock_delivery.py`;
- `tests/core/deleverage/test_deleverage_stock_delivery.py`;
- `tests/core/deleverage/test_deleverage_swap_collateral.py`;
- `contracts/core/AuctionHouse.vy`;
- `contracts/core/Deleverage.vy`;
- `contracts/vaults/SimpleErc20.vy`;
- `config/contract-artifact-expectations.json` and bound artifact identities.

Consequences:

- retain the four tests unchanged unless a separately authorized authority update occurs;
- never validate this census against an uncommitted candidate worktree;
- all cleanup work must be locally committed before the Phase 7 clean-checkout run;
- do not update the bound hashes merely to make cleanup pass.

#### B. Migrations import the test package

Base and Robinhood migrations import `ZERO_ADDRESS`, `EIGHTEEN_DECIMALS`, and related values from `tests.constants`. `scripts/params/params_utils.py` does the same.

Consequences:

- retain `tests/constants.py` and the repository/test Python path behavior;
- do not rename the `tests` package or move constants during this cleanup;
- do not assume deployment code is independent of the test tree.

#### C. Frozen dependency-security gate

`tests/deployment/test_dependency_gate.py`:

- imports the selected direct/transitive packages;
- freezes SHA-256 values for `requirements.in` and `requirements.txt`;
- reads `docs/chains/rh/evidence/dependency-security-gate.md` at runtime;
- validates pinned versions, retained exceptions, and evidence text.

Consequences:

- retain all three files;
- do not split or edit requirements in this task;
- run this test in the named locked environment where IPython is present;
- never delete the evidence document as “completed evidence.”

#### D. Artifact-check system

The retained system includes:

- `config/contract-artifact-expectations.json`;
- `scripts/check_contract_artifacts.py`;
- `scripts/update_contract_artifact_expectations.py`;
- `scripts/export_abis.py`;
- `tests/inventory/test_contract_artifacts.py`;
- `tests/inventory/test_bluechip_yield_prices_artifacts.py`;
- `tests/deployment/test_abi_export.py`;
- every committed ABI referenced by the expectations file or retained tests/scripts.

`config/BluePrint.py`, proposal builders, block-clock inventory, and direct contract tests also reference artifact paths.

Consequences:

- `config/contract-artifact-expectations.json` is a required generated artifact and invalidates any “zero generated lines” target;
- do not regenerate or rewrite expectations during cleanup;
- retain all 52 checked-in ABI JSON files and verify repository ABI parity;
- retain Uniswap and its artifact record in this task.

#### E. Migration-runner importers and disposition

| Importer/reference | Disposition in this task |
| --- | --- |
| `scripts/migrate.py` → `MigrationRunner` | Retain unchanged; live operator path |
| `scripts/check_deployment.py` → `build_robinhood_plan` | Retain unchanged; invoked three times in the operator quickstart |
| `tests/deployment/test_secret_handling.py` → `MigrationError` | Retain |
| `config/robinhood_blueprint.py` static component census | Retain; blueprint is load-bearing |
| `scripts/check_block_clock_inventory.py` | Remove only with the complete block-clock process package |
| `tests/inventory/test_block_clock_inventory.py` | Remove only with the complete block-clock process package |
| internal references in `migration_runner.py` | Retain; runner is out of scope |

Do not remove `build_robinhood_plan` or reduce the runner in this cleanup.

#### F. Manifest schema and deployment records

`scripts/utils/manifest_schema.py` is 3,665 lines and is consumed by the runner, fork qualification, `tests/deployment/test_manifest_schema.py`, and `tests/deployment/test_current_manifest_promotion.py`.

The schema and current-manifest format are out of scope. Deleting old checked-in history does not authorize changing either.

Retain at minimum:

- `migration_history/base-mainnet/v1/current-manifest.json`;
- `migration_history/robinhood-mainnet/v1/current-manifest.json`;
- the directory paths required by `config/network_profiles.py` and live scripts.

In `tests/deployment/test_manifest_schema.py`, adapt only the corpus-iteration/count assertions around baseline lines 1265 and 1280 after step manifests are extracted. Do not modify schema-validation logic. Keep all current-manifest promotion tests intact.

#### G. Documentation is sometimes executable input

Before deleting any document, run a baseline-bound reverse-reference search from `tests/`, `scripts/`, `config/`, `migrations/`, `.github/`, and retained docs. Search literal `docs/` paths and computed `Path` joins. Any document read by retained code/tests is retained.

#### H. `migration_history/` consumers

The intended Train 2 extraction retains 2 `current-manifest.json` files totaling 146,579 lines and removes 66 numeric step manifests totaling 2,811,048 lines. The following 13 direct/static consumers at the bound baseline must each receive the listed disposition:

| Consumer | Coupling type | Disposition |
| --- | --- | --- |
| `tests/deployment/test_base_profile_regression.py` | Current-manifest and configured-directory regression | Retain; do not change operator/profile semantics |
| `tests/deployment/test_manifest_schema.py` | **Directory-iterating:** globs every Base `*.json` at baseline lines 1265/1280; also tests current manifests | Retain; adapt only those corpus iteration/count assertions |
| `tests/deployment/test_network_profiles.py` | Current-manifest path | Retain unchanged |
| `tests/deployment/test_robinhood_blueprint.py` | Current-manifest input plus three-directory static path census | Retain the census; numeric step-file removal does not authorize path changes |
| `tests/inventory/test_block_clock_inventory.py` | Directory-scanning policy | Remove only with the atomic block-clock process package |
| `tests/deployment_profiles/test_lootbox_deployment_profiles.py` | Directory-root policy scan | Retain and rerun; do not weaken the scan to accommodate deletion |
| `scripts/verify_blockscout.py` | Robinhood current-manifest only | Retain |
| `scripts/migrate.py` | Operational history root | Retain unchanged; live CLI is out of scope |
| `scripts/check_block_clock_inventory.py` | Directory-scanning policy | Remove only with the atomic block-clock process package |
| `scripts/utils/migration_runner.py` | Operational history directory; writes step and current manifests | Retain unchanged; old checked-in extraction does not change future runner behavior |
| `config/network_profiles.py` | Declares Base/RH-mainnet/RH-testnet history directories | Retain all declarations unchanged |
| `config/robinhood_blueprint.py` | Static current-manifest and history-directory rows | Retain unchanged |
| `config/block-clock-inventory.json` | Directory-scanning policy and exclusions | Remove only with the atomic block-clock process package |

`scripts/console.py` is an indirect live consumer: it resolves `paths.history_dir / "current-manifest.json"` through `config/network_profiles.py`. It remains retained under the network-profile/current-manifest disposition above.

`migration_history/robinhood-testnet/v1` is declared by `config/network_profiles.py` and asserted by `tests/deployment/test_robinhood_blueprint.py`, but it does not exist at the bound baseline. The final dangling-path scan must treat this as an intentional declared-but-absent future path: do not create it, delete its declarations, or report it as cleanup breakage.

### 2.4 Correct deployment CLI defect inventory

The current CLI declares `--start-timestamp`/`--start` with the string default `"0"`. Therefore `_migrations()` takes the explicit-start branch and `_latest_manifest_timestamp()` is unreachable from the normal CLI. The `int("current")` behavior is real dead code from the operator’s current path and is not the cleanup priority.

The actual operator defects are already recorded in `docs/chains/rh/robinhood-deployment-support-specification.md`, including:

- default invocation replays migrations from `0000` rather than resuming;
- `--blueprint` silently defaults to Base;
- environment/default help text conflicts with behavior;
- RPC URLs are logged in full;
- further network, signer, chain-ID, finality, and fail-closed deficiencies.

Decision: **all of these defects are out of scope for this cleanup because correcting them changes live operator behavior.** Retain the support specification and flag a separate deployment-owner task in the final report. Do not preserve the bugs as approved semantics, but do not modify them here.

## 3. Explicit retention list

### 3.1 Root and toolchain

Retain:

- `.python-version`;
- `LICENSE.md`;
- `README.md`;
- `pytest.ini`;
- `requirements.in` and `requirements.txt`;
- `.github/workflows/python-tests.yml`;
- repository `.gitignore` entries required by the retained workflow.

### 3.2 Configuration

Retain unless a reverse trace conclusively proves otherwise:

- `config/BluePrint.py`;
- `config/network_profiles.py`;
- `config/robinhood_launch.py`;
- `config/robinhood_blueprint.py`;
- `config/robinhood-parameters.json`;
- `config/robinhood-reward-launch-plan.json`;
- `config/contract-artifact-expectations.json`.

`config/block-clock-inventory.json` may leave only as part of the atomic block-clock process subpackage described in Train 2.

### 3.3 Test harness

Retain:

- `tests/conftest.py`;
- every `tests/conf_*.py` file;
- `tests/constants.py`;
- `tests/utils/clock_profiles.py`;
- root and subtree `conftest.py` files required by the integrated lane design;
- direct behavior/security tests and all BluePrint-bound tests.

Do not create `tests/unit`, `tests/contracts`, or `tests/integration` in this cleanup. Candidate pure/process tests include Python-side config tests, `tests/deployment/test_network_profiles.py`, `tests/deployment_profiles/`, and `tests/clock/test_clock_profiles.py`, but they should remain in their current paths with scoped fixture overrides and existing markers.

### 3.4 Deployment and artifact tooling

Retain:

- all `migrations/` source files;
- `scripts/migrate.py`;
- `scripts/check_deployment.py`;
- `scripts/utils/migration_runner.py`;
- `scripts/utils/manifest_schema.py`;
- required deploy/config/account/manifest helpers;
- artifact checker/updater/exporter and all 52 checked-in ABIs;
- current Base and Robinhood manifests.

### 3.5 Unconditional document keep-list

Retain these even if they look like plans/evidence:

- `docs/chains/rh/component-matrix.md`;
- `docs/chains/rh/current-owner-priorities.md`;
- `docs/chains/rh/decision-register.md`;
- `docs/chains/rh/deployment-owner-quickstart.md`;
- `docs/chains/rh/deployment-owner-readiness.md`;
- `docs/chains/rh/robinhood-deployment-support-specification.md`;
- `docs/chains/rh/evidence/dependency-security-gate.md`;
- `docs/chains/rh/rh-test-speed-implementation-plan.md`;
- `docs/chains/rh/reward-launch-qualification.md`;
- `docs/chains/rh/shared-block-clock-specification.md`;
- the current files under `docs/chains/rh/smart-contract-changes/` (15 tracked files at the bound baseline).

Add any additional runtime/operator document discovered by the required reverse-reference scan. The keep-list is a minimum, not permission to delete everything else blindly.

### 3.6 Mock contracts

Inventory all 34 `contracts/mock/` files against retained tests and scripts. Keep every mock with a retained consumer. Remove a mock only when all of its consumers are extracted in the same train and the extraction report records the relationship.

Uniswap mocks stay because Uniswap removal is out of scope. Probe-only mocks may leave with the complete probe package.

## 4. Safe extraction candidates

### 4.1 Deployment-history snapshots

Keep current manifests and live directory structure. Record and remove old numeric step manifests after:

- generating path/mode/blob/byte/SHA-256 entries;
- verifying recovery from baseline `610b43f4508e85628a1362532a79d68d71ea902c`;
- identifying all retained current-manifest consumers;
- adapting historical-count/corpus tests without changing schema behavior;
- updating live documentation that states active-tree step-manifest counts.

This is the largest safe reduction and does not require a manifest-schema rewrite.

Apply the consumer dispositions in Section 2.3H. In `tests/deployment/test_manifest_schema.py`, only the two Base-history corpus-iteration/count assertions around baseline lines 1265/1280 may change; schema-validation behavior and current-manifest promotion remain protected. Preserve the declared-but-absent `migration_history/robinhood-testnet/v1` profile path without creating the directory.

### 4.2 Dashboard

Remove together:

- `docs/chains/rh/dashboard/`;
- `docs/chains/rh/status.yaml` if no retained operator/runtime consumer remains;
- `.github/workflows/rh-handoff-dashboard.yml`;
- dashboard-only documentation references.

Retain `.github/workflows/python-tests.yml`.

### 4.3 Completed documents and evidence

Delete only documents that are all of:

- not in the unconditional keep-list;
- not read by code/tests;
- not referenced as current operator/security/configuration authority;
- completed or superseded;
- recoverable and recorded in the extraction manifest.

### 4.4 Generated ABIs — retained wholesale

Do not spend Train 2 inventory time looking for removable ABI JSON files. `tests/deployment/test_abi_export.py` verifies repository output parity and asserts exactly 52 exports from `contracts/`; the bound tree has 52 checked-in ABI files. Retain the directory wholesale and run the parity test at final validation.

`scripts/export_abis.py` excludes `contracts/mock/` and `contracts/testing/` through `DEFAULT_EXCLUDE_DIRS = ("mock", "testing")`. Therefore permitted probe-only testing-contract or unused-mock removal does not change the 52-output ABI census; do not rewrite the ABI test or outputs in response.

### 4.5 Block-clock process package

Evaluate atomically:

- `config/block-clock-inventory.json`;
- `scripts/check_block_clock_inventory.py`;
- `tests/inventory/test_block_clock_inventory.py`;
- completed inventory-generation evidence/docs.

The three code/config files above total 23,184 lines at the bound baseline. This is a conditional reduction, not authority to remove the retained `docs/chains/rh/shared-block-clock-specification.md` or direct clock behavior tests.

Retain direct dual-clock behavior in `tests/clock/` and `tests/utils/clock_profiles.py`. If the process package has any retained runtime/security consumer that cannot be decoupled without touching live tooling, revert this subpackage and report it as de-scoped.

`tests/inventory/` survives this cleanup: retain `tests/inventory/conftest.py`, `tests/inventory/test_contract_artifacts.py`, and `tests/inventory/test_bluechip_yield_prices_artifacts.py`. Do not misread this package as permission to delete the entire directory.

### 4.6 Parked/one-time surfaces

Candidates:

- `contracts/testing/`, `scripts/probes/`, and `tests/probes/` as one probe package;
- `tests/deployment/fork/` plus fork-only evidence, after deterministic local invariants are mapped;
- `tests/vaults/test_stock_token_vault_comparison.py`, after selected Simple-vault invariants are mapped or ported;
- parked CCIP examples and evidence under `docs/chains/rh/examples/` and related CCIP planning docs.

Retain production CCIP behavior. Retain Uniswap source, mocks, behavior tests, artifacts, and artifact expectations in this task.

## 5. Wall-clock performance contract

### 5.1 Authoritative metric

Process wall time from `/usr/bin/time -p` field `real` is authoritative. Pytest’s reported duration is supplementary because teardown/garbage-collection overhead can be invisible to pytest.

The benchmark machine is the current local Mac, using only the locked Python 3.12 environment in Section 0.6. Baseline and final comparisons must run on that machine, in the same agent session, with the same environment and matching cache methodology.

### 5.2 Exact Phase 0 evidence commands

Before editing, run all Phase 0 commands from the temporary clean detached reference worktree created in Section 0.3 at `610b43f4508e85628a1362532a79d68d71ea902c`. This is evidence capture, not an implementation/review gate.

#### A. Full-suite failure-identity baseline

The checked-in speed document contains aggregate counts but not the 13 failing and 25 erroring identities. Capture both lanes now and keep their JUnit XML outside the worktree:

```bash
PY=/Users/wigglez/dev/ripe-protocol-validation-envs/rh-wave2-py312/bin/python
baseline_evidence_root=$(mktemp -d /private/tmp/rh-simplification-baseline.XXXXXX)
chmod 700 "$baseline_evidence_root"
mkdir -p "$baseline_evidence_root/boa" "$baseline_evidence_root/pycache" "$baseline_evidence_root/xdg" "$baseline_evidence_root/hypothesis" "$baseline_evidence_root/tmp" "$baseline_evidence_root/pytest-cache" "$baseline_evidence_root/basetemp-lean" "$baseline_evidence_root/basetemp-comprehensive"
chmod -R 700 "$baseline_evidence_root"
export ETHERSCAN_API_KEY=local-placeholder
export RIPE_BOA_CACHE_DIR="$baseline_evidence_root/boa"
export PYTHONPYCACHEPREFIX="$baseline_evidence_root/pycache"
export XDG_CACHE_HOME="$baseline_evidence_root/xdg"
export HYPOTHESIS_STORAGE_DIRECTORY="$baseline_evidence_root/hypothesis"
export TMPDIR="$baseline_evidence_root/tmp"
unset WEB3_ALCHEMY_API_KEY ALCHEMY_API_KEY ETH_RPC_URL BASE_RPC_URL RPC_URL WEB3_PROVIDER_URI PRIVATE_KEY MNEMONIC AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY
unset RIPE_RH_FORK_MODE RIPE_RH_FORK_MANIFEST RIPE_RH_FORK_IDENTITY_MANIFEST

(
  set +e
  /usr/bin/time -p "$PY" -m pytest -o cache_dir="$baseline_evidence_root/pytest-cache" --basetemp="$baseline_evidence_root/basetemp-lean" --junitxml="$baseline_evidence_root/baseline-lean.xml" -q >"$baseline_evidence_root/baseline-lean.log" 2>&1
  baseline_lean_status=$?
  /usr/bin/time -p "$PY" -m pytest -o addopts='' -o cache_dir="$baseline_evidence_root/pytest-cache" --basetemp="$baseline_evidence_root/basetemp-comprehensive" --junitxml="$baseline_evidence_root/baseline-comprehensive.xml" -q >"$baseline_evidence_root/baseline-comprehensive.log" 2>&1
  baseline_comprehensive_status=$?
  printf 'baseline_lean_status=%s baseline_comprehensive_status=%s\n' "$baseline_lean_status" "$baseline_comprehensive_status"
)
```

Record both exit codes immediately. Verify both XML files parse, preserve the terminal logs, and record SHA-256 values for all four files. Derive a sorted baseline failure/error identity set for each lane from JUnit `(classname, name)` plus `file` for collection errors, and cross-check it against the terminal summary node IDs. Do not treat the known nonzero exits as a reason to fix unrelated baseline failures.

The full-suite wall times are capacity-planning context, not representative benchmark inputs. Reusing the Phase 0 suite cache between lean and comprehensive is permitted because the purpose here is failure identity, not cold/warm performance.

#### B. Representative cold/warm benchmarks

Only `tests/tokens` and `tests/data/test_mission_control.py` are performance benchmarks. This loop deliberately creates a fresh private runtime root for **each** target, then reuses that target’s root for its immediate warm rerun:

```bash
PY=/Users/wigglez/dev/ripe-protocol-validation-envs/rh-wave2-py312/bin/python
for target in tests/tokens tests/data/test_mission_control.py; do
  benchmark_root=$(mktemp -d /private/tmp/rh-simplification-benchmark.XXXXXX)
  chmod 700 "$benchmark_root"
  mkdir -p "$benchmark_root/boa" "$benchmark_root/pycache" "$benchmark_root/xdg" "$benchmark_root/hypothesis" "$benchmark_root/tmp" "$benchmark_root/pytest-cache" "$benchmark_root/basetemp"
  chmod -R 700 "$benchmark_root"
  export ETHERSCAN_API_KEY=local-placeholder
  export RIPE_BOA_CACHE_DIR="$benchmark_root/boa"
  export PYTHONPYCACHEPREFIX="$benchmark_root/pycache"
  export XDG_CACHE_HOME="$benchmark_root/xdg"
  export HYPOTHESIS_STORAGE_DIRECTORY="$benchmark_root/hypothesis"
  export TMPDIR="$benchmark_root/tmp"
  unset WEB3_ALCHEMY_API_KEY ALCHEMY_API_KEY ETH_RPC_URL BASE_RPC_URL RPC_URL WEB3_PROVIDER_URI PRIVATE_KEY MNEMONIC AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY
  unset RIPE_RH_FORK_MODE RIPE_RH_FORK_MANIFEST RIPE_RH_FORK_IDENTITY_MANIFEST

  (
    set +e
    /usr/bin/time -p "$PY" -m pytest -o cache_dir="$benchmark_root/pytest-cache" --basetemp="$benchmark_root/basetemp" "$target" >"$benchmark_root/cold.log" 2>&1
    cold_status=$?
    /usr/bin/time -p "$PY" -m pytest -o cache_dir="$benchmark_root/pytest-cache" --basetemp="$benchmark_root/basetemp" "$target" >"$benchmark_root/warm.log" 2>&1
    warm_status=$?
    printf 'target=%s cold_status=%s warm_status=%s root=%s\n' "$target" "$cold_status" "$warm_status" "$benchmark_root"
  )
done
```

For each target, record the target, runtime-root path, cold/warm exit status, pytest duration, and `/usr/bin/time` `real`, `user`, and `sys`. The fresh per-target `PYTHONPYCACHEPREFIX` intentionally makes bytecode cold on the first run; the immediate second run measures Python bytecode and Boa artifacts warm. Do not substitute a different file, share a cache across targets, compare against a baseline measured after cleanup, or use pytest’s number as the headline result.

#### C. Socket-purity gate

`tests/clock/test_clock_profiles.py` is a 57-test purity gate, not a benchmark: its sub-second test work makes a 10% timing threshold meaningless. Give it its own fresh private runtime root:

```bash
PY=/Users/wigglez/dev/ripe-protocol-validation-envs/rh-wave2-py312/bin/python
purity_root=$(mktemp -d /private/tmp/rh-simplification-purity.XXXXXX)
chmod 700 "$purity_root"
mkdir -p "$purity_root/boa" "$purity_root/pycache" "$purity_root/xdg" "$purity_root/hypothesis" "$purity_root/tmp" "$purity_root/pytest-cache" "$purity_root/basetemp"
chmod -R 700 "$purity_root"
export ETHERSCAN_API_KEY=local-placeholder
export RIPE_BOA_CACHE_DIR="$purity_root/boa"
export PYTHONPYCACHEPREFIX="$purity_root/pycache"
export XDG_CACHE_HOME="$purity_root/xdg"
export HYPOTHESIS_STORAGE_DIRECTORY="$purity_root/hypothesis"
export TMPDIR="$purity_root/tmp"
export PURITY_PYTEST_CACHE="$purity_root/pytest-cache"
export PURITY_BASETEMP="$purity_root/basetemp"
unset WEB3_ALCHEMY_API_KEY ALCHEMY_API_KEY ETH_RPC_URL BASE_RPC_URL RPC_URL WEB3_PROVIDER_URI PRIVATE_KEY MNEMONIC AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY
unset RIPE_RH_FORK_MODE RIPE_RH_FORK_MANIFEST RIPE_RH_FORK_IDENTITY_MANIFEST
/usr/bin/time -p "$PY" -c 'import os, socket, pytest; from unittest.mock import patch; patch.object(socket, "socket", side_effect=AssertionError("socket forbidden")).start(); raise SystemExit(pytest.main(["-q", "-o", "cache_dir=" + os.environ["PURITY_PYTEST_CACHE"], "--basetemp=" + os.environ["PURITY_BASETEMP"], "tests/clock/test_clock_profiles.py"]))'
```

All 57 selected tests must pass with `socket.socket` blocked, proving that this pure subtree neither opens a socket nor deploys the full protocol graph. Record pass/fail and the exact command, but exclude its wall time from the ±10% performance rule.

### 5.3 Existing high-leverage fixes to preserve

The baseline already includes the two high-leverage changes:

- lean lane disables `unraisableexception`;
- `RIPE_BOA_CACHE_DIR` wires Titanoboa compilation caching.

It also includes lazy socket allocation and optimized Uniswap setup. Train 1 verifies and preserves them; it does not implement a parallel test framework.

### 5.4 Final timing acceptance

At the final branch tip, repeat the exact cold/warm commands with matching cache methodology.

Acceptance:

- no representative warm wall-clock regression greater than 10% without an explained, owner-relevant reason;
- sandboxed local clock tests bind no socket;
- cache reuse remains effective and is reported explicitly;
- final report includes both pytest and process-wall numbers;
- the purity gate passes but is not treated as a timing benchmark.

The cleanup’s primary speed obligation is not to regress the integrated speed lane. Further fixture optimization is allowed only when dependency tracing proves it low risk and it remains inside Train 1.

## 6. Three independently revertible implementation trains

The agent runs these continuously and does not request review between them.

### Train 1 — Preserve and verify the integrated speed foundation

Scope:

- add the exact tracked plan copy at `docs/simplification/implementation-plan.md`;
- capture the Phase 0 lean/comprehensive JUnit identity baseline, representative cold/warm wall baselines, and socket-purity result;
- verify `pytest.ini`, current markers, `--fork`, root plugin registration, Boa cache wiring, and lazy port behavior;
- verify both `python -m pytest --collect-only -q` and bare `pytest --collect-only -q` work in the locked environment;
- preserve existing lane classifications and subtree fixture overrides;
- add only narrowly proven fixture overrides if a retained pure/process test still deploys the global graph unnecessarily;
- preserve `.github/workflows/python-tests.yml`;
- validate the workflow YAML syntax and ensure it references only retained paths and commands.

CI limitation:

The implementation branch is not pushed, so the agent cannot observe a green GitHub Actions run. Acceptance is limited to syntactic validity, retained-path/command validity, pinned action references, and successful execution of the equivalent local commands. Do not claim CI passed.

Forbidden in this train:

- new marker taxonomy;
- new `tests/unit` hierarchy;
- pytest plugin relocation;
- requirement changes;
- production contract edits;
- broad fixture rearchitecture without a measured dependency trace.

Commit as one broad, independently revertible speed-foundation train if changes are necessary. If current RH already satisfies the train, record a no-change verification and proceed.

### Train 2 — Bulk extraction with load-bearing retention

Scope:

- create `docs/simplification/extracted-files.tsv` before deletion;
- remove old deployment step manifests while retaining current manifests and live directory structure;
- update only historical-corpus/count tests and docs needed to reflect Git-backed recovery;
- remove the dashboard and dashboard workflow;
- prune completed documents only after the required keep-list and reverse-reference scan;
- retain all 52 ABIs and verify their deterministic parity rather than inventorying them for removal;
- attempt the block-clock process-package extraction atomically;
- add concise recovery instructions.

If this train removes an entire directory named by a root `pytest.ini` `--ignore` entry, remove that stale `--ignore` entry in the same commit. This is the only authorized `pytest.ini` maintenance outside Train 1. Do not remove `--ignore=tests/inventory`: that directory and its artifact tests survive even if the block-clock inventory test leaves.

Recovery source:

Every extracted path must recover from commit `610b43f4508e85628a1362532a79d68d71ea902c`. Do not duplicate extracted bulk under a new in-repository archive directory.

Do not change:

- manifest schema or current-manifest format;
- migration runner, CLI, planning API, or operator semantics;
- artifact expectation identities;
- frozen requirements/dependency evidence.

Use `git mv` if a retained file is relocated. Otherwise prefer explicit deletions plus the extraction manifest rather than copy-and-delete moves that obscure review.

Commit this as one broad extraction train. If a subpackage cannot be removed safely, restore that subpackage before committing and report the de-scope.

### Train 3 — Parked and one-time surface retirement

Scope:

- remove the complete probe package after confirming production loading still excludes `contracts/testing`;
- remove fork qualification after mapping deterministic retained invariants;
- retire the vault comparison after mapping/porting selected Simple-vault invariants;
- remove parked CCIP examples/evidence while retaining production behavior;
- remove mocks only when every consumer leaves in the same train;
- remove any additional one-time script only after import, CLI, CI, docs, and operator-command searches return no retained consumer.

If this train removes an entire directory named by a root `pytest.ini` `--ignore` entry, remove that stale `--ignore` entry in the same commit. In particular, remove `--ignore=tests/probes` if and only if `tests/probes/` is removed completely. Do not otherwise redesign the lane configuration.

Explicit retention:

- Uniswap V2 source, mocks, tests, ABI, and artifact expectations;
- all production contracts;
- every mock used by a retained behavior test;
- live deployment/operator code and docs.

Commit this as one broad, independently revertible parked-surface train. Revert unsafe subpackages and finish the rest.

## 7. Consolidated final validation and review

Do not start this section until all implementation trains are complete and all intended changes are locally committed. The clean validation checkout and the BluePrint HEAD census require committed state.

### 7.1 Clean checkouts

- Create a temporary detached clean validation worktree at the completed, committed branch tip.
- Reuse the untouched temporary detached reference worktree created for Phase 0 at `610b43f4508e85628a1362532a79d68d71ea902c`; if an interruption removed it, recreate it at that exact commit and record the replacement.
- Use the same locked interpreter and private cache methodology for both.
- Confirm no generated/untracked files contaminate either measurement.

Ten worktrees were already registered when this plan was prepared. Do not clean, prune, or reuse any of them. Create task-specific parents with `mktemp -d /private/tmp/rh-simplification-validation.XXXXXX` and add the detached worktrees beneath those parents. After final evidence is captured, verify both task-created checkouts are clean, remove only those two with `git worktree remove`, and leave every pre-existing worktree untouched. If either task-created worktree is dirty, retain it and report the path rather than forcing removal.

### 7.2 Static and dependency checks

- `git diff --check`;
- full status and untracked-file inventory;
- YAML parse of `.github/workflows/python-tests.yml`;
- retained-path and command checks for the workflow, without claiming remote execution;
- searches for dangling deleted paths/imports/docs;
- an explicit exception for the intentional declared-but-absent `migration_history/robinhood-testnet/v1` path in Section 2.3H;
- full document runtime-reference scan;
- full mock consumer inventory and exact 52-output ABI parity check;
- extraction-manifest format/hash checks;
- representative and boundary-file baseline recovery checks;
- review with `git diff --find-renames=50% --stat`, `--summary`, and the complete diff.

### 7.3 Authority and artifact checks

Run from the clean committed validation checkout:

- BluePrint/source-authority validation, including the HEAD-bound stock M4 census;
- `scripts/check_contract_artifacts.py`;
- retained artifact inventory tests;
- dependency-security gate in the locked environment;
- current-manifest schema and promotion tests;
- network-profile and deployment-support static tests;
- migration import/collection smoke proving `tests.constants` remains available.

No retained production artifact may drift. No expectation/authority hash may be refreshed merely to pass.

### 7.4 Full test runs at the end

Run and retain full logs for:

```bash
PY=/Users/wigglez/dev/ripe-protocol-validation-envs/rh-wave2-py312/bin/python
final_evidence_root=$(mktemp -d /private/tmp/rh-simplification-final.XXXXXX)
chmod 700 "$final_evidence_root"
mkdir -p "$final_evidence_root/boa" "$final_evidence_root/pycache" "$final_evidence_root/xdg" "$final_evidence_root/hypothesis" "$final_evidence_root/tmp" "$final_evidence_root/pytest-cache" "$final_evidence_root/basetemp-lean" "$final_evidence_root/basetemp-comprehensive"
chmod -R 700 "$final_evidence_root"
export ETHERSCAN_API_KEY=local-placeholder
export RIPE_BOA_CACHE_DIR="$final_evidence_root/boa"
export PYTHONPYCACHEPREFIX="$final_evidence_root/pycache"
export XDG_CACHE_HOME="$final_evidence_root/xdg"
export HYPOTHESIS_STORAGE_DIRECTORY="$final_evidence_root/hypothesis"
export TMPDIR="$final_evidence_root/tmp"
unset WEB3_ALCHEMY_API_KEY ALCHEMY_API_KEY ETH_RPC_URL BASE_RPC_URL RPC_URL WEB3_PROVIDER_URI PRIVATE_KEY MNEMONIC AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY
unset RIPE_RH_FORK_MODE RIPE_RH_FORK_MANIFEST RIPE_RH_FORK_IDENTITY_MANIFEST

(
  set +e
  # Lean default lane.
  /usr/bin/time -p "$PY" -m pytest -o cache_dir="$final_evidence_root/pytest-cache" --basetemp="$final_evidence_root/basetemp-lean" --junitxml="$final_evidence_root/final-lean.xml" -q >"$final_evidence_root/final-lean.log" 2>&1
  final_lean_status=$?

  # Comprehensive local lane. tests/deployment/fork is collected here. Remote
  # fork work remains disabled because RIPE_RH_FORK_MODE is unset (default:
  # disabled), both external-manifest variables are unset, and its autouse safety
  # fixture blocks external networking in disabled mode.
  /usr/bin/time -p "$PY" -m pytest -o addopts='' -o cache_dir="$final_evidence_root/pytest-cache" --basetemp="$final_evidence_root/basetemp-comprehensive" --junitxml="$final_evidence_root/final-comprehensive.xml" -q >"$final_evidence_root/final-comprehensive.log" 2>&1
  final_comprehensive_status=$?
  printf 'final_lean_status=%s final_comprehensive_status=%s\n' "$final_lean_status" "$final_comprehensive_status"
)
```

Also run any extracted/mapped targeted invariant suites needed to prove their replacements.

Budget approximately 13 wall minutes for each lean run and at least 15 wall minutes for each comprehensive run on the current machine. Phase 0 plus final validation therefore requires at least four long suite executions; allow roughly 60–90 minutes or more of suite wall time before any evidence-changing rerun. These are planning estimates, not pass criteria.

Acceptance is:

- complete runs were attempted from the clean committed tip;
- both final JUnit files parse and their logs, exit codes, paths, and SHA-256 values are recorded;
- for each lane, `final failure/error identities - Phase 0 baseline failure/error identities` is empty after normalization and terminal-summary cross-check;
- removed/renamed collected identities are fully explained by the test/invariant disposition map;
- every pre-existing failure/error is listed honestly;
- all newly added/modified targeted tests pass;
- remote/fork/secret-dependent tests not run are enumerated precisely;
- no suite is called green if it is not green.

### 7.5 Final performance comparison

Repeat the exact two-target Section 5 cold/warm procedure with one new private runtime root per target and compare baseline/final process wall time. Repeat the separate 57-test socket-purity gate as pass/fail evidence, not as a timing comparison. The full candidate lean wall measurement occurs only in Section 7.4 at this end stage.

### 7.6 Comprehensive review

Review the entire branch for:

- accidental live operator-path changes;
- missing docs/runbooks;
- broken dependency/hash gates;
- artifact drift;
- stale imports/path references;
- deleted security intent;
- unsupported-network regressions;
- accidental generated files;
- unreadable delete/add pairs that should have used `git mv`;
- conflicts with the explicit keep-list.

Fix introduced findings, commit final fixes, and rerun every top-level gate whose evidence changed.

## 8. Definition of done

The branch is ready for end review when:

- all three trains are complete or explicitly de-scoped and independently revertible;
- the active tree is materially smaller, with before/after counts reported but no retention rule violated for a numeric target;
- old history/evidence is recoverable from the exact baseline;
- current manifests and live deployment paths remain unchanged;
- the integrated lean/comprehensive test system remains intact;
- named wall-clock benchmarks use the same machine/environment/methodology;
- Phase 0 and final JUnit identity sets are preserved in the external evidence bundle and compared lane by lane;
- full lean and comprehensive local runs were performed at the end;
- no new unexplained failure/error node IDs exist;
- retained production artifacts and authority/hash gates are unchanged;
- CI workflow syntax/paths are valid, with no unsupported claim that CI ran;
- live operator docs and every runtime-read document remain;
- the final report records achieved reduction, timings, tests, de-scopes, risks, and exact next action;
- the implementation worktree is clean and no remote mutation occurred.

## 9. Effort expectation

This is a multi-day long-running task, not a multi-hour cleanup.

Planning range on the current machine/environment:

- Train 1 verification and narrow fixes: approximately 0.5–1 agent-day;
- Train 2 dependency trace and bulk extraction: approximately 1–2 agent-days;
- Train 3 invariant mapping and parked-surface retirement: approximately 1–2 agent-days;
- final full-suite runs, review, fixes, and reruns: approximately 0.5–1.5 agent-days.

Expected total: roughly 3–6 focused agent-days, depending on pre-existing suite failures and how much of the conditional block-clock and parked surfaces can be removed. This estimate is context, not a deadline or authority to skip final validation.

The two Phase 0 and two final long-suite runs alone should be budgeted at roughly 60–90 wall minutes or more, before evidence-changing reruns. Train 2 carries well over 95% of the projected line-count reduction because of the numeric manifest snapshots. If external time pressure forces a de-scope, prioritize completing Train 2 safely; do not use time pressure to skip its consumer trace, recovery manifest, or the consolidated final gates.

## 10. Success measures

Expected outcome at the bound baseline, to be confirmed rather than treated as a quota:

| Candidate | Tracked files removed | Tracked lines removed | Confidence/condition |
| --- | ---: | ---: | --- |
| 66 numeric step manifests | 66 | 2,811,048 | Exact; primary Train 2 target |
| Dashboard directory + dashboard workflow | 27 | 20,333 | Exact if dashboard leaves |
| `docs/chains/rh/status.yaml` | 0–1 | 0–1,087 | Only if no retained operator/runtime consumer remains |
| Core block-clock process package | 0–3 | 0–23,184 | Conditional atomic package; shared behavior/spec stays |
| Fork/probe/vault-comparison/CCIP-example candidates | 0–44 | 0–13,629 | Conditional on invariant mapping; replacements may add lines |
| Other completed/superseded docs | To be measured | Planning range 40,000–70,000 | Provisional only; keep-list and runtime trace control |
| `scripts/abis/` | 0 | 0 | Retained wholesale |

If most conditional packages and the provisional document range land, a reasonable planning zone is roughly **500,000–575,000 tracked lines** and **470–590 tracked files**, plus/minus replacement tests and the three required simplification artifacts. The file range is deliberately wide because document and parked-package dispositions are conditional. The 66 step manifests alone account for roughly 95–98% of projected line reduction; that is a line-volume fact, not a claim that the other trains lack comprehension or assurance value.

The projection is not an acceptance gate. Retention rules and evidence-based de-scopes win over every number above.

Report, but do not optimize blindly for:

- tracked files and lines before/after;
- active-tree disk footprint before/after;
- old history snapshots removed versus current manifests retained;
- docs kept/removed and runtime references resolved;
- ABI parity (`52/52` retained) and mocks kept/removed with consumer counts;
- selected/default/comprehensive collection counts;
- named cold/warm wall times and pytest times;
- full lean/comprehensive outcomes;
- number of introduced failures/errors: target zero;
- retained production-artifact drift: target zero;
- unresolved dangling paths/imports: target zero;
- unrecoverable extracted paths: target zero.

Retention rules take precedence over file-count and line-count reduction.

## 11. Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| In-flight branch conflict | Exact baseline, freeze note, independent trains, and Section 14 owner-specific rebase policy |
| Live operator docs deleted | Unconditional keep-list plus literal/computed runtime-reference scan |
| Dependency-hash gate broken | Requirements and dependency evidence are retained and immutable in this task |
| BluePrint HEAD census fails | Preserve bound files, commit before validation, never refresh hashes for cleanup |
| Artifact/ABI coupling broken | Retain all 52 ABI outputs and run exact repository parity; do not rewrite expectations |
| Migration command broken | Runner, CLI, planning API, schema, migrations, and `tests.constants` remain in scope-protected paths |
| Historical deployment evidence lost | Baseline blob manifest plus representative/boundary recovery verification |
| Test assurance silently lost | Invariant disposition map and full end-of-task lean/comprehensive runs |
| Sandbox socket failure misreported | Lazy port is already integrated; local non-Anvil test must pass with socket guard |
| Baseline aggregate counts cannot identify regressions | Capture parseable lean/comprehensive JUnit and terminal logs before editing; compare normalized identities at the end |
| Stale fork opt-in arms remote work | Explicitly unset all three `RIPE_RH_FORK_*` controls and rely on the disabled-mode network guard |
| Scope-coupled train blocks all value | Three broad independently revertible trains; de-scope unsafe train and finish others |
| Large diff is unreadable | No in-repo archive copies; `git mv` retained moves; final `--find-renames` review |
| Production bytecode changes | No production Vyper edits and final artifact parity |
| CI falsely reported green | Local syntax/path validation only; explicit statement that workflow was not dispatched |

## 12. Explicit non-goals

This plan does not:

- fix the deployment CLI defect inventory;
- change migration resume semantics;
- reduce or replace the migration runner;
- change manifest schema or slim current manifest records;
- split dependencies;
- remove Uniswap;
- change production contracts or economics;
- deploy, fork remotely, push, merge, or publish;
- integrate other feature branches;
- rewrite history or reduce existing clone size;
- require every pre-existing suite failure to be fixed;
- sacrifice retained safety/operator dependencies for a repository-size target.

## 13. Final handoff report format

The implementing agent’s final response and `docs/simplification/README.md` must include:

1. Exact worktree, branch, baseline, final commit, and broad commit list.
2. Confirmation that `docs/simplification/implementation-plan.md` is the exact plan used.
3. Train-by-train summary, including any reverted/de-scoped train.
4. Before/after active-tree metrics and comparison with the non-binding Section 10 projection.
5. Extraction-manifest and recovery results.
6. Retained docs, all 52 ABIs, mocks, current manifests, and reasons.
7. Baseline/final named benchmark table with pytest and `/usr/bin/time` values, plus separate socket-purity outcomes.
8. Baseline and final lean/comprehensive JUnit/log absolute paths, SHA-256 values, exit codes, outcomes, and normalized failure/error identity diff.
9. Removed/renamed test identities and their invariant-disposition entries.
10. Artifact, BluePrint, dependency-gate, schema, workflow-syntax, and dangling-reference results.
11. Tests not run and exact reason.
12. Known residual risks and separate deployment-owner follow-ups.
13. Confirmation that no push, PR, deployment, remote fork, tag, or external archive occurred.
14. Confirmation that only task-created validation/reference worktrees were removed, or exact retained dirty paths.
15. Exact next authorized action: end-of-task review and landing decision, not deployment.

## 14. Landing and conflict strategy

### 14.1 State before implementation

- Current `rh` already includes `codex/rh-test-speed-integration`; do not merge it again.
- `/Users/wigglez/dev/ripe-protocol-rh` is user-owned and dirty. At plan finalization it had tracked edits under `config/`, `contracts/`, `docs/`, `scripts/abis/`, and `tests/`, plus untracked `docs/chains/rh/vault-migration/`. All are outside this task; protect the entire worktree even if its status changes again.
- `instant-bond-lane` diverges from RH: RH has 14 commits not in the lane; the lane has 5 commits and approximately 7,083 added lines not in RH.
- Older remediation/test-plan worktrees are not implementation inputs.

### 14.2 Freeze policy

Preferred landing condition: freeze new writes to `rh` and avoid large path-moving changes in active branches while the simplification run is in progress. This is a coordination request, not permission for the implementing agent to alter other branches.

If RH moves during implementation, finish the exact-baseline branch and final report. Do not silently rebase. The landing owner decides whether to accept the exact-baseline branch or authorize a separate rebase/integration pass with a repeated Phase 7.

### 14.3 Default order

1. Current RH/test-speed integration is the simplification baseline.
2. Run and review this simplification branch.
3. If accepted, an authorized integration owner lands simplification onto RH.
4. The `instant-bond-lane` owner then rebases the feature branch onto the simplified RH layout and resolves its feature-specific conflicts.
5. Vault-migration work remains on its owner’s branch/worktree and is integrated separately.

This rebase is materially lower risk than the earlier concept because this plan does not reorganize tests into new `unit/contracts/integration` hierarchies. It is still a broad delete/modify conflict surface, so the feature owner—not the cleanup agent—owns semantic conflict resolution.

If the owner instead wants `instant-bond-lane` to land first, stop before implementation, land/review it separately, and create a newly measured simplification baseline. Do not attempt to combine both in this long task.

### 14.4 Conflict ownership

- Simplification implementer: extraction manifest, retained-path mapping, and cleanup-specific conflicts.
- Feature-branch owner: semantic adaptation of feature contracts/tests/docs to the simplified tree.
- Deployment owner: any conflict touching migration commands, runner/schema, current manifests, operator docs, or deployment semantics.
- Integration owner: final rebase/merge mechanics and authorization to push/open a PR.

Any authorized rebase that changes the final tree invalidates prior final-suite evidence. Repeat the complete Phase 7 validation after conflict resolution.

## 15. Copy-paste fresh-agent instruction

> Read `/Users/wigglez/dev/ripe-protocol/RH-CODEBASE-SIMPLIFICATION-PLAN.md` completely and implement it end to end from exact baseline `610b43f4508e85628a1362532a79d68d71ea902c`. Work only in a new isolated `codex/rh-codebase-simplification` worktree, and add an exact tracked copy of the plan at `docs/simplification/implementation-plan.md`. This is one uninterrupted multi-day task: before editing, capture the one reference lean/comprehensive JUnit pair, the two named cold/warm wall benchmarks with a fresh cache per target, and the separate socket-purity gate; then execute the three independently revertible trains continuously with only targeted debugging checks; finally run the candidate lean/comprehensive suites, artifact/authority/dependency gates, recovery checks, benchmarks, and comprehensive review together at the end. Do not pause for train reviews or micro-gates. The current RH already contains the test-speed integration; this cleanup protects it but does not promise more speed. Preserve its pytest configuration, Boa cache, lazy port allocation, unraisable-exception setting, and Python workflow. Retain all 52 ABIs. Do not change production Vyper, requirements, migration CLI/runner/planning API, manifest schema/current-manifest format, or Uniswap. Retention and load-bearing coupling rules override size targets. If one train becomes unsafe, revert/de-scope that train, finish the others, and report it at the end. Unset RPC/secrets and all three `RIPE_RH_FORK_*` controls for local runs. Do not touch any existing worktree, including the user-owned tracked edits and untracked vault-migration material in the dirty RH worktree. Do not push, open a PR, merge, deploy, use secrets, rewrite history, or integrate another branch. Stop only for Section 0.4 hard stops. Deliver the clean locally committed branch, extraction manifest, out-of-tree JUnit/log evidence with hashes, final report, de-scopes, and exact landing recommendation for one end-of-task review.
