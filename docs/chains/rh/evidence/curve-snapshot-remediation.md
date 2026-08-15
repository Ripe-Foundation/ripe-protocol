# Curve snapshot remediation evidence and operating boundary

**Candidate:** PR #157, `codex/rh-curve-sc-16-sc-23` into
`rh-audit-remediation`

**Scope:** SC-16 duration-weighted GREEN reference-pool state, snapshot-ring
capacity safety, danger and recovery continuity, SC-23 freshness behavior,
governed runtime identity, and the downstream SC-06 PriceDesk composition
surface in `CurvePrices`.

**Lifecycle boundary:** this record binds candidate behavior and reproducible
review evidence. RH-D043 remains a recommendation until the owner ratifies the
exact final head. Nothing here authorizes deployment, registration,
configuration, activation, release, or a merge into `rh`.

## Candidate Git binding

The source and deployed-runtime identities below bind the contract respin. The
PR description must additionally bind the final rebased head, tree, exact
`rh-audit-remediation` base, and synthetic merge commit after the last target
refresh. Any later source, dependency, compiler, constructor, or target-branch
change invalidates that integration binding and requires the affected evidence
to be regenerated.

| Identity | Bound value |
| --- | --- |
| Unfixed source commit | `4a72a1f` |
| Unfixed Curve source SHA-256 | `f6e8234be8e433ed344f6f61d9cf04d20a4327c773759bb6aced44b9f65ebd0c` |
| Candidate Curve source SHA-256 | `8ad730930c80ad51616d080100ce8c1fb941f6b73713af39f347601b64c20050` |
| Candidate Curve source Git blob | `76233779bb34059de16a5a6740233fc4dc0f59ca` |
| Vyper / optimizer | 0.4.3 / `gas` |
| Creation bytes / SHA-256 | 24,715 / `615d3214330cce4a703d8bac42d67b37a019d74f0e72873180aff6c5588b9d87` |
| Runtime-template bytes / SHA-256 | 22,683 / `01317cc59d46094f472d76c3a6160957885f2815dc310cc6f570986695db63dd` |
| Immutable bytes / SHA-256 | 448 / `1bb22cb4def89de539144e8b54d6c546e472fb4f685e58064a980ce4b930e08b` |
| Constructor-bound runtime bytes / SHA-256 | 23,131 / `abd717d4382564b0bd8f10be288dc7dd51da3205d0bb291e23c9fde179331998` |
| EIP-170 headroom | 1,445 bytes |
| Committed ABI / canonical ABI SHA-256 | `3f06fa5c83f4404bfb97da689ea3b4611e94c60a504174001210033c7c429772` / `8a8f259d19103e7feb261ea5edf3bb14968d08c4200c3421a6621ba53ba1c62f` |
| Event count / canonical SHA-256 | 23 / `68cf7e9dd23ef0d45fd35109bd1573cdcbb86086a6400ec6d2822615e737f411` |
| Selector count / canonical SHA-256 | 86 / `6e82d509c91a02bef0aeaa755f99710a9b300dd56bc2a40124bd049a6cc954e0` |

The constructor-bound runtime uses the Robinhood RipeHQ, zero temporary
governance as specified by migration `0003`, the selected Curve AddressProvider
and registry IDs 7, 11, 12, and 13, GREEN and sGREEN, and constructor values
600 and 50,400. Capture substitutes a deterministic interface-compatible
AddressProvider at the selected address so the source can be compiled and
deployed reproducibly without relying on live external code. The complete
binding and prospective governance initialization state are governed by
`config/contract-artifact-expectations.json`; the strict capture produces 19
deployed runtimes plus its sealed manifest.

## RH-D043 candidate decision

The candidate uses chronological block-duration weighting and accepts the
resulting rolling danger-entry lag. A new ratio receives weight only after a
later observation establishes its duration. That lag resists manipulation of
weight by balance inflation, but it means an abrupt dangerous observation is
not retroactively credited for time before it was observed.

The recommended live `maxNumSnapshots` is 10. It matches the existing Base
configuration and the S=10 PriceDesk composition measurement. Because the
contract accepts at most one successful write per block and depends on
qualifying activity, ten entries do not imply a fixed wall-clock horizon.
Operations must bind and monitor an honest snapshot cadence rather than infer
one from capacity alone. Increasing capacity above 10 reopens runtime and
composition-gas qualification.

Classification is inclusive: `weightedRatio >= dangerTrigger` is dangerous.
The trigger must remain above the pool's expected resting ratio and must not be
configured at equilibrium. A change that could put the resting pool on or near
the boundary requires renewed equilibrium analysis and operating approval.

### Configuration-transition classes

- **Category A, no semantic or capacity change:** preserve ring, cursor,
  counter, and all continuity anchors.
- **Category B, capacity change:** clear the complete old ring, seed once under
  the new capacity, preserve the accumulated danger counter, clear continuity,
  and anchor danger or recovery at confirmation when the seed is respectively
  dangerous or safe. A failed seed reverts the confirmation atomically.
- **Category C, `dangerTrigger` or `staleBlocks` change:** preserve the ring and
  accumulated counter; clear danger and both recovery anchors; evaluate the
  retained ring under the confirmed policy; anchor danger at confirmation for
  a nonzero dangerous result, anchor recovery at confirmation for a nonzero
  safe result with historical danger, and leave all anchors clear when the
  result is unavailable.
- **Category D, non-classification tuning only:** preserve ring, cursor,
  counter, and continuity anchors.

Category C deliberately refuses to credit elapsed time across a policy
boundary. Freshness expansion can make retained observations available for
the current classification, but cannot bridge an expired gap. A transition to
zero freshness cannot use an expired pre-confirmation recovery anchor to clear
the counter. A still-fresh shrink may shorten the subsequently observed safe
window, but only from the new confirmation anchor. None of these transitions
erases or reduces `numBlocksInDanger`.

The ring remains available for current classification after Category C; this
is not a claim that an old policy was continuously satisfied. If retained
history is unavailable, later writes must establish new observable continuity.
The focused matrix covers old-dangerous/new-dangerous,
old-dangerous/new-safe, old-safe/new-dangerous, unavailable history, stale
3-to-100 expansion, stale 3-to-0 transition, and a simultaneous trigger plus
freshness change.

### Retained dispositions

A fully empty pool may be proposed before liquidity arrives. Confirmation
revalidates, requires a nonzero seed, and reverts atomically if liquidity is
still absent; the active configuration and pending action remain available for
retry or explicit cancellation. This pre-liquidity governance workflow is an
intentional ergonomic choice, not an activation recommendation.

The duplicate scalar arguments to `_isValidGreenRefPoolConfig` remain because
current callers bind them to `_refConfig` and changing the internal signature
would create unrelated bytecode churn without correcting behavior. The mock
pool and registry setters remain intentionally permissionless test controls;
comments now prevent them from being mistaken for production authorization
evidence. Negative authorization coverage continues to use the real contract
and registry graph.

## Production caller and gas-bearing surface

Generic `CurvePrices.addPriceSnapshot` returns `False`, so PriceDesk's generic
snapshot route does not write the GREEN ring. `addGreenRefPoolSnapshot`
authorizes the valid-RIPE-address class rather than Teller by name. Teller is
the only current in-repository production caller, through
`Teller._performHousekeeping`; ordinary user actions can therefore cause the
write indirectly. A real-Teller regression exercises that route through
PriceDesk registry ID 2.

Same-block suppression permits only one successful write per block. The first
qualifying Teller action in a new block can bear the full O(`maxNumSnapshots`)
traversal and write cost. Later same-block attempts do not add another
observation. Operator capacity selection and transaction-gas guidance must
account for that first-caller cost.

### Enforced PriceDesk composition budgets

The explicit `gas` lane runs in CI despite the repository's default marker
exclusion. It enforces:

| Route | Measured baseline | CI ceiling |
| --- | ---: | ---: |
| Robinhood GREEN -> Curve -> PriceDesk -> Chainlink USDG | 25,558 | 50,000 |
| Worst honest four-coin path after eight misses | 126,181 | 200,000 |

The first ceiling leaves approximately 96% margin and the second approximately
58%. These are top-level deterministic Boa measurements, not raw-call stipends.
The CI workflow-health regression fails if either the BlueChip or Curve gas
file is removed from the snapshot-gas job.

The downstream SC-06 requalification replaced PriceDesk with exact PR #152
commit `3752d5d0c220cbb5491c232b859adf50d64c0841` and source SHA-256
`7fd7e8eedd883a10ee7a225cb666896324d7b9b47de3a136175f62e00267561c`
while retaining this exact Curve source. All nine route nodes passed. The
bounded PriceDesk added 142 gas to the normal route (25,700 total) and 1,741
gas to the worst honest route (127,922 total); both remain below the same
50,000 and 200,000 ceilings. The retained JUnit binds those two exact sources.

### Maximum-ring cold-access measurements

`scripts/measure_curve_snapshot_gas.py` deploys an isolated system per path and
uses Boa's py-evm access-counter reset immediately before the measured call.
That private hook is intentionally kept outside pytest because it is
incompatible with pytest snapshot-isolation checkpoints. On the governed
Curve source above:

| Path | Gas |
| --- | ---: |
| Partial 10-entry all-fresh view | 915,409 |
| Full 100-entry all-fresh view | 1,011,839 |
| Full 100-entry mostly-stale view | 940,492 |
| Wrapped 100-entry all-fresh view | 1,013,019 |
| Add snapshot to a full 100-entry ring | 1,058,081 |
| Confirm capacity 100-to-99, clear, and reseed | 1,302,608 |

These are cold-access operational measurements, not ordinary CI assertions.
They justify the recommended live S=10 bound and require a documented margin
in transaction construction. The exact 100-entry values must not be treated as
stable warm-process budgets.

## Test provenance and reproducible recipes

The unfixed baseline is commit `4a72a1f` with Curve source SHA-256
`f6e8234be8e433ed344f6f61d9cf04d20a4327c773759bb6aced44b9f65ebd0c`.
Four fail-first regressions demonstrated:

1. one safe snapshot erased a danger counter from 5 to 0;
2. a fully stale ring returned the last 50% ratio (`5000`) instead of an
   unavailable zero status;
3. capacity shrink then regrowth resurrected discarded 70% and 80% slots,
   producing `8046`; and
4. an extreme `staleBlocks` value poisoned the view with arithmetic reversion.

Each defect was reproduced by checking out that exact baseline, restoring the
candidate test file and two isolated mocks, applying the retained
`fail-first-overlay.patch`, and running these exact nodes:

```sh
python -m pytest -q -p no:cacheprovider \
  tests/priceSources/curve/test_green_ref_pool.py::test_sc16_single_safe_snapshot_preserves_danger_history \
  tests/priceSources/curve/test_green_ref_pool.py::test_sc23_fully_stale_status_returns_zero \
  tests/priceSources/curve/test_green_ref_pool.py::test_capacity_regrowth_cannot_resurrect_discarded_slots \
  tests/priceSources/curve/test_green_ref_pool.py::test_extreme_stale_blocks_rejected_without_poisoning_view
```

The four failures expose, respectively, danger 5 to 0, stale result 5000
instead of 0, resurrected-history result 8046 instead of the fresh 8500 seed,
and an arithmetic revert in the view at `snapshot.update + staleBlocks`. The
overlay changes only the observation sequence/assertion point needed to make
those values visible; its resulting test-file SHA-256 and exact preparation
recipe are recorded in `evidence-manifest.yaml`. The fixed Base run executes
all four permanent regressions as part of its 59 passing nodes.

The final focused behavior recipe is:

```sh
python -m pytest -q -p no:cacheprovider \
  tests/priceSources/curve/test_green_ref_pool.py
```

The explicit composition-gas recipe is:

```sh
python -m pytest -o addopts='' -m gas -s \
  tests/priceSources/curve/test_robinhood_launch_route.py
```

The governed artifact recipe is:

```sh
python -m pytest -q -p no:cacheprovider \
  tests/inventory/test_contract_artifacts.py
```

`evidence-manifest.yaml` records the exact source bindings, commands, node
counts, passed/failed/skipped/deselected counts, tool versions, artifact sizes,
and SHA-256 hashes. CI on the retargeted PR supersedes a local claim only where
it publishes the same recipe and retained output.

### Pre-existing test rewrite disclosure

Seven existing tests were semantically corrected because they encoded latest
snapshot, balance-weighted, non-expiring, or eager-reset behavior that
contradicted the remediated duration/freshness state machine:

- `test_danger_block_counting` now asserts duration-based danger accrual;
- `test_weighted_ratio_calculation` derives chronological interval weights;
- `test_stale_snapshots_excluded` expects unavailable status when every
  observation is expired;
- `test_empty_pool_scenarios` distinguishes proposal validity from
  confirmation seeding;
- `test_weighted_ratio_edge_cases` uses the corrected interval boundaries;
- `test_stale_blocks_exact_threshold` pins inclusive freshness; and
- `test_usdc_dominant_pool_scenarios` no longer treats stale last-ratio fallback
  as a valid status.

`test_config_update_overwrites_data` was superseded by the stronger
`test_capacity_config_update_resets_ring`, which proves full clearing,
single-seed behavior, and counter continuity. `test_curve_pool_data_accuracy`
is unchanged; it appeared only as diff context.

## Pinned Base-fork qualification

The fork is pinned to Base block 34,471,929. The qualification environment is
Python 3.12.0, pytest 8.4.2, Titanoboa 0.2.7, and Vyper 0.4.3. Credentials are
provided through the established sanitized local shell environment; no secret
values are logged or committed. Retained JUnit must bind the exact final head
and merge candidate, command, selected nodes, and all pass/fail/skip/deselect
counts.

The exact credentialed Base-through-Anvil run at block 34,471,929 passed all 59
green-ring nodes in 195.93 seconds. The existing `test_curve_prices.py`
asset/LP lane has inherited harness debt, not a Curve-pool math divergence:
target `e7b6eeab768a009469a38a7ce8a35bb7e8d8f4bc` and candidate test commit
`937b491a01f005bd1a65edb9ad81ddf1668596e2` each produced the same 24 failed /
8 passed set, and the parsed failed-node sets are identical.

At the pinned block, timestamp 1,755,733,205, the USDC Chainlink round was
updated at 1,755,702,597. Its initial age was 30,608 seconds. The Chainlink
setup timelock advanced 3,601 blocks to timestamp 1,755,776,417 and age 73,820
seconds. The later Curve confirmation timelock advanced another 3,601 blocks
to timestamp 1,755,819,629 and age 117,032 seconds, beyond MissionControl's
86,400-second global freshness value. The fixture's direct Chainlink source
uses per-feed `staleTime=0` and remains nonzero, while PriceDesk correctly
supplies the global bound. That causes 23 confirmation failures and one
cascading missing-event assertion on both revisions.

The repository retains all five JUnit documents, not only their digests, plus
the complete failure set, exact commands, versions, sanitized environment,
timestamps, counts, hashes, fail-first outputs, and PR #152 composition
measurement in
[`curve-snapshot-remediation/evidence-manifest.yaml`](curve-snapshot-remediation/evidence-manifest.yaml).
The evidence grants no production exception for the inherited harness debt.

## Monitoring, pause, disable, and reopen conditions

Before activation, operators must bind:

1. a finite honest snapshot cadence and an alert before observations expire;
2. rolling ratio, spot ratio, availability, danger counter, recovery state,
   last successful block, and fallback/failure alerts;
3. first-caller and worst-path gas monitoring against transaction and source
   budgets;
4. an immediate source pause procedure and a rehearsed timelocked PriceDesk ID
   2 disable procedure; and
5. a repair, fresh-observation, verification, and ordered re-enable runbook.

Qualification reopens on any Curve source, compiler, dependency, constructor,
registry, or immutable change; capacity above 10; missed refresh or sustained
unavailable/fallback state; gas approaching the selected margin; a threshold
or pool-equilibrium change; a new caller, consumer, or registry topology; any
change to freshness-revival or post-confirmation anchoring semantics; or drift
in the pinned Base failure set. Owner ratification of RH-D043 must name the
exact final head and does not waive any of these controls.
