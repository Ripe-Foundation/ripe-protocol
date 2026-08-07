# RH Smart-Contract Logic Test-Coverage Gap Plan

## 1. Purpose and target

This document is an implementation plan for closing test-coverage gaps in the
smart-contract logic changed on the Robinhood (`rh`) branch. It is deliberately
limited to contract behavior. It does not plan deployment, live-chain,
configuration-inventory, artifact, CI, dashboard, or other infrastructure work.

The review target used to prepare this plan is:

- Branch: `rh`
- Pull request: PR #67
- Head commit: `7d8c76e5134bf866ccbb051fdf5030b6e83cef8b`
- Head tree: `1d115e9a01f01f933e3e80747902080387f2113c`
- Compared with: `master` at
  `91eda49ccd34a25090582aff0695075c4c806011`
- Review date: 2026-08-06
- Revision: 5

Revision 3 corrected the SwitchboardBravo direction, recorded the measured
22-failure baseline, added route-specific StabVault preconditions, and
distinguished removed conversion selectors from explicitly disabled recovery
entry points. Revision 4 assigns the three formerly unowned baseline failures,
excludes the source-inventory file under the plan's existing scope boundary,
adds the measured strict Uniswap manipulation xfail as owner decision D-03,
and tightens the recovery and verification instructions. The re-verified facts
retained from revision 2—the 22 historical Teller selectors,
`DEACTIVATION_ZERO`/`DEACTIVATION_DUST` values, and cited function/test anchors—
matched the pinned source. The recovery-selector classification was the
contract-facing fact that required correction.

Revision 5 records the owner's interview decisions: the current pinned RH
Defaults contract is the candidate matrix source with
`maxBorrowPerInterval = 25e18` confirmed; Ledger keeps lazy-at-first-read ArbSys
validation because the constructor probe conflicted with Titanoboa; and all
Uniswap test additions are deferred. The existing Uniswap strict xfail and its
economic concern remain acknowledged but unchanged and are excluded from this
plan's implementation and completion gates.

The implementation agent should work against the current `rh` PR code, not a
deployed-contract inventory. If the PR head changes before implementation,
first re-diff the production `.vy` files and their tests, then update only the
parts of this plan affected by the new contract logic.

In this document, “runtime” or “deployed contract” means a fresh local Boa test
instance compiled from the pinned `rh` source. It never means a contract already
deployed on Robinhood, Base, or any other live network.

## 2. Scope boundaries

### In scope

- Tests of production Vyper contract behavior changed by the `rh` PR.
- Contract-level success, revert, boundary, state-transition, event, and
  accounting assertions.
- Cross-contract behavior where a changed contract calls another protocol
  contract.
- Test-only mocks or harnesses when public production entry points cannot
  exercise an important internal arithmetic boundary.
- Runtime checks that removed production selectors are not callable.

### Out of scope

- Which contracts are or are not deployed.
- Fork tests, RPC tests, live-chain qualification, live deployment migrations,
  or release work. Contract-level RipeGov position-migration behavior remains
  in scope.
- Deployment scripts and deployment configuration.
- ABI, bytecode, artifact, manifest, or source-inventory pinning.
- CI configuration, coverage dashboards, test-runner infrastructure, or
  environment setup.
- Documentation-only and Python-only changes that do not exercise contract
  logic.
- Adding production functionality as part of the test task.

If a new test exposes a production-code defect, the implementation agent should
report the defect and failing test. It should not weaken the expectation to make
the current implementation pass, and it should not silently change production
contracts under this plan.

### Mandatory owner decisions before implementation

The owner interview resolved D-02 and D-03. D-01 has an approved candidate
source but remains open until the complete literal matrix is reviewed. Record
all decisions in the implementation handoff; the mere presence of a value in
the pinned branch is not field-level matrix approval.

| Decision | Status in this revision | Blocks |
| --- | --- | --- |
| D-01 Defaults authority | **IN PROGRESS — current RH source approved as candidate; full matrix approval required** | Work package 1 test edits |
| D-02 Ledger validation posture | **APPROVED — option A, preserve lazy-at-first-read validation** | Unblocks Work package 2 |
| D-03 Uniswap test scope | **APPROVED — defer all Uniswap test changes** | Work package 7 excluded |

- **D-01 — Defaults authority.** The owner must approve an explicitly enumerated
  literal matrix covering every field and array entry returned by all seventeen
  `DefaultsRobinhood` getters. The candidate matrix may be transcribed from the
  pinned contract for owner review, but the contract source alone is not the
  approval and a blanket “use current code” is insufficient unless the owner
  has reviewed and approved that complete matrix. The existing parameter ledger
  disagrees with the contract on multiple values and must not be silently
  selected, repaired, or used as an oracle under this plan. The owner has
  confirmed `maxBorrowPerInterval = 25e18`; every remaining field still requires
  matrix review.
- **D-02 — Ledger ArbSys validation posture.** Preserve the current lazy
  posture: the exact ArbSys address is accepted at construction;
  missing/reverting/malformed behavior fails closed on first read; no fallback
  is allowed. The owner chose this because constructor probing was attempted but
  conflicted with Titanoboa. Work package 2 must test this current behavior.
- **D-03 — Uniswap test scope.** Make no changes to
  `tests/priceSources/uniswap/` or `UniswapV2Prices.vy` under this plan. The owner
  acknowledges the existing strict xfail and manipulation concern but does not
  want additional Uniswap tests now. Work package 7 is therefore deferred and
  excluded from this plan's completion gate; do not reinterpret deferral as a
  security finding being fixed or accepted as harmless.

Only D-01 remains a blocking interview item. Transcribe and submit its complete
matrix before editing Work package 1 tests. Work packages 2-6 and 8-9 may
proceed; Work package 7 must be skipped. The P0-before-P1 ordering preference in
Section 4 is a sequencing preference, not a gate.

"Beginning" Work package 1 means **editing test code**. Transcribing the
candidate D-01 matrix from the pinned contract and submitting it for owner
review is explicitly permitted before full approval; that is how the matrix
reaches the owner in the first place. Work package 2 is unblocked by D-02.

Record each decision in this form before handoff:

```text
Decision: D-01, D-02, or D-03
Status: APPROVED
Selection: exact approved option or attached literal matrix
Approver: owner name/role
Date: YYYY-MM-DD
Authority reference: commit, signed message, or attached decision record
```

### Fresh-agent startup procedure

A fresh implementation agent **must** perform these steps before editing:

0. Verify this document's own recorded identity (plan commit/blob or SHA-256,
   per "Plan custody" in Section 16) against the copy in hand, and quote it in a
   startup report together with the D-01/D-02/D-03 decision records. A plan copy
   whose identity cannot be verified is not a basis for implementation.
1. Check out `rh` in a clean isolated worktree and verify the head commit and
   tree against Section 1. Do not implement against `master` or a deployed
   contract snapshot.
2. If either identity differs, stop, re-diff changed production `.vy` files and
   related tests, and obtain approval for a refreshed plan before implementation.
   **Exception:** a head that differs from Section 1 *only* by commits produced
   under this plan does not require a refreshed plan. Verify this by diffing
   `contracts/` against `7d8c76e5134bf866ccbb051fdf5030b6e83cef8b` and
   confirming no production `.vy` file changed. Test-only, mock-only, and the
   plan-document custody commit are expected as the nine slices land. Without
   this exception every slice after the first would falsely trigger a stop.
3. Read this document completely, including the out-of-scope boundaries,
   D-01/D-02 decisions, known-red exclusions, and definition of done.
4. Confirm the recorded D-01, D-02, and D-03 decisions. Do not infer them from source,
   historical tests, a JSON ledger, deployment state, or this plan's test names.
5. Before adding a proposed test, search the current suite for a semantically
   equivalent assertion. Record the existing file and test name if the gap is
   already closed; do not add duplicate test volume.
6. Modify only the test files named by the applicable work package and narrowly
   necessary test-only mocks/harnesses. Any required production `.vy` change is
   a stop condition requiring separate owner authorization.

## 3. Test-quality rules

Every added test must follow these rules. The definition of done enforces them:

1. Test observable behavior. Do not treat source-text matching, an ABI artifact,
   or a compiled-bytecode snapshot as proof of runtime behavior.
2. Include a positive control and a negative case when a test could otherwise
   pass because an earlier guard reverted.
3. On an expected revert, snapshot and assert every relevant value is unchanged:
   token balances, shares, user and global points, Ledger membership and touch
   state, pending configuration, and emitted events.
4. For arithmetic thresholds, test the triplet immediately below, exactly at,
   and immediately above the boundary whenever all three values are valid.
5. For funds-moving paths, assert both sides of the transfer and the protocol's
   accounting state. An event alone is not sufficient.
6. For events, assert all fields, including indexed addresses/IDs and numeric
   payloads. Do not assert only that an event with the right name exists.
7. Avoid duplicate tests. Extend the most relevant existing module unless a new
   file has a clearly distinct responsibility.
8. Do not add `skip`, `xfail`, timing sleeps, or dependence on test ordering.
9. A test for a removed external function must probe the deployed contract at
   runtime with the old selector and assert that it is not callable. ABI absence
   alone is out of scope.
10. Prefer production entry points. Use a test-only harness only for a genuinely
    unreachable internal arithmetic case, and keep that harness outside the
    production contract tree.

## 4. Priority and execution order

| Order | Priority | Work package | Main risk covered |
| --- | --- | --- | --- |
| 1 | P0 | DefaultsRobinhood runtime defaults | Untested constructor bindings and launch behavior |
| 2 | P0 | Ledger action-block source | Wrong chain clock, silent fallback, partial state |
| 3 | P0 | Teller custody and route hardening | Reentrancy, false receipt accounting, callable removed routes |
| 4 | P0 | RipeGov controls and migration | Point-accounting loss, callback inconsistency, unsafe migration |
| 5 | P1 | Lootbox core-pointer routing | Mint/borrow rewards routed through the wrong core contract |
| 6 | P1 | Vault math/hardening and BasicVault matcher | Rounding, donation, depletion/dormant-state, immutable-asset and harness errors |
| 7 | Deferred | UniswapV2Prices | Owner-directed no-test-change exclusion for this plan |
| 8 | P1/P2 | Switchboard execution-time validation | Stale governance assumptions and invalid disables |
| 9 | P2 | Token governance surface | Incorrect CCIP administration after governance changes |

P0 work should land before the lower-priority packages. This is a sequencing
preference, not a gate: D-01 blocks only Work package 1 test edits, D-02 unblocks
Work package 2, and D-03 requires Work package 7 to be skipped. Within an active
package, add the failure-path tests before refactoring shared fixtures so the
reason for each fixture change remains visible.

### Complete changed-contract disposition

Every changed non-mock, non-testing production contract in the target diff has
one explicit disposition below. “Preserve” means the reviewed suite already
binds the changed behavior strongly enough that adding more tests would be
duplication; those tests still form part of the regression baseline.

| Changed contract | Disposition in this plan |
| --- | --- |
| `contracts/config/DefaultsRobinhood.vy` | Work package 1: direct runtime coverage of every getter and constructor-bound address. |
| `contracts/config/SwitchboardAlpha.vy` | Work package 8: fill only missing changed action branches. |
| `contracts/config/SwitchboardBravo.vy` | Work package 8: execution-time MissionControl/pointer revalidation. |
| `contracts/config/SwitchboardCharlie.vy` | Work package 8: complete preferred-vault pending event assertions. |
| `contracts/config/SwitchboardEcho.vy` | Work package 8: reachable disable guards and state composition. |
| `contracts/core/AuctionHouse.vy` | Preserve: conditional latch and deficit-skip behavior already have strong exact and end-to-end tests. |
| `contracts/core/BondRoom.vy` | Preserve: changed weighted-threshold behavior is already strongly tested. |
| `contracts/core/CreditEngine.vy` | Preserve: changed arithmetic and current/retired stability-vault exclusion are strongly tested. |
| `contracts/core/CreditRedeem.vy` | Preserve: changed weighted-threshold behavior is already strongly tested. |
| `contracts/core/HumanResources.vy` | Preserve direct HR coverage; Work package 4 covers its contributor-transfer interaction with disabled RipeGov users. |
| `contracts/core/Lootbox.vy` | Work package 5: alternate and unset core-pointer behavior. |
| `contracts/core/Teller.vy` | Work package 3: custody mutex, exact receipt, removed routes, and migration orchestration. |
| `contracts/data/Ledger.vy` | Work package 2: lazy ArbSys validation and exact action-block reads. |
| `contracts/data/MissionControl.vy` | Preserve: current stability-vault classification tests cover defaults, registry sources, and retired vaults. |
| `contracts/priceSources/UniswapV2Prices.vy` | Deferred by D-03: acknowledged but no contract or test changes under this plan. |
| `contracts/tokens/modules/Erc20Token.vy` | Work package 9: runtime CCIP admin behavior. |
| `contracts/vaults/RipeGov.vy` | Work package 4: disabled-user accounting, BoardRoom callbacks, and direct migration guards. |
| `contracts/vaults/StabilityPool.vy` | Work package 6: deactivation paths and removed compatibility surfaces. |
| `contracts/vaults/modules/BasicVault.vy` | Preserve contract behavior; Work package 6 owns one pre-existing Boa matcher repair needed to restore its behavioral regression test. |
| `contracts/vaults/modules/StabVault.vy` | Work package 6: rounding, donation, deactivation, and immutable-asset behavior. |

The added Vyper files under `contracts/mock/` and `contracts/testing/` are test
support and are excluded by the original scope. The Vyper example under
`docs/chains/rh/examples/` is documentation sample code, not a production
protocol contract, and is also excluded from this contract-logic gap plan.

## 5. Work package 1 — DefaultsRobinhood runtime behavior

### Files

- Add `tests/config/test_defaults_robinhood_contract.py`.
- Reuse current config-struct interfaces and ordinary Boa deployment fixtures.
- Do not couple this runtime suite to the parameter ledger, source parser,
  committed ABI, deployment generator, or artifact inventory.

### Gap

`DefaultsRobinhood.vy` is production Vyper code and therefore remains in scope
even though it returns configuration values. Its current seven-address
constructor and seventeen external getters need direct runtime assertions. The
existing `tests/config/test_defaults_robinhood.py` primarily validates peripheral
source/ledger/generator synchronization and is not a substitute for deploying
the contract and asserting its returned structs and arrays.

Do not derive the expected literals by reading values from the contract under
test, parsing its source, calling its getters to populate expectations, or
copying the conflicting parameter ledger without approval. D-01 must supply the
authority. Hard-code that approved matrix in the runtime test and place a short
provenance comment beside it identifying the D-01 decision record and pinned
commit. If the deployed-in-test contract disagrees, report the mismatch as a
contract defect; do not update the expectation to match the observed result.

Before editing test code, transcribe a complete candidate matrix with one row
per returned scalar/struct field and array entry, including array order and
constructor-bound symbolic addresses. Submit that matrix for D-01 approval and
stop this work package until the approved version is returned. This matrix is a
human decision artifact, not a generated test oracle; do not add a parser or
generator to the test suite.

### Required tests

- `test_constructor_bound_addresses_round_trip_through_runtime_getters`
  - Deploy with seven unique nonzero sentinel addresses in the current argument
    order: contributor template, training wheels, RIPE, GREEN, Savings GREEN,
    USDG, and WETH.
  - Assert each sentinel appears in every applicable runtime getter and no two
    constructor inputs are accidentally swapped.
  - Deploy a second instance with different sentinels as a control against
    hardcoded fixture addresses.

- `test_general_and_debt_defaults_match_approved_values`
  - Assert every field of `genConfig()` and `genDebtConfig()`, including the
    nested auction parameters.
  - Check boolean gates as well as numeric fields.

- `test_ripe_allocations_and_rewards_defaults_match_approved_values`
  - Assert the exact runtime results of `ripeAvailForRewards()`,
    `ripeAvailForHr()`, `ripeAvailForBonds()`, and every `rewardsConfig()` field.
  - Assert allocation percentages sum to the total specified by the approved
    D-01 matrix.

- `test_bond_hr_and_governance_defaults_match_approved_values`
  - Assert every field of `ripeBondConfig()`, `ripeGovVaultConfigs()`, and
    `hrConfig()` plus `underscoreRegistry()`, `trainingWheels()`, and
    `shouldCheckLastTouch()`.

- `test_asset_configs_match_approved_rows_order_and_values`
  - Assert the exact number and order of returned asset rows.
  - For each row, assert its constructor-bound asset and every nested config
    field. Do not merely compare array length or a subset of limits.

- `test_priority_defaults_and_lite_signers_match_approved_values`
  - Assert complete results from `priorityLiqAssetVaults()`,
    `priorityStabVaults()`, `priorityPriceSourceIds()`, and `liteSigners()`.
  - Explicitly assert `priorityStabVaults()` is exactly the single entry
    `(vaultId=1, asset=sGREEN)` using the constructor-bound Savings GREEN
    address. This closes the Robinhood Defaults-to-MissionControl registration
    seam that the DefaultsBase-based classifier tests do not cover.
  - Include empty-array assertions wherever the approved D-01 matrix specifies
    an empty array.

- `test_defaults_cross_field_invariants_hold_at_runtime`
  - Assert each minimum is no greater than its corresponding maximum, active
    vault IDs are valid for their intended row, allocation totals are valid,
    and nonzero-required constructor-bound addresses remain nonzero in output.
  - These invariant assertions supplement, but do not replace, the exact-value
    assertions above.

### Acceptance criteria

- The current seven-argument contract is deployed and all seventeen external
  getters are exercised at runtime.
- D-01 is recorded, and every expected literal comes from that approved matrix
  rather than from the contract under test or an unapproved conflicting source.
- Every returned struct field and array entry is asserted, not sampled.
- Tests fail on an address-order swap, and every numeric field is asserted with
  exact equality so that any one-unit deviation from the approved matrix fails.
- No production-default assertion depends on a JSON ledger, Python extractor,
  ABI file, deployment script, or deployed-chain state.

## 6. Work package 2 — Ledger action-block source

### Files

- Modify `tests/data/test_ledger_action_block.py`.
- Reuse its existing action-block mock; extend that mock only if it cannot emit
  short, oversized, or reverting return data.

### Gap

The current Ledger accepts the exact ArbSys precompile address as an action-block
source without probing it in the constructor. Validation occurs when the value
is read. D-02 approves this current lazy-at-read posture because the attempted
constructor probe conflicted with Titanoboa. Replace the historical
constructor-failure expectations accordingly. The native `block.number` mode
must remain separate, and a configured ArbSys source must never silently fall
back.

### Required tests

- `test_arb_sys_constructor_defers_validation_to_first_runtime_read`
  - Configure the source as the exact ArbSys address with no compatible code.
  - Assert Ledger construction succeeds and stores the source.
  - Assert the first action-block read reverts.
  - Assert no user touch state is created or modified.

- `test_get_arb_action_block_returns_exact_identity_word`
  - Install a source returning a valid 32-byte word.
  - Assert `getArbActionBlock()` returns that exact value without timestamp or
    native-block substitution.
  - Touch a user and assert `lastTouch` records the same exact value.

- `test_get_arb_action_block_rejects_invalid_returndata_without_fallback`
  - Parameterize missing code, explicit revert, empty data, short data, and
    oversized data.
  - For each mode, assert the view call and the first state-changing touch both
    fail closed.
  - Assert the contract does not fall back to `block.number` or `block.timestamp`.
  - Assert `lastTouch`, user membership, and other Ledger state remain unchanged.

- `test_native_action_block_mode_does_not_call_arb_sys`
  - Retain or add a positive control showing the native mode still records the
    production native clock and does not depend on code at the ArbSys address.

### Required repair of the L3a mutation machinery

Replacing the constructor-failure expectations is necessary but not sufficient:
6 of this module's 13 pre-existing failures come from its L3a mutation
framework, which is red for a separate reason and is not covered by the tests
above.

- `test_l3a_mutant_source_identities_are_frozen` pins SHA-256 identities of
  mutant sources derived from the current `Ledger.vy`. The
  `no_constructor_probe` mutant anchors on the source text
  `if _actionBlockSource == ARB_SYS:\n        _: uint256 = self._getArbActionBlock()`,
  which no longer exists at head, so the helper raises before any assertion.
  All five frozen identities (`typed_call`, `truncation`, `no_constructor_probe`,
  `native_fallback`, `monotonic`) currently fail.
- `test_l3a_removed_probe_mutant_fails_missing_constructor_case` fails for the
  same reason.

Under approved D-02, **retire the `no_constructor_probe`
mutant**: its premise — that removing the constructor probe is a defect — is
now the production behavior itself, so the mutant is meaningless. Rebind the
remaining mutants' source anchors to the head `Ledger.vy` and refresh their
frozen identities. Record the retirement and each refreshed digest in the
handoff; do not delete the mutation framework wholesale, and do not refresh a
digest without confirming the mutant still expresses a real defect.

### Acceptance criteria

- D-02's approved lazy-at-read validation is implemented exactly as specified.
- Constructor behavior and runtime-read behavior are tested separately.
- All malformed return-data sizes are covered.
- At least one state-changing Ledger path proves that a failed clock read is
  atomic.
- Under the accepted lazy posture, no test expects constructor-time probing of
  the exact ArbSys address.
- All 13 pre-existing failures in `tests/data/test_ledger_action_block.py` are
  resolved: the 7 constructor parameterizations respecified, and the 6 L3a
  mutation-framework failures repaired per the section above.

## 7. Work package 3 — Teller custody and route hardening

### Files

- Modify `tests/core/teller/test_teller_deposit.py`. At the pinned head
  `tests/core/teller/` contains only `test_teller_action_block.py`,
  `test_teller_deposit.py`, `test_teller_rebalance.py`, and
  `test_teller_withdraw.py`; there is no separate reentrancy or
  adversarial-vault module, and the mutation controls and reentrancy
  cross-product cases all live in `test_teller_deposit.py`. Put all Work
  package 3 cases there. Do not create a parallel duplicate suite.
- Modify `tests/core/teller/test_teller_action_block.py` only to replace the
  failing source-occurrence inventory with observable housekeeping behavior.
  Do not repair it by changing the expected source count from five to four.
- Use existing mock assets and vaults before adding a new adversarial mock.

**Pre-existing failures owned by this package.** Six tests in
`test_teller_deposit.py` are red at the pinned head and must be repaired here,
not deleted and not reported as pre-existing-and-ignored:

- `test_t6_vault_receipt_equality_mutant_silently_accepts_short_report`
- `test_t6_real_basic_vault_blocks_short_report_without_teller_equality`
- `test_t1_mutex_removal_mutant_exposes_offsetting_nested_receipt`
- `test_t1_real_basic_vault_blocks_offsetting_receipt_without_teller_mutex`
- `test_predeployment_undecorated_route_reentrancy_cross_product[redemption-governance]`
- `test_predeployment_undecorated_route_reentrancy_cross_product[redemption-trusted]`

The `t1`/`t6` mutation controls fail because of the brittle anchoring described
below; the two `redemption-*` parameterizations fail because they still
reference the removed single-item `redeemCollateral` route via
`prepare_calldata`. Repair each by rebinding to a surviving route and a
statement-level anchor. Deleting a mutation control is permitted only if the
handoff records that the property it proved is bound by a named replacement
test.

One additional pre-existing failure in
`test_teller_action_block.py::test_teller_callsite_classification_and_identity_matrix_is_preserved`
is also owned by this package. Its literal source-count assertion is outside the
behavioral standard in Section 3 and must be replaced under Gap E below.

### Gap A: receipt-measurement mutex

The deposit path uses `receiptMeasurementActive` while measuring exact custody
receipt. The suite needs a runtime proof that a callback cannot enter another
custody-changing Teller route during that window. Existing source-mutation
helpers are brittle when a harmless source comment or statement location
changes, and one route reference is stale after removal of the single-item
redemption function.

### Required tests

- `test_receipt_measurement_mutex_blocks_nested_batch_redemption`
  - During deposit receipt measurement, have an adversarial token or vault call
    `redeemCollateralFromMany`, the surviving production route.
  - Make all permissions, balances, vault IDs, and list lengths valid so the
    nested call reaches the mutex rather than an earlier guard.
  - Assert the transaction reverts atomically and no balances, shares, Ledger
    state, or rewards state change.

- `test_receipt_measurement_mutex_allows_normal_sequential_operations`
  - Execute a normal deposit and then a separate batch redemption.
  - Assert the mutex is cleared after the deposit and both operations account
    for the exact token amounts.

- Preserve a mutation-discrimination control if the repository continues to
  use mutation tests. The mutation should remove only the mutex assertion using
  a statement-level anchor tolerant of comments and formatting. Do not pin a
  whole-file hash or a prose comment. The adversarial scenario must reach a
  different result with the guard removed.
- Commit `f38ac90` moved byte-identical Teller helpers and invalidated pre-move
  whole-file source pins. Before using any interim mutation helper, update both
  its statement match and any unavoidable source pin against the post-`f38ac90`
  source at the pinned head. Prefer eliminating the whole-file pin in favor of
  the narrow semantic anchor so future code motion cannot disable the proof.

### Gap B: exact receipt and vault-result equality

- Keep or add `test_deposit_reverts_when_vault_reports_result_different_from_receipt`.
  Use a vault that actually receives the expected tokens but reports a different
  deposit result. Assert Teller rejects the mismatch and the entire transaction
  rolls back.
- Add the complementary success case with exact custody delta and exact vault
  return value.
- If an existing mutation helper proves this assertion matters, make its source
  anchor statement-specific rather than comment- or hash-specific.

### Gap C: removed single-item selectors

Vyper default arguments exposed multiple selectors for each removed function.
Add one parameterized runtime test covering every previously callable selector,
not merely one selector per function name:

```text
redeemCollateral(address,uint256,address)
redeemCollateral(address,uint256,address,uint256)
redeemCollateral(address,uint256,address,uint256,bool)
redeemCollateral(address,uint256,address,uint256,bool,bool)
redeemCollateral(address,uint256,address,uint256,bool,bool,bool)
redeemCollateral(address,uint256,address,uint256,bool,bool,bool,address)

buyFungibleAuction(address,uint256,address)
buyFungibleAuction(address,uint256,address,uint256)
buyFungibleAuction(address,uint256,address,uint256,bool)
buyFungibleAuction(address,uint256,address,uint256,bool,bool)
buyFungibleAuction(address,uint256,address,uint256,bool,bool,bool)
buyFungibleAuction(address,uint256,address,uint256,bool,bool,bool,address)

claimFromStabilityPool(uint256,address,address)
claimFromStabilityPool(uint256,address,address,uint256)
claimFromStabilityPool(uint256,address,address,uint256,address)
claimFromStabilityPool(uint256,address,address,uint256,address,bool)

redeemFromStabilityPool(uint256,address)
redeemFromStabilityPool(uint256,address,uint256)
redeemFromStabilityPool(uint256,address,uint256,address)
redeemFromStabilityPool(uint256,address,uint256,address,bool)
redeemFromStabilityPool(uint256,address,uint256,address,bool,bool)
redeemFromStabilityPool(uint256,address,uint256,address,bool,bool,bool)
```

Suggested name:

- `test_removed_single_item_routes_are_not_callable_at_runtime`

For each old selector, send correctly encoded calldata directly to the deployed
Teller and assert it cannot execute. Pair this with positive calls to the
surviving batch routes so a generic fallback or calldata-construction mistake
cannot create a false pass:

- `redeemCollateralFromMany(...)`
- `buyManyFungibleAuctions(...)`
- `claimManyFromStabilityPool(...)`
- `redeemManyFromStabilityPool(...)`

The stale `scripts/abis/Teller.json` may be used only as a convenience to
cross-check the historical input encodings listed above. It must not be the
assertion oracle: the runtime call result is the proof, and the test's selector
list must remain explicit even if that stale ABI is later removed or repaired.

### Gap D: RipeGov migration orchestration

In the existing migration tests, add:

- `test_migrate_ripe_gov_position_rejects_unsupported_source_asset_atomically`
- `test_migrate_ripe_gov_position_emits_complete_event`

The event assertion must cover the user, source/target assets, source/target
vault IDs, transferred token amount, transferred points, and any other current
event field. The failure test must assert source and target vault balances,
shares, points, Ledger membership, and Lootbox state are unchanged.

### Gap E: observable Teller housekeeping classification

Retire the failing source-count test only after every surviving housekeeping
route is bound by a named runtime assertion. Build a route-to-evidence matrix in
the implementation handoff with these production groupings:

| Expected housekeeping behavior | Surviving routes to bind |
| --- | --- |
| Low risk, user subject, update debt | `deposit`, `depositMany`, `convertToSavingsGreenAndDepositIntoStabPool`, `depositIntoGovVault`, `claimLoot`, `adjustLock`, `releaseLock` |
| High risk, user subject, update debt | `withdraw`, `withdrawMany`, `rebalance`, `claimManyFromStabilityPool` |
| High risk, user subject, do not update debt in housekeeping | `borrow` |
| Low risk, user subject, do not update debt in housekeeping | `repay` |
| Low risk, recipient subject, update debt | `redeemCollateralFromMany`, `buyManyFungibleAuctions`, `redeemManyFromStabilityPool`, `purchaseRipeBond` |
| Low risk, caller subject, update debt | `liquidateUser`, `liquidateManyUsers`, `claimLootForManyUsers` |
| Caller-supplied risk/user/debt flags | external `performHousekeeping` |
| Low risk, user subject, update debt through external Teller call | `Deleverage` callsite |

For each row, cite an existing runtime test that proves the risk flag, touched
subject, and debt-update choice, or add a parameterized case in
`test_teller_action_block.py`. Observe risk through the same-block Ledger rule,
observe subject identity through exact `lastTouch` changes with decoy users
unchanged, and observe the debt-update choice through exact debt state or a
narrow test-only CreditEngine recorder. A test that only searches Teller or
Deleverage source text is not acceptable evidence.

Suggested replacement tests:

- `test_teller_route_housekeeping_risk_and_subject_matrix`
- `test_teller_route_housekeeping_debt_update_matrix`

If setup for a route already lives in another owning test module, strengthen
that test and cite it rather than duplicating its economic setup here. The
handoff matrix must nevertheless cover every route listed above before the old
source-count test is deleted.

### Acceptance criteria

- No test references a route removed from production except the explicit raw
  selector-absence test.
- The mutex test proves it reached the intended guard.
- Receipt delta, vault return value, and final accounting are asserted together.
- Migration success and failure cases assert full cross-contract state.
- The failing source-count inventory is gone, and every surviving Teller/
  Deleverage housekeeping route has named runtime evidence for risk, subject,
  and debt-update classification.

## 8. Work package 4 — RipeGov controls and migration

### Files

- Modify `tests/vaults/test_ripe_gov_controls_and_migration.py`.
- Modify `tests/vaults/test_ripe_gov_vault.py` only for cases that belong to its
  existing vault-accounting responsibility.
- Add a minimal BoardRoom recorder mock only if the existing mock cannot expose
  callback count and arguments.

### Gap A: disabled users and contributor transfers

Add a small state-table suite around `transferContributorRipeTokens`:

- `test_contributor_transfer_enabled_users_moves_tokens_and_points`
- `test_contributor_transfer_from_disabled_sender_moves_tokens_without_points`
- `test_contributor_transfer_to_disabled_recipient_accounts_for_dropped_points_exactly`
- `test_contributor_transfer_between_disabled_users_does_not_move_points`

For every case, assert:

- sender and recipient token balances;
- sender and recipient current and total governance points;
- `totalGovPoints`;
- the sum of affected users' points versus the global change;
- emitted event fields; and
- unrelated users remain unchanged.

The disabled-recipient case is especially important. Lock the current arithmetic
explicitly, including whether points are intentionally removed from both the user
and global totals. If the observed result violates the contract's documented
accounting invariant, leave the test failing and report the production defect;
do not bless the behavior with a weaker assertion.

### Gap B: BoardRoom callback behavior

Add:

- `test_enabled_user_point_update_calls_boardroom_once_with_final_points`
- `test_disabled_user_point_update_skips_boardroom_and_point_mutation`

Use otherwise identical operations. Assert callback count, user address, final
point value, and atomicity if the callback reverts. This pair must demonstrate
that the disabled-user early return—not some unrelated precondition—causes the
callback difference.

### Gap C: direct export guards

Call `exportPositionForMigration` directly as the configured Teller so each
vault guard is isolated from Teller's own validation. Add parameterized tests
covering:

- caller is not Teller;
- source vault is not paused;
- target vault address is zero;
- target vault is not a contract;
- target vault is the source vault itself;
- the position was already migrated out;
- the source position is empty;
- the position's token/point accounting is inconsistent; and
- the attempted withdrawal is not the complete position.

Suggested names:

- `test_direct_export_rejects_invalid_migration_context_atomically`
- `test_direct_export_moves_full_position_and_sets_tombstone`
- `test_direct_export_emits_complete_event`

For every revert, snapshot source shares, vault balances, point totals,
`positionMigratedOut`, and Ledger state. The success case must prove the complete
position moves and a second export cannot occur.

### Gap D: direct import guards

Likewise call `importPositionForMigration` directly as Teller and cover:

- caller is not Teller;
- target vault is not paused;
- source vault address is zero, non-contract, or the target itself;
- amount is zero;
- the source tombstone/authorization condition is missing;
- the target user already has shares, current points, total points, or other
  non-empty `GovData` state;
- the target did not receive the asserted token amount; and
- the resulting target shares would be zero.

Suggested names:

- `test_direct_import_rejects_invalid_migration_context_atomically`
- `test_direct_import_rejects_partially_nonempty_target_position`
- `test_direct_import_reconstructs_position_and_emits_complete_event`

The success case must assert token receipt, shares, current/total user points,
global points, Ledger membership, source binding, and all event fields.

### Acceptance criteria

- Direct vault tests isolate every production guard from Teller validation.
- Every migration revert is state-atomic.
- Disabled-user tests assert global as well as per-user accounting.
- Callback behavior is checked with arguments, not just call occurrence.

## 9. Work package 5 — Lootbox core-pointer routing

### Files

- Modify `tests/core/lootbox/test_loot_claim.py`.
- Modify `tests/core/lootbox/test_loot_deposit_points.py`.
- Reuse the existing alternate Teller/core-recorder fixtures if available.

### Required tests

- `test_claim_deposit_loot_uses_current_teller_pointer`
  - Repoint the relevant core address to a different valid Teller-like contract.
  - Assert the claim route calls the new pointer, not the original fixture.
  - Assert claimed points and Ledger state match the alternate core's values.

- `test_claim_deposit_loot_reverts_atomically_when_teller_pointer_is_unset`
  - Ensure the user otherwise has a claimable vault position.
  - Assert balances, claim accounting, points, and last-touch state are unchanged.

- `test_get_claimable_loot_with_position_reverts_when_teller_pointer_is_unset`
  - Include a no-position control that exercises the intended early-return path.
  - Include a position-bearing case that must reach the pointer lookup.

- `test_get_claimable_loot_from_alternate_pointer_matches_claimed_amount`
  - Query the view, execute the claim without changing the clock or position,
    and assert the claimed amount equals the viewed amount.

### Acceptance criteria

- Unset-pointer tests contain a control proving the intended branch is reached.
- View and state-changing paths agree under an alternate valid pointer.
- Reverts cannot partially update rewards, points, or Ledger touch state.

## 10. Work package 6 — Vault math/hardening and BasicVault matcher

### Files

- Modify `tests/vaults/modules/test_stab_vault_hardening.py`.
- Modify `tests/vaults/modules/test_stab_vault_claims.py`.
- Modify `tests/vaults/modules/test_stab_vault_redemptions.py`.
- Modify `tests/vaults/test_stock_token_vault_comparison.py` only for the
  pre-existing BasicVault revert-matcher repair below.
- Use a dedicated math harness only if no public deposit/withdraw/redeem sequence
  can hit a required overflow or rounding boundary.

### Required baseline repair: BasicVault total-loss guard

The `simple-erc20` parameterization of
`test_new_deposit_after_total_loss_with_old_accounting` already reaches the
correct production guard, but uses the wrong Boa matcher form. Change only:

```python
with boa.reverts("insufficient vault backing"):
```

to:

```python
with boa.reverts(dev="insufficient vault backing"):
```

The Vyper text is a `# dev:` assert annotation, so the positional raw-revert
matcher cannot see it. Preserve every existing post-revert balance, share, and
user-accounting assertion. Do not change the production guard or weaken the
expected reason. This one-line harness repair is contract-logic test work and is
authorized within this package; it is not an infrastructure change.

### Gap A: round-up and donation boundaries

Add:

- `test_withdrawal_rounds_shares_up_at_exact_remainder_boundary`
- `test_withdrawal_rounding_boundary_below_exact_above`
- `test_direct_donation_cannot_create_zero_share_or_value_capture_deposit`
- `test_decimal_offset_one_unit_boundary_preserves_accounting`

Drive these through public deposit and withdrawal/redemption operations where
possible. For each case, assert:

- shares burned/minted using the contract's exact integer formula;
- token balances before and after;
- total shares and accounted assets;
- no depositor receives a free claim on another user's donation; and
- no nonzero valid deposit silently mints zero shares unless that is an explicit
  production rule.

Use `x-1`, `x`, and `x+1` values around the first quotient with a nonzero
remainder and around `DECIMAL_OFFSET`.

### Gap B: active-pair depletion and dormant residual semantics

The production behavior is not “reject a deactivated asset.” Claims and
redemptions read `claimableBalances` even when the asset is no longer in the
active index, so a dust-deactivated pair with residual balance remains usable.
The missing event branch occurs when an **active** pair is fully depleted:
`_reduceClaimableBalances` removes it and emits `ClaimAssetDeactivated` with
`balance=0` and `reason=DEACTIVATION_ZERO`, whose numeric value is **1**.
`DEACTIVATION_DUST` is **2**.

Add these tests in the owning claim, redemption, and hardening modules:

- In `tests/vaults/modules/test_stab_vault_claims.py`:
  - `test_full_claim_depletes_active_pair_and_emits_deactivation_zero_reason_one`
  - `test_dust_deactivated_pair_with_residual_balance_remains_claimable`
- In `tests/vaults/modules/test_stab_vault_redemptions.py`:
  - `test_full_redemption_depletes_active_pair_and_emits_deactivation_zero_reason_one`
- In `tests/vaults/modules/test_stab_vault_hardening.py`:
  - `test_claimable_green_swap_depletes_active_pair_and_emits_deactivation_zero_reason_one`

For each depletion test:

1. First activate the exact `(stabAsset, claimAsset)` pair and assert
   `indexOfClaimableAsset` is nonzero. This precondition is load-bearing: a
   dormant pair bypasses `_removeClaimableAsset` and would make an event test
   vacuous.
2. Fully consume the pair through the named public path using the maximum valid
   amount.
3. Assert the complete `ClaimAssetDeactivated` event: exact stability asset,
   claim asset, `balance == 0`, expected post-removal active count, and
   `reason == 1`.
4. Assert the pair's index is zero, active-array compaction is correct, total and
   pair claimable balances are exact, and all token/share/burn or redemption
   accounting for that path reconciles.

**Route-specific preconditions.** Steps 3 and 4 are not uniform across the three
routes; two of them cannot produce a "pure depletion" call, and an implementer
who assumes otherwise will write assertions that cannot pass.

- *Activation vehicle.* Use the `swapForLiquidatedCollateral` path to activate a
  pair. The explicit `activateClaimAssets` maintenance route asserts
  `vaultData.isPaused` and cannot be used mid-flow. To manufacture a dust
  deactivation for the dormant-residual test, use `pruneClaimableAssets`, which
  has no pause gate.
- *Claim route.* Pass `_maxUsdValue = MAX_UINT256`. A finite `_maxUsdValue`
  below `maxClaimUsdValue` is floor-divided and can strand 1 wei, leaving the
  pair nonzero and the deactivation event unemitted.
- *Redemption route.* The same call that emits `ClaimAssetDeactivated` for the
  depleted pair then adds the spent GREEN as a new claimable balance for that
  stability asset, which will normally **activate** the `(stabAsset, GREEN)`
  pair. So assert `activeCount == 0` from the event payload, but expect
  post-call `getNumActiveClaimAssets() == 1` with `(stabAsset, GREEN)` active at
  index 1 and its own `ClaimAssetActivated` event — the depleted pair's slot is
  reused. Alternatively use `savings_green` as the stability asset to suppress
  the GREEN re-add. `test_claim_data_model_tracks_redemption_reduction_and_green_addition`
  in the hardening module is the working template.
- *Claimable-GREEN swap route.* `swapWithClaimableGreen` first executes
  `_addSwapClaimable`, which asserts a nonzero reported amount and real token
  custody, so the depleting call must also transfer a nonzero liquidation asset
  in. If that asset is new it registers and activates another pair **before**
  the deactivation event, shifting both `activeCount` and the post-call array
  layout. Seed the active `(stabAsset, GREEN)` pair first, pass `green_token`
  as the liquidation asset with a small fresh transfer, and set `_greenAmount`
  to at least the post-receipt pair balance.

For the dormant-residual test, create a dust deactivation with a positive
remaining balance, prove its index is zero, then claim from that balance and
assert the exact payout/accounting. Do not expect a revert and do not relabel
reason `1` as “zero reason.”

### Gap C: immutable asset identity after HQ changes

Add:

- `test_green_asset_identity_does_not_change_after_hq_repoint`
- `test_savings_green_asset_identity_does_not_change_after_hq_repoint`

The contracts snapshot these identities. Repoint Headquarters to replacement
addresses and assert existing vault behavior continues to use the immutable
constructor values. Include a control showing ordinary dynamic pointers still
follow Headquarters where production code intends them to.

### Gap D: removed and disabled compatibility selectors

Own these cases in `tests/vaults/modules/test_stab_vault_hardening.py`.
Suggested test names:

- `test_removed_conversion_selectors_are_not_callable_at_runtime`
- `test_stability_pool_recovery_entrypoints_are_disabled_for_all_callers`

**These are two different situations and must not be tested the same way.**
On `master`, `StabilityPool.vy` exported the whole `stabVault.__interface__`
and `vaultData.__interface__`; at head both are replaced by explicit selective
export lists.

*Genuinely removed — assert not callable:*

- `valueToShares(address,uint256,bool)` (master `StabVault.vy:368`)
- `sharesToValue(address,uint256,bool)` (master `StabVault.vy:406`)

Neither appears in head's `stabVault` export list, so the selectors are absent
from the runtime dispatcher.

*Source-declared but explicitly disabled — assert unconditional behavior:*

`recoverFunds(address,address)` and
`recoverFundsMany(address,address[])` (declared in Vyper as
`DynArray[address, 20]`) were **not** removed. Head
declares them directly in `contracts/vaults/StabilityPool.vy:219-227` under a
"Disabled Recovery" heading, each body an unconditional `raise`. Do not write a
selector-absence assertion for these. A raw call cannot prove dispatcher
presence because both an absent selector and an unconditional `raise` revert;
the contract's compiled external wrapper plus its observable behavior are the
relevant test surface. Assert the disabled behavior directly: each entry point
reverts for **every** caller,
including one otherwise authorized for recovery elsewhere in the protocol, and
no funds move and no vault state changes. A passing recovery call on a
`SimpleErc20` vault that still exports the real `vaultData` passthrough, using
the configured Switchboard caller and an unregistered donated asset, is the
positive control proving the caller and recovery setup are valid while
StabilityPool remains disabled.

For the removed conversion selectors, use a surviving exported view as the
calldata control proving the probe harness itself works and the contract answers
well-formed calls. Prefer `getTotalAmountForVault` with a configured stability
asset because it is usable while unpaused. If using `getTotalUserValue` or
`getTotalValue`, first pause the StabilityPool and satisfy their price/asset
preconditions; both route through `_getCurrentTotalValue`, which asserts the
vault is paused. Do not let an earlier pause guard create a false-positive
selector test, and do not use ABI artifacts as the assertion source.

Note that Section 3 rule 9 ("assert that it is not callable") applies only to
the genuinely removed selectors above.

`canActivateClaimAsset` is not an externally reachable production behavior. Do
not add a production-facing test solely to cover dead/unexported code. Test it
only if a public route reaches it or if a narrowly scoped math harness is already
needed for another required case.

### Acceptance criteria

- Public financial operations cover normal, exact-boundary, and one-unit edge
  cases.
- Donations cannot create an unasserted accounting windfall.
- The BasicVault total-loss guard regression passes with the correct `dev=`
  matcher and unchanged post-revert accounting assertions.
- Claim, redemption, and claimable-GREEN swap depletion paths each bind the
  active-pair `reason == 1` event, and dormant residual claimability is preserved.
- Immutable-versus-dynamic address behavior is demonstrated by paired controls.
- Both removed conversion selectors are absent at runtime with a surviving-view
  calldata control.
- Both StabilityPool recovery entry points revert for every caller with no state
  or funds movement, while the authorized `SimpleErc20` recovery control
  succeeds on an unregistered donated asset.

## 11. Work package 7 — UniswapV2Prices deferred

D-03 removes Uniswap work from this plan. The implementation agent must not:

- modify `contracts/priceSources/UniswapV2Prices.vy`;
- modify, add, remove, skip, or re-mark any test beneath
  `tests/priceSources/uniswap/`;
- add a test-only Uniswap harness or mock for new coverage; or
- claim the existing strict xfail or manipulation concern is resolved.

The previously identified pending-update, arithmetic, snapshot, clamp, and
manipulation items are acknowledged but deferred to a future owner-authorized
Uniswap effort. They are not implementation requirements or completion gates
for this document. Leave the current Uniswap source and suite byte-for-byte
unchanged relative to the implementation branch baseline.

## 12. Work package 8 — Switchboard execution-time validation

### Files

- Modify `tests/config/test_switchboard_alpha.py`.
- Modify `tests/config/test_switchboard_bravo.py`.
- Modify `tests/config/test_switchboard_charlie.py`.
- Modify `tests/vaults/test_ripe_gov_controls_and_migration.py` for Echo's
  RipeGov disable state machine. Existing Echo disable tests and fixtures live
  there; do not split those cases into `tests/config/test_switchboard_echo.py`,
  which currently owns unrelated PSM/Endaoment behavior.
- Run `tests/config/test_switchboard_echo.py` unchanged as an adjacent Echo
  regression module.

### SwitchboardBravo

Add execution-time revalidation cases for pending actions that depend on the
current MissionControl classification or pointer state:

- `test_execute_liq_config_revalidates_current_mission_control_target`
- `test_execute_debt_terms_revalidates_current_mission_control_target`
- `test_execute_whitelist_revalidates_current_mission_control_target`

For each test:

1. Create a valid pending action.
2. Change the relevant Headquarters/MissionControl pointer or stability-vault
   classification through an authorized public governance action.
3. Attempt execution after the delay.
4. Assert execution uses current state and either succeeds against the current
   valid target or **reverts** on the now-invalid action, leaving the pending
   action and all destination-contract state unchanged.

Use non-default valid pointers in at least one success control. Preserve the
current classifier regression tests in `tests/data/test_mission_control.py` and
`tests/core/creditEngine/test_credit_borrow.py`; they already cover monotonic
registration and exclusion of current/retired stability vaults and should not be
duplicated for test-count volume.

**Classifier direction (corrected).** `isStabVaultId` is monotonic *and*
acceptance-only inside Bravo, so neither direction of a
"classify-then-reject" test is reachable. At the pinned head the classifier is
consulted at exactly one Bravo site — `SwitchboardBravo.vy:406`, inside the
`_stakersPointsAlloc != 0` branch of `_isValidAssetDepositParams` — and only to
set `hasStakerVault = True`. If no listed vault ID is the core RipeGov vault or
a classified stability vault, the validator returns `False`. `MissionControl.vy`
writes `isStabVaultId[...] = True` at four sites (253, 309, 422, 461) and never
writes `False`.

Classification therefore strictly *widens* acceptance. Both steps of the earlier
prescription are unreachable: a genuinely classifier-dependent proposal cannot be
created while the ID is unclassified (the proposal-time validator rejects it
first), and registering an ID can never invalidate an already-pending action on
the same MissionControl. Do not write a test that classifies an ID and then
expects execution to reject.

Test the two directions that are actually reachable:

- **Proposal-time gate.** Assert `setAssetDepositParams`/`addAsset` with
  `stakersPointsAlloc != 0` and only an unclassified, non-core vault ID is
  rejected at proposal; then classify that ID through an authorized registry
  source and assert the same proposal now succeeds. This binds line 406 in both
  directions without any impossible state.
- **Execution-time revalidation via MissionControl replacement.** This is the
  real divergence vector, and it is publicly reachable.
  `_setPendingAssetConfig` stores the *raw* `_missionControl` argument
  (lines 285, 629), while `executePendingAction` re-resolves an empty stored
  value through `RipeHq.getAddr(MISSION_CONTROL_ID)` at execution time
  (lines 754-756). Propose with an empty `_missionControl` so both ends resolve
  through Headquarters, swap the `MISSION_CONTROL_ID` registration during the
  timelock to an instance whose `isStabVaultId` state differs, then assert
  execution revalidates against the *new* instance. Note that an explicitly
  passed `_missionControl` cannot produce this divergence:
  `_resolveMissionControl` asserts the argument is not the current instance
  (line 215), and the stored explicit address is reused verbatim at execution.

Every `executePendingAction` asset branch (lines 758-803) merges the pending
fields into the current stored config and re-asserts `_isValidAssetConfig`, so
the three named tests below are sound as execution-time revalidation cases —
scope them to pointer/MissionControl-replacement and cross-field merged-config
divergence rather than to classifier flips. Note also that none of the
liq-config, debt-terms, or whitelist *proposal-time* validators consults
`isStabVaultId` directly; the classifier reaches those branches only through
execution-time merged-config revalidation.

An invalid execution **reverts**; it does not "reject atomically" and clear the
action. Assert that the pending action survives the failed execution intact and
remains cancellable or expirable, rather than asserting it was consumed.

Do not fabricate unreachable states with direct storage mutation.
Pointer-replacement cases may still test both directions when both are publicly
reachable.

### SwitchboardEcho

Place the following cases in
`tests/vaults/test_ripe_gov_controls_and_migration.py`, adjacent to
`test_echo_disable_validator_returns_false_instead_of_reverting`,
`test_echo_user_disable_timelock_flow_and_revalidation`, and
`test_echo_global_disable_timelock_flow`.

Add reachable disable-state cases:

- `test_disable_rejects_invalid_disable_type_without_state_change`
- `test_disable_rejects_when_vault_binding_changed_before_execution`
- `test_disable_rejects_already_disabled_target`
- `test_global_and_user_disable_states_compose_without_reenabling`
- `test_disable_event_contains_complete_target_reason_and_scope`

Do not mutate storage to exercise impossible pending-action shapes. Focus on
states reachable through public governance and user actions.

### SwitchboardCharlie

Add or strengthen:

- `test_preferred_vault_pending_event_contains_new_address_and_confirmation_block`

Assert the full event payload and pending storage values agree.

### SwitchboardAlpha

Review the existing validation matrix for every changed action branch. Add only
the missing branches, each with a valid control and a state-atomic invalid case.
Do not duplicate generic ownership, pause, or delay tests already common to the
suite.

### Acceptance criteria

- Pending actions are tested against state changes between proposal and
  execution.
- Tests distinguish current target/classification state from proposal-time
  state.
- All invalid executions preserve pending and destination-contract state.
- No unreachable-storage-shape tests are added solely for line coverage.

## 13. Work package 9 — Token governance surface

### Files

- Modify `tests/tokens/test_erc20.py`.

### Required token tests

For Green, Ripe, and Savings Green, add a parameterized suite:

- `test_ccip_admin_equals_current_hq_governance`
- `test_ccip_admin_follows_confirmed_hq_governance_change`
- `test_ccip_admin_pre_setup_behavior_is_explicit`

Assert exact addresses before and after a confirmed governance handoff. The
pre-setup case must assert the actual contract rule—zero address or revert—as
an explicit expectation rather than accepting either result.

### Acceptance criteria

- All three token types are exercised through the same behavioral matrix.
- The test proves the admin is read from current Headquarters governance rather
  than cached at token deployment.
- Pre-setup behavior is one exact assertion, not a permissive either/or.

## 14. Existing coverage to preserve, not churn

The implementation agent must keep these already-strong areas green and avoid
rewriting them without a concrete missing behavior. "Already-strong" describes
intended coverage, not a measured-green baseline — see the measured redness in
Section 16, which includes failures in the BasicVault and AuctionHouse
territory listed below:

- MissionControl stability-vault registry initialization and monotonic tracking.
- CreditEngine exclusion of current and retired stability vault IDs.
- RipeGov/Teller migration happy path and basic authorization.
- BasicVault safety and recovery restrictions.
- AuctionHouse core auction lifecycle and stock-delivery flows.
- StabilityPool/StabVault ordinary claim, redemption, and state-model behavior.
- Existing pointer-following positive paths.

The goal is stronger behavioral discrimination, not a larger number of nearly
identical happy-path tests.

## 15. Suggested implementation slices

Keep reviews small enough to diagnose failures. A sensible sequence is:

1. DefaultsRobinhood direct runtime getters and constructor binding.
2. Ledger lazy action-block validation and malformed-return atomicity.
3. Teller mutex, receipt equality, removed selectors, and migration event.
4. RipeGov disabled-user accounting, callbacks, and direct migration guards.
5. Lootbox pointer routing.
6. StabilityPool/StabVault financial boundaries.
7. **Skip — UniswapV2Prices is deferred by D-03.**
8. Switchboard execution-time state changes.
9. Token CCIP admin behavior.

Within each slice:

1. Add the narrow failing test.
2. Prove it reaches the intended branch with a valid control.
3. Add full state/event assertions.
4. Run the owning test module.
5. Run the slice's adjacent path before moving on, per the table below.

"The adjacent logical suite" for a slice means only the paths listed here, not
the full Section 16 set:

| Slice | Adjacent path to run |
| --- | --- |
| 1 DefaultsRobinhood | `tests/config/test_defaults_robinhood_contract.py` |
| 2 Ledger | `tests/data/` |
| 3 Teller | `tests/core/teller/` |
| 4 RipeGov | `tests/vaults/test_ripe_gov_controls_and_migration.py`, `tests/vaults/test_ripe_gov_vault.py` |
| 5 Lootbox | `tests/core/lootbox/` |
| 6 StabilityPool/StabVault/BasicVault matcher | `tests/vaults/modules/`, `tests/vaults/test_stock_token_vault_comparison.py` |
| 7 UniswapV2Prices | **Deferred; do not run as a modification gate and do not edit** |
| 8 Switchboards | `tests/config/test_switchboard_*.py` |
| 9 Token CCIP | `tests/tokens/` |

A pre-existing failure owned by a later slice, or listed among the measured
pre-existing redness in Section 16, does not block the current slice's step 5.
Only a regression introduced by the current slice does. Run the full Section 16
set once at the end, not after every slice.

Slice 7 has no implementation or verification action in this plan. The final
scope check must instead prove Uniswap production and test files are unchanged.

## 16. Verification matrix

### Focused modules

At minimum, run these exact focused modules changed or preserved by this plan:

```text
tests/config/test_defaults_robinhood_contract.py
tests/data/test_ledger_action_block.py
tests/data/test_mission_control.py
tests/core/teller/test_teller_action_block.py
tests/core/teller/test_teller_deposit.py
tests/vaults/test_ripe_gov_controls_and_migration.py
tests/vaults/test_ripe_gov_vault.py
tests/core/lootbox/test_loot_claim.py
tests/core/lootbox/test_loot_deposit_points.py
tests/vaults/modules/test_stab_vault_hardening.py
tests/vaults/modules/test_stab_vault_claims.py
tests/vaults/modules/test_stab_vault_redemptions.py
tests/vaults/test_stock_token_vault_comparison.py
tests/config/test_switchboard_alpha.py
tests/config/test_switchboard_bravo.py
tests/config/test_switchboard_charlie.py
tests/config/test_switchboard_echo.py
tests/tokens/test_erc20.py
tests/core/creditEngine/test_credit_borrow.py
```

### Exact adjacent logical suites

For purposes of this plan and Section 17, “adjacent logical suites” means
exactly the following paths—nothing broader is implied:

```text
tests/data/
tests/core/teller/
tests/core/lootbox/
tests/vaults/
tests/tokens/
tests/config/test_defaults_robinhood_contract.py
tests/config/test_switchboard_alpha.py
tests/config/test_switchboard_bravo.py
tests/config/test_switchboard_charlie.py
tests/config/test_switchboard_echo.py
tests/core/creditEngine/test_credit_borrow.py
```

When running the `tests/vaults/` adjacent path, pass
`--ignore=tests/vaults/test_basic_vault_consumer_inventory.py`. That file is a
source-inventory gate, not a runtime contract-logic test, and is formally
excluded below under the user's explicit no-infrastructure/no-inventory scope.

Run these suites **serially**. This is not a judgment call: the repository's
Boa fixtures share global environment state, and parallel workers are known to
produce spurious failures at reused addresses that are indistinguishable from
real regressions. The baseline recorded below was measured serially.

Run pytest outside a restrictive command sandbox. The session-scoped `free_port`
fixture in `tests/conf_env.py` binds a socket, which a sandboxed run rejects with
`PermissionError: [Errno 1] Operation not permitted` at fixture setup — an error
that masquerades as a collection failure rather than a sandbox restriction.

Use the verified local validation interpreter
`/Users/wigglez/dev/ripe-protocol-validation-envs/rh-wave2-py312/bin/python`
(Python 3.12.0, Titanoboa 0.2.7, Vyper 0.4.3, pytest 8.4.2) unless the owner
provides a replacement. Use private mode-0700 temporary Boa/pytest caches and
the repository's existing non-secret `ETHERSCAN_API_KEY=local-placeholder`
convention. This records the measured environment; it does not authorize CI or
dependency changes.

### Known-red exclusions at the pinned head

The following files are known-red at `7d8c76e5134bf866ccbb051fdf5030b6e83cef8b`
and are outside this contract-logic plan:

```text
tests/config/test_defaults_robinhood.py
tests/inventory/test_contract_artifacts.py
tests/deployment/test_abi_export.py
tests/vaults/test_basic_vault_consumer_inventory.py
```

They validate parameter-ledger/generator synchronization, committed ABI/artifact
state, or a reviewed source-inventory digest rather than the runtime contract
behaviors targeted here.
Do not modify, delete, skip, or weaken them under this plan. Their failures do
not fail this plan's definition of done, but the final handoff must list them as
pre-existing excluded failures so nobody mistakes the branch-wide suite for
green.

The first three files are outside the focused and adjacent paths. The BasicVault
consumer inventory sits beneath `tests/vaults/`, which is why the exact
`--ignore` above is required. Its reviewed inventory pins seven production
sources and six have substantively drifted on `rh`; regenerating it is a
separate source-inventory review judgment, not a mechanical contract-test fix.

### Measured pre-existing redness inside the adjacent paths

A serial run of the focused modules and the exact adjacent paths at
`7d8c76e5134bf866ccbb051fdf5030b6e83cef8b`, in the locked Python 3.12
validation environment, produced:

```text
22 failed, 1657 passed, 1 xfailed
```

These 22 failures are **pre-existing at the pinned head**, not caused by this
plan. All 22 were reconfirmed to fail in isolation, so none is an ordering or
Boa trace-pollution artifact. The blanket rule "no newly failing test in the
focused or exact adjacent paths may be dismissed as known red" stands only for
tests that are *newly* failing; it must not be read as a claim that these paths
are green at head. This measured command included the now-excluded BasicVault
source-inventory file. After applying that one-file scope exclusion, 21 failing
contract-logic tests remain and are assigned to Work packages 2, 3, and 6.

**`tests/data/test_ledger_action_block.py` — 13 failures. Owner: Work package 2
(gated on D-02).**

- `test_arb_sys_constructor_fails_closed_when_call_or_decode_is_invalid`
  — 7 parameterizations (`missing`, `reverting`, `short_31`, `oversized_33`,
  `oversized_64`, `oversized_gt_64`, `incompatible`). These encode the
  constructor-time fail-closed posture; the head constructor
  (`contracts/data/Ledger.vy:190-192`) only asserts the address is in
  `[empty, ARB_SYS]` and performs no probe, so deployment succeeds and the
  expected revert never occurs.
- `test_l3a_mutant_source_identities_are_frozen` — 5 parameterizations
  (`typed_call`, `truncation`, `no_constructor_probe`, `native_fallback`,
  `monotonic`).
- `test_l3a_removed_probe_mutant_fails_missing_constructor_case`.

**`tests/core/teller/test_teller_deposit.py` — 6 failures. Owner: Work package 3
(Gaps A and B).**

- `test_t6_vault_receipt_equality_mutant_silently_accepts_short_report`
- `test_t6_real_basic_vault_blocks_short_report_without_teller_equality`
- `test_t1_mutex_removal_mutant_exposes_offsetting_nested_receipt`
- `test_t1_real_basic_vault_blocks_offsetting_receipt_without_teller_mutex`
- `test_predeployment_undecorated_route_reentrancy_cross_product`
  — parameterizations `redemption-governance` and `redemption-trusted`.

**Revision 4 disposition of the remaining three measured failures.**

- `tests/core/teller/test_teller_action_block.py::test_teller_callsite_classification_and_identity_matrix_is_preserved`
  — asserts a literal occurrence count in the Teller source text
  (`teller_source.count('self._performHousekeeping(True, _user, True, a)') == 5`);
  the head source contains 4. This is source-text matching, the genre Section 3
  rule 1 forbids as proof of runtime behavior, and it is red because the `rh`
  branch legitimately changed Teller callsites. **Owner: Work package 3,
  Gap E.** Replace it with the complete runtime route-to-evidence matrix; do not
  merely change five to four.
- `tests/vaults/test_basic_vault_consumer_inventory.py::test_basic_vault_consumer_inventory_matches_reviewed_sources`
  — a source-inventory pinning test. Its inventory
  (`docs/chains/rh/hardening/basic-vault-consumer-inventory.md`, pinned baseline
  `1e36c0c3dd168dbf292456eb5760b02d1f1e4a80`) pins SHA-256 digests for 7
  production sources, and **6 of the 7 have drifted** at the pinned head:
  `AuctionHouse.vy`, `CreditEngine.vy`, `CreditRedeem.vy`, `HumanResources.vy`,
  `Lootbox.vy`, and `Teller.vy`. This is not a single byte-identical helper
  move; it spans six contracts with substantive `rh` changes, so regenerating
  the inventory is a real review judgment, not a mechanical refresh.
  Source-inventory pinning is explicitly **out of scope** per Section 2.
  **Disposition: formally excluded from this plan** using the exact
  `--ignore` above. Do not regenerate the inventory here.
- `tests/vaults/test_stock_token_vault_comparison.py::test_new_deposit_after_total_loss_with_old_accounting[simple-erc20]`
  — **a test-harness defect, not a production defect.** The production guard
  fires correctly (`assert custodyBefore >= nominalBefore + _amount
  # dev: insufficient vault backing`), but it reverts with an empty reason
  (`Revert(b'')`), so the positional matcher `boa.reverts("insufficient vault
  backing")` cannot match. The correct idiom for a dev-comment assert in this
  suite is `boa.reverts(dev="insufficient vault backing")`. **Owner: Work
  package 6 required baseline repair.** Change only the matcher form and retain
  every accounting assertion.

Section 14 lists "BasicVault safety and recovery restrictions" and "AuctionHouse
core auction lifecycle and stock-delivery flows" among the already-strong areas
to keep green. Work package 6 restores the BasicVault behavioral regression,
while the source inventory remains excluded; "preserve, not churn" describes
the contract behavior rather than an instruction to preserve a broken matcher
or refresh peripheral source pins.

### Deferred Uniswap residual present in the original measured baseline

The original `1 xfailed` result was
`tests/priceSources/uniswap/test_minimal_prices.py::test_repeated_manipulated_snapshots_cannot_persistently_suppress_price`.
It is strict and represents the acknowledged economic behavior described by
D-03. Uniswap is no longer in the focused/adjacent execution set, and neither
this test nor its marker may be changed. The final handoff must list the issue as
deferred, not green or resolved.

This is test verification, not a request to add or modify CI infrastructure.

### Plan custody before a new-session handoff

The owner selected a dedicated implementation worktree and branch rooted at the
pinned `rh` head:

```text
Branch: codex/rh-smart-contract-test-coverage
Worktree: /Users/wigglez/dev/ripe-protocol-rh-smart-contract-test-coverage
```

Commit this final document as the branch's first change and record its commit
and blob identities in the handoff. All implementation work governed by this
document must occur in that worktree. This authorizes the local branch,
worktree, and plan commit; it does not authorize a push, PR update, merge, or
direct mutation of `rh`.

## 17. Definition of done

This plan is complete only when:

- The implementation startup report records the immutable plan identity and
  approved D-01/D-02/D-03 decision records.
- Every P0 and P1 test above is implemented or explicitly shown to be covered by
  an existing semantically equivalent test, with the exact file and test name
  recorded in the implementation handoff.
- P2 tests are implemented unless a specific existing equivalent or
  public-unreachability reason is documented.
- Each new revert test proves relevant state is unchanged.
- Each new guard test has a positive control proving the intended branch is
  reached.
- Financial boundary tests assert exact integer values at the boundary and on
  neighboring inputs.
- Removed-selector tests probe deployed runtime behavior.
- Events are checked field by field.
- No required test is skipped or newly marked expected-failure. The existing
  strict Uniswap xfail remains byte-for-byte unchanged outside this plan's
  execution gate under D-03.
- All 21 measured in-scope baseline failures are repaired by their assigned
  Work packages, and every focused module and exact adjacent logical path in
  Section 16 passes on the final dedicated implementation-branch candidate with
  the one explicit BasicVault source-inventory `--ignore`.
- The four known-red/out-of-scope files in Section 16 remain unmodified and are
  recorded as pre-existing exclusions. No other failure or xfail may be carried.
- `contracts/priceSources/UniswapV2Prices.vy` and every file beneath
  `tests/priceSources/uniswap/` are unchanged from the dedicated branch's pinned
  RH baseline, and the acknowledged residual is listed as deferred.
- Changes are limited to tests and narrowly necessary test-only mocks/harnesses.
- Any discovered contract defect is reported with its reproducing test instead
  of being hidden by a weakened expectation.
