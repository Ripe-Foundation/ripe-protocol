# Track 3: Phase-0 Block Inventory and Component Matrix

**Status:** Draft for owner review

**Prepared:** 23 July 2026

**Planning baseline:** `1bb8bd5b8837a06c818c3fb9e7b599b5dd29f2b1`

## Fresh-agent instruction

Treat this document as the task contract. Produce a complete, reproducible inventory of the shared contract clock surface and the Base-versus-Robinhood deployment component matrix.

This is an analysis and specification track. Do not modify production contracts, defaults, migrations, tests, or `docs/chains/rh-summary.md`. Do not silently decide owner-level Phase-0 choices. Make evidence-backed recommendations and surface the decisions explicitly.

Use a dedicated branch or worktree named `rh-track-3-phase-0-inventory`. Do not edit files owned by the Chainlink or Stock Token probe tracks. Commit deliverables to the track branch with clear messages; never push directly to or merge into the shared `rh` or `master` branch. The owner reviews and integrates the work.

## Worktree bootstrap

The owner must commit the approved track briefs to the `rh` integration branch before kickoff. The fresh agent is responsible for creating its own worktree:

1. Start from `/Users/wigglez/dev/ripe-protocol`.
2. Verify that the integration worktree is clean, `rh` resolves to the approved integration commit, and this brief exists in that commit.
3. Confirm that branch `rh-track-3-phase-0-inventory` and path `/Users/wigglez/dev/ripe-protocol-track-3-phase-0-inventory` do not already exist. If either exists, stop and ask the owner; do not reuse, delete, reset, or overwrite it.
4. Create the isolated worktree from the committed `rh` baseline:

   ```bash
   git -C /Users/wigglez/dev/ripe-protocol worktree add \
     -b rh-track-3-phase-0-inventory \
     /Users/wigglez/dev/ripe-protocol-track-3-phase-0-inventory \
     rh
   ```

5. Verify the new worktree's branch, commit, and clean status. Record the full starting commit in the deliverables.
6. Run every subsequent command and make every edit inside `/Users/wigglez/dev/ripe-protocol-track-3-phase-0-inventory`.

Do not modify or commit from the integration worktree. Leave the track worktree and branch in place for owner review; do not remove or merge them yourself.

## Objective

Create the two artifacts that define the first shared-contract implementation scope:

1. `docs/chains/rh/block-number-inventory.md`
2. `docs/chains/rh/component-matrix.md`

Together, they must answer:

- where Ripe depends on `block.number`;
- which uses are already configurable;
- which uses embed Base cadence or true same-number assumptions;
- which shared contracts need modification;
- which components are reused unchanged, modified, replaced, disabled, or deferred on Robinhood;
- which differences are configuration-only; and
- which unresolved decisions block implementation.

The artifacts must be detailed enough that a later agent can write the shared block-clock specification without repeating the repository audit.

## Controlling constraints

- Follow [`../rh-summary.md`](../rh-summary.md).
- Preserve one canonical, chain-portable production contract source.
- `DefaultsRobinhood` is the intended chain-specific defaults artifact; it must not contain divergent protocol logic.
- Prefer constructor arguments, storage, governed parameters, and defaults over `chain.id` branches.
- Do not mechanically convert all clocks to timestamps.
- Retain `block.number` where its semantics are acceptable on both chains.
- Treat repeated and jumping Robinhood block numbers as first-class test conditions.
- Use the component statuses exactly as defined in `rh-summary.md`: `reused unchanged`, `modified`, `replaced`, `disabled`, and `deferred`.
- A component's source status and its live deployed version are separate facts.
- The selected executive-summary architecture controls. Do not import the superseded federated design from `hood-chain.md`.

The controlling Hightop Notes source is `/Users/wigglez/dev/hightop-notes/random/hood/hood-chain-executive-summary.md`. If that local checkout is unavailable, use the [GitHub copy](https://github.com/mickhagen/hightop-notes/blob/main/random/hood/hood-chain-executive-summary.md). If neither source is accessible, stop rather than silently skipping the required architecture.

## Baseline protocol

- [ ] Record the current branch, full commit hash, working-tree status, and audit date.
- [ ] Compare the current commit with planning baseline `1bb8bd5b8837a06c818c3fb9e7b599b5dd29f2b1`.
- [ ] If production contract code changed, identify the delta before generating either artifact.
- [ ] Exclude `contracts/mock/` from the primary production inventory, but record mock/test clock dependencies separately if they affect test design.
- [ ] Record both matching-line count and exact occurrence count so repeated uses on one line are not conflated.

At the planning baseline, a sanity check found 95 matching production-contract lines, 100 exact occurrences, and 17 Vyper files. Regenerate these values; do not treat them as acceptance criteria.

Document reproducible commands that use a fixed-string search such as `rg -F 'block.number'` or a correctly escaped literal. Never use an unescaped `.` and present its broader regex matches as `block.number` results.

## Deliverable A: Block-number inventory

Create:

`docs/chains/rh/block-number-inventory.md`

### Required method

- [ ] Search all production Vyper contracts for exact `block.number` uses.
- [ ] Map existing production `block.timestamp` uses and timestamp-denominated constants in a separate context appendix, including explicit unit boundaries such as `SwitchboardDelta.DAY_IN_SECONDS`. Do not include these sites in the `block.number` totals or assume they require changes.
- [ ] Search comments, constants, constructor arguments, defaults, Mission Control fields, and generated parameter sources for cadence assumptions even where `block.number` is not on the same line.
- [ ] Trace each runtime use to the function, state variable, setter, bounds check, defaults source, and relevant tests.
- [ ] Identify duplicate constants or validation rules maintained in more than one contract.
- [ ] Distinguish current configured values from hard maximums and from comments describing intent.
- [ ] Record how each use behaves when the number:
  - remains constant across many transactions;
  - advances by one;
  - jumps forward by several increments; and
  - differs materially in wall-clock cadence between Base and Robinhood.

### Required categories

Assign every retained site one primary category:

1. configurable economic duration;
2. hardcoded economic duration;
3. per-number rate or reward accrual;
4. true same-number security guard; or
5. telemetry only.

Use secondary tags where one site participates in more than one behavior.

### Required table fields

For every site include:

- stable inventory ID;
- contract and source path;
- line and function;
- exact expression or concise description;
- primary category and secondary tags;
- state/configuration source;
- current Base value and intended wall-clock meaning, if known;
- behavior under repeated/jumping Robinhood numbers;
- risk if unchanged;
- recommended disposition;
- Base and Robinhood parameter implications;
- affected setters, validators, defaults, migrations, and tests;
- decision owner; and
- confidence/evidence notes.

### Mandatory focused findings

The inventory must explicitly resolve the implementation surface, but not the owner decision, for:

- `Lootbox.ONE_DAY`;
- `Lootbox` points, rewards, and Underscore send intervals;
- both `MAX_COOLDOWN_BLOCKS = 7_200` definitions in `Deleverage` and `SwitchboardDelta`;
- the four-hours-versus-one-day intended cooldown ceiling;
- `Ledger`'s one-action-per-`block.number` guard;
- governance, registry, and Switchboard timelocks;
- borrow and PSM interval capacity;
- auction windows and discount progression;
- RipeGov and BondRoom timing;
- price-source snapshots; and
- telemetry-only emissions.

Do not recommend changing a clock merely because it uses `block.number`. State the semantic failure or configuration need.

### Timestamp context appendix

Add a separate appendix for existing production `block.timestamp` uses and timestamp-denominated constants. For each logical use, record the contract/function, purpose, unit, configuration source, relevant tests, and whether it creates a mixed block/second boundary. Explain why it is already chain-portable or what separate review it needs. Keep this appendix outside the `block.number` inventory IDs and totals.

## Deliverable B: Component matrix

Create:

`docs/chains/rh/component-matrix.md`

### Required scope

Inventory every component relevant to a clean Robinhood deployment:

- config/defaults and Switchboards;
- core protocol contracts;
- data contracts;
- registries;
- GREEN, RIPE, and optional SavingsGreen;
- vault implementations and Stability Pool;
- price sources;
- PSM and reserve/yield dependencies;
- liquidation, insurance, rewards, and governance;
- Base-only liquidity, treasury, Underscore, and yield integrations;
- CCIP additions and token-admin requirements;
- deployment blueprints, migrations, manifests, ABI/export, and verification tooling; and
- test infrastructure required for Base and Robinhood profiles.

Derive the inventory from current contracts, defaults generation, migration history, scripts, ABIs, and the selected architecture. Do not assume that every source file is independently deployed.

### Required table fields

For each component include:

- component and deployable contract;
- source path;
- role on Base;
- intended role on Robinhood;
- status: `reused unchanged`, `modified`, `replaced`, `disabled`, or `deferred`;
- same shared source required?;
- Base configuration;
- Robinhood configuration or omission;
- external dependencies and addresses;
- clock dependencies;
- live Base version versus proposed canonical version;
- temporary/permanent divergence implications;
- unresolved decision;
- required specification;
- required tests; and
- evidence/confidence.

### Required decision coverage

The matrix must visibly surface:

- canonical shared source and live-version policy;
- `DefaultsRobinhood`;
- clock-related shared modifications;
- SavingsGreen/sGREEN inclusion or omission;
- `SimpleErc20` versus `RebaseErc20`/`SharesVault`;
- Stock Token feeds and CreditRedeem disablement;
- USDG price path and PSM enabled/disabled state;
- Endaoment yield configuration;
- unsupported Curve, Aerodrome, Underscore, treasury, and yield paths;
- GREEN/RIPE local pricing deferral;
- GREEN and RIPE CCIP pools;
- assisted registration versus `getCCIPAdmin()`;
- Solidity build/test/deployment tooling; and
- Base contracts that may remain on older live bytecode.

Do not label configuration differences as contract forks. Do not use `modified` for a component whose source is unchanged and only receives different parameters.

## Decision register

Each deliverable must contain a short decision register with:

- decision;
- available options;
- evidence;
- recommendation;
- affected components;
- owner/approver;
- needed-by point; and
- status.

At minimum, surface:

- live Base parity versus temporary or permanent live-version divergence;
- shared clock posture;
- cooldown maximum intent;
- Ledger same-number guard policy;
- SavingsGreen deployment;
- Stock Token vault;
- USDG price path;
- CCIP registration/admin path; and
- Solidity toolchain boundary.

Recommendations must not be presented as approvals.

## Cross-track interface

- Track 1 owns current Chainlink facts and the final CCIP decision. Until then, mark those matrix entries `pending Track 1`.
- Track 2 owns the behavioral Stock Token transferability result. Until then, mark the collateral transferability evidence `pending Track 2`.
- This track owns the canonical inventory IDs and matrix rows the other tracks should reference.
- Do not wait for Tracks 1 and 2 to finish. Use explicit pending fields, then provide a clean update path.

## Validation

- [ ] Every production `block.number` occurrence maps to an inventory entry.
- [ ] Existing production `block.timestamp` uses and timestamp-denominated constants are mapped separately so mixed-unit boundaries and already-correct timestamp semantics are visible.
- [ ] Inventory totals can be reproduced from documented commands.
- [ ] Every deployable or intentionally omitted Robinhood component maps to exactly one matrix row or a clearly defined grouped row.
- [ ] Every `modified`, `replaced`, `disabled`, or `deferred` status includes a reason.
- [ ] Every hardcoded cadence finding traces through both enforcement and configuration paths.
- [ ] File paths, contract names, constants, fields, and current defaults are verified against the pinned commit.
- [ ] The artifacts contain no point-in-time external address presented as current without a dated primary source.
- [ ] The selected architecture and the superseded federated design are not mixed.
- [ ] Markdown and whitespace checks pass.

## Stop conditions

Stop and involve the owner if:

- the release commit cannot be pinned;
- the selected architecture conflicts with current code in a way that changes scope;
- a component cannot be classified without choosing a new architecture;
- an apparent shared-contract change would require a Robinhood-only variant;
- the inventory reveals an unrecognized mint, governance, custody, or liquidation authority boundary; or
- completing the matrix would require guessing an owner-level decision.

Otherwise, record uncertainty and continue the inventory.

## Completion criteria

This track is complete only when:

- both artifacts are complete and reproducible;
- all current production clock sites are classified;
- the deployment inventory is fully represented;
- cross-track dependencies are explicit;
- recommendations and owner decisions are clearly separated;
- the next block-clock specification can be written directly from the artifacts; and
- the completion report identifies the exact `rh-summary.md` checkboxes eligible for owner review and closure.

Do not mark checkboxes in `rh-summary.md` yourself and do not implement the resulting contract changes.
