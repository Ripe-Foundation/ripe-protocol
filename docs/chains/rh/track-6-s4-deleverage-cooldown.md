# Track 6 S4: Portable Deleverage Cooldown and Authorized Context

**Status:** Draft for owner and security review; no implementation or kickoff is
authorized

**Prepared:** 24 July 2026

**Planning baseline:** `382eb7da82bc4ed54be945311a8ccd30fae87dec`

**Minimum-change amendment:** 24 July 2026 — Stage A must first determine
whether any production change is necessary when Robinhood leaves
`deleverageCooldown = 0`. Stage B is prohibited unless the owner explicitly
rejects that no-source-change path after reviewing its lost protection.

**Required launch baseline:** the reviewed Track 6 S3 implementation and its
checked-inventory reconciliation must be integrated into `rh`; the exact commit
is intentionally not guessed in this draft

## Fresh-agent instruction

Treat this document as the task contract. Work only on Track 6 slice S4:
first determine whether the existing contracts with zero cooldown satisfy the
selected launch scope. Only if the owner rejects the resulting no-pacing risk
may S4 replace the duplicated ceiling and repeated-number bypass with a shared
maximum and authorized multi-leg context.

S4 has three stages:

1. **Stage A — security and compatibility decision:** repository-read-only
   analysis plus one decision record. No contract, ABI, test, inventory,
   dependency, migration, or external-repository change is allowed.
2. **Stage B — production implementation:** blocked until the owner and an
   independent security reviewer approve every mandatory decision below,
   approve the exact file set, and resolve dependency sequencing with H-01.
3. **Stage C — checked-inventory reconciliation:** blocked until an independent
   reviewer approves the Stage B production implementation.

The default result of Stage A is **no production change** unless evidence
demonstrates an indispensable nonzero launch cooldown and the owner rejects the
configuration-only alternative. Do not convert a recommendation into approval,
infer that Teller is the coordinator, or silently change the Base Underscore
integration.

Use branch `rh-track-6-s4-deleverage-cooldown`. Commit Stage A to that branch
and stop at the first checkpoint. Never push directly to or merge into `rh` or
`master`; the owner reviews and integrates the work.

This brief authorizes no live RPC, signer, transaction, deployment, registry
change, governance action, dependency change, or external communication.

## Hard launch and sequencing gates

### S3 must be integrated first

Do not create the S4 branch or worktree until:

- S3 has passed both mandatory reviewer gates;
- S3 is integrated into `rh`;
- the S2 inventory on `rh` includes the reviewed S3 reconciliation;
- the S1/S2 tests pass on the resulting integration commit; and
- this brief is committed to that same or a later reviewed `rh` commit.

S4 consumes the post-S3 source hashes, cadence inventory, review-provenance
model, and artifact process. Do not branch from the current planning baseline,
copy S3 files from its floating worktree, or restamp a pre-S3 inventory.

### H-01 controls the Stage B dependency baseline

H-01 Stage A may proceed independently. Before S4 Stage B begins, the owner
must record one of these orders:

1. **H-01 first:** integrate the approved dependency profile, then compile and
   implement S4 against it; or
2. **S4 first:** implement S4 against the current exact dependency profile,
   then deliberately repeat S4's compiler, artifact, ABI, S1/S2, targeted, and
   full-suite evidence after H-01 changes dependencies.

No answer means H-01 first. An H-01 alert analysis or candidate lock is not an
integrated dependency profile.

### Track 8 and external coordination

Before Stage B, verify that no active Track 8 or other branch owns an S4 file.
The Underscore repository is a downstream compatibility input, not an S4
write target. Any required Underscore source or deployment change needs its own
reviewed brief, branch, approvals, and rollout.

### Minimum-change directive controls Stage A

Read `docs/chains/rh/minimal-contract-change-reassessment.md` from the current
integration branch. If the S4 worktree predates that document, record the
amendment as a post-launch input and ask the owner how the evidence record
should cite the integrated directive. Do not copy or merge files blindly.

Stage A must compare:

1. current Deleverage/Delta/Teller source with cooldown fixed at zero and
   nonzero activation prohibited;
2. current source with an accepted future-enable risk;
3. a smaller configuration or operational mitigation; and
4. the proposed shared source change.

Cleaning up the duplicated constant, correcting its comment, or improving
future portability is not by itself sufficient to authorize Stage B.

## Worktree bootstrap

After all launch gates above close, the fresh agent must:

1. Start from `/Users/wigglez/dev/ripe-protocol`.
2. Verify that:
   - the integration worktree is clean;
   - `rh` resolves to the owner-approved post-S3 commit;
   - this brief exists in that commit;
   - S1, S2, and reviewed S3 are ancestors of `rh`;
   - no H-01 dependency change is floating beneath the selected Stage B order;
   - the branch and path below do not exist; and
   - no active branch overlaps Stage A or proposed Stage B ownership.
3. Record:
   - the full starting commit;
   - the integrated S3 implementation and approval commits;
   - SHA-256 hashes of this brief,
     `docs/chains/rh/shared-block-clock-specification.md`,
     `docs/chains/rh/block-clock-validation-plan.md`,
     `contracts/core/Deleverage.vy`,
     `contracts/config/SwitchboardDelta.vy`,
     `contracts/core/Teller.vy`, their generated ABIs, and the S2 inventory;
   - installed Vyper, Titanoboa, and pytest versions;
   - S1/S2 counts and results; and
   - the selected H-01/S4 order.
4. Confirm that branch `rh-track-6-s4-deleverage-cooldown` and path
   `/Users/wigglez/dev/ripe-protocol-track-6-s4-deleverage-cooldown` do not
   already exist. If either exists, stop. Do not reuse, delete, reset, or
   overwrite it.
5. Create the isolated worktree:

   ```bash
   git -C /Users/wigglez/dev/ripe-protocol worktree add \
     -b rh-track-6-s4-deleverage-cooldown \
     /Users/wigglez/dev/ripe-protocol-track-6-s4-deleverage-cooldown \
     rh
   ```

6. Verify the new worktree's branch, commit, clean status, hashes, runtime
   versions, and S1/S2 baseline.
7. Perform every subsequent command and edit inside the S4 worktree.

Do not modify or commit from the integration worktree.

## Required reading

Read and verify the integrated versions of:

### Program and Track 6 authority

- `docs/chains/rh-summary.md`
- `docs/chains/rh/minimal-contract-change-reassessment.md`
- `docs/chains/rh/component-matrix.md`, especially CM-014, CM-034, and CM-044
- `docs/chains/rh/block-number-inventory.md`, especially BN-012
- `docs/chains/rh/shared-block-clock-specification.md`, especially BN-012,
  S4, and the decision register
- `docs/chains/rh/block-clock-validation-plan.md`, especially BN-012 and the
  repeated/boundary profiles
- `docs/chains/rh/track-6-s1-clock-harness.md`
- `docs/chains/rh/track-6-s2-checked-clock-inventory.md`
- `docs/chains/rh/track-6-s3-lootbox-floor.md`
- integrated `docs/chains/rh/lootbox-floor-implementation-record.md`
- `docs/chains/rh/robinhood-deployment-support-specification.md`, including
  reservation `0020_Track6S4DeleverageCooldown.py`
- `docs/chains/rh/robinhood-deployment-validation-plan.md`
- `docs/chains/rh/track-7-h1-dependency-security-preflight.md`

### Ripe production and test surfaces

- `contracts/core/Deleverage.vy`
- `contracts/config/SwitchboardDelta.vy`
- `contracts/core/Teller.vy`
- `contracts/core/TellerUtils.vy`
- `contracts/modules/Addys.vy`
- `tests/conf_core.py`
- `tests/core/deleverage/test_deleverage_for_withdrawal.py`
- `tests/core/deleverage/test_deleverage_permissions.py`
- `tests/config/test_switchboard_delta.py`
- `tests/core/teller/test_teller_withdraw.py`
- `tests/core/teller/test_teller_rebalance.py`
- `tests/clock/test_clock_profiles.py`
- `config/block-clock-inventory.json`
- `scripts/check_block_clock_inventory.py`
- `tests/inventory/test_block_clock_inventory.py`
- `scripts/abis/Deleverage.json`
- `scripts/abis/SwitchboardDelta.json`
- `scripts/abis/Teller.json`
- every historical Base migration that deploys or replaces Deleverage,
  SwitchboardDelta, or Teller
- `migration_history/base-mainnet/v1/current-manifest.json`

### Read-only downstream compatibility input

At planning time, local Underscore commit
`5b0a6354caf102865ab173aaa0c6bab0b492030f` contains the only production-source
call sites found for `deleverageForWithdrawal`:

- `/Users/wigglez/dev/underscore-protocol/contracts/vaults/modules/LevgVaultWallet.vy`
- `/Users/wigglez/dev/underscore-protocol/contracts/mock/MockRipe.vy`
- relevant leverage/redemption tests under
  `/Users/wigglez/dev/underscore-protocol/tests/vaults/leverage/`

The Underscore worktree contains unrelated user changes at planning time. Do not
edit, clean, stage, reset, or rely on its working-tree files. Read committed
content with `git show <recorded-commit>:<path>`, record the full commit, and
re-run a fixed-string search for every call site. If its committed HEAD changed,
record the delta. Stop before making a compatibility recommendation if the
relevant committed source is unavailable or ambiguous.

The current Ripe source contains no production call to
`deleverageForWithdrawal`; its direct calls are in tests. The current
Underscore `LevgVaultWallet` calls the four-argument Ripe function in two
redemption/withdrawal paths. This verified fact overrides any assumption that
Teller is already the sole coordinator.

## Controlling constraints

- Default to unchanged Deleverage, SwitchboardDelta, and Teller source with
  `deleverageCooldown = 0`. Production changes require an owner-approved
  necessity finding after the lost pacing protection is explained.
- Preserve one canonical Ripe source for Base, Robinhood, and future EVM
  chains. No Robinhood-specific contract, branch, address check, or `chain.id`
  conditional is allowed.
- Do not preserve the current repeated-number bypass merely because Base
  usually advances `NUMBER` between transactions.
- Do not treat every currently permitted Ripe or Underscore address as an
  authorized multi-leg coordinator.
- Preserve zero cooldown as disabled unless the owner explicitly chooses
  otherwise.
- Preserve exact cooldown expiry at
  `currentNumber == lastNumber + cooldown`.
- Preserve the near-redemption safety escape unless security review selects a
  narrower, proved replacement.
- Keep `lastDeleverageBlock` as the governing persistent checkpoint unless a
  separately approved design proves migration and storage safety.
- A changed governed cooldown applies immediately to an existing checkpoint,
  matching current storage semantics, unless the owner explicitly changes that
  policy.
- One authoritative maximum belongs to Deleverage. SwitchboardDelta may
  preflight against the current Deleverage getter but cannot own a second cap.
- Queue-time Switchboard validation does not replace execution-time
  enforcement by the current registered Deleverage.
- Do not infer that the four-argument ABI can be removed, retained, or wrapped.
  Its compatibility treatment is an owner/security decision informed by the
  downstream caller trace.
- Do not change deleverage formulas, trusted-caller policy, liquidation,
  redemption thresholds, minimum-deleverage logic, buffer logic, asset
  ordering, token routing, PSM behavior, or unrelated Teller withdrawals.
- Do not rewrite historical migrations or migration history.
- Recommendations and test candidates are not live parameter approvals.

## Stage A exact ownership

Stage A may add only:

- `docs/chains/rh/deleverage-cooldown-security-decision.md`.

It must not edit any existing file, requirement, source, ABI, test, inventory,
migration, manifest, or external repository.

The decision record must be committed to the S4 branch and presented at the
mandatory checkpoint. Then stop.

## Stage A — security and compatibility decision

### Phase A0: test whether S4 is necessary

Before designing a maximum or context, prove from source, defaults, migrations,
manifests, and dated read-only evidence:

- the initial and observed cooldown posture;
- whether any selected Robinhood launch flow requires a nonzero cooldown;
- what exact exploit or abuse zero cooldown permits;
- which existing authorization, nonreentrancy, liquidation, debt, limit, and
  pause controls reduce that risk;
- whether a manifest assertion and governance prohibition on nonzero activation
  are sufficient for launch;
- what monitoring or operational response can reduce residual risk without a
  contract change; and
- why new Deleverage/Delta/Teller code would create less total risk than
  accepting zero cooldown.

If the owner accepts zero cooldown after reviewing this analysis, recommend:

- unchanged production contracts and ABIs;
- no S4 migration;
- explicit Robinhood zero-value configuration/assertions;
- an activation gate requiring a later dedicated security review; and
- closure of S4 with no Stage B or Stage C.

### Phase A1: freeze and reproduce the baseline

Record:

- repository, branch, full commit, clean status, and local/UTC timestamps;
- S3 and S2 integration/approval commits;
- source, ABI, inventory, compiler-input, and dependency hashes;
- compiler/runtime versions;
- current constructor signatures and every deployment call site;
- direct block-number and cadence-candidate counts;
- baseline targeted, S1, S2, and full-suite results; and
- the exact Underscore committed input and fixed-string call-site results.

Verify from source:

- both `MAX_COOLDOWN_BLOCKS` constants equal `7_200`;
- Deleverage and SwitchboardDelta validate independently;
- fresh Deleverage storage initializes `deleverageCooldown` to `0`;
- `lastDeleverageBlock` uses `0` as the unset sentinel;
- a successful withdrawal deleverage writes the current `block.number`;
- the cooldown currently blocks only when `block.number > lastBlock` and
  `block.number < lastBlock + cooldown`;
- equality at `lastBlock + cooldown` is eligible;
- near-redemption may bypass an active cooldown;
- Deleverage currently accepts registered Ripe and qualifying Underscore
  callers, not only Teller;
- Ripe Teller currently has no production call to
  `deleverageForWithdrawal`;
- Underscore `LevgVaultWallet` currently uses the four-argument ABI in two
  committed paths;
- the Underscore redemption-preparation call supplies `_vaultId = 0`, which
  Deleverage resolves through `getFirstVaultIdForAsset`; and
- source-backed deployment and migration evidence maps SwitchboardDelta to
  Switchboard registry ID `4`. If the integrated evidence does not establish
  that mapping, record the ambiguity and stop before using the ID in a rollout
  plan.

Distinguish code facts, dated live evidence, test behavior, and assumptions.
The Track 6 read-only Base result that observed configured cooldown `0` is dated
evidence, not a permanent onchain fact.

### Phase A2: map the real call and state-transition graph

For each known or plausible flow, document:

- top-level caller and user;
- every Ripe/Underscore contract crossed;
- whether one or multiple collateral legs can occur;
- whether the calls occur in one top-level EVM transaction;
- the caller seen by Deleverage;
- which leg writes `lastDeleverageBlock`;
- whether the flow depends on the current same-number bypass;
- whether transient `didHandleAsset`/`didHandleVaultId` state affects it;
- how a revert unwinds context and deleverage state;
- whether the flow exists on Base, Robinhood, or both; and
- compatibility under every proposed ABI/context option.

At minimum cover:

- one direct Ripe/Teller-style test call;
- `Teller.withdraw`;
- `Teller.withdrawMany`;
- `Teller.rebalance`;
- Underscore redemption preparation with `_vaultId = 0` and the resulting
  `getFirstVaultIdForAsset` resolution;
- Underscore vault-token collateral withdrawal;
- two distinct assets for one user;
- the same asset/vault repeated;
- two users in one top-level call;
- delegated callers;
- registered Ripe Departments;
- registered Underscore addresses;
- arbitrary contracts and EOAs; and
- registry replacement during a pending governance action.

Do not invent a Teller integration that does not exist. If the desired future
coordinator is Teller, state the new production behavior and downstream changes
that would be required.

### Phase A3: define the threat model

The decision record must analyze:

- independent transactions sharing one EVM `NUMBER`;
- a bundle or sequencer batch containing many transactions at one number;
- repeated calls in one transaction;
- a malicious registered Ripe or Underscore caller;
- cooldown griefing in which an authorized caller performs a minimal successful
  deleverage against a victim solely to write `lastDeleverageBlock` and deny or
  delay the victim's later withdrawal;
- forged, guessed, copied, or zero context identifiers;
- cross-user and cross-coordinator context substitution;
- context reuse after completion or in a later transaction;
- nested context opening and reentrancy;
- callback-driven calls during token, vault, PriceDesk, CreditEngine, PSM, or
  Teller interactions;
- a failed middle leg followed by recovery;
- near-redemption state manufactured between legs;
- zero/nonzero cooldown transitions;
- maximum reduction or increase during an existing window;
- registry replacement between queue and execution;
- arithmetic at unset, exact-expiry, and maximum values; and
- a Base upgrade that resets unenumerable per-user checkpoints.

For every threat, identify:

- protected asset or invariant;
- required attacker authority;
- current behavior;
- proposed behavior;
- residual risk;
- test or proof;
- rollout implication; and
- security owner.

### Phase A4: compare context architectures

Analyze at least:

1. **No exception:** every later call, including same-transaction legs, obeys
   cooldown unless near redemption.
2. **Deleverage-managed explicit context:** an approved coordinator opens a
   user/caller-bound transient context and supplies an opaque ID to each leg.
3. **Coordinator-managed transient scope:** the approved coordinator maintains
   transient flow state and calls a context-aware Deleverage entry point.
4. **Backward-compatible wrapper plus new context entry point:** retain the
   four-argument function as a no-context path and add a separately named or
   default-argument context path.
5. **Coordinated cross-repository ABI replacement:** change Ripe and
   Underscore together under an explicit mixed-version rollout plan.

For each option, compare:

- independent same-number protection;
- authorization source;
- user/caller/context binding;
- transaction-only lifetime;
- nesting and replay behavior;
- four-argument ABI compatibility;
- Ripe Teller changes;
- Underscore source/deployment changes;
- mixed old/new version safety;
- bytecode and migration surface;
- testing feasibility under S1; and
- rollback before and after registry changes.

Reject:

- the current `block.number > lastBlock` exception;
- `tx.origin`;
- `msg.sender` alone as proof of one multi-leg flow;
- a reusable persistent bypass nonce;
- an unbound boolean;
- a context open to every valid Ripe or Underscore address;
- duplicate maximum constants;
- a context that survives the transaction; and
- a chain-specific implementation.

### Phase A5: compare maximum and activation policies

Analyze:

| Policy | Base immutable maximum | Robinhood immutable maximum | Intent |
| --- | ---: | ---: | --- |
| Preserve enforced Base ceiling | `7_200` | `1_200` | Approximately four hours under the approved planning cadence |
| Preserve the source comment's wall-time intent | `43_200` | `7_200` | Approximately one day |
| Another value | owner supplied | derived only after cadence approval | Requires separate evidence and approval |

The analysis must distinguish:

- immutable maximum;
- initial stored cooldown;
- later governed cooldown;
- activation approval; and
- S6 parameter-manifest ownership.

The current initial value is `0`. S4 must not activate a nonzero cooldown merely
to demonstrate the new maximum. The decision record should recommend whether
S4 preserves zero at deployment and leaves any nonzero Base/Robinhood value to
S6 or a later governance release.

For the maximum, evaluate:

- security benefit from pacing;
- withdrawal/deleverage availability;
- governance authority expansion;
- current Base ceiling preservation;
- stale comment intent;
- effect on an already-recorded checkpoint;
- jump behavior; and
- the fact that dated live Base evidence observed a configured value of `0`.

### Phase A6: design mixed-version and state migration

For Deleverage, SwitchboardDelta, Teller if selected, and every approved
external coordinator, construct an old/new compatibility matrix:

| Caller/coordinator | Old Deleverage | New Deleverage |
| --- | --- | --- |
| old four-argument caller | required result | required result |
| new context-aware caller | required result | required result |
| arbitrary valid Ripe caller | required result | required result |
| arbitrary valid Underscore caller | required result | required result |

Address:

- Deleverage RipeHq registry ID 18;
- Teller RipeHq registry ID 17 if its source changes;
- SwitchboardDelta Switchboard registry ID 4;
- governed values `minDeleverageBps`, `deleverageBuffer`,
  `deleverageCooldown`, and `underscoreSafeSpreadBps`;
- the unenumerable `lastDeleverageBlock` mapping;
- pause and governance state;
- pending Delta actions;
- old/new ABI and code hashes;
- timelock ordering;
- safe mixed-version calls;
- temporary drift owner, deadline, and closure proof;
- rollback while old contracts remain usable; and
- forward remediation after registry changes.

A plan that requires three registry changes to be atomic must prove how the
actual timelocks and registries provide atomicity. Otherwise specify a
compatible staged order and the safe posture between steps.

### Phase A7: produce an implementation and validation split

Propose the smallest Stage B file set and exact tests for the selected options.
Separate:

- mechanical authoritative-maximum work;
- context/ABI work;
- downstream compatibility work;
- artifact/ABI generation;
- Base convergence planning; and
- S2 inventory reconciliation.

If the maximum can safely land separately but context cannot, state whether
splitting S4 reduces or increases mixed-version risk. Do not split an atomic
safety group merely to make the first PR smaller.

## Mandatory checkpoint 0: owner and security decisions

Create and commit
`docs/chains/rh/deleverage-cooldown-security-decision.md`, then stop.

The record must contain:

- frozen inputs and baseline results;
- complete Ripe and Underscore call graph;
- threat model and residual-risk table;
- context-option comparison;
- maximum/activation comparison;
- ABI and mixed-version matrix;
- Base state and rollout analysis;
- proposed exact Stage B ownership;
- proposed test matrix;
- H-01 sequencing consequence;
- recommended decisions with rationale;
- dissenting or rejected options;
- open blockers; and
- a clearly marked approval record.

The checkpoint must ask the owner and security reviewer to decide:

0. **Implementation necessity:** accept unchanged source with zero cooldown and
   no pacing protection, or reject that risk and authorize consideration of a
   production change. If unchanged source is accepted, decisions 1–11 are
   deferred and Stage B does not exist for the initial release.
1. **Maximum wall-time intent:** four hours, one day, or another exact duration.
2. **Per-chain immutable values:** exact Base and Robinhood maxima and the
   cadence approval supporting them.
3. **Activation posture:** preserve initial `0`, or approve another exact
   initial/governed value and its owning release.
4. **Coordinator set:** Teller, an identified Underscore coordinator, another
   exact contract, no coordinator, or a combination.
5. **Context architecture:** exact option, open/close authority, transient
   location, ID type, user/caller binding, nesting, and replay policy.
6. **Near-redemption policy:** preserve the independent safety bypass or adopt
   a separately proved restriction.
7. **ABI compatibility:** treatment of the four-argument entry point and
   mixed old/new callers.
8. **Cross-repository policy:** whether an Underscore change is required and,
   if so, the separate brief, owner, sequence, and deployment gate.
9. **Base live-version policy:** exact component set, staged/atomic order,
   temporary-drift bounds, state preservation, rollback, and no permanent
   divergence.
10. **H-01/S4 order:** exact dependency baseline for Stage B and mandatory
    revalidation.
11. **Stage B file set and atomicity:** whether mechanical maximum and context
    changes land together or as separately reviewed releases.

No response means unchanged source, zero cooldown, and no production edit. The
Stage A author may recommend but may not select these decisions.

## Proposed Stage B ownership

This section is a planning ceiling, not authorization. Checkpoint 0 must approve
the exact subset before Stage B.

### Production, tests, ABI, and evidence

Stage B may change only an approved subset of:

- `contracts/core/Deleverage.vy`;
- `contracts/config/SwitchboardDelta.vy`;
- `contracts/core/Teller.vy`, only if the approved coordinator design requires
  a real Teller change;
- `tests/conf_core.py`, only for an approved Deleverage constructor argument;
- `tests/core/deleverage/test_deleverage_for_withdrawal.py`;
- `tests/core/deleverage/test_deleverage_permissions.py`, only for caller and
  context authorization;
- `tests/config/test_switchboard_delta.py`;
- `tests/core/teller/test_teller_withdraw.py`, only if Teller changes;
- `tests/core/teller/test_teller_rebalance.py`, only if Teller/rebalance
  behavior changes;
- generated `scripts/abis/Deleverage.json`;
- generated `scripts/abis/SwitchboardDelta.json`, only if its external ABI
  actually changes;
- generated `scripts/abis/Teller.json`, only if Teller's external ABI changes;
  and
- new `docs/chains/rh/deleverage-cooldown-implementation-record.md`.

If the selected design needs another Ripe file, stop and obtain a reviewed
brief amendment. Do not edit the Underscore repository under S4.

### Stage C checked-inventory reconciliation

Only after mandatory reviewer gate 1 may Stage C also change:

- `config/block-clock-inventory.json`;
- `scripts/check_block_clock_inventory.py`, only as narrowly required to
  recognize the approved generic maximum/context surface; and
- `tests/inventory/test_block_clock_inventory.py`, only for deterministic
  inventory and mutation expectations.

The implementation author may not self-approve a semantic inventory change.

### Prohibited files and actions

Do not change:

- `contracts/config/DefaultsBase.vy`;
- future `contracts/config/DefaultsRobinhood.vy`;
- MissionControl parameter structs or storage;
- `config/BluePrint.py`;
- parameter/report-generation files;
- historical or proposed migrations;
- migration history or committed manifests;
- H-01 dependencies or tests;
- S1 utilities or clock-profile definitions;
- another contract ABI;
- external Underscore source or tests;
- CI;
- `docs/chains/rh-summary.md`; or
- another track's deliverables.

## Stage B — approved production implementation

Do not begin until checkpoint 0 closes and its exact decisions are recorded in
this brief or the approved decision record.

### Phase B1: implement one authoritative maximum

Subject to the approved design:

1. remove both `MAX_COOLDOWN_BLOCKS` constants;
2. add `_maxDeleverageCooldown` to the Deleverage constructor;
3. require the immutable maximum to be nonzero and not
   `max_value(uint256)`;
4. store it as an immutable with an unambiguous chain-neutral name;
5. expose `maxDeleverageCooldown()`;
6. make `Deleverage.setDeleverageCooldown` the execution-time authority for
   `value <= maximum`;
7. make `SwitchboardDelta.setDeleverageCooldown` query the current registered
   Deleverage getter before queuing; and
8. retain Deleverage validation at execution if the registry target or maximum
   changed while an action was pending.

Do not duplicate the immutable value in Delta, Teller, defaults, or a chain
conditional. Zero governed cooldown remains valid unless checkpoint 0 says
otherwise.

### Phase B2: implement only the approved context

The implementation must prove:

- every independent later call within an active nonzero cooldown is blocked
  even when `NUMBER` repeats;
- only the exact approved coordinator can open/use a context;
- context is bound to the intended user and caller/flow;
- context exists only for one top-level transaction;
- a follow-up leg cannot forge, copy, substitute, or replay it;
- nesting follows the approved policy;
- a failed/reverted flow leaves no reusable authority;
- no-context calls retain approved first-call, expiry, zero-cooldown, and
  near-redemption behavior; and
- old/new ABI behavior matches the approved compatibility matrix.

Do not add a generic privileged cooldown bypass. Context authorizes only the
reviewed multi-leg continuation.

### Phase B3: preserve cooldown arithmetic and safety behavior

For a nonzero cooldown and initialized checkpoint, the default rule must be:

```text
currentNumber < lastNumber + cooldown => blocked
currentNumber == lastNumber + cooldown => eligible
```

Apply the approved context and near-redemption exceptions explicitly rather
than through number identity. Preserve:

- zero cooldown disabled behavior;
- unset checkpoint behavior;
- successful-call checkpoint write;
- current immediate effect of a governed cooldown change;
- existing deleverage formula and caps; and
- all unrelated permissions, events, storage, and external behavior.

Use checked arithmetic and prove the approved maximum cannot create an unsafe
sum under realistic EVM number bounds. Do not silently saturate or wrap.

### Phase B4: update fixtures and tests

The normal Base fixture must use the approved Base immutable maximum and retain
stored cooldown `0` unless activation was separately approved. Add focused
helpers for Robinhood maximum cases without changing unrelated global fixture
semantics.

#### Maximum and governance matrix

For both approved chain profiles cover:

- constructor maximum `0`;
- constructor maximum `max_value(uint256)`;
- governed cooldown `0`;
- maximum minus one;
- exact maximum;
- maximum plus one;
- Delta queue-time rejection;
- Deleverage execution-time rejection;
- current Deleverage registry target changed after queue;
- current target has a lower maximum at execution;
- pending-action cancel and expiry; and
- event and stored-value parity.

#### Cooldown boundary profiles

Using S1, cover:

- first successful deleverage;
- repeated `NUMBER` independent call;
- `last + cooldown - 1`;
- exact `last + cooldown`;
- `last + cooldown + 1`;
- representative `+2/+4` jumps;
- synthetic `+60` stress;
- boundary skip from before to after expiry;
- cooldown set to zero during a window;
- cooldown increased/decreased during a window; and
- two users at the same number.

#### Context security matrix

Cover:

- approved multi-leg, distinct-asset continuation;
- same asset/vault repetition under existing transient handling;
- unauthorized valid Ripe Department;
- unauthorized Underscore address;
- an authorized caller attempting a minimal successful deleverage solely to
  start a victim's cooldown;
- arbitrary contract and EOA;
- random, zero, stale, and copied IDs;
- wrong user;
- wrong coordinator/caller;
- nested opening;
- reentrant callback attempt;
- context use after explicit close;
- context use after top-level return in a later transaction;
- reverted middle leg;
- two contexts/users in one transaction if approved;
- no-context four-argument path if retained; and
- old/new mixed-version fixtures.

#### Near-redemption matrix

Prove:

- healthy position remains cooldown-blocked;
- genuinely near-redemption projected post-withdrawal may use only the approved
  bypass;
- a forged context cannot claim near-redemption;
- context does not broaden the threshold;
- threshold/minimum/buffer branches remain independent; and
- price or collateral changes used in the test actually establish the intended
  precondition.

#### Downstream compatibility

Create only approved Ripe-side mocks/fixtures. Prove the committed
four-argument Underscore call shape has the selected compatibility result.
Include an explicit case where `_vaultId = 0`, prove that the intended vault is
resolved through `getFirstVaultIdForAsset`, and confirm that the selected
ABI/context design preserves that zero-means-resolve behavior.
If true end-to-end evidence requires an Underscore change, stop and route it to
the separately approved cross-repository slice.

### Phase B5: regenerate and compare ABIs

Generate ABIs into disposable directories first.

For Deleverage, record:

- constructor maximum argument and exact position;
- `maxDeleverageCooldown()` signature;
- context-aware entry points;
- four-argument compatibility result;
- unchanged unrelated functions/events; and
- normalized old/new diff.

SwitchboardDelta's embedded Deleverage interface changes runtime code but need
not change SwitchboardDelta's external ABI. Do not commit a byte-identical ABI.
Apply the same rule to Teller: update its ABI only for an approved external
surface change.

Never hand-edit ABI JSON.

### Phase B6: artifact and implementation record

Create `docs/chains/rh/deleverage-cooldown-implementation-record.md`.

Record:

- planning, launch, decision, implementation, and approval commits;
- compiler and dependency versions;
- exact changed files;
- source/compiler-input hashes;
- old/new normalized ABI hashes and diffs;
- old/new creation and runtime bytecode hashes for every changed contract;
- Base and Robinhood Deleverage constructor inputs and runtime hashes;
- proof of identical canonical source/compiler inputs across chain profiles;
- expected immutable-driven Deleverage runtime difference;
- S1/S2 and targeted/full test results;
- current manifest addresses and registry IDs;
- dated live Base code/config evidence when separately approved;
- downstream Underscore commit/call-site evidence;
- selected decisions and approval provenance;
- S2 drift expected before reconciliation; and
- every unresolved deployment, external, audit, or rollout gate.

Do not claim identical deployed runtime where immutable values differ.

### Phase B7: specify, but do not execute, convergence

The record must provide a forward rollout for Base and an initial-deployment
assertion for Robinhood.

For Base address:

- Deleverage registry ID 18;
- Teller registry ID 17 if changed;
- SwitchboardDelta registry ID 4 within Switchboard;
- every approved external coordinator/dependency;
- all current governed Deleverage values;
- unenumerable `lastDeleverageBlock`;
- current and pending Delta actions;
- pause/governance state;
- timelock order;
- safe mixed-version windows;
- old/new code and ABI hashes;
- rollback and forward remediation; and
- temporary drift owner/deadline/closure.

Do not claim the per-user checkpoint mapping can be snapshotted from committed
manifests. If live cooldown is nonzero at rollout, define a conservative
pause/wait/reset policy and obtain separate approval.

For Robinhood, preserve Track 7 reservation
`0020_Track6S4DeleverageCooldown.py` as a predeployment artifact assertion.
Do not create or execute that migration in S4.

## Mandatory reviewer gate 1: production and security

After Stage B:

1. commit only the approved Stage B files;
2. run all targeted tests that can pass before inventory reconciliation;
3. run S2 and record only the expected reviewed drift;
4. provide source, tests, ABIs, artifacts, implementation record, downstream
   compatibility evidence, and rollout plan to an independent reviewer; and
5. stop.

The reviewer must verify:

- every checkpoint-0 decision is implemented exactly;
- no current/alternate coordinator gained a generic bypass;
- repeated-number independent calls are blocked;
- authorized multi-leg behavior is real and narrowly scoped;
- downstream compatibility evidence is honest;
- maximum and execution-time validation are authoritative;
- Base/Robinhood artifacts are reproducible;
- historical migrations/history are unchanged;
- convergence does not assume impossible atomicity or enumerable mappings;
- S2 failed only for the approved semantic/source delta; and
- no unrelated behavior or file changed.

No Stage C inventory edit is allowed until the reviewer or owner supplies
immutable approval provenance for the exact Stage B implementation.

## Stage C — checked-inventory reconciliation

After gate 1:

- remove only obsolete duplicate `MAX_COOLDOWN_BLOCKS` candidates;
- add the approved generic immutable/getter/context cadence candidates;
- preserve BN-012 identity and all unrelated IDs;
- update content hashes for every changed production file;
- preserve direct 100/95/17 counts unless the checker proves a separately
  reviewed reason to change them;
- record the gate-1 approval commit as semantic provenance;
- update deterministic mutation fixtures;
- prove deletion/renaming/movement of the authoritative maximum is detected;
- prove reintroducing a duplicate cap fails; and
- do not broaden an ignore or regex to hide the new surface.

The final checker output must distinguish:

- unchanged direct `block.number` inventory, unless reviewed source mechanics
  require an exact change;
- the removed duplicate maximum;
- the new authoritative maximum/context surface;
- unchanged unrelated timestamp/seconds/mixed-clock records; and
- new production content hashes.

## Mandatory reviewer gate 2: merge readiness

Before merge, an independent security/Track 6 reviewer must inspect:

- the complete branch diff;
- checkpoint-0 decisions and provenance;
- Stage B and inventory approval commits;
- source and ABIs;
- compiler/runtime and artifact hashes;
- downstream compatibility evidence;
- Base/Robinhood clock-profile tests;
- Base convergence and rollback;
- S1/S2 and full-suite results;
- changed-file scope and whitespace; and
- merge-base/freshness against `rh`.

Any production edit reopens gate 1. Any post-review test, ABI, inventory, or
record change reopens the relevant review scope. Only the owner merges and
pushes.

## Cross-track interface

- **S1:** use the integrated exact clock controller. Do not change profiles or
  patch mechanics for S4.
- **S2:** consume post-S3 inventory and use the same two-gate semantic
  reconciliation process. Do not self-approve.
- **S3:** must be integrated first. S4 may not restamp or overwrite S3
  provenance.
- **S5:** owns the Ledger guard. Do not bundle another same-number security
  problem merely because both involve repeated `NUMBER`.
- **S6:** owns final per-chain governed cooldown values, defaults, and the
  broader cadence basis. S4 supplies only the approved maximum interface and
  zero/default behavior unless checkpoint 0 explicitly says otherwise.
- **Track 7:** owns migration namespace, execution, manifests, and live
  rehearsal. S4 supplies artifact assertions and a convergence plan.
- **H-01:** controls the dependency profile and mandatory revalidation order.
- **Track 8:** owns vault-accounting changes. Do not alter withdrawal
  settlement/accounting as part of cooldown work.
- **Underscore:** read-only compatibility input. Any source/deployment change
  is a separate cross-repository track.

Record a collision and stop before editing another owner's file.

## Approval and safety boundaries

### Stage A agent may

- inspect Ripe source, history, manifests, tests, and integrated documents;
- inspect only committed Underscore source/history read-only;
- run existing local tests and compilers;
- create and commit the one Stage A decision record; and
- recommend exact options.

### Fresh approval is required before

- beginning Stage B or Stage C;
- selecting any checkpoint-0 decision;
- changing production source, tests, ABI, inventory, dependencies, or
  generated output;
- adding or removing a coordinator;
- changing the four-argument ABI;
- editing or testing against a modified Underscore checkout;
- creating a cross-repository branch;
- using a live RPC or explorer;
- accessing a secret;
- creating/editing a migration or manifest;
- deploying, verifying, registering, pausing, configuring, signing, or
  broadcasting;
- contacting an external party;
- publishing the branch; or
- ticking `docs/chains/rh-summary.md`.

## Stop conditions

Stop and report if:

- S3 is not reviewed, integrated, or reconciled in S2;
- the H-01/S4 order is unresolved before Stage B;
- Ripe or Underscore call sites cannot be enumerated;
- the coordinator or four-argument ABI policy remains ambiguous;
- any checkpoint-0 decision is missing;
- a proposed context can be forged, substituted, nested unexpectedly, or
  reused;
- independent same-number transactions can bypass a nonzero cooldown;
- near-redemption safety cannot be preserved or deliberately replaced;
- a maximum exists in more than one contract;
- Delta queue and Deleverage execution can disagree unsafely;
- a new constructor or ABI cannot coexist with the approved rollout order;
- Base convergence assumes atomic registry changes that cannot be executed;
- per-user checkpoints must be enumerated to migrate safely;
- an Underscore edit is required without a separate approved track;
- S1 or S2 is red on the untouched launch baseline;
- S2 drift exceeds the approved S4 change;
- artifact builds are not reproducible;
- a historical migration/history file appears to require editing;
- a test must be skipped, weakened, or made environment-dependent;
- another branch owns an S4 file; or
- any live/state-changing action would be required.

A blocked result is preferable to an implicit privilege or broken downstream
flow.

## Validation

### Stage A baseline

Run on the untouched post-S3 launch commit:

```bash
PYTHONPATH=. pytest -q tests/core/deleverage/test_deleverage_for_withdrawal.py
PYTHONPATH=. pytest -q tests/core/deleverage/test_deleverage_permissions.py
PYTHONPATH=. pytest -q tests/config/test_switchboard_delta.py
PYTHONPATH=. pytest -q tests/core/teller/test_teller_withdraw.py
PYTHONPATH=. pytest -q tests/core/teller/test_teller_rebalance.py
PYTHONPATH=. pytest -q tests/clock/test_clock_profiles.py
PYTHONPATH=. python scripts/check_block_clock_inventory.py --check
PYTHONPATH=. pytest -q tests/inventory/test_block_clock_inventory.py
PYTHONPATH=. pytest --collect-only -q
PYTHONPATH=. pytest -q
git diff --check
```

Also:

- [ ] Confirm only the Stage A decision record changed.
- [ ] Confirm committed Underscore source was inspected without modifying its
  worktree.
- [ ] Confirm every Ripe and Underscore caller is listed.
- [ ] Confirm every threat and option has a disposition.
- [ ] Confirm all eleven checkpoint decisions remain visibly pending.
- [ ] Record commands, versions, counts, durations, hashes, and failures.

If a baseline failure exists, reproduce it from the untouched launch commit and
separate it from S4.

### Stage B before reviewer gate 1

Run:

```bash
PYTHONPATH=. pytest -q tests/core/deleverage/test_deleverage_for_withdrawal.py
PYTHONPATH=. pytest -q tests/core/deleverage/test_deleverage_permissions.py
PYTHONPATH=. pytest -q tests/config/test_switchboard_delta.py
PYTHONPATH=. pytest -q tests/core/teller/test_teller_withdraw.py
PYTHONPATH=. pytest -q tests/core/teller/test_teller_rebalance.py
PYTHONPATH=. pytest -q tests/clock/test_clock_profiles.py
PYTHONPATH=. python scripts/check_block_clock_inventory.py --check
git diff --check
```

S2 is expected to fail only for the planned, approved S4 cadence/content drift
before gate 1. Record every diagnostic; do not edit S2 yet.

### Final after Stage C

Run serially:

```bash
PYTHONPATH=. pytest -q tests/core/deleverage/test_deleverage_for_withdrawal.py
PYTHONPATH=. pytest -q tests/core/deleverage/test_deleverage_permissions.py
PYTHONPATH=. pytest -q tests/core/deleverage
PYTHONPATH=. pytest -q tests/config/test_switchboard_delta.py
PYTHONPATH=. pytest -q tests/core/teller/test_teller_withdraw.py
PYTHONPATH=. pytest -q tests/core/teller/test_teller_rebalance.py
PYTHONPATH=. pytest -q tests/clock/test_clock_profiles.py
PYTHONPATH=. python scripts/check_block_clock_inventory.py --check
PYTHONPATH=. pytest -q tests/inventory/test_block_clock_inventory.py
PYTHONPATH=. pytest --collect-only -q
PYTHONPATH=. pytest -q
git diff --check
```

Also:

- [ ] Confirm the exact changed-file set matches approved Stage B/C ownership.
- [ ] Confirm every historical migration and migration-history file is
  byte-identical to the launch commit.
- [ ] Confirm Defaults, parameters, reports, dependencies, CI, unrelated ABIs,
  external repositories, and the master checklist are unchanged.
- [ ] Confirm Base and Robinhood use identical canonical source and creation
  artifacts.
- [ ] Explain immutable-driven runtime differences.
- [ ] Confirm same-number independent calls fail and authorized contexts pass.
- [ ] Confirm exact expiry, zero cooldown, near-redemption, governance changes,
  and maximum boundaries.
- [ ] Confirm mixed-version and downstream compatibility evidence.
- [ ] Confirm S2 counts/provenance are reconciled.
- [ ] Confirm no secrets or raw live responses appear.
- [ ] Record every command, result, duration, baseline, decision, approval, and
  final commit.

## Completion reports

### Stage A handoff

Report:

- launch commit and exact changed file;
- frozen hashes and dependency/compiler versions;
- Ripe and Underscore call graph;
- threat and context-option conclusions;
- maximum/activation analysis;
- mixed-version and Base convergence risks;
- recommended decisions;
- all eleven owner/security questions;
- baseline validation results; and
- blockers.

Then stop. Do not state that S4 is implemented or complete.

### Final S4 handoff

After Stage B, Stage C, and both reviewer gates, report:

- planning, launch, decision, Stage B, approval, inventory, and final commits;
- exact changed files;
- checkpoint-0 decisions and provenance;
- compiler/runtime versions;
- constructor, context, and ABI diff;
- Base/Robinhood maximum and governed-value matrices;
- full context/security test matrix;
- source, ABI, creation-bytecode, and runtime hashes;
- current Base evidence or explicit blocker;
- Underscore compatibility evidence and separate-track status;
- Base rollout, mixed-version, state, rollback, and drift summary;
- S2 before/after diagnostics and reconciled counts;
- every validation command/result;
- both reviewer approvals;
- unresolved S6, H-01, Track 7, external, audit, and live-deployment gates; and
- which Track 6 S4 and Section 2 checklist items are eligible for owner review.

Do not edit or tick `docs/chains/rh-summary.md`. Source integration does not
authorize deployment, activate a nonzero cooldown, or close later launch gates.

## 30 July 2026 historical integration checkpoint

Corrected PR #61 entered `rh` at the then-current integration commit
`ad831669943ccfe7b9ed57454995dfce51630a66`, tree
`3467f4a75aa37203d615407d5baf9c5fc9035639`. The integrated full-payoff,
safe-conversion, and dust boundaries do not reopen the historical S4
zero-cooldown decision or activate Stage B/Stage C from this brief.

Robinhood `deleverageCooldown`, `fullPayoffBuffer`, `overageBps`,
`dustThreshold`, and `dustBps` remain zero. The latter four controls lack
machine-facing Robinhood parameter/planning representation; resolving that gap
is deployment-owner work under a separately authorized machine implementation
track. This append-only note changes none of the original conclusions above and
grants no migration,
deployment, configuration, activation, or release authority.
