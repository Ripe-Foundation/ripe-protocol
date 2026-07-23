# Robinhood Chain Technical Deployment Summary

**Prepared:** 23 July 2026

**Ripe protocol baseline reviewed:** `91d846e8618fbaf3d8fb6770361b48d542d82a76`

**Source basis:** Hightop Notes research dated 22 July 2026 and decision-record updates/live verification through 23 July 2026

## Purpose

This document is the high-level engineering checklist for deploying the selected Ripe architecture on Robinhood Chain. It covers only work that belongs in or directly changes this repository: contracts, configuration, deployment and verification scripts, test infrastructure, and release artifacts.

Detailed designs, invariants, implementation notes, and test vectors should be written as separate task-level specifications before each workstream begins.

Off-repo liquidity provisioning, hosted monitoring and dashboards, alert response, operational runbooks, signer operations, partner coordination, and legal work are intentionally out of scope. Repository changes needed to expose state, verify deployments, or support those systems remain in scope.

## Controlling architecture

This checklist follows the selected architecture in [`random/hood/hood-chain-executive-summary.md`](https://github.com/mickhagen/hightop-notes/blob/main/random/hood/hood-chain-executive-summary.md) in the separate Hightop Notes repository, not the larger federated architecture proposed in that repository's `random/hood/hood-chain.md` research document.

The primary implementation constraint is one canonical, chain-portable smart-contract codebase and release line. Do not create a Robinhood-only protocol branch, duplicate the contract suite, or add Robinhood-specific variants of core contracts. Except for `DefaultsRobinhood`, changes to Ripe-owned production contracts should be shared improvements that remain deployable on Base, Robinhood, and future EVM chains. Put chain differences in defaults, constructor arguments, governed parameters, address/configuration data, and migration scripts rather than in duplicated contracts or `chain.id` conditionals.

- Deploy a full, chain-local Ripe credit system on Robinhood.
- Keep positions, collateral, pricing, liquidation, parameters, and governance local to each chain.
- Bridge only GREEN and RIPE between Base and Robinhood.
- Use standard Chainlink CCIP BurnMint pools with the smallest RipeHq compatibility layer possible; deploy the same Ripe-owned pool implementation on both chains with different network configuration.
- If SavingsGreen/sGREEN is deployed, keep it chain-local.
- Use official Chainlink feeds for supported Stock Tokens without applying the Robinhood UI/corporate-action multiplier a second time.
- Use USDG as the Robinhood PSM reserve if an approved USDG price path is available.
- Reuse the existing liquidation and insurance architecture.
- Disable Base-only and price-dependent integrations that do not have valid Robinhood replacements.
- Accept the selected design's documented issuer-control, stale-market-price, local-governance-drift, and shared-GREEN-risk consequences.

If the team reopens the federated architecture, global issuance allocators, custom bridge accounting, cross-chain governance, an issuer-aware vault, session-aware pricing, or special liquidation recovery, this checklist must be re-scoped before implementation continues.

## How to read the component matrix

The Base-versus-Robinhood matrix is a deployment and configuration inventory, not a plan for separate contract forks. `Reused unchanged` is one status.

| Status | Meaning under the shared-contract rule |
|---|---|
| `reused unchanged` | Deploy or use the same canonical implementation without changing its source. Constructor arguments, defaults, addresses, and governed values may differ by chain. |
| `modified` | Change the canonical shared implementation once to remove a chain assumption or make behavior configurable. The resulting code must support Base and Robinhood and pass both test profiles; do not create a Robinhood-only version. Subject to the Phase-0 live-version policy, an existing Base deployment may remain on older bytecode even though the canonical source has advanced. |
| `replaced` | Fulfill a component's role with a different existing or newly shared implementation because the original component is intrinsically tied to an unavailable dependency. Prefer a generic reusable replacement, not a Robinhood-specific copy. |
| `disabled` | Keep the shared code available but omit the component, leave it unregistered, or turn its feature flag off because its dependency or price source is unavailable on Robinhood. |
| `deferred` | Keep the component outside the initial launch scope until a later specification and enablement gate are approved. |

## Critical path

```text
Freeze release and inventory
        |
        v
Resolve shared-source, live-version, clock, CCIP, vault, sGREEN, and USDG choices
        |
        v
Prove minimal GREEN bridge and Stock Token transferability
        |
        v
Generalize shared contracts; add Robinhood defaults and deployment tooling
        |
        v
Pass unit, deployment, cross-chain, and adversarial tests
        |
        v
Complete full-stack testnet deployment and soak
        |
        v
Freeze and execute restricted mainnet release
```

## 0. Freeze scope and resolve blocking choices

- [ ] Pin the exact release commit and regenerate the `block.number` inventory from that commit.
- [ ] Commit to one canonical contract source and release line for Base and Robinhood; separate chain configuration and migration directories must not become separate protocol branches.
- [ ] Create a Base-versus-Robinhood component matrix using the definitions above: `reused unchanged`, `modified`, `replaced`, `disabled`, or `deferred`.
- [ ] Freeze the contracts that will be deployed on Robinhood and the Base-only contracts that will be omitted.
- [ ] Approve the live-version policy for every `modified` or `replaced` component while retaining one canonical source:
  - require the live Base deployment to migrate before Robinhood launches;
  - permit temporary deployed-version drift with an owner, bounds, and convergence plan; or
  - explicitly accept permanent live-version divergence only where a component is immutable or migrating a custody-bearing deployment would be unacceptably risky.
- [ ] Record every permanent live-version exception in the component matrix with its technical cause, risk, governance approval, and operational implications. This is an exception to live-bytecode parity, not permission to create chain-specific source.
- [ ] If temporary drift makes Robinhood the first production deployment of generalized shared-contract revisions while Base retains its battle-tested bytecode, explicitly approve that rollout posture and apply the corresponding review, testnet, and soak requirements.
- [ ] Approve the shared clock posture: retain `block.number` where its semantics are acceptable on both chains, move cadence assumptions into per-chain parameters, and change hardcoded or same-number behavior in the canonical shared contracts.
- [ ] Resolve the deployable Stock Token vault path:
  - nominal-balance `SimpleErc20`; or
  - share-based `RebaseErc20`/`SharesVault`.
- [ ] Decide whether to deploy SavingsGreen/sGREEN on Robinhood; if it is omitted, identify the resulting Stability Pool, insurance, rewards, and lifecycle-test changes in the component matrix.
- [ ] Resolve the USDG price path:
  - existing Chainlink feed;
  - existing reviewed adapter;
  - new fixed/capped adapter with explicit depeg behavior; or
  - PSM disabled.
- [ ] Pin the supported CCIP contracts release and decide how its Solidity contracts and artifacts will be built, tested, and deployed from this currently Vyper-focused repository.
- [ ] Prefer Chainlink-assisted registration so Robinhood can deploy the same existing GREEN and RIPE token implementations without adding a Robinhood-only `getCCIPAdmin()` change.
- [ ] Confirm the supported registration path with Chainlink. If `getCCIPAdmin()` is unavoidable, design it as part of a new shared token revision usable on every chain and explicitly resolve the resulting Base migration, temporary live-version mismatch, or permanently accepted live divergence for the immutable Base tokens.
- [ ] Prove the two highest-uncertainty paths before building the full deployment:
  - a Stock Token can transfer into and back out of a third-party test contract; and
  - test GREEN can bridge Base Sepolia → Robinhood testnet → Base Sepolia through the proposed RipeHq-authorized pool path.

**Exit condition:** the release commit, shared-source and live-version policy, component inventory and any permanent live-version exceptions, clock posture, sGREEN decision, vault/CCIP/USDG choices, and minimal testnet bridge design are approved.

## 1. Add Robinhood deployment support

- [ ] Add explicit Robinhood mainnet and testnet targets to the migration CLI and network configuration.
- [ ] Add Robinhood chain IDs, RPC selection, explorer/verification support, gas settings, confirmation policy, and environment-variable handling without inheriting Base/Alchemy/Basescan assumptions.
- [ ] Add a dedicated Robinhood blueprint containing only verified Robinhood addresses:
  - governance and operational accounts;
  - canonical USDG;
  - launch Stock Tokens and Chainlink feeds;
  - CCIP Router, chain selector, Token Admin Registry, and pool configuration;
  - intentionally disabled integrations; and
  - Robinhood-specific parameters.
- [ ] Add `DefaultsRobinhood` or an equivalent generated defaults artifact rather than modifying `DefaultsBase` in place.
- [ ] Treat `DefaultsRobinhood` as the intended chain-specific contract exception: it supplies Robinhood values and inventory but must not contain divergent protocol logic.
- [ ] Create separate Robinhood testnet and mainnet migration trees and manifest histories.
- [ ] Establish the Robinhood release-artifact convention: define the `migration_history/` paths, which manifests and verification outputs are committed, and where any evidence too large or sensitive for Git is retained.
- [ ] Make the Robinhood migration sequence deploy the same canonical contract implementations selected for Base, plus only the explicitly approved shared additions such as CCIP pools, and configure all registries, Departments, Switchboards, assets, price sources, and governance roles.
- [ ] Make every omitted integration explicit in the deployment manifest; do not silently substitute zero addresses where downstream code expects a live contract.
- [ ] Add post-deployment verification that checks deployed bytecode, constructor arguments, registry IDs, Department mint permissions, governance ownership, token/feed mappings, feature flags, and parameter values.
- [ ] Ensure contract export/ABI and explorer-verification tooling supports every new Robinhood and CCIP contract.
- [ ] Prevent Robinhood manifests from containing accidental Base token, oracle, DEX, yield, treasury, or Underscore addresses.

**Exit condition:** a clean, repeatable local/fork deployment produces the intended Robinhood inventory and passes all post-deployment assertions.

## 2. Parameterize block-based behavior for Base and Robinhood

Robinhood's EVM `block.number` advances as an approximate Ethereum L1-height estimate. Many Robinhood L2 blocks may share one number, followed by delayed or multi-number jumps. Most Ripe durations and rates are already supplied through constructors, Mission Control, or Defaults; those should use different Base and Robinhood values while the consuming contract stays identical. The first shared-contract changes should remove the remaining hardcoded cadence assumptions and generalize same-number behavior. Do not mechanically convert every site to timestamps or add chain-specific branches.

- [ ] Classify every retained `block.number` use as:
  - configurable economic duration;
  - hardcoded economic duration;
  - per-number rate or reward accrual;
  - true same-number guard; or
  - telemetry only.
- [ ] Define Base and Robinhood values for all block-denominated defaults, including governance and registry timelocks, borrow/PSM intervals, auctions, locks, rewards, cooldowns, and price snapshots.
- [ ] Recalculate per-number rates, especially RIPE rewards, so each chain preserves the intended time-based economics through configuration.
- [ ] Move hardcoded cadence assumptions out of shared contracts and into constructor, storage, governance, or Defaults-supplied parameters, beginning with `Lootbox.ONE_DAY`.
- [ ] Replace the duplicated `7_200` maximum deleverage cooldown constants in `Deleverage` and `SwitchboardDelta` with one consistent configurable design. Before selecting each chain's value, resolve whether the intended wall-clock maximum is approximately four hours, as `7_200` produces at Base's roughly two-second cadence, or one day, as the existing 12-second-block comment states.
- [ ] Resolve `Ledger`'s one-action-per-`block.number` rule as a chain-portable security policy. If it cannot safely tolerate repeated Robinhood numbers, change the shared guard for both chains rather than creating a Robinhood variant.
- [ ] Review repeated and jumping numbers across:
  - token, governance, registry, and Switchboard timelocks;
  - borrow and PSM interval capacity;
  - auction start/end and discount progression;
  - deleverage cooldowns;
  - RipeGov locks and points;
  - Lootbox points, rewards, and send intervals; and
  - any retained price-source snapshots.
- [ ] Add a checked inventory or CI guard so new, unreviewed block-number or chain-cadence dependencies cannot enter the shared contract surface.
- [ ] Run the same contract artifacts under a Base clock profile and a Robinhood clock profile that holds `block.number` constant across many transactions, advances it by one, and jumps it by several increments.
- [ ] Confirm that RipeHq and registry timelocks behave correctly before using them to register CCIP pools as Departments.

**Exit condition:** every deployed block-number dependency has one shared implementation, approved per-chain parameters, and passing Base plus repeated/jumping-number Robinhood tests.

## 3. Implement GREEN and RIPE CCIP integration

- [ ] Add a pinned, reproducible CCIP build and test dependency instead of relying on unversioned external artifacts.
- [ ] Implement the minimal Department-compatible BurnMint pool layer:
  - GREEN pool exposes `canMintGreen() == true` and no RIPE mint capability;
  - RIPE pool exposes `canMintRipe() == true` and no GREEN mint capability;
  - the pool remains the direct caller of `GreenToken.mint()` or `RipeToken.mint()`; and
  - standard CCIP Router, remote-pool, decimal, burn/mint, and rate-limit behavior remains intact.
- [ ] Deploy the same GREEN pool implementation on Base and Robinhood and the same RIPE pool implementation on Base and Robinhood; keep Router, selector, remote-pool, ownership, and rate-limit differences in configuration.
- [ ] Do not insert a standalone mint adapter that is not the direct token-mint caller; it will not satisfy the current RipeHq authorization path.
- [ ] Use assisted registration with the existing shared token implementation if Chainlink supports it. If Phase 0 requires `getCCIPAdmin()`, implement and test a shared token revision rather than a Robinhood-only token contract.
- [ ] Add deployment/configuration steps for the Base and Robinhood pools:
  - token-administrator and pool registration;
  - RipeHq Department registration;
  - remote token and pool mappings;
  - Base↔Robinhood selectors and Routers;
  - 18-decimal normalization;
  - conservative inbound and outbound rate limits; and
  - governance ownership and emergency administration.
- [ ] Add tests that prove each pool has exactly one intended RipeHq mint capability and cannot mint through any alternate caller.
- [ ] Add bidirectional GREEN and RIPE bridge tests that reconcile source burns, destination mints, in-flight messages, and total cross-chain supply.
- [ ] Add negative tests for wrong Router, selector, token, remote pool, decimal configuration, Department permission, and governance owner.
- [ ] Exercise rate-limit exhaustion, paused/resumed pools, delayed delivery, and standard CCIP manual execution.
- [ ] Test Robinhood collateral → GREEN mint → bridge to Base → Base PSM redemption, including the fact that rate limits constrain propagation speed but do not cap cumulative Robinhood credit exposure.
- [ ] Enforce CCIP as the sole active minting bridge; any later bridge migration must pause CCIP, settle in-flight messages, reconcile supply, and revoke the old mint authority first.

**Exit condition:** both tokens bridge in both directions through shared pool implementations, all permissions are minimal, and cross-chain supply reconciles under normal and recovery flows.

## 4. Configure Stock Token collateral and pricing

- [ ] Add a reusable transferability probe for each candidate Stock Token and run it against the exact launch contract.
- [ ] Finish the `SimpleErc20` versus `RebaseErc20`/`SharesVault` comparison:
  - `SimpleErc20` preserves nominal balances after an issuer burn and can create persistent phantom collateral plus first-withdrawer advantage;
  - `RebaseErc20` uses `SharesVault` live-balance accounting and socializes a custody loss pro rata.
- [ ] Test the chosen vault's accepted behavior for donations, measured deposits, total-balance loss, zero-balance recovery, blocked transfers, withdrawals, and internal-share liquidation.
- [ ] If the chosen behavior is unacceptable, stop and write a separate vault-change specification before modifying custody code.
- [ ] Add only canonical Stock Token addresses with exact official Chainlink feed mappings and verified decimals.
- [ ] Confirm through tests that `ChainlinkPrices` and `PriceDesk` normalize token/feed decimals correctly and do not apply `uiMultiplier()` or any equivalent multiplier a second time.
- [ ] Define and test the chosen staleness configuration across regular, extended, overnight, weekend, holiday, halt, and reopening-gap scenarios.
- [ ] Configure conservative per-user deposit limits, global deposit limits, LTVs, liquidation thresholds, debt ceilings, fees, and auction parameters.
- [ ] Set `AssetConfig.canRedeemCollateral = false` for every Stock Token, then verify `MissionControl.getRedeemCollateralConfig()` returns `canRedeemCollateralAsset == false` so CreditRedeem cannot extract it.
- [ ] Ensure Stock Token configuration does not route assets into Base treasury, Endaoment partner-liquidity, Curve, Aerodrome, Underscore, or yield integrations; keep `shouldSwapInStabPools = false` unless governance deliberately accepts Stability Pool custody of pausable, blocklistable, and administratively burnable Stock Tokens.
- [ ] Add issuer-control mocks and adversarial tests for token pause, account/vault/liquidator blocklist, administrative burn, forced transfer/redeem behavior, oracle pause, and implementation upgrade.
- [ ] Verify that deposits, withdrawals, borrowing, repayment, auctions, and liquidations either succeed or fail exactly as the selected risk posture documents; do not silently add special recovery behavior.

**Exit condition:** the chosen vault, feed, asset flags, and risk parameters have a complete behavioral test record for normal operation and issuer-controlled failures.

## 5. Configure the USDG PSM

- [ ] Deploy `EndaomentPSM` with canonical six-decimal USDG as its reserve asset.
- [ ] Keep the existing USDC-named storage, methods, and events only if passing USDG does not create unsafe logic or operational ambiguity.
- [ ] Configure the yield lego ID and yield-vault address as disabled; no Base USDC yield route may remain reachable.
- [ ] Add USDG to `PriceDesk` through the approved Phase-0 price path.
- [ ] If a new fixed/capped adapter is selected, specify and test depeg direction, price bounds, stale/failure behavior, governance controls, and pause behavior in a separate implementation spec.
- [ ] If no approved USDG price path exists, deploy the PSM disabled or omit it according to the frozen inventory.
- [ ] Configure deliberately small mint/redeem interval limits, fees, allowlists if used, and initial feature flags.
- [ ] Test six-decimal mint and redemption math, fees, interval rollover under Robinhood block behavior, insufficient reserves, price failure/depeg, and disabled yield calls.

**Exit condition:** USDG pricing and PSM behavior are reproducible and tested, or every PSM mint/redeem path is verifiably disabled.

## 6. Isolate or disable unsupported integrations

- [ ] Audit constructor, registry, and runtime assumptions for every Base-specific integration in the selected Robinhood inventory.
- [ ] Omit or disable unsupported Curve and Aerodrome price/liquidity contracts.
- [ ] Omit or disable Base USDC, Base yield strategies, and unsupported yield legos.
- [ ] Omit or disable Underscore vault detection, hooks, reward transfers, registry dependencies, and bypasses.
- [ ] Separate `EndaomentPSM`, which remains conditionally in scope for USDG, from Base-only Endaoment treasury and partner-liquidity routes.
- [ ] Disable GREEN- and RIPE-price-dependent features until Robinhood has an approved local liquidity source and price adapter.
- [ ] Preserve a deferred re-enable path for GREEN- and RIPE-price-dependent features through a separate adapter specification covering the reference market, minimum liquidity/observation requirements, pricing method, and manipulation/thin-market tests.
- [ ] Ensure omitted contracts and zero-address configuration fail closed without breaking unrelated deposit, borrow, repay, liquidation, governance, or bridge flows.
- [ ] Add regression tests proving disabled integrations cannot be reached accidentally.

**Exit condition:** the Robinhood deployment contains no hidden Base dependency, and every disabled path fails closed without disabling the selected core protocol.

## 7. Build the Robinhood validation suite

- [ ] Add Base and Robinhood environment profiles that deploy the same shared contract artifacts with different defaults and can model each chain's `block.number` behavior.
- [ ] Add unit and property tests for every shared contract change, including cadence parameterization, CCIP capability boundaries, and any shared token-admin or USDG adapter code.
- [ ] Add a clean-deployment test that executes the full Robinhood migration sequence and validates the resulting manifest and onchain configuration.
- [ ] Add a full local protocol lifecycle test: deposit Stock Token, borrow GREEN, repay, withdraw, liquidate, exercise the selected Stability Pool/insurance path, settle any resulting bad debt through the existing accounting and repayment path, and distribute RIPE rewards.
- [ ] Add two-chain integration tests for both token bridges and cross-chain supply reconciliation.
- [ ] Add failure tests for stale feeds, reopening gaps, issuer controls, insufficient liquidation liquidity assumptions, PSM depletion/depeg, CCIP delays, bad remote configuration, rate limits, and separate Base/Robinhood emergency actions.
- [ ] Execute a parameter change end-to-end through Robinhood-local governance, including its timelock and resulting onchain configuration.
- [ ] Verify Base governance messages and cross-chain dispatchers have no privileged execution path on Robinhood; any shared signer addresses still act only through Robinhood-local governance.
- [ ] Add drift detection that distinguishes expected configuration differences from implementation differences and fails any unapproved Base-versus-Robinhood contract-version divergence.
- [ ] Keep the complete Base test suite passing; Robinhood work must not silently change Base economic timing or permissions.
- [ ] Add post-deployment smoke scripts for a small borrow/repay, PSM mint/redeem, liquidation, and GREEN/RIPE bridge in both directions.

**Exit condition:** contract, deployment, regression, cross-chain, and adversarial tests pass from a clean checkout with reproducible configuration.

## 8. Execute the technical release workflow

### Phase A — implementation freeze

- [ ] Approve the task-level specs produced from sections 1–7.
- [ ] Freeze one canonical contract implementation set, the CCIP version, configuration schema, deployment inventory, and address sources.
- [ ] Record which components require live Base parity before Robinhood launch, which temporary live-version differences governance has accepted with convergence plans, and which immutable or custody-bearing components have approved permanent live-version divergence.
- [ ] Re-verify all external addresses and chain metadata instead of copying the research snapshot.

### Phase B — full-stack testnet

- [ ] Deploy the complete selected protocol inventory on Robinhood testnet.
- [ ] Deploy and register GREEN and RIPE pools on Base Sepolia and Robinhood testnet.
- [ ] Configure USDG/test reserve, one candidate Stock Token, its Chainlink feed, the selected SavingsGreen/Stability Pool path, local governance, roles, and conservative parameters.
- [ ] Run every post-deployment assertion, lifecycle smoke test, bridge reconciliation, and focused failure test.
- [ ] Keep the deployment live long enough to observe real Robinhood block progression, feed updates, CCIP delivery/manual execution, and permissioned maintenance flows.
- [ ] Record the exact deployed bytecode, addresses, constructor arguments, roles, config, and test evidence.

### Phase C — production candidate

- [ ] Rebuild from the frozen commit and dependency lockfiles.
- [ ] Repeat focused security review for all changed contracts and deployment scripts.
- [ ] Produce the final mainnet parameter and address manifest.
- [ ] Rehearse deployment, verification, role transfer, pause, and rollback/abort procedures against a production-like environment.
- [ ] Require every technical launch gate below before broadcasting the mainnet deployment.

### Phase D — restricted mainnet

- [ ] Deploy and verify the local Robinhood protocol.
- [ ] Complete production CCIP token/pool registration and RipeHq Department permissions.
- [ ] Verify very small GREEN and RIPE transfers in both directions and reconcile supply.
- [ ] Enable only the approved USDG and Stock Token paths with small limits.
- [ ] Confirm CreditRedeem, unsupported integrations, and unpriced features remain disabled.
- [ ] Archive the final manifests and post-deployment verification output using the `migration_history/` and release-evidence convention established in section 1.

## Technical launch gates

- [ ] Release commit, dependency versions, inventory, and parameter/address manifests are frozen.
- [ ] No Robinhood-only protocol branch or core-contract variant exists; `DefaultsRobinhood` and network deployment/configuration artifacts contain the intended chain differences.
- [ ] Every deployed block-number dependency is implemented once and tested under both Base and Robinhood semantics.
- [ ] Robinhood deployment and verification tooling works from a clean checkout.
- [ ] GREEN and RIPE pool code has minimal, token-specific RipeHq permissions.
- [ ] Production token and pool registration is complete on both chains.
- [ ] GREEN and RIPE bridge successfully in both directions and total supply reconciles.
- [ ] The Robinhood-mint → CCIP → Base PSM propagation test passes.
- [ ] USDG pricing and PSM behavior are validated, or the PSM is verifiably disabled.
- [ ] The selected SavingsGreen, Stability Pool, and insurance path is deployed or intentionally omitted according to the component matrix and passes its lifecycle tests.
- [ ] Each launch Stock Token has a verified contract/feed mapping, selected vault path, disabled CreditRedeem, and issuer-failure test record.
- [ ] No unsupported Base integration is reachable.
- [ ] Full-stack testnet, adversarial tests, Base regression tests, and deployment rehearsal pass.
- [ ] Every live Base-versus-Robinhood implementation-version difference is explicitly approved and recorded in the component matrix: temporary differences are bounded and tracked to convergence; permanent differences are limited to components that are immutable or whose custody-bearing deployment would be unacceptably risky to migrate, and include their technical justification and accepted risk.
- [ ] Exact deployed code, roles, registry entries, feature flags, and parameters match the approved manifests.

## Explicit technical non-goals

The selected release does not include:

- a separate Robinhood protocol branch, duplicated core-contract suite, or Robinhood-only version of a shared Ripe contract;
- `chain.id`-based behavior branches in core protocol logic where defaults, constructor arguments, storage, or governance parameters can express the difference;
- global onchain GREEN quota or RIPE emission allocators;
- custom bridge sender/receiver, quarantine, claim, checkpoint, conservation-counter, or incident-controller contracts;
- cross-chain governance messages, executors, receipts, or proof fallbacks;
- RIPE origin tracking, voting quarantine, or repatriation caps;
- a new issuer-aware Stock Token custody vault unless the Phase-0 vault decision reopens scope;
- session-aware Stock Token pricing or automatic reduce-only modes;
- special frozen-liquidation, recovery-claim, or batch-isolation machinery;
- bridging sGREEN;
- a second active minting bridge;
- migrating the existing Base GREEN or RIPE tokens unless assisted CCIP registration proves unavailable; or
- converting every `block.number` use to timestamps.

## Follow-on specification split

Create these as separate documents when the corresponding workstream starts:

- Robinhood deployment inventory and Base-difference matrix.
- Shared-contract block-clock parameterization and dual-chain test specification.
- CCIP pool, permission, registration, and supply-reconciliation specification.
- Stock Token vault, oracle, configuration, and failure-behavior specification.
- USDG PSM and price-adapter specification.
- GREEN/RIPE local market-price adapter and feature re-enable specification.
- Unsupported-integration disablement matrix.
- Robinhood test and deployment-verification plan.
