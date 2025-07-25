# Liquidations

Understanding liquidation is crucial for safely using Ripe Protocol. The system employs a sophisticated multi-layered defense system designed to minimize user losses while maintaining protocol solvency and GREEN's stability.

## Why Liquidations Enable Asset Diversity

**The key to Ripe's multi-collateral innovation**: Our robust liquidation system is what allows the protocol to safely support such a wide variety of assets—from blue-chip cryptocurrencies to volatile memecoins, yield-bearing tokens, tokenized stocks and even NFTs.

While other protocols limit themselves to only the "safest" assets, Ripe's three-phase liquidation system can handle virtually any asset because:

1. **Risk is Isolated**: Each user's position is independent—one person's risky collateral doesn't affect others
2. **Multiple Defense Layers**: Three phases ensure even highly volatile assets can be liquidated efficiently
3. **Graduated Response**: System tries gentle methods first, only using aggressive liquidation as last resort
4. **Market Impact Control**: Stability pools and auctions prevent large market dumps
5. **Customized Parameters**: Each asset has tailored thresholds based on its specific risk profile

This sophisticated system transforms traditionally "unbankable" assets into viable collateral, expanding financial access while maintaining system safety.

## What is Liquidation?

Liquidation occurs when a borrower's position becomes undercollateralized—their debt exceeds safe levels relative to their collateral value. It's a protective mechanism that ensures protocol stability by repaying debt through collateral sales.

**Key Benefits:**
- Prevents bad debt accumulation
- Maintains GREEN's peg stability
- Protects all protocol users
- Minimizes losses through prioritized mechanisms

## The Redemption Safety Net

### How Redemptions Protect You from Liquidation

Before liquidation ever occurs, Ripe has an additional safety mechanism: **the redemption threshold**. This creates a buffer zone where other users can help restore your position to health without you losing value.

**How it works:**
- When your position enters the redemption zone (before liquidation threshold)
- GREEN holders can redeem their tokens against your collateral
- You receive a 1:1 value exchange (no loss, unlike liquidation)
- Your debt is reduced, potentially restoring your position to good health
- This happens automatically without any action from you

**Example:**
```
Your position:
- Collateral: $8,500 worth of WETH
- Debt: $8,000 GREEN
- Redemption threshold: 90%
- Liquidation threshold: 95%

Status: In redemption zone (but not liquidation zone)
- Someone redeems 1,000 GREEN against your position
- You lose $1,000 of WETH, but debt reduced by $1,000
- New position: $7,500 collateral, $7,000 debt
- Result: Position restored to safe zone, liquidation avoided!
```

This mechanism serves as an early warning system and automatic position improvement tool, often preventing liquidations entirely.

## When Liquidation Occurs

### Understanding Liquidation Threshold

The liquidation threshold is a critical safety parameter that determines when your position becomes eligible for liquidation. It works differently from your borrowing limit (LTV).

**Key Concept**: The liquidation threshold defines the **minimum collateral value** required for a given debt level.

**Calculation**: `Minimum Collateral Required = Debt × 100% / Liquidation Threshold%`

### How It Works

Unlike LTV which limits how much you can borrow, the liquidation threshold determines when you're in danger:

**Example with 95% Liquidation Threshold:**
```
Your debt: $10,000 GREEN
Liquidation threshold: 95%
Minimum collateral needed: $10,000 × 100% / 95% = $10,526

If your collateral drops below $10,526 → Liquidation eligible
```

### Why Higher Percentages Mean Tighter Requirements

A 95% liquidation threshold is MORE restrictive than 85%:
- 95% threshold = collateral must be at least 105.3% of debt
- 85% threshold = collateral must be at least 117.6% of debt

The higher the percentage, the less buffer you have before liquidation.

### Complete Example

**Starting Position:**
- Collateral: $10,000 WETH
- LTV: 80% (can borrow up to $8,000)
- You borrow: $7,000
- Liquidation threshold: 95%

**Liquidation Check:**
- Minimum collateral required: $7,000 × 100% / 95% = $7,368
- Your collateral ($10,000) > Required ($7,368) ✅ Safe

**If WETH price drops to $7,300:**
- Your collateral ($7,300) < Required ($7,368) ❌ Liquidatable

## Ripe's Advanced Liquidation System

Unlike simple liquidation systems, Ripe implements a **three-phase hierarchy** with multiple specialized mechanisms:

### Phase 1: Internal Recovery
- **[Stablecoin Burning](stablecoin-burning.md)** - Burns user's GREEN/sGREEN for debt repayment
- **[Endaoment Transfer](endaoment-transfer.md)** - Transfers stablecoins directly to protocol reserves

### Phase 2: Stability Pool Integration  
- **[Stability Pool Swaps](stability-pool-swaps.md)** - Trades collateral with pool depositors at controlled discounts

### Phase 3: Market Mechanisms
- **[Dutch Auctions](dutch-auctions.md)** - Time-based discount auctions for remaining collateral

## Core Liquidation Components

### **[Liquidation Phases](liquidation-phases.md)**
Learn about the three-phase priority system that processes assets strategically to minimize user losses.

### **[Unified Repayment Formula](unified-repayment-formula.md)**
Understand the mathematical foundation that determines exactly how much debt gets repaid across all mechanisms.

### **[Keeper Incentives](keeper-incentives.md)**
Discover how liquidators are rewarded for maintaining system health and what this means for liquidated users.

## Key Advantages Over Traditional Systems

### 1. Pre-Liquidation Protection
The redemption mechanism often prevents liquidations entirely:
- Acts as an automatic position improvement tool
- 1:1 value exchange (no loss to user)
- Creates a buffer before actual liquidation
- Helps maintain GREEN's peg while protecting users

### 2. Loss Minimization
When liquidation does occur, the priority system attempts the least costly methods first:
- Phase 1: Zero market impact (burning/transfers)
- Phase 2: Controlled market impact (stability pools)
- Phase 3: Open market only if necessary (auctions)

### 2. Speed and Efficiency
Multiple mechanisms can operate simultaneously, ensuring rapid debt resolution during market stress.

### 3. Market Impact Control
Stability pools and gradual auctions prevent large market dumps that could cascade into further liquidations.

### 4. User Protection
The system preserves as much user value as possible while ensuring protocol safety.

## Getting Started

If you're new to liquidations:
1. Start with **[Liquidation Phases](liquidation-phases.md)** to understand the process flow
2. Review **[Stablecoin Burning](stablecoin-burning.md)** to see the most user-friendly mechanism
3. Learn about **[Stability Pool Swaps](stability-pool-swaps.md)** for the most common liquidation type

If you're interested in the technical details:
1. Study the **[Unified Repayment Formula](unified-repayment-formula.md)** for the mathematical foundation
2. Explore **[Dutch Auctions](dutch-auctions.md)** for the market mechanism details
3. Understand **[Keeper Incentives](keeper-incentives.md)** for the economic incentives

## Safety First

The best liquidation is the one that never happens. Monitor your Debt Health regularly and maintain adequate safety buffers. The liquidation system is designed to protect you, but prevention is always better than recovery.

---

*For borrowing strategies that help avoid liquidation, see the [Borrowing section](../borrowing/README.md).*