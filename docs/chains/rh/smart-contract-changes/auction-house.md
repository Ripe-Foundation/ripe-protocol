# AuctionHouse: safe-conversion and batch-isolation rationale

## Current disposition

The corrected shared `AuctionHouse` source is integrated into `rh` at commit
`ad831669943ccfe7b9ed57454995dfce51630a66`. It has not been deployed or
activated on Robinhood.

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

## Downstream consistency

AuctionHouse's safe-conversion preflight is paired with Deleverage's
post-withdraw consistency assertion and capped valuation. The two checks defend
different boundaries: preflight prevents a known zero-safe conversion from
mutating the vault, while the downstream check rejects divergent vault or asset
behavior after the actual amount sent is known. See
[`Deleverage.vy` lines 1194-1212](../../../../contracts/core/Deleverage.vy#L1194).

## What this does not authorize

The integrated logic does not select a Robinhood vault, asset, price source,
auction configuration, account, migration, deployment, activation, or release.
