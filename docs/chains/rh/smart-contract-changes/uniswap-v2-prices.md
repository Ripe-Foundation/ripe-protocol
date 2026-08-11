# UniswapV2Prices: monitoring-only reserve adapter

## Scope

[`UniswapV2Prices.vy`](../../../../contracts/priceSources/UniswapV2Prices.vy)
is a small Uniswap V2-style RIPE monitoring adapter. It replaces the
deleted `RobinhoodUniswapV2RipePrices` research prototype; the two designs must
not coexist or be treated as alternative deployment choices.

The owner has permanently classified this adapter as monitoring-only. Its
standard `PriceSource` methods return no protocol feed: `getPrice` returns zero,
`getPriceAndHasFeed` returns `(0, False)`, and `hasPriceFeed` returns `False`.
Operators read the combined snapshot/spot observation through
`getMonitoringPrice` or the explicit monitoring views. This contract-level
boundary prevents an accidental PriceDesk registration from turning the spot
reserve ratio into collateral or other value-bearing authority.

The contract starts from Ripe's existing `AeroRipePrices` price-source shape
and changes only the venue-specific read path. Its pair interface and reserve
ratio follow Underscore Protocol's `UniswapV2.vy` Lego at commit
`78532a77ebddc176fb2a73899dcc79ba25a8001f`:

- read `token0`, `token1`, and `getReserves` from one immutable pair;
- require the immutable RIPE token to be one of those pair tokens;
- price the other token through PriceDesk;
- normalize both token decimal domains to an 18-decimal RIPE price; and
- retain Aero-style snapshots, downside immediacy, upside throttling, pause,
  governance, and timelocked configuration.

The configuration lifecycle is the one explicit non-venue departure from
`AeroRipePrices`: the otherwise incomplete Aero confirmation and cancellation
stubs are replaced with the existing snapshot-price-source flow copied from
`UndyVaultPrices` and `BlueChipYieldPrices`. A proposal stores the complete
configuration behind a timelock; confirmation revalidates it, confirms the
action, installs it, clears pending state, and attempts a fresh snapshot;
cancellation is governance-only, pause-gated, cancels the action, and clears
pending state. The pending, updated, and cancelled events use the same field
placement as those snapshot price sources.

The adapter supports RIPE in either pair position, rejects zero reserves and
unsupported token decimals above 18, returns zero for an unavailable quote
price or arithmetic overflow, and exposes no feed for assets other than the
configured RIPE token. Construction rejects zero pool/RIPE addresses and a
pair that does not contain RIPE. Monitoring reads return zero before the first
snapshot and after all snapshots become stale. Protocol-facing feed reads
remain disabled regardless of snapshot state.

## Verification

[`test_minimal_prices.py`](../../../../tests/priceSources/uniswap/test_minimal_prices.py)
contains regression cases covering token order, decimal combinations, reserve
and quote ratios, zero and malformed inputs, arithmetic overflow, bootstrap,
snapshots, staleness, ring-buffer rollover and shrinkage, upside throttling,
downside behavior, governance, events, standard snapshot-source configuration
confirmation and cancellation, superseded and expired timelocks, permissions,
recursive quote calls, pause behavior, and the permanent no-feed boundary.
Repeated spot manipulation is retained as a passing characterization of the
accepted monitoring limitation rather than a failing collateral-oracle
invariant. The repository ABI is exported as
[`UniswapV2Prices.json`](../../../../scripts/abis/UniswapV2Prices.json).

Final source, ABI, and constructor-bound deployed-runtime hashes are generated
from the integrated candidate by the late artifact lane. Historical hashes in
earlier review records are not authority for this monitoring-only revision.

## Readiness boundary

This is not a collateral-oracle readiness record. The observed value is a spot
reserve ratio, not a time-weighted oracle. The contract does not prove
that the immutable pair came from an approved factory, enforce minimum
liquidity, or bind a Robinhood pair address. Repeated permissioned protocol
snapshot triggers can still persist a manipulated monitoring value; the
regression suite records that accepted limitation directly.

The adapter must never be admitted as a PriceDesk feed or included in a
value-bearing priority/source path. Deployment tooling may deploy it for direct
monitoring, but must not register it as a PriceDesk source. Any future proposal
to make it value-bearing reopens oracle architecture, factory/pair provenance,
liquidity, manipulation resistance, parameters, ownership, and security review
as a new owner decision.
