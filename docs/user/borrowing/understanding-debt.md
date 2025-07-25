# Understanding Your Debt

Managing debt effectively requires understanding how it's calculated, how it grows, and how various factors affect your position. This guide explains everything you need to know about your Ripe Protocol debt.

## Debt Components

Your total debt consists of two parts that are tracked separately:

### 1. Principal
The original amount you borrowed:
- Fixed at borrowing time
- Doesn't change until repayment
- The baseline for interest calculations

### 2. Accrued Interest
The cost of borrowing over time:
- Accumulates continuously
- Compounds into the total
- Rate based on your collateral mix

**Total Debt = Principal + Accrued Interest**

## How Interest Accumulates

### Continuous Compounding

Ripe uses continuous compounding for precise calculations:

```
Interest at time t = Principal × (e^(rate × time) - 1)
```

This means:
- Interest accrues every block (~2 seconds on Base)
- Small amounts compound frequently
- More accurate than daily/monthly compounding

### Real-World Example

**Initial Borrow**:
- Principal: 10,000 GREEN
- Annual Rate: 5%
- Daily Rate: 0.0137%

**Interest Growth**:
- Hour 1: 0.057 GREEN
- Day 1: 1.37 GREEN  
- Week 1: 9.59 GREEN
- Month 1: 41.10 GREEN
- Year 1: 500 GREEN

Your debt grows predictably based on time and rate.

## Weighted Debt Terms

With multiple collateral types, your debt terms are weighted averages:

### How Weighting Works

Each asset contributes to your overall terms based on its borrowing power:

**Example Portfolio**:
```
Asset    Value     LTV    Max Debt   Rate   Weight
WETH     $20,000   80%    $16,000    5%     76%
USDC     $5,000    90%    $4,500     3%     21%
PEPE     $1,000    50%    $500       12%    3%
------------------------------------------------
Total    $26,000          $21,000    4.8%   100%
```

Your effective rate: (5% × 0.76) + (3% × 0.21) + (12% × 0.03) = 4.8%

### Why Weighting Matters

- **Better Rates**: High-value, low-risk assets improve your average
- **Risk Distribution**: No single asset dominates your terms
- **Optimization Opportunity**: Add assets strategically to improve rates

## Critical Debt Thresholds

Ripe Protocol uses three key thresholds that determine your position's safety. Understanding these is crucial for managing your debt effectively.

### 1. Loan-to-Value (LTV) Ratio

**What it is**: Your basic borrowing limit
**How it works**: You can borrow up to this percentage of your collateral value
**Calculation**: `Maximum Debt = Collateral Value × LTV%`

**Example**:
```
Collateral: $10,000 WETH
LTV: 80%
Maximum you can borrow: $8,000 GREEN
```

### 2. Redemption Threshold

**What it is**: The danger zone where other users can redeem your collateral
**How it works**: When your collateral value drops below a certain ratio to your debt
**Calculation**: `Minimum Collateral = Debt × 100% / Redemption Threshold%`

**Example**:
```
Your debt: $8,000 GREEN
Redemption threshold: 90%
Redemption triggers when collateral < $8,889
(Because $8,000 × 100% / 90% = $8,889)
```

**Important**: When in the redemption zone, other GREEN holders can pay off portions of your debt and take equivalent collateral. This helps restore GREEN's peg while giving you a warning before liquidation.

### 3. Liquidation Threshold

**What it is**: The critical point where forced liquidation occurs
**How it works**: When your collateral value drops below the minimum required
**Calculation**: `Minimum Collateral = Debt × 100% / Liquidation Threshold%`

**Example**:
```
Your debt: $8,000 GREEN
Liquidation threshold: 95%
Liquidation triggers when collateral < $8,421
(Because $8,000 × 100% / 95% = $8,421)
```

**Critical**: At this point, your position will be liquidated through the three-phase liquidation system.

## How Thresholds Work Together

### Risk Progression Example

**Starting Position**:
- Collateral: $10,000
- Maximum borrow (80% LTV): $8,000
- You borrow: $7,000
- Initial safety margin: $3,000

**As collateral value drops OR debt grows from interest**:

1. **Healthy Zone** (Collateral > $8,750)
   - Below maximum LTV
   - No risk of redemption or liquidation
   - Can still borrow more

2. **Redemption Zone** (Collateral between $7,778 - $7,368)
   - Redemption threshold: 90%
   - Others can redeem your collateral
   - Warning to add collateral or repay debt

3. **Liquidation Zone** (Collateral < $7,368)
   - Liquidation threshold: 95%
   - Forced liquidation begins
   - Three-phase liquidation process activates

### Key Insight: The Inverse Relationship

Unlike LTV which is a forward calculation (debt as % of collateral), redemption and liquidation thresholds work inversely:
- They define the **minimum collateral required** for a given debt level
- As your collateral drops OR debt grows, you approach these danger zones
- Higher threshold percentages = tighter requirements

## Practical Examples

### Example 1: Interest Impact on Thresholds

**Day 1**:
- Collateral: $10,000
- Debt: $6,000
- Safe from all thresholds

**Day 180** (5% APR):
- Collateral: $10,000 (unchanged)
- Debt: $6,150 (with interest)
- Redemption threshold: $6,833 (closer to danger)
- Still safe but margin reduced

### Example 2: Multi-Collateral Weighted Thresholds

When you have multiple assets, thresholds are weighted by debt capacity:

```
Asset A: $8,000 value, 80% LTV, 90% redemption threshold
Asset B: $2,000 value, 50% LTV, 80% redemption threshold

Weighted redemption threshold = 
  (90% × $6,400 + 80% × $1,000) / $7,400 = 88.6%
```

Understanding these thresholds is crucial for avoiding costly redemptions and liquidations. Monitor your position relative to all three thresholds, not just your borrowing limit.

Next: Learn about [Borrowing Limits](borrowing-limits.md) →