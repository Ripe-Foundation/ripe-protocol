# Robinhood Chain Technical Deployment Summary

**Prepared:** 23 July 2026

**Ripe protocol baseline reviewed:** `91d846e8618fbaf3d8fb6770361b48d542d82a76`

**Source basis:** Hightop Notes research dated 22 July 2026 and decision-record updates/live verification through 23 July 2026

**Checklist reconciliation baseline:** `dd51c637f1462bede7529a53427bfb4327dbfb12` on 24 July 2026

**Minimum-contract-change directive:** 24 July 2026 — implementation necessity
is being re-evaluated in
[`minimal-contract-change-reassessment.md`](rh/minimal-contract-change-reassessment.md)

A checked planning or evidence item means that decision or artifact is complete at the reconciliation baseline. It does not imply that dependent implementation, deployment, activation, validation, or launch gates are complete unless the item itself says so. Any later reconciliation that closes or reopens an item must update the reconciliation baseline in the same commit.

## Purpose

This document is the high-level engineering checklist for deploying the selected Ripe architecture on Robinhood Chain. It covers only work that belongs in or directly changes this repository: contracts, configuration, deployment and verification scripts, test infrastructure, and release artifacts.

Detailed designs, invariants, implementation notes, and test vectors should be written as separate task-level specifications before each workstream begins.

Off-repo liquidity provisioning, hosted monitoring and dashboards, alert response, operational runbooks, signer operations, partner coordination, and legal work are intentionally out of scope. Repository changes needed to expose state, verify deployments, or support those systems remain in scope.

## Controlling architecture

This checklist follows the selected architecture in [`random/hood/hood-chain-executive-summary.md`](https://github.com/mickhagen/hightop-notes/blob/main/random/hood/hood-chain-executive-summary.md) in the separate Hightop Notes repository, not the larger federated architecture proposed in that repository's `random/hood/hood-chain.md` research document.

The primary implementation constraint is one canonical, chain-portable smart-contract codebase and release line. Do not create a Robinhood-only protocol branch, duplicate the contract suite, or add Robinhood-specific variants of core contracts. Except for `DefaultsRobinhood`, changes to Ripe-owned production contracts should be shared improvements that remain deployable on Base, Robinhood, and future EVM chains. Put chain differences in defaults, constructor arguments, governed parameters, address/configuration data, and migration scripts rather than in duplicated contracts or `chain.id` conditionals.

The second controlling constraint is to make the absolute minimum necessary
production smart-contract changes for the initial Robinhood release. Reuse
existing source first; then prefer `DefaultsRobinhood`, constructor or governed
values, omission, disabled features, explicit risk acceptance, tests, tooling,
and deployment assertions. A shared improvement is not automatically required
merely because it is cleaner or more portable. Before any production-contract
change, present the owner with the no-source-change path, the concrete risk of
accepting it, the smallest mitigation, and the incremental risk introduced by
new code. The owner must explicitly reject the acceptable no-change paths
before implementation proceeds.

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
Resolve minimal inventory, accepted risks, CCIP, vault, sGREEN, and USDG choices
        |
        v
Prove minimal GREEN bridge and Stock Token transferability
        |
        v
Reuse contracts unchanged; add defaults/tooling; approve only indispensable changes
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

- [ ] Pin the exact release commit for implementation and release freeze.
- [x] Regenerate and review the `block.number` inventory at the audited planning baseline.
  - Evidence: [`block-number-inventory.md`](rh/block-number-inventory.md) and [`component-matrix.md`](rh/component-matrix.md).
- [x] Commit to one canonical contract source and release line for Base and Robinhood; separate chain configuration and migration directories must not become separate protocol branches.
  - Decision evidence: [`component-matrix.md`](rh/component-matrix.md) and [`shared-block-clock-specification.md`](rh/shared-block-clock-specification.md).
- [ ] Reassess every `modified` or `replaced` component under the
  minimum-contract-change directive. For each one, document the unchanged,
  configuration-only, disabled, or omitted alternative; the concrete accepted
  risk; and why any remaining source change is indispensable.
  - Working record:
    [`minimal-contract-change-reassessment.md`](rh/minimal-contract-change-reassessment.md).
- [x] Create a Base-versus-Robinhood component matrix using the definitions above: `reused unchanged`, `modified`, `replaced`, `disabled`, or `deferred`.
  - Evidence: [`component-matrix.md`](rh/component-matrix.md).
- [ ] Freeze the contracts that will be deployed on Robinhood and the Base-only contracts that will be omitted.
- [ ] Approve the live-version policy for every `modified` or `replaced` component while retaining one canonical source:
  - require the live Base deployment to migrate before Robinhood launches;
  - permit temporary deployed-version drift with an owner, bounds, and convergence plan; or
  - explicitly accept permanent live-version divergence only where a component is immutable or migrating its state-bearing or custody-bearing deployment would be unacceptably risky.
  - **CM-008 decision recorded:** leave the deployed Base Ledger untouched
    indefinitely because its state migration is unacceptably risky; Robinhood
    will be the first deployment of the revised portable Ledger. This is a
    live-bytecode exception, not a source fork.
- [ ] Record every permanent live-version exception in the component matrix with its technical cause, risk, governance approval, and operational implications. This is an exception to live-bytecode parity, not permission to create chain-specific source.
- [ ] If temporary drift makes Robinhood the first production deployment of generalized shared-contract revisions while Base retains its battle-tested bytecode, explicitly approve that rollout posture and apply the corresponding review, testnet, and soak requirements.
- [x] Approve the shared clock analysis posture: retain `block.number` where its
  semantics are acceptable and use per-chain parameters where required.
  Production changes previously proposed for hardcoded or same-number behavior
  are reopened for necessity review under the 24 July minimum-change directive.
  - Decision evidence: [`shared-block-clock-specification.md`](rh/shared-block-clock-specification.md),
    [`block-clock-validation-plan.md`](rh/block-clock-validation-plan.md), and
    [`minimal-contract-change-reassessment.md`](rh/minimal-contract-change-reassessment.md).
- [ ] Resolve the deployable Stock Token vault path through Track 8:
  - treat Stock Tokens as mandatory for initial launch;
  - specify the smallest demonstrably sufficient shared containment patch;
  - prove its backing, settlement, debt, custody, and issuer-control invariants;
    and
  - require a separate necessity decision before any broader corrected-share,
    reward, Ledger, or migration redesign.
- [ ] Decide whether to deploy SavingsGreen/sGREEN on Robinhood; if it is omitted, identify the resulting Stability Pool, insurance, rewards, and lifecycle-test changes in the component matrix.
- [x] Resolve the USDG price path:
  - **Selected:** use the existing official Chainlink USDG/USD feed through the shared `ChainlinkPrices`/`PriceDesk` path.
  - Existing-adapter and new-adapter alternatives are not required for the selected path.
  - The PSM deployment and activation posture remains separately gated.
  - Decision evidence: [`usdg-psm-decision.md`](rh/usdg-psm-decision.md).
- [ ] Pin the supported CCIP pool/API reference and decide how the selected
  thin Solidity subclasses and artifacts will be dependency-locked, built,
  delta-tested, verified, and deployed with exact compiler/EVM settings.
  - Owner decision required before implementation: authorize or reject the
    bounded H-12 Solidity build/test/artifact package. The reference contract,
    scratch builds, and independent reference review do not authorize adding
    production dependencies or tooling.
- [x] Select Chainlink-assisted registration as the preferred path so Robinhood
  can deploy the same existing GREEN and RIPE token implementations without
  adding a Robinhood-only `getCCIPAdmin()` change.
  - This checkbox closes only Ripe's internal topology preference; it does not
    establish Chainlink support or authorize registration. Decision evidence:
    [`ccip-integration-decision.md`](rh/ccip-integration-decision.md).
    Chainlink confirmation remains open below.
- [ ] Confirm the supported registration path with Chainlink. If `getCCIPAdmin()` is unavoidable, design it as part of a new shared token revision usable on every chain and explicitly resolve the resulting Base migration, temporary live-version mismatch, or permanently accepted live divergence for the immutable Base tokens.
- [ ] Prove the two highest-uncertainty paths before building the full deployment:
  - a Stock Token can transfer into and back out of a third-party test contract; and
  - test GREEN can bridge Base Sepolia → Robinhood testnet → Base Sepolia through the proposed RipeHq-authorized pool path.

**Exit condition:** the release commit, minimal unchanged deployment inventory,
accepted-risk register, shared-source/live-version policy, any indispensable
contract changes, sGREEN decision, vault/CCIP/USDG choices, and minimal testnet
bridge design are approved.

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

Robinhood's EVM `block.number` advances as an approximate Ethereum L1-height
estimate. Many Robinhood L2 blocks may share one number, followed by delayed or
multi-number jumps. Most Ripe durations and rates are already supplied through
constructors, Mission Control, or Defaults; those should use different Base and
Robinhood values while the consuming contract stays identical. Hardcoded or
same-number behavior does not automatically justify a source change when the
affected feature can safely remain disabled or its risk can be explicitly
accepted. Do not mechanically convert sites to timestamps, generalize dormant
features for future use, or add chain-specific branches.

- [ ] Classify every retained `block.number` use as:
  - configurable economic duration;
  - hardcoded economic duration;
  - per-number rate or reward accrual;
  - true same-execution-block guard; or
  - telemetry only.
- [ ] Define Base and Robinhood values for all block-denominated defaults, including governance and registry timelocks, borrow/PSM intervals, auctions, locks, rewards, cooldowns, and price snapshots.
- [ ] Recalculate per-number rates, especially RIPE rewards, so each chain preserves the intended time-based economics through configuration.
- [x] Retain the integrated S3 Lootbox immutable-floor change as an approved
  minimal shared improvement. Robinhood uses floor `7_200` and mutable interval
  `0`; Base uses floor `43_200`. Deployment and Base convergence remain
  separately gated.
  - Decision evidence:
    [`lootbox-floor-implementation-record.md`](rh/lootbox-floor-implementation-record.md)
    and
    [`minimal-contract-change-reassessment.md`](rh/minimal-contract-change-reassessment.md).
- [x] Close S4 without a production-contract change for the initial release:
  deploy the existing shared Deleverage and SwitchboardDelta source unchanged,
  keep Robinhood `deleverageCooldown = 0`, accept the resulting lack of pacing,
  omit Underscore, and reopen S4 before either Underscore inclusion or any
  nonzero cooldown proposal or queued action.
  - Decision and independent-security evidence:
    [`deleverage-cooldown-security-decision.md`](rh/deleverage-cooldown-security-decision.md).
  - Track 7 H-08 must later prove the actual deployed graph omits Underscore,
    the live cooldown is zero, and no prohibited pending cooldown or Underscore
    registry action exists. Migration `0020` is omitted or assertion-only and
    may never be state-changing.
- [ ] Implement S5's owner-selected portable action-block boundary only after
  Stage A and independent security review select the smallest abstraction.
  Preserve the existing same-execution-block action ordering; use native
  `block.number` for ordinary EVM deployments and Robinhood
  `ArbSys.arbBlockNumber()` for child-block identity. Do not migrate the
  deployed Base Ledger, reinterpret the check as time/freshness, or use
  `chain.id`.
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

**Exit condition:** every deployed block-number dependency either uses the
unchanged shared implementation with approved parameters/accepted risk or has
an owner-approved indispensable change; Base and repeated/jumping-number
Robinhood tests pass.

## 3. Implement GREEN and RIPE CCIP integration

- [ ] Confirm that GREEN/RIPE bridging is required for the initial release. If
  it is not launch-critical, prefer deferral over token or pool changes.
- [ ] Pin the exact Chainlink source/API used as the inherited implementation.
  Prove the subclass adds no storage or bridge override, while treating
  upstream audit claims as evidence for the base rather than automatic
  coverage of the Ripe integration.
- [ ] Implement the minimal Department-compatible BurnMint pool layer:
  - inherit the concrete Chainlink `BurnMintTokenPool` in Solidity;
  - pass through its standard five constructor arguments;
  - GREEN pool retains both views, with `canMintGreen() == true` and
    `canMintRipe() == false`;
  - RIPE pool retains both views, with `canMintGreen() == false` and
    `canMintRipe() == true`;
  - add no storage and override no CCIP behavior;
  - the pool remains the direct caller of `GreenToken.mint()` or `RipeToken.mint()`; and
  - standard CCIP Router, RMN proxy, chain/pool lifecycle, optional allowlist,
    decimal, burn/mint, rate-limit, event, error, and administration behavior
    is inherited intact.
- [ ] Deploy the same GREEN pool implementation on Base and Robinhood and the same RIPE pool implementation on Base and Robinhood; keep Router, selector, remote-pool, ownership, and rate-limit differences in configuration.
- [ ] Do not insert a standalone mint adapter. A separately registered adapter
  could technically become RipeHq's authorized direct caller, but is rejected
  because it adds a mint-critical contract and governance surface without
  solving a token-interface problem.
- [ ] Use assisted registration with the existing shared token implementation if Chainlink supports it. If Phase 0 requires `getCCIPAdmin()`, stop for an owner decision: the standing default is a tested shared token revision, while the technically smaller Robinhood-only pre-deployment hook requires an explicit shared-source-policy exception and must not imply a Base migration.
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
- [ ] Add inheritance/delta tests for standard selectors, event indexing,
  custom-error encodings, storage layout, method identifiers, complete chain
  removal, remote-pool enumeration, and rate-limit reconfiguration without
  capacity reset.
- [ ] Measure the complete destination `balanceOf` + `releaseOrMint` +
  `balanceOf` path against the lane token-gas overhead on a Base fork and both
  test lanes; activation requires explicit margin, not a local estimate.
- [ ] Exercise rate-limit exhaustion, the owner-approved Department lifecycle
  choice, delayed delivery, and standard CCIP manual execution.
- [ ] Test Robinhood collateral → GREEN mint → bridge to Base → Base PSM redemption, including the fact that rate limits constrain propagation speed but do not cap cumulative Robinhood credit exposure.
- [ ] Enforce CCIP as the sole active minting bridge; any later bridge migration must pause CCIP, settle in-flight messages, reconcile supply, and revoke the old mint authority first.

**Exit condition:** both tokens bridge in both directions through shared pool implementations, all permissions are minimal, and cross-chain supply reconciles under normal and recovery flows.

## 4. Configure Stock Token collateral and pricing

- [x] Require Stock Tokens in the initial Robinhood launch and direct Track 8
  to specify the smallest demonstrably sufficient shared containment patch.
  This product decision does not approve unchanged listing, comprehensive
  vault/Ledger redesign, implementation, deployment, or activation.
  - Decision evidence:
    [`minimal-contract-change-reassessment.md`](rh/minimal-contract-change-reassessment.md);
    the revised Track 8 minimum-launch record remains required.
- [ ] Add a reusable transferability probe for each candidate Stock Token and run it against the exact launch contract.
- [ ] Finish the `SimpleErc20` versus `RebaseErc20`/`SharesVault` comparison:
  - `SimpleErc20` preserves nominal balances after an issuer burn and can create persistent phantom collateral plus first-withdrawer advantage;
  - `RebaseErc20` uses `SharesVault` live-balance accounting and socializes a custody loss pro rata.
- [ ] Test the chosen vault's accepted behavior for donations, measured deposits, total-balance loss, zero-balance recovery, blocked transfers, withdrawals, and internal-share liquidation.
- [ ] Complete Track 8's separate vault-change specification and approve its
  minimum-containment checkpoint before modifying custody or settlement code.
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

- [ ] Confirm that a PSM is required at initial launch. Prefer omission, or the
  existing source deployed disabled and without GREEN mint authority, over a
  source change.
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
- [ ] For every changed production contract, approve a necessity record showing
  why unchanged source, configuration, omission, disablement, or accepted risk
  is insufficient.
- [ ] Freeze one canonical contract implementation set, the CCIP version, configuration schema, deployment inventory, and address sources.
- [ ] Record which components require live Base parity before Robinhood launch, which temporary live-version differences governance has accepted with convergence plans, and which immutable or state-bearing/custody-bearing components have approved permanent live-version divergence.
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
- [ ] Every production-contract difference is the smallest indispensable
  change after documented owner review of the no-source-change alternative.
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
- [ ] Every live Base-versus-Robinhood implementation-version difference is explicitly approved and recorded in the component matrix: temporary differences are bounded and tracked to convergence; permanent differences are limited to components that are immutable or whose state-bearing or custody-bearing deployment would be unacceptably risky to migrate, and include their technical justification and accepted risk.
- [ ] Exact deployed code, roles, registry entries, feature flags, and parameters match the approved manifests.

## Explicit technical non-goals

The selected release does not include:

- broad contract modernization or portability changes that are not required by
  the frozen initial Robinhood feature set;
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
