# AuctionHouse: safe-conversion and batch-isolation rationale

## Current disposition

The corrected shared `AuctionHouse` source entered `rh` at historical import
ancestor `ad831669943ccfe7b9ed57454995dfce51630a66`. Current `master` and
current `rh` (`5f5d22b7…`, tree `7454b545…`) both resolve
[`AuctionHouse.vy`](../../../../contracts/core/AuctionHouse.vy) to Git blob
`48cbbbca22c87e490ef0f88aae4f643ab5b87987`, SHA-256
`e5a1603d27e22abc3fa0bf98971dbc16732afe8647b1fe323916216036998921`.
This page is therefore a historical/shared-source rationale rather than a
current `master..rh` production delta. No reviewed Robinhood repository
authority establishes a deployment or activation; no live-chain state was
queried for this documentation refresh.

The current runtime template is 24,373 bytes, with 203 bytes of EIP-170
headroom and SHA-256
`f91c53f0fbfe66b2f9e07003ba712cb976d6941a3b98ec0891918faa0bf6eead`.

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

## Current Stock-delivery and liquidation composition evidence

Later integrated evidence now exercises the AuctionHouse source in the
GuardedErc20/Stock composition rather than only through isolated conversion
helpers:

- [`test_auctionhouse_stock_delivery.py`](../../../../tests/core/auctionHouse/test_auctionhouse_stock_delivery.py),
  Git blob `f19d5dcb1fcf7a6a37132ee1a0b0e02b3b70c3e7`, SHA-256
  `2a0be15fe4241562bee5b3157a1f98d17ba9306c7403314c2a7e514df96a9546`,
  covers Stock collateral delivery, exact movement, atomic failures, and
  composed auction paths;
- [`test_ah_liquidation.py`](../../../../tests/core/auctionHouse/test_ah_liquidation.py),
  Git blob `07ae370b7e6530d84db38413dbc07e3e3d86edf5`, SHA-256
  `5492d71ed4afe64d0e266ccc3557f849b2ad0ffc2bc7d1f69511f2ba36cc0c07`,
  contains the expanded liquidation-composition cases; and
- [`test_ah_auctions.py`](../../../../tests/core/auctionHouse/test_ah_auctions.py),
  Git blob `d45629865f93e22dae240c319d393aed04ac8e82`, SHA-256
  `ecda7d232bf17da43a511f9ac88d3a7ef58f3e4356e9b97edf9af44ab8a71d9a`,
  preserves ordinary auction behavior alongside the new composition evidence.

This closes the prior documentation gap around integrated Stock delivery and
liquidation composition. It does not prove a Robinhood deployment, configured
asset, live liquidity, or final release route. No behavioral test was rerun for
this documentation-only refresh.

## What this does not authorize

The integrated logic does not select a Robinhood vault, asset, price source,
auction configuration, account, migration, deployment, activation, or release.
