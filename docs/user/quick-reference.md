# Quick Reference Guide

Essential parameters, formulas, and thresholds for Ripe Protocol operations.

## Core Concepts

### Asset Parameters by Category

| Asset Type | Typical LTV | Redemption | Liquidation | Interest Rate | Example Assets |
|------------|-------------|------------|-------------|---------------|----------------|
| **Stablecoins** | 85-95% | 87-97% | 90-98% | 2-5% APR | USDC, USDT, USDS |
| **Blue-Chip Crypto** | 75-85% | 77-87% | 80-90% | 4-8% APR | WETH, WBTC |
| **Yield-Bearing** | 70-80% | 72-82% | 75-85% | 3-7% APR | stETH, rETH, LP tokens |
| **Exotic Assets** | 30-60% | 35-65% | 40-70% | 10-25% APR | PEPE, SHIB, Meme coins |
| **NFTs** | 30-50% | 40-60% | 50-70% | 8-20% APR | Collections, Art |
| **RWAs** | 70-95% | 75-97% | 80-98% | 1-8% APR | Tokenized assets |

### Key Formulas

#### Borrowing Power
```
Borrowing Power = Σ(Asset Value × Asset LTV)
```

#### Weighted Parameters
```
Weight = Asset's Borrowing Power / Total Borrowing Power
Weighted Parameter = Σ(Asset Parameter × Weight)
```

#### Liquidation Threshold Check
```
Minimum Collateral Required = Debt × 100% / Liquidation Threshold%
Position Safe If: Current Collateral > Minimum Required
```

#### Unified Repayment Formula
```
Liquidation Amount = What's needed to restore health + Fees + Safety margin
```
Protocol calculates exactly what's needed - nothing more, nothing less.

## RIPE Block Rewards

### Distribution (150M RIPE over ~5 years)

| Category | Description | Calculation |
|----------|-------------|------------|
| **Borrowers** | GREEN debt holders | Principal × Blocks |
| **Stakers** | RIPE/RIPE LP (governance), sGREEN/GREEN LP (stability) | Balance × Blocks × Asset Weight |
| **Vote Depositors** | Future governance-selected assets | Balance × Blocks × Voter Allocation |
| **General Depositors** | All vault deposits | USD Value × Blocks |

### Asset Weights & Allocations
- **RIPE**: 100% weight (governance vault only)
- **RIPE LP**: 150% weight (governance vault only)
- **sGREEN/GREEN LP**: Staker allocation (stability pools only)
- Lock bonus: 0% (1 day) to 200% (3 years)

## Liquidation System

### Three Phases (Run Simultaneously)

| Phase | Assets | Cost to You | Speed |
|-------|--------|-------------|-------|
| **Phase 1** | Your GREEN/sGREEN (burned), Stables/GREEN LP (to Endaoment) | Liquidation fee only | Instant |
| **Phase 2** | Swapped with stability pools | Fee + 5-15% discount | Instant |
| **Phase 3** | Dutch auction (anyone buys with GREEN) | Fee + 5-25% discount | Hours |

### Keepers
- Bots monitor 24/7 and liquidate instantly when eligible
- Earn 1-2% of liquidated debt
- No delays or negotiations - immediate execution

## Dynamic Rate Protection

### GREEN/USDC Pool Triggers

| Pool Ratio | Multiplier | Additional |
|------------|------------|------------|
| < 60% GREEN | 1.0x | Normal rates |
| 60-70% GREEN | 1.5x-2.5x | Progressive increase |
| > 70% GREEN | 2.5x-3.0x | + Time boost (0.1%/1000 blocks) |

**Key**: Rates only update when YOU interact with your position

## Stability Pools

### What You Deposit
- sGREEN (yield-bearing GREEN)
- GREEN LP tokens (from GREEN/USDC)

### What You Earn
- Base yields (sGREEN appreciation, LP fees)
- Liquidation profits (5-15% discounts)
- RIPE rewards (Stakers category)
- Arbitrage activity (when GREEN < $1)

### Withdrawal Options
Choose any available assets up to your share value:
- Your original deposits
- Liquidated collateral (ETH, WBTC, etc.)
- GREEN from redemptions

## Governance Vault

### Lock Duration → Points Bonus

| Duration | Bonus | Total Multiplier |
|----------|-------|------------------|
| 1 day | 0% | 1.0x |
| 6 months | ~35% | 1.35x |
| 1 year | ~65% | 1.65x |
| 3 years | 200% | 3.0x |

### Withdrawal Impact
- **Normal exit**: Withdraw X% → Lose X% of points
- **Early exit**: Pay 80% penalty + lose 100% points

## Quick Safety Checks

### Position Health Zones

| Zone | Status | Action |
|------|--------|--------|
| **Safe** | Well above all thresholds | Continue normal operations |
| **Caution** | Approaching redemption threshold | Monitor closely |
| **Redemption** | Between redemption & liquidation | GREEN holders can redeem |
| **Danger** | At/below liquidation threshold | Immediate liquidation by keepers |

### Emergency Actions
1. **Add collateral** - Instant health improvement
2. **Repay debt** - Reduce outstanding GREEN
3. **Check rates** - May have increased if GREEN > 60% of pool
4. **Delegate** - Enable automated management

## Fee Summary

| Action | Fee | Paid To |
|--------|-----|---------|
| **First borrow** | 0.5% Daowry fee | Endaoment |
| **Liquidation** | 5-25% penalty | Liquidators/Pools |
| **Stability pool** | No fees | You earn instead |
| **Early governance exit** | 80% tokens | Other stakers |

## Protocol Comparison

### Why Ripe is Different

| Feature | Ripe | Others |
|---------|------|--------|
| **Collateral** | 10+ assets in ONE loan | Separate positions each |
| **Parameters** | Weighted average blend | Fixed per market |
| **Liquidation** | Only what's needed | Fixed percentages |
| **Asset support** | Meme coins to RWAs | Conservative only |
| **Yields** | Keep all collateral yields | Often forfeited |

## Common Scenarios

### Healthy Multi-Collateral Position
```
Collateral: $5k USDC (90% LTV) + $5k WETH (80% LTV)
Max Borrow: $4,500 + $4,000 = $8,500
Actual Debt: $6,000 (safe buffer maintained)
Weighted LTV: 85%
```

### Approaching Liquidation
```
Debt: $8,000
Liquidation Threshold: 95%
Minimum Collateral Needed: $8,421
Current Collateral: $8,500 (getting close!)
Action: Add collateral or repay immediately
```

### GREEN Under Peg
```
Market: GREEN at $0.95
Opportunity: Buy GREEN, redeem for $1 collateral
Effect: Creates buying pressure, restores peg
Who: Anyone with GREEN (not just depositors)
```

## Essential Links

- **Docs**: Full protocol documentation
- **Governance**: Vote on protocol changes (when active)
- **Analytics**: Monitor positions and pool health
- **Support**: Get help from community

---

This guide covers 90% of what you need. For edge cases and detailed mechanics, see full documentation.