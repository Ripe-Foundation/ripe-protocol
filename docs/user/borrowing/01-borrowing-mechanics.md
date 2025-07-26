# Borrowing Mechanics

Borrowing in Ripe Protocol involves minting [GREEN stablecoins](green.md) against [deposited collateral](collateral-assets/deposit-withdrawal-mechanics.md). The protocol calculates borrowing capacity based on collateral values and parameters, with multiple safety mechanisms throughout the process.

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

With multiple collateral types, your borrowing terms (interest rate, liquidation threshold, etc.) are weighted averages based on each asset's contribution to your total borrowing power. See [Understanding Debt](02-understanding-debt.md#weighted-debt-terms) for detailed calculations.

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

Your interest rate is based on:
- Asset-specific base rates for each collateral type
- Dynamic adjustments for market conditions
- GREEN pool imbalance multipliers (if applicable)

With multiple collateral types, you pay a weighted average rate. Higher-risk assets have higher rates, but their impact is proportional to their contribution to your borrowing power.

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

## Borrowing Limits

Ripe Protocol implements multiple types of limits to ensure system stability and gradual growth. These include per-user limits, global protocol caps, and time-based interval restrictions.

For complete details about all limit types, how they interact, and strategies for working within them, see [Borrowing Limits](04-borrowing-limits.md).

## Economic Use Cases

### Liquidity Without Selling
The protocol enables capital access while maintaining asset exposure, avoiding taxable disposition events and preserving upside potential.

### Yield Arbitrage
When yield-bearing collateral rates exceed borrowing costs, the protocol design creates natural arbitrage opportunities that benefit both borrowers and the ecosystem.

### Rapid Capital Access
The permissionless nature and automated risk assessment enable immediate liquidity access based purely on collateral value, eliminating traditional lending friction.

These mechanisms demonstrate how Ripe's borrowing system creates value through efficient capital allocation and innovative financial primitives.

The borrowing mechanics demonstrate how Ripe Protocol creates efficient capital markets through automated risk assessment and dynamic parameter adjustment.