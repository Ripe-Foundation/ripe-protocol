# Borrowing Mechanics

Borrowing in Ripe Protocol involves minting [GREEN stablecoins](../green.md) against [deposited collateral](../collateral-assets/deposit-withdrawal-mechanics.md). The protocol calculates borrowing capacity based on collateral values and parameters, with multiple safety mechanisms throughout the process.

## Borrowing Power Calculation

Borrowing power represents the maximum GREEN mintable based on deposited collateral values and their respective loan-to-value parameters.

### Core Formula

Total borrowing power equals the sum of each asset's value multiplied by its loan-to-value ratio.

The protocol:
1. Determines current USD values through oracle price feeds
2. Applies asset-specific loan-to-value ratios
3. Aggregates all contributions for total capacity

### Calculation Mechanics

With multiple collateral types, each asset contributes based on:
- Market value at current oracle prices
- Asset-specific LTV percentage
- Aggregated into unified borrowing capacity

Higher LTV assets (like stablecoins at 90%) provide more borrowing power per dollar than lower LTV assets (like volatile tokens at 50%).

### Parameter Blending

The protocol calculates weighted average terms based on each asset's proportional contribution to borrowing power.

#### Weighting Mechanism

Parameters blend according to borrowing power contribution:
- Assets with higher LTV ratios exert greater influence
- Interest rates combine proportionally
- Risk metrics unify across the portfolio

#### System Properties

The weighted average mechanism ensures:
- Proportional parameter influence based on borrowing contribution
- Risk distribution across multiple asset types
- Dynamic recalculation when portfolio composition changes
- Mathematical precision in term determination

## The Borrowing Process

### Step 1: Pre-Borrow Validation

The protocol performs several checks before allowing borrowing:

1. **Sufficient Collateral**: Requested amount ≤ borrowing power
2. **Minimum Debt**: Loans must exceed minimum threshold
3. **User Limits**: Within per-user debt ceiling
4. **Global Limits**: Protocol hasn't reached total debt cap
5. **Interval Limits**: Current period's borrowing capacity available

#### Minimum Debt Rationale

The protocol enforces minimum debt thresholds for:

**Economic Viability**:
- Transaction costs must justify position maintenance
- Liquidation profitability ensures keeper participation
- Gas efficiency across all operations

**System Efficiency**:
- Prevents accumulation of dust positions
- Reduces computational overhead
- Maintains liquidation economics

These thresholds ensure all positions remain economically viable for both users and protocol maintainers.

### Step 2: Interest Rate Determination

Your interest rate combines:

**Base Rate Components**:
- Asset-specific rates (weighted by borrowing power)
- Protocol base rate
- Market conditions

**Dynamic Adjustments**:
- GREEN pool health and balance ratios
- Time spent in imbalanced state
- Automatic rate multipliers during stress

**Example Calculation**:
```
WETH portion: $16,000 at 5% = $800/year
USDC portion: $4,500 at 3% = $135/year  
PEPE portion: $500 at 15% = $75/year
Weighted Rate: $1,010/$21,000 = 4.8% APR
```

### Step 3: Origination Fee (Daowry)

The protocol charges a one-time origination fee on new borrows:
- Typically 0.5% of borrowed amount
- Deducted from minted GREEN
- Distributed to sGREEN holders
- Creates immediate value for savers

**Fee Structure**:
- Borrower requests: 10,000 GREEN
- Daowry (0.5%): 50 GREEN
- Borrower receives: 9,950 GREEN
- Debt recorded: 10,000 GREEN

### Step 4: GREEN Distribution Options

The protocol offers multiple distribution methods for borrowed GREEN:

#### 1. Direct Distribution
Borrowers receive standard GREEN tokens directly.

#### 2. Automatic sGREEN Conversion
Borrowed GREEN can be automatically wrapped into sGREEN:

**Economic Benefits:**
- Immediate yield accrual on borrowed funds
- No separate conversion transaction
- Yield may exceed borrowing costs
- Creates self-sustaining debt positions

This mechanism creates potential positive carry positions where sGREEN yield may exceed borrowing costs, depending on market conditions and protocol revenue generation.

#### 3. Direct Stability Pool Participation
Borrowed funds can flow directly into stability pools:
- Protocol converts GREEN → sGREEN → Stability Pool atomically
- Immediate participation in liquidation premiums
- Compound sGREEN yield with stability rewards
- Strengthens protocol resilience
- Potential access to discounted collateral

The protocol automatically handles necessary conversions for stability pool participation within single transactions.

## Interest Rate Updates and Management

### When Your Rate Updates

Your interest rate is recalculated in several scenarios:

1. **User-Initiated Actions**:
   - Borrowing additional GREEN
   - Repaying any amount (partial or full)
   - Adding or removing collateral
   - Changing collateral composition

2. **Keeper Updates**:
   - Anyone can call `updateDebtForUser` to refresh rates
   - Triggered after market movements or pool health changes
   - Updates position to current dynamic rates
   - Permissionless operation

3. **Automatic Triggers**:
   - During liquidation processes
   - When collateral is redeemed
   - As part of certain protocol operations

### Understanding Rate Refreshes

**Rate Update Design**:
- Gas optimization through on-demand updates
- User-initiated interactions determine timing
- Predictable rate changes at known points

**Rate Update Mechanics**:
- Rate decreases benefit from immediate updates
- Rate increases apply only on interaction
- Pool health metrics indicate rate direction

**Rate Update Timing**:
Rate changes apply at specific interaction points. Positions maintain existing rates until borrower actions or keeper updates trigger recalculation. This design optimizes gas costs while ensuring eventual rate convergence.

### Keeper Economics

Keepers update rates due to:

1. **MEV Opportunities**: Rate updates before liquidations
2. **Protocol Accuracy**: System-wide rate synchronization
3. **Automation Services**: Dedicated keeper infrastructure
4. **Economic Incentives**: Gas cost reimbursement mechanisms

This decentralized approach ensures rates stay current without centralized intervention.

## Advanced Interest Mechanics

### Compound Interest Calculation

The protocol calculates interest continuously using block-based compounding:

- Interest compounds each block (approximately every few seconds)
- Continuous compounding results in slightly higher effective rates
- A 10% nominal rate yields approximately 10.5% effective annual rate
- This mechanism is standard across DeFi protocols

### Dynamic Rate Integration

When rates change due to pool health:

1. **Existing Interest**: Locked at previous rate
2. **New Interest**: Accrues at new rate
3. **Blended Cost**: Weighted average over time

This mechanism prevents retroactive rate changes while enabling dynamic market response.

For complete details about debt management, see [Understanding Your Debt](understanding-debt.md).

## Special Collateral Types

### NFT Collateral Support

Ripe Protocol includes infrastructure for NFT collateral, enabling:

- **Verified Collections**: Support for established NFT projects
- **Fractional Ownership**: Tokenized NFT shares as collateral
- **Floor Price Valuation**: Conservative pricing mechanisms
- **Specialized Parameters**: NFT-specific risk metrics

**Note**: NFT collateral availability depends on governance approval and oracle support.

### Yield-Bearing Collateral

Deposit assets that earn yield while collateralizing loans:

- **Liquid Staking Tokens**: stETH, rETH, etc.
- **LP Tokens**: From approved DEX pools
- **Vault Tokens**: From integrated yield protocols

Yield-bearing collateral continues accruing value while securing debt positions.

## Borrowing Limits

Ripe Protocol implements multiple types of limits to ensure system stability and gradual growth. These include per-user limits, global protocol caps, and time-based interval restrictions.

For complete details about all limit types, how they interact, and strategies for working within them, see [Borrowing Limits](borrowing-limits.md).

## Economic Use Cases

### Liquidity Without Selling
The protocol enables capital access while maintaining asset exposure, avoiding taxable disposition events and preserving upside potential.

### Yield Arbitrage
When yield-bearing collateral rates exceed borrowing costs, the protocol design creates natural arbitrage opportunities that benefit both borrowers and the ecosystem.

### Rapid Capital Access
The permissionless nature and automated risk assessment enable immediate liquidity access based purely on collateral value, eliminating traditional lending friction.

These mechanisms demonstrate how Ripe's borrowing system creates value through efficient capital allocation and innovative financial primitives.

The borrowing mechanics demonstrate how Ripe Protocol creates efficient capital markets through automated risk assessment and dynamic parameter adjustment.