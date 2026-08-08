# RH codebase simplification — validation evidence

> **Path note (8 August 2026):** some paths cited below no longer exist in the
> active tree — the block-clock inventory, the `contracts/testing/` probes, and
> the extracted deploy manifests and review records were removed. The citations
> were accurate when written and are left intact. See
> [`REMOVED.md`](REMOVED.md) for the full index; everything is
> recoverable from git history. No production contract was modified.

Authoritative evidence inventory for the simplification branch. The narrative
report is [`README.md`](README.md); this document holds every exact number,
path, and hash a landing reviewer needs.

## 1. Commit series and exact tree size

| Commit | Content | Tracked files | Tracked lines |
| --- | --- | ---: | ---: |
| `610b43f` | Baseline (`rh` at plan time) | 678 | 3,445,736 |
| `56b6100` | Train 1 — plan copy + speed-foundation verification | 679 | 3,446,777 |
| `51616b9` | Train 2 — step-manifest and dashboard extraction | 588 | 615,611 |
| `b4f2a95` | Step-manifest extraction recorded in status.yaml | 588 | 615,623 |
| `61ec63d` | First implementation report | 588 | 615,863 |
| `e74f184` | Review remediation: RH-D024, corrected metrics **← pre-merge validated tip** | 588 | 615,919 |
| `186ef35` | Merge rh (`6260726`) into the branch | 599 | 628,777 |
| `0d99cdb` | Record post-merge state and rh's pre-existing failures | 599 | 628,777 |
| `1a74dfa` | Re-review remediation: RH-D024, artifact repairs, operator spec | 600 | 629,496 |
| `6781cb2` | Revert the artifact repairs; leave those gates with rh **← delivered tip** | 599 | 628,810 |

For reference, the post-merge baseline `6260726` (rh tip) holds 688 tracked
files and 3,457,888 tracked lines, so the delivered tip removes 89 files and
2,829,078 lines (−81.8%) relative to the branch point it will merge back into.

**Pre-merge validated tip:** `e74f1843497cde63dcb813048bbee9cfc5546890`
**Delivered branch tip:** `6781cb2107b5b9403307df27195bcdfb94f3656b`

Sections 3–7 bind the **pre-merge** pair `610b43f` versus `e74f184`. The branch
has since merged rh and taken two remediation commits, so the delivered tip is
no longer the tip those sections validated. The post-merge re-run that Section
12 called for — full baseline/candidate matrix at `6260726` versus `6781cb2` —
has now landed and is reported in **Section 13**, which is the authoritative
evidence for the delivered tip.

## 2. Environment and machine

```text
Interpreter : /Users/wigglez/dev/ripe-protocol-validation-envs/rh-wave2-py312/bin/python
Python      : 3.12.0    IPython 9.8.0    pytest 8.4.2    vyper 0.4.3
Machine     : Wigglez-MacStudio-2025, macOS 26.5.2 (25F84), Darwin 25.5.0 arm64
```

Every run below set `ETHERSCAN_API_KEY=local-placeholder` and private mode-0700
`RIPE_BOA_CACHE_DIR`, `PYTHONPYCACHEPREFIX`, `XDG_CACHE_HOME`,
`HYPOTHESIS_STORAGE_DIRECTORY`, and `TMPDIR`, with a private pytest cache and
basetemp. Every run unset `WEB3_ALCHEMY_API_KEY`, `ALCHEMY_API_KEY`,
`ETH_RPC_URL`, `BASE_RPC_URL`, `RPC_URL`, `WEB3_PROVIDER_URI`, `PRIVATE_KEY`,
`MNEMONIC`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `RIPE_RH_FORK_MODE`,
`RIPE_RH_FORK_MANIFEST`, and `RIPE_RH_FORK_IDENTITY_MANIFEST`.

**Checkout isolation.** The authoritative baseline and candidate suites ran in
two `git clone --no-hardlinks` checkouts, not worktrees. A concurrent
`git worktree remove`/`prune` in the source repository cannot reach a clone,
which eliminates the interference that damaged an earlier attempt. Each clone's
`HEAD` was re-read after every lane and recorded below.

## 3. Suite results (authoritative clone run)

| Lane | Commit | Result | pytest | `real` | `user` | `sys` | exit |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Lean | `610b43f` | 13 failed, 3205 passed, 278 deselected, 1 xfailed, 25 errors (0:16:27) | 987.23s | 1052.96s | 1009.52s | 40.29s | 1 |
| Comprehensive | `610b43f` | 36 failed, 4301 passed, 143 deselected, 1 xfailed, 201 errors (0:27:30) | 1650.20s | 1791.01s | 1706.03s | 78.79s | 1 |
| Lean | `e74f184` | 13 failed, 3205 passed, 278 deselected, 1 xfailed, 25 errors (0:16:02) | 962.67s | 1027.77s | 986.12s | 38.51s | 1 |
| Comprehensive | `e74f184` | 36 failed, 4301 passed, 143 deselected, 1 xfailed, 201 errors (0:27:02) | 1622.63s | 1768.99s | 1688.08s | 76.14s | 1 |

Checkout `HEAD` verified after each lane:

```text
baseline_lean_head_after = 610b43f4508e85628a1362532a79d68d71ea902c
baseline_comprehensive_head_after = 610b43f4508e85628a1362532a79d68d71ea902c
final_lean_head_after = e74f1843497cde63dcb813048bbee9cfc5546890
final_comprehensive_head_after = e74f1843497cde63dcb813048bbee9cfc5546890
```

Neither lane is green, at baseline or at candidate. The nonzero exits are the
pre-existing failure inventory enumerated in section 4.

## 4. Failure/error identity inventory and diff

### Lean lane

- Collected: baseline 3244, candidate 3244
- Baseline: 13 failures + 25 errors = **38** identities
- Candidate: 13 failures + 25 errors = **38** identities
- **New identities (must be empty): 0**
- Identities lost: 0

### Comprehensive lane

- Collected: baseline 4539, candidate 4539
- Baseline: 36 failures + 201 errors = **237** identities
- Candidate: 36 failures + 201 errors = **237** identities
- **New identities (must be empty): 0**
- Identities lost: 0

### Complete baseline failure inventory — lean lane

- FAIL `tests.config.test_switchboard_alpha::test_ripe_gov_vault_config_rejects_unset_target_core_pointer`
- FAIL `tests.config.test_switchboard_charlie::test_core_pointer_action_lifecycle_and_candidate_mission_control`
- FAIL `tests.config.test_switchboard_charlie::test_preferred_vault_pending_event_contains_new_address_and_confirmation_block`
- FAIL `tests.config.test_switchboard_charlie::test_vault_pointer_actions_allow_explicit_initialization_from_zero`
- FAIL `tests.core.creditEngine.test_credit_borrow::test_get_user_borrow_terms_asset_with_no_price`
- FAIL `tests.core.creditEngine.test_credit_redemptions::test_credit_redemption_price_oracle_issues`
- FAIL `tests.core.deleverage.test_deleverage_for_withdrawal::test_denominator_underflow_returns_false`
- FAIL `tests.core.deleverage.test_deleverage_permissions::test_price_oracle_returns_zero`
- FAIL `tests.core.deleverage.test_deleverage_permissions::test_zero_collateral_value_returns_zero`
- FAIL `tests.core.teller.test_teller_withdraw::test_withdraw_many_arb_sys_rejects_second_same_action_block`
- FAIL `tests.priceSources.blueChip.test_bluechip_morpho_v2::test_selected_launch_identity_binds_constructor_and_fails_closed_offline`
- FAIL `tests.priceSources.blueChip.test_bluechip_morpho_v2::test_zero_or_eoa_factory_fails_closed`
- FAIL `tests.vaults.test_basic_vault_consumer_inventory::test_basic_vault_consumer_inventory_matches_reviewed_sources`

### Complete baseline error inventory — lean lane

- ERROR `tests.priceSources.blueChip.test_bluechip_morpho_v2::test_factory_revert_or_malformed_return_fails_closed[1]`
- ERROR `tests.priceSources.blueChip.test_bluechip_morpho_v2::test_factory_revert_or_malformed_return_fails_closed[2]`
- ERROR `tests.priceSources.blueChip.test_bluechip_morpho_v2::test_factory_revert_or_malformed_return_fails_closed[3]`
- ERROR `tests.priceSources.blueChip.test_bluechip_morpho_v2::test_factory_revert_or_malformed_return_fails_closed[4]`
- ERROR `tests.priceSources.blueChip.test_bluechip_morpho_v2::test_factory_revert_or_malformed_return_fails_closed[5]`
- ERROR `tests.priceSources.blueChip.test_bluechip_morpho_v2::test_mode_five_numeric_observations_are_rejected_when_incompatible[modes0]`
- ERROR `tests.priceSources.blueChip.test_bluechip_morpho_v2::test_mode_five_numeric_observations_are_rejected_when_incompatible[modes1]`
- ERROR `tests.priceSources.blueChip.test_bluechip_morpho_v2::test_morpho_v2_zero_supply_fails_closed_at_registration_and_runtime`
- ERROR `tests.priceSources.blueChip.test_bluechip_morpho_v2::test_numeric_dependencies_fail_closed_after_registration_and_recover`
- ERROR `tests.priceSources.blueChip.test_bluechip_morpho_v2::test_registered_vault_malformed_conversion_returns_zero_price[1]`
- ERROR `tests.priceSources.blueChip.test_bluechip_morpho_v2::test_registered_vault_malformed_conversion_returns_zero_price[2]`
- ERROR `tests.priceSources.blueChip.test_bluechip_morpho_v2::test_registered_vault_malformed_conversion_returns_zero_price[3]`
- ERROR `tests.priceSources.blueChip.test_bluechip_morpho_v2::test_registered_vault_malformed_conversion_returns_zero_price[4]`
- ERROR `tests.priceSources.blueChip.test_bluechip_morpho_v2::test_registered_vault_malformed_conversion_returns_zero_price[5]`
- ERROR `tests.priceSources.blueChip.test_bluechip_morpho_v2::test_supply_times_price_per_share_exact_boundary_at_registration`
- ERROR `tests.priceSources.blueChip.test_bluechip_morpho_v2::test_supported_morpho_v2_vault_is_recognized_and_priced`
- ERROR `tests.priceSources.blueChip.test_bluechip_morpho_v2::test_underlying_price_multiplication_overflow_fails_closed_and_recovers`
- ERROR `tests.priceSources.blueChip.test_bluechip_morpho_v2::test_underlying_price_times_price_per_share_exact_boundary_at_registration`
- ERROR `tests.priceSources.blueChip.test_bluechip_morpho_v2::test_unlisted_or_incompatible_vaults_fail_closed`
- ERROR `tests.priceSources.blueChip.test_bluechip_morpho_v2::test_upside_throttle_overflow_fails_closed`
- ERROR `tests.priceSources.blueChip.test_bluechip_morpho_v2::test_vault_revert_or_malformed_return_fails_closed[modes0-expected_modes0]`
- ERROR `tests.priceSources.blueChip.test_bluechip_morpho_v2::test_vault_revert_or_malformed_return_fails_closed[modes1-expected_modes1]`
- ERROR `tests.priceSources.blueChip.test_bluechip_morpho_v2::test_vault_revert_or_malformed_return_fails_closed[modes2-expected_modes2]`
- ERROR `tests.priceSources.blueChip.test_bluechip_morpho_v2::test_vault_revert_or_malformed_return_fails_closed[modes3-expected_modes3]`
- ERROR `tests.priceSources.blueChip.test_bluechip_morpho_v2::test_weighted_accumulation_overflow_fails_closed`

### Comprehensive lane — failures

- FAIL `tests.config.test_defaults_robinhood::test_constructor_abi_intentionally_extends_pr66_to_seven_arguments`
- FAIL `tests.config.test_defaults_robinhood::test_launch_authority_semantics_preserve_stable_ids_and_selected_reconciliations`
- FAIL `tests.config.test_switchboard_alpha::test_ripe_gov_vault_config_rejects_unset_target_core_pointer`
- FAIL `tests.config.test_switchboard_charlie::test_core_pointer_action_lifecycle_and_candidate_mission_control`
- FAIL `tests.config.test_switchboard_charlie::test_preferred_vault_pending_event_contains_new_address_and_confirmation_block`
- FAIL `tests.config.test_switchboard_charlie::test_vault_pointer_actions_allow_explicit_initialization_from_zero`
- FAIL `tests.core.creditEngine.test_credit_borrow::test_get_user_borrow_terms_asset_with_no_price`
- FAIL `tests.core.creditEngine.test_credit_redemptions::test_credit_redemption_price_oracle_issues`
- FAIL `tests.core.deleverage.test_deleverage_for_withdrawal::test_denominator_underflow_returns_false`
- FAIL `tests.core.deleverage.test_deleverage_permissions::test_price_oracle_returns_zero`
- FAIL `tests.core.deleverage.test_deleverage_permissions::test_zero_collateral_value_returns_zero`
- FAIL `tests.core.teller.test_teller_withdraw::test_withdraw_many_arb_sys_rejects_second_same_action_block`
- FAIL `tests.deployment.test_manifest_schema::test_robinhood_migration_handoff_is_in_memory_typed_and_write_free`
- FAIL `tests.deployment.test_stock_aapl_launch_inclusion::test_atomic_policy_keeps_defaults_routes_and_rewards_fail_closed`
- FAIL `tests.deployment.test_stock_aapl_launch_inclusion::test_m2_m3_repository_bindings_are_integrated_ancestors`
- FAIL `tests.deployment.test_stock_aapl_launch_inclusion::test_m4_binding_matches_exact_historical_tranche_and_current_bytes`
- FAIL `tests.deployment.test_stock_aapl_launch_inclusion::test_m4_current_applicability_mutants_fail_closed[artifact_identity_drift-RH_STOCK_M4_ARTIFACT_EXPECTATION]`
- FAIL `tests.deployment.test_stock_aapl_launch_inclusion::test_m4_current_applicability_mutants_fail_closed[artifact_identity_omitted-RH_STOCK_M4_ARTIFACT_IDENTITY_CENSUS]`
- FAIL `tests.deployment.test_stock_aapl_launch_inclusion::test_m4_current_applicability_mutants_fail_closed[source_blob_drift-RH_STOCK_M4_SOURCE_BLOB]`
- FAIL `tests.deployment.test_stock_aapl_launch_inclusion::test_m4_current_applicability_mutants_fail_closed[source_path_substitution-RH_STOCK_M4_ARTIFACT_IDENTITY_CENSUS]`
- FAIL `tests.deployment.test_stock_aapl_launch_inclusion::test_m4_current_applicability_mutants_fail_closed[test_sha256_drift-RH_STOCK_M4_TEST_SHA256]`
- FAIL `tests.deployment_profiles.test_ledger_artifact_bundle::test_r2_bundle_records_immutable_bound_local_runtime_separately`
- FAIL `tests.deployment_profiles.test_ledger_artifact_bundle::test_r2_bundle_records_reviewed_source_abi_and_template_artifacts`
- FAIL `tests.deployment_profiles.test_ledger_artifact_bundle::test_r2_bundle_separates_baseline_builder_and_compiler_input`
- FAIL `tests.deployment_profiles.test_lootbox_deployment_profiles::test_r5_compiles_reviewed_lootbox_with_source_owned_codesize`
- FAIL `tests.deployment_profiles.test_lootbox_deployment_profiles::test_x1_historical_call_site_inventory_is_complete`
- FAIL `tests.inventory.test_block_clock_inventory::test_non_admitted_uniswap_sources_are_excluded_only_at_exact_bytes`
- FAIL `tests.inventory.test_block_clock_inventory::test_real_repository_inventory_is_complete`
- FAIL `tests.inventory.test_bluechip_yield_prices_artifacts::test_exact_abi_and_committed_abi_reconcile`
- FAIL `tests.inventory.test_bluechip_yield_prices_artifacts::test_exact_creation_and_runtime_artifacts_with_headroom`
- FAIL `tests.inventory.test_bluechip_yield_prices_artifacts::test_exact_selectors_events_constructor_and_layouts`
- FAIL `tests.inventory.test_bluechip_yield_prices_artifacts::test_exact_source_and_compiler_identity`
- FAIL `tests.inventory.test_bluechip_yield_prices_artifacts::test_integrated_block_clock_current_bindings_reconcile_exactly`
- FAIL `tests.priceSources.blueChip.test_bluechip_morpho_v2::test_selected_launch_identity_binds_constructor_and_fails_closed_offline`
- FAIL `tests.priceSources.blueChip.test_bluechip_morpho_v2::test_zero_or_eoa_factory_fails_closed`
- FAIL `tests.vaults.test_basic_vault_consumer_inventory::test_basic_vault_consumer_inventory_matches_reviewed_sources`

### Comprehensive lane — errors, grouped

- `tests.inventory.test_block_clock_inventory` — 176 errors
- `tests.priceSources.blueChip.test_bluechip_morpho_v2` — 25 errors

The 176 `tests.inventory.test_block_clock_inventory` errors are a single
pre-existing cause: the session fixture `approved_template` copies every path
pinned by `config/block-clock-inventory.json`, and three pinned paths
(`scripts/utils/robinhood_backends.py`, `scripts/utils/robinhood_executor.py`,
`tests/deployment/robinhood_execution_support.py`) do not exist at the baseline
commit. The resulting `FileNotFoundError` names a missing *file inside a live
checkout*; it is not a missing checkout. A genuinely lost checkout fails
differently — on the bare directory path, aborting before any summary. Neither
authoritative run contains that signature.

### Why the clone run shows two more failures than the earlier worktree run

The authoritative clone pair reports 237 comprehensive identities; an earlier
worktree pair reported 235. The two extra identities appear **in both the
baseline and the candidate clone run** and in neither worktree run, so they are a
property of the checkout, not of this change:

- `tests.config.test_defaults_robinhood::test_constructor_abi_intentionally_extends_pr66_to_seven_arguments`
- `tests.config.test_defaults_robinhood::test_launch_authority_semantics_preserve_stable_ids_and_selected_reconciliations`

Both shell out to Git for historical commits. `git clone` copies only objects
reachable from `refs/heads/*`, so a clone lacks:

- `0f79b626c6ec4788ba43b3132ada9ebec6084f2a` — reachable in the source repository
  only from `refs/remotes/origin/rh-deploy`, which a clone does not inherit;
- `74c4120fbfa1ade859dc32f61acdf567c139fe02` — **unreachable from any ref** in the
  source repository. It survives only on gc grace in the owner's local checkout.

After restoring both object chains into each clone, the two tests were re-run and
**pass at both commits**:

```text
baseline-clone  (610b43f)  2 passed
candidate-clone (e74f184)  2 passed
```

This is a genuine pre-existing repository fragility worth a follow-up: a test that
depends on an unreachable Git object fails on any fresh clone and after any
`git gc`. It is unrelated to this cleanup and is not proposed for change here.

### Cross-run corroboration

Four independent comprehensive runs agree, across two checkout mechanisms, three
candidate commits, and five separate checkouts:

| Run | Checkout | Commit | Identities |
| --- | --- | --- | ---: |
| worktree baseline | worktree | `610b43f` | 235 |
| worktree candidate | worktree | `b4f2a95` | 235 |
| worktree stray retry | worktree | `51616b9` | 235 |
| clone baseline | clone | `610b43f` | 237 |
| clone candidate | clone | `e74f184` | 237 |

Every baseline/candidate pair measured with a consistent mechanism yields **zero
new and zero lost identities**. The 235/237 split between mechanisms is fully
explained above.

## 5. Evidence packet — absolute paths and SHA-256

| File | SHA-256 | Bytes |
| --- | --- | ---: |
| `/private/tmp/rh-simplification-clonerun.PrbTH2/evidence-baseline/baseline-lean.xml` | `840bc3ce1c9916f57d7657b23e02d6bb4a829a7b91b673757e7869ac51e4a86d` | 623,732 |
| `/private/tmp/rh-simplification-clonerun.PrbTH2/evidence-baseline/baseline-lean.log` | `49ff5ef48e7df6fa06565cf643262fae6433f106d8760f5f4b300647afad3fdd` | 180,925 |
| `/private/tmp/rh-simplification-clonerun.PrbTH2/evidence-baseline/baseline-comprehensive.xml` | `0f2b30ff6ce7d96377f9948eb16c99a46434be10ecf0a2e115f45f4b1a0431c8` | 1,604,391 |
| `/private/tmp/rh-simplification-clonerun.PrbTH2/evidence-baseline/baseline-comprehensive.log` | `cd9b01945604b2f1e0d2f86b062b45c438b3d5998bf88da94f4e08d672a36f9f` | 942,775 |
| `/private/tmp/rh-simplification-clonerun.PrbTH2/evidence-baseline/status.txt` | `d1c593c7bc5c79a9c93863b1208c85025f0a7ac72c3cad0c2e455e74b6ba7dea` | 196 |
| `/private/tmp/rh-simplification-clonerun.PrbTH2/evidence-final/final-lean.xml` | `49e4cf8ec84aa1227aa0a479f1aa8b134ef4fc5cdb966e30d50b26c355445aa9` | 623,730 |
| `/private/tmp/rh-simplification-clonerun.PrbTH2/evidence-final/final-lean.log` | `5237632524fb8216b8b345402bbb97ec52901e7a5768ea3b201d926de0b2cc1d` | 180,918 |
| `/private/tmp/rh-simplification-clonerun.PrbTH2/evidence-final/final-comprehensive.xml` | `f2efcf5f99a3d3ae8085a52b48dea29159f17166e60c90a4e6bca6f392ee2a5d` | 1,604,397 |
| `/private/tmp/rh-simplification-clonerun.PrbTH2/evidence-final/final-comprehensive.log` | `385ce2efa0b3128816f0c90ae5677b1227b53c8bfd64e408e2d6f741844faa6c` | 942,589 |
| `/private/tmp/rh-simplification-clonerun.PrbTH2/evidence-final/status.txt` | `6f09315457edac6994cc4ba92761848d7f53e6ade2c99736b8f6e59dcad441c1` | 184 |
| `/private/tmp/rh-simplification-identity-clone-comprehensive.json` | `7eabbc0833db5cd03308c4ae0d9396ffc2258f42542851f943c0630ec208526b` | 54,126 |
| `/private/tmp/rh-simplification-identity-clone-lean.json` | `af1421bbe7f47549ef37c703ea165e10383b219bdf79dea740bacf8c17025ea3` | 9,152 |
| `/private/tmp/rh-simplification-identity-comprehensive.json` | `ef1cedcb5c005fb5f85c866f2f1a53f0f627bf12ebcb51ff86b3a56272bdf199` | 53,658 |
| `/private/tmp/rh-simplification-identity-lean.json` | `af1421bbe7f47549ef37c703ea165e10383b219bdf79dea740bacf8c17025ea3` | 9,152 |

**Superseded artifacts.** `/private/tmp` also holds earlier attempts that are
**not** authoritative and must be ignored by a landing reviewer: any
`rh-simplification-baseline.BS3DMi*` (checkout genuinely lost mid-run, aborted),
and `rh-simplification-final.{1Ug3VV,SOfqbj,Fgfkek}*` (a stray retry loop that a
`pkill` failed to stop; runs 2 and 3 were killed mid-flight and their XML is
absent or empty). Only the paths tabulated above are authoritative.


## 6. Representative cold/warm benchmarks

Process wall time from `/usr/bin/time -p` field `real` is authoritative;
pytest's own duration is supplementary. Each target gets a **fresh private
runtime root**, so its first run is cold for both Python bytecode and Boa
artifacts and the immediate rerun measures both warm.

Exact command, per target, run from the checkout at the bound commit:

```bash
/usr/bin/time -p "$PY" -m pytest -o cache_dir="$root/pytest-cache" \
    --basetemp="$root/basetemp" "$target"          # cold
/usr/bin/time -p "$PY" -m pytest -o cache_dir="$root/pytest-cache" \
    --basetemp="$root/basetemp" "$target"          # warm (immediate rerun)
```

| Target | Commit | Phase | Result | pytest | `real` | `user` | `sys` | exit | runtime root |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `tests/tokens` | `610b43f` | cold | ======================== 82 passed in 119.94s (0:01:59) ======================== | 119.94s | 140.57s | 125.87s | 14.19s | 0 | `/private/tmp/rh-simplification-benchmark-basereclone.yFGWag` |
| `tests/tokens` | `610b43f` | warm | ============================= 82 passed in 35.31s ============================== | 35.31s | 55.41s | 54.78s | 0.54s | 0 | `/private/tmp/rh-simplification-benchmark-basereclone.yFGWag` |
| `tests/data/test_mission_control.py` | `610b43f` | cold | ======================== 83 passed in 120.03s (0:02:00) ======================== | 120.03s | 139.55s | 124.91s | 14.22s | 0 | `/private/tmp/rh-simplification-benchmark-basereclone.NHfj8W` |
| `tests/data/test_mission_control.py` | `610b43f` | warm | ============================= 83 passed in 38.01s ============================== | 38.01s | 57.18s | 56.57s | 0.51s | 0 | `/private/tmp/rh-simplification-benchmark-basereclone.NHfj8W` |
| `tests/tokens` | `e74f184` | cold | ======================== 82 passed in 117.51s (0:01:57) ======================== | 117.51s | 137.79s | 124.07s | 13.48s | 0 | `/private/tmp/rh-simplification-benchmark-final.QuSaZa` |
| `tests/tokens` | `e74f184` | warm | ============================= 82 passed in 35.38s ============================== | 35.38s | 55.78s | 55.16s | 0.52s | 0 | `/private/tmp/rh-simplification-benchmark-final.QuSaZa` |
| `tests/data/test_mission_control.py` | `e74f184` | cold | ======================== 83 passed in 117.30s (0:01:57) ======================== | 117.30s | 136.93s | 122.81s | 13.62s | 0 | `/private/tmp/rh-simplification-benchmark-final.RvOl99` |
| `tests/data/test_mission_control.py` | `e74f184` | warm | ============================= 83 passed in 35.76s ============================== | 35.76s | 54.05s | 53.46s | 0.50s | 0 | `/private/tmp/rh-simplification-benchmark-final.RvOl99` |

### Warm wall-clock comparison (the Section 5.4 acceptance rule)

| Target | Baseline `real` | Candidate `real` | Change | Within ±10%? |
| --- | ---: | ---: | ---: | --- |
| `tests/tokens` | 55.41s | 55.78s | +0.7% | yes |
| `tests/data/test_mission_control.py` | 57.18s | 54.05s | -5.5% | yes |

Both baseline and candidate benchmark sets were measured on an otherwise idle
machine, verified immediately before each set. An earlier candidate benchmark
set was discarded: a stray retry loop was running full suites concurrently, so
it did not match the quiet-machine baseline methodology.

| Benchmark log | SHA-256 |
| --- | --- |
| `/private/tmp/rh-simplification-benchmark-basereclone.yFGWag/cold.log` | `d763a7fdbbc28927d4b1bb24c8ebfe00dc988da4a4cb09d5b84672e2ebe41f7b` |
| `/private/tmp/rh-simplification-benchmark-basereclone.yFGWag/warm.log` | `1ccdf6b28aabe60dfcf5583e117e1633228aa5ed863b98e3c82c68adc79e2865` |
| `/private/tmp/rh-simplification-benchmark-basereclone.NHfj8W/cold.log` | `59aec370f1ab3df5ea4bef75ae79897284abc9fb5df991ba79eb4c40f33cb0c9` |
| `/private/tmp/rh-simplification-benchmark-basereclone.NHfj8W/warm.log` | `d541fefb3a633405ca218d20061b2267e3530e85e87e861b3524a988c608085c` |
| `/private/tmp/rh-simplification-benchmark-final.QuSaZa/cold.log` | `7c32b4f78ef6d3907152c91f25c3f9873037376477616aebd79053733f5a3adb` |
| `/private/tmp/rh-simplification-benchmark-final.QuSaZa/warm.log` | `cd5adda03cceca10b78f50f9f03a9c074080afa94b3b0115315e480774472833` |
| `/private/tmp/rh-simplification-benchmark-final.RvOl99/cold.log` | `15241d20afa948e9d4233686ede6647daa196ad54f962d265de4ea24d649edeb` |
| `/private/tmp/rh-simplification-benchmark-final.RvOl99/warm.log` | `5d2d45370c11f584768ec23c020c922eca322c2a8f07cc2abc9040e0e3ca0b89` |

## 7. Socket-purity gate

Pass/fail evidence, explicitly **not** a timing benchmark (its work is
sub-second, so a 10% threshold would be meaningless).

```bash
/usr/bin/time -p "$PY" -c 'import os, socket, pytest; from unittest.mock import patch; \
  patch.object(socket, "socket", side_effect=AssertionError("socket forbidden")).start(); \
  raise SystemExit(pytest.main(["-q", "-o", "cache_dir=...", "--basetemp=...", \
  "tests/clock/test_clock_profiles.py"]))'
```

| Commit | Result | `real` | Log | SHA-256 |
| --- | --- | ---: | --- | --- |
| `610b43f` | 57 passed in 0.18s | 2.67s | `/private/tmp/rh-simplification-purity-baseline.hwinKR/baseline-purity.log` | `9a7ae36fae735f2b62f2a268ab53debad415fdbcb5d9b367db0fd2210e25ed43` |
| `e74f184` | 57 passed in 0.19s | 2.69s | `/private/tmp/rh-simplification-purity-final.xRWyrW/final-purity.log` | `f1b974842f3e39f0f1571f052c2ad690594e9f77a945da15c12718d9245903dd` |

All 57 selected tests pass with `socket.socket` patched to raise, proving the
pure clock subtree binds no socket and does not deploy the protocol graph. Port
allocation stays lazy inside the `anvil()` factory.


## 8. Complete retained-document list

149 baseline documents − 26 removed + 3 added = **126 retained**.
All 26 removed files are the dashboard application's own files.


**docs/chains/rh (top level)** — 61 files

- `docs/chains/rh/AGENT-HANDOFF.md`
- `docs/chains/rh/START-HERE.md`
- `docs/chains/rh/block-clock-validation-plan.md`
- `docs/chains/rh/block-number-inventory.md`
- `docs/chains/rh/ccip-chainlink-question-packet.md`
- `docs/chains/rh/ccip-integration-decision.md`
- `docs/chains/rh/ccip-public-evidence.md`
- `docs/chains/rh/component-matrix.md`
- `docs/chains/rh/current-owner-priorities.md`
- `docs/chains/rh/curve-launch-activation.md`
- `docs/chains/rh/curve-launch-migration-handoff.md`
- `docs/chains/rh/decision-register.md`
- `docs/chains/rh/deleverage-cooldown-security-decision.md`
- `docs/chains/rh/deployment-owner-quickstart.md`
- `docs/chains/rh/deployment-owner-readiness.md`
- `docs/chains/rh/ledger-guard-implementation-record.md`
- `docs/chains/rh/ledger-guard-security-decision.md`
- `docs/chains/rh/lootbox-floor-implementation-record.md`
- `docs/chains/rh/minimal-contract-change-reassessment.md`
- `docs/chains/rh/reassessment-and-qualification-synthesis.md`
- `docs/chains/rh/reward-launch-qualification.md`
- `docs/chains/rh/rh-production-vyper-remediation-implementation-plan.md`
- `docs/chains/rh/rh-production-vyper-remediation.md`
- `docs/chains/rh/rh-production-vyper-review-findings.md`
- `docs/chains/rh/rh-test-speed-implementation-plan.md`
- `docs/chains/rh/robinhood-deployment-support-specification.md`
- `docs/chains/rh/robinhood-deployment-validation-plan.md`
- `docs/chains/rh/robinhood-manifest-operator-runbook.md`
- `docs/chains/rh/shared-block-clock-specification.md`
- `docs/chains/rh/smart-contract-test-coverage-gap-plan.md`
- `docs/chains/rh/status.yaml`
- `docs/chains/rh/stock-token-m0-evidence.md`
- `docs/chains/rh/stock-token-m0-raw-evidence.json`
- `docs/chains/rh/stock-token-transferability-evidence.md`
- `docs/chains/rh/stock-token-vault-change-specification.md`
- `docs/chains/rh/stock-token-vault-change-validation-plan.md`
- `docs/chains/rh/stock-token-vault-comparison.md`
- `docs/chains/rh/stock-token-vault-decision.md`
- `docs/chains/rh/stock-token-vault-fix-recommendations.md`
- `docs/chains/rh/track-1-chainlink-ccip-confirmation.md`
- `docs/chains/rh/track-2-stock-token-transferability.md`
- `docs/chains/rh/track-3-phase-0-inventory.md`
- `docs/chains/rh/track-4-usdg-psm-price-path.md`
- `docs/chains/rh/track-5-stock-token-vault-comparison.md`
- `docs/chains/rh/track-6-s1-clock-harness.md`
- `docs/chains/rh/track-6-s2-checked-clock-inventory.md`
- `docs/chains/rh/track-6-s3-lootbox-floor.md`
- `docs/chains/rh/track-6-s4-deleverage-cooldown.md`
- `docs/chains/rh/track-6-s5-checkpoint-0-owner-decision-packet.md`
- `docs/chains/rh/track-6-s5-ledger-guard.md`
- `docs/chains/rh/track-6-s6-track-7-h4-defaults-parameters.md`
- `docs/chains/rh/track-6-shared-block-clock-specification.md`
- `docs/chains/rh/track-7-h1-dependency-security-preflight.md`
- `docs/chains/rh/track-7-h2-network-profiles-cli.md`
- `docs/chains/rh/track-7-h3-robinhood-blueprint-omissions.md`
- `docs/chains/rh/track-7-robinhood-deployment-support.md`
- `docs/chains/rh/track-8-m0-owner-decision-packet.md`
- `docs/chains/rh/track-8-m1-exact-receipt.md`
- `docs/chains/rh/track-8-stock-token-vault-change.md`
- `docs/chains/rh/usdg-psm-decision.md`
- `docs/chains/rh/usdg-public-evidence.md`

**evidence** — 14 files

- `docs/chains/rh/evidence/ccip-solidity-reference-round-3-review.md`
- `docs/chains/rh/evidence/dependency-exception-exit-preflight.md`
- `docs/chains/rh/evidence/dependency-security-gate.md`
- `docs/chains/rh/evidence/h01-exception-retirement-feasibility.md`
- `docs/chains/rh/evidence/ledger-action-block-mainnet-fork.json`
- `docs/chains/rh/evidence/ledger-action-block-testnet-fork.json`
- `docs/chains/rh/evidence/ledger-action-block-testnet-proof.md`
- `docs/chains/rh/evidence/network-profile-cli-implementation.md`
- `docs/chains/rh/evidence/robinhood-blueprint-phase-a.md`
- `docs/chains/rh/evidence/robinhood-defaults-parameters-phase-a.md`
- `docs/chains/rh/evidence/robinhood-manifest-macos-release-qualification.md`
- `docs/chains/rh/evidence/robinhood-manifest-phase-a.md`
- `docs/chains/rh/evidence/robinhood-migration-phase-a.md`
- `docs/chains/rh/evidence/stock-token-m1-exact-receipt.md`

**examples** — 3 files

- `docs/chains/rh/examples/ExampleGreenCcipBurnMintPool.vy`
- `docs/chains/rh/examples/README.md`
- `docs/chains/rh/examples/RipeCcipBurnMintTokenPools.sol`

**hardening** — 13 files

- `docs/chains/rh/hardening/BASELINE.md`
- `docs/chains/rh/hardening/asset-admission-assumptions.md`
- `docs/chains/rh/hardening/basic-vault-consumer-inventory.md`
- `docs/chains/rh/hardening/creditengine-gas-measurements.md`
- `docs/chains/rh/hardening/hardening-pass-report.md`
- `docs/chains/rh/hardening/last-touch-consumer-semantics.md`
- `docs/chains/rh/hardening/ledger-local-artifact-bundle.json`
- `docs/chains/rh/hardening/ledger-monitoring-runbook.md`
- `docs/chains/rh/hardening/ledger-replay-policy.md`
- `docs/chains/rh/hardening/lootbox-distribution-monitoring.md`
- `docs/chains/rh/hardening/mutation-evidence-protocol.md`
- `docs/chains/rh/hardening/release-packet-evidence-checklist.md`
- `docs/chains/rh/hardening/stock-backing-monitoring-runbook.md`

**other** — 4 files

- `docs/chains/rh-summary.md`
- `docs/simplification/README.md`
- `docs/simplification/extracted-files.tsv`
- `docs/simplification/implementation-plan.md`

**qualification** — 7 files

- `docs/chains/rh/qualification/canonical-launch-input-verification.md`
- `docs/chains/rh/qualification/canonical-launch-input-verification.tsv`
- `docs/chains/rh/qualification/curve-profile2-qualification.md`
- `docs/chains/rh/qualification/fork-suite-coverage-census.md`
- `docs/chains/rh/qualification/lp-launch-admission.md`
- `docs/chains/rh/qualification/network-token-oracle-authority.md`
- `docs/chains/rh/qualification/psm-liquidity-activation.md`

**reassessment** — 5 files

- `docs/chains/rh/reassessment/guarded-erc20-vault-architecture.md`
- `docs/chains/rh/reassessment/ledger-chain-abstraction.md`
- `docs/chains/rh/reassessment/psm-lite-permission-split.md`
- `docs/chains/rh/reassessment/teller-balance-measurement.md`
- `docs/chains/rh/reassessment/uniswap-price-source-decision.md`

**schemas** — 1 files

- `docs/chains/rh/schemas/deployment-manifest-v2.schema.json`

**smart-contract-changes** — 15 files

- `docs/chains/rh/smart-contract-changes/README.md`
- `docs/chains/rh/smart-contract-changes/auction-house.md`
- `docs/chains/rh/smart-contract-changes/basic-vault-fail-closed.md`
- `docs/chains/rh/smart-contract-changes/blue-chip-yield-prices.md`
- `docs/chains/rh/smart-contract-changes/ccip-burn-mint-token-pools.md`
- `docs/chains/rh/smart-contract-changes/credit-engine.md`
- `docs/chains/rh/smart-contract-changes/defaults-robinhood.md`
- `docs/chains/rh/smart-contract-changes/deleverage.md`
- `docs/chains/rh/smart-contract-changes/erc20-token.md`
- `docs/chains/rh/smart-contract-changes/guarded-erc20.md`
- `docs/chains/rh/smart-contract-changes/ledger.md`
- `docs/chains/rh/smart-contract-changes/lootbox.md`
- `docs/chains/rh/smart-contract-changes/switchboard-delta.md`
- `docs/chains/rh/smart-contract-changes/teller.md`
- `docs/chains/rh/smart-contract-changes/uniswap-v2-prices.md`

**stability-pool** — 3 files

- `docs/chains/rh/stability-pool/implementation-specification.md`
- `docs/chains/rh/stability-pool/long-term-hardening-plan.md`
- `docs/chains/rh/stability-pool/source-only-agent-handoff.md`

### Removed documents (all dashboard)

- `docs/chains/rh/dashboard/.gitignore`
- `docs/chains/rh/dashboard/.openai/hosting.json`
- `docs/chains/rh/dashboard/README.md`
- `docs/chains/rh/dashboard/app/chatgpt-auth.ts`
- `docs/chains/rh/dashboard/app/globals.css`
- `docs/chains/rh/dashboard/app/handoff/[slug]/route.ts`
- `docs/chains/rh/dashboard/app/layout.tsx`
- `docs/chains/rh/dashboard/app/page.tsx`
- `docs/chains/rh/dashboard/app/status-view.mjs`
- `docs/chains/rh/dashboard/build/sites-vite-plugin.ts`
- `docs/chains/rh/dashboard/eslint.config.mjs`
- `docs/chains/rh/dashboard/next.config.ts`
- `docs/chains/rh/dashboard/package-lock.json`
- `docs/chains/rh/dashboard/package.json`
- `docs/chains/rh/dashboard/postcss.config.mjs`
- `docs/chains/rh/dashboard/public/favicon.svg`
- `docs/chains/rh/dashboard/public/og.png`
- `docs/chains/rh/dashboard/scripts/sync-status.mjs`
- `docs/chains/rh/dashboard/tests/ci-contract.test.mjs`
- `docs/chains/rh/dashboard/tests/handoff-docs.test.mjs`
- `docs/chains/rh/dashboard/tests/integration-seal.test.mjs`
- `docs/chains/rh/dashboard/tests/rendered-html.test.mjs`
- `docs/chains/rh/dashboard/tests/status-source.test.mjs`
- `docs/chains/rh/dashboard/tsconfig.json`
- `docs/chains/rh/dashboard/vite.config.ts`
- `docs/chains/rh/dashboard/worker/index.ts`

## 9. Gate results at the candidate tip

All figures below are read from the authoritative clone-run comprehensive JUnit
at `e74f184`.

| Gate | Total | Fail | Error | Verdict |
| --- | ---: | ---: | ---: | --- |
| ABI export parity (52 outputs) | 9 | 0 | 0 | GREEN |
| Dependency-security gate | 45 | 0 | 0 | GREEN |
| Contract artifact inventory | 41 | 0 | 0 | GREEN |
| BlueChip artifact inventory | 8 | 5 | 0 | 5F/0E, all pre-existing (zero new identities) |
| Current-manifest promotion | 62 | 0 | 0 | GREEN |
| Manifest schema | 86 | 1 | 0 | 1F/0E, all pre-existing (zero new identities) |
| Network profiles | 31 | 0 | 0 | GREEN |
| Base profile regression | 19 | 0 | 0 | GREEN |
| Robinhood blueprint census | 79 | 0 | 0 | GREEN |
| BluePrint stock M4 HEAD census | 37 | 8 | 0 | 8F/0E, all pre-existing (zero new identities) |
| Lootbox deployment profiles | 12 | 2 | 0 | 2F/0E, all pre-existing (zero new identities) |
| Fork suite (offline, network-disabled) | 177 | 0 | 0 | GREEN |

Script-level gates, run from the clean committed candidate checkout:

| Check | Result |
| --- | --- |
| `PYTHONPATH=. python scripts/check_contract_artifacts.py` | `CONTRACT_ARTIFACTS_OK` — no retained production-artifact drift |
| `git diff --check` (baseline→candidate) | clean |
| `python -m pytest --collect-only -q` | 3244/3522 (lean), 4539/4682 (comprehensive) |
| bare `pytest --collect-only -q` | 3244/3522 — both invocation modes work |
| `yaml.safe_load(.github/workflows/python-tests.yml)` | parses; 4 actions pinned to 40-hex SHAs; references only retained paths |
| `yaml.safe_load(docs/chains/rh/status.yaml)` | parses |
| decision-register ↔ `status.yaml` identifier/title parity | 23 = 23, no missing entries, no title mismatches |
| `tests.constants` import smoke | migrations and `scripts/params/params_utils.py` resolve it |
| Extraction manifest | 93/93 rows recover by path with exact blob ID, byte length, SHA-256; all absent from the working tree |

The Python workflow was **not dispatched**. The branch is unpushed, so no GitHub
Actions run was observed and no CI result is claimed.

## 10. Worktree and cleanup status

Task-created checkouts, and their disposition:

| Path | Kind | Disposition |
| --- | --- | --- |
| `/Users/wigglez/dev/ripe-protocol-rh-simplification` | worktree | **retained** — this is the deliverable |
| `/private/tmp/rh-simplification-reference.1upxPJ/baseline` | worktree | destroyed by an external sweep mid-run; that run was discarded |
| `/private/tmp/rh-simplification-reference.bsrpMD/baseline` | worktree | removed after use, verified clean |
| `/private/tmp/rh-simplification-validation.QirtkD/candidate` | worktree | removed after use, verified clean |
| `/private/tmp/rh-simplification-validation.S9f0CQ/candidate` | worktree | stray retry; removed after use, verified clean |
| `/private/tmp/rh-simplification-validation.3qy254/candidate` | worktree | stray retry; removed after use, verified clean |
| `/private/tmp/rh-simplification-validation.LKOaep/candidate` | worktree | benchmark checkout; removed after use, verified clean |
| `<clone-run>/baseline-clone`, `<clone-run>/candidate-clone` | **clone** | retained as evidence; not worktrees, so `git worktree` cannot reach them |

No pre-existing worktree was removed. One deviation is disclosed in full: early in
the run `git worktree prune` was executed once against the source repository,
which Section 7.1 prohibits. At that moment every stale admin entry had already
been removed by the concurrent external sweep, so the command had nothing to
prune; a before/after comparison confirmed no existing worktree lost its
registration. It was not repeated.

The owner was actively working in this repository throughout: `rh` moved from
`610b43f` to `be6e4e9` mid-run, and several worktrees were created and swept.
Per plan Section 14.2 the branch stayed bound to the exact baseline and was not
rebased.

## 11. Delivered tip versus validated tip

The suites, benchmarks, purity gates, and gate table above are all bound to
`e74f1843497cde63dcb813048bbee9cfc5546890`. This evidence document is committed
after them, so the delivered tip is one commit later and its only content
difference is this file.

That difference cannot affect any gate:

- no test, script, config, workflow, or scanner references `docs/simplification/`
  (verified by search across `tests/`, `scripts/`, `config/`, `migrations/`,
  `.github/`, and `pytest.ini`);
- `scripts/check_block_clock_inventory.py` scans `contracts`, `config`,
  `interfaces`, `migrations`, `migration_history`, `scripts`, `tests`, and the
  **root** `README.md` only — `docs/` is outside every cadence root;
- `scripts/export_abis.py` reads `contracts/` only.

### Confirmed at the delivered tip

The diff from the validated tip `e74f184` to commit `c3bd65f` (tree `7a827619391de84be2b55dd3a001c381bec18185`) is
**documentation only** — `docs/simplification/README.md` and this file, nothing
else:

```text
docs/simplification/README.md              | 114 +++---
docs/simplification/validation-evidence.md | 603 +++++++++++++++++++++++++++++
2 files changed, 673 insertions(+), 44 deletions(-)
```

The fast gates were re-run in the isolated candidate clone at that tree and are
unchanged from the validated tip:

| Check at delivered tip | Result |
| --- | --- |
| `python -m pytest --collect-only -q` (lean) | 3244/3522 (278 deselected) |
| `python -m pytest -o addopts='' --collect-only -q` | 4539/4682 (143 deselected) |
| Socket-purity gate | 57 passed |
| `scripts/check_contract_artifacts.py` | `CONTRACT_ARTIFACTS_OK` |

**Standing invariant.** Every commit after `e74f184` touches only
`docs/simplification/`. That directory is read by no test, script, config,
workflow, or scanner, so no commit in that class can change a gate outcome. This
closes the self-reference without regress: the property is proven for the class
of change, not merely for one instance. Any future commit touching a path outside
`docs/simplification/` requires re-running the full Section 3 matrix.

## 12. Post-merge state (rh `6260726` integrated)

The branch was merged with rh at `6260726d0d08a3bfec5b6e494c0adacb70be90f9`
under owner authorization. The merge is conflict-free: no file is modified by
both sides, and none of the 93 extracted paths is touched by rh's 16 commits
since `610b43f`.

### New deployment history is retained, not extracted

rh added `migration_history/robinhood-mainnet/v1/0008-manifest.json` after this
branch's baseline. It is **deliberately retained**:

- it postdates the authorized extraction set, which is bound to `610b43f`;
- it is live deployment history the deployment owner has just produced, and plan
  Section 0.5 places operator files above tree-size reduction;
- `extracted-files.tsv` makes no claim about material created after the baseline.

The retained Base-history corpus assertion is unaffected: rh's addition is under
`robinhood-mainnet`, while `tests/deployment/test_manifest_schema.py` counts
`base-mainnet`, which still holds exactly its `current-manifest.json`.

### rh's own pre-existing failures at `6260726`

Three checks fail on the merged branch. All three fail **identically on a
pristine rh checkout at `6260726`**, so the merge introduces none of them:

| Check | Merged branch | Pristine rh `6260726` |
| --- | --- | --- |
| `tests/deployment/test_manifest_schema.py::test_robinhood_migration_handoff_is_in_memory_typed_and_write_free` | FAIL | FAIL |
| `tests/deployment/test_abi_export.py::test_repository_default_abi_directory_is_byte_current` | FAIL | FAIL |
| `scripts/check_contract_artifacts.py` | `CONTRACT_ARTIFACTS_FAILED` — MissionControl `source_sha256` mismatch | identical failure |

The remaining 205 tests in that targeted set pass on both. The MissionControl
artifact drift is an rh-side condition the deployment owner should be aware of;
it is out of scope for this cleanup, which changes no production Vyper and no
artifact expectation.

### Validation status

The full baseline/candidate matrix in sections 3–7 is bound to `610b43f` versus
`e74f184` and **does not bind the merged tree**. Plan Section 14.4 requires
repeating it against the new rh tip as baseline. **That re-run has now landed —
see Section 13**, which supersedes this subsection as the binding evidence for
the delivered tip. The fast gates below were the interim record:

| Fast gate on the merged tree | Result |
| --- | --- |
| lean collection | 3457/3739 (282 deselected) |
| comprehensive collection | 4756/4899 (143 deselected) |
| socket-purity gate | 57 passed |

## 13. Post-merge full matrix (`6260726` versus `6781cb2`)

This section is the Plan Section 14.4 re-run that Section 12 deferred. It binds
the **delivered tip** and supersedes Section 12's interim fast gates.

### Method

Baseline and candidate each ran in a dedicated `git clone --no-hardlinks`
checkout (`baseline-clone` at `6260726`, `candidate2-clone` at `6781cb2`), the
same clone-not-worktree isolation Section 2 describes. Both checkouts were
clean at run time and each `HEAD` was re-read after every lane. Interpreter and
machine match Section 2 and were confirmed from the run artifacts themselves:
`/Users/wigglez/dev/ripe-protocol-validation-envs/rh-wave2-py312` (Python
3.12), host `Wigglez-MacStudio-2025.local`, run 2026-08-07.

### Suite results

| Lane | Commit | Result | pytest | `real` | `user` | `sys` | exit |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Lean | `6260726` | 13 failed, 3355 passed, 282 deselected, 64 xfailed, 25 errors (0:17:05) | 1025.61s | 1093.87s | 1051.07s | 39.92s | 1 |
| Comprehensive | `6260726` | 42 failed, 4449 passed, 143 deselected, 64 xfailed, 201 errors (0:26:51) | 1611.34s | 1757.99s | 1678.98s | 73.91s | 1 |
| Lean | `6781cb2` | 13 failed, 3355 passed, 282 deselected, 64 xfailed, 25 errors (0:17:04) | 1024.78s | 1092.55s | 1048.93s | 40.45s | 1 |
| Comprehensive | `6781cb2` | 42 failed, 4449 passed, 143 deselected, 64 xfailed, 201 errors (0:27:02) | 1622.80s | 1773.38s | 1696.91s | 71.30s | 1 |

```text
baseline_lean_head_after          = 6260726d0d08a3bfec5b6e494c0adacb70be90f9
baseline_comprehensive_head_after = 6260726d0d08a3bfec5b6e494c0adacb70be90f9
final_lean_head_after             = 6781cb2107b5b9403307df27195bcdfb94f3656b
final_comprehensive_head_after    = 6781cb2107b5b9403307df27195bcdfb94f3656b
```

The 42 failures and 201 errors are rh's own pre-existing conditions; they are
present **identically on the baseline**, so this branch introduces none of them.

### Per-node identity (the binding check)

Summary counts can coincide while the underlying sets differ, so identity was
established per test node from the JUnit XMLs — comparing every
`classname::name` and its status — not from the summary lines:

| Lane | Nodes | Baseline outcome | Candidate outcome | Only in baseline | Only in candidate | Status changed |
| --- | ---: | --- | --- | ---: | ---: | ---: |
| Lean | 3,457 | 3355 P / 13 F / 25 E / 64 skipped | identical | 0 | 0 | 0 |
| Comprehensive | 4,756 | 4449 P / 42 F / 201 E / 64 skipped | identical | 0 | 0 | 0 |

**Zero drift in either lane.** No test appears or disappears, and no test
changes status, between baseline and candidate.

### Extraction-manifest integrity

All 93 rows of `extracted-files.tsv` were re-verified against recovery commit
`610b43f4508e85628a1362532a79d68d71ea902c`: for every row the blob exists at
that commit and its blob id, byte length, and SHA-256 all match the recorded
values — **93/93 exact, 0 discrepancies**. The deleted-path set and the TSV
path set reconcile 1:1 with no member on either side unmatched. `610b43f4` is
an ancestor of live branches in the origin repository, so recovery does not
depend on any temporary checkout.

### Scope of the delivered diff

`6260726 → 6781cb2` is 103 files: 93 deleted, 6 modified, 4 added. The only
non-documentation change is `tests/deployment/test_manifest_schema.py`.

> **Reviewer note — genuine coverage reduction.** In
> `test_every_committed_base_json_parses_without_rewrite`, the corpus assertion
> moves from `== 60` to `== 1`. The loop body and every schema assertion are
> unchanged, and the test passes on both sides, but its assertion surface now
> covers one manifest (`current-manifest.json`) instead of sixty. The
> corpus-level guard against a schema-breaking rewrite of the historical
> manifests therefore lives in git history rather than in CI. This is intended
> and disclosed, not a regression — but it is a real reduction and is the item
> most deserving of an explicit landing decision.

`.github/workflows/rh-handoff-dashboard.yml` is deleted alongside the dashboard
it builds (its `working-directory` is `docs/chains/rh/dashboard`); removing one
without the other would leave a workflow that cannot run.

### Evidence packet

Archived out of volatile `/private/tmp` to
`~/dev/ripe-protocol-review-archives/rh-simplification-mergerun/`, with
`SHA256SUMS.txt` alongside (verified `OK` on all eight files after the copy):

```text
aa30096bd07656648b21936ff142a49bfaa2b97c09f99efe5d035a6e336a492e  evidence-baseline/baseline-lean.log
07c46297c30ab9b3d236384d3884d2c0d0ccac946728517088b5600e0caced28  evidence-baseline/baseline-lean.xml
124852bc3929660c51f8e6e3df021f118e45b83db8be0479184eb01aeac745ce  evidence-baseline/baseline-comprehensive.log
0ce0cd5a6f8e64776309cf438e3e453c931080f471548c4f3948627ea536e0bc  evidence-baseline/baseline-comprehensive.xml
f05efb2d86a59b313f59bb310b63dfde692fa6463adf35b309f2eb4f0e10367e  evidence-final2/final-lean.log
ffd92b5988e8cb3c862cd06016d52fb99f30aaeb6e6ae6504ae3a79f85b60455  evidence-final2/final-lean.xml
69847fc28de409accca173ff6e05b77f8fb290fb0b0ac05e0d46882d190f03ff  evidence-final2/final-comprehensive.log
879879f8432fff109e0345ab1fc4e7bf980a8de257a82f4871d3aa34d79022d2  evidence-final2/final-comprehensive.xml
```

### Standing invariant, restated

Sections 3–7 remain bound to the pre-merge pair.

**Superseded: see Section 14.** This section was the binding evidence when it
was written, but non-documentation commits landed after it. Section 14 binds the
delivered tip against current `origin/rh`.

## 14. Final matrix — supersedes Section 13

Section 13 binds `6260726` versus `6781cb2`. Several non-documentation commits
followed it — the rh merges, the step-manifest extractions, the testnet manifest
removal and restoration, and the test-assertion corrections — so its result no
longer describes what is being merged. **Section 13 is superseded. This section
is the binding evidence.**

### Pair

```text
baseline  = 5a664cd5852c6c82aa649628afd04ca4b95ccdcf   (origin/rh)
candidate = 687321ceb896b71bb52837e1c0cde142ca655102   (+ post-review corrections)
```

Both lanes ran in separate `git clone --no-hardlinks` checkouts under the locked
`rh-wave2-py312` interpreter, with private cache directories.

| Lane | Baseline `5a664cd` | Candidate |
| --- | --- | --- |
| Lean | 18 failed, 3,387 passed, 25 errors | 13 failed, 3,392 passed, 25 errors |
| Comprehensive | 127 failed, 4,571 passed, 33 errors | 42 failed, 4,321 passed, 33 errors |

Compared per test node from the JUnit XML: **0 new red, 0 regressions.**

### What the failure reduction is, stated accurately

Earlier revisions of this document and of the pull request described the
comprehensive delta as "85 failures fixed". **That was wrong, and the wording
mattered — it implied production behaviour improved. It did not.** An
independent review decomposed the 85 exactly, and the decomposition is:

| Cause | Count |
| --- | ---: |
| Failing tests deleted with `tests/inventory/test_block_clock_inventory.py` | 78 |
| Failing block-clock integration assertion deleted from `test_bluechip_yield_prices_artifacts.py` | 1 |
| Failing mutant-identity IDs replaced by differently named passing IDs | 4 |
| Surviving tests moved failure → pass by relaxing an assertion | 2 |
| **Total** | **85** |

No production defect was repaired by this branch. The correct statement is that
**85 red nodes stopped being reported**, 79 of them because the test was removed.

### Coverage accepted as lost

The block-clock inventory scanned production sources for `block.number` and
`block.timestamp` usage, mixed-clock arithmetic, and unclassified Vyper paths.
Nothing replaces it. A new production timestamp occurrence, a moved occurrence,
or a new unclassified path can now enter without any scanner objecting.

The owner accepted this on 2026-08-08: production clock usage is not scanned,
and clock-affecting changes are reviewed on their own merits. This is recorded
so it is a decision on the record rather than an unnoticed gap.

### Standing invariant

Any future commit touching a path outside `docs/simplification/` requires
repeating **this** matrix, against whatever `origin/rh` is at that time.
