# Unified Repayment Formula

The protocol calculates exactly how much liquidation is needed to restore your position to health - nothing more, nothing less.

## Core Concept

Instead of fixed percentages (like always liquidating 50%), Ripe uses a dynamic formula that liquidates only what's necessary to:
- Bring your position back to safe collateralization
- Cover liquidation fees
- Add a small safety buffer

## Why This Matters

**Traditional Protocols**: "Your position is unhealthy? We'll liquidate 50% of everything."

**Ripe Protocol**: "Your position needs $2,500 liquidated to be healthy again? We'll take exactly $2,500."

## Simple Example

```
Your position:
- Debt: $8,000
- Collateral: $12,000
- Status: Slightly underwater

Other protocols: Liquidate $6,000 (50%)
Ripe: Liquidate $2,500 (only what's needed)
You save: $3,500 of collateral
```

## The Formula

Without complex math, it essentially calculates:

**Liquidation Amount = What's needed to restore health + Fees + Safety margin**

The same formula applies whether your assets go through:
- Phase 1: Burning/transfers
- Phase 2: Stability pools  
- Phase 3: Dutch auctions

## Key Benefits

- **Minimal impact**: Only liquidates what's mathematically required
- **Consistent**: Same calculation across all liquidation types
- **Transparent**: Predictable outcomes based on your position
- **Fair**: No arbitrary percentages or excessive liquidations

The unified formula ensures you keep maximum collateral while the protocol stays solvent.

Next: Learn about [Liquidation Configuration](08-liquidation-configuration.md) →