# `rh` Production Vyper Remediation — Implementation Handoff

**Status:** Owner-authorized local implementation handoff

**Revision:** 3 — owner-directed crank-then-verify workflow, 2026-08-06

## 1. Mission

Implement every authorized remediation in this document against the pinned
Robinhood pull-request candidate, then perform one consolidated focused
verification pass. This is an execution handoff, not another review assignment.

The implementation agent should proceed through all work packages without
pausing for intermediate design review or asking the owner to repeat decisions
already frozen here. Use the smallest coherent implementation that satisfies
the stated invariants. When a package exposes an ordinary implementation
detail, resolve it using the existing repository architecture and continue.

Complete the implementation packages as one uninterrupted build pass. Do not
run a full-suite baseline before editing, do not stop for per-package approval,
and do not run focused suites after each package. Add or update the required
test cases while implementing, but execute tests only in the consolidated
end-of-pass phase in Section 18. The complete repository-wide serial suite is
reserved for the subsequent independent review/test phase.

Do not deploy, activate, merge, push, or publish anything. Do not modify live
chain state. Do not commit unless separately authorized. The required outcome
is a complete implementation in an isolated worktree, one focused final
verification record, and a handoff ready for independent review/full-suite
testing.

## 2. Controlling baseline and authority

Implementation is bound to:

- Repository: `Ripe-Foundation/ripe-protocol`
- Pull request: PR #67
- Source branch: `rh`
- Commit: `7d8c76e5134bf866ccbb051fdf5030b6e83cef8b`
- Tree: `1d115e9a01f01f933e3e80747902080387f2113c`
- Base: `master@91eda49ccd34a25090582aff0695075c4c806011`
- Merge base: `91eda49ccd34a25090582aff0695075c4c806011`
- Vyper version declared by the affected contracts: `0.4.3`
- Owner-decision date: 2026-08-06

PR #67 identifies the pinned implementation candidate. References to PR #66
inside `config/robinhood-parameters.json` are legitimate upstream provenance
for the owner-approved Profile 1 launch inputs; do not rewrite that provenance
to PR #67 merely to make the numbers match.

Use the prepared isolated `codex/` implementation branch and worktree created
from the exact pinned commit. Do not implement in the owner's `rh` worktree or
in the current `master` worktree. Do not rebase onto a later mutable `rh` tip
during the task. Report any later branch movement in the final handoff; the
owner can choose a later delta integration separately.

The prepared handoff location is:

- Worktree: `/Users/wigglez/dev/ripe-protocol-rh-production-vyper-remediation`
- Branch: `codex/rh-production-vyper-remediation`

Its clean starting `HEAD` is a documentation-only seed commit. The seed's
first parent must be the exact pinned source commit above, and the seed delta
must contain only:

- `docs/chains/rh/rh-production-vyper-remediation-implementation-plan.md`
- `docs/chains/rh/rh-production-vyper-review-findings.md`

The implementation agent should use this prepared worktree rather than create
another one. Treat `HEAD^` as the immutable production-source baseline and
`HEAD` as the clean handoff baseline. Do not edit or delete the two controlling
documents except for a clearly labeled final evidence/status addendum required
by this plan.

Authority order for this task:

1. This implementation handoff and its frozen owner decisions.
2. [`rh-production-vyper-review-findings.md`](rh-production-vyper-review-findings.md)
   for evidence and rationale.
3. The pinned source and tests.
4. Existing Robinhood documentation that does not conflict with items 1–3.

The separate smart-contract test-coverage plan may be reused for test ideas,
but this handoff supersedes its older owner-decision gates and Uniswap scope
where they conflict. In particular, Defaults authority is decided and the
narrow Uniswap configuration-state fix is authorized here.

## 3. Execution rules

1. Verify that the clean handoff `HEAD` has exactly one parent, that `HEAD^` is
   the pinned commit/tree, and that the seed delta contains only the two named
   Markdown files before editing.
2. Require a clean isolated worktree at startup. Generated caches belong under
   a private temporary directory, not the repository.
3. Preserve unrelated user changes and do not edit other worktrees.
4. Make production changes only where a work package explicitly requires them.
5. Add or update required tests as part of the implementation pass, but do not
   run them package-by-package. Never weaken a correct expectation merely to
   make current code pass.
6. Do not recompile after every package. The only intentional mid-pass compile
   is the combined WP4/WP5 StabilityPool size check because that contract has
   approximately 202 bytes of headroom. Compile all changed contracts once
   more in the consolidated final phase. EIP-170 remains a hard gate.
7. Regenerate ABIs and governed artifacts only from the final exact source and
   pinned compiler settings.
8. In the final verification phase, run Boa suites in an environment that
   permits local socket binding. A
   sandbox failure at `tests/conf_env.py:119` from `free_port/socket.bind` is an
   environment error, not a contract result.
9. Continue through all work packages without opening test lanes between them.
   Obey the terminal conditions in Section 3.3; do not turn a hard safety
   failure into an unbounded refactor.
10. Preserve honest expected failures and exclusions. Do not convert the
    deferred Uniswap manipulation xfail into a pass, delete it, or hide it.
11. Run only the consolidated focused checks in Section 18. Record every
    outcome honestly and leave the complete serial suite to the subsequent
    independent review/test phase.

### 3.1 Package ordering and shared-file dependencies

Use this order:

1. WP0 establishes immutable identity and inventory without running tests.
2. WP1 reconciles Defaults and feeds final ABI/artifact work in WP10.
3. WP2 and WP3 reconcile the deployment sequence before deployment tests.
4. WP4 and WP5 are one StabilityPool bytecode lane: both change
   `StabVault.vy`, and the guarded pause may also require the smallest
   StabilityPool export/wrapper change. Compile and measure their combined
   production delta once as an early feasibility check, then measure again in
   the consolidated final phase.
5. WP6 and WP7 are one governance-position lane because they share
   RipeGov/Teller/Ledger state assumptions. Implement their tests together but
   defer execution.
6. WP8 and WP9 are independent after identity is bound.
7. WP10 runs only after every production source and compiler input is final.
8. WP11 completes the implementation pass; only then begin the single focused
   verification phase against that same exact candidate.

Do not regenerate an ABI, artifact, source hash, or size record between partial
changes and then carry it forward as final evidence.

### 3.2 Production-contract change budget and justification

The following are ceilings, not instructions to change every listed contract:

- **WP2 — `MissionControl.vy`:** D-08 explicitly selects constructor
  initialization. A migration-only setter call would produce the same immediate
  Robinhood state but would not implement the owner's chosen fresh-deployment
  invariant. Keep the constructor change and bind constants `1`/`2` to the
  Base and Robinhood migration ordering in CI.
- **WP4/WP5 — `StabVault.vy` and, only as needed, `StabilityPool.vy`:** an
  on-chain stale-price quarantine and guarded unpause cannot be supplied by a
  migration or runbook after an oracle fails. Prefer a StabilityPool-specific
  pause wrapper over a shared `VaultData.vy` change. A shared VaultData refactor
  is allowed only if Vyper module constraints make the wrapper impossible and
  its bytecode/behavior impact is proven across every consumer.
- **WP6 — `RipeGov.vy`:** D-05 changes runtime full-exit accounting; migration
  configuration cannot enforce it.
- **WP7 — Teller/RipeGov/Ledger composition:** a user-triggered atomic position
  migration must clean runtime Ledger participation in the same transaction.
  Change only the smallest contract surface that can express the already
  trusted cleanup; do not add a broad public Ledger permission.
- **WP8 — `SwitchboardBravo.vy`:** proposal and confirmation must reject a
  semantically wrong target on chain; deployment-only validation would not
  protect later governance rotations.
- **WP9 — `UniswapV2Prices.vy`:** the stale pending copy is overwritten inside
  confirmation. Only the contract can merge approved policy into the latest
  live snapshot state atomically.

`DefaultsRobinhood.vy` remains the semantic authority and should not change.
WP3 leaves `Ledger.vy` behavior unchanged. D-09 leaves `Erc20Token.vy`
unchanged. Do not modify `AuctionHouse.vy` or `Deleverage.vy` source.

### 3.3 Terminal stop-and-report conditions

Do not pause for an intermediate owner or design review. End implementation and
return the consolidated evidence report only if one of these hard conditions
is reached:

1. The exact commit/tree or clean documentation-seed boundary cannot be
   obtained.
2. The mandatory WP4 on-chain unpause guard cannot fit below EIP-170 after
   bounded, local optimization inside the authorized StabilityPool lane.
3. Success would require changing `AuctionHouse.vy`, `Deleverage.vy`, compiler
   settings, a frozen owner decision, or the deferred Uniswap manipulation
   policy.
4. Success would require a broad new ABI/storage/oracle architecture beyond the
   narrow state explicitly authorized here.
5. A changed contract still exceeds EIP-170 or a safety invariant cannot be
   satisfied without weakening a correct test.

When a terminal condition occurs, do not commit, push, or improvise a policy
change. Finish only independent work that remains safe, preserve the exact
evidence, and return one final blocked handoff identifying the condition and
smallest unresolved decision. This is a terminal report, not an intermediate
review phase.

## 4. Frozen owner decisions

These decisions are complete and must not be reopened by the implementation
agent.

| ID | Controlling decision |
| --- | --- |
| D-01 | Current pinned `DefaultsRobinhood.vy` values and seven-argument/no-Steakhouse structure are authoritative. Reconcile the repository to them; do not restore historical values. |
| D-02 | Preserve strict Stability Pool valuation. Add minimal paused stale-oracle quarantine/recovery by reusing dormant/prune/activation machinery. Mark every no-price quarantined pair, count them globally, and reject on-chain unpause until the count is zero. Never continue normal activity against silently zero-valued claim assets. |
| D-03 | Do not implement Uniswap TWAP, liquidity-floor, or manipulation defenses. Preserve the strict xfail and disclose the accepted risk. |
| D-04 | RipeGov disable must not calculate/checkpoint new points. It is an overflow/revert escape hatch; unsafe uncheckpointed accrual is intentionally not credited. |
| D-05 | A disabled user's partial exit preserves frozen points. A complete per-asset exit clears the already-stored points without calculating new accrual. |
| D-06 | Set dormant activation to `$0.10` and retention to `$0.05`. Add no aggregate dormant tracking. |
| D-07 | Keep Ledger's existing source constructor argument. Robinhood passes `0x64`; no constructor probe. Require exact immutable readback and a real-node ArbSys health call before registration. |
| D-08 | MissionControl initializes mutable `coreRipeGovVaultId = 2` and `preferredStabVaultId = 1`. Verify registry types after vault deployment and transition every setup-zero timelock to its approved nonzero value before Safe handoff. |
| D-09 | Keep `getCCIPAdmin()` exactly as implemented. Do not add a `tempGov` fallback. Test and regenerate ABIs around current behavior. |
| D-10 | Fix only Uniswap pending-configuration state overwrite. Preserve live snapshot progress and stored snapshot slots; do not redesign price formation. |

## 5. Explicit exclusions

Do not perform any of the following:

- Reintroduce Steakhouse into Robinhood Defaults, constructor inputs, active
  asset configuration, or priority liquidation.
- Restore old Defaults values such as `maxBorrowPerInterval = 50`, priority
  sources `[1, 3]`, or a zero bond restart delay.
- Add Uniswap TWAP, cumulative-price logic, minimum liquidity, or another
  manipulation defense.
- Add aggregate dormant-pair/value accounting.
- Add a Ledger constructor-time ArbSys call.
- Remove or behaviorally change `getCCIPAdmin()`.
- Change the documented behavior that Stability Pool positions are excluded
  from borrowing power but remain phase-2 liquidatable.
- Add a price check to `canAcceptLiquidationAsset` for the retracted F-08
  finding.
- Deploy, activate, push, merge, publish, or modify live-chain state.

Historical evidence may continue to mention Steakhouse or earlier values when
clearly labeled historical. Remove or update only material that falsely claims
those items are part of the current Robinhood deployment authority.

## 6. Work package 0 — Bind and inventory without test execution

### Actions

1. Enter the prepared worktree and verify its branch, clean status, parent
   commit/tree, and exact two-file documentation seed delta.
2. Record handoff `HEAD`, source-baseline `HEAD^`, both trees, merge base,
   status, Python, Vyper, Boa, and pytest identities.
3. Recompute the changed production Vyper manifest and confirm the same 20
   production paths listed in the review.
4. Record the already-established known-red evidence without rerunning it:
   - Defaults suite: 14 passed, 20 failed in the shared-object-store worktree.
   - Governed artifacts: four pass and five stale source hashes.
   - Uniswap: 74 passed and one strict xfail when run unsandboxed.
   - Runtime sizes: Deleverage 24,569; AuctionHouse 24,556; CreditEngine 24,392;
     StabilityPool 24,374.
5. Treat the reviewer's provisional `1,657 passed / 22 failed` adjacent-path
   observation only as historical context. Do not spend the implementation pass
   reproducing or diagnosing it.
6. Do not run pytest, Boa suites, ABI checks, artifact checks, or the complete
   serial suite in WP0. Begin implementation immediately after identity,
   cleanliness, and scope are confirmed.

### Completion evidence

- Exact identity record.
- Clean starting status.
- Confirmed 20-path production scope and recorded historical evidence.
- Confirmation that no pre-edit test suite was run.

## 7. Work package 1 — Reconcile Robinhood Defaults authority

### Production-source rule

`contracts/config/DefaultsRobinhood.vy` at the pinned head is the selected
authority. Do not change its semantics except for formatting required by an
approved tool. It must remain:

- Seven constructor arguments.
- No Steakhouse immutable or constructor argument.
- No Steakhouse `assetConfigs` entry.
- No Steakhouse priority-liquidation entry.
- Current values, including:
  - `maxBorrowPerInterval = 25 * EIGHTEEN_DECIMALS`.
  - Rewards availability `1_000_000 * EIGHTEEN_DECIMALS`.
  - HR availability `0`.
  - Bond availability `1_000_000 * EIGHTEEN_DECIMALS`.
  - Bond `amountPerEpoch = 100 * 10**6`.
  - Bond `maxRipePerUnit = 50 * EIGHTEEN_DECIMALS`.
  - Bond `restartDelayBlocks = 2 * HOUR_IN_BLOCKS`.
  - WETH `minDepositBalance = 5 * 10**14`.
  - Priority price sources `[1, 2]`.

### Required changes

1. Update `config/BluePrint.py` and every Defaults constructor consumer to pass
   exactly seven arguments and remove the Steakhouse binding.
2. Update the Robinhood Defaults generator/checker and canonical parameter
   records to emit the exact current source matrix.
3. Update `tests/config/test_defaults_robinhood.py` to assert all seventeen
   getter results literally, including every struct field, array length, order,
   nested entry, and constructor argument.
4. Remove current-authority claims that contradict the selected values or
   no-Steakhouse structure. Preserve historical records only when labeled as
   historical/superseded.
5. Regenerate `scripts/abis/DefaultsRobinhood.json` from the exact source.
6. Update governed artifact expectations for Defaults only after the complete
   source/compiler input is final.

### Required tests

- Constructor succeeds with seven arguments and rejects an obsolete eighth.
- All seventeen getters match the literal matrix.
- No generated deployment input or active configuration contains Steakhouse.
- Exact asset and priority-array lengths/orders are asserted.
- Parameter generation/check mode is idempotent and clean.
- `tests/config/test_defaults_robinhood.py` is fully green.

### Acceptance

No source, test, ABI, Blueprint, generator, parameter ledger, or current launch
document disagrees about the seven-argument contract or current values.

## 8. Work package 2 — MissionControl pointers and setup finalization

### Production changes

In `contracts/data/MissionControl.vy`:

1. Add readable named constants for RipeGov vault ID `2` and StabilityPool vault
   ID `1`.
2. In `__init__`, assign the existing mutable public storage fields:
   - `self.coreRipeGovVaultId = 2`.
   - `self.preferredStabVaultId = 1`.
3. Mark StabilityPool ID `1` in `self.isStabVaultId` during initialization.
4. Do not make the public fields immutable and do not remove Charlie's
   governed rotation setters.

This constructor behavior is intentional owner policy, not an accidental
substitute for a migration call. Do not replace it with migration-only setter
calls.

MissionControl is deployed before the vault contracts, so its constructor must
not attempt a target-interface call. Numeric initialization is followed by
post-vault deployment verification.

### Migration changes

In the Robinhood migration sequence:

1. After `migrations/robinhood-mainnet/0004_Vaults.py` deploys the vaults,
   assert:
   - ID `1` resolves to StabilityPool and passes its interface probes.
   - ID `2` resolves to RipeGov and passes its interface probes.
   - MissionControl returns `preferredStabVaultId == 1` and
     `coreRipeGovVaultId == 2`.
   - `isStabVaultId(1)` is true.
2. In `0007_FinishSetup.py`, execute the 12 component finalizations that
   correspond to contracts actually deployed by the pinned Robinhood sequence,
   before `finishRipeHqSetup`:
   - Five action timelocks: Alpha, Bravo, Charlie, Delta, and Echo.
   - Two price-source action timelocks: Chainlink and Curve.
   - HumanResources' action timelock.
   - Four registry timelocks: Switchboard, PriceDesk, VaultBook, and RipeHq.
   `BlueChipYieldPrices` is not deployed at this candidate: its block in
   `0003_PriceSources.py` is commented out. Do not fetch or finalize it in
   `0007_FinishSetup.py`, and do not turn this work package into authorization
   to deploy it.
3. Use each component's approved minimum when calling
   `setActionTimeLockAfterSetup()` unless an exact approved nonminimum value is
   already present in `BluePrint.py`.
4. Read every required delay back and assert it is nonzero and equals the
   selected value before `finishRipeHqSetup` transfers governance to the Safe.
5. Preserve the irreversible handoff as the final operation.

### Required tests

- Fresh MissionControl immediately returns IDs `2` and `1`.
- A CI test binds StabilityPool/RipeGov to IDs `1`/`2` in both
  `migrations/base-mainnet/1008_VaultBook.py` and
  `migrations/robinhood-mainnet/0004_Vaults.py`; reordering either migration
  without updating the approved invariant fails.
- Charlie can still rotate each pointer after setup and preserves its existing
  target-interface/pause validation.
- Wrong registry order, wrong type, zero pointer, or paused target fails the
  deployment verification.
- Setup begins with zero action delay where intended.
- Finish setup moves every required component to its approved nonzero delay.
- The migration evidence contains one pre-state, transaction result, and exact
  post-state row for each of the 12 deployed-component finalization calls, plus
  proof that no absent BlueChip contract was fetched or called.
- No pointer or timelock assertion occurs after Safe handoff.

## 9. Work package 3 — Ledger Robinhood deployment proof

### Contract rule

Keep `contracts/data/Ledger.vy` behavior unchanged:

- Constructor retains `_actionBlockSource`.
- Zero selects native mode outside Robinhood.
- Exact `0x64` selects ArbSys mode.
- Every other address reverts.
- Do not add a constructor-time precompile probe.

### Deployment changes

In `migrations/robinhood-mainnet/0001_Registries.py` and the live Robinhood
profile:

1. Require the intended constructor input to be exact `0x64`.
2. Immediately after deployment and before registry registration, call the
   deployed `ACTION_BLOCK_SOURCE()` getter through the node and require exact
   `0x0000000000000000000000000000000000000064`.
3. Separately call `getArbActionBlock()` through the real node and require a
   successful exactly decoded nonzero value.
4. Treat the second call only as precompile-health evidence; it does not prove
   the selected immutable.
5. A live Robinhood run must reject a missing RPC, a Boa-only/local RPC, native
   override, getter mismatch, failed call, malformed return, or zero result.
6. Keep native override support only in explicitly local/fork/non-Robinhood
   profiles. It must not be possible for a generic environment variable to
   select native mode in the live Robinhood profile.
7. Correct comments and documents that claim Ledger's constructor already
   probes `arbBlockNumber()`.

### Required tests

- Live-profile input accepts exact `0x64` and rejects zero/native/other values.
- A mocked deployment with stored native mode fails pre-registration even when
  hard-coded `getArbActionBlock()` returns nonzero.
- Exact immutable readback plus valid ArbSys result passes.
- Missing/malformed/zero ArbSys response fails.
- Native non-Robinhood Ledger tests remain green.
- Constructor-probe-removal tests and docs describe the same chosen behavior.

## 10. Work package 4 — Minimal stale-oracle quarantine and recovery

### Design constraint

StabilityPool currently has approximately 202 bytes of deployed-runtime
headroom. Do not add a large new quarantine registry or broad emergency
write-down system. Reuse the existing global pause, active/dormant distinction,
pruning, activation, balances, liabilities, and events.

The unpause protection is a hard on-chain invariant. A runbook-only instruction
is not an acceptable fallback because a no-price quarantine may exclude an
unbounded principal from NAV, and price-source restoration is publicly visible.
A single counter without per-pair identity is also insufficient: activating an
ordinary dormant pair could otherwise decrement the wrong obligation.

Before completing the broad WP4/WP5 test matrix, implement the smallest
compiling production prototype containing the quarantine marker, count,
guarded pause path, and new `$0.10/$0.05` constants. Measure the combined
StabilityPool runtime immediately. If the mandatory behavior cannot be kept
below 24,576 bytes after bounded local optimization, trigger Section 3.3 rather
than downgrading the guard.

### Required behavior

Implement the following minimal state transition in
`contracts/vaults/modules/StabVault.vy` and exports/tests as needed:

1. Governance/Switchboard pauses StabilityPool through the existing pause path.
2. While paused, maintenance may deactivate an **active** claim pair whose
   non-raising USD-price lookup returns zero.
3. Record the transition on chain before removing the active-list entry:
   - Mark the exact `(stabAsset, claimAsset)` pair as no-price quarantined.
   - Increment one global no-price quarantine count exactly once.
   - Use fail-closed arithmetic and prevent duplicate marking.
4. Deactivation removes only the active-list entry. It must preserve:
   - `claimableBalances[stabAsset][claimAsset]`.
   - `totalClaimableBalances[claimAsset]`.
   - Actual token custody.
   - All user shares.
5. Emit the existing deactivation event with a new explicit no-price reason.
   Do not mislabel it as dust or zero balance.
6. The affected pool remains paused while the asset is unpriced. Deposits,
   withdrawals, transfers, claims, redemptions, and liquidations already
   guarded by the global pause must remain unavailable.
7. An unpriced dormant pair cannot reactivate because the non-raising price is
   zero.
8. Governance may configure a working replacement price source through the
   existing oracle/configuration system. While still paused, any caller may use
   the existing activation maintenance path once the value meets the selected
   activation threshold and capacity is available.
9. A successful activation of a marked pair must clear only that pair's marker
   and decrement the global count exactly once. Activating an ordinary dormant
   pair must not change the quarantine count.
10. Replace the direct unguarded StabilityPool pause export with the smallest
    StabilityPool-specific path that preserves the existing `pause(bool)` ABI,
    Switchboard authorization, state flag, and event. Every attempt to change
    from paused to unpaused must assert the global no-price quarantine count is
    zero. No authorized Switchboard may bypass the guard.
11. Only after every marked pair has been successfully reactivated may
    governance unpause normal operations.
12. Add no haircut, confiscation, liability deletion, forced claim, or silent
   zero-NAV continuation. No exact haircut was owner-approved.

Use the minimum state that is actually sufficient: an internal per-pair marker
plus a global count with the cheapest usable readback. Prefer implementing the
guard in `StabVault.vy` plus a StabilityPool-specific pause export/wrapper. If
Vyper module rules force a shared `VaultData.vy` refactor, preserve the exact
pause ABI/event/authorization for every vault and measure/retest every affected
runtime; do not silently broaden shared semantics.

### Required tests

- One active stale/reverting feed reproduces the pre-fix NAV/operation freeze.
- Pause succeeds without requiring the failing price.
- While paused, the active unpriced pair can be deactivated with the exact
  no-price reason.
- The exact pair marker and global count transition from false/zero to true/one.
- Custody, pair liability, total liability, shares, and unrelated pairs do not
  change during deactivation.
- Normal activity remains blocked while paused.
- Unpause reverts on chain while the global no-price quarantine count is
  nonzero, regardless of which authorized Switchboard initiates it.
- Activation at price zero is a no-op and cannot erase liability.
- After an alternate/restored price becomes valid, activation succeeds while
  paused, clears that pair marker/count exactly once, and restores strict NAV.
- Multiple quarantined pairs count independently; reactivating one still leaves
  unpause blocked until all are recovered.
- Activating or pruning an ordinary dormant/dust pair cannot decrement or clear
  a no-price quarantine.
- Unpause and normal deposit/withdraw/claim behavior succeed only after the
  recovery sequence.
- A priced active asset cannot use the no-price quarantine branch.
- Unaffected Stability Pool behavior and liquidation fallback remain intact.
- Runtime remains below 24,576 bytes with an exact recorded size.

## 11. Work package 5 — Dormant thresholds and routing regression

### Production changes

In `contracts/vaults/modules/StabVault.vy`:

- Set `ACTIVATION_USD_THRESHOLD = 10 * 10**16` (`$0.10`).
- Set `RETENTION_USD_THRESHOLD = 5 * 10**16` (`$0.05`).
- Preserve the exact `>= activation` and `< retention` boundary semantics.
- Add no aggregate dormant count/value storage.

### Required tests

- `$0.099...` remains dormant and `$0.10` activates.
- `$0.05` remains active and a value below `$0.05` prunes.
- Values between `$0.05` and `$0.10` preserve the previous state, proving
  hysteresis.
- Permissionless activation remains allowed only while paused.
- Later claimable inflow crossing `$0.10` auto-activates.
- Existing dormant liability/custody invariants remain exact.
- Add a regression proving the retracted F-08 concern remains false: pricing or
  fallback happens before collateral transfer, and no duplicate preflight price
  check is introduced.

Update current Stability Pool documentation and monitoring thresholds. Record
the accepted residual aggregate/value-appreciation risk.

## 12. Work package 6 — RipeGov overflow escape and full-exit cleanup

### Preserve the emergency path

Do not checkpoint or calculate new points in either disable function. Preserve
the irreversible global/user disable markers and the ability to operate on
position balances without invoking the unsafe accrual calculation.

### Full-exit behavior

For every withdrawal or transfer path that can reduce a disabled user's
per-asset shares to zero:

1. Partial exit:
   - Update shares/position metadata.
   - Preserve the already-stored `govPoints` exactly.
   - Do not calculate new accrual or a proportional penalty.
2. Full per-asset exit:
   - Do not calculate new accrual.
   - Capture the already-stored points for that asset.
   - Set the per-asset stored points to zero.
   - Subtract exactly that captured amount from `totalUserGovPoints[user]` and
     `totalGovPoints`, with existing invariant checks/fail-closed arithmetic.
   - Preserve correct unlock/terms/share cleanup.
3. Apply the rule consistently to direct withdrawals, full internal transfers,
   contributor transfers, liquidation-authorized withdrawal paths, and any
   other route that can deplete the disabled user's asset position.
4. Do not award the removed frozen points to the transfer recipient.
5. Canonical RipeGov totals must update atomically. Do not make the emergency
   exit depend on a potentially reverting external Boardroom callback. If a
   downstream Boardroom notification is required, record a pending sync and
   expose a separately retryable synchronization path, or use the repository's
   existing nonblocking pattern. Never strand the asset exit.

### Required tests

- Construct a state where the normal latest-points calculation demonstrably
  overflows/reverts.
- Per-user and global disabling still succeed from that state.
- Uncheckpointed accrual is not credited.
- Partial withdrawal and transfer preserve frozen points.
- Full withdrawal and full transfer clear the per-asset points and decrement
  user/global totals exactly.
- One asset's full exit does not clear another asset's saved points.
- Repeated full-exit cleanup is idempotent or fails safely without underflow.
- Bad-debt and unlock restrictions remain enforced.
- A reverting Boardroom cannot block the emergency balance exit.
- Events and views expose the final canonical totals.

The pinned tests
`test_disabled_withdrawals_keep_points_frozen_and_still_enforce_unlock` and
`test_disabled_sender_can_transfer_balance_without_moving_or_zeroing_points`
encode the old all-exits-keep-points behavior. D-05 expressly supersedes that
expectation only at the complete per-asset exit boundary:

- Retain their partial-exit and unlock assertions unchanged.
- Split or rename their full-exit cases so a partial withdrawal/transfer keeps
  frozen points while a full withdrawal/transfer clears them and reconciles
  totals.
- Do not weaken the old tests wholesale or treat their expected failure as a
  regression exemption.

Update comments and documentation to state that forfeiting unsafe pending
accrual is intentional liveness behavior.

## 13. Work package 7 — Atomic RipeGov position migration cleanup

### Required production behavior

In the Teller/RipeGov/Ledger migration composition:

1. Preserve atomic export, exact token receipt proof, and import.
2. After successful import and before registering the target Ledger position:
   - Prove the source vault reports no remaining user assets/balance for the
     migrated position.
   - Remove the source vault ID from the user's Ledger participation list.
3. Allow this removal through the smallest purpose-appropriate trusted path.
   Prefer a narrowly authorized Teller migration cleanup over a broad public
   Ledger permission. Do not rely on a later Lootbox claim for cleanup.
4. Add the target vault only after source removal. This prevents migration from
   temporarily or permanently exceeding the configured vault-position limit.
5. If the target Ledger entry already exists, do not duplicate it.
6. If the target vault has a stale zero-balance internal asset registration,
   clean it atomically before import or accept it only through an exact
   zero-state path. Never merge nonzero target balance or governance data.
7. Preserve the source tombstone and all replay protections.
8. Any failure reverts export, transfer, import, Ledger changes, points, and
   events as one transaction.

### Required tests

- Source Ledger entry is removed and target entry added on success.
- User at the maximum vault count remains at the maximum rather than exceeding
  it.
- Existing target Ledger entry is not duplicated.
- Stale zero target registration is handled as specified.
- Nonzero target balance/data still rejects.
- Source cleanup failure reverts the entire migration.
- Repeated migration and reverse migration remain blocked by tombstones.
- Batch Echo migration preserves per-user atomicity and emits exact events.

## 14. Work package 8 — Bravo special Stability Pool type validation

### Production changes

In `contracts/config/SwitchboardBravo.vy`:

1. Preserve the existing nonzero and VaultBook-valid-ID checks.
2. Resolve the target address and require nonzero contract code.
3. Probe the same minimum Stability Pool capability used by Charlie, including
   `totalClaimableBalances(...)` and `isPaused()` or the smallest equivalent
   interface proof.
4. Apply the probe to every nonzero `specialStabPoolId` proposal and again at
   confirmation through the existing full-config validation.
5. Do not alter Charlie's already-correct preferred-pool probes.
6. Preserve MissionControl's intentional monotonic classification only after a
   target passes validation.

### Required tests

- Valid StabilityPool ID passes.
- Zero ID remains allowed where current semantics allow it.
- Valid VaultBook ID pointing to SimpleErc20, RipeGov, an EOA, or a partial
  interface mock fails.
- Revalidation at confirmation catches target/config drift.
- A failed proposal/confirmation never marks `isStabVaultId`.
- Existing Charlie tests remain green.

## 15. Work package 9 — Narrow Uniswap pending-state preservation

### Production changes

Keep the existing `PriceConfig` and `PendingPriceConfig` storage/ABI layout to
avoid a broad migration. At confirmation:

1. Load the latest live `priceConfigs[asset]`.
2. Copy only these four approved policy fields from the pending config:
   - `minSnapshotDelay`.
   - `maxNumSnapshots`.
   - `maxUpsideDeviation`.
   - `staleTime`.
3. Preserve the latest live `lastSnapshot`.
4. Preserve `nextIndex` when it remains in range. If the ring shrinks below the
   live index, clamp deterministically to `nextIndex % newMaxNumSnapshots`.
5. Do **not** clear or rewrite snapshot slots solely because the configured
   window shrinks. `_getWeightedPrice` already reads only indices below the live
   `maxNumSnapshots` and applies the existing stale-time filter. Preserving
   stored slots avoids turning this state-overwrite fix into a price-formation
   change; if the window is later expanded, still-valid retained samples follow
   the pre-existing behavior.
6. Save the merged live config, clear pending state, then attempt the normal
   snapshot using the merged config.
7. Ensure replacing or canceling a pending action clears/bookkeeps the old
   action consistently with the existing timelock model.

Do not add cumulative prices, TWAP, liquidity checks, or change the spot-price
formula.

### Required tests

- Multiple snapshots during the timelock are preserved at confirmation.
- `lastSnapshot` never rewinds.
- Cursor progression remains correct for unchanged, expanded, and shrunk
  windows.
- Shrinking does not mutate out-of-window snapshot storage.
- Immediately after shrink, the weighted price equals the exact arithmetic mean
  of valid retained samples in indices `[0, newMaxNumSnapshots)`.
- A later expansion includes only stored samples that remain valid under the
  unchanged stale-time and zero-sample filters.
- A changed minimum delay cannot cause confirmation to overwrite live progress
  when the immediate snapshot is ineligible.
- Replaced/cancelled proposals do not leave usable orphan actions.
- Existing 74 passing Uniswap tests remain green.
- The one strict manipulation xfail remains present, strict, and honestly
  reported.

## 16. Work package 10 — ABI, selector, artifact, and bytecode reconciliation

### Teller and Defaults

1. Regenerate `scripts/abis/Teller.json` so the four removed single-item
   selectors and obsolete overloads are absent.
2. Regenerate `scripts/abis/DefaultsRobinhood.json` with the seven-argument
   constructor.
3. Produce a selector diff and search every script, frontend reference, SDK,
   proposal, and deployment caller for removed Teller entry points.
4. Update in-repository consumers to batch APIs. Record external consumers that
   cannot be edited here.

### Token ABIs

Regenerate `Erc20Token`, `GreenToken`, `RipeToken`, and `SavingsGreen` ABIs so
the retained `getCCIPAdmin()` selector is present. Add direct tests proving:

- Current pre-setup behavior, including revert if `ripeHq == 0`.
- Post-setup return equals `RipeHq.governance()`.
- No `tempGov` fallback was introduced.

### All changed contract artifacts

After all production source changes are final:

1. Regenerate every affected ABI and governed artifact.
2. Recompute source hashes, transitive compiler-input integrity, creation
   bytes, runtime-template bytes, immutable-bound/deployed runtime where
   applicable, metadata, selectors, and layouts.
3. At minimum resolve the currently stale records for CreditEngine,
   DefaultsRobinhood, Ledger, Lootbox, and Teller, plus every contract changed
   by this remediation.
4. Update `config/contract-artifact-expectations.json` from actual compiler
   output. CreditEngine's pinned source currently measures a 24,296-byte
   runtime template, not the stale 24,151 record.
5. Reconcile AuctionHouse's deployed value to 24,556/20 under the pinned
   compiler. Remove or relabel the stale 24,549/27 claims.
6. Replace arithmetic-only `size + headroom == 24,576` assertions with
   compiler-backed exact comparisons, or label them only as frozen-record
   integrity checks.
7. Correct `basic-vault-fail-closed.md` so it no longer claims the arithmetic
   test independently measures AuctionHouse.

### Hard EIP-170 gate

Every deployed runtime must be `< 24,576` bytes. Record exact size and headroom
for all touched size-sensitive contracts after final compilation. Pay special
attention to:

- Deleverage: previously 7 bytes headroom; its source must remain unchanged.
- AuctionHouse: previously 20 bytes headroom; its source must remain unchanged.
- StabilityPool: previously 202 bytes headroom; keep D-02/D-06 minimal.
- CreditEngine: previously 184 deployed-runtime bytes headroom; avoid source
  changes unless independently required.

If an authorized touched contract exceeds EIP-170, attempt only bounded local
optimization within that package's existing approved behavior. If the breach
remains—or remediation would require changing Deleverage, AuctionHouse,
compiler settings, or a frozen decision—trigger Section 3.3. Do not remove
tests, alter measurement methods, or substitute a template measurement.

## 17. Work package 11 — Documentation and operational consistency

Update current documentation so it agrees with final source and decisions:

- Current Robinhood Defaults/no-Steakhouse matrix.
- MissionControl pointer initialization and vault-ID verification.
- Setup-zero versus post-setup nonzero timelocks.
- Ledger lazy validation, exact immutable readback, and separate ArbSys health
  check; remove all false constructor-probe claims.
- Stability stale-price pause/deactivate/reprice/reactivate runbook.
- `$0.10/$0.05` dormant thresholds and accepted aggregate residual risk.
- RipeGov overflow-disable rationale and full-exit point clearing.
- RipeGov migration Ledger cleanup.
- Bravo special Stability Pool target validation.
- Uniswap config-state preservation and separately deferred manipulation risk.
- Retained `getCCIPAdmin()` lifecycle behavior.
- Stability positions remain non-borrowing but phase-2 liquidatable.

Do not rewrite historical evidence as though it had always contained the new
facts. Mark superseded records or add dated corrections.

## 18. One consolidated end-of-pass verification

Do not enter this section until WPs 1–11 are implemented, documentation is
updated, and final ABIs/artifacts have been generated. There are no intermediate
review gates and no per-package test runs.

Use private mode-0700 temporary cache directories and a socket-capable test
environment. Perform one consolidated final compilation/runtime-size check,
then run the focused checks below once. If a focused check exposes an
implementation defect, fix it and rerun only the failed or directly affected
node(s). Do not restart the entire focused batch and do not run the complete
repository serial suite in this implementation assignment.

### Single focused batch

At minimum:

1. `tests/config/test_defaults_robinhood.py`
2. `tests/data/test_mission_control.py`
3. Relevant Robinhood migration/deployment tests
4. `tests/data/test_ledger_action_block.py`
5. `tests/deployment_profiles/test_ledger_robinhood_profile.py`
6. `tests/vaults/modules/test_stab_vault_hardening.py`
7. `tests/vaults/modules/test_stab_vault_claims.py`
8. `tests/vaults/modules/test_stab_vault_redemptions.py`
9. `tests/vaults/modules/test_stab_vault_claim_data_fuzz.py`
10. Relevant AuctionHouse Stability Pool liquidation suites
11. `tests/vaults/test_ripe_gov_controls_and_migration.py`
12. `tests/config/test_switchboard_bravo.py`
13. `tests/priceSources/uniswap/`
14. Direct token/CCIP admin lifecycle tests
15. `tests/test_vault_pointer_runtime_sizes.py`
16. `tests/core/deleverage/test_deleverage_phase2.py::test_actual_deployed_runtime_stays_under_eip170`
17. `tests/deployment/test_abi_export.py`
18. `tests/inventory/test_contract_artifacts.py`
19. `scripts/check_contract_artifacts.py`

`tests/test_vault_pointer_runtime_sizes.py` does not measure Deleverage or
AuctionHouse. The named phase-2 test is the controlling deployed-runtime gate
for their exact 24,569/7 and 24,556/20 measurements. The ABI-export suite is the
byte-for-byte repository gate for regenerated `scripts/abis/` output.

### Consolidated final gates

- Compile every changed production contract from the final source and record
  exact deployed runtime sizes/headroom.
- Run the listed focused contract, migration, ABI, artifact, and size checks in
  one end-of-pass batch or the smallest practical set of final commands.
- Preserve the strict Uniswap manipulation xfail as the accepted open security
  xfail from this remediation. Explain every other final skip/xfail/failure.
- If a focused test fails because of the implementation, fix the defect and
  rerun only that node and directly coupled nodes.
- Do not run a pre-edit suite, do not run suites between work packages, and do
  not run the complete repository-wide serial suite. The independent reviewer
  will run broader/full-suite testing after this implementation handoff.
- Run runtime-size and artifact checks only from the final source/compiler
  inputs, except for the single early WP4/WP5 StabilityPool feasibility compile.

### Requirements for tests added or updated during implementation

- Assert exact state, balances, liabilities, points, IDs, selectors, events,
  and revert reasons—not only transaction success.
- Prove rollback on every failed cross-contract transition.
- Include boundary values immediately below, at, and above thresholds.
- Include wrong-interface but valid-registry targets.
- Include multiple state changes during timelocks.
- Include repeated/idempotent calls and batch behavior.
- Never count an environment error as a passing or failing contract test.

## 19. Definition of done

The task is complete only when all of the following are true:

1. Every work package in Sections 6–17 is implemented or explicitly marked as
   an owner-approved exclusion from Section 5.
2. Defaults source, BluePrint, generator, parameters, tests, ABI, and artifacts
   agree on the current seven-argument/no-Steakhouse matrix.
3. MissionControl pointers are initialized to `2`/`1`, bound by CI to both Base
   and Robinhood vault ordering, and registry-verified. All 12 deployed-component
   setup finalizations have exact nonzero readback evidence before Safe handoff;
   absent BlueChip is neither fetched nor finalized.
4. Robinhood Ledger registration proves both exact immutable `0x64` selection
   and separate live ArbSys health.
5. StabilityPool has a tested, liability-preserving paused recovery route for
   active assets whose price becomes unavailable, and on-chain unpause reverts
   until every marked no-price quarantine is reactivated and the global count
   is zero.
6. Dormant thresholds are exactly `$0.10/$0.05` with hysteresis tests.
7. RipeGov disable remains a no-update overflow escape, while a disabled full
   per-asset exit clears stored points and totals without blocking asset exit.
8. RipeGov migration atomically removes stale source Ledger participation and
   does not exceed the position-count assumption.
9. Bravo rejects non-StabilityPool special IDs before monotonic classification.
10. Uniswap confirmation preserves intervening live snapshot state and stored
    snapshot slots; no manipulation-defense or price-formation change is
    present.
11. `getCCIPAdmin()` remains behaviorally unchanged and all relevant ABIs/tests
    represent it honestly.
12. Every governed artifact and runtime-size record matches actual final
    compiler output.
13. Every touched deployed runtime is below EIP-170.
14. The single final focused verification batch is green except the explicit
    strict Uniswap manipulation xfail. Any focused failure that remains is
    reported honestly. The complete repository serial suite is explicitly
    deferred to the subsequent independent review/test phase and is not an
    implementation-agent completion gate.
15. The worktree contains no caches, logs, temporary artifacts, or unrelated
    changes.
16. No commit, push, deployment, activation, or live-chain mutation occurred
    without separate authorization.

## 20. Final handoff format

Return one final evidence report containing:

- Implementation branch/worktree path.
- Final commit and tree identities for the dirty or committed candidate.
- Exact OS, architecture, Python, Vyper, Boa, pytest, dependency-lock, compiler,
  and relevant environment identities used for final verification.
- Changed-file manifest grouped by work package.
- Per-package implementation summary and invariant mapping.
- Exact final focused commands with pass/fail/error/skip/xfail/xpass counts and
  any narrowly rerun failed/coupled node IDs.
- Explicit confirmation that no pre-edit, per-package, or complete repository
  serial suite was run under this implementation assignment.
- Exact final runtime sizes and headroom.
- ABI selector diffs and artifact-check results.
- SHA-256 for every regenerated ABI and governed artifact, recomputed from the
  final bytes on disk with `shasum -a 256 <path>` (or a byte-equivalent tool).
  List the exact command and path set; never copy digests forward from prose.
- Any external consumer that still uses removed Teller selectors.
- The retained Uniswap manipulation exception.
- Residual risks, especially dormant aggregate exposure and any operational
  dependency in stale-oracle recovery.
- Confirmation that no commit/push/deploy/activation occurred unless separately
  authorized.
- Any Section 3.3 terminal condition, the exact evidence proving it, and the
  smallest unresolved scope—without silently claiming Definition of Done.

Do not return an intermediate review request. Complete the entire authorized
implementation pass and single focused end verification, then return the
consolidated handoff for independent review/full-suite testing.
