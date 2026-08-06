# Track 6 S6 / Track 7 H-04: Robinhood Defaults and Parameter Manifest

**Current reconciliation status (2026-07-27):** Documentation-only
current-state correction for independent complete-file exact-hash review.
The brief was reviewed, published, and integrated. This correction authorizes
neither Phase A nor Phase B, creates no H-04 evidence or implementation
artifact, and does not convert any blocked value into parameter authority.

**Current reconciliation baseline commit:**
`8d1d2d40c3ca795a37b8cb5bbed54c5e805cddaa`

**Current reconciliation baseline tree:**
`68a0d26e35d0437eea62eb4495e68ad25cbf85d1`

**Published H-04 provenance:** commit
`d7809b82f0e2adc660b1e40fe0e4e28d6056b35a`, tree
`336db452b7c331debb565350651418312ee0b203`, complete-file SHA-256
`2d9a1e0777751265b4aacc1c65434349e19c7c91f2a1d796bf9ff0f4bb349010`.
That commit is an ancestor of the current reconciliation baseline.

**Historical published status:** Documentation-reconciliation draft for
independent review. This revision authorizes neither Phase A nor Phase B.
H-01, the corrected H-02 implementation, and owner-closed Track 8 M0 are
integrated. The Track 8 M1 brief is integrated, but M1 implementation remains
separately gated. Phase A is blocked until the reviewed H-03 implementation is
integrated and every other prerequisite below is satisfied. S5 remains an
independent in-flight workstream and does not supply a final source,
constructor, ABI, or `shouldCheckLastTouch` input to this brief.

**Historical documentation-reconciliation kickoff commit:**
`332ae2bc8e0ce4b694766d6d20759295d9267ec3`

**Historical kickoff tree:** `f67dc91e47331785837de879b6557b285aec3b1b`

**Historical reconciliation branch:**
`rh-track-6-s6-track-7-h4-defaults-parameters`

**Historical reconciliation worktree:**
`/Users/wigglez/dev/ripe-protocol-track-6-s6-track-7-h4-defaults-parameters`

## 2026-07-27 current-state reconciliation layer

This section is a current authority and lifecycle overlay on the complete
historical brief below. It supersedes only stale status, prerequisite, launch,
and handoff statements that were true at publication. It does not rewrite the
contemporaneous record or alter the Defaults inventory, classification method,
ownership boundaries, Phase A or conditional Phase B ceilings, prohibited
paths, units, manifest rules, owner decisions, stop conditions, or parameter
dispositions.

The overlay is bound to exact current `rh`
`8d1d2d40c3ca795a37b8cb5bbed54c5e805cddaa`, tree
`68a0d26e35d0437eea62eb4495e68ad25cbf85d1`. The original publication
identity, kickoff identity, and historical branch/worktree above remain
provenance only and are not changed or republished by this correction.

### Exact current authority bindings

| Authority | Current binding at `8d1d2d40` | Reconciled effect |
| --- | --- | --- |
| H-01 dependency implementation and exception retirement | The reviewed H-01 payload remains integrated at `575d47b82055b42da2bddf1535d8076cd7cf4c63`; the final transition is integrated at `7098211db5693f986b65ec7a9e897f3518e9538c`. `docs/chains/rh/evidence/dependency-security-gate.md` SHA-256 is `81baca680d8f21c309d87e83f25366ea50c8d27700cd3e0d6ea7001a1892b41c`. | The dependency prerequisite and final operative exception split are controlling. |
| H-03 Phase A/R6 and Phase B immutable blueprint | Phase A/R6 closure is integrated at `2c8468affaa4301fbe51287d76e9e1c0c5d4fb21`; the post-S5 evidence is integrated at `6217d4860b98c343e076d4df2e3916f8e59a2bf2`; implementation is integrated from `35e3a8df5c0768f17121407c18da185aabd82f43` with Gate 1 provenance at `ee07d9b6b4ae85f76646617051ec7d331e30a824`. The Phase A evidence SHA-256 is `f1f8bf077723b08b87da6244a56ea36706c82152182e227972abe02363146d22`. | H-03 documentation, implementation, and immutable blueprint are integrated; all 18 typed blockers remain open. |
| S5 Ledger guard | The final S5 integration record is integrated at `81478fe33dfa47a8e135682a047b64949650cb29`. `docs/chains/rh/ledger-guard-implementation-record.md` SHA-256 is `6ce94f25f00e6924b540378f09ed1a84ce401e6474863b2eae6820437b2f847b`; the security decision SHA-256 is `15610bac4293d06320581dc1603b2980ea352af55d89f040ccab18ca26c9e739`. | S5 source behavior is controlling; deployment values remain evidence-bound and must not be guessed. |
| Track 8 M1 exact receipt | Phase B implementation is integrated at `66eae5ac516466be360fe53a53a4bcd672c1ed23`. `docs/chains/rh/evidence/stock-token-m1-exact-receipt.md` SHA-256 is `999a9dcadf0d15332f8847e198cdf82efc32e099f31b496ecdb4f3e64b78c0eb`. | Exact receipt/custody enforcement is controlling; M2-M5 configuration and activation inputs remain blocked. |
| H-05 Phase A | The controlling evidence was published at `28d2dc9b2fb3b9e55d792b811ce5738555e1762a` and integrated through merge `7a3a36666f277277fa08b55081b3f58c7cd3ba64`. `docs/chains/rh/evidence/robinhood-migration-phase-a.md` SHA-256 is `28c3e32b9732334c4904667eeb983d057d5d96391fb5fd8b13f37a9f5033af7c`. | Phase A planning authority is integrated; H-05 Phase B remains downstream and requires separate authorization. |
| H-06 Phase A | Manifest-v2 evidence is integrated through `70dd76516ca9b4af8c0797c327bf15732634e5f6`. `docs/chains/rh/evidence/robinhood-manifest-phase-a.md` SHA-256 is `54aea0a8df18d83dc53493ba561195d432d8e7df0d057932eeed7dfe60cd7c19`. | The deployment/evidence manifest-v2 protocol is controlling and remains distinct from H-04's parameter manifest. |
| Thin-Solidity CCIP reference decision | Current `rh` commit `8d1d2d40c3ca795a37b8cb5bbed54c5e805cddaa` selects the reviewed reference direction. `docs/chains/rh/ccip-integration-decision.md` SHA-256 is `9b668e3b6aaba48f0ec4af60af1a3d92de4e9c190aeefadd3cc69f2afc5d1ab2`; Round 3 review SHA-256 is `4d122008a538a3bc3cb962a90c345fb7415b682e69d4641bbab85bd9fcf2688c`; reviewed reference source SHA-256 is `28fea3591caf8955a4c1f47d34f5abfe249564001578687525f94fddf5cfac77`; reference README SHA-256 is `fe298fa2bc7215494ae3c2d61f19b7c716f5919f2a4ce74837a4de86155a8ad0`. | The subclass is a non-production reference only; it supplies no H-04 parameter value or deployment authority. |

### H-01 operative dependency state

The integrated dependency implementation and final exception-retirement
transition are both controlling. The current split is exact:

- retired and historical only: Click, Pygments, and Pymdown Snippets;
- retained and operative: pytest and Pymdown b64; and
- held toolchain: pytest `8.4.2`, Titanoboa `0.2.7`, and Vyper `0.4.3`.

This repository evidence records exception disposition only. It does not
establish, and this reconciliation does not infer, GitHub or Dependabot alert
closure.

### H-03 integrated graph and still-open parameter blockers

The following implementation paths now exist and are integrated:

- `config/robinhood_blueprint.py`;
- `tests/deployment/test_robinhood_blueprint.py`; and
- `tests/deployment/test_robinhood_omissions.py`.

The approved immutable inventory remains exactly 60 components, 94 surfaces,
103 source-path records, 288 explicit relations over 284 unique
phase-qualified triples, 18 open blockers, 48 symbolic inputs, 38 registry
expectations, 24 negative assertions, and 2 promotion records. Integration of
the blueprint does not close any of its 18 blockers.

In particular, `TrainingWheels` and `specialStabPoolId` remain H-04 parameter
blockers. The PSM preactivation auto-deposit setting must change to `false`.
Terminal promotion preserves the approved global-mint/PSM activation ordering.
Ordinary Teller LP deposit routes are the only allowed LP deposit path; no
trusted or direct-vault bypass is allowed, and LTV is explicitly zero.
GREEN/RIPE CCIP capabilities remain disabled continuously through promotion.

### S5 controlling semantic direction

The integrated Ledger guard has one exact selector split:

- source zero uses native `block.number`;
- exact source `0x64` uses the ArbSys child-block identity;
- the ArbSys response must be exactly 32 bytes and the call uses
  `max_outsize=65`;
- there is no fallback; and
- every other source value fails closed.

`shouldCheckLastTouch` remains enabled for Robinhood. This statement does not
guess a deployment address, constructor value, or other deployment input
beyond the controlling S5 evidence.

### Track 8 M1 controlling implementation and remaining gates

M1 Phase B exact-receipt implementation is integrated and controlling. The
reviewed Teller runtime is 24,152 bytes, leaving 424 bytes of EIP-170
headroom. Teller now enforces exact receipt/custody accounting with a mutex;
any failed exactness assertion or downstream call reverts atomically.

M1 integration does not authorize Stock activation. Every remaining M2-M5
launch or configuration value, including the audit, vault, registration,
cap-integer, address, and atomic-activation proofs, remains blocked until its
own controlling authority exists.

### H-05 integrated Phase A boundary

H-05 Phase A owns deterministic import-free discovery, semantic ordering,
typed blocked planning, report serialization, and later execution planning.
It did not publish a namespace or executable skeleton. Its separately gated
conditional Phase B ceiling remains exactly:

- `docs/chains/rh/evidence/robinhood-migration-phase-a.md`;
- `config/network_profiles.py`;
- `scripts/migrate.py`;
- `scripts/utils/migration_runner.py`;
- `tests/deployment/test_migration_discovery.py`; and
- `tests/deployment/test_execution_plan.py`.

H-05 consumes H-04's later reviewed exact hashes and values. H-05 Phase B is
downstream, requires separate authorization, and supplies no H-04 value.

### H-06 integrated Phase A boundary

H-04's parameter manifest and H-06's deployment/evidence manifest-v2 schema,
immutable history, and current-index protocol are different authorities.
H-06's controlling direction is macOS/APFS-only initially:

- immutable publication uses `renameatx_np(..., RENAME_EXCL)` only, with no
  fallback;
- durability uses file `fsync`, `F_FULLFSYNC`, exclusive rename, directory
  `fsync`, and final `F_FULLFSYNC` in the approved sequence;
- current-index promotion permits `os.replace` only under the cooperative lock
  after validating the expected prior-index hash and immutable target; and
- Linux is initially unsupported and fails closed.

Its conditional Phase B ceiling remains exactly eight files:

- `docs/chains/rh/evidence/robinhood-manifest-phase-a.md`;
- `scripts/utils/migration.py`;
- `scripts/utils/json_file.py`;
- `scripts/utils/manifest_schema.py`;
- `docs/chains/rh/schemas/deployment-manifest-v2.schema.json`;
- `tests/deployment/test_manifest_schema.py`;
- `tests/deployment/test_current_manifest_promotion.py`; and
- `.gitignore`.

H-06 Phase B is separately owner-authorized and, as of this reconciliation,
is being implemented in an isolated worktree. Those uncommitted bytes are
non-controlling, were not inspected for this reconciliation, and supply no
H-04 authority.

### CCIP reference-only state

The reviewed thin-Solidity subclass selected at the current baseline is
reference material only. It is non-production and not deployment-authorized.
RipeHq IDs `23` and `24` remain provisional reference IDs, and GREEN/RIPE CCIP
capabilities remain disabled continuously through promotion.

Production dependency packaging, compiler/build settings, audit, gas
qualification, external roles, registration, and activation remain separately
blocked. No provisional CCIP ID, address, role, route, or capability value is
imported into H-04's parameter authority.

### Current prerequisite and blocker disposition

| H-04 prerequisite or input | Current disposition | H-04 consequence |
| --- | --- | --- |
| H-01 dependency implementation and final exception transition | Satisfied and integrated | Consume only the held toolchain and operative two-exception split; make no external alert-state claim. |
| Corrected H-02 profile API and Track 8 M0 | Satisfied and integrated | Re-read from final `rh`; historical closure remains valid. |
| H-03 Phase A/R6, immutable blueprint, source, and tests | Satisfied and integrated | Phase A may later inventory its exact symbolic inputs, but all 18 blockers stay open. |
| S5 Ledger guard | Satisfied and integrated | Use the exact source semantics above; do not infer any unproven deployment value. |
| Track 8 M1 exact receipt | Satisfied and integrated | Exact receipt is controlling; all M2-M5 activation/configuration inputs remain blockers. |
| H-05 Phase A | Satisfied and integrated | H-04 may later supply reviewed hashes/values; H-05 Phase B remains downstream. |
| H-06 Phase A | Satisfied and integrated | Keep the two manifest authorities distinct; uncommitted Phase B bytes are non-controlling. |
| Thin-Solidity CCIP reference decision | Satisfied only as a reference-direction decision | No production package, parameter, registration, role, address, or activation authority exists. |
| H-04 current-state correction | Pending independent complete-file exact-hash review and later integration decision | Phase A and Phase B remain unauthorized. |
| H-04-owned values and every S5-, M1-M5-, oracle-, rewards-, PSM-, LP-, CCIP-, role-, cap-, fee-, cadence-, or address-dependent input without final authority | Blocked or conditional | Preserve a typed `blocked`, `omitted`, `deferred`, or `unresolved` disposition; never substitute a Base or provisional value. |
| Phase A owner authorization on an exact final `rh` freeze | Missing | No parameter inventory, evidence artifact, recommendation, baseline tests, or implementation may begin. |
| Phase B owner authorization and closed approved Phase A packet | Missing and downstream | No Defaults source, parameter manifest, generator, tests, migration, deployment, configuration, or activation may begin. |

### Historical stale-statement disposition

| Historical location or statement family | Publication-time meaning | Current disposition |
| --- | --- | --- |
| Top-level “draft,” M1-unimplemented, H-03-not-integrated, and S5-in-flight status | Correct at the historical kickoff and publication. | Retained as labeled historical provenance; superseded by this dated layer. |
| Hard gate 1 H-01 identity | Bound the original integrated dependency payload only. | Still historical provenance; the final `7098211db5693f986b65ec7a9e897f3518e9538c` exception-retirement transition and operative two-exception split now control. |
| Hard gate 2 statement that M1 implementation is unauthorized | Preserved the publication-time Track 8 gate. | Superseded: M1 Phase B is integrated; M2-M5 and Stock activation remain blocked. |
| Hard gate 3 statements that H-03 evidence/source/tests are absent and its worktree is uncommitted | Preserved the publication-time concurrency boundary. | Superseded: the Phase A/R6 record, immutable blueprint, source, tests, and Gate 1 provenance are integrated; all 18 blockers remain open. |
| Hard gate 4 statements that S5 is in flight and does not supply source/ABI/`shouldCheckLastTouch` direction | Prevented consumption of unintegrated S5 bytes. | Superseded for integrated source semantics: the Ledger guard and enabled `shouldCheckLastTouch` direction now control. Any deployment value not fixed by that evidence remains blocked. |
| Future Phase A seal steps 3-5 and validation item 11, where H-03/S5/M1 could still be unfinished | Required a fresh final-baseline check rather than floating-worktree consumption. | The conditional procedure remains sound, but current status is now satisfied/integrated for H-03, S5, and M1. Unintegrated bytes from any later worktree remain non-controlling. |
| Minimum-change instruction barring inference of S5 source, constructor, ABI, or `shouldCheckLastTouch` | Prevented preselection from the then-active S5 worktree. | Still controls as a no-inference rule; exact integrated evidence may be consumed, while absent deployment inputs may not be guessed. |
| Historical H-05 handoff to “discovery, ordering, and skeletons” | Reflected the earlier specification allowance. | Corrected: Phase A published no namespace or executable skeleton and owns the narrower planning/report boundary and conditional six-file Phase B ceiling. |
| No historical H-06 handoff | H-06 had not yet supplied integrated Phase A authority. | Added: H-06's manifest-v2 protocol and conditional eight-file ceiling are distinct from H-04; current uncommitted H-06 Phase B bytes are non-controlling. |
| Historical Track 8 handoff treating all M1-M5 implementation as later | Correct before M1 integration. | Corrected: M1 exact receipt is integrated; every M2-M5 launch/configuration input stays blocked. |
| Historical CCIP handoff without the selected thin-Solidity reference | Correct before the reference decision. | Corrected: the subclass is non-production reference material only; IDs `23`/`24` are provisional and disabled, and production qualification/activation remains blocked. |

After this correction receives independent complete-file exact-hash review and
the final `rh` baseline is frozen, a separately authorized Phase A may begin
repository-only inventory/classification, provenance tracing, denominator and
unit reconciliation, and preparation of the one-file owner-decision packet.
It may record every unresolved dependency as a typed blocker. It must not
select values that remain dependent on S5 deployment evidence, Track 8 M2-M5,
oracle/reward/PSM/LP/CCIP/role/cap/fee/cadence/address authorities, H-05 or H-06
implementation bytes, or another unfinished track.

The historical “draft,” “uncommitted,” “in-flight,” prerequisite, and
“independent review is the only next step” statements below remain accurate
records of the publication-time state. Where they conflict with this dated
overlay, this overlay controls only the present lifecycle and handoff status.
The only next action authorized by this correction is independent review of
the complete corrected file; neither H-04 phase is authorized.

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

The original documentation reconciliation did not authorize Phase A, creation
of the Phase A evidence file, baseline test execution, parameter analysis, or
a recommendation. This current-state correction also authorizes none of those
actions. Independent complete-file exact-hash review of the corrected brief is
the only next step authorized here.

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
- `docs/chains/rh/evidence/dependency-exception-exit-preflight.md`
- `docs/chains/rh/evidence/network-profile-cli-implementation.md`
- `docs/chains/rh/track-7-h3-robinhood-blueprint-omissions.md`
- `docs/chains/rh/evidence/robinhood-blueprint-phase-a.md`
- `config/robinhood_blueprint.py`
- `tests/deployment/test_robinhood_blueprint.py`
- `tests/deployment/test_robinhood_omissions.py`
- `docs/chains/rh/track-6-s3-lootbox-floor.md`
- `docs/chains/rh/deleverage-cooldown-security-decision.md`
- `docs/chains/rh/track-6-s5-ledger-guard.md`
- `docs/chains/rh/track-6-s5-checkpoint-0-owner-decision-packet.md`
- `docs/chains/rh/ledger-guard-security-decision.md`
- `docs/chains/rh/ledger-guard-implementation-record.md`
- every additional S5 decision/evidence artifact integrated before Phase A
- integrated H-03 implementation, tests, and Phase A evidence
- `docs/chains/rh/track-8-m0-owner-decision-packet.md`
- `docs/chains/rh/stock-token-m0-evidence.md`
- `docs/chains/rh/stock-token-vault-change-specification.md`
- `docs/chains/rh/stock-token-vault-change-validation-plan.md`
- `docs/chains/rh/track-8-m1-exact-receipt.md`
- `docs/chains/rh/evidence/stock-token-m1-exact-receipt.md`
- `docs/chains/rh/evidence/robinhood-migration-phase-a.md`
- `docs/chains/rh/evidence/robinhood-manifest-phase-a.md`
- `docs/chains/rh/ccip-integration-decision.md`
- `docs/chains/rh/evidence/ccip-solidity-reference-round-3-review.md`
- `docs/chains/rh/examples/README.md`
- `docs/chains/rh/examples/RipeCcipBurnMintTokenPools.sol`
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

H-05 Phase A owns deterministic import-free discovery, semantic ordering,
typed blocked planning, report serialization, and later execution planning.
It published neither a namespace nor an executable skeleton. This slice
supplies reviewed typed values and hashes only. H-05's conditional Phase B
ceiling is the exact six files recorded in the current-state overlay; it
cannot create migration `0040` or any other migration file, and Phase B
remains downstream and requires separate authorization.

### H-06

H-06 owns the deployment/evidence manifest-v2 schema, immutable-history writer
and reader, and current-index promotion protocol. H-04 owns the parameter
manifest. Neither may substitute for or silently absorb the other. The
conditional H-06 Phase B ceiling is the exact eight files recorded in the
current-state overlay. Separately authorized uncommitted H-06 implementation
bytes remain non-controlling and provide no H-04 parameter authority.

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
eligibility. M0 is owner-closed and integrated, and M1 exact-receipt Phase B
implementation is integrated and controlling. M1 supplies exact
receipt/custody accounting, mutex, and atomic-rollback behavior only; it does
not authorize Stock activation or supply the audit, configuration,
atomic-activation, address, vault-ID, cap-integer, or operational proof
required by M2-M5. This slice owns only reviewed configuration projections.
Every field that depends on those later artifacts remains blocked until its
exact Track 8 gate closes.

### Track 1 / CCIP

GREEN and RIPE CCIP are a separately reviewed promotion target within seven
days after launch, not an initial-launch blocker or configuration assumption.
The current thin-Solidity subclass decision is a reviewed reference direction
only: it is non-production and not deployment-authorized. RipeHq IDs `23` and
`24` remain provisional, and GREEN/RIPE capabilities remain disabled
continuously through promotion. Production dependency packaging,
compiler/build settings, audit, gas, external roles, registration, and
activation remain separately blocked. If Track 1 or H-12 evidence is
incomplete or late, the routes remain disabled. No provisional pool ID,
address, remote mapping, admin, capability, or artifact enters this slice
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
