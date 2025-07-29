# Liquidations: When Leverage Goes Wrong (But Not Too Wrong)

Other protocols: "Your position dropped 10%? We're taking everything. Thanks for playing."

Ripe: "Let's fix this together. We'll use your sGREEN first, take only what we need, and you keep the rest."

Four layers of protection. Partial liquidations only. Your own assets used first. This isn't charity — it's math. Keeping borrowers alive keeps the protocol healthy. Dead borrowers don't pay interest.

## Executive Summary

**Key Points:**
- 🛡️ **Four defense layers**: Redemption buffer → Your own assets → Stability pools → Dutch auctions
- 📊 **Partial only**: Liquidates just enough to restore health, not entire position
- 💰 **Fair pricing**: 5-15% liquidation fees
- ⚡ **Automated**: Keeper network ensures rapid execution
- 🎯 **Your assets first**: Uses your stability pool deposits and stablecoins with no penalties

**Quick Visual: The Liquidation Flow**
```
Your Position Becomes Unhealthy
            ↓
    REDEMPTION ZONE (First)
    └─ GREEN holders can redeem
       at $1 (no penalty for you)
            ↓
    LIQUIDATION TRIGGERED
            ↓
┌───────────────────────────────┐
│   PHASE 1: Your Own Assets    │
│   • Your sGREEN in pools      │
│   • Your GREEN LP in pools    │
│   • Your stablecoin deposits  │
└────────────┬──────────────────┘
             ↓ (if needed)
┌───────────────────────────┐
│   PHASE 2: Stability Pool │
│   • Instant swaps         │
│   • 5-15% discount only   │
└────────────┬──────────────┘
             ↓ (if needed)
┌───────────────────────────┐
│   PHASE 3: Dutch Auction  │
│   • Public sale           │
│   • Increasing discounts  │
└───────────────────────────┘
```

**What This Means For You:**
- ✅ Multiple chances to avoid liquidation
- ✅ Keep most of your collateral
- ✅ Lower fees than other protocols
- ✅ No cascade liquidations
- ✅ Fair, transparent process

## Quick Navigation

**Understanding the Basics:**
- [Why Liquidations Matter](#why-liquidations-matter) - Protocol safety and borrower protection
- [Risk Zones](#understanding-the-risk-zones) - Three thresholds and visual guide
- [Redemption Buffer](#the-redemption-buffer) - Your first line of defense

**The Liquidation Process:**
- [Phase 1: Own Assets](#phase-1-using-your-own-assets-first) - GREEN/sGREEN burning
- [Phase 2: Stability Pools](#phase-2-stability-pool-swaps) - Instant liquidity
- [Phase 3: Dutch Auctions](#phase-3-dutch-auctions) - Time-based discounts

**Advanced Topics:**
- [Liquidation Economics](#liquidation-economics) - Fees and calculations
- [Keeper Network](#the-keeper-network) - Automated execution
- [Common Scenarios](#common-scenarios) - Real-world examples
- [Bad Debt Handling](#what-if-bad-debt-occurs) - Last resort measures

---

## Why Liquidations Matter

### Protecting Protocol Solvency

Liquidations serve as the critical mechanism ensuring that [GREEN](01-green-stablecoin.md) remains fully backed. When [borrowing positions](03-borrowing.md) become undercollateralized due to collateral value drops or accumulated interest, the protocol must act to prevent bad debt accumulation. Without effective liquidations, GREEN could lose its peg, affecting GREEN and sGREEN holders.

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

## The Three-Phase Liquidation Process

When liquidation becomes necessary, Ripe employs a carefully orchestrated three-phase approach designed to minimize impact while ensuring debt repayment.

### Phase 1: Using Your Own Assets First

The protocol first looks to your existing positions within Ripe:

**Your Stability Pool Deposits**
- Your own [sGREEN](04-sgreen.md) deposits in stability pools → burned to reduce debt
- Your own GREEN LP deposits in stability pools → sent to Endaoment to reduce debt
- Direct debt reduction with no penalties or discounts
- These are YOUR deposits being used to pay YOUR debt

**Your Stablecoin Collateral**
- USDC, USDT, and other stablecoins you deposited as collateral
- Transferred to [Endaoment](11-endaoment.md) treasury at 1:1 value
- No liquidation discount applied to stablecoins
- Immediately reduces your debt dollar-for-dollar

### Phase 2: Stability Pool Swaps

Next, the protocol engages [stability pools](05-stability-pools.md) for instant liquidity:

**How Pool Swaps Work**
1. Your collateral (ETH, WBTC, etc.) needs liquidation
2. [Stability pools](05-stability-pools.md) hold GREEN LP tokens and [sGREEN](04-sgreen.md)
3. Pool assets swap for your collateral at the liquidation discount
4. Pool participants get discounted assets, you avoid market dumps

**The Win-Win Dynamic**
- You avoid harsh market conditions and slippage
- Pool depositors earn fixed discounts (typically 5-15%)
- Protocol maintains orderly liquidations
- No dependence on external market depth

**Additional Pool Benefits**
- Depositors earn RIPE rewards from the Stakers allocation
- GREEN holders can redeem against pool collateral for peg stability
- Flexible withdrawal lets depositors choose which assets to claim

**Special Note on Permissioned Assets**
For regulated assets (tokenized securities, real estate):
- Dedicated permissioned pools with whitelisted participants
- Same swap mechanics but restricted access
- Ensures compliance throughout liquidation process

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

> **💡 TL;DR**: If you're at 80% LTV and need to get back to 50%, we only liquidate exactly what's needed - not your entire position. In the example below, you keep 25% of your collateral instead of losing everything.

**Real Example: Partial vs Full Liquidation**

```
Your position hits liquidation threshold:
- Debt: $1,000
- Collateral: $1,250 (too risky!)
- Target: Get back to safe 50% LTV

Other protocols: Take ALL $1,250 → You get $0

Ripe Protocol:
- Takes only $937.50 of collateral
- Pays down debt to $156.25
- You keep $312.50 (25% of original!)
- Position restored to exactly 50% LTV

The 10% liquidation fee ($93.75) goes to stability pool depositors
as their profit for providing instant liquidity.
```

> **🎯 Key Takeaway**: You lost $937.50 but kept $312.50. On other protocols, you'd lose everything. That's a $312.50 difference in your pocket.

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

### Quick Comparison

| Feature | Traditional DeFi | Ripe Protocol |
|---------|-----------------|---------------|
| **Liquidation Amount** | Entire position (100%) | Only what's needed (partial) |
| **Warning System** | None | Redemption buffer zone |
| **Liquidation Fee** | 13-50% penalty | 5-15% fixed discount |
| **Who Can Buy** | MEV bots only | Anyone (pools + auctions) |
| **Your Assets Used** | No | Yes (GREEN/sGREEN first) |
| **Market Impact** | Large dumps | Phased, orderly process |

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

## What If Bad Debt Occurs?

Despite all protective mechanisms, extreme market conditions could potentially create bad debt (where liquidation proceeds don't fully cover the debt). The protocol has a clear resolution mechanism:

**Bond Sales for Recovery**: The protocol can sell [bonds](10-bonds.md) to raise funds that clear bad debt. This process:
- Creates RIPE tokens beyond the 1 billion supply cap
- Distributes the dilution fairly across all RIPE holders
- Ensures bond buyers receive their full allocation
- Maintains protocol solvency without penalizing users

For example, if 1M RIPE is needed to cover bad debt, the total supply becomes 1.001 billion. This transparent mechanism ensures GREEN remains fully backed while distributing any dilution proportionally across all RIPE holders.

## Liquidations That Don't Ruin Lives

Here's what actually matters:

**When others get liquidated**: They lose everything. Position gone. Starting over from zero.

**When you get liquidated on Ripe**: You lose some. Position survives. Still in the game.

That $312.50 difference in our example? That's rent money. That's staying in crypto versus rage quitting. That's the difference between a setback and a catastrophe.

The protocol doesn't do this to be nice. It does it because borrowers who survive keep borrowing, keep paying interest, keep the system running. Your success is the protocol's success.

So go ahead. Take that loan. The safety net has four layers.

---

*For technical implementation details, see the [AuctionHouse Technical Documentation](../technical/core/AuctionHouse.md).*