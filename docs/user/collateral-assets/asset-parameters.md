# Asset Parameters

Ripe Protocol assets operate according to risk-calibrated parameters that balance capital efficiency with protocol safety. These parameters determine borrowing capacity, interest rates, liquidation thresholds, and system behavior.

## Asset Configuration Framework

Each supported asset receives a configuration defining:
- Maximum borrowing capacity (LTV)
- Interest rate parameters
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

### 4. Liquidation Penalty

If liquidation occurs, this fee is applied to incentivize keepers and maintain protocol health.

**Typical Penalties:**
- Stablecoins: 5%
- Major cryptocurrencies: 10%
- Volatile assets: 15%

The penalty deducts from collateral value, not as additional debt.

### 5. Deposit Limits

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
Asset    Value      LTV    Rate   Liq.Threshold   Max Debt    Weight
WETH     $10,000    80%    5.0%   85%            $8,000      57.1%
USDC     $2,500     90%    3.0%   95%            $2,250      16.1%
stETH    $5,000     75%    4.5%   83%            $3,750      26.8%
PEPE     $350       50%    12.0%  65%            $175        1.2%
-------------------------------------------------------------------
Total    $17,850                                  $14,175     100%

**Weighted Calculations:**
Weighted LTV = 79.4%
  = (80% × 57.1%) + (90% × 16.1%) + (75% × 26.8%) + (50% × 1.2%)

Weighted Interest Rate = 4.76%
  = (5.0% × 57.1%) + (3.0% × 16.1%) + (4.5% × 26.8%) + (12.0% × 1.2%)

Weighted Liquidation Threshold = 84.8%
  = (85% × 57.1%) + (95% × 16.1%) + (83% × 26.8%) + (65% × 1.2%)

### Result Interpretation

The aggregate position characteristics:
- Maximum borrowing capacity: $14,175 (79.4% of $17,850)
- Blended interest rate: 4.76% on borrowed GREEN
- Liquidation threshold: 84.8% of collateral value

High-value, low-risk assets (WETH, USDC) dominate parameters, while volatile assets (PEPE) have minimal impact due to small borrowing power contribution.

## The Vault System

Ripe Protocol stores assets in specialized vaults optimized for different token types and use cases.

### Vault Organization

Each supported asset can have one or more vaults:
- **Primary Vault**: Default destination for deposits
- **Special Purpose Vaults**: For specific strategies or features
- **Vault IDs**: Unique identifiers for each vault

The Teller automatically routes deposits to appropriate vaults based on:
1. Asset type and characteristics
2. Available vault capacity
3. Specified preferences (if any)

### Types of Vaults

#### Simple ERC-20 Vaults
**For**: Standard tokens (WETH, USDC, most assets)
**Mechanics**:
- Direct balance tracking (1 token = 1 balance unit)
- Deposited amounts match withdrawal availability
- No complexity or conversions
- Lowest gas costs

**Example Assets**: WETH, WBTC, USDC, LINK, UNI

#### Rebase/Yield Vaults  
**For**: Tokens that change balance or earn yield
**Mechanics**:
- Share-based accounting system
- Shares represent percentage ownership of vault
- Captures all yields, rebases, and rewards
- Balance grows automatically

**Example Assets**: stETH, aTokens, cTokens, yield-bearing stablecoins

**Share Mechanics Example**:
Deposit: 100 stETH when vault contains 1,000 stETH
Receive: 10% of vault shares
Vault growth: 1,100 stETH from staking rewards
Withdrawal availability: 110 stETH (10% share)
```

#### Stability Pool (Special Vault)
**For**: [sGREEN](../sgreen.md) (Savings GREEN) only
**Purpose**: Backstop for [liquidations](../liquidations/stability-pool-mechanics.md)
**Special Features**:
- Earns liquidation premiums
- First line of defense for bad debt
- Higher risk but higher rewards
- Separate documentation section

**Unique Mechanics**:
- Deposits might be used for liquidations
- Receive discounted collateral in return
- RIPE rewards for participation

#### Governance Vault
**For**: RIPE token only
**Purpose**: Voting power and enhanced rewards
**Special Features**:
- Time-locked deposits (3-24 months)
- Voting power based on lock duration
- Boosted rewards for longer locks
- Early exit penalties

**Lock Multipliers**:
3 months: 1.0x voting power
6 months: 1.5x voting power
12 months: 2.0x voting power
24 months: 3.0x voting power

### Asset-to-Vault Routing

#### Automatic Routing

Deposits without vault specification:
1. System checks vault support for asset
2. Selects primary vault (typically Simple ERC-20)
3. Routes deposit automatically
4. Point accumulation begins immediately

#### Manual Vault Selection

Vault ID specification enables:
- Secondary vault access
- Specialized vault utilization
- Custom routing preferences

**Specification scenarios**:
- Stability pool deposits
- Specialized yield vault usage
- Non-primary vault targeting

### Points and Rewards Accumulation

Deposits accumulate points for RIPE reward conversion:

#### Point Mechanics
Per-block accumulation includes:
1. **Balance Points**: Based on token amount
2. **USD Value Points**: Based on dollar value
3. **Multipliers Applied**: Based on asset type
4. **Points Accumulated**: Added to total balance

#### Point Allocation by Asset Type
Different assets earn different point rates:

**Stablecoin Deposits**:
- Lower volatility = lower point rate
- Consistent value tracking
- Suitable for conservative positions

**Blue-chip Crypto**:
- Moderate point rates
- Balance of risk and reward
- Common deposit choice

**Volatile/New Assets**:
- Higher point rates
- Compensates for elevated risk
- Significant farming potential

**Governance Stakes**:
- Highest point multipliers
- Rewards long-term alignment
- Boosts based on lock time

### Asset Whitelisting and Restrictions

Some assets have special requirements:

#### Whitelisted Assets
Certain assets require approval to deposit:
- **Tokenized Securities**: KYC/AML required
- **Institutional Assets**: Accredited investor only
- **Geographic Restrictions**: Compliance with local laws
- **New/Experimental Assets**: Gradual rollout

**Whitelist Process**:
1. Asset implements whitelist contract
2. Address requires approval
3. Approval process varies per asset
4. Approved addresses deposit normally

#### Whitelist Verification
Restricted assets implement on-chain whitelist checks that verify approval status before accepting deposits. The protocol enforces these restrictions at the contract level, ensuring compliance throughout the asset lifecycle.

### Deposit Limit Framework

Protocol growth protection through limits:

#### Limit Rationale
- **Risk Management**: Gradual exposure to new assets
- **Liquidity Management**: Maintain orderly liquidations
- **Technical Scaling**: Controlled growth phases
- **Community Protection**: Prevent manipulation

#### Types of Limits

**Per-User Limits**:
Example: Maximum $100,000 PEPE per address
- Prevents concentration risk
- Other assets remain available
- Governance adjusts over time

**Global Limits**:
Example: Maximum $10M PEPE protocol-wide
- Aggregate across all positions
- Available capacity basis
- Governance parameter

**Minimum Balances**:
Example: Minimum 100 USDC deposit
- Prevents dust accumulation
- Maintains gas efficiency
- Initial deposit requirement

### Vault Security and Risks

#### Security Features
- **Immutable Logic**: Core vault code cannot change
- **Access Controls**: Only authorized contracts can move funds
- **Withdrawal Protection**: Restricted to depositor address
- **Audit History**: All vaults professionally audited

#### Risk Considerations
- **Smart Contract Risk**: Bugs could affect funds
- **Integration Risk**: Issues with yield sources
- **Upgrade Risk**: New vaults need time to prove safety
- **Composability Risk**: Interactions between systems

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