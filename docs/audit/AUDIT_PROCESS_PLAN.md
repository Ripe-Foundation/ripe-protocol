# Ripe Protocol Smart Contract Audit Plan

## Document status

- **Purpose:** define a contract-first security audit of the Ripe Protocol code on `rh`.
- **Planning baseline:** `rh` / `origin/rh` contract tree at commit `02468586d710e2cce2360c2bc07e94de6ebdab29`, tree `082a460d0ee190ac74a87ab29828d9c867ddff06`.
- **Contract-focused revision:** 2026-08-11.
- **Primary scope:** 62 production Vyper contracts, two Ripe-owned Solidity contracts, their imported modules and interfaces, the 18 vendored Solidity dependencies they compile against, and tests that provide evidence about those contracts.
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

- All 62 production Vyper contracts and both Ripe-owned Solidity contracts have exactly one primary component owner.
- Every state-changing external, privileged, `@nonreentrant`, and `@payable` path is manually reviewed and mapped to direct or clearly identified composed-test evidence.
- Every material contract transaction flow in Section 6 has one canonical end-to-end model and completed permutation review.
- Every applicable cross-cutting invariant in Section 8 is reconciled across all contracts that read or write it.
- Every confirmed issue has a stable identifier, severity, affected contracts and flows, proof, and disposition.
- Every inherited `F-`, `DV-`, strict-xfail, and relevant `RH-D` contract issue is rechecked against the exact audit candidate without losing its original identity.
- Remediated findings receive regression evidence and independent retest.
- Unreviewed contracts, functions, branches, flows, or assumptions are listed explicitly rather than hidden behind a green test suite.

An audit report may accurately finish while reporting unresolved findings. It may not describe contracts as ready or safe when a Critical or High issue remains unresolved.

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

The production Vyper surface at the planning baseline contains 973 external functions, including 582 state-changing externals, 59 `@nonreentrant` externals, and four `@payable` externals, plus 1,640 explicit `assert`/`raise` conditions and 1,521 `if`/`elif` branches.

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

- The default lean collection selects 3,550 tests and deselects 282.
- Clearing repository `addopts` selects 4,521 tests and deselects 143.
- Both ordinary lanes retain the default `--fork local` selection. It deselects 102 of 404 price-source nodes and 40 of 326 Endaoment nodes; clearing `addopts` is not an all-fork contract suite.
- The suite contains 22 strict-xfail nodes from 13 sites covering `DV-04`, `DV-05`, `DV-08`, `DV-09`, `DV-10`, `DV-13`, `DV-14`, `DV-15`, and the owner-deferred Uniswap manipulation issue.
- Marker-only collection selects four fuzz and five gas nodes. Marker names or green wrapper output must never be treated as evidence without a non-zero expected collection.
- The Solidity subtree has no Forge unit-test directory. `forge build --root solidity` establishes compilation only, not behavioral correctness.

Each batch must run its focused contract tests, relevant composed tests, and new adversarial proofs in an isolated environment. Record exact commands, selected/deselected/xfailed counts, seeds, and raw failures. Use separate processes when mutable global Boa state can leak between selections.

Quantitative coverage may help locate untouched code, but contract closure depends on semantic mapping and adversarial evidence.

## 5. Contract batches

The 62 primary non-mock Vyper contracts total 37,873 physical source lines. The two Ripe-owned Solidity contracts add 117 lines. The 18-file, 1,792-line vendored Solidity subtree is dependency source, not a separate infrastructure batch.

The delta columns compare `master` commit `91eda49…` with planning baseline `rh` commit `0246858…`. Delta concentration prioritizes review order; unchanged contracts remain in scope.

| Batch | Contract area | Primary Vyper | Owned Solidity | Raw primary lines | Changed Vyper | Churn | Risk emphasis |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | Shared modules and protocol state | 6 | 0 | 3,148 | 3 | 116 | State ownership, permissions, clock identity, shared invariants |
| 2 | Governance, registries, and configuration contracts | 13 | 0 | 10,600 | 6 | 1,589 | Dependency replacement, privileged configuration, unsafe combinations |
| 3 | Asset/vault registries and oracle contracts | 13 | 0 | 7,397 | 2 | 919 | Price integrity, admission, manipulation, failure handling |
| 4 | Tokens and cross-chain supply contracts | 5 | 2 | 1,224 | 1 | 16 | Supply, shares, signatures, bridge authority and conservation |
| 5 | Vaults and contract-level position migration | 9 | 0 | 4,171 | 5 | 1,380 | Custody, shares, rebases/loss, Stability Pool, migration |
| 6 | Teller entry points | 2 | 0 | 1,488 | 2 | 269 | Deposit/withdraw boundary, callbacks, actual receipt |
| 7 | Credit and debt lifecycle | 2 | 0 | 1,690 | 2 | 28 | Borrow/repay/redemption, interest, bad debt |
| 8 | Liquidation, auctions, and deleveraging | 3 | 0 | 2,854 | 1 | 33 | Insolvency, settlement, incentives, liveness |
| 9 | Endaoment contracts | 3 | 0 | 2,255 | 0 | 0 | Reserve custody, PSM economics, privileged transfers |
| 10 | Rewards and bonds | 3 | 0 | 2,082 | 2 | 248 | Accrual, claim, vesting, budgets, multi-user fairness |
| 11 | Governance and operational department contracts | 3 | 0 | 1,081 | 1 | 28 | Execution authority, compensation, fund/token issuance |

Twenty-five of 62 Vyper contracts differ between `master` and `rh`, with 4,199 added and 427 deleted lines. Batches 2, 5, 3, and 6 contain 89.9% of the changed production-contract churn. Review capacity should be weighted accordingly without treating unchanged source as audited.

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
- Configured and contract-reachable exposure, including debt limits and admission changes.

### Batch 3 — Asset/vault registries and oracle contracts

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
- Uniswap V2 provenance, reserve assumptions, snapshot cadence, poisoning, bootstrap, and stale handling.
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
- RipeHq mint-capability checks and pool authority.
- Cross-chain burn/mint conservation, remote identity, rate limits, pause, ownership, router/RMN, replay, and lane asymmetry.
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
- RipeGov permissions, lock paths, points, and rewards.
- Migration authorization, source/target validation, exact transfer/share preservation, list integrity, retries, atomicity, and cleanup.
- Fee-on-transfer, blacklist, reentrancy, and failed-transfer behavior.
- `DV-04`, `DV-05`, `DV-08`, `DV-09`, `DV-10`, `DV-13`, `DV-14`, and `DV-15` dispositions.

### Batch 6 — Teller entry points

**Primary contracts**

- `contracts/core/Teller.vy`
- `contracts/core/TellerUtils.vy`

**Contract focus**

- Deposit, withdrawal, rebalance, and housekeeping paths.
- Caller/user/beneficiary separation and delegated actions.
- Actual custody deltas and agreement with vault results.
- Ordinary user flows versus VaultMigrator-only paths.
- State ordering, callbacks, reentrancy, and partial failure.
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
- Same-block/reordered operations, oracle dependence, bad debt, and recovery.

### Batch 8 — Liquidation, auctions, and deleveraging

**Primary contracts**

- `contracts/core/AuctionHouse.vy`
- `contracts/core/AuctionHouseNFT.vy`
- `contracts/core/Deleverage.vy`

**Contract focus**

- Liquidation eligibility and account-health transitions.
- Auction creation, pricing, bidding, settlement, claim, and cancellation.
- Collateral/debt conservation using actual delivered custody.
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
| `AUD-FLOW-05` | Liquidation, auction, settlement, and bad-debt reconciliation | 8 | 1, 3–8, 10 |
| `AUD-FLOW-06` | Deleverage and residual account health | 8 | 1, 3–8 |
| `AUD-FLOW-07` | BasicVault and RipeGov position migration | 5 | 1, 2, 4–6, 10 |
| `AUD-FLOW-08` | Stability Pool deposit, claim, and liquidation absorption | 5 | 1, 3–5, 8, 10 |
| `AUD-FLOW-09` | Reward accrual, claim, cleanup, bond creation, vesting, and redemption | 10 | 1, 2, 4–7, 10 |
| `AUD-FLOW-10` | Endaoment reserve movement and PSM mint/redeem | 9 | 1–4, 7, 9 |
| `AUD-FLOW-11` | Price resolution, source failure, and asset/source admission | 3 | 2, 3, 5–9 |
| `AUD-FLOW-12` | Governance, timelock, department, and configuration mutation | 2 or 11 | 1–3, 11 |
| `AUD-FLOW-13` | CCIP burn, message validation, mint, and aggregate supply | 4 | 2, 4 |

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
- **State:** empty, first user, existing position, last user, threshold, insolvent, paused, legacy, migrated, partially configured, and recovered.
- **Asset/dependency:** standard, fee-on-transfer, rebasing/loss, blacklist, callback, failed/malformed return, deficient backing, stale/zero/extreme price, and outage.
- **Ordering:** repeat, reorder, retry, replay, same action block, expiry/cooldown boundary, front-run, and multi-user interleaving.
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

Start with at most five active component pods. Flow agents count against the real work-in-progress limit; they are not free extra capacity.

| Wave | Contract work | Exit condition |
| --- | --- | --- |
| 0 | Freeze the contract candidate; assign all 64 Ripe-owned production contracts; bind inherited contract issues; establish shared invariant and finding registers. | Zero unowned or double-owned contracts; starting charters accepted. |
| 0.5 | Calibrate on the Batch 5 `BasicVault.vy` / `SimpleErc20.vy` exact-custody slice and `AUD-FLOW-01`. | Source review, test mapping, adversarial proof, flow handoff, and synthesis quality are accepted before broad fan-out. |
| 1 | Run Batches 1–4 and continue Batch 5, weighting capacity toward Batches 2, 5, and 3. Start `AUD-FLOW-11`, `AUD-FLOW-12`, and `AUD-FLOW-13` when their component models stabilize. | Shared state, authority, price, token, vault, and migration models are stable. |
| 2 | Run Batches 6, 7, 10, and 11; activate deposit/withdraw, borrow/repay, reward, migration, and governance flows. Start Batch 9 as capacity permits. | User-entry, debt, reward, governance, and Endaoment contract models are stable. |
| 3 | Run and close Batch 8 plus liquidation/deleverage flows; execute protocol-wide invariant and adversarial campaigns. | All 11 batches, 13 flows, shared matrices, inherited issues, and findings reconcile against one exact candidate. |
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

## 10. Kickoff decisions

Only the following owner decisions are required before audit execution:

1. Exact contract commit/tree to audit.
2. Which network/configuration values and admitted contract features should be used when assessing realistic exposure.
3. Whether vendored CCIP dependencies receive independent source review or pinned-upstream reliance plus Ripe integration review.
4. Which prior audits, known issues, and accepted risks are supplied.
5. Maximum concurrent component and flow agents.
6. Where private findings, raw proof output, and the canonical findings register live.
7. Whether assessment-only proof tests may be committed before remediation authorization.

Everything else is subordinate to the contract audit. If a requested artifact or activity does not help answer a contract behavior, security, or economic-risk question, it should not consume audit time.

## 11. Baseline verification record

The contract-focused revision preserves the following previously reproduced planning facts for the bound `rh` tree:

- 62 production Vyper contracts, all assigned exactly once across Batches 1–11, totaling 37,873 physical lines.
- Two Ripe-owned Solidity contracts totaling 117 lines and 18 vendored Solidity dependency files totaling 1,792 lines.
- 973 Vyper external functions, including 582 state-changing externals, 59 `@nonreentrant` externals, and four `@payable` externals.
- 1,640 explicit `assert`/`raise` conditions and 1,521 `if`/`elif` branches.
- `master…rh` at the planning baseline is `0/462`; 25 production Vyper contracts differ with 4,626 lines of churn.
- Default collection is `3,550/3,832` selected; clearing repository `addopts` is `4,521/4,664` selected.
- The local-fork selection omits 142 price-source and Endaoment nodes from both ordinary lanes.
- The suite carries 22 strict-xfail nodes from 13 source sites.
- The Solidity contracts compile with solc `0.8.26`; compilation is not a security conclusion.

These facts organize the audit. They do not establish test health, absence of findings, deployed-state correctness, or contract safety.
