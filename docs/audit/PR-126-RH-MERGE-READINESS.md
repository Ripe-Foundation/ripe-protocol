# PR #126 — Remediations-to-RH merge-readiness review

**Repository:** `Ripe-Foundation/ripe-protocol`

**Pull request:** [#126](https://github.com/Ripe-Foundation/ripe-protocol/pull/126)
(`rh-audit-remediation` → `rh`)

**Base:** `origin/rh` `36ee0db42482c3e7d6c43d045fc02655b90bebf4`

**Reviewed remediation head:** `origin/rh-audit-remediation`
`5f3848c051655e6b9b7e439fb6db13348d87ade3`

**Last contract-change commit:** `c9ae47e1854e676b5846c98baa40f5d0fdfaf324`
(PRs after that on this head are documentation and CI only)

**Reviewed:** 2026-08-17

**Classification:** independent source-merge review. This is not deployment,
configuration, activation, migration, or release authorization.

## Purpose and scope

This record answers whether `rh-audit-remediation` is suitable to merge into
`rh`. It covers merge mechanics, whether the intended contract remediations are
actually present and tested, composed protocol behavior, quality, and the owner
decisions that close remaining process questions.

**Out of scope here:** live Base configuration, Base PriceDesk timelock, Base
RipeGov migration (issue #150 / draft PR #83), and Instant Bonds (PR #156).
Those are separate workstreams.

This document supersedes the merge verdict in
[`PR-126-SMART-CONTRACT-FINDINGS.md`](PR-126-SMART-CONTRACT-FINDINGS.md) for the
exact head above. That older file still says **REQUEST CHANGES** against
reviewed head `81d6146`. Later PRs #139–#177 closed the High/Medium items listed
there. Do not treat it as current.

Live residual triage remains
[`PR-126-DERIVED-FOLLOW-UP-REGISTER.md`](PR-126-DERIVED-FOLLOW-UP-REGISTER.md).

## Verdict

**The remediations source is ready to become `rh`.**

`origin/rh-audit-remediation` at `5f3848c` is a clean 172-commit fast-forward of
undeployed `rh`. The intended contract High/Medium remediations are present,
internally consistent, and backed by regressions that assert the new invariants.
Exact-head CI is green. The remaining items are owner-accepted residuals,
deferred defense-in-depth, or activation/ops gates.

GitHub cannot merge until PR #126 is marked ready and `Protect rh` receives a
last-push approval. That is process, not a source defect.

Merge **`origin/rh-audit-remediation` @ `5f3848c` only.** Local
`rh-audit-remediation` has historically been 47 commits behind origin and must
not be the merge source.

Do not interpret this merge as launch authority.

## Owner decisions recorded in this review

These were made while discussing the merge-readiness findings. They are part of
this verdict.

| Item | Decision | Effect on this merge |
| --- | --- | --- |
| Issue [#153](https://github.com/Ripe-Foundation/ripe-protocol/issues/153) CreditEngine auction repayment bound | Do not implement now | Deferred defense-in-depth. AuctionHouse already caps live debt before collateral transfer. |
| DER-01 Teller `performHousekeeping` | Registered Ripe addresses are fully trusted | Accepted under the intended caller-trust model. Not a missing authorization invariant. |
| Instant Bonds PR #156 | Out of scope | Separate feature. Not part of this merge. |
| Nested BlueChip / DER-T01 | Understood; not a current launch path | Activation gate only. RH launch keeps BlueChip undeployed. |

SC-03 / B-AUD-007 (sGREEN first-depositor donation) remains the Auditor B
operational disposition: no virtual-share contract change in this wave. The
constructor `assert _initialSupply == 0` closes SC-27 only. Operational seed
and live-state readback stay on the launch checklist.

## Merge mechanics

| Item | Evidence |
| --- | --- |
| Merge-base | `36ee0db` — `rh` is an ancestor of remediations |
| Fast-forward | Yes. `rh` has zero unique commits |
| Commits added | 172 |
| Diff | 260 files, +64,262 / −20,908 |
| Component PRs | 71 merged into remediations; none still open into that branch |
| PR #126 | Draft, `MERGEABLE`, `reviewDecision=REVIEW_REQUIRED` |
| Exact-head CI | [PR run 32055765249](https://github.com/Ripe-Foundation/ripe-protocol/actions/runs/32055765249) and [push run 32055761077](https://github.com/Ripe-Foundation/ripe-protocol/actions/runs/32055761077) succeeded; `rh-pr-gate` passed |
| RH deployment state | None. These departments are replaced by migration, not proxy-upgraded. No live RH storage to break |
| Base bytecode | Merging into `rh` does not deploy or rebind live Base |

`Protect rh` requires last-push approval and `rh-pr-gate`. Fast-forward is the
correct method.

## What was verified

- Git ancestry, file inventory, and PR/CI state against `origin/rh` and
  `origin/rh-audit-remediation`.
- High conservation independently against remediations source: SC-01, SC-02,
  SC-27, B-AUD-011, B-AUD-014.
- Local execution on `5f3848c` of the High conservation and SC-13 suites:
  depleted-collateral GREEN burn cap, fee-free retry burn cap, live-debt auction
  cap, max-discount live-debt cap, sGREEN constructor, user-bound Underscore.
  **15 passed.**
- Domain review of liquidation / debt / Endaoment / Deleverage, pricing and
  oracles, vaults, Teller / authority, and bonds.
- Holistic composition: Teller ↔ Deleverage ABI, borrow / liquidation hysteresis,
  quarantine fail-closed, PriceDesk isolation, SharesVault delivery bound.

Repository remediation documents were treated as claims and checked against
source. Where they disagreed, source won.

## Finding closures that matter for this merge

"Fixed" means the contract changed and a regression asserts the post-fix
invariant, not merely that a happy path still works.

| Finding | Status | Basis |
| --- | --- | --- |
| SC-01 StabPool over-burn | **Fixed** | Phases capped at `debt + keeper` before the swap. Settlement asserts instead of clamping after the burn. `test_depleted_collateral_burn_is_capped_by_creditable_debt` asserts `GREEN burned == debt reduction + keeper mint` on the 105/90 case. |
| SC-02 Auction over-seizure | **Fixed at AuctionHouse** | Each purchase iteration caps GREEN, and therefore discounted collateral, by `getUserDebtAmount` (includes interest) before transfer. Same-borrower batches re-read debt. |
| SC-03 / B-AUD-007 sGREEN donation | **Operational, not contract-closed** | Still 1:1 at zero supply. Matches Auditor B. Launch gate, not a source-merge blocker. |
| SC-27 Unbacked initial mint | **Fixed** | `SavingsGreen.vy` `assert _initialSupply == 0`. |
| B-AUD-011 / SC-06 / SC-22 PriceDesk isolation | **Fixed for direct sources** | Per-source stipend `raw_call`; malformed/contradictory responses rejected; later healthy source still used. |
| B-AUD-001 / 008 BasicVault shortfall | **Fixed** | Custody shortfall zeros valuation and loot share. |
| SC-10 Whole-account quarantine | **Accepted residual** | Owner rejected asset-local quarantine for this wave. |
| SC-07 / 09 Deleverage reentrancy and stab fail-soft | **Fixed** | Shared `@nonreentrant`; settlement rereads debt and reverts if the amount moved; unavailable Stability Pool cohorts are skipped on the broad path. |
| SC-08 Repeat no-progress fees | **Fixed** | Fee-bearing charge is once per episode; retries are fee-free. |
| SC-11 Repay liveness | **Fixed** | Full repay skips valuation; remaining-debt STANDARD path does not require every oracle. |
| SC-12 RipeGov exit fee | **Fixed** | Live-claim fee math; sole-holder early exit reverts. Same-owner multi-address recapture is an accepted economic boundary. |
| SC-13 Underscore binding | **Fixed in source** | Lego callers need a user grant. Issue #161 remains an activation/deploy gate while Underscore is disabled. |
| SC-14 Checkpoints | **Fixed** | Sender checkpointed after mutation; in-vault recipient after that. |
| SC-15 Stale-vault terms | **Fixed** | Terms used to accrue the interval are preserved when traversal finds no eligible record. |
| SC-16 / 17 / 23 Yield and Curve snapshots | **Fixed** | Ring reset, duration TWAP, age-bounded fallback. |
| SC-18 / 19 Endaoment conservation | **Fixed** | Received-amount minting; StableSwap-NG removal capped by executable LP. Real-pool proof is a manual fork lane. |
| SC-20 / 21 Oracle stale / future time | **Fixed** on Chainlink / Pyth / Stork / RedStone | Strictest nonzero bound; future timestamps rejected. |
| SC-24 / 25 / 26 / 29 / 30 | **Fixed** | Reward-dust funding, bounded enumeration, value-aware `lowestLtv`, disabled-slot recovery, attainable max discount. |
| B-AUD-012 Empty Teller batches | **Fixed** on `depositMany` / `withdrawMany` | Sibling many-routes still fail closed downstream and roll back atomically. |
| B-AUD-014 Partner liquidity | **Fixed** | Only the current action's LP delta is split. Feature remains Switchboard-gated. |
| B-AUD-015 / 016 / 017 | **Fixed** | VaultBook confirm-time funds; stab mint auth; sGREEN pause/blacklist on exits. |
| #153 CreditEngine bound | **Deferred** | Owner: not now. AuctionHouse is the only caller and already caps. |
| DER-01 Housekeeping | **Accepted** | Owner: all registered Ripe addresses are trusted. |
| DER-T01 Nested BlueChip | **Activation gate** | See below. Not a current RH launch path. |

## Nested BlueChip (DER-T01)

This is a PriceDesk composition, not a separate product.

PriceDesk asks each registered source for a price and gives that call a 250,000-gas
stipend. If the source reverts, burns the stipend, or returns garbage, PriceDesk
skips it and tries the next source.

`BlueChipYieldPrices` (intended PriceDesk slot 3) does not have its own feed for
the vault token. It prices Morpho / Euler / Fluid / Moonwell / Aave / Compound
receipts by calling **back into PriceDesk** for the underlying:

```
PriceDesk → BlueChip (250k stipend) → PriceDesk.getPrice(underlying) → Chainlink / Curve / …
```

The inner scan is not given its own budget. After an earlier source has consumed
part of the stipend, an honest nested lookup can run out of gas and be reported
as a failed source. UndyVaultPrices has the same shape.

RH launch does not use this path. Priority sources stay `[1, 2]` (Chainlink and
Curve for GREEN). BlueChip at slot 3 is blueprint-selected and not deployed.
Direct assets through those two sources are the qualified envelope.

Do not register BlueChip or Undy as a protocol price source until a topology or
budget change is selected and re-qualified.

## Holistic system

After this merge, `rh` remains a coherent protocol source line.

- Fail-closed is the default: PriceDesk isolates bad sources; quarantine freezes
  the account; Deleverage reverts if debt moved mid-transaction; SharesVault fails
  closed outside a ±2 governance-admitted receipt delta.
- Teller matches Deleverage. Singular `deleverageUser` is gone from both sides.
  `deleverageManyUsers` and `deleverageWithSpecificAssets` remain.
- Borrow still cannot run while `inLiquidation` is set. The flag clears on a
  health-restoring repay or `updateDebtForUser`, not by borrowing.
- `UserBorrowTerms.hasQuarantinedAsset` is computed, not stored in Ledger
  `UserDebt`. No RH storage layout is being migrated in place.

Intentional ABI / product changes the next RH deploy will ship:

- `purchaseRipeBond` no longer has a one-argument form; callers must pass an
  amount and may pass `_minRipePayout`.
- `deleverageUser` is removed.
- `setUserConfig` defaults flipped from all-true to all-false.
- StabilityPool dropped unused single-item claim/redeem selectors.

In-repo tests were updated. Any off-repo client must follow the new ABI.

## Quality

The remediations are high quality. They are not test theater.

What holds:

- Findings landed as named PRs with adversarial regressions.
- Residuals are classified (accepted / activation / assessment) instead of being
  silently skipped. There is one strict xfail, and it matches the accepted
  Stability Pool dormant-dust residual (DER-02).
- The CI flake was fixed by withdrawing unsafe `--dist load`, not by skipping
  the failing test.
- Exact-artifact / headroom theater was retired. EIP-170 plus runtime pins
  remain.

What is not perfect, and is not a merge blocker:

- A few hot-path comments still cite the retired RH-D036 “zero-growth waiver.”
  CreditEngine still says it has “effectively no EIP-170 headroom” at
  24,382 / 24,576 (~194 bytes free).
- AuctionHouse sits at 24,568 bytes (8 bytes of EIP-170 room). Later liquidation
  engine edits will need size recovered first.
- Ordinary PR CI excludes `artifact` and `fork_qualification`. A green default
  run is not SC-04 token-matrix closure or the SC-19 live-pool proof.

## Residuals that do not block this merge

| Residual | Why it does not block a source merge into undeployed `rh` |
| --- | --- |
| SC-03 operational sGREEN seed | Auditor disposition. Hard activation gate. |
| SC-10 whole-account quarantine | Owner-accepted conservative policy. |
| #153 CreditEngine auction bound | Owner: not now. |
| DER-01 Teller housekeeping | Owner: Ripe addresses are trusted. |
| DER-T01 nested BlueChip stipend | Activation-blocked. Launch keeps BlueChip undeployed. |
| DER-T03 specialized stale-time | Policy question for BlueChip / Undy, not a confirmed bug. |
| DER-02 / DER-03 / DER-04 | Accepted dust residual; Comet enablement gate; trusted-integration withdrawal binding. |
| #160 / #161 | Fee-free retry monitor; Underscore deploy/config verification. |
| SC-28 hardcoded non-RH fallbacks | Dormant unless that source is enabled. |
| Contributor clone inventory | Future clones pick up source; existing clones need a separate migrate / monitor / accept decision. |

## Process to land

1. Merge `origin/rh-audit-remediation` at `5f3848c` only. Do not merge a stale
   local remediations worktree.
2. Mark PR #126 ready for review.
3. Obtain the `Protect rh` last-push approval on that SHA.
4. Fast-forward `origin/rh` to `5f3848c`.
5. If the branch moves, re-run `rh-pr-gate` and merge the new exact head.

Still required before any RH activation, and not granted by this merge:
operational sGREEN seed, Underscore-off until #161 verification, no nested
BlueChip / Undy PriceDesk activation, no Comet enablement without a token-aware
exit policy, live PriceDesk / Stock / stale-time reads, and the separate
deployment ceremony.

## Related documents

- [`AUDIT_PROCESS_PLAN.md`](AUDIT_PROCESS_PLAN.md)
- [`REMEDIATION-GUIDE.md`](REMEDIATION-GUIDE.md)
- [`PR-126-SMART-CONTRACT-FINDINGS.md`](PR-126-SMART-CONTRACT-FINDINGS.md)
  (historical; reviewed head `81d6146`)
- [`PR-126-DERIVED-FOLLOW-UP-REGISTER.md`](PR-126-DERIVED-FOLLOW-UP-REGISTER.md)
- [`../chains/rh/decision-register.md`](../chains/rh/decision-register.md)
