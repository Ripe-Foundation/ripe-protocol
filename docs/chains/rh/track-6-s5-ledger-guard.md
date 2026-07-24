# Track 6 S5: Portable User-Action Guard and State-Safe Rollout

**Status:** Revised draft after owner action-block direction; no implementation
or kickoff is authorized

**Prepared:** 24 July 2026

**Planning baseline:** `27765d29094256fa9619dd44a0bfd145863de8b7`

**Owner action-block direction:** 24 July 2026 — preserve the existing
same-execution-block security property through a narrow shared Ledger clock
abstraction. Robinhood uses `ArbSys(0x64).arbBlockNumber()` as its child-chain
block identity. The deployed Base Ledger remains untouched indefinitely because
its accounting state makes migration risk disproportionate. Production
implementation remains prohibited until Stage A proves the smallest safe
abstraction and an independent security reviewer approves it.

**Required launch baseline:** this brief must be reviewed and committed to `rh`.
Stage A may run while H-01 and S4 are in progress. Stage B remains blocked on
the reviewed H-01 dependency baseline, the reviewed S4 ownership decision, and
every owner/security decision in Checkpoint 0.

## Fresh-agent instruction

Treat this document as the task contract. Work only on Track 6 slice S5:
validate the owner-selected same-execution-block property, choose the smallest
chain-portable action-block abstraction, and—only after explicit approval—
implement it without changing unrelated Ledger accounting. Robinhood is the
first production deployment of the revised canonical Ledger. The existing Base
Ledger is not migrated or replaced.

S5 has three stages:

1. **Stage A — threat model and architecture decision:** repository-read-only
   analysis plus one decision record. No production contract, ABI, test,
   inventory, dependency, migration, or external-repository change is allowed.
2. **Stage B — production implementation:** blocked until the owner and an
   independent security reviewer approve every mandatory decision below,
   approve the exact file set, and close the H-01/S4 sequencing gates.
3. **Stage C — checked-inventory reconciliation:** blocked until an independent
   reviewer approves the Stage B production implementation and rollout record.

The required result of Stage A is an evidence-backed recommendation for the
smallest safe action-block source boundary. It may recommend stopping if
Robinhood does not expose the required child-block primitive or if the
abstraction adds unacceptable risk. It may not silently fall back to disabling
the guard, convert the policy into elapsed time or oracle freshness, broaden the
protected action set, or assume that replacing the live Base Ledger is safe
merely because RipeHq can register a new address.

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

### Owner-selected minimum-change direction controls Stage A

Stage A must consume
`docs/chains/rh/minimal-contract-change-reassessment.md` and treat these owner
decisions as fixed inputs:

- preserve the existing same-execution-block identity policy;
- this is not an elapsed-time, rate-limit, oracle-freshness, or price-snapshot
  policy;
- Robinhood's identity source is the Arbitrum child-chain block returned by
  `ArbSys(0x64).arbBlockNumber()`;
- ordinary EVM deployments use their native execution `block.number`;
- the repository keeps one forward canonical Ledger source with no `chain.id`
  branch;
- Robinhood is the first production deployment of that revised source;
- the current Base Ledger and its accounting state remain untouched
  indefinitely; and
- permanent Base/Robinhood live-bytecode divergence is accepted for this
  state-bearing component and must be recorded, not “converged” through a risky
  migration.

Stage A must minimize how that decision is implemented. Compare at least an
immutable generic action-block provider with the smallest reviewed
native/external-source helper. A separate provider must justify its extra
deployment and call-failure surface; an internal helper must justify its mode,
source, and ABI. Neither may silently fall back from the configured child-block
identity to ancestor `block.number`.

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
- `docs/chains/rh/minimal-contract-change-reassessment.md`
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

### External primary sources

- Robinhood Chain's current official network and Nitro/ArbOS documentation:
  `https://docs.robinhood.com/chain/` and
  `https://docs.robinhood.com/chain/run-a-full-node/`
- Arbitrum's current official block-number documentation:
  `https://docs.arbitrum.io/arbitrum-essentials/arbitrum-vs-ethereum/block-numbers-and-time`
- the current authoritative Offchain Labs ArbSys interface/source for the
  Robinhood Nitro/ArbOS release

Record retrieval dates and exact versions. A documentation claim does not
replace the required Robinhood testnet evidence, and a live probe remains
owner-gated.

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

1. **Minimum production change.** The owner has rejected disabling the
   same-block property. Change only the narrow clock boundary required to
   preserve it on Robinhood; unrelated Ledger accounting, action policy,
   timing, freshness, and portability work are prohibited.
2. **One canonical implementation.** No Robinhood branch, Robinhood-only
   production contract, `chain.id` conditional, or chain-selected source.
3. **Threat is same execution block.** Do not substitute transient-only
   reentrancy, elapsed seconds, oracle freshness, or cross-block pacing. A
   separate action in the next child block is allowed even if it follows
   quickly.
4. **Live accounting state is an invariant.** Registration indirection does
   not make a deployed Ledger replaceable. Robinhood may deploy the revised
   Ledger only from empty state; the existing Base Ledger must not be migrated
   or replaced.
5. **Preserve locked-account protection.** `isLockedAccount` enforcement must
   remain active in every selected mode, including guard-disabled mode.
6. **Preserve authority or tighten it deliberately.** Do not widen callers,
   let callers self-select a weaker policy, or substitute `tx.origin`.
7. **No silent semantic reuse.** Do not reinterpret `shouldCheckLastTouch` as
   elapsed time or freshness. Stage A must decide whether the existing Boolean
   remains the enable/disable control for the portable same-block check.
8. **No generic-clock scope creep.** The action-block source must not be used
   for timelocks, cooldowns, rates, auctions, rewards, capacity, price
   freshness, or telemetry without a separate specification.
9. **Authoritative child-block evidence.** Local patched block numbers are not
   proof of ArbSys behavior. Require official interface/version evidence plus
   a read-only or separately approved testnet probe.
10. **History is immutable.** Do not rewrite old migrations, manifests, or
   generated deployment evidence.
11. **No Base Ledger migration.** The deployed Base Ledger remains on its
    current bytecode indefinitely. This is an approved permanent live-version
    exception caused by non-enumerable, high-value accounting state, not
    permission for a Base source fork.
12. **S5 does not own Robinhood defaults.** Future `DefaultsRobinhood` values
    and the broader S6 parameter profile remain S6-owned.
13. **No implementation before approval.** Checkpoint 0 is a hard owner and
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

## Stage A — action-block architecture and security decision

### Phase A0 — freeze the owner-selected property and minimize the change

Before designing the abstraction:

- record the owner decision verbatim and its 24 July 2026 provenance;
- prove the exact current any-touch/checked-higher-risk ordering behavior rather
  than simplifying it to “one transaction per block”;
- prove that Robinhood ancestor `block.number` cannot represent the selected
  child-block identity and that disabling the flag would remove an
  owner-required property;
- state explicitly that the next child block clears the guard regardless of
  elapsed wall time or oracle state;
- identify the smallest production boundary capable of supplying native block
  identity on ordinary EVM chains and ArbSys child-block identity on
  Robinhood;
- compare the new-code, call, ABI, gas, deployment, failure, and audit risks of
  each abstraction shape;
- prove that no Base Ledger deployment, state migration, registry action, or
  convergence deadline is part of S5; and
- stop if the selected child-block source cannot be proven or the proposed
  mechanism silently changes action classification.

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

Then define the selected Robinhood comparison without pretending it is already
implemented:

| Sequence | Selected portable result |
|---|---|
| two checked actions for one user in the same Robinhood child block | second action rejects |
| two checked actions for one user in successive child blocks that share one ancestor `block.number` | second action may proceed |
| unchecked lower-risk touch then checked higher-risk action in one child block | higher-risk action rejects, preserving current ordering |
| checked higher-risk touch then unchecked lower-risk touch in one child block | lower-risk action may proceed, preserving current ordering |
| two users in one child block | isolated per-user behavior |
| configured child-block source reverts, returns malformed data, or violates monotonic assumptions | fail closed; never fall back to ancestor `block.number` |

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

Compare at least these narrow clock-source placements:

1. **Immutable generic provider interface.** The revised canonical Ledger calls
   an immutable `ActionBlockClock` provider. Ordinary EVM deployments select a
   native-number provider; Robinhood selects a provider that reads
   `ArbSys(0x64).arbBlockNumber()`. Define provider code, authority, deployment,
   failure, gas, diagnostics, and manifest assertions.
2. **Immutable source/mode inside Ledger.** The revised Ledger uses a small
   internal helper configured at deployment to read native `block.number` or a
   reviewed external child-block source. Define mode validation, external-call
   behavior, constructor/ABI impact, and why embedding the mode is smaller and
   no less safe than a provider.
3. **Another generic action-block boundary.** Admit it only if it preserves the
   same Ledger call and action semantics with less code or failure surface.

Moving the guard to Teller, adding elapsed-time state, introducing a
transaction-context guard, and disabling the policy are outside the
owner-selected direction unless Stage A proves the action-block abstraction
cannot satisfy it and returns to the owner.

The Base state inventory remains mandatory evidence for why the current Base
Ledger must not migrate. It is not a request to design or prove a migration.
The Robinhood Ledger is a fresh deployment with no state import.

### Phase A4 — Define the threat model

For each scenario below, state:

- attacker capability;
- required transaction ordering;
- affected user;
- relevant caller or department authority;
- whether current BN-002 prevents it;
- whether Teller’s existing nonreentrant lock already prevents it;
- whether native execution-block identity prevents it on Base-like chains;
- whether ArbSys child-block identity prevents it on Robinhood;
- bypasses and griefing risk;
- false-positive user impact; and
- evidence or test needed.

Required scenarios:

- nested/reentrant higher-risk composition;
- two separately submitted transactions in one Base `NUMBER`;
- two separately submitted transactions in one Robinhood child block;
- transactions in successive Robinhood child blocks that share one ancestor
  `block.number`;
- many child blocks during one repeated ancestor `block.number`;
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
- child-block source failure, malformed return, repeat, `+1`, and nonmonotonic
  evidence;
- native-provider behavior on a Base-like profile;
- Robinhood child-block behavior under a dated testnet probe; and
- current Base bytecode coexisting indefinitely with the revised Robinhood
  artifact.

The repository’s “Flash Loan Protection” heading is supporting provenance. The
owner has clarified that the intended boundary is the same execution block,
not a duration or a guarantee that external financial state refreshed.

### Phase A5 — Compare architectures

Compare at least:

| Candidate | Required analysis |
|---|---|
| immutable generic `ActionBlockClock` provider | one canonical provider interface; native and ArbSys source mechanics; extra deployment/staticcall, immutability, failure, gas, verification, and future-chain extension |
| immutable source/mode helper in Ledger | constructor/immutable and ABI impact; native and ArbSys call path; mode validation; smaller deployment graph versus tighter chain-mechanism coupling |
| direct ArbSys read in Ledger with no abstraction | smallest line count versus loss of ordinary-EVM portability; reject unless the shared source remains correct without `chain.id` or a Robinhood branch |
| retain ancestor `block.number` on Robinhood | false throttling across multiple child blocks; conflicts with owner-selected execution-block identity |
| disable BN-002 | exact lost property; recorded as considered and owner-rejected |
| transient or elapsed-time replacement | conflicts with the selected block-identity property; retain only as rejected alternatives with evidence |

Reject:

- `chain.id` branching;
- Robinhood-only Ledger source or an issuer-specific guard;
- `tx.origin`;
- treating ancestor `block.number` as the Robinhood action-block identity;
- timestamp equality without an elapsed-seconds policy;
- setting `shouldCheckLastTouch=False` as the selected Robinhood policy;
- silently falling back to ancestor `block.number` when the configured
  child-block source fails;
- a mutable clock source that can change the security boundary without the
  separately approved governance and migration model;
- letting an arbitrary caller self-select whether protection applies;
- using the action clock for any duration, freshness, capacity, auction,
  reward, or timelock policy;
- changing current lower-risk/high-risk arming semantics without separate owner
  approval; and
- migrating or replacing the deployed Base Ledger.

### Phase A6 — Specify policy semantics

The decision record must define:

- the selected same-execution-block property and explicit non-goals;
- the portable action-block interface or helper contract;
- native-number and ArbSys child-number source semantics;
- provider/source immutability and validation;
- source-call failure, malformed-return, and nonmonotonic-evidence behavior;
- whether lower-risk touches preserve the current arming behavior;
- canonical high-risk action set;
- exact existing housekeeping timing;
- user identity for every action;
- delegation semantics;
- recipient/receiver/keeper/liquidator handling;
- zero-address behavior;
- Underscore exemption under the same child-block policy;
- external `performHousekeeping` caller and parameter policy;
- locked-account behavior;
- failure/revert behavior;
- pause behavior;
- observability and diagnostic views;
- event requirements;
- constructor, immutable, provider, and mode configuration;
- initialization/default behavior on Base, Robinhood, and local tests;
- compatibility with the old `shouldCheckLastTouch` getter/setter;
- storage and ABI impact;
- Robinhood abort/rollback semantics before any state-bearing transaction;
- the permanent Base live-version exception; and
- manifest and post-deployment proof of the selected action-block source.

Do not encode an ambiguous set of booleans that permits an unsupported source
or an accidental fallback. If the existing `shouldCheckLastTouch` Boolean is
retained, it may only enable or disable the same approved block-identity guard;
it may not select a different clock or policy.

### Phase A7 — Verify action-block-source authority

Stage A must distinguish four values and never present them as interchangeable:

- native EVM `block.number` on Base-like chains;
- Robinhood's ancestor-height `block.number`;
- Robinhood's RPC/receipt child-chain block number; and
- `ArbSys(0x64).arbBlockNumber()` observed in contract execution.

Require:

- current official Robinhood Nitro/ArbOS version evidence;
- the authoritative ArbSys interface, address, return type, and documented
  child-block semantics;
- a reproducible read-only or separately owner-approved Robinhood testnet probe
  proving that the precompile exists and agrees with receipt child-block
  identity;
- same-child-block evidence, if the RPC/sequencer can intentionally construct
  it, or an explicit stop if that property cannot be tested;
- successive-child-block evidence while ancestor `block.number` repeats;
- native-provider parity under the Base S1 profile;
- local mock/provider tests for revert, malformed return, and forbidden
  fallback; and
- compiler, ABI, and staticcall evidence for the selected Vyper integration.

The largest observed child-block gap or cadence is evidence, not a protocol
maximum or time guarantee. Stage A must stop if the critical source semantics
cannot be tested faithfully.

### Phase A8 — Specify state-safe rollout and rollback

For Base and Robinhood separately, define:

- old and new artifact set;
- registration and call graph before activation;
- the single activation boundary;
- initialization and verification of the immutable action-block source;
- whether mixed versions are possible;
- abort assertions;
- rollback boundary;
- behavior for transactions in flight;
- event and monitoring requirements;
- permanent live-version exception ownership and operational implications; and
- proof that no permanent chain-specific source is created.

For Base, require:

- the deployed Ledger address, bytecode, ABI, configuration, and behavior remain
  unchanged;
- no Base migration, registry action, state import/export, convergence
  deadline, or rollback plan is created by S5;
- the source repository clearly distinguishes current live Base evidence from
  the new forward canonical source; and
- the component matrix records why permanent live-bytecode divergence is safer
  than migrating non-enumerable accounting state.

For Robinhood, require:

- a fresh Ledger deployment with no imported Base state;
- the approved action-block source established and verified before any
  state-bearing user action;
- fail-closed behavior on a missing, malformed, or wrong source;
- abort before activation if the provider, ArbSys, ABI, runtime hash, or
  manifest assertion differs;
- rollback only before the first state-bearing action unless a separately
  reviewed state migration exists; and
- no claim that a provider can be swapped casually after Ledger has state.

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

0. **Owner-direction validation:** confirm that Stage A evidence supports the
   selected same-execution-block property, Robinhood child-block source, and
   explicit non-goals. If not, return to the owner rather than substituting
   another policy.
1. **Abstraction shape:** immutable generic `ActionBlockClock` provider,
   immutable native/external-source helper in Ledger, or another smaller
   reviewed generic boundary.
2. **Clock-source contract:** exact native and ArbSys interfaces, addresses,
   constructor/immutable inputs, validation, failure behavior, and prohibition
   on fallback.
3. **Current arming semantics:** preserve or separately change the existing
   lower-risk-touch and checked-higher-risk ordering behavior.
4. **High-risk action set:** canonical protected actions and any explicit
   exclusions.
5. **Underscore policy:** preserve, remove, or revise the current user
   classification exemption, noting Underscore is absent from the initial
   Robinhood launch.
6. **Identity policy:** canonical user, caller, delegate, recipient, keeper,
   liquidator, and zero-address semantics.
7. **External housekeeping policy:** authorized callers, caller-supplied risk
   flags, griefing controls, and Deleverage compatibility.
8. **Configuration and compatibility:** treatment of
   `shouldCheckLastTouch`, events, views, defaults, constructor/ABI, and
   diagnostics.
9. **Locked and paused behavior:** lock enforcement and fail-closed pause and
   clock-source failure behavior.
10. **Base live-version exception:** no migration or convergence; record the
    deployed artifact retained, technical cause, accepted risk, approval, and
    operational implications.
11. **H-01/S4 sequence:** exact integrated dependency and overlapping-file
    baseline for Stage B.
12. **Stage B ownership:** exact allowed production, interface, provider, test,
    fixture, ABI, and record files.
13. **Evidence bar:** official and live ArbSys evidence, artifact/storage/gas
    checks, targeted suites, S1/S2, full suite, testnet soak, and external-audit
    decision.

The approval record must name each decision, date, approver, evidence commit,
and any conditions. “Proceed,” approval of this brief, or approval of another
slice is not sufficient.

If no answer is provided, the default is:

- no Stage B;
- no change to live Base policy;
- no Robinhood Ledger deployment or guard activation;
- no fallback to the ancestor-number guard or disabled guard; and
- no migration or deployment work.

## Proposed Stage B ownership

The exact file set is a Checkpoint 0 decision. Depending on the selected
architecture, it may include a strict subset of:

### Production and interfaces

- `contracts/data/Ledger.vy`
- one new narrowly named generic action-block provider contract, only if
  explicitly selected;
- one new provider interface, only if explicitly selected;
- `contracts/core/Teller.vy`, only if Stage A proves a necessary call-contract
  change rather than ordinary consumption of the revised Ledger;
- `contracts/data/MissionControl.vy` and
  `contracts/config/SwitchboardDelta.vy`, only if the existing Boolean cannot
  safely remain the enable/disable control;
- `contracts/config/DefaultsLocal.vy`, only for approved local-fixture
  compatibility; and
- interfaces required by the approved action-block call graph.

### Tests and fixtures

- `tests/conf_core.py`
- `tests/data/test_ledger.py`
- `tests/config/test_switchboard_delta.py`
- relevant Teller domain tests
- relevant CreditEngine and Stability Pool tests
- new focused S5 tests under an owner-approved path
- provider/source unit and failure tests under an owner-approved path
- `tests/clock/test_clock_profiles.py`, only if new generic harness coverage is
  required

### Generated artifacts and records

- only ABIs corresponding to approved changed contracts
- `docs/chains/rh/ledger-guard-implementation-record.md`

Stage B does not own:

- future `contracts/config/DefaultsRobinhood.vy`;
- `contracts/config/DefaultsBase.vy`;
- `scripts/params/general.py` or CAD-001 work;
- any historical migration or manifest;
- Track 7’s reserved `0030_Track6S5LedgerGuard.py`;
- S4-only cooldown/context code;
- dependency files;
- S2 inventory files before Stage C;
- `rh-summary.md`;
- Underscore source; or
- live execution.

Teller, MissionControl, SwitchboardDelta, Defaults interfaces, and config
structs are prohibited unless Checkpoint 0 names the exact necessary line and
rejects the unchanged-call/config alternative. No S5 file may contain
Robinhood-branded production logic or `chain.id`.

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

- ordinary-EVM deployments use native execution `block.number`;
- Robinhood uses the configured ArbSys child-block identity and never its
  ancestor-height `block.number`;
- no `chain.id` or Robinhood-specific production branch exists;
- an unauthorized caller cannot select, change, arm, clear, bypass, or weaken
  the clock or guard;
- user identity follows the approved action table;
- lower-risk arming and housekeeping ordering exactly preserve approval;
- two checked actions for one user in one child block cannot both succeed;
- a checked action in the next child block is not rejected merely because the
  ancestor number or timestamp repeats;
- source failure or malformed data reverts rather than falling back;
- revert behavior does not leave partial `lastTouch` state;
- different users remain isolated;
- Underscore behavior exactly matches approval;
- external housekeeping cannot be used as an unapproved griefing or bypass
  surface;
- locked-account enforcement remains active in every mode;
- paused behavior fails closed as approved;
- old protection is not disabled before new protection is active; and
- unrelated accounting and economic semantics do not change.

### Phase B3 — Preserve Base state and establish fresh Robinhood state

For Base:

- prove no production, ABI, migration, registry, defaults, governance, or live
  deployment file changes the current Base Ledger;
- record its deployed runtime and address as retained evidence;
- do not create a state-enumeration or convergence procedure;
- do not set a future migration deadline; and
- record permanent live-version divergence with its technical cause and
  accepted operational implications.

For Robinhood:

- deploy the approved new Ledger only as a fresh component;
- preserve all existing accounting storage layout and semantics unless a
  separately approved line is indispensable to the clock boundary;
- initialize the immutable provider/source from the reviewed manifest;
- prove `lastTouch` stores only the approved action-block identity;
- preserve the Teller-only call and locked-account assertion;
- activate no user path until the source and runtime assertions pass; and
- treat any proposal to import Base Ledger state as an immediate stop.

No local fixture may be presented as Base migration evidence because S5 has no
Base migration.

### Phase B4 — Implement explicit policy configuration

If configuration changes are approved:

- use an explicit immutable provider/source contract;
- validate the mode and source at construction;
- prohibit a mutable source unless a separate security and migration decision
  expressly approves it;
- expose diagnostic views needed by operators;
- preserve timelock/governance authority;
- prevent unsupported source/mode combinations;
- define initialization for Base and local fixtures;
- leave Robinhood values to S6 unless Checkpoint 0 expressly grants a narrow
  exception; and
- document how `shouldCheckLastTouch` continues to enable or disable only the
  same approved block-identity check.

Do not introduce seconds, durations, freshness windows, or another pacing
policy into this configuration.

### Phase B5 — Build the canonical security matrix

Tests must cover at least:

| Dimension | Required cases |
|---|---|
| current comparison | all Phase A1 sequences under current policy |
| native action block | repeat, `+1`, `+2`, `+4`, `+60`; source agrees with native Base-profile execution block |
| Robinhood action block | same child block, next child block under repeated ancestor number, successive child blocks, source failure/malformed return, no fallback |
| transaction | same child-block transactions, successive-child-block transactions, nested call, revert/reset |
| risk order | low→high, high→low, high→low→high, high→high |
| identity | user, caller, delegate, recipient, receiver, keeper, liquidator, zero |
| caller authority | Teller internal route, valid Ripe external route, invalid caller |
| action | every approved high-risk Teller action |
| user isolation | same user and two-user interleaving |
| Underscore | wallet, vault, ordinary user, caller/user distinction |
| lock/pause | locked in every mode; relevant contracts paused |
| policy | existing enable/disable behavior, source/mode inputs, invalid source/mode, immutable selection |
| coexistence | retained live Base artifact and new Robinhood artifact; no convergence assumption |
| deployment | fresh Robinhood initialization, provider/source assertion, pre-state rollback boundary |

Test names must state the protected property. A test that merely reproduces a
revert without proving why does not close a security requirement.

### Phase B6 — Validate EVM semantics and artifacts

For the action-block source:

- inspect compiler output and calldata/return decoding for every staticcall;
- prove native and ArbSys source behavior in the approved environments;
- prove missing, reverting, malformed, and wrong-mode sources fail closed;
- prove there is no implicit `chain.id` dispatch or ancestor-number fallback;
- measure the added gas on every protected Teller path; and
- do not suppress provider or framework discrepancies.

For every changed production contract:

- regenerate only the corresponding ABI;
- compare creation and runtime artifacts;
- compare storage layouts;
- record constructor and immutable differences;
- verify shared source under Base and Robinhood parameter profiles;
- prove no production import from `contracts/mock/**` or
  `contracts/testing/**`; and
- record all bytecode differences with causes.

The retained live Base Ledger is compared as deployment evidence, not expected
to equal the revised Robinhood runtime. Creation input and source provenance
for the new forward artifact remain canonical and reproducible.

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
- permanent Base live-version-exception provenance and operational
  implications;
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
- live Base Ledger state and deployment remain untouched;
- fresh Robinhood Ledger initialization and action-block source are proven;
- same-child-block identity protects the selected threat;
- low-risk, identity, Underscore, external-housekeeping, lock, and pause
  semantics match approval;
- native and ArbSys source evidence is authoritative;
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
- add only reviewed action-block provider/source identifiers required by the
  inventory schema;
- preserve stable IDs and semantic owner;
- record the changed forward Ledger source and unchanged deployed Base
  artifact;
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
- the merge recommendation names all remaining Track 7, S6, audit, permanent
  Base-exception, and Robinhood launch gates.

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
generation. S5 supplies the approved action-block provider/source constructor
inputs, `shouldCheckLastTouch` compatibility, and manifest constraints; it does
not choose unrelated Robinhood parameters.

### S7–S10

S5 must not absorb timelock/registry validation, lifecycle capacity, disabled
integration assertions, or CAD reporting merely because they consume related
configuration.

### Track 7

Track 7 owns migration namespace, execution planning, manifest schema,
verification tooling, and rehearsal. S5 supplies reviewed artifacts and exact
assertions for reserved migration `0030_Track6S5LedgerGuard.py`, including the
fresh Robinhood Ledger source, provider/source identity, ArbSys result, and
permanent no-Base-migration disposition.

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
- the selected abstraction and source/failure architecture;
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
- ArbSys availability or child-block semantics cannot be proven;
- same-child-block behavior cannot be tested faithfully;
- the selected source can fail open or fall back to ancestor `block.number`;
- the proposed design introduces time, freshness, or cross-block pacing;
- a valid Ripe caller can grief or bypass the policy;
- locked-account protection weakens in any mode;
- the plan requires migrating or replacing the deployed Base Ledger;
- any Base migration or convergence deadline appears;
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
- compiler, ABI, and staticcall evidence for the selected action-block source;
- approved Robinhood ArbSys and secondary EVM validation;
- ABI generation and exact diff checks;
- storage-layout comparison;
- creation/runtime bytecode comparison;
- unchanged deployed Base Ledger evidence;
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
- Base no-migration evidence;
- action-block architecture comparison;
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
- unchanged Base deployment and fresh Robinhood Ledger evidence;
- security-matrix results;
- native/ArbSys action-block authority;
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
- permanent Base live-version exception and Robinhood deployment
  prerequisites;
- unresolved risks and owner actions; and
- explicit statement that merge readiness does not authorize deployment,
  activation, migration execution, or launch.
