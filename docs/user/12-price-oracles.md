# Price Oracles: The Truth About Your Money

One bad price feed can destroy a protocol. Positions liquidated on fake spikes. Exploits draining millions. Users losing everything to a malicious update.

Ripe doesn't rely on any single source. We check Chainlink, Pyth, Stork, and Curve in priority order — taking the first valid price. If one fails, we instantly fall back to the next.

Your collateral value comes from the most reliable source available at that moment.

## Why Pricing Matters in Ripe

Every critical protocol operation depends on accurate pricing:

- **Borrowing Power**: Your collateral value determines how much GREEN you can borrow
- **Liquidation Safety**: Price movements trigger liquidations when positions become risky
- **Redemption Values**: Direct redemptions exchange GREEN for exactly $1 of collateral
- **Stability Pool Profits**: Liquidation discounts are calculated from current market prices
- **Interest Rates**: Dynamic rates respond to GREEN's market price

With so much at stake, we've built a pricing system that's both robust and transparent.

## The Multi-Oracle Advantage

Instead of relying on a single price feed, Ripe aggregates multiple independent oracle providers:

```
Asset Price Request Flow:

Your Asset (e.g., ETH)
    ↓
Price Desk (Aggregator)
    ↓
1. Check Priority Oracles (Chainlink first)
2. If no price, check secondary oracles
3. Return first valid price found
    ↓
Accurate USD Value
```

This design provides several benefits:

- **No Single Point of Failure**: If Chainlink goes down, Pyth can provide prices
- **Asset Flexibility**: Different oracles support different assets
- **Cost Optimization**: Use expensive oracles only for critical assets
- **Future-Proof**: New oracle providers can be added seamlessly

## Our Oracle Providers

### 1. Chainlink (Primary)

The industry standard for decentralized price feeds:

- **Coverage**: Major crypto assets (ETH, BTC, stablecoins, blue chips)
- **Reliability**: Battle-tested across DeFi with billions secured
- **Update Frequency**: Varies by asset based on volatility
- **Trust Model**: Decentralized node operators with reputation

Chainlink serves as our primary oracle for most mainstream assets due to its proven track record and wide deployment.

### 2. Curve Pools (Specialized)

Direct pricing from the largest stablecoin liquidity pools:

- **Coverage**: Stablecoins, Curve LP tokens, GREEN pairs
- **Reliability**: Based on actual tradeable liquidity
- **Special Feature**: Monitors GREEN's peg in real-time
- **Trust Model**: On-chain AMM state, manipulation-resistant

**Critical for GREEN Stability**: The Curve price feed maintains the "Green Reference Pool" data that directly impacts [dynamic interest rates](03-borrowing.md#dynamic-interest-rates-emergency-mechanism-only). By taking weighted snapshots of the GREEN/USDC pool balance over time, the protocol can detect when GREEN trades below peg and automatically adjust borrowing costs to restore balance. This creates a powerful feedback loop — when GREEN weakens, higher rates incentivize borrowers to buy GREEN for repayment, strengthening the peg.

### 3. Pyth Network (High-Frequency)

Sub-second price updates from institutional providers:

- **Coverage**: Wide range including stocks, forex, commodities, and crypto
- **Reliability**: Professional market makers provide data
- **Update Frequency**: Can update every slot if needed
- **Trust Model**: Aggregated from multiple institutional sources

Useful for assets requiring frequent updates or those not covered by Chainlink.

### 4. Stork Network (Emerging)

Next-generation oracle with unique features:

- **Coverage**: Growing selection of DeFi assets
- **Reliability**: Novel cryptographic attestation model
- **Update Frequency**: On-demand with nanosecond precision
- **Trust Model**: Decentralized publishers with stakes

Provides additional redundancy and supports newer assets.

### 5. Blue Chip Yield Prices (Specialized)

Custom pricing for yield-bearing tokens from major protocols:

- **Coverage**: aTokens (Aave), cTokens (Compound), Morpho positions, Euler, etc.
- **Reliability**: Direct integration with protocol contracts
- **Special Feature**: Handles rebasing and yield accrual correctly
- **Trust Model**: Based on underlying protocol's accounting

**Two-Layer Pricing**: This oracle combines real-time underlying asset prices (from Chainlink or other primary oracles) with weighted snapshots of the share price/exchange rate. For example, to price a Morpho USDC position:
- **Underlying USDC price**: Fetched in real-time from Chainlink ($1.00)
- **Morpho share price**: Weighted average over time (e.g., 1.05 USDC per share)
- **Final position value**: $1.00 × 1.05 = $1.05 per share

**Manipulation Protection**: Only the exchange rate uses weighted snapshots — the underlying asset price remains current. This prevents attackers from manipulating the yield token's exchange rate through flash loans or temporary spikes, while ensuring the collateral responds immediately to market movements in the underlying asset. The snapshots also include upside deviation throttling for the exchange rate, gradually incorporating sudden appreciation rather than accepting it immediately.

## Staleness Protection

Stale prices are dangerous. Here's how we prevent them:

### Global Staleness Threshold
- Default: 3600 seconds (1 hour) for most assets
- Stricter limits for volatile assets
- Relaxed for stable assets like USDC

### Per-Oracle Configuration
Each oracle can have custom staleness limits:
- Chainlink: Uses round timestamp
- Pyth/Stork: Uses publish timestamp  
- Curve: Always current (reads directly from pool state)
- Blue Chip: Snapshot-based with minimum delays

### What Happens When Prices Go Stale?

1. **Primary Oracle Stale**: System automatically checks secondary oracles
2. **All Oracles Stale**: Operations can be configured to either:
   - Use last known price (for non-critical operations)
   - Revert transaction (for critical operations like liquidations)
3. **No Feed Available**: New assets without feeds cannot be borrowed against

## Price Priority System

Not all oracles are created equal. Our priority system ensures the best price source is used:

```
Priority Order (Configurable):
1. Chainlink (most trusted for major assets)
2. Curve Pools (for stablecoins and LP tokens)
3. Pyth Network (backup for Chainlink assets)
4. Stork Network (additional redundancy)
5. Blue Chip Yield (for yield-bearing tokens)
```

Governance can adjust priorities based on:
- Oracle reliability track record
- Gas costs for updates
- Asset-specific considerations
- Market conditions

## Security Measures

### Time-Locked Changes
- New oracle additions: 24-hour delay
- Oracle priority changes: 12-hour delay  
- Feed updates: 6-hour delay
- Emergency disables: Instant (governance multisig)

### Fail-Safe Mechanisms
- Automatic fallback to secondary oracles
- Pause functionality for compromised feeds
- Fund recovery for stuck update fees
- Governance override capabilities

## Trust Through Verification

Here's what your lending protocol won't tell you: they probably use one oracle. Maybe two if they're fancy.

Ripe connects to four independent price sources with instant fallback. Primary oracle down? We're already using the backup. No delays. No manual intervention. No single point of failure.

This isn't paranoia. It's the difference between a protocol that survives oracle outages and one that doesn't.

When your primary oracle fails — and it will — your positions keep getting priced.

That's not a feature. That's survival.

---

*For technical implementation details, see:*
- *[Price Desk Technical Documentation](../technical/registries/PriceDesk.md) - Oracle aggregation system*
- *[Chainlink Prices](../technical/priceSources/ChainlinkPrices.md) - Chainlink integration*
- *[Curve Prices](../technical/priceSources/CurvePrices.md) - AMM-based pricing and GREEN monitoring*
- *[Pyth Prices](../technical/priceSources/PythPrices.md) - High-frequency oracle updates*
- *[Stork Prices](../technical/priceSources/StorkPrices.md) - Decentralized price attestations*
- *[Blue Chip Yield Prices](../technical/priceSources/BlueChipYieldPrices.md) - Yield token valuations*