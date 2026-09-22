# Base deployed departments: proposal-only handoff

Import `start-hq-timelocks.safe.json` into the Base governance Safe's Transaction
Builder. It contains 21 readable calls to HQ: replacements of IDs 5–22, followed
by additions of VaultMigrator, RipeReserveEngine and RipeReserveVesting. Confirm
those additions later in exactly that order to obtain IDs 25, 26 and 27.

This batch starts timelocks only. It does not confirm anything, transfer funds,
initialize rewards, refresh snapshots, change parameters or enable departments.
HQ's existing 21,600-block delay (about 12 hours) is unchanged. New department
registry/action delays remain zero. Tokens, Ledger, CCIP and current vaults are
not replaced by this batch. BondBooster is a BondRoom dependency, not an HQ slot.

## Rehearsal evidence

`report.json` records a read-only-upstream Base fork at block **51,663,472**.
All 21 proposals and their later confirmations passed with governance impersonated
locally. No network transaction was signed or sent. This checks ordered governance
calls, not Safe signatures or a Safe MultiSend execution/gas estimate.

- New MC has all 27 live assets; their configurations match exactly.
- All 55 raw borrower debt records, checked Ledger globals and five retained
  vaults' aggregate balances are unchanged by the confirmations.
- No vault funds, shares or locks are migrated. Individual depositor lock records
  were not independently enumerated in this run; aggregate conservation is not
  represented as an exhaustive account-level audit.
- At the original oracle timestamp, all MC assets except RIPE and RIPE/WETH LP
  have nonzero prices. RIPE is deliberately UI-only; RIPE/WETH LP was already
  unpriced on the old desk. Undy quotes have small snapshot-window differences.
- Both legacy SP deposit-asset NAV reads succeed in that current-timestamp
  diagnostic. mcbETH/VVV one-unit dust valuations remain one unit each.
- In the unmodified 12-hour wait, all six staged Undy snapshots become stale.
  A separate fork at the same block confirmed HQ slots 6, 8, 5 and 7, then called
  Alpha.addPriceSnapshot(asset, 8) for all six assets. Every call returned true
  and every Undy quote became nonzero, without rewinding the timestamp or
  fabricating an oracle update. Snapshot refresh must be part of activation.
- Foxtrot.initRewards() passed after MC activation in that separate fork. Its
  saved rewards settings match the live MC's settings.
- The new Alpha's 80% buyback action and new Echo's allowlist-enforcement and
  redemption-enablement actions passed in the post-activation diagnostic.

## Not an approval for bare confirmations

The confirmation sequence alone leaves MC rewards uninitialized, Teller paused,
CE buybacks at zero, and PSM minting/redemption disabled. The later atomic cutover
must include the agreed configuration calls and snapshot refreshes. Populate the
PSM redemption allowlist before relying on allowlisted testing. Recheck live
oracle freshness and pending actions immediately before the actual cutover.

Treasury is still held by old contracts. This run inventoried known MC assets
plus the PSM underlying/yield token, not every historical incoming transfer:

- Old EndaomentFunds: USDC, undyEURC, RIPE, GREEN/USDC LP.
- Old PSM: undyUSDC yield shares.

Those assets still need an explicit transfer sequence, tested before retiring
their old departments. This run did not simulate treasury transfer or end-to-end
liquidation/deleverage, replay department-local state, or prove all pending
controller actions/permissions have been reconciled. Starting the HQ timelocks
does not perform or approve those remaining steps.

Reserves and VaultMigrator remain paused. Reserve economics are dormant
placeholders, not approved sale parameters. The new ReserveEngine's RIPE-minting
permission requires a separate HQ configuration proposal after its registration;
HQ does not permit proposing that permission for an unregistered ID.

Explorer status for all 38 deployed contracts is recorded separately in
`explorer-verification.json`. Any non-success entry remains unresolved and must
not be presented as verified. No live governance transaction was submitted.
