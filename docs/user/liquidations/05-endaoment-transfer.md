# Endaoment Transfer

Endaoment transfer moves eligible stablecoins directly to protocol reserves during liquidation, preserving full asset value while you still pay standard liquidation fees.

## How It Works

When your position requires liquidation and you hold eligible stablecoins:

1. **Protocol transfers stablecoins** to Endaoment (treasury)
2. **Credits full oracle value** against your debt
3. **You pay liquidation fees** on the repaid amount
4. **No market selling** - direct treasury deposit

## Eligible Assets

Typically high-quality stablecoins the protocol wants to accumulate:
- USDC, USDT, USDS, FRAX
- Other governance-approved stablecoins

## Example

```
Your position needs $15,000 liquidation
You have: 20,000 USDC collateral
Liquidation fee: 5%

Process:
- Transfer 15,000 USDC → Endaoment
- Credit $15,000 against debt
- You owe: $750 liquidation fee (5%)
- You keep: 5,000 USDC
```

## Key Points

### For You
- **Full value credit** - No liquidation discount on transferred assets
- **Still pay fees** - Standard liquidation fee applies (typically 5%)
- **Instant processing** - No waiting for buyers
- **Better than selling** - Avoids market slippage

### For Protocol
- **Builds reserves** - Treasury accumulates stable assets
- **No market impact** - Doesn't create sell pressure
- **Efficient process** - Simple transfer vs complex auctions

## Cost Comparison

**Endaoment Transfer:**
- Asset value: 100% credited
- Liquidation fee: 5%
- Total cost: 5%

**Regular Liquidation (Phase 3):**
- Asset discount: 5-10%
- Liquidation fee: 5%
- Total cost: 10-15%

Result: Endaoment transfer saves you the asset discount, though liquidation fees still apply.

## Summary

Endaoment transfer is a Phase 1 mechanism that moves your stablecoins to protocol reserves at full value. While you still pay liquidation fees for being liquidated, you avoid the additional discount losses of market-based liquidations.

Next: Learn about [Stability Pool Swaps](06-stability-pool-swaps.md) →