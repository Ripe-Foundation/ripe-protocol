# UniswapV2Prices: non-admitted price-source candidate

## Scope

[`UniswapV2Prices.vy`](../../../../contracts/priceSources/UniswapV2Prices.vy)
is a small Uniswap V2-style RIPE price-source candidate. It replaces the
deleted `RobinhoodUniswapV2RipePrices` research prototype; the two designs must
not coexist or be treated as alternative deployment choices.

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
pair that does not contain RIPE. Protocol-facing price reads fail closed before
the first snapshot and after all snapshots become stale.

## Verification

[`test_minimal_prices.py`](../../../../tests/priceSources/uniswap/test_minimal_prices.py)
contains 75 collected regression cases covering token order, decimal combinations, reserve
and quote ratios, zero and malformed inputs, arithmetic overflow, bootstrap,
snapshots, staleness, ring-buffer rollover and shrinkage, upside throttling,
downside behavior, governance, events, standard snapshot-source configuration
confirmation and cancellation, superseded and expired timelocks, permissions,
recursive quote calls, and pause behavior. The unresolved repeated
spot-manipulation case is retained as a
strict expected failure pending the owner architecture decision. The repository
ABI is exported as
[`UniswapV2Prices.json`](../../../../scripts/abis/UniswapV2Prices.json).

Current compiler facts with Vyper `0.4.3+commit.bff19ea2`:

| Property | Value |
| --- | --- |
| Source SHA-256 | `5f783d681b919a1f42b266ac3bef881c90c0083b389b941652cdeebaaa2a5699` |
| Source bytes | 15,636 |
| Runtime-template bytes | 13,669 |
| Runtime-template EIP-170 headroom | 10,907 bytes |
| Runtime-template SHA-256 | `2dc8fa0469958bc4d829be6b10ede1210152dacfa3e2c95a847250cb286677d8` |
| Constructor-bound immutable bytes | 256 |
| Deployed-runtime bytes | 13,925 |
| Deployed-runtime EIP-170 headroom | 10,651 bytes |
| Canonical ABI SHA-256 | `e38fc81f7af8c64219e6b7484d458a68756fd8cb771ca434509b7fbe00fc423b` |
| Committed ABI file SHA-256 | `1171f61c3eeed8930165c6851e64985da75e1352d31bc1862dceffa5813afe23` |

## Readiness boundary

This is not a production-readiness or deployment record. The current price is
a spot reserve ratio, not a time-weighted oracle. The contract does not prove
that the immutable pair came from an approved factory, enforce minimum
liquidity, or bind a Robinhood pair address. Repeated permissioned protocol
snapshot triggers can still persist a manipulated spot price; the regression
suite records that unresolved behavior as a strict expected failure.

Before PriceDesk admission, security review must resolve those behaviors and
bind the pair, quote asset/feed, liquidity and manipulation limits, oracle
architecture, parameters, ownership, deployment, and monitoring. Deployment
must also call `setActionTimeLockAfterSetup()` before any configuration or
admission step. No migration,
PriceDesk registration, configuration, deployment, or activation is included
in this change.
