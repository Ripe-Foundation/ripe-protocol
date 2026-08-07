# RH Test-Speed Implementation Plan

## Purpose

This is the execution handoff for making the Robinhood test workflow fast enough for normal startup iteration without deleting meaningful protocol-safety coverage.

The implementation must produce two intentionally different workflows:

1. A lean default developer/PR lane that gives fast feedback and is what `python -m pytest` runs.
2. An explicit comprehensive lane for artifact reproduction, deployment evidence, full fuzzing, gas evidence, and fork qualification.

Do not continue treating every release-assurance check as part of the inner loop. Do not claim success from pytest's reported duration alone; measure process wall time.

## Fresh-agent execution contract

This file is the authoritative implementation instruction. A fresh agent must:

1. Work only in the existing `codex/rh-test-speed-implementation-plan` worktree named below. Do not create another branch or worktree.
2. Read this file completely before editing or running the baseline suite.
3. Verify the frozen commit, tree, branch, and initial status exactly as instructed below.
4. Treat **Decisions already made**, **Scope**, and **Forbidden changes** as locked owner decisions. Do not re-derive or reopen them.
5. Execute Work Packages 0 through 4 in order. Do not apply a later performance cut before capturing the earlier required baseline.
6. Update this plan only where it explicitly requires measured targets/results to be recorded; do not rewrite its strategy during implementation.
7. Keep all execution local and network-free except a dependency installation that is explicitly allowed by Work Package 4 and approved through the environment's normal permission flow.
8. Stop only at a stated stop condition or genuine owner decision. Otherwise continue through verification and the final report.
9. Leave all implementation changes unstaged and uncommitted. Do not push, merge, deploy, or change release/gate state.

## Frozen starting point

- Repository: `/Users/wigglez/dev/ripe-protocol`
- Source branch: `rh`
- Starting commit: `7d8c76e5134bf866ccbb051fdf5030b6e83cef8b`
- Starting tree: `1d115e9a01f01f933e3e80747902080387f2113c`
- Planning branch: `codex/rh-test-speed-implementation-plan`
- Planning worktree: `/Users/wigglez/dev/ripe-protocol-rh-test-speed-plan`

The source `rh` branch was clean and matched `origin/rh` when this plan was created. The primary `master` worktree contained pre-existing untracked `docs/` content and must not be used or cleaned.

The implementing agent must begin with:

```bash
cd /Users/wigglez/dev/ripe-protocol-rh-test-speed-plan
git rev-parse HEAD^{commit} HEAD^{tree}
git status --short --branch
```

Expected initial state:

- Commit and tree exactly match the values above.
- The only expected uncommitted path is this plan.
- Stop and report if the baseline, branch, or worktree contains any other change. Do not rebase onto a newer `rh` tip without explicit owner approval.

## Decisions already made

These are implementation decisions, not questions for the next agent:

1. The default command must be fast. Release evidence will not run by default.
2. Safety tests will be retained unless they are exact semantic duplicates. Expensive tests should first be moved to the appropriate explicit lane, then optimized where worthwhile.
3. The performance branch will not modify production contracts, regenerate current deployment evidence, or reconcile unrelated stale artifact/source expectations.
4. Wall-clock time is authoritative. Pytest's internal timer is supplementary because it omits expensive process shutdown.
5. Cold-cache and warm-cache results must be reported separately.
6. The built-in pytest `unraisableexception` plugin will be disabled through root `pytest.ini` `addopts` in the default lane and enabled in the comprehensive lane. This mechanism was directly verified under the pinned pytest 8.4.2 with both a plugin probe and a real Boa contract test. The comprehensive lane is manual, so automatic CI will not exercise this plugin; the owner accepts that narrower assurance in exchange for iteration speed.
7. The complete StabilityPool Hypothesis campaign will remain available, but it will not run in the default lane. The StabilityPool specification records the 140 examples as validation already completed, not as a standing default-command requirement. Some Robinhood deployment documentation calls for a full suite during release validation; the explicit comprehensive lane preserves that requirement without making it the developer default.
8. The Uniswap minimal-price behavior suite remains core behavioral coverage and must be optimized, not simply hidden.
9. `pytest-xdist` is not automatically authorized as permanent infrastructure. Run the bounded experiment below and retain it only if it produces at least a 30% warm-wall reduction with stable results.
10. Add only one lean Python CI job. Do not build a version matrix or a new release-gate framework in this task.
11. Do not commit, push, merge, deploy, run remote forks, or alter lifecycle/gate status. Leave an unstaged, uncommitted implementation handoff unless the owner separately authorizes the next action.

## Verified starting evidence

The following measurements were reproduced locally against the frozen `rh` source. They are the baselines for this task.

### Runner correctness

- `python -m pytest` aborts during collection because `tests/deployment/test_dependency_gate.py` imports IPython at module import time while the selected `ripe-lite` environment lacks IPython.
- Bare `pytest` fails earlier while importing `conf_core` because the repository root is not reliably on `sys.path`; `config.BluePrint` cannot be imported.
- There is no `pytest.ini`, `pyproject.toml` pytest configuration, or Python-test CI workflow.
- Ignored `.pyc` files under `tests/__pycache__/` embed paths from the deleted `ripe-protocol-basic-vault-fail-closed` worktree and can produce phantom traceback paths.

### Shutdown overhead

One warm-cache test, `tests/data/test_ledger.py::test_ledger_initial_state`, produced:

| Mode | Pytest time | Process wall time |
|---|---:|---:|
| Default plugins | 26.35s | 64.62s |
| `-p no:unraisableexception` | 26.29s | 45.06s |

The flag saved 19.56 wall seconds while pytest's own timer was essentially unchanged. Pytest 8.4.2's plugin performs five `gc.collect()` passes at process cleanup; the deployed Boa heap makes those passes expensive.

### Cache effect

The same test was run twice with a new isolated Boa cache:

| Cache state | Pytest time | Process wall time |
|---|---:|---:|
| Fresh | 104.07s | 120.93s |
| Reused immediately | 26.64s | 44.89s |

Branch-switch cache misses are therefore a material user-experience problem, but they do not explain persistent full-suite cost.

Titanoboa's `DiskCache` defaults to a one-week access-time TTL. A developer returning after a week can therefore receive a cold compile on any branch, including `master`; this recurring cache eviction must be distinguished from branch-specific regression.

### Recent behavioral hotspots

- `tests/priceSources/uniswap/test_minimal_prices.py`: 74 passed, 1 expected failure, 110.53 pytest seconds, 133.23 wall seconds with `unraisableexception` already disabled. Its shared setup was 26.23 seconds, leaving roughly 84 seconds of test calls.
- `tests/vaults/modules/test_stab_vault_claim_data_fuzz.py`: four pytest items execute 140 Hypothesis examples. A prior focused run measured roughly 95 seconds of test calls after shared setup.

The earlier statement that StabilityPool fuzzing was the single dominant recent cause is withdrawn. The Uniswap file was added one day earlier and is a comparable hotspot. Do not rank recent commits by collected-item count; re-time them in wall seconds.

### Suite scale and current red state

- `master`: 2,527 selected tests under the local fork policy.
- Current `rh`: effectively 4,401 selected tests when the 45 dependency-gate cases are included.
- The proposed default lane selects 3,134 tests: only about 28% fewer than current `rh`. Lane selection alone cannot justify an absolute wall-time promise.
- A cold diagnostic run was stopped at 74% after 840.88 pytest seconds with pre-existing failures and errors. Extrapolating that broken partial run is not an acceptance benchmark.
- Expensive artifact checks currently abort early on stale expectations. Reconciliation would make those checks run farther and may initially increase suite duration.

The original “low single-digit minutes” prediction was not established and must not be repeated as a forecast. Work Package 0 must build a cost model from the repaired 3,134-test lane before an absolute full-lane target is committed.

## Success criteria

All of the following are required:

1. Both `python -m pytest --collect-only -q` and bare `pytest --collect-only -q` start from the repository root without import or collection errors in the documented development environment.
2. The default lane is explicit, documented, and excludes release-only evidence.
3. A representative pure test no longer deploys the complete Ripe protocol or binds a localhost port.
4. Disabling `unraisableexception` saves at least 15 wall seconds on the representative warm contract smoke, which must complete in no more than 50 wall seconds. This replaces the noise-sensitive 45-second threshold.
5. `test_minimal_prices.py` retains all distinct behavioral assertions and improves from 133.23 wall seconds to no more than 80 wall seconds warm.
6. Work Package 0 records a repaired pre-optimization baseline after runner repair, lane classification, and stale-bytecode cleanup, but before disabling `unraisableexception`, adding fixture overrides, optimizing Uniswap, or trying xdist.
7. The default warm lane improves by at least 50% versus that pinned baseline and meets the absolute target derived from the ranked duration table. If Work Package 0 shows that 50% is not supported by identified cuts, stop for an owner decision before excluding more core behavior.
8. The default cold lane meets the separately derived cold-cache target; it is never inferred from the warm result.
9. The comprehensive lane remains invocable with one documented command and reports all existing pre-task failures honestly.
10. Full StabilityPool fuzz coverage remains invocable and retains the existing 40/20/40/40 example budgets.
11. The default lane does not silently omit core contract behavior. Every excluded area is listed in the lane manifest below.
12. One lean Python CI job runs the default lane. The comprehensive run remains manual and must not become a required or scheduled gate in this task.

If the target derived in Work Package 0 is not achieved after Work Packages 1–3, the bounded parallelism experiment becomes mandatory. If the measured plan still cannot achieve a 50% warm-wall reduction, stop with the updated ranked residual table; do not delete additional tests speculatively.

## Scope

### Allowed implementation paths

- `pytest.ini` or one equivalent root pytest configuration file
- `tests/conftest.py`
- `tests/conf_core.py`
- `tests/conf_env.py`
- Narrow `conftest.py` files under test subtrees when required to scope fixtures or markers
- `tests/deployment/test_dependency_gate.py`
- `tests/config/test_defaults_robinhood.py` only to add lane classification
- `tests/config/test_robinhood_reward_launch_plan.py` only to add lane classification
- `tests/priceSources/uniswap/test_minimal_prices.py`
- `tests/vaults/modules/test_stab_vault_claim_data_fuzz.py`
- `tests/vaults/test_stock_token_vault_comparison.py` only to add lane classification
- `tests/core/creditEngine/test_stock_backing.py` only to mark the gas benchmark
- `tests/inventory/test_contract_artifacts.py`
- `tests/deployment/test_abi_export.py`
- `scripts/check_contract_artifacts.py` and `scripts/export_abis.py` only if Work Package 3 reaches their optimization step
- One new lean Python workflow under `.github/workflows/`
- `requirements.in` and `requirements.txt` only if the measured xdist experiment passes its retention threshold
- This implementation plan

Any other tracked path requires owner approval before editing.

### Forbidden changes

- No `contracts/**` edits
- No source-authority hash, ABI, bytecode, deployment-manifest, or release-evidence refresh
- No Robinhood lifecycle, readiness, dashboard, or gate-status changes
- No weakening an assertion merely to turn a pre-existing red result green
- No remote RPC, fork, deployment, publication, or secret-dependent operation
- No cleanup of another worktree or the primary `master` worktree

## Lane contract

Implement and document these commands.

### Default developer/PR lane

```bash
python -m pytest
```

The root pytest configuration must:

- Establish a stable root and Python import path so both invocation styles work.
- Disable `unraisableexception` for this lane.
- Register all markers.
- Exclude the release-only areas listed below.
- Preserve the existing local-fork default and fail closed against accidental remote RPC use.

Use this default selection contract unless a measured pytest limitation requires an equivalent formulation:

```ini
addopts =
    -p no:unraisableexception
    --ignore=tests/deployment
    --ignore=tests/deployment_profiles
    --ignore=tests/inventory
    --ignore=tests/probes
    -m "not release and not artifact and not fuzz and not gas and not fork_qualification"
```

Default exclusions:

- `tests/deployment/**`
- `tests/deployment_profiles/**`
- `tests/inventory/**`
- `tests/probes/**`
- Full fork qualification
- Contract artifact and ABI reproduction
- Dependency-security evidence
- Full StabilityPool fuzzing
- Gas benchmarks
- Machine/environment identity evidence
- Documentation, dashboard, and release-status assertions

Classify these out-of-directory modules explicitly:

- `tests/config/test_defaults_robinhood.py`: `release`
- `tests/config/test_robinhood_reward_launch_plan.py`: `release`
- `tests/vaults/test_stock_token_vault_comparison.py`: `release`
- `tests/vaults/modules/test_stab_vault_claim_data_fuzz.py`: `fuzz`
- `tests/core/creditEngine/test_stock_backing.py::test_c2_marginal_gas_protocol`: `gas`

These tests are not deleted; they move to the comprehensive lane. If a file inside an excluded directory is truly a fast, stable unit test, it may be explicitly promoted back only after its fixture graph and wall time are demonstrated.

### Comprehensive lane

Use this command to override the default exclusions and marker expression:

```bash
python -m pytest -o addopts=''
```

Under the pinned pytest 8.4.2, this override re-enables the built-in `unraisableexception` plugin; that behavior was directly verified. Re-prove it after adding the real configuration. Do not add a custom orchestration framework. The comprehensive command must:

- Collect every repository test.
- Re-enable `unraisableexception`.
- Run the 140-example StabilityPool campaign.
- Run artifact, ABI, inventory, dependency, gas, and fork-policy evidence as applicable without enabling remote fork access by default.
- Report current pre-existing source/artifact failures rather than rewriting expectations in this task.

### Focused developer runs

An explicitly named path or node inside a directory excluded by `--ignore` is still collected. An explicitly named node carrying one of the excluded markers is deselected and exits 5 unless the marker expression is overridden. Therefore ordinary and ignored-directory focused runs work directly, while the four marker-classified modules and the marked gas node require:

```bash
python -m pytest -o addopts='' path/or/nodeid
```

## Work Package 0 — Repair, profile, and set the cost-based target

This package establishes the only valid full-lane baseline. Do not apply performance changes before it is captured.

### 1. Repair and classify the runner without disabling plugins

Add one root pytest configuration file with:

- `testpaths = tests`
- The repository root and `tests` on the Python import path
- Registered markers: `release`, `artifact`, `fuzz`, `gas`, `fork_qualification`, and `serial`
- The default directory exclusions and marker expression in this plan
- No `-p no:unraisableexception` yet

For the Work Package 0 baseline, use the final lane-contract `addopts` block but omit only this line:

```ini
-p no:unraisableexception
```

After `B_cold`, `B_warm`, and the ranked table are recorded, Work Package 1 adds that exact line. This ordering is mandatory; otherwise the largest immediate cut contaminates the pre-optimization baseline.

Add the specified module/test markers. Move the `IPython.lib.lexers.IPython3Lexer` import inside the specific dependency test or release-only fixture that uses it. The comprehensive dependency test must still fail clearly when its required environment is incomplete; do not convert it into an unconditional skip.

Do not add tox, nox, a Makefile, a custom Python runner, or multiple pytest configurations.

### 2. Remove stale ignored bytecode from this worktree

First list only ignored bytecode under this exact worktree and confirm it is untracked. Then delete only `tests/**/__pycache__/*.pyc` and empty `__pycache__` directories in this worktree. Do not run broad `git clean`, touch another worktree, or delete the user's Boa disk cache.

Run benchmarks with bytecode writing enabled and a private `PYTHONPYCACHEPREFIX`. Do not set `PYTHONDONTWRITEBYTECODE=1`: it would force assertion re-rewriting and make repeat runs slower than the developer workflow being measured.

### 3. Capture the repaired baseline

Prove that both root invocation styles collect. The selected count must be explained; the independently reproduced expectation for this lane is 3,134.

Run the repaired default lane twice against the same isolated Boa cache with the built-in plugin still enabled. Treat the second run as the warm baseline `B_warm`; retain the first as the cold baseline `B_cold`. Use `--durations=0` and `/usr/bin/time -p`, and produce a ranked table that separates:

- Session setup
- Per-file and per-test call time
- Teardown
- Process time invisible to pytest
- Known pre-existing failures/errors

Do not extrapolate from item count or from the earlier broken 74% run.

### 4. Record the target in this plan before optimization

From the ranked table, list every planned saving that affects the retained 3,134-test lane. Do not count full fuzz, artifact, ABI, or release tests again because lane classification has already excluded them from `B_warm`. Do not count the pure-test fixture override as a full-lane saving because retained contract tests still cause the session-scoped protocol graph to deploy once.

Set the absolute warm target only if the identified cuts plus the bounded xdist experiment plausibly support at least a 50% reduction from `B_warm`. Record the numeric target and cost model in this plan. Set a separate cold target from `B_cold`. If the evidence does not support a 50% reduction, stop for an owner decision before excluding additional core behavior.

### Work Package 0 acceptance

- Both pytest invocation styles collect the repaired lane.
- Default collection does not import IPython.
- The selected count and all exclusions reconcile.
- Cold and warm wall baselines exist.
- A ranked residual-duration table and explicit cost model exist.
- Numeric warm and cold targets are written into this plan before Work Package 1 starts.

## Work Package 1 — Take the verified shutdown cut

After freezing the Work Package 0 baseline, add `-p no:unraisableexception` to root `addopts` exactly as specified in the lane contract.

Re-run the representative warm contract smoke with `/usr/bin/time -p`. Verify with `pytest --trace-config` or an equivalent plugin-manager probe that:

- Default lane: `unraisableexception` is not loaded.
- `python -m pytest -o addopts=''`: `unraisableexception` is loaded.

Keep the comprehensive workflow manual. This intentionally means automatic lean CI does not provide unraisable-exception assurance; do not add a nightly or required comprehensive gate without new owner authorization.

### Work Package 1 acceptance

- The representative smoke saves at least 15 wall seconds and completes in no more than 50 wall seconds warm.
- Default and comprehensive plugin-loading behavior is proven.
- The comprehensive dependency test still fails clearly if IPython is genuinely absent.

## Work Package 2 — Make focused pure runs bypass the protocol bootstrap

`tests/conf_core.py::ripe_hq` is session-scoped and autouse. It costs roughly 26 warm seconds once per pytest process, not once per test. Bypassing it materially improves focused pure/evidence invocations, but it is not expected to improve the 3,134-test default lane because retained contract tests still require one session deployment.

The shutdown-plugin and fixture-override savings are also not generally additive: pure runs with no deployed Boa heap have negligible garbage-collection cost, while retained contract runs benefit from the plugin cut but still need protocol setup.

### 1. Use the existing no-op override pattern

Keep the root autouse fixture as the default approach. The repository already contains eight session-scoped no-op `ripe_hq` overrides:

- `tests/config/test_defaults_robinhood.py`
- `tests/deployment/test_base_profile_regression.py`
- `tests/deployment/test_dependency_gate.py`
- `tests/deployment/test_network_profiles.py`
- `tests/deployment/test_secret_handling.py`
- `tests/deployment/fork/conftest.py`
- `tests/inventory/test_block_clock_inventory.py`
- `tests/inventory/test_bluechip_yield_prices_artifacts.py`

Extend that proven pattern with narrowly scoped subtree `conftest.py` overrides. At minimum, none of these areas may resolve the real protocol fixture unless an individual test explicitly needs it:

- `tests/clock/**`
- `tests/deployment/**`
- `tests/deployment_profiles/**`
- `tests/inventory/**`
- `tests/probes/**`
- `tests/priceSources/uniswap/test_minimal_prices.py`

Use `pytest --setup-plan` on one representative test from each area to prove the fixture graph, not just runtime inference.

Do not remove root `autouse=True` and audit all 4,356 tests unless the subtree-override approach is proven insufficient. That higher-blast-radius fallback requires an owner decision supported by concrete failing node ids and fixture evidence.

### 2. Make the local port lazy

The current session-scoped `anvil` fixture depends on session-scoped `free_port`, which binds a socket even when the local Boa path never starts Anvil.

Refactor so a free port is allocated only inside the code path that actually launches Anvil. A local Boa run must not resolve or bind a port. Preserve existing explicit Anvil and remote-fork behavior without exercising a remote connection in this task.

### Work Package 2 acceptance

- A pure clock-model test completes without compiling/deploying the protocol and without socket access.
- A focused Uniswap module run no longer pays the approximately 26-second unrelated full-protocol setup.
- Existing representative contract tests still receive a fully initialized protocol.
- No network call occurs in the default lane.
- The final report attributes this package to focused-invocation latency and does not claim it materially reduced the full default lane without measured proof.

## Work Package 3 — Optimize the retained hotspots without losing behavior

### 1. Uniswap minimal-price suite

The function-scoped builder currently performs repeated `boa.load` deployments for tokens, pair, quote desk, HQ, and price source across 75 items.

Implement the smallest safe reuse strategy:

- Precompile reusable contract factories once with Boa's partial-load/factory API where supported.
- ~~Create one canonical module-scoped deployment for tests that use default
  constructor values.~~ **Superseded by the Order-independence correction below.**
- ~~Rely on verified Boa test anchors to restore canonical state between test
  calls.~~ **Superseded: anchors do not restore Titanoboa's contract registry.**
- Keep fresh deployments only for tests that genuinely exercise constructor variants, invalid identity, decimals, or setup state.
- Consolidate parametrized cases only when the same semantic branches and assertion values remain explicit.

Before changing assertions, write a compact behavior inventory by test name. After refactoring, prove the same inventory remains. The existing expected failure must remain explicit; do not convert it silently.

Target: no more than 80 warm wall seconds for the file, with a stretch target of 60 seconds.

#### Implemented behavior inventory

Recorded by test name before any assertion edit; the optimization changes fixtures and
deployment reuse only, so this inventory and the explicit expected failure remain unchanged.

- Price correctness: `test_prices_ripe_from_either_uniswap_v2_token_position`, `test_normalizes_uniswap_v2_token_decimals`, `test_tracks_uniswap_v2_reserve_ratio`, `test_scales_linearly_with_quote_asset_price`, `test_zero_quote_price_returns_zero`, `test_zero_reserve_returns_zero`, `test_constructor_rejects_pair_without_configured_ripe`, `test_preserves_precision_when_inverse_reserve_ratio_is_sub_unit`, `test_unsupported_token_decimals_return_zero`, `test_runtime_unsupported_token_decimals_return_zero`, `test_constructor_rejects_zero_pool_or_ripe`, `test_only_exposes_the_configured_ripe_asset`, and `test_constructor_sets_expected_immutables_and_defaults`.
- Snapshot behavior: `test_protocol_price_is_zero_until_first_snapshot`, `test_empty_price_desk_argument_uses_registered_price_desk`, `test_latest_snapshot_reads_current_uniswap_price`, `test_add_snapshot_stores_price_and_emits_event`, `test_snapshot_delay_is_enforced_at_exact_boundary`, `test_snapshot_buffer_wraps_and_overwrites_oldest_entry`, `test_weighted_price_is_arithmetic_mean_of_live_snapshots`, `test_snapshot_upside_is_throttled_by_default_ten_percent`, `test_downside_is_immediate_and_combined_price_uses_lower_value`, `test_combined_price_uses_weighted_floor_when_spot_is_higher`, `test_all_stale_snapshots_fail_closed_to_zero`, `test_repeated_manipulated_snapshots_cannot_persistently_suppress_price` (expected failure), and `test_non_ripe_snapshot_operations_are_noops`.
- Governance and access control: `test_rejects_invalid_price_configurations`, `test_accepts_price_configuration_boundaries`, `test_governance_can_propose_and_confirm_configuration`, `test_configuration_cannot_be_confirmed_before_timelock`, `test_config_confirmation_adds_fresh_snapshot`, `test_config_confirmation_clamps_cursor_when_snapshot_window_shrinks`, `test_governance_can_cancel_configuration`, `test_governance_cannot_cancel_configuration_while_paused`, `test_new_config_proposal_replaces_pending_record_without_cancelling_old_action`, `test_expired_config_remains_reported_as_pending_until_cancelled`, `test_pre_setup_zero_timelock_requires_deployment_gate`, `test_config_proposal_emits_complete_event`, `test_unauthorized_callers_cannot_snapshot_or_configure`, `test_pause_zeroes_price_and_blocks_state_changes`, `test_unsupported_feed_lifecycle_stubs_report_no_action`, and `test_only_switchboard_can_pause`.
- Adversarial inputs: `test_reverting_pair_read_fails_closed`, `test_truncated_reserve_response_fails_closed`, `test_reserve_response_with_trailing_bytes_uses_canonical_prefix`, `test_malformed_token_identity_response_fails_closed`, `test_reverting_quote_price_source_fails_closed`, `test_price_multiplication_overflow_returns_zero`, `test_truncated_quote_price_response_fails_closed`, `test_quote_response_with_trailing_bytes_uses_canonical_prefix`, and `test_recursive_quote_request_terminates_without_mutation`.

#### Order-independence correction

Follow-up review falsified the module-scoped deployment premise: Titanoboa 0.2.7
anchors restore EVM state but not the contract registry, and the shared deployment
produced order-dependent results. The correction keeps compiled factories
module-scoped but always creates a fresh deployment when the builder is called,
matching the original fixture semantics even if a future test calls the builder
twice. A follow-up cleanup also replaced the duplicated, order-sensitive defaults
tuple with one immutable deployment-config value. A lazy
`request.getfixturevalue` alternative was tested and rejected because it collided
with Titanoboa's fixture-anchor stack and produced 58 teardown errors
(reviewer-verified, 2026-08-06); it must not be reintroduced. Forward, reversed,
and deterministic shuffled runs each continue
to produce 74 passes and the same one expected failure in 6.31s, 6.32s, and
6.39s wall respectively, while remaining well below the 60-second stretch target.
The reviewer subsequently extended this to forward, reverse, four seeded shuffles,
and the comprehensive lane with the plugin enabled; every run produced the same
74 passes and one expected failure (reviewer-verified, 2026-08-06).

### 2. StabilityPool fuzzing

Mark the module `fuzz` and remove it from the default lane. Preserve the 40/20/40/40 comprehensive budgets.

Then attempt the low-risk runtime improvement:

- Predeploy reusable claim-token pools or compiled factories outside individual Hypothesis examples.
- Let Boa/Hypothesis anchors restore state per example.
- Keep deterministic cap-20 boundary coverage in the ordinary contract lane.

Do not reduce comprehensive example counts merely to make the comprehensive number look better. If fixture reuse is unsafe or changes shrinking/reproduction semantics, retain the current comprehensive implementation and report it as intentionally expensive.

The implemented module pool intentionally reuses the same 21 token addresses
across the 140 examples. Boa/Hypothesis anchors restore their EVM state, and the
campaign passed in both forward and reversed test order (reviewer-verified,
2026-08-06), but address diversity between examples is no longer a fuzz dimension.
Deterministic cap-20 coverage in the ordinary lane continues to exercise distinct
simultaneous addresses.

### 3. Artifact and ABI reproduction

Moving these checks out of the default lane is required. Compiler-pipeline refactoring is conditional: do it only if the comprehensive warm run remains above 15 wall minutes after the preceding work.

If required:

- Compile each exact `(compiler version, settings, source hash, transitive input hash)` once per process.
- Reuse compiled outputs across mutation/expectation cases.
- Keep one real subprocess end-to-end checker test.
- Obtain all supported Vyper outputs from one invocation rather than three invocations per contract.
- Reuse ABI compile outputs within the session.

Do not introduce a persistent cache that can return stale output without all identity inputs in its key.

### Work Package 3 acceptance

- Uniswap behavior inventory is unchanged and target wall time is met.
- Default lane does not collect/run full fuzz, artifact, ABI, gas, or release evidence.
- Comprehensive commands still select each excluded category.
- No source/artifact expectation is rewritten.

## Work Package 4 — Bounded parallelism experiment and lean CI

### 1. Parallelism experiment

Only after fixture scoping, test the default lane serially and with:

```bash
python -m pytest -n 4 --dist loadscope
```

Use a disposable environment under `/private/tmp` for the experiment; do not install experimental packages into the shared `ripe-lite` environment. If installation needs network access, request it through the environment's normal approval mechanism. Retain `pytest-xdist` only if all conditions hold:

- At least 30% warm wall-time improvement against the same selected node set
- Same pass/fail/skip/xfail/deselect result
- No Boa state, port, cache, filesystem, or Hypothesis collisions
- Peak memory is acceptable on the reference machine
- Three consecutive runs are stable

If retained, pin it in both requirements inputs/lock and use exactly four workers by default. Do not use `-n auto`. Mark filesystem mutation, artifact publication, gas, and other non-parallel-safe cases `serial` and keep them outside the default parallel lane.

If the threshold is not met, revert the dependency/config experiment completely and preserve the serial design.

### 2. Minimal Python CI

Add one workflow with one Python 3.12 job that:

- Installs the pinned requirements
- Uses private cache/temp directories
- Unsets RPC and secret environment variables
- Supplies only the non-secret local Etherscan placeholder if required
- Runs the default lane
- Uploads or prints durations sufficient to diagnose regression

Do not add a Python-version matrix, remote forks, deployment gates, or a required comprehensive job. Add a manual `workflow_dispatch` entry for the comprehensive lane in the same workflow.

### Work Package 4 acceptance

- The retained serial or parallel default command meets the numeric warm target established in Work Package 0 and achieves at least a 50% reduction from `B_warm`.
- The CI workflow runs exactly the lean default lane.
- The comprehensive lane is not made a per-commit blocker.
- The final report states explicitly that unraisable-exception assurance remains in the manual comprehensive workflow, not lean CI.

## Required measurement protocol

Every timing table must include:

- Exact commit and tree
- Python, pytest, Titanoboa, Vyper, and Hypothesis versions
- Selected/collected/deselected counts
- Cache state: fresh isolated or immediately reused
- Pytest-reported duration
- `/usr/bin/time -p` real/user/sys duration
- Pass/fail/error/skip/xfail counts
- Whether `unraisableexception` was loaded
- Worker count and distribution mode

Use a private temporary cache for cold measurements; never clear or mutate the user's existing Boa cache. Use the same temporary cache for the immediately following warm measurement.

Keep bytecode writing enabled and direct it to a private `PYTHONPYCACHEPREFIX`. Do not use `PYTHONDONTWRITEBYTECODE=1` for performance benchmarks.

Unset all RPC and secret-shaped environment variables for local runs. Do not run remote-fork tests.

Required benchmark set:

1. One pure clock test with `--setup-plan`
2. `tests/data/test_ledger.py::test_ledger_initial_state`
3. `tests/priceSources/uniswap/test_minimal_prices.py`
4. `tests/vaults/modules/test_stab_vault_claim_data_fuzz.py`
5. Repaired default lane before performance cuts, cold and warm, with `--durations=0`
6. Final default lane, cold and warm
7. Comprehensive lane, warm, or an honest first-failure/partial profile if pre-existing correctness drift prevents completion
8. Serial versus four-worker default lane if xdist reaches the experiment

Re-time the recent Uniswap and StabilityPool introduction checkpoints only if the commits can be archived and run without changing their dependency environment. Use wall seconds, not item counts. This comparison is diagnostic and must not delay the immediate verified cuts.

## Pre-existing failures and stop rules

The performance implementation must not absorb unrelated correctness repair.

Before edits, record the current collection failures and a compact fingerprint of known artifact/source/inventory failures. After edits, compare the failure set.

Stop and ask the owner if:

- A production contract change appears necessary.
- A source-authority, ABI, artifact, inventory, deployment-profile, or release-status expectation would need updating.
- A test must be deleted without a provable semantic duplicate.
- The default lane cannot meet the target without excluding ordinary core behavior beyond the decisions in this plan.
- xdist changes outcomes or creates nondeterminism.
- Another writer changes the implementation worktree or the frozen baseline.

Do not stop merely because the comprehensive suite retains pre-existing red failures; report them separately and continue with safe performance work that can be verified on known-good subsets.

## Reviewer-feedback disposition

All explicit material feedback was incorporated as follows:

| Feedback | Disposition |
|---|---|
| Reviewer workflow falsely called unjoined findings verified | Accepted as a provenance warning. The workflow is outside this repository, so no repo edit is authorized; claims in this plan were independently checked. |
| Stability fuzz named as the dominant recent cause | Accepted correction. That causal headline is withdrawn; Uniswap and fuzz are comparable recent hotspots. |
| Pytest hides roughly 40 seconds of wall time | Accepted and reproduced. The exact local saving from disabling the plugin was 19.56 seconds, with 38.27 seconds invisible in the default run. |
| Low-single-digit forecast unsupported | Accepted. The fixed forecast is removed; Work Package 0 must establish a cost-based target. |
| Correctness reconciliation may make artifact checks slower | Accepted. Baseline first, and keep correctness reconciliation out of this performance branch. |
| Root commands do not currently run | Accepted and reproduced; runner reliability is Work Package 0. |
| No Python CI | Accepted; add exactly one lean job. |
| Stale bytecode points to a deleted worktree | Accepted and reproduced; perform targeted worktree-only cleanup. |
| Cold versus warm Boa cache was not measured | Accepted and closed: 120.93 seconds cold versus 44.89 seconds warm for the representative test. |
| Fuzz example count scales linearly but is not the only lever | Accepted. Full budgets stay comprehensive-only; fixture reuse is attempted before reducing assurance. |
| `pytest.ini` `addopts` cannot disable the built-in plugin | Rejected after direct reproduction under pinned pytest 8.4.2. An isolated plugin probe reported `False` from ini `addopts` and `True` after `-o addopts=''`; a real Boa test completed in 45.82 wall seconds through the ini mechanism. No shim is needed. |
| Eight-minute target has no cost model | Accepted. The fixed target is removed; Work Package 0 profiles the repaired 3,134-test lane and records the absolute target before optimization. |
| Plugin and fixture savings are not additive | Accepted and made explicit. They primarily improve contract and pure focused invocations respectively. |
| Session-scoped `ripe_hq` cannot materially move the full-lane target | Accepted. Work Package 2 is now scoped to focused-invocation latency. |
| Prefer existing no-op `ripe_hq` overrides | Accepted. The eight existing examples are named; subtree overrides are the default, while root-autouse removal is an owner-gated fallback. |
| Explicit paths bypass `--ignore` but not `-m` | Accepted and reproduced. Focused-run instructions now distinguish the two cases. |
| `PYTHONDONTWRITEBYTECODE=1` distorts repeat benchmarks | Accepted. Benchmarks keep bytecode enabled under a private `PYTHONPYCACHEPREFIX`. |
| Lean CI does not run unraisable-exception assurance | Accepted as an intentional owner-aligned tradeoff. The comprehensive workflow remains manual; no nightly or required gate is added. |
| Repaired baseline was ambiguous | Accepted. It is now precisely after runner repair, lane classification, and bytecode cleanup, before every performance cut. |
| Temporary uncommitted worktree risks data loss | Accepted. The worktree is moved to the durable `/Users/wigglez/dev/ripe-protocol-rh-test-speed-plan` path while remaining unstaged and uncommitted. |
| Boa cache silently expires | Accepted. The one-week access-time TTL is documented as a recurring cold-run cause on every branch. |
| No checkpoint timing bisect | Partly accepted. It remains a diagnostic after the repaired-lane profile and must not delay the already verified cuts. |
| Reclassification could look like an unapproved policy change | Accepted with clarification. The StabilityPool spec records completed validation rather than a default-run mandate; release documents that call for a full suite remain satisfied by the comprehensive lane. |
| Artifact checker subprocess count refutation | No change required. The original statement concerned approximately 27 Vyper subprocesses from three outputs across nine contracts and remains correct. |
| Dependency-stack bloat | Confirmed absent: both branches pin 92 distributions, with no added/removed packages and only security-version changes. |

## Implementation results — 2026-08-06 owner override

The owner superseded the package-by-package measurement gates during execution: no
pre-optimization default baseline, numeric Work Package 0 target, intermediate
default runs, comprehensive run, or multi-run xdist experiment was permitted.
Implementation proceeded continuously, followed by collection checks, affected
targeted tests, and one final default-lane measurement. Therefore no 50% claim or
warm-default target claim is made.

### Bound toolchain and collection

- Commit: `7d8c76e5134bf866ccbb051fdf5030b6e83cef8b`
- Tree: `1d115e9a01f01f933e3e80747902080387f2113c`
- Python 3.12.0; pytest 8.4.2; Titanoboa 0.2.7; Vyper 0.4.3;
  Hypothesis 6.138.15.
- Default collection through both `python -m pytest` and bare `pytest`: 3,134
  selected from 3,412 discovered tests, with 278 marker-deselected tests and no
  collection errors.
- Comprehensive collect-only: 4,401 selected from 4,544 tests, with the 143
  local-fork-policy deselections retained. A representative release, fuzz, gas,
  artifact, ABI, and offline fork-policy selection collected explicitly through
  `python -m pytest -o addopts=''`.
- Plugin-manager probes: default `unraisableexception=False`; comprehensive
  override `unraisableexception=True`.

### Timing and outcome evidence

All implementer-measured runs used one serial worker, isolated caches under
`/private/tmp`, private bytecode storage, local fork policy, the non-secret
Etherscan placeholder, and unset RPC/secret-shaped variables. Rows labeled as
reviewer measurements use the separately attributed reviewer environment.

| Run | Cache | Plugin | Pytest | Wall (`real`) | Outcome |
|---|---|---|---:|---:|---|
| Pure clock model with socket guard | reused isolated | off | 0.01s | 0.89s | 1 passed; no socket access |
| Ledger representative smoke | immediately reused | off | 27.60s | 45.17s | 1 passed |
| Uniswap minimal prices, forward | immediately reused | off | 5.09s | 6.31s | 74 passed, 1 xfailed |
| Uniswap minimal prices, reversed | immediately reused | off | 5.15s | 6.32s | 74 passed, 1 xfailed |
| Uniswap minimal prices, shuffled | immediately reused | off | 5.22s | 6.39s | 74 passed, 1 xfailed |
| StabilityPool full fuzz | reused isolated | on | 62.76s | 97.89s | 4 passed; 40/20/40/40 examples |
| Pre-correction default lane | fresh isolated | off | 718.71s | 770.91s | 3,085 passed, 23 failed, 25 errors, 1 xfailed, 278 deselected |
| Delivered default lane, reviewer measurement | warm reviewer cache | off | 577.69s | 638.40s | 3,085 passed, 23 failed, 25 errors, 1 xfailed, 278 deselected |
| Deployment subtree follow-up | reused isolated | on | 82.95s | 85.88s | 706 passed, 15 failed, 1 skipped, 1 fork-policy deselected |

The ledger warm smoke improves by 19.45 wall seconds from the verified 64.62s
plugin-enabled starting evidence and meets the 50s ceiling. The corrected Uniswap
warm file improves by at least 126.84 wall seconds from the verified 133.23s starting
evidence and meets both the 80s target and 60s stretch target in every tested
order. AST comparison proves all 51 test functions are structurally unchanged,
and the explicit expected failure remains unchanged.

The pre-correction fresh-cache default run spent 52.20s outside pytest
(`770.91 - 718.71`). The delivered-tree reviewer measurement spent 60.71s outside
pytest (`638.40 - 577.69`; reviewer-verified, 2026-08-06). The remaining ranked
cost picture is:

1. Retained pytest-visible default work: 577.69s warm on the delivered tree,
   dominated by the broad contract behavior corpus.
2. Process/shutdown work invisible to pytest: 60.71s warm on the delivered tree.
3. Cold session compile/setup: approximately 90s observed before sustained test
   progress; the full `--durations=0` output was emitted, but the execution
   transport truncated the middle of that 5,693-line table, so no false exact
   setup number is recorded.
4. Optimized order-independent Uniswap hotspot: 5.09–5.22s warm pytest /
   6.31–6.39s warm wall.

### Final RH rebase verification — 2026-08-07

The historical measurements above remain bound to the frozen `7d8c76e` source.
They are not used as evidence for integration into current RH. The implementation
was separately rebound to final RH commit
`2c026b0ee8a296e1b8bcb9d5d70651eaf385438e` (tree
`eced68c3bf23ca0198b0be4b5e2b3d3b7f7474d4`) as signed implementation commit
`25b9220a073c033b5f979d9201a4ed5a677ebab5` (tree
`2e505d818af9edb9d4f4d44176ff428109d72c06`). The only cherry-pick conflict was
in the StabilityPool fuzz module; the resolution preserves RH's production
`RETENTION_THRESHOLD = 5 * 10**16` and the candidate's marker and reusable-token
optimization.

Current collection and lane controls were reverified:

- Default collection through both `python -m pytest` and bare `pytest`: 3,244
  selected from 3,522 discovered tests, with 278 marker-deselected tests and no
  collection errors.
- Comprehensive collect-only: 4,539 selected from 4,682 tests, with the 143
  local-fork-policy deselections retained.
- Plugin-manager probes: default `unraisableexception=False`; comprehensive
  override `unraisableexception=True`.
- Uniswap minimal prices: 75 passed and 1 expected failure; the second warm run
  completed in 5.93s pytest / 7.37s wall.
- StabilityPool comprehensive fuzz: 4 passed across the retained 40/20/40/40
  example budgets in 143.65s pytest / 178.72s wall.

The final default-lane comparison used isolated caches, one serial worker, local
fork policy, the non-secret Etherscan placeholder, and unset RPC/secret-shaped
variables on both trees. Because the marker annotations that exclude 135
release/fuzz/gas tests exist only in the candidate patch, pristine RH used
equivalent explicit ignores/deselection. Both sides therefore executed the same
3,244 test cases in the same order.

| Tree | Cache | Pytest | Wall (`real`) | Outcome |
|---|---|---:|---:|---|
| Pristine final RH `2c026b0` | fresh isolated | 727.77s | 790.35s | 3,205 passed, 13 failed, 25 errors, 1 xfailed |
| Rebound candidate `25b9220` | warm isolated | 711.79s | 769.63s | 3,205 passed, 13 failed, 25 errors, 1 xfailed |

The ordered JUnit records match exactly for all 3,244 nodes, including outcome
classification. A separate nine-module replay also matched exactly: each tree
reported 494 passed, 12 failed, and 25 errors with the same 37 non-passing node
ids. The full Teller subtree passed identically on both trees (268 passed); the
additional Teller withdrawal failure requires earlier full-suite state and was
then reproduced at the same collection position on pristine RH. Therefore the
current 13-failure/25-error set is pre-existing on final RH, and the rebound
candidate introduces no new failing or erroring node. The candidate's first cold
pass took 924.15s wall, but its detailed pytest summary was lost to execution
transport truncation, so no unsupported cold pytest-duration claim is made.

The manual-only workflow parses locally and retains explicit lean/comprehensive
selection, pinned actions, isolated runtime directories, and rolling Titanoboa
cache keys. It was not dispatched because the exactly reproduced RH baseline
failures would intentionally leave either full default run red. Automatic PR and
push triggers remain absent under the owner's prior manual-only authorization.

### Failure and omitted-work record

- Pre-edit artifact checker fingerprint: `CreditEngine` source SHA-256 expected
  `48b81f3c3b2218b4075cc4c84d9940aba85d24c315bef61e9f17c1f9d9382f7a`,
  observed `d8fae4e9cffff0d95adbe48a59e57c622585f021017b94089f8a70e615c36e43`.
  A final focused `scripts/export_abis.py --check` run also confirmed changed
  outputs for `DefaultsRobinhood`, `Ledger`, `MissionControl`, `RipeGov`,
  `SwitchboardCharlie`, `SwitchboardEcho`, and `Teller`. The earlier note that
  the ABI checker passed was incorrect and is withdrawn. Neither expectation nor
  any generated output was changed.
- Final default failures: 1 Teller action-block failure, 6 Teller deposit failures,
  13 Ledger action-block failures, 2 BlueChip Morpho V2 failures plus 25 setup
  errors from a 10-argument constructor receiving 11 arguments, and 1 BasicVault
  consumer-inventory failure. No changed implementation file appears in this
  failure set. Follow-up review ran the five failing modules in a git-backed
  worktree at the frozen commit and reproduced the exact 23-failure/25-error set;
  three delivered-tree full-lane runs also produced byte-identical failing node
  ids (reviewer-verified, 2026-08-06). Final-report item 11 is therefore closed:
  no default-lane failure was introduced by this implementation.
- The dependency evidence module now collects without IPython. Its specific rich
  rendering test fails clearly at execution with `ModuleNotFoundError: IPython`
  in the incomplete `ripe-lite` environment, as required.
- A follow-up run closed the previously unexecuted `tests/deployment/**` gap:
  706 passed, 15 failed, 1 skipped, and the archive-qualification node was safely
  deselected by local fork policy. Git-backed baseline and lock-faithful-environment
  checks split the failures precisely (reviewer-verified, 2026-08-06): 10 are
  pre-existing repository-state failures (one ABI-currentness, one
  manifest-schema, one Robinhood blueprint
  source-authority, and seven historical stock-launch bindings); five are
  `ripe-lite` dependency drift and all pass in the lock-faithful Python 3.12
  environment with IPython 9.8.0. CI installs `requirements.txt`, so a manual
  comprehensive deployment-subtree run is expected to report the 10
  repository-state failures rather than all 15 local failures.
  The 45 dependency-gate items that aborted collection on the frozen source now
  execute as 40 passes plus those five environment-attributable failures. No
  expectation, artifact, production contract, or release evidence was changed.
- The comprehensive suite was not run. Artifact/ABI compiler-pipeline refactoring
  was therefore not triggered by the conditional 15-minute threshold.
- `pytest-xdist` was absent and the owner allowed only one final default-lane
  measurement, so the required serial/three-parallel-run retention experiment was
  not run. xdist was not retained and requirements/config remain serial.
- The new workflow was parsed locally but GitHub Actions was not available for an
  end-to-end CI execution. Follow-up review established that the lean lane's
  accepted 23-failure/25-error baseline would make every pull-request run red.
  The owner explicitly authorized a temporary manual-only workflow in this Codex
  task on 2026-08-06 by replying, "yes manual only fine for now"; manual dispatch
  can select either the lean or comprehensive lane. Automatic PR
  coverage, push coverage, and criterion 12 remain explicitly open until the
  baseline failures are triaged. The lean condition defaults safely for a future
  non-dispatch trigger. Titanoboa caching uses rolling per-run keys, hashes both
  Vyper sources and interfaces, restores first from the exact input-hash prefix
  and then the broader Python/platform prefix, and uses an explicit
  `if: always()` save. A cancelled, install-failed, or otherwise partial run can
  therefore cause at most one suboptimal restore rather than permanently occupy
  the primary key. Unraisable-exception assurance remains in the manual
  comprehensive selection.
- One ignored current-worktree bytecode file reappeared under
  `tests/deployment/__pycache__/` after the deployment-subtree run despite the
  private `PYTHONPYCACHEPREFIX`. It contained no deleted-worktree path and was
  removed again; zero bytecode files reference the deleted
  `basic-vault-fail-closed` worktree. A deployment test or subprocess can still
  write bytecode outside the prefix, so this cleanup is not self-maintaining.
- Local workflow validation explicitly checked: manual `workflow_dispatch`, the
  future-trigger-safe lean condition, 30/120-minute lane timeouts, pinned restore
  and save subactions, rolling `github.run_id` primary keys, both restore prefixes,
  inclusion of `interfaces/**/*.vyi`, and the `always()` save condition.
  The reviewer also checked the pinned cache subactions' actual `action.yml` files:
  `cache-primary-key` is a real restore output and both subactions are main-only,
  so the explicit save step is the component that persists a failed run's cache
  (reviewer-verified, 2026-08-06).

## Final verification and handoff

Before reporting completion, run:

```bash
git diff --check
git status --short --branch
git diff --stat
git diff --numstat
```

Because this plan begins untracked, also run:

```bash
git diff --no-index --check /dev/null docs/chains/rh/rh-test-speed-implementation-plan.md
git diff --no-index --numstat /dev/null docs/chains/rh/rh-test-speed-implementation-plan.md
```

For the two `--no-index` commands, exit status 1 is expected because the files differ; whitespace-check output must be empty. Normal `git diff` output does not include untracked files, so the final scope report must reconcile `git status` with both normal and no-index numstat.

The final report must include:

1. Starting and ending commit/tree
2. Exact changed-file list and numstat
3. Before/after timing table following the required protocol
4. Default and comprehensive collection counts
5. Fixture-graph proof for pure tests
6. Unraisable-plugin loading proof for each lane
7. Uniswap behavior-inventory comparison
8. Fuzz-budget proof
9. Serial/parallel experiment result and whether xdist was retained
10. CI workflow result, if the environment permits it
11. Pre-existing versus newly introduced failure comparison
12. Any unmet target, with a ranked residual-duration table

Do not describe the work as complete if only pytest's internal timer improved, if the default command still aborts, or if excluded test categories cannot be invoked explicitly.
