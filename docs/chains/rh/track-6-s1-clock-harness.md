# Track 6 S1: Dual-Clock Harness Foundation

**Status:** Draft for owner review; do not launch until the owner approvals below are explicit

**Prepared:** 23 July 2026

**Planning baseline:** `758f45f5455fd7c05b25533d2d748769bcfc49c2`

## Fresh-agent instruction

Treat this document as the task contract. Implement only the reusable test harness specified as Track 6 implementation slice S1. The result must let later test slices run identical compiled Ripe artifacts under exact Base and Robinhood EVM-observed-number profiles while controlling `block.number` and `block.timestamp` independently.

This is test infrastructure only. Do not modify production contracts, defaults, configuration artifacts, migrations, deployment scripts, generated ABIs, dependency pins, CI, or `docs/chains/rh-summary.md`. Do not implement any Track 6 contract slice or approve a provisional clock or parameter value.

Use branch `rh-track-6-s1-clock-harness`. Commit the validated deliverables to that branch with clear messages. Never push directly to or merge into `rh` or `master`; the owner reviews and integrates the work.

## Owner approvals required before kickoff

The fresh agent must verify that the owner has explicitly approved all three of these S1 decisions:

1. `+2` and `+4` as the representative Robinhood jump sizes used by `R-J2-J4`;
2. `+60` as a conservative synthetic stress jump, explicitly **not** an authoritative Robinhood maximum; and
3. the pinned Boa patch mechanism described below, without adding Anvil, a pytest plugin, or another dependency.

If the approvals are absent or ambiguous, stop before creating the implementation worktree. Draft approval of this brief is not itself approval of the three runtime/profile decisions.

## Worktree bootstrap

The owner must first commit this approved brief to `rh`. The fresh agent is responsible for creating its own worktree:

1. Start from `/Users/wigglez/dev/ripe-protocol`.
2. Verify that:
   - the integration worktree is clean;
   - `rh` resolves to the owner-approved integration commit;
   - this brief exists in that commit;
   - `docs/chains/rh/shared-block-clock-specification.md` and `docs/chains/rh/block-clock-validation-plan.md` exist in that commit; and
   - Track 6's reviewed specification cycle is closed.
3. Record the full starting commit and SHA-256 hashes of both Track 6 specification files in the completion report.
4. Confirm that branch `rh-track-6-s1-clock-harness` and path `/Users/wigglez/dev/ripe-protocol-track-6-s1-clock-harness` do not already exist. If either exists, stop and ask the owner; do not reuse, delete, reset, or overwrite it.
5. Create the isolated worktree:

   ```bash
   git -C /Users/wigglez/dev/ripe-protocol worktree add \
     -b rh-track-6-s1-clock-harness \
     /Users/wigglez/dev/ripe-protocol-track-6-s1-clock-harness \
     rh
   ```

6. Verify the new worktree's branch, commit, clean status, and specification hashes.
7. Run every subsequent command and make every edit inside `/Users/wigglez/dev/ripe-protocol-track-6-s1-clock-harness`.

Do not modify or commit from the integration worktree. Leave the branch and worktree in place for owner review; do not remove or merge them yourself.

## Exact file ownership

This slice may change only:

- new `tests/utils/clock_profiles.py`;
- new `tests/clock/test_clock_profiles.py`; and
- `tests/conftest.py`, only as narrowly needed to register or expose the fixture.

If the implementation requires any other file, stop and explain why. In particular, do not change:

- any file under `contracts/`;
- `requirements.txt` or dependency metadata;
- defaults, parameter reports, migrations, manifests, ABI exports, or deployment tooling;
- the S2 inventory files; or
- another Robinhood track's files.

## Required reading

Read the current integrated versions of:

- `docs/chains/rh-summary.md`
- `docs/chains/rh/shared-block-clock-specification.md`
- `docs/chains/rh/block-clock-validation-plan.md`
- `docs/chains/rh/block-number-inventory.md`
- `docs/chains/rh/component-matrix.md`
- `docs/chains/rh/track-6-shared-block-clock-specification.md`
- `tests/conftest.py`
- `tests/conf_core.py`
- representative helper, fixture, and snapshot patterns throughout `tests/` (the new `tests/utils/` directory does not exist at the planning baseline); and
- the pinned runtime versions in `requirements.txt`.

The controlling Hightop Notes source is:

`/Users/wigglez/dev/hightop-notes/random/hood/hood-chain-executive-summary.md`

If the local checkout is unavailable, use the [GitHub copy](https://github.com/mickhagen/hightop-notes/blob/main/random/hood/hood-chain-executive-summary.md). If neither source is accessible, stop rather than silently skipping the selected architecture. Do not import the superseded federated design from `random/hood/hood-chain.md`.

Use the integrated Track 6 documents as the authority if this brief abbreviates a field or example. If those documents changed after this brief's planning baseline, record the delta and stop on any material conflict rather than choosing one silently.

## Objective

Implement and validate a small, deterministic API that:

- defines the exact synthetic clock profiles approved by Track 6;
- sets EVM `NUMBER` and timestamp independently without implicit mining;
- rejects accidental backwards movement inside a scenario;
- isolates every scenario through Boa anchoring or equivalent snapshot restoration;
- records machine-searchable traces for controlled clock mutations and observed contract calls;
- exposes exact boundary helpers used by later contract slices;
- supports the three named parameter profiles without creating Robinhood-specific contract source; and
- gives later slices an identical-artifact assertion boundary.

S1 proves the harness. It does not deploy the full Ripe system, create `DefaultsRobinhood`, or guess unresolved Base/Robinhood parameter values.

## Phase A: Re-verify the runtime primitive

The first tests in `tests/clock/test_clock_profiles.py` must fail closed unless the installed environment satisfies the specification.

- [ ] Assert the installed versions are `titanoboa==0.2.7` and `pytest==8.4.2`.
- [ ] Prove direct assignment to `boa.env.evm.patch.block_number`.
- [ ] Prove direct assignment to `boa.env.evm.patch.timestamp`.
- [ ] Prove NUMBER and timestamp can move independently by arbitrary approved deltas.
- [ ] Prove two observed calls can be made with the same NUMBER while timestamp moves.
- [ ] Prove `boa.env.anchor()` restores both values after the context exits.
- [ ] Prove the helper does not depend on automatic mining or an implicit clock advance.

Use the pinned stack already in the repository. Do not install or add a dependency. Anvil is not an accepted primary fallback because ordinary mining cannot faithfully model repeated state-changing calls at one EVM `NUMBER`.

An approved later dependency-security refresh may intentionally change the pinned Boa or pytest versions and trip this exact-version gate. That failure is expected and must remain fail-closed until a separately reviewed change approves the new expected versions and re-proves every runtime primitive in this phase. Do not loosen the assertion to a version range merely to accommodate a pin refresh.

Stop if any pinned version differs, a runtime write is ignored, a call implicitly advances a controlled clock, or anchor restoration is unreliable.

## Phase B: Implement the public clock API

Implement these public concepts in `tests/utils/clock_profiles.py`:

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

The exact Python types and fixture composition may follow existing repository conventions, but the public behavior and names above must remain recognizable and documented in code.

In S1, `deployed_system` is a minimal fixture boundary, not a deployment of the complete Ripe protocol. It validates the clock and parameter-profile names, applies scenario isolation, accepts or wraps a caller-supplied minimal deployment factory, and exposes the artifact fingerprint and profile metadata that later slices need. S1 must prove that boundary with the smallest available test deployment; later slices supply the concrete full-system factory, approved parameter extraction, and protocol-specific assertions.

### Mutation behavior

- `set` rejects a decreasing NUMBER or timestamp within a scenario. Anchor restoration is the only permitted backwards transition.
- Every explicit mutation records the intended and actual before/after values.
- No helper call advances either clock unless that movement is explicitly requested.
- `apply` validates the profile name, step range, and exact resulting point.
- `hold_number(seconds=x)` advances timestamp by `x` while holding NUMBER.
- `hold_timestamp(numbers=x)` advances NUMBER by `x` while holding timestamp.
- Invalid negative offsets, invalid intervals, impossible windows, unknown parameter profiles, and out-of-range steps fail clearly.

### Observation behavior

`observed_call` records:

- stable inventory ID;
- component IDs when supplied;
- profile name and step;
- optional deterministic/property-test seed;
- intended and actual pre-call NUMBER/timestamp;
- actual post-call NUMBER/timestamp;
- parameter-profile name and relevant values or bounds supplied by the caller;
- success or revert and a normalized reason;
- target address, function signature, and human-readable call label; and
- the state field, event, or boundary assertion used to prove what context the target observed.

The helper may not claim that a contract observed the controlled context merely because the environment has that value. A later scenario must supply a persisted field, event, or behavior-changing boundary assertion. Do not log secrets or unrelated full state.

## Phase C: Implement the exact profiles

Unless a test needs headroom for an existing absolute value, use:

```text
N = 1_000_000
T = 2_000_000_000
```

Implement exactly:

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

`B`, `S`, and `E` must be derived from the supplied scenario state, never copied from a current live height. Preserve the evidence label on each profile:

- documented Base model;
- documented Robinhood/Arbitrum model;
- dated empirical observation;
- owner-approved representative assumption; or
- owner-approved conservative stress assumption.

Do not label `+60` as observed, guaranteed, or a maximum.

## Phase D: Implement exact boundary helpers

The helpers must make these points easy to request and diagnose:

| Boundary | Controlled NUMBER |
| --- | ---: |
| before open | `start - 1` |
| exact open | `start` |
| after open | `start + 1` |
| last valid | `end - 1` |
| exact end | `end` |
| after end | `end + 1` |
| skip open | `start - 1 -> start + 1` |
| skip whole window | `start - 1 -> end + 1` |

Do not embed generic claims that every contract opens or expires at the same comparison operator. Later slice tests own the domain-specific expected result. S1 owns exact point construction, validation, and traceability.

## Phase E: Isolation, fixtures, and artifact boundary

- [ ] Run each parametrized scenario inside a fresh `boa.env.anchor()`.
- [ ] Assert initial NUMBER/timestamp, sequence index zero, and an empty trace at scenario start.
- [ ] Verify all controller state and environment state are restored after success and revert paths.
- [ ] Ensure a failing scenario does not contaminate the next profile or parameter-profile case.
- [ ] Keep the fixture registration in `tests/conftest.py` narrow and free of production deployment behavior.
- [ ] Provide a reusable artifact-fingerprint helper or assertion boundary covering source content, compiler version/settings, ABI, and unbound creation bytecode.
- [ ] Prove that switching `base_current`, `base_canonical`, and `robinhood_candidate` does not select different production source.
- [ ] Treat actual parameter extraction and full-system deployments as later-slice responsibilities.

If cached deployments are used in a demonstration test, snapshot immediately after deployment and restore before each profile/parameter pair. Do not introduce a global fixture whose hidden state changes the behavior of existing tests.

## Phase F: Test the harness itself

`tests/clock/test_clock_profiles.py` must include focused tests for:

- installed-version and runtime primitive gate;
- every exact profile and its length;
- `R-REP128` retaining all 128 points;
- independent NUMBER and timestamp movement;
- monotonicity rejection;
- unknown profile, invalid step, invalid boundary, and invalid parameter-profile failures;
- derived boundaries and the two skip transitions;
- trace schema on success and revert;
- anchor restoration after success, assertion failure, and caught revert;
- cross-test isolation;
- no implicit clock advance;
- deterministic diagnostic formatting;
- identical-artifact fingerprint equality across parameter-profile labels; and
- an intentional fingerprint mismatch that fails clearly.

Prefer a minimal existing or test-local deployable contract only when necessary to prove observed-call behavior. Do not add a production or mock contract file; if an existing contract cannot prove the behavior within this slice's ownership, stop and propose a separately reviewed expansion.

Every failure must begin with a searchable line shaped like:

```text
CLOCK_FAIL id=BN-012 components=CM-044,CM-014 profile=R-REP128
```

Then include the step, before/after values, parameter profile, seed, function/label, expected result, actual result, and profile prefix through the failure. Tests must assert the stable prefix and core fields rather than brittle full formatting.

## Approval and safety boundaries

The agent may:

- read repository and public-source material;
- implement and run the three owned test files;
- make a recommendation when an implementation detail is not fully prescribed; and
- commit validated work to the S1 branch.

The agent may not without fresh owner approval:

- add or update a dependency;
- change the approved profile values;
- substitute a different EVM runtime;
- add files outside the exact ownership list;
- modify production code, defaults, migrations, manifests, CI, or ABI exports;
- sign or broadcast a transaction;
- contact an external party; or
- mark a `rh-summary.md` checkbox complete.

## Stop conditions

Stop and report evidence if:

- installed Boa or pytest versions differ from the pinned versions;
- direct independent control, repeated NUMBER, arbitrary jump, or restoration fails;
- the runtime implicitly mines or advances a controlled value;
- isolation cannot be proven;
- exact profiles cannot be represented without approximation;
- the API requires a new dependency or file outside the approved ownership;
- the identical-artifact boundary would require a chain-specific production source;
- observed-call proof cannot name a state, event, or boundary observable; or
- a concurrent change overlaps an owned file.

Do not hide a failed runtime primitive with a skipped or xfailed test.

## Validation

Run, in order:

```bash
PYTHONPATH=. pytest -q tests/clock/test_clock_profiles.py
PYTHONPATH=. pytest -q
git diff --check
```

Also:

- [ ] Confirm `git status --short` contains only the three approved file paths.
- [ ] Confirm no dependency, production, generated, migration, manifest, ABI, or CI file changed.
- [ ] Confirm every exact profile and public helper is covered.
- [ ] Confirm no test selects chain-specific production source.
- [ ] Confirm diagnostics contain no secrets.
- [ ] Record command outputs, durations, starting commit, specification hashes, and final commit.

If the full suite has a pre-existing failure, reproduce it on the untouched starting commit and clearly separate it from S1. Do not weaken or skip an existing test to obtain a green result.

## Completion report

The final handoff must include:

- starting and final commit;
- exact changed files;
- owner approvals relied upon;
- installed runtime versions;
- concise API and profile summary;
- validation commands and results;
- any pre-existing failures;
- stop conditions encountered;
- remaining decisions or follow-on work; and
- which Track 6 S1 / Section 2 items are **eligible for owner review**.

Do not edit or tick `docs/chains/rh-summary.md`. The owner decides whether the S1 requirement is complete after review and integration.
