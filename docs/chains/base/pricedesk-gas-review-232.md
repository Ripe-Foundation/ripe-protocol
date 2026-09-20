# PR #232: implementation review closure

This document records the C01–C26 changes from reviewed head
`c0df6656cf1cc6db9e1d3c9b99930318d4c9a694` and the R01–R16 follow-up from
`eaf460bf2fc5d1bf75ccf966903c6898b8889701`, plus the nine-item maintenance
follow-up from `4b31851f0862648a504d5f46b7c300d2313710cc`. The dedicated branch remains
`codex/pricedesk-configurable-gas`, stacked on parent
`bdf7f3da7113aabde60ab8eceab6a960a841bb88` (`codex/base-upgrade-fork-rehearsal`).
The 2026-09-20 initial readback found no subsequent head or parent changes.
Signed prior history is preserved. [PR #232](https://github.com/Ripe-Foundation/ripe-protocol/pull/232)
binds the final published/validated commit to its complete workflow run, actual
counts and immutable links to this document and the handoff. This is implementation
review evidence, not deployment approval.

## Remaining maintenance follow-up: items 1–9

| Item | Disposition and evidence |
| --- | --- |
| 1 | Disclose all three inherited unsupported edges R-100, R-101 and R-108 below, in the implementation handoff and PR description. Qualify `config/robinhood_blueprint.py`'s current-source description. Graph entries and 166 direct / 12 indirect counts remain unchanged. |
| 2 | `KNOWN_NON_CODE_REFERENCES` in `tests/deployment/test_robinhood_blueprint.py` pins each of the 30 distinct exceptions and its occurrence allowance (36 total). The shared content validator rejects new or extra non-code references, allows repairs, retains all bounds/Teller/duplicate/named-call checks, and does not claim semantic validation. Five new regression cases cover non-Teller comments, extra existing exceptions, repair, and both bounds. Remove obsolete baseline entries or reduce counts when references are repaired. |
| 3 | The legacy CLI module description and all eight rejected flags direct users to `scripts/base_full_update_fork.py`. Help coverage checks every flag; early rejection and inherited methods remain. `test_legacy_staging_selection_reaches_load_dotenv` establishes parsing reaches setup at `load_dotenv`, not successful staging execution. |
| 4 | Add the enclosing-allowance mechanism immediately before the nested GREEN zero-price assertion. Direct fallback, zero result, strict revert and diagnostic 3.5M recovery remain unchanged; the larger allowance is not a production recommendation. |
| 5 | Archived `anvil-estimator-smoke-v5.py` now exits with a quoted configuration example for missing/empty `PRICEDESK_REVIEW_OUTPUT`, before directories or Anvil. Three offline controls cover missing/empty values and output paths containing spaces, intercepting process launch. This is archive maintenance, not new Anvil or production qualification evidence. |
| 6 | The rollback negative control invokes the same positive proof with named arguments and explains intentional coupling. Distinctive assertion, underlying `BoaError`, errored relay, absent callback and all positive restoration/event assertions remain. |
| 7 | Repair the relative PriceDesk link in `evidence/reviewer-v4.txt`, introduced by this PR at `c0df6656` and unchanged through the reviewed follow-up; it was not inherited from the parent. Refresh published archive hashes while retaining the original inventory. Whole-PR link validation includes Markdown and non-Markdown documentation and multiline labels. |
| 8 | Preserve every gas ceiling, the parent/current comparisons below, and existing behavior/accounting checks. These are local regression tolerances; no 2.5% tightening or new owner gate was requested or added. |
| 9 | Preserve parent merge → retarget to `master` → integration revalidation → actual eligible `rh-pr-gate` success, plus all separate qualification and activation requirements. None is completed by this maintenance work. |

## R01–R16 follow-up disposition

| Item | Disposition and file/test evidence |
| --- | --- |
| R01 | Aligned `config/BluePrint.py` comments, candidate README, implementation handoff, deferred qualification and this closure: retain Base's 1.5M/1.5M immutable floors for the approved implementation/rehearsal scope. Production qualification and any owner decision to lower them remain separate; no later lower-floor decision is recorded. Record the final decision and date when established. Lowering a deployed floor requires a replacement PriceDesk; overrides cannot do it. Values are unchanged. |
| R02 | Added the parent/current comparison and sensitivity explanation below; retained all nine ceilings and behavioral assertions without a new approval gate. |
| R03 | `test_governance_rollback_proof_rejects_missing_relay` in `tests/core/teller/test_teller_reentrancy_assessment_proofs.py` removes only the relay stub in memory, invokes the same positive proof, and catches only its distinctive failed post-callback assertion. It requires the underlying BoaError, an errored relay call and no snapshot callback call. Compilation/setup/unrelated assertion errors cannot satisfy the control. All positive balance, points, debt, participation and event assertions remain. No temporary plugin is required. |
| R04 | `scripts/base_upgrade_fork.py::main` rejects `--probe` and all seven dependent modes immediately after parsing. Eight parameterized `test_legacy_probe_cli_rejects_before_setup` cases in `tests/test_base_review_safety.py` forbid setup/environment/RPC access, check exit 2 and the full-update diagnostic. The supported-selection test reaches `load_dotenv`; it does not establish full staging execution. Existing import/help/compatibility tests remain. |
| R05 | `_gas_source`, `_raw_source`, `_set_priorities`, `ETH` and `ZERO_ADDRESS` now live with the builder in non-collected `tests/registries/price_desk_helpers.py`. Isolation and source-budget suites import it directly; helper bodies, constructor budgets and ordering are preserved. |
| R06 | Re-anchored all 21 authority relations in `config/robinhood_blueprint.py` to `_isSwitchboardAddr` and actual exported/wrapped callers. Current source also shows Endaoment's guarded wrappers and StabilityPool's disabled recovery, now accurately cited. Repaired R-099/R-271/R-279 by actual target calls, removed R-238's duplicate, and trimmed unrelated Teller headings. `test_robinhood_blueprint.py` validates all source-pointer bounds, duplicate relation pointers, the original Teller content check, and the named authority/direct-call evidence; 166 direct / 12 indirect edges remain. Bravo wording now identifies its current asset-deposit/accrual writes. |
| R07 | The handoff's selected inventory now covers Curve, Undy, BlueChip, wsuperOETHb, conditional RedStone and retained legacy Aero, with source/config links and profile enablement. It links the explicitly incomplete, deferred production inventory; current monitor code does not authenticate legacy Aero. |
| R08 | Added the deferred D01 caller/estimator evidence matrix in `pricedesk-gas-plan/follow-up-qualification.md`, covering identical inputs/pre-state, due/no-op/ring/batch/position state, actual RPC/buffered/generous limits, state/events and final binding across wallets/frontends, keepers, liquidation and Appraiser/integrations. No qualification run or operational tool added. |
| R09 | Renamed the Curve regression to `test_nested_curve_fallback_requires_sufficient_enclosing_quote_budget`; removed two misplaced comments and retained the explanation in the actual allowance-margin test. Direct fallback, nested failure, strict caller and illustrative recovery assertions remain. |
| R10 | `test_drafts_do_not_enter_live_base_migration_queue` detects stable candidate identifiers through parsed string constants as well as bytes/names. Both drafts fail the renamed CamelStyle/comment-edited control. Ordinary/fresh-label future migrations and advancing synthetic history remain allowed; real history is untouched. |
| R11 | Quoted worktree/cache/output paths in the current handoff and historical commands; documented `PRICEDESK_REVIEW_OUTPUT` as generated outputs. The negative control requires only committed input. Published packet hashes are refreshed while `original_published_inventory` and historical capture hashes remain unchanged. |
| R12 | The PR completion statement and evidence links bind to the final published SHA after it exists; workflow evidence must match that same SHA. The final PR description is the post-publication record. |
| R13 | Evidence README labels the contracts/tests-only instruction as historical revision-7 scope, links current handoff/closure, and retains the notice that portability/navigation edits changed archival bytes. |
| R14 | Separate topical commits retain the existing signed history. This table maps every requested item to evidence; the final report identifies the new signed commits. |
| R15 | Accepted governance/API behavior is unchanged: immediate `_canGovern` writes while paused, separate registry timelocks, whole-tuple writes, per-field zero resets, effective getter, address lifecycle and read-modify-write/intervening-change checks. No new timelock, getter or paused-write restriction. |
| R16 | Refreshed #231/#232 status and retained parent-merge → retarget to `master` → revalidate integration. Manual CI cannot satisfy `rh-pr-gate`; a later eligible PR/merge-group run must execute/pass it, and retargeting alone is not a guaranteed trigger. Qualification, authentication, fork/claim, deployment and activation boundaries remain below. |

### Wider blueprint drift retained by owner direction

The reviewed baseline contains **30 distinct blank/comment-only references,
appearing 36 times**, outside the named R06 repairs. Separately, these three
unsupported direct relationships are inherited from parent `bdf7f3da` and remain
included in the pinned **166 direct relationships**:

| Relationship | Current-source evidence problem | Disposition |
| --- | --- | --- |
| R-100, Bravo → Switchboard | `SwitchboardBravo.vy:490–492` is MissionControl asset-deposit logic, not the claimed Switchboard call. | Retained; wider graph reconciliation deferred. |
| R-101, Bravo → Alpha | Cites the same unrelated `SwitchboardBravo.vy:490–492`; current Bravo makes no corresponding Alpha call. | Retained; wider graph reconciliation deferred. |
| R-108, Charlie → AuctionHouse | Current Charlie makes no corresponding AuctionHouse call. | Retained; wider graph reconciliation deferred. |

On 2026-09-20 the owner explicitly directed: **"Preserve the scoped graph and
report wider drift"**. These entries and the 166 direct / 12 indirect counts remain
unchanged. The general safeguard checks bounds and substantive content across all
covered source files, with explicit occurrence limits for the known non-code
exceptions. It rejects new exceptions and additional occurrences while permitting
repairs; bounds, duplicate-reference and Teller-content checks remain. Substantive
content does not establish a claimed call: R-100/R-101 illustrate that distinction.
Semantic checks cover the named R06 relationships, not the entire historical graph.
Reconciliation remains separate implementation work. The complete non-code pointer
inventory follows; occurrence allowances are explicit in the test baseline.

The exploratory non-code-pointer list (not a complete semantic audit) is:

| Current source file | Inherited pointer line(s) retained |
| --- | --- |
| `contracts/config/SwitchboardCharlie.vy` | `442`, `464` |
| `contracts/config/SwitchboardDelta.vy` | `527`, `1088` |
| `contracts/core/AuctionHouse.vy` | `414`, `1123` |
| `contracts/core/CreditEngine.vy` | `192`, `269`, `604`, `734`, `1145`, `1233` |
| `contracts/core/CreditRedeem.vy` | `204`, `207`, `244`, `312`, `319` |
| `contracts/core/Deleverage.vy` | `580`, `996`, `1199` |
| `contracts/core/EndaomentPSM.vy` | `293` |
| `contracts/core/Lootbox.vy` | `1217-1220` |
| `contracts/core/TellerUtils.vy` | `143` |
| `contracts/registries/VaultBook.vy` | `147`, `161`, `162` |
| `contracts/vaults/RipeGov.vy` | `259`, `383` |
| `contracts/vaults/modules/StabVault.vy` | `651`, `866` |

## C01–C26 disposition

| Item | Disposition |
| --- | --- |
| C01 | Fixes below address all five reported existing failures. Complete applicable manual lean workflow validation is required on the final published SHA; the PR description and completion report record that result. Earlier 938-case evidence was only selected-suite validation. |
| C02 | Added the complete source-budget module (18 gas cases) and the named nested BlueChip starvation case to snapshot-gas; the inclusion guard requires both. The 30-minute limit is unchanged. |
| C03 | Corrected the CLI runtime-template pin to 24,360 and removed the retired-waiver comment; the separate complete deployed pin remains 24,488. |
| C04 | Both governance callback doubles and the repayment/stock-backing doubles implement the successful no-op relay. `getAddr`, unsafe-asset checks and the callback's `addPriceSnapshot` phase remain. |
| C05 | The rollback test positively requires `intended post-callback rollback`, emitted only after callback success. Balance, points, debt, participation and event restoration checks remain. The committed R03 negative control proves the missing-relay variant fails this exact assertion. |
| C06 | All nine absolute gas measurements/violations are reported together. The three exceeded limits receive explicit measured headroom below; accounting, monotonic growth and relative traversal checks remain. |
| C07 | Removed local-user paths without exempting archives from hygiene. Current published hashes/sizes and original reviewed-head hashes are separate inventory fields. |
| C08 | Real Curve/Chainlink regression preserves direct fallback success, nested failure at the Base floor, strict-caller failure and recovery with an illustrative larger enclosing allowance. The nested route inventory and isolation scope are in the implementation handoff. No production budget or contract changed. |
| C09 | Preserved deferred RPC-estimator D01 for both snapshot paths and all callers, including Appraiser. The handoff records the 19 housekeeping sites, conditional deposit path and no-op funding requirement. |
| C10 | Qualified failure-isolation wording in the handoff and PR description by invocation and enclosing boundary; retained canonical-wrong-answer limitations. |
| C11 | Preserved final implementation/address/config binding, 1.5x source and normal-transaction margins, repeated/nested single-source faults, supported batches/positions and 80%-of-cap qualification. Recheck the actual cap; changing the immutable maximum requires deployment. |
| C12 | A shared dependency validator rejects the older compatibility plan before registry reads or mutations and identifies the full-update harness. Import/help tests remain; current activation uses the same validator. Four historical documents bind reproduction scope; individual evidence identifies distinct harness hashes. |
| C13 | Explicitly distinguished historical `TellerBaseUpgradeCandidate20260914` from unauthenticated current `TellerPriceDeskGasCandidate20260919`; cutover/rollback ordering remains. |
| C14 | Separate Base/local/Robinhood fixtures deploy all four constructor settings, apply/read back the actual override table, authorize the desk locally and exercise real Curve quotes/due snapshots. The Base Undy stand-in checks the applied quote allowance only. Generic fixtures remain default-only; earlier profile-labeled cases are explicitly allowance-margin tests. |
| C15 | Preserved immediate `_canGovern` budget writes while paused, distinct from registry timelocks, and their existing permission coverage. |
| C16 | Preserved whole-tuple replacement, zero resets, effective-only getter, address lifecycle, read-modify-write and intervening-change checks. No raw getter added. |
| C17 | Preserved 5,000 compiled-overhead allowance, measured maximum 2,881 and remaining margin 2,119; compiler/gas-schedule requalification remains mandatory. |
| C18 | Semantically re-anchored all 49 Teller references, including inherited invalid ranges, and corrected obsolete hard-coded route wording. Added current-source bounds/non-comment coverage; 166 direct / 12 indirect relation pins remain. |
| C19 | Tests exclude drafts directly from the real queue and exercise frontier/start behavior against isolated history with a legitimate future migration. A timestamped draft copy is detected by the same assertion. Live history is unchanged. |
| C20 | Moved the shared isolated PriceDesk builder to non-collected `registries/price_desk_helpers.py` and changed every consumer. Constructor defaults and source ordering are unchanged. |
| C21 | Documented Titanoboa 0.2.7 / py-evm 0.12.1b1 private journal assumptions. Normal/exception tests prove cold account/storage state, restoration of journal identity and warmth, and usable enclosing/nested anchors. The finally also covers reset/setup errors. |
| C22 | Documented repository-relative `migration_source_sha256` keys versus historical basename-oriented keys, preserving archive and bridge/helper coverage. No unsupported consumer or normalizer was invented. |
| C23 | Current publication status links the dated PR; no-push statements explicitly describe historical local validation. GPG signing remains accurate. |
| C24 | Repaired all 24 broken archive links to corresponding versions/shared supplements. Portability edits are labeled; current and original published hashes remain distinguishable. |
| C25 | Packet entry point leads to current implementation/closure status and deferred release boundaries; original imperative directions are visibly historical. |
| C26 | Preserved executed migrations 1402/1403, deployed manifests and out-of-queue rehearsal bodies. Future production bodies still require qualified values, fresh timestamps/labels and authorization. |

## Gas measurements and unchanged runtimes

Python 3.12.13, pytest 8.4.2, Vyper 0.4.3, Titanoboa 0.2.7 and py-evm 0.12.1b1,
local Boa EVM, `PYTHONHASHSEED=0`, 20 active claim assets and maintenance batch 15.
The test measures Boa execution-gas deltas with its existing anchor/warmth setup;
these are local regression limits, not intrinsic-inclusive production gas limits.
No production contract code or compiler configuration changed in this review round.

| Path | Measured gas | Previous ceiling | Final ceiling | Headroom over measurement |
| --- | ---: | ---: | ---: | ---: |
| Deposit | 575,512 | 540,000 | 610,000 | 5.99% |
| Withdrawal | 515,208 | 480,000 | 550,000 | 6.75% |
| Existing receipt | 11,214 | 50,000 | 50,000 | 345.87% |
| Prune | 404,592 | 500,000 | 500,000 | 23.58% |
| Activation | 999,281 | 1,200,000 | 1,200,000 | 20.09% |
| Single claim | 905,697 | 1,390,000 | 1,390,000 | 53.47% |
| Claim batch | 9,314,307 | 9,100,000 | 9,790,000 | 5.11% |
| Liquidation preflight | 490,664 | 600,000 | 600,000 | 22.28% |
| Liquidation iterator | 490,181 | 600,000 | 600,000 | 22.40% |

The parent comparison uses the same local measurement basis:

| Path | Parent measurement / ceiling | Parent headroom | Current measurement / ceiling | Current headroom |
| --- | ---: | ---: | ---: | ---: |
| Deposit | 536,011 / 540,000 | 3,989 gas; 0.74% | 575,512 / 610,000 | 34,488 gas; 5.99% |
| Withdrawal | 475,707 / 480,000 | 4,293 gas; 0.90% | 515,208 / 550,000 | 34,792 gas; 6.75% |
| Claim batch | 8,608,932 / 9,100,000 | 491,068 gas; 5.70% | 9,314,307 / 9,790,000 | 475,693 gas; 5.11% |

Deposit and withdrawal gained relative headroom, so the updated ceilings are less
sensitive to small increases than their parent limits. Claim-batch headroom
tightened slightly. A 5% tolerance, rounded up to 10,000, accommodates small local
execution/layout cost changes while still failing larger increases on these
costly paths; it is a regression tolerance, not production transaction sizing.
Rounding makes the deposit/withdrawal allowance somewhat larger than 5%. The
existing-receipt ceiling remains comparatively loose at about 346% headroom;
the nine-path check is not equally sensitive on every path. Behavioral, accounting,
monotonic-growth and relative-traversal assertions remain independent safeguards.
Routine local ceiling updates do not introduce a new owner-approval gate. R02
changes no ceiling and requires no production optimization.

The diagnostic retained all behavioral assertions and exposed all three original
violations in one failure. Only those three limits changed: measured gas × 1.05,
rounded up to the next 10,000. Existing passing limits were retained. The cost of
configurable-budget reads remains explicit; no production optimization was adopted.

Teller's CLI runtime template is **24,360 bytes**. Its complete deployed runtime is
**24,488 bytes** including immutable data, leaving **88 bytes** below EIP-170.
PriceDesk remains **19,541 bytes** (5,035 bytes headroom). The complete runtime-table
test and template test remain separate. The new Curve 3.5M quote allowance appears
only in a regression; Base's implementation/rehearsal 1.5M/1.5M immutable floors
are unchanged, with production qualification and any lower-floor decision separate.

## Remaining maintenance local validation

The nine-item follow-up passed **122 focused tests**: 84 blueprint cases,
35 CLI/staging/archive-safety cases, both governance rollback proofs, and the
nested Curve regression. There were **no skips, deselections or failures** in
this explicit selection. It used a fresh Boa cache and an output path containing
spaces. The workflow/hygiene checks passed **27 tests**, for **149 distinct local
passes**. No skip, xfail or workflow exclusion was added. The supported CLI
selection check stops at `load_dotenv`; Anvil checks intercept process launch.
Neither establishes a completed staging or Anvil execution.

Whole-PR relative-link validation compares parent `bdf7f3da` to the final review
contents and inspects every added/modified Markdown file anywhere in the repository
plus every added/modified non-Markdown file under `docs/`. It handles multiline
Markdown-style labels in both formats. Final scope: **28 Markdown files / 97
relative-link occurrences**, **21 non-Markdown documentation files / 1 occurrence**;
**49 files / 98 occurrences, zero broken targets**. The same checker reproduced
the reviewed baseline's 98 occurrences with exactly the reported broken archive
link. The previous 62-link check was a narrower Markdown-only scope.

Packet validation verifies all **39 current** and **39 original** size/SHA-256
entries, exact **40-file** coverage including the manifest, and unchanged
`original_published_inventory`. Scope checks confirm production contracts,
interfaces/ABIs, budget values, gas ceilings, compiler settings, CI configuration,
executed migrations and deployed manifests are unchanged from `4b31851f`.
Only the blueprint module docstring changed; its graph data is identical.

Use the output/cache environment documented below, then run:

```sh
"$PRICEDESK_PYTHON" -m pytest -q --tb=short -o addopts='' \
  -o cache_dir="$PRICEDESK_REVIEW_OUTPUT/pytest" \
  --junitxml="$PRICEDESK_REVIEW_OUTPUT/focused.xml" \
  tests/deployment/test_robinhood_blueprint.py \
  tests/test_base_review_safety.py \
  tests/core/teller/test_teller_reentrancy_assessment_proofs.py::test_governance_post_clear_nested_deposit_rolls_back_after_housekeeping \
  tests/core/teller/test_teller_reentrancy_assessment_proofs.py::test_governance_rollback_proof_rejects_missing_relay \
  tests/priceSources/curve/test_robinhood_launch_route.py::test_nested_curve_fallback_requires_sufficient_enclosing_quote_budget
"$PRICEDESK_PYTHON" -m pytest -q \
  -o cache_dir="$PRICEDESK_REVIEW_OUTPUT/pytest" \
  tests/test_lean_shard_coverage.py tests/inventory/test_repository_hygiene.py
"$PRICEDESK_PYTHON" scripts/export_abis.py --check
git diff --check 4b31851f
```

Complete applicable workflow evidence belongs to the exact published SHA, recorded
in the PR description after publication. Earlier workflow run `35495658225`
validated only `4b31851f`; it is not evidence for the new maintenance commit.

## Historical R01–R16 local validation (reviewed head `4b31851f`)

The exact focused command below, with a fresh Boa cache and a review-output path
containing spaces, passed **358 tests** (279 affected cases + 79 blueprint cases),
with the existing single C2 attested-interpreter skip. The workflow/hygiene command
passed **27 tests**, for **385 distinct local passes**. Both the positive rollback
proof and its committed negative control passed. Earlier exploratory validation
exposed unrelated non-code blueprint pointers; the scoped final check follows the
owner's direction above, retaining all pre-existing assertions. No skip, xfail or
workflow exclusion was added.

ABI export check passed for **60 exports**, with the existing **58 excluded Vyper
contracts**. All **39 current** and **39 original** packet entries verified, all
**62 links in the then-selected Markdown scope** resolved (not all documentation formats), and shell syntax/path hygiene/diff
checks passed. `config/BluePrint.py` has an identical Python AST to the reviewed
head; only comments changed. Production contracts, budget values, interfaces,
exported ABIs, compiler configuration, workflow selection, executed migrations
and deployed manifests are unchanged from `eaf460bf`.

The local code/test commits are GPG-signed `27816ce6` (proofs/CLI/helpers/drafts)
and `c2ad884c` (scoped blueprint evidence). The final documentation commit follows
these without rewriting history. Complete workflow evidence is recorded after
publication in the PR description, with the exact final SHA and immutable links;
this local result does not substitute for that workflow or for `rh-pr-gate`.

## Reproducible validation

Set `PRICEDESK_WORKTREE` to the existing dedicated worktree and
`PRICEDESK_PYTHON` to the repository's pinned Python executable.
`PRICEDESK_REVIEW_OUTPUT` is an optional writable local output directory; paths
containing spaces are supported. All caches/logs/XML are generated outputs. No
pre-existing output, completion report or temporary pytest plugin is an input.

```sh
cd "$PRICEDESK_WORKTREE"
export PRICEDESK_REVIEW_OUTPUT="${PRICEDESK_REVIEW_OUTPUT:-${TMPDIR:-/tmp}/pr232-review}"
mkdir -p "$PRICEDESK_REVIEW_OUTPUT"
export PYTHONHASHSEED=0
export PYTHONPYCACHEPREFIX="$PRICEDESK_REVIEW_OUTPUT/python"
export RIPE_BOA_CACHE_DIR="$PRICEDESK_REVIEW_OUTPUT/boa"

"$PRICEDESK_PYTHON" -m pytest -q --tb=short -o addopts='' \
  -o cache_dir="$PRICEDESK_REVIEW_OUTPUT/pytest" \
  --junitxml="$PRICEDESK_REVIEW_OUTPUT/focused.xml" \
  tests/test_base_review_safety.py tests/test_price_desk_staging.py \
  tests/test_price_desk_gas_helpers.py tests/test_vault_pointer_runtime_sizes.py \
  tests/core/teller/test_teller_deposit.py::test_m1_teller_runtime_size_dual_guard \
  tests/core/teller/test_teller_reentrancy_assessment_proofs.py \
  tests/core/creditEngine/test_credit_repay.py::test_repay_uses_safe_collateral_without_pricing_zero_amount_position \
  tests/core/creditEngine/test_stock_backing.py \
  tests/priceSources/curve/test_robinhood_launch_route.py \
  tests/registries/test_price_desk_isolation.py \
  tests/registries/test_price_desk_source_budgets.py \
  tests/vaults/modules/test_stab_vault_hardening.py::test_value_and_maintenance_gas_remain_bounded_at_active_claim_ceiling \
  tests/deployment/test_robinhood_blueprint.py

"$PRICEDESK_PYTHON" -m pytest -q \
  -o cache_dir="$PRICEDESK_REVIEW_OUTPUT/pytest" \
  --junitxml="$PRICEDESK_REVIEW_OUTPUT/workflow-hygiene.xml" \
  tests/test_lean_shard_coverage.py tests/inventory/test_repository_hygiene.py
"$PRICEDESK_PYTHON" scripts/export_abis.py --check
git diff --check
git grep -lI '/''Users/'  # Expected status 1: no matches.

gh workflow run python-tests.yml --repo Ripe-Foundation/ripe-protocol \
  --ref codex/pricedesk-configurable-gas -f lane=lean
```

The hygiene grep uses a split pattern to avoid embedding the prohibited path.
The unchanged hygiene rule also checks machine hostnames and embedded session
citations. Packet validation recomputes every `files` size/SHA-256, compares the
untouched `original_published_inventory` to its recorded Git revision, and checks
local links against their actual targets. Portability edits are disclosed in the
packet README and inventory publication notes.

For just the positive proof and committed negative control, use the environment
above and this fresh-checkout command (both cases should **pass**):

```sh
"$PRICEDESK_PYTHON" -m pytest -q --tb=short -o addopts='' \
  -o cache_dir="$PRICEDESK_REVIEW_OUTPUT/pytest" \
  tests/core/teller/test_teller_reentrancy_assessment_proofs.py::test_governance_post_clear_nested_deposit_rolls_back_after_housekeeping \
  tests/core/teller/test_teller_reentrancy_assessment_proofs.py::test_governance_rollback_proof_rejects_missing_relay
```

The negative control deletes only the double's successful relay stub, then calls
the positive proof unchanged. It must fail the distinctive intended-rollback
assertion, with an underlying BoaError trace proving the errored relay and absence
of `addPriceSnapshot`. An arbitrary pytest nonzero exit is not evidence. The
positive case retains every accounting/event restoration assertion.

Complete validation means the 12 lean shards, deployment-controls, snapshot-gas
and Solidity job all succeed on the published SHA. Manual dispatch skips only the
PR/merge aggregation job `rh-pr-gate`. A later eligible PR or merge-group run must
actually execute and pass it. The workflow does not explicitly subscribe to
edited PR events; changing the base branch alone is not a guaranteed trigger.
Lean excludes deployment, release, artifact,
fuzz, gas and fork-qualification markers; separate jobs cover deployment controls
and the selected gas suites. Deployment retains the existing four named defaults
snapshot deselections (seven parameter cases), plus existing marker/archive gates.
No new exclusion was added. CI uses Ubuntu, Python 3.12.0, pinned `requirements.txt`,
Foundry 1.3.5 for Solidity, and the workflow's cleared RPC/credential environment.

## Release boundaries

Implementation review readiness remains separate from production readiness.
Source/transaction budgets, the 6M maximum, RPC-estimator D01, final bytecode/config
readback, full fork rehearsal, deployment and activation remain unqualified or
unauthorized here. Preserve 1.5x source/normal margins, repeated and nested
single-source faults, the actual chain/client cap and its 80% bound. Table entries
are not automatic deployment configuration. Existing candidate labels and frozen
seven-argument migrations do not authenticate compatible new nine-argument desks
or relay Tellers. No live transactions, migration rewrites or merge were performed.


The 2026-09-20 status readback found #231 open with changes requested and #232 a
draft targeting the parent. Do not merge or retarget prematurely. After the
parent merges, retarget #232 to `master` and validate that resulting integration
again. There is no `main` branch. Activate authenticated PriceDesk HQ slot 7 before
relay Teller slot 17 (or atomically in that order); roll back Teller first before
restoring an incompatible desk. Requalify runtimes and compiled forwarding overhead
after compiler/optimizer/code changes and after relevant gas-schedule changes.
Historical harness hashes do not recreate missing original harness bytes.
