# Stablecoin Burning

Stablecoin burning uses GREEN or sGREEN you've deposited in Ripe Protocol to repay debt during liquidation—a zero-loss liquidation mechanism.

## How It Works

**Most common scenario**: You have sGREEN deposited in a stability pool earning yield. During liquidation:

1. Protocol withdraws your sGREEN from the stability pool
2. Redeems sGREEN to GREEN at current exchange rate
3. Burns GREEN to reduce your debt
4. No value lost—debt reduced 1:1

## Key Requirements

- **Only works with protocol deposits** - Cannot access your wallet
- **Limited to deposited amount** - Can only burn what you've placed in Ripe
- **Automatic process** - No action needed from you

## Example

```
Your position:
- Debt: $10,000 GREEN
- Need to repay: $6,000 
- Have in stability pool: 7,000 sGREEN (rate: 1.05)

During liquidation:
- Withdraw 7,000 sGREEN from pool → 7,350 GREEN
- Burn 6,000 GREEN for debt
- Return 1,350 GREEN to you
- Result: Zero loss (vs 5-10% loss in normal liquidation)
```

## Benefits

- **No market impact** - No selling, no slippage
- **Full value preserved** - GREEN burns at $1, sGREEN at exchange rate
- **Dual purpose** - Your stability pool deposits protect against liquidation while earning yield

## Summary

If you have sGREEN in stability pools, it automatically protects you during liquidation by reducing debt at full value. This Phase 1 mechanism executes before any collateral liquidation, minimizing your losses.

Next: Learn about [Endaoment Transfer](endaoment-transfer.md) →