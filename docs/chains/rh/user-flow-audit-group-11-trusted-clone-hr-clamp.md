# Group 11 — trusted clone, HR refund clamp

**Status: owner-approved 2026-08-19 and implemented in #195. The Hunk 4
cancellation-credit rule is partially superseded by the owner-authorized PR
#211 candidate dated 2026-08-25; integration remains pending.**

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
   `compensation()` / `cliffTime()` getters. The 2026-08-25 supersession
   extends the getter set trusted by cancellation accounting to
   `totalClaimed()`.
3. Do not walk the Contributor set to reconstruct an aggregate
   reserve.
4. **Partially superseded 2026-08-25.** Contributor cash, cancellation
   state, and event reporting stay unchanged. Official pre-cliff cancel
   after an early cash still reports **full original C**. The former
   implication that Ledger must also credit the full `C` is superseded
   by the burn-coupled rule below.
5. Cancellation credit saturates at the uint256 ceiling. The original
   rule used `forfeitedAmount` directly:

   `creditedAmount = min(forfeitedAmount, MAX_UINT256 - currentBudget)`

   `MAX_UINT256` means unlimited HR budget. Unrepresentable excess
   credit is intentionally discarded. The non-burn path still uses
   this rule; the 2026-08-25 burn path first derives `refundAmount`
   under the superseding formula below and applies the same clamp.
6. Human Resources still calls
   `Ledger.refundRipeAfterCancelPaycheck(0)` when no headroom
   exists. The Ledger call is never skipped, so Ledger pause and
   authorization stay on the cancellation path even when credit
   is zero.
7. `RipePaycheckCancelled.forfeitedAmount` reports the full
   forfeiture, not the credited amount.
8. Do not add storage, signatures, return values, or events.
9. Create-time `depositLockDuration` follows the live-max band now
   on `rh` after #188 merged: `0 < D <= live RipeGov max`, live max
   must be configured, `D` below the live min remains allowed, and
   confirmed terms are not rewritten after later min/max changes.
   Keep the static `D <= MAX_UINT256 - 2**64` overflow ceiling.

Ruling 9 supersedes and reverses the earlier draft-6 ruling that
HR create validation should be static slack only and must not
read `ripeGovVaultConfig`. Draft 6 still applies to cash and
final transfer: paycheck deposits remain live-clamped, and the
stored term is forwarded raw on owner transfer. #188 is already
merged; its live lock-band behavior is now base `rh` behavior.

This also reverses draft 6’s previous no-saturation direction for
Hunk 4. Draft 6 kept ordinary `budget += forfeitedAmount` and
treated a MAX overwrite while live grants existed as a blocked
or retryable path. The owner-approved clamp makes MAX writable
at any time and discards credit that cannot be represented.

## 2026-08-25 PR #211 Hunk 4 supersession

The owner authorized a narrow candidate change to the burn-path cancellation
credit. The `_shouldBurnPosition == False` path is unchanged. On the burn path,
Human Resources first withdraws the selected Contributor position, checkpoints
Lootbox, calculates
`actualBurnAmount = min(withdrawalAmount, RIPE.balanceOf(HumanResources))`, and
burns `actualBurnAmount`. It then calculates:

`claimedAmount = min(_amount, Contributor(msg.sender).totalClaimed())`

`recoveredClaimedAmount = min(claimedAmount, actualBurnAmount)`

`refundAmount = _amount - claimedAmount + recoveredClaimedAmount`

The existing uint256 budget-headroom clamp applies to `refundAmount`, and
`Ledger.refundRipeAfterCancelPaycheck` is still called when the credited amount
is zero. Existing Teller housekeeping, conditional legacy-vault cleanup, the
burn assertion, and transaction-wide atomic rollback remain unchanged.

RIPE is fungible for this calculation. Any RIPE actually burned from the
selected Contributor position, including unrelated residue, offsets claimed
compensation up to `claimedAmount`. Claimed compensation capacity is never
restored by more than the amount actually burned. The candidate adds no
storage, signatures, return values, or events and leaves Ledger unchanged.

## What this ticket implements

| Hunk | Change |
| --- | --- |
| 1 | Overflow-safe vest helper on Contributor. Keep `# dev: vesting length overflow`. |
| 2 | `areValid` create bounds on Human Resources, including the live lock band. |
| 3 | Saturating `getTotalClaimed` / `getTotalCompensation`. |
| 4 | Human Resources burn-coupled refund on the pre-cliff burn path, followed by the existing refund clamp. Ledger remains byte-identical. |
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

At the PR #211 candidate, Hunk 4 is only this Human Resources boundary:

```
if not _shouldBurnPosition:
    refundAmount = _amount
else:
    # Existing withdrawal and Lootbox checkpoint happen first.
    actualBurnAmount = min(withdrawalAmount, RIPE.balanceOf(HumanResources))
    burn(actualBurnAmount)
    claimedAmount = min(_amount, Contributor(msg.sender).totalClaimed())
    recoveredClaimedAmount = min(claimedAmount, actualBurnAmount)
    refundAmount = _amount - claimedAmount + recoveredClaimedAmount

budget = Ledger.ripeAvailForHr()
creditedAmount = min(refundAmount, max_value(uint256) - budget)
Ledger.refundRipeAfterCancelPaycheck(creditedAmount)
```

Below the ceiling, non-burn refunds stay exact. Burn-path credit can be less
than `forfeitedAmount`: it restores the unclaimed amount plus claimed capacity
offset by actual burn. When `budget == MAX`, the call still happens with
`creditedAmount == 0` and the budget stays `MAX`.

HR `cashRipeCheck` stays mint + deposit. The RIPE burn assertion
and false-return rollback stay. No `hrGrant`, no
`hrCancelCreditLiability`, no `consumeHrContributorCash`, no
`applyHrContributorSettlement`.

Hunk 5 uses an effective vesting maximum at Delta execute that
mirrors Human Resources’ absolute `vestingLength <= 2**128`
ceiling:

- `2**128` when configured `maxVestingLength` is zero;
- `min(configured max, 2**128)` when configured max is nonzero.

That covers an alternate registered switchboard seeding
`maxVestingLength > 2**128`. Official Delta cannot then accept
`minCliffLength > 2**128`. Equality at `2**128` is accepted.
A failed execute keeps the `# dev: infeasible hr config` reason,
rolls back the config write, and leaves the pending action.
The zero-max reject/equality test remains, and an Alpha-seeded
`maxVestingLength = 2**129` proof shows `minCliff = 2**128 + 1`
reverts while `2**128` succeeds. Restoring the old “trust any
nonzero max” check makes that oversize-max test fail.

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
- Burn-path credit trusts the selected Contributor clone's
  `totalClaimed()`. A clone that understates it can over-restore
  compensation capacity. This is within the existing trusted-clone
  ruling; Human Resources keeps no parallel grant or provenance record.
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
  introduced by #195. Under the PR #211 candidate, that fungible burn
  also restores claimed compensation capacity, capped by
  `min(claimedAmount, actualBurnAmount)`.
- Cancellation burns only one selected RipeGov position. If
  `actualBurnAmount < claimedAmount`, the difference is not
  automatically recovered after the one-shot cancellation. Any later
  compensation-budget adjustment is a separate owner-authorized
  governance action.
- `RipePaycheckCancelled.forfeitedAmount` continues to report the full
  forfeiture, not the Ledger credit. The values can diverge because of
  burn shortfall or uint256 headroom, and no event reports the credited
  amount. Off-chain accounting must reconcile exact pre- and post-call
  `ripeAvailForHr` state.

## Open owner policy follow-up

`Contributor._getTotalVested()` continues vesting from `startTime` and does not
use `cliffTime`, so pre-cliff cash remains possible. PR #211 changes only the
cancellation-accounting consequence. Whether the cliff should also gate
claiming remains a separate owner policy decision and is not decided or
implemented here.
