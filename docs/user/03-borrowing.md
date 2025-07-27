# Borrowing on Ripe: Unlock Liquidity Without Selling

Ripe Protocol enables borrowing [GREEN stablecoins](01-green-stablecoin.md) against your [deposited collateral](02-collateral-assets.md) through an automated system that weighs risks, adjusts rates dynamically, and maintains protocol stability. This isn't just another lending platform — it's a sophisticated credit engine that transforms idle assets into productive capital while preserving your exposure to upside potential.

## Why Borrow on Ripe

### Capital Efficiency Without Compromise

When you deposit assets into Ripe vaults, they don't just sit idle. The protocol evaluates your collateral portfolio and extends credit lines based on weighted risk parameters. This means:

- **Maintain asset exposure** while accessing liquidity
- **Avoid taxable events** from selling appreciated assets  
- **Compound yields** by borrowing at one rate and earning at another
- **Access instant liquidity** without credit checks or applications

The borrowing system serves as the demand driver for [GREEN](01-green-stablecoin.md), creating natural use cases that strengthen the stablecoin's utility and adoption. GREEN is minted when you borrow and burned when you repay, maintaining supply-demand equilibrium.

## How Borrowing Works

### Unified Position Structure

In Ripe Protocol, all your collateral across all vaults backs a single, unified loan position. You don't have separate loans for each asset — instead, your entire collateral portfolio supports one consolidated debt position. This design simplifies management and maximizes capital efficiency.

### The Credit Calculation Engine

Ripe's credit engine performs sophisticated calculations to determine your borrowing capacity:

1. **Collateral Valuation**: Each deposited asset is valued using real-time price feeds
2. **LTV Application**: Asset-specific loan-to-value ratios determine borrowing power
3. **Term Weighting**: Multiple assets create weighted average terms
4. **Risk Assessment**: Dynamic adjustments based on market conditions

This multi-factor approach ensures fair credit access while maintaining system security.

### Weighted Debt Terms Explained

When you deposit multiple collateral types, Ripe doesn't just average your terms — it weights them based on each asset's contribution to your total borrowing power. Here's how it works:

**Example Portfolio:**
```
ETH: $10,000 value × 70% LTV = $7,000 borrowing power
WBTC: $5,000 value × 65% LTV = $3,250 borrowing power  
USDC: $15,000 value × 90% LTV = $13,500 borrowing power

Total Borrowing Power = $23,750
```

**Weighted Interest Rate Calculation:**
```
ETH weight: $7,000 / $23,750 = 29.5%
WBTC weight: $3,250 / $23,750 = 13.7%
USDC weight: $13,500 / $23,750 = 56.8%

If rates are: ETH 6%, WBTC 7%, USDC 4%
Your rate = (6% × 29.5%) + (7% × 13.7%) + (4% × 56.8%) = 5.0%
```

This weighting applies to all debt terms: interest rates, liquidation thresholds, redemption thresholds, and origination fees. Assets with higher borrowing power have proportionally greater influence on your overall terms.

## Key Safety Thresholds

### Understanding Your Risk Levels

Three critical thresholds govern your position's safety. Understanding how they work — and how they work together — is essential for managing risk.

### The Three Thresholds Explained

**1. Loan-to-Value (LTV) Ratio: Your Borrowing Limit**

The LTV determines your maximum borrowing capacity as a percentage of collateral value.

- **What it means**: You can borrow up to this percentage of your collateral
- **Direction**: Higher debt OR lower collateral value → Higher LTV usage (risky)
- **Example**: 70% LTV on $10,000 collateral = $7,000 maximum borrow

**2. Redemption Threshold: The Warning Zone**

When your position becomes eligible for collateral redemption by GREEN holders.

- **What it means**: Other users can pay off your debt and take equivalent collateral
- **How it's calculated**: Position at risk when collateral < debt ÷ redemption threshold
- **Example with 80% threshold**:
  ```
  Your debt: $8,000
  Redemption triggers when collateral < $10,000
  (Because $8,000 ÷ 0.80 = $10,000)
  ```
- **Purpose**: Provides market-based deleveraging and early warning before [liquidation](06-liquidations.md)

**3. Liquidation Threshold: The Danger Zone**

The critical point where forced [liquidation](06-liquidations.md) begins to protect the protocol.

- **What it means**: Your position will be liquidated
- **How it's calculated**: Liquidation when collateral < debt ÷ liquidation threshold  
- **Example with 90% threshold**:
  ```
  Your debt: $8,000
  Liquidation triggers when collateral < $8,889
  (Because $8,000 ÷ 0.90 = $8,889)
  ```
- **No escape**: Once triggered, liquidation proceeds automatically

### How Thresholds Work Together

Here's how a position progresses through risk zones as conditions change:

**Starting Position Example:**
- Collateral: $10,000
- Maximum borrow (70% LTV): $7,000
- You borrow: $6,000
- Initial safety margin: $4,000

**As collateral value drops OR debt grows from interest:**

**Zone 1: Healthy (Collateral > $8,571)**
- ✅ Below maximum LTV
- ✅ No redemption risk
- ✅ Can still borrow more

**Zone 2: Caution (Collateral $8,571 - $7,500)**
- ⚠️ Above max LTV, cannot borrow more
- ✅ Still safe from redemption
- ⏰ Time to add collateral or reduce debt

**Zone 3: Redemption (Collateral $7,500 - $6,667)**
- 🚨 Redemption threshold breached (80%)
- ⚠️ GREEN holders can redeem your collateral
- ⏰ Last chance to avoid liquidation

**Zone 4: Liquidation (Collateral < $6,667)**
- 💀 Liquidation threshold breached (90%)
- 🔴 Automatic liquidation begins
- 📉 Collateral sold to repay debt

### The Critical Inverse Relationship

Unlike LTV which calculates forward (debt as % of collateral), redemption and liquidation thresholds work inversely — they define the **minimum collateral required** for a given debt level. This means:

- As debt grows from interest → You approach thresholds
- As collateral value drops → You approach thresholds  
- Higher threshold percentages = Tighter requirements = Less room for error

Understanding this inverse relationship helps you monitor the right metrics and take action before it's too late.

## Dynamic Interest Rates

### Base Rates vs Dynamic Adjustments

**Important**: Your normal interest rate is the weighted average from your collateral mix (as explained in "Weighted Debt Terms" above). Dynamic rate adjustments are an emergency mechanism that only activates during severe market stress — this is NOT the default state.

### When Dynamic Rates Activate

Ripe monitors the GREEN/USDC liquidity pool as a health indicator. Under normal conditions, you simply pay your weighted base rate. Dynamic adjustments only trigger when GREEN is under significant peg pressure.

**Key Point**: Dynamic rates are a protective mechanism that may never activate. They exist to incentivize market corrections during extreme conditions, not to penalize everyday borrowing.

**How Pool Monitoring Works:**
- **Balanced State**: 50% GREEN / 50% USDC → Base rates apply
- **Danger Zone**: GREEN exceeds 60% → Rate multipliers activate
- **Scaling Adjustments**: Rates increase proportionally from 60% to 100% GREEN

### Three-Layer Rate Adjustment

When imbalances occur, rates adjust through three mechanisms:

1. **Ratio-Based Multiplier**
   - Scales continuously based on pool composition
   - Higher GREEN percentage = Higher multiplier
   - Example: 65% GREEN might trigger a 1.5x multiplier, 80% GREEN a 2.5x multiplier

2. **Time-Based Accumulation**  
   - Additional increases for sustained imbalances
   - Typically 0.01% per 100 blocks in danger zone
   - Creates urgency for market correction

3. **Maximum Rate Protection**
   - Hard caps prevent excessive rates
   - Protocol maximum (e.g., 50% APR)
   - Protects borrowers from extreme conditions

**Real Example:**
```
Your weighted base rate (from collateral mix): 5% APR
This is what you pay under normal conditions!

If pool reaches 70% GREEN for 5,000 blocks:
- Your base rate: 5% (unchanged)
- Dynamic multiplier: 2.0x = 10% total
- Time boost: 0.01% × 50 = 0.5%
- Temporary rate: 10.5% APR

When pool returns to balance:
- Dynamic adjustments deactivate
- You return to paying just your 5% base rate
```

## Borrowing Limits and Safety

### Multi-Tiered Limit System

Ripe implements several limits to ensure sustainable growth:

**1. Collateral-Based Limits**
- Fundamental constraint based on deposited value
- Maximum = Sum of (Asset Value × LTV Ratio)

**2. Per-User Debt Ceiling**
- Individual caps during protocol growth phase
- Equal limits for all users
- Gradually increased by governance

**3. Global Debt Limit**
- System-wide GREEN supply cap
- Prevents unlimited minting
- Protects protocol stability

**4. Interval Borrowing Limits**
- Time-based windows (e.g., per 1,000 blocks)
- Prevents flash loan attacks
- Smooths borrowing demand

**5. Minimum Debt Requirement**
- Starts at ~$10 during early protocol growth
- Will increase gradually as protocol scales
- Ensures position economic viability
- Reduces system complexity

When borrowing, the most restrictive limit applies. This creates a robust framework that protects both individual users and the protocol.

## The Borrowing Experience

### Step-by-Step Process

1. **Deposit Collateral**: Add assets to Ripe vaults
2. **Calculate Capacity**: System determines your borrowing power
3. **Choose Amount**: Borrow up to your available limit
4. **Pay Origination Fee**: Small one-time fee (typically 0.5%)
5. **Choose How to Receive**: Option to receive as GREEN, auto-convert to sGREEN, or deposit directly into Stability Pool

### Distribution Options

When borrowing, you can choose one of three ways to receive your funds:

**Option 1: Direct GREEN** 
- Receive standard GREEN stablecoins
- Use immediately for any purpose
- Most flexible option

**Option 2: Auto-Convert to [sGREEN](04-sgreen.md)**
- Borrowed GREEN automatically wrapped into yield-bearing [sGREEN](04-sgreen.md)
- Start earning yield immediately on borrowed funds
- Potential for positive carry (yield > borrow rate)
- No separate conversion transaction needed

**Option 3: Direct to [Stability Pool](05-stability-pools.md)**
- Borrowed GREEN converted to sGREEN and deposited into [Stability Pool](05-stability-pools.md) in one transaction
- Earn both sGREEN yield AND stability pool rewards
- Participate in liquidations for discounted collateral
- Maximum yield potential but least liquid option

### Origination Fee (Daowry)

A one-time 0.5% fee on new borrows that:
- Flows directly to [sGREEN](04-sgreen.md) holders
- Creates immediate protocol revenue
- Aligns borrower and saver incentives

Example: Borrow 10,000 GREEN → Pay 50 GREEN fee → Receive 9,950 GREEN

## Repayment Flexibility

Ripe Protocol offers complete repayment flexibility:
- **No prepayment penalties** - Repay any amount at any time
- **No fixed terms** - Keep your loan as long as needed
- **Partial payments allowed** - Reduce debt incrementally
- **Instant debt reduction** - Payments immediately lower your risk

This flexibility lets you manage debt according to your needs without restrictive schedules or penalties.

---

Ready to start borrowing? Check your vault balances and available credit in the Ripe app.