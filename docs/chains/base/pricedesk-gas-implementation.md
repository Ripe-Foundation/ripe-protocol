# PriceDesk gas implementation and review follow-up

The contract implementation is commit `e35f86542eb516ee7953e336845bafe9ee9b00ab`,
stacked on PR #231 pin `bdf7f3da7113aabde60ab8eceab6a960a841bb88` in
`codex/pricedesk-configurable-gas`, worktree
`/Users/wigglez/dev/ripe-protocol-pricedesk-gas`. This follow-up addresses the
review feedback with local tests, staging compatibility fixes and documentation.
It does not approve a production configuration, deployment, activation or release.

The integration branch still resolves to the original `bdf7f3da` pin (read-only
remote check on 2026-09-19). Executed `2026091402`/`2026091403`, Base deployment
manifests and the historical constructor-position test remain unchanged. The
existing planning packet stays untracked; its follow-up document and corresponding
packet checksum were updated in place, and the operative instructions are also
recorded in this committed report and the staging guide.

The follow-up commits are `fc275c5c` (staging compatibility), `ce54ae6e`
(test coverage and measurements), and the documentation commit containing this
report. They are local and GPG-signed.

## Configuration decisions still requiring the owner

The original approved prompt explicitly retained Base's 1.5M quote / 1.5M
snapshot floors and Robinhood/local's 250k / 150k floors. Two questions were
submitted during this follow-up; until answered those configuration values remain
unchanged:

1. **Base:** recommend 250k quote / 150k snapshot / 75k feed defaults, with
   separately configured and qualified address-specific overrides, including
   Undy. A 1.5M immutable quote floor makes each repeated faulty-source call much
   more expensive and cannot later be lowered through governance. The new
   staging bodies remain unqualified inputs, not deployable release approval.
2. **Robinhood/local Curve:** recommend a 500k snapshot override to preserve
   Teller's previous allowance. Without one, Curve shares the 150k default with
   generic asset snapshots. The reviewer's approximately 111k live-Base result
   suggests only 1.35x headroom at 150k, but a Base measurement does not qualify
   Robinhood's actual source, pool, state or gas schedule. Neither 150k nor 500k
   should be presented as qualified for an unmeasured deployment.

Feed defaults remain 75k and the provisional maximum is 6M. No selected override
or maximum is a substitute for cold source measurements and complete-transaction
qualification. Do not stage a final candidate until its permanent floors and
per-address overrides are settled and authenticated.

## Disposition of the review

| Review item | Disposition |
| --- | --- |
| 1. Base floor and nested faults | Owner choice pending above. Added a cold synthetic comparison reproducing the 1.5M floor's repeated-failure cost and lost Undy route, alongside a 250k floor / 2M Undy experiment. These are experiments, not live-source qualification. |
| 2. Teller activation order | Added a real-Teller regression against a desk without the relay, including last-touch rollback. Documented slot 7 before slot 17, including atomic ordering and rollback. The full-update diagnostic explicitly checks that order. |
| 3. Foxtrot runtime failure | Fixed the stale 12,061-byte expectation to the measured 18,278 bytes. The growth came from predecessor `0833dddd`; the earlier implementation report missed the full edited runtime-table test. That omission was an error. The full table is now in the recorded default lane. |
| 4. Curve snapshot allowance | Owner choice pending above; no silent acceptance of the lower margin. |
| 5. Curve cold boundary | Reproduced and pinned warm 120k and cold 160k at 10k resolution, with a cold 250k/160k = 1.5625x margin check. The old 110k warm pin understates the current requirement. |
| 6. Constructor consumers | Appended both arguments in the two snapshot diagnostic call sites. Added new `2026091900` full-oracle staging and `2026091901` bridge/Teller staging bodies with fresh labels. The full-update diagnostic selects and fingerprints the new oracle body. Frozen `2026091402`/`2026091403` and deployed manifests are unchanged. |
| 7. Three-field replacement | Read-modify-write procedure below; zero is explicitly a reset. |
| Feed check inside snapshots | Default/override underfunding tests prove no source call occurs; another test proves a later feed-check failure rolls back an earlier snapshot. |
| Permissionless token-scale sync | Default/override feed-budget tests cover underfunding, no writes/events, successful sync and first-set-only behavior. |
| Non-strict conversion helpers | All four helpers cover zero-with-feed, invalid reply, revert and source OOG, with an underfunded failure and fully funded fallback. |
| Committed report / counts | This report records the complete commands and measured results. The previous 245/38 counts combined separate focused runs and omitted the full runtime table. Use the lanes below for this revision. |
| Large original commit | Preserved the signed, already reviewed `e35f8654` rather than rewriting its identity. Review follow-ups are separate commits for tests, staging compatibility and the handoff. |
| Stale staging document | Updated current constructor, configurable budgets, relay/D01 status, candidate labels and activation dependency; marked old bridge evidence as historical. |
| Stable revert text | Tests pin the full `Error(string)` encoding of `insufficient source gas` across conversion helpers. Treat this text as an external compatibility contract. |
| Overhead assumptions | Base gas repricing and cold-access price changes are explicit requalification triggers below and in the planning packet. |
| Test-module coupling | Moved the complete runtime table to `tests/runtime_sizes.py`; gas tests no longer import another collected test module for it. |
| Over-max BlueChip setup | Kept the tightened admission behavior and its state-consistency assertions. A cheap initial route permits setup; the expensive route must still fail confirmation. Previously starved inner calls are not evidence of admissibility under eager qualification. |
| Blueprint source pointers | Refreshed PriceDesk line references and Teller relay descriptions; the Teller-to-Curve edge is now an indirect dependency through PriceDesk. |

## Measured local evidence

The installed Python 3.12.13, pytest 8.4.2, Vyper 0.4.3 / Titanoboa 0.2.7 build counts full deployed runtimes,
including immutables:

| Contract | Bytes | EIP-170 headroom |
| --- | ---: | ---: |
| PriceDesk | 19,541 | 5,035 |
| Teller | 24,488 | 88 |
| SwitchboardFoxtrot | 18,278 | 6,298 |

`SOURCE_CALL_GAS_OVERHEAD = 5,000` was checked against actual compiled instructions
at both default budgets and the 6M maximum:

| Call path | Measured overhead |
| --- | ---: |
| Ordinary quote | 2,667 |
| Eager admission quote | 2,881 |
| Feed check | 2,859 |
| Generic snapshot (source warmed by the feed check) | 361 |
| Green-reference relay | 2,859 |

The smallest remaining margin is 2,119 gas. This is evidence for the tested
compiler, call paths and EVM schedule, not a permanent constant across repricing.

The identical cold-prestate snapshot tests bisect local **execution** gas and
check a coarse grid plus limits within 128 gas of the boundary:

| Mock path, 1.5M snapshot allowance | First successful execution limit |
| --- | ---: |
| Generic asset snapshot | 1,649,341 |
| Green-reference relay | 1,640,912 |

No non-monotonic success bands were observed at tested limits. Successful state
and events match a generous-gas run; failures restore earlier snapshot/caller
writes. Even a not-due no-op needs the eager forwarding proof. These mock limits
exclude transaction intrinsic gas and do not qualify RPC estimation or actual
production D01 behavior.

The four-coin Curve quote sweep now records both warm 120k and cold 160k. Compared
with the old warm 110k pin, 10k of the difference is visible under warm execution
and another 40k comes from cold measurement (all at 10k resolution). The cold
margin is **1.5625x**, not 2.27x. This applies only to that fixture and topology.

The Base nested-fault comparison uses priority `[1,8,2,9,4,5]`, a source that
exhausts every Chainlink call, Undy performing one/two underlying lookups, its
no-feed revisits, and a healthy outer fallback. Price 200 means the nested Undy
route survives; price 42 means it was lost and the outer fallback answered.
The final test log records each envelope and total execution gas. This quote-only
comparison does not measure snapshots or live dependencies. These synthetic
results cannot select production Undy budgets by themselves.


| Quote floor | Undy allowance tested | Nested lookups | Result | Execution gas |
| --- | --- | ---: | --- | ---: |
| 1.5M | 1.5M default | 1 | Outer fallback | 3,024,766 |
| 1.5M | 3M override | 1 | Undy survives | 3,071,541 |
| 1.5M | 3M override | 2 | Outer fallback | 4,525,358 |
| 1.5M | 3.5M override | 2 | Undy survives | 4,580,928 |
| 1.5M | 6M override | 2 | Undy survives | 4,580,928 |
| 250k | 2M override | 2 | Undy survives | 830,928 |

One correction to the review: **6M is not required by this mock route**; 3.5M
also succeeds. These trials do not find the minimum successful allowance.
The repeated-failure cost and permanent-floor concern are nevertheless confirmed.

## Exact verification commands

Run from the designated worktree. The interpreter is shared with the original
checkout; `pytest.ini` resolves repository/test imports from this worktree.
All local artifacts and caches go outside the checkout:

```sh
cd /Users/wigglez/dev/ripe-protocol-pricedesk-gas
export PYTHONPYCACHEPREFIX=/private/tmp/pricedesk-configurable-gas/python
export RIPE_BOA_CACHE_DIR=/private/tmp/pricedesk-configurable-gas/boa
pricedesk_python=/Users/wigglez/dev/ripe-protocol/.venv/bin/python
mkdir -p /private/tmp/pricedesk-configurable-gas

"$pricedesk_python" -m pytest -q \
  -o cache_dir=/private/tmp/pricedesk-configurable-gas/pytest \
  --junitxml=/private/tmp/pricedesk-configurable-gas/review-default.xml \
  tests/registries/test_price_desk_isolation.py \
  tests/registries/test_price_desk_token_decimals.py \
  tests/test_price_desk_aggregate_source_count_guard.py \
  tests/test_base_review_safety.py \
  tests/test_vault_pointer_runtime_sizes.py \
  tests/test_price_desk_staging.py \
  tests/priceSources/curve/test_green_ref_pool.py \
  tests/registries/test_price_desk_source_budgets.py \
  tests/config/test_defaults_base_priority_id9.py \
  tests/config/test_switchboard_bravo_green_snapshot.py \
  tests/config/test_switchboard_bravo_token_scale.py::test_replacement_mission_control_updates_only_its_price_desk \
  tests/priceSources/aero/test_minimal_prices.py::test_price_desk_composition_treats_monitor_as_valid_no_feed \
  tests/priceSources/curve/test_robinhood_launch_route.py \
  > /private/tmp/pricedesk-configurable-gas/review-default.log 2>&1

"$pricedesk_python" -m pytest -q -s -m gas \
  -o cache_dir=/private/tmp/pricedesk-configurable-gas/pytest \
  --junitxml=/private/tmp/pricedesk-configurable-gas/review-gas-final.xml \
  tests/registries/test_price_desk_gas.py \
  tests/registries/test_price_desk_aggregate_protocol_gas.py \
  tests/registries/test_price_desk_source_budgets.py \
  tests/priceSources/curve/test_robinhood_launch_route.py \
  > /private/tmp/pricedesk-configurable-gas/review-gas-final.log 2>&1

"$pricedesk_python" -m pytest -q -o addopts='' \
  -o cache_dir=/private/tmp/pricedesk-configurable-gas/pytest \
  --junitxml=/private/tmp/pricedesk-configurable-gas/review-abi-staging.xml \
  tests/deployment/test_stale_time_oracle_abi.py \
  tests/deployment/test_base_staging_runner_order.py \
  tests/deployment/test_price_desk_token_scale_bootstrap.py \
  > /private/tmp/pricedesk-configurable-gas/review-abi-staging.log 2>&1
```

Default and gas lanes retain repository addopts. The final command deliberately
selects only the three directly relevant, normally excluded files; it does not
run the deployment suite. Results: **292 default + 44 gas + 21 ABI/staging = 357 distinct passing tests**,
with zero failures, errors or skips in these selected lanes. JUnit case identities
were checked for duplicates across the three runs. The Robinhood blueprint's
built-in validation also passes when importing `config.robinhood_blueprint`. No full suite, RPC
fork, live qualification, deployment, Safe operation, push or publication was run.

## Budget changes and activation

`setSourceGasBudgets(source, quote, snapshot, feed)` replaces **all three raw
fields**. Each zero independently resets that field to its immutable default.
To change only one effective budget:

1. Bind the chain, current PriceDesk and exact source address. Read
   `getSourceGasBudgets(source)` immediately before preparing the change.
2. Preserve the two effective values not being changed, replace the intended
   value, and submit all three values. For example, `(2M, 1.5M, 75k)` changing only
   feed gas to 100k becomes `(2M, 1.5M, 100k)`, never `(0, 0, 100k)`.
3. Simulate the full call and source/transaction consequences, then verify all
   three effective values and `SourceGasBudgetsUpdated` after execution. Recheck
   for intervening governance changes before signing/execution.

The view exposes effective values. Preserving a default as an explicit nonzero
value preserves behavior but differs from raw zero in events. If raw-zero
representation matters, reconstruct the raw fields from authenticated events;
do not infer them from the effective getter. Overrides follow addresses, remain
after disable/re-enable, and never migrate to a replacement address. Configure
and qualify replacements before admitting/activating them.

Both current candidates must be authenticated. Confirm **HQ slot 7 first**, then
**slot 17**, or both atomically in that order. Verify the relay selector and all
source overrides before opening Teller. Roll back the relay Teller before
restoring an incompatible desk. See [the staging guide](staged-upgrade-deployment.md).

## Remaining release work and limitations

Canonical `(price > 0, true)` and `(0, false)` replies intentionally bypass the
ordinary-quote full-budget proof. A dependency can catch inner underfunding and
return a plausible but wrong canonical answer; the desk cannot authenticate that
answer from this interface. Focused mock and real-wsuperOETHb-composition tests
preserve this limitation. Authenticate deployed source/dependency behavior before
accepting this policy for a release; local green tests do not close it.

Qualify the final source addresses, implementations, feed/priorities, budgets,
asset inventory, mature observations, supported batches and complete transactions
at a fresh finalized Base block. Retain the owner's 1.5x source/normal-transaction
margins, repeated/nested single-fault model, 80%-of-cap bound, and Pool-1 claim
qualification. Production D01 still requires the actual client's `eth_estimateGas`
and submitted buffered/generous comparisons for both snapshot paths. The new
staging tests use real PriceDesk/Teller code with local legacy-dependency doubles;
they do not replace the full fork rehearsal or journal/resume qualification.

Requalify after code, compiler/optimizer, source, dependency, budget, priority,
ring/batch, chain/client changes, **Base gas repricing**, or cold-access cost
changes. Remeasure the compiled overhead and all affected forwarding envelopes.
The changed BlueChip setup is a reminder that admission must fund inner failures:
a route previously admitted via starved nested calls can fail under the new
requirements. Neither a floor nor an immediate governance setter guarantees
ongoing source availability.
