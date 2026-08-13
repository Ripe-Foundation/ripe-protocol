# Ripe Protocol Smart Contract Audit Plan

## Document status

- **Purpose:** define a contract-first security audit of the Ripe Protocol code on `rh`.
- **Planning baseline:** live `rh` / `origin/rh` contract tree at commit `6ce9c6a8813e9ba9bcf5f9a810af1e8bc86b05e8`, tree `6a0aa2a24b4d89e0d1106045423c766a58936410`.
- **Contract-focused revision:** 2026-08-12.
- **Execution model:** rolling `rh` intake with exact per-workstream evidence snapshots and impact-scoped revalidation; ordinary branch movement does not stop the audit.
- **Primary scope:** 62 production Vyper contract files, two Ripe-owned Solidity source files defining three pool contracts, their imported modules and interfaces, the 18 vendored Solidity dependencies they compile against, and tests that provide evidence about those contracts.
- **Primary question:** can an untrusted or privileged actor cause incorrect authorization, accounting, custody, pricing, debt, supply, reward, liquidation, migration, cross-chain, or availability behavior in the contracts?
- **Not an audit result:** this plan organizes the work. It does not itself establish that any contract is safe.

The audit is deliberately centered on smart-contract source and composed smart-contract behavior. Deployment infrastructure is not an independent audit subject.

## 0. Contract-first mandate

Reviewer and agent time must be spent on:

- Contract entry points, internal paths, storage, state transitions, and invariants.
- Authorization, privilege changes, initialization, and configuration reachable through contract calls.
- Actual asset custody, token supply, shares, debt, collateral, rewards, reserves, and value conservation.
- External calls, callbacks, reentrancy, malicious dependencies, non-standard tokens, and failure atomicity.
- Economic manipulation, ordering, timing, oracle behavior, liquidation, and insolvency.
- End-to-end transaction flows across multiple contracts and all material permutations of those flows.
- Tests, reproductions, fuzzing, and stateful properties that prove or refute claims about contract behavior.
- Contract-level migration logic, including `VaultMigrator.vy`; this is distinct from reviewing deployment scripts.
- Vyper and Solidity source that is actually compiled into the protocol, including the Ripe CCIP wrappers and their pinned vendored dependencies.

The following are out of scope as standalone workstreams:

- Deployment scripts and deployment orchestration.
- Historical migration-script inventories.
- Manifests, ABI export pipelines, explorer verification, and source-publication mechanics.
- CI workflow design, cache behavior, release automation, documentation provenance, and repository cleanup.
- Operational runbooks, release packets, launch checklists, and key-custody procedures.
- Whether a particular release was or should be deployed, activated, or published.

A reviewer may inspect a non-contract artifact only when it is the shortest way to resolve a contract question—for example, which value initializes a contract, which price source is admitted, which address has an on-chain role, or what configured cap bounds a finding. That inspection stays supporting evidence inside the relevant contract batch. It does not become a separate infrastructure audit.

If time is constrained, cut non-contract evidence work before reducing contract review depth.

## 1. Audit objective and completion standard

The audit must determine:

1. What every production contract and externally reachable function can do.
2. Who can call each privileged path and how that authority can change on-chain.
3. Which storage and accounting invariants must always hold.
4. How value, debt, shares, supply, prices, rewards, and permissions move across contract boundaries.
5. Which external dependencies and token behaviors can violate assumptions.
6. Which adversarial sequences, boundary values, interleavings, and failure paths are possible.
7. Whether existing tests actually demonstrate the required behavior.
8. Which findings, known defects, accepted risks, and untested behaviors remain.

The comprehensive contract audit is complete only when:

- All 62 production Vyper contracts and all three Ripe-owned Solidity contracts have exactly one primary component owner.
- Every state-changing external, privileged, `@nonreentrant`, and `@payable` path is manually reviewed and mapped to direct or clearly identified composed-test evidence.
- Every material contract transaction flow in Section 6 has one canonical end-to-end model and completed permutation review.
- Every applicable cross-cutting invariant in Section 8 is reconciled across all contracts that read or write it.
- Every confirmed issue has a stable identifier, severity, affected contracts and flows, proof, and disposition.
- Every inherited `F-`, `DV-`, strict-xfail, and relevant `RH-D` contract issue is rechecked against the exact audit candidate without losing its original identity.
- Remediated findings receive regression evidence and independent retest.
- Unreviewed contracts, functions, branches, flows, or assumptions are listed explicitly rather than hidden behind a green test suite.

An audit report may accurately finish while reporting unresolved findings. It may not describe contracts as ready or safe when a Critical or High issue remains unresolved. Its conclusions apply to the exact final report commit/tree; later `rh` changes require impact-scoped delta review before inheriting those conclusions.

## 2. Standard workflow for every contract batch

Each batch follows the same seven steps.

### Step 1 — Freeze contract scope

Record:

- Exact commit and tree.
- Primary contract paths and imported contract dependencies.
- Interfaces, external protocols, and contract configuration values needed to understand behavior.
- Entry points, privileged roles, state owners, and downstream callers.
- Relevant tests and known issues.
- Exact `master…rh` contract delta for the batch.
- Explicit exclusions.

The charter must link every intersecting `F-`, `DV-`, strict-xfail, accepted-risk, and contract-relevant `RH-D` identifier.

### Live `rh` change and non-blocking reconciliation

Freezing scope means that each conclusion and proof remains reproducible against an exact commit and tree. It does **not** require the `rh` branch to stop moving, and ordinary `rh` changes do not pause the audit program.

The audit lead maintains a branch-change ledger. Intake checkpoints occur before a batch or flow begins, before it closes, and before the final report snapshot is frozen. Additional checks may run whenever `rh` advances; intake triage should be quick and must not hold unrelated work. At each checkpoint, record:

- Previous and new `rh` commit/tree.
- Changed production contracts, imported modules, interfaces, and contract-relevant test evidence.
- The affected batch owners, flow owners, shared invariants, findings, and proofs.
- Semantic-impact classification, required revalidation, reviewer, and completion state.
- The newest exact commit against which each batch and flow conclusion is valid.

Classify each change by contract impact rather than commit size or line count:

1. **No contract-semantic impact:** documentation, deployment/release material, repository maintenance, or other changes that do not alter compiled contract behavior. Test-only changes may strengthen or weaken evidence but do not by themselves invalidate a source conclusion. Continue every contract and flow workstream; update only the affected evidence mapping when relevant.
2. **Localized contract impact:** a production-contract change with effects confined to identified contracts, entry points, or invariants and no credible propagation into unrelated flows. Continue all unrelated workstreams. Reopen only the affected source paths, test claims, findings, and transaction-flow permutations.
3. **Cross-cutting or material contract impact:** a change to authorization, initialization, accounting, custody, price resolution, debt, supply, liquidation, migration, external-call behavior, shared interfaces/registries, or another load-bearing assumption. Pause closure only for the affected batches, flows, and invariant families while their owners revalidate. Unaffected work continues.

A change is not material merely because it touches many lines, and a small diff is not minor merely because it touches few. Review semantic reach, value and authority at risk, interface/storage effects, downstream callers, and changed adversarial behavior.

Agents continue from their recorded snapshots and must not silently relabel old evidence as current. When a newer change intersects their work, they retain completed analysis that remains valid, mark only affected conclusions stale, and publish the delta handoff to the relevant component and flow owners. Do not restart a whole batch when path-level or invariant-level revalidation is sufficient.

A full-program pause is exceptional and requires the audit lead to show that the candidate can no longer be reproduced or that a change invalidates shared assumptions across most of the contract system. Normal fixes, additions, merges, and localized refactors do not meet that threshold.

Before final reporting, freeze one final report commit/tree and reconcile the cumulative contract delta from the starting snapshot through that final snapshot. Closure requires zero untriaged production-contract changes, refreshed evidence for every affected conclusion, and an explicit list of any post-baseline changes not reviewed. Later `rh` movement does not retroactively change what was audited; it creates a new delta-review obligation before the later commit can inherit the report's conclusions.

### Step 2 — Build the contract model

For each contract, document:

- Purpose and assets or authority at risk.
- Storage owned and storage read from other contracts.
- External/public entry points and caller restrictions.
- Internal call graph and state-transition graph.
- Trusted contracts, untrusted actors, callbacks, and external dependencies.
- Initialization assumptions and unsafe partial states.
- Contract invariants, preconditions, postconditions, and failure-atomicity requirements.

### Step 3 — Manual source review

Review the source path by path. Do not substitute automated output or test success for reading the contract.

For every state-changing external or privileged entry point, trace:

- Caller and beneficiary.
- Inputs and boundary values.
- Reads, writes, and emitted events.
- Internal and external calls.
- Asset, share, supply, debt, reward, price, and permission deltas.
- Reverts and whether all prior effects roll back.
- Reentrancy and callback reachability.
- Same-block, timestamp, ordering, retry, and replay behavior.
- Interaction with every applicable invariant.

### Step 4 — Map existing tests

Map contract behaviors to exact test nodes and assertions. Distinguish:

- Direct unit evidence.
- Composed integration evidence.
- Indirect fixture execution without a behavior assertion.
- Mock-only evidence.
- Strict xfails and known defects.
- Untested or weakly tested behavior.

Do not use test filenames, collection totals, or line coverage as a proxy for semantic coverage.

### Step 5 — Execute adversarial validation

Add or run focused proof tests for the highest-risk gaps. Prefer:

- Boundary and negative tests.
- Malicious caller, receiver, token, vault, oracle, and callback models.
- Stateful sequences and cross-function invariant tests.
- Multi-user and keeper/liquidator interleavings.
- Arithmetic, rounding, dust, first/last-user, and empty-state properties.
- Reorder, repeat, replay, partial-failure, and dependency-outage cases.
- Economic manipulation and capital-feasibility analysis.

Assessment proof work must not change production contracts. Contract fixes belong to a separately authorized remediation branch.

### Step 6 — Reconcile composed flows

Share source-sensitive conclusions with every transaction-flow agent that crosses the batch. A batch may not close a behavior that depends on another contract until the owning reviewer accepts the shared invariant and call/state/value model or records a preserved disagreement.

### Step 7 — Report findings and gaps

Produce one compact batch packet containing:

1. Contract and authority map.
2. Invariant, state-transition, and value-flow model.
3. Source-to-test and adversarial-proof record.
4. Findings, inherited-issue dispositions, unresolved questions, and unchecked surface.

These are required contents, not four mandatory files. Artifact volume is not progress.

## 3. Contract review standard

Every batch applies the following checklist where relevant.

### Authorization and initialization

- Correct callers for every privileged function.
- Direct and indirect privilege escalation.
- Governance, timelock, guardian, department, migrator, keeper, and integration boundaries.
- Role transfer, replacement, renunciation, and recovery behavior implemented by contracts.
- Reinitialization, partial initialization, zero addresses, stale dependencies, and unsafe defaults.
- Blast radius of each privileged contract action.

The audit reviews the on-chain authority model. It does not audit off-chain signer operations or key-management procedures.

### Accounting and custody

- Actual received and sent balances rather than nominal transfer amounts.
- Conservation of assets, shares, supply, debt, collateral, reserves, rewards, and liquidation proceeds.
- Rounding direction, precision loss, dust, minimums, maximums, and accumulated leakage.
- First depositor, last withdrawer, empty vault, zero supply, deficient backing, and insolvent states.
- Agreement between internal accounting, reported value, and token custody.

### State transitions and composition

- Valid and invalid transitions, repeats, reorders, retries, and terminal cleanup.
- Cross-function and cross-contract invariant preservation.
- Partial work and failure atomicity before and after external interaction.
- Index/list integrity when users, vaults, borrowers, assets, or positions are added, removed, or migrated.
- Isolation: failure for one asset, vault, oracle, or user must not unexpectedly block unrelated state.

### External behavior

- Reentrancy and callback surfaces.
- Fee-on-transfer, rebasing, blacklist, pause, malformed-return, callback, and failed-transfer tokens.
- Oracle staleness, decimals, confidence, manipulation, disagreement, zero/extreme values, and outage.
- External vault/protocol identity, liquidity, share-price, and failure assumptions.
- Malicious or unavailable receivers, keepers, liquidators, routers, pools, and integrations.

### Time, ordering, and economics

- Timestamp, inherited `block.number`, and ArbSys action-block semantics.
- Same-action restrictions, cooldowns, expiries, reward cadence, auction timing, and snapshot cadence.
- Front-running, sandwiching, griefing, keeper competition, liquidation ordering, and replay.
- Capital required, profit path, victim loss, protocol loss, detectability, and recoverability.
- Current configured exposure and realistically reachable exposure through contract-authorized changes.

### Cross-chain contracts

- Mint/burn conservation across lanes.
- Remote token and pool identity.
- Domain separation, duplicate/reordered messages, ownership, allowlists, rate limits, pause, router, and RMN assumptions.
- Source/destination asymmetry and failure recovery.
- Ripe-owned wrapper behavior and security-relevant inherited behavior from pinned vendored contracts.

## 4. Source-to-test and proof standard

The production Vyper surface at the planning baseline contains 982 external functions, including 586 state-changing externals, 59 `@nonreentrant` externals, and four `@payable` externals, plus 1,637 explicit `assert`/`raise` conditions and 1,509 `if`/`elif` branches.

Traceability is tiered to keep it rigorous:

- **Tier 1 — exhaustive:** all state-changing external, privileged, `@nonreentrant`, and `@payable` paths; every custody, accounting, debt, supply, price, reward, configuration, liquidation, and contract-migration transition; and every inherited issue.
- **Tier 2 — exhaustive inside the risk boundary:** material branches, reverts, external failures, events, and dependency outcomes reachable from Tier 1.
- **Tier 3 — risk-selected:** remaining views and helpers. Record total population, reviewed count, selection rationale, and every omitted area.

For each Tier 1 row, record:

- Contract and function.
- Allowed and forbidden callers.
- Material input classes and boundaries.
- State/value deltas and invariant effects.
- Exact direct or composed test nodes.
- Assertion quality.
- Missing proof and planned adversarial validation.
- Final conclusion and linked finding IDs.

### Test-suite facts that affect contract evidence

- The default lean collection selects 3,605 tests and deselects 294.
- Clearing repository `addopts` selects 4,834 tests and deselects 143.
- Both ordinary lanes retain the default `--fork local` selection. It selects 247 of 349 price-source nodes and 286 of 326 Endaoment nodes, deselecting 102 and 40 respectively; clearing `addopts` is not an all-fork contract suite.
- The suite contains one strict-xfail node from one site: `DV-15`, the accepted dormant-dust exit limitation in Stability Pool. The former strict xfails for `DV-04`, `DV-05`, `DV-08`, `DV-09`, `DV-10`, `DV-13`, `DV-14`, and Uniswap manipulation are no longer an open-xfail register; their changed behavior and regressions still require audit review.
- Marker-only collection selects four fuzz and ten gas nodes. Marker names or green wrapper output must never be treated as evidence without a non-zero expected collection.
- `solidity/test/RipeCcipBurnMintTokenPools.t.sol` now provides seven passing Forge tests for compiled-in capabilities, constructor bindings, and inherited owner controls of the token-specific candidate wrappers. This is useful focused evidence, not coverage of the full inherited CCIP message, chain-configuration, allowlist, mint/burn, and rate-limit state machines.

Each batch must run its focused contract tests, relevant composed tests, and new adversarial proofs in an isolated environment. Record exact commands, selected/deselected/xfailed counts, seeds, and raw failures. Use separate processes when mutable global Boa state can leak between selections.

Quantitative coverage may help locate untouched code, but contract closure depends on semantic mapping and adversarial evidence.

## 5. Contract batches

The 62 primary non-mock Vyper contracts total 37,733 physical source lines. The two Ripe-owned Solidity source files add 123 lines and define three pool contracts. The 18-file, 1,792-line vendored Solidity subtree is dependency source, not a separate infrastructure batch.

The delta columns compare live `master` commit `91eda49…` with planning baseline `rh` commit `6ce9c6a…`. Delta concentration prioritizes review order; unchanged contracts remain in scope.

| Batch | Contract area | Primary Vyper | Owned Solidity files | Current source lines | Changed owned files | Owned-source churn | Risk emphasis |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | Shared modules and protocol state | 6 | 0 | 3,148 | 3 | 116 | State ownership, permissions, clock identity, shared invariants |
| 2 | Governance, registries, and configuration contracts | 13 | 0 | 10,662 | 6 | 1,656 | Dependency replacement, privileged configuration, unsafe combinations |
| 3 | Asset/vault registries, oracle, and monitoring contracts | 13 | 0 | 7,151 | 2 | 673 | Price integrity, admission, monitoring isolation, failure handling |
| 4 | Tokens and cross-chain supply contracts | 5 | 2 | 1,230 | 3 | 139 | Supply, shares, signatures, bridge authority and conservation |
| 5 | Vaults and contract-level position migration | 9 | 0 | 4,220 | 5 | 1,473 | Custody, reserved claims, exact delivery, Stability Pool, migration |
| 6 | Teller entry points | 2 | 0 | 1,483 | 2 | 264 | Deposit/withdraw boundary, callbacks, actual receipt |
| 7 | Credit and debt lifecycle | 2 | 0 | 1,679 | 2 | 93 | Borrow/repay/redemption, account freeze, interest, bad debt |
| 8 | Liquidation, auctions, and deleveraging | 3 | 0 | 2,865 | 1 | 148 | Insolvency, retry/freeze state, settlement, incentives, liveness |
| 9 | Endaoment contracts | 3 | 0 | 2,255 | 0 | 0 | Reserve custody, PSM economics, privileged transfers |
| 10 | Rewards and bonds | 3 | 0 | 2,082 | 2 | 248 | Accrual, claim, vesting, budgets, multi-user fairness |
| 11 | Governance and operational department contracts | 3 | 0 | 1,081 | 1 | 28 | Execution authority, compensation, fund/token issuance |

`rh` is a strict 521-commit descendant of `master` at the planning baseline. Twenty-seven of 64 Ripe-owned production source files differ: 25 Vyper files plus both Solidity files, with 4,296 added and 542 deleted lines. Batches 2, 5, 3, and 6 contain 84.0% of the 4,838 lines of owned-source churn. Review capacity should be weighted accordingly without treating unchanged source as audited.

Since the prior `02468586…` plan baseline, 11 Vyper files and both owned Solidity files changed. The ownership topology remains complete, but the audit emphasis must now include:

- Uniswap V2's replacement with an inert `PriceSource` surface and separate manipulable RIPE/WETH monitoring views.
- Stability Pool reserved-liability, exact-delivery, claim-asset separation, and dormant-dust behavior.
- RipeGov term/point preservation and stricter ordinary, governance, and legacy migration boundaries.
- Whole-account liquidation freeze, zero-progress retry, singleton/batch equivalence, refund arithmetic, and collateral-delivery behavior.
- Proposal- and execution-time validation of priority Stability Pool and liquidation configuration.
- Candidate-versus-legacy CCIP pool semantics and the lack of intrinsic constructor-token/capability coupling in the token-specific wrappers.

### Batch 1 — Shared modules and protocol state

**Primary contracts**

- `contracts/modules/Addys.vy`
- `contracts/modules/DeptBasics.vy`
- `contracts/modules/LocalGov.vy`
- `contracts/modules/TimeLock.vy`
- `contracts/data/Ledger.vy`
- `contracts/data/MissionControl.vy`

**Contract focus**

- Address lookup, authorization, governance transfer, and timelock behavior.
- Canonical state ownership and allowed writers.
- Ledger invariants used by deposits, debt, rewards, and liquidations.
- Native versus ArbSys action-block identity and failure behavior.
- User/vault and borrower index integrity.
- Global risk-parameter validation and downstream failure propagation.

### Batch 2 — Governance, registries, and configuration contracts

**Primary contracts**

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

**Contract focus**

- Department registration, replacement, enablement, and authority.
- Address integrity and dependency rewiring.
- Governance, timelock, guardian, and emergency behavior enforced on-chain.
- Configuration ranges, defaults, and unsafe combinations.
- Initialization order, partial states, and replacement paths.
- Proposal- and confirmation-time revalidation of target MissionControl pointers, preferred Stability Pool identity, supported assets, live contract capability, pause state, and liquidation-asset acceptance.
- Configured and contract-reachable exposure, including debt limits and admission changes.

### Batch 3 — Asset/vault registries, oracle, and monitoring contracts

**Primary contracts**

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

**Contract focus**

- Asset/vault registration and authoritative address selection.
- Routing, fallback, aggregation, staleness, heartbeat, decimals, sign, confidence, and zero/extreme prices.
- Manipulation resistance and spot/liquidity dependence.
- Morpho V2 factory/vault validation and fail-closed behavior.
- `UniswapV2Prices.vy` is now deliberately monitoring-only: prove every `PriceSource` price/configuration path remains inert, every administrative method either returns `False` or reverts as specified, and no protocol price consumer can treat its monitoring output as an admitted oracle feed.
- RIPE/WETH constructor identity and 18-decimal assumptions, reserve orientation, raw-call returndata validation, integer bounds, overflow-safe multiplication, PriceDesk/WETH lookup failure, and zero-on-failure behavior of the manipulable monitoring views.
- Cross-source disagreement, source replacement, failure, and denial of service.
- Fidelity of oracle mocks used as proof.

### Batch 4 — Tokens and cross-chain supply contracts

**Primary contracts**

- `contracts/tokens/modules/Erc20Token.vy`
- `contracts/tokens/modules/Erc4626Token.vy`
- `contracts/tokens/GreenToken.vy`
- `contracts/tokens/RipeToken.vy`
- `contracts/tokens/SavingsGreen.vy`
- `solidity/src/RipeTokenPool.sol`
- `solidity/src/RipeCcipBurnMintTokenPools.sol`

**Dependency contracts**

- `solidity/src/v0.8/` vendored Chainlink CCIP 1.5.1 and OpenZeppelin source.

**Contract focus**

- Mint, burn, transfer, approval, permit/signature, and authorization.
- ERC-20/ERC-4626 compatibility, conversions, and rounding.
- Supply conservation and privileged issuance.
- RipeHq mint-capability checks, inherited `getToken()` binding, and pool authority. The token-specific candidate wrappers compile capabilities into bytecode but accept an arbitrary constructor token; the audit must prove the surrounding contract composition binds the intended token to the declared capability.
- Separation between `RipeCcipBurnMintTokenPools.sol` as the token-specific repository candidate and `RipeTokenPool.sol` as the legacy configurable-capability contract; neither model inherits assurance from the other.
- Cross-chain burn/mint conservation, remote identity, rate limits, pause, ownership, router/RMN, replay, and lane asymmetry.
- Gaps beyond the seven focused Forge tests, especially inherited chain configuration, allowlist, message validation, mint/burn, rate-limit, ownership-transfer, and recovery state machines.
- Non-standard token behaviors assumed by downstream contracts.

### Batch 5 — Vaults and contract-level position migration

**Primary contracts**

- `contracts/vaults/modules/VaultData.vy`
- `contracts/vaults/modules/BasicVault.vy`
- `contracts/vaults/modules/SharesVault.vy`
- `contracts/vaults/modules/StabVault.vy`
- `contracts/vaults/SimpleErc20.vy`
- `contracts/vaults/RebaseErc20.vy`
- `contracts/vaults/StabilityPool.vy`
- `contracts/vaults/RipeGov.vy`
- `contracts/core/VaultMigrator.vy`

**Contract focus**

- Deposit, withdrawal, balance, share, and custody invariants.
- Yield, positive/negative rebases, loss, dust, and rounding.
- Stability Pool deposit, claim, redemption, and liquidation effects.
- Reserved claim liabilities, custody-deficit fail-closed behavior, exact recipient delivery, prohibition on using a stability asset as a claim asset, active/dormant claim transitions, per-claim configuration, singleton/batch claim equivalence, and reward aggregation.
- RipeGov permissions, contributor-specific lock terms, vault-local point-disable policy, export checkpoints, lock-term refresh boundaries, points, and rewards.
- Migration authorization, Teller-pause prerequisite, classification of every current RipeGov vault ID, legacy-route separation, source/target validation, exact transfer/share preservation, list integrity, retries, atomicity, and cleanup.
- Fee-on-transfer, blacklist, reentrancy, and failed-transfer behavior.
- Revalidate the changed behavior formerly pinned by `DV-04`, `DV-05`, `DV-08`, `DV-09`, `DV-10`, `DV-13`, and `DV-14`; carry `DV-15` as the sole current strict-xfail residual for dormant dust stranded after full exit.

### Batch 6 — Teller entry points

**Primary contracts**

- `contracts/core/Teller.vy`
- `contracts/core/TellerUtils.vy`

**Contract focus**

- Deposit, withdrawal, rebalance, and housekeeping paths.
- Caller/user/beneficiary separation and delegated actions.
- Actual custody deltas and agreement with vault results.
- Ordinary user flows versus VaultMigrator-only paths.
- State ordering, callbacks, reentrancy, partial failure, and the receipt-measurement guard across every custody-changing or housekeeping route.
- Action-block enforcement, fees, rewards, health checks, and utility/view consistency.

### Batch 7 — Credit and debt lifecycle

**Primary contracts**

- `contracts/core/CreditEngine.vy`
- `contracts/core/CreditRedeem.vy`

**Contract focus**

- Borrow eligibility, collateral value, limits, and health.
- Deficient backing and Stock-token delivery assumptions.
- Interest, rate updates, accrual timing, and precision.
- Partial/full repay, overpayment, refund, and third-party repayment.
- Debt conservation through mint, burn, repayment, redemption, and liquidation.
- Whole-account freeze while fungible auctions remain, threshold unification, zero-progress retry behavior, and agreement between health views and state-changing liquidation/redemption paths.
- Same-block/reordered operations, oracle dependence, bad debt, and recovery.

### Batch 8 — Liquidation, auctions, and deleveraging

**Primary contracts**

- `contracts/core/AuctionHouse.vy`
- `contracts/core/AuctionHouseNFT.vy`
- `contracts/core/Deleverage.vy`

**Contract focus**

- Liquidation eligibility and account-health transitions.
- Singleton/batch liquidation and purchase equivalence, including caller/pause checks, aggregate keeper rewards, refunds, and event/accounting outcomes.
- Auction creation, retry ownership, whole-account freeze, pricing, bidding, settlement, claim, cancellation, and the rule that zero-repayment/no-auction passes remain economically inert.
- Collateral/debt conservation using actual delivered custody, including exact Stability Pool receipt and Savings Green conversion.
- Stability Pool and Savings Green interactions.
- Deleverage phases, asset selection, swaps, and withdrawal effects.
- Front-running, griefing, stale prices, unfillable auctions, bad debt, and liveness.

### Batch 9 — Endaoment contracts

`Endaoment` is the spelling used by the repository.

**Primary contracts**

- `contracts/core/Endaoment.vy`
- `contracts/core/EndaomentFunds.vy`
- `contracts/core/EndaomentPSM.vy`

**Contract focus**

- Fund custody, allowed destinations, and privileged transfers.
- PSM/stabilizer mint-redeem accounting.
- Pricing, fees, slippage, limits, decimals, and reserve conservation.
- Insolvency, dependency failure, and interaction with Green, Savings Green, Ripe, and credit.

### Batch 10 — Rewards and bonds

**Primary contracts**

- `contracts/core/Lootbox.vy`
- `contracts/core/BondRoom.vy`
- `contracts/config/BondBooster.vy`

**Contract focus**

- Deposit/borrow point accrual and reward allocation.
- Claiming, refresh cadence, double claims, exact delivery, dust, forfeiture, and cleanup.
- Bond creation, accounting, vesting, redemption, and booster effects.
- Rounding, supply/budget constraints, timing, and multi-user fairness.
- Teller, CreditEngine, RipeGov, and migration side effects.

### Batch 11 — Governance and operational department contracts

**Primary contracts**

- `contracts/core/Boardroom.vy`
- `contracts/core/HumanResources.vy`
- `contracts/modules/Contributor.vy`

**Contract focus**

- Proposal/execution authority and contract-enforced governance transitions.
- Contributor creation, compensation, update, and removal.
- Token/fund issuance limits and blueprint initialization behavior.
- Timelock, emergency, contributor/operator separation, and cross-department escalation.
- Blast radius of compromised or unavailable privileged callers as expressed by contract logic.

## 6. End-to-end contract transaction flows

Component review alone is insufficient. Each flow receives one flow agent responsible for the complete call/state/value model and its material permutations.

| Flow ID | Contract transaction flow | Home batch | Participating batches |
| --- | --- | ---: | --- |
| `AUD-FLOW-01` | Deposit and exact custody | 6 | 1–6, 10 |
| `AUD-FLOW-02` | Withdrawal, actual receipt, and accounting cleanup | 6 | 1–7, 10 |
| `AUD-FLOW-03` | Borrow and GREEN delivery | 7 | 1–7, 10 |
| `AUD-FLOW-04` | Repayment and redemption | 7 | 1–4, 7 |
| `AUD-FLOW-05` | Liquidation, account freeze/retry, auction, settlement, and bad-debt reconciliation | 8 | 1, 3–8, 10 |
| `AUD-FLOW-06` | Deleverage, queued-auction interaction, and residual account health | 8 | 1, 3–8 |
| `AUD-FLOW-07` | BasicVault and RipeGov position migration, including legacy-route separation | 5 | 1, 2, 4–6, 10 |
| `AUD-FLOW-08` | Stability Pool deposit, reserved claims, exact delivery, dormant dust, and liquidation absorption | 5 | 1, 3–5, 8, 10 |
| `AUD-FLOW-09` | Reward accrual, claim, cleanup, bond creation, vesting, and redemption | 10 | 1, 2, 4–7, 10 |
| `AUD-FLOW-10` | Endaoment reserve movement and PSM mint/redeem | 9 | 1–4, 7, 9 |
| `AUD-FLOW-11` | Price resolution, source failure, asset/source admission, and monitoring isolation | 3 | 2, 3, 5–9 |
| `AUD-FLOW-12` | Governance, timelock, department, and configuration mutation | 2 or 11 | 1–3, 11 |
| `AUD-FLOW-13` | CCIP pool capability/token binding, burn, message validation, mint, and aggregate supply | 4 | 2, 4 |

Each flow packet must show:

- Initiating actor, caller, beneficiary, entry point, and terminal outcomes.
- Exact contract call graph and trust boundaries.
- Expected storage, custody, supply, debt, share, reward, reserve, and event deltas.
- Preconditions, postconditions, rollback requirements, and observable evidence.
- Exact source paths/functions and tests.
- Findings, inherited issues, unchecked variants, and owner decisions.

### Required flow permutations

Every applicable dimension is covered directly, by justified risk-driven combinations, or listed as a gap:

- **Caller:** user, delegate, keeper, governance, migrator, integration, forbidden caller, and caller/beneficiary separation.
- **Amount:** zero, one, dust, rounding boundary, partial, full, minimum, maximum, and accumulated leakage.
- **State:** empty, first user, existing position, last user, threshold, insolvent, paused, legacy, migrated, partially configured, active/dormant claim, reserved-liability deficit, queued auction, and recovered.
- **Asset/dependency:** standard, fee-on-transfer, rebasing/loss, blacklist, callback, failed/malformed return, deficient backing, stale/zero/extreme price, and outage.
- **Ordering:** singleton versus batch, repeat, reorder, zero-progress retry, replay, same action block, expiry/cooldown boundary, front-run, and multi-user interleaving.
- **Failure point:** before, during, and after external interaction; unchanged-state guarantee; rollback; resume; isolation; terminal cleanup.
- **Economic state:** shallow/deep liquidity, rate-limit exhaustion, keeper/liquidator competition, slippage, bad debt, and capital-feasible manipulation.
- **Cross-chain when applicable:** source/destination asymmetry, remote identity, duplicate/reordered message, ownership, allowlist, router/RMN, pause, and rate limits.

Do not attempt a meaningless full Cartesian product. Cover every material factor and boundary directly, use pairwise or higher-order combinations where factors interact, and use stateful/property-based sequences for ordering-dependent invariants. Preserve the rationale for omitted combinations.

## 7. Parallel agent execution

The audit is intentionally parallel, but source ownership and final conclusions remain singular.

### Component agents

Each active component agent or pod owns one batch and is accountable for:

- The canonical model of its contracts.
- Function-by-function manual review.
- Contract-specific test mapping and proof work.
- Findings rooted in its source.
- Handing accepted source-sensitive conclusions to flow agents.

One agent may specialize in source review and another in contract tests or adversarial proofs, but they work from one batch model and one findings register.

### Flow agents

Each flow agent owns one end-to-end transaction flow. The flow agent may inspect any supporting contract but may not create a competing source-level conclusion for a contract owned by another component agent. Suspected shared root causes are routed to the owning component agent and linked to every affected flow.

### Central review

One audit lead owns:

- Scope and contract-ownership integrity.
- The shared permission, custody, supply, debt, price, and external-call matrices.
- Finding identity and severity consistency.
- Dependency disagreements and final report synthesis.

Critical/High candidates and other load-bearing conclusions require a fresh-context challenger who did not author the conclusion or implement its fix.

### Capacity and waves

The methodological ceiling is five active component pods when the execution environment has that capacity. The default Codex kickoff uses one audit lead plus three worker agents, for four concurrent participants total. Flow agents count against the real work-in-progress limit; they are not free extra capacity. Never exceed the runtime's available agent slots.

| Wave | Contract work | Exit condition |
| --- | --- | --- |
| 0 | Record the starting contract snapshot; assign all 65 Ripe-owned production contracts across 64 source files; bind inherited contract issues; establish the branch-change ledger plus shared invariant and finding registers. | Zero unowned or double-owned contracts; starting charters accepted; rolling `rh` intake owner and checkpoints established. |
| 0.5 | Calibrate on the Batch 5 `BasicVault.vy` / `SimpleErc20.vy` exact-custody slice and `AUD-FLOW-01`. | Source review, test mapping, adversarial proof, flow handoff, and synthesis quality are accepted before broad fan-out. |
| 1 | Run Batches 1–4 and continue Batch 5, weighting capacity toward Batches 2, 5, and 3. Start `AUD-FLOW-11`, `AUD-FLOW-12`, and `AUD-FLOW-13` when their component models stabilize. | Shared state, authority, price, token, vault, and migration models are stable. |
| 2 | As foundation slots release, run Batches 6, 7, 8, 10, and 11, pairing CreditEngine and AuctionHouse review early because the current candidate changes their shared freeze/retry state machine. Activate deposit/withdraw, borrow/repay, liquidation/deleverage, reward, migration, and governance flows. Start Batch 9 in the next available slot. | User-entry, debt, liquidation, reward, governance, and Endaoment contract models are stable. |
| 3 | Close Batch 9 and every remaining composed flow; execute protocol-wide invariant and adversarial campaigns, with independent replay of Stability Pool, liquidation, migration, monitoring-isolation, and CCIP capability/token-binding claims. Freeze the final report snapshot and reconcile all contract changes since the starting snapshot. | All 11 batches, 13 flows, shared matrices, inherited issues, findings, and `rh` change-ledger entries reconcile against the exact final report commit/tree. |
| 4 | Independently retest authorized contract remediations and all affected flows. | Every remediation has regression proof; every finding has a final disposition; remaining risk and unchecked contract surface are explicit. |

Agents may begin reading a dependent contract early. They may not close a dependency-sensitive conclusion before the relevant owner publishes a stable handoff.

## 8. Protocol-wide contract invariants

Maintain one reconciled matrix for each invariant family.

### Permission integrity

- Every privileged contract function has the intended caller.
- On-chain role changes cannot bypass timelock, governance, guardian, department, or initialization rules.
- Replacing a dependency cannot create unauthorized state writers, minters, asset handlers, or price setters.

### Custody and share conservation

- Contract accounting follows actual token balance deltas.
- Assets cannot be created, lost, double-counted, stranded, or withdrawn twice.
- Shares and reported value remain consistent through deposits, withdrawals, rebases, losses, migration, and liquidation.

### Debt and collateral conservation

- Debt minted, accrued, repaid, redeemed, liquidated, and written down reconciles globally and per account.
- Collateral cannot support multiple incompatible claims.
- Bad debt and deficient backing are recognized and contained.

### Token and cross-chain supply conservation

- Privileged mint/burn paths are bounded by contract authority.
- GREEN, RIPE, Savings Green, and bridged supply reconcile across all contract paths.
- Duplicate, reordered, malformed, or unauthorized cross-chain messages cannot inflate aggregate supply.

### Price integrity

- Every price consumer resolves the intended source with correct decimals, freshness, and failure behavior.
- Stale, zero, extreme, manipulated, unavailable, or conflicting sources cannot silently produce unsafe value.
- Source admission and replacement cannot bypass safety assumptions.

### Rewards and reserves

- Points, rewards, bond value, and reserves cannot be double-created, double-claimed, unfairly reassigned, or stranded.
- Cleanup, migration, loss, and last-user behavior preserve earned and unearned balances according to intended rules.

### Failure atomicity and liveness

- Failed external calls do not leave partial internal state.
- One malicious or broken asset, vault, oracle, receiver, user, or keeper does not unexpectedly freeze unrelated contract state.
- Retriable paths remain retriable; terminal paths clean up fully.

### Contract migration continuity

- Vault and RipeGov position migration preserves ownership, assets, shares, indexes, locks, points, and rewards.
- Retry, partial batch, legacy routing, and cleanup cannot duplicate or forfeit state.

## 9. Findings and severity

New findings use `AUD-###`. Hypotheses use `AUD-HYP-###`; observations use `AUD-OBS-###`; flows use `AUD-FLOW-##`. Existing `F-`, `DV-`, and contract-relevant `RH-D` identifiers remain unchanged and receive linked current dispositions.

Every finding records:

- Root-cause contract, function, and exact source reference.
- Affected contracts and transaction flows.
- Violated invariant.
- Preconditions and attacker/privileged capabilities.
- Reproduction or decisive reasoning.
- Asset, accounting, authority, availability, or economic impact.
- Current configured exposure and realistically contract-reachable exposure.
- Confidence and unchecked assumptions.
- Remediation direction without editing production source during assessment.
- Final disposition and independent-retest evidence where applicable.

Severity:

- **Critical:** credible loss of most or all at-risk funds, unrestricted minting, systemic insolvency, or protocol-wide takeover.
- **High:** substantial loss, bad debt, permanent freezing, or major privilege compromise under realistic conditions.
- **Medium:** bounded loss, serious accounting or availability failure, or meaningful invariant violation requiring material preconditions.
- **Low:** limited-impact weakness with constrained exploitability.
- **Informational:** hardening or test-quality concern without demonstrated security impact.

Allowed dispositions:

- Open.
- Fix planned.
- Fixed pending retest.
- Fixed and verified.
- Partially fixed.
- Risk accepted.
- Not applicable.
- Duplicate.
- Re-affirmed.
- Challenged.
- Superseded.
- Disputed, with both rationales preserved.

A challenged or disputed inherited issue blocks any dependent conclusion until the disagreement is resolved or explicitly carried as unresolved risk.

## 10. Fresh-orchestrator kickoff

A fresh top-level audit task may begin from this document without inheriting the planning conversation. Use the following defaults unless the owner explicitly overrides them. An unavailable optional input does not block source review, test mapping, flow modeling, or unrelated audit work; record the assumption or gap and continue.

### Default operating decisions

1. **Candidate:** before assigning work, resolve the current live `rh` ref and record the exact starting commit/tree. Distinguish local docs-only plan commits from the production-contract snapshot. Do not pull, reset, switch, clean, or otherwise mutate an existing user worktree to obtain the candidate; use clean isolated worktrees or detached copies.
2. **Exposure:** assess both the current `rh` contract configuration and every realistically contract-reachable configuration or limit. Configuration and deployment artifacts are supporting evidence only, not separate audit workstreams.
3. **CCIP:** deeply review the Ripe-owned pool contracts and every inherited behavior reachable through their integration. Treat unchanged, pinned upstream CCIP code as a declared dependency boundary rather than duplicating a full upstream audit; expand review when Ripe changes it, relies on a subtle inherited behavior, or a finding path crosses it.
4. **Inherited evidence:** bind all repository-available prior findings, accepted risks, strict xfails, and relevant contract audit material at kickoff. Missing external reports do not stop the audit; list them as unavailable inputs and incorporate them if supplied later.
5. **Capacity:** use one fresh audit-lead/orchestrator plus three worker agents. The lead owns scope, the branch-change ledger, finding identity, cross-agent reconciliation, and final synthesis. Do not consume the lead slot with a full primary batch while coordination or reconciliation remains pending.
6. **Artifacts:** create one isolated audit workspace, record its absolute path, and give each worker a separate evidence subdirectory or worktree. Keep one canonical findings register, contract-ownership map, flow register, invariant matrices, and `rh` branch-change ledger under lead ownership. Raw outputs and security-sensitive findings remain local. Do not stage, commit, push, publish, or delete audit artifacts without owner authorization.
7. **Proof work:** agents may run existing tests and create assessment-only proof tests in their isolated audit worktrees. They must not edit production contracts. Proof tests remain uncommitted until the owner authorizes a commit; production fixes require a separately authorized remediation branch and independent retest.
8. **External actions:** no push, pull request, deployment, activation, release, external message, or repository cleanup is part of audit authorization. Preserve all pre-existing dirty, staged, untracked, and worktree state.

### Startup sequence

1. Read this plan completely before delegating.
2. Inspect repository and worktree state read-only, resolve the live `rh` candidate, and create a kickoff packet with the exact commit/tree, contract-source inventory, changed-source intake, inherited-issue inputs, audit workspace paths, agent roster, and unresolved assumptions.
3. Start Wave 0.5 before broad fan-out. Assign the three workers to the same calibration slice with non-competing responsibilities:
   - **Component/source worker:** manually model and review `contracts/vaults/modules/BasicVault.vy` and `contracts/vaults/SimpleErc20.vy`; own their source-level conclusions and candidate findings.
   - **Test/adversarial worker:** independently map existing evidence for the same contracts, identify semantic gaps, and design or run focused custody/receipt proofs without changing production source.
   - **Flow/permutation worker:** own `AUD-FLOW-01`, the deposit and exact-custody journey, including the applicable caller, amount, state, asset/dependency, ordering, failure-point, and economic permutations.
4. The audit lead reconciles the three packets into one accepted contract model, custody invariant, source-to-test record, flow model, and findings disposition. Preserve disagreements until resolved; do not average conflicting conclusions.
5. If calibration quality is acceptable, fan out through the waves in Section 7, prioritizing Batches 2, 5, 3, and 6 while retaining complete coverage of all batches and flows. Rotate workers between component, evidence, and flow responsibilities only with explicit ownership handoffs.
6. Apply the live-`rh` protocol in Section 2 throughout. Minor or localized `rh` changes reopen only affected evidence and never block unrelated agents. Notify the owner promptly of a credible Critical/High candidate, but continue safe unrelated audit work.
7. At every handoff, record exact source references, commands and outputs, assumptions, unchecked surface, affected flows/invariants, and the newest commit against which the conclusion remains valid.

### Authority and escalation boundary

The orchestrator should make ordinary audit-method decisions and keep work moving. Ask the owner only when progress requires production-contract edits, artifact commits/publication, external actions, a scope expansion beyond the contracts, or a business/risk-acceptance judgment. A branch advance, missing optional document, test failure, disputed hypothesis, or localized code change is an audit input to investigate, not by itself a reason to stop the program.

Everything else is subordinate to the contract audit. If a requested artifact or activity does not help answer a contract behavior, security, or economic-risk question, it should not consume audit time.

## 11. Baseline verification record

The 2026-08-12 refresh reproduced the following planning facts against live `rh` commit `6ce9c6a…` in a clean detached worktree:

- 62 production Vyper contracts are assigned exactly once across Batches 1–11, totaling 37,733 physical lines.
- Two Ripe-owned Solidity source files total 123 lines and define three pool contracts; 18 vendored Solidity dependency files total 1,792 lines.
- The Vyper surface contains 982 external functions, including 586 state-changing externals, 59 `@nonreentrant` externals, and four `@payable` externals.
- It contains 1,637 explicit `assert`/`raise` conditions and 1,509 `if`/`elif` branches.
- Live `master…rh` is `0/521`; 27 of 64 Ripe-owned production source files differ with 4,838 lines of churn.
- Seven Python test modules were added since the prior plan inventory: the tree now has 178 test-support Python files, including 158 `test_*.py` modules totaling 154,181 lines.
- Default collection is `3,605/3,899` selected; clearing repository `addopts` is `4,834/4,977` selected.
- The local-fork selection chooses `247/349` price-source nodes and `286/326` Endaoment nodes, omitting 142 nodes from both ordinary lanes.
- The suite carries one strict-xfail node, `DV-15`, from one source site.
- Marker-only collection selects four fuzz and ten gas nodes.
- Foundry `1.3.5-stable` compiled 21 Solidity files with solc `0.8.26`; `forge test --offline --root solidity` passed all seven focused tests in `RipeCcipBurnMintTokenPools.t.sol`. Compilation and seven focused tests are not a conclusion about the full inherited CCIP state machine.
- The live branch is 60 commits beyond the prior `02468586…` plan baseline; 11 production Vyper files and both owned Solidity files changed in that interval.

These facts organize the audit. They do not establish test health, absence of findings, deployed-state correctness, or contract safety.
