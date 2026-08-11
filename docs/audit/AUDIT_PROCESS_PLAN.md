# Ripe Protocol Component Audit Process Plan

## Document status

- **Purpose:** define how Ripe Protocol will be reviewed component by component.
- **Planning baseline:** live `rh` / `origin/rh` at commit `02468586d710e2cce2360c2bc07e94de6ebdab29`, tree `082a460d0ee190ac74a87ab29828d9c867ddff06`.
- **Created:** 2026-07-28.
- **Refreshed:** 2026-08-11 from the live remote `refs/heads/rh`; the local `rh` worktree was 80 commits behind and was not used as the refresh source.
- **Process model amended:** 2026-08-11 to add transaction-flow cells, canonical permutation coverage, cross-agent evidence and finding controls, and capacity-safe sub-waves.
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

The repository's default pytest lane intentionally excludes deployment, deployment-profile, inventory, release, artifact, fuzz, gas, and fork-qualification classes. No batch may infer whole-scope coverage from the lean lane alone. The audit record must state which lane and markers ran, which paths were deselected or ignored, and whether global Boa state, Git-history dependencies, operating-system constraints, or network opt-ins affect reproducibility.

### 2.5 Keep conclusions reproducible

Every material conclusion should identify the reviewed commit, file/function or interaction, relevant test or reproduction, assumptions, impact, and confidence. Commands and test environments should be recorded without secrets.

### 2.6 Use documentation and prior work as inputs, not proof

Audit inputs should include:

- The exact source, compiler artifacts, deployment manifests, configuration, and onchain state in scope.
- The [technical documentation linked from the repository README](https://ripe-finance.gitbook.io/ripe-developers), captured with its URL and access date or as a versioned snapshot when possible.
- Intended-behavior specifications and architecture notes.
- Prior audit reports, known-issue lists, incident reports, remediations, and accepted-risk records supplied for the batch.
- Current `rh` source-authority documents and decision registers, read with their dates and lifecycle boundaries.
- `docs/simplification/REMOVED.md`, `docs/simplification/extracted-files.tsv`, and the associated validation evidence when an audit conclusion depends on extracted deployment history, removed test/probe infrastructure, or recovery claims.

Source and deployment evidence remain authoritative for what the system actually does. Documentation establishes intent and context; any divergence between documentation, tests, source, and deployed configuration must be logged rather than silently resolved. Private findings and sensitive operational material must stay in the approved private reporting channel.

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
- Required reviewers and completion criteria.

**Gate:** scope, baseline, and dependencies are agreed before detailed review begins.

### Phase 1 — Architecture and threat-model mapping

Document:

- Component purpose and assets at risk.
- Users, administrators, governance, keepers, integrations, and external protocols.
- Trust boundaries and privileged operations.
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

Static tools or compiler diagnostics may supplement manual review, but tool output is evidence to triage rather than a substitute for reasoning.

**Output:** annotated review notes and candidate findings with source references.

### Phase 3 — Existing test-suite assessment

Build a source-to-test traceability matrix covering:

- Each externally reachable function.
- Each privileged function.
- Each meaningful branch and revert condition.
- Each state transition and invariant.
- Each event relied upon by operators or integrations.
- Each external dependency and abnormal response.
- Each previously reported or remediated issue relevant to the component.

Assess:

- Whether the test actually reaches the intended branch.
- Whether assertions prove the important postconditions.
- Whether revert tests validate the correct reason and unchanged state.
- Whether fixtures or mocks hide production behavior.
- Whether tests are independent and deterministic.
- Whether coverage comes only indirectly through another component.
- Whether fork tests pin blocks and external dependencies reproducibly.
- Whether the lean, comprehensive, release, artifact, fuzz, gas, fork, macOS-only, and Solidity-build lanes collectively cover the claimed scope.
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

The current test topology has two automated Python lanes plus a dedicated macOS manifest-promotion job:

- The default lean lane applies `pytest.ini`, which excludes `tests/deployment`, `tests/deployment_profiles`, and `tests/inventory` and deselects `release`, `artifact`, `fuzz`, `gas`, and `fork_qualification` markers.
- The comprehensive lane clears repository `addopts`; on Linux it skips the APFS-bound manifest-promotion module, which runs separately on macOS.
- Fork qualification remains explicit and network-dependent. It must run only with a chartered provider, exact block/pin, chain identity, socket policy, and teardown/replay record.

Use the following tool classes, recording commands, configuration, version, limitations, and raw output:

- **Compilation evidence:** version-pinned Vyper compilation plus relevant `annotated_ast`, deployment/runtime control-flow graph, storage `layout`, `method_identifiers`, runtime source map, integrity hash, ABI, and bytecode outputs; and Foundry/solc compilation for the Ripe CCIP wrappers and vendored dependencies. Compiler artifacts support source review and deployment comparison; they are not security findings by themselves.
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

The table below uses physical source lines, including comments and blank lines, from the refreshed `rh` tree. Counts cover primary Ripe-owned production source only; imported dependencies, vendored Solidity, mocks, tests, deployment artifacts, remediation, reporting, and independent retest add effort. Sizes are relative planning aids, not calendar estimates. Each size combines source volume with integration breadth, accounting/economic density, adversarial surface, privilege, and expected cross-batch validation; it is not derived from line count alone.

| Batch | Primary Vyper | Owned Solidity | Raw primary lines | Size | Principal complexity flags |
| --- | ---: | ---: | ---: | --- | --- |
| 1 | 6 | 0 | 3,148 | L | Shared state, permissions, action-block identity, and invariants used by most downstream components |
| 2 | 13 | 0 | 10,600 | XL | Address initialization, four defaults variants, governance, and five configuration switchboards |
| 3 | 13 | 0 | 7,397 | XL | Heterogeneous active/candidate price sources, normalization, staleness, admission, and registry routing |
| 4 | 5 | 2 | 1,224 | XL | Token standards, privileged and cross-chain supply, signatures, shares, CCIP ownership/rate limits, and two languages |
| 5 | 9 | 0 | 4,171 | XL | Four vault families, exact custody, shares/rebases/losses, rewards, and unified position migration |
| 6 | 2 | 0 | 1,488 | L | Central asset entry point, typed custody observations, action-block checks, callbacks, and broad side effects |
| 7 | 2 | 0 | 1,690 | L | Debt, interest, zero-backing containment, Stock collateral, repayment, redemption, and oracle dependence |
| 8 | 3 | 0 | 2,854 | L | Auctions, Stock delivery, deleveraging, bad debt, incentives, and liveness |
| 9 | 3 | 0 | 2,255 | L | Reserve custody, privileged transfers, stabilizer, yield positions, and PSM economics |
| 10 | 3 | 0 | 2,082 | L | Rewards, send floors, claim/migration cleanup, bonds, cadence, budgets, and multi-user fairness |
| 11 | 3 | 0 | 1,081 | M | Governance execution, contributor templates, compensation, and authority |
| 12 | 0 | 0 | Not comparable | XL | 151 enumerated release-identity files plus config, operational scripts, Solidity build inputs, CI, provenance, and network-specific deployment state |

The 62 primary non-mock Vyper files total 37,873 raw lines, and the two Ripe-owned Solidity wrappers add 117 lines. Batch 4 must also review the 18-file, 1,792-line vendored Chainlink/OpenZeppelin subtree as a pinned dependency, without misclassifying it as Ripe-owned source. Batch 12's 151 enumerated release-identity files are 85 migrations, six retained current manifests, 54 exported ABIs, and six Vyper interfaces; its scope also includes eight top-level config files, 48 non-ABI scripts, one Python CI workflow, Solidity build configuration, and relevant provenance fixtures/documents.

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

**Primary outcome**

Evidence that the audited contracts and configuration are the exact contracts and configuration that deployment tooling intends to install and operate on each declared network, without confusing repository readiness with executed deployment or activation.

## 7. Cross-cutting review campaigns

Some risks cannot be closed inside one component batch or transaction flow. At program kickoff, assign one **program matrix owner**, normally the audit lead, and record that person in the audit index. Every batch charter must also name a **batch matrix steward**, normally one of that batch's reviewers, and every flow charter must name a **flow matrix steward**, normally the flow owner.

The stewards seed relevant rows during Phase 1, update them as evidence develops, validate integration rows during Phase 5, and submit versioned deltas at the relevant Phase 6 or flow-closure gate. The program owner reconciles the shared matrices after every batch and flow closure, resolves duplicates or conflicting classifications with the reviewers, and signs the final reconciliation in Section 9. Phase 7 retests must update affected rows and flow packets rather than leaving the pre-fix state in place.

Maintain cross-batch matrices for:

### Access control and governance

Map every privileged function to its allowed caller, how that caller is assigned, how authority changes, timelock/emergency constraints, and tests.

### Asset and accounting conservation

Trace actual custody, internal balances, shares, Green/Ripe supply, debt, rewards, reserves, and liquidation proceeds across component boundaries.

Require observed token balance deltas wherever nominal transfer amounts can diverge because of fees, blacklists, rebases, callbacks, deficient backing, or bridge behavior.

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

Use a consistent severity model, refined during audit kickoff:

- **Critical:** credible loss of most or all at-risk funds, unrestricted minting, systemic insolvency, or protocol-wide takeover.
- **High:** substantial loss, bad debt, permanent freezing, or major privilege compromise under realistic conditions.
- **Medium:** bounded loss, significant accounting/availability failure, or serious violation requiring meaningful preconditions.
- **Low:** limited-impact correctness or security weakness with constrained exploitability.
- **Informational:** hardening, clarity, maintainability, observability, or test-quality concern without a demonstrated security impact.

Severity should account for impact, likelihood, required privilege, capital, timing, detectability, recoverability, and blast radius. Confidence should be reported separately.

Allowed dispositions:

- Open.
- Fix planned.
- Fixed pending retest.
- Fixed and verified.
- Partially fixed.
- Risk accepted.
- Not applicable.
- Duplicate.
- Disputed, with both rationales preserved.

## 9. Program-level completion

After all batches:

1. Reconcile cross-batch and cross-flow findings, duplicate root causes, linked manifestations, and preserved disagreements.
2. Run the lean, comprehensive, release, artifact, fuzz, gas, fork-qualification, macOS-only, Solidity-build, and protocol-wide invariant/integration gates applicable to the final candidate; record every exclusion.
3. Have the program matrix owner reconcile and sign off the aggregate permission, asset-flow, debt, price, and deployment matrices plus every canonical flow packet.
4. Reproduce generated defaults, ABIs, compiler artifacts, artifact-expectation records, current manifests, and deployed runtime identities from their declared authorities.
5. Reconcile Base mainnet/Sepolia and Robinhood mainnet/testnet configuration, CCIP lane symmetry, active/admitted feature state, and intentional differences.
6. Confirm every accepted risk has an owner and explicit rationale.
7. Confirm every remediation is tied to a regression test and independent retest.
8. Produce a final report that separates:
   - reviewed source and deployment scope;
   - fixed findings;
   - unresolved findings;
   - accepted residual risks;
   - test limitations;
   - unaudited or changed code.
9. Establish a delta-review policy for changes made after the final reviewed commit.

The protocol audit is complete only for the exact reviewed source, configuration, and deployment scope. Later changes require impact triage and, where material, a targeted re-audit.

## 10. Parallel execution model

The program should maximize concurrent evidence gathering without allowing
dependent batches to reach incompatible conclusions. A batch may start before
all upstream batches finish, but it may not close a dependency-sensitive phase
until the relevant upstream model, invariant, and finding handoffs are stable.

The default initial capacity is **five active component pods**, plus one program
matrix owner and one deployment/integration lead. Transaction-flow cells are an
explicit second execution dimension, not uncounted work: every active flow cell
must have a home pod, named participating-pod liaisons, and an entry in the
program work-in-progress register. The initial Deposit flow cell is part of the
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
| F01 | Deposit and exact custody | 6, with the bounded Batch 5 pilot first | 1–6, 10, 12 |
| F02 | Withdrawal, actual receipt, and accounting cleanup | 6 | 1–7, 10, 12 |
| F03 | Borrow and GREEN delivery | 7 | 1–7, 10, 12 |
| F04 | Repayment and redemption | 7 | 1–4, 7, 12 |
| F05 | Liquidation, auction, settlement, and bad-debt reconciliation | 8 | 1, 3–8, 10, 12 |
| F06 | Deleverage and residual account health | 8 | 1, 3–8, 12 |
| F07 | BasicVault and RipeGov position migration | 5 | 1, 2, 4–6, 10, 12 |
| F08 | Stability Pool deposit, claim, and liquidation absorption | 5 | 1, 3–5, 8, 10 |
| F09 | Reward accrual, claim, cleanup, bond creation, vesting, and redemption | 10 | 1, 2, 4–7, 10, 12 |
| F10 | Endaoment reserve movement and PSM mint/redeem | 9 | 1–4, 7, 9, 12 |
| F11 | Price resolution, source failure, and asset/source admission | 3 | 2, 3, 5–9, 12 |
| F12 | Governance, timelock, department, and configuration mutation | 2 or 11, selected in the charter | 1–3, 11, 12 |
| F13 | CCIP burn, message, remote validation, mint, and aggregate supply | 4 | 2, 4, 12 |
| F14 | Deployment, migration, manifest, permission, and runtime-identity transition | 12 | 2–5, 12 |

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
| Wave 0 — Program freeze | Select the global baseline, deployments/networks, lifecycle scope, reporting channel, severity authority, evidence templates, hypothesis/finding registries, flow inventory, handoff states, and matrix owner. Draft starting batch and flow charters in parallel. | Shared operating decisions are recorded and every starting pod and flow passes Phase 0. |
| Wave 1 — Foundation and pilot fan-out | Run Batches 1–4 concurrently. Within Batches 2–4, charter F11 Price Resolution, F12 Governance/Configuration, and F13 CCIP as named flow work where capacity permits. Use the fifth pod slot for the bounded Batch 5 F01 Deposit flow calibration slice. The deployment/integration lead begins F14/Batch 12 provenance, deployment-order, four-network, generated-defaults, and manifest mapping. | Batches 1–4 publish stable permission, state/clock, pricing/admission, token/CCIP, and dependency handoffs. F01 publishes a completed pilot packet and retrospective; F11–F14 publish the versioned packets or handoffs required for later flows. Measured reconciliation throughput sets later pod and flow-cell caps. |
| Wave 2A — Primary user-flow fan-out | Respect the five-pod cap: finalize Batch 5 and activate Batches 6, 7, 10, and 11. Run Deposit/Withdrawal, Borrow/Repay, Migration/Stability Pool, Rewards/Bonds, and Governance/Configuration flow work as their charters and handoffs permit. Batch 12 mapping continues under the central lead. | Vault/migration, Teller, debt, reward, and governance models are stable; completed pods release capacity deliberately. |
| Wave 2B — Remaining economic and liquidation fan-out | As an active pod releases a slot, activate Batch 9. Activate Batch 8 architecture, source review, and test mapping in the next released slot. If program priorities require Batch 9 before Batch 11, record that decision without exceeding the cap. | Endaoment and preliminary liquidation/deleverage flow packets are reconciled; Batch 8 has stable pricing, vault, and debt closure dependencies identified. |
| Wave 3 — System and liquidation closure | Close Batch 8 after pricing, vault, and debt handoffs. Finalize Batch 12 and F14, then run aggregate access-control, value-conservation, debt, pricing, external-call, timing, availability, flow-composition, and network-parity campaigns. | All batch reports, flow packets, findings, and matrix deltas are reconciled against one final reviewed candidate. |
| Wave 4 — Remediation and independent retest | Implement approved non-overlapping fixes in parallel, serialize shared-source or deployment changes, and assign independent retesters. | Every finding has a verified, partial, accepted, disputed, or open disposition and affected program matrices are updated. |

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
  record identifies reporting agent, affected source owner, affected flows,
  invariant, evidence state, and one of `draft`, `under review`, `confirmed`,
  `closed`, `duplicate`, or `superseded`.
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

1. Approve this process and adjust the batch boundaries.
2. Decide whether `02468586d710e2cce2360c2bc07e94de6ebdab29` is the first audit freeze or only this plan's refresh baseline. If `rh` has moved, produce an exact delta inventory before rebinding.
3. Select the exact deployed-network/configuration scope, active/admitted/candidate/legacy feature scope, evidence locations, and private reporting boundary.
4. Establish the program matrix owner, deployment/integration lead, severity owner, hypothesis/finding registries, handoff states, evidence templates, and initial pod/flow-cell capacity.
5. Charter Batches 1–4 and F01. Also charter F11, F12, F13, and the early F14 mapping work inside their home pods or central lead when the recorded flow-cell cap permits. Use a bounded Batch 5 calibration slice—`BasicVault.vy`, `SimpleErc20.vy`, their direct Teller/Ledger/VaultBook dependencies, and the exact-custody tests—as F01's first flow packet. It is a representative asset-moving surface without pretending the entire 4,171-line vault/migration batch can close before upstream models exist.
6. Inventory the owned source, generated/vendored dependencies, tests, migrations, manifests, prior security reports, deployed identities, and known lifecycle decisions for every starting pod and the flow pilot.
7. Launch Wave 1 only after those batch and flow charters pass Phase 0: run Batches 1–4 in parallel, use the fifth pod slot for the F01/Batch 5 pilot, and begin early Batch 12 provenance/configuration mapping under the deployment/integration lead.
8. Allow F01 to map and test supporting Teller, Ledger, VaultBook, token, and reward behavior immediately, but keep source-sensitive conclusions provisional until their owning pods publish stable handoffs. Complete Batches 1–4 before formally closing Batch 5.
9. Retrospect on the completed pilot packet, reconciliation backlog, challenged conclusions, and handoff latency. Update this operating plan if needed, convert T-shirt sizes into reviewer-day ranges, and set the Wave 2 pod and flow-cell caps from measured throughput.
10. Expand Batch 5 to StabilityPool, RipeGov, and VaultMigrator after the Batch 1/2/4 handoffs stabilize, then start Wave 2A and 2B as slots become available. Do not wait for unrelated batches to close, and do not exceed the recorded cap.
11. Begin any formal batch or flow's Phase 1 only after its scope-freeze gate is complete.

## 12. Refreshed `rh` test-inventory observations

These are filename-, collection-, and fixture-level observations from `rh` at `02468586d710e2cce2360c2bc07e94de6ebdab29`, included only to prioritize Phase 3 work. They are not findings, do not prove that a behavior lacks indirect integration coverage, and do not turn focused refresh validation into a whole-suite result.

- The tree has 151 `test_*.py` modules. The default lane collected 3,550 selected tests with 282 deselections; the comprehensive collection selected 4,521 with 143 deselections.
- `Boardroom.vy` still has no dedicated test module; the current test tree references it through shared deployment fixtures.
- `tests/registries/` still contains dedicated Address Registry and Ripe HQ modules but no dedicated Price Desk, Vault Book, or Switchboard module. Those contracts have integration and configuration consumers that must be mapped before judging coverage.
- `tests/modules/` contains LocalGov and TimeLock modules but no dedicated Addys or DeptBasics module.
- `RedStone.vy` still has no dedicated price-source test module. It is deployed through shared fixtures and must receive exact behavior-to-test mapping rather than a filename-only coverage judgment.
- Morpho V2, Uniswap V2, VaultMigrator, RipeGov migration, Stability Pool hardening, exact BasicVault custody, network profiles, current manifests, ABI/artifact identity, and fork qualification now have substantial dedicated suites. Their size is not proof that every permission, branch, invariant, external failure, or production composition is covered.
- The Solidity CCIP subtree has no Forge unit-test directory. Current evidence is primarily compilation plus Python migration, manifest-consumer, RipeHq, artifact, and documentation checks. Batch 4 must decide which inherited TokenPool/rate-limit/ownership behavior can rely on pinned upstream evidence and which Ripe composition paths require direct local tests.
- The default lane excludes the deployment, deployment-profile, and inventory directories and multiple evidence markers. A green lean result cannot close Batch 12 or any batch relying on release, artifact, fuzz, gas, or fork evidence.
- The simplification work removed the former block-clock inventory and probe packages. Retained clock evidence includes `tests/clock/test_clock_profiles.py`, deployment network-clock tests, and Ledger/Teller/composed-route tests; the audit must explicitly map what evidence was lost, retained, or replaced.
- Numeric historical step manifests were extracted from the active tree. Tests now center on current-manifest schemas, consumers, promotion, recovery metadata, and directory/source ownership; audit replay or historical-deployment claims may require byte-exact recovery from the recorded Git objects.
- Provenance tests use full Git history and committed fixtures. Fresh-clone and post-GC reproducibility must be demonstrated instead of assuming the owner's object database or remote-tracking refs exist elsewhere.

The first charter for each affected batch must convert these observations into exact function/branch/invariant traceability and distinguish genuinely missing coverage from adequate indirect or upstream coverage.

## 13. Decisions to make before the first audit batch

- Whether the first target is the refreshed `rh` commit, a later release candidate, deployed Base or Robinhood bytecode/configuration, or an explicitly reconciled combination.
- Which of Base mainnet, Base Sepolia, Robinhood mainnet, Robinhood testnet, local simulation, and historical deployments are in scope.
- Which present source is active, admitted, deployed, parked, candidate-only, legacy-only, or intentionally disabled; these lifecycle labels affect threat modeling but not source ownership.
- Whether both Robinhood launch defaults and generated live-replacement defaults are in scope, and which live reads or human-edited inputs are authoritative for regeneration.
- Whether CCIP review includes only the Ripe wrappers and integration or also an independent review of the 18 vendored dependency files and upstream 1.5.1 equivalence.
- How extracted numeric manifests and removed test/probe infrastructure will be recovered and used when historical deployment or regression evidence depends on them.
- Whether prior external audits and known issues will be supplied at kickoff.
- Whether each batch is reviewed by one reviewer plus independent retest, or by two reviewers from the start.
- Which initial flow inventory changes are approved, which pod owns each flow, and how many flow cells may be active without exceeding reconciliation capacity.
- Where the program work-in-progress register, hypothesis/finding registry, versioned dependency handoffs, raw evidence, and canonical flow packets will live.
- Which conclusions require a fresh-context challenger beyond the mandatory Critical/High candidate rule, and who may serve in that role.
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

These checks establish that the refreshed inventory and plan structure match the bound repository tree. They do not establish full-suite health, deployed-byte parity, live-chain correctness, absence of findings, or audit completion.
