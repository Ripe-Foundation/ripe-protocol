# Independent Review of the `rh` Production Vyper Review

## 1. Executive verdict

**Release posture: NO-SHIP.**

The prior smart-contract review contains several useful source-level findings,
but it is not sufficient release evidence and its conclusion that the branch is
"almost safe" is not supported. The pinned `rh` candidate has a Defaults
authority decision that is not yet reconciled across the repository, red
exact-head validation, stale ABIs and governed artifacts,
deployment-sequencing hazards, and material unaddressed contract risks.

This document records the independent review findings so they can be assigned,
resolved, retested, and closed without relying on the original Codex task.

No production deployment or integration approval is granted by this document.

## 2. Review target and evidence boundary

The findings are bound to this immutable review target:

- Branch: `rh`
- Pull request: [PR #67](https://github.com/Ripe-Foundation/ripe-protocol/pull/67)
- Head commit: `7d8c76e5134bf866ccbb051fdf5030b6e83cef8b`
- Head tree: `1d115e9a01f01f933e3e80747902080387f2113c`
- Compared with: `master` at
  `91eda49ccd34a25090582aff0695075c4c806011`
- Merge base: `91eda49ccd34a25090582aff0695075c4c806011`
- Review date: 2026-08-06
- Errata verification date: 2026-08-06
- Document revision: 2
- Production Vyper files changed: 20

At review time, GitHub reported no status checks and no review decision for the
pull request. That state is time-sensitive and must be refreshed before any
release decision.

All source references in this document refer to the pinned `rh` head above.
If the head commit or tree changes, the changed production Vyper scope and all
affected findings must be revalidated before this record is used.

A subsequent claim-by-claim verification pass adjudicated 139 statements in
revision 1 as 113 true, 21 partly true, 2 false, and 3 unverified. It reproduced
all measured byte sizes, artifact outcomes, Uniswap counts, and Defaults
arithmetic. Revision 2 incorporates the two hard errors, all supported severity
and attribution corrections, and the incidental CreditEngine artifact drift.

## 3. Validation evidence

The following checks were run in an isolated checkout detached at the exact
`rh` head. They did not modify the source worktree.

### 3.1 Defaults validation

`tests/config/test_defaults_robinhood.py` produced:

- 14 passed
- 20 failed

The dominant failure is the mismatch between the seven-argument source
constructor and the eight-argument constructor expected by `BluePrint.py`, the
committed ABI, the generator, and the tests. Independent failures also include
the expected `GREEN_POOL_MA_EXP_TIME` and deployment-readiness values.

Only four of the 20 failures were adjudicated as independent root causes. Most
of the remainder cascade from those causes. The earlier 13-passed/21-failed
tally came from an isolated object store in which a Git-object-dependent check
also failed; two reruns in a shared-object-store worktree both produced the
correct 14-passed/20-failed tally. The result must not be described as 20
distinct contract bugs. It nevertheless proves that the exact-head Defaults
gate is not green.

### 3.2 Governed contract artifacts

The artifact checker passed for:

- `AuctionHouse`
- `Deleverage`
- `SimpleErc20`
- `SwitchboardDelta`

It failed source-hash validation for:

- `CreditEngine`
- `DefaultsRobinhood`
- `Ledger`
- `Lootbox`
- `Teller`

Five of the nine governed artifact records checked are therefore stale against
the pinned source.

### 3.3 Runtime-size validation

The current runtime-size test passed for the relevant size-sensitive vault and
core contracts, including Deleverage even though it is outside the 20-file
production Vyper diff.
The most release-sensitive results were:

| Contract | Runtime bytes | EIP-170 headroom |
| --- | ---: | ---: |
| `Deleverage` | 24,569 | 7 bytes |
| `AuctionHouse` | 24,556 | 20 bytes |
| `CreditEngine` | 24,392 | 184 bytes |
| `StabilityPool` | 24,374 | 202 bytes |

The passing size test is useful, but the margins do not tolerate uncontrolled
compiler drift or even small source changes. The repository also contains
conflicting AuctionHouse size records, discussed in Finding F-13.

These four values were independently reproduced both through the repository
test and through standalone Boa compilation using each source file's
`#pragma optimize codesize`; no global `-O` override was applied.

### 3.4 Uniswap test evidence

The exact-head Uniswap suite produced:

- 74 passed
- 1 strict expected failure

The expected failure is recorded as pending an owner decision because spot
snapshots remain manipulable without a TWAP or liquidity floor. This is an open
security decision, not a green release result.

### 3.5 Test-environment caveat

The Boa suites require an environment that permits local socket binding. Under
the restricted sandbox used during verification, collection failed at
`tests/conf_env.py:119` when `free_port` called `socket.bind`, producing the
misleading result `1 xfailed, 74 errors in 0.35s`. The valid Uniswap result in
Section 3.4 came from an unsandboxed run. Future release records must state this
requirement and must not classify sandbox socket errors as contract failures.

### 3.6 Full-suite limitation

The complete serial suite was not rerun during this independent review because
the exact-head configuration and artifact gates already failed decisively.
Subsequent reviewer feedback reported a provisional `1,657 passed / 22 failed`
result within adjacent paths, but did not include the complete command,
per-file result, or failure node-ID manifest in the supplied record. It is a
warning that the baseline was not green, not an immutable measurement.

The owner later selected a faster execution workflow: the implementation agent
does not reproduce a full-suite baseline or run tests package-by-package. It
implements every authorized work package first, performs one consolidated
focused verification pass, and returns the result for a separate independent
review/full-suite phase.

## 4. Release-blocking findings

### F-01 — Defaults authority is decided but repository reconciliation is incomplete

**Severity:** BLOCKER

**Area:** `contracts/config/DefaultsRobinhood.vy`
**Status:** Owner decision recorded; repository-wide reconciliation remains open

The current contract source materially disagrees with the approved
configuration records, constructor consumers, committed ABI, tests, and launch
documentation.

The pinned source:

- Takes seven constructor arguments and removes the Steakhouse USDG vault.
- Allocates `1,000,000e18` RIPE to rewards.
- Allocates `0` RIPE to Human Resources.
- Allocates `1,000,000e18` RIPE to bonds.
- Omits Steakhouse from configured assets and priority liquidation.
- Returns priority price sources `[1, 2]` rather than `[1, 3]`.

Relevant source areas include `DefaultsRobinhood.vy:45-53`, `:124-137`,
`:251-404`, `:411-414`, and `:427-428`.

The same branch still contains contradictory authority and consumers:

- `config/BluePrint.py:403-412` supplies eight constructor arguments, including
  Steakhouse.
- `scripts/abis/DefaultsRobinhood.json` declares an eight-argument constructor.
- `tests/config/test_defaults_robinhood.py` expects the eight-argument form,
  active Steakhouse configuration, priority liquidation `[Steakhouse, WETH]`,
  and priority price sources `[1, 3]`.
- `config/robinhood-parameters.json` records rewards, Human Resources, and bonds
  at `1,000e18` RIPE each.
- `config/robinhood-reward-launch-plan.json` and
  `docs/chains/rh/reward-launch-qualification.md` describe a shared 1,000-RIPE
  launch budget.

The reward difference is economically material. At the configured rate of
`0.009 RIPE` per block and five blocks per minute, a 1,000,000-RIPE reward
allocation supports approximately 42 years of emissions rather than roughly
15.4 days. Stability claims can draw from that same enlarged reward pool. The
bond allocation is 1,000 times the recorded approval, while the Human Resources
allocation is zero.

On 2026-08-06, the owner selected the current pinned `rh` source as the intended
authority: retain the seven-argument constructor, remove every Steakhouse
dependency/configuration entry, and retain the current source values. The owner
specifically reconfirmed `maxBorrowPerInterval = 25 GREEN`, priority price
sources `[1, 2]`, and the two-hour bond restart delay, and reversed the earlier
instruction to restore the historical values.

This is an owner intent record, not independent proof of live deployed values.
The remaining blocker is atomic reconciliation of constructor consumers, ABIs,
tests, artifacts, parameters, deployment documentation, and launch evidence to
that selected source. The generated seventeen-getter matrix must enumerate the
current source literally and prove that no historical Steakhouse field or value
is reintroduced.

The prior review's statement that the Defaults are sensible is unsupported.

### F-02 — Exact-head validation and governed artifacts are red

**Severity:** BLOCKER

**Area:** Configuration and artifact release gates
**Status:** Open

The Defaults test result and governed-artifact failures in Section 3 establish
that the candidate is internally inconsistent. These are release-gate failures,
not documentation polish.

The prior review did not provide:

- Exact commands or test counts.
- Compiler, Python, Vyper, Boa, or dependency identities.
- Artifact source hashes.
- ABI or selector reconciliation.
- An explanation of known-red or environment-dependent tests.

Required closure:

1. Resolve F-01.
2. Regenerate every governed artifact from the approved exact source.
3. Re-run the artifact checker without exclusions.
4. Re-run the Defaults tests on the same immutable candidate.
5. Preserve commands, environment identities, and complete output as release
   evidence.

### F-03 — Committed ABIs disagree with production source

**Severity:** BLOCKER

**Area:** `Teller` and `DefaultsRobinhood` integration surfaces
**Status:** Open

The new Teller source removes four single-item entry points:

- `redeemCollateral`
- `buyFungibleAuction`
- `claimFromStabilityPool`
- `redeemFromStabilityPool`

The committed `scripts/abis/Teller.json` still advertises these removed calls in
multiple overload variants. Clients generated from this repository artifact can
therefore encode calls to selectors that no longer exist and revert at runtime.

The committed Defaults ABI independently retains the obsolete eight-argument
constructor while the source accepts seven arguments.

The prior review correctly calls the Teller source change breaking, but misses
that the repository's own published integration artifacts are already stale.

Required closure:

- Regenerate both ABIs from the approved source.
- Produce an old-to-new selector inventory.
- Identify every script, frontend, bot, deployment tool, SDK, and external
  integrator that consumes the removed selectors or constructor.
- Add runtime tests showing the removed selectors are not callable and the
  supported batch selectors remain callable.
- Do not deploy until all in-scope consumers are migrated.

### F-04 — Core vault pointers can remain zero through ownership handoff

**Severity:** BLOCKER

**Area:** `contracts/data/MissionControl.vy` and deployment migrations
**Status:** Open

`MissionControl` declares `coreRipeGovVaultId` and `preferredStabVaultId`, but
the constructor does not initialize them. The Defaults interface does not
supply them. The existing vault and finish-setup migrations do not set them
before the ownership handoff sequence.

The relevant evidence includes:

- `MissionControl.vy:195-198` — exact pointer storage names.
- `MissionControl.vy:220-259` — constructor without pointer initialization.
- `migrations/robinhood-mainnet/0004_Vaults.py` — IDs are deterministically
  assigned as StabilityPool `1`, RipeGov `2`, and SimpleErc20 `3`, but the two
  MissionControl pointers are not set.
- `migrations/robinhood-mainnet/0007_FinishSetup.py` — setup proceeds toward
  Safe ownership handoff without setting either pointer.

The Charlie setter paths validate the target interfaces and require the target
vault to be unpaused. Contrary to revision 1, they do **not** currently enforce
a delayed correction: `SwitchboardCharlie` is constructed with
`actionTimeLock = 0`, and the call to `setActionTimeLockAfterSetup()` is
commented out in `0007_FinishSetup.py`. As migrated, a post-handoff correction
can be made through two back-to-back Safe transactions with zero enforced block
delay. The pointer omission remains a deployment blocker, while the zero-delay
state is a separate governance-hardening concern.

Required closure:

- In `MissionControl.__init__`, initialize the existing mutable storage fields
  from named constants: `coreRipeGovVaultId = 2` and
  `preferredStabVaultId = 1`.
- Do not make the public pointers themselves immutable; preserve Charlie's
  governed future-rotation path and existing ABI.
- Mark ID `1` as a Stability Pool classifier during initialization.
- Fail deployment when either pointer is zero, invalid, paused, or the wrong
  semantic vault type.
- Because MissionControl deploys before VaultBook and its vaults, validate after
  `0004_Vaults.py` that IDs `1` and `2` resolve to the intended contracts and
  interfaces.
- Execute and verify the 12 component finalizations backed by the pinned
  deployment sequence before Safe handoff: five switchboards, two deployed
  price sources (Chainlink and Curve), HumanResources, and four registry
  timelocks. `BlueChipYieldPrices` is commented out in
  `0003_PriceSources.py`; do not fetch/finalize or deploy it under this item.
- Read the deployed values back from chain and record them in the deployment
  manifest.
- Test the deployment ordering, zero-delay setup behavior, post-setup minimum
  delay, and failure conditions.

### F-05 — One stale active oracle can freeze Stability Pool operations

**Severity:** HIGH / release blocker; remediation decided

**Area:** `contracts/vaults/modules/StabVault.vy` and StabilityPool pause export
**Status:** Open

`_getValueOfClaimableAssets` loops over active claimable assets and requests
strict pricing. A stale, reverting, or otherwise unusable feed for one active
asset can revert the entire NAV computation.

That NAV path is consumed by major operations, including:

- Deposits.
- Withdrawals.
- Claims and redemption accounting.
- Total-value views.
- Downstream liquidation paths that rely on Stability Pool accounting.

Relevant source areas include `StabVault.vy:153-206`, `:381-385`, `:597-618`,
and `:749-755`.

The pruning path does not provide reliable self-recovery. It prices
non-strictly, but only deactivates when `usdValue != 0` and the value is below
the dormant floor. An active asset with no usable price therefore cannot be
pruned by that mechanism (`StabVault.vy:1174-1184`).

The branch's own Stability Pool handoff material acknowledges the stale-feed
denial-of-service condition. The prior review omits it.

The owner selected strict/fail-closed valuation plus a minimal paused
quarantine/recovery path. That path must mark each exact no-price pair, maintain
a global quarantine count, preserve custody/liabilities/shares, and reject
unpause on chain until every marked pair has been reactivated. A runbook-only
pause requirement is insufficient because the excluded principal can be
unbounded and feed restoration is publicly observable.

### F-06 — Uniswap manipulation posture remains explicitly unresolved

**Severity:** HIGH / deferred accepted risk

**Area:** `contracts/priceSources/UniswapV2Prices.vy`
**Status:** Owner acknowledged and deferred; excluded from current implementation

The suite contains a strict expected failure stating that spot snapshots remain
manipulable without a TWAP or minimum-liquidity floor. A strict security xfail
pending an owner decision cannot be summarized as a green or safe result.

Setting RIPE LTV to zero limits a borrowing-related blast radius, but it does
not prove that every protocol or operator consumer of the price is harmless.
The complete consumer inventory and economic consequences remain controlling.

Required closure:

- No TWAP, liquidity-floor, or other manipulation-defense source change is
  authorized in the current remediation.
- Preserve the strict xfail and report it as an accepted open risk rather than
  a passing security gate.
- Before release, record every consumer, the bounded zero-LTV blast radius,
  monitoring, emergency response, and conditions that would reopen or retire
  the exception.

### F-07 — RipeGov disable intentionally skips unsafe accrual; full-exit semantics are decided

**Severity:** MEDIUM documentation/test gap; saved-point remediation required

**Area:** `contracts/vaults/RipeGov.vy`
**Status:** D-04 and D-05 decided

The disable setters record a disable block without first checkpointing the
user's accrued governance points. Once disabled, the update logic skips normal
point accrual and advances the last-update marker. Points earned after the prior
checkpoint but before disabling are therefore not credited.

On 2026-08-06, the owner clarified that this is intentional. The feature exists
to recover when calculating the next points update would overflow or otherwise
revert. Calling the unsafe update from the disable path would defeat the escape
hatch and could make the user impossible to disable. No checkpoint-on-disable
change is authorized.

The remaining gap is evidence: existing tests establish disabled-state
mechanics but do not explicitly construct an overflow-causing points state,
show that the ordinary update fails, and then prove that disabling still
succeeds and restores position-operation liveness.

The implementation also allows a disabled user to withdraw or transfer all
backing while retaining the already saved governance points indefinitely.
Tests explicitly expect this. Under D-05, that behavior must change only at the
full-exit boundary: partial emergency withdrawals preserve frozen points, while
a zero-balance exit clears the already-stored points without calculating new
accrual.

Required closure:

- Preserve the no-update disable path and intentional forfeiture of unsafe,
  uncheckpointed accrual.
- Document the overflow/revert recovery rationale and irreversible semantics.
- Add a test in which an ordinary points update demonstrably reverts from the
  unsafe state, disabling succeeds without that calculation, saved points stay
  fixed, and withdrawals/transfers remain operational.
- On complete backing exit, clear the already-stored per-asset points and
  reconcile user/global totals without invoking the unsafe accrual calculation.
- Preserve emergency withdrawal liveness and keep any Boardroom/governance
  synchronization from becoming a new blocking external dependency.
- Add partial-exit, full-exit, multi-asset, aggregate-total, and downstream
  governance-consistency tests.

## 5. Other material branch findings

### F-08 — RETRACTED: liquidation pricing occurs before collateral transfer

**Severity:** RETRACTED / informational correction

**Area:** `AuctionHouse` and `StabVault`
**Status:** No production fix supported by this finding

Revision 1's causal narrative was wrong. `canAcceptLiquidationAsset` does not
itself read a price, but the relevant AuctionHouse flow handles pricing before
collateral transfer:

- `AuctionHouse.vy:304` obtains current debt and terms in raising mode.
- `_transferCollateral` calls `_getAssetAmount` at `AuctionHouse.vy:1230`.
- `_getAssetAmount` calls `PriceDesk.getAssetAmount(..., True)` at
  `AuctionHouse.vy:1266`.
- The vault transfer occurs later at `AuctionHouse.vy:1239` or `:1245`.

The verified no-feed scenario falls back to auction rather than reaching
`StabVault._addClaimableBalance`. The proposed revision-1 remedy—duplicating a
price check inside `canAcceptLiquidationAsset`—would not change this behavior.

No availability defect or contract change is asserted by F-08. Retaining an
explicit regression test for no-feed, stale-feed, and zero-price routing would
still improve evidence, but it is not a release fix for the retracted claim.

### F-09 — Dormant-asset value capture is real but was described imprecisely

**Severity:** MEDIUM-HIGH; minimal mitigation selected with residual risk accepted

**Area:** Stability Pool dormant-asset accounting
**Status:** Owner decision recorded; implementation and tests pending

The prior report describes a generic deposit, claim-dormant, and withdraw
sequence as though it automatically yields free value. Claims burn shares based
on recognized NAV, so simply claiming a dormant asset is not intrinsically
free extraction.

The more accurate value-capture boundary is an activation-driven NAV jump:

1. Deposit while dormant asset value is excluded from NAV.
2. The dormant position activates, either automatically when later flow raises
   it above the activation threshold or through permissionless maintenance
   while the vault is paused.
3. Withdraw after activation and unpause using the increased recognized NAV.

`activateClaimAssets` has no caller restriction; any address may call it while
the vault is paused (`StabVault.vy:1195-1201`). Separately, new claimable-asset
inflow automatically registers a dormant pair once its updated balance reaches
the `$0.25` activation threshold (`StabVault.vy:1224-1246`). Governance is
therefore not required to call activation, although a privileged actor must
have placed the vault into the paused state for the manual path.

The per-pair threshold is only a creation-time dust bound. It is not a durable
cap on the value of a dormant pair and there is no cumulative on-chain cap over
the number or aggregate value of dormant pairs. The prior review's aggregate
monitoring recommendation is valid; its exploit permissions and bound were not
described accurately.

There is a more severe interaction with the selected stale-oracle remediation:
a no-price quarantine deliberately moves an active pair with potentially
unbounded principal out of recognized NAV. If governance could unpause before
reactivation, a user could enter against depressed NAV while a publicly visible
price restoration is pending, then benefit from automatic or manual activation.
The D-02 on-chain pair marker/count and hard unpause guard are therefore required
controls, not part of D-06's deliberately omitted aggregate dormant accounting.

Owner-selected closure:

- Lower `ACTIVATION_USD_THRESHOLD` from `$0.25` to `$0.10`.
- Lower `RETENTION_USD_THRESHOLD` from `$0.10` to `$0.05`, preserving a
  five-cent hysteresis band and avoiding boundary churn.
- Do not add aggregate dormant-pair/value tracking or a new dormant-state
  subsystem in this remediation.
- Document permissionless paused activation, automatic flow-driven activation,
  and the exact transaction ordering.
- Monitor dormant-pair proliferation and activation events.
- Explicitly retain the residual risk that many dormant pairs or price
  appreciation can make aggregate dormant value exceed the per-pair entry
  threshold.

### F-10 — RipeGov position migration cleanup preserves Ledger invariants

**Severity:** MEDIUM-HIGH

**Area:** `RipeGov`, `Ledger`, and Teller-mediated migration
**Status:** Closed in integrated `rh` source; deployment remains separately gated

The migration now proves source Ledger participation before export, proves the
source position is empty after export, and performs atomic cleanup through a
narrow `Ledger.removeVaultFromUserForMigration` entry point authorized only to
the current Teller. Teller verifies the removal before proceeding.

Source removal occurs before the conditional target add. Therefore a user at
the configured position limit never needs a transient extra slot: replacing a
source with a new target preserves the count, while a pre-existing target
reduces it by one. The target import accepts only a coherent stale-zero asset
registration; a nonzero target position reverts. A completed migration cannot
be replayed because the source Ledger-participation proof fails before export.

Focused tests cover missing-source rollback, Teller-only and Ledger-pause
authorization, maximum-count replacement, pre-existing target participation,
stale-zero target registration, nonzero-target rejection, and repeated
migration failure without mutation. These source and test guarantees close the
repository finding; they do not authorize a production transaction or relax
the separate deployment gates.

### F-11 — Bravo special Stability Pool IDs are not type-safe

**Severity:** MEDIUM-HIGH

**Area:** `SwitchboardBravo`, `MissionControl`, and `AuctionHouse`
**Status:** Open

Monotonically increasing VaultBook IDs prove identity, not interface or semantic
type. Revision 1 overstated the scope: Charlie's preferred Stability Pool path
already probes `totalClaimableBalances` and `isPaused` on the target at
`SwitchboardCharlie.vy:555-569`. No additional Charlie type probe is justified
by this finding.

Bravo's `specialStabPoolId` remains the real gap. It verifies only that the ID is
a valid VaultBook registration (`SwitchboardBravo.vy:490-492`) and does not
probe the target's Stability Pool interface. When the configuration is applied,
`MissionControl._setAssetConfig` permanently marks every nonzero special ID in
the monotonic `isStabVaultId` classifier (`MissionControl.vy:302-309`). A wrong
ID can therefore permanently misclassify or exclude collateral and cause
AuctionHouse to issue StabilityPool ABI calls to an arbitrary vault, reverting
liquidation flows.

Required closure:

- Add a Stability Pool interface/capability probe to Bravo's nonzero
  `specialStabPoolId` validation.
- Validate the actual Bravo target contract, not just its numeric ID.
- Test arbitrary valid non-StabilityPool vault IDs.
- Preserve and regression-test Charlie's existing target probes.

### F-12 — Pending Uniswap configuration can overwrite newer snapshot state

**Severity:** MEDIUM-HIGH

**Area:** `contracts/priceSources/UniswapV2Prices.vy`
**Status:** Owner approved a narrow fix; implementation and tests pending

`updatePriceConfig` copies the complete live `PriceConfig` into pending state,
including mutable fields such as `lastSnapshot` and `nextIndex`. Snapshots can
continue advancing during the timelock. Confirmation later replaces the live
configuration wholesale with the stale pending copy before attempting another
snapshot.

This can:

- Rewind the snapshot cursor.
- Restore a stale last-snapshot time.
- Overwrite or lose intervening snapshot history.
- Produce inconsistent behavior when delay or window size changes.

Existing tests cover aligned examples but do not prove preservation across all
intervening snapshot counts, delay changes, or ring-size changes.

Owner-selected closure:

- Store only policy fields in pending configuration.
- At confirmation, merge approved policy fields into the current live state.
- Preserve or correctly clamp live cursor and timestamp state.
- Preserve stored snapshot slots when the ring shrinks. The live read bound and
  existing stale-time filter determine participation; clearing would alter the
  weighted price and exceed the narrow state-preservation fix.
- Test the exact retained-sample mean after shrink and existing behavior after
  later expansion.
- Clear or deliberately account for replaced pending actions.
- Keep the patch narrowly limited to configuration-state preservation; do not
  add TWAP, liquidity-floor, or manipulation-defense changes under this item.

### F-13 — Runtime-size evidence is internally inconsistent

**Severity:** MEDIUM

**Area:** Bytecode release evidence
**Status:** Open reconciliation

The current deployed-runtime test measures AuctionHouse at 24,556 bytes with 20
bytes of headroom. Other branch records describe 24,549 bytes with 27 bytes of
headroom, while the runtime template records 24,460 bytes with 116 bytes of
headroom.

Template-versus-deployed differences can be legitimate, but two different
values are presented as deployed facts. The prior review reports approximately
20 bytes without binding its compiler, commit, command, or deployed/template
method.

The stale 24,549/27 pair is embedded in
`tests/inventory/test_contract_artifacts.py`, but that test asserts only that
`size + headroom == 24,576`; it never recompiles AuctionHouse or compares the
recorded pair with actual bytes. It is structurally unable to detect size drift.
`docs/chains/rh/smart-contract-changes/basic-vault-fail-closed.md:92-94`
incorrectly states that this test pins the exact measurement.

There is an additional CreditEngine mismatch:

- `config/contract-artifact-expectations.json` records a runtime-template size
  of 24,151 bytes.
- Independent compilation at the pinned head measures 24,296 bytes.
- The corresponding headroom is therefore 280 bytes, not the stale recorded
  425 bytes.

AuctionHouse and Deleverage template measurements reproduced their records;
CreditEngine did not. Deleverage also has only seven bytes of deployed-runtime
headroom, making evidence discipline especially important.

Required closure:

- Pin exact compiler and dependency versions.
- Distinguish template, constructor-instantiated, and deployed-runtime values.
- Regenerate every size record from the final candidate.
- Replace arithmetic-only frozen-pair assertions with exact compiler-backed
  comparisons, or label them explicitly as record-integrity checks rather than
  measurement tests.
- Correct the false exact-measurement statement in
  `basic-vault-fail-closed.md`.
- Fail release on record drift or any EIP-170 breach.

### F-14 — Ledger deployment validation does not prove the selected block source

**Severity:** HIGH

**Area:** `contracts/data/Ledger.vy` and Robinhood deployment configuration
**Status:** Open deployment guard

The production default uses the intended `0x64` source, but the migration's
nonzero check does not prove that the deployed Ledger selected it.

`Ledger.getArbActionBlock()` always calls `_getArbActionBlock()`, which calls the
hard-coded `ARB_SYS` address. It does not consult the immutable
`ACTION_BLOCK_SOURCE` (`Ledger.vy:206-231`). Consequently,
`migrations/robinhood-mainnet/0001_Registries.py:45-49` can return a nonzero
ArbSys value even if the Ledger was accidentally deployed in native mode. The
check validates that `0x64` responds; it does not validate the deployed mode.

However, `config/robinhood_launch.py` permits
`RIPE_LEDGER_BLOCK_SOURCE=native` to override that source. This is useful for
some local or fork contexts but dangerous for a live Robinhood deployment.

The constructor at `Ledger.vy:189-200` allowlists zero or exact `0x64` and
stores the immutable, but it does not call `arbBlockNumber()`. Repository text
claiming an immediate constructor probe is therefore false, including:

- `migrations/robinhood-mainnet/0001_Registries.py:34-38`.
- `docs/chains/rh/smart-contract-changes/ledger.md:300-307`.
- `docs/chains/rh/hardening/ledger-replay-policy.md:38-49`.

Other documentation already records that the constructor probe was removed,
so the repository is internally inconsistent on this security property.

Required closure:

- For a live Robinhood profile, fail closed unless the configured source is the
  exact `0x64` adapter.
- Prevent a generic environment override from silently changing the production
  clock.
- Read back `ACTION_BLOCK_SOURCE()` from the deployed Ledger and require exact
  `0x64` before registration or ownership handoff.
- Treat `getArbActionBlock()` only as an independent precompile-health check,
  not as proof of the selected Ledger mode.
- Retain lazy runtime validation with the selected strict pre-registration
  immutable readback and node-executed health check; do not restore the
  constructor-time probe.
- Correct all false constructor-probe comments and documentation.
- Record the deployed address, immutable readback, and successful ArbSys read in
  the manifest.

### F-15 — `getCCIPAdmin` has unclear pre-setup behavior

**Severity:** LOW-MEDIUM

**Area:** `contracts/tokens/modules/Erc20Token.vy`
**Status:** Current source behavior retained by owner decision

`getCCIPAdmin()` calls `RipeHq(self.ripeHq).governance()` even before
`finishTokenSetup` installs a nonzero `ripeHq`. Pre-setup CCIP tooling may
therefore observe a revert rather than the temporary governor.

Owner-selected closure:

- Keep `getCCIPAdmin()` in the shared ERC-20 module exactly as implemented.
- Do not add a `tempGov` fallback or otherwise change source behavior.
- Treat a possible pre-setup revert as accepted lifecycle behavior.
- Add direct tests for pre-setup and post-setup behavior without changing the
  implementation.
- Regenerate and reconcile the token ABIs so the retained selector is honestly
  represented.

### F-16 — Stability-position liquidation asymmetry is documented as intentional

**Severity:** INFORMATIONAL / documented economic semantics

**Area:** Credit and liquidation composition
**Status:** Implemented and documented; reopen only if policy changes

Stability positions are excluded from borrowing-power calculations, but the
truthful position iterator still exposes them to later liquidation phases and
AuctionHouse is permitted to withdraw them.

Revision 1 failed to credit the existing intent evidence. The behavior is
explicitly described in the source comment at `StabVault.vy:263-269`, in
`docs/chains/rh/smart-contract-changes/auction-house.md:57-63`, and in
`docs/chains/rh/smart-contract-changes/credit-engine.md:70-79`. The dedicated
AuctionHouse test also states that Stability Pool positions remain
non-collateral but phase-2 liquidatable.

This is still an economically important asymmetry worth exposing to users and
integrators, but it is not an unrecorded branch defect or an open approval in
the pinned repository evidence.

Required closure:

- Preserve the existing documented behavior and end-to-end test.
- Include the behavior in user/integrator-facing liquidation documentation.
- Reopen the economic decision only if the owner wants stability positions to
  become liquidation-isolated.

## 6. Findings about the prior review's methodology

### R-01 — The review is not bound to immutable evidence

The prior report provides no exact PR head, commit, tree, base, merge base, or
exact changed-path manifest. A branch name is mutable and cannot support a
production approval by itself.

### R-02 — The stated scope is imprecise

The report refers to a `SimpleErc20` path even though `SimpleErc20.vy` is not
one of the 20 changed production contracts. It does not provide a complete
manifest proving that every in-scope production Vyper change was reviewed.

### R-03 — There is no reproducible test record

The report makes contract-by-contract safety claims without commands, test
counts, environment identity, failure dispositions, or complete-suite evidence.
It misses the red Defaults gate, five stale governed artifacts, and the strict
Uniswap security xfail.

### R-04 — ABI and artifact compatibility were not reviewed

The report notices source-level API removal but does not compare source selectors
with committed ABIs or inventory downstream consumers. It also misses the
Defaults constructor mismatch and source-hash drift.

### R-05 — Deployment and governance sequencing were under-reviewed

The pointer issue was identified, but the review does not trace the production
migrations through ownership handoff, the actual zero-delay Charlie state,
pause conditions, immutable Ledger readback, or post-handoff recovery cost.

### R-06 — Finding taxonomy and severity are inconsistent

The report mixes:

- Newly introduced defects.
- Deployment/configuration omissions.
- Intentional but unapproved economics.
- Accepted residual risks.
- Pre-existing unrelated observations.

These categories require different owners and closure evidence. The report
gives a speculative dormant-asset scenario high prominence while omitting the
1,000-times Defaults conflict, stale ABIs, red tests, and active-oracle freeze.

### R-07 — The release threshold is too narrow

The prior report does address several non-theft dimensions, including
deployment assertions, configuration validation, API compatibility, and
monitoring. Revision 1 overstated that omission. Its favorable conclusion still
weights the absence of a clear free-theft path too heavily relative to the
unresolved evidence. A production decision must comprehensively close:

- Economic misconfiguration.
- Frozen deposits, withdrawals, claims, and liquidations.
- Broken deployment or initialization.
- Stale integration artifacts.
- Governance-accounting errors.
- Irrecoverable ownership sequencing.
- Compiler and bytecode-limit fragility.

The absence of an obvious direct theft does not justify "almost safe."

### R-08 — Recommendations are not paired with closure evidence

Many recommendations are directionally sensible, and the prior report does
propose a deploy-time assertion script. Revision 1 failed to credit that
recommendation. The broader gap remains: most findings do not state the exact
reproducer, invariant, test, owner decision, consumer inventory, or retained
evidence required for closure.

## 7. What the prior review got right

The following observations should be retained in the final remediation record:

- Exact-receipt checks and transient custody mutexes are meaningful defenses.
- `BasicVault` fails closed against custody shortfalls.
- The MissionControl core/preferred pointer omission is real.
- Migration cleanup is necessary.
- Numeric VaultBook IDs do not prove contract type.
- The Teller single-item API removal is a breaking change.
- AuctionHouse has a dangerously small bytecode margin.
- Equal-count Uniswap observations are not a true time-weighted average.
- Ledger's Robinhood block-number adapter is conceptually correct.
- A deploy-time assertion script is an appropriate recommendation.

These positive findings establish useful implementation qualities, but they do
not override the release blockers or prove system-level safety.

Separately, this independent review confirmed that AuctionHouse's
requested-versus-received accounting is directionally correct and that
Deleverage has only seven bytes of deployed-runtime headroom. Those two points
were not findings made by the prior review and must not be attributed to it.

## 8. Required closure sequence

The smallest defensible closure order is:

1. **Freeze and rebind the candidate.** Record commit, tree, merge base, exact
   production Vyper manifest, compiler, and dependency identities.
2. **Apply Defaults authority.** Reconcile every source and consumer to the
   owner-approved current literal matrix.
3. **Repair integration artifacts.** Regenerate ABIs, source hashes, bytecode
   records, manifests, and selector inventories.
4. **Repair deployment invariants.** Set and verify core/preferred pointers,
   transition every required setup-zero timelock to its approved nonzero value
   before ownership handoff, and prove the deployed Ledger's immutable
   Robinhood block source.
5. **Resolve Stability Pool availability.** Implement the selected minimal
   stale-oracle recovery and dormant thresholds, plus Bravo special-pool typing
   and migration cleanup.
6. **Apply the oracle decisions.** Preserve the accepted Uniswap manipulation
   xfail while fixing the separate live-snapshot configuration overwrite.
7. **Apply governance semantics.** Preserve no-update disable behavior, clear
   stored points only at a disabled user's full per-asset exit, and leave the
   documented stability-position liquidation asymmetry unchanged.
8. **Add focused adversarial tests.** Cover every finding's success, revert,
   boundary, state-transition, and cross-contract behavior.
9. **Finish the complete implementation pass.** Do not introduce per-package
   approval, review, or test gates.
10. **Run one consolidated focused verification.** Compile the final contracts
    and run the selected Defaults, artifact, ABI/selector, runtime-size,
    Uniswap, Stability Pool, migration, and deployment checks once. Fix and
    narrowly rerun only failed/coupled nodes; defer the complete serial suite to
    the independent review phase.
11. **Return one final evidence handoff.** Report the final delta, focused
    commands/results, sizes, artifacts, and residual risks together.

## 9. Owner decisions and implementation authority

The owner has recorded all decisions below. Their executable implementation
requirements are consolidated in
[`rh-production-vyper-remediation-implementation-plan.md`](rh-production-vyper-remediation-implementation-plan.md),
which is the controlling implementation handoff.

### D-01 — Defaults authority and literal matrix — DECIDED

**Owner decision recorded 2026-08-06:** Use the complete current
`DefaultsRobinhood` source at the pinned head as the intended value and
structure authority.

- Keep the seven-argument constructor.
- Keep Steakhouse fully removed from constructor inputs, immutables,
  `assetConfigs`, and priority liquidation.
- Keep all current source values; do not restore the historical values.
- Specifically keep `maxBorrowPerInterval = 25 GREEN`, priority price sources
  `[1, 2]`, and `restartDelayBlocks = 2 * HOUR_IN_BLOCKS`.

Implementation must emit and reconcile the complete seventeen-getter literal
matrix. This decision records owner intent but does not claim independent proof
that live deployed contracts already use those values.

### D-02 — Stability Pool stale-oracle policy — DECIDED

**Owner decision recorded 2026-08-06:** Preserve strict/fail-closed valuation
and add the smallest controlled emergency quarantine and recovery process that
reuses the existing global pause and active/dormant/prune/activation machinery.

- A stale or reverting active-asset oracle must not silently become a zero
  valuation while normal pool activity continues.
- The pool must remain paused while the affected asset is quarantined and until
  a valid price source allows it to be reactivated.
- Normal deposits and withdrawals must not resume against unresolved depressed
  NAV.
- While paused, an active unpriced pair may be moved out of active NAV with an
  explicit no-price reason. Deactivation must preserve its pair balance, total
  liability, token custody, and all user shares.
- Mark each exact no-price pair and increment a global quarantine count. A
  counter without per-pair identity is insufficient because ordinary dormant
  activation must never discharge a quarantine.
- Restoration or an alternate valid price source must permit reactivation while
  still paused; successful reactivation clears only that pair's marker/count.
- Preserve the existing `pause(bool)` ABI and authorization, but enforce on
  chain that unpause reverts while the global quarantine count is nonzero.
- Do not add a haircut, write-down, confiscation, liability deletion, or a
  large independent quarantine subsystem.

The implementation handoff specifies the complete transition, authority,
events, recovery conditions, invariants, bytecode constraint, and adversarial
tests. No additional design-review pause is required.

### D-03 — Uniswap manipulation defense — DEFERRED

**Owner decision recorded 2026-08-06:** Acknowledge the manipulation issue but
make no Uniswap TWAP, liquidity-floor, or other manipulation-defense change in
the current implementation.

- The current strict xfail remains an honest open-risk signal.
- It must not be reported as a passing security test.
- The current remediation scope excludes work intended to make the price source
  manipulation-resistant.
- Any release relying on the source requires an explicit exception record with
  consumer inventory, zero-LTV blast radius, monitoring, and emergency
  response.

This decision applies to the manipulation-defense issue. It does not silently
dispose of the separate F-12 pending-configuration state-overwrite finding.

### D-04 — RipeGov disable checkpoint semantics — DECIDED

**Owner decision recorded 2026-08-06:** Preserve the current no-update disable
path. Its purpose is to recover when the next points calculation would overflow
or otherwise revert; checkpointing inside disable could make the escape hatch
unusable.

- Do not calculate or checkpoint new points during global or per-user disable.
- Uncheckpointed accrual is intentionally not credited.
- Keep the disable marker irreversible.
- Add an explicit overflow/revert recovery test and document this rationale.

### D-05 — RipeGov saved points after backing exits — DECIDED

**Owner decision recorded 2026-08-06:** Preserve frozen saved points during
partial emergency withdrawals, but clear the already-stored points when the
disabled user's position in that asset reaches zero.

- Do not calculate or credit new accrual during the exit.
- Do not use potentially overflowing proportional point arithmetic in the
  partial emergency path.
- A full exit must clear that asset's stored points and safely decrement the
  user's and global stored totals.
- Preserve withdrawal liveness; downstream governance synchronization must not
  introduce a new external-call blocker.
- Test partial and full exits, multiple assets, aggregate accounting, and
  Boardroom/governance consistency.

### D-06 — Dormant claim-asset exposure — DECIDED

**Owner decision recorded 2026-08-06:** Use the smallest constant-only
mitigation and do not add aggregate dormant-state logic.

- Set activation to `$0.10` in 18-decimal USD units.
- Set retention to `$0.05` in 18-decimal USD units.
- Preserve hysteresis between activation and pruning.
- Add no aggregate pair-count or value cap in this remediation.
- Accept and document the residual aggregate/value-appreciation risk.
- Update boundary tests, maintenance tests, events/documentation, and monitoring
  thresholds to the selected values.

### D-07 — Ledger source-validation posture — DECIDED

**Owner decision recorded 2026-08-06:** Keep the existing
`_actionBlockSource` constructor argument, pass exact `0x64` for Robinhood, and
do not call/probe ArbSys from the constructor.

- Before registry registration, read back `ACTION_BLOCK_SOURCE()` from the
  deployed Ledger and require exact `0x64`.
- Separately call `getArbActionBlock()` through the real node and require its
  exact-return validation and a nonzero result.
- A live Robinhood deployment must reject `native`, missing/Boa-only RPC mode,
  a failed immutable readback, or a failed ArbSys health call.
- Keep native zero available only for explicitly non-Robinhood deployment
  profiles.
- Correct every comment and document that falsely claims the constructor probes
  `arbBlockNumber()`.

The owner confirmed that the construction limitation concerns calling/probing
ArbSys during construction, not passing the existing source-selection
argument.

### D-08 — Pointer values and post-setup timelocks — DECIDED

**Owner decision recorded 2026-08-06:** Initialize the two pointer values
directly in the MissionControl constructor and complete the post-setup timelock
transition before Safe handoff.

- Define named constants for RipeGov ID `2` and StabilityPool ID `1`.
- Assign `coreRipeGovVaultId = 2` and `preferredStabVaultId = 1` to the existing
  mutable storage fields in `MissionControl.__init__`.
- Preserve the public storage ABI and Charlie governance setters; do not make
  the pointers themselves immutable.
- Mark ID `1` in `isStabVaultId` during initialization.
- After VaultBook/vault deployment, prove IDs `1` and `2` resolve to the expected
  contract interfaces before ownership handoff.
- Every setup-zero switchboard must call `setActionTimeLockAfterSetup()` before
  Safe handoff, using its approved minimum unless another exact value is
  recorded, and the migration must assert no required component remains at
  zero.
- At the pinned candidate this means 12 deployed-component finalizations:
  five switchboards, Chainlink, Curve, HumanResources, and four registries.
  BlueChipYieldPrices is not deployed and must not be fetched or finalized.

### D-09 — CCIP admin before token setup — DECIDED

**Owner decision recorded 2026-08-06:** Keep `getCCIPAdmin()` in the shared
ERC-20 module exactly as implemented and make no source-behavior change.

- Retain the selector.
- Do not return `tempGov` before setup.
- Accept and document the current pre-setup behavior, including a possible
  revert while `ripeHq` is zero.
- Add direct lifecycle tests and reconcile the generated/committed token ABIs
  without modifying the contract behavior.

### D-10 — Uniswap pending-configuration state preservation — DECIDED

**Owner decision recorded 2026-08-06:** Include the narrow F-12 correctness fix
as a small, contained change.

- Pending governance state must contain policy changes rather than a stale copy
  of mutable snapshot progress.
- Confirmation must preserve the latest live cursor and timestamp.
- Window-size changes must have explicit, tested slot-retention semantics.
- Keep this work separate from the deferred manipulation-defense issue; no
  TWAP, liquidity-floor, or pricing-policy redesign is authorized.
- Preserve the existing storage/ABI shape. Merge the pending policy fields into
  the latest live configuration at confirmation and preserve/clamp current
  cursor progress. Do not clear stored samples on shrink; the existing live
  window bound and stale-time filter control whether they participate.
- If the initial approach grows, refactor it within this narrow model rather
  than introducing a broad storage, ABI, or oracle-architecture redesign.

### Implementation authorization gate

The owner has authorized one uninterrupted implementation pass governed by
[`rh-production-vyper-remediation-implementation-plan.md`](rh-production-vyper-remediation-implementation-plan.md).
The implementation agent should complete all work packages and return one
consolidated evidence handoff rather than pausing for intermediate review.
That scope distinguishes:

- Policy-driven production changes resulting from owner decisions.
- Mechanical ABI, artifact, size-record, migration, comment, and documentation
  reconciliation.
- Focused regression tests.
- One consolidated focused verification and a handoff for subsequent
  independent full-suite/release review.

This authorization covers local source, test, artifact, ABI, migration, and
documentation changes in an isolated worktree. It does not authorize a commit,
push, merge, deployment, activation, publication, or live-chain mutation.

## 10. Exact production Vyper scope

The 20 changed non-test, non-mock production Vyper files reviewed are:

1. `contracts/config/DefaultsRobinhood.vy`
2. `contracts/config/SwitchboardAlpha.vy`
3. `contracts/config/SwitchboardBravo.vy`
4. `contracts/config/SwitchboardCharlie.vy`
5. `contracts/config/SwitchboardEcho.vy`
6. `contracts/core/AuctionHouse.vy`
7. `contracts/core/BondRoom.vy`
8. `contracts/core/CreditEngine.vy`
9. `contracts/core/CreditRedeem.vy`
10. `contracts/core/HumanResources.vy`
11. `contracts/core/Lootbox.vy`
12. `contracts/core/Teller.vy`
13. `contracts/data/Ledger.vy`
14. `contracts/data/MissionControl.vy`
15. `contracts/priceSources/UniswapV2Prices.vy`
16. `contracts/tokens/modules/Erc20Token.vy`
17. `contracts/vaults/RipeGov.vy`
18. `contracts/vaults/StabilityPool.vy`
19. `contracts/vaults/modules/BasicVault.vy`
20. `contracts/vaults/modules/StabVault.vy`

Mocks, testing probes, and the documentation example Vyper contract changed in
the branch were excluded from the production-contract count, while their use as
test evidence remained relevant where applicable.

## 11. Final assessment

The prior report is a useful preliminary source review, especially for exact
receipt handling, pointer initialization, migration cleanup, identifier typing,
API removal, and bytecode pressure. It is not a production-readiness review and
its favorable conclusion should not be carried into a release decision.

PR #67 remains **NO-SHIP** until every authorized work package and focused
implementation gate is closed against one immutable candidate, followed by the
separately scheduled independent review/full-suite phase. The implementation
agent's deliberately streamlined test record is not release approval.
