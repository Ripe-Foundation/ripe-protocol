# PR #126 — Derived Finding and Follow-Up Register

**Repository:** `Ripe-Foundation/ripe-protocol`

**Integration branch:** `rh-audit-remediation`

**Source snapshot:** `07c3c96cf9f8c0cdac7a78fcb3cdf837f56da9fc`

**Checked:** 2026-08-17

**Purpose:** retain contract findings, conditional risks, test gaps, owner decisions,
and live-configuration exposures discovered while remediating the original PR #126
finding set.

This is a triage register, not a deployment authorization. It intentionally keeps
production-contract findings separate from test-only gaps, accepted design
boundaries, and deployment/configuration work. A row marked **conditional** is not
being represented as an active exploit.

## Status key

- **Open — contract:** confirmed or credible production-contract behavior needing a
  fix or explicit acceptance.
- **Assessment:** credible shape, but the impact or required contract change is not
  yet established.
- **Activation gate:** acceptable only while the named feature/configuration remains
  disabled or otherwise contained.
- **Test gap:** implementation evidence is incomplete; not by itself proof of a
  contract defect.
- **Accepted residual:** reviewed behavior retained deliberately.
- **Closed/rejected:** superseded, fixed, or disproved against the current source.

## 1. Formally tracked GitHub issues

| Issue | Classification | Current disposition |
| --- | --- | --- |
| [#161](https://github.com/Ripe-Foundation/ripe-protocol/issues/161) — Teller user-bound Underscore authorization | Activation/deployment gate | The production-contract remediation merged into `rh-audit-remediation` through PR [#170](https://github.com/Ripe-Foundation/ripe-protocol/pull/170). Registered Underscore Legos are now bound to user grants on the affected Teller routes, and Deleverage no longer grants registry-only cross-user trust. The issue remains open while the aggregate is not on the default branch and Underscore remains disabled; do not activate a nonzero registry until the remediated contracts are deployed and the configuration is verified. |
| [#160](https://github.com/Ripe-Foundation/ripe-protocol/issues/160) — AuctionHouse fee-free retry liveness | Activation gate | No on-chain keeper reward exists for fee-free retries. Require the protocol-operated monitor/keeper before activating the behavior. This is operational unless a later design requires an on-chain incentive. |
| [#159](https://github.com/Ripe-Foundation/ripe-protocol/issues/159) — AuctionHouse provenance and optional test hardening | Test/release maintenance | Optional shared test helper and cold-key maximum-batch gas regression. No open production-contract defect. |
| [#154](https://github.com/Ripe-Foundation/ripe-protocol/issues/154) — CreditEngine C2 gas identity | Test/release maintenance | Reassess after the artifact-process simplification and PR #146. No open production-contract defect established by this issue. |
| [#153](https://github.com/Ripe-Foundation/ripe-protocol/issues/153) — CreditEngine auction repayment bound | Open — contract hardening | AuctionHouse currently caps repayment before collateral transfer, but `CreditEngine.repayDuringAuctionPurchase` does not independently reject a repayment above live debt. PR #169 changes CreditEngine but does not add this defense-in-depth bound. Reassess against the final post-#169 runtime; implement only if the deployed contract remains below EIP-170, otherwise record a deliberate deferral. |
| [#150](https://github.com/Ripe-Foundation/ripe-protocol/issues/150) — Base RipeGov migration rebind | Deployment/migration | Rebase and requalify the separate Base migration after SC-12. Not an RH production-contract defect. |

## 2. Original finding dispositions and work still in flight

| Finding | Status at this snapshot | Required closure |
| --- | --- | --- |
| SC-10 — account-wide quarantine / signal split | Accepted residual | Preserve the current whole-account quarantine when any positive-LTV asset is unsafe. The owner explicitly rejected the experimental asset-local branch for this remediation wave. Reopen only through a separately reviewed product/security decision. |
| SC-13 — Underscore cross-user authority | Fixed in the remediation branch | PR [#170](https://github.com/Ripe-Foundation/ripe-protocol/pull/170) merged the user-bound TellerUtils/Deleverage remediation and focused adversarial coverage. Issue #161 remains an activation/deployment gate while Underscore is disabled and the aggregate contracts are not deployed. |
| SC-14 — reward checkpoint sender omission | In PR [#169](https://github.com/Ripe-Foundation/ripe-protocol/pull/169) | PR #169 now covers AuctionHouse, CreditEngine, and Deleverage sender checkpoints, internal-transfer recipient checkpoints, and rollback behavior. Do not treat SC-14 as an independent unassigned task. Merge only after the current branch is contract-reviewed, deployable under EIP-170, and green. |
| SC-24, SC-25, SC-26, SC-30 | In PR [#169](https://github.com/Ripe-Foundation/ripe-protocol/pull/169) | The rebased implementation remains under review. Resolve all review and CI findings, then re-review the final smart-contract behavior before merge. |
| SC-28 — hardcoded `wsuperOETHb` fallbacks | Dormant non-RH integration hazard | Before enabling the source, remove or safely govern the literal MCBETH price of `1` and VVV default of `$2.40`, or enforce an exclusion that prevents them from becoming protocol-consumable fallback prices. |

## 3. Derived production-contract findings and assessments

### DER-01 — Teller `performHousekeeping` caller-controlled account effects

**Status:** Assessment

**Where:** `contracts/core/Teller.vy`, external `performHousekeeping`

Any registered Ripe address can select `_user`, `_isHigherRisk`,
`_shouldUpdateDebt`, and an optional `Addys` bundle. This can touch a third-party
account's `lastTouch`, trigger debt refresh, snapshot Curve state, and alter whether
the last-touch check is enforced. An isolated assessment worktree exists, but no
final verdict establishes whether this is exploitable, grief-only, or safe under the
intended registered-caller trust model.

**Next action:** finish the assessment and issue a plain contract verdict. Do not
start a duplicate implementation before the assessment identifies the missing
authorization invariant, if any.

### DER-02 — Stability Pool dormant dust is stranded after a full exit

**Status:** Accepted residual, ratified in PR #174; strict xfail retained

**Where:** `tests/vaults/modules/test_stab_vault_hardening.py`, DV-15

A sub-activation claim remains directly claimable while the economic owner holds
Stability Pool shares. After a complete share exit, that value is not paid to the
exiting cohort and may later reach a new cohort through the deployed paused
activation path. PR [#174](https://github.com/Ripe-Foundation/ripe-protocol/pull/174)
established that dormant value is outside NAV immediately before exit and recorded
the owner's acceptance of the unpaid-but-bounded residual. “Bounded” refers to
below-`$0.10` entry plus finite configured-pair exposure; appreciation can increase a
dormant pair before maintenance activates it.

**Next action:** retain event monitoring, best-effort claim-before-exit warnings, and
the planned-maintenance activation procedure. Reopen only if monitoring cannot be
maintained, activation fails, aggregate exposure becomes material, or observed user
impact invalidates the accepted handling.

### DER-03 — Multi-holder indexed-token full exit can remain rounding-blocked

**Status:** Activation gate confirmed and retained in PR #174

**Where:** SharesVault withdrawal behavior for Comet-style indexed tokens

PR #163 intentionally chose a minimal exact-custody fix. PR
[#174](https://github.com/Ripe-Foundation/ripe-protocol/pull/174) then reproduced the
real cWETHv3 multi-holder full-exit boundary and confirmed that the exiting holder's
maximum attainable delivery can remain below the theoretical claim while the peer
loses nothing. Current configured Comet position tokens were observed deposit-disabled
with zero shares.

**Next action:** treat this as an enablement gate for affected Comet assets. If those
assets will be admitted, select a token-aware full-exit policy and add exact
deposit-to-accrual-to-withdrawal fork regressions.

### DER-04 — Deleverage withdrawal intent is not bound to observed withdrawal

**Status:** Low conditional accepted residual from PR #132

**Where:** `deleverageForWithdrawal`, `deleverageManyUsers`, and
`deleverageWithSpecificAssets`

A governance-admitted/trusted integration can report withdrawal intent not bound to
the amount actually withdrawn, producing bounded forced deleveraging. The existing
assessment did not show direct attacker profit and launch containment keeps the
relevant integrations disabled/restricted.

**Next action:** reopen before enabling a trusted integration that can exercise the
affected routes. SC-13 narrows Underscore authority but does not bind withdrawal
amounts for every valid Ripe caller.

### DER-05 — Deleverage fail-soft skips have no reason-specific signal

**Status:** Observability residual, not a settlement defect

**Where:** broad Deleverage Stability Pool availability probing

An unavailable Stability Pool cohort is skipped whether the cause is price failure,
pause, or claim-custody deficit. Strict/direct paths still fail closed and the broad
path correctly falls back to ordinary collateral, but operators do not receive a
reason-specific on-chain signal from the skip itself.

**Next action:** decide whether existing external monitoring is sufficient. Add an
event/status surface only if operational response requires the distinction; do not
weaken the fail-soft behavior.

### DER-06 — BasicVault total-issuer-burn policy disposition

**Status:** Accepted residual; account-wide fail-closed behavior retained

**Where:** BasicVault consumers, CreditEngine, CreditRedeem, AuctionHouse, Deleverage

Current integrated behavior quarantines the entire account when a positive-LTV asset
loses all backing. The owner chose to preserve that conservative fail-closed boundary
and to ignore the experimental asset-local branch for this remediation wave.

**Next action:** none for PR #126. Reopen only through a separately scoped design
decision that explicitly replaces the account-wide quarantine policy.

## 4. Qualification results and remaining gaps

### DER-T01 — PriceDesk aggregate transaction gas envelope

**Status:** Qualified only for a bounded direct-asset envelope; nested BlueChip
composition remains activation-blocked

PR [#173](https://github.com/Ripe-Foundation/ripe-protocol/pull/173) executed the
borrower-wide composition through real valuation, liquidation, and Deleverage entry
points. Nine direct assets across three registered sources fit under the observed
32-million gas limit, with keeper batches qualified only up to two liquidation users
or three Deleverage users under the saturated topology. Larger batches failed
atomically.

The overall qualification did not pass: when a predecessor consumes its allowance,
an honest nested BlueChip lookup can exhaust the enclosing 250,000-gas source bound
after its nested PriceDesk call succeeds. PR #173 also recorded a repository/live
slot-3 source divergence.

**Next action:** do not activate the affected nested topology until the owner selects
and qualifies a source/topology or gas-budget change. Re-read the live registry before
activation. Any source-count, enumerable-asset, stipend, or operator-batch growth
invalidates the measured direct-asset envelope.

### DER-T02 — Endaoment real-pool SC-19 proof is not in ordinary CI

**Status:** Qualified at one pinned Base state; manual release requalification remains

PR [#173](https://github.com/Ripe-Foundation/ripe-protocol/pull/173) reran the real
StableSwap-NG boundary proof at pinned Base block `34,471,929` for the recorded
Endaoment runtime, pool implementation, parameters, coin ordering, and keeper budget.
The proof passed, but ordinary CI still excludes `fork_qualification`.

**Next action:** rerun the named fork lane for a release candidate and after any
Endaoment, pool implementation, parameter, ordering, or keeper-budget change. A
default green CI run is not evidence that this qualification executed.

### DER-T03 — BlueChip/Undy ignore the caller/global stale-time argument

**Status:** Policy question; not yet classified as a bug

BlueChipYieldPrices and UndyVaultPrices explicitly ignore the `_staleTime` supplied
by PriceDesk/MissionControl and use their own per-asset snapshot configuration.
Therefore the SC-20 `min(nonzero global, nonzero feed)` tightening implemented for
Chainlink/Pyth/Stork/RedStone does not constrain these derived-vault snapshots.

**Next action:** decide whether the global stale time is intended as a universal
upper bound or whether BlueChip/Undy are intentionally governed solely by their
specialized snapshot configuration. If universal, apply the strictest nonzero bound
and test both sources; if specialized, preserve the behavior and document the
exception.

### DER-T04 — Live per-feed stale-time inventory was not refreshed

**Status:** Current-state verification gap

Repository migrations now configure 86,400-second RH defaults, and a prior Base read
showed the global value is 86,400. That does not establish the current live value of
every configured feed after all migrations and updates.

**Next action:** read every active feed's configured stale time and effective resolved
bound from the live target immediately before activation. Preserve the distinction
between repository configuration and observed chain state.

## 5. Accepted economic and integration boundaries

| Boundary | Disposition |
| --- | --- |
| RGV-LOCK-01 | Conditional Teller touching does not resolve RipeGov weighted-lock shortening when positions are combined. Retain as accepted economic design unless the owner rejects lock shortening. |
| RipeGov same-pool fee redistribution | A controller can split holdings across addresses and recapture part of the redistributed fee; permissionless contracts cannot prove beneficial ownership. A genuine sole-address holder also cannot release early until another address holds shares. Reviewed and accepted in PR #144. |
| Endaoment Lego net reporting | Custody reconciliation cannot prove that a configured Lego reports the venue's net contribution when downstream fees or pre-existing Lego inventory exist. Such routes remain unsupported until qualified. |
| PriceDesk source/topology growth | Fixed per-source stipends isolate individual failures but make source admission and registry growth an availability constraint. Requalify new source types and materially larger registries. |
| Deleverage optional economic controls | Full-payoff buffer, overage, and dust parameters remain zero/deferred. Enabling them requires separate economic qualification. |

## 6. Live configuration and activation exposures

### DER-C01 — Base PriceDesk registry timelock observed at zero

**Status:** Live configuration exposure requiring a fresh read

The prior read-only Base review observed `PriceDesk.registryChangeTimeLock() == 0`
while sibling registry timelocks were nonzero. With a zero delay, source changes can
be initiated and confirmed without a meaningful waiting period. Repository tests
and new-deployment migrations expect a nonzero value, but source intent is not proof
that the existing deployment was corrected.

**Next action:** re-read the live PriceDesk. If still zero, execute a separately
reviewed configuration correction and verify the resulting value on-chain. This is
not fixed by the PriceDesk gas-isolation contract change.

### DER-C02 — Stock-token risk position needs current-state reconciliation

**Status:** Challenged owner/configuration disposition; not a confirmed live exploit

RH-D004 limits the initial Stock Token to AAPL and RH-D005 says Stock routes remain
disabled until containment closes. A separate review alleged a broader live equity
set at 70% LTV without containment. Repository defaults, historical dumps, and live
state have diverged before, so neither statement should be silently promoted into a
current fact.

**Next action:** obtain a fresh on-chain inventory of admitted equities, vault routes,
deposit/borrow flags, LTVs, prices, liabilities, and containment configuration. If
routes are enabled contrary to RH-D005, treat that as a launch/security blocker; if
disabled, retain it as an activation gate.

Other activation-only items that remain tracked elsewhere include Contributor
blueprint/timelock replacement, yield-snapshot monitoring, PriceDesk
deployment/re-registration, Curve activation configuration, and Aero monitoring
consumer cutover.

## 7. Rechecked claims that are not open findings

These are retained to prevent stale review notes from being re-filed:

1. **Four sibling empty-batch routes:** `redeemCollateralFromMany`,
   `buyManyFungibleAuctions`, `claimManyFromStabilityPool`, and
   `redeemManyFromStabilityPool` do not have Teller-level early length assertions,
   but their downstream implementations assert that value was spent/claimed. An
   empty batch reverts before Teller housekeeping and the transaction rolls back
   atomically. This does not reproduce B-AUD-012's successful victim-housekeeping
   behavior. Early checks could improve error clarity/gas but are not an open
   security finding on the current source.
2. **RipeGov forced release via Underscore:** valid, but already tracked by issue
   #161 and addressed by the user-bound `TellerUtils` remediation merged in PR #170.
   It is not an untracked tenth item.
3. **Stability vault in `priorityLiqAssetVaults`:** merged Deleverage code explicitly
   skips vault IDs classified as Stability Pool cohorts in phase 2. The latent
   cohort-revert path is closed in the current source.
4. **CreditEngine stale-only-vault terms wipe:** fixed by PR #146. Current code
   preserves the terms used to accrue the interval when stale traversal removes the
   final live vault and includes capacity-recovery coverage.
5. **RH-D029 exact headroom waiver:** historical release bookkeeping, not a current
   contract finding. CreditEngine's identity and measured size changed after the
   waiver was written. If the final release still uses exact-identity waivers, retire
   or reissue RH-D029 once against the final deployment candidate; do not rebind it
   per development PR. EIP-170 remains the actual deployment requirement.
6. **Zero LP supply arithmetic, Curve transition bugs, PriceDesk malformed-source
   isolation, SC-20/SC-21, and SC-29:** later merged PRs closed these specific items;
   do not reopen them from older review transcripts without new reproducing evidence.

## 8. Immediate triage order

1. Finish PR #169 for SC-14/24/25/26/30: resolve all review and CI findings, verify
   all changed runtimes remain deployable, and re-review the final contract behavior.
2. Reassess issue #153 against the final post-#169 CreditEngine runtime.
3. Finish DER-01 Teller housekeeping assessment before authorizing a contract edit.
4. Resolve DER-T01's nested-source activation blocker and repository/live PriceDesk
   topology divergence before enabling the affected source composition.
5. Decide DER-T03's specialized-oracle staleness policy before changing BlueChip or
   Undy behavior.
6. Re-read DER-C01, DER-C02, and DER-T04 live configuration before activation claims.
7. Retain the ratified DER-02 policy and DER-03 Comet activation gate unless their
   documented reopening conditions occur; schedule SC-28 only if its integration is
   enabled.

## Summary

The derived backlog is smaller than the raw review transcripts imply. The largest
stale claims—the four empty-batch siblings, the priority-liquidity Stability Pool
classification, and the stale-only-vault terms wipe—are not open defects on the
current source. The material open items are:

- PR #169's SC-14/24/25/26/30 implementation and issue #153's optional independent
  repayment bound;
- the unresolved Teller housekeeping assessment;
- the nested BlueChip/PriceDesk activation blocker and specialized-oracle staleness
  policy question;
- accepted or activation-gated Stability Pool, Comet full-exit, and withdrawal-binding
  liveness boundaries; and
- the Base PriceDesk timelock and Stock configuration, which require fresh live-state
  reads rather than more contract bookkeeping.

No newly discovered Critical or High contract exploit was established by this sweep.
The register should be refreshed whenever one of the named PRs/issues lands or a live
configuration read changes an activation premise.
