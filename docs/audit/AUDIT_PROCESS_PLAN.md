# Ripe Protocol Component Audit Process Plan

## Document status

- **Purpose:** define how Ripe Protocol will be reviewed component by component.
- **Planning baseline:** live `rh` / `origin/rh` at commit `02468586d710e2cce2360c2bc07e94de6ebdab29`, tree `082a460d0ee190ac74a87ab29828d9c867ddff06`.
- **Created:** 2026-07-28.
- **Refreshed:** 2026-08-11 from the live remote `refs/heads/rh`; the local `rh` worktree was 80 commits behind and was not used as the refresh source.
- **Process model amended:** 2026-08-11 to add transaction-flow cells, canonical permutation coverage, cross-agent evidence and finding controls, and capacity-safe sub-waves.
- **Independent-review reconciliation:** 2026-08-11 to add an activation decision packet, inherited-authority and known-defect carry-forward, exact test-gate selection rules, governance-key and configured-exposure review, delta-weighted scheduling, tiered traceability, and budget/stop-loss gates.
- **Scope of this document:** audit organization, review standards, work batches, evidence, and completion gates.
- **Refresh performed:** repository-wide source, test, configuration, migration, manifest, ABI, CI, Solidity-build, and provenance inventory plus focused integrity validation.
- **Not in scope:** treating this refresh as the audit itself, making or closing security findings, changing production source, attesting live-chain state, or authorizing deployment, configuration, activation, or release.

The planning baseline identifies the tree used to organize this document. Each actual audit batch must pin its own target commit and tree, deployment/configuration snapshot, compiler and test-tool versions, external dependency identities, and any relevant onchain state before review begins. A later `rh` commit does not silently update an active audit batch.

### Current `rh` inventory snapshot

The refreshed tree contains:

- 62 primary non-mock Vyper files totaling 37,873 physical source lines.
- Two Ripe-owned Solidity CCIP wrapper files totaling 117 lines, plus 18 vendored Chainlink/OpenZeppelin Solidity files totaling 1,792 lines.
- 34 Vyper mock contracts, which remain fidelity-review subjects rather than primary production ownership files.
- 170 Python test files, including 151 `test_*.py` modules totaling 146,979 lines.
- 85 committed migration scripts: 66 Base mainnet, three Base Sepolia, 13 Robinhood mainnet, and three Robinhood testnet.
- Six retained current-manifest snapshots, 54 exported ABIs, six Vyper interfaces, eight top-level configuration files, and 48 non-ABI operational scripts.
- Four non-local declared network profiles or deployment families: Base mainnet, Base Sepolia, Robinhood mainnet, and Robinhood testnet, plus the local profile.

The snapshot's default lean collection is 3,550 selected tests plus 282 deselections; clearing repository `addopts` collects 4,521 selected tests plus 143 deselections. Collection success and the focused refresh checks recorded in Section 14 are inventory evidence only, not a full-suite or security conclusion.

### Relevance assessment

The original process remains sound: frozen baselines, assessment/remediation separation, evidence-first review, 12 primary ownership batches, cross-cutting matrices, independent retest, and dependency-aware parallel work are all still applicable. The July plan was nevertheless materially stale for `rh`. This refresh incorporates:

- Robinhood-specific launch and live-replacement defaults, network profiles, chain identity, and deployment source authority.
- The action-block clock model used by Ledger on an Arbitrum-derived chain, alongside timestamp and inherited `block.number` semantics.
- Exact-receipt and deficient-backing containment, Stock-token delivery paths, Stability Pool hardening, RipeGov controls, and the unified VaultMigrator surface.
- Morpho V2 yield pricing and the present but non-admitted Uniswap V2 price-source candidate.
- Solidity/Foundry CCIP token pools, vendored dependency provenance, cross-chain supply conservation, and four-network wiring.
- The simplified migration-history model, retained current manifests, extracted-file recovery evidence, artifact identity gates, and lean/comprehensive CI lanes.

Historical decision documents, parked-lane labels, and prior test reports remain inputs. They do not remove source from the audit scope, prove current behavior, or replace a fresh batch baseline and execution record.

## 0. Program decision packet and activation gate

This program has two distinct outputs:

1. A **candidate-specific launch/activation decision packet** that can support a
   time-bound `GO`, `CONDITIONAL GO`, `NO-GO`, or `NOT ASSESSED` recommendation
   for one exact source, artifact, configuration, deployment, and authority
   candidate.
2. A **comprehensive audit completion record** under Section 9, covering all 12
   batches, canonical flows, cross-cutting matrices, remediations, residual
   risks, and post-freeze deltas.

Neither output authorizes deployment, migration execution, configuration,
activation, or release. Those phases still require fresh exact owner authority.
A launch decision may be needed before the comprehensive program finishes; it
must therefore state every incomplete batch, flow, test lane, external fact,
and residual uncertainty rather than presenting partial review as full audit
completion.

The decision packet must bind:

- Exact commit/tree, compiler inputs, source/runtime identities, manifests,
  configuration, network, deployed addresses, active feature set, and onchain
  observation time.
- The current reconciled `status.yaml`, `RH-D` decisions, inherited `F-` and
  `DV-` issues, parameter-ledger invalidation triggers, audit findings, and
  strict-xfail register that intersect the candidate.
- Governance Safe/authority identity, signer and quorum evidence, modules,
  guards, recovery/rotation controls, final permission state, and irreversible
  handoff status.
- Required local, artifact, release, fork, Solidity, configuration, migration,
  and runtime-identity gates, with exact selected and deselected node counts.
- The recommendation, rationale, decision owner, timestamp, expiry/recheck
  triggers, open conditions, monitoring/abort controls, and prohibited
  substitutions.

### 0.1 Hard activation rule

Activation is `NO-GO` when any of the following is true:

- A Critical finding is not `Fixed and verified` or `Not applicable`; Critical
  risk acceptance is not an activation disposition.
- A High finding is `Open`, `Fix planned`, `Fixed pending retest`, `Partially
  fixed`, `Challenged`, or `Disputed`. A High `Risk accepted` disposition
  requires explicit written activation authority naming the exact exposure,
  configured caps, reachable cap increases, monitoring, expiry, and owner.
- A potentially Critical/High inherited `F-`, `DV-`, `RH-D`, strict-xfail, or
  deployment-readiness item lacks a current re-affirmed, superseded, fixed, or
  explicitly accepted disposition against the candidate.
- An applicable gate selects zero tests, expected collection is not asserted,
  the fork axis or strict-xfail result is unaccounted for, or a required
  Solidity/runtime/deployment identity is unreproduced.
- Governance signer/quorum/key custody, an irreversible authority handoff, a
  required external identity, or a deployment/configuration blocker remains
  unverified.

A Medium item may remain only as an explicit `Risk accepted` disposition with
written activation authority. Low and Informational items may remain open only
when the decision packet names their owner, bounded exposure, monitoring,
remediation/recheck trigger, and expiry. `CONDITIONAL GO` cannot be used to
route around a Critical/High rule.

### 0.2 Budget, calendar, and stop-loss gate

Before each wave, the owner must record a maximum reviewer-day budget,
wall-clock envelope, compute/RPC budget, active-pod and active-flow cap, and the
decision that additional spend is intended to inform. A wave may not begin
with these fields blank. The audit lead halts fan-out and requests an owner
decision when any of the following occurs:

- The wave consumes 75% of a budget while more than 50% of its exit evidence is
  still open.
- Matrix reconciliation, dependency handoffs, independent challenges, or
  retests become the throughput bottleneck for two consecutive reporting
  intervals.
- The candidate, authority corpus, deployment scope, or configured exposure
  changes enough to invalidate the frozen charter.
- A new Critical/High root cause changes the launch decision, or evidence shows
  the current batch/flow decomposition is producing duplicate or rubber-stamped
  work.

The bounded calibration pilot runs before full Wave 1 fan-out. Its measured
review, synthesis, reconciliation, and challenge throughput must be accepted by
the owner before committing the larger program budget.

### 0.3 Right-sized launch-decision track

The comprehensive audit remains the default long-form program. When the
immediate decision is launch readiness, the owner may authorize a narrower
decision track without representing it as comprehensive completion:

- **Lane A — Release identity first:** reproduce source-to-runtime identity for
  every Robinhood deployment target, defaults authority, manifest, final
  permission state, and Safe action surrounding irreversible setup.
- **Lane B — Delta and authority spine:** review all `master…rh` changed
  value-moving production source plus RipeHq, Ledger, MissionControl,
  Switchboards, Teller, registries, token authority, and governance handoff.
- **Lane C — Four launch compositions:** `LDT-01` custody ingress/egress and
  migration; `LDT-02` borrow/repay/liquidation/deleverage; `LDT-03`
  price/admission/configuration mutation; and `LDT-04` deployment identity,
  final permissions, and proof that parked or disabled features remain
  unreachable.

This track may combine required content into four evidence packets rather than
creating one file per batch artifact. It must still satisfy Section 0.1, list
all unaudited source, and obtain a fresh-context challenge for every
load-bearing launch claim.

## 1. Audit objective

The audit should produce an evidence-backed assessment of:

1. What each component is intended to do.
2. How its contracts, inherited modules, interfaces, configuration, and dependencies implement that intent.
3. Which trust assumptions, permissions, invariants, external calls, and failure modes govern it.
4. How well the existing tests demonstrate the intended behavior and protect against unsafe behavior.
5. Which security, correctness, accounting, availability, integration, or test-coverage gaps remain.
6. What must be remediated, accepted as residual risk, or reviewed again before the component is considered complete.

The audit will be divided into bounded batches. A contract has one primary ownership batch, while its interactions with other components are also reviewed at the relevant integration boundaries. End-to-end transaction flows may cross several batches; each material flow receives one named flow owner and one canonical flow packet without displacing the primary source owner for any contract.

### Audit program at a glance

| Order | Batch | Primary result |
| --- | --- | --- |
| 1 | Shared modules and protocol state | Shared authority, state-ownership, and accounting invariants |
| 2 | Governance, registries, and configuration control plane | Complete configuration and dependency-replacement authority map |
| 3 | Asset, vault, and price registries plus oracle sources | Price-integrity and asset-registration threat model |
| 4 | Protocol tokens, tokenized accounting, and cross-chain supply | Token/accounting compatibility plus cross-chain supply and bridge-authority model |
| 5 | Deposit vaults, vault accounting, and position migration | Vault-family accounting, asset-behavior, and migration-continuity model |
| 6 | Deposit and withdrawal entry points | End-to-end Teller boundary assessment |
| 7 | Credit, borrowing, repayment, and debt lifecycle | Debt state machine and conservation model |
| 8 | Liquidations, auctions, and deleveraging | Insolvency, collateral, and bad-debt flow model |
| 9 | Endaoment subsystem | Reserve, fund-flow, and mint/redeem model |
| 10 | Rewards, bonds, and incentive distribution | Incentive accrual and distribution model |
| 11 | Protocol governance and operational departments | Governance and department authority matrix |
| 12 | Deployment, migrations, interfaces, and release integrity | Deployment-to-audited-source integrity evidence |

## 2. Operating principles

### 2.1 Freeze the review target

Before a batch starts, record:

- Git commit and tree hash.
- Branch, remote-ref verification, worktree, and cleanliness.
- Vyper, Titanoboa, Python, pytest, solc, Foundry, and dependency versions applicable to the batch.
- Exact Ripe-owned and vendored source identities, including the Chainlink/OpenZeppelin Solidity subtree when CCIP is in scope.
- Relevant deployment manifests, migrations, defaults, and configured addresses.
- Supported networks and any differences between local, Base mainnet/Sepolia, and Robinhood mainnet/testnet deployments in scope.
- Whether configuration represents a fresh launch, a live-replacement snapshot, a candidate, an admitted component, or active onchain state.
- Known exclusions and accepted assumptions.

Code movement after the freeze either starts a new audit revision or is handled as an explicit, reviewable delta.

### 2.2 Separate assessment from remediation

The audit phase should be evidence-first. Contract changes, test additions, configuration changes, and migration work should occur in separately authorized remediation branches. This keeps findings independent from their fixes and makes the final retest scope precise.

### 2.3 Review behavior, not only files

Each batch must cover:

- Direct source files.
- Imported and inherited modules.
- Ripe-owned Solidity, vendored source, compiler settings, and external protocol code where applicable.
- Interfaces and exposed ABI.
- Storage layout and initialization.
- Registry, configuration, and governance dependencies.
- External calls and token/oracle assumptions.
- Deployment and migration wiring.
- Direct tests, shared fixtures, mocks, integration tests, and fork tests.
- Generated files and the human-edited sources, commands, and live inputs from which they are derived.
- Cross-component state transitions.

### 2.4 Treat test coverage as semantic evidence

Line or statement coverage is useful but not sufficient. The audit must also map behaviors, branches, state transitions, permissions, invariants, failure paths, economic boundaries, and interactions to tests.

The repository's default pytest lane intentionally excludes deployment,
deployment-profile, inventory, release, artifact, fuzz, gas, and H-09 fork
paths. No batch may infer whole-scope coverage from the lean lane alone. The
audit record must state which marker and path selectors ran, which `--fork`
mode applied, which nodes were selected/deselected/ignored/xfail, and whether
global Boa state, Git-history dependencies, operating-system constraints, or
network opt-ins affect reproducibility.

### 2.5 Keep conclusions reproducible

Every material conclusion should identify the reviewed commit, file/function or interaction, relevant test or reproduction, assumptions, impact, and confidence. Commands and test environments should be recorded without secrets.

### 2.6 Use documentation and prior work as inputs, not proof

Audit inputs should include:

- The exact source, compiler artifacts, deployment manifests, configuration, and onchain state in scope.
- The [technical documentation linked from the repository README](https://ripe-finance.gitbook.io/ripe-developers), captured with its URL and access date or as a versioned snapshot when possible.
- Intended-behavior specifications and architecture notes.
- Prior audit reports, known-issue lists, incident reports, remediations, and accepted-risk records supplied for the batch.
- The canonical Robinhood authority corpus, including:
  - `docs/chains/rh/status.yaml` for machine-readable lifecycle and blocker state;
  - `docs/chains/rh/decision-register.md` for the canonical `RH-D` decision and accepted-risk namespace;
  - `docs/chains/rh/rh-production-vyper-review-findings.md` for inherited `F-01` through `F-16` NO-SHIP findings;
  - `docs/chains/rh/component-matrix.md` for component dispositions and reuse claims;
  - `config/robinhood-parameters.json` for the 403-row parameter ledger, blocker states, provenance, and per-row invalidation triggers; and
  - every strict `DV-` or owner-deferred xfail intersecting the batch.
- `docs/simplification/REMOVED.md`, `docs/simplification/extracted-files.tsv`, and the associated validation evidence when an audit conclusion depends on extracted deployment history, removed test/probe infrastructure, or recovery claims.

Source and deployment evidence remain authoritative for what the system actually does. Documentation establishes intent and context; any divergence between documentation, tests, source, and deployed configuration must be logged rather than silently resolved. Private findings and sensitive operational material must stay in the approved private reporting channel.

These authorities must be rebound before Wave 0 closes. At the planning
baseline, `status.yaml` names program subject `0372d486…`, 131 commits before
the reviewed `rh` commit, with 19 contract paths changed afterward. The
parameter ledger names baseline `a86650b…`, 212 commits before the reviewed
commit, with 41 contract paths changed afterward. Their current bytes remain
mandatory historical and decision inputs, but neither stale subject identity
may be treated as current candidate proof. Rebinding must preserve existing
identifiers, disposition history, accepted-risk rationale, and invalidation
triggers while showing exactly what changed.

New audit findings use the `AUD-###` namespace. Hypotheses use `AUD-HYP-###`,
observations use `AUD-OBS-###`, and flow IDs use `AUD-FLOW-##`. Existing
`RH-D###`, `F-##`, `DV-##`, component, parameter, blocker, and launch-track IDs
are linked rather than renumbered or re-opened as apparently new findings.

## 3. Standard workflow for every batch

### Phase 0 — Batch charter and scope freeze

Create a short batch charter containing:

- Primary contracts and owned source paths.
- Supporting modules, interfaces, configuration, migrations, and tests.
- Entry points and privileged roles.
- Material transaction flows owned by the batch or traversing its source, with named flow owners.
- Explicit exclusions.
- Upstream dependencies and downstream consumers.
- Target commit and environment.
- Language/compiler and vendored-dependency scope.
- Network, manifest, configuration-source, and deployed-state scope.
- The exact `master…rh` production delta intersecting the batch and the
  evidence, if any, proposed for unchanged source.
- Every inherited `RH-D`, `F-`, `DV-`, component, parameter, blocker,
  strict-xfail, prior-audit, and accepted-risk identifier intersecting scope,
  with its current and proposed disposition.
- A baseline-suite record with exact command, selected/deselected/skipped/
  xfailed counts, known failures, fork mode, marker/path selection, and raw
  output location.
- The approved reviewer-day, calendar, compute/RPC, active-work, and stop-loss
  envelope for the batch.
- Required reviewers and completion criteria.

**Gate:** scope, baseline, dependencies, inherited dispositions, baseline test
result, authority freshness, and resource envelope are agreed before detailed
review begins.

### Phase 1 — Architecture and threat-model mapping

Document:

- Component purpose and assets at risk.
- Users, administrators, governance, keepers, integrations, and external protocols.
- Trust boundaries and privileged operations.
- Governance Safe, signer/quorum, module/guard, key custody/rotation/recovery,
  emergency authority, cross-chain key reuse, and irreversible handoff
  assumptions, without collecting or exposing secret material.
- State machine and critical state transitions.
- Asset, debt, share, price, reward, and permission flows as applicable.
- External calls, callbacks, reentrancy surfaces, and denial-of-service dependencies.
- Assumptions about tokens, price sources, block/time behavior, and third-party systems.
- Cross-chain supply, message, rate-limit, remote-pool, and ownership assumptions where CCIP is reachable.
- Which operations use timestamp, inherited `block.number`, the ArbSys action-block source, or another clock.
- Migration and live-replacement invariants, including preservation of user positions, registry topology, and generated configuration.
- Component-specific invariants.

**Output:** an architecture/data-flow note and an initial invariant register.

### Phase 2 — Manual contract review

Review every in-scope public, external, internal, and privileged path for:

- Authorization and role transitions.
- Multisig threshold and signer concentration, Safe modules/guards, key
  compromise/rotation/recovery, transaction simulation, final ownership, and
  the consequences of governance/Safe/guardian role concentration.
- Initialization and configuration safety.
- State-update ordering and reentrancy.
- Accounting conservation and balance reconciliation.
- Rounding, precision, decimal normalization, overflow/underflow, and zero-value behavior.
- Input validation and unsafe defaults.
- Pausing, shutdown, recovery, and liveness.
- External-call return values and failure handling.
- Event accuracy and observability.
- Dependency failure, stale data, and malicious integration behavior.
- Griefing, front-running, sandwiching, and denial-of-service opportunities.
- Cross-function and cross-contract invariant preservation.
- Source/runtime identity, generated-input authority, and immutable constructor binding.
- Cross-chain mint/burn authority, replay/domain separation, remote-pool configuration, rate limits, RMN behavior, and ownership handoff where applicable.
- Configured launch exposure, authorized reachable exposure after timelocked or
  emergency changes, time-to-increase, uncapped balances, and whether severity
  changes when a cap or admission state changes.

Static tools or compiler diagnostics may supplement manual review, but tool output is evidence to triage rather than a substitute for reasoning.

**Output:** annotated review notes and candidate findings with source references.

### Phase 3 — Existing test-suite assessment

Build a tiered source-to-test traceability matrix. On the planning baseline,
the production Vyper surface contains 973 external functions, including 582
state-changing externals, 59 `@nonreentrant` externals, and four `@payable`
externals, plus 1,640 explicit `assert`/`raise` conditions and 1,521 `if`/`elif`
branches. Treating all of these as equivalent rows would invite superficial
sign-off.

- **Tier 1 — exhaustive:** every state-changing external, privileged function,
  `@nonreentrant` or `@payable` path, custody/debt/supply/price/reward/
  configuration/migration transition, affected invariant, and previously
  reported or remediated issue.
- **Tier 2 — exhaustive for the selected risk boundary:** every meaningful
  branch, revert, event, external abnormal response, and integration outcome
  reachable from Tier 1 or used by a launch, monitoring, accounting, or safety
  decision.
- **Tier 3 — counted risk selection:** remaining view/helper behavior is sampled
  by risk and dependency. The matrix records the total population, reviewed
  count, selection rationale, and every untraced remainder as an explicit gap;
  it may not silently mark the remainder covered.

Assess:

- Whether the test actually reaches the intended branch.
- Whether assertions prove the important postconditions.
- Whether revert tests validate the correct reason and unchanged state.
- Whether fixtures or mocks hide production behavior.
- Whether tests are independent and deterministic.
- Whether coverage comes only indirectly through another component.
- Whether fork tests pin blocks and external dependencies reproducibly.
- Whether the lean and comprehensive-local lanes, release/fuzz/gas markers,
  path-selected artifact and H-09 gates, macOS-only job, and separately executed
  Solidity build collectively cover the claimed scope.
- Whether marker and path selectors collect a non-zero, expected population and
  whether a zero-test exit was incorrectly normalized as green.
- Whether the default `--fork local` selection removed Base/mainnet nodes from
  either lean or comprehensive results.
- Whether strict xfails represent inherited open defects, and whether an XPASS
  indicates a required disposition/retest update rather than a generic suite
  regression.
- Whether a test depends on unreachable Git objects, a dirty worktree, platform-specific filesystem behavior, shared compiler caches, or mutable global Boa state.

**Output:** traceability matrix, coverage evidence, and prioritized test-gap register.

### Phase 4 — Adversarial and invariant validation

Design or review targeted validation for:

- Boundary and zero-value cases.
- Maximum/minimum configured values.
- Repeated and reordered operations.
- Multi-user interactions.
- Malicious or non-standard tokens and receivers.
- Reentrancy and callback behavior.
- Stale, invalid, extreme, or conflicting prices.
- Partial failure and dependency outage.
- Rounding accumulation and value leakage.
- Stateful/property-based sequences.
- Invariants spanning multiple contracts.
- Cross-chain burn/mint sequences, remote-chain misconfiguration, rate-limit exhaustion, duplicate/reordered messages, and bridge pause/ownership failure.
- Vault and RipeGov migration retries, partial batches, list/index preservation, point accounting, legacy-only routes, and rollback atomicity.
- Divergence between launch defaults, generated live-replacement defaults, configured storage, current manifests, and deployed runtime.

New proof-of-concept or regression tests should be proposed in the audit record. Adding them to the repository belongs to the remediation phase unless the batch charter explicitly authorizes test-only changes.

**Output:** reproducible proofs, invariant results, and confirmed findings or closed hypotheses.

### Phase 5 — Integration and deployment review

Confirm that the reviewed behavior is correctly connected through:

- Ripe HQ and registry addresses.
- Switchboard/default configuration.
- Vault and price-source registration.
- Deployment blueprints and constructor arguments.
- Migrations and manifest history.
- Network profiles, chain-ID guards, RPC/fork opt-ins, and explorer/verifier adapters.
- Launch defaults versus live-replacement defaults and their generation/validation path.
- CCIP token-admin registration, pool ownership, remote pool/token wiring, router/RMN configuration, and source-chain symmetry.
- ABI/interface consistency.
- Permissions granted after deployment.
- Network-specific configuration.

Review both sides of each cross-component interaction. Do not assume that isolated component correctness proves system correctness.

**Output:** integration matrix and deployment/configuration observations.

### Phase 6 — Findings review and batch report

For each finding, record:

- Stable identifier.
- Title, severity, confidence, and status.
- Affected source and deployment/configuration scope.
- Preconditions and attack or failure path.
- Impact and affected invariant.
- Evidence or minimal reproduction.
- Recommended remediation and reasonable alternatives.
- Residual risk if no change is made.
- Required regression test.

Also record informational observations, test gaps, and explicitly tested hypotheses that did not become findings.

**Gate:** all findings have evidence, severity rationale, an owner, and a disposition, and the batch has contributed or explicitly marked not applicable its rows in every cross-cutting matrix from Section 7.

### Phase 7 — Remediation and independent retest

For approved fixes:

1. Review the exact source and test delta.
2. Run the required regression and batch suites.
3. Re-evaluate affected invariants and integrations.
4. Check whether the fix introduces new permissions, storage, external calls, or deployment changes.
5. Record fixed, partially fixed, risk accepted, or unresolved status.

**Gate:** no batch is closed solely because a patch exists or tests pass. Closure requires independent verification against the finding and its affected invariant.

## 4. Standard evidence package

Each batch should produce the same small set of artifacts:

1. **Batch charter** — baseline, scope, dependencies, exclusions, and reviewers.
2. **Component map** — contracts, roles, assets, state, and call/data flows.
3. **Invariant register** — invariant, rationale, enforcement points, and validation.
4. **Source-to-test matrix** — behavior and branch coverage with exact test references.
5. **Test-gap register** — missing or weak evidence, risk, and proposed test.
6. **Findings register** — confirmed issues and informational observations.
7. **Cross-cutting matrix delta** — rows added, changed, closed, or marked not applicable by the batch.
8. **Batch report** — executive summary, detailed results, residual risks, and open decisions.
9. **Remediation/retest log** — exact fix commit, tests, reviewer, and final status.
10. **Source ownership manifest** — every primary production source assigned exactly once, with supporting, vendored, generated, mock, interface, migration, and cross-batch dependencies separately classified.
11. **Transaction-flow index and flow packets** — every material end-to-end flow led by the batch or materially traversing its source, with the canonical owner, participating batches, permutation coverage, handoffs, findings, and closure state.

The batch charter incorporates inherited-authority dispositions, the
`master…rh` delta, the baseline-suite/known-failing record, and the approved
resource envelope. The findings register links inherited identifiers and uses
the `AUD-` namespace only for genuinely new audit conclusions. The batch report
states its contribution to the Section 0 decision packet.

This list defines required content, not eleven separate files. A pod or
right-sized decision lane should combine compatible material into the smallest
reviewable evidence bundle that preserves ownership, raw evidence,
reproducibility, and independent challenge. Artifact count is never a progress
metric.

Artifacts should distinguish:

- **Observed fact:** directly supported by source, test output, deployment data, or a reproduction.
- **Inference:** a conclusion drawn from observed facts.
- **Assumption:** an input accepted for the current review.
- **Decision:** an owner-approved disposition or risk acceptance.

## 5. Test-coverage review standard

For each component, coverage should be assessed across the following dimensions:

| Dimension | Required question |
| --- | --- |
| Entry points | Does every external and public behavior have direct or clearly mapped integration coverage? |
| Permissions | Are allowed and forbidden callers tested for every privileged path and role transition? |
| State transitions | Are all valid transitions, invalid transitions, repeats, and ordering changes covered? |
| Accounting | Are conservation, custody deltas, debt/share/reward totals, rounding, and dust checked? |
| Boundaries | Are zero, one, maximum, minimum, empty-state, first-user, and last-user cases covered? |
| Failure paths | Are reverts, dependency failures, unchanged-state guarantees, and recovery tested? |
| External behavior | Are callbacks, malicious contracts, unusual ERC-20 behavior, stale prices, and bad return data represented? |
| Time/block behavior | Are same-block, boundary-block, cooldown, expiry, and delayed-action cases tested where relevant? |
| Multi-party behavior | Are interleavings between users, keepers, governance, liquidators, and integrations covered? |
| Integration | Is the component tested through its real callers and dependencies, not only isolated mocks? |
| Invariants | Are critical invariants checked over sequences, ideally with stateful or property-based tests? |
| Deployment | Are constructor arguments, registration, permissions, defaults, migrations, and network differences validated? |
| Migration | Are retries, partial batches, index/list preservation, rollback, legacy routes, source cleanup, and state continuity validated? |
| Cross-chain | Are mint/burn conservation, remote identities, replay/order, rate limits, ownership, pause/RMN behavior, and lane symmetry validated? |
| Provenance | Can source, generated configuration, ABI, compiler input, runtime bytecode, manifest, and deployed address identities be reproduced independently? |

Quantitative coverage should be collected where the Vyper/Titanoboa toolchain reports it reliably. Any unavailable or misleading metric must be called out. Semantic gaps remain reportable even when quantitative coverage is high.

For transaction-flow validation, every applicable dimension above must be explicitly covered, justified as not applicable, or recorded as a gap. Reviewers should not attempt a meaningless full Cartesian product. Use direct coverage for each material factor and boundary, risk-driven pairwise or higher-order combinations where factors interact, and stateful/property-based sequences for ordering-dependent invariants. Preserve the selection rationale, seeds, shrinking results, and untested combinations in the flow packet.

### 5.1 Tooling baseline

The batch charter should pin the exact audit environment. On the refreshed `rh` baseline, the repository uses Python `3.12.0` in CI and locks Vyper `0.4.3`, Titanoboa `0.2.7`, pytest `8.4.2`, pytest-cov `7.0.0`, coverage.py `7.10.6`, and Hypothesis `6.138.15`. The Solidity subtree pins solc `0.8.26`, EVM `paris`, via-IR compilation, 80,000 optimizer runs, and no bytecode hash. The repository does not pin the Foundry executable itself, so each CCIP batch must record `forge --version` in addition to `foundry.toml`.

The current automated topology has two Python CI lanes plus a dedicated macOS
manifest-promotion job. It does **not** have an automated Solidity/Foundry CI
job.

- The default lean lane applies `pytest.ini`, which excludes
  `tests/deployment`, `tests/deployment_profiles`, and `tests/inventory` and
  deselects `release`, `artifact`, `fuzz`, `gas`, and `fork_qualification`
  markers.
- The comprehensive lane clears repository `addopts`; on Linux it skips the
  APFS-bound manifest-promotion module, which runs separately on macOS.
- Both lanes still inherit `tests/conf_env.py`'s default `--fork local`
  selection. On the planning baseline this third selection axis deselects 102
  of 404 `tests/priceSources` nodes and 40 of 326 `tests/core/endaoment` nodes.
  Clearing `addopts` does not make the comprehensive lane an all-fork superset.
- With `addopts` cleared, marker-only collection selects 131 `release`, four
  `fuzz`, and five `gas` nodes. The registered `artifact`,
  `fork_qualification`, and `serial` markers each select zero nodes.
- The real artifact gate is path-selected:
  `tests/inventory/test_contract_artifacts.py` plus
  `tests/test_vault_pointer_runtime_sizes.py` collect 50 nodes.
- The H-09 fork framework is path- and environment-selected under
  `tests/deployment/fork/**`; it does not use the `fork_qualification` marker.
  In safe-default disabled mode, the bound tree collects 177 of 178 nodes and
  deliberately deselects the one archive-required node. Archive qualification
  requires `RIPE_RH_FORK_MODE=read-only-archive-fork`, complete accepted owner
  envelopes and identities, the exact endpoint alias and block pin, read-only
  RPC policy, evidence destination, and teardown/replay record.
- The suite contains 22 strict-xfail nodes from 13 decorator sites covering
  `DV-04`, `DV-05`, `DV-08`, `DV-09`, `DV-10`, `DV-13`, `DV-14`, `DV-15`, and
  the owner-deferred Uniswap snapshot-manipulation case. They are an inherited
  open-defect register, not ordinary green-suite noise. A strict XPASS requires
  disposition reconciliation and independent retest before the baseline gate
  is considered restored.

Every gate command must first perform or retain a collection preflight and
assert a non-zero expected selected count, the expected deselection set, fork
mode, and strict-xfail inventory. A zero-node pytest exit or any wrapper that
normalizes it to success is a failed gate.

| Gate | Canonical selection on the planning baseline | Collection expectation |
| --- | --- | --- |
| Lean Python | Repository-default `python -m pytest` | 3,550 selected of 3,832; 282 deselected |
| Comprehensive local inventory | `python -m pytest -o addopts=''` | 4,521 selected of 4,664; 143 deselected, including the fork and H-09 safe-default axes. Linux CI additionally ignores the macOS-only promotion module and must assert its correspondingly smaller exact population. |
| Release | `python -m pytest -o addopts='' -m release` | 131 selected |
| Artifact/runtime size | `python -m pytest -o addopts='' tests/inventory/test_contract_artifacts.py tests/test_vault_pointer_runtime_sizes.py` | 50 selected |
| Fuzz | `python -m pytest -o addopts='' -m fuzz` | Four selected |
| Gas | `python -m pytest -o addopts='' -m gas` | Five selected |
| H-09 safe default | `python -m pytest -o addopts='' tests/deployment/fork` with H-09 opt-in variables absent | 177 selected of 178; one exact safe-default deselection |
| H-09 archive qualification | Same path with the chartered opt-in envelope, identities, endpoint, and evidence controls | Non-zero exact node/classification ledger defined by the charter; no unapproved network access |
| macOS manifest promotion | `python -m pytest -o addopts='' tests/deployment/test_current_manifest_promotion.py` on the qualified APFS runner | Non-zero exact collection recorded by the job |
| Solidity build | `forge build --root solidity`, with `forge --version` recorded | All owned and vendored inputs compiled; currently a separately executed gate, not CI |

Use the following tool classes, recording commands, configuration, version, limitations, and raw output:

- **Compilation evidence:** version-pinned Vyper compilation plus relevant `annotated_ast`, deployment/runtime control-flow graph, storage `layout`, `method_identifiers`, runtime source map, integrity hash, ABI, and bytecode outputs; and separately executed Foundry/solc compilation for the Ripe CCIP wrappers and vendored dependencies until an explicit Solidity CI job exists. Compiler artifacts support source review and deployment comparison; they are not security findings by themselves.
- **Execution and coverage:** pytest/Titanoboa for focused, batch, integration, and full-suite execution. Titanoboa ships a `boa.coverage` plug-in for coverage.py; configure it through pytest-cov/coverage.py and validate its Vyper line and branch reporting against a deliberately reached and unreached branch before adopting thresholds.
- **Property and sequence testing:** Hypothesis with Titanoboa for generated values, stateful sequences, and invariant campaigns, with seeds and shrinking results retained.
- **Optional static analysis:** evaluate [Slither](https://github.com/crytic/slither) and appropriate Solidity tooling in an isolated audit environment. Slither is not pinned by this repository; first prove compatibility with the exact Vyper/Solidity versions, imports, vendored source, and initialized-module patterns, then record which detectors and printers are applicable. A clean or incomplete run never replaces manual review.
- **Deployment integrity:** repository ABI export, contract-artifact expectation checks, migration/current-manifest validation, network-profile assertions, verification adapters, Foundry artifacts, and runtime-bytecode comparison tools, executed read-only unless a separate deployment authorization exists.
- **Reproducibility controls:** private caches and basetemps, socket denial where required, secret/environment scrubbing, full Git history for provenance tests, and separate processes for suites that share mutable Boa state.

The pilot batch must turn these mechanisms into a versioned command sheet. Tool installation or experimentation must not alter the frozen repository environment.

## 6. Proposed audit batches and order

The order below starts with shared trust, state, and price infrastructure before auditing components that depend on them. Batches may overlap only when ownership and frozen commits are explicit.

The registry work described at kickoff is split between Batches 2 and 3: Ripe HQ, Switchboard, Address Registry, and defaults form the authority/configuration control plane, while Price Desk, Vault Book, and price sources form the asset/valuation data plane. They can be scheduled as one paired workstream, but should retain separate threat models and findings scopes.

### Planning size and resourcing

The table below uses physical source lines, including comments and blank lines,
from the refreshed `rh` tree. Counts cover primary Ripe-owned production source
only; imported dependencies, vendored Solidity, mocks, tests, deployment
artifacts, remediation, reporting, and independent retest add effort. The delta
columns compare `master` commit `91eda49…` with planning baseline `rh`
`0246858…`; churn is additions plus deletions and counts a new file by all of
its added lines. Sizes are relative planning aids, not calendar estimates. Each
size combines source volume, delta, integration breadth, accounting/economic
density, adversarial surface, privilege, and expected cross-batch validation;
it is not derived from line count alone.

| Batch | Primary Vyper | Owned Solidity | Raw primary lines | Changed Vyper vs `master` | `+/-` churn | Size | Principal complexity flags |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 1 | 6 | 0 | 3,148 | 3 | 116 | L | Shared state, permissions, action-block identity, and invariants used by most downstream components |
| 2 | 13 | 0 | 10,600 | 6 | 1,589 | XL | Address initialization, four defaults variants, governance, and five configuration switchboards |
| 3 | 13 | 0 | 7,397 | 2 | 919 | XL | Heterogeneous active/candidate price sources, normalization, staleness, admission, and registry routing |
| 4 | 5 | 2 | 1,224 | 1 | 16 | XL | Token standards, privileged and cross-chain supply, signatures, shares, CCIP ownership/rate limits, and two languages |
| 5 | 9 | 0 | 4,171 | 5 | 1,380 | XL | Four vault families, exact custody, shares/rebases/losses, rewards, and unified position migration |
| 6 | 2 | 0 | 1,488 | 2 | 269 | L | Central asset entry point, typed custody observations, action-block checks, callbacks, and broad side effects |
| 7 | 2 | 0 | 1,690 | 2 | 28 | L | Debt, interest, zero-backing containment, Stock collateral, repayment, redemption, and oracle dependence |
| 8 | 3 | 0 | 2,854 | 1 | 33 | L | Auctions, Stock delivery, deleveraging, bad debt, incentives, and liveness |
| 9 | 3 | 0 | 2,255 | 0 | 0 | L | Reserve custody, privileged transfers, stabilizer, yield positions, and PSM economics |
| 10 | 3 | 0 | 2,082 | 2 | 248 | L | Rewards, send floors, claim/migration cleanup, bonds, cadence, budgets, and multi-user fairness |
| 11 | 3 | 0 | 1,081 | 1 | 28 | M | Governance execution, contributor templates, compensation, and authority |
| 12 | 0 | 0 | Not comparable | N/A | N/A | XL | 151 enumerated release-identity files plus config, operational scripts, Solidity build inputs, CI, provenance, and network-specific deployment state |

The 62 primary non-mock Vyper files total 37,873 raw lines, and the two Ripe-owned Solidity wrappers add 117 lines. Batch 4 must also review the 18-file, 1,792-line vendored Chainlink/OpenZeppelin subtree as a pinned dependency, without misclassifying it as Ripe-owned source. Batch 12's 151 enumerated release-identity files are 85 migrations, six retained current manifests, 54 exported ABIs, and six Vyper interfaces; its scope also includes eight top-level config files, 48 non-ABI scripts, one Python CI workflow, Solidity build configuration, and relevant provenance fixtures/documents.

`rh` is a strict 462-commit descendant of `master` at the planning baseline.
Twenty-five of 62 production Vyper files differ, with 4,199 added and 427
deleted lines. Batches 2, 5, 3, and 6 contain 4,157 of 4,626 changed lines
(89.9% of production-source churn); Batch 9 contains none. Delta concentration
sets reviewer priority and supports the right-sized decision track, but does
not prove unchanged source safe. The repository supplies no current external
audit of `master` that can be assumed as inherited assurance. Any reduced
review of unchanged source is an explicit owner risk acceptance naming the
evidence relied upon and the unreviewed remainder.

After the pilot, replace relative sizes with reviewer-day ranges based on measured source mapping, test analysis, adversarial validation, reporting, and independent-retest throughput. Do not infer effort from line count alone.

### Batch 1 — Shared modules and protocol state

**Primary source scope**

- `contracts/modules/Addys.vy`
- `contracts/modules/DeptBasics.vy`
- `contracts/modules/LocalGov.vy`
- `contracts/modules/TimeLock.vy`
- `contracts/data/Ledger.vy`
- `contracts/data/MissionControl.vy`

**Initial test roots**

- `tests/modules/`
- `tests/data/`
- `tests/clock/`
- Relevant action-block, vault-migration, and composed Teller tests
- Shared fixtures in `tests/conf_*.py` and `tests/conftest.py`

**Audit focus**

- Shared authorization and address lookup assumptions.
- Governance transfer, timelock, and privilege boundaries.
- Canonical state ownership and allowed writers.
- Ledger/accounting invariants used by deposits, debt, rewards, and liquidations.
- Native versus ArbSys action-block identity, strict returndata validation, same-action exclusion, and failure behavior.
- User/vault and borrower index integrity during removals, migrations, and partial cleanup.
- Global risk parameters and their validation.
- Failure propagation to downstream components.

**Primary outcome**

A trusted foundation map for later batches, including shared invariants and privileged write paths.

### Batch 2 — Governance, registries, and configuration control plane

**Primary source scope**

- `contracts/registries/RipeHq.vy`
- `contracts/registries/Switchboard.vy`
- `contracts/registries/modules/AddressRegistry.vy`
- `contracts/config/DefaultsBase.vy`
- `contracts/config/DefaultsLocal.vy`
- `contracts/config/DefaultsRobinhood.vy`
- `contracts/config/DefaultsRobinhoodLive.vy`
- `contracts/config/SwitchboardAlpha.vy`
- `contracts/config/SwitchboardBravo.vy`
- `contracts/config/SwitchboardCharlie.vy`
- `contracts/config/SwitchboardDelta.vy`
- `contracts/config/SwitchboardEcho.vy`
- `contracts/config/TrainingWheels.vy`

**Initial test roots**

- `tests/registries/`
- `tests/config/test_defaults_robinhood*.py`
- `tests/config/test_switchboard_*.py`
- `tests/config/test_training_wheels.py`
- Relevant governance and timelock tests from `tests/modules/`

**Audit focus**

- Department registration, replacement, enablement, and authority.
- Address integrity and dependency rewiring.
- Governance/Safe/guardian identity, signer set, threshold, signer
  independence, modules, guards, transaction policy, key custody/rotation/
  recovery, cross-chain address reuse, and concentration of emergency and
  treasury-controlling authority.
- Configuration ranges, defaults, and unsafe combinations.
- Authority and non-interchangeability of Base/local, Robinhood launch, and generated Robinhood live-replacement defaults.
- Timestamp, inherited-block, and action-block units at every configuration boundary.
- Governance/timelock enforcement and emergency controls.
- Initialization order and partial-configuration states.
- MissionControl, Ledger, vault-pointer, and VaultMigrator registration/replacement paths.
- Network-specific configuration parity and intentional differences.

**Primary outcome**

A complete map of who can configure or replace protocol dependencies and how unsafe configuration is prevented or detected.

### Batch 3 — Asset, vault, and price registries plus oracle sources

**Primary source scope**

- `contracts/registries/PriceDesk.vy`
- `contracts/registries/VaultBook.vy`
- `contracts/priceSources/modules/PriceSourceData.vy`
- `contracts/priceSources/AeroRipePrices.vy`
- `contracts/priceSources/BlueChipYieldPrices.vy`
- `contracts/priceSources/ChainlinkPrices.vy`
- `contracts/priceSources/CurvePrices.vy`
- `contracts/priceSources/PythPrices.vy`
- `contracts/priceSources/RedStone.vy`
- `contracts/priceSources/StorkPrices.vy`
- `contracts/priceSources/UndyVaultPrices.vy`
- `contracts/priceSources/UniswapV2Prices.vy`
- `contracts/priceSources/wsuperOETHbPrices.vy`

**Initial test roots**

- `tests/registries/`
- `tests/priceSources/`

**Fidelity-review subjects**

- Oracle and registry mocks under `contracts/mock/`, compared with the production dependencies they represent

**Audit focus**

- Asset/vault registration and authoritative address selection.
- Price-source routing, fallback, and aggregation behavior.
- Admission state versus mere source presence: an audited candidate is not automatically registered, configured, deployed, or active.
- Staleness, heartbeat, decimals, sign, confidence, and zero-price handling.
- Manipulation resistance and dependence on spot/liquidity conditions.
- Morpho V2 factory/vault validation and fail-closed behavior in BlueChipYieldPrices.
- Uniswap V2 pair provenance, reserve/liquidity assumptions, snapshot cadence, bootstrap/stale handling, upside throttling, and repeated snapshot poisoning.
- The owner-deferred strict-xfail for repeated manipulated Uniswap snapshots,
  carried as an inherited issue until re-affirmed, superseded, fixed, or
  explicitly accepted for the exact admitted/disabled lifecycle state.
- Cross-source disagreement, source failure, and denial of service.
- Governance replacement and configuration safety.
- Mock fidelity versus production oracle behavior.

**Primary outcome**

A price-integrity and asset-registration threat model that downstream vault, credit, and liquidation reviews can rely upon.

### Batch 4 — Protocol tokens, tokenized accounting, and cross-chain supply

**Primary source scope**

- `contracts/tokens/modules/Erc20Token.vy`
- `contracts/tokens/modules/Erc4626Token.vy`
- `contracts/tokens/GreenToken.vy`
- `contracts/tokens/RipeToken.vy`
- `contracts/tokens/SavingsGreen.vy`
- `solidity/src/RipeTokenPool.sol`
- `solidity/src/RipeCcipBurnMintTokenPools.sol`

**Pinned dependency scope**

- `solidity/src/v0.8/` vendored Chainlink CCIP 1.5.1 and OpenZeppelin source
- `solidity/foundry.toml`

**Initial test roots**

- `tests/tokens/`
- CCIP migration, manifest-consumer, artifact, verification, and RipeHq capability tests
- Shared token fixtures under `tests/conf_*.py` and `tests/conftest.py`

**Fidelity-review subjects**

- Token mocks under `contracts/mock/`, including non-standard transfer, blacklist, fee, and callback behavior used by the tests

**Audit focus**

- Mint, burn, transfer, approval, permit/signature, and authorization behavior.
- ERC-20/ERC-4626 compatibility and rounding direction.
- Share/asset conversions and first/last depositor behavior.
- Supply conservation and privileged issuance.
- RipeHq's two-sided mint-capability checks and token-admin/pool authority.
- Cross-chain burn/mint conservation, remote token/pool identities, router/RMN trust, ownership handoff, allowlists, rate limits, pause behavior, and lane symmetry.
- Differences between the testnet `RipeTokenPool` constructor-flag wrapper and the mainnet token-specific pure-capability wrappers.
- Vendored-source identity, compiler settings, upstream equivalence, and build/verification reproducibility.
- Blacklist, fee-on-transfer, rebasing, callback, and non-standard token assumptions.
- Integration assumptions made by vault, credit, reward, and liquidation components.

**Primary outcome**

A token/accounting compatibility model plus cross-chain supply, authority, dependency, and lane-configuration invariants for all asset-moving batches.

### Batch 5 — Deposit vaults, vault accounting, and position migration

**Primary source scope**

- `contracts/vaults/modules/VaultData.vy`
- `contracts/vaults/modules/BasicVault.vy`
- `contracts/vaults/modules/SharesVault.vy`
- `contracts/vaults/modules/StabVault.vy`
- `contracts/vaults/SimpleErc20.vy`
- `contracts/vaults/RebaseErc20.vy`
- `contracts/vaults/StabilityPool.vy`
- `contracts/vaults/RipeGov.vy`
- `contracts/core/VaultMigrator.vy`

**Initial test roots**

- `tests/vaults/`
- Relevant SwitchboardEcho, Ledger, Lootbox, MissionControl, artifact, and runtime-size tests
- Relevant Teller, credit, and liquidation integration tests

**Fidelity-review subjects**

- Vault and token mocks under `contracts/mock/`, compared with the production vault/token behaviors each test claims to represent

**Audit focus**

- Deposit, withdrawal, share, balance, and custody invariants.
- Simple versus share/rebase accounting behavior.
- Yield, positive/negative rebases, loss, dust, and rounding.
- Stability Pool deposits, claims, redemptions, and liquidation effects.
- Ripe governance vault permissions, Teller-only lock paths, point-accrual controls, and reward interactions.
- Unified BasicVault/RipeGov migration authorization, source/target validation, exact transfer and share preservation, list/index integrity, batch atomicity, retries, Base-only legacy routing, and post-migration cleanup.
- The strict `DV-04`, `DV-05`, `DV-08`, `DV-09`, `DV-10`, `DV-13`, `DV-14`,
  and `DV-15` nodes touching vault, Teller, stability, price, and migration
  behavior, with their inherited source decisions and activation effect.
- Fee-on-transfer, rebasing, blacklisting, reentrancy, and failed-transfer behavior.
- Registration and configuration through Vault Book.
- Consistency between reported value, internal accounting, and actual custody.

**Primary outcome**

An accounting and migration-continuity model plus test matrix for every supported vault family, asset-behavior class, and authorized migration route.

### Batch 6 — Deposit and withdrawal entry points

**Primary source scope**

- `contracts/core/Teller.vy`
- `contracts/core/TellerUtils.vy`

**Initial test roots**

- `tests/core/teller/`
- Relevant vault, Ledger, Mission Control, rewards, credit, and deleverage tests

**Audit focus**

- Deposit, withdrawal, rebalance, and housekeeping call paths.
- Caller/user separation, delegated actions, and integration permissions.
- Asset custody deltas and agreement with vault results.
- Strict separation between ordinary user flows and VaultMigrator-only export/import or identity-step flows.
- State-update ordering, callbacks, reentrancy, and partial failure.
- Action-block enforcement across deposit, withdrawal, housekeeping, rebalance, and migration-composed routes.
- Fees, points/rewards side effects, account health, and withdrawal constraints.
- Behavior across supported vault types and non-standard tokens.
- Utility/view consistency with state-changing behavior.

**Primary outcome**

End-to-end assurance for the user-facing deposit and withdrawal boundary, including all state and accounting side effects.

### Batch 7 — Credit, borrowing, repayment, and debt lifecycle

**Primary source scope**

- `contracts/core/CreditEngine.vy`
- `contracts/core/CreditRedeem.vy`

**Integration scope**

- Debt and collateral state in Ledger and Mission Control.
- Teller, vault, token, oracle, rewards, and liquidation interactions.

**Initial test roots**

- `tests/core/creditEngine/`
- Relevant Teller, vault, Ledger, Mission Control, and liquidation tests

**Audit focus**

- Borrow eligibility, collateral value, limits, and health calculations.
- Zero/deficient backing and Stock-token delivery assumptions, including when debt terms, withdrawal limits, and governance weights must collapse to zero or fail closed.
- Interest/rate updates, accrual timing, and precision.
- Partial/full repay, overpayment, refunds, and third-party repayment.
- Debt conservation across mint, burn, repayment, redemption, and liquidation.
- Buyback, redemption, discount, and dynamic-rate behavior.
- Same-block and reordered operations.
- Oracle, configuration, and asset-decimal dependencies.
- Bad debt, insolvent states, and recovery paths.

**Primary outcome**

A complete debt state machine, debt-conservation invariant set, and behavior-to-test matrix.

### Batch 8 — Liquidations, auctions, and deleveraging

**Primary source scope**

- `contracts/core/AuctionHouse.vy`
- `contracts/core/AuctionHouseNFT.vy`
- `contracts/core/Deleverage.vy`

**Initial test roots**

- `tests/core/auctionHouse/`
- `tests/core/deleverage/`
- Relevant credit, vault, Stability Pool, token, Ledger, and price tests

**Audit focus**

- Liquidation eligibility and account-health transitions.
- Auction creation, pricing, bidding, settlement, claim, and cancellation.
- Collateral/debt conservation through partial and full liquidation, using actual delivered custody rather than nominal transfer requests.
- Stability Pool and Savings Green interactions.
- NFT-specific custody and valuation assumptions.
- Deleveraging phases, asset selection, swaps, and withdrawal effects.
- Incentives, front-running, griefing, stale prices, and liveness.
- Bad debt, unfillable auctions, zero-value collateral, and dependency failure.

**Primary outcome**

An end-to-end insolvency and liquidation model showing where value, debt, collateral, and risk move under normal and adversarial conditions.

### Batch 9 — Endaoment subsystem

`Endaoment` is the spelling used by the repository contracts and tests.

**Primary source scope**

- `contracts/core/Endaoment.vy`
- `contracts/core/EndaomentFunds.vy`
- `contracts/core/EndaomentPSM.vy`

**Initial test roots**

- `tests/core/endaoment/`
- Relevant token, price, registry, credit, and governance tests

**Audit focus**

- Fund custody, allowed destinations, and privileged transfers.
- Stabilizer and PSM mint/redeem accounting.
- Pricing, fees, slippage, limits, and decimal handling.
- Governance and operational permissions.
- Reserve conservation and insolvency/failure behavior.
- Interaction with Green, Savings Green, Ripe, credit, and external assets.

**Primary outcome**

A reserve and fund-flow model with explicit mint/redeem and governance invariants.

### Batch 10 — Rewards, bonds, and incentive distribution

**Primary source scope**

- `contracts/core/Lootbox.vy`
- `contracts/core/BondRoom.vy`
- `contracts/config/BondBooster.vy`

**Initial test roots**

- `tests/core/lootbox/`
- `tests/core/bondRoom/`
- `tests/config/test_bond_booster.py`
- Relevant deposit, borrow, governance-vault, and token tests

**Audit focus**

- Points accrual from deposits and borrowing.
- Reward allocation, claiming, refresh cadence, and double-claim prevention.
- Per-deployment Underscore send floors, exact claim delivery, terminal dust, forfeiture/cleanup behavior, and migration interaction.
- RIPE/Underscore reward sources and authorization.
- Bond creation, accounting, vesting/redemption, and booster effects.
- Rounding, dust, budget/supply constraints, and multi-user fairness.
- Timestamp/block assumptions and manipulation.
- Cross-component side effects from Teller and Credit Engine.

**Primary outcome**

An incentive-accounting model proving how rewards and bond value are created, assigned, and claimed.

### Batch 11 — Protocol governance and operational departments

**Primary source scope**

- `contracts/core/Boardroom.vy`
- `contracts/core/HumanResources.vy`
- `contracts/modules/Contributor.vy`

**Initial test roots**

- `tests/core/humanResources/`
- Relevant governance, registry, token, and configuration tests

**Audit focus**

- Proposal/execution and operational authority.
- Contributor creation, compensation, update, and removal.
- Token and fund issuance limits.
- Template/blueprint initialization.
- Governance handoff, timelock, and emergency behavior.
- Safe signer/quorum composition, key lifecycle and recovery, module/guard
  authority, contributor/operator separation, and the blast radius of a
  compromised or unavailable signer set.
- Cross-department privilege escalation or unintended authority.

**Primary outcome**

A role and authority matrix for governance and operational departments, including all value-moving permissions.

### Batch 12 — Deployment, migrations, interfaces, and release integrity

**Primary release/integration scope**

- `config/BluePrint.py`
- `config/robinhood_blueprint.py`
- `config/network_profiles.py`
- `config/Ccip.py`
- JSON launch, reward, parameter, and artifact-expectation configuration under `config/`
- `interfaces/`
- `migrations/`
- Retained `migration_history/**/current-manifest.json` snapshots
- Deployment and verification utilities under `scripts/`
- Exported ABIs under `scripts/abis/`
- Batch 4-owned Solidity source and vendored inputs, plus `foundry.toml` and generated build artifacts used for deployment or verification
- `.github/workflows/python-tests.yml` and `pytest.ini`
- Deployment, deployment-profile, inventory, current-manifest, workflow-health, and provenance tests
- `docs/simplification/` recovery/provenance records and relevant `tests/fixtures/robinhood/provenance/` inputs

**Audit focus**

- Deployment order, arguments, deterministic addresses, and initialization.
- Department, vault, asset, and price-source registration.
- Permission grant/revoke sequence and final authority.
- The exact Safe readback and signer/quorum/module/guard evidence before the
  irreversible `0007_FinishSetup.py` governance handoff, plus recovery truth
  after the deployer loses authority.
- Launch defaults, generated live-replacement defaults, source-of-truth inputs, and network-specific values.
- Migration ordering, uniqueness, replay/resume behavior, current-manifest promotion, and source/history separation.
- Consequences of extracting numeric historical manifests and probe/block-clock infrastructure, including byte-exact recovery and every retained consumer's behavior.
- Base mainnet/Sepolia and Robinhood mainnet/testnet chain IDs, directory ownership, RPC safety, fork opt-ins, explorer adapters, and intentional asymmetry.
- CCIP pool deployment/wiring order, remote-manifest consumption, Safe transaction boundaries, verification commands, and four-network symmetry.
- Source/interface/ABI consistency.
- Artifact expectation files, generated ABI freshness, immutable-bound versus template runtime identities, EIP-170 headroom, and stale-artifact failure behavior.
- Verification and provenance of deployed bytecode.
- Safety of operational scripts, account selection, secret handling, resume/rollback, and failure recovery.
- Lean/comprehensive/macOS CI lane semantics, action pinning, cache isolation, deselections, and fresh-clone reproducibility.
- The separately executed Solidity build gate and the absence of a current
  Solidity/Foundry CI job; no Python CI result may stand in for CCIP compilation.

**Primary outcome**

Evidence that the audited contracts and configuration are the exact contracts and configuration that deployment tooling intends to install and operate on each declared network, without confusing repository readiness with executed deployment or activation.

## 7. Cross-cutting review campaigns

Some risks cannot be closed inside one component batch or transaction flow. At program kickoff, assign one **program matrix owner**, normally the audit lead, and record that person in the audit index. Every batch charter must also name a **batch matrix steward**, normally one of that batch's reviewers, and every flow charter must name a **flow matrix steward**, normally the flow owner.

The stewards seed relevant rows during Phase 1, update them as evidence develops, validate integration rows during Phase 5, and submit versioned deltas at the relevant Phase 6 or flow-closure gate. The program owner reconciles the shared matrices after every batch and flow closure, resolves duplicates or conflicting classifications with the reviewers, and signs the final reconciliation in Section 9. Phase 7 retests must update affected rows and flow packets rather than leaving the pre-fix state in place.

Maintain cross-batch matrices for:

### Access control and governance

Map every privileged function to its allowed caller, how that caller is assigned, how authority changes, timelock/emergency constraints, and tests.

### Governance keys and irreversible authority custody

Bind each governance, Safe, guardian, treasury-controlling, deployer, CCIP
admin, owner, and emergency role to the actual contract/account type. Review
Safe signer identities, threshold, signer independence, modules, guards,
fallback handlers, transaction policy/simulation, cross-chain reuse, hardware
or organizational custody evidence, rotation, recovery, compromise response,
and liveness. Prove the final readback before and after every irreversible
handoff, especially `0007_FinishSetup.py`. Record only public control evidence;
never collect seed phrases, private keys, or secret recovery material.

### Asset and accounting conservation

Trace actual custody, internal balances, shares, Green/Ripe supply, debt, rewards, reserves, and liquidation proceeds across component boundaries.

Require observed token balance deltas wherever nominal transfer amounts can diverge because of fees, blacklists, rebases, callbacks, deficient backing, or bridge behavior.

### Configured exposure and reachable cap expansion

For each value-moving finding, record current configured launch exposure,
deployed/live exposure when applicable, uncapped balances or deposits,
authorized maximum/reachable configuration, who can raise it, the shortest
timelock or emergency path, monitoring, and the invalidation trigger. Severity
must consider both current loss bounds and a realistic governance-reachable
state. On the planning baseline, Robinhood's configured global debt limit is
500e18 versus Base's 200,000e18, while SwitchboardAlpha can change the limit
through governance; the smaller launch value alone cannot permanently bound
severity.

### External-call and reentrancy surfaces

Inventory all token transfers, oracle calls, callbacks, swaps, vault calls, and untrusted receivers; verify state ordering and nested-call behavior.

### Cross-chain supply and message integrity

Reconcile RIPE and GREEN supply across every burn/mint lane; map TokenAdminRegistry, router, on/off-ramp, RMN, owner, rate-limit admin, allowlist, remote pool/token, and RipeHq mint authority. Validate lane configuration in both directions and distinguish source compilation, pool deployment, Safe wiring, ownership transfer, activation, and live operation.

### Oracle and valuation dependence

Map every price consumer to source, decimals, freshness, failure behavior, configuration, and manipulation assumptions.

### Block, time, and ordering dependence

Inventory cooldowns, accrual, expiries, snapshots, same-block restrictions, reward cadence, auctions, and ordering-sensitive behavior. Label every value as timestamp, inherited `block.number`, ArbSys child/action block, or another explicit clock, and test repeated inherited block numbers plus malformed/unavailable action-block sources.

### Migration and state continuity

Trace vault and RipeGov position migration, source export, target import, Teller custody, Ledger participation, Lootbox points/rewards, RipeGov locks, governance configuration, legacy Base routing, retries, partial batches, and cleanup. Prove that migration preserves value and invariants without leaving duplicate, stranded, or prematurely removed state.

### Denial of service and recovery

Identify whether a failing asset, oracle, vault, user, keeper, or privileged dependency can block unrelated users or prevent recovery.

### Deployment and network parity

Compare audited assumptions with each supported deployment's addresses, parameters, migrations, manifests, bridge lanes, clock model, verifier, and enabled feature set. A source present on `rh` may still be candidate-only, parked, non-admitted, undeployed, or inactive.

### Artifact and source authority

Map every human-edited authority, generated contract/configuration, ABI, compiler input, immutable binding, runtime bytecode, manifest, migration, historical recovery record, and deployed address. Require independent reproduction and fail closed on stale or ambiguous authority rather than selecting the newest-looking artifact.

## 8. Finding severity and disposition

New findings receive stable `AUD-###` identifiers. Existing `F-`, `DV-`,
`RH-D`, component, parameter, blocker, or prior-audit IDs remain in their
original namespace and are linked from the audit record.

Use a consistent severity model, refined during audit kickoff:

- **Critical:** credible loss of most or all at-risk funds, unrestricted minting, systemic insolvency, or protocol-wide takeover.
- **High:** substantial loss, bad debt, permanent freezing, or major privilege compromise under realistic conditions.
- **Medium:** bounded loss, significant accounting/availability failure, or serious violation requiring meaningful preconditions.
- **Low:** limited-impact correctness or security weakness with constrained exploitability.
- **Informational:** hardening, clarity, maintainability, observability, or test-quality concern without a demonstrated security impact.

Severity should account for impact, likelihood, required privilege, capital,
timing, detectability, recoverability, and blast radius. Confidence should be
reported separately. Each finding records two exposure views:

- **Configured exposure:** credible impact at the exact candidate's launch or
  deployed caps, admission state, balances, and enabled features.
- **Reachable exposure:** credible impact after realistic authorized cap,
  admission, pause, role, or dependency changes, including the shortest
  timelock/emergency path and any uncapped value.

The final severity is not automatically the lower configured-exposure result.
If governance can reach the higher-impact state within the decision horizon,
the finding either carries that severity or records the exact containment,
monitoring, expiry, and reclassification trigger. Every finding also states its
activation effect: `blocks`, `conditional`, or `nonblocking` under Section 0.1.

Allowed dispositions:

- Open.
- Fix planned.
- Fixed pending retest.
- Fixed and verified.
- Partially fixed.
- Risk accepted.
- Not applicable.
- Duplicate.
- Re-affirmed — an inherited decision, accepted risk, or issue disposition was
  rechecked against the exact candidate and remains valid.
- Challenged — current evidence may invalidate an inherited disposition; both
  rationales remain preserved and the item blocks any dependent conclusion
  until resolved.
- Superseded — a named later authority or finding replaces the earlier item
  without deleting its history.
- Disputed, with both rationales preserved.

## 9. Program-level completion

After all batches:

1. Reconcile cross-batch and cross-flow findings, duplicate root causes, linked manifestations, and preserved disagreements.
2. Run the lean, comprehensive, release, path-selected artifact, fuzz, gas,
   path/environment-selected H-09 fork, macOS-only, separately executed
   Solidity-build, and protocol-wide invariant/integration gates applicable to
   the final candidate. Assert each gate's non-zero collection, expected
   deselections, fork mode, strict-xfail inventory, and exclusions.
3. Have the program matrix owner reconcile and sign off the aggregate permission, asset-flow, debt, price, and deployment matrices plus every canonical flow packet.
4. Reproduce generated defaults, ABIs, compiler artifacts, artifact-expectation records, current manifests, and deployed runtime identities from their declared authorities.
5. Reconcile Base mainnet/Sepolia and Robinhood mainnet/testnet configuration, CCIP lane symmetry, active/admitted feature state, and intentional differences.
6. Confirm every accepted risk has an owner, configured and reachable exposure,
   explicit rationale, expiry/recheck trigger, and current re-affirmation; carry
   forward every inherited `RH-D`, `F-`, `DV-`, parameter, blocker, and
   strict-xfail disposition.
7. Confirm every remediation is tied to a regression test and independent retest.
8. Produce a final report that separates:
   - reviewed source and deployment scope;
   - fixed findings;
   - unresolved findings;
   - accepted residual risks;
   - test limitations;
   - unaudited or changed code.
9. Establish a delta-review policy for changes made after the final reviewed commit.

The protocol audit evidence record may be finalized while explicitly reporting
unresolved findings; that does not make the candidate launchable. Any open or
otherwise unresolved Critical/High item forces the Section 0 decision packet to
`NO-GO`. The protocol audit is complete only for the exact reviewed source,
configuration, and deployment scope. Later changes require impact triage and,
where material, a targeted re-audit.

## 10. Parallel execution model

The program should maximize concurrent evidence gathering without allowing
dependent batches to reach incompatible conclusions. A batch may start before
all upstream batches finish, but it may not close a dependency-sensitive phase
until the relevant upstream model, invariant, and finding handoffs are stable.

The default initial capacity is **five active component pods**, plus one program
matrix owner and one deployment/integration lead. Transaction-flow cells are an
explicit second execution dimension, not uncounted work: every active flow cell
must have a home pod, named participating-pod liaisons, and an entry in the
program work-in-progress register. The initial `AUD-FLOW-01` Deposit flow cell is part of the
bounded Batch 5 pilot rather than a sixth source-owning pod. The audit lead
should raise or lower the pod or flow-cell caps only after the pilot measures
review, synthesis, cross-batch reconciliation, and independent-retest
throughput. More active agents are not useful if canonical model, evidence, or
finding reconciliation becomes the bottleneck.

### 10.1 Component pods, transaction-flow cells, and central roles

Each component pod owns one batch and names:

- A batch lead accountable for its charter, canonical component model, findings,
  and report.
- A contract-review lane for architecture, source paths, permissions,
  accounting, and manual review.
- A test-evidence lane for source-to-test mapping, assertion quality, coverage,
  fixtures, mocks, and reproducibility.
- An adversarial lane for hypotheses, boundaries, malicious integrations,
  properties, stateful sequences, and proof design.
- An integration liaison responsible for dependency handoffs, Phase 5 evidence,
  and the batch's cross-cutting matrix delta.

One person may cover multiple lanes when staffing requires it, but the batch
lead must keep one canonical architecture and invariant model. The independent
retester must not be the person who implemented the remediation being verified.

Each transaction-flow cell names:

- A **flow owner** accountable for one canonical end-to-end call, state, value,
  and test model from initiating actor through terminal outcome.
- A **home pod**, normally the batch that owns the primary entry point or the
  flow's dominant state transition.
- A liaison from every materially traversed component pod, responsible for
  accepting source-sensitive rows and routing candidate findings.
- A fresh-context challenger for Critical/High candidates and other
  load-bearing conclusions selected by the audit lead; that challenger must not
  be the conclusion's author or the remediation implementer.

The flow owner may inspect and test supporting source across batch boundaries,
but does not displace the component pod's authority over its canonical source
model or independently finalize a source-level finding in another pod.

Central roles are:

- The **program matrix owner**, who reconciles permissions, asset flows, debt,
  prices, external calls, timing, availability, and deployment evidence across
  all pods.
- The **deployment/integration lead**, who owns cross-batch wiring, network
  configuration, source/runtime provenance, and the final Batch 12 conclusion.
- The **severity and risk owner**, selected at kickoff, who resolves
  cross-batch severity consistency and records formal risk acceptance.

### 10.2 Transaction-flow ownership and evidence

The initial flow inventory below is a kickoff baseline. Phase 0 may split a flow
when it contains materially different entry points, assets, or terminal states,
or merge only when one flow packet can remain coherent and independently
reviewable. Staffing convenience alone is not a reason to hide distinct flows.

| Flow ID | Canonical flow | Default home batch | Principal participating batches |
| --- | --- | --- | --- |
| `AUD-FLOW-01` | Deposit and exact custody | 6, with the bounded Batch 5 pilot first | 1–6, 10, 12 |
| `AUD-FLOW-02` | Withdrawal, actual receipt, and accounting cleanup | 6 | 1–7, 10, 12 |
| `AUD-FLOW-03` | Borrow and GREEN delivery | 7 | 1–7, 10, 12 |
| `AUD-FLOW-04` | Repayment and redemption | 7 | 1–4, 7, 12 |
| `AUD-FLOW-05` | Liquidation, auction, settlement, and bad-debt reconciliation | 8 | 1, 3–8, 10, 12 |
| `AUD-FLOW-06` | Deleverage and residual account health | 8 | 1, 3–8, 12 |
| `AUD-FLOW-07` | BasicVault and RipeGov position migration | 5 | 1, 2, 4–6, 10, 12 |
| `AUD-FLOW-08` | Stability Pool deposit, claim, and liquidation absorption | 5 | 1, 3–5, 8, 10 |
| `AUD-FLOW-09` | Reward accrual, claim, cleanup, bond creation, vesting, and redemption | 10 | 1, 2, 4–7, 10, 12 |
| `AUD-FLOW-10` | Endaoment reserve movement and PSM mint/redeem | 9 | 1–4, 7, 9, 12 |
| `AUD-FLOW-11` | Price resolution, source failure, and asset/source admission | 3 | 2, 3, 5–9, 12 |
| `AUD-FLOW-12` | Governance, timelock, department, and configuration mutation | 2 or 11, selected in the charter | 1–3, 11, 12 |
| `AUD-FLOW-13` | CCIP burn, message, remote validation, mint, and aggregate supply | 4 | 2, 4, 12 |
| `AUD-FLOW-14` | Deployment, migration, manifest, permission, and runtime-identity transition | 12 | 2–5, 12 |

Each flow cell follows the program's phase discipline: Phase 0 freezes the flow
charter; Phase 1 creates its canonical end-to-end model; Phases 2 and 3 trace
source and tests; Phase 4 validates adversarial permutations; Phase 5 obtains
cross-component acceptance; Phase 6 closes or explicitly leaves open the flow
assessment; and Phase 7 revalidates every affected flow after remediation.

Every flow cell starts with a frozen flow charter that records:

- Flow ID, initiating actor, entry point, beneficiary, and terminal outcomes.
- Target commit/tree, networks, deployed/configured state, lifecycle status, and
  explicit exclusions.
- Home pod, flow owner, participating pod liaisons, and required challenger.
- Preconditions, trust boundaries, privileged variants, and external systems.
- Expected state, custody, supply, debt, share, reward, reserve, and event deltas.
- Crossed contracts, source owners, upstream handoffs, and closure dependencies.
- Applicable permutation dimensions, selection method, and completion criteria.

The canonical flow packet contains:

1. End-to-end call, state, value, and trust-boundary graph.
2. Preconditions, expected postconditions, rollback/atomicity requirements, and
   observability expectations.
3. Permutation matrix with exact source and test references, evidence status,
   not-applicable rationale, and gaps.
4. Executed commands, raw outputs, seeds, reproductions, failed attempts, and
   unchecked areas needed to reproduce the assessment.
5. Hypothesis and finding links, including the affected invariant and every
   flow in which a shared root cause manifests.
6. Versioned dependency handoffs and participating-owner acceptance records.
7. Residual assumptions, open decisions, and the final flow-closure record.

Use the following canonical permutation dimensions. A flow charter may add
dimensions but may not silently omit an applicable one.

| Dimension | Required variants or questions |
| --- | --- |
| Caller and authority | User, delegate, keeper, governance, migrator, integration, and forbidden caller; caller/beneficiary separation and role transitions |
| Amount and arithmetic | Zero, one, dust, rounding boundary, partial, full, configured maximum/minimum, decimal normalization, and accumulated leakage |
| Position and lifecycle state | Empty, first user, existing position, last user, healthy, threshold, insolvent, legacy, migrated, initialized, partially configured, paused, and recovered |
| Asset, vault, and receiver behavior | Standard, fee-on-transfer, rebasing/loss, blacklist, callback/reentrancy, deficient backing, failed/malformed return, supported vault families, and actual receipt |
| Time, block, and ordering | Same action block, repeated inherited block, timestamp and expiry boundaries, delay/cooldown, retry, repeat, reorder, replay, and stateful sequences |
| External dependency | Fresh/stale/zero/extreme/conflicting price, revert, outage, replacement, bad returndata, liquidity exhaustion, and misconfiguration |
| Multi-party and economic behavior | User interleavings, keeper/liquidator competition, front-running, sandwiching, griefing, rate-limit exhaustion, and fairness |
| Failure atomicity and recovery | Failure before/during/after external interaction, partial work, unchanged-state guarantee, retry/resume, rollback, isolation of unrelated users, and terminal cleanup |
| Network and configuration lifecycle | Base/Robinhood, mainnet/testnet/local, launch/live replacement, active/admitted/candidate/parked/legacy, and intentional network asymmetry |
| Cross-chain, when applicable | Source/destination symmetry, remote identity, duplicate/reordered message, domain separation, allowlist, ownership, router/RMN, pause, and rate limits |

Each applicable factor receives direct and boundary coverage. Risk-bearing factor
interactions receive pairwise or higher-order coverage, and order-dependent
behavior receives stateful/property-based validation. The flow packet must
explain why its selected combinations are sufficient and preserve all omitted
or infeasible combinations as explicit limitations.

A flow may begin architecture mapping, source tracing, and test mapping before
all participating batches complete. It may close only when:

- Every crossed component owner accepts its source-sensitive rows or records a
  preserved disagreement.
- Required dependency snapshots are `stable` or `accepted`, rather than merely
  `draft`.
- Its invariant and cross-cutting rows are reconciled by the program matrix owner.
- Candidate findings have one canonical root-cause identity, severity owner
  disposition, and linked affected flows.
- Required fresh-context challenges and reproducibility checks are complete.
- Unchecked variants, residual assumptions, and changed or unaudited source are
  explicit in the closure record.

### 10.3 Parallelism inside a batch and across flows

| Phase | Safe concurrency | Required synchronization |
| --- | --- | --- |
| Phase 0 — Scope freeze | Low | One batch charter and one charter per active flow must bind the baseline, source owners, dependencies, reviewers, and completion gates before fan-out. |
| Phase 1 — Architecture | Moderate | Pods establish canonical component models; flow owners establish canonical end-to-end models. Conflicts are resolved before either becomes a stable handoff. |
| Phases 2 and 3 — Contracts and tests | High | Source, test, and flow reviewers work concurrently and exchange exact path/function/test references through the handoff and hypothesis registries. |
| Phase 4 — Adversarial validation | High after initial invariant and flow registers | Proof work may fan out by threat family or flow permutation, but every result returns to the canonical component invariant and flow packet. |
| Phase 5 — Integration | Moderate | Evidence collection may run early; dependency-sensitive flow conclusions wait for joint acceptance by the flow owner and owning component pods. |
| Phase 6 — Findings and report | Moderate | Evidence drafting may be parallel, but root-cause identity, linked flow manifestations, severity, disposition, and reports are centrally reconciled. |
| Phase 7 — Remediation and retest | High only for non-overlapping fixes | Shared source and release artifacts require a named integration owner; each fix receives independent retest and affected flows are revalidated. |

### 10.4 Program waves

The waves control when conclusions may close, not when reviewers may begin
reading code or mapping tests.

| Wave | Concurrent work | Exit condition |
| --- | --- | --- |
| Wave 0 — Program freeze and authority rebind | Select the global baseline, deployments/networks, lifecycle scope, decision target, reporting channel, severity authority, evidence templates, hypothesis/finding registries, flow inventory, handoff states, and matrix owner. Rebind `status.yaml`, `RH-D`, `F-`, `DV-`, component, parameter, blocker, and strict-xfail state to the candidate. Record the overall and first-wave resource envelope. | Shared operating decisions and authority freshness are recorded; the Section 0 decision packet shell exists; and the calibration charter passes Phase 0. |
| Wave 0.5 — Calibration before fan-out | Run only the bounded Batch 5 / `AUD-FLOW-01` exact-custody slice over `BasicVault.vy`, `SimpleErc20.vy`, direct Teller/Ledger/VaultBook dependencies, and exact-custody tests. Dependency-sensitive conclusions remain provisional. Measure source review, traceability, adversarial work, synthesis, handoff, challenge, and reporting throughput. | The pilot packet, limitations, known-defect carry-forward, retrospective, reviewer-day range, wall-clock range, and stop-loss data are accepted by the owner. The owner authorizes, resizes, narrows, or stops Wave 1. |
| Wave 1 — Delta-weighted foundation fan-out | Within the approved five-pod cap, run Batches 1–4 and continue Batch 5. Weight reviewer capacity first toward Batches 2, 5, and 3, which contain 84.0% of production-source churn, while preserving Batch 1 and 4 dependency ownership. Pre-charter Batch 6's changed Teller surface without allowing it to close before upstream handoffs. Within Batches 2–4, charter `AUD-FLOW-11` Price Resolution, `AUD-FLOW-12` Governance/Configuration, and `AUD-FLOW-13` CCIP where capacity permits. The deployment/integration lead begins `AUD-FLOW-14`/Batch 12 release-identity mapping. | Batches 1–4 publish stable permission, state/clock, pricing/admission, token/CCIP, governance-key, and dependency handoffs; Batch 5 either closes or records exact upstream blockers; `AUD-FLOW-11` through `AUD-FLOW-14` publish the versioned packets or handoffs needed by later flows. |
| Wave 2A — Primary user-flow fan-out | Respect the five-pod cap: finalize Batch 5 and activate Batches 6, 7, 10, and 11. Run Deposit/Withdrawal, Borrow/Repay, Migration/Stability Pool, Rewards/Bonds, and Governance/Configuration flow work as their charters and handoffs permit. Batch 12 mapping continues under the central lead. | Vault/migration, Teller, debt, reward, and governance models are stable; completed pods release capacity deliberately. |
| Wave 2B — Remaining economic and liquidation fan-out | As an active pod releases a slot, activate Batch 9. Activate Batch 8 architecture, source review, and test mapping in the next released slot. If program priorities require Batch 9 before Batch 11, record that decision without exceeding the cap. | Endaoment and preliminary liquidation/deleverage flow packets are reconciled; Batch 8 has stable pricing, vault, and debt closure dependencies identified. |
| Wave 3 — System and liquidation closure | Close Batch 8 after pricing, vault, and debt handoffs. Finalize Batch 12 and `AUD-FLOW-14`, then run aggregate access-control, governance-key, configured-exposure, value-conservation, debt, pricing, external-call, timing, availability, flow-composition, and network-parity campaigns. | All batch reports, flow packets, inherited dispositions, findings, and matrix deltas are reconciled against one final reviewed candidate. |
| Wave 4 — Remediation and independent retest | Implement approved non-overlapping fixes in parallel, serialize shared-source or deployment changes, and assign independent retesters. | Every finding and inherited issue has a final recorded disposition and affected program matrices/flow packets are updated. Any unresolved Critical/High item remains an explicit audit outcome and forces the activation packet to `NO-GO`. |

### 10.5 Coordination, finding identity, and isolation rules

- Use one isolated worktree and evidence area per batch, all pinned to the same
  program baseline unless the charter explicitly records a different target.
- Do not rebase active assessment pods onto moving protocol code. Record later
  changes for delta review against the frozen baseline.
- Keep one primary batch owner for every contract. A pod that discovers a
  concern in a supporting dependency opens a dependency handoff to the owning
  pod instead of independently finalizing a duplicate finding.
- Keep one primary owner and one canonical packet for every flow. A component
  manifestation discovered by multiple flow cells links to one root-cause
  hypothesis or finding rather than creating competing IDs.
- Maintain a program hypothesis registry before formal finding assignment. Each
  `AUD-HYP-###` record identifies reporting agent, affected source owner,
  affected flows, inherited identifiers, invariant, evidence state, and one of
  `draft`, `under review`, `confirmed`, `closed`, `duplicate`, or `superseded`.
  A confirmed new root cause receives one `AUD-###` finding; inherited issues
  retain their existing identifier and receive a linked current disposition.
- At the end of Phase 1, each pod publishes a versioned dependency snapshot:
  actors, state owners, invariants, assumptions, upstream requirements, and
  downstream consumers.
- Dependency handoffs use explicit `draft`, `stable`, `superseded`, and
  `accepted` states and bind the source commit/tree plus artifact version.
- During Phase 5, the consuming and owning pods jointly accept or reject
  dependency-sensitive integration rows; the flow owner joins when the row is
  part of a canonical transaction flow.
- Each pod submits versioned matrix deltas; only the program matrix owner edits
  the reconciled program-level matrices.
- Preserve raw commands, outputs, reproductions, failed attempts, assumptions,
  and unchecked areas in the approved evidence area. Agent summaries do not
  replace the underlying record.
- Critical/High candidates and other load-bearing conclusions selected by the
  audit lead require a fresh-context challenger to reproduce the claim from the
  frozen source and raw evidence before final severity or closure.
- Assessment remains separate from remediation. Any charter-authorized
  test-only proof work uses a batch-specific branch and may not silently change
  production source or the shared baseline.
- Remediation branches declare owned paths before implementation. Overlapping
  contract, fixture, migration, manifest, ABI, or configuration changes are
  serialized through one integration owner.
- Solidity wrapper or vendored-source changes require the Batch 4 owner and
  deployment/integration lead to agree on source provenance, compiler settings,
  build artifacts, verification inputs, and the corresponding migration/manifest
  delta before either batch can close.

The audit lead should review active-pod capacity at the end of every wave. The
review must include active flow cells, open handoffs, unresolved hypotheses,
matrix-owner backlog, and challenger/retest capacity. The objective is maximum
trustworthy throughput, not maximum simultaneous agent or reviewer count.

## 11. Recommended kickoff sequence

1. Approve this process, the comprehensive-versus-right-sized decision scope,
   and any batch/flow boundary changes.
2. Decide whether `02468586d710e2cce2360c2bc07e94de6ebdab29`
   is the first audit freeze or only this plan's refresh baseline. If `rh` has
   moved, produce exact source, test, authority, configuration, and deployment
   deltas before rebinding.
3. Rebind `status.yaml`, the `RH-D` register, inherited `F-`/`DV-` issues,
   component matrix, parameter ledger/invalidation triggers, blocker state, and
   strict-xfail register to the exact candidate. Preserve identifiers and
   historical rationales.
4. Select the deployed-network/configuration scope,
   active/admitted/candidate/legacy feature scope, decision date, evidence
   locations, private reporting boundary, and Section 0 decision owner.
5. Establish the program matrix owner, deployment/integration lead, severity
   owner, `AUD-` hypothesis/finding registries, handoff states, evidence
   templates, baseline-suite record, and overall resource/stop-loss envelope.
6. Run Wave 0.5 before foundation fan-out. Charter only the bounded
   Batch 5 / `AUD-FLOW-01` slice over `BasicVault.vy`, `SimpleErc20.vy`, direct
   Teller/Ledger/VaultBook dependencies, and exact-custody tests. Keep
   dependency-sensitive conclusions provisional.
7. Retrospect on the pilot's reviewer-days, wall clock, reconciliation backlog,
   challenged conclusions, handoff latency, artifact burden, and uncovered
   surface. Obtain the owner's explicit continue/resize/narrow/stop decision
   and Wave 1 budget.
8. Charter Batches 1–4 and the continuation of Batch 5. Charter
   `AUD-FLOW-11`, `AUD-FLOW-12`, `AUD-FLOW-13`, and early `AUD-FLOW-14` work
   only within the approved capacity. Pre-charter Batch 6's changed Teller
   surface for early mapping.
9. Inventory owned source, `master…rh` delta, generated/vendored dependencies,
   tests, strict xfails, migrations, manifests, authorities, prior security
   reports, deployed identities, configured/reachable exposure, and known
   lifecycle decisions for every starting pod and flow.
10. Launch Wave 1 only after each batch and flow charter passes Phase 0. Weight
    reviewer effort toward Batches 2, 5, and 3 while preserving Batches 1 and 4
    as foundation owners; begin Batch 12 identity mapping under the central lead.
11. Expand Batch 5 to StabilityPool, RipeGov, and VaultMigrator only after the
    Batch 1/2/4 handoffs stabilize, then start Waves 2A and 2B as slots become
    available. Do not wait for unrelated batches and do not exceed the approved
    resource or work-in-progress cap.
12. Begin any formal batch or flow's Phase 1 only after its scope-freeze gate is
    complete. Refresh the Section 0 decision packet at every wave exit and
    immediately after any Critical/High or authority-changing evidence.

## 12. Refreshed `rh` test-inventory observations

These are filename-, collection-, and fixture-level observations from `rh` at `02468586d710e2cce2360c2bc07e94de6ebdab29`, included only to prioritize Phase 3 work. They are not findings, do not prove that a behavior lacks indirect integration coverage, and do not turn focused refresh validation into a whole-suite result.

- The tree has 151 `test_*.py` modules. The default lane collected 3,550 selected tests with 282 deselections; the comprehensive collection selected 4,521 with 143 deselections.
- The default `--fork local` hook remains active even with `addopts` cleared. It
  deselects 102 of 404 price-source nodes and 40 of 326 Endaoment nodes; those
  142 Base/mainnet-fork nodes are absent from both ordinary CI lanes.
- Marker-only collection selects 131 `release`, four `fuzz`, and five `gas`
  nodes, but zero `artifact`, `fork_qualification`, or `serial` nodes. Artifact
  evidence is the explicit 50-node path gate, and H-09 fork evidence is the
  `tests/deployment/fork/**` path/environment gate.
- The suite carries 22 strict-xfail nodes from 13 sites. These name `DV-04`,
  `DV-05`, `DV-08`, `DV-09`, `DV-10`, `DV-13`, `DV-14`, `DV-15`, and the
  owner-deferred Uniswap manipulation item; they must be handled as inherited
  issue state in every affected charter and decision packet.
- `Boardroom.vy` still has no dedicated test module; the current test tree references it through shared deployment fixtures.
- `tests/registries/` still contains dedicated Address Registry and Ripe HQ modules but no dedicated Price Desk, Vault Book, or Switchboard module. Those contracts have integration and configuration consumers that must be mapped before judging coverage.
- `tests/modules/` contains LocalGov and TimeLock modules but no dedicated Addys or DeptBasics module.
- `RedStone.vy` still has no dedicated price-source test module. It is deployed through shared fixtures and must receive exact behavior-to-test mapping rather than a filename-only coverage judgment.
- Morpho V2, Uniswap V2, VaultMigrator, RipeGov migration, Stability Pool hardening, exact BasicVault custody, network profiles, current manifests, ABI/artifact identity, and fork qualification now have substantial dedicated suites. Their size is not proof that every permission, branch, invariant, external failure, or production composition is covered.
- The Solidity CCIP subtree has no Forge unit-test directory. Current evidence is primarily compilation plus Python migration, manifest-consumer, RipeHq, artifact, and documentation checks. Batch 4 must decide which inherited TokenPool/rate-limit/ownership behavior can rely on pinned upstream evidence and which Ripe composition paths require direct local tests.
- The Python workflow does not compile the Solidity subtree. Until a dedicated
  job exists, `forge build --root solidity` is a separately executed recorded
  gate and a green Python workflow is not CCIP compilation evidence.
- The default lane excludes the deployment, deployment-profile, and inventory directories and multiple evidence markers. A green lean result cannot close Batch 12 or any batch relying on release, artifact, fuzz, gas, or fork evidence.
- The simplification work removed the former block-clock inventory and probe packages. Retained clock evidence includes `tests/clock/test_clock_profiles.py`, deployment network-clock tests, and Ledger/Teller/composed-route tests; the audit must explicitly map what evidence was lost, retained, or replaced.
- Numeric historical step manifests were extracted from the active tree. Tests now center on current-manifest schemas, consumers, promotion, recovery metadata, and directory/source ownership; audit replay or historical-deployment claims may require byte-exact recovery from the recorded Git objects.
- Provenance tests use full Git history and committed fixtures. Fresh-clone and post-GC reproducibility must be demonstrated instead of assuming the owner's object database or remote-tracking refs exist elsewhere.

The first charter for each affected batch must convert these observations into exact function/branch/invariant traceability and distinguish genuinely missing coverage from adequate indirect or upstream coverage.

## 13. Decisions to make before the first audit batch

- Whether the owner is funding the comprehensive audit, the right-sized launch
  decision track, or a staged decision that begins narrow and expands only
  after the calibration gate.
- Whether the first target is the refreshed `rh` commit, a later release candidate, deployed Base or Robinhood bytecode/configuration, or an explicitly reconciled combination.
- Which of Base mainnet, Base Sepolia, Robinhood mainnet, Robinhood testnet, local simulation, and historical deployments are in scope.
- Which present source is active, admitted, deployed, parked, candidate-only, legacy-only, or intentionally disabled; these lifecycle labels affect threat modeling but not source ownership.
- Whether both Robinhood launch defaults and generated live-replacement defaults are in scope, and which live reads or human-edited inputs are authoritative for regeneration.
- Whether CCIP review includes only the Ripe wrappers and integration or also an independent review of the 18 vendored dependency files and upstream 1.5.1 equivalence.
- How extracted numeric manifests and removed test/probe infrastructure will be recovered and used when historical deployment or regression evidence depends on them.
- Whether prior external audits and known issues will be supplied at kickoff.
- Whether any unchanged `master` source may receive reduced review, exactly
  which evidence supports that reliance, and who accepts the unreviewed risk;
  repository history alone is not an audit.
- Whether each batch is reviewed by one reviewer plus independent retest, or by two reviewers from the start.
- Which initial flow inventory changes are approved, which pod owns each flow, and how many flow cells may be active without exceeding reconciliation capacity.
- The maximum reviewer-days, wall-clock period, compute/RPC spend, and stop-loss
  thresholds for calibration and every later wave.
- Where the program work-in-progress register, hypothesis/finding registry, versioned dependency handoffs, raw evidence, and canonical flow packets will live.
- Which conclusions require a fresh-context challenger beyond the mandatory Critical/High candidate rule, and who may serve in that role.
- Which Safe, signer, quorum, module, guard, guardian, key-rotation/recovery,
  and irreversible-handoff evidence the owner will supply without exposing
  secret key material.
- Where private findings and public-safe reports will live.
- Whether test-only proof work may be committed during assessment or only during remediation.
- Which Git-history, operating-system, compiler-cache, RPC, archive-node, and secret-handling controls are required for reproducible evidence.
- The final severity rubric and risk-acceptance authority.
- The required lean, comprehensive, release, artifact, fuzz, gas, fork, macOS, Solidity, whole-protocol, and invariant gates after batch remediation.

## 14. Refresh verification record

This document refresh used a detached, clean worktree at the exact baseline commit and private temporary caches. It made no change to `rh`, performed no RPC request, and did not execute a migration, deployment, configuration, activation, or release action.

Evidence reproduced during the refresh:

- Live `refs/heads/rh` and cached `origin/rh` both resolved to `02468586d710e2cce2360c2bc07e94de6ebdab29`; its tree was `082a460d0ee190ac74a87ab29828d9c867ddff06`.
- An exact source-ownership census assigned all 62 production Vyper files to Batches 1–11 once, with zero unassigned files and a total of 37,873 lines.
- The two owned Solidity wrappers, 18 vendored Solidity dependencies, 34 Vyper mocks, 151 test modules, 85 migrations, six current manifests, 54 ABIs, six interfaces, eight config files, and 48 non-ABI scripts were counted from the same tree.
- Default collection: `3,550/3,832` selected, 282 deselected, collection exit 0.
- Comprehensive collection with repository `addopts` cleared: `4,521/4,664` selected, 143 deselected, collection exit 0.
- Focused workflow, simplification-index, current-manifest consumer/promotion, schema, network-profile, and ABI-export validation: 204 passed.
- Focused contract-artifact and EIP-170 runtime-size validation: 50 passed.
- `forge build --root solidity`: 20 Solidity files compiled successfully with solc `0.8.26`; lint notes were emitted, but compilation succeeded.

Independent-review reconciliation reproduced the following additional
planning facts against the same source baseline:

- Exact-head GitHub Actions runs
  [31473039816](https://github.com/Ripe-Foundation/ripe-protocol/actions/runs/31473039816)
  (push) and
  [31473046484](https://github.com/Ripe-Foundation/ripe-protocol/actions/runs/31473046484)
  (pull request) completed successfully for `02468586…`. They establish only
  the configured Python workflow jobs, not marker-zero artifact/fork gates or
  Solidity compilation.
- Marker-only collection with `addopts` cleared: `release=131`, `fuzz=4`,
  `gas=5`, `artifact=0`, `fork_qualification=0`, and `serial=0`; zero-node
  marker selections exited 5.
- Explicit artifact/runtime-size paths collected 50 nodes. The H-09 path in
  disabled safe-default mode collected 177 of 178 nodes and deselected the one
  archive-required node.
- The default local-fork hook selected 302 of 404 price-source nodes and 286 of
  326 Endaoment nodes, confirming 142 fork-axis deselections beyond marker and
  path selection.
- Collection identified 22 strict-xfail nodes from 13 source sites.
- The production Vyper census contains 973 external functions, 582
  state-changing externals, 59 `@nonreentrant` externals, four `@payable`
  externals, 1,640 explicit `assert`/`raise` conditions, and 1,521 `if`/`elif`
  branches.
- `master…rh` is `0/462`; 25 production Vyper files differ with 4,626 lines of
  churn. Per-batch changed-file/churn counts in Section 6 were independently
  derived from the canonical ownership lists.
- `status.yaml`'s named program subject was 131 commits behind the planning
  baseline with 19 contract paths changed; the 403-row parameter ledger's
  named baseline was 212 commits behind with 41 contract paths changed. All
  403 parameter rows carry invalidation triggers, and 47 are status `blocked`.
- The current Python workflow contains no Solidity/Foundry build step.

These checks establish that the refreshed inventory and plan structure match the bound repository tree. They do not establish full-suite health, deployed-byte parity, live-chain correctness, absence of findings, or audit completion.
