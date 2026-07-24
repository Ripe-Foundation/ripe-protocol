# Block-clock validation plan

**Status:** Implementation-ready test plan; runtime and CI choices beyond the
currently pinned stack remain owner-gated

**Prepared:** 23 July 2026

**Review revision:** 23 July 2026 — added the lower-risk-to-higher-risk Ledger
case, runtime primitive gate, and `contracts/testing/**` classification

**Minimum-change revision:** 24 July 2026 — BN-012 tests validate the selected
zero-cooldown/no-change candidate first; BN-025 validates the retained narrow S3
change; and BN-002 validates the owner-selected portable same-execution-block
direction. S5 implementation remains blocked on its Stage A architecture and
security gate, and the deployed Base Ledger remains outside migration scope.

**Authority:** [`shared-block-clock-specification.md`](shared-block-clock-specification.md),
the integrated Track 3 inventory, and the integrated component matrix

This plan defines future tests. It does not add or modify a test, runtime,
dependency, contract, default, script, migration, generated report, or CI file.

## Validation contract

The same canonical source and compiler inputs must produce one creation artifact
per contract. Base and Robinhood scenarios deploy that same artifact with
different approved constructor/default parameters. Constructor immutables may
make deployed runtime bytes differ; source hash, compiler settings, ABI, and
unbound creation bytecode must match. No test selects a different production
source, mock implementation of a production contract, or `chain.id` behavior.

The pinned environment is:

- `titanoboa==0.2.7`;
- `pytest==8.4.2`; and
- the repository's existing Vyper/compiler configuration.

Direct assignment to `boa.env.evm.patch.block_number` and
`boa.env.evm.patch.timestamp` was verified during Track 6, including independent
arbitrary jumps. The active pyenv `ripe-lite` environment resolved
`titanoboa==0.2.7`; assignment of `+7` NUMBER and `+11` seconds inside
`boa.env.anchor()` produced the exact values and restored both afterward. The
repository has no venv, so `test_clock_profiles.py` must make installed-version,
direct-assignment, and anchor-restoration checks its first S1 gate. The required
profiles therefore need no Anvil instance, plugin, or new dependency if that gate
passes.

Track 6 launched from `rh` at `5018da6d19516509e0d8674b3728e73bca92e2ad`.
The `rh` integration branch later advanced to
`cfb6762c740a196e3d187f779a3e2b1060c2128a`, which adds
`contracts/testing/StockTokenTransferProbe.vy` but no clock or cadence dependency.
S2 must classify `contracts/testing/**` as non-production, count it separately,
prohibit production imports from it, and reproduce the unchanged
100-occurrence/95-line/17-file production baseline on both commits.

## Fixture and helper API

S1 adds `tests/utils/clock_profiles.py`,
`tests/clock/test_clock_profiles.py`, and a narrowly registered fixture in
`tests/conftest.py`. The public test API is:

```python
ClockPoint(number: int, timestamp: int)
ClockProfile(name: str, points: tuple[ClockPoint, ...], evidence: str)

clock_controller.set(number=..., timestamp=...)
clock_controller.apply(profile, step)
clock_controller.hold_number(seconds=...)
clock_controller.hold_timestamp(numbers=...)
clock_controller.at_open(init_number, delay, offset=0)
clock_controller.at_expiry(confirm_number, expiration, offset=0)
clock_controller.at_interval(start_number, interval, offset=0)
clock_controller.at_window(start_number, end_number, boundary="start", offset=0)
clock_controller.observed_call(stable_id, label, callable, *args, **kwargs)

deployed_system(clock_profile, parameter_profile)
parameter_profile in {"base_current", "base_canonical", "robinhood_candidate"}
```

`set` rejects decreasing NUMBER or timestamp inside one scenario unless the caller
is restoring an anchor. It records every explicit mutation. Calls do not advance
either clock implicitly.

`observed_call` records:

- stable ID, component IDs, profile, step, and optional Hypothesis seed;
- intended and actual pre-call NUMBER/timestamp;
- post-call NUMBER/timestamp;
- parameter-profile name and the relevant values/bounds;
- success/revert and normalized reason;
- target address, function signature, transaction/call label; and
- the asserted state/event field that proves the target observed the context.

Where a contract persists or emits NUMBER/timestamp, the helper compares that
field to the pre-call context. Otherwise the scenario must assert a boundary
result whose truth changes at the controlled value. Environment state alone is
not accepted as proof for a production behavior.

The exact profiles are imported from the specification:

```text
B-ORD       (N,T),(N+1,T+2),(N+2,T+4),(N+3,T+6),(N+4,T+8)
R-REP128    (N,T+floor(i/4)) for i=0..127
R-PLUS1     (N,T),(N,T+1),(N+1,T+12),(N+1,T+13)
R-J2-J4     (N,T),(N,T+1),(N+2,T+24),(N+2,T+25),(N+4,T+48)
BOUNDARY-OPEN   (B-1,T),(B+1,T+24)
BOUNDARY-WINDOW (S-1,T),(E+1,T+24)
R-STRESS60  (N,T),(N,T+1),(N+60,T+720)
MIXED       (N,T),(N,T+3600),(N+2,T+3600),(N+2,T+7200)
```

`N=1_000_000` and `T=2_000_000_000` unless a test needs headroom for an existing
absolute value. `B`, `S`, and `E` are derived from scenario state, never hardcoded
to a live height.

Each parametrized case runs inside a fresh `boa.env.anchor()`. Deployment
fixtures that cache contracts must snapshot immediately after deployment and
restore before each profile/parameter pair. The controller asserts the initial
clock, sequence index zero, clean trace, and expected storage checkpoint after
restore. A failure to restore is a harness failure, not a skipped protocol case.

## Identical-artifact and parameter checks

The session fixture compiles canonical sources once, fingerprints source content,
compiler version/settings, ABI, and creation bytecode, then deploys the same
fingerprint under:

- `base_current`: currently tested Base values and current behavior;
- `base_canonical`: the selected release behavior, which may be unchanged Base
  source or an owner-approved indispensable shared change; and
- `robinhood_candidate`: approved Robinhood values from `DefaultsRobinhood`.

Before any behavioral assertion, the test fails if artifact fingerprints differ
between profiles. Parameter extraction then compares every constructor immutable,
getter, MissionControl field, and generated defaults entry to a checked parameter
manifest. This distinguishes same artifact from different deployment data.

For BN-002, BN-012, and BN-025, comparison tests keep current Base behavior
visible beside the selected Robinhood disposition. BN-012 proves the
configuration/no-change path unless S4 closes its necessity gate. BN-025 proves
the retained S3 artifact and keeps any Base convergence separate. BN-002 proves
the revised forward canonical artifact on a fresh Robinhood deployment while
treating the deployed Base Ledger as permanent retained regression evidence;
it must not invent a Base convergence action.

## Boundary helpers

Every duration/window suite uses exact named points:

| Boundary | Controlled NUMBER | Expected generic result |
| --- | ---: | --- |
| before open | `start - 1` | unavailable |
| exact open | `start` | available unless source deliberately uses strict `>` |
| after open | `start + 1` | available |
| last valid | `end - 1` | available |
| exact end | `end` | unavailable/fresh/expired, by domain |
| after end | `end + 1` | unavailable/fresh/expired |
| skip open | `start - 1 -> start + 1` | no phantom exact-boundary side effect |
| skip whole window | `start - 1 -> end + 1` | fail closed or documented catch-up |

Lootbox BN-025 is the deliberate exception: current strict `>` makes
`lastSend + interval` unavailable and `+1` available. Capacity intervals
BN-027–029 become fresh at exact equality. `TimeLock` actions are valid at
confirmation and invalid at exact expiration. Auctions are valid at start and
invalid at end.

## Test layers

1. **Harness unit:** exact clock points, independent movement, trace schema,
   anchor isolation, and artifact fingerprints.
2. **Contract unit:** each stable ID's arithmetic, validator, storage, event, and
   exact boundaries under every applicable profile.
3. **Governance flow:** initiate, wait/jump, confirm/expire, setter execution,
   mid-period parameter change, immutable bounds, and permissions.
4. **Integration:** Teller/Ledger/CreditEngine/Lootbox, PSM/Echo, complete
   timelock inheritors, RipeHq/AddressRegistry CCIP Department registration, and
   PriceDesk routing.
5. **Lifecycle:** deposit/borrow/repay/withdraw/liquidate/auction/bond/reward
   sequences with points, emissions, interest, capacity, and locks moving in
   their intended domains.
6. **Deployment-negative:** unsupported Robinhood address, deployment, registry,
   capability, route, flags, and external permission are absent.
7. **Inventory:** direct and indirect cadence dependencies stay mapped.

## BN and CAD test map

Every row runs `B-ORD`, `R-REP128`, `R-PLUS1`, `R-J2-J4`, and `R-STRESS60` unless
the row explicitly says an omitted Robinhood integration runs a negative
deployment assertion instead. Duration rows also run the applicable boundary
profile.

| ID; components | Primary test location | Required assertions |
| --- | --- | --- |
| BN-001; CM-001,002 | `tests/tokens/test_erc20.py` | Base/RH values and bounds; pending data observes NUMBER; before/exact/after confirmation |
| BN-002; CM-008,009,034 | `tests/data/test_ledger.py` plus Teller domain tests and focused action-block-source tests at the S5-approved path | Current native behavior; RH same-child-block rejection and next-child-block allowance even when ancestor `block.number` repeats; current lower/higher-risk ordering, Underscore classification, call/write/pause/authority/locked-account behavior; fail-closed provider/source validation; no Base migration |
| BN-003; LocalGov components | `tests/modules/test_local_gov.py` and inheritor suites | all LocalGov values/bounds and exact confirmation |
| BN-004; all TimeLock components | `tests/modules/test_time_lock.py` and each inheritor suite | before/open/last-valid/exact-expiry/jump-past; stress headroom |
| BN-005; CM-005,032 | `tests/core/humanResources/test_hr_contributor.py` | transfer authority delay plus independent vesting seconds |
| BN-006; CM-005,032 | same Contributor suite | ownership delay plus independent vesting seconds |
| BN-007; CM-023 | `tests/vaults/test_ripe_gov_vault.py` | prior shares receive full gap; weight/bonus floors; relative totals |
| BN-008; CM-023 | same RipeGov suite | min/max lock, withdrawal exact unlock, early release |
| BN-009; CM-023 | same RipeGov suite | weighted lock, bonus at boundaries, deposit before/after jump, term change |
| BN-010; CM-017 | `tests/priceSources/curve/test_green_ref_pool.py` plus RH disabled suite | Base staleness boundary; no RH deployment/registration |
| BN-011; CM-017,030 | Curve suite and `tests/core/creditEngine/test_credit_dyn_rate.py` | same-number suppression; `+1/+2/+4/+60` danger delta/cap; RH base-rate fallback |
| BN-012; CM-044,014,034 | `tests/core/deleverage/test_deleverage_for_withdrawal.py`, Delta suite | zero-cooldown Robinhood path has no pacing and never activates the duplicated ceiling/bypass; nonzero same-NUMBER/context/exact-boundary assertions only if S4 is approved |
| BN-013; CM-014,029 | `tests/config/test_switchboard_delta.py` and BondRoom suite | past/equal/future absolute input clamps to EVM NUMBER |
| BN-014; CM-029 | `tests/core/bondRoom/test_ripe_bonds.py` | entry/progress, partial and whole epoch skip, no retroactive capacity |
| BN-015; CM-029 | same BondRoom suite | preview equals execution at every clock point |
| BN-016; CM-029,014 | same BondRoom/Delta suites | manual chain-native absolute start |
| BN-017; CM-029 | same BondRoom suite | exact end, next epoch, multi-epoch containing-window calculation |
| BN-018; CM-004 | `tests/registries/test_ripe_hq.py` and CCIP registration integration | capability pending/exact confirmation and no premature mint role |
| BN-019; registry CMs | `tests/registries/test_address_registry.py` | add pending/exact confirm, values/bounds, CCIP pool add |
| BN-020; registry CMs | same registry suite | update pending/exact confirm and jump |
| BN-021; registry CMs | same registry suite | disable pending/exact confirm, shared-delay policy, interaction with pending add/update |
| BN-022; CM-033 | `tests/core/lootbox/test_loot_deposit_points.py` | global/asset/user prior balances across jump; allocation floors/conservation |
| BN-023; CM-033 | `tests/core/lootbox/test_loot_borrow_points.py` | prior principal across jump; borrow/repay ordering; user/global totals |
| BN-024; CM-033 | `tests/core/lootbox/test_loot_ripe_rewards.py` | 324/day nominal comparison, gap-at-prior-rate, cap, allocation dust, rate change order |
| BN-025; CM-033,013 | `tests/core/lootbox/test_underscore_rewards.py`, Charlie suite, RH disabled suite | retained S3 immutable floor; Base `43,200`; RH floor `7,200` with interval zero and no distributor; constructor/setter and strict `>` assertions |
| BN-026; CM-033 | same Underscore suite plus event-consumer fixture | repeated/gapped telemetry accepted; log identity, not NUMBER, is unique |
| BN-027; CM-048,046 | `tests/core/endaoment/test_endaoment_psm_mint.py`, config/Echo suites | repeat bucket, exact refill, one reset after many intervals, mid-bucket change, disabled flags |
| BN-028; CM-048,046 | `tests/core/endaoment/test_endaoment_psm_redeem.py`, config/Echo suites | same plus mint/redeem independence |
| BN-029; CM-030,009 | `tests/core/creditEngine/test_credit_borrow.py` | per-user independence, exact refill, no carry/catch-up, MIXED interest |
| BN-030; CM-026,009 | `tests/core/auctionHouse/test_ah_auctions.py`, Alpha/Bravo suites | copied delay/duration, start/end points, future vs active parameter changes |
| BN-031; CM-026 | same AuctionHouse suite | discount integer monotonicity, repeated quote, skipped prices, exact-end rejection |
| BN-032; CM-038,029 | `tests/config/test_bond_booster.py` and BondRoom suite | absolute expiry before/exact/after; min lock conversion; units unaffected by repeat |
| CAD-001; CM-009,017,030,055 | dynamic-rate suite and `tests/scripts/test_params_cadence_units.py` | raw 10, display 0.001%, runtime integer sequence/cap; no RH danger producer; future raw 60 remains gated |

## Timestamp test map

All rows prove NUMBER movement alone cannot satisfy a seconds boundary and
timestamp movement alone cannot satisfy a NUMBER boundary. Disabled rows also
assert no Robinhood deployment/registration.

| ID | Test location | `MIXED` assertion |
| --- | --- | --- |
| TS-001 | `tests/tokens/test_signatures.py` | permit valid at deadline, invalid after, independent of BN-001 |
| TS-002 | HR Contributor suites | cliff/vesting moves only with seconds; authority confirm only with NUMBER |
| TS-003 | `tests/priceSources/test_pyth_prices.py` | fresh/stale/future seconds; RH omission |
| TS-004 | `tests/priceSources/blueChip/**` | same timestamp suppresses snapshot; delay/staleness seconds; RH omission |
| TS-005 | `tests/priceSources/test_chainlink_prices.py` | future/stale `updatedAt` with held NUMBER; timelock with held time |
| TS-006 | `tests/priceSources/test_aero_ripe.py` | snapshot delay/staleness seconds; RH omission |
| TS-007 | `tests/priceSources/test_stork_prices.py` | fresh/stale/future seconds; RH omission |
| TS-008 | `tests/priceSources/test_undy_vault_prices.py` | snapshot delay/staleness seconds; RH omission |
| TS-009 | RedStone price suite, added if current coverage lacks boundary cases | fresh/stale/future seconds; RH omission |
| TS-010 | CreditEngine borrow/dynamic-rate suites | held NUMBER accrues interest as time advances; NUMBER jump with held time adds no interest |
| TS-011 | `tests/registries/test_address_registry.py` | lastModified follows timestamp; eligibility follows NUMBER |

## Selected-disposition acceptance properties

### Ledger

- Current-Base comparison proves every successful housekeeping call writes
  `lastTouch`, an unchecked lower-risk touch followed by a checked higher-risk
  action at the same NUMBER reverts, and a `+1` clears that rejection.
- Current-Base comparison also proves a checked higher-risk action followed by an
  unchecked lower-risk touch succeeds, while a later checked action at the same
  NUMBER reverts.
- Users classified as Underscore wallets/vaults skip the assertion; the test does
  not substitute caller identity for user classification and still verifies the
  `lastTouch` write.
- The Robinhood profile proves two transactions in the same actual child block
  share one action-block ID and trigger the current checked-action rejection.
- The next Robinhood child block clears the guard even when inherited
  `block.number` remains unchanged; elapsed seconds alone do not clear it.
- The selected source is immutable or equivalently non-mutable after
  deployment, validates its native/Robinhood mode or provider, and fails closed
  on unavailable, malformed, unsupported, or misconfigured child-block data.
- `shouldCheckLastTouch=false` remains a compatibility/configuration test, not
  the selected Robinhood launch posture.
- The forward source/ABI/creation-artifact boundary stays canonical across
  deployments; constructor immutables may produce expected runtime differences.
- No test proposes, simulates, or claims a migration of the deployed Base
  Ledger. Base is regression evidence only.
- Tests prove the action-block abstraction is not consumed by timelocks,
  rewards, rates, auctions, capacity intervals, or any other protocol clock.
- A cross-transaction seconds guard, if approved, tests exact seconds boundary,
  future timestamp rejection assumptions, governance changes, and migration.
- Locked-account protection remains later-call invariant even when pacing is off.
- No assertion uses `chain.id` or Robinhood-specific production artifacts.

### Deleverage

- The minimum-change candidate proves the cooldown is initialized and retained
  at zero, the dormant maximum cannot force a migration, and no manifest or
  governance step silently enables nonzero pacing.
- If a nonzero cooldown is approved, one independent call at the same NUMBER is
  within cooldown and the exact boundary/near-redemption behavior is tested.
- Only an approved context design may bypass; another user, caller, context,
  transaction, or replay cannot.
- Delta and Deleverage maximum-consistency assertions apply only to the
  approved nonzero design.

### Lootbox

- The retained S3 candidate proves interval zero leaves Robinhood Underscore
  rewards disabled while preserving the immutable `7,200` floor and no
  Robinhood Underscore address, permission, route, or call exists.
- Deployment rejects a floor below the approved chain value and setter tests
  cover `floor-1`, `floor`, max, and immutability.
- Current strict send boundary is preserved in Base comparison.

### CAD-001

- Raw value and runtime arithmetic are unchanged by formatting.
- Display derives from declared field units, not a generic percentage helper.
- The test fails if display regresses to `0.10%`.
- No active Robinhood Curve registration can produce danger numbers.

## Invariant and property-test candidates

Use deterministic examples first. Property tests use recorded seeds and bounded
integers that avoid meaningless overflow-only cases:

- NUMBER and timestamp are nondecreasing independently within a scenario.
- Repeating NUMBER never creates elapsed-number rewards, points, age, or progress.
- For a checkpointed rate/balance `x`, one jump `j` adds exactly `x*j` before
  configured caps and documented integer floors.
- Splitting a jump without a state/rate change is equivalent to one jump for
  linear accrual; with a checkpoint change it is intentionally not equivalent.
- Timelock eligibility is exactly its half-open interval.
- Capacity never exceeds its cap, never carries unused capacity, and resets once.
- Auction discounts are nondecreasing inside the window and inaccessible outside.
- BondRoom returns the unique containing epoch and never mints skipped capacity.
- Lock/expiry validity is monotone from valid to invalid.
- Timestamp interest is independent of NUMBER capacity.
- Sum of reward buckets is at most charged distribution; the exact dust is
  reported and owner-approved.
- Unsupported Robinhood component sets are closed under address, registration,
  permission, routing, and callable feature flags.

## Governance and lifecycle scenarios

The minimum cross-contract scenarios are:

1. RipeHq/AddressRegistry CCIP Department add, confirm, capability initiate,
   confirm, permitted mint, disable, and negative premature/unknown-address calls.
2. Teller lower-risk housekeeping followed by higher-risk action, then the
   reverse order, through Ledger, CreditEngine debt update, Lootbox borrow
   points, repeat/jump, repay, Underscore-user classification, and locked-account
   checks under Base-enabled and Robinhood-disabled policies. Replacement
   scenarios run only if approved.
3. Multi-asset withdrawal through Teller and Deleverage with cooldown zero.
   Context, independent same-NUMBER, and exact cooldown-end scenarios run only
   if a nonzero S4 design is approved.
4. PSM mint/redeem bucket independence with both flags false, governed interval
   change, and no GREEN mint authority; activation tests remain skipped/blocked
   until Track 4 owner gates approve.
5. Liquidation creates an auction, repeats price, jumps inside, changes future
   defaults, jumps past end, and proves the active auction kept copied params.
6. RipeGov deposit/lock, Lootbox points, BondRoom preview/purchase, jump over one
   and many epochs, early release/expiry, and RIPE emission conservation.
7. Chainlink timestamp staleness with held NUMBER and a governance timelock with
   held timestamp.
8. Complete Robinhood deployment graph negative assertion for Curve/Aero/
   BlueChip/Pyth/Stork/RedStone/Undy/wrapped-yield/Underscore and disabled PSM.

## Runtime, CI tiers, and fallback

Suggested budgets, to be measured in S1 rather than treated as guarantees:

- `clock-smoke`: harness plus one representative contract, under 60 seconds;
- `clock-pr`: all IDs on `B-ORD`, `R-PLUS1`, `R-J2-J4`, boundaries, under
  8 minutes;
- `clock-full`: adds `R-REP128`, `R-STRESS60`, lifecycle, property tests, and
  inventory mutation tests, under 25 minutes.

Compilation is session-scoped and deployments are snapshot-restored to avoid
multiplied setup cost. Tests may be split by existing pytest markers only after a
marker is registered in repository config. No test may shorten the exact
`R-REP128` profile without renaming it.

Anvil is not the primary fallback because ordinary mining increments its block
height and cannot faithfully create many state-changing transactions at one
NUMBER. If a future Boa version loses direct patching, stop S1. The owner must
approve a pinned lower-level EVM mechanism that supports repeated NUMBER,
arbitrary jumps, timestamp independence, snapshots, and identical artifact
deployment. That decision includes dependency, CI image, maintenance owner, and
cost. Tests must not approximate the repeat profile with read-only calls.

## Failure diagnostics

Every failure begins with one machine-searchable line:

```text
CLOCK_FAIL id=BN-012 components=CM-044,CM-014 profile=R-REP128
step=37 before=(1000000,2000000009) after=(1000000,2000000009)
params=robinhood_candidate seed=none function=deleverageForWithdrawal
expected="independent call blocked" actual="returned true"
```

It then prints the full profile prefix through the failing step, relevant
configured values/bounds, stored start/last/confirm/end checkpoints, revert/event
details, artifact fingerprint, and source occurrence key from the checked
inventory. Secret material and full unrelated state are excluded.

## Commands and completion

The future implementation runs, in order:

```bash
pytest -q tests/clock/test_clock_profiles.py
python scripts/check_block_clock_inventory.py --check
pytest -q tests/inventory/test_block_clock_inventory.py
pytest -q
git diff --check
```

Track 6 plan acceptance requires that an implementation reviewer can trace each
BN/CAD/TS row to a named test, select either chain profile without changing
production source, reproduce exact boundaries and jumps, distinguish current
Base from proposed canonical behavior, and diagnose a failure by stable ID.
