# Stock Token Vault Loss Mitigation and Fix Recommendations

**Status:** Recommendation for owner review; not approved for implementation

**Prepared:** 23 July 2026

**Applies to:** the shared Base/Robinhood vault, borrowing, liquidation, and
operations paths

**Evidence basis:** [`stock-token-vault-comparison.md`](stock-token-vault-comparison.md)
and [`stock-token-vault-decision.md`](stock-token-vault-decision.md)

## Owner direction and scope

The owner confirmed that approval to continue Track 5 analysis was not
acceptance of the zero-backed behavior and requested a concrete record of:

- the simplest way to stop borrowing against phantom assets;
- the production changes needed to make the behavior safe;
- the operational response if live custody and protocol accounting diverge;
  and
- the longer-term vault design recommended for issuer-controlled collateral.

This document supplies that recommendation. It does not modify production
contracts, change live configuration, select a production vault, authorize a
migration, or authorize deployment.

## Executive recommendation

Use a defense-in-depth sequence rather than treating one change as the entire
solution:

1. **Immediate operational protection:** continuously compare actual ERC-20
   custody with the vault's accounted amount. On any deficit, disable all new
   borrowing with the existing global borrow switch, disable deposits for the
   affected asset, and disable purchases of that asset's auctions.
2. **Smallest phantom-borrowing code guard:** make `SimpleErc20` return zero
   CreditEngine collateral amount for an asset whenever its aggregate live
   balance is below its aggregate accounted balance. Do not attempt a partial
   per-user allocation in this first patch. Reject internal balance transfers
   while that deficit exists. This guard must ship with the deficit-aware
   debt-health behavior described below; it is not safe as a standalone view
   change.
3. **Required companion fix:** measure the exact token balance delta for every
   deposit. Otherwise a short-received transfer can itself create an accounted
   deficit.
4. **Stock Token settlement policy:** do not permit internal auction settlement
   for issuer-controlled assets. Require actual external token delivery before
   GREEN payment and debt reduction are committed.
5. **Preferred permanent vault direction:** use share-based, pro-rata live
   claims for issuer-controlled collateral, with explicit total-loss,
   post-zero, and bad-debt behavior added before listing.

The minimum code mitigation deliberately values an affected asset at zero
rather than trying to use its remaining custody. This is conservative, simple
to audit, and guarantees that users do not receive credit for tokens the
protocol cannot allocate safely.

## The invariant that must be enforced

For each `(vault, asset)`:

```text
live custody     = IERC20(asset).balanceOf(vault)
accounted amount = the aggregate token amount represented by vault accounting
deficit          = live custody < accounted amount
```

The following must always be true:

```text
sum of amounts credited for borrowing <= live custody
GREEN paid during settlement <= value of collateral actually and safely delivered
```

For the minimum fail-closed patch, use the stronger rule:

```text
if deficit:
    borrowing amount for every user of that vault asset = 0
    internal settlement for that vault asset = disabled
```

This stronger rule avoids silently choosing a loss-allocation policy in an
emergency patch.

## Immediate mitigation using current production controls

### Continuous solvency check

Monitor every registered ERC-20 vault asset at least once per block, supplemented
by every relevant token/vault event:

```text
liveBalance      = token.balanceOf(vault)
reportedTotal    = vault.getTotalAmountForVault(token)
rawStoredTotal   = vault.totalBalances(token), where exposed
deficit          = liveBalance < reportedTotal
```

For `SimpleErc20`, `reportedTotal` is nominal accounting and can exceed live
custody. For `RebaseErc20`, the common total view is already the live token
balance; monitoring must also retain raw share supply so a zero-live,
nonzero-share state is visible. A Rebase partial loss will not appear as
`liveBalance < reportedTotal`; it must be detected as an unexplained decrease
in assets per share, an issuer-control event, or a custody decrease without a
matching vault withdrawal.

Alert data must include:

- chain, vault address and VaultBook ID;
- asset address and symbol;
- live balance, reported amount, raw stored amount, and deficit;
- deposit, borrow, withdrawal, and auction flags;
- token pause/blocklist state when available;
- users with the affected asset and their debt state; and
- the first block and transaction where the divergence appeared.

Monitoring is detection, not the fix. No monitor should automatically rewrite
user balances or treat a later donation as proof that the original loss has
been restored to the same users.

### Deficit response

When `liveBalance < reportedTotal` is confirmed:

1. Call the existing global `SwitchboardAlpha.setCanBorrow(False)` path. This
   is currently the only reliable immediate switch that prevents all new
   GREEN borrowing.
2. Call `SwitchboardCharlie.setCanDepositAsset(asset, False)` for the affected
   asset so new deposits cannot be captured by old claims or deepen ambiguous
   accounting.
3. Call `SwitchboardCharlie.setCanBuyInAuctionAsset(asset, False)` so neither
   internal nor external purchases proceed while the affected asset is under
   incident review.
4. Keep repayment enabled.
5. Reconcile affected users, debt, auctions, token-control events, and actual
   custody before re-enabling anything.
6. Make an explicit owner decision on withdrawals. Allowing withdrawals during
   a `SimpleErc20` deficit gives remaining custody to first movers; disabling
   withdrawals freezes all users. There is no neutral automatic choice under
   the current accounting.

Disabling deposits alone does **not** stop existing phantom collateral from
supporting new debt. Pausing a vault also does not change the amount returned
to CreditEngine. The global borrow switch is therefore required until a
per-asset fail-closed borrowing control exists.

### Why setting LTV to zero is not the emergency control

For a newly configured, not-yet-live Stock Token, keeping LTV at zero is a
valid pre-launch guard.

For an already enabled asset, the current
`SwitchboardBravo._isLtvWithinMaxDeviation` explicitly rejects changing a
nonzero LTV directly to zero (`SwitchboardBravo.vy:553-565`). Even if that
restriction were removed, an LTV change would not:

- fix internal auction settlement;
- fix first-withdrawer behavior;
- fix post-zero deposits;
- reconcile existing nominal balances; or
- provide a total-loss bad-debt path.

LTV is an economic parameter, not a custody-integrity switch.

## Smallest code mitigation for phantom borrowing

This is the recommended first component of a shared contract patch for the live
`SimpleErc20` path. Together with the deficit-aware debt-health behavior below,
it prevents the most dangerous consequence—new credit against an aggregate
custody deficit—without choosing how remaining tokens should be allocated among
users.

### 1. Make the CreditEngine-only amount view fail closed

`BasicVault._getUserAssetAndAmountAtIndex` is the view used by
`CreditEngine._getUserBorrowTerms` (`BasicVault.vy:114-121`;
`CreditEngine.vy:687-769`). Before returning the user's nominal amount:

```text
asset          = userAssets[user][index]
userNominal    = userBalances[user][asset]
accountedTotal = totalBalances[asset]
liveTotal      = IERC20(asset).balanceOf(self)

if liveTotal < accountedTotal:
    return asset, 0

return asset, userNominal
```

CreditEngine already skips zero amounts before pricing them. The result is:

- a solvent asset behaves exactly as it does today;
- any aggregate deficit gives that asset zero borrowing value for every user;
- unrelated solvent collateral remains usable;
- `getMaxBorrowAmount` and actual borrow validation use the same fail-closed
  value; and
- the token cannot support additional GREEN issuance while underbacked.

This view change must not be deployed by itself when existing debt can be
present. CreditEngine currently skips a zero amount before collecting that
asset's debt terms. If the affected asset is the user's only collateral, the
weighted liquidation threshold can therefore become zero and
`canLiquidateUser` can return false. Release 1 must propagate an explicit
deficit state into debt health and liquidation so zero borrowing value cannot
be misread as healthy or non-actionable debt. Until that companion behavior is
implemented, the operational response remains the global borrow shutdown and
the affected-asset auction shutdown.

This first patch should not return
`min(userNominal, liveTotal)`. With multiple users, that calculation can credit
the same live tokens to each user and still make aggregate borrowing exceed
custody.

It should also not pro-rate users in the minimal patch. Pro-rating is a valid
permanent policy, but it is a policy choice with rounding, withdrawal,
settlement, reward, and post-zero consequences. Fail-closed valuation is the
smaller and safer emergency invariant.

### 2. Reject internal transfers while Simple is underbacked

Before `BasicVault._transferBalanceWithinVault` reduces one user's nominal
balance and credits another, require:

```text
IERC20(asset).balanceOf(self) >= totalBalances[asset]
```

If the check fails, the internal move must revert before either user's
accounting changes. This prevents AuctionHouse from interpreting a nominal
movement as delivered collateral while the asset is underbacked.

The same check must cover internal transfers initiated by both AuctionHouse
and CreditEngine. It is a solvency check, not an issuer-specific branch.

### 3. Add a per-asset borrowing kill switch

The protocol currently has a global `canBorrow` flag but no independent
per-asset `canUseAsCollateral` flag. Add a generic asset configuration flag
whose disabled state gives that asset zero borrowing credit when computing:

- collateral value;
- maximum debt;
- borrow previews;
- borrow validation; and
- debt-health/liquidation terms, while preserving the explicit deficit state
  needed to resolve existing debt.

Disabling this flag must be a fast, permissioned safety action. Re-enabling it
should require the normal stronger governance confirmation path and a
successful backing reconciliation.

The automatic deficit check remains necessary even after this flag exists. The
flag provides an operational override; it must not be the only thing standing
between an unnoticed issuer burn and phantom credit.

### 4. Fix deposit measurement in the same release

Teller currently transfers the requested amount and then the vault infers the
deposit from the requested amount and aggregate post-transfer balance
(`Teller.vy:271-305`; `BasicVault.vy:23-39`;
`SharesVault.vy:25-46`).

Measure the per-call delta instead:

```text
before = IERC20(asset).balanceOf(vault)
perform transferFrom or transfer to vault
after = IERC20(asset).balanceOf(vault)
received = after - before

require received > 0
credit, emit, and apply limits using received
```

The vault must receive `received`, not the originally requested amount. Tests
must cover fee-on-transfer, short delivery, a prior donation, and tokens that
change behavior between calls.

Without this change, an ordinary short-received deposit can cause
`accountedTotal > liveTotal`, activating the new fail-closed borrowing guard
even without an issuer loss.

## Auction and liquidation changes

### External-only settlement for issuer-controlled collateral

For a Stock Token or any asset with arbitrary burn, forced transfer,
confiscation, pause, or blocklist controls, require external settlement:

```text
AuctionHouse -> vault.withdrawTokensFromVault(...)
             -> token transfer to recipient succeeds
             -> amount actually delivered is returned
             -> GREEN payment and debt reduction commit
```

Add an asset-level configuration such as
`allowInternalAuctionSettlement`. It must be `False` for Stock Tokens.
AuctionHouse must reject `_shouldTransferBalance=True` when the flag is false;
the buyer must not be able to override the asset policy.

The existing external path is the safer basis because a pause, blocklist, or
missing balance reverts the transaction atomically before GREEN payment and
debt reduction persist. Internal accounting cannot prove ERC-20
deliverability.

### Keep a generic backing check even with external-only Stock Tokens

External-only settlement protects the buyer, but the borrowing and debt-health
views still need live backing. The backing guard must therefore be independent
of auction configuration.

### Define deficit and total-loss debt progress

When the fail-closed guard gives an underbacked asset zero credit—or when an
asset's live-backed amount actually becomes zero—CreditEngine can also lose
the weighted liquidation threshold. Today `_canLiquidateUser` returns false
when the threshold is zero (`CreditEngine.vy:971-979`), even if debt remains.

The follow-on implementation must define a distinct uncollateralized-debt
state:

1. an aggregate deficit is carried as an explicit debt-health input rather
   than disappearing when the priced amount is set to zero;
2. debt greater than zero with deficit or zero live-backed collateral is
   eligible for resolution even when the weighted liquidation threshold is
   zero;
3. no auction is created for zero-backed collateral;
4. no liquidator is asked to pay for the missing asset;
5. remaining deliverable collateral, if any, is handled normally through a
   settlement path that cannot exceed custody;
6. the unrepaid remainder is transferred exactly once into the existing
   protocol bad-debt accounting; and
7. the user's debt and `Ledger.badDebt` cannot both retain the same liability.

This transition requires a separate invariant and lifecycle review. Simply
changing `_canLiquidateUser` to return true at zero is insufficient because it
would permit entry without defining how the unrecoverable debt exits the user
position.

## Preferred permanent vault behavior

For issuer-controlled collateral, the preferred direction remains
`RebaseErc20`/`SharesVault`, after the following gaps are fixed:

1. deposits use exact per-call received balance delta;
2. partial custody loss reduces every user's live claim pro rata;
3. CreditEngine always consumes the live converted claim, never raw shares;
4. internal auction settlement is disabled for Stock Tokens;
5. total loss enters the explicit uncollateralized-debt path;
6. when live balance is zero and old shares remain, new deposits are disabled
   until governance completes the loss-resolution/migration procedure;
7. rewards and monitoring distinguish raw shares from live token claims; and
8. rounding guarantees that aggregate credited/withdrawable amounts never
   exceed live custody.

The simplest safe post-zero rule is a freeze:

```text
if totalShares > 0 and liveBalance == 0:
    reject new deposits
    reject internal settlement
    report zero borrowing value
    enter the defined debt/loss-resolution process
```

Do not allow a fresh depositor to recapitalize old shares implicitly. Any
recapitalization or restoration must be an explicit owner-approved operation
with documented allocation.

## Approaches not recommended

### `min(user nominal, live vault balance)`

Unsafe with multiple users because each user can be credited against the same
aggregate live balance.

### Silently rewriting nominal balances after a loss

This chooses who bears the loss, can change user property rights, and can make
later donations or recoveries impossible to attribute. It requires an explicit
allocation and migration design.

### Treating a later donation as automatic recovery

The donor, issuer, old users, and new users may have different claims. A
balance increase alone does not establish who should receive it.

### Oracle-price removal as the primary kill switch

A missing/zero price may revert broader account-health calculations and can
block liquidation or withdrawal paths. Custody solvency and price validity are
separate conditions and need separate controls.

### Monitoring without an onchain guard

Monitoring can be delayed or fail. Borrow validation and settlement must fail
closed onchain even if no operator reacts.

### LTV-only mitigation

LTV changes do not make auction delivery honest and are not an immediate
per-asset shutdown mechanism under the current Switchboard rules.

## Base deployment implications

The checked-in Base defaults route multiple collateral assets through vault ID
3 (`DefaultsBase.vy:1237-1249`), and the repository's canonical deployment/test
configuration assigns ID 3 to `SimpleErc20` (`tests/conf_core.py:670-688`).
That establishes relevance to the Base architecture, but it does not by itself
prove the exact currently deployed Base bytecode or live registry mapping.
Track 3 must record those onchain source/version facts before migration.

The accounting flaw is reachable for a Base asset only if live custody can fall
without the matching Simple vault accounting falling—for example, forced burn
or confiscation, negative rebase, an unaccounted token transfer, or an
overcredited short-received deposit. A conventional non-rebasing ERC-20 that
cannot remove tokens from the vault does not spontaneously create the issuer
burn scenario. Stock Tokens make the precondition directly material because
issuer control may remove or freeze custody independently of Ripe's nominal
ledger.

The recommended Base response is:

1. add the live/accounted invariant monitor now;
2. prepare the global-borrow, per-asset-deposit, and per-asset-auction shutdown
   runbook;
3. implement the shared fail-closed borrowing, deficit-aware debt-health, and
   internal-transfer guards in a new canonical vault version;
4. deploy and register that version rather than introducing Base-only logic;
5. disable new deposits into the old version before migration;
6. reconcile every old-vault asset and user position; and
7. migrate only through a separately tested, owner-approved procedure.

Existing funds mean a VaultBook address cannot simply be replaced without
respecting its live-funds checks and the users' stored positions. Robinhood
must deploy the same approved shared source/version; it must not launch Stock
Token borrowing on the old Simple implementation.

## Required acceptance tests

No fix is complete until tests prove:

1. a one-unit aggregate deficit makes the affected Simple asset contribute
   zero to `getMaxBorrowAmount` and actual borrow validation;
2. other solvent assets in the same account retain their correct borrowing
   value;
3. partial and total issuer burns cannot support new GREEN debt;
4. the sum of all user borrowing amounts for an asset never exceeds live
   custody;
5. internal transfers revert atomically during a deficit;
6. no failed internal or external settlement charges GREEN or reduces debt;
7. Stock Token auctions cannot select internal settlement;
8. external pause/blocklist failures remain atomic and retryable;
9. fee-on-transfer and short-received deposits credit exactly the received
   delta;
10. pre-existing donations are not credited as a new user's deposit;
11. total loss enters the bad-debt path exactly once without auctioning missing
    tokens;
12. new deposits are rejected while zero live balance and old claims coexist;
13. a partial deficit with existing debt cannot become non-liquidatable merely
    because fail-closed valuation produced a zero weighted threshold;
14. Base and Robinhood deployments use the same source and behavior; and
15. monitoring reports nominal amount, raw shares, live claim, live custody,
    and deficit without conflating the units.

The existing Track 5 comparison suite should remain as regression coverage.
New tests must initially fail against the current unsafe behavior and pass only
against the proposed shared version.

## Recommended implementation order and gates

### Release 0 — operations only

- deploy monitoring and alerts;
- write and rehearse the deficit response runbook; and
- keep Robinhood Stock Token deposits and borrowing disabled.

**Gate:** owner approval is required before any Base configuration transaction.

### Release 1 — minimum shared safety patch

- exact deposit delta;
- fail-closed Simple borrowing value on aggregate deficit;
- an explicit deficit signal carried through debt health so existing debt cannot
  become falsely healthy or non-liquidatable;
- internal-transfer deficit guard;
- per-asset collateral enable/disable flag; and
- tests for all CreditEngine and AuctionHouse consumers.

Release 1 is a containment release: it stops new phantom-backed debt and stops
nominal internal settlement. If a deficit already exists, repayment remains
available but final loss allocation and bad-debt disposal remain frozen pending
Release 2. It must not manufacture a zero-backed auction merely to make the
position appear to progress.

**Gate:** contract review, audit decision, Base migration plan, and owner
approval.

### Release 2 — issuer-controlled collateral completion

- approved share-based vault behavior;
- external-only Stock Token auction policy;
- total-loss and bad-debt transition;
- post-zero deposit/recovery policy;
- monitoring/event semantics; and
- Base/Robinhood migration and smoke tests.

**Gate:** explicit owner vault selection and acceptance of the complete
loss-allocation and bad-debt behavior.

## Decision requested from the owner

The technical recommendation is:

> Ship the fail-closed borrowing guard and deficit-aware debt-health handling as
> the smallest shared containment patch, force external settlement for Stock
> Tokens, and use a corrected share-based vault as the permanent
> issuer-controlled collateral path.

This recommendation is not yet authorization to implement or deploy it. The
next owner decision is whether to open Release 1 as a dedicated shared
vault-change implementation track.
