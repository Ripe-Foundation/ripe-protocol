# PR #67 Remediation Plan

Status: approved for isolated implementation; not approved for merge, push, deployment, activation, or release.

## Bound candidate

- Repository: `Ripe-Foundation/ripe-protocol`
- PR: `#67`
- Review base: `91eda49ccd34a25090582aff0695075c4c806011`
- Review head and implementation baseline: `02468586d710e2cce2360c2bc07e94de6ebdab29`
- Integration branch: `codex/pr67-remediation-integration`
- The user's existing checkout and branch are out of scope and must remain untouched.

## Execution policy

This is a broad remediation, not a sequence of micro-patches. Each implementation lane owns its complete source, test, and documentation surface, finishes the lane's edits, and then runs one focused compile/test pass. Repeated full-suite runs during implementation are prohibited. Full suites, fork rehearsals, artifact regeneration, and independent rereview happen once against the integrated candidate after all source waves are complete.

Each lane works in a separate worktree and branch pinned to the bound head. Lanes may commit locally but may not push, deploy, activate, or merge. One lane owns each production file. Shared ABIs, artifact expectations, fixtures, workflows, and final runbooks are updated only after the production source is frozen.

## Settled owner decisions

1. `UniswapV2Prices` is monitoring-only. It must not be admitted as a collateral or other value-bearing price authority. Manipulable reserve observations are not required to become a collateral-grade oracle.
2. RipeGov migration must preserve each position's original lock, stored terms, and governance points.
3. Every historical RipeGov vault must be excluded from the generic vault-migration route. Historical sources remain eligible only through the dedicated RipeGov migration route.
4. Legacy Base migration remains `migrateLegacyRipeGovPositions(address[])`: a bounded batch of many users. For each user, every supported source asset is snapshotted before the first withdrawal and all supported positions migrate atomically.
5. RIPE and the active RIPE LP may have their `minLockDuration` reduced together during the controlled wind-down window. A one-block reduction is valid only after the census proves it is below every migrating position's stored historical minimum.
6. Batch size is selected from measured worst-case gas and preflight evidence, up to the source ceiling of 25 users. A late failure reverting the whole batch is accepted atomic behavior, not a reason to impose one-user calls.
7. Robinhood is still an internal testing deployment; preserving pre-remediation user state is not required.
8. CCIP is already live. CCIP work is live-state reconciliation, hardening, evidence, and documentation—not a preactivation gate or a rollback assumption.
9. Existing Git history is accepted. Do not rewrite it.
10. The checked-in Vyper ABI inventory is current at the bound head. Intentional selector removals are accepted subject to external-consumer inventory and corrected documentation; do not restore wrappers without a demonstrated consumer need.

## Wave 1 — production smart contracts

### Lane C1 — RipeGov and migration core

Exclusive production ownership: `VaultMigrator.vy`, migration-specific `Teller.vy` code, `RipeGov.vy`, `SwitchboardEcho.vy`, required migration structs/interfaces, and the historical-RipeGov classifier consumer.

Required closure:

- exclude all historical RipeGov IDs from generic migration;
- preserve global and per-user governance-point accrual-disable state, or implement an explicitly equivalent fail-closed target state;
- preserve pre-refresh unlock, terms, stored points, and pending points in both legacy and exporter-capable RipeGov migration;
- retain fail-closed target-virginity and replay/tombstone behavior;
- keep the settled multi-user, all-assets-per-user ABI and behavior;
- reconcile the exact Teller, target, source, VaultMigrator, Ledger, and CreditEngine pause requirements;
- add active-lock, dual-asset, multi-user, late-user rollback, batch-boundary, duplicate/empty/no-position, target-dirty, same-action-block, debt-health, and exact restoration coverage;
- correct Base migration documentation to the implemented batch shape.

### Lane C2 — Stability Pool and liquidation accounting

Exclusive production ownership: `StabVault.vy`, `StabilityPool.vy`, `AuctionHouse.vy`, stability-pool capability checks in `SwitchboardBravo.vy` and `SwitchboardCharlie.vy`, and directly required interfaces.

Required closure:

- prevent zero-price active claim assets from disappearing from NAV and being abandoned by an exiting cohort;
- prevent custody deficits from remaining fully valued;
- make liquidation receipt accounting call-local so prior donations cannot mask a short receipt;
- prevent fee-on-transfer or short outbound receipts from burning liabilities/shares as if the user received the full nominal amount;
- prevent `inLiquidation` from remaining latched when direct settlement consumes healthy collateral and no auction can clear the deficient remainder;
- require proposed/confirmed preferred Stability Pools to support every selector that downstream liquidation now calls, including `canAcceptLiquidationAsset`;
- preserve storage and enforce deployed-runtime size limits after the complete lane is implemented.

### Lane C3 — pricing and price-source admission

Exclusive production ownership: `UniswapV2Prices.vy`, BlueChip/Morpho price-source contracts, and directly required price interfaces/configuration.

Required closure:

- make the Uniswap monitoring-only boundary explicit and enforce it against collateral/value-bearing admission;
- retain or document accepted monitoring limitations without presenting the source as manipulation-resistant;
- correct BlueChip/Morpho V2 constructor, provenance, and failure-path compatibility;
- produce exact deployment-migration handoff items for Wave 2 rather than editing shared deployment scripts early;
- close price-test order contamination if it is local to the owned fixtures; otherwise hand it to final validation.

## Wave 2 — deployment, live systems, and repository tooling

### Lane O1 — migration runner and deployment safety

Required closure:

- bind the selected network profile to the RPC chain ID before any signing or submission;
- make exhausted retries and `None` transaction results fail closed rather than log as confirmed;
- correct resume/retry/start-timestamp semantics and prove non-idempotent steps cannot replay silently;
- either bind the advertised Safe backend or remove the false executable path;
- prevent candidate manifests from becoming current before the corresponding registry activation is confirmed;
- preserve prior active generations while replacement activation is pending;
- validate every imperative migration input marked unverified by the source-authority configuration;
- make ledger-signing and Defaults preparation fail on the wrong chain;
- repair `ccip_send.py` account construction, integer amount handling, and chain binding.

### Lane O2 — CCIP live reconciliation

Required closure:

- make every repository constant, parameter report, test, and document match live immutable order: RIPE pool ID 23 and GREEN pool ID 24;
- record activation transaction identities, observation blocks, owners/admins, token bindings, remote pools, and exact runtime/constructor evidence;
- reconcile the live 1.5.1 implementation with repository version, compiler, source, license, and notice claims;
- add Solidity build and focused tests to CI;
- prove or remediate automatic destination execution gas for every token and direction;
- obtain an explicit owner disposition for disabled lane rate limits and zero `rateLimitAdmin`;
- correct stale documents that still describe CCIP as deferred or inactive;
- validate existing supported-chain wiring instead of treating `isSupportedChain` as sufficient proof.

### Lane O3 — deployment migrations, ABIs, artifacts, and final documentation

Required closure:

- reconcile BlueChip/Uniswap deployment and registry steps with the frozen monitoring-only and constructor decisions;
- fix Base replay callers for final constructor shapes;
- make deployment migrations emit and verify the actual Safe registry actions they claim;
- correct the false `0009` claim that no signatures moved;
- regenerate all Vyper ABIs from final integrated source and inventory off-repository consumers of removed Teller/StabilityPool selectors and events;
- bind full deployed runtime and constructor immutables, not only compiler-template size;
- repair order-dependent shared fixtures and preserve both test-order reproductions;
- update status, runbooks, coverage records, and lifecycle documents to final code and live state.

## Final integrated validation

No full-suite or fork gate begins until Waves 1 and 2 are integrated and source/ABI shapes are frozen.

The final candidate must then pass, once per required environment:

1. Vyper and Solidity compilation, storage-layout review, ABI regeneration, and deployed-runtime/EIP-170 checks.
2. Focused contract regression and adversarial selections for every remediated finding.
3. Complete repository test suite with per-node failure/error identity retained.
4. Both known fixture-order directions.
5. Base fork rehearsal of timelocked RIPE+LP wind-down, multi-user batches, exact lock/point import, late-user rollback, configuration restoration, and reconciliation.
6. Robinhood clean deployment/fork qualification with chain binding, Safe calldata, manifest lifecycle, and registry postconditions.
7. CCIP full-path evidence for both tokens and both directions, or an explicit blocked/accepted-risk disposition.
8. Independent adversarial rereview of the integrated diff against this plan and the original finding ledger.

## Merge gate

The PR remains request-changes until every item above has either reproducible closure evidence or a specific owner-approved accepted-risk disposition. A green aggregate test count alone is not sufficient.
