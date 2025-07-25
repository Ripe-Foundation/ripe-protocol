# How Assets Work in Ripe

Every asset in Ripe Protocol operates according to carefully calibrated parameters that balance user opportunity with protocol safety. Understanding these parameters helps you make informed decisions about which assets to use and how to optimize your position.

## Asset Configuration Basics

When an asset is added to Ripe, it receives a configuration that determines:
- How much you can borrow against it
- What interest rate you'll pay
- When liquidation might occur
- How it behaves during system events

These aren't arbitrary numbers—they're based on market data, risk analysis, and community governance.

## Key Parameters Explained

### 1. Loan-to-Value (LTV) Ratio

The LTV determines your borrowing power. An 80% LTV means you can borrow up to $80 worth of GREEN for every $100 of collateral.

**How it's determined:**
- **Volatility**: More volatile assets have lower LTVs
- **Liquidity**: Deeper markets support higher LTVs
- **Track Record**: Established assets earn higher ratios
- **Correlation**: Assets that move together might have adjusted LTVs

**Examples:**
- USDC: 90% LTV (stable, liquid)
- WETH: 80% LTV (established, liquid)
- SHIB: 50% LTV (volatile, speculative)

### 2. Interest Rates

Each asset has a base borrowing rate that reflects its risk profile.

**Rate Components:**
- **Base Rate**: Set per asset based on risk
- **Dynamic Adjustment**: Rates can increase during market stress
- **Utilization Impact**: High demand can push rates up

**Typical Ranges:**
- Stablecoins: 2-5% APR
- Blue-chips: 5-10% APR
- Volatile assets: 10-20% APR

### 3. Liquidation Threshold

This critical parameter determines when your position becomes eligible for liquidation. It's always higher than the LTV to provide a safety buffer.

**Example:**
- LTV: 80%
- Liquidation Threshold: 85%
- Buffer: 5% margin for market movements

This means you can borrow up to 80%, but liquidation only starts if your debt exceeds 85% of collateral value.

### 4. Liquidation Penalty

If liquidation occurs, this fee is applied to incentivize liquidators and maintain protocol health.

**Typical Penalties:**
- Stablecoins: 5%
- Major cryptocurrencies: 10%
- Volatile assets: 15%

The penalty comes from your collateral, not additional debt.

### 5. Deposit Limits

To manage risk, assets may have limits:

**Per-User Limits:**
- Prevents concentration risk
- Typically higher for stable assets
- May increase based on history

**Global Limits:**
- Total protocol exposure to an asset
- Prevents systemic risk
- Adjusted by governance

## How Collateral Value is Calculated

### Real-Time Pricing

Ripe uses multiple price sources to ensure accurate, manipulation-resistant valuations:

1. **Priority Sources**: Configurable oracle hierarchy (typically Chainlink first)
2. **Backup Oracles**: Pyth Network, Stork, and other price feeds
3. **DEX Integration**: Direct pricing from Curve and other DEXs
4. **Smart Routing**: Takes the first valid price from the priority order

The protocol doesn't average prices—it uses the first available valid price from its configured sources. If a priority oracle (like Chainlink) has stale or unavailable data, it automatically falls back to the next source. Prices update continuously, ensuring your collateral value reflects current market conditions.

### Value Calculation Example

Let's walk through how your total collateral value is determined:

```
Your Deposits:
- 5 WETH at $2,000 each = $10,000
- 2,500 USDC = $2,500
- 2.5 stETH at $2,000 each = $5,000
- 3.5M PEPE at $0.0001 = $350

Total Collateral Value = $17,850
```

This total value forms the foundation for all borrowing calculations.

## Working with Multiple Assets

When you deposit multiple assets, Ripe automatically calculates weighted averages for all parameters based on each asset's borrowing power contribution.

### How Weighted Terms Are Calculated

The protocol weights each parameter by the asset's maximum borrowing power (Value × LTV):

```
Weight = Asset's Max Borrowing Power / Total Borrowing Power
```

### Complete Example

**Your Portfolio (same assets as above):**
```
Asset    Value      LTV    Rate   Liq.Threshold   Max Debt    Weight
WETH     $10,000    80%    5.0%   85%            $8,000      57.1%
USDC     $2,500     90%    3.0%   95%            $2,250      16.1%
stETH    $5,000     75%    4.5%   83%            $3,750      26.8%
PEPE     $350       50%    12.0%  65%            $175        1.2%
-------------------------------------------------------------------
Total    $17,850                                  $14,175     100%
```

**Weighted Calculations:**
```
Weighted LTV = 79.4%
  = (80% × 57.1%) + (90% × 16.1%) + (75% × 26.8%) + (50% × 1.2%)

Weighted Interest Rate = 4.76%
  = (5.0% × 57.1%) + (3.0% × 16.1%) + (4.5% × 26.8%) + (12.0% × 1.2%)

Weighted Liquidation Threshold = 84.8%
  = (85% × 57.1%) + (95% × 16.1%) + (83% × 26.8%) + (65% × 1.2%)
```

### What This Means

Your overall position:
- Can borrow up to $14,175 (79.4% of $17,850)
- Pays 4.76% interest on borrowed GREEN
- Becomes liquidatable if debt exceeds 84.8% of collateral value

The high-value, low-risk assets (WETH, USDC) dominate your terms, while the risky asset (PEPE) has minimal impact due to its small contribution to borrowing power.

## The Vault System

Assets don't float freely in Ripe—they live in specialized vaults designed for different token types:

### Simple Vaults
For standard ERC-20 tokens:
- Direct 1:1 balance tracking
- Straightforward deposits/withdrawals
- Most common vault type

### Rebase Vaults
For yield-bearing tokens:
- Share-based accounting
- Captures token rebases/yields
- Value grows over time

### Stability Pool
Special vault for protocol protection:
- Accepts stablecoins
- Earns liquidation premiums
- Provides system stability

### Governance Vault
For RIPE token staking:
- Time-locked positions
- Voting power accumulation
- Additional rewards

## Parameter Updates

Asset parameters aren't fixed forever. They can be adjusted through governance based on:

- Market conditions
- Asset performance
- Risk metrics
- Community decisions

Changes typically include:
- Time delays for major adjustments
- Gradual implementation
- Clear communication
- Grandfathering of existing positions

---

Ready to start borrowing? Continue to the [Borrowing](../borrowing/README.md) section →