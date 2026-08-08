# Track 7: Robinhood Deployment-Support Specification

> **1 August 2026 currentness overlay:** The specification below is historical
> planning authority. The current candidate is based on
> `5f5d22b7ee78cbb904c4fe3c6e46599c330c4353`, tree
> `7454b5456ebb6cd02d716a64b408629ab501629e`, and selects unchanged
> CurvePrices at ID 2 for GREEN only. Current `rh` integrates H-04 schema v2, H-05 deterministic
> blocked planning, M4 proof, H-06 candidate-class qualification, and corrected
> PR #61. Required identity bindings, Curve launch inputs, Defaults rendering, four Deleverage
> machine-parameter rows, final operator binding, rehearsal, and release
> preparation remain. No live action or migration history exists; actual
> deployment remains outside the pause process.

**Status:** Draft for owner review; specification-only

**Prepared:** 23 July 2026

**Planning baseline:** `758f45f5455fd7c05b25533d2d748769bcfc49c2`

## Fresh-agent instruction

Treat this document as the task contract. Produce an implementation-ready specification and validation plan for adding Robinhood mainnet and approved test-environment support to the existing Ripe deployment, migration, verification, ABI, manifest, and release-evidence tooling.

This track is specification-only. Do not modify production contracts, defaults, `BluePrint.py`, scripts, migrations, manifests, ABI exports, tests, dependencies, CI, or `docs/chains/rh-summary.md`. Do not deploy a contract, sign or broadcast a transaction, select production accounts, or turn a recommendation into owner approval.

Use branch `rh-track-7-deployment-support`. Commit only the approved specification deliverables to that branch with clear messages. Never push directly to or merge into `rh` or `master`; the owner reviews and integrates the work.

## Worktree bootstrap

The owner must first commit this approved brief to `rh`. The fresh agent is responsible for creating its own worktree:

1. Start from `/Users/wigglez/dev/ripe-protocol`.
2. Verify that the integration worktree is clean, `rh` resolves to the approved integration commit, and this brief exists in that commit.
3. Verify that the reviewed Track 1 through Track 6 planning and evidence artifacts listed below exist in the integration commit.
4. Record:
   - the full starting commit;
   - the content hashes of `docs/chains/rh-summary.md`, `docs/chains/rh/component-matrix.md`, `docs/chains/rh/shared-block-clock-specification.md`, and `docs/chains/rh/block-clock-validation-plan.md`; and
   - the latest migration and manifest IDs present at kickoff.
5. Confirm that branch `rh-track-7-deployment-support` and path `/Users/wigglez/dev/ripe-protocol-track-7-deployment-support` do not already exist. If either exists, stop and ask the owner; do not reuse, delete, reset, or overwrite it.
6. Create the isolated worktree:

   ```bash
   git -C /Users/wigglez/dev/ripe-protocol worktree add \
     -b rh-track-7-deployment-support \
     /Users/wigglez/dev/ripe-protocol-track-7-deployment-support \
     rh
   ```

7. Verify the new worktree's branch, commit, clean status, and recorded hashes.
8. Run every subsequent command and make every edit inside `/Users/wigglez/dev/ripe-protocol-track-7-deployment-support`.

Do not modify or commit from the integration worktree. Leave the Track 7 branch and worktree in place for owner review; do not remove or merge them yourself.

## Launch-input rule

This specification may run in parallel with Track 6 S1 and S2 implementation. It must consume their approved briefs and record their eventual artifacts as pending inputs; it must not assume that their code exists or invent their validation results.

Before kickoff, the integration baseline must contain reviewed artifacts for:

- Track 1: CCIP public evidence, question packet, and integration-decision record;
- Track 2: Stock Token transferability probe and evidence;
- Track 3: component matrix and block-number inventory;
- Track 4: USDG public evidence and PSM decision;
- Track 5: vault comparison, decision, and fix recommendations; and
- Track 6: shared block-clock specification and validation plan.

If one of those files is absent, stop. If an artifact exists but retains an external, owner, security, or implementation gate, record it as `pending` with its exact owner and consequence. Do not treat an unanswered Chainlink question, unexecuted live Stock Token probe, pending vault remediation, disabled PSM, or unimplemented S1/S2 slice as a reason to guess.

Track 7 must be reconciliation-friendly: if a parallel input lands during drafting, record the input commit and update the affected row without absorbing unrelated implementation work.

## Objective

Produce:

1. `docs/chains/rh/robinhood-deployment-support-specification.md`; and
2. `docs/chains/rh/robinhood-deployment-validation-plan.md`.

Together, the documents must:

- audit the existing deployment system from CLI selection through committed manifest evidence;
- define a chain-neutral network/configuration abstraction that supports Robinhood without inheriting Base, Alchemy, Basescan, or Etherscan assumptions;
- define the exact selected deployment inventory and dependency graph using the component-matrix IDs;
- separate canonical source, chain defaults, external addresses, migration sequencing, and live-bytecode policy;
- reserve non-colliding Robinhood migration namespaces and IDs for the initial deployment and Track 6 slices S3–S10;
- specify manifest, verification, ABI, release-evidence, retry, abort, and role-transfer behavior;
- make every omitted or disabled integration explicit and fail closed;
- define clean-deployment, post-deployment, regression, and negative validation;
- split implementation into narrow follow-on PRs with file ownership and owner gates; and
- map every Section 1 checklist item to a concrete implementation artifact and test.

The output must let future implementation agents edit the deployment system without rediscovering its current assumptions or making product, security, address, governance, or release decisions themselves.

## Controlling constraints

- Follow [`../rh-summary.md`](../rh-summary.md), especially Sections 0, 1, 7, 8, the launch gates, and the non-goals.
- Preserve one canonical production-contract source and release line for Base and Robinhood.
- Do not create a Robinhood contract branch, duplicated core suite, or `chain.id` behavior branch.
- `DefaultsRobinhood` is the intended chain-specific defaults artifact; it supplies values and inventory, not divergent protocol logic.
- Keep chain identity, RPCs, explorers, gas/confirmation policy, external addresses, defaults, migration paths, and release evidence explicit.
- Never silently substitute a Base address, zero address, local mock, or placeholder for an omitted or unknown Robinhood dependency.
- Separate `omitted`, `deployed disabled`, `deferred`, and `blocked pending decision`; they have different authority and validation surfaces.
- Re-verify all time-sensitive network metadata and external addresses from current primary sources at implementation or release freeze. Do not copy research-snapshot addresses into production configuration.
- Never commit RPC credentials, private keys, API keys, hardware-wallet data, Safe signatures, or other secrets.
- An incomplete external answer may reserve a configuration/migration slot, but it may not invent a contract release, router, selector, registry, pool address, feed, token address, role, or permission.
- Recommendations are not approvals. Preserve owner/security/risk/operations decisions as explicit gates.

The controlling Hightop Notes source is:

`/Users/wigglez/dev/hightop-notes/random/hood/hood-chain-executive-summary.md`

If the local checkout is unavailable, use the [GitHub copy](https://github.com/mickhagen/hightop-notes/blob/main/random/hood/hood-chain-executive-summary.md). If neither source is accessible, stop rather than silently skipping the selected architecture. Do not import the superseded federated design from `random/hood/hood-chain.md`.

## Required repository reading

Read and verify the current integrated versions of:

### Program and track artifacts

- `docs/chains/rh-summary.md`
- `docs/chains/rh/component-matrix.md`
- `docs/chains/rh/block-number-inventory.md`
- `docs/chains/rh/shared-block-clock-specification.md`
- `docs/chains/rh/block-clock-validation-plan.md`
- `docs/chains/rh/ccip-public-evidence.md`
- `docs/chains/rh/ccip-chainlink-question-packet.md`
- `docs/chains/rh/ccip-integration-decision.md`
- `docs/chains/rh/stock-token-transferability-evidence.md`
- `docs/chains/rh/usdg-public-evidence.md`
- `docs/chains/rh/usdg-psm-decision.md`
- `docs/chains/rh/stock-token-vault-comparison.md`
- `docs/chains/rh/stock-token-vault-decision.md`
- `docs/chains/rh/stock-token-vault-fix-recommendations.md`
- every committed `track-*.md` brief under `docs/chains/rh/`; and
- the approved Track 6 S1 and S2 briefs, whether or not their implementations have merged.

### Deployment and configuration code

- `config/BluePrint.py`
- `scripts/migrate.py`
- `scripts/verify.py`
- `scripts/export_abis.py`
- `scripts/console.py`
- `scripts/utils/migration.py`
- `scripts/utils/migration_runner.py`
- `scripts/utils/migration_helpers.py`
- `scripts/utils/deploy_args.py`
- `scripts/utils/verify_etherscan.py`
- `scripts/utils/json_file.py`
- `scripts/utils/log.py`
- `scripts/utils/mock_account.py`
- `scripts/utils/safe_account.py`
- `scripts/utils/ledger_account.py`
- all current `migrations/base-mainnet/*.py`
- all current `migration_history/base-mainnet/v1/*-manifest.json`
- all current `scripts/abis/*.json`
- `scripts/params/regenerate_defaults.py`
- `scripts/params/run_all.py`
- the remaining parameter-generation scripts and generated reports;
- `requirements.txt`
- `.gitignore`
- `README.md`; and
- repository test/config files that determine import paths, markers, and runtime setup.

Use repository search to find every network name, chain ID, RPC constructor, explorer URL/key, `migration_history` path, manifest reader/writer, verification provider, account backend, confirmation assumption, and environment-variable read. Do not rely only on the CLI entrypoint.

Inventory whether deployment tooling currently has tests. If no deployment-tooling test suite exists, say so and specify the future test files instead of claiming coverage.

## Phase A: Audit the existing deployment system

Create a code-grounded current-state map before recommending changes.

### CLI and network selection

- [ ] Trace every network choice exposed by `scripts/migrate.py`, `scripts/verify.py`, and `scripts/console.py`.
- [ ] Identify duplicated network choices, defaults, aliases, help-text mismatches, and unsupported custom values.
- [ ] Trace how `--chain`, environment, fork, RPC override, blueprint, version, and migration ID reach runtime behavior.
- [ ] Record every environment variable read, when it is read, whether absence breaks unrelated commands, and whether its value can appear in logs or manifests.
- [ ] Trace current Alchemy URL construction and identify where a fully supplied RPC URL must bypass it.
- [ ] Trace current Basescan/Etherscan selection and assumptions.

### Migration execution

- [ ] Trace discovery, sorting, ID parsing, class loading, blueprint injection, account selection, prompt/confirmation behavior, and migration execution.
- [ ] Trace how migrations record deployments, constructor arguments, metadata, intermediate manifests, and `current-manifest.json`.
- [ ] Determine idempotency, rerun, skip, resume, partial-failure, and duplicate-ID behavior.
- [ ] Determine whether a migration can detect that onchain state differs from its prior manifest.
- [ ] Trace local, fork, Safe, Ledger, and private-key/account behavior without accessing secrets.
- [ ] Identify every place Base-specific data or naming leaks into generic runtime logic.

### Verification, ABIs, and manifests

- [ ] Trace contract verification from manifest record through provider request and explorer link.
- [ ] Record supported languages/artifacts and the current Vyper-only/Solidity boundary.
- [ ] Trace constructor argument encoding, blueprints/proxies/modules, compiler metadata, and source paths.
- [ ] Trace ABI export selection, naming, collision handling, and generated-file review.
- [ ] Describe the committed `migration_history/base-mainnet/v1/` convention as it exists, including missing or skipped migration manifests.
- [ ] Identify stale comments, path names, or provider terminology that could mislead a Robinhood operator.

For every finding, record exact file/function/line or stable source reference from the starting commit. Separate a defect from a design limitation and a Robinhood-specific blocker.

### Dependency-security preflight

- [ ] Record a dated snapshot of current dependency-security alerts and map each affected package to deployment, verification, RPC, testing, or unrelated runtime use.
- [ ] Treat the 13 alerts reported by GitHub during the 23 July 2026 `rh` push as dated evidence, not a stable count; re-query the authoritative alert set at implementation kickoff.
- [ ] Re-check the reported `requests` and `urllib3` findings specifically because migration and verification tooling uses the Python network stack to communicate with RPC and explorer services.
- [ ] Recommend the smallest reviewed pin-refresh plan that clears relevant high/moderate findings before deployment rehearsal without silently changing compiler, transaction, or test behavior.
- [ ] Record transitive constraints, release notes, behavior changes, rollback, full-suite requirements, and the owner/security approval needed before editing pins.
- [ ] Coordinate with Track 6 S1: if a refresh changes `titanoboa==0.2.7` or `pytest==8.4.2`, S1's exact-version gate must fail until a reviewed update approves the new pins and re-proves independent NUMBER/timestamp control, repeated values, jumps, and anchor restoration.

Track 7 specifies this work but does not change a dependency. No deployment rehearsal or signing workflow may rely on an untriaged relevant high/moderate alert set.

## Phase B: Specify the network/configuration abstraction

Define the smallest shared abstraction that supports current Base behavior and Robinhood without chain-specific protocol logic.

### Required network-profile fields

Specify a reviewed schema with at least:

- canonical network identifier;
- display name;
- chain ID;
- environment (`local`, test environment, mainnet);
- default public RPC source or `none`;
- required user-supplied RPC environment variable;
- explorer browser base URL;
- verification API URL and provider/protocol type;
- verification API-key environment variable or explicit keyless mode;
- native gas token metadata needed by tooling;
- EIP-1559/legacy fee strategy;
- confirmation count;
- reorg/finality policy;
- read timeout and retry policy;
- fork-mode behavior;
- migration directory;
- migration-history directory;
- blueprint/defaults identifier; and
- enabled account backends.

Keep secrets as environment references, never values. Prefer an explicit user-supplied RPC URL over constructing a vendor URL. Adding Robinhood must not require an Alchemy account or a Basescan key.

### Network fact verification

For Robinhood mainnet and the intended test environment:

- [ ] Verify current chain IDs and official names from primary sources.
- [ ] Verify official RPC endpoints or document that operators must supply one.
- [ ] Verify explorer browser and API behavior.
- [ ] Verify whether source verification uses Etherscan-compatible, Blockscout-compatible, Sourcify, custom, or unsupported APIs.
- [ ] Verify fee-market behavior exposed to ordinary EVM clients.
- [ ] Verify documented or owner-selected confirmation/finality posture.
- [ ] Record retrieval date and source URL for every time-sensitive fact.

Do not browse arbitrary third-party chain lists when an official source exists. If an official Robinhood testnet no longer exists, has restricted access, or is not adequate for the required lifecycle and CCIP work, record the fact and specify owner-approved alternatives. Do not invent a testnet, chain ID, or production-like guarantee.

Any read-only RPC sampling must be reproducible, sanitized, and clearly labeled empirical rather than authoritative. Committing raw evidence requires owner approval if it is large, provider-specific, or could expose operational metadata.

## Early owner-review checkpoint

After completing Phase A and the proposed Phase B network-profile schema, the agent may pause and offer an early checkpoint before expanding the deployment graph and validation plan. Present the current audit findings, network-profile table, primary-source record, unresolved facts, and any abstraction decision that would materially shape Phases C–H in the working draft of Deliverable A.

This checkpoint is intended to reduce late review churn; it is not a third deliverable, completion of Track 7, approval of production values, or permission to implement deployment support. Do not merge a partial specification unless the owner explicitly requests it. If the owner elects not to review the checkpoint, continue with the remaining specification while keeping every unresolved field explicit.

## Phase C: Define the deployment inventory and graph

Use stable `CM-*` IDs from the integrated component matrix. Produce one row per selected, omitted, disabled, deferred, or blocked component.

Each row must include:

- component ID and name;
- disposition;
- canonical source and artifact;
- deployment form (contract, module, external address, configuration only);
- constructor arguments and their source;
- dependencies and deployment order;
- migration ID reservation;
- registry name/ID and registration sequence;
- RipeHq Department/capability requirements;
- governance/admin/guardian/operations roles;
- external permissions;
- defaults and parameter source;
- post-deployment assertions;
- omission or disabled-path assertions;
- live Base bytecode policy;
- rollback/abort boundary; and
- owner and approval status.

### Required deployment postures

- `DefaultsRobinhood` is separate from `DefaultsBase` but contains values and inventory only.
- Underscore vault detection, hooks, reward transfers, registry dependencies, and bypasses are omitted or fail closed.
- Base-only Endaoment treasury/partner routes are separate from the conditionally in-scope `EndaomentPSM`.
- The PSM is either omitted or deployed disabled, with `canMint == false`, `canRedeem == false`, no GREEN mint capability, and resolved `shouldAutoDeposit == false`, until all Track 4 activation gates pass.
- Stock Token collateral cannot be enabled until the selected vault path and Track 5-required shared fixes/owner acceptance are complete.
- `CreditRedeem` remains disabled for Stock Tokens.
- `shouldSwapInStabPools` remains false unless governance explicitly accepts Stability Pool custody of issuer-controlled Stock Tokens.
- SavingsGreen/sGREEN and the resulting Stability Pool/insurance/rewards graph remain a named owner decision; do not assume deployment.
- GREEN- and RIPE-market-price-dependent features remain disabled until their separate adapter specification and enablement gates pass.
- Unsupported Curve, Aerodrome, Pyth, Stork, RedStone, Underscore-yield, wrapped-yield, and other Base-only integrations are omitted or unregistered as approved, not populated with zeros.
- CCIP pool/router/registry fields remain `pending Track 1 / Chainlink` where facts are unanswered. Reserve the integration surface without fabricating a supported release, address, interface, or permission.

Trace the direct-mint-caller rule: the configured token pool itself must be the RipeHq-authorized caller if it invokes GREEN/RIPE minting. A standalone adapter cannot satisfy a `msg.sender` capability check on behalf of a different pool.

## Phase D: Reserve migration namespaces and IDs

Define, without creating migration files:

- `migrations/robinhood-testnet/`;
- `migrations/robinhood-mainnet/`;
- `migration_history/robinhood-testnet/v1/`; and
- `migration_history/robinhood-mainnet/v1/`.

If the official environment uses a different reviewed canonical identifier, state the mapping and use one name consistently. Never let a marketing alias and chain identifier create two histories for one network.

### Reservation table

Reserve stable, collision-free IDs and intended filenames for:

- token and RipeHq deployment;
- data/config registries;
- core Departments;
- governance and timelocks;
- selected vaults and assets;
- selected price sources;
- optional SavingsGreen/Stability Pool path;
- optional disabled PSM deployment/configuration;
- final capability/role/configuration handoff;
- CCIP pool and Department registration, pending Track 1;
- Track 6 S3 Lootbox floor;
- Track 6 S4 Deleverage cooldown/context;
- Track 6 S5 Ledger portable guard;
- Track 6 S6 Robinhood defaults and approved parameters;
- Track 6 S7 timelock/registry validation setup;
- Track 6 S8 lifecycle/capacity setup;
- Track 6 S9 disabled-integration manifest assertions; and
- Track 6 S10 tooling-only CAD report correction, explicitly marked as not requiring an onchain migration unless its implementation proves otherwise.

For each reservation, state prerequisite decisions, expected artifacts, dependencies, whether it is initial-deployment-only or upgrade-capable, and who can reassign it.

Do not assume the Base numeric sequence is suitable. The specification must explain its namespace/version convention, ordering guarantees, duplicate detection, and how future post-launch migrations avoid collisions.

### Execution semantics

Specify:

- preflight;
- dry-run or plan mode;
- clean deploy;
- checkpoint writes;
- idempotent rerun;
- safe resume after partial failure;
- explicit skip with evidence;
- irreversible step declaration;
- transaction receipt/finality check;
- manifest reconciliation;
- abort behavior;
- rollback where actually possible;
- new-address adoption;
- old-address retirement;
- role transfer;
- Safe/multisig handoff; and
- post-handoff loss of deployer authority.

Do not call redeployment or role reassignment “rollback” unless the prior state can actually be restored.

## Phase E: Specify manifests and release evidence

Define a versioned manifest schema that can represent both deployment and deliberate absence.

Include:

- schema version and network profile;
- chain ID and environment;
- canonical source commit;
- dirty-worktree prohibition;
- compiler and dependency versions;
- source, compiler-input, ABI, creation-bytecode, and deployed-bytecode hashes;
- contract address, deployer, transaction hash, receipt block/hash, and confirmations;
- constructor arguments and immutable values;
- verification provider, status, URL, and evidence timestamp;
- component-matrix ID and disposition;
- dependency graph and migration ID;
- registry IDs and entries;
- Department capabilities;
- owner/admin/guardian/operations roles;
- feature flags;
- selected defaults and parameters;
- external addresses with provenance and retrieval date;
- explicitly omitted/disabled/deferred integrations;
- live Base versus Robinhood version policy;
- pending decisions and launch blockers;
- post-deployment assertion results; and
- prior-manifest hash or progression link.

The schema must distinguish:

- a contract not deployed;
- a contract deployed but not registered;
- a registered contract with capability disabled;
- a feature flag disabled;
- a zero value that is a legitimate parameter; and
- an unresolved or missing value that blocks deployment.

Define what is committed under `migration_history/`, what remains local/operator evidence, and what is never written. No secret, raw key material, complete wallet transcript, or unsanitized provider response belongs in a manifest.

Specify how `current-manifest.json` is generated, validated, linked to immutable step manifests, and prevented from hiding an incomplete or failed migration.

## Phase F: Specify verification, ABI, and CCIP Solidity boundaries

- [ ] Define chain-neutral verifier adapters and the unsupported-provider failure.
- [ ] Define constructor/immutable encoding and compiler metadata required for reproducible verification.
- [ ] Define blueprint, module, proxy-like, and ordinary-contract verification behavior.
- [ ] Define ABI export inputs, deterministic naming, collision handling, and review of changed ABIs.
- [ ] Preserve current Vyper deployment support.
- [ ] Record Track 1's thin-subclass decision, exact Chainlink dependency pin,
  Solidity/compiler/EVM profile, and pending support/gas/review facts.
- [ ] Define how the CCIP Solidity outputs enter manifests, verification, and
  ABI export through the existing Python authority without guessed artifacts.
- [ ] Keep CCIP artifacts out of the initial deployment graph until the supported release and interface are approved.

If the existing verification provider cannot verify Robinhood contracts, specify a truthful `unverified — provider unsupported` state and a launch decision gate. Do not report verification success from browser availability alone.

## Phase G: Produce the clean-deployment validation plan

`robinhood-deployment-validation-plan.md` must define staged validation without implementing tests.

### Stage 1: Static and unit validation

- dependency-alert triage, pin provenance, and reviewed resolution of deployment-tooling findings;
- deliberate S1 exact-version-gate failure and re-approval when its pinned runtime changes;
- network-profile schema and unknown-network rejection;
- environment-variable presence without secret logging;
- chain-ID/RPC mismatch rejection;
- deterministic migration discovery and duplicate-ID failure;
- manifest schema and progression;
- constructor/source/artifact hashes;
- verifier adapter selection;
- ABI collision behavior;
- excluded integration handling; and
- Base profile regression.

### Stage 2: Local clean deployment

- execute the complete selected Robinhood migration graph from a clean checkout;
- use the same canonical artifacts intended for Base/Robinhood;
- apply approved Robinhood defaults only;
- validate every address, role, registry entry, capability, feature flag, and parameter;
- prove omitted integrations have no address, registry row, permission, route, or callable flag;
- prove a partial failure can stop and resume only where specified;
- regenerate and compare immutable/current manifests; and
- reject a dirty tree, stale build artifact, or mismatched chain ID.

### Stage 3: Fork or production-like rehearsal

- connect through the reviewed network profile;
- verify gas, receipts, confirmations, explorer behavior, and manifest evidence;
- rehearse Safe/multisig and role transfers without using production authority;
- run deployment-negative tests against a maintained list of forbidden Base addresses;
- run Track 6 S1 profiles and the S2 inventory guard when those slices exist;
- validate owner-approved live-version differences;
- rehearse abort/recovery for each irreversible boundary; and
- prove a full rebuild from the frozen commit reproduces artifacts.

### Stage 4: Robinhood test environment

- deploy the complete selected graph;
- configure one approved reserve and candidate Stock Token only after their gates;
- exercise deposit, borrow, repay, withdraw, liquidation, bad-debt accounting, and selected insurance/Stability Pool behavior;
- execute one local-governance parameter change through its timelock;
- prove Base governance/cross-chain dispatch has no privileged Robinhood path;
- execute approved PSM behavior or prove it remains disabled;
- execute CCIP bridge/reconciliation only after Track 1 and Chainlink gates;
- observe real block progression and run clock-sensitive cases;
- verify every contract and archive sanitized evidence; and
- keep the environment live for the owner-approved soak period.

### Stage 5: Mainnet rehearsal and restricted release

- freeze commit, dependencies, component graph, addresses, parameters, and manifests;
- re-verify every external address and network fact;
- rebuild and compare artifact hashes;
- rehearse exact migration, verification, role-transfer, pause, and abort runbooks;
- require launch-gate evidence before any broadcast;
- deploy with small initial limits;
- run post-deployment configuration assertions before enabling value paths;
- perform owner-approved minimal smoke actions;
- reconcile GREEN/RIPE supply after CCIP becomes active; and
- archive final immutable manifests and evidence.

### Required negative cases

The plan must include:

- unknown/mismatched chain ID;
- Base RPC or address leakage into Robinhood;
- missing RPC/explorer credential;
- explorer API incompatibility;
- stale or changed external address;
- duplicated/out-of-order migration ID;
- partial deployment and stale current manifest;
- wrong constructor argument or artifact hash;
- unverified bytecode;
- deployer retaining authority after handoff;
- omitted integration accidentally deployed or registered;
- zero-address call path;
- PSM mint/redeem/auto-deposit unexpectedly enabled;
- Stock Token collateral enabled before vault approval;
- CreditRedeem or Stability Pool swap unexpectedly enabled;
- unsupported price source reachable;
- CCIP pool capability active before timelock/registration completion;
- bad remote/token/pool CCIP configuration;
- unapproved live-version divergence; and
- failure to run S1/S2 gates once integrated.

Every future test must name its proposed file, prerequisite, fixture/network, expected evidence, runtime tier, and owner. Do not claim a clean-deployment test exists when it is only specified.

## Phase H: Split implementation into follow-on PRs

Propose small, ordered implementation slices. At minimum, separate:

1. dependency-security preflight and any narrowly reviewed pin refresh needed before deployment rehearsal;
2. network-profile abstraction and CLI selection;
3. Robinhood blueprint schema plus explicit address/omission validation;
4. `DefaultsRobinhood` generation and approved parameter manifest;
5. migration namespace, discovery, ID reservation, and skeletons;
6. manifest schema/versioning and release-evidence writer;
7. explorer verification adapter and ABI/artifact handling;
8. post-deployment assertion/checker tooling;
9. clean-deployment and negative test suite;
10. test-environment deployment/runbook;
11. production rehearsal and restricted-release runbook; and
12. CCIP Solidity inheritance/artifact integration after Track 1 closes.

For every slice include:

- purpose and exact expected files;
- input decisions and Track dependencies;
- component/migration IDs;
- allowed code versus generated output;
- Base regression impact;
- targeted and full validation commands;
- secrets and external-action boundary;
- reviewer/approver;
- abort conditions;
- rollback or remediation boundary; and
- downstream consumer.

Do not bundle unresolved contract semantics, parameter approval, network plumbing, and live deployment into one PR merely because all are needed for launch.

## Required decision register

The specification must contain a decision register with, at minimum:

| Decision area | Required disposition |
| --- | --- |
| Robinhood mainnet facts | chain ID, RPC policy, explorer/verification, gas, confirmations, source/date |
| Robinhood test environment | official environment or owner-approved alternative and limitations |
| Network-profile API | schema, identifiers, overrides, secret handling, owner |
| Migration namespace/version | paths, ID convention, reservations, collision policy |
| Manifest/release evidence | schema, committed/local/never-stored fields, retention |
| Live-version policy | strict parity, bounded temporary drift, or narrow permanent exception per component |
| SavingsGreen/sGREEN | deploy or omit and downstream graph |
| Stock Token vault | selected path, required shared fixes, owner acceptance |
| USDG/PSM | omit or deployed disabled; activation gates |
| CCIP | supported release, toolchain, registration path, pools, addresses, capabilities |
| Governance/admin roles | address source, timelock, Safe/multisig, handoff |
| External addresses | primary-source verification and freeze process |
| Gas/finality/retries | explicit owner/operations policy |
| CI | local commands now and future integration point |
| Dependency supply chain | alert triage, affected tooling, pin-refresh boundary, S1 re-approval, and deployment-rehearsal gate |
| Base upgrades | migration IDs, timing, drift/convergence, rollback |

Each row must include options, evidence, recommendation, owner, prerequisite, deadline/slice, and status. Clearly label recommendations; never write `approved` without an actual recorded owner decision.

## Deliverable A: Deployment-support specification

`docs/chains/rh/robinhood-deployment-support-specification.md` must contain:

- starting commit and input hashes;
- current deployment-system audit;
- assumption/defect/blocker register;
- network-profile schema and verified fact table;
- component deployment graph;
- configuration and environment-variable map;
- migration namespace and reservation table;
- manifest/release-evidence schema;
- verification/ABI/Solidity design;
- role/capability/registry sequence;
- disabled/omitted integration matrix;
- live-version policy map;
- follow-on implementation slices;
- decision register; and
- exact Section 1 checklist handoff.

## Deliverable B: Deployment validation plan

`docs/chains/rh/robinhood-deployment-validation-plan.md` must contain:

- validation principles and environments;
- proposed test paths and fixtures;
- clean-checkout and reproducibility procedure;
- static/unit/local/fork/testnet/mainnet validation matrix;
- migration idempotency/resume/abort cases;
- manifest and artifact assertions;
- post-deployment role/registry/capability/parameter assertions;
- negative Base-dependency and disabled-integration cases;
- Track 6 S1/S2 integration points;
- lifecycle/governance/PSM/vault/CCIP gates;
- smoke and supply-reconciliation plan;
- failure diagnostics and evidence retention;
- commands expected after each follow-on slice; and
- launch-gate mapping.

## Cross-track interface

- **Track 1 / CCIP:** consume the integrated decision and question packet. Route new Chainlink questions through the owner-approved Track 1 channel; do not contact Chainlink independently.
- **Track 2 / transferability:** consume fork/probe evidence. Treat live-chain sender/recipient eligibility and token acquisition as owner/counsel inputs, not deployment-tool assumptions.
- **Track 3 / matrix and inventory:** use stable component IDs and accepted dispositions. Report reconciliation gaps; do not renumber IDs.
- **Track 4 / USDG:** preserve the decision record and activation blockers. Deployment support must represent omitted versus deployed-disabled PSM precisely.
- **Track 5 / vault:** reserve only the owner-approved path and required shared-fix dependencies. Do not implement or bypass vault remediation.
- **Track 6 / clocks:** reserve migration IDs for S3–S10. Consume S1/S2 when integrated, but keep their validation status `pending` until commands actually pass. Any dependency refresh that changes S1's pinned Boa or pytest versions must intentionally trip its exact-version gate and receive reviewed pin/profile re-approval; do not classify that failure as an ordinary regression or weaken the assertion.
- **Future GREEN/RIPE price adapter:** keep disabled-feature slots explicit and deferred; do not select a market.

If two tracks propose the same migration, manifest field, network identifier, ABI path, or test file, record the collision and assign integration to the owner. Do not edit another track's branch.

## Approval and safety boundaries

The agent may:

- inspect local code, history, manifests, and artifacts;
- use current public primary documentation;
- make read-only public RPC calls with sanitized reproducible commands;
- draft the two owned documents;
- recommend schemas, identifiers, reservations, and implementation slices; and
- commit the reviewed deliverables to the Track 7 branch.

The agent must obtain fresh owner approval before:

- contacting Chainlink, Robinhood, an issuer, an explorer operator, or another external party;
- installing or selecting a new dependency or toolchain;
- editing code, defaults, configuration, migrations, manifests, ABIs, tests, CI, or generated output;
- accepting an address, role, Safe, guardian, parameter, migration ID, live-version policy, or deployment inventory as production-approved;
- accessing, requesting, displaying, or storing a secret;
- signing or broadcasting a transaction;
- deploying or verifying a live contract;
- committing raw RPC/provider evidence beyond the agreed artifact scope; or
- marking a `rh-summary.md` checkbox complete.

## Stop conditions

Stop and report evidence if:

- a required integrated track artifact is missing;
- the current toolchain cannot be described without accessing secrets;
- official Robinhood network facts cannot be verified;
- no adequate test environment exists and an owner alternative is required;
- the manifest model cannot distinguish omission, disabled state, and unresolved blockers;
- existing tooling inherently leaks a secret or Base address into another network;
- migration discovery cannot support isolated namespaces without a larger redesign;
- CCIP Solidity artifacts, exact dependency/compiler/EVM settings, and
  inheritance-delta evidence cannot fit a shared, reproducible release process;
- a proposal requires Robinhood-only core-contract source or `chain.id` protocol logic;
- an unresolved choice materially changes the graph and alternatives cannot safely be specified;
- a migration ID/path collides with integrated or parallel work;
- another branch changes one of the two owned deliverables; or
- satisfying the brief would require a state-changing external action.

Where safe, record mutually exclusive alternatives and their consequences rather than blocking the entire document. Stop only when proceeding would fabricate a fact, approval, or executable plan.

## Validation

Before handoff:

- [ ] Verify every repository path cited by the documents exists at the starting commit or is explicitly labeled a proposed future path.
- [ ] Verify every selected component uses an integrated component-matrix ID.
- [ ] Re-run searches for network/RPC/explorer/environment/migration/manifest assumptions.
- [ ] Confirm every Section 1 checklist item maps to an implementation slice and validation case.
- [ ] Confirm Track 6 S3–S10 migration needs have explicit reservations or an explained non-onchain disposition.
- [ ] Confirm every omitted/disabled component has a negative assertion.
- [ ] Confirm network and address facts have sources and retrieval dates.
- [ ] Confirm recommendations and approvals are visibly distinct.
- [ ] Confirm no code, configuration, migration, manifest, ABI, test, dependency, CI, generated output, or summary checkbox changed.
- [ ] Confirm the two documents are internally consistent and cross-linked.
- [ ] Run `git diff --check`.
- [ ] Record the starting commit, input hashes, source dates, validation commands, and final commit.

Use repository-native Markdown checks if they already exist. Do not add a documentation dependency for this track.

## Completion criteria

Track 7 is complete when:

- both deliverables exist and pass owner/reviewer scrutiny;
- the current deployment system is mapped precisely enough to avoid rediscovery;
- Robinhood network/configuration behavior is specified without Base/vendor assumptions;
- every component has a disposition and deployment/omission assertion;
- migration namespaces and Track 6 reservations are collision-free;
- manifests can prove code, configuration, permissions, omissions, and live-version policy;
- verification and future Solidity artifacts have explicit boundaries;
- clean-deployment and negative validation are implementation-ready;
- unresolved owner/external decisions remain explicit and do not masquerade as defaults; and
- follow-on PRs have disjoint enough ownership to review and run safely.

The completion report must state which Section 1 and release-workflow checklist items are **eligible for owner review**. It must not edit or tick `docs/chains/rh-summary.md`; the owner closes checklist items only after the corresponding implementation and validation have landed.
