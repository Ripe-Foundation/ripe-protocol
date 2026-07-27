# Track 6 S6 / Track 7 H-04: Robinhood Defaults and Parameter Manifest

**Status:** Documentation-reconciliation draft for independent review. This
revision authorizes neither Phase A nor Phase B. H-01, the corrected H-02
implementation, and owner-closed Track 8 M0 are integrated. The Track 8 M1
brief is integrated, but M1 implementation remains separately gated. Phase A
is blocked until the reviewed H-03 implementation is integrated and every
other prerequisite below is satisfied. S5 remains an independent in-flight
workstream and does not supply a final source, constructor, ABI, or
`shouldCheckLastTouch` input to this brief.

**Documentation-reconciliation kickoff commit:**
`332ae2bc8e0ce4b694766d6d20759295d9267ec3`

**Kickoff tree:** `f67dc91e47331785837de879b6557b285aec3b1b`

**Reconciliation branch:** `rh-track-6-s6-track-7-h4-defaults-parameters`

**Reconciliation worktree:**
`/Users/wigglez/dev/ripe-protocol-track-6-s6-track-7-h4-defaults-parameters`

## Fresh-agent instruction

When separately authorized after the gates below close, implement one combined
workstream satisfying both:

- Track 6 slice S6, “per-chain defaults/bounds/rates”; and
- Track 7 slice H-04, “`DefaultsRobinhood` and parameter manifest.”

These are not two independent implementation tracks. They name overlapping
files and one semantic output. This brief assigns one agent and one branch to
the combined boundary so that no second agent independently creates
`DefaultsRobinhood`, a competing parameter manifest, or duplicate tests.

The work has two hard stages:

1. **Phase A — inventory and owner decision packet.** Read-only repository
   analysis and one durable evidence document. Stop for owner and independent
   review. Do not create production source, the parameter manifest, a
   generator, or tests.
2. **Phase B — conditional implementation.** Begin only after every required
   Phase A parameter and file choice is approved, every prerequisite is
   integrated, and the owner gives file-exact implementation authorization.

No approval of this brief authorizes Phase B, a production value, a contract
change, a migration, a deployment, a governance action, a signer, a
transaction, or an external write.

This documentation reconciliation does not authorize Phase A, creation of the
Phase A evidence file, baseline test execution, parameter analysis, or a
recommendation. Independent review of this complete revised brief is the only
next step authorized here.

## Why S6 and H-04 are one workstream

The integrated Track 6 specification assigns S6:

- `contracts/config/DefaultsRobinhood.vy`;
- `tests/config/test_defaults_robinhood.py`;
- the Robinhood parameter/default inventory;
- relevant parameter tooling; and
- the approved values consumed by later S7-S9 and Track 7.

The integrated Track 7 deployment specification assigns H-04:

- `contracts/config/DefaultsRobinhood.vy`;
- `config/robinhood-parameters.json`;
- `tests/config/test_defaults_robinhood.py`;
- `tests/deployment/test_network_clock_profiles.py`; and
- deterministic parameter-generation support.

Launching S6 and H-04 independently would create conflicting ownership of the
same production artifact and source of truth. This combined slice establishes
the following authority:

- the reviewed JSON manifest is the typed input and value/provenance authority;
- `DefaultsRobinhood.vy` is a deterministic generated or mechanically
  verified projection of the approved fields that belong to the canonical
  `Defaults` interface;
- deployment-only values that do not belong to `Defaults` remain typed
  manifest entries and later-slice inputs rather than being forced into the
  contract;
- the H-03 blueprint remains the graph/disposition authority, not a parameter
  store; and
- later H-05/H-08/H-09 slices consume these artifacts read-only.

No parallel S6 or H-04 branch may own any file reserved here.

## Hard sequencing and launch gates

### 1. H-01 and H-02 control the runtime and profile boundary

The reviewed H-01 payload is integrated at
`575d47b82055b42da2bddf1535d8076cd7cf4c63`. The original reviewed H-02
implementation is integrated at
`6c3052668555a7104ea12a7fb1a7c641c7e6b304`; the reviewed post-integration
correction is integrated at
`cb3fe7392c44613aaeec49bd2486369fe0da3556`. Both are ancestors of the
documentation-reconciliation kickoff commit. These two prerequisite
integrations are satisfied at this kickoff.

Phase A must consume H-02's public profile API from the then-current integrated
source. It must not copy or infer that API from a floating worktree or from
historical status prose in the H-02 evidence record.

If H-01 dependencies, the H-02 profile API, account/identity ordering, or
Base-compatibility behavior changes after bootstrap, stop and reconcile only
after review.

### 2. Track 8 controls the launch product graph

Track 8 M0 reviewed decision bytes were fixed at
`c5c8b699b229792dc61e66af35502684ea3c8155`. The final closure-record commit
is `11824aa672809ad49ad7b2f823b9fb02c6e4608b`, and the integration merge is
`e1f14ddb030c5ce3f44d4cdd54e8c6daaad41369`.
The Track 8 M1 brief is integrated at this reconciliation's kickoff commit,
but it explicitly leaves M1 implementation unauthorized.

The controlling M0 launch graph and product requirements are:

- AAPL is the only initial Stock Token; each additional Stock Token is a
  separate later release with token-specific identity, runtime, transfer,
  oracle, control, and route evidence.
- AAPL targets `$5,000` per-user and `$25,000` global exposure, converted at
  the final price freeze using the integrated formula and approved feed. The
  actual freeze price and fixed 18-decimal cap integers remain later typed
  blockers. Exactly one AAPL vault may be enabled, and every trusted or
  Department AAPL deposit route remains disabled.
- AAPL Stock use remains atomically blocked until the complete
  `M1 + M2 + M3 + M4 proof + approved M5` containment group, audit, exact
  configuration, and activation gates are complete. External settlement is
  the frontend default. The owner-approved guarded internal-settlement
  direction and partial-fill invariant are Track 8 mechanism authority, not
  an H-04 implementation choice.
- Chain-native sGREEN deposits and withdrawals are launch requirements.
  sGREEN must never receive a CCIP route.
- GREEN and RIPE CCIP are separately reviewed promotion targets within seven
  days after launch, not launch blockers. If any identity, route, authority,
  supply, accounting, monitoring, rollback, or state-independence gate is
  incomplete or late, launch and continue with CCIP disabled.
- Canonical USDG and the approved USDG/USD feed govern the EndaomentPSM launch
  target. Curve is not a PSM dependency. Redemption must be proved first and
  GREEN mint authority granted last.
- GREEN Stability Pool and RIPE governance-vault participation are launch
  requirements. Stock Tokens remain excluded from Stability Pool custody and
  swaps and from CreditRedeem extraction.
- GREEN/USDG LP and RIPE/WETH LP are launch deposit tokens with explicit
  legitimate `ltv=0`; their factory, pool, oracle, artifact, runtime, address,
  and composed-route inputs remain blockers until separately proved.
- USDG is PSM/LP-only and is not ordinary Teller collateral.
- Rewards launch globally disabled with `arePointsEnabled=false` and
  `ripePerBlock=0`. A separately reviewed activation is targeted within seven
  days and may then include AAPL depositors and AAPL-backed borrowers. Missing
  the target leaves rewards disabled; it does not promote a value
  automatically.
- Underscore and every other unsupported Base-only integration are omitted
  from the initial Robinhood launch.
- Current Base deployments remain unchanged. Any future Base cutover requires
  a separate proposal, evidence, migration design, security review, and owner
  authorization.

These M0 decisions freeze product and route requirements; they do not approve
the future Ripe/LP addresses, a vault or VaultBook ID, exact cap integers,
defaults, a manifest, implementation, deployment, configuration, activation,
signing, or a transaction. Every post-M0 value or artifact not yet proved
remains a typed blocker.

### 3. H-03 controls topology and symbolic inputs

The H-03 brief is integrated, but no H-03 Phase A evidence, implementation, or
test artifact is integrated at the documentation-reconciliation kickoff. The
active H-03 worktree reports Phase A under owner and independent review and
Phase B unauthorized. That uncommitted worktree is concurrent-ownership and
gate-status evidence only; none of its contents is controlling authority here.

Phase A for this combined slice must not begin until the reviewed H-03 Phase A
record, immutable blueprint implementation, and owned tests are integrated
into the then-current `rh`.

This combined slice consumes:

- the exact H-03 symbolic component rows;
- required/omitted/disabled/deferred/blocked dispositions;
- registry-topology constraints;
- symbolic asset and contract input names; and
- H-03 blocker IDs.

It must not add, remove, or reclassify a component. A required parameter whose
H-03 component remains blocked stays blocked here.

### 4. S3, S4, and S5 remain independently bounded

- **S3:** consume the integrated Robinhood Lootbox floor requirement and
  interval-zero Underscore posture. The shared source change is accepted and
  integrated: Robinhood uses immutable floor `7_200` and mutable interval `0`.
  The floor and interval are deployment inputs, not new `Defaults` fields.
  Live Base convergence remains separately governed and must not be inferred
  from source integration. Do not edit Lootbox or its historical migrations.
- **S4:** consume the reviewed no-code, zero-cooldown initial-launch
  disposition and initial Underscore omission. Do not add an S4 field, select a
  dormant maximum, create a constructor/config assignment, or create a
  state-changing S4 migration.
- **S5:** treat S5 as an independent in-flight workstream. Its integrated
  brief and owner packet do not close the final Ledger source input,
  constructor argument, ABI, or `shouldCheckLastTouch` value. Do not infer or
  preselect any of them from an active worktree, probe, recommendation, or
  draft. Preserve the deployed Base Ledger as the approved permanent
  live-bytecode exception and do not create a Base Ledger migration.

If S5 is not final at Phase A, record its entries as blocked. Phase B cannot
guess them.

### 5. Every value requires explicit approval

The Track 6 decision register still contains open cadence, reward, timelock,
capacity, auction, lock, and economic decisions. A recommendation is not an
approval.

Phase B cannot begin while any value included in the contract or manifest is:

- `pending`, `recommended/open`, `blocked`, provisional, or conditional;
- copied from Base merely because no Robinhood value exists;
- converted by an unapproved nominal cadence ratio;
- inferred from a comment rather than runtime semantics;
- represented with ambiguous blocks/seconds/basis-points/token units;
- a zero value used to conceal missing input; or
- an address copied from Base, a local fixture, or an unreviewed external
  source.

Omit an optional unresolved component. Block a required unresolved component.
Never invent a value to make the artifact compile.

## Documentation-reconciliation kickoff and future Phase A seal

This documentation-only reconciliation was bootstrapped from clean integrated
`rh` at exact commit
`332ae2bc8e0ce4b694766d6d20759295d9267ec3`, tree
`f67dc91e47331785837de879b6557b285aec3b1b`. Local `rh`, cached
`origin/rh`, and live `origin/rh` matched that commit. The branch and worktree
named at the top of this document were newly created from that identity. The
integration worktree was not modified.

The current worktree is reserved for this brief reconciliation and independent
review. It must not create the Phase A evidence file or begin Phase A.

Before a later Phase A kickoff:

1. Require this complete reconciled brief to be independently reviewed and
   present in the exact owner-approved `rh` baseline.
2. Verify the integration worktree is clean and local `rh`, cached
   `origin/rh`, and live `origin/rh` resolve to that same reviewed commit.
3. Verify H-01, corrected H-02, reviewed H-03 Phase A plus implementation and
   tests, owner-closed M0, the integrated M1 brief, S3, and S4 are ancestors of
   that commit.
4. Record current S5 status. If S5 is still not final, retain every
   S5-dependent value as blocked; S5 completion is not permission to infer a
   field.
5. Recheck every active worktree for exact file ownership. Do not consume,
   copy, or relabel unintegrated H-03, S5, or M1 content as approved.
6. Obtain an explicit owner instruction naming the exact Phase A baseline and
   whether this reconciliation worktree is to be continued or replaced. Do
   not silently reuse, delete, reset, overwrite, or recreate it.
7. Record the exact starting commit, tree, parent, author/committer identity,
   commit time, and SHA-256 of every controlling document.
8. Use the integrated H-01 locked environment. If the active environment does
   not match, stop or obtain separate authorization for a disposable locked
   environment. Do not alter dependency files in this track.
9. Run and record H-01's dependency gate, H-02's targeted suite, S1 clock
   profiles, S2 inventory checks and tests, integrated H-03 targeted tests,
   collection, and the serial full suite.
10. Remove task-specific temporary caches and basetemp directories after each
    command. Do not write into a shared user cache if an isolated cache is
    required.

Stop on any identity mismatch, dirty integration state, failed baseline,
missing authority document, unresolved worktree instruction, or unexpected
file owner.

## Required reading

Read every file in this section before Phase A.

### Program and owner authority

- `docs/chains/rh-summary.md`
- `docs/chains/rh/shared-block-clock-specification.md`
- `docs/chains/rh/block-clock-validation-plan.md`
- `docs/chains/rh/component-matrix.md`
- every integrated decision register in those program records
- `docs/chains/rh/minimal-contract-change-reassessment.md`
- `docs/chains/rh/robinhood-deployment-support-specification.md`
- `docs/chains/rh/robinhood-deployment-validation-plan.md`
- `docs/chains/rh/evidence/dependency-security-gate.md`
- `docs/chains/rh/evidence/network-profile-cli-implementation.md`
- `docs/chains/rh/track-7-h3-robinhood-blueprint-omissions.md`
- `docs/chains/rh/track-6-s3-lootbox-floor.md`
- `docs/chains/rh/deleverage-cooldown-security-decision.md`
- `docs/chains/rh/track-6-s5-ledger-guard.md`
- `docs/chains/rh/track-6-s5-checkpoint-0-owner-decision-packet.md`
- every additional S5 decision/evidence artifact integrated before Phase A
- integrated H-03 implementation, tests, and Phase A evidence
- `docs/chains/rh/track-8-m0-owner-decision-packet.md`
- `docs/chains/rh/stock-token-m0-evidence.md`
- `docs/chains/rh/stock-token-vault-change-specification.md`
- `docs/chains/rh/stock-token-vault-change-validation-plan.md`
- `docs/chains/rh/track-8-m1-exact-receipt.md`
- `docs/chains/rh/usdg-psm-decision.md`

Also read
`/Users/wigglez/dev/hightop-notes/random/hood/hood-chain-executive-summary.md`.
If the local Hightop Notes checkout is unavailable, use the repository source
identified by `rh-summary.md`. If neither is accessible, stop rather than
silently skipping the required architecture input.

### Defaults and configuration authority

- `interfaces/Defaults.vyi`
- `interfaces/ConfigStructs.vyi`
- `contracts/config/DefaultsBase.vy`
- `contracts/config/DefaultsLocal.vy`
- `contracts/data/MissionControl.vy`
- `contracts/config/SwitchboardAlpha.vy`
- `contracts/config/SwitchboardBravo.vy`
- `contracts/config/SwitchboardCharlie.vy`
- `contracts/config/SwitchboardDelta.vy`
- `contracts/config/SwitchboardEcho.vy`
- integrated `config/robinhood_blueprint.py`

### Consumers and deployment tooling

- every constructor or initializer that accepts `Defaults`;
- every function that reads the structs returned by `Defaults`;
- `scripts/utils/deploy_args.py`
- `scripts/utils/migration.py`
- `scripts/utils/migration_runner.py`
- `scripts/utils/migration_helpers.py`
- `scripts/params/regenerate_defaults.py`
- `scripts/params/run_all.py`
- `scripts/params/params_utils.py`
- `scripts/params/general.py`
- all current Defaults, MissionControl, Switchboard, asset-config, rewards,
  Stability Pool, RipeGov, PSM, and deployment tests.

### Parameter and live-evidence inputs

- committed Base parameter reports under `scripts/params/`;
- the committed Base manifest and relevant migration history;
- Track 3 inventory and component matrix;
- Track 4 USDG/PSM evidence;
- Track 6 S1/S2/S3/S4/S5 evidence;
- Track 8 exact-token, Base exposure, and graph evidence; and
- any separately approved, sanitized read-only evidence integrated before
  bootstrap.

Historical Base values are comparison evidence, not Robinhood defaults.

## Exact ownership

### Phase A owns exactly one new evidence file

- `docs/chains/rh/evidence/robinhood-defaults-parameters-phase-a.md`

No other file may change before the Phase A checkpoint is approved.

### Conditional Phase B ownership

The default proposed implementation boundary is:

- `contracts/config/DefaultsRobinhood.vy`
- `config/robinhood-parameters.json`
- `tests/config/test_defaults_robinhood.py`
- `tests/deployment/test_network_clock_profiles.py`
- one deterministic Robinhood-only generator selected at Phase A; the
  preferred candidate is
  `scripts/params/generate_robinhood_defaults.py`
- the Phase A evidence file above, updated in the same commit when an approved
  value, disposition, or generator conclusion changes.

The proposed generator path is not approved by this brief. Phase A must compare:

1. a new deterministic, network-free Robinhood generator;
2. a narrowly parameterized refactor of
   `scripts/params/regenerate_defaults.py`; and
3. checked-in manual source plus a deterministic parity verifier.

Recommend option 1 unless evidence shows unavoidable duplication or a
consumer incompatibility. The current Base generator performs live Base
reads, embeds Base addresses and block constants, and writes
`DefaultsBase.vy`; reusing it without a hard input/output separation is
prohibited.

If Phase A requires a different file, stop and obtain file-exact approval
before creating it.

### Prohibited files

This workstream must not change:

- `contracts/config/DefaultsBase.vy`;
- `contracts/config/DefaultsLocal.vy`;
- `interfaces/Defaults.vyi`;
- `interfaces/ConfigStructs.vyi`;
- `config/BluePrint.py`;
- integrated H-02 or H-03 source/tests;
- `scripts/params/run_all.py`;
- `scripts/params/params_utils.py` or `scripts/params/general.py` while S10 owns
  the CAD reporting correction;
- any production core, vault, token, price-source, Ledger, PSM, or governance
  contract other than the new `DefaultsRobinhood.vy`;
- any ABI;
- any migration or migration history;
- any manifest other than the new parameter manifest;
- `rh-summary.md`;
- S3, S4, S5, Track 8, or Track 1 records;
- dependency files; or
- any external repository.

An apparent need to change one of these files is a stop condition and owner
decision, not permission to broaden the slice.

## Objective

Produce the smallest deterministic Robinhood configuration artifact that:

1. implements the existing canonical `Defaults` interface without adding
   divergent protocol logic;
2. derives every emitted value from one reviewed typed manifest;
3. preserves unit meaning under Robinhood block behavior;
4. represents the selected initial graph and its disabled/blocked surfaces
   exactly;
5. separates initial launch values from later governance actions;
6. contains no Base address or unreviewed fallback;
7. keeps S4's no-code disposition and the live Base S5 exception intact;
8. changes no existing Base artifact or behavior;
9. is reproducible without RPC, secrets, mutable environment values, or
   current wall-clock state; and
10. supplies later Track 7 slices with fail-closed typed inputs rather than
    executable deployment authority.

This is a configuration/defaults slice, not a protocol redesign.

## Required manifest semantics

`config/robinhood-parameters.json` must be schema-validated by Phase B tests
and must distinguish at least:

- `launch_initial`;
- `fast_follow`;
- `deployment_assertion_only`;
- `disabled`;
- `omitted`;
- `blocked`;
- `not_applicable`; and
- `unresolved`.

Every entry must include:

- stable parameter ID;
- H-03 component ID or cross-track owner;
- destination artifact and exact field path;
- semantic description;
- raw integer/string/address value when approved;
- unit and denominator;
- whether the unit is blocks, seconds, basis points, token base units,
  percentage allocation, boolean, address, registry ID, or hash;
- source/evidence citation and source commit;
- owner and reviewer class;
- approval status, date, and provenance;
- launch phase;
- prerequisite/blocker IDs;
- whether zero is a legitimate value;
- Base comparison value, if relevant, labeled evidence-only;
- conversion rule and rounding direction, if converted;
- expected generated-source representation;
- downstream consumers; and
- invalidation triggers.

The schema must reject:

- missing fields;
- duplicate IDs or destination paths;
- unknown status/unit values;
- placeholder strings;
- unapproved production values;
- zero-as-missing;
- Base/local addresses in Robinhood fields;
- unresolved values included in generated source;
- percentages whose allocations do not conserve the required denominator;
- block values without an approved cadence basis;
- seconds values mislabeled as blocks;
- address-shaped literals in narrative fields;
- fast-follow values silently used as launch defaults; and
- deployment-only inputs forced into a non-existent `Defaults` field.

The generated Vyper source must contain no provenance or status logic.
Governance and deployment tooling consume the manifest, while the contract
returns only approved canonical interface values.

## Minimum-change rules

### 1. Apply the minimum-change order

For every requirement, prefer in order:

1. no production change;
2. typed manifest-only configuration;
3. existing shared behavior;
4. disabled, omitted, or deferred functionality; and
5. only then the smallest explicitly approved production source change.

`DefaultsBase.vy` must remain unchanged. Any future
`DefaultsRobinhood.vy` must implement the unchanged canonical `Defaults`
interface, contain no divergent protocol logic, and contain only fields
explicitly approved for that contract. Deployment-only values remain typed
manifest entries for the correct later owner; they must not be forced into a
contract or interface merely for convenience.

Do not modify a shared contract merely to make a parameter easier to express.
Do not introduce `chain.id` branching, Robinhood-only protocol behavior, or a
Base migration. Preserve the deployed Base Ledger as the approved permanent
live-bytecode exception.

For every proposed contract field, the Phase A packet must state:

- why manifest-only configuration is insufficient;
- the concrete risk of making no contract change;
- the smallest sufficient implementation;
- the Base and Robinhood blast radius; and
- the residual risk the owner would accept.

If any answer is missing or does not defeat the no-change/configuration option,
the field is not eligible for Phase B. An S4 field is prohibited. No S5 source,
constructor, ABI, or `shouldCheckLastTouch` input may be inferred or
preselected.

### 2. Preserve safe initial state

The initial artifact must represent the exact reviewed launch state, not the
desired end state a week later.

Examples:

- rewards initially disabled remain disabled in the deployment default even
  if a separately approved fast-follow enablement is targeted;
- CCIP target status does not create a CCIP address, role, or capability;
- an enabled PSM target does not bypass its ordered disabled-deploy, funding,
  canary, and mint-authority gates;
- AAPL cannot become reachable before the complete Track 8 activation group;
  and
- a blocked exact address cannot be replaced with zero merely to compile.

### 3. Fast-follow promotion is a new reviewed release

A deadline, target date, elapsed seven-day window, or prewritten alternate
value never promotes a fast-follow setting into the active manifest or
generated defaults automatically.

Every fast-follow promotion requires:

1. fresh, explicit owner authorization for the exact promotion;
2. regeneration of the manifest, generated artifact, hashes, and deployment or
   governance plan from the then-current reviewed baseline;
3. rerun of every affected targeted, mutation, clock-profile, and regression
   validation; and
4. independent review of the resulting exact artifacts before integration or
   any deployment/governance action.

If the promotion misses its target window, it remains disabled or blocked
until that gate completes.

### 4. Configuration is not evidence

A configured flag or address does not prove:

- token exact-transfer behavior;
- oracle availability or freshness;
- pool implementation compatibility;
- CCIP support or transfer success;
- Stock containment correctness;
- S5 child-block identity;
- role ownership; or
- deployed runtime parity.

Keep those as explicit prerequisites and later assertion inputs.

### 5. No silent Base parity

For every value, compare four options:

1. unchanged Base value with identical semantics;
2. cadence-converted Robinhood value;
3. Robinhood-specific product/risk value; and
4. disabled/omitted/no-value posture.

Select only an owner-approved result. A Base value is not a default answer.

### 6. No broad “Robinhood cadence ratio”

The S3 floor approval does not approve a general six-to-one conversion. For
each block-count field, record:

- intended economic or security duration;
- ordinary Base and Robinhood cadence evidence;
- repeated-number behavior;
- `+1`, `+2/+4`, boundary-skip, and `+60` stress behavior;
- floor/ceil rounding;
- minimum nonzero safety bound;
- whether jumps intentionally skip capacity or windows; and
- owner acceptance of the resulting wall-time range.

Rates require an economic decision, not reciprocal duration conversion.

## Phase A — inventory, collision resolution, and owner packet

### A1. Freeze the baseline and ownership map

Record:

- all bootstrap identities and tests;
- every file owned by this brief;
- every active branch touching those files;
- the exact S6/H-04 overlap resolved here;
- every downstream consumer;
- the selected candidate generator comparison; and
- any unresolved ownership collision.

### A2. Build the complete `Defaults` field inventory

Enumerate every field returned through:

- `genConfig`;
- `genDebtConfig`;
- `ripeAvailForRewards`;
- `ripeAvailForHr`;
- `ripeAvailForBonds`;
- `ripeBondConfig`;
- `rewardsConfig`;
- `ripeGovVaultConfigs`;
- `hrConfig`;
- `underscoreRegistry`;
- `trainingWheels`;
- `shouldCheckLastTouch`;
- `assetConfigs`;
- `priorityLiqAssetVaults`;
- `priorityStabVaults`;
- `priorityPriceSourceIds`; and
- `liteSigners`.

For each field, trace:

- constructor/initialization consumer;
- later Switchboard setter and authority, if any;
- whether the field is one-time, mutable, or only an initial seed;
- unit/denominator;
- clock inventory IDs;
- Base/local value and behavior;
- proposed Robinhood initial value/status;
- fast-follow value/status, if any;
- controlling owner decision;
- tests;
- operational disable/re-enable path; and
- whether it belongs in generated source, manifest only, or another slice.

### A3. Build the deployment-only parameter inventory

Include every approved or blocked value needed by H-05/H-08/H-09 but absent
from `Defaults`, including:

- S3 Lootbox floor and initial Underscore send interval;
- S4 zero cooldown assertion;
- S5 action-block source/constructor input and live Base exception;
- timelock and registry-delay values;
- absolute expiry/headroom rules;
- PSM fees, caps, interval, allowlists, reserve funding, auto-deposit posture,
  enable flags, and mint-authority sequence;
- AAPL exposure targets and final token-unit conversion inputs;
- Stock asset routes and disabled controls;
- the complete owner-closed M0 launch graph: AAPL, GREEN, RIPE, chain-native
  sGREEN, canonical USDG, GREEN/USDG LP, and RIPE/WETH LP, preserving the exact
  route, activation, disabled, and blocked distinctions for each;
- launch-active GREEN Stability Pool and RIPE governance-vault inputs;
- GREEN/USDG LP and RIPE/WETH LP deposit-only inputs with explicit legitimate
  `ltv=0`, while their unproved artifact, pool, oracle, runtime, address, and
  composed-route inputs remain blocked;
- reward initial and fast-follow states;
- the GREEN/RIPE CCIP disabled-at-launch and separately reviewed
  within-seven-day promotion posture, plus the permanent sGREEN no-CCIP rule,
  without inventing pool addresses or capabilities;
- external price-source stale times and priorities; and
- role, signer, and TrainingWheels symbolic inputs.

Do not assign exact addresses or values that are not already reviewed and
integrated. The M0 product graph is controlling, but future Ripe/LP addresses,
runtime hashes, vault/registry selections, freeze-time AAPL cap integers, and
post-deployment facts remain typed blockers until their later gates close.

### A4. Classify initial launch versus fast follow

For every field or action, state one exact phase:

- deployed initial value;
- pre-activation configuration;
- atomic Stock activation;
- within-seven-day separately reviewed CCIP promotion;
- within-seven-day separately reviewed reward activation;
- post-launch release;
- omitted; or
- blocked.

At minimum, reconcile:

- rewards deployed globally disabled versus a separately validated,
  separately authorized activation target within seven days;
- AAPL disabled staging versus the complete atomic M1–M5 activation group;
- GREEN/RIPE CCIP disabled at launch unless and until a separately reviewed
  promotion closes, while sGREEN remains permanently excluded from CCIP;
- USDG/PSM redemption-first and GREEN-mint-last launch sequencing;
- chain-native sGREEN deposits and withdrawals active at launch;
- launch-active GREEN Stability Pool and RIPE governance-vault roles;
- GREEN/USDG LP and RIPE/WETH LP deposit-only, explicit-zero-LTV launch roles
  with every unproved external input blocked;
- additional Stock Tokens only after token-specific later-release evidence;
  and
- owner-approved guarded internal Stock settlement as a Track 8 mechanism
  direction whose M1–M5 implementation and activation remain blocked.

No time target converts a later action into an initial default.

### A5. Resolve every clock and economic field

Map all applicable BN and CAD IDs from S6. Create tables for:

- timelocks and action expiries;
- governance locks and boosts;
- capacity refill intervals;
- auctions and bonds;
- reward point attribution;
- RIPE emission rate;
- dynamic-rate fields;
- PSM mint/redeem buckets;
- debt intervals;
- cooldown assertions; and
- timestamp-only HR terms.

For each table include the S1 profile outcomes, selected semantics, exact
candidate values, alternative no-change/disabled posture, and owner/reviewer.

Do not use S10's CAD display correction as authority for a raw runtime value.

### A6. Define the asset-configuration matrix

For every initial or staged asset, specify all `AssetConfig` fields and their
status where that structure applies, and explicitly state `not_applicable`
where the M0-approved route does not use ordinary Teller asset configuration.
The matrix must account for the complete owner-closed M0 graph and the omission
rule that bounds the set:

- AAPL;
- GREEN;
- RIPE;
- sGREEN;
- canonical USDG;
- GREEN/USDG LP;
- RIPE/WETH LP;
- an explicit omission rule for every other asset.

The matrix must prove:

- AAPL has exactly one enabled vault at activation;
- AAPL trusted/Department deposit routes cannot bypass caps;
- Stock Stability Pool and CreditRedeem routes are disabled;
- both LP rows have explicit legitimate zero borrowing power and no omitted
  LTV masquerading as zero;
- chain-native sGREEN deposits and withdrawals are launch requirements and
  sGREEN has no CCIP surface;
- GREEN Stability Pool and RIPE governance-vault participation match M0;
- USDG is not ordinary Teller collateral;
- PSM configuration preserves redemption-first and GREEN-mint-last activation;
- Underscore and Base-only integrations are absent;
- reward allocations match the approved initial phase;
- no omitted field inherits an enabling default; and
- every exact address remains blocked until identity evidence is approved.

Represent AAPL auction purchasing, borrowing, and internal settlement as
blocked until the complete Track 8 M1–M5 group is approved, implemented,
audited, configured, and atomically activated. Do not reinterpret or implement
the owner-approved settlement direction here.

### A7. Specify deterministic generation

Compare the three generator options and return one recommendation. The
selected design must:

- run without RPC, credentials, mutable environment values, or wall-clock
  dependence;
- read one reviewed manifest;
- render deterministically;
- fail on any unresolved included field;
- preserve canonical `Defaults` selectors and tuple order;
- reject Base/local address leakage;
- generate byte-identical output twice;
- support a check-only mode;
- never overwrite `DefaultsBase.vy`;
- print no secret-bearing values;
- write atomically; and
- preserve readable, reviewable Vyper rather than opaque generated blobs.

The evidence must state whether the generator itself is production tooling or
development-only tooling and who owns future changes.

### A8. Produce the owner decision packet

Order the returned decision packet by blast radius rather than by source-file
order. Put launch-critical asset configuration, containment, PSM activation
ordering, and other state- or authority-enabling decisions first; put
lower-consequence allocation and presentation choices last. Preserve stable
decision IDs so later approval, supersession, and checklist evidence remain
unambiguous.

The Phase A evidence must return, at minimum, explicit decisions for:

1. generator/file boundary;
2. complete initial global flags;
3. debt caps and capacity values;
4. cadence basis per duration class;
5. timelocks and expiry headroom;
6. reward point attribution and initial/fast-follow allocations;
7. RIPE emission and available buckets;
8. governance lock/boost terms;
9. bond/HR inclusion and values;
10. every initial/staged asset configuration;
11. AAPL exposure and activation values still pending final price freeze;
12. sGREEN, Stability Pool, RipeGov, and any LP parameters selected by the
    integrated H-03/Track 8 graph;
13. PSM parameters and ordered activation gates;
14. S3/S4/S5 deployment inputs;
15. priority vault and price-source lists;
16. role/signer/TrainingWheels symbolic inputs;
17. every legitimate zero;
18. every omitted or blocked field; and
19. exact Phase B file ownership.

Each recommendation must include:

- no-change/disabled alternative;
- why manifest-only configuration is insufficient if a contract field is
  proposed;
- risk of no change;
- smallest sufficient value, configuration, or implementation;
- separate Base and Robinhood blast radius;
- residual risk the owner would accept;
- reviewer;
- approval form; and
- downstream invalidation effect.

## Phase A mandatory checkpoint

Create only:

`docs/chains/rh/evidence/robinhood-defaults-parameters-phase-a.md`

Return the complete file, its SHA-256, baseline identity, validation results,
and concise checkpoint summary. Leave it unstaged and uncommitted for complete
independent review.

The evidence must contain:

- complete field and deployment-only inventories;
- S6/H-04 ownership resolution;
- generator comparison;
- typed manifest schema proposal;
- initial/fast-follow table;
- BN/CAD disposition table;
- asset matrix;
- all open values and blockers;
- exact Phase B file proposal;
- complete test matrix;
- Base compatibility/no-change proof;
- minimum-change stress test;
- owner decision packet; and
- confirmation that no implementation, RPC, secret access, external write,
  contract change, migration, deployment, governance action, signing, or
  transaction occurred.

If the owner gives no answer, Phase B remains prohibited.

After owner and independent review, record the exact approval provenance in
the evidence and commit only that document to the feature branch. Do not begin
Phase B until the complete Phase A owner-decision packet has independent
complete-file approval, exact Phase B file ownership has been reverified, and
a separate file-exact owner implementation authorization is recorded. A
recommendation, owner-decision request, or Phase A approval is not Phase B
approval.

## Phase B — conditional implementation

Phase B is not authorized by this brief.

If later authorized, it must:

1. reconcile onto the exact then-current reviewed `rh` without rebase or
   history rewriting;
2. re-run the baseline gates and invalidate approvals affected by incoming
   changes;
3. create the approved typed manifest;
4. implement the approved deterministic generator or verifier;
5. generate `DefaultsRobinhood.vy` mechanically;
6. prove the contract implements the unchanged canonical `Defaults` interface;
7. add the two approved test files;
8. update the Phase A evidence in the same commit for any approved conclusion
   or value change;
9. after all Phase B validation passes, commit exactly the authorized and
   validated files to the feature branch with clear provenance;
10. stop at Reviewer Gate 1 before inventory reconciliation or merge; and
11. perform no migration, deployment, live read, signing, or external write.

### Contract requirements

`DefaultsRobinhood.vy` must:

- compile under the integrated pinned compiler;
- implement every current `Defaults` selector exactly once;
- preserve tuple field order and types;
- contain no chain-ID branch;
- contain no Base/local address;
- contain no runtime environment access;
- contain no unapproved component;
- use exact approved units and values;
- encode initial state, never silently fast-follow state;
- return empty arrays only when omission is reviewed and consumers support it;
- contain no placeholder or sentinel pretending to be a production input; and
- add no storage, mutable state, owner, setter, or protocol logic.

### Manifest requirements

The checked-in manifest must:

- validate independently of the generated source;
- hash every generated artifact/input;
- retain approval provenance without secrets;
- identify values consumed outside `Defaults`;
- distinguish values pending final deployment freeze from approved fixed
  values;
- reject an executable plan while a required value is pending; and
- never contain RPC URLs, keys, private addresses, raw provider payloads, or
  signer secrets.

## Required tests

### `tests/config/test_defaults_robinhood.py`

At minimum prove:

- canonical selector and tuple compatibility;
- every generated field equals the approved manifest;
- deterministic generation and check-only mode;
- no Base/local address leakage;
- no unresolved or fast-follow value enters launch defaults;
- every legitimate zero is explicitly typed;
- array ordering is deterministic;
- allocation denominators conserve exactly;
- omitted/disabled/blocked distinctions survive generation;
- `contracts/config/DefaultsBase.vy` and
  `contracts/config/DefaultsLocal.vy` each remain byte-for-byte identical to
  their respective kickoff-baseline versions; they are not expected to be
  identical to each other;
- S3/S4/S5 boundaries are preserved;
- AAPL cannot be accidentally active before Track 8 gates;
- Stock Stability Pool/CreditRedeem/trusted routes remain disabled;
- chain-native sGREEN launch routing is present and no sGREEN CCIP route can
  be generated;
- GREEN Stability Pool, RIPE governance-vault, and both deposit-only LP rows
  match the integrated graph, including explicit zero LTV for both LP rows;
- the USDG PSM ordering is redemption first and GREEN mint last;
- rewards remain globally disabled at launch unless a separately reviewed
  promotion proves the post-launch state;
- incomplete GREEN/RIPE CCIP promotion inputs remain disabled without
  blocking launch;
- Underscore remains omitted; and
- repeated generation produces byte-identical Vyper.

### `tests/deployment/test_network_clock_profiles.py`

At minimum prove every approved block-based field under:

- `B-ORD`;
- `R-REP128`;
- `R-PLUS1`;
- `R-J2-J4`;
- `BOUNDARY-OPEN`;
- `BOUNDARY-WINDOW`;
- `R-STRESS60`; and
- `MIXED` where seconds and block values interact.

Tests must cover exact-before/equality/after boundaries, multi-window jumps,
one-reset/no-carry semantics, rounding, nonzero floors, expiry headroom, and
initial-versus-fast-follow values.

Do not copy production logic into expected-value helpers. Use the integrated
S1 fixtures and S2 checked inventory.

### Generator and manifest mutation tests

Mutations must fail for:

- missing or duplicate parameter;
- unknown unit/status;
- zero replacing missing;
- Base address insertion;
- unresolved included value;
- fast-follow value promoted to initial;
- tuple reordering;
- allocation overflow/underflow;
- block/seconds swap;
- unapproved cadence conversion;
- nondeterministic key ordering;
- stale generated source;
- changed manifest after source generation;
- output path targeting `DefaultsBase.vy`; and
- RPC/environment access.

## Validation

Run serially in the integrated locked environment:

1. generator/manifest unit tests;
2. `tests/config/test_defaults_robinhood.py`;
3. `tests/deployment/test_network_clock_profiles.py`;
4. all existing Defaults/MissionControl/Switchboard tests;
5. applicable rewards, RipeGov, Stability Pool, PSM, CreditEngine, auction,
   and asset-config suites;
6. H-01 dependency gate;
7. H-02 targeted suite;
8. H-03 targeted suite;
9. S1 clock profiles;
10. S2 checker and inventory tests;
11. integrated S3/S4 regressions and any then-integrated S5 regressions,
    while an unfinished S5 keeps every S5-dependent entry blocked;
12. Track 8 tests available at the integrated baseline;
13. collection;
14. the serial full suite;
15. deterministic two-build artifact comparison;
16. `git diff --check`; and
17. untracked-file whitespace checks before files are staged.

Use distinct private basetemp/cache directories and remove them after each
command. Report warnings, deselections, skips, xfails, and expected S2
inventory changes exactly. Do not suppress a new inventory finding.

## Reviewer Gate 1 — implementation and parameter correctness

Stop at the exact committed feature-branch implementation head. A feature
branch commit records a reviewable artifact; it is not integration approval
and does not authorize a push, merge, deployment, or governance action.
Independent reviewers must:

- inspect the complete Phase A evidence, manifest, generator, Vyper source,
  and tests;
- reproduce every file hash and generation result;
- verify every value has approval provenance;
- verify no owner decision was inferred;
- confirm initial and fast-follow states are distinct;
- confirm all Track 8/S3/S4/S5/H-03 boundaries;
- verify canonical interface and tuple compatibility;
- inspect every address and legitimate zero;
- verify block/seconds/economic conversions;
- verify Base and Local artifacts are unchanged;
- review the complete diff, not only summaries;
- run the required targeted tests and a risk-proportionate full suite; and
- identify every remaining deployment-only blocker.

No reviewer may approve their own parameter decision or silently replace
missing owner provenance.

## Reviewer Gate 2 — integration readiness

After Gate 1 approves the exact committed implementation head, and any Gate 1
corrections have themselves been independently reviewed and committed:

1. reconcile exact current `rh` without rebase/history rewriting;
2. stop if any controlling input changed;
3. rerun every affected test and deterministic-generation check;
4. update the Phase A evidence in the same commit for any approved changed
   conclusion;
5. reconcile S2 inventory only with independent semantic approval;
6. if reconciliation or an approved correction changes files, leave that
   delta uncommitted for independent review, then commit it to the feature
   branch only after approval;
7. return exact final hashes, topology, commits, test results, and remaining
   blockers; and
8. obtain final independent merge-readiness approval.

Do not merge or push `rh`. A feature-branch push requires explicit owner
authorization. Owner integration remains separate.

## Cross-track handoffs

### H-03

H-03 supplies symbolic graph inputs. This slice cannot amend its blueprint.
Any graph change returns to H-03 first.

### H-05

H-05 owns migration discovery, ordering, and skeletons. This slice supplies
typed values and hashes only. It cannot create migration `0040` or any other
migration file.

### H-08 and H-09

H-08 proves deployed state against the approved manifest. H-09 proves the
complete clean deployment and negative graph. Neither result is claimed here.

### S7-S10

- S7 owns timelock/registry lifecycle tests beyond parameter selection.
- S8 owns economic/capacity lifecycle validation.
- S9 owns disabled/omitted integration assertions.
- S10 owns CAD report formatting and generated reports.

This slice may provide approved inputs but must not absorb those files.

### Track 8

Track 8 owns Stock containment mechanism, vault selection, and activation
eligibility. M0 is owner-closed and integrated, including the settlement
direction, but it does not supply the post-M0 implementation, audit,
configuration, atomic-activation, address, vault-ID, cap-integer, or
operational proof required by M1-M5. This slice owns only reviewed
configuration projections. Every field that depends on those later artifacts
remains blocked until its exact Track 8 gate closes.

### Track 1 / CCIP

GREEN and RIPE CCIP are a separately reviewed promotion target within seven
days after launch, not an initial-launch blocker or configuration assumption.
If Track 1 or H-12 evidence is incomplete or late, the routes remain disabled.
No pool, remote mapping, admin, capability, or artifact enters this slice
before those gates close. sGREEN must never receive a CCIP route.

## Approval boundaries

Approval of Phase A may authorize:

- recording exact parameter decisions;
- approving one generator/file design; and
- opening a later file-exact Phase B request.

It does not authorize:

- production source;
- a production parameter merely because it is recommended;
- a migration or deployment;
- an address freeze;
- a PSM, reward, Stock, sGREEN, LP, or CCIP activation;
- a Base change;
- an external read/write;
- secrets, signing, funding, or transactions; or
- integration into `rh`.

Approval of Phase B code still does not authorize deployment or governance
configuration.

## Stop conditions

Stop and return to the owner if:

- any hard sequencing gate is incomplete;
- an active branch owns a reserved file;
- H-03 and Track 8 disagree on the launch graph;
- a required field is unresolved;
- a value is copied from Base without approval;
- a general cadence ratio is applied without field-specific approval;
- a rate is treated as a duration conversion;
- an address lacks exact identity evidence;
- a legitimate zero cannot be distinguished from missing;
- `Defaults` cannot express a desired action without interface change;
- the generator needs RPC, credentials, mutable environment state, or
  wall-clock input;
- generated output is nondeterministic;
- `DefaultsBase` or another prohibited file appears in the diff;
- initial and fast-follow states collapse;
- AAPL or another Stock route becomes reachable early;
- S4 no-code posture or the Base S5 exception is contradicted;
- S2 inventory changes without semantic review;
- any targeted or full validation fails;
- an unapproved skip/xfail is proposed;
- an external action becomes necessary; or
- the minimum configuration slice expands into protocol redesign.

## Completion criteria

Phase A is complete only when:

- the single evidence file contains every required table and decision;
- every source claim is cited;
- every unresolved value is explicit;
- the exact Phase B file set is returned;
- independent review has no unresolved findings; and
- the owner has either approved decisions or left Phase B visibly blocked.

The combined workstream is implementation-complete only when:

- Phase A and file-exact Phase B authorization are durable;
- the typed manifest is complete and approved;
- the generated contract is deterministic and interface-compatible;
- all tests pass;
- Base/Local artifacts and behavior are unchanged;
- both reviewer gates approve;
- S2 inventory is reconciled if needed;
- deliverables are committed on the feature branch; and
- the completion report distinguishes code readiness from deployment,
  configuration, and launch readiness.

It is integration-complete only after the owner separately reviews, merges,
and pushes the exact approved branch. It is never deployment-complete merely
because these artifacts exist.

## Completion report

Return:

- starting and final commit/tree identities;
- all controlling artifact hashes;
- exact files changed;
- parameter/manifest hash and schema version;
- generated-source hash and deterministic comparison;
- every owner decision and provenance;
- unresolved values and blockers;
- initial versus fast-follow table;
- targeted, collection, and full-suite results;
- warnings/skips/xfails/deselections;
- S2 inventory delta and approval;
- Base/Local negative-diff proof;
- reviewer Gate 1 and Gate 2 provenance;
- checklist items that are eligible for owner closure, each with its evidence
  reference, while leaving the controlling checklist unticked;
- branch/remote/ahead-behind/worktree state;
- explicit confirmation of no migration, deployment, external write, signing,
  or transaction; and
- the exact next owner action.
