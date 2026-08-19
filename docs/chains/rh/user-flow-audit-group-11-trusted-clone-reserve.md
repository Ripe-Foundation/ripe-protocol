# Group 11 — trusted clone, thin Ledger

**Status: SIGNED by owner 2026-08-18 (verbal) / implementing.**

This brief **supersedes** Hunk 4-A+
(`user-flow-audit-group-11-implementation-hunk4-a-plus.md`)
and draft 6 Hunk 4’s “cash always reduces reserved” recipe.
Hunks 1, 2, 3, and 5 of draft 6 stay in force.

Closed draft PR: https://github.com/Ripe-Foundation/ripe-protocol/pull/194

## Owner rulings that changed the design

1. The Contributor clone is trusted. It is created from the HR
   template we set. Do not store a parallel grant map on HR to
   defend against lying `compensation()` / `cliffTime()` getters.
2. Contributor cash and cancel stay as they are today, including
   official pre-cliff cancel crediting **full original C** after an
   early cash.
3. Do not build `ripeAvailForHr` / `MAX` setter machinery for
   overlapping `H = MAX/2` clones. Vesting grants will sit well
   below the HR budget.

## What this ticket implements

| Hunk | Change |
| --- | --- |
| 1 | Overflow-safe vest helper on Contributor. |
| 2 | `areValid` create bounds on HumanResources. |
| 3 | Saturating `getTotalClaimed` / `getTotalCompensation`. |
| 4 (thin) | One Ledger `hrReservedCompensation`: live grant notional. `+= C` on create, 1:1 `−amount` / `budget += amount` on cancel. **Not** reduced on cash. Setter `_amount <= MAX - reserved`. |
| 5 | Infeasible `minCliff > maxVest` reverts on Delta execute. |

HR `cashRipeCheck` stays mint + deposit. HR refund stays one-arg
`refundRipeAfterCancelPaycheck` plus optional burn (burn return
value is asserted). No `hrGrant`, no `hrCancelCreditLiability`,
no `consumeHrContributorCash`, no `applyHrContributorSettlement`.

## Accepted residuals

- After a fully paid, never-cancelled vest, reserved still includes
  that `C`. `setRipeAvailForHr(MAX)` can stay blocked.
- After a post-cliff / frozen cancel of `C-P`, leftover `P` can
  stay in reserved.
- Official cash cannot remint: the trusted clone sends
  `getClaimable()` and increments `totalClaimed`.

## Deployment

Adding one Ledger `uint256` and small HR/Contributor/Delta edits.
No `hrGrant` backfill. Not an A+ storage migration.
