# Borrowing Mechanics

Understanding how borrowing works in Ripe Protocol helps you make informed decisions and manage your position effectively. This guide breaks down the entire process from calculating your borrowing power to receiving your GREEN tokens.

## How Borrowing Power is Calculated

Your borrowing power depends on the combined value and parameters of all your deposited collateral.

### The Basic Formula

```
Borrowing Power = Σ(Asset Value × Asset LTV)
```

For each asset you've deposited:
1. Current USD value is determined via oracles
2. Multiplied by that asset's loan-to-value ratio
3. All assets summed for total borrowing power

### Real Example

Let's say you deposit:
- **10 WETH** at $2,000 each = $20,000 value
  - WETH LTV: 80%
  - Borrowing power: $16,000

- **5,000 USDC** = $5,000 value
  - USDC LTV: 90%
  - Borrowing power: $4,500

- **100,000 PEPE** at $0.00001 = $1,000 value
  - PEPE LTV: 50%
  - Borrowing power: $500

**Total Borrowing Power: $21,000**

You could borrow up to 21,000 GREEN against this collateral.

### Weighted Averages

When you have multiple assets, Ripe calculates weighted average terms:

```
Weighted LTV = Total Borrowing Power / Total Collateral Value
              = $21,000 / $26,000
              = 80.8%
```

This unified approach gives you better terms than your riskiest asset alone.

## The Borrowing Process

### Step 1: Pre-Borrow Checks

Before you can borrow, the protocol verifies:

1. **Sufficient Collateral**: Requested amount ≤ borrowing power
2. **Minimum Debt**: Loans must exceed minimum threshold
3. **User Limits**: Within per-user debt ceiling
4. **Global Limits**: Protocol hasn't reached total debt cap
5. **Interval Limits**: Current period's borrowing capacity available

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

A one-time fee charged when borrowing:
- Typically 0.5% of borrowed amount
- Deducted from minted GREEN
- Distributed to sGREEN holders

**Example**:
- Borrow request: 10,000 GREEN
- Daowry (0.5%): 50 GREEN
- You receive: 9,950 GREEN
- Debt recorded: 10,000 GREEN

### Step 4: GREEN Distribution

You can receive your borrowed GREEN in several ways:

#### 1. Direct to Wallet
Receive standard GREEN tokens for immediate use in DeFi or spending.

#### 2. As Savings GREEN (sGREEN)
Receive your loan as sGREEN to start earning yield immediately:

**Benefits:**
- Yield begins accruing instantly
- No conversion transaction needed
- Potentially offset borrowing costs
- Automatic compounding

**Example Strategy:**
```
Borrow: 10,000 GREEN at 5% APR
Receive as: sGREEN earning 8% APR
Net Result: +3% APR profit
```

This creates a "self-paying loan" where yield covers interest costs. For comprehensive information about sGREEN, see the dedicated [Savings GREEN (sGREEN) guide](../sgreen.md).

#### 3. To Stability Pool
Direct your borrowed GREEN to stability pools as sGREEN:
- Automatically converts GREEN → sGREEN before depositing
- Start earning liquidation premiums immediately
- Stack sGREEN yield on top of stability pool rewards
- Support protocol stability
- Access to discounted collateral during liquidations

**Note**: Stability pools only accept sGREEN deposits, not naked GREEN. The protocol handles the conversion automatically when you select this option.

## Interest and Debt Management

Once you borrow, interest begins accruing immediately using continuous compounding. Your rate is refreshed whenever you interact with the protocol (borrow, repay, adjust collateral).

For detailed information about how interest accumulates, debt health calculations, and risk management, see [Understanding Your Debt](understanding-debt.md).

## Borrowing Limits

Ripe Protocol implements multiple types of limits to ensure system stability and gradual growth. These include per-user limits, global protocol caps, and time-based interval restrictions.

For complete details about all limit types, how they interact, and strategies for working within them, see [Borrowing Limits](borrowing-limits.md).

## Common Use Cases

### Liquidity Without Selling
Access funds while maintaining crypto exposure - deposit assets and borrow against them without triggering taxable events.

### Yield Arbitrage
Deposit yield-bearing assets (like stETH) and borrow at lower rates to capture the spread.

### Emergency Capital
Quickly access funds during market opportunities or personal needs without lengthy approval processes.

Next: Learn about [Understanding Your Debt](understanding-debt.md) →