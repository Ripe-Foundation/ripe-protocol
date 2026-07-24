# Track 6 S3: Portable Lootbox Interval Floor

**Status:** Owner and reviewer approved for kickoff; implementation remains open

**Prepared:** 23 July 2026

**Planning baseline:** `c2ded229fefe2ad614693c999bd89faeaec1535e`

**Approval record:** On 23 July 2026, the owner approved all four decisions
below and selected Decision 3 option 1: the approximately 2-second Base /
12-second Robinhood cadence basis is approved for this isolated floor, making
the Robinhood value `7_200` final. The independent brief reviewer approved the
task contract and recommended the `max_value(uint256)` floor guard incorporated
below. Broader cadence-sensitive rates, timelocks, and S6 parameters remain
open.

## Fresh-agent instruction

Treat this document as the task contract. Implement only Track 6 implementation
slice S3: replace the Base-specific minimum Underscore send interval embedded in
the shared `Lootbox` source with one immutable, per-deployment floor while
preserving every other Lootbox behavior.

This is the program's first production-contract change. The implementation must
remain one shared, chain-portable contract. Do not create a Robinhood-specific
Lootbox, use `chain.id`, change reward economics, alter the exact send boundary,
create `DefaultsRobinhood`, rewrite a historical migration, execute a migration,
or change live state.

Use branch `rh-track-6-s3-lootbox-floor`. Commit the implementation to that
branch with clear messages, but do not push directly to or merge into `rh` or
`master`. Leave the branch and worktree in place for review.

S3 has two mandatory reviewer gates:

1. production source, tests, ABI, artifact hashes, and rollout analysis are
   reviewed before the checked inventory is reconciled; and
2. the final inventory reconciliation, targeted tests, S1/S2 gates, and full
   suite are reviewed before merge.

The implementation branch is not merge-ready until both gates close. An
implementation author may not self-approve the semantic inventory change.

## Owner approvals required before kickoff

The fresh agent must verify that the owner explicitly approved all four
decisions below. Approval of this draft as a writing artifact is not itself
approval of these production decisions.

### Decision 1: immutable safety floor

Approve:

- one immutable minimum per Lootbox deployment that is neither zero nor
  `max_value(uint256)`;
- the shared implementation name `MIN_UNDERSCORE_SEND_INTERVAL`;
- an external view named `minUnderscoreSendInterval()`; and
- unconditional initialization of the immutable even when the initial governed
  interval is `0`.

The immutable is a deployment safety floor, not a governed reward parameter.
Changing it requires a new deployment. Governance continues to control the
stored `underscoreSendInterval`, but may not set that interval below the
deployment's floor.

### Decision 2: preserve the exact send boundary

Approve retaining:

```text
block.number > lastUnderscoreSend + underscoreSendInterval
```

Equality remains too early. Changing `>` to `>=` is outside S3 and must not be
smuggled into the parameterization.

### Decision 3: Base and Robinhood values

Approve:

- Base floor: `43_200`;
- Robinhood floor: `7_200`; and
- Base test/default behavior remaining `43_200`.

The Robinhood value uses the Track 6 cadence basis of approximately 2 seconds
per Base block and 12 seconds per Robinhood-observed L1 number. The approval
forms considered were:

1. approve that cadence basis for S3 and approve `7_200` as the final
   Robinhood Lootbox floor; or
2. approve `7_200` only as the S3 test/deployment candidate, with Robinhood
   deployment and parameter-manifest approval blocked until S6 closes the
   cadence-basis row.

The owner selected option 1 on 23 July 2026. This approval is intentionally
narrow: `7_200` is final for the Lootbox safety floor, while S6 must still close
the cadence basis for rates, timelocks, capacities, and other parameters where
the mapping is more economically sensitive.

### Decision 4: live Base version policy

Approve:

- one shared source and constructor interface for Base and Robinhood;
- eventual coordinated Base redeployment and RipeHq registry rewire;
- only bounded, explicitly tracked temporary live-bytecode drift while that
  rollout is reviewed and scheduled;
- old/new source, ABI, creation-bytecode, deployed-bytecode, and constructor
  records;
- an explicit rollback/forward-remediation plan; and
- no permanent Base/Robinhood divergence.

S3 implements and validates the artifact. It does not authorize or execute the
Base deployment, registry change, capability change, Robinhood deployment, or
any live transaction.

If any decision is absent, ambiguous, or materially different, stop before
creating the implementation worktree.

## Worktree bootstrap

The owner must first commit this reviewed brief to `rh`. The fresh agent is
responsible for creating its own worktree:

1. Start from `/Users/wigglez/dev/ripe-protocol`.
2. Verify that:
   - the integration worktree is clean;
   - `rh` resolves to the owner-approved integration commit;
   - this brief exists in that commit;
   - S1 and S2 are ancestors of `rh`;
   - `docs/chains/rh/shared-block-clock-specification.md`,
     `docs/chains/rh/block-clock-validation-plan.md`,
     `config/block-clock-inventory.json`, and the S1/S2 implementation files
     exist in that commit; and
   - the four decisions above have explicit owner provenance.
3. Record:
   - the full starting commit;
   - SHA-256 hashes of this brief, both Track 6 specification files,
     `contracts/core/Lootbox.vy`, `scripts/abis/Lootbox.json`, and the S2
     inventory;
   - installed `vyper`, `titanoboa`, and `pytest` versions; and
   - the clean S2 totals, including 100 direct production occurrences across
     95 lines and 17 files.
4. Confirm that branch `rh-track-6-s3-lootbox-floor` and path
   `/Users/wigglez/dev/ripe-protocol-track-6-s3-lootbox-floor` do not exist.
   If either exists, stop and ask the owner. Do not reuse, delete, reset, or
   overwrite it.
5. Create the isolated worktree:

   ```bash
   git -C /Users/wigglez/dev/ripe-protocol worktree add \
     -b rh-track-6-s3-lootbox-floor \
     /Users/wigglez/dev/ripe-protocol-track-6-s3-lootbox-floor \
     rh
   ```

6. Verify the new worktree's branch, commit, clean status, hashes, runtime
   versions, and S2 baseline.
7. Run all subsequent commands and edits inside
   `/Users/wigglez/dev/ripe-protocol-track-6-s3-lootbox-floor`.

Do not modify or commit from the integration worktree.

## Controlling constraints

- Preserve one canonical Lootbox source for Base, Robinhood, and future EVM
  chains.
- Parameterize the shared implementation once; do not branch on network,
  address, token name, or `chain.id`.
- Limit production semantics to the approved immutable floor and getter.
- Preserve all reward amounts, allocations, permissions, events, storage
  behavior, and strict send eligibility except for replacing the hardcoded
  floor.
- A zero initial governed interval still means Underscore rewards are disabled.
- Even when the governed interval is `0`, the Robinhood deployment must carry
  the `7_200` immutable so a later governed enablement cannot fall back to the
  Base floor or an unsafe zero floor.
- Robinhood must have no Underscore registry, distributor registration, or
  reward permission at launch. S3 tests the disabled constructor posture but
  does not create the deployment graph.
- Do not change point attribution, `ripePerBlock`, reward tokenomics, interval
  reporting, or another Track 6 clock behavior.
- Recommendations are not approvals. Do not infer a live rollout authorization
  from source approval.

## Exact file ownership

### Stage 1: implementation before the first reviewer gate

The S3 implementation may change only:

- `contracts/core/Lootbox.vy`;
- `tests/conf_core.py`, only to pass the new Base floor to the shared Lootbox
  fixture;
- `tests/core/lootbox/test_underscore_rewards.py`;
- `tests/config/test_switchboard_charlie.py`, only where the governance path
  needs floor/boundary coverage;
- `scripts/abis/Lootbox.json`, generated from the canonical source;
- new `docs/chains/rh/lootbox-floor-implementation-record.md`.

If another production, test, interface, or generated file is required, stop and
explain why before editing it.

### Stage 2: checked-inventory reconciliation after reviewer approval

Only after the first reviewer gate supplies immutable approval provenance may
the branch also change:

- `config/block-clock-inventory.json`;
- `scripts/check_block_clock_inventory.py`, only as narrowly required to keep
  the new generic floor identifier discoverable; and
- `tests/inventory/test_block_clock_inventory.py`, only for deterministic
  inventory/mutation expectations.

The implementation author must not invent the semantic approval commit. The
reviewer or owner must provide the approval reference after reviewing Stage 1.
The final inventory must preserve Track 3 provenance, preserve all unrelated
records, and honestly record the changed Lootbox content hash and cadence
surface.

### Explicitly prohibited files

Do not change:

- `contracts/config/DefaultsBase.vy`; it does not contain this parameter;
- future `contracts/config/DefaultsRobinhood.vy`; S6 owns it;
- any file under `migrations/base-mainnet/`;
- any committed file under `migration_history/`;
- `scripts/params/general.py` or `scripts/params/general_output.md`; S10 owns
  the cadence-report formatter;
- Track 7's proposed migration namespace or a Robinhood manifest;
- dependencies, CI, unrelated ABIs, or `docs/chains/rh-summary.md`.

Historical migrations are immutable records. This includes, without limitation:

- `migrations/base-mainnet/1016_Lootbox.py`;
- `migrations/base-mainnet/2025071801_LootBoxPointsRefresh.py`;
- `migrations/base-mainnet/2025080900_Lootbox.py`; and
- `migrations/base-mainnet/2025112500_New_Endaoment_Features.py`.

Do not "fix" their constructor call sites. Base convergence requires a new,
separately reviewed forward migration under the Track 7 convention.

## Required reading

Read the current integrated versions of:

### Program authority

- `docs/chains/rh-summary.md`
- `docs/chains/rh/shared-block-clock-specification.md`
- `docs/chains/rh/block-clock-validation-plan.md`
- `docs/chains/rh/block-number-inventory.md`
- `docs/chains/rh/component-matrix.md`
- `docs/chains/rh/robinhood-deployment-support-specification.md`
- `docs/chains/rh/robinhood-deployment-validation-plan.md`
- `docs/chains/rh/track-6-shared-block-clock-specification.md`
- `docs/chains/rh/track-6-s1-clock-harness.md`
- `docs/chains/rh/track-6-s2-checked-clock-inventory.md`

### Source, tests, tooling, and history

- `contracts/core/Lootbox.vy`
- `contracts/data/Ledger.vy`
- `contracts/data/MissionControl.vy`
- `contracts/config/SwitchboardCharlie.vy`
- `contracts/registries/RipeHq.vy`
- `contracts/modules/Addys.vy`
- `contracts/modules/DeptBasics.vy`
- `tests/conf_core.py`
- all files under `tests/core/lootbox/`
- `tests/config/test_switchboard_charlie.py`
- `tests/utils/clock_profiles.py`
- `tests/clock/test_clock_profiles.py`
- `config/block-clock-inventory.json`
- `scripts/check_block_clock_inventory.py`
- `tests/inventory/test_block_clock_inventory.py`
- `scripts/export_abis.py`
- `scripts/params/general.py`
- the historical Base migration files named above;
- the current committed Base migration history and manifest entry for RipeHq
  registry ID 16; and
- `requirements.txt`.

The controlling Hightop Notes source is:

`/Users/wigglez/dev/hightop-notes/random/hood/hood-chain-executive-summary.md`

If the local checkout is unavailable, use the
[GitHub copy](https://github.com/mickhagen/hightop-notes/blob/main/random/hood/hood-chain-executive-summary.md).
If neither source is accessible, stop rather than silently skipping the
selected architecture. Do not import the superseded federated design.

The integrated Track 6 and Track 7 specifications control if this brief
abbreviates a requirement. Stop on a material conflict rather than silently
choosing one document.

## Objective

Produce one narrow shared-contract revision that:

- removes `ONE_DAY = 43_200 # on Base` from shared Lootbox source;
- accepts a nonzero minimum interval as a constructor argument;
- stores that value as an immutable;
- exposes it through `minUnderscoreSendInterval()`;
- applies it in both the constructor's nonzero-interval validation and
  `setUnderscoreSendInterval`;
- preserves the constructor's disabled posture when the governed interval is
  `0`;
- preserves strict `>` distribution eligibility;
- preserves Base behavior with floor and interval `43_200`;
- proves the Robinhood disabled posture with floor `7_200` and interval `0`;
- supports later Robinhood enablement with a chain-correct `7_200` floor;
- updates only the Lootbox ABI;
- records reproducible artifact and live-version evidence; and
- leaves live deployment, defaults generation, migration execution, and
  reporting to their owning slices.

## Phase A: re-verify the baseline

Before editing:

- [ ] Confirm `ONE_DAY` is declared once in `Lootbox.vy` and used only by the
  constructor and setter minimum validations.
- [ ] Confirm distribution eligibility is independently enforced with strict
  `>`.
- [ ] Confirm the constructor skips the governed-interval floor check when
  `_underscoreSendInterval == 0`.
- [ ] Confirm the central test fixture currently deploys Lootbox with interval
  `43_200`.
- [ ] Confirm SwitchboardCharlie forwards the governed interval without owning
  a separate floor.
- [ ] Confirm `DefaultsBase.vy` has no Lootbox floor or interval field.
- [ ] Confirm `scripts/params/general.py` formats
  `underscoreSendInterval` through `format_blocks_to_time`, and record this as
  S10-owned work that S3 will not change.
- [ ] Enumerate every constructor call site and classify it as active test
  fixture, historical migration, proposed future deployment, or other.
- [ ] Confirm existing Base migrations and migration history are unchanged.
- [ ] Run the targeted Lootbox and SwitchboardCharlie tests, S1, S2, and the
  full suite on the untouched starting commit.

If any baseline claim differs, record the exact source delta and stop on a
material semantic conflict.

## Phase B: implement the shared immutable floor

In `contracts/core/Lootbox.vy`:

1. remove the Base-specific `ONE_DAY` constant;
2. add constructor argument `_minUnderscoreSendInterval`;
3. require the approved floor to be neither zero nor
   `max_value(uint256)`;
4. assign it unconditionally to immutable
   `MIN_UNDERSCORE_SEND_INTERVAL`;
5. expose external view `minUnderscoreSendInterval()`;
6. when `_underscoreSendInterval != 0`, require it to be at least the
   immutable floor;
7. in `setUnderscoreSendInterval`, require `_numBlocks` to be at least the
   immutable floor; and
8. preserve every other check, state write, event, permission, and behavior.

Do not:

- change the order or meaning of existing constructor arguments except for the
  reviewed insertion of the new floor;
- alter the existing `max_value(uint256)` setter rejection;
- add a chain, token, or address conditional;
- make the floor governed or stored in mutable storage;
- infer the floor from the initial governed interval;
- automatically enable Underscore rewards;
- initialize `lastUnderscoreSend` to a new value;
- change strict `>` to `>=`; or
- change reward amounts, RIPE availability, allocation, or distribution code.

Use the smallest constructor-interface change that clearly distinguishes the
immutable floor from the mutable initial interval. Document the chosen argument
order and why it minimizes deployment mistakes.

## Phase C: update and extend tests

Update the central fixture with:

```text
minimum floor = 43_200
initial governed interval = 43_200
```

Existing tests must continue to exercise Base behavior. Add focused deployment
helpers or fixtures for the comparison cases without changing the global
fixture's semantics.

### Constructor matrix

Cover:

| Floor | Initial interval | Expected result |
| ---: | ---: | --- |
| `0` | `0` | revert: invalid floor |
| `max_value(uint256)` | `0` | revert: invalid floor |
| `43_200` | `43_199` | revert: invalid interval |
| `43_200` | `43_200` | deploy; Base behavior enabled |
| `43_200` | `43_201` | deploy |
| `7_200` | `0` | deploy; Robinhood posture disabled |
| `7_200` | `7_199` | revert: invalid interval |
| `7_200` | `7_200` | deploy when explicitly testing future enablement |
| `7_200` | `7_201` | deploy |

For the `7_200` / `0` case, prove:

- `minUnderscoreSendInterval() == 7_200`;
- `underscoreSendInterval() == 0`;
- `hasUnderscoreRewards() == false`;
- deposit and yield reward amounts remain zero under the existing constructor
  behavior; and
- distribution cannot proceed.

### Setter matrix

Under an authorized Switchboard caller, cover floor minus one, exact floor, and
floor plus one for both `43_200` and `7_200` deployments. Preserve:

- unauthorized-caller rejection;
- paused-contract rejection;
- `max_value(uint256)` rejection;
- no-change rejection; and
- the existing event shape and value.

The Robinhood disabled deployment must prove that a later setter call is still
bounded by `7_200`, even though deployment skipped the initial interval assert.

### Exact distribution boundary

Using the integrated S1 clock controller, prove under Base and Robinhood
parameter profiles:

- `last + interval - 1` is too early;
- `last + interval` is still too early because the contract uses strict `>`;
- `last + interval + 1` is eligible when all unrelated preconditions hold;
- repeated-number calls do not advance eligibility; and
- representative and stress jumps cannot bypass the configured interval except
  by landing strictly after it.

Use observed-call diagnostics tied to BN-025/BN-026 and CM-033. Do not replace
all existing tests mechanically if a small focused table supplies the new
boundary evidence.

### Switchboard and Base regression

Prove:

- SwitchboardCharlie still timelocks and forwards the requested governed
  interval;
- it cannot set a value that Lootbox rejects below the immutable floor;
- existing Base Underscore reward tests remain green at `43_200`;
- unrelated Lootbox claim, points, and RIPE reward suites remain green; and
- the same Lootbox source is compiled for both parameter profiles.

## Phase D: regenerate and verify the ABI

Use the existing ABI exporter with the pinned compiler. Generate into a
temporary directory first and compare outputs.

Update only `scripts/abis/Lootbox.json`. Verify:

- the constructor contains exactly one new `uint256` floor argument in the
  reviewed position;
- `minUnderscoreSendInterval()` is present with the expected mutability and
  return type;
- no existing function, event, error/revert contract, or output is removed or
  renamed; and
- no unrelated ABI file changes.

Do not manually edit the JSON to mimic the expected interface.

## Phase E: artifact and live-version record

Create `docs/chains/rh/lootbox-floor-implementation-record.md`.

Record:

- starting and implementation commits;
- compiler and dependency versions;
- source and compiler-input hashes;
- old and new ABI hashes and a normalized ABI diff;
- old and new creation-bytecode hashes;
- candidate deployed-runtime hashes for:
  - Base floor `43_200`, interval `43_200`; and
  - Robinhood floor `7_200`, interval `0`;
- the constructor arguments used for every candidate hash;
- proof that both candidates use identical shared source and compiled creation
  bytecode;
- the expected immutable-driven runtime difference between Base and Robinhood;
- current Base RipeHq and registry-ID-16 Lootbox addresses from committed
  manifests;
- dated read-only verification of the current live Base address and runtime
  code hash when an approved public endpoint is available;
- exact S1/S2 and test results;
- the inventory drift expected before reconciliation;
- the selected owner decisions and approval provenance; and
- every unresolved deployment, audit, security, or rollout gate.

Do not claim that different immutable constructor values yield identical
deployed runtime. The one-codebase requirement is identical canonical source,
compiler input, and creation artifact; reviewed constructor inputs may produce
different immutable-bearing deployed runtime.

If live Base verification is unavailable, record it as an unresolved rollout
input. Do not guess or copy a stale address/hash as current fact.

## Phase F: specify, but do not execute, Base convergence

The implementation record must contain a concrete forward-rollout plan for
review. At minimum, it must address:

- a new migration ID selected later by the Track 7/integration owner;
- deployment of the new shared Lootbox artifact with Base floor `43_200`;
- snapshot and preservation of current governed values:
  - `hasUnderscoreRewards`;
  - `underscoreSendInterval`;
  - `undyDepositRewardsAmount`;
  - `undyYieldBonusAmount`; and
  - `lastUnderscoreSend`;
- the fact that a newly deployed Lootbox starts with fresh storage and cannot
  automatically preserve `lastUnderscoreSend`;
- the safe posture during that reset, including whether Underscore rewards
  remain disabled until a controlled first eligible send;
- RipeHq registry-ID-16 replacement timing and timelock;
- restoration and verification of the new Lootbox's RIPE mint capability;
- prevention of simultaneous old/new mint authority;
- SwitchboardCharlie and Addys resolution after the registry change;
- event, getter, and stored-value verification;
- rollback reality before and after the registry/capability transition;
- old/new code hashes and manifests;
- temporary live-version drift owner, bounds, deadline, and convergence
  evidence; and
- post-change smoke tests.

The plan must state which steps are reversible, which require a forward fix,
and what happens to a pending Underscore distribution window. It may recommend
a design adjustment if exact state continuity is necessary, but that adjustment
requires a new owner/reviewer decision and is not silently added to S3.

For Robinhood, reserve the Track 7 meaning of
`0010_Track6S3LootboxFloor.py`: a predeployment artifact assertion, not an
onchain upgrade transaction when the correct Lootbox is included in the initial
deployment. Do not create that migration file in S3.

## Mandatory reviewer gate 1: production implementation

After Phases A–F:

1. commit the Stage 1 files;
2. run all targeted tests that can pass before inventory reconciliation;
3. run S2 and record its exact expected drift diagnostics without weakening or
   suppressing them;
4. provide the diff, artifact record, constructor/ABI comparison, test results,
   and rollout plan to the reviewer; and
5. stop.

The reviewer must verify:

- production semantics match all four owner decisions;
- the historical migration tree is unchanged;
- the ABI change is minimal;
- Base and Robinhood boundary tests are meaningful;
- artifact hashes are reproducible;
- the Base state-reset/rewire analysis is adequate;
- S2 failed only for the expected reviewed source/cadence delta; and
- no unrelated behavior or file changed.

Do not begin inventory reconciliation until the reviewer or owner supplies
immutable approval provenance for the exact Stage 1 implementation.

## Phase G: reconcile the S2 checked inventory

After gate 1:

- update the reviewed cadence pattern so
  `MIN_UNDERSCORE_SEND_INTERVAL` remains machine-discoverable;
- remove only obsolete `ONE_DAY` candidates;
- add every new immutable-floor candidate emitted by the reviewed source;
- preserve BN-025/BN-026 identities and the direct 100/95/17 baseline unless
  the checker proves an independently reviewed reason to change them;
- update the Lootbox path content hash;
- preserve Track 3 review provenance;
- use the gate-1 approval commit for the semantic reconciliation;
- update deterministic count assertions and mutation fixtures;
- ensure deleting, renaming, or moving the new floor produces an actionable
  failure; and
- do not broaden the cadence checker so far that unrelated identifiers become
  suppressible or disappear.

If S2's current single-hardening-provenance design requires a reviewed
restamp, record that fact and perform it mechanically against the gate-1
approval commit. Do not present a large provenance-only diff as new semantic
classification.

The final checker output must distinguish:

- unchanged direct `block.number` inventory;
- changed cadence candidates caused by the approved S3 source/test/ABI delta;
- unchanged unrelated seconds/timestamp/mixed-clock surfaces; and
- the new Lootbox production content hash.

## Mandatory reviewer gate 2: merge readiness

Before merge, an independent reviewer must inspect:

- the complete branch diff;
- owner-decision provenance;
- Stage 1 and inventory approval commits;
- source and ABI;
- old/new artifact hashes;
- current Base evidence and rollout plan;
- targeted Base and Robinhood clock tests;
- S1 and S2 results;
- full-suite result;
- whitespace and changed-file scope; and
- merge-base/branch freshness against current `rh`.

Any post-review production edit reopens gate 1. Any post-review inventory,
test, ABI, or implementation-record edit reopens the relevant review scope.
Only the owner merges and pushes after reviewer approval.

## Cross-track interface

- **S1:** consume the integrated clock controller and artifact boundary. Do not
  modify S1 utilities merely to make a Lootbox test convenient.
- **S2:** S3 is the first production customer of the checked inventory. Its
  planned failure and reviewed reconciliation are required evidence, not
  optional cleanup.
- **S6:** owns `DefaultsRobinhood`, final parameter manifest, and any remaining
  cadence-basis approval. S3 supplies the constructor interface and tested
  candidate values.
- **S10:** owns `format_blocks_to_time` and CAD-001 reporting correction.
  S3 must identify but not fix the existing Lootbox interval report.
- **Track 7:** owns migration namespaces, deployment graph/tooling, manifests,
  and execution. S3 supplies artifact requirements and the Base rollout plan.
- **Track 8:** owns shared vault changes. S3 must not alter Lootbox point or
  reward accounting as part of the vault work.

Record any file or decision collision and stop before editing another track's
owned surface.

## Approval and safety boundaries

The agent may:

- inspect repository code, history, manifests, and integrated specifications;
- run existing local tests and compilers;
- perform read-only public RPC verification without secrets;
- implement the approved shared Lootbox floor;
- update the owned tests and ABI;
- create the implementation record;
- commit Stage 1 for reviewer inspection;
- after explicit gate-1 approval, reconcile the owned S2 files; and
- recommend a future deployment/rollback plan.

The agent must obtain fresh owner approval before:

- changing any of the four owner decisions;
- changing another Lootbox semantic;
- editing a historical or new migration;
- creating `DefaultsRobinhood`;
- changing reports or parameter-generation code;
- changing live-version policy;
- adding a dependency;
- accessing a secret;
- signing or broadcasting a transaction;
- deploying, verifying, registering, rewiring, pausing, or configuring a live
  contract;
- contacting an external party; or
- editing or ticking `docs/chains/rh-summary.md`.

## Stop conditions

Stop and report evidence if:

- any owner decision is missing;
- the starting source or Track 6 specification materially changed;
- S1 or S2 is absent or red on the untouched baseline;
- a historical migration appears to require rewriting;
- `DefaultsBase` or `DefaultsRobinhood` appears necessary for S3;
- preserving strict `>` is incompatible with the proposed implementation;
- disabled deployment cannot retain the immutable floor safely;
- a new source path, chain branch, or Robinhood-specific Lootbox is required;
- a production behavior outside the minimum floor changes;
- the ABI diff removes or renames an existing surface;
- artifact builds are not reproducible;
- Base state continuity or rewire safety requires an unapproved contract
  feature;
- S2 drift differs from the reviewed S3 delta;
- the full suite requires weakening or skipping an existing test;
- another active track overlaps an owned file; or
- a live/state-changing action would be required.

Do not hide a guard failure with an ignore, placeholder approval, broad regex,
or skipped test.

## Validation

### Baseline

Run on the untouched starting commit:

```bash
PYTHONPATH=. pytest -q tests/core/lootbox/test_underscore_rewards.py
PYTHONPATH=. pytest -q tests/config/test_switchboard_charlie.py
PYTHONPATH=. pytest -q tests/clock/test_clock_profiles.py
PYTHONPATH=. python scripts/check_block_clock_inventory.py --check
PYTHONPATH=. pytest -q tests/inventory/test_block_clock_inventory.py
PYTHONPATH=. pytest -q
git diff --check
```

### Stage 1 before reviewer gate

Run:

```bash
PYTHONPATH=. pytest -q tests/core/lootbox/test_underscore_rewards.py
PYTHONPATH=. pytest -q tests/config/test_switchboard_charlie.py
PYTHONPATH=. pytest -q tests/clock/test_clock_profiles.py
PYTHONPATH=. python scripts/check_block_clock_inventory.py --check
git diff --check
```

The S2 command is expected to fail only for the planned S3 cadence/content
delta before gate 1. Record every diagnostic and do not alter S2 yet.

### Final after reviewed inventory reconciliation

Run, in order:

```bash
PYTHONPATH=. pytest -q tests/core/lootbox/test_underscore_rewards.py
PYTHONPATH=. pytest -q tests/config/test_switchboard_charlie.py
PYTHONPATH=. pytest -q tests/core/lootbox
PYTHONPATH=. pytest -q tests/clock/test_clock_profiles.py
PYTHONPATH=. python scripts/check_block_clock_inventory.py --check
PYTHONPATH=. pytest -q tests/inventory/test_block_clock_inventory.py
PYTHONPATH=. pytest -q
git diff --check
```

Also:

- [ ] Confirm the exact changed-file set matches the two-stage ownership list.
- [ ] Confirm all historical migrations and migration history are byte-identical
  to the starting commit.
- [ ] Confirm `DefaultsBase`, future `DefaultsRobinhood`, S10 reporting,
  dependencies, CI, unrelated ABIs, and the master checklist are unchanged.
- [ ] Confirm the Base and Robinhood cases use the same canonical source and
  creation artifact.
- [ ] Confirm deployed-runtime differences are fully explained by reviewed
  immutable constructor inputs.
- [ ] Confirm every constructor, setter, and strict-boundary matrix row passes.
- [ ] Confirm S2 production direct counts remain reconciled.
- [ ] Confirm no secrets appear in logs or the implementation record.
- [ ] Record every command, result, duration, baseline commit, approval commit,
  and final commit.

If a pre-existing failure exists, reproduce it on the untouched baseline and
separate it from S3. Do not weaken or skip a test to obtain a green result.

## Completion report

The final handoff must include:

- starting, Stage 1, approval, inventory-reconciliation, and final commits;
- exact changed files;
- the four owner decisions and provenance;
- compiler/runtime versions;
- constructor and ABI diff summary;
- Base and Robinhood floor/interval matrices;
- strict-boundary evidence under S1 profiles;
- old/new source, ABI, creation-bytecode, and deployed-runtime hashes;
- current live Base evidence or an explicit unresolved-live-evidence blocker;
- Base rollout, state-reset, rewire, rollback, and temporary-drift summary;
- S2 before/after diagnostics and reconciled counts;
- all validation commands and results;
- reviewer sign-offs for both gates;
- unresolved migration, audit, S6, Track 7, and live-deployment gates; and
- which Track 6 S3 / Section 2 checklist items are eligible for owner review.

Do not edit or tick `docs/chains/rh-summary.md`. Source integration does not
authorize deployment or close the later launch gates.
