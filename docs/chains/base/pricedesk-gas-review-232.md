# PR #232: C01–C26 review changes

This follow-up starts from reviewed head `c0df6656cf1cc6db9e1d3c9b99930318d4c9a694`
on `codex/pricedesk-configurable-gas`. The parent remains
`bdf7f3da7113aabde60ab8eceab6a960a841bb88` on
`codex/base-upgrade-fork-rehearsal`; no upstream drift affected these fixes.
[PR #232](https://github.com/Ripe-Foundation/ripe-protocol/pull/232) records the final
published commit, complete workflow run SHA, job results and run link. This file
records source changes and reproducible local validation, not a deployment approval.
After the parent merges and this PR is retargeted to the repository's `master`,
the resulting integration requires validation again. There is no `main` branch.

## Disposition

| Item | Disposition |
| --- | --- |
| C01 | Fixes below address all five reported existing failures. Complete applicable manual lean workflow validation is required on the final published SHA; the PR description and completion report record that result. Earlier 938-case evidence was only selected-suite validation. |
| C02 | Added the complete source-budget module (18 gas cases) and the named nested BlueChip starvation case to snapshot-gas; the inclusion guard requires both. The 30-minute limit is unchanged. |
| C03 | Corrected the CLI runtime-template pin to 24,360 and removed the retired-waiver comment; the separate complete deployed pin remains 24,488. |
| C04 | Both governance callback doubles and the repayment/stock-backing doubles implement the successful no-op relay. `getAddr`, unsafe-asset checks and the callback's `addPriceSnapshot` phase remain. |
| C05 | The rollback test positively requires `intended post-callback rollback`, emitted only after callback success. Balance, points, debt, participation and event restoration checks remain. The missing-relay in-memory negative control must fail this exact assertion. |
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

The diagnostic retained all behavioral assertions and exposed all three original
violations in one failure. Only those three limits changed: measured gas × 1.05,
rounded up to the next 10,000. Existing passing limits were retained. The cost of
configurable-budget reads remains explicit; no production optimization was adopted.

Teller's CLI runtime template is **24,360 bytes**. Its complete deployed runtime is
**24,488 bytes** including immutable data, leaving **88 bytes** below EIP-170.
PriceDesk remains **19,541 bytes** (5,035 bytes headroom). The complete runtime-table
test and template test remain separate. The new Curve 3.5M quote allowance appears
only in a regression; Base's approved 1.5M/1.5M immutable floors are unchanged.

## Reproducible validation

Run from the designated worktree with `PRICEDESK_PYTHON` pointing to the repository's
pinned Python environment. Cache/output paths below are local review artifacts.

```sh
export PYTHONHASHSEED=0
export PYTHONPYCACHEPREFIX=/private/tmp/pr232-review/python
export RIPE_BOA_CACHE_DIR=/private/tmp/pr232-review/boa

"$PRICEDESK_PYTHON" -m pytest -q --tb=short -o addopts='' \
  -o cache_dir=/private/tmp/pr232-review/pytest \
  --junitxml=/private/tmp/pr232-review/focused-final.xml \
  tests/test_base_review_safety.py tests/test_price_desk_staging.py \
  tests/test_price_desk_gas_helpers.py tests/test_vault_pointer_runtime_sizes.py \
  tests/core/teller/test_teller_deposit.py::test_m1_teller_runtime_size_dual_guard \
  tests/core/teller/test_teller_reentrancy_assessment_proofs.py \
  tests/core/creditEngine/test_credit_repay.py::test_repay_uses_safe_collateral_without_pricing_zero_amount_position \
  tests/core/creditEngine/test_stock_backing.py \
  tests/priceSources/curve/test_robinhood_launch_route.py \
  tests/registries/test_price_desk_isolation.py \
  tests/registries/test_price_desk_source_budgets.py \
  tests/vaults/modules/test_stab_vault_hardening.py::test_value_and_maintenance_gas_remain_bounded_at_active_claim_ceiling

"$PRICEDESK_PYTHON" -m pytest --collect-only -q -o addopts='' -m gas \
  tests/registries/test_price_desk_source_budgets.py
"$PRICEDESK_PYTHON" -m pytest -q \
  tests/test_lean_shard_coverage.py tests/inventory/test_repository_hygiene.py
"$PRICEDESK_PYTHON" -m pytest -q -o addopts='' \
  tests/deployment/test_robinhood_blueprint.py
"$PRICEDESK_PYTHON" scripts/export_abis.py --check
git diff --check
git grep -lI '/''Users/'  # Expected status 1: no matches.

gh workflow run python-tests.yml --repo Ripe-Foundation/ripe-protocol \
  --ref codex/pricedesk-configurable-gas -f lane=lean
```

The hygiene grep uses a split pattern to avoid embedding the prohibited path. The unchanged hygiene rule
also checks machine hostnames and embedded session citations.

The repaired rollback test also runs with a local pytest collection plugin removing
only `addGreenRefPoolSnapshot` from `GOVERNANCE_REVERTING_PRICE_CALLBACK_SOURCE`
in memory. Invoke the same node with `PYTHONPATH=/private/tmp/pr232-review` and
`-p rollback_negative_control`. Its expected failure is the positive distinctive
reason assertion at the early missing-relay call; no worktree file is mutated.
The positive run retains all accounting/event rollback assertions.

Complete validation means the 12 lean shards, deployment-controls, snapshot-gas
and Solidity job all succeed on the published SHA. Manual dispatch skips only the
PR/merge aggregation job `rh-pr-gate`. Lean excludes deployment, release, artifact,
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
