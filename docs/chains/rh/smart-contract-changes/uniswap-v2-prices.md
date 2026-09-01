# UniswapV2Prices: monitoring-only pool observer

## Scope

[`UniswapV2Prices.vy`](../../../../contracts/priceSources/UniswapV2Prices.vy)
is deliberately not an oracle. It combines two monitoring surfaces:

- constructor-bound convenience views for one canonical 18-decimal RIPE/WETH
  Uniswap V2 pair; and
- a stateless `getPoolMonitoringPrice(asset, pool, partner)` view for direct
  offchain observation of caller-supplied Uniswap V2-shaped tuples.

The generic view does not admit a pool, create a feed, or persist configuration.
The caller remains responsible for qualifying the pool's factory provenance,
token identities and behavior, liquidity, manipulation exposure, and the
partner asset's PriceDesk route.

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

Five non-interface behaviors remain:

- `isMonitoringOnly()` identifies the contract's permanent role;
- `getPoolMonitoringPrice(asset, pool, partner)` returns the asset's current
  USD spot price, normalized to 18 decimals, for a caller-supplied tuple;
- `getRipePoolState()` returns RIPE reserve, WETH reserve, and pair timestamp;
- `getRipeWethMonitoringPrice()` returns the current spot WETH-per-RIPE ratio;
- `getRipeUsdMonitoringPrice()` combines that ratio with PriceDesk's current
  WETH/USD observation for direct monitoring.

The constructor binds RipeHq, the canonical pair, RIPE, and WETH as immutables.
It requires that pair to contain exactly RIPE and WETH, in either order, and
requires both tokens to use 18 decimals. Those requirements protect only the
three canonical convenience views; they do not qualify generic tuples.

For the generic USD view, PriceDesk is resolved dynamically through RipeHq ID
7 and queried for the supplied partner, not the asset. A registry rotation
therefore does not stale the route. Supported token decimals are 0 through 18,
and the result is normalized to 18 decimals.

## Failure semantics and trust boundary

The generic view returns zero for decoded semantic invalidity: zero or
identical input identities, pool-token mismatch, reserves or timestamps beyond
Uniswap V2 bounds, zero reserves, decimals above 18, a missing PriceDesk,
missing or zero partner pricing, ratio truncation, or unsafe final
multiplication.

Typed external-call failures are different. A non-contract or non-pair pool,
a missing or malformed token `decimals()` response, an invalid RipeHq, or a
short or reverting pool or PriceDesk response reverts the view. Overlong typed
responses use their ABI prefix. Consumers must handle those reverts explicitly;
the API does not promise zero for every dependency failure.

No factory check or liquidity floor is enforced onchain. A contract that
reports matching `token0`, `token1`, and reserves can satisfy the structural
checks without being a canonical Uniswap deployment. Even a genuine pool's
spot reserves are immediately manipulable. These are deliberate monitoring
limitations, not oracle security properties.

## Removed oracle-like machinery

The monitoring revision removes all snapshot storage, ring-buffer averaging,
staleness policy, upside throttling, pending configuration, local governance,
action timelocks, pause state, and priced-asset state. Generic observation is a
pure caller-supplied view rather than stored feed configuration. Historical
sampling, aggregation, tuple qualification, alerting, and manipulation
detection belong in the offchain monitoring system.

This removal is intentional. Snapshot and throttling machinery made a
manipulable spot observer resemble a collateral-grade oracle without providing
the security properties of one.

## Verification

[`test_minimal_prices.py`](../../../../tests/priceSources/uniswap/test_minimal_prices.py)
covers the canonical and generic surfaces, both token orderings, multiple
independent tuples, partner-specific PriceDesk routing, 0/6/8/18-decimal
normalization, asymmetric identity mismatches, reserve and timestamp bounds,
zero reserves, missing prices, unsupported decimals, ratio truncation, unsafe
multiplication, live reserve changes, and every inert PriceSource entrypoint.
It also locks the typed-call behavior for EOAs, non-pair contracts, invalid
RipeHq identities, and short, overlong, or reverting pair and PriceDesk
responses. The ABI-export test requires the generic selector explicitly.

The current runtime template is 4,200 bytes. A constructor-bound test
deployment is 4,360 bytes, leaving 20,216 bytes below the 24,576-byte EIP-170
ceiling. Template size is not a substitute for deployed runtime size when
immutables are present.

## Deployment and readiness boundary

The currently observed live Robinhood instance predates the generic ABI and
does not expose `getPoolMonitoringPrice`. It cannot be changed in place.
Both the historical `0008_UniswapV2Prices.py` module and the pending
source-driven department-redeployment migration compile the current contract
source when executed. Consequently, a future authorized execution would deploy
the new runtime even without a migration-logic change.

This source and ABI candidate does not authorize migration execution, a new
deployment, replacement, registration, configuration, or activation. Any such
phase must separately bind and review the exact source, compiler output,
constructor inputs, manifest treatment, and operational consumers.

Neither the canonical nor generic monitoring getter may be used for borrowing,
liquidation, collateral, accounting, or any other value-bearing decision. Any
proposal to make this component value-bearing requires a new oracle
architecture, risk decision, and security review.
