# PriceDesk gas implementation and review follow-up

Current review closure: [C01–C26, R01–R16 and remaining maintenance changes and validation](pricedesk-gas-review-232.md).
As of 2026-09-20, the source is published in [PR #232](https://github.com/Ripe-Foundation/ripe-protocol/pull/232).
The earlier review results below are selected-suite historical evidence, not
complete revised-head validation. See the PR description for the final workflow
SHA and run results.

The remaining nine-item maintenance follow-up passed **149 distinct local tests**
(122 focused plus 27 workflow/hygiene), without skips in that selection. Whole-PR
link validation covers all 28 added/modified Markdown files and 21 non-Markdown
documentation files: **98 relative-link occurrences, zero broken targets**.
All 39 current and 39 original packet hashes verify, with original inventory
preserved. The closure records exact commands and scope; final CI must bind to
this follow-up's published SHA. The earlier CI run applies only to `4b31851f`.

The historical R01–R16 validation at `4b31851f` passed **385 distinct tests** (358 affected
and blueprint cases plus 27 workflow/hygiene cases), with the existing C2
attested-interpreter skip. The fresh-cache focused command used an output path
containing spaces. ABI, packet hash, link and unchanged-scope checks passed.
The closure includes exact commands and the separately deferred wider blueprint
drift; the PR description binds complete CI evidence to the final published SHA.

The contract implementation is commit `e35f86542eb516ee7953e336845bafe9ee9b00ab`,
stacked on PR #231 pin `bdf7f3da7113aabde60ab8eceab6a960a841bb88` in
`codex/pricedesk-configurable-gas`, worktree
`$PRICEDESK_WORKTREE`. This follow-up addresses the
review feedback with local tests, staging compatibility fixes and documentation.
It does not approve a production configuration, deployment, activation or release.

The integration branch still resolves to the original `bdf7f3da` pin (read-only
remote check on 2026-09-20). Executed `2026091402`/`2026091403`, Base deployment
manifests and the historical constructor-position test remain unchanged. The
planning packet is now tracked here, including its 39 inventoried files and
checksum manifest. This is the canonical copy; the original checkout's older
untracked packet remains untouched. Its README distinguishes the original
approved prompt from subsequent implementation and review follow-ups.

The first-review commits are `fc275c5c` (staging compatibility), `ce54ae6e`
(test coverage and measurements), and `62ad1a48` (handoff). Re-review code and tests
are committed as `1ee9585b`; this documentation commit versions the canonical
packet and records that earlier disposition. These commits were subsequently
published in PR #232 on 2026-09-19 and remain GPG-signed.

## Configuration boundaries

Retain Base's **1.5M/1.5M immutable floors for the approved implementation and
rehearsal scope**. Production qualification and any owner decision to lower those
floors remain separate. No later decision to lower them is recorded; record the
final decision and its date when established. Lowering a deployed immutable floor
requires a replacement PriceDesk; source overrides cannot lower it.
This independent follow-up does not wait for that production decision. No deployment
values are qualified by the local mock experiments below.

`PRICE_DESK_SOURCE_GAS_OVERRIDES` in `config/BluePrint.py` now holds explicit
per-profile raw `(quote, snapshot, feed)` tuples. The rehearsal drafts apply
these before relinquishing setup governance and verify all effective values:

| Profile | Source | Raw override tuple | Status |
| --- | --- | --- | --- |
| Base | Curve | `(0, 1_500_000, 0)` | Retains the implementation/rehearsal floor; a lower floor needs a replacement desk. |
| Base | Undy | `(3_500_000, 1_500_000, 0)` | Provisional; quote allowance passes the existing two-lookup mock at the 1.5M floor. |
| Local / Robinhood | Curve | `(0, 500_000, 0)` | Provisional; preserves the former Teller allowance, with local cold measurements below. |

Zero resets its field to the immutable default. Local/Robinhood constructor
floors remain 250k/150k; feed defaults remain 75k and the maximum remains 6M.
The table is consumed by the rehearsal drafts and tested for all profiles;
adding it does not change any live contract or automatically reconfigure legacy
migration bodies or the generic shared test fixture. Every actual deployment
still needs qualified constructor values, exact source bindings, applied/read-back
overrides, and complete-transaction evidence before cutover.

## Re-review disposition

| Re-review item | Result |
| --- | --- |
| 1. Drafts occupy the live migration queue | Moved both bodies to `scripts/rehearsal/base_candidates/`, without timestamped migration names. `FullUpdate` and offline tests load paths directly. Direct live-queue exclusion and isolated queue/history tests protect this boundary without freezing the future migration frontier. Production reintroduction requires qualification, explicit authorization, and fresh timestamps/labels. |
| 2. Required deployment-controls failure | Kept the correct current-source indirect Teller→Curve relation and deliberately changed the direct/indirect pins from 167/11 to 166/12. Ran the whole required deployment-controls selection: 876 passed. |
| Four inherited reserve-engine failures | Reproduced and fixed the omitted `SwitchboardFoxtrotSetup` source inventory. Both Foxtrot sources now have semantic-method and reserve-mutator checks. Source review remains separate from the approved registered deployment inventory: this does not silently authorize a new live variant. Three additional regressions cover those boundaries. |
| 3. Interacting floor/override decisions | Added the per-profile table above, shared constructor/budget checks, exact address bindings, and apply/readback before governance relinquishment in both drafts. Tests cover replay and refused handoff on missing entries, invalid budgets, dropped writes, or constructor mismatch. The C01–C26 handoff preserves Base floors; optional lower floors remain deferred. |
| 4. Source versus live Robinhood blueprint | Module documentation explicitly scopes pointers/relations to the current checkout. The retained Robinhood Teller generation uses its direct Curve call; the new relay description is not evidence of live redeployment. |
| Duplicated oracle body | Kept the historical executed body independent: sharing mutable implementation would change its seven-argument behavior and break reproducibility. Both current drafts share the new budget helper. A structural parity regression pins the oracle draft's non-budget behavior to frozen `2026091402`, allowing only named constructor/readback/override/label changes. |
| Weakened readback assertion | Both drafts now verify all four immutable getters. Independent literal constructor-profile pins already exist in `test_price_desk_current_constructor_bindings` and were preserved and rerun; new literal override-table pins and a constructor-mismatch test add coverage. Comparing the deployment readback to its blueprint is appropriate when a separate test pins the approved profile. |
| Narrower migration fingerprint | Restored every historical `20260914*.py` body, plus both current drafts and their shared Python helper. Keys now use repository-relative paths. A regression proves changing the bridge changes its fingerprint. The broader project fingerprint also remains in place. |
| Divergent untracked packets | Versioned this worktree's canonical packet and all inventoried evidence; refreshed its metadata/checksums. The main-checkout copy remains untouched and is explicitly historical. |
| “GPG-signed” wording | Disagree with the reviewer's SSH diagnosis: all three prior follow-up commits contain `BEGIN PGP SIGNATURE` and `git verify-commit` reports good signatures with RSA key `625E97736545F6FDCAF1EF002BF641157E6D4240`. The GPG wording is correct. |
| Source-pointer boundaries | Trimmed constructor and quote references to their function bodies; extended the snapshot helper reference through its final Boolean decode. |
| Fragile slot-17 assertion | Validate required slots 6/8/5/7/17 and duplicates before any proposal/read/write. Missing slots now raise `BASE_ACTIVATION_REQUIRED_SLOT_MISSING:<id>`, and ordering always puts compatible PriceDesk before Teller. Tests remove every required slot. |

## Disposition of the review

| Review item | Disposition |
| --- | --- |
| 1. Base floor and nested faults | Implementation/rehearsal Base floors preserved; production qualification and any lower-floor decision remain separate. Added a cold synthetic comparison reproducing the 1.5M floor's repeated-failure cost and lost Undy route, alongside a 250k floor / 2M Undy experiment. These are experiments, not live-source qualification. |
| 2. Teller activation order | Added a real-Teller regression against a desk without the relay, including last-touch rollback. Documented slot 7 before slot 17, including atomic ordering and rollback. The full-update diagnostic explicitly checks that order. |
| 3. Foxtrot runtime failure | Fixed the stale 12,061-byte expectation to the measured 18,278 bytes. The growth came from predecessor `0833dddd`; the earlier implementation report missed the full edited runtime-table test. That omission was an error. The full table is now in the recorded default lane. |
| 4. Curve snapshot allowance | The re-review adds explicit provisional per-profile Curve overrides and cold local measurements; Base cannot lower its override below the retained 1.5M implementation/rehearsal immutable floor. |
| 5. Curve cold boundary | Reproduced and pinned warm 120k and cold 160k at 10k resolution, with a cold 250k/160k = 1.5625x margin check. The old 110k warm pin understates the current requirement. |
| 6. Constructor consumers | Appended both arguments in the two snapshot diagnostic call sites. Added current-ABI oracle and bridge/Teller bodies with fresh labels; the re-review moved them out of the live queue to `scripts/rehearsal/base_candidates/`. The full-update diagnostic loads the oracle draft by path and fingerprints both drafts. Frozen `2026091402`/`2026091403` and deployed manifests are unchanged. |
| 7. Three-field replacement | Read-modify-write procedure below; zero is explicitly a reset. |
| Feed check inside snapshots | Default/override underfunding tests prove no source call occurs; another test proves a later feed-check failure rolls back an earlier snapshot. |
| Permissionless token-scale sync | Default/override feed-budget tests cover underfunding, no writes/events, successful sync and first-set-only behavior. |
| Non-strict conversion helpers | All four helpers cover zero-with-feed, invalid reply, revert and source OOG, with an underfunded failure and fully funded fallback. |
| Committed report / counts | This report records the complete commands and measured results. The previous 245/38 counts combined separate focused runs and omitted the full runtime table. Those prior lanes are preserved below; the latest re-review adds the complete deployment-controls run. |
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

The new Curve tests restore cold transaction state before each due relay call,
using the same local GREEN/USDG fixture under each profile's snapshot allowance:

| Due-state case | Curve source execution gas | Margin at 500k | Margin at 1.5M |
| --- | ---: | ---: | ---: |
| New ring slot after configuration | 122,801 | 4.0716x | 12.2149x |
| Populated ten-slot ring, next due update | 83,001 | 6.0240x | 18.0721x |

These measurements support the provisional 500k local/Robinhood allowance. They
are not live Base or Robinhood measurements, do not close production D01, and do
not qualify every ring state or dependency. Existing Curve-route measurements
also reproduce: 28,374 nested quote, 169,797 four-coin quote, and 73,218 Teller
housekeeping execution gas.

## Historical re-review verification commands and results (before C01–C26)

These historical commands now use portable, quoted paths. Set `PRICEDESK_WORKTREE`
and `PRICEDESK_PYTHON` to the designated worktree and pinned interpreter.
`PRICEDESK_REVIEW_OUTPUT` is an optional writable output directory (spaces are
supported); logs, JUnit XML and caches are generated outputs, never required inputs.
Run from the designated worktree with the interpreter/cache environment below.
The deployment command mirrors the required job's test selection and existing
exclusions. Workflow files were not changed in that historical run; C02 now extends gas coverage.

```sh
cd "$PRICEDESK_WORKTREE"
export PRICEDESK_REVIEW_OUTPUT="${PRICEDESK_REVIEW_OUTPUT:-${TMPDIR:-/tmp}/pr232-review}"
mkdir -p "$PRICEDESK_REVIEW_OUTPUT"
export PYTHONPYCACHEPREFIX="$PRICEDESK_REVIEW_OUTPUT/python"
export RIPE_BOA_CACHE_DIR="$PRICEDESK_REVIEW_OUTPUT/boa"
pricedesk_python="$PRICEDESK_PYTHON"

"$pricedesk_python" -m pytest -q \
  -o cache_dir="$PRICEDESK_REVIEW_OUTPUT/pytest" \
  --junitxml="$PRICEDESK_REVIEW_OUTPUT/rereview-focused.xml" \
  tests/test_price_desk_staging.py tests/test_base_review_safety.py \
  tests/priceSources/curve/test_robinhood_launch_route.py \
  > "$PRICEDESK_REVIEW_OUTPUT/rereview-focused.log" 2>&1

"$pricedesk_python" -m pytest -q -s -m gas \
  -o cache_dir="$PRICEDESK_REVIEW_OUTPUT/pytest" \
  --junitxml="$PRICEDESK_REVIEW_OUTPUT/rereview-curve-gas.xml" \
  tests/priceSources/curve/test_robinhood_launch_route.py \
  > "$PRICEDESK_REVIEW_OUTPUT/rereview-curve-gas.log" 2>&1

env -u WEB3_ALCHEMY_API_KEY -u ALCHEMY_API_KEY -u ETH_RPC_URL \
  -u BASE_RPC_URL -u RPC_URL -u WEB3_PROVIDER_URI -u PRIVATE_KEY \
  -u MNEMONIC -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY \
  -u ETHERSCAN_API_KEY -u BASESCAN_API_KEY PYTHONHASHSEED=0 \
  "$pricedesk_python" -m pytest -q -o addopts='' \
  -o cache_dir="$PRICEDESK_REVIEW_OUTPUT/pytest" \
  --basetemp="$PRICEDESK_REVIEW_OUTPUT/rereview-deployment-final-tmp" \
  --junitxml="$PRICEDESK_REVIEW_OUTPUT/rereview-deployment-final.xml" \
  --durations=25 \
  -m 'not release and not artifact and not fuzz and not gas and not fork_qualification' \
  --deselect 'tests/deployment/test_operator_chain_guards.py::test_defaults_snapshot_rejects_every_non_robinhood_mainnet_chain' \
  --deselect 'tests/deployment/test_operator_chain_guards.py::test_defaults_snapshot_accepts_robinhood_mainnet_chain' \
  --deselect 'tests/deployment/test_operator_chain_guards.py::test_defaults_snapshot_sanitizes_untrusted_token_metadata' \
  --deselect 'tests/deployment/test_operator_chain_guards.py::test_defaults_snapshot_preserves_safe_existing_labels' \
  tests/deployment \
  > "$PRICEDESK_REVIEW_OUTPUT/rereview-deployment-final.log" 2>&1

"$pricedesk_python" scripts/export_abis.py --check \
  > "$PRICEDESK_REVIEW_OUTPUT/rereview-abi.log" 2>&1
git diff --check
git verify-commit fc275c5c ce54ae6e 62ad1a48
```

Results: **53 focused + 9 Curve gas + 876 deployment-controls = 938 distinct
passing tests**, with zero failures, errors or skips among selected cases.
Selection deselected 9, 9 and 13 nodes respectively; the deployment exclusions
are the existing job/marker/archive gates, not new exceptions. One inherited
`websockets.legacy` deprecation warning remains. ABI check passes for 60 exported
ABIs (58 excluded Vyper contracts). No production contract changed in this
re-review, so the complete runtime measurements above remain from the prior run.

The first deployment-controls attempt passed 874 cases and failed two existing
symlink tests with sandbox `PermissionError`. Repeating the same selection with
worktree write permission passed all 876; the temporary links were removed.
The four previously inherited source-inventory failures and this branch's
relation-count failure are fixed, not deselected. A development-only local
fixture also needed correction because deployment `BluePrint("local")` lacks
unrelated token/Curve dictionaries; the final profile test uses the lightweight
local dictionaries and real PriceDesk code.

## Previous implementation verification commands

Run from the designated worktree. The interpreter is shared with the original
checkout; `pytest.ini` resolves repository/test imports from this worktree.
All local artifacts and caches go outside the checkout:

```sh
cd "$PRICEDESK_WORKTREE"
export PRICEDESK_REVIEW_OUTPUT="${PRICEDESK_REVIEW_OUTPUT:-${TMPDIR:-/tmp}/pr232-review}"
mkdir -p "$PRICEDESK_REVIEW_OUTPUT"
export PYTHONPYCACHEPREFIX="$PRICEDESK_REVIEW_OUTPUT/python"
export RIPE_BOA_CACHE_DIR="$PRICEDESK_REVIEW_OUTPUT/boa"
pricedesk_python="$PRICEDESK_PYTHON"

"$pricedesk_python" -m pytest -q \
  -o cache_dir="$PRICEDESK_REVIEW_OUTPUT/pytest" \
  --junitxml="$PRICEDESK_REVIEW_OUTPUT/review-default.xml" \
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
  > "$PRICEDESK_REVIEW_OUTPUT/review-default.log" 2>&1

"$pricedesk_python" -m pytest -q -s -m gas \
  -o cache_dir="$PRICEDESK_REVIEW_OUTPUT/pytest" \
  --junitxml="$PRICEDESK_REVIEW_OUTPUT/review-gas-final.xml" \
  tests/registries/test_price_desk_gas.py \
  tests/registries/test_price_desk_aggregate_protocol_gas.py \
  tests/registries/test_price_desk_source_budgets.py \
  tests/priceSources/curve/test_robinhood_launch_route.py \
  > "$PRICEDESK_REVIEW_OUTPUT/review-gas-final.log" 2>&1

"$pricedesk_python" -m pytest -q -o addopts='' \
  -o cache_dir="$PRICEDESK_REVIEW_OUTPUT/pytest" \
  --junitxml="$PRICEDESK_REVIEW_OUTPUT/review-abi-staging.xml" \
  tests/deployment/test_stale_time_oracle_abi.py \
  tests/deployment/test_base_staging_runner_order.py \
  tests/deployment/test_price_desk_token_scale_bootstrap.py \
  > "$PRICEDESK_REVIEW_OUTPUT/review-abi-staging.log" 2>&1
```

Default and gas lanes retain repository addopts. The final command deliberately
selects only the three directly relevant, normally excluded files; it does not
run the deployment suite. The prior review results were **292 default + 44 gas + 21 ABI/staging = 357 distinct passing tests**,
with zero failures, errors or skips in these selected lanes. JUnit case identities
were checked for duplicates across the three runs. The Robinhood blueprint's
built-in validation also passes when importing `config.robinhood_blueprint`.
These two historical local validation runs preceded publication of PR #232.
They did not run the full repository suite, an RPC fork, live qualification,
deployment, Safe operation, push or publication. Current validation is recorded
in the C01–C26 / R01–R16 closure linked above.

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

Budget writes use `_canGovern` immediately, including while paused; they do not
use the registry action timelock. This chosen authority model is unchanged.

The view exposes effective values. Preserving a default as an explicit nonzero
value preserves behavior but differs from raw zero in events. If raw-zero
representation matters, reconstruct the raw fields from authenticated events;
do not infer them from the effective getter. Overrides follow addresses, remain
after disable/re-enable, and never migrate to a replacement address. Configure
and qualify replacements before admitting/activating them.

Both current candidate types must be authenticated. Confirm **HQ slot 7 first**, then
**slot 17**, or both atomically in that order. Verify the relay selector and all
source overrides before opening Teller. Roll back the relay Teller before
restoring an incompatible desk. See [the staging guide](staged-upgrade-deployment.md).

## Remaining release work and limitations

Adequately funded direct source calls retain failure isolation. Ordinary quotes
require full-budget funding after failed, malformed or zero-with-feed results;
canonical usable/no-feed replies bypass that proof. Admission, feed checks and
both snapshot paths check funding eagerly. A detected funding failure reverts
that PriceDesk invocation, but an enclosing isolation boundary may catch it, so
nested fallback availability depends on qualified enclosing budgets.

For an enclosing cap B, an inner failing call with the same budget needs
`B + ceil(B / 63) + 5,000`: 1,528,810 gas at Base's 1.5M floor, before other
source work. The real Curve/Chainlink regression has direct USDG fallback success
with stale Chainlink, while nested GREEN returns zero (or the strict-caller error)
at the Curve floor even with 10M transaction gas. An illustrative 3.5M Curve quote
override restores that test route; it is not a production recommendation.

The following is a **selected current-source inventory**, not the complete production
route inventory. References describe the checkout and candidate configuration,
not authenticated deployed implementations. The [complete final inventory remains
deferred](pricedesk-gas-plan/follow-up-qualification.md#complete-production-route-inventory).

| Nested route | Repository evidence and qualification scope |
| --- | --- |
| Curve → underlying coins / USDG | [CurvePrices](../../../contracts/priceSources/CurvePrices.vy), `_getStableLpPrice`, `_getCryptoLpPrice`, `_getSingleTokenPrice`, calls PriceDesk for underlying assets. The real Curve/Chainlink regression reproduces stale-Chainlink fallback loss for nested GREEN/USDG. Qualify every enabled pool/coin route. |
| Undy → underlying asset | [UndyVaultPrices](../../../contracts/priceSources/UndyVaultPrices.vy), `_getPrice`, looks up `_config.underlyingAsset`; configuration validation also prices the underlying. Authenticate every retained vault and dependency, including any nested/repeated underlying paths. The one/two-lookup fault experiment is a synthetic comparison. |
| BlueChip → underlying asset | [BlueChipYieldPrices](../../../contracts/priceSources/BlueChipYieldPrices.vy), `_getPrice`, prices the underlying before protocol-specific share conversion. Both [Base oracle](../../../scripts/rehearsal/base_candidates/oracles_psm_reserves.py) and [bridge](../../../scripts/rehearsal/base_candidates/price_desk_gas_bridge.py) drafts keep slot 3 disabled. The [Robinhood profile](../../../config/BluePrint.py), `CM-018`, defers BlueChip; local tests deliberately enable it. Qualify this route only for a profile/configuration that actually enables it. |
| wsuperOETHb → SUPER_OETH | [wsuperOETHbPrices](../../../contracts/priceSources/wsuperOETHbPrices.vy), `_getPrice`, uses a strict nested SUPER_OETH lookup. Qualify its underlying implementation, fallback and conversion behavior. |
| RedStone → ETH/USD | [RedStone](../../../contracts/priceSources/RedStone.vy), `_getPrice`, performs the nested lookup only when `needsEthToUsd` is enabled and the primary feed produced a usable price. Bind the final per-asset flag. |
| Retained legacy Aero | Both Base drafts retain the legacy slot-6 address. The current [AeroRipePrices](../../../contracts/priceSources/AeroRipePrices.vy) is a monitor: its PriceSource surface returns no feed, while its separate monitoring valuation looks up WETH. This does **not** establish the legacy oracle's lookup/catch behavior; authenticate its actual deployed implementation and dependencies before inventorying its production routes. |

This does not claim that every live route fails. An adequately funded enclosing
route must cover inner failed, malformed and zero-with-feed branches as well as
its normal source work and repeated invocations.

Teller's 19 housekeeping call sites span all flow families plus conditional
deposit housekeeping. At a 1.5M snapshot budget the relay needs at least 1,528,810
gas at its funding sample even for a genuine no-op; absent/disabled sources return
before that proof. RPC-estimator D01 must compare identical prestates at estimated,
submitted buffered and generous limits for both generic and reference snapshots,
across frontend, wallet, keeper, liquidation and integration callers, including Appraiser.
Use the deferred [D01 evidence matrix](pricedesk-gas-plan/follow-up-qualification.md#d01-caller-and-estimator-evidence-matrix).

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

Recheck the actual chain/client transaction cap during qualification. Changing the
immutable maximum later requires a new deployment. Bind each acceptance decision
to its final implementation, source addresses, configuration and qualification evidence.


The 2026-09-20 status refresh found #231 open with changes requested and #232 a
draft targeting the parent branch. The integration sequence remains: **parent
merges → #232 targets `master` → resulting integration is validated again**.
A manual workflow success does not establish `rh-pr-gate` success: an eligible PR
or merge-group run must actually execute and pass that gate. The workflow does
not explicitly subscribe to edited PR events, so retargeting alone must not be
assumed to trigger it. Separate deployment/activation authority remains required.
Historical harness hashes identify recorded bytes; they cannot recreate missing
original harness files. The current guarded harness is not an exact substitute.


The R01–R16 follow-up repaired the named blueprint evidence. The remaining
maintenance safeguard checks substantive source content against an explicit
occurrence-aware baseline: 30 distinct blank/comment-only pointers, 36 occurrences.
It prevents new/additional exceptions and permits repairs, without reconciling the
entire inherited graph. Known unsupported parent relationships are R-100
Bravo → Switchboard and R-101 Bravo → Alpha (both cite MissionControl asset-deposit
logic at `SwitchboardBravo.vy:490–492`), plus R-108 Charlie → AuctionHouse (no
corresponding current call). All three remain included in the direct-edge count.
The owner's 2026-09-20 direction was to preserve the scoped graph and report that
wider drift; see [the closure record](pricedesk-gas-review-232.md#wider-blueprint-drift-retained-by-owner-direction).
The unchanged 166 direct / 12 indirect counts are a scoped invariant, not evidence
that every inherited relationship matches current source.
