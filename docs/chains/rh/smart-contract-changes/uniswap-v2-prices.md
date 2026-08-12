# UniswapV2Prices: RIPE/WETH monitoring-only adapter

## Scope

[`UniswapV2Prices.vy`](../../../../contracts/priceSources/UniswapV2Prices.vy)
is deliberately not an oracle. It is a stateless observer for exactly one
canonical 18-decimal RIPE/WETH Uniswap V2 pair.

The contract continues to implement the repository `PriceSource` interface so
registry and generic tooling can call it safely. That interface is an inert
compatibility shell:

- `getPrice` always returns zero;
- `getPriceAndHasFeed` always returns `(0, false)`;
- `hasPriceFeed` and every pending-action view return false;
- `getPricedAssets` returns an empty list;
- every feed, snapshot, disable, and timelock mutation returns false; and
- unsupported no-return pause and recovery mutations revert `monitoring only`.

An accidental PriceDesk registration therefore neither supplies a protocol
price nor creates a missing-selector denial of service.

## Functional monitoring surface

Only four non-interface behaviors remain:

- `isMonitoringOnly()` identifies the contract's permanent role;
- `getRipePoolState()` returns RIPE reserve, WETH reserve, and pair timestamp;
- `getRipeWethMonitoringPrice()` returns the current spot WETH-per-RIPE ratio;
- `getRipeUsdMonitoringPrice()` combines that ratio with PriceDesk's current
  WETH/USD observation for direct monitoring.

The constructor binds RipeHq, the pair, RIPE, and WETH as immutables. It
requires the pair to contain exactly RIPE and WETH, in either order, and
requires both tokens to use 18 decimals. PriceDesk is resolved dynamically
through RipeHq ID 7 so a registry rotation does not stale the USD monitoring
view.

Pool, RipeHq, and PriceDesk reads fail closed to zero on a revert or malformed
response. Arithmetic overflow in the WETH/USD multiplication also returns
zero. These checks improve monitoring robustness; they do not make the spot
ratio safe for protocol valuation.

## Removed oracle-like machinery

The monitoring revision removes all snapshot storage, ring-buffer averaging,
staleness policy, upside throttling, pending configuration, local governance,
action timelocks, pause state, priced-asset state, and generic asset handling.
Historical sampling, aggregation, alerting, and manipulation detection belong
in the off-chain monitoring system.

This removal is intentional. Snapshot and throttling machinery made a
manipulable spot observer resemble a collateral-grade oracle without providing
the security properties of one.

## Verification

[`test_minimal_prices.py`](../../../../tests/priceSources/uniswap/test_minimal_prices.py)
covers both token orderings, immutable identity, exact pair and decimal
validation, all PriceSource stubs, reserve and USD observations, zero reserves,
malformed and reverting dependencies, missing WETH/USD data, overflow, and the
immediate/non-persistent effect of reserve manipulation.

The deployment migration binds the new four-argument constructor and performs
readbacks of the monitoring marker, immutables, and permanent no-feed result.
The repository ABI and constructor-bound deployed-runtime identity are
regenerated from the integrated source. The measured deployed runtime is 3,781
bytes, with 20,795 bytes of EIP-170 headroom.

## Readiness boundary

The existing deployed instance cannot be changed in place. Source changes
describe a replacement deployment, which requires separate authorization,
runtime/constructor binding, manifest handling, and operational consumer
updates. This PR does not deploy, register, activate, or replace anything.

Neither monitoring getter may be used for borrowing, liquidation, collateral,
accounting, or any other value-bearing decision. Any proposal to make this
component value-bearing requires a new oracle architecture and security review.
