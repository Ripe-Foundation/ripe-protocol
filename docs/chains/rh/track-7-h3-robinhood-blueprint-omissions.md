# Track 7 H-03: Robinhood Blueprint and Explicit Omissions

**Status:** Phase A R6 correction pending independent complete-file review and
exact-hash owner approval. H-02 and Track 8 M0 are integrated. Owner decisions
`D-H03-005` (typed caller-to-callee relations) and `D-H03-006` (terminal
global-mint sequence) are approved, but they do not approve the R6 bytes or
`D-H03-004-R6`. Those two approvals are owner-attested provenance, not facts
independently verifiable from repository bytes. Phase B remains blocked until
the complete corrected Phase A package is approved, the provenance-only
amendment gate closes, the package is committed as a new baseline, and Phase
B is separately authorized.

**Prepared:** 24 July 2026; planning status corrected 25 July 2026

**Planning baseline:** `c0d0e708ae4a89ed730615c9eaf2d23a4fecc05d`

## Fresh-agent instruction

Treat this document as the task contract. Implement only Track 7 follow-on
slice H-03: add one small, immutable, symbolic Robinhood deployment blueprint
and prove that every selected, omitted, disabled, deferred, and blocked
component surface is represented honestly.

This is offline deployment-configuration and test work. It is not a production
contract change, parameter approval, address freeze, migration, manifest,
deployment, activation, or launch authorization. The blueprint must never
contain a production address, silently borrow a Base value, treat zero as a
missing-value substitute, or turn an unresolved Track 1, Track 4, Track 6,
Track 8, product, security, oracle, governance, or operations decision into a
selected deployment input.

Apply the owner's minimum-change directive throughout:

1. make no production smart-contract change;
2. modify no existing Base blueprint or default;
3. introduce only the smallest pure-Python schema needed by downstream
   deployment tooling;
4. prefer an explicit omission, disabled posture, deferral, or blocker over a
   guessed component or compatibility scaffold; and
5. preserve residual risk and future work as typed data rather than solving it
   by expanding H-03.

Use branch `rh-track-7-h3-robinhood-blueprint-omissions-r6`. Leave the
documentation-only R6 deliverables unstaged and uncommitted for complete
independent exact-hash review. Never push or merge into `rh` or `master`; the
owner reviews and separately authorizes any later integration.

## Worktree bootstrap

H-02 and Track 8 M0 are already integrated at the planning baseline. Phase A's
two outputs are this corrected brief and
`docs/chains/rh/evidence/robinhood-blueprint-phase-a.md`. Phase B may begin
only after those exact two candidate files receive independent review and
owner approval, any approval metadata is inserted through the independently
confirmed provenance-only amendment gate, and the resulting two files are
committed together on the R6 H-03 branch and integrated into `rh` as the new
H-03 baseline. A fresh Phase B agent must resume that exact isolated R6
branch/worktree; it must not reuse the rejected R5 worktree or restart from an
older planning baseline:

1. Start from `/Users/wigglez/dev/ripe-protocol`.
2. Verify that:
   - the integration worktree is clean;
   - local `rh` and `origin/rh` resolve to the same owner-approved commit;
   - this brief exists in that commit;
   - the merged Track 7 support specification and validation plan contain the
     reviewed H-03/U-015 corrections;
   - the reviewed H-02 network-profile implementation, post-integration
     correction, and sanitized evidence are integrated into `rh`;
   - H-01, S1, S2, and S3 remain integrated;
   - the H-01 dependency gate, H-02 targeted tests, S1, and S2 pass on the
     untouched baseline;
   - the owner-closed Track 8 M0 packet, specification, validation plan, and
     evidence present in `rh` are identified exactly, without treating any
     later M1-M5 gate as closed; and
   - no branch or worktree other than the exact named H-03 branch/worktree
     owns an H-03 file.
3. Record:
   - the full starting commit;
   - SHA-256 hashes of this brief, both Track 7 authority documents, the
     integrated H-02 record and implementation files, `config/BluePrint.py`,
     the component matrix, and every integrated Track 8 input;
   - the Python, pip, Vyper, Titanoboa, and pytest versions;
   - local/remote branch parity;
   - the exact H-02 public API consumed by H-03; and
   - baseline H-01, H-02, S1, S2, collection, and full-suite results.
4. Confirm that branch
   `rh-track-7-h3-robinhood-blueprint-omissions-r6` and path
   `/Users/wigglez/dev/ripe-protocol-track-7-h3-robinhood-blueprint-omissions-r6`
   exist, are paired with each other, and contain the exact approved Phase A
   documentation commit. If either is absent, mismatched, dirty outside the
   approved Phase A package, or points to different history, stop and ask the
   owner. Do not create, reuse under another identity, delete, reset, or
   overwrite anything.
5. After the Phase A documentation commit is integrated, obtain explicit owner
   authorization to merge that exact current `rh` commit into the existing
   H-03 branch without rebase or history rewriting. Stop on any unexpected
   incoming path, conflict, or authority drift.
6. Verify the reconciled worktree's branch, commit, clean status, file hashes,
   dependency versions, and baseline test results.
7. Run every subsequent command and make every edit inside
   `/Users/wigglez/dev/ripe-protocol-track-7-h3-robinhood-blueprint-omissions-r6`.

Do not modify or commit from the integration worktree.

## Hard sequencing rule: H-02 controls the profile interface

H-03 must consume the reviewed, integrated H-02 profile API. It must not read a
floating H-02 worktree as authority, cherry-pick an unintegrated H-02 commit,
copy H-02 files manually, anticipate an API from a Phase A proposal, or branch
from a pre-H-02 `rh`.

Stop before editing if:

- H-02 is not integrated locally and remotely;
- either H-02 reviewer gate is incomplete or conditional;
- the integrated H-02 record does not identify the exact public profile API;
- `robinhood-mainnet` and `robinhood-testnet` do not resolve through that API;
- H-02 permits either Robinhood profile to fall back to Base;
- the integrated dependency state differs from the reviewed H-02 evidence; or
- any H-02 file or authority document changes after H-03 bootstrap.

If `rh` advances after H-03's Phase A approval, stop. Reconcile only after the
owner authorizes the exact new baseline, refresh all recorded identities, and
rerun affected validation. Do not continue against a stale checkpoint.

## Planning corrections carried by this brief

This reviewed H-03 batch corrects two stale planning statements:

1. U-015 said the Track 8 specification and validation plan did not exist.
   They are integrated, along with the owner-closed M0 evidence and decision
   packet. The truthful blockers are the separately gated M1-M5
   implementation, composed-proof, deployment, and activation work.
2. The validation command map assigned
   `tests/deployment/test_registry_topology.py` to H-03 even though that file is
   created and owned by H-08. H-03 must prove its own registry-slot
   expectations in its two owned test files. The H-08 file is run only after
   H-08 creates it.

These are documentation corrections, not expanded implementation authority.
H-03 still owns exactly three implementation/test files. It also owns one
durable Phase A evidence record so the source-backed topology analysis and
owner approval do not exist only in a task response.

R4b corrected the exact H-02 history paths, LP ordinary-only routing,
reward-state separation, global-mint proposal, and approval continuity, but
was rejected. R5 preserves those valid corrections, implements the approved
typed caller-to-callee relation model, records `D-H03-006` as approved,
regenerates every relation and dependent count, and reconciles all
supersession/status language, but was rejected for unsupported `R-282`, a
truncated canonical exclusion rule, and drift from the integrated H-04
lifecycle vocabulary. R6 corrects only those documentation defects and the
mechanically dependent promotion, count, assertion, provenance, and handoff
language. It does not authorize Phase B.

Independent re-review then verified the first complete R6 candidate at brief
SHA-256
`43f29ba8b7cc7a7cc4497a2dc4d1ff3c7086bbae20505d16ae16e161919d51b6`
and evidence SHA-256
`a9c2b2d7628b5a00594b25604f31d8ca34c9ffd1cf3ec3976df9f23498684418`,
including every canonical count and source proof. It requested that the
launch-disabled meaning of the two token CCIP capability rows be made
explicit. Those hashes were never approved and are superseded by this
clarified R6 candidate; no inventory, lifecycle assignment, or count changed.

## Exact file ownership

H-03 may add only:

- `docs/chains/rh/evidence/robinhood-blueprint-phase-a.md`;
- `config/robinhood_blueprint.py`;
- `tests/deployment/test_robinhood_blueprint.py`; and
- `tests/deployment/test_robinhood_omissions.py`.

The evidence record is Phase A analysis and approval provenance only; it is not
an executable input, implementation authority, production-value record, or
substitute for the immutable blueprint. No other implementation, test, fixture,
generated, schema, migration, manifest, or evidence file is authorized.

## Prohibited files and scope

Do not modify:

- any file under `contracts/` or `interfaces/`;
- `config/BluePrint.py`;
- `config/network_profiles.py`;
- `contracts/config/DefaultsBase.vy`, any future
  `contracts/config/DefaultsRobinhood.vy`, or another default;
- `scripts/migrate.py`, `scripts/console.py`, `scripts/verify.py`, or any
  deployment helper;
- anything under `migrations/` or `migration_history/`;
- manifests, generated defaults, parameter reports, artifacts, or ABIs;
- `tests/deployment/test_network_profiles.py`,
  `tests/deployment/test_secret_handling.py`,
  `tests/deployment/test_base_profile_regression.py`, or another H-02 file;
- the future H-08-owned `tests/deployment/test_registry_topology.py`;
- Track 1, Track 4, Track 6, Track 8, S4, S5, or H-01/H-02 records;
- the component matrix, decision registers, validation plans, or support
  specification beyond the reviewed planning corrections committed with this
  brief;
- `docs/chains/rh-summary.md`; or
- another track's files.

Do not create:

- a Robinhood smart contract, default contract, migration, manifest, history,
  address file, parameter file, generated artifact, verifier, or RPC client;
- a second network-profile registry;
- a Robinhood-only protocol implementation;
- a generic deployment framework;
- a compatibility adapter to make a blocked component look selected; or
- an executable plan.

If an H-03 test exposes a defect owned by H-04, H-05, H-06, H-08, H-09,
Track 8, or another slice, record it and stop at the ownership boundary.

## Required reading

Read and verify the integrated versions of all items below.

### Program authority

- `docs/chains/rh-summary.md`
- `docs/chains/rh/robinhood-deployment-support-specification.md`, especially
  Sections 8, 13, 15, 18 H-03, and 19
- `docs/chains/rh/robinhood-deployment-validation-plan.md`, especially Stage
  1, NEG-016–025, NEG-031, NEG-033–037, and H-03
- `docs/chains/rh/component-matrix.md`, all CM-001–060 rows
- `docs/chains/rh/minimal-contract-change-reassessment.md`

### Integrated H-02 authority

- `docs/chains/rh/track-7-h2-network-profiles-cli.md`
- `docs/chains/rh/evidence/network-profile-cli-implementation.md`
- `config/network_profiles.py`
- `tests/deployment/test_network_profiles.py`
- `tests/deployment/test_secret_handling.py`
- `tests/deployment/test_base_profile_regression.py`

If any named H-02 artifact is absent from integrated `rh`, stop. Do not infer
its interface from the H-02 brief alone.

### Existing blueprint and deployment consumers

- `config/BluePrint.py`
- `scripts/utils/deploy_args.py`
- `scripts/migrate.py`
- `scripts/utils/migration.py`
- `scripts/utils/migration_runner.py`
- `scripts/utils/json_file.py`

These files are read-only in H-03. Build a repository-wide import/use map for
`BluePrint`, `ADDYS`, `PARAMS`, `CORE_TOKENS`, `CURVE_PARAMS`, `WHALES`,
`YIELD_TOKENS`, `blueprint_id`, and every integrated H-02 profile-to-blueprint
field. Do not assume the list is exhaustive for analysis.

### Registry and topology authority

- `contracts/modules/Addys.vy`
- `contracts/registries/RipeHq.vy`
- `contracts/registries/VaultBook.vy`
- `contracts/registries/PriceDesk.vy`
- `contracts/registries/Switchboard.vy`
- `contracts/registries/modules/AddressRegistry.vy`
- `contracts/core/CreditEngine.vy`
- `contracts/core/CreditRedeem.vy`
- `contracts/core/Teller.vy`
- `contracts/core/BondRoom.vy`
- `contracts/core/HumanResources.vy`
- `contracts/core/Lootbox.vy`
- `contracts/core/Endaoment.vy`
- `contracts/core/EndaomentFunds.vy`
- `contracts/config/SwitchboardBravo.vy`
- `contracts/config/SwitchboardDelta.vy`
- `contracts/config/SwitchboardEcho.vy`

Classify every registry-domain ID by authority:

- A **source-hard-coded ID** is compiled into a consumer and cannot shift
  without breaking canonical source assumptions. Verify it from source;
  documentation is not sufficient when source can answer.
- A **registration-order ID** is not defined by a source constant. Record the
  committed Base manifest and deployment history as precedent evidence, encode
  the expected Robinhood semantic placement as a constraint H-05 must satisfy,
  and do not call it source-defined.
- A **provisional reservation** is neither a deployed registry row nor a
  source-hard-coded ID. Preserve its semantic intent without assigning an
  address, capability, or deployment status.

At the planning baseline, source defines RipeHq IDs 1–22, VaultBook IDs 1 and
2, PriceDesk IDs 2 and 4, and Switchboard ID 1. VaultBook IDs 3 and 4,
PriceDesk IDs 1, 3, and 5, and Switchboard IDs 2–5 are registration-order
outcomes, not source constants. Re-verify that classification from the
integrated H-03 baseline and stop if it changed.

### Cross-track inputs

- `docs/chains/rh/ccip-chainlink-question-packet.md`
- `docs/chains/rh/ccip-integration-decision.md`
- `docs/chains/rh/ccip-public-evidence.md`
- `docs/chains/rh/usdg-psm-decision.md`
- `docs/chains/rh/usdg-public-evidence.md`
- `docs/chains/rh/stock-token-vault-comparison.md`
- `docs/chains/rh/stock-token-vault-decision.md`
- `docs/chains/rh/stock-token-vault-fix-recommendations.md`
- `docs/chains/rh/block-number-inventory.md`
- `docs/chains/rh/shared-block-clock-specification.md`
- `docs/chains/rh/lootbox-floor-implementation-record.md`
- `docs/chains/rh/deleverage-cooldown-security-decision.md`
- `docs/chains/rh/track-6-s5-ledger-guard.md`
- `docs/chains/rh/track-6-s5-checkpoint-0-owner-decision-packet.md`
- any reviewed S5 decision/evidence files integrated into `rh` before H-03
  bootstrap
- `docs/chains/rh/track-6-s6-track-7-h4-defaults-parameters.md`
- `docs/chains/rh/track-8-stock-token-vault-change.md`
- `docs/chains/rh/stock-token-vault-change-specification.md`
- `docs/chains/rh/stock-token-vault-change-validation-plan.md`
- `docs/chains/rh/stock-token-m0-evidence.md`
- `docs/chains/rh/stock-token-m0-raw-evidence.json`
- `docs/chains/rh/track-8-m0-owner-decision-packet.md`
- `docs/chains/rh/track-8-m1-exact-receipt.md`

Never treat a local untracked packet, floating worktree, reviewer message, or
chat summary as integrated authority.

### Base compatibility fixtures

- `migration_history/base-mainnet/v1/current-manifest.json`
- the Base blueprint consumers discovered by the import/use map
- the integrated H-02 Base regression tests

Base files and live state are evidence only. H-03 must not copy their addresses
or mutate them.

## Objective

Produce the smallest pure-Python H-03 implementation that:

1. exposes one immutable Robinhood blueprint schema for the integrated H-02
   `robinhood-mainnet` and `robinhood-testnet` profiles;
2. represents every stable component ID CM-001 through CM-060 exactly once;
3. distinguishes a required symbolic input from `omitted`, `disabled`,
   `deferred`, and `blocked`;
4. represents deployment disposition separately from disabled feature,
   capability, route, and registry sub-surfaces where one component needs both;
5. distinguishes source-hard-coded IDs, required registration-order
   constraints, and provisional reservations while preserving each semantic
   name and empty-slot invariant without deploying placeholders;
6. contains no production address, private role, parameter value, external
   endpoint, artifact hash, or live version selection;
7. makes missing and unresolved values fail closed rather than falling back to
   Base, local, zero, `None`-as-success, or another profile;
8. makes every initial-launch omission and disabled path machine-testable;
9. consumes owner-closed Track 8 M0 and its required active chain-native
   sGREEN posture, while leaving Stock containment M1-M5, PSM activation,
   rewards, CCIP, S5, and every other later unresolved decision visibly
   blocked at the exact sub-surface where it matters; and
10. preserves `config/BluePrint.py` and intended Base profile behavior
    byte-for-byte.

H-03 is a declarative graph boundary. It does not construct contract arguments,
load addresses, instantiate `BluePrint`, discover migrations, write manifests,
contact a network, or execute a step.

## Required semantic vocabulary

The minimal H-03 schema must make these meanings unambiguous:

- `required`: the component or field belongs in the selected graph, but any
  later concrete value must come from its separately approved owner and
  freeze;
- `omitted`: no Robinhood artifact, address, registry row, capability,
  permission, approval, route, manifest contract record, or callable
  configured path exists;
- `disabled`: a component or topology-preserving scaffold may exist, but every
  named value path, capability, role, flag, allocation, route, and approval is
  explicitly inert;
- `deferred`: the component or feature is outside the initial release and
  requires a new reviewed release before it can become required; and
- `blocked`: the desired disposition cannot be finalized because a named
  owner, evidence, security, external, or implementation gate remains open.

These states are not aliases:

- `blocked` is not permission to omit;
- `deferred` is not a zero-address deployment;
- `disabled` is not merely "not yet configured";
- `omitted` cannot reserve a sequential slot with an unrelated contract; and
- `required` is not approval of a production value.

If a component is required while one sub-surface is disabled or blocked, model
both facts explicitly. Do not collapse the row to a single optimistic label.

The exact lifecycle vocabulary is:

- `deployed_initial_value`;
- `pre_activation_configuration`;
- `atomic_stock_activation`;
- `within_seven_day_separately_reviewed_ccip_promotion`;
- `within_seven_day_separately_reviewed_reward_activation`;
- `post_launch_release`;
- `omitted`; and
- `blocked`.

The CCIP-promotion phase applies only to the exact six CCIP surfaces approved
in the evidence record. Within that exact set, `S-001-CCIP-CAP` and
`S-002-CCIP-CAP` are capabilities of tokens deployed at launch: their
`disabled` disposition must hold from `deployed_initial_value` continuously
through the separate CCIP-promotion checkpoint. Their promotion-phase label
identifies the controlling reviewed action and is not permission to leave
them unspecified at launch. The other four CCIP members are deferred
artifact/registration/toolchain surfaces.

The reward-activation phase applies only to the separate reward
`PromotionRecord`; every referenced reward surface remains `disabled` at
`deployed_initial_value`. A zero reward-activation cardinality among
`SurfaceRecord` values is therefore correct and required, not an unused enum
value.

## Symbolic-input rules

A required future value must be represented by:

- a stable symbolic field ID;
- its type or semantic class;
- the component(s) that consume it;
- the owner/gate that may provide it;
- whether it is required before H-04, H-05, H-09, testnet, or production
  freeze; and
- its current status.

Do not store:

- an address-shaped string;
- a zero-address string;
- a Base address;
- a local test address;
- an RPC URL or environment value;
- a private account or role;
- a guessed constructor value;
- a chain-specific cadence, fee, cap, timelock, reward, oracle, or risk
  parameter; or
- a sentinel that a downstream consumer could mistake for a legitimate value.

Legitimate future zero values, such as disabled flags or the approved
no-yield-position posture, must be represented as named assertions or typed
configuration requirements. They must not share the representation for
"missing."

## Schema constraints

Phase A must propose the exact public API for owner and reviewer approval. The
implementation should normally use small frozen dataclasses, enums, tuples,
and read-only mappings, but the brief does not pre-approve names that conflict
with the integrated H-02 interface.

At minimum the schema must provide:

- one immutable blueprint identity shared by both Robinhood profiles;
- exact accepted H-02 profile IDs;
- stable component IDs;
- component name and source classification;
- deployment disposition;
- symbolic required fields;
- registry-domain/ID/name, ID-authority class, or reserved-slot metadata when
  applicable;
- capability, route, feature, and activation sub-surface dispositions;
- separately reviewed promotion actions, distinct from launch-state surfaces;
- stable relation IDs, closed relation kinds, target component IDs, phases,
  nonempty tuples of mechanically resolvable `path:line` proofs, semantic
  bases, and exact evidence-authority-ID tuples;
- blocker IDs and accountable owner classes;
- negative assertion IDs;
- downstream slice ownership;
- exact controlling-evidence-ID tuples; and
- a pure lookup/validation API.

Approved `D-H03-005` fixes relation semantics:

1. direct execution/call relations use caller to callee direction;
2. a governed contract points to its authority registry/controller through a
   separately typed `authority_dependency`;
3. a controller points to a target only where source proves a direct call;
4. a configuration writer does not point to downstream consumers merely
   because they read the configuration;
5. registry membership/admission belongs in registration-order and registry
   expectation records, not fictitious runtime calls; and
6. indirect/transitive security assertions require a separate typed record
   with a complete multi-source proof tuple.

Every canonical row is one explicit edge. Grouped Cartesian expansion is
forbidden. Selected-source to omitted-target edges are permitted when required
to prove a source-retained disabled or fail-closed route. Phase B must encode
only the independently reviewed R6 relation records and may not reinterpret
or regroup them.

All nested values must be immutable. Importing or validating the module must
not:

- read an environment variable;
- read or write a file;
- inspect Git;
- import a deployment runner or account helper;
- initialize Boa;
- contact a network;
- load a key;
- resolve an address; or
- mutate global state.

There must be one schema authority. Do not maintain parallel component,
registry, omission, and blocker dictionaries that can drift independently
unless they are derived deterministically from one immutable record set.

## Component completeness and current truth

Every CM-001–060 ID must occur exactly once in the primary component table.
Grouped prose in the component matrix does not permit a grouped or missing code
identity.

The primary table must distinguish:

1. selected shared core components;
2. topology-preserving disabled scaffolds;
3. Base-only or unsupported omissions;
4. future-release deferrals;
5. unresolved blockers; and
6. non-onchain tooling/test components.

For each row, compare the component matrix with the Track 7 graph and current
cross-track evidence. Where authorities disagree or a later integrated record
supersedes an earlier recommendation:

- record both sources;
- identify the controlling later authority;
- do not silently choose;
- stop at the Phase A checkpoint if the selected H-03 representation is not
  mechanically implied; and
- propose the minimum-change disposition.

No code comment or test name may claim that an open M1, S5, CCIP, oracle,
reward, role, or production-value gate has passed.

Track 8 M0 is owner-closed and must never be described as open. Its selected
launch outcomes do not close M1-M5 or any implementation, proof, deployment,
configuration, or activation gate.

## Blueprint amendment ownership

After H-03 integrates, closing a blocker does not automatically reclassify its
blueprint row. Any change from `blocked`, `deferred`, `disabled`, or `omitted`
to another disposition requires a new reviewed H-03 amendment or an explicit
owner-approved revision of this slice, including updated tests and both H-03
reviewer gates. H-04, H-05, H-06, H-08, H-09, Track 8, and other downstream
slices must consume the blueprint read-only and must not edit it in place.

## Registry-topology invariants

H-03 must encode the ID authority class with each topology expectation. The
absence of a source constant for a documented registration-order ID is not an
authority conflict; it is the reason H-05 must prove the exact order.

H-03 must verify and encode at least:

### RipeHq

- canonical IDs 1 through 22 retain their source-defined meanings;
- an omitted optional integration cannot shift a later hard-coded ID;
- IDs 23 and 24 are only provisional CCIP reservations while CCIP is deferred;
- a provisional reservation is not a registry row or capability grant; and
- an unrelated or zero-address placeholder is prohibited.

### VaultBook

- source-hard-coded ID 1 remains Stability Pool;
- source-hard-coded ID 2 remains RipeGov;
- registration-order ID 3 remains Simple ERC20 Vault;
- registration-order ID 4 remains Rebase ERC20 Vault;
- Track 8 controls which approved shared Stock containment artifact may occupy
  the applicable canonical slot; and
- no Stock route becomes enabled merely because the slot exists.

### PriceDesk

- registration-order ID 1 remains Chainlink;
- source-hard-coded ID 2 remains Curve;
- registration-order ID 3 remains BlueChipYield;
- source-hard-coded ID 4 remains Pyth;
- registration-order ID 5 remains Stork;
- an empty reserved ID is not reassigned to a later source; and
- unsupported sources remain unreachable.

### Switchboard

- source-hard-coded ID 1 remains Alpha;
- registration-order IDs 2 through 5 remain Bravo, Charlie, Delta, and Echo;
- Echo's presence, if topology requires it, does not activate PSM;
- Delta remains unchanged with the S4 zero-cooldown initial posture; and
- no omitted Underscore or Base integration receives a Switchboard route.

Tests in H-03's owned files must prove these expectations. H-03 must not create
the H-08 registry checker. Tests must distinguish a source invariant from a
required H-05 registration-order constraint rather than presenting both as the
same kind of fact.

## Mandatory unresolved rows

The Phase A table must include, at minimum, the following explicit
dispositions and blockers.

### Track 8 and Stock Tokens

- Stock Tokens are an initial-launch requirement; treating all Stock Tokens as
  omitted is not an acceptable final launch graph.
- M0 is owner-closed. Until M1–M3 are approved and implemented, M4's composed
  proof passes, and M5 activation is separately approved, every Stock asset
  registration, vault selection, borrow route, liquidation route, CreditRedeem
  route, Stability Pool route, trusted deposit route, reward route, and
  activation surface remains `blocked` or `disabled` as appropriate.
- If integrated M0 authority selects AAPL-first restricted activation, H-03 may
  represent only symbolic AAPL identity/configuration requirements. It must not
  copy the known live address into the blueprint.
- Every other Stock Token remains separately omitted or blocked according to
  the integrated M0 matrix. AAPL evidence does not generalize.
- H-03 cannot approve a vault artifact or production route.

### SavingsGreen and Stability Pool

- Owner-closed Track 8 M0 requires active chain-native sGREEN and the GREEN
  Stability Pool at launch; omission and inert-topology alternatives are
  superseded.
- H-03 Phase A must trace every constructor, hard-coded ID, consumer, registry
  consequence, and launch/security route required by that selected posture.
- Canonical source requires a real SavingsGreen deployment identity for
  RipeHq construction; do not replace it with zero or assume a sparse
  registry.
- sGREEN remains permanently excluded from CCIP. Stock custody and swaps in
  the Stability Pool remain disabled until their separately approved Track 8
  gates say otherwise.

### USDG and EndaomentPSM

- Owner-closed M0 and source topology require CM-048 at RipeHq ID 22. H-03
  must represent disabled staging followed by gated launch activation; it must
  not reopen omission as an option.
- The blueprint requires explicit staging assertions for `canMint=false`,
  `canRedeem=false`, no GREEN mint capability, no yield route, no approval,
  and no generic Teller asset route. Source initializes auto-deposit to
  `True`; the launch-disabled posture therefore requires an explicit,
  separately reviewed pre-activation action setting it to `False`.
- The official price path does not approve USDG identity, reserve values,
  parameters, deployment, or activation.
- No address or zero-address placeholder belongs in H-03.

### RipeHq capabilities and Teller initialization

- RipeHq source initializes `mintEnabled=True`. The selected launch graph
  therefore requires an explicit pre-activation transition to `False` and a
  testable assertion that global minting remains disabled throughout staging.
- Encode separate post-registration target tuples for Switchboard blacklist
  authority, VaultBook RIPE minting, and AuctionHouse, CreditEngine, and
  Endaoment GREEN minting. A generic "capabilities pending" record is
  insufficient and no tuple may be enabled before its setup/handoff gates.
- Encode owner-approved `D-H03-006`: with global minting disabled, configure
  and verify every
  exact Department capability tuple and prove all unlisted capability bits
  false; enable and prove PSM redemption; make the CM-048
  `(canMintGreen=True, canMintRipe=False,
  canSetTokenBlacklist=False)` grant the final capability-tuple mutation;
  re-verify the complete tuple set; then call
  `RipeHq.setMintingEnabled(True)` as the final launch activation. No
  capability, route, parameter, or registry mutation may follow that global
  re-enable within the launch plan. This approved ordering does not approve
  any execution detail or R6 artifact; Phase B remains blocked.
- Teller's `_shouldPause` constructor argument is a separate symbolic input
  and launch-safety surface. It must have exact owners, blockers, consumers,
  and lifecycle semantics; H-03 must not infer its value from asset settings
  or select it.

### LP deposit-only semantics

- Represent each approved LP's explicit legitimate `ltv=0` configuration as a
  required but currently blocked configuration surface.
- Represent the absent LP borrowing route/capability separately as omitted.
  Missing LTV data must never satisfy the zero-LTV requirement.
- For each of `I-GREEN-USDG-LP` and `I-RIPE-WETH-LP`, the only permitted
  Teller entrypoints are the ordinary `deposit` and `depositMany` paths.
  `depositFromTrusted` is forbidden for the LP asset regardless of producer,
  vault ID, lock duration, or supplied `Addys`; no Department-specific or
  direct-vault bypass may substitute for an ordinary Teller deposit. Encode
  this as a dedicated assertion over both LP identities and mutation-test
  every trusted producer/call-site class, not as descriptive
  "deposit-only" prose.

### Rewards, HR, bonds, and Underscore

- Global launch rewards are a deployed-initial disabled state. The possible
  seven-day action is a separate immutable promotion record that references
  the exact reward surfaces, remains deferred and blocked on the rewards
  validation/monitoring/kill package, and requires a new reviewed release.
  Elapsed time or the launch-state record alone cannot perform the promotion.
- GREEN/RIPE CCIP has a separate immutable promotion record referencing only
  `S-001-CCIP-CAP`, `S-002-CCIP-CAP`, `S-051-ARTIFACT`,
  `S-052-ARTIFACT`, `S-053-REGISTRATION`, and `S-058-TOOLCHAIN`. It remains
  deferred, separately reviewed, nonautomatic, and blocked on the Track 1
  security/toolchain package. It does not change launch state if incomplete
  or late.
- Boardroom, BondRoom, BondBooster, Lootbox reward minting, HumanResources,
  Contributor instances, and related allocations stay disabled or blocked.
- Lootbox remains the shared S3 artifact with the Robinhood symbolic floor
  requirement and interval-zero Underscore posture; H-03 does not supply the
  value.
- Underscore is omitted from the initial Robinhood launch: no vault, wallet,
  price source, reward bypass, deleverage integration, approval, or route.
- S4 remains a no-code, zero-cooldown launch posture. H-03 must not create an S4
  migration or future nonzero cooldown.

### Ledger/S5

- The fresh Robinhood Ledger row remains blocked on the integrated S5
  implementation/proof gates unless those gates are closed before H-03
  bootstrap.
- The live Base Ledger remains the accepted permanent state-bearing exception;
  H-03 cannot create or imply a Base migration.
- If S5 is still open, H-03 records the exact future source/provider
  requirements symbolically and cannot mark the Ledger deployable.

### CCIP and cross-chain paths

- CM-051–053 and CM-058 remain deferred/blocked while Track 1 and the toolchain
  gate are open.
- RipeHq IDs 23/24 remain provisional semantic reservations only.
- No pool address, remote mapping, token-admin registration, direct mint
  capability, route, or cross-chain assumption is present.
- Initial Stock activation must remain chain-local unless a later reviewed M0
  decision explicitly reopens the graph.

### Unsupported Base integrations and price sources

- CM-007, CM-017–020, CM-035–042, CM-050, CM-054, and CM-060 receive the exact
  omission/deferral posture from integrated authority.
- No Base DEX, yield, treasury, oracle, Underscore, local-only generated value,
  or external protocol address may appear.
- CreditEngine's Curve danger path must remain a named base-rate-fallback
  assertion while Curve is absent; H-03 does not change the contract.

## Required negative assertions

The H-03 code must make the following validation-plan cases directly testable
in its owned tests:

- NEG-016 omitted integration deployed;
- NEG-017 zero used as a placeholder;
- NEG-018 PSM mint enabled;
- NEG-019 PSM redeem enabled;
- NEG-020 PSM auto-deposit or yield enabled;
- NEG-021 Stock collateral enabled before Track 8 gates;
- NEG-022 Stock CreditRedeem enabled;
- NEG-023 Stock Stability Pool swap enabled;
- NEG-024 unsupported oracle reachable;
- NEG-025 premature CCIP capability;
- NEG-031 registry ID shift;
- NEG-033 premature Savings path;
- NEG-034 inactive HR path enabled;
- NEG-035 premature bond/reward path;
- NEG-036 disabled scaffold gains authority; and
- NEG-037 PriceDesk semantic slot reuse.

The H-03 test set must also include a dedicated Teller exact-receipt assertion
and mutation family. It must prove that every source `depositFromTrusted`
producer is governed by one M1 policy and that success requires exact receipt
and exact vault return, while short/zero/excess/malformed returns, reentrancy,
and downstream failure roll back atomically. NEG-021 alone is not sufficient
for this boundary.

It must additionally include:

- `NEG-H03-LP-ORDINARY-ONLY`
  `test_lp_assets_exclude_every_trusted_teller_route`, asserting for both
  approved LP identities that the exact allowed Teller route set is
  `deposit`/`depositMany`, the `depositFromTrusted` set is empty, and no
  Department/direct-vault bypass exists; and
- `NEG-H03-GLOBAL-MINT-SEQUENCE`
  `test_global_mint_reenable_is_final_launch_activation`, asserting the
  owner-approved `D-H03-006` sequence of global disable, exact tuple
  configuration/verification, PSM redemption proof, final PSM tuple mutation,
  full re-verification, and final global re-enable. Execution and proof remain
  blocked; the approved sequence does not authorize Phase B or a production
  action.

Use the validation plan's exact test names where it assigns one to an H-03
file. If a case requires a deployed contract, migration plan, or H-08 checker,
H-03 proves only its declarative prerequisite and leaves the integration tier
to the owning later slice. Do not fake an integration result with a dictionary
unit test.

## Phase A — source-backed graph and API design

Before editing implementation files:

1. Verify every H-02 profile and blueprint-related API from integrated source.
2. Build a complete CM-001–060 disposition table with:
   - deployment status;
   - symbolic inputs;
   - registry domain/ID/name or reservation;
   - disabled/blocked sub-surfaces;
   - phase-qualified component relations;
   - blocker and owner IDs;
   - negative assertion IDs;
   - downstream slice; and
   - exact controlling evidence.
3. Build the exact RipeHq, VaultBook, PriceDesk, and Switchboard topology
   tables. For each numeric ID, label its authority as source-hard-coded,
   registration-order, or provisional reservation; cite source for the first
   class and the committed Base manifest/deployment history for the second.
   Include exact RipeHq global-mint and post-registration capability
   transitions rather than a catch-all handoff flag.
4. Trace omission versus inert-scaffold feasibility for SavingsGreen and PSM.
5. Consume the owner-closed Track 8 M0 decisions while keeping every later
   M1-M5 implementation, proof, deployment, and activation gate open.
6. Design a generic address-shaped-literal rejection plus a read-only,
   test-time comparison with the values already present in
   `config/BluePrint.py` and the Base manifest. Do not copy those addresses into
   any H-03 file.
7. Trace every current and proposed consumer of the H-03 API and prove H-03
   need not modify one.
8. Propose the smallest immutable public API and explain why each field is
   necessary for H-04/H-05/H-09.
9. Design mutation tests for missing CM rows, duplicates, mutable nested state,
   status flattening, zero/Base fallback, registry shifts, blocker removal,
   profile aliasing, reward-state/promotion collapse, LP trusted-route
   admission, and early or nonterminal global-mint re-enable.
10. Identify every required fact H-03 cannot own.

### Phase A mandatory checkpoint

Stop before creating any H-03 code or test file. Create
`docs/chains/rh/evidence/robinhood-blueprint-phase-a.md` and return that
complete file, its SHA-256, and a concise checkpoint summary. The evidence file
must durably contain:

- baseline identities and validation results;
- the integrated H-02 API and exact proposed H-03 API;
- the full CM-001–060 table;
- the four registry-topology tables;
- the active chain-native SavingsGreen/Stability selection and excluded-path
  proof;
- the PSM omission-versus-disabled-staging proof;
- the owner-approved terminal global-mint sequence, its blocked
  execution/proof status, and its non-approval of the R6 artifact;
- the exact LP ordinary-only route assertion and trusted-route mutation
  coverage;
- the launch-disabled reward inventory and exact two-record promotion-action
  inventory;
- the current Track 8 M0 reconciliation;
- the address-shaped-literal rejection and read-only Base-comparison strategy;
- the exact two-file Phase A documentation package, its required baseline
  reset, and the later four-file Phase B ownership boundary;
- the negative and mutation test matrix;
- every unresolved field with owner and deadline;
- any authority conflict or need for a prohibited file; and
- confirmation that no secret, environment value, address freeze, network,
  signing, migration, contract change, or external action occurred.

The checkpoint must ask the owner only for decisions that the source-backed
analysis makes necessary. It must not ask the owner to approve a production
address, contract artifact, migration, or parameter in H-03.

Immediately before owner approval, re-hash every cited integrated authority.
Also re-hash any observed mutable cross-track worktree artifact and confirm it
is explicitly non-authoritative. Integrated drift, a changed controlling
conclusion, or any attempt to use uncommitted cross-track evidence as authority
requires refreshed review and blocks approval.

After exact-hash review, owner approval must name the reviewed brief and
evidence hashes. Inserting dated approval metadata changes the evidence bytes,
so those post-insertion bytes must not be called the already reviewed bytes.
The only permitted post-approval change is a provenance-only amendment to the
designated provenance block in this same evidence record. A second independent
reviewer must then:

1. hash both post-amendment files;
2. compare the candidate-to-post-amendment diff exactly;
3. confirm the brief is byte-identical to its approved hash;
4. confirm every evidence change is confined to the authorized provenance
   block and contains only the approved decision IDs, actor/role, date, and
   reviewed hashes; and
5. record independent confirmation of the post-amendment evidence hash.

Any other byte change voids the approval and requires full exact-hash review
again. Only after this gate closes may the exact unchanged brief and confirmed
post-amendment evidence be committed together on the H-03 branch. Do not
create a second checkpoint or implementation-evidence document. If Phase A is
rejected or materially revised, update and re-review the same two-document
package.
Any Phase B or Gate 1 change to an approved disposition, topology
classification, blocker, or public-API conclusion must update the Phase A
evidence record in the same commit and trigger review of both artifacts; the
blueprint remains the executable schema authority, while the evidence record
preserves the approved rationale and supersession history.

The safe default is no implementation until deployment-tooling, protocol,
security, Track 8, and affected product/risk owners approve the checkpoint.
Approval of this brief authorizes Phase A only.

## Phase B — minimal immutable blueprint

Only after the Phase A checkpoint is approved:

1. Add the approved immutable schema to
   `config/robinhood_blueprint.py`.
2. Bind it only to integrated H-02 `robinhood-mainnet` and
   `robinhood-testnet` identities.
3. Encode CM-001–060 exactly once.
4. Encode registry semantics and reservations without a deployable placeholder.
5. Encode symbolic input requirements without values.
6. Encode every approved omission, disabled surface, deferral, and blocker.
7. Provide pure deterministic validation and lookup functions.
8. Reject unknown, Base, local, or aliased profiles.
9. Reject missing rows, duplicate IDs, invalid transitions, mutable nested
   state, missing blocker provenance, registry shifts, and semantic slot reuse.
10. Keep module import free of side effects and H-04/H-05 execution logic.

If a concise immutable record set cannot express the approved model without a
framework, stop and return a smaller interface proposal. Do not build a generic
configuration engine.

## Phase C — blueprint tests

`tests/deployment/test_robinhood_blueprint.py` must at minimum prove:

- exact accepted H-02 Robinhood profiles;
- identical symbolic graph semantics for mainnet and testnet;
- no Base/local/unknown profile acceptance;
- all 60 stable component IDs, exactly once;
- immutable primary and nested structures;
- pure import and validation with relevant environment variables absent;
- no filesystem, Git, Boa, account, RPC, or network side effect;
- no address-shaped production value in the blueprint;
- no zero/Base/local fallback;
- required fields are symbolic and owner/gate-attributed;
- missing and unresolved are distinct from legitimate disabled values;
- every relation ID, kind, phase, target component ID, source proof, and
  evidence-authority ID resolves; direct, authority, and indirect orientation
  matches `D-H03-005`;
- all blocker IDs have an accountable owner class;
- every source-hard-coded registry ID is source-correct;
- every registration-order ID matches its reviewed precedent and is encoded as
  an H-05 constraint rather than a source constant;
- PriceDesk reservations cannot be repurposed;
- omitted components have no artifact/route/capability surface;
- disabled components enumerate their negative surfaces;
- deferred and blocked are distinct;
- the CCIP-promotion phase is confined to the exact six reviewed surfaces,
  while `S-001-CCIP-CAP` and `S-002-CCIP-CAP` are explicitly disabled from
  launch continuously through that promotion checkpoint;
- the reward-activation phase has zero `SurfaceRecord` members and appears
  only on the separate reward `PromotionRecord`;
- owner-closed Track 8 M0 is represented closed without representing any
  later M1-M5 gate as passed;
- Base `config/BluePrint.py` is unchanged;
- integrated H-02 Base regression remains green; and
- mutation cases fail closed with stable diagnostics.

## Phase D — omission and disabled-path tests

`tests/deployment/test_robinhood_omissions.py` must implement the H-03-owned
portion of every Required negative assertion above.

At minimum prove:

- every Base-only integration is absent from the RH graph;
- no omitted row has an address, registry row, permission, approval, route, or
  manifest-record expectation;
- zero cannot satisfy a required symbolic field;
- every disabled scaffold has exact negative capabilities;
- RipeHq's source-default `mintEnabled=True` is represented with its required
  pre-activation `False` transition; the five pre-PSM post-registration HQ
  target tuples are exact and remain withheld before their gates; the PSM
  GREEN tuple is a separately blocked final capability-tuple mutation; and
  global re-enable is represented as the owner-approved final launch
  activation, with execution and proof still blocked;
- Teller's initial pause choice remains symbolic, owner-attributed, and
  impossible to default or infer;
- each approved LP has an explicit zero-LTV configuration requirement while
  its borrowing route is separately omitted, and both LPs reject
  `depositFromTrusted` and every Department/direct-vault bypass while allowing
  only ordinary `deposit`/`depositMany` entrypoints;
- no Stock surface is enabled before its integrated Track 8 gates;
- `canRedeemCollateral=false` and
  `shouldSwapInStabPools=false` remain required for Stock assets;
- PSM mint, redeem, yield, GREEN capability, approvals, and Teller routes
  remain absent when disabled; auto-deposit must be changed from its source
  default `True` to `False` through an approved pre-activation action;
- SavingsGreen deposits/withdrawals and the GREEN Stability path remain
  required, while Stock and CCIP paths remain disabled or omitted exactly as
  selected;
- HR, contributors, bonds, and Underscore remain inert; every reward surface
  is launch-disabled and the possible seven-day promotion is a separate,
  deferred record that cannot self-activate;
- unsupported oracles are absent and their semantic slots reserved;
- CCIP pool artifacts, registration, and remote routes remain absent, while
  the GREEN/RIPE CCIP mint-burn capabilities remain disabled from launch
  continuously through the separately reviewed promotion checkpoint;
- a missing early registry row cannot shift a later semantic ID;
- a reserved empty slot cannot be filled by a different component; and
- a blocked row cannot be reclassified by deleting its blocker.

Tests must use synthetic values only. They must not copy a production address
into any H-03 file. A Base-address comparison must derive values at test time
from the read-only committed Base authority, then prove none can become
blueprint data.

## Test isolation

All H-03 tests:

- run with external networking disabled;
- run with relevant environment variables absent;
- use synthetic non-production fixtures;
- do not read `.env`, a keychain, or a credential file;
- use temporary directories for any filesystem spy;
- restore monkeypatches and global state;
- do not depend on test order;
- do not write under `migrations/` or `migration_history/`;
- do not initialize Boa unless an existing broader regression requires it; and
- do not turn a missing later-slice file into a skip that hides H-03 failure.

The H-08-owned `tests/deployment/test_registry_topology.py` is not an H-03
deliverable. If it does not yet exist, that is expected. Record it as
not-applicable for H-03 rather than creating, skipping, or xfail-marking a fake
file.

## Phase E — validation

Run serially from the isolated H-03 worktree:

1. import the H-03 module with relevant environment variables absent;
2. `python -m pytest -q tests/deployment/test_robinhood_blueprint.py`;
3. `python -m pytest -q tests/deployment/test_robinhood_omissions.py`;
4. both H-03 files together;
5. `python -m pytest -q tests/deployment/test_base_profile_regression.py`;
6. the complete H-02 targeted suite;
7. the H-01 dependency gate;
8. the S1 clock profile suite;
9. the S2 checked-inventory guard;
10. existing blueprint/deployment-argument tests;
11. `python -m pytest --collect-only -q`;
12. `python -m pytest -q`; and
13. tracked and untracked whitespace checks, including
    `git diff --no-index --check /dev/null <new-file>` before the files are
    staged.

If H-08 has integrated before final H-03 validation, also run
`tests/deployment/test_registry_topology.py`. Otherwise record that the
H-08-owned file does not yet exist and do not treat that as an H-03 failure.

Record exact commands, environment exclusions, versions, collected counts,
pass/fail/skip totals, durations, and expected unavailable later-slice tests. A
green exit code does not waive a missing semantic assertion.

## Mandatory reviewer gates

### Gate 1 — implementation, topology, and security

Before the branch may be considered merge-ready, independent reviewers must:

- inspect every changed line;
- verify the exact two-file Phase A documentation package is committed and
  integrated as the new baseline before Phase B, then verify Phase B changes
  exactly the evidence record plus the three implementation/test files;
- inspect the complete Phase A evidence and approval provenance;
- confirm the provenance-only amendment has an independent exact-diff/hash
  confirmation and that the brief stayed byte-identical to its approved hash;
- confirm the Phase A CM/topology conclusions and the implemented blueprint
  agree, with any approved revision recorded in the same commit;
- compare all CM-001–060 records with integrated authority;
- independently verify source-hard-coded IDs from source and
  registration-order IDs from committed Base deployment evidence;
- confirm every unresolved Track input remains blocked;
- confirm Stock Tokens are not silently omitted as a final launch solution;
- confirm sGREEN and PSM conclusions match the Phase A approved proof;
- confirm no production address, Base value, zero placeholder, secret,
  endpoint, parameter, or live artifact entered the module;
- verify import purity and immutable nested state;
- inspect negative and mutation tests for false-positive passes;
- verify H-04/H-05/H-06/H-08/H-09 boundaries remain intact;
- inspect all test evidence; and
- confirm no network, signing, migration, contract change, or external action
  occurred.

Any material finding returns the branch to implementation and requires a fresh
Gate 1 review.

### Gate 2 — integration readiness

After Gate 1 approval:

1. fetch and compare current `rh`;
2. stop if H-02, Track 8, S5, or another controlling input changed;
3. reconcile only with explicit owner authorization;
4. refresh every cited integrated authority hash and the CM/blocker
   comparison; re-hash any observed mutable cross-track worktree artifact and
   treat it as non-authoritative until separately reviewed and committed;
5. rerun H-03, H-02, H-01, S1, S2, Base regression, collection, and full-suite
   validation;
6. compare the exact diff with Gate 1;
7. confirm no active track owns an overlapping file;
8. record local and remote ahead/behind plus a virtual merge; and
9. obtain explicit owner approval before merge.

No push to `rh`, merge, worktree removal, or branch deletion is authorized by
either gate.

## Approval boundaries

Allowed without further owner approval after Phase A checkpoint approval:

- edits to the exact three H-03 implementation/test files;
- the provenance-only Phase A evidence amendment, but only through the
  independently confirmed exact-diff/hash gate above;
- offline deterministic tests;
- local import and schema validation;
- temporary test directories inside the normal test process; and
- commits to the H-03 branch.

Require separate owner approval:

- any file outside exact ownership;
- any dependency or environment change;
- any contract, default, migration, manifest, history, ABI, artifact, or
  generated-value change;
- any production address, role, parameter, cap, timelock, reward, or route;
- closing a Track 1, Track 4, Track 6, Track 8, security, product, risk, oracle,
  governance, or operations blocker;
- any network request, even read-only;
- any secret/account access or external write;
- any push to or merge into `rh`/`master`; and
- any deployment, signing, verification, configuration, or activation.

## Stop conditions

Stop and return to the owner/reviewers if:

- H-02 is absent, stale, or not fully reviewed;
- the integration baseline is dirty or local/remote `rh` differ;
- an H-03 file is concurrently owned;
- a prohibited file is required;
- integrated authority disagrees on a component or registry identity;
- an ID classified as registration-order is represented as source-hard-coded,
  or H-05 cannot preserve its reviewed order;
- required SavingsGreen or owner-closed PSM disabled staging cannot be
  represented safely without a source change;
- a required field would need a guessed, Base, local, zero, or production
  value;
- a production address or endpoint would be needed;
- Track 8 M0 or minimum-containment status cannot remain explicit;
- a relation record departs from approved `D-H03-005` typed orientation;
- a launch-order record departs from approved `D-H03-006`;
- a blocker must be flattened to make a test pass;
- a registry ID can shift or a semantic slot can be repurposed;
- the H-02 API requires H-03 to mutate network-profile state;
- another track changes H-02, Track 8, S5, or topology authority after
  checkpoint approval;
- tests require external networking;
- H-01, H-02, S1, S2, Base regression, collection, or the full suite regresses;
  or
- implementation grows beyond a small immutable schema and narrow tests.

## Required deliverables

### Deliverable A — durable Phase A evidence

- `docs/chains/rh/evidence/robinhood-blueprint-phase-a.md`

### Deliverable B — immutable symbolic blueprint

- `config/robinhood_blueprint.py`

### Deliverable C — blueprint tests

- `tests/deployment/test_robinhood_blueprint.py`

### Deliverable D — omission and disabled-path tests

- `tests/deployment/test_robinhood_omissions.py`

No second checkpoint or implementation-evidence Markdown, production data
file, address file, manifest, migration, or generated artifact is an H-03
deliverable.

## Completion criteria

H-03 is complete only when:

- H-02 is integrated and recorded;
- Phase A receives explicit owner/reviewer approval;
- the Phase A evidence and approval provenance are durable and the
  provenance-only amendment has independent exact-diff/hash confirmation;
- the two-file Phase A documentation package is integrated as the Phase B
  baseline, after which the evidence record plus exactly three
  implementation/test files are the complete Phase B boundary;
- both Robinhood profiles consume one shared symbolic graph;
- CM-001–060 are complete, unique, immutable, and source-backed;
- all required fields remain symbolic;
- all omissions, disabled surfaces, deferrals, and blockers remain explicit;
- Stock launch requirements and open Track 8 gates are both represented
  honestly;
- sGREEN and PSM topology conclusions have approved evidence;
- approved `D-H03-005` relation semantics and `D-H03-006` global-mint order
  are encoded exactly without treating either as artifact or execution
  approval;
- LP ordinary-only routing and the reward-state/promotion split are encoded
  and mutation-tested;
- source-hard-coded registry semantics cannot shift or be repurposed;
- registration-order constraints remain explicit inputs to H-05;
- no production address, Base fallback, zero placeholder, secret, network, or
  live action exists;
- Base blueprint and H-02 behavior remain compatible;
- all required validation passes;
- both reviewer gates close;
- deliverables are committed to the H-03 branch; and
- the owner decides whether to integrate.

The agent must report which post-M0 checklist and downstream gates become
eligible for owner review. M0 is already owner-closed and must not be reopened
or re-closed. The agent must not tick `docs/chains/rh-summary.md` or approve a
deployment graph.

## Completion report

Report:

- branch, worktree, starting commit, and final commit;
- exact files changed;
- H-02 integration identity and consumed API;
- Phase A evidence hash and checkpoint approval provenance;
- candidate and post-provenance hashes plus the independent provenance-only
  exact-diff/hash confirmation;
- CM-001–060 completeness and disposition counts;
- exact registry-topology proof, including each ID's authority class;
- SavingsGreen and PSM conclusions;
- relation-orientation and global-mint owner-decision status;
- LP ordinary-only and reward-promotion conclusions;
- Track 8 M0 and Stock blocker state;
- symbolic-input and no-address proof;
- negative/mutation tests and exact outcomes;
- Base compatibility results;
- reviewer-gate status;
- remaining blockers and downstream ownership;
- local/remote ahead-behind and push status; and
- explicit confirmation of no contract/default/migration/manifest/history/
  artifact/generated-value change, secret access, network access, external
  write, signing, deployment, verification, activation, `rh`/`master` merge,
  or checklist edit.
