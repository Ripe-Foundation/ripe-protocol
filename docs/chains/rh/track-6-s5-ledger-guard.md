# Track 6 S5: Portable User-Action Guard and State-Safe Rollout

**Status:** Draft for owner and security review; no implementation or kickoff is
authorized

**Prepared:** 24 July 2026

**Planning baseline:** `3e6e6f230169fc445d0b29454457480c62efd89a`

**Required launch baseline:** this brief must be reviewed and committed to `rh`.
Stage A may run while H-01 and S4 are in progress. Stage B remains blocked on
the reviewed H-01 dependency baseline, the reviewed S4 ownership decision, and
every owner/security decision in Checkpoint 0.

## Fresh-agent instruction

Treat this document as the task contract. Work only on Track 6 slice S5:
identify the security property intended by BN-002, select a chain-portable
replacement, and—only after explicit approval—implement that replacement
without losing or corrupting live Ledger accounting state.

S5 has three stages:

1. **Stage A — threat model and architecture decision:** repository-read-only
   analysis plus one decision record. No production contract, ABI, test,
   inventory, dependency, migration, or external-repository change is allowed.
2. **Stage B — production implementation:** blocked until the owner and an
   independent security reviewer approve every mandatory decision below,
   approve the exact file set, and close the H-01/S4 sequencing gates.
3. **Stage C — checked-inventory reconciliation:** blocked until an independent
   reviewer approves the Stage B production implementation and rollout record.

The safe result of Stage A may be **do not implement yet**. Do not infer the
threat model from the existing comment, treat the current guard as ordinary
reentrancy protection, or assume that replacing Ledger is safe merely because
RipeHq can register a new address.

Use branch `rh-track-6-s5-ledger-guard`. Commit Stage A to that branch and stop
at Checkpoint 0. Never push directly to or merge into `rh` or `master`; the
owner reviews and integrates the work.

This brief authorizes no live RPC, signer, transaction, deployment, registry
change, governance action, dependency change, external-repository write, or
external communication.

## Why this slice has a stronger gate

The current code calls BN-002 “one action per block,” and the existing Ledger
tests call it “Flash Loan Protection.” Neither label is a complete threat
model.

The actual behavior is:

- every successful Teller housekeeping call writes
  `Ledger.lastTouch[_user] = block.number`;
- when the governed flag is enabled, a higher-risk action for a user not
  classified as an Underscore wallet or vault rejects if **any** earlier
  housekeeping call for that user occurred at the same EVM `NUMBER`;
- a lower-risk touch is not checked, but it still arms the later rejection;
- a higher-risk touch followed by a lower-risk touch succeeds, but a later
  checked action in the same `NUMBER` rejects;
- Underscore-classified users skip the assertion but still write `lastTouch`;
  and
- a Robinhood repeated-number interval could extend that rejection across many
  otherwise independent transactions.

The implementation location also matters. Ledger is not a disposable guard
contract. It stores live protocol accounting for vault participation, debt,
borrowers, points and rewards, auctions, locks, bonds, bad debt, and other
system state. Much of that state is held in mappings that are not automatically
enumerable from the contract. Replacing the live Base Ledger with an empty
deployment would be a state-loss event, not a normal guard upgrade.

Therefore S5 must choose the protected threat and a state-safe architecture
before it edits production code.

## Hard launch and sequencing gates

### Stage A may begin from the reviewed post-S3 baseline

Do not create the S5 branch or worktree until:

- S3 has passed both reviewer gates and is integrated into `rh`;
- the S2 inventory on `rh` includes the reviewed S3 reconciliation;
- the S1/S2 validation passes on that integration baseline;
- this brief is reviewed and committed to that same or a later `rh` commit;
- the S5 branch and worktree path are unused; and
- no active branch owns the Stage A decision-record path.

Stage A is evidence-only and may proceed while H-01, S4, and Track 8 run. It
must record their exact current states rather than copying floating work.

### H-01 controls the Stage B dependency baseline

Stage B may not begin from H-01’s candidate lock or checkpoint evidence. H-01
must pass its mandatory reviewer gate and its approved dependency change must be
integrated into `rh`.

After H-01 integration, S5 must repeat:

- compiler and runtime version capture;
- contract compilation and artifact hashing;
- targeted tests;
- S1 profiles;
- S2 checked-inventory validation; and
- the full test suite.

S5 must not edit dependency files or weaken H-01’s exact-version assertions.

### S4 controls overlapping Teller and SwitchboardDelta ownership

S4 and S5 may both select changes to `Teller.vy`,
`SwitchboardDelta.vy`, their interfaces, ABIs, fixtures, or tests.

Stage A may analyze those surfaces in parallel, but:

- Checkpoint 0 must consume the latest reviewed S4 decision record;
- it must state whether S4 and S5 overlap by file, ABI, storage, migration,
  deployment order, or rollback boundary;
- Stage B may not begin while an unintegrated S4 implementation owns an S5
  production file;
- the safe default order is H-01, then S4, then S5; and
- any other order requires explicit owner approval plus both slices’
  independent reviewers confirming that the file and artifact boundaries do
  not conflict.

Do not merge two security mechanisms into one PR merely because both touch
Teller.

### Track 7 owns migration execution

Track 7 reserves `0030_Track6S5LedgerGuard.py` for the eventual Robinhood
migration. S5 may specify its required preconditions, assertions, order,
rollback boundary, and expected artifacts. S5 must not create or execute that
migration unless a later owner-approved implementation brief explicitly moves
the file into scope.

Historical Base migrations and committed migration manifests are immutable
evidence. Never edit them to make a new constructor, registration, or policy
appear retroactive.

### Underscore is read-only compatibility input

The Underscore repository may rely on the present exemption and may compose
Ripe Teller operations through Ripe Lego or wallet flows. S5 may read committed
Underscore source and tests. It must not edit, clean, reset, commit, push, or
deploy from that repository.

Any required Underscore change needs its own reviewed brief, branch, approvals,
and rollout.

## Worktree bootstrap

After the Stage A launch gates close, the fresh agent must:

1. Start from `/Users/wigglez/dev/ripe-protocol`.
2. Verify that:
   - the integration worktree is clean;
   - local `rh` and `origin/rh` resolve to the same owner-approved commit;
   - this brief exists in that commit;
   - S1, S2, and reviewed S3 are ancestors of `rh`;
   - H-01 and S4 states are recorded, without treating a floating branch as
     integration truth;
   - the branch and worktree path below do not exist; and
   - no active branch owns the Stage A decision-record path.
3. Record:
   - the full starting commit;
   - the integrated S1, S2, and S3 merge/approval commits;
   - the exact H-01, S4, Track 7, and Track 8 states;
   - SHA-256 hashes of this brief,
     `docs/chains/rh/shared-block-clock-specification.md`,
     `docs/chains/rh/block-clock-validation-plan.md`,
     `docs/chains/rh/block-number-inventory.md`,
     `docs/chains/rh/component-matrix.md`,
     `contracts/data/Ledger.vy`,
     `contracts/core/Teller.vy`,
     `contracts/core/TellerUtils.vy`,
     `contracts/data/MissionControl.vy`,
     `contracts/config/SwitchboardDelta.vy`,
     their generated ABIs, and the S2 inventory;
   - installed Python, Vyper, Titanoboa, and pytest versions;
   - S1/S2 counts and results; and
   - the current full-suite collected and passing counts.
4. Confirm that branch `rh-track-6-s5-ledger-guard` and path
   `/Users/wigglez/dev/ripe-protocol-track-6-s5-ledger-guard` do not already
   exist. If either exists, stop. Do not reuse, delete, reset, or overwrite it.
5. Create the isolated worktree:

   ```bash
   git -C /Users/wigglez/dev/ripe-protocol worktree add \
     -b rh-track-6-s5-ledger-guard \
     /Users/wigglez/dev/ripe-protocol-track-6-s5-ledger-guard \
     rh
   ```

6. Verify the new worktree’s branch, commit, clean status, hashes, runtime
   versions, S1/S2 baseline, and full-suite baseline.
7. Perform every subsequent command and edit inside the S5 worktree.

Do not modify or commit from the integration worktree.

## Required reading

Read and verify the integrated versions of the following sources.

### Program and Track 6 authority

- `docs/chains/rh-summary.md`
- `docs/chains/rh/component-matrix.md`, especially CM-008, CM-009, CM-014,
  and CM-034
- `docs/chains/rh/block-number-inventory.md`, especially BN-002
- `docs/chains/rh/shared-block-clock-specification.md`, especially BN-002, S5,
  and the decision register
- `docs/chains/rh/block-clock-validation-plan.md`, especially the Ledger
  acceptance properties
- `docs/chains/rh/track-6-s1-clock-harness.md`
- `docs/chains/rh/track-6-s2-checked-clock-inventory.md`
- `docs/chains/rh/track-6-s3-lootbox-floor.md`
- `docs/chains/rh/lootbox-floor-implementation-record.md`
- `docs/chains/rh/track-6-s4-deleverage-cooldown.md`
- the latest reviewed S4 decision and implementation records, if they exist
- `docs/chains/rh/robinhood-deployment-support-specification.md`, including
  reservation `0030_Track6S5LedgerGuard.py`
- `docs/chains/rh/robinhood-deployment-validation-plan.md`
- `docs/chains/rh/track-7-h1-dependency-security-preflight.md`
- the integrated H-01 evidence and implementation records, once available

If any required integrated file is missing, record it as a dependency. Do not
read a floating branch as if it were the approved source of truth.

### Ripe production surfaces

- `contracts/data/Ledger.vy`
- `contracts/core/Teller.vy`
- `contracts/core/TellerUtils.vy`
- `contracts/data/MissionControl.vy`
- `contracts/config/SwitchboardDelta.vy`
- `contracts/config/DefaultsBase.vy`
- `contracts/config/DefaultsLocal.vy`
- `contracts/modules/Addys.vy`
- `contracts/modules/DeptBasics.vy`
- `contracts/core/CreditEngine.vy`
- `contracts/core/Deleverage.vy`
- `contracts/core/AuctionHouse.vy`
- `contracts/registries/RipeHq.vy`
- `interfaces/Defaults.vyi`
- `interfaces/ConfigStructs.vyi`
- every interface imported for the selected guard path

Do not assume the S5 file set from the shared specification is necessarily
state-safe. The architecture checkpoint may narrow or correct that file set.

### Ripe tests and fixtures

- `tests/conf_core.py`
- `tests/data/test_ledger.py`
- `tests/config/test_switchboard_delta.py`
- `tests/core/teller/test_teller_deposit.py`
- `tests/core/teller/test_teller_withdraw.py`
- `tests/core/teller/test_teller_rebalance.py`
- `tests/core/creditEngine/test_credit_borrow.py`
- `tests/core/creditEngine/test_credit_repay.py`
- `tests/vaults/modules/test_stab_vault_claims.py`
- `tests/core/deleverage/test_deleverage_for_withdrawal.py`, especially its
  documented sequential-withdrawal transient-storage behavior
- `tests/core/deleverage/conftest.py`, especially the fresh-Deleverage fixture
  used as a transient-storage workaround
- every Teller-domain test covering a higher-risk action identified in Stage A
- `tests/clock/test_clock_profiles.py`
- `config/block-clock-inventory.json`
- `scripts/check_block_clock_inventory.py`
- `tests/inventory/test_block_clock_inventory.py`

Record that `DefaultsLocal.shouldCheckLastTouch` is false at the planning
baseline. A passing local full suite does not prove the Base-enabled policy
unless the relevant tests explicitly enable and exercise it.

### ABIs, migrations, and deployment evidence

- `scripts/abis/Ledger.json`
- `scripts/abis/Teller.json`
- `scripts/abis/MissionControl.json`
- `scripts/abis/SwitchboardDelta.json`
- every historical Base migration that deploys, replaces, registers, or
  configures Ledger, Teller, MissionControl, or SwitchboardDelta
- `migration_history/base-mainnet/v1/current-manifest.json`
- the manifest and migration-history chain needed to reconstruct each current
  live address and artifact

At the planning baseline, the committed manifest identifies the live Base
Ledger as `0x365256e322a47Aa2015F6724783F326e9B24fA47`. Treat that as a
point-in-time evidence claim to re-verify from committed records. Do not perform
a live RPC query without separate owner approval.

### Git history evidence

Inspect at least:

- commit `4ac5449b3e792600baf20edb0ec9e1819ec45bfe`, titled `last touch`;
- commit `3deb55894f3c6418e85ddce78a4489006625e8c1`, which introduced the
  Base/local default split; and
- commit `a62309c4eae5e98216712c5cfd05f5f58f25e2e1`, titled `bug fix`,
  which changed the Underscore classification input.

Git messages and old test headings are intent evidence, not final authority.
Reconstruct the actual diff and current behavior before drawing conclusions.

### Read-only Underscore compatibility input

At planning time, the local Underscore checkout is
`/Users/wigglez/dev/underscore-protocol`. Record its committed HEAD and dirty
state, then read committed content only, including:

- `contracts/legos/RipeLego.vy`;
- user-wallet and leverage flows that call Ripe Teller;
- tests that compose withdraw, borrow, rebalance, claim, or repay actions; and
- any code that depends on the Underscore wallet/vault exemption.

Ignore unrelated untracked files. Do not clean or modify that repository.

## Controlling constraints

1. **One canonical implementation.** No Robinhood branch, Robinhood-only
   production contract, `chain.id` conditional, or chain-selected source.
2. **Threat before mechanism.** Do not select transient storage, elapsed
   seconds, both, or disablement until the protected threat is explicit.
3. **Live accounting state is an invariant.** Registration indirection does
   not make Ledger state replaceable. No Ledger replacement may proceed without
   an exhaustive, independently reviewed state-enumeration and atomic-migration
   proof.
4. **Preserve locked-account protection.** `isLockedAccount` enforcement must
   remain active in every selected mode, including guard-disabled mode.
5. **Preserve authority or tighten it deliberately.** Do not widen callers,
   let callers self-select a weaker policy, or substitute `tx.origin`.
6. **No silent semantic reuse.** Do not silently reinterpret
   `shouldCheckLastTouch` as a different guard or unit.
7. **No placeholder timing.** A one-second persistent interval is not an
   approved security policy. Any seconds value needs a stated threat,
   boundary semantics, and owner acceptance.
8. **No test-only truth.** Titanoboa behavior must not be treated as EVM
   transient-storage authority when its behavior is known to differ.
9. **History is immutable.** Do not rewrite old migrations, manifests, or
   generated deployment evidence.
10. **Base convergence is required.** Temporary reviewed live-bytecode drift
    may be bounded; permanent Base/Robinhood source divergence is prohibited.
11. **S5 does not own Robinhood defaults.** Future `DefaultsRobinhood` values
    and the broader S6 parameter profile remain S6-owned.
12. **No implementation before approval.** Checkpoint 0 is a hard owner and
    independent-security-reviewer gate.

## Stage A ownership

Stage A may create or edit only:

- `docs/chains/rh/ledger-guard-security-decision.md`

It may run read-only repository commands and tests that do not update tracked
artifacts. It may not edit:

- production contracts or interfaces;
- tests or fixtures;
- generated ABIs;
- the checked inventory;
- dependency files;
- migrations or manifests;
- `rh-summary.md`;
- the shared Track 6 specification or validation plan;
- the S4 brief or records;
- the Underscore repository; or
- any external system.

If Stage A concludes that the shared Track 6 specification’s assumed S5 file
set or “new Ledger artifact” posture is unsafe, record the conflict and request
an owner/security-approved planning correction. Do not silently follow it and
do not silently diverge from it.

## Stage A — threat model and architecture decision

### Phase A1 — Freeze and reproduce the baseline

Record:

- the exact integration commit and all required file hashes;
- H-01, S4, Track 7, and Track 8 states;
- runtime and compiler versions;
- the exact S1/S2 inventory counts;
- the full-suite collected and passing counts;
- targeted Ledger/Teller/credit/config test results;
- the current Base/local `shouldCheckLastTouch` defaults;
- the current committed Base Ledger, Teller, MissionControl, and
  SwitchboardDelta addresses and artifact evidence; and
- all warnings, skips, xfails, and environment-dependent results.

Reproduce the current guard behavior with explicit Base-enabled configuration.
At minimum prove:

| Sequence | Current expected result |
|---|---|
| lower-risk touch, then checked higher-risk action, same `NUMBER` | higher-risk action rejects |
| checked higher-risk action, then lower-risk touch, same `NUMBER` | lower-risk touch succeeds |
| checked higher-risk, lower-risk, checked higher-risk, same `NUMBER` | final higher-risk action rejects |
| rejected sequence, then `NUMBER + 1` | checked action can proceed if no other condition blocks |
| Underscore-classified user | assertion skipped, `lastTouch` still written |
| locked user, guard flag false | account remains rejected |
| two different users, same `NUMBER` | per-user state remains isolated |

Do not inherit the present zero-address test’s “revert or success is
acceptable” posture. Record the actual behavior and require Checkpoint 0 to
select the intended zero-user policy.

### Phase A2 — Reconstruct intent and the complete call graph

Build a stable-ID action table. For every Teller path that reaches
`_performHousekeeping`, record:

- action and function;
- external entry point;
- caller authorization;
- `_user`, caller, payer, receiver, recipient, delegate, liquidator, or keeper
  identity as applicable;
- `_isHigherRisk` value and why;
- `_shouldUpdateDebt` value;
- whether housekeeping occurs before or after external effects;
- whether the entry point is `@nonreentrant`;
- callbacks or external transfers before and after guard evaluation;
- whether a lower-risk touch can arm a later higher-risk rejection;
- Underscore classification behavior;
- locked-account behavior; and
- relevant tests.

The minimum high-risk set to verify from current source includes:

- `withdraw`;
- `withdrawMany`;
- `rebalance`;
- `borrow`;
- `claimFromStabilityPool`; and
- `claimManyFromStabilityPool`.

Do not assume that this list is exhaustive if the integrated source differs.

Separately analyze external `Teller.performHousekeeping`. Current source allows
any address accepted by `addys._isValidRipeAddr(msg.sender)` to provide:

- the higher-risk flag;
- the user;
- whether debt should update; and
- an Addys bundle.

Identify every production caller, but do not equate “only one source call site
found” with the authorization boundary. Determine whether a valid Ripe
department, vault, or switchboard can grief a user by writing or arming guard
state, choose another user, or choose a weaker risk flag.

At the planning baseline, the sole production-source caller found is
`Deleverage.deleverageForWithdrawal`, which calls
`Teller.performHousekeeping(False, _user, True, a)` in
`contracts/core/Deleverage.vy`. Re-verify that fact from the integrated source
and record the exact line. One source call site does not narrow
`addys._isValidRipeAddr` authorization or eliminate the broader griefing
analysis.

Inspect `contracts/core/AuctionHouse.vy` and commit
`4ac5449b3e792600baf20edb0ec9e1819ec45bfe` explicitly. AuctionHouse does not
contain a current production `performHousekeeping` call at the planning
baseline, but the commit that introduced `lastTouch` changed AuctionHouse and
the BN-002 planning record names liquidation safety. Determine what that
historical change did and whether any liquidation path is protected directly,
indirectly, or not at all by the current guard.

### Phase A3 — Audit state and migration feasibility

Create a Ledger state inventory, separate from the block-clock inventory.
For each storage field or mapping, record:

- purpose;
- key dimensions;
- whether keys are enumerable onchain;
- whether a committed indexer or event log is sufficient to reconstruct every
  live key;
- whether the value participates in debt, collateral, reward, auction, lock,
  bond, bad-debt, or authorization accounting;
- whether zero is meaningful;
- whether migration can be proven complete;
- invariants tying it to another field or contract; and
- consequences of omission, duplication, or stale replay.

The audit must cover all Ledger storage, not just `lastTouch`.

Compare at least these state-placement options:

1. **Preserve the live Ledger and move the portable guard to Teller.** Continue
   calling the existing Ledger with checking disabled only after the new guard
   is active, so the existing locked-account check remains enforced.
2. **Preserve the live Ledger and add a generic shared guard contract.** Define
   its registration, authority, state, migration, pause, diagnostics, and
   rollback model. Reject an issuer- or Robinhood-branded variant.
3. **Change or replace Ledger.** This is admissible only if every live Ledger
   state field is exhaustively enumerable and an atomic state migration can be
   independently proven. A partial or offchain-best-effort migration fails.
4. **Disable the present check without replacement.** This requires explicit
   security acceptance of the lost property and is not the default.

If a persistent per-user timestamp is proposed in Teller or a new guard,
analyze how that new state affects later upgrades and whether the selected
contract remains safely replaceable.

The safe default is to preserve the live Ledger bytecode and state unless the
checkpoint establishes otherwise.

### Phase A4 — Define the threat model

For each scenario below, state:

- attacker capability;
- required transaction ordering;
- affected user;
- relevant caller or department authority;
- whether current BN-002 prevents it;
- whether Teller’s existing nonreentrant lock already prevents it;
- whether the candidate transient layer prevents it;
- whether the candidate elapsed-seconds layer prevents it;
- bypasses and griefing risk;
- false-positive user impact; and
- evidence or test needed.

Required scenarios:

- nested/reentrant higher-risk composition;
- two separately submitted transactions in one Base `NUMBER`;
- many separately submitted transactions during one Robinhood repeated
  `NUMBER`;
- lower-risk then higher-risk sequencing;
- higher-risk then lower-risk then higher-risk sequencing;
- delegated actions and identity substitution;
- receiver/recipient/keeper/liquidator identity differences;
- a valid Ripe address calling `performHousekeeping` for a victim;
- a valid Ripe address choosing `_isHigherRisk=False`;
- Underscore wallet/vault composition through Ripe Lego;
- flash-loan-funded borrow, withdraw, rebalance, or claim sequences;
- price/snapshot update ordering;
- lock added or removed between actions;
- policy change between actions;
- failed/reverted action and state rollback;
- two different users in the same transaction;
- zero-address input;
- paused Ledger, Teller, guard, or MissionControl;
- timestamp repeat, small increment, boundary, large jump, and future-value
  assumptions; and
- mixed old/new deployments during rollout or rollback.

The repository’s “Flash Loan Protection” heading is a lead, not proof that the
current property is necessary or sufficient.

### Phase A5 — Compare architectures

Compare at least:

| Candidate | Required analysis |
|---|---|
| retain BN-002 unchanged | Robinhood throttling, cross-chain semantics, and explicit rejection rationale |
| disable BN-002 | exact lost property and accepted risk |
| transient guard only | entry/exit placement, existing `@nonreentrant` overlap, per-user semantics, external housekeeping, Underscore, EVM truth |
| elapsed-seconds guard only | threat fit, value and bounds, low-risk arming, timestamp trust, griefing, persistent state migration |
| transient plus elapsed seconds | independent purpose of each layer, interaction, failure/rollback, observability |
| guard in existing Ledger | live-state upgrade/migration feasibility |
| guard in Teller | action-boundary coverage, replacement/state implications, old Ledger call |
| separate generic ActionGuard | registration, authority, pause, migration, diagnostics, added complexity |

Reject:

- `chain.id` branching;
- Robinhood-only source or an issuer-specific guard;
- `tx.origin`;
- retaining `block.number` identity;
- timestamp equality without an elapsed-seconds policy;
- silently setting `shouldCheckLastTouch=False`;
- letting an arbitrary caller self-select whether protection applies;
- a guard entered only at end-of-action housekeeping when the selected threat
  requires whole-action coverage;
- relying on Teller’s `@nonreentrant` without analyzing the externally callable
  `performHousekeeping` and cross-contract paths;
- persistent state in a supposedly stateless/redeployable contract without a
  migration model; and
- replacing Ledger without complete state proof.

### Phase A6 — Specify policy semantics

The decision record must define:

- protected threat or threats;
- transient protection arming rule;
- persistent pacing arming rule;
- whether lower-risk touches arm either layer;
- canonical high-risk action set;
- exact action-entry and exit timing;
- user identity for every action;
- delegation semantics;
- recipient/receiver/keeper/liquidator handling;
- zero-address behavior;
- Underscore exemption separately for each selected layer;
- external `performHousekeeping` caller and parameter policy;
- locked-account behavior in every mode;
- failure/revert behavior;
- pause behavior;
- policy-update behavior;
- observability and diagnostic views;
- event requirements;
- mode and value configuration;
- initialization/default behavior on Base, Robinhood, and local tests;
- seconds value, lower/upper bounds, and exact boundary comparator if pacing is
  selected;
- whether policy changes apply immediately or prospectively;
- compatibility with the old `shouldCheckLastTouch` getter/setter;
- storage and ABI impact; and
- emergency disable/rollback semantics.

Use an explicit mode/value model if the selected architecture has multiple
layers. Do not encode an ambiguous set of booleans that allows an accidental
unsupported combination.

### Phase A7 — Verify transient-storage test authority

The repository uses Vyper transient mappings in other contracts. The integrated
test suite explicitly documents a Titanoboa behavior in
`tests/core/deleverage/test_deleverage_for_withdrawal.py` where transient
storage does not clear between simulated transactions, and
`tests/core/deleverage/conftest.py` supplies a fresh-Deleverage fixture as a
workaround. Treat those comments and tests as provenance for a reported
environment-specific behavior, not proof that the behavior still exists under
the post-H-01 pinned environment or that it applies identically to S5.

If a transient S5 layer is proposed:

- verify the exact Vyper compiler output and opcode use;
- state the EVM transaction-boundary property being relied on;
- reproduce the Titanoboa behavior under the integrated H-01/S1 environment;
- do not change production semantics to match a test-runner defect;
- do not hide a mismatch with a skip, xfail, or silent reset;
- identify the approved S1/reset mechanism, if it accurately models EVM
  transaction boundaries;
- require a second execution environment or other independently reviewable
  evidence if Titanoboa cannot prove the property; and
- include a negative test showing that the transient flag cannot persist into
  an independent EVM transaction.

Stage A must stop if the proposed critical security property cannot be tested
faithfully.

### Phase A8 — Specify state-safe rollout and rollback

For Base and Robinhood separately, define:

- old and new artifact set;
- registration and call graph before activation;
- the single activation boundary;
- initialization of any new policy or per-user state;
- how the old NUMBER guard stays active until the replacement is active;
- how the old guard is disabled without disabling locked-account protection;
- whether mixed versions are possible;
- abort assertions;
- rollback boundary;
- behavior for transactions in flight;
- event and monitoring requirements;
- live-version drift owner and convergence bound; and
- proof that no permanent chain-specific source is created.

If Ledger remains unchanged, require:

- byte-identical Ledger source/artifact evidence;
- unchanged accounting ABI unless explicitly justified;
- preserved Teller-only Ledger call;
- `_shouldCheck=False` only after the replacement is active;
- locked-account regression proof; and
- no attempt to migrate or rewrite Ledger accounting state.

If Ledger changes, require an exhaustive state migration specification,
independent audit, rehearsed atomic migration, and owner approval before Stage B
may be authorized. S5’s default Stage B scope does not include such a
migration.

### Phase A9 — Define implementation and audit slices

Propose the smallest reviewable, atomic implementation plan. It must:

- separate architecture approval from code;
- keep unrelated Ledger accounting out of scope;
- keep S4 mechanics out of S5;
- identify every production source, interface, fixture, test, and ABI;
- identify the exact artifact and storage-layout comparisons;
- reserve migration requirements for Track 7;
- define independent review boundaries;
- state whether a dedicated external audit is required;
- define S2 inventory reconciliation as a separate final stage; and
- state which component-matrix and decision-register rows would need a later
  owner-approved reconciliation.

Do not split a single protection mechanism across deployments when a partial
state could silently disable both old and new protection.

## Stage A deliverable

Create:

- `docs/chains/rh/ledger-guard-security-decision.md`

It must contain:

- baseline and provenance;
- current behavior proof;
- complete action/call graph;
- Ledger state and enumerability inventory;
- threat matrix;
- architecture comparison;
- Underscore compatibility analysis;
- selected or recommended policy semantics;
- test-authority analysis;
- Base and Robinhood rollout comparison;
- exact proposed Stage B file set;
- migration and Track 7 requirements;
- reviewer/audit requirements;
- unresolved items;
- recommendation with confidence;
- explicit rejected alternatives; and
- Checkpoint 0 approval table with every decision still visibly pending.

Recommendations are not approvals.

## Checkpoint 0 — mandatory owner and security decision

Stop after Stage A. Do not edit production code until the owner and an
independent security reviewer explicitly decide all of the following:

1. **Protected threat:** nested/reentrant composition, cross-transaction pacing,
   both, or accepted disablement.
2. **Guard location and Ledger posture:** preserve Ledger and use Teller;
   preserve Ledger and use a generic guard; or approve a separately audited,
   exhaustive Ledger state migration.
3. **Transient layer:** whether it exists, what arms it, where it begins and
   ends, and which actions it covers.
4. **Persistent pacing layer:** whether it exists, its seconds value and bounds,
   exact boundary, update timing, and timestamp-trust acceptance.
5. **Lower-risk arming:** whether lower-risk touches arm the transient layer,
   persistent layer, both, or neither.
6. **High-risk action set:** the canonical protected actions and any explicit
   exclusions.
7. **Underscore policy:** exemption or inclusion for each layer, with
   downstream evidence.
8. **Identity policy:** canonical user, caller, delegate, recipient, keeper,
   liquidator, and zero-address semantics.
9. **External housekeeping policy:** authorized callers, caller-supplied risk
   flags, griefing controls, and Deleverage compatibility.
10. **Configuration and compatibility:** explicit mode/value schema, old
    `shouldCheckLastTouch` transition, events, views, defaults, and ABI.
11. **Locked and paused behavior:** lock enforcement in every mode and
    fail-closed pause behavior.
12. **Base rollout:** live-version policy, activation order, rollback boundary,
    convergence deadline, and whether a dedicated external audit is required.
13. **H-01/S4 sequence:** exact integrated dependency and overlapping-file
    baseline for Stage B.
14. **Stage B ownership:** exact allowed production, interface, test, fixture,
    ABI, and record files.
15. **Evidence bar:** required secondary EVM evidence, artifact checks,
    migration rehearsal, targeted suites, S1/S2, and full-suite results.

The approval record must name each decision, date, approver, evidence commit,
and any conditions. “Proceed,” approval of this brief, or approval of another
slice is not sufficient.

If no answer is provided, the default is:

- no Stage B;
- no change to live Base policy;
- no Robinhood activation of the current NUMBER guard;
- no Ledger replacement; and
- no migration or deployment work.

## Proposed Stage B ownership

The exact file set is a Checkpoint 0 decision. Depending on the selected
architecture, it may include a strict subset of:

### Production and interfaces

- `contracts/data/Ledger.vy`
- `contracts/core/Teller.vy`
- `contracts/data/MissionControl.vy`
- `contracts/config/SwitchboardDelta.vy`
- `contracts/config/DefaultsBase.vy`
- `contracts/config/DefaultsLocal.vy`
- a new generic shared guard contract, only if explicitly selected
- `interfaces/Defaults.vyi`
- `interfaces/ConfigStructs.vyi`
- interfaces required by the approved call graph

### Tests and fixtures

- `tests/conf_core.py`
- `tests/data/test_ledger.py`
- `tests/config/test_switchboard_delta.py`
- relevant Teller domain tests
- relevant CreditEngine and Stability Pool tests
- new focused S5 tests under an owner-approved path
- `tests/clock/test_clock_profiles.py`, only if new generic harness coverage is
  required

### Generated artifacts and records

- only ABIs corresponding to approved changed contracts
- `docs/chains/rh/ledger-guard-implementation-record.md`

Stage B does not own:

- future `contracts/config/DefaultsRobinhood.vy`;
- `scripts/params/general.py` or CAD-001 work;
- any historical migration or manifest;
- Track 7’s reserved `0030_Track6S5LedgerGuard.py`;
- S4-only cooldown/context code;
- dependency files;
- S2 inventory files before Stage C;
- `rh-summary.md`;
- Underscore source; or
- live execution.

If the architecture preserves Ledger unchanged, `contracts/data/Ledger.vy` and
`scripts/abis/Ledger.json` are prohibited Stage B edits. Record their hashes as
negative evidence.

## Stage B — conditional production implementation

### Phase B1 — Reconcile the approved baseline

Before editing:

- rebase or recreate from the exact owner-approved post-H-01/post-S4 `rh`
  baseline;
- re-read the integrated H-01 and S4 records;
- verify no file overlap or semantic conflict;
- repeat all Stage A hashes and tests;
- confirm every Checkpoint 0 approval remains valid;
- confirm no intervening contract change invalidates the action graph or state
  inventory; and
- stop if the exact approved file set has changed.

Do not carry an unreviewed Stage A worktree forward through conflicts.

### Phase B2 — Implement the selected guard atomically

Implement only the selected design.

Required invariants:

- no canonical guard decision depends on `block.number`;
- no `chain.id` or Robinhood-specific production branch exists;
- an unauthorized caller cannot arm, clear, bypass, or weaken the guard;
- user identity follows the approved action table;
- lower-risk arming exactly matches approval;
- every protected action enters the guard before the external effects relevant
  to the selected threat;
- a transient layer is scoped to the EVM transaction and cannot leak into the
  next transaction;
- a persistent layer uses the approved seconds value, bounds, comparator, and
  update timing;
- revert behavior does not leave partial guard state;
- different users remain isolated;
- Underscore behavior exactly matches approval;
- external housekeeping cannot be used as an unapproved griefing or bypass
  surface;
- locked-account enforcement remains active in every mode;
- paused behavior fails closed as approved;
- old protection is not disabled before new protection is active; and
- unrelated accounting and economic semantics do not change.

If both transient and persistent layers are selected, each must enforce its own
named threat. Passing one layer must not silently bypass the other.

### Phase B3 — Preserve live Ledger state

If Ledger is unchanged:

- prove its source and generated artifact are unchanged;
- preserve the existing Teller-only call;
- preserve its locked-account assertion;
- pass `_shouldCheck=False` only under the approved atomic transition;
- retain existing `lastTouch` state without pretending it was migrated;
- document that stale `lastTouch` values are harmless under the selected new
  policy; and
- prove no new code reads them as seconds or another unit.

If a Ledger change was exceptionally approved:

- stop unless the separate state-migration specification and audit required by
  Checkpoint 0 are integrated;
- prove full storage compatibility or complete atomic migration;
- prove every non-enumerable mapping is accounted for;
- reconcile every accounting invariant before activation; and
- treat any missing key or unexplained balance as an abort.

No test fixture may stand in for live state-enumeration proof.

### Phase B4 — Implement explicit policy configuration

If configuration changes are approved:

- use explicit modes and units;
- validate every bound at construction and governance-set time;
- emit events for persistent policy changes;
- expose diagnostic views needed by operators;
- preserve timelock/governance authority;
- prevent unsupported mode combinations;
- define initialization for Base and local fixtures;
- leave Robinhood values to S6 unless Checkpoint 0 expressly grants a narrow
  exception; and
- document the transition from `shouldCheckLastTouch`.

Do not keep a misleading getter whose name says “last touch” if it now selects a
different policy without a compatibility explanation and deprecation plan.

### Phase B5 — Build the canonical security matrix

Tests must cover at least:

| Dimension | Required cases |
|---|---|
| current comparison | all Phase A1 sequences under current policy |
| EVM `NUMBER` | repeat, `+1`, `+2`, `+4`, `+60`, boundary skip |
| timestamp | repeat, below boundary, exact boundary, above boundary, large jump |
| transaction | nested same transaction, separate transactions, revert/reset |
| risk order | low→high, high→low, high→low→high, high→high |
| identity | user, caller, delegate, recipient, receiver, keeper, liquidator, zero |
| caller authority | Teller internal route, valid Ripe external route, invalid caller |
| action | every approved high-risk Teller action |
| user isolation | same user and two-user interleaving |
| Underscore | wallet, vault, ordinary user, caller/user distinction |
| lock/pause | locked in every mode; relevant contracts paused |
| policy | each supported mode, invalid modes, value bounds, governed update |
| mixed version | old guard only, new guard only, forbidden partial activation |
| migration | initialization, stale lastTouch, rollback boundary |

Test names must state the protected property. A test that merely reproduces a
revert without proving why does not close a security requirement.

### Phase B6 — Validate EVM semantics and artifacts

For a transient design:

- inspect compiler output for transient opcodes;
- prove transaction-boundary clearing in an authoritative environment;
- document any Titanoboa reset workaround and why it is faithful;
- fail if transient state survives a separate EVM transaction; and
- do not suppress known framework discrepancies.

For every changed production contract:

- regenerate only the corresponding ABI;
- compare creation and runtime artifacts;
- compare storage layouts;
- record constructor and immutable differences;
- verify shared source under Base and Robinhood parameter profiles;
- prove no production import from `contracts/mock/**` or
  `contracts/testing/**`; and
- record all bytecode differences with causes.

If Ledger is intentionally unchanged, its runtime and ABI equality are required
negative checks.

### Phase B7 — Specify, but do not execute, rollout

Update `docs/chains/rh/ledger-guard-implementation-record.md` with:

- approved decisions and provenance;
- exact source and artifact hashes;
- storage-layout findings;
- test and environment evidence;
- Base and Robinhood parameter expectations;
- activation order;
- pre-activation assertions;
- abort conditions;
- rollback boundary;
- live-version drift owner and convergence deadline;
- Track 7 migration requirements;
- external audit status; and
- every unresolved deployment or governance action.

No live deployment, governance action, registry write, signer use, or migration
execution is authorized.

## Reviewer Gate 1 — production and rollout review

Stop after Stage B.

An independent reviewer—not the implementation author—must verify:

- the approved threat and architecture were implemented exactly;
- no unapproved file or semantic change landed;
- live Ledger state is preserved or the exceptional migration proof is
  complete;
- action entry timing protects the selected threat;
- low-risk, identity, Underscore, external-housekeeping, lock, and pause
  semantics match approval;
- transient and timestamp evidence is authoritative;
- storage layouts and ABIs are safe;
- H-01 and S4 compatibility is proven;
- targeted, S1/S2, and full-suite validation passes;
- rollout is atomic and rollback is honest; and
- no live action occurred.

The reviewer records approval or findings in the implementation record. The
author may respond to findings but may not self-approve.

No inventory edit is allowed before Gate 1 approval.

## Stage C — checked-inventory reconciliation

After Gate 1 approval, Stage C may edit only:

- `config/block-clock-inventory.json`;
- `docs/chains/rh/block-number-inventory.md`;
- `docs/chains/rh/shared-block-clock-specification.md`;
- `docs/chains/rh/block-clock-validation-plan.md`;
- `docs/chains/rh/component-matrix.md`, if the approved architecture changes
  component disposition or artifact posture;
- S2 inventory tests or fixtures strictly required by the approved
  reconciliation; and
- the implementation record.

The implementation author may propose the changes. They may not self-approve
the semantic classification.

Required reconciliation:

- update BN-002 from `block.number` identity to the approved portable policy;
- remove only reviewed production occurrences;
- add any new indirect timestamp or transient-policy identifiers required by
  the inventory schema;
- preserve stable IDs and semantic owner;
- record whether Ledger remained unchanged;
- correct the S5 file/artifact posture if the state-safe architecture differs
  from the planning assumption;
- update the decision register with owner/security provenance;
- reconcile component-matrix version and migration implications; and
- keep deployment and launch gates open.

Do not add an inventory ID merely to silence S2. Every new or changed row needs
semantic evidence and an independent owner.

## Reviewer Gate 2 — merge readiness

An independent reviewer must verify:

- Gate 1 approval exists and is dated;
- the S2 inventory reconciles exact occurrences and indirect patterns;
- the planning documents match the approved implementation;
- no open threat or migration question is mislabeled as complete;
- the final branch is based on the approved post-H-01/post-S4 baseline;
- targeted, S1/S2, full-suite, ABI, storage, and artifact checks pass;
- commit scope is exact and whitespace is clean;
- no migration, deployment, push to protected branches, or live action
  occurred; and
- the merge recommendation names all remaining Track 7, S6, audit, Base
  convergence, and launch gates.

Only the owner may integrate the branch into `rh`. Integration into `rh` is not
approval to deploy or activate the guard.

## Cross-track interface

### H-01

H-01 owns dependency security and the authoritative lock. S5 consumes that
baseline and must not refresh or loosen it.

### S4

S4 owns Deleverage cooldown bounds and authorized multi-leg context. S5 owns
the general user-action guard. Any shared Teller or SwitchboardDelta edit must
have an explicit order and one semantic owner per line.

### S6

S6 owns `DefaultsRobinhood`, final chain parameter profiles, and broad defaults
generation. S5 supplies an approved mode/value schema and constraints; it does
not choose unrelated Robinhood parameters.

### S7–S10

S5 must not absorb timelock/registry validation, lifecycle capacity, disabled
integration assertions, or CAD reporting merely because they consume related
configuration.

### Track 7

Track 7 owns migration namespace, execution planning, manifest schema,
verification tooling, and rehearsal. S5 supplies reviewed artifacts and exact
assertions for reserved migration `0030_Track6S5LedgerGuard.py`.

### Track 8

Track 8 owns Stock Token vault safety. S5 must include the relevant
withdraw/borrow/liquidation call paths in its threat model, but it must not
implement Track 8 accounting fixes.

### Underscore

Underscore is compatibility evidence only. Any required downstream change is a
separate workstream.

## Approval and safety boundaries

Allowed without further approval during Stage A:

- read repository and committed external-repository source;
- inspect local Git history and committed manifests;
- run non-mutating local tests and compilation;
- produce the single Stage A decision record.

Requires Checkpoint 0 approval:

- every production, interface, fixture, test, ABI, or implementation-record
  change;
- the selected threat and architecture;
- any elapsed-seconds value;
- any change to Underscore exemption;
- any change to external housekeeping authorization;
- any Ledger artifact change;
- and the exact Stage B file set.

Requires a later separate approval:

- dependency edits;
- migration creation or execution;
- live RPC;
- signer use;
- governance or registry action;
- Base or Robinhood deployment;
- external communication;
- Underscore edits;
- checklist closure; and
- merge into `rh` or `master`.

## Stop conditions

Stop and return to the owner if:

- the protected threat remains ambiguous;
- S4 owns an overlapping file or ABI without an approved order;
- H-01 is not integrated before Stage B;
- current Teller action or external-housekeeping behavior differs materially
  from the Stage A graph;
- lower-risk arming is not explicitly decided;
- Underscore compatibility cannot be established from committed evidence;
- the chosen user identity is ambiguous;
- the selected persistent seconds value is a placeholder;
- timestamp trust is unacceptable for the selected threat;
- transient behavior cannot be tested faithfully;
- the proposed design duplicates an existing `@nonreentrant` lock without
  closing a distinct threat;
- a valid Ripe caller can grief or bypass the policy;
- locked-account protection weakens in any mode;
- the plan requires replacing Ledger without exhaustive state proof;
- any Ledger mapping key set cannot be enumerated for a proposed migration;
- the old guard must be disabled before the new one is active;
- an unsupported mixed-version state can occur;
- an ABI or storage-layout change is unexplained;
- a historical migration or manifest would need editing;
- a chain-specific source branch appears;
- the S2 inventory cannot reconcile;
- tests require a skip, xfail, or relaxed assertion to pass;
- any live action becomes necessary; or
- an owner/security decision is missing.

## Validation requirements

### Stage A minimum

Run from the isolated S5 worktree:

```bash
PYTHONPATH=. pytest -q tests/data/test_ledger.py
PYTHONPATH=. pytest -q tests/config/test_switchboard_delta.py
PYTHONPATH=. pytest -q tests/core/teller/test_teller_deposit.py
PYTHONPATH=. pytest -q tests/core/teller/test_teller_withdraw.py
PYTHONPATH=. pytest -q tests/core/teller/test_teller_rebalance.py
PYTHONPATH=. pytest -q tests/core/creditEngine/test_credit_borrow.py
PYTHONPATH=. pytest -q tests/core/creditEngine/test_credit_repay.py
PYTHONPATH=. pytest -q tests/vaults/modules/test_stab_vault_claims.py
PYTHONPATH=. pytest -q tests/clock/test_clock_profiles.py
PYTHONPATH=. python scripts/check_block_clock_inventory.py --check
PYTHONPATH=. pytest -q tests/inventory/test_block_clock_inventory.py
PYTHONPATH=. pytest --collect-only -q
PYTHONPATH=. pytest -q
git diff --check
```

Use the integrated H-01 record if it changes the authoritative environment or
commands. Do not install or refresh dependencies within S5.

### Stage B minimum

Repeat the Stage A commands, plus:

- every new focused S5 test;
- every Teller domain suite mapped to a protected action;
- compiler and opcode evidence for transient storage, if selected;
- approved secondary EVM validation, if required;
- ABI generation and exact diff checks;
- storage-layout comparison;
- creation/runtime bytecode comparison;
- unchanged Ledger hash check when Ledger is preserved;
- Base and Robinhood parameter-profile runs;
- migration-plan dry validation owned by Track 7, when available; and
- full suite under the integrated H-01 environment.

### Stage C minimum

Repeat:

```bash
PYTHONPATH=. python scripts/check_block_clock_inventory.py --check
PYTHONPATH=. pytest -q tests/inventory/test_block_clock_inventory.py
PYTHONPATH=. pytest -q tests/clock/test_clock_profiles.py
PYTHONPATH=. pytest --collect-only -q
PYTHONPATH=. pytest -q
git diff --check
```

Record exact commands, versions, counts, durations, warnings, and failures.
Never report “all tests pass” without the collected and passing counts.

## Completion reports

### Stage A report

Report:

- branch and starting commit;
- exact files changed;
- current behavior and intent evidence;
- action/call graph;
- Ledger state-migration feasibility;
- threat and architecture comparison;
- recommended policy;
- Underscore findings;
- H-01/S4 dependency state;
- tests and counts;
- all unresolved decisions; and
- explicit statement that no production code, migration, live action, or
  external write occurred.

Stop for Checkpoint 0.

### Stage B report

Report:

- approval provenance;
- reconciled starting commit;
- exact files and semantics changed;
- source, ABI, storage, and bytecode evidence;
- Ledger-preservation evidence;
- security-matrix results;
- transient/timestamp authority;
- targeted, S1/S2, and full-suite results;
- rollout/rollback plan;
- remaining Track 7/S6/audit/live gates; and
- explicit statement that no inventory edit, migration, deployment,
  governance action, or protected-branch integration occurred.

Stop for Reviewer Gate 1.

### Final report

After Gate 2, report:

- both reviewer approvals;
- final commit graph;
- exact inventory reconciliation;
- all validation evidence;
- merge recommendation;
- Base convergence and Robinhood deployment prerequisites;
- unresolved risks and owner actions; and
- explicit statement that merge readiness does not authorize deployment,
  activation, migration execution, or launch.
