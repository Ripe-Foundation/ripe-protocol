# Unified Repayment Formula

The protocol implements a single mathematical formula that calculates optimal liquidation amounts across all liquidation mechanisms. This formula ensures consistent behavior whether assets go through burning, stability pools, or auctions.

## Summary

The unified repayment formula dynamically calculates the minimum liquidation amount needed to restore position health, considering multi-collateral positions, weighted parameters, and safety buffers. Unlike static percentage systems, this approach minimizes liquidation impact while ensuring protocol solvency.

## Formula Purpose

The calculation determines the exact debt repayment amount needed by incorporating:
- Current debt position
- Total collateral value
- Target loan-to-value ratio with safety buffer
- Asset-specific liquidation fees

**Output**: Minimum repayment amount that restores position health with appropriate margin.

## Mathematical Approach

### Fixed Percentage Systems
Many protocols use predetermined liquidation percentages:
- Static ratios regardless of position specifics
- Often liquidate more than necessary
- Simple but imprecise

### Dynamic Calculation
Ripe's formula adapts to each position:
- Calculates based on actual parameters
- Accounts for multi-collateral complexity
- Minimizes liquidation while ensuring safety

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

## Formula Characteristics

1. **Precision Targeting**
   - Calculates exact repayment requirements
   - Avoids excessive liquidation
   - Consistent across all mechanisms

2. **Comprehensive Calculation**
   - Incorporates all fees and costs
   - Accounts for target LTV buffer
   - Handles weighted parameters

3. **Universal Application**
   - Same formula for all liquidation types
   - Works with future mechanisms
   - Ensures predictable outcomes

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

## Formula Impact

1. **Consistent methodology** - Single formula across all mechanisms
2. **Optimal sizing** - Minimum viable liquidation amount
3. **Parameter integration** - Incorporates all position-specific values
4. **Conservative approach** - May slightly over-repay for safety
5. **Predictable results** - Deterministic calculation from inputs

The unified repayment formula creates a standardized approach to liquidation sizing that balances position recovery with value preservation.

Next: Learn about [Keeper Incentives](keeper-incentives.md) →