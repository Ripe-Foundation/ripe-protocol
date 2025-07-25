# Asset Parameters

Ripe Protocol assets operate according to risk-calibrated parameters that balance capital efficiency with protocol safety. These parameters determine borrowing capacity, interest rates, liquidation thresholds, and system behavior.

## Asset Configuration Framework

Each supported asset receives a configuration defining:
- Maximum borrowing capacity (LTV)
- Interest rate parameters
- Redemption thresholds
- Liquidation thresholds
- System behavior rules

Parameters derive from market data analysis, risk assessments, and governance decisions.

## Key Parameters Explained

### 1. Loan-to-Value (LTV) Ratio

The LTV determines borrowing capacity. An 80% LTV enables borrowing up to $80 worth of GREEN per $100 of collateral value.

**Determination factors:**
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

This parameter determines liquidation eligibility. The threshold exceeds LTV to provide a safety buffer.

**Example:**
- LTV: 80%
- Liquidation Threshold: 85%
- Buffer: 5% margin for market movements

This configuration allows borrowing up to 80% while liquidation begins only when debt exceeds 85% of collateral value.

### 4. Redemption Threshold

The redemption threshold activates GREEN redemptions before liquidation becomes possible. This creates a buffer zone for automatic deleveraging.

**Example:**
- LTV: 80%
- Redemption Threshold: 82%
- Liquidation Threshold: 85%

When debt-to-collateral ratio exceeds 82%, GREEN holders can redeem tokens against the position at a 1:1 value exchange, helping positions deleverage before liquidation risk.

### 5. Liquidation Penalty

If liquidation occurs, this fee is applied to incentivize keepers and maintain protocol health.

**Typical Penalties:**
- Stablecoins: 5%
- Major cryptocurrencies: 10%
- Volatile assets: 15%

The penalty deducts from collateral value, not as additional debt.

### 6. Deposit Limits

Risk management implements deposit limits:

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

The protocol employs multiple price sources for manipulation-resistant valuations:

1. **Priority Sources**: Configurable oracle hierarchy (typically Chainlink first)
2. **Backup Oracles**: Pyth Network, Stork, and other price feeds
3. **DEX Integration**: Direct pricing from Curve and other DEXs
4. **Smart Routing**: Takes the first valid price from the priority order

The protocol uses the first available valid price from configured sources without averaging. Priority oracle unavailability triggers automatic fallback to secondary sources. Continuous price updates maintain current market valuations.

### Value Calculation Example

Total collateral value calculation process:

Example deposits:
- 5 WETH at $2,000 each = $10,000
- 2,500 USDC = $2,500
- 2.5 stETH at $2,000 each = $5,000
- 3.5M PEPE at $0.0001 = $350

Total Collateral Value = $17,850

This total value provides the basis for borrowing calculations.

## Working with Multiple Assets

Multiple asset deposits result in weighted average parameters based on each asset's borrowing power contribution.

### Weighted Term Calculation

The protocol weights each parameter by the asset's maximum borrowing power (Value × LTV):

Weight = Asset's Max Borrowing Power / Total Borrowing Power

### Complete Example

**Portfolio example:**
Asset    Value      LTV    Rate   Red.Threshold  Liq.Threshold   Max Debt    Weight
WETH     $10,000    80%    5.0%   82%           85%            $8,000      57.1%
USDC     $2,500     90%    3.0%   92%           95%            $2,250      16.1%
stETH    $5,000     75%    4.5%   80%           83%            $3,750      26.8%
PEPE     $350       50%    12.0%  60%           65%            $175        1.2%
---------------------------------------------------------------------------------
Total    $17,850                                                $14,175     100%

**Weighted Calculations:**
Weighted LTV = 79.4%
  = (80% × 57.1%) + (90% × 16.1%) + (75% × 26.8%) + (50% × 1.2%)

Weighted Interest Rate = 4.76%
  = (5.0% × 57.1%) + (3.0% × 16.1%) + (4.5% × 26.8%) + (12.0% × 1.2%)

Weighted Redemption Threshold = 81.9%
  = (82% × 57.1%) + (92% × 16.1%) + (80% × 26.8%) + (60% × 1.2%)

Weighted Liquidation Threshold = 84.8%
  = (85% × 57.1%) + (95% × 16.1%) + (83% × 26.8%) + (65% × 1.2%)

### Result Interpretation

The aggregate position characteristics:
- Maximum borrowing capacity: $14,175 (79.4% of $17,850)
- Blended interest rate: 4.76% on borrowed GREEN
- Redemption threshold: 81.9% of collateral value
- Liquidation threshold: 84.8% of collateral value

High-value, low-risk assets (WETH, USDC) dominate parameters, while volatile assets (PEPE) have minimal impact due to small borrowing power contribution.

## Parameter Updates

Asset parameters remain adjustable through governance based on:

- Market conditions
- Asset performance
- Risk metrics
- Community decisions

Changes typically include:
- Time delays for major adjustments
- Gradual implementation
- Clear communication
- Grandfathering of existing positions

## Summary

The asset parameter system provides a flexible framework for universal collateral support, balancing system stability with capital efficiency through calibrated risk parameters and automated mechanisms.