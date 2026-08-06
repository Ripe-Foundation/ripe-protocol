# Track 6: Shared Block-Clock Specification

**Status:** Draft for owner review; do not launch before the Track 3 merge precondition is satisfied

**Prepared:** 23 July 2026

**Planning baseline:** `1a87e59ede2b0a08fc37c24af7f54fd864f3079f`

## Fresh-agent instruction

Treat this document as the task contract. Convert the reviewed and integrated Track 3 clock inventory into an implementation-ready specification for one canonical Ripe contract source that supports Base, Robinhood, and future EVM deployments through shared logic and explicit configuration.

This track is specification-only. Do not modify production contracts, tests, defaults, parameter-generation scripts, migrations, CI, or `docs/chains/rh-summary.md`. Do not silently approve provisional values or owner-level security and tokenomics decisions. The implementation and test-harness changes defined by this track must be delivered through separate follow-on branches and reviews.

Use a dedicated branch or worktree named `rh-track-6-block-clock-spec`. Do not edit files owned by another Robinhood track. Commit only the approved specification deliverables to the track branch; never push directly to or merge into the shared `rh` or `master` branch. The owner reviews and integrates the work.

## Hard launch precondition: Track 3 must merge first

This brief may be reviewed and committed before Track 3 is integrated, but Track 6 must not launch from the planning baseline above.

Before creating the Track 6 worktree, verify that:

1. the reviewed Track 3 deliverables have been merged into the local `rh` integration branch;
2. these files exist in that exact integration commit:
   - `docs/chains/rh/block-number-inventory.md`; and
   - `docs/chains/rh/component-matrix.md`;
3. the integrated inventory contains its semantic inventory, exact-occurrence coverage ledger, indirect cadence-dependency section, timestamp context appendix, decision register, and validation record;
4. the integrated component matrix contains the stable component IDs referenced by the inventory; and
5. the owner confirms that the Track 3 review cycle is closed.

If any condition is false, stop. Do not read a floating Track 3 worktree as the authoritative launch input, copy its files into Track 6, or create the Track 6 branch from a pre-merge `rh`.

## Worktree bootstrap

Only after the Track 3 merge precondition is satisfied:

1. Start from `/Users/wigglez/dev/ripe-protocol`.
2. Verify that the integration worktree is clean, `rh` resolves to the reviewed integration commit, and this brief plus both Track 3 deliverables exist in that commit.
3. Record:
   - the full `rh` integration commit;
   - the commits that introduced the Track 3 deliverables;
   - the current `docs/chains/rh/block-number-inventory.md` content hash; and
   - the current `docs/chains/rh/component-matrix.md` content hash.
4. Confirm that branch `rh-track-6-block-clock-spec` and path `/Users/wigglez/dev/ripe-protocol-track-6-block-clock-spec` do not already exist. If either exists, stop and ask the owner; do not reuse, delete, reset, or overwrite it.
5. Create the isolated worktree from the post-Track-3 `rh` baseline:

   ```bash
   git -C /Users/wigglez/dev/ripe-protocol worktree add \
     -b rh-track-6-block-clock-spec \
     /Users/wigglez/dev/ripe-protocol-track-6-block-clock-spec \
     rh
   ```

6. Verify the new worktree's branch, commit, clean status, and inventory hashes.
7. Run every subsequent command and make every edit inside `/Users/wigglez/dev/ripe-protocol-track-6-block-clock-spec`.

Do not modify or commit from the integration worktree. Leave the Track 6 worktree and branch in place for owner review; do not remove or merge them yourself.

## Objective

Produce:

1. `docs/chains/rh/shared-block-clock-specification.md`; and
2. `docs/chains/rh/block-clock-validation-plan.md`.

Together, the documents must:

- disposition every stable clock and cadence ID from the integrated Track 3 inventory;
- define the EVM-observed-number models used for Base and Robinhood testing;
- state the intended wall-clock or semantic meaning of every retained duration, rate, guard, snapshot, and telemetry use;
- define proposed Base and Robinhood values, bounds, rounding rules, and owner approvals;
- specify every shared-source change without a `chain.id` branch;
- define one dual-profile validation harness for identical compiled artifacts;
- define a checked inventory or CI guard;
- separate configuration-only work from shared contract, tooling, defaults, migration, and test changes;
- record live Base bytecode and rollout implications; and
- split implementation into reviewable follow-on changes.

The output must be detailed enough that implementation agents do not need to rediscover Track 3 facts or make architecture decisions while editing code.

## Controlling constraints

- Follow [`../rh-summary.md`](../rh-summary.md), especially Section 2.
- Treat the integrated Track 3 inventory and component matrix as authoritative for stable IDs and audited scope.
- Preserve one canonical production source for Base and Robinhood.
- Prefer constructor arguments, storage, governed parameters, defaults, and migrations over hardcoded chain cadence.
- Do not add `chain.id` branches or Robinhood-specific production-contract variants.
- Do not mechanically convert every `block.number` use to `block.timestamp`.
- Retain block-number behavior where repeated and jumping values preserve acceptable semantics.
- Redesign a shared behavior only where the inventory demonstrates a semantic or configurability failure.
- Keep timestamp-denominated behavior in seconds unless a separately proven defect requires a change.
- A disabled Robinhood integration still needs an explicit omission or negative-registration test; disabled does not mean unaudited.
- Provisional conversions from Track 3 are evidence-backed candidates, not approved production parameters.
- Source status, per-chain configuration, and live deployed bytecode are separate facts.

The controlling Hightop Notes source is:

`/Users/wigglez/dev/hightop-notes/random/hood/hood-chain-executive-summary.md`

If the local checkout is unavailable, use the [GitHub copy](https://github.com/mickhagen/hightop-notes/blob/main/random/hood/hood-chain-executive-summary.md). If neither source is accessible, stop rather than silently skipping the selected architecture. Do not import the superseded federated design from `random/hood/hood-chain.md`.

## Required repository reading

Read the current integrated versions of:

- `docs/chains/rh-summary.md`
- `docs/chains/rh/block-number-inventory.md`
- `docs/chains/rh/component-matrix.md`
- `docs/chains/rh/track-3-phase-0-inventory.md`
- `contracts/tokens/modules/Erc20Token.vy`
- `contracts/data/Ledger.vy`
- `contracts/data/MissionControl.vy`
- `contracts/modules/LocalGov.vy`
- `contracts/modules/TimeLock.vy`
- `contracts/modules/Contributor.vy`
- `contracts/vaults/RipeGov.vy`
- `contracts/priceSources/CurvePrices.vy`
- `contracts/core/Deleverage.vy`
- `contracts/core/BondRoom.vy`
- `contracts/core/Lootbox.vy`
- `contracts/core/EndaomentPSM.vy`
- `contracts/core/CreditEngine.vy`
- `contracts/core/AuctionHouse.vy`
- `contracts/core/Teller.vy`
- `contracts/registries/RipeHq.vy`
- `contracts/registries/modules/AddressRegistry.vy`
- `contracts/config/BondBooster.vy`
- `contracts/config/SwitchboardAlpha.vy`
- `contracts/config/SwitchboardBravo.vy`
- `contracts/config/SwitchboardCharlie.vy`
- `contracts/config/SwitchboardDelta.vy`
- `contracts/config/SwitchboardEcho.vy`
- `contracts/config/DefaultsBase.vy`
- `contracts/config/DefaultsLocal.vy`
- `config/BluePrint.py`
- `scripts/params/params_utils.py`
- `scripts/params/general.py`
- `scripts/params/regenerate_defaults.py`
- current generated parameter reports under `scripts/params/`
- current Base migration and manifest evidence; and
- every test and configuration path named by the integrated inventory.

Use repository search to verify that the integrated inventory still covers every exact production `block.number` occurrence. Do not renumber Track 3 IDs or regenerate its artifacts inside this track. If the launch commit contains a production-contract delta after the Track 3 audit, stop and require Track 3 reconciliation before specifying the changed surface.

## Phase A: Freeze the observed-number models

Define the clock models against which the specification and later tests will be judged.

### Evidence requirements

- [ ] Record the retrieval date and current primary source for Base block-number semantics.
- [ ] Record the retrieval date and current primary source for Robinhood's EVM `NUMBER` semantics.
- [ ] Distinguish RPC-visible L2 block height, EVM `block.number`, timestamp, and any underlying L1-origin estimate; do not treat similarly named fields as interchangeable.
- [ ] Record observed repeat lengths and jump sizes from an approved public or test environment where reproducible.
- [ ] Separate documented guarantees from empirical observations and conservative stress assumptions.
- [ ] Do not present the largest observed jump as a protocol maximum unless a current authoritative source guarantees it.

No deployment or signed transaction is authorized. Use public documentation, existing verified contracts, read-only RPC calls, or already-approved evidence. If proving EVM opcode behavior requires a new onchain probe, stop and request a separately approved probe plan.

### Required profiles

Define at least:

1. **Base ordinary profile:** normal Base cadence and boundary behavior.
2. **Robinhood repeat profile:** many state-changing calls or transactions observe the same number.
3. **Robinhood advance-by-one profile:** the observed number advances exactly one.
4. **Robinhood bounded-jump profile:** the number advances by each owner-approved representative jump.
5. **Boundary-skip profile:** a jump crosses an opening, expiry, refill, auction, epoch, lock, or cooldown boundary.
6. **Stress-jump profile:** a conservative jump larger than the ordinary observed range to test safe failure or catch-up behavior.
7. **Mixed-clock profile:** block number and timestamp are controlled independently enough to test intentional seconds-versus-number boundaries.

The specification must name exact synthetic sequences for each profile. If the current test runtime cannot independently model repeated numbers, jumps, and timestamp movement, document the limitation and recommend a narrowly scoped harness mechanism. Do not install a new runtime or implement the harness in this track.

## Phase B: Disposition the complete Track 3 inventory

The specification must contain one authoritative table row for every integrated:

- `BN-*` semantic inventory ID;
- indirect cadence-dependent ID such as `CAD-*`; and
- timestamp-context `TS-*` ID.

At the drafting reference, Track 3 contains `BN-001` through `BN-032`, `CAD-001`, and `TS-001` through `TS-011`. The integrated files control if the reviewed set changes before launch.

### Required fields for every `BN-*` and `CAD-*` row

- stable ID;
- component-matrix IDs;
- contract, function, setter, validator, and configuration source;
- semantic category;
- current repository or dated Base value;
- evidence status of the live Base value;
- intended wall-clock duration, economic rate, security property, or telemetry meaning;
- Base target value and immutable/governed bounds;
- Robinhood target value and immutable/governed bounds;
- conversion basis and rounding rule;
- repeat, `+1`, ordinary-jump, boundary-skip, and stress-jump behavior;
- retained, configuration-only, shared-source change, disabled/omitted, or separate-spec disposition;
- exact proposed source/config/defaults/migration/tooling changes;
- tests and clock profiles;
- owner/approver;
- approval status;
- live Base bytecode consequence; and
- implementation slice and dependency.

### Required fields for every `TS-*` row

- stable ID;
- seconds-domain purpose;
- block-number interaction, if any;
- retained, disabled, or separate-defect disposition;
- required mixed-clock or omission test;
- configuration/default implications; and
- explicit confirmation that no Robinhood-only conversion is required.

Do not close an ID with “no change” without stating why repeated and jumping numbers are acceptable or why the integration is absent on Robinhood.

## Phase C: Resolve every Section 2 surface

The following subsections are mandatory. They organize the specification but do not replace the row-by-row inventory disposition.

### Shared semantic or configurability failures

Specify, without implementing:

- the shared replacement policy for the Ledger same-number guard;
- one consistent configurable design for the duplicated Deleverage/SwitchboardDelta cooldown ceiling;
- a call-context-safe replacement for any Deleverage exception that currently relies on same-number identity;
- the shared parameterization of the Lootbox minimum send interval currently enforced through `ONE_DAY`; and
- the indirect cadence-reporting correction and inactive-Robinhood posture identified by `CAD-001`.

For every shared change, include:

- threat or failure being corrected;
- rejected designs;
- storage, constructor, setter, validator, event, ABI, defaults, migration, and governance implications;
- backward compatibility;
- Base and Robinhood deployment implications;
- test properties; and
- audit or security-review boundary.

Do not combine the Ledger decision with the mechanical hardcode changes if its threat model remains unapproved. A separate Ledger implementation slice may remain blocked while approved Lootbox, cooldown, reporting, and harness slices proceed.

### Per-number rates and points

Disposition:

- RipeGov points;
- Lootbox deposit points;
- Lootbox borrow points;
- `ripePerBlock` monetary emission; and
- every indirect per-number economic rate.

For each:

- trace whether elapsed-number scaling affects absolute economics, relative allocation only, thresholds, claim timing, or monetary supply;
- quantify Base and Robinhood wall-time behavior under the approved profiles;
- state whether configuration can preserve intent or a shared normalization change is required;
- define rounding, accumulated remainder, and jump attribution;
- test balance or rate changes immediately before and after a jump; and
- require tokenomics/rewards approval for economic outputs.

Do not assume that multiplying a Base rate by a nominal cadence ratio is sufficient. Model repeat and jump attribution and state who receives value accumulated across the gap.

### Token, governance, registry, and Switchboard timelocks

Cover:

- token HQ-change delays and bounds;
- LocalGov delays and bounds;
- every deployable `TimeLock` inheritor, including action confirmation and expiration;
- Contributor key-action delays alongside timestamp-based vesting;
- RipeHq capability changes;
- AddressRegistry add, update, and disable delays; and
- absolute-number operator inputs.

The specification must:

- list every deployable inheritor rather than treating `TimeLock` as one configuration row;
- define Base and Robinhood values and bounds;
- test before-open, exact-open, last-valid, exact-expiry, and jump-past-expiry behavior;
- define minimum confirmation-window headroom relative to the stress-jump profile;
- resolve whether one registry delay remains acceptable for add, update, and disable;
- preserve seconds-domain telemetry where appropriate; and
- include the RipeHq plus AddressRegistry sequence used to register a CCIP pool as a Department.

### Borrow and PSM interval capacity

Cover:

- per-user CreditEngine borrow capacity;
- EndaomentPSM mint capacity;
- EndaomentPSM redeem capacity; and
- enabled, disabled, or omitted PSM outcomes from Track 4.

Specify:

- intended wall-clock interval;
- exact refill boundary;
- behavior across repeated numbers and multi-number jumps;
- whether unused capacity carries over;
- whether a jump refills once or for multiple elapsed intervals;
- separate mint and redeem buckets;
- governed parameter-change behavior mid-interval; and
- combined tests showing timestamp interest accrual remains independent from number-based capacity.

Do not decide the USDG/PSM launch posture in this track. Consume an integrated Track 4 decision if available or mark the PSM-specific activation fields pending Track 4 and owner.

### Auctions, bonds, locks, and cooldowns

Cover:

- AuctionHouse delay, duration, eligibility, end, and discount progression;
- BondRoom epoch entry, preview/execution parity, restart, catch-up, and skipped epochs;
- BondBooster absolute expiry;
- RipeGov locks, bonus calculations, withdrawals, and early release; and
- Deleverage cooldown enforcement and exceptions.

Specify exact behavior at:

- repeated numbers;
- `+1`;
- start minus one, start, and start plus one;
- end minus one, end, and end plus one;
- one-epoch and multi-epoch jumps;
- a jump over the entire available window; and
- a parameter change during an active period.

The owner must decide the intended Deleverage maximum in wall time before the spec assigns final Base and Robinhood values. Preserve the explicit option space, including the approximately four-hour Base behavior implied by `7_200` and the approximately one-day intent stated by the existing comment.

### Price-source snapshots and mixed clocks

Cover:

- Curve snapshot staleness, same-number suppression, danger accumulation, and dynamic-rate coupling;
- timestamp-based Chainlink and other oracle staleness;
- timestamp-based snapshot sources;
- disabled price integrations; and
- `CAD-001` raw, displayed, and runtime-effective units.

The specification must:

- keep Curve and its dynamic-rate coupling explicitly inactive on Robinhood unless a separate feature-reenable specification approves them;
- define negative deployment/registration assertions;
- avoid converting timestamp-based oracle staleness into block counts;
- test future timestamps, stale timestamps, repeated numbers, and jumps in the correct domains; and
- define the parameter-report formatter correction and raw/display/runtime regression test required before generated parameter reports are treated as parity evidence.

### Telemetry

For telemetry-only uses:

- retain the observed number unless a consumer requirement proves otherwise;
- state that numbers may repeat or jump;
- identify consumers that assume uniqueness or sequentiality; and
- define documentation or monitoring changes without altering protocol behavior unnecessarily.

## Phase D: Define the dual-profile validation harness

Create:

`docs/chains/rh/block-clock-validation-plan.md`

The plan must define, but not implement:

- the fixture or helper API for selecting a clock profile;
- how identical compiled contract artifacts run under Base and Robinhood profiles;
- how block number and timestamp are advanced or held independently;
- how each transaction or call records the number and timestamp it observed;
- deterministic repeat and jump sequences;
- exact boundary helpers;
- snapshot/reset isolation between scenarios;
- parameter injection for Base and Robinhood defaults;
- invariant and property-test candidates;
- unit, integration, governance-flow, and lifecycle test layers;
- expected test locations and naming;
- compatibility with the pinned titanoboa/pytest runtime;
- any Anvil or lower-level EVM fallback, with a reason and dependency boundary;
- runtime and CI cost; and
- failure diagnostics that print the stable inventory ID and active profile.

At minimum, map tests for:

- every `BN-*` and `CAD-*` ID;
- every mixed-boundary `TS-*` ID;
- all shared-source changes;
- all per-chain values and bounds;
- RipeHq/AddressRegistry CCIP Department registration;
- disabled integration non-registration;
- repeat, `+1`, ordinary jump, boundary skip, and stress jump; and
- both current Base behavior and proposed canonical behavior where live-version drift is possible.

The test plan must not depend on chain-specific production bytecode.

## Phase E: Specify the checked inventory and CI guard

The repository currently has no committed `.github` workflow, so do not assume a CI integration point exists.

Define:

- the canonical checked inventory or allowlist format;
- whether the guard is a pytest test, repository script, or both;
- the command used locally and by future CI;
- exact fixed-string occurrence counting;
- how stable IDs map to source occurrences without becoming unusably line-number brittle;
- how additions, removals, and moved occurrences require inventory review;
- how indirect cadence assumptions such as `CAD-*`, block-denominated constants, comments, defaults, and generated reports are checked;
- how timestamp-domain uses remain separate;
- allowed paths such as mocks and tests;
- failure output and remediation instructions; and
- the owner of inventory updates.

The guard must fail on an unmapped new production cadence dependency. It must not encourage developers to suppress findings by adding an ID without semantic review.

## Phase F: Produce the implementation split

In `shared-block-clock-specification.md`, define small follow-on implementation slices. At minimum, consider:

1. dual-profile test harness foundation;
2. checked inventory/CI guard;
3. Lootbox minimum-interval parameterization;
4. Deleverage/SwitchboardDelta cooldown unification and exception design;
5. Ledger portable-guard change, separately gated by security approval;
6. per-chain defaults, bounds, and per-number rate configuration;
7. timelock and registry boundary tests;
8. borrow/PSM capacity and auction/epoch tests;
9. disabled price-source assertions; and
10. `CAD-001` parameter-report correction and regression tests.

For each slice, record:

- included stable IDs and component IDs;
- exact files expected to change;
- prerequisites and owner decisions;
- whether production bytecode changes;
- Base live-version policy;
- test commands and acceptance criteria;
- review and audit needs;
- rollback or abort boundary; and
- which later slice consumes it.

Do not force unrelated semantic changes into one PR merely because they share `block.number`.

## Required decision register

The main specification must include:

| Decision | Options | Evidence | Recommendation | Affected IDs/components | Owner | Needed before | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |

At minimum, include:

- shared clock posture;
- Base and Robinhood cadence/conversion basis;
- representative and stress jump profiles;
- live Base parity or bounded drift for each shared modification;
- Ledger protected threat and replacement policy;
- Deleverage cooldown maximum wall-time intent;
- Deleverage call-context exception;
- Lootbox minimum-interval configuration design;
- RipeGov and Lootbox point attribution under jumps;
- RIPE emission rate and tokenomics;
- timelock values, bounds, expiration headroom, and registry add/update/disable policy;
- borrow and PSM interval refill semantics;
- auction and bond jump/skip policy;
- disabled price-source and dynamic-rate posture;
- `CAD-001` report correction;
- dual-profile harness mechanism; and
- inventory/CI guard integration.

Recommendations are not approvals. Use explicit `open`, `recommended`, `approved`, `rejected`, `blocked`, and `not applicable` statuses, with approval provenance and date for any non-open owner decision.

## Cross-track interface

- Track 3 owns the authoritative inventory and component IDs. Track 6 must consume the reviewed integrated files and must not renumber or rewrite them.
- Track 1 owns current Chainlink/CCIP facts. Track 6 owns only the token, RipeHq, registry, and Switchboard timing behavior used by later CCIP registration.
- Track 4 owns whether the PSM is enabled, disabled, or omitted. Track 6 specifies the interval behavior for every outcome without changing that decision.
- Track 5 does not block the clock specification.
- Track 7 deployment support will consume the approved per-chain parameter table, defaults requirements, negative-registration assertions, and validation profiles.
- If a cross-track result is not integrated, mark the affected field pending and continue every independent ID. Do not read another track's mutable worktree as release truth.

## Approval gates

Stop and obtain owner approval before:

- treating Track 3 provisional values as final;
- selecting the shared clock posture;
- selecting a Deleverage cooldown duration or exception policy;
- selecting or disabling the Ledger guard policy;
- approving RIPE emission or point-accrual economics;
- approving timelock, expiry, capacity, auction, epoch, or lock parameters;
- approving a live Base upgrade or divergence plan;
- choosing a new test runtime or CI dependency;
- changing production code, tests, defaults, scripts, migrations, generated reports, or CI;
- deploying a probe or broadcasting a transaction; or
- expanding into a Robinhood-only contract or a timestamp conversion program.

Read-only repository analysis, public documentation, read-only RPC evidence, and specification drafting may proceed without separate approval.

## Stop conditions

Stop and involve the owner if:

- the Track 3 merge precondition is not satisfied;
- the integrated inventory no longer reconciles the launch commit;
- EVM-observed-number semantics or a safe stress profile cannot be supported by current evidence;
- a proposed design requires chain-specific production source;
- a per-number economic change lacks an identified tokenomics or risk owner;
- the Ledger threat model cannot be stated precisely;
- a timelock or auction window cannot tolerate the evidence-backed jump profile;
- the current test runtime cannot model a required profile without a new dependency decision;
- a shared change creates an unplanned Base migration or custody risk;
- a timestamp-domain defect materially expands beyond this specification; or
- current code conflicts with the selected architecture.

Otherwise, record unresolved decisions and complete every independent inventory row and implementation slice.

## Validation

- [ ] The Track 6 starting commit contains the reviewed Track 3 inventory and component matrix.
- [ ] Their starting content hashes are recorded.
- [ ] Every integrated `BN-*`, `CAD-*`, and `TS-*` ID has exactly one disposition row.
- [ ] Every exact production `block.number` occurrence remains mapped by Track 3.
- [ ] Every Section 2 checklist surface is covered.
- [ ] Every per-number rate is economically traced, not merely numerically converted.
- [ ] Every deployable timelock inheritor has explicit values, bounds, and boundary tests.
- [ ] Borrow, PSM, auction, bond, lock, cooldown, and snapshot behavior cover repeat and jump profiles.
- [ ] Disabled integrations have negative deployment or registration assertions.
- [ ] Shared-source changes contain no `chain.id` branch.
- [ ] The dual-profile plan runs identical artifacts.
- [ ] Mixed timestamp/block behavior is controlled and tested in the correct units.
- [ ] The inventory guard detects direct and indirect cadence dependencies.
- [ ] Provisional recommendations and owner approvals are visibly distinct.
- [ ] Live Base version implications are recorded per implementation slice.
- [ ] No production or test code was changed.
- [ ] Markdown and whitespace checks pass.

## Completion criteria

This track is complete only when:

- both specification artifacts are complete and reproducible;
- the full integrated Track 3 inventory is dispositioned;
- the Base and Robinhood observed-number profiles are evidence-backed and concrete;
- every Section 2 duration, rate, guard, capacity, auction, lock, reward, snapshot, and telemetry surface has a proposed disposition;
- owner decisions are approved or explicitly block only the dependent implementation slices;
- the separate implementation slices can be assigned without rediscovering architecture or inventory facts;
- the next Lootbox, cooldown, harness, defaults, and guarded Ledger PRs have exact acceptance criteria;
- no code or configuration was modified; and
- the completion report identifies the exact `rh-summary.md` items eligible for owner review and closure.

Do not mark any checkbox in `rh-summary.md` yourself.
