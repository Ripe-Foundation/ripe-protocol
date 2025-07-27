# Liquidations: A Multi-Layered Defense System

Ripe Protocol's liquidation system represents a sophisticated approach to managing undercollateralized positions. Rather than harsh, immediate liquidations that can devastate borrowers, Ripe employs a graduated system designed to protect both users and the protocol. Multiple lines of defense work together to maintain GREEN's stability while giving borrowers every opportunity to recover.

## Why Liquidations Matter

### Protecting Protocol Solvency

Liquidations serve as the critical mechanism ensuring that [GREEN](01-green-stablecoin.md) remains fully backed. When [borrowing positions](03-borrowing.md) become undercollateralized due to collateral value drops or accumulated interest, the protocol must act to prevent bad debt accumulation. Without effective liquidations, the protocol could become insolvent, threatening all participants.

### The Borrower-Friendly Approach

Unlike traditional DeFi protocols that liquidate entire positions at once, Ripe only liquidates the minimum necessary to restore healthy collateralization. This approach:

- **Preserves User Value**: Keep as much collateral as possible
- **Reduces Market Impact**: Smaller liquidations mean less selling pressure
- **Enables Recovery**: Partial liquidations allow positions to potentially recover
- **Maintains Fairness**: Fixed fees rather than arbitrary penalties

## Understanding the Risk Zones

### The Three Critical Thresholds

Your position's safety depends on three key thresholds that work together to create graduated risk zones:

**1. Maximum LTV (Loan-to-Value)**
- Your borrowing limit as a percentage of collateral
- Example: 70% LTV on $10,000 = $7,000 maximum borrow
- Cannot borrow more once reached

**2. Redemption Threshold**
- Early warning system before liquidation
- GREEN holders can redeem against your position
- Provides market-based deleveraging opportunity
- Example: At 80% threshold, others can swap GREEN for your collateral at par

**3. Liquidation Threshold**
- The danger zone where forced liquidation begins
- Calculated as minimum collateral needed for your debt
- Example: At 90% threshold with $8,000 debt, liquidation starts when collateral < $8,889

### How Risk Escalates: Visual Zone Map

Consider a position with $10,000 initial collateral and $6,000 debt:

```
POSITION HEALTH VISUALIZATION (for $6,000 debt)
←─────────────────────────────────────────────────────────────→
$10,000                    $8,571      $7,500     $6,667      $0
  YOU                        ↓           ↓           ↓
  ARE                   Max LTV     Redemption  Liquidation
  HERE                   (70%)        (80%)        (90%)

[════ SAFE ZONE ════][CAUTION][REDEMPTION][LIQUIDATION]
     ✅ Healthy        ⚠️ Warning  🚨 Danger    💀 Critical
```

**Zone Breakdown:**

**🟢 Zone 1: Healthy** (Collateral > $8,571)
- Below 70% LTV maximum
- Can still borrow more
- No intervention possible

**🟡 Zone 2: Warning** (Collateral $8,571 - $7,500)
- Exceeded max LTV, cannot borrow
- Still safe from redemption
- Time to add collateral or repay

**🟠 Zone 3: Redemption** (Collateral $7,500 - $6,667)
- Redemption threshold breached
- GREEN holders can redeem your collateral
- Acts as automatic deleveraging

**🔴 Zone 4: Liquidation** (Collateral < $6,667)
- Liquidation threshold breached
- Multi-phase liquidation activates
- Position being actively liquidated

*For a detailed explanation of how these thresholds work together, see [Understanding Three Thresholds](03-borrowing.md#how-thresholds-work-together-a-visual-guide) in the borrowing documentation.*

## The Redemption Buffer

### Your First Line of Defense

Before liquidation becomes possible, the redemption mechanism provides a unique protective buffer. When your position enters the redemption zone:

- **GREEN holders can exchange** their tokens for your collateral at exactly $1 value
- **No discount applied** - fair value exchange protects you from penalties
- **Reduces your debt** automatically as collateral is redeemed
- **May prevent liquidation** by improving your position health

This mechanism serves dual purposes: protecting borrowers through gradual deleveraging while helping maintain GREEN's $1 peg during market stress.

### How Redemptions Help Everyone

When GREEN trades below $1:
- Arbitrageurs buy cheap GREEN from markets
- Redeem it against positions for $1 of collateral
- Creates buying pressure that restores the peg
- Provides liquidity exactly when needed most

## The Three-Phase Liquidation Process

When liquidation becomes necessary, Ripe employs a carefully orchestrated three-phase approach designed to minimize impact while ensuring debt repayment.

### Phase 1: Using Your Own Assets First

The protocol first looks to your existing positions within Ripe:

**GREEN and [sGREEN](04-sgreen.md) Burning**
- If you hold GREEN or [sGREEN](04-sgreen.md) in stability pools
- These are burned first to repay your debt
- Most direct form of repayment
- No market impact or external sales

**Stablecoin Transfers**
- Other stablecoins (USDC, USDT) you've deposited
- Transferred to [Endaoment](10-endaoment.md) treasury
- Used to back protocol reserves
- Counts toward debt repayment

### Phase 2: Stability Pool Swaps

Next, the protocol engages [stability pools](05-stability-pools.md) for instant liquidity:

**How Pool Swaps Work**
1. Your collateral (ETH, WBTC, etc.) needs liquidation
2. [Stability pools](05-stability-pools.md) hold GREEN LP tokens and [sGREEN](04-sgreen.md)
3. Pool assets swap for your collateral at the liquidation discount
4. Pool participants get discounted assets, you avoid market dumps

**Special Note on Permissioned Assets**
For regulated assets (tokenized securities, real estate):
- Dedicated permissioned pools with whitelisted participants
- Same swap mechanics but restricted access
- Ensures compliance throughout liquidation process

**The Win-Win Dynamic**
- You avoid harsh market conditions and slippage
- Pool depositors earn fixed discounts (typically 5-15%)
- Protocol maintains orderly liquidations
- No dependence on external market depth

**Additional Pool Benefits**
- Depositors earn RIPE rewards from the Stakers allocation
- GREEN holders can redeem against pool collateral for peg stability
- Flexible withdrawal lets depositors choose which assets to claim

*For deeper understanding of stability pool mechanics, see [Stability Pools](05-stability-pools.md).*

### Phase 3: Dutch Auctions

For any remaining collateral after pools are exhausted:

**Time-Based Discounts**
- Auctions start with small discounts (e.g., 2%)
- Discounts increase linearly over time (up to 20%)
- Anyone with GREEN can buy instantly at current discount
- No waiting for auction to "end" - immediate settlement

**Auction Mechanics**
- Initial delay prevents front-running
- Buyers can purchase any amount of fungible assets
- GREEN payment is burned, reducing your debt
- Auction ends when all collateral sold or debt repaid
- Any excess collateral value returns to you

## Liquidation Economics

### Understanding Liquidation Fees

Liquidation fees serve multiple purposes in the ecosystem:

**Fee Structure**
- Base liquidation fee: Typically 5-15% depending on asset risk
- Keeper rewards: Small additional fee (0.1-0.5%) for liquidation executors
- Total impact: Your cost becomes others' profit opportunity

**Where Fees Go**
1. **Stability Pool Depositors**: Receive discounted collateral as compensation
2. **Keepers**: Earn rewards for monitoring and executing liquidations
3. **Auction Buyers**: Purchase collateral below market value
4. **Protocol**: No direct protocol extraction - all value flows to participants

### Partial Liquidation Design

Ripe's system only liquidates enough to restore healthy LTV:

**Target Calculation**
- Determines minimum repayment for safe LTV
- Adds small buffer (1-2%) for safety
- Preserves maximum collateral possible
- Single formula works across all liquidation types

**Example Partial Liquidation**
```
Starting position: 
- Debt: $1,000
- Collateral: $1,250 (LTV = 80% - at liquidation threshold!)
- Max allowed LTV: 50%
- Liquidation fee: 10%

Protocol's unified formula: R = (D - T×C) × (1-F) / (1 - F - T)
Where: D = debt, C = collateral, T = target LTV, F = fee ratio

Calculation:
- R = ($1,000 - 0.50×$1,250) × 0.90 / (1 - 0.10 - 0.50)
- R = ($1,000 - $625) × 0.90 / 0.40
- R = $375 × 0.90 / 0.40
- R = $843.75 (amount to repay)

What happens:
1. Need to liquidate $937.50 of collateral (to get $843.75 after 10% fee)
2. Stability pools pay $843.75 (they keep 10% discount = $93.75)
3. Your debt reduces by $843.75

Final position:
- Debt: $1,000 - $843.75 = $156.25
- Collateral: $1,250 - $937.50 = $312.50
- New LTV: $156.25 ÷ $312.50 = 50% exactly!

Success! The unified formula perfectly calculates the liquidation amount
to achieve target LTV, while you keep 25% of your original collateral.
```

## The Keeper Network

### Your Automated Safety Net

Keepers are the protocol's decentralized guardians — independent operators who monitor positions and execute liquidations when needed. Think of them as automated lifeguards watching over the protocol.

**How Keepers Work**
- Monitor all positions 24/7 for liquidation thresholds
- Trigger liquidations the moment positions become unsafe
- Earn small rewards (typically 0.1-0.5% of debt) for their service
- Compete to execute liquidations quickly and efficiently

**Why This Benefits You**
- **Faster Response**: Liquidations happen within blocks, not hours
- **Fair Execution**: Open competition prevents insider advantages
- **Lower Losses**: Quick action minimizes how underwater positions get
- **Always Active**: Global network ensures 24/7 coverage

Anyone can be a keeper — no special permissions needed. This open system ensures liquidations happen promptly and fairly, protecting both borrowers and the protocol.

## Why Ripe's System is Superior

### Borrower Protection Features

1. **Graduated Intervention**: Redemption buffer before liquidation
2. **Partial Liquidations**: Only liquidate what's necessary
3. **Internal Recovery First**: Use your own assets before external sales
4. **Fixed Discounts**: No arbitrary penalties or excessive fees
5. **Multiple Mechanisms**: Three phases provide redundancy

### System Stability Benefits

1. **Orderly Process**: Phased approach prevents cascade failures
2. **Deep Liquidity**: Stability pools provide instant buyers
3. **Market Independence**: Not reliant on external exchange depth
4. **Rapid Execution**: Automated systems respond instantly
5. **Proven Resilience**: Designed for extreme market conditions

## Common Scenarios

### Scenario 1: Flash Crash with Redemption Buffer
*ETH drops from $2,500 to $1,800 in minutes*

**Your Position:**
- Collateral: 10 ETH (was $25,000, now $18,000)
- Debt: $15,000 GREEN
- LTV jumps: 60% → 83%

**What Happens:**
- At 80% you hit redemption threshold (not liquidation yet!)
- Arbitrageurs buy cheap GREEN and redeem $3,000 against your position
- Your debt drops to $12,000, LTV improves to 67%
- ETH rebounds to $2,100 within hours
- **Result**: Position saved by redemption buffer, no liquidation triggered

**Key Insight**: The redemption mechanism bought you time during extreme volatility.

### Scenario 2: Interest Accumulation Triggers Liquidation
*Forgot about your position for 6 months*

**Your Position Evolution:**
- Collateral: $62,500 ETH + $3,000 USDC = $65,500 total
- Max borrowing power: (ETH × 70%) + (USDC × 90%) = $43,750 + $2,700 = $46,450
- Debt: $46,000 (99% of max borrowing power - risky!)
- Month 3: $46,920 debt from 8% APR interest (exceeds borrowing power)
- Month 6: $47,840 debt (position underwater - liquidation triggered!)
- Also have: 2,000 sGREEN in stability pool (not collateral)

**Liquidation Execution:**
1. **Phase 1**: Burns your 2,000 sGREEN → debt drops to $45,840
2. **Phase 1**: Transfers 3,000 USDC to Endaoment → debt drops to $42,840
3. **Phase 2**: Need to restore position to safe borrowing capacity
   - Current: $42,840 debt, $62,500 ETH collateral only
   - ETH max borrowing: $62,500 × 70% = $43,750
   - Already under max! But need buffer for safety
   - Target: reduce debt to $40,000 (64% of ETH value)
   - Using unified formula with modest liquidation:
   - Liquidate $3,155 ETH at 10% fee → receive $2,840 GREEN
   - Your debt: $42,840 - $2,840 = $40,000
   - Your collateral: $62,500 - $3,155 = $59,345 ETH
   - New borrowing capacity: $59,345 × 70% = $41,541 (debt is $40,000 ✓)

**Final Damage:**
- Lost $315 to liquidation discount ($3,155 × 10%)
- Plus lost all your USDC collateral ($3,000)
- Total loss: $3,315 vs paying $1,840 interest
- **Key Insight**: Interest slowly pushes you toward liquidation - monitor regularly!

### Scenario 3: Multi-Collateral Liquidation
*You have diverse collateral when liquidation hits*

**Your Position:**
- 5,000 sGREEN in stability pool ($5,250 value - 0% LTV, not counted as collateral)
- 10,000 USDC (90% LTV)
- 3 ETH ($6,000, 70% LTV)
- Max borrowing power: ($10,000 × 90%) + ($6,000 × 70%) = $9,000 + $4,200 = $13,200
- Debt: $13,000 (98.5% of max - liquidation triggered!)
- Assets total: $21,250 (but only $16,000 counts as collateral)

**Important Note:** sGREEN and GREEN LP tokens have 0% LTV - they cannot be used as collateral for borrowing. Your actual borrowing capacity comes only from USDC and ETH.

**Liquidation Sequence:**
1. **Phase 1**: Burns your 5,000 sGREEN → debt drops to $7,750
2. **Phase 1**: Transfers 7,000 USDC to Endaoment → debt drops to $750
3. **Phase 2**: Swaps 0.42 ETH with stability pools → debt cleared
   - Need $833 of ETH to get $750 after 10% fee
   - You keep: 3,000 USDC + 2.58 ETH
4. **Final Position**: Debt cleared, borrowing capacity restored
   - Remaining: 3,000 USDC + 2.58 ETH = $8,160 collateral value
   - Max borrowing: ($3,000 × 90%) + ($5,160 × 70%) = $6,312

**Key Insight**: Your sGREEN holdings, while not collateral, serve as your first line of defense in liquidation - protecting your actual collateral assets.

### Scenario 4: Worst Case - High Fee Asset
*Your experimental token position goes bad*

**Your Position:**
- Collateral: $10,000 in volatile gaming token
- Debt: $5,000 (50% LTV)
- Token drops 30% → collateral now $7,000
- LTV jumps to 71%, triggering liquidation
- Liquidation fee: 15% (high-risk asset)

**What Happens:**
- No stability pools for this asset - straight to auction
- Current position: $5,000 debt / $7,000 collateral = 71.4% LTV
- Using unified formula to reach 50% LTV: R = (D - T×C) × (1-F) / (1 - F - T)
- R = ($5,000 - 0.50×$7,000) × 0.85 / (0.85 - 0.50)
- R = $1,500 × 0.85 / 0.35 = $3,643 repayment needed
- Collateral to liquidate (includes 15% fee): $3,643 / 0.85 = $4,286
- Dutch auction: buyers pay $3,643 GREEN for $4,286 of collateral
- Auction discount at purchase: 12% (buyers pay 88% of value)
- Actual GREEN paid: $3,643 × 0.88 = $3,206
- **Result**: Debt reduced by $3,206 to $1,794
- **Your collateral**: $7,000 - $4,286 = $2,714
- **New LTV**: $1,794 ÷ $2,714 = 66% (not quite at target due to auction discount)

**Key Insight**: Auction discounts mean you don't get full debt reduction. Lost $1,080 total ($643 liq fee + $437 auction discount).

## What If Bad Debt Occurs?

Despite all protective mechanisms, extreme market conditions could potentially create bad debt (where liquidation proceeds don't fully cover the debt). The protocol has a clear resolution mechanism:

**Bond Sales for Recovery**: The protocol can sell [bonds](09-bonds.md) to raise funds that clear bad debt. This process:
- Creates RIPE tokens beyond the 1 billion supply cap
- Distributes the dilution fairly across all RIPE holders
- Ensures bond buyers receive their full allocation
- Maintains protocol solvency without penalizing users

For example, if 1M RIPE is needed to cover bad debt, the total supply becomes 1.001 billion. This transparent mechanism ensures the protocol can always recover while treating all participants fairly.

## The Bottom Line

Ripe Protocol's liquidation system represents a fundamental rethinking of how DeFi handles risk. By prioritizing borrower protection while maintaining protocol solvency, the system creates sustainable conditions for all participants. The multi-phase approach, redemption buffer, and partial liquidation design work together to give you every opportunity to maintain your position while ensuring GREEN remains fully backed.

Understanding these mechanisms empowers you to borrow with confidence, knowing that the protocol's design aligns with your interests even in worst-case scenarios.

---

*For technical implementation details, see the [AuctionHouse Technical Documentation](../technical/core/AuctionHouse.md).*