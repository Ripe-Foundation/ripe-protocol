# Unified Repayment Formula

Ripe uses a mathematical formula to calculate exactly how much of your collateral gets liquidated—no more, no less. This ensures fair liquidations that only take what's needed to restore your position to health.

## What It Does

The formula calculates the minimum liquidation needed by considering:
- Your current debt
- Your collateral value  
- Target safety level after liquidation
- Liquidation fees

**Result**: Precise liquidation amount that restores health without over-liquidating.

## Why It Matters

### Traditional Liquidations (Other Protocols)
"Liquidate 50% of position" → Often takes too much
"Fixed percentages" → One-size-fits-all approach
**Problem**: You lose more than necessary

### Ripe's Formula
"Calculate exact amount needed" → Takes only what's required
"Dynamic calculation" → Adapts to your specific position
**Benefit**: Minimal loss, maximum fairness

## Simple Examples

### Example 1: Small Liquidation Needed
```
Your position:
- Debt: $8,000
- Collateral: $12,000
- Health: Slightly below threshold

Formula calculates: Need to liquidate $2,500 worth
Result: You keep $9,500 of collateral, debt reduced to healthy level
```

### Example 2: Larger Liquidation Required
```
Your position:
- Debt: $15,000  
- Collateral: $18,000
- Health: Significantly underwater

Formula calculates: Need to liquidate $8,000 worth
Result: You keep $10,000 of collateral, position restored to safety
```

## How It Protects You

1. **No Over-Liquidation**
   - Takes exactly what's needed
   - Preserves maximum collateral
   - No arbitrary percentages

2. **Accounts for All Costs**
   - Includes liquidation fees upfront
   - No surprises after liquidation
   - Clear total cost calculation

3. **Dynamic Adjustment**
   - Adapts to market conditions
   - Considers asset volatility
   - Optimizes for your specific mix

## The Math (Simplified)

Without diving into complex formulas:

```
Amount to liquidate = 
  (How underwater you are + Safety buffer + Fees)
  ÷ 
  (Value recovery rate)
```

The formula ensures that after liquidation:
- Your remaining debt is safely collateralized
- You won't face immediate re-liquidation
- Maximum value is preserved

## Real Impact

**Scenario: You need liquidation**

Other protocols might:
- Take 50% of everything
- Use fixed rules
- Over-liquidate for "safety"

Ripe's formula:
- Calculates you only need 23% liquidated
- Takes exactly that amount
- Saves you 27% of your collateral

**That's real money saved.**

## Key Takeaways

1. **Mathematical precision** - Not arbitrary percentages
2. **Minimal liquidation** - Only what's needed to restore health
3. **Fair to users** - Protects your remaining collateral
4. **Transparent calculation** - No hidden surprises
5. **Better outcomes** - Typically save 20-40% vs. traditional liquidations

The Unified Repayment Formula is complex math working simply in your favor—ensuring every liquidation is as small as possible while still protecting the protocol.

Next: Learn about [Keeper Incentives](keeper-incentives.md) →