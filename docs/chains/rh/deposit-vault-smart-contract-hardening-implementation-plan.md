# RH Deposit-Vault Smart-Contract Hardening Implementation Plan

## 1. Purpose

This is the implementation handoff for hardening the two critical RH deposit-vault systems:

1. Ripe governance vault: RipeGov
2. Stability pool: StabilityPool together with its StabVault accounting module

The work is deliberately limited to production smart-contract logic and tests that prove that logic. The intended reader is a fresh implementation agent with no prior session context.

This plan does not authorize a deployment, merge, push, configuration change, or release. It also does not amend the prior test-only coverage-gap plan or any separately approved exit-only change specification. Those artifacts have their own scope and gates.

It also does not, by itself, authorize production-contract edits. The owner’s standing RH rule is to make the fewest possible production smart-contract changes. Section 5.4 is therefore a mandatory owner gate before Work Packages 2 through 6 may change production source.

## 2. Bound baseline and startup gate

The analysis behind this plan was performed against the local RH branch at:

| Item | Bound value |
|---|---|
| Branch | rh |
| Commit | be6e4e9805e9b499b10f61cd219c555e62b43857 |
| Tree | dba8a4e557e3a943e25bb84d9911842c74371415 |
| Analysis date | 2026-08-07 |

Before editing anything, the implementation agent must print and record:

- absolute worktree path;
- branch name;
- HEAD commit;
- HEAD tree;
- short status;
- diff against the bound baseline.

The committed copy of this plan may be a docs-only descendant of the bound commit. That is an allowed administrative delta only if the complete diff from the bound commit contains this Markdown file and nothing else. Any production or test delta is baseline drift.

If the production/test baseline differs, stop. Rebind the plan to the new exact commit only after reviewing every intervening change to the contracts and tests named below. Do not silently apply this plan to a later mutable RH tip.

Use an isolated worktree and a new codex/ branch. Do not work directly on rh, master, or an existing dirty worktree. Preserve all unrelated changes.

### 2.1 Known local paths

These paths were valid when this plan was revised and must be checked rather than guessed:

- repository anchor: /Users/wigglez/dev/ripe-protocol
- local RH reference worktree: /Users/wigglez/dev/ripe-protocol-rh
- committed plan branch: codex/rh-deposit-vault-hardening-plan
- plan worktree at handoff: /Users/wigglez/dev/ripe-protocol-rh-deposit-vault-hardening-plan
- pinned validation environment: /Users/wigglez/dev/ripe-protocol-validation-envs/rh-wave2-py312

The validation environment currently resolves Python 3.12.0, Vyper 0.4.3, titanoboa 0.2.7, pytest 8.4.2, and Hypothesis 6.138.15. Re-record these versions in the startup report. Do not upgrade or substitute the compiler during this work.

## 3. Scope boundary

### 3.1 Primary production contracts

Review and change these only where required by a work package:

- contracts/vaults/RipeGov.vy
- contracts/vaults/StabilityPool.vy
- contracts/vaults/modules/StabVault.vy
- contracts/vaults/modules/SharesVault.vy
- contracts/vaults/modules/VaultData.vy

### 3.2 Composed production contracts

These are in scope only where a deposit-vault invariant crosses the contract boundary:

- contracts/core/Teller.vy
- contracts/core/TellerUtils.vy
- contracts/core/HumanResources.vy
- contracts/modules/Contributor.vy
- contracts/core/AuctionHouse.vy
- contracts/data/MissionControl.vy
- contracts/registries/PriceDesk.vy
- contracts/modules/Addys.vy
- contracts/config/SwitchboardAlpha.vy
- contracts/config/SwitchboardBravo.vy
- contracts/config/SwitchboardCharlie.vy
- contracts/config/SwitchboardDelta.vy
- contracts/config/SwitchboardEcho.vy

A fresh caller and state-flow search is mandatory before changing any external method restriction. Do not assume the above list is a complete caller inventory.

### 3.3 Primary behavior tests

Extend the existing suites before creating parallel suites:

- tests/vaults/test_ripe_gov_vault.py
- tests/vaults/test_ripe_gov_controls_and_migration.py
- tests/vaults/modules/test_stab_vault.py
- tests/vaults/modules/test_stab_vault_claims.py
- tests/vaults/modules/test_stab_vault_redemptions.py
- tests/vaults/modules/test_stab_vault_hardening.py
- tests/vaults/modules/test_stab_vault_claim_data_fuzz.py
- tests/core/teller/test_teller_deposit.py
- tests/core/teller/test_teller_action_block.py
- tests/core/teller/test_teller_withdraw.py
- tests/core/teller/test_teller_rebalance.py
- tests/core/humanResources/test_hr_other.py
- tests/core/humanResources/test_hr_contributor.py
- tests/core/auctionHouse/test_ah_liq_stab.py
- tests/core/auctionHouse/test_ah_liq_stab_edge_cases.py
- tests/data/test_mission_control.py

Test-only token, callback, and oracle mocks may be added when they are the smallest way to exercise actual contract behavior. They must not become a new framework.

### 3.4 Explicitly out of scope

Do not spend time on:

- CI or workflow files;
- changes to pytest configuration, plugins, cache policy, collection policy, or parallelism;
- coverage dashboards or percentage targets;
- deployment scripts, manifests, RPC/fork qualification, or chain operations;
- monitoring, keeper operations, runbooks, frontend behavior, or documentation unrelated to this handoff;
- general test-harness cleanup;
- vault migration redesign.

Existing migration behavior remains a regression gate because changes to shared vault logic must not break it. Contract bytecode size is an acceptance constraint, not a request for build-system work.

### 3.5 Known baseline findings

The implementation work is motivated by these concrete behaviors on the bound tree:

- RipeGov lock deposit, lock adjustment, and lock release trust every registered RIPE address rather than a purpose-specific caller.
- A registered contract can create governance shares against custody already attributed to another user, with no new token receipt at the direct vault boundary.
- A registered but unrelated contract can change another user’s lock and can trigger release-fee effects.
- A vault-level same-user governance transfer initiated through the authorized AuctionHouse or CreditEngine path can mutate lock state. It is not an ordinary user-callable method. The Contributor wrapper creates a separate constrained same-owner case, but neither reachability constraint makes the vault invariant safe.
- An active StabilityPool claim asset whose returned price is zero is omitted from NAV while deposits and withdrawals remain live, creating an explicit cohort-redistribution surface.
- The reviewed StabilityPool tests appeared to cover only small zero-price examples. Work Package 1 must reproduce and quantify the existing cases before treating large-value, multi-cohort economics as an established gap.
- A pre-existing token donation can help aggregate custody appear sufficient when a later settlement transfers less than the declared claim amount.
- Active claim liabilities can remain recorded after custody falls through a rebase or burn, without a complete deficit-response matrix.
- Teller protects only nested deposits during its receipt-measurement window; other custody-changing callbacks need a complete contract-behavior matrix.
- The non-raising price request does not guarantee non-reversion when the underlying price source itself reverts or returns invalid data.
- RipeGov overflow-disable tests do not begin from a real arithmetic failure, and there is no stateful RipeGov invariant model.
- A stability-reward lock test accepts an unused duration input and can pass under zero-value lock configuration without proving an unlock boundary.
- A position with only a tiny dormant claim balance and no raw stability-asset balance needs an explicit exit-liveness regression so dust cannot strand the account.
- RipeGov migration needs a regression for a source position whose Ledger membership was cleaned before migration; the migration must not silently become impossible while vault state still exists.

These are implementation targets, not a license to change unrelated shared behavior.

## 4. Security model and invariants

Every implementation choice and every new test must map to at least one invariant below.

### 4.1 Shared deposit-vault invariants

SV-1. No receipt, no shares. A deposit can mint shares only for value actually received into the intended vault custody in the same transaction.

SV-2. Conservation. A user cannot claim, redeem, withdraw, or transfer more value than the system received for that position, except for an explicitly funded reward.

SV-3. Atomic failure. Any failed price lookup, token transfer, callback, cap check, lock check, or accounting update leaves balances, shares, locks, points, indexes, claim data, and global totals unchanged.

SV-4. Least privilege. Registration as a valid RIPE address is not, by itself, authority to create another user’s shares, change another user’s lock, or burn another user’s exit fee.

SV-5. Pause integrity. The pause state blocks every ordinary user mutation intended to be paused. Only explicitly documented recovery actions may remain available.

SV-6. No receipt-window interleaving. While Teller measures an inbound custody delta, no callback may change the same destination balance through another protocol route.

### 4.2 RipeGov invariants

RG-1. User shares and total shares change by the same accepted amount, subject only to a documented fee or rounding rule.

RG-2. lastShares is the user’s actual post-operation share balance, never a nominal input.

RG-3. Global point totals equal the sum of user point contributions for every asset and point type.

RG-4. A lock cannot be shortened by transfer, same-address transfer, contributor movement, configuration change, or indirect protocol call. The only exception is a separately authorized release path whose fee and effects are exact.

RG-5. A same-user transfer is a true no-op for shares, locks, points, checkpoints, and timestamps.

RG-6. Disabling point updates permits safe exits but does not permit deposits, transfers, or unrelated state mutation to bypass a broken accounting path.

RG-7. A migrated position is tombstoned exactly once and cannot be withdrawn, transferred, rewarded, or migrated twice from the source vault.

### 4.3 StabilityPool and StabVault invariants

SP-1. Recorded active-claim liabilities never exceed actual custody for the corresponding token after any successful operation.

SP-2. The sum of user shares equals global shares for each claim asset and for the stability position.

SP-3. Every accepted price state follows one explicit policy. Valid price, zero price, absent feed, stale data, source revert, and malformed return data must not be conflated.

SP-4. Burning stability shares delivers the exact value required by the selected accounting policy. A failed or short outbound transfer rolls back the burn.

SP-5. Deposit indexes, redemption indexes, claim indexes, cap accounting, and user claim data remain mutually consistent after pruning, activation, depletion, restoration, and rounding.

SP-6. Donations, fee-on-transfer behavior, rebases, burns, false returns, missing returns, malformed returns, and callbacks cannot create phantom value or conceal a custody deficit.

## 5. Decisions and authorizations that must be explicit

Do not bury any of the following choices inside a patch. SP-PRICE-01 has an existing default. GOV-WEIGHT-01, RG-SIZE-01, RH-CHANGE-01, and RH-LANE-01 require an explicit recorded disposition before the affected production work proceeds.

### 5.1 SP-PRICE-01: unavailable active-claim price

The owner correction in docs/chains/rh/rh-production-vyper-remediation.md records a liveness policy: an active claim asset whose resolved price is zero is omitted from StabilityPool NAV while deposits and withdrawals remain available. This can transfer value between cohorts when the omitted asset is economically valuable.

Choose and record exactly one policy before implementing Work Package 5:

A. Preserve zero-skip liveness. This is the default authorized by the bound RH baseline. Add strong characterization tests, quantify redistribution at material sizes, and preserve atomic failure when the price source itself reverts or returns malformed data.

B. Fail closed on incomplete NAV. Recommended for the strongest accounting safety. Deposits, withdrawals, claims, redemptions, and share transfers that depend on total pool value revert while any active claim asset lacks a valid price. Asset-specific recovery operations may remain available only if they provably improve the deficit or price state.

C. Define an asymmetric policy. This requires a separate approved design specifying which actions may proceed, at what valuation, and why no cohort can extract value from another.

Without a new owner decision, implement A only. Do not silently convert the existing liveness choice into B.

### 5.2 GOV-WEIGHT-01: zero governance weight

The current conditional weighting logic can make a configured zero multiplier behave like the base unweighted value. Existing tests do not establish a coherent contract.

Preferred rule: zero means zero points. Always apply the configured multiplier, including zero.

Alternative rule: zero is invalid configuration, or zero is explicitly normalized and stored as 100 percent. If choosing this rule, reject ambiguity at configuration time.

Whichever rule is selected must be asserted at zero, one unit, one less than full scale, full scale, and greater than full scale if the configuration permits it.

DefaultsRobinhood currently configures only RIPE for this vault and sets assetWeight to 100_00. Selecting “zero means zero” therefore does not change the bound launch default, but it does change the meaning of a future governed zero configuration.

There is no autonomous default for this decision. If GOV-WEIGHT-01 is unresolved, the implementation agent may complete caller tracing, baseline health, and the failing zero-weight characterization, then must stop before changing production semantics.

### 5.3 RG-SIZE-01: RipeGov optimization and bytecode budget

The bytecode limit is a day-one architectural gate, not a final cleanup item. Reproduction with the pinned Vyper 0.4.3 environment and each source file’s own pragma produced:

| Contract | Source optimization | Runtime bytes | EIP-170 headroom |
|---|---:|---:|---:|
| RipeGov.vy | default gas optimization; no source pragma | 24,499 | 77 |
| StabilityPool.vy | source pragma optimize codesize | 24,275 | 301 |
| Teller.vy | source pragma optimize codesize | 24,043 | 533 |

The independent reviewer reported Teller as 24,042 bytes; local reproduction on the bound tree returned 24,043 bytes. The implementation gate must use the freshly reproduced value, not either report.

For this plan, “reasonable safety margin” means at least 200 runtime bytes. A candidate below 200 bytes requires a separate owner waiver that records the exact final size and residual deployment risk.

A diagnostic global -O codesize compile of unchanged RipeGov produced 22,927 bytes, or 1,649 bytes of headroom. This is only an estimate of the source-pragma option. It is not an acceptance build and does not authorize changing optimization mode.

Choose one:

A. Keep current optimization and implement only source substitutions or reductions that preserve semantics and leave at least 200 bytes after the approved hardening.

B. Add a source-level codesize optimization pragma to RipeGov, explicitly accepting changed gas costs, then re-run every affected behavior and size check. This requires owner approval.

C. Make no RipeGov production change and explicitly accept the residual risks, while retaining characterization tests where useful.

D. Pursue a new contract or migration architecture. This is outside this plan and requires a separate design and authorization.

Do not use a global compiler -O flag for baseline or candidate acceptance. Compile each file normally so its checked-in pragma controls optimization.

### 5.4 RH-CHANGE-01: minimum production-contract change authorization

The controlling RH default is the fewest possible production smart-contract changes. Before Work Packages 2 through 6 edit production source, present one row per proposed change with:

- concrete exploit or failure if no change is made;
- realistic reachability and blast radius;
- no-change or accepted-residual-risk option;
- configuration, omission, disabled-feature, or existing-shared-behavior alternative;
- smallest production-code mitigation;
- expected contracts, ABI/storage effects, and bytecode delta;
- new-code risk and residual risk after mitigation.

The owner must explicitly approve the exact subset of production changes. Approval of this planning document, test writing, or one row does not authorize the remaining rows.

### 5.5 RH-LANE-01: migration-lane sequencing

At review time, local branch codex/rh-vault-migration-phase1 is an in-flight candidate from the same bound baseline and modifies contracts/config/SwitchboardEcho.vy, contracts/core/Teller.vy, and contracts/core/TellerUtils.vy. This overlaps the migration regression in Section 9.5 and Teller hardening in Section 13. Its state is drift-prone and must be rechecked at startup.

Recommended sequence: finish, accept, or reject the migration lane first. If accepted and integrated, rebind this entire plan to the exact integrated commit before deposit-vault implementation. If rejected, record that disposition and retain the present bound baseline. Do not modify Teller in two live lanes at once.

If the owner prioritizes deposit-vault hardening first, pause the migration lane and require it to rebase onto the completed deposit-vault baseline. The owner must record which lane goes first.

## 6. Implementation sequence

The required order is:

1. Resolve RH-LANE-01, rebind, and record baseline suite health.
2. Inventory callers, state flows, contract sizes, and existing tests.
3. Add and demonstrate each failing adversarial test against the rebound baseline.
4. Present the minimum-change table and obtain RH-CHANGE-01 plus affected semantic/size decisions.
5. Pair each authorized production fix with its failing regression and return that focused slice to green.
6. Add the authorized RipeGov and StabilityPool stateful invariant suites.
7. Correct stability-reward lock tests and any confirmed dead argument.
8. Run focused, fuzz, composed, and shared-vault behavior suites explicitly.
9. Perform ABI, selector, layout, runtime-size, and source-diff review.

Do not combine all changes into one unreviewable patch. Work Package 1 is intentionally red only while proving a specific baseline defect. For each finding: add one failing regression, run it on the rebound baseline and record the expected failure, implement only the separately authorized fix, and return that slice to green before moving to an unrelated finding.

Do not leave a permanent xfail in the final suite. A temporary xfail(strict=True) is acceptable only for a deliberately preserved test-only checkpoint; remove it when the paired fix lands. The final branch must contain plain assertions and no expected failure for a remediated issue.

## 7. Work Package 0: rebind and caller inventory

### Tasks

- Recheck codex/rh-vault-migration-phase1 and resolve RH-LANE-01 before selecting the implementation baseline.
- Create or identify a clean detached copy of the exact implementation baseline for baseline-versus-candidate checks.
- Run every Section 16 behavior set against the exact baseline before changing tests or contracts. Record commands, collected counts, passed, failed, skipped, deselected, xfailed, and duration. An independent reviewer observed 146 passing tests in the two RipeGov vault files on the original bound baseline, but the implementation agent must reproduce rather than inherit that result.
- Reproduce compiler versions and the runtime-size table in RG-SIZE-01 using normal per-file pragma compilation.
- Confirm that the explicit fuzz command collects the existing four tests in tests/vaults/modules/test_stab_vault_claim_data_fuzz.py. A zero-test collection is a stop, not green evidence.
- Confirm every external caller of:
  - RipeGov.depositTokensWithLockDuration
  - RipeGov.adjustLock
  - RipeGov.releaseLock
  - RipeGov.transferBalanceWithinVault
  - StabilityPool.depositTokensInVault
  - StabilityPool.withdrawTokensFromVault
  - StabVault.claimFromStabilityPool and claimManyFromStabilityPool
  - StabVault.redeemFromStabilityPool and redeemManyFromStabilityPool
  - Teller.depositFromTrusted
  - Teller.depositIntoGovVault
- Trace custody and accounting for:
  - ordinary deposits;
  - governance deposits with locks;
  - contributor distributions;
  - stability deposits;
  - liquidation claim assets;
  - rewards and loot-box auto-deposits;
  - claim and redemption paths.
- Record which caller is supposed to have authority, whose tokens move, whose shares change, and where exact receipt is established.
- Inventory the existing zero-price tests by asset value, number of cohorts, operations, and price transitions. Replace the “small-example” assessment in Section 3.5 with reproduced evidence.
- Prepare the RH-CHANGE-01 minimum-change table for every proposed production edit, including the option to accept each residual risk and change no production code.

### Stop conditions

Stop before implementation if:

- a production caller contradicts a proposed access restriction;
- an external interface or persisted-layout change appears necessary but is not covered by this plan;
- a required hardening change would strand existing user state;
- any candidate contract cannot retain at least 200 bytes of runtime headroom and no exact owner waiver exists;
- GOV-WEIGHT-01, RG-SIZE-01, RH-CHANGE-01, or RH-LANE-01 is required for the next production step but unresolved;
- the baseline behavior suites are not green or their failures are not classified before candidate work;
- an explicit fuzz lane collects zero tests.

### Deliverable

A concise evidence bundle in the implementation PR description or review notes containing:

- baseline identity and suite-health table;
- caller and custody-flow matrix;
- reproduced runtime-size table;
- existing zero-price test inventory;
- minimum-change decision table;
- recorded owner decisions and lane order.

Do not create a peripheral inventory system.

## 8. Work Package 1: failing adversarial regression tests

Write these tests first. Confirm that each intended hardening test fails for the expected security reason on the bound baseline.

### 8.1 RipeGov authority matrix

For depositTokensWithLockDuration, adjustLock, and releaseLock, test calls from:

- the position owner;
- an unrelated EOA;
- Teller;
- AuctionHouse;
- CreditEngine;
- HumanResources;
- SwitchboardAlpha;
- SwitchboardBravo;
- SwitchboardCharlie;
- SwitchboardDelta;
- SwitchboardEcho;
- StabilityPool;
- another registered vault;
- another registered core contract;
- a removed or invalid RIPE address.

For each rejected caller, snapshot and assert no change to:

- token custody;
- user shares and total shares;
- lastShares;
- lock duration and unlock time;
- user points and global points;
- fee balances;
- timestamps and checkpoints.

Required attack regressions:

- a registered address cannot allocate shares to Alice against Bob’s already-accounted custody without moving tokens;
- an unrelated registered StabilityPool cannot extend Bob’s lock;
- an unrelated registered StabilityPool cannot release Bob’s lock and charge or burn the exit fee;
- an untrusted caller cannot choose an arbitrary beneficiary and arbitrary lock duration.

Expected test names, subject to the WP0 caller inventory confirming Teller-only authority:

- test_registered_non_teller_cannot_mint_gov_shares_from_existing_custody
- test_registered_non_teller_cannot_adjust_another_users_lock
- test_registered_non_teller_cannot_release_another_users_lock
- test_rejected_gov_privileged_call_is_fully_atomic

### 8.2 Same-address and contributor lock matrix

Exercise:

- same-address transferBalanceWithinVault initiated by AuctionHouse;
- same-address transferBalanceWithinVault initiated by CreditEngine;
- rejected same-address attempt by an ordinary user;
- same-address contributor transfer;
- transfer to a different user;
- zero amount;
- full amount;
- partial amount;
- expired lock;
- maximum lock;
- configured duration above maximum;
- configured duration below minimum;
- prior unlock later than newly computed unlock.

Assert that same-address movement changes no state and that contributor transfer never shortens an existing lock.

Suggested test names:

- test_gov_same_user_transfer_is_complete_noop
- test_contributor_transfer_cannot_shorten_existing_lock
- test_contributor_duration_is_clamped_to_current_governance_bounds

### 8.3 Stability zero-price economics

Use two active claim assets and at least two depositor cohorts. Give the zero-priced asset a material share of true economic value rather than a dust amount.

Exercise:

- deposit before zero price;
- deposit while zero price;
- partial and full withdrawal while zero price;
- price restoration;
- claim and redemption before and after restoration;
- repeated price flapping;
- maximum active-asset count.

For every transition, compute the expected cohort value under the selected SP-PRICE-01 policy. A test that checks only that the transaction succeeds is insufficient.

Suggested test names:

- test_zero_price_active_claim_asset_cohort_redistribution_is_explicit
- test_large_zero_price_claim_asset_nav_policy
- test_price_restore_does_not_corrupt_claim_or_share_accounting

### 8.4 Stability token and custody matrix

Create focused token behaviors for:

- exact transfer;
- pre-existing donation plus exact transfer;
- pre-existing donation plus short transfer;
- inbound fee;
- downward rebase after activation;
- upward rebase after activation;
- burn from vault custody;
- outbound fee or burn;
- false return;
- no return;
- malformed or trailing return data;
- revert;
- callback before transfer;
- callback after transfer.

For every failure, assert full atomic rollback of custody, shares, indexes, cap usage, and claim data.

Suggested test names:

- test_preexisting_donation_cannot_mask_short_stability_receipt
- test_active_claim_custody_deficit_blocks_value_extracting_actions
- test_outbound_short_delivery_rolls_back_stability_share_burn
- test_malformed_token_return_cannot_mutate_stability_accounting

## 9. Work Package 2: RipeGov authorization, locks, and pause hardening

### 9.1 Narrow privileged callers

Subject to the fresh caller inventory, restrict these functions to Teller:

- depositTokensWithLockDuration
- adjustLock
- releaseLock

Do not use the broad valid-RIPE-address predicate for capabilities that mutate arbitrary users.

If a second legitimate production caller exists, give that caller a narrowly named and separately tested capability. Do not retain the broad registry-wide authorization as a convenience.

### 9.2 Make same-address transfers true no-ops

Add the narrowest RipeGov-level guard so owner equals recipient returns before any lock, point, checkpoint, or transfer mutation.

Do not change SharesVault family-wide behavior unless a full consumer inventory proves that every inheriting vault wants identical semantics.

### 9.3 Prevent contributor lock shortening

When contributor shares move into RipeGov:

- resolve the current minimum and maximum governance lock bounds;
- clamp the contributor duration to those bounds;
- preserve the recipient’s later existing unlock;
- reject or safely handle a contradictory configuration;
- calculate points from the final effective lock, not the nominal requested duration.

### 9.4 Pause semantics

Preferred rule: adjustLock and releaseLock revert while RipeGov is paused. Deposits, transfers, and ordinary withdrawals must retain their intended pause behavior. Migration and overflow-disable escape operations may remain available only where an existing recovery invariant requires them.

Add one matrix test covering every public state-changing RipeGov method in paused and unpaused states.

### 9.5 Preserve RipeGov migration liveness

Add a regression in tests/vaults/test_ripe_gov_controls_and_migration.py for a source position that still has governance-vault state after its source Ledger membership was cleaned.

First prove whether that state is reachable through authorized production methods. If it is reachable, migration must use authoritative vault state or an equivalently safe source of truth so the user is not stranded. If it is not reachable, add the shortest contract-behavior proof of the blocking invariant. Do not redesign the migration protocol or expand its authority surface under this work package.

Also retain exact-once migration, source tombstone, destination shares, locks, points, post-migration withdrawal, and repeated-migration regressions.

### Completion criteria

- Only the intended caller can create locked governance shares or mutate a user lock.
- Same-user transfer changes no state.
- Contributor movement cannot shorten a lock.
- Pause behavior is explicit for every public mutation.
- Existing legitimate Teller, HumanResources, reward, withdrawal, and migration flows remain green.

## 10. Work Package 3: RipeGov points and overflow recovery

### 10.1 Resolve zero-weight semantics

Implement GOV-WEIGHT-01 in the smallest contract layer that owns the weighting rule. Delete or rewrite contradictory tests. Do not retain assertions that pass only because the tested balance is zero or the multiplier is bypassed.

### 10.2 Prove the overflow-disable escape from an actual unsafe state

Construct a test state in which an ordinary point update genuinely overflows or reaches the relevant arithmetic failure. Test-local direct storage setup is acceptable only to establish an otherwise impractical extreme state; invoke normal contract methods for the behavior under test.

Prove:

- the ordinary point update reverts;
- an unauthorized caller cannot disable point updates;
- the authorized switchboard can disable the affected point path;
- partial exit succeeds after disable;
- full exit succeeds after disable;
- a second asset remains correct;
- repeated cleanup is safe or rejects exactly as designed;
- unlock, bad-debt, transfer, and Boardroom paths do not corrupt global totals;
- global and per-user disables remain irreversible as specified;
- repeated disable attempts reject atomically and no later operation resurrects stale point debt.

### 10.3 Add a RipeGov stateful model

Model at least:

- two users;
- two assets;
- deposit;
- direct donation;
- partial and full withdrawal;
- user transfer;
- contributor transfer;
- lock adjustment and release;
- point update;
- point disable;
- pause and unpause;
- Boardroom interaction.

After every step assert RG-1 through RG-7. Bias generated values around zero, one, minimum lock, maximum lock, unlock boundary, fee boundary, full balance, one less than full balance, and arithmetic limits.

This is a smart-contract behavior test, not a coverage exercise. Keep it near the RipeGov test suite.

## 11. Work Package 4: StabilityPool custody and delivery hardening

### 11.1 Detect active-claim custody deficits

Before any action that values or transfers an active claim asset, compare recorded liability with actual token custody.

At minimum, cover:

- total pool value calculation;
- deposit;
- withdrawal;
- stability-share transfer if it changes value ownership;
- claimFromStabilityPool and claimManyFromStabilityPool;
- redeemFromStabilityPool and redeemManyFromStabilityPool;
- claim-asset activation;
- claim-data pruning;
- liquidation settlement that adds claim assets.

A value-extracting action must not proceed while it can socialize an unexplained deficit. A repair action may proceed only if it cannot worsen another user’s position.

Test deficit creation by downward rebase and by token burn from vault custody. Test repair by direct replenishment and confirm normal operations resume without changing user liabilities.

### 11.2 Prevent donations from masking short receipts

Do not harden receipt accounting with a naive post-balance-equals-recorded-total assertion; a donation would then become a denial-of-service vector.

Preferred design:

- StabilityPool pulls the expected claim tokens from the authenticated AuctionHouse;
- StabilityPool measures its own before and after custody;
- it records exactly the measured amount;
- it rejects any measured amount that violates the liquidation settlement contract.

Acceptable alternative:

- retain push settlement only if the authenticated caller supplies a measured amount that StabilityPool can independently bind to the current transaction and destination balance;
- prove that pre-existing donations cannot satisfy a later short transfer.

The following sequence must fail atomically:

1. donate D tokens directly to StabilityPool;
2. transfer only Q minus D for a liquidation that declares Q;
3. attempt to record Q.

The donation must remain unallocated surplus or be handled by an explicit, separately authorized surplus policy. It must not be credited as liquidation receipt.

### 11.3 Enforce exact outbound delivery

For assets whose registered token policy requires exact transfer:

- measure recipient balance before and after claim or redemption;
- require the exact expected increase;
- burn shares or reduce liabilities only after the delivery check can pass atomically.

Cover fee-on-transfer, burn-on-transfer, false return, malformed return, callback, and revert. If the protocol deliberately supports a non-exact token class, define that class and its accounting rule explicitly rather than weakening all assets.

When proceeds are routed through Teller for automatic deposit, assert exact delivery at the final destination vault as well as exact liability reduction in StabilityPool. A successful intermediate transfer is not sufficient.

### 11.4 Prevent dormant dust from stranding exit

Test a user whose position contains:

- zero raw stability-asset balance;
- one or more below-activation dormant claim balances;
- values immediately below, exactly at, and immediately above activation and pruning thresholds.

The user must have a defined way to exit or recover every economically owned balance without relying on a future liquidation by someone else. If the chosen rule converts, claims, prunes, or retains dust, assert conservation and exact rounding across repeated partial exits. Do not solve the case by silently deleting a liability.

### 11.5 Preserve contract size

Compile every changed deployed contract and record runtime bytecode size. The default acceptance threshold is at least 200 bytes of headroom; anything smaller requires the exact owner waiver defined by RG-SIZE-01. Do not delete security checks or weaken tests to make the bytecode fit.

## 12. Work Package 5: Stability unavailable-price policy

### 12.1 Exercise the actual PriceDesk boundary

Test StabilityPool against PriceDesk behavior for:

- valid nonzero price;
- returned zero;
- absent feed;
- stale or otherwise invalid response if supported;
- underlying source revert;
- empty return data;
- malformed return data;
- restored valid price.

Apply the matrix to:

- view functions that report total value or redemption value;
- deposit;
- withdrawal;
- stability-share transfer;
- single and batch claim;
- single and batch redemption;
- prune;
- activation;
- liquidation settlement.

### 12.2 If SP-PRICE-01 chooses A

Preserve the zero-skip rule exactly and add economic characterization assertions. Source revert, malformed response, and unexpected call failure remain atomic failures unless the approved policy explicitly classifies them as zero.

The tests must make the redistribution consequence visible at meaningful scale. They must not describe the behavior as safe merely because the transaction remains live.

### 12.3 If SP-PRICE-01 chooses B

Centralize the completeness check so every NAV-dependent path uses the same rule. Do not patch only deposits or only withdrawals.

Allow only narrowly defined recovery actions during incomplete pricing, and prove that each permitted action cannot extract value or worsen another user’s claim.

### Completion criteria

Every price failure mode has one deliberate result across every affected method. No hidden exception converts a source revert into an unexplained partial update.

## 13. Work Package 6: Teller receipt-measurement interleaving

The current receiptMeasurementActive flag blocks another deposit while Teller measures custody, but other custody-changing Teller routes can still be reached by a malicious token callback. That can invalidate the before-and-after balance measurement.

### Implementation rule

While receiptMeasurementActive is true, block every Teller entry point that can change the measured destination’s custody or create a dependent vault mutation, including as applicable:

- withdraw;
- rebalance;
- collateral redemption;
- stability redemption;
- single or batch claim;
- liquidation;
- deleverage;
- another deposit through any route.

Place the guard at the smallest central internal boundary that all relevant routes cross. Do not merely add a nonreentrant decorator to depositFromTrusted or depositIntoGovVault if that breaks legitimate protocol composition without closing the complete callback surface.

### Required callback matrix

For callbacks before and after token balance movement, test:

- same-route nested deposit;
- cross-route nested deposit;
- withdrawal;
- rebalance;
- claim;
- redemption;
- liquidation;
- deleverage.

Every custody-changing nested action must fail and the outer deposit must either:

- succeed with an exact measured receipt and no nested state change; or
- revert completely.

Also prove that:

- receiptMeasurementActive clears after success and revert;
- ordinary non-callback operations still work;
- governance auto-deposit, contributor deposit, stability rewards, and loot-box deposit preserve intended composition;
- no callback can exploit a different token or vault to corrupt the measured operation.

## 14. Work Package 7: StabilityPool stateful invariant model

Add a multi-user, multi-asset state machine that exercises real contract entry points.

### State and operations

Model:

- at least three users;
- GREEN, sGREEN, and two claim assets;
- deposits and partial/full withdrawals;
- direct donations;
- liquidations;
- claim-asset activation and pruning;
- single and batch claims;
- single and batch redemptions;
- stability-share transfers if supported;
- zero price, absent feed, source failure, and price restoration;
- custody deficit and repair;
- cap boundary and maximum active-asset count.

### Boundaries

Bias examples around:

- zero and one;
- share-conversion rounding points;
- one less than full balance and full balance;
- claim activation threshold;
- prune threshold;
- redemption index transition;
- maximum asset array length;
- pool depletion and first deposit after depletion;
- cap minus one, cap, and cap plus one;
- dust remainders and repeated small operations.

### Invariants

After every successful step assert SP-1 through SP-6. After every reverted step compare a complete state snapshot and prove atomicity.

The model must independently compute expected liabilities and ownership. Re-reading the same contract value on both sides is not an oracle.

## 15. Work Package 8: stability-reward lock correctness

Existing reward-lock tests pass a _stabRewardsLockDuration argument that is not used by the tested helper. On the bound fixture, default minimum lock and lock-point ratio values can make a test pass without proving that rewards are locked.

### Tasks

- Trace the authoritative reward-lock configuration from MissionControl through the reward deposit.
- Remove a dead test/helper argument if confirmed dead, or wire the intended production input only if that is the approved design.
- Configure nonzero lock duration and nonzero lock-point ratio in every test that claims to verify a reward lock.
- Assert the exact unlock timestamp or block and the exact point contribution, not merely that a position exists.

### Required matrix

Test:

- lock-point ratio at 0, 33, 50, and 100 percent;
- zero, minimum, ordinary, and maximum configured duration;
- withdrawal one unit before unlock;
- withdrawal exactly at unlock;
- reward added to an existing unlocked position;
- reward added to an existing later-locked position;
- weighted unlock calculation after multiple reward deposits;
- replacing the active MissionControl configuration source with a second valid config contract, proving the reward lock reads the new source, then restoring the original config source and proving subsequent rewards use the original values again.

## 16. Focused verification

Run behavior tests in increasing composition order. These commands are verification recipes for contract logic; they do not authorize changes to pytest.ini, CI, plugins, or repository test infrastructure.

### 16.0 Pinned local runner and marker policy

From the candidate worktree, establish private writable caches so titanoboa does not attempt to write to an unavailable home cache:

```zsh
RH_VAULT_PYTHON=/Users/wigglez/dev/ripe-protocol-validation-envs/rh-wave2-py312/bin/python
RH_VAULT_TEST_ROOT=$(mktemp -d /private/tmp/rh-deposit-vault-tests.XXXXXX)
chmod 700 "$RH_VAULT_TEST_ROOT"
mkdir -p "$RH_VAULT_TEST_ROOT/boa" "$RH_VAULT_TEST_ROOT/pycache" "$RH_VAULT_TEST_ROOT/xdg" "$RH_VAULT_TEST_ROOT/hypothesis" "$RH_VAULT_TEST_ROOT/basetemp"

rh_vault_pytest() {
  env \
    -u WEB3_ALCHEMY_API_KEY \
    -u ALCHEMY_API_KEY \
    -u ETH_RPC_URL \
    -u BASE_RPC_URL \
    -u RPC_URL \
    -u WEB3_PROVIDER_URI \
    -u PRIVATE_KEY \
    -u MNEMONIC \
    -u AWS_ACCESS_KEY_ID \
    -u AWS_SECRET_ACCESS_KEY \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPYCACHEPREFIX="$RH_VAULT_TEST_ROOT/pycache" \
    XDG_CACHE_HOME="$RH_VAULT_TEST_ROOT/xdg" \
    HYPOTHESIS_STORAGE_DIRECTORY="$RH_VAULT_TEST_ROOT/hypothesis" \
    ETHERSCAN_API_KEY=local-placeholder \
    RIPE_AUDIT_CACHE="$RH_VAULT_TEST_ROOT/boa" \
    "$RH_VAULT_PYTHON" -c 'import os, sys; from boa.interpret import set_cache_dir; set_cache_dir(os.environ["RIPE_AUDIT_CACHE"]); import pytest; raise SystemExit(pytest.main(sys.argv[1:]))' \
    -q -p no:cacheprovider --basetemp="$RH_VAULT_TEST_ROOT/basetemp" "$@"
}
```

Record the output of:

```zsh
"$RH_VAULT_PYTHON" --version
"$RH_VAULT_PYTHON" -c 'import importlib.metadata as m; print("vyper", m.version("vyper")); print("titanoboa", m.version("titanoboa")); print("pytest", m.version("pytest")); print("hypothesis", m.version("hypothesis"))'
```

pytest.ini excludes fuzz tests by default. Do not edit it. Use this policy:

- deterministic regression and boundary tests remain unmarked and run in the normal focused lanes;
- comprehensive Hypothesis/state-machine campaigns use pytest.mark.fuzz;
- create the new generated suites as tests/vaults/test_ripe_gov_invariants.py and tests/vaults/modules/test_stab_vault_invariants.py;
- run every fuzz completion gate explicitly with command-line -m fuzz;
- run collect-only first and treat zero collected tests as failure.

The explicit command-line marker overrides the default marker expression. On the bound tree, this command must collect four existing claim-data fuzz tests:

```zsh
rh_vault_pytest --collect-only -m fuzz tests/vaults/modules/test_stab_vault_claim_data_fuzz.py
```

### 16.1 RipeGov focused set

Baseline and candidate deterministic command:

```zsh
rh_vault_pytest \
  tests/vaults/test_ripe_gov_vault.py \
  tests/vaults/test_ripe_gov_controls_and_migration.py \
  tests/core/humanResources/test_hr_other.py \
  tests/core/humanResources/test_hr_contributor.py \
  tests/data/test_mission_control.py \
  tests/core/lootbox/test_loot_ripe_rewards.py
```

Candidate generated-invariant command:

```zsh
rh_vault_pytest --collect-only -m fuzz tests/vaults/test_ripe_gov_invariants.py
rh_vault_pytest -m fuzz tests/vaults/test_ripe_gov_invariants.py
```

### 16.2 StabilityPool focused set

Baseline and candidate deterministic command:

```zsh
rh_vault_pytest \
  tests/vaults/modules/test_stab_vault.py \
  tests/vaults/modules/test_stab_vault_claims.py \
  tests/vaults/modules/test_stab_vault_redemptions.py \
  tests/vaults/modules/test_stab_vault_hardening.py \
  tests/core/auctionHouse/test_ah_liq_stab.py \
  tests/core/auctionHouse/test_ah_liq_stab_edge_cases.py
```

Baseline existing fuzz command:

```zsh
rh_vault_pytest -m fuzz tests/vaults/modules/test_stab_vault_claim_data_fuzz.py
```

Candidate generated-invariant command:

```zsh
rh_vault_pytest --collect-only -m fuzz tests/vaults/modules/test_stab_vault_invariants.py
rh_vault_pytest -m fuzz \
  tests/vaults/modules/test_stab_vault_claim_data_fuzz.py \
  tests/vaults/modules/test_stab_vault_invariants.py
```

### 16.3 Composed deposit and callback set

Baseline and candidate command:

```zsh
rh_vault_pytest \
  tests/core/teller/test_teller_deposit.py \
  tests/core/teller/test_teller_action_block.py \
  tests/core/teller/test_teller_withdraw.py \
  tests/core/teller/test_teller_rebalance.py \
  tests/core/humanResources/test_hr_other.py \
  tests/core/humanResources/test_hr_contributor.py \
  tests/core/lootbox/test_loot_ripe_rewards.py \
  tests/core/auctionHouse/test_ah_liq_stab.py \
  tests/core/auctionHouse/test_ah_liq_stab_edge_cases.py
```

Add any other reward, governance, liquidation, or auto-deposit test file reached by the final caller diff. Record additions rather than silently relying on broad collection.

### 16.4 Shared-vault regression set

If SharesVault or VaultData changes, run every inheriting vault suite. Do not infer shared safety from RipeGov and StabilityPool alone:

```zsh
rh_vault_pytest tests/vaults
rh_vault_pytest -m fuzz tests/vaults
```

Record both collections. The first command is expected to deselect fuzz; the second must execute it.

### 16.5 Contract acceptance checks

Use a clean detached worktree for the rebound baseline and the pinned compiler:

```zsh
RH_VAULT_VYPER=/Users/wigglez/dev/ripe-protocol-validation-envs/rh-wave2-py312/bin/vyper
RH_VAULT_BASELINE_WORKTREE=/absolute/path/to/clean-rebound-baseline
RH_VAULT_CANDIDATE_WORKTREE=/absolute/path/to/candidate

rh_vault_runtime_size() {
  "$RH_VAULT_VYPER" -f bytecode_runtime "$1" | awk '{bytes=(length($0)-2)/2; print bytes, 24576-bytes}'
}

rh_vault_runtime_size "$RH_VAULT_BASELINE_WORKTREE/contracts/vaults/RipeGov.vy"
rh_vault_runtime_size "$RH_VAULT_BASELINE_WORKTREE/contracts/vaults/StabilityPool.vy"
rh_vault_runtime_size "$RH_VAULT_BASELINE_WORKTREE/contracts/core/Teller.vy"
rh_vault_runtime_size "$RH_VAULT_CANDIDATE_WORKTREE/contracts/vaults/RipeGov.vy"
rh_vault_runtime_size "$RH_VAULT_CANDIDATE_WORKTREE/contracts/vaults/StabilityPool.vy"
rh_vault_runtime_size "$RH_VAULT_CANDIDATE_WORKTREE/contracts/core/Teller.vy"
```

Do not pass -O in acceptance commands. Each source file’s checked-in pragma must control optimization. If RG-SIZE-01 authorizes adding a RipeGov codesize pragma, the candidate source must contain it and the normal command above must reproduce the result.

For each changed deployed source path, compare ABI, method identifiers, and storage layout with the exact rebound baseline:

```zsh
RH_VAULT_CONTRACT_PATH=contracts/vaults/RipeGov.vy
for RH_VAULT_FORMAT in abi method_identifiers layout; do
  diff -u \
    <("$RH_VAULT_VYPER" -f "$RH_VAULT_FORMAT" "$RH_VAULT_BASELINE_WORKTREE/$RH_VAULT_CONTRACT_PATH") \
    <("$RH_VAULT_VYPER" -f "$RH_VAULT_FORMAT" "$RH_VAULT_CANDIDATE_WORKTREE/$RH_VAULT_CONTRACT_PATH")
done
```

Repeat with RH_VAULT_CONTRACT_PATH set to every changed deployed contract. A nonzero diff is not automatically a failure, but every changed ABI entry, selector, and storage item must be intended and explicitly approved.

For every changed production contract:

- compile successfully;
- record baseline and candidate runtime bytecode size using normal per-file pragma compilation;
- confirm at least 200 bytes of headroom or attach the exact RG-SIZE-01 owner waiver;
- inspect the generated diff for unexpected ABI, event, selector, storage-layout, or revert-semantic changes;
- confirm no persisted storage slot moved unless separately approved;
- confirm every new branch has a behavior test;
- confirm every security regression fails on the bound baseline and passes on the candidate for the intended reason.

Do not modify workflow or harness files to make this verification pass.

## 17. Stop conditions

Stop and report before proceeding if any of the following occurs:

- HEAD or tree contains a production/test delta from the rebound baseline before implementation begins; the committed plan-only delta is allowed as specified in Section 2;
- RH-LANE-01 is unresolved or another live lane is modifying Teller, TellerUtils, RipeGov, StabilityPool, or StabVault;
- the next production edit lacks an exact RH-CHANGE-01 owner approval;
- GOV-WEIGHT-01 or RG-SIZE-01 is unresolved and the next edit would choose it implicitly;
- a legitimate production caller would be blocked by the proposed least-privilege rule;
- the selected price policy is still unresolved and a patch would choose it implicitly;
- an accounting hardening requires a storage migration or user-state rewrite;
- the implementation needs an ABI-breaking change not explicitly approved;
- a shared base-vault change alters an unrelated vault’s semantics;
- candidate runtime headroom falls below 200 bytes without an exact owner waiver;
- a test requires altering production semantics merely to make the test convenient;
- an existing security regression fails for a reason unrelated to the candidate;
- an explicit fuzz lane collects zero tests or a completion-gate suite is deselected without a separate executed lane;
- a remediated issue remains xfailed rather than passing with plain assertions;
- any rejected operation leaves partial contract state behind.

When stopped, report the exact contract, method, invariant, caller/state sequence, and smallest viable options. Do not broaden scope without authorization.

## 18. Definition of done

This plan is complete only when all of the following are true. For a production-risk item, completion means either the authorized mitigation passes its regression or RH-CHANGE-01 records an exact no-change residual-risk acceptance and the characterization test preserves the known behavior. Do not label an accepted residual risk as remediated.

- [ ] Exact baseline, tree, worktree, branch, and clean starting state are recorded.
- [ ] The committed plan-only delta is identified and no other pre-implementation drift exists.
- [ ] RH-LANE-01 names the lane order and the non-active overlapping lane is paused, rejected, or integrated.
- [ ] Pinned Python, Vyper, titanoboa, pytest, and Hypothesis versions are reproduced.
- [ ] All mandatory deterministic and fuzz behavior sets have a baseline health record before edits.
- [ ] Production caller inventory is complete for every restricted method.
- [ ] SP-PRICE-01 is recorded and implemented exactly.
- [ ] GOV-WEIGHT-01 is recorded and tested at all boundaries.
- [ ] RG-SIZE-01 is recorded and every changed deployed contract retains at least 200 bytes of headroom or has an exact owner waiver.
- [ ] RH-CHANGE-01 records the owner-approved production-change subset and accepted residual risks.
- [ ] RipeGov broad-address authority is either remediated and regression-tested or explicitly accepted as residual risk.
- [ ] Same-user governance-transfer mutation is either remediated and regression-tested or explicitly accepted as residual risk.
- [ ] Contributor lock shortening is either remediated and regression-tested or explicitly accepted as residual risk.
- [ ] RipeGov pause semantics are explicitly selected and tested, including an exact residual acceptance if unchanged.
- [ ] Reachable pre-cleaned Ledger migration state is either made live and regression-tested or explicitly accepted as residual risk.
- [ ] Actual point-overflow recovery is proven, including safe partial and full exit.
- [ ] RipeGov has a multi-user, multi-asset stateful invariant suite.
- [ ] Active-claim custody deficits are either blocked before value extraction or explicitly accepted as residual risk with characterization.
- [ ] Donation-masked short liquidation receipt is either prevented or explicitly accepted as residual risk with characterization.
- [ ] Outbound short delivery is either prevented from burning shares/reducing liabilities or explicitly accepted as residual risk with characterization.
- [ ] Dormant-only dust exit behavior is either made conserving and live or explicitly accepted as residual risk with characterization.
- [ ] Every unavailable-price and malformed-price state has a deliberate, consistent result.
- [ ] Teller receipt-window interleaving is either closed and regression-tested or explicitly accepted as residual risk with the full callback matrix characterized.
- [ ] StabilityPool has a multi-user, multi-asset stateful invariant suite with reachable zero-price cases.
- [ ] Stability-reward tests prove exact nonzero lock and point behavior.
- [ ] Focused, composed, shared-vault, migration-regression, and explicitly selected fuzz/invariant behavior suites pass with nonzero collection.
- [ ] Changed deployed contracts compile below the runtime bytecode limit with no unapproved ABI or storage-layout change.
- [ ] No remediated security test remains xfailed, skipped, or deselected from all executed lanes.
- [ ] No CI, harness, deployment, monitoring, or unrelated code was changed.

A green test count alone is not completion. The final review must map each security finding to a production fix or an explicitly accepted policy, and to a regression test that would fail if the vulnerability returned.

## 19. Fresh-agent startup report

The implementation agent should begin with this concise report before making changes:

- Repository anchor:
- Plan branch and plan commit:
- Plan file absolute path:
- Worktree:
- Branch:
- HEAD commit:
- HEAD tree:
- Bound baseline commit and tree:
- Committed plan-only delta confirmed:
- Baseline drift: yes or no
- Working tree clean: yes or no
- Python, Vyper, titanoboa, pytest, and Hypothesis versions:
- RipeGov, StabilityPool, and Teller runtime sizes and headroom:
- Baseline RipeGov deterministic suite counts:
- Baseline StabilityPool deterministic suite counts:
- Baseline existing fuzz suite collection and counts:
- Baseline composed Teller/AuctionHouse suite counts:
- SP-PRICE-01 selected policy:
- GOV-WEIGHT-01 selected rule:
- RG-SIZE-01 selected option and owner waiver if any:
- RH-CHANGE-01 approved production-change rows:
- RH-LANE-01 active-first lane and other-lane disposition:
- Confirmed RipeGov privileged callers:
- Confirmed StabilityPool settlement callers:
- Proposed production files:
- Proposed behavior-test files:
- Unrelated existing changes preserved:
- Stop condition encountered: none, or exact reason

If a decision is unresolved, the agent may complete baseline health, read-only tracing, size reproduction, the minimum-change table, and failing characterization tests. It must then stop before production edits that choose the unresolved policy.

## 20. Existing RH context to read before implementation

Read these after binding the exact baseline and before editing production code:

- docs/chains/rh/rh-production-vyper-remediation.md for the current owner correction on unavailable StabilityPool pricing and the current bytecode constraint;
- docs/chains/rh/reassessment/teller-balance-measurement.md for the direct-vault caller boundary and receipt-measurement composition analysis;
- docs/chains/rh/smart-contract-test-coverage-gap-plan.md for existing behavior-test placement, without inheriting its separate test-only file ceiling;
- docs/chains/rh/stability-pool/long-term-hardening-plan.md for prior StabilityPool risk framing, subject to later owner corrections;
- docs/chains/rh/stock-token-vault-change-specification.md for the previously identified Teller-only governance lock-deposit boundary.
- pytest.ini for the default marker exclusions; do not edit it for this plan.

When these documents conflict, the exact bound production source plus the latest explicit owner correction controls. This implementation plan controls only the deposit-vault hardening scope stated here.

The standing owner minimum-contract-change directive is controlling even though it is not encoded in the bound production tree. This plan records its operational requirements in RH-CHANGE-01 so a fresh agent does not need prior-session context.
