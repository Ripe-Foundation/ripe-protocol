# AuctionHouse: safe-conversion and batch-isolation rationale

## Current disposition

This worktree extends the historically shared `AuctionHouse` source with
backing-aware BasicVault consumer boundaries. The candidate source is Git blob
`2241f8cb38f4f69c68e9da535119b525256af8dc`, SHA-256
`2c2332d6e1a5fe1ad77c30554ecbb95e2ea78feec228ad56196aa663e251fe89`.
It is not integrated into `rh`, deployed, configured, or activated.

The runtime template is 24,436 bytes, with 140 bytes of template headroom and
SHA-256
`f9d1f719d28f0fd48f98317307b366aa261a607328335d81869eed6c0fd384a6`.
The constructor-bound deployed runtime is 24,532 bytes, leaving 44 bytes below
the EIP-170 limit.

## Why the change exists

When Deleverage withdraws an Underscore Basic Earn vault asset, the vault's
nominal share amount is insufficient evidence that the underlying conversion
is usable. AuctionHouse now performs a preflight before the vault mutates
either ledger or token state:

- clamp the requested amount to the user's recorded vault amount;
- clamp again to the vault's actual token balance;
- call `convertToAssetsSafe` on that bounded amount; and
- return the soft-zero result `(0, false)` when safe conversion is zero.

The exact boundary is
[`AuctionHouse.vy` lines 1189-1208](../../../../contracts/core/AuctionHouse.vy#L1189).
Only the registered Deleverage address can invoke this wrapper.

## Soft-zero and batch behavior

Auction purchase helpers are intentionally soft-failing for per-item
conditions: invalid recipient, inactive or out-of-window auction, disallowed
configuration, zero available balance, absent vault, or zero collateral can
return zero without corrupting the rest of a multi-purchase attempt. The batch
loop subtracts only the amount actually spent, so one skipped purchase does not
consume another purchase's GREEN budget. See
[`AuctionHouse.vy` lines 1047-1078](../../../../contracts/core/AuctionHouse.vy#L1047)
and [`AuctionHouse.vy` lines 1081-1168](../../../../contracts/core/AuctionHouse.vy#L1081).

This is batch isolation, not error suppression for completed transfers: once
collateral is sent, payment transfer, amount-consistency, and debt repayment
must all succeed atomically.

## Deficient BasicVault collateral

Priority liquidation and general vault iteration now require a nonzero
backing-aware amount before attempting stability-pool settlement or auction
creation. Manual auction creation rejects a deficient position. If an existing
auction becomes deficient, its purchase returns zero without mutating auction,
debt, GREEN, or collateral state, allowing a batch to preserve earlier healthy
purchases.

An all-deficient liquidation now leaves `inLiquidation` false when it seizes
nothing and creates no auction, so backing restoration can be followed by a
permissionless retry. Stability Pool's truthful indexed getter also restores
phase-2 visibility for eligible positions; CreditEngine separately excludes
stability vault ID `1` from borrowing power.

The Deleverage withdrawal wrapper and collateral-transfer helper also return a
soft-zero/skip result for deficient collateral. Deleverage can therefore
continue to later healthy assets instead of reverting the entire user flow.

## Downstream consistency

AuctionHouse's safe-conversion preflight is paired with Deleverage's
post-withdraw consistency assertion and capped valuation. The two checks defend
different boundaries: preflight prevents a known zero-safe conversion from
mutating the vault, while the downstream check rejects divergent vault or asset
behavior after the actual amount sent is known. See
[`Deleverage.vy` lines 1194-1212](../../../../contracts/core/Deleverage.vy#L1194).

## Current Stock-delivery and liquidation composition evidence

The feature tests exercise the shared protected SimpleErc20 composition rather
than only isolated conversion helpers:

- [`test_auctionhouse_stock_delivery.py`](../../../../tests/core/auctionHouse/test_auctionhouse_stock_delivery.py)
  covers exact Stock collateral delivery, atomic failures, deficient existing
  auctions, batch preservation, and cross-vault liquidation continuation;
- [`test_ah_liquidation.py`](../../../../tests/core/auctionHouse/test_ah_liquidation.py)
  contains the expanded liquidation-composition cases; and
- [`test_ah_auctions.py`](../../../../tests/core/auctionHouse/test_ah_auctions.py)
  preserves ordinary auction behavior and freezes the current source, ABI,
  and shared Vault interface.

This evidence does not prove a Robinhood deployment, configured asset, live
liquidity, or final release route.

## What this does not authorize

The integrated logic does not select a Robinhood vault, asset, price source,
auction configuration, account, migration, deployment, activation, or release.
