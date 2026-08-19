# Group 11 — trusted clone, HR refund clamp

**Status: owner-approved 2026-08-19. Implemented in #195.**

This brief is self-contained. It records the owner-approved
no-Ledger redesign for Human Resources cancellation credit.
The clamp is written against the unchanged Base Ledger
(`refundRipeAfterCancelPaycheck` is a bare `ripeAvailForHr += _amount`).

Closed draft PR: https://github.com/Ripe-Foundation/ripe-protocol/pull/194

## Owner rulings

Approved 2026-08-19:

1. Ledger remains unchanged. No `hrReservedCompensation` or any
   equivalent counter/liability. No Ledger migration, reserve
   backfill, or initialization.
2. Contributor clones are trusted. Do not store a parallel grant
   map on Human Resources to defend against lying
   `compensation()` / `cliffTime()` getters.
3. Do not walk the Contributor set to reconstruct an aggregate
   reserve.
4. Contributor cash and cancel stay as they are today, including
   official pre-cliff cancel reporting **full original C** after
   an early cash.
5. Cancellation credit saturates at the uint256 ceiling:

   `creditedAmount = min(forfeitedAmount, MAX_UINT256 - currentBudget)`

   `MAX_UINT256` means unlimited HR budget. Unrepresentable
   excess credit is intentionally discarded.
6. Human Resources still calls
   `Ledger.refundRipeAfterCancelPaycheck(0)` when no headroom
   exists. The Ledger call is never skipped, so Ledger pause and
   authorization stay on the cancellation path even when credit
   is zero.
7. `RipePaycheckCancelled.forfeitedAmount` reports the full
   forfeiture, not the credited amount.
8. Do not add storage, signatures, return values, or events.
9. Create-time `depositLockDuration` follows the #188 live-max band:
   `0 < D <= live RipeGov max`, live max must be configured, `D`
   below the live min remains allowed, and confirmed terms are not
   rewritten after later min/max changes. Keep the static
   `D <= MAX_UINT256 - 2**64` overflow ceiling.

Ruling 9 supersedes and reverses the earlier draft-6 ruling that
HR create validation should be static slack only and must not
read `ripeGovVaultConfig`. Draft 6 still applies to cash and
final transfer: paycheck deposits remain live-clamped, and the
stored term is forwarded raw on owner transfer.

This also reverses draft 6’s previous no-saturation direction for
Hunk 4. Draft 6 kept ordinary `budget += forfeitedAmount` and
treated a MAX overwrite while live grants existed as a blocked
or retryable path. The owner-approved clamp makes MAX writable
at any time and discards credit that cannot be represented.

## What this ticket implements

| Hunk | Change |
| --- | --- |
| 1 | Overflow-safe vest helper on Contributor. Keep `# dev: vesting length overflow`. |
| 2 | `areValid` create bounds on Human Resources, including the live lock band. |
| 3 | Saturating `getTotalClaimed` / `getTotalCompensation`. |
| 4 | Human Resources refund clamp only. Ledger is byte-identical to the PR base. |
| 5 | Infeasible `minCliff > effectiveMaxVest` reverts on Delta execute. |

Hunks 1, 2, 3, and 5 remain. The trusted-clone ruling remains.

Hunk 2’s seven representability bounds reject a create when:

1. `compensation > MAX_UINT256 // 2`
2. `vestingLength > 2**128`
3. `depositLockDuration > MAX_UINT256 - 2**64`
4. `startDelay > MAX_UINT256 - block.timestamp`
5. `vestingLength > MAX_UINT256 - startTime`
6. `cliffLength > MAX_UINT256 - startTime`
7. `unlockLength > MAX_UINT256 - startTime`

Those are static overflow checks. Creation and confirmation also
require a live RipeGov lock band:

- `depositLockDuration != 0`
- live `maxLockDuration != 0`
- `depositLockDuration <= live maxLockDuration`

A duration below the live general minimum is still allowed. Later
min/max changes do not rewrite a confirmed term. If the live
maximum falls below a pending duration before confirmation, the
pending action is cancelled and no clone is deployed.

Hunk 4 is only this Human Resources boundary:

```
budget = Ledger.ripeAvailForHr()
creditedAmount = min(_amount, max_value(uint256) - budget)
Ledger.refundRipeAfterCancelPaycheck(creditedAmount)
```

Ordinary below-ceiling refunds stay exact:
`budget += forfeitedAmount`. When `budget == MAX`, the call still
happens with `creditedAmount == 0` and the budget stays `MAX`.

HR `cashRipeCheck` stays mint + deposit. The RIPE burn assertion
and false-return rollback stay. No `hrGrant`, no
`hrCancelCreditLiability`, no `consumeHrContributorCash`, no
`applyHrContributorSettlement`.

Hunk 5 uses an effective vesting maximum at Delta execute:

- configured `maxVestingLength`, when nonzero;
- `2**128`, when configured max is zero.

Require `minCliffLength <= effectiveMaxVestingLength`. Equality
is accepted. A failed execute keeps the `# dev: infeasible hr
config` reason, rolls back the config write, and leaves the
pending action in place. HR still hard-caps
`vestingLength <= 2**128`, so a zero configured max is not
unbounded.

## Rejected reserve design (historical)

The previous thin-Ledger draft added `hrReservedCompensation`:
`+= C` on create, 1:1 decrement on cancel, unchanged on cash,
and `setRipeAvailForHr(_amount)` required
`_amount <= MAX - reserved`. That design is rejected. It is not
implemented here. Ledger has no reserve field, getter, update,
or setter-headroom guard.

## Accepted residuals

- At `MAX`, any positive forfeiture credits `0`. The event still
  reports the full forfeiture. Excess credit that cannot be
  represented is discarded.
- After a fully paid, never-cancelled vest, `setRipeAvailForHr(MAX)`
  succeeds. There is no leftover reserved notional.
- After a post-cliff or frozen cancel of `C-P` at a below-ceiling
  budget, the budget increases by `C-P` exactly.
- Official cash cannot remint: the trusted clone sends
  `getClaimable()` and increments `totalClaimed`.
- A `MAX//2` grant can still exceed RipeGov/SharesVault
  representable share output when fully cashed, and two such
  grants can exceed remaining RIPE total-supply headroom. Those
  are governance-only, unrealistic-value cases and remain out of
  scope.
- Pre-cliff cancellation withdraws and burns the Contributor’s
  entire RIPE vault position, including unrelated RIPE deposited
  to that address. Enabling third-party deposits or directing
  other rewards to a Contributor can expose those tokens to
  cancellation burn. This is accepted pre-existing behavior, not
  introduced by #195.
