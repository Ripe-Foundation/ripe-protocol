# Advanced Borrowing Mechanics

Ripe Protocol's architecture enables complex borrowing interactions through its multi-collateral system, dynamic rate mechanisms, and integrated yield features. These advanced mechanics demonstrate how the protocol's components work together.

## Multi-Collateral Term Calculation

Ripe's weighted term system calculates borrowing parameters based on the proportional contribution of each collateral asset to total borrowing power.

### Weighted Parameter Mechanics

Unlike protocols with isolated positions, adding even small amounts of low-risk collateral can improve terms across your entire position:

**Example Portfolio Transformation**:
```
Before: 
- 10 ETH ($20,000) at 5% APR, 80% LTV
- Maximum borrow: $16,000
- Weighted rate: 5.0%

Add $2,000 USDC:
- 10 ETH + 2,000 USDC ($22,000 total)
- New maximum borrow: $17,800
- New weighted rate: 4.64%
- Rate improvement: 0.36% on entire position!
```

### Asset Parameter Categories

**High-LTV Assets** (90%+ LTV, 3-4% rates)
- USDC, USDT - Stable value characteristics
- DAI/USDS - Decentralized stablecoins

**Standard Collateral** (70-85% LTV, 4-6% rates)
- WETH, WBTC - Established cryptocurrencies
- stETH, rETH - Liquid staking derivatives

**Conservative Parameters** (40-70% LTV, 8-15% rates)
- Mid-cap tokens - Higher volatility assets
- LP tokens - Liquidity provider positions

### Parameter Calculation Examples

**Example Portfolio Composition**
```
80% Blue-chip collateral (WETH, WBTC)
20% Stablecoin collateral (USDC)
Resulting weighted rate: Closer to blue-chip rates with improved LTV
```

These examples demonstrate how the weighted average calculation produces different effective rates based on portfolio composition.

## Yield-Bearing Collateral Mechanics

### sGREEN Integration

The protocol enables automatic conversion of borrowed GREEN to sGREEN (savings GREEN):

**Mechanism**:
- Borrowed GREEN can be wrapped into sGREEN in the same transaction
- sGREEN accrues yield while the underlying debt remains denominated in GREEN
- The yield differential between sGREEN and borrowing rates varies with market conditions
- This integration creates economic incentives that help maintain protocol stability

**Technical Flow**:
```
1. Borrow GREEN from CreditEngine
2. Automatic conversion to sGREEN if selected
3. sGREEN balance grows over time
4. Debt remains in GREEN terms
```

### Stability Pool Integration

Borrowed funds can flow directly into stability pools through protocol mechanisms:

**Technical Components**:
- GREEN converts to sGREEN (requirement for stability pools)
- Stability pool deposits earn liquidation premiums
- RIPE protocol rewards accrue to depositors
- Original loan terms remain unchanged

**Yield Sources in Stability Pools**:
- Base sGREEN appreciation
- Liquidation premium distribution
- RIPE token rewards
- All yields compound within the pool

### Rate Update Asymmetry

The protocol's rate update mechanism creates temporal differences:

**Update Mechanics**:
- Pool stress increases both borrowing rates and sGREEN yields
- Existing positions maintain historical rates until interaction
- New deposits receive current market rates immediately
- This temporal difference is a designed feature of the system

The mechanism ensures market forces naturally work to restore equilibrium.

## Keeper Interaction Mechanics

The protocol's keeper system enables permissionless rate updates, creating interesting dynamics for position management.

### Rate Update Economics

Keeper incentives align with protocol health:
- Anyone can trigger rate updates for any position
- Updates benefit both the position owner and protocol accuracy
- MEV opportunities encourage timely updates
- No permission required ensures market efficiency

This decentralized approach maintains accurate system-wide rates without central coordination.

### Rate Persistence Mechanism

The protocol's interaction-based update system:

**Technical Implementation**:
- Interest rates snapshot at last interaction
- Rates persist until next user-initiated action
- No automatic rate updates forced on users
- Different positions may have different effective rates

This design reduces gas costs and provides rate predictability for existing positions.

## Liquidation Mechanics

### Health Factor Calculation

The protocol uses health factor to determine position safety:

```
Health Factor = (Collateral Value × Liquidation Threshold) / Total Debt
```

**Health Factor Ranges**:
- Above 1.0: Position is safe from liquidation
- Below 1.0: Position eligible for liquidation
- Near 1.0: Increased monitoring recommended

### Liquidation Priority

When liquidation occurs, the protocol selects collateral based on:
- Asset liquidity characteristics
- Minimization of user loss
- Gas efficiency considerations
- Market impact assessment

## Economic Mechanics

### Borrowing vs Selling Economics

The protocol enables liquidity access without asset disposal:

**Key Differences**:
- Borrowing maintains asset ownership and upside exposure
- No realization event occurs with borrowing
- Interest costs vs potential appreciation
- Collateral remains productive in yield-bearing vaults

### Cost Structure Analysis

**Total Borrowing Cost Components**:
- Base interest rate (asset-weighted)
- Origination fee (one-time)
- Compound interest effect
- Gas costs for transactions

## Redemption and Liquidation Thresholds

### Redemption Mechanism

Before liquidation, positions enter redemption eligibility:

**Redemption Threshold**: Typically 105-110% collateralization
- GREEN holders can redeem against underwater positions
- Provides warning before liquidation
- Helps maintain GREEN peg stability

### Critical Thresholds

**Position States**:
- Healthy: Above all thresholds
- Redemption Zone: Below redemption threshold
- Liquidation Zone: Below liquidation threshold
- Insolvent: Debt exceeds collateral value

## Protocol Interaction Examples

### Multi-Collateral Position Mechanics

When multiple assets back a single loan:
- Each asset contributes proportionally to borrowing power
- Weighted average parameters determine position terms
- Liquidation selects optimal assets to minimize loss
- Addition or removal of assets recalculates all parameters

### Yield-Bearing Position Dynamics

Positions with yield-bearing collateral exhibit:
- Collateral value growth over time
- Improving health factor without intervention
- Compound effects from both yield and appreciation
- Automatic capture of all underlying yields

### Recursive Borrowing Mechanics

The protocol supports recursive positions where:
- Borrowed GREEN purchases additional collateral
- New collateral increases borrowing capacity
- Process repeats until desired leverage achieved
- Each iteration compounds both risk and reward

## Risk Parameters and Calculations

### Position Risk Metrics

The protocol calculates various risk indicators:

**Concentration Risk**: Single asset exposure relative to total collateral
**Volatility Risk**: Weighted volatility based on asset composition
**Liquidity Risk**: Ability to liquidate without significant slippage
**Correlation Risk**: Similar price movements across collateral assets

### Dynamic Risk Assessment

Risk parameters adjust based on:
- Market volatility indicators
- Liquidity depth changes
- Protocol utilization rates
- Historical liquidation data

### System Risk Boundaries

The protocol enforces limits to maintain stability:
- Maximum debt per collateral type
- Aggregate exposure limits
- Minimum position sizes
- Rate adjustment caps

---

These advanced mechanics demonstrate the technical depth of Ripe Protocol's borrowing system, showing how multiple components interact to create a flexible yet secure lending environment.