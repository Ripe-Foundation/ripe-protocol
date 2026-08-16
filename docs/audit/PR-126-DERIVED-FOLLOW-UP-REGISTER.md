# PR #126 — Derived Finding and Follow-Up Register

**Repository:** `Ripe-Foundation/ripe-protocol`

**Integration branch:** `rh-audit-remediation`

**Source snapshot:** `cfdaa8a92e89b7cb78fd731787f9fcbf9c38a724`

**Checked:** 2026-08-16

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
| [#161](https://github.com/Ripe-Foundation/ripe-protocol/issues/161) — Teller user-bound Underscore authorization | Activation gate / contract work | Active local SC-13 work binds registered Legos to a user-specific grant through `TellerUtils` and narrows Deleverage trust. This issue also owns the RipeGov forced-release/fee-harvest path; it is not a separate untracked finding. Do not enable a nonzero Underscore registry until the implementation is reviewed and merged. |
| [#160](https://github.com/Ripe-Foundation/ripe-protocol/issues/160) — AuctionHouse fee-free retry liveness | Activation gate | No on-chain keeper reward exists for fee-free retries. Require the protocol-operated monitor/keeper before activating the behavior. This is operational unless a later design requires an on-chain incentive. |
| [#159](https://github.com/Ripe-Foundation/ripe-protocol/issues/159) — AuctionHouse provenance and optional test hardening | Test/release maintenance | Optional shared test helper and cold-key maximum-batch gas regression. No open production-contract defect. |
| [#154](https://github.com/Ripe-Foundation/ripe-protocol/issues/154) — CreditEngine C2 gas identity | Test/release maintenance | Reassess after the artifact-process simplification and PR #146. No open production-contract defect established by this issue. |
| [#153](https://github.com/Ripe-Foundation/ripe-protocol/issues/153) — CreditEngine auction repayment bound | Open — contract hardening | AuctionHouse currently caps repayment before collateral transfer, but `CreditEngine.repayDuringAuctionPurchase` does not independently reject a repayment above live debt. Add the defense-in-depth check when CreditEngine is already being changed if the complete deployed runtime remains below EIP-170; otherwise record a deliberate deferral. PR #169 does not include this issue. |
| [#150](https://github.com/Ripe-Foundation/ripe-protocol/issues/150) — Base RipeGov migration rebind | Deployment/migration | Rebase and requalify the separate Base migration after SC-12. Not an RH production-contract defect. |

## 2. Original finding work still open or in flight

| Finding | Status at this snapshot | Required closure |
| --- | --- | --- |
| SC-03 — **High** — sGREEN first-depositor donation | Owner-selected operational containment; the unseeded contract behavior remains technically vulnerable | The owner chose not to add virtual/dead shares. Seed and retain the first governance-held shares before borrowing is enabled, verify them on-chain, and prevent the seed from being withdrawn. Treat this as the remaining High until that launch invariant is durably enforced and read back on-chain. |
| SC-10 — account-wide quarantine / signal split | Owner decision; related experimental worktree exists | Decide whether one unsafe positive-LTV asset should quarantine the whole account or only that asset. The experimental issuer-burn/unwind work changes previously accepted RH-D028 behavior and overlaps CreditEngine/AuctionHouse work; do not merge it as a mechanical cleanup. |
| SC-13 — Underscore cross-user authority | In progress | Finish and review the user-bound `TellerUtils`/Deleverage change, including unrelated-Lego negative tests and the RipeGov forced-release route. Issue #161 remains the activation blocker. |
| SC-14 — reward checkpoint sender omission | Open; not included in PR #169 | Checkpoint the sender before liquidation/redemption collateral leaves, checkpoint the recipient after an internal transfer, and prove atomic rollback. Preserve behavior while the relevant reward allocations are zero. |
| SC-24, SC-25, SC-26, SC-30 | In PR [#169](https://github.com/Ripe-Foundation/ripe-protocol/pull/169) | Review and merge only after its focused contract behavior and final CI are green. |
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

**Status:** Open — bounded liveness residual; sole current strict xfail

**Where:** `tests/vaults/modules/test_stab_vault_hardening.py`, DV-15

A sub-activation claim remains directly claimable while the economic owner holds
Stability Pool shares. After a complete share exit, that claim becomes unreachable
to the owner until another liquidation replenishes the same pair enough to activate
it. The amount is bounded below `$0.10` per pair at entry by the selected threshold,
but later value appreciation and multiple pairs remain operational considerations.

**Next action:** either retain the accepted governed-replenishment/runbook policy or
authorize a recovery/redistribution design. A contract fix likely needs a new
external recovery surface and an explicit ownership policy.

### DER-03 — Multi-holder indexed-token full exit can remain rounding-blocked

**Status:** Conditional liveness residual accepted in PR #163

**Where:** SharesVault withdrawal behavior for Comet-style indexed tokens

PR #163 intentionally chose a minimal exact-custody fix. Partial withdrawals and a
sole-holder full exit are qualified, but a multi-holder Comet full exit can still
revert at an unfavorable index-rounding boundary rather than charge the rounding
difference to remaining holders.

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

### DER-06 — BasicVault total-issuer-burn policy remains unsettled

**Status:** Owner decision / overlapping experimental work

**Where:** BasicVault consumers, CreditEngine, CreditRedeem, AuctionHouse, Deleverage

Current integrated behavior can quarantine an entire account when a single
positive-LTV asset loses all backing. An experimental worktree changes this to
asset-local deficit handling so healthy collateral remains actionable. That is a
security/product policy change, not a mechanical follow-up, and it overlaps PR #169
in CreditEngine and AuctionHouse.

**Next action:** resolve the desired account-level versus asset-level fail-closed
boundary before continuing or merging the experimental work.

## 4. Test and qualification gaps

### DER-T01 — PriceDesk aggregate transaction gas envelope

**Status:** Test/availability gap

Per-source gas isolation is tested, including hostile sources and nested honest
lookups. What remains unexecuted is the borrower-wide composition:

```text
assets priced in one transaction × registered sources × per-operation stipend
```

The simple upper-bound arithmetic can exceed an ordinary transaction budget, while
the actually reachable gas depends on topology, early success, source order, and
the number of borrower assets. The previously discussed `~37.5M` value is a
projection, not an executed protocol-path measurement.

**Next action:** add one end-to-end multi-asset liquidation/deleverage measurement
using the intended maximum launch topology. Treat source registration/topology
growth beyond that envelope as requiring requalification.

### DER-T02 — Endaoment real-pool SC-19 proof is not in ordinary CI

**Status:** Test gap

The StableSwap-NG boundary tests are marked `fork_qualification`; `pytest.ini` and
ordinary CI exclude that marker. Local fork evidence exists, but CI can remain green
without rerunning the real-pool executable-cap proof.

**Next action:** run this lane for release candidates or add a scheduled/manual CI
job that explicitly selects `fork_qualification` and asserts a nonzero collected
count. Do not pretend a default green run exercised it.

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

Other activation-only items that remain tracked elsewhere include the sGREEN seed,
Contributor blueprint/timelock replacement, yield-snapshot monitoring, PriceDesk
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
   #161 and addressed by the active user-bound `TellerUtils` work. It is not an
   untracked tenth item.
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

1. Review PR #169 for SC-24/25/26/30, but keep SC-14 and issue #153 visibly open.
2. Finish the SC-13/#161 user-bound authorization work, including RipeGov forced
   release coverage.
3. Finish DER-01 Teller housekeeping assessment before authorizing a contract edit.
4. Make the SC-10/DER-06 account-quarantine policy decision before continuing the
   overlapping issuer-burn worktree.
5. Run the DER-T01 aggregate PriceDesk gas test and the DER-T02 Endaoment fork lane
   as focused qualification work.
6. Re-read DER-C01 and DER-C02 live configuration before activation claims.
7. Schedule SC-28 and any chosen DV-15/Comet liveness design after the overlapping
   workstreams settle.

## Summary

The derived backlog is smaller than the raw review transcripts imply. The largest
stale claims—the four empty-batch siblings, the priority-liquidity Stability Pool
classification, and the stale-only-vault terms wipe—are not open defects on the
current source. The material open items are:

- SC-14 and issue #153, which are not included in PR #169;
- the SC-13/#161 authorization change already in progress;
- the unresolved account-wide quarantine policy and Teller housekeeping assessment;
- bounded/conditional DV-15, Comet full-exit, and withdrawal-binding liveness risks;
- two focused test gaps around aggregate PriceDesk gas and Endaoment's real-pool
  qualification; and
- the Base PriceDesk timelock and Stock configuration, which require fresh live-state
  reads rather than more contract bookkeeping.

No newly discovered Critical/High contract exploit was established by this sweep.
SC-03 remains the original audit's sole unresolved High at the contract level when
sGREEN is unseeded; the owner-selected seed-and-retain launch invariant is its
containment rather than a source-code fix. The register should be refreshed whenever
one of the named PRs/issues lands or a live configuration read changes an activation
premise.
