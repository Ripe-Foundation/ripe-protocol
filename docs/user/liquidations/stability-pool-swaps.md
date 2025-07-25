# Stability Pool Swaps

Stability pool swaps are the primary liquidation mechanism in Ripe Protocol, allowing pool depositors to acquire liquidated collateral at discounts while protecting liquidated users from harsh market impacts.

## How It Works

When your collateral needs liquidation:

1. **Protocol checks stability pools** for available assets
2. **Swaps your collateral** with pool depositors at fixed discount
3. **Pool assets pay your debt** - GREEN LP tokens go to Endaoment, sGREEN is burned
4. **You avoid market selling** - no slippage or timing issues

## Current Pool Assets

**What's in stability pools today:**
- **sGREEN** - The primary stability asset (burned when used)
- **GREEN LP tokens** - Liquidity pool tokens (sent to Endaoment when used)

**Priority order:**
1. GREEN LP tokens used first → sent to Endaoment
2. sGREEN used second → redeemed and burned

### Permissioned Asset Pools

For regulated/whitelisted assets (tokenized securities, real estate):
- **Dedicated pools** can be created for compliant liquidations
- **Only whitelisted depositors** can provide liquidity
- **Only whitelisted users** can have these assets liquidated through the pool
- **Compliance maintained** throughout the liquidation process
- **Same swap mechanics** but restricted participant set

## Understanding Liquidation Fees & Discounts

**Key insight**: The liquidation fee you pay becomes the discount for stability pool depositors.

### How Liquidation Fee is Calculated

Like other debt terms, your liquidation fee is weighted across all collateral:

```
Example Multi-Collateral Position:
- $50,000 WETH (liquidation fee: 5%)
- $30,000 WBTC (liquidation fee: 5%)  
- $20,000 PEPE (liquidation fee: 10%)

Weighted Liquidation Fee:
(50,000 × 5% + 30,000 × 5% + 20,000 × 10%) / 100,000 = 6%
```

### How This Becomes Pool Discount

When liquidated, your 6% fee becomes the pool's discount:

```
Your collateral value: $10,000
Liquidation fee: 6%
Pool pays: $9,400 (gets 6% discount)
Your cost: $600
```

**The flow:**
1. You pay 6% liquidation fee
2. Pool depositors get your collateral at 6% discount
3. This discount is their compensation for providing liquidity

## Benefits vs. Risks

### For Liquidated Users
✅ **Better than auctions** - Your liquidation fee is the only cost
✅ **Instant resolution** - No waiting for buyers
✅ **No market impact** - Doesn't crash asset prices

❌ **Still costs money** - Pay your weighted liquidation fee
❌ **No control** - Automatic process

### For Pool Depositors
✅ **Earn on liquidations** - Buy assets at discount
✅ **Passive income** - Automated process
✅ **Diversification** - Acquire various assets

❌ **Asset risk** - Acquired assets may decline
❌ **Timing risk** - Can't control when liquidations occur

## Multi-Pool Example

Large liquidations may use multiple pools:

```
Your liquidation needs: $100,000
Your weighted liquidation fee: 6%
Pool capacities:
- Primary pool: $60,000 GREEN LP tokens
- Secondary pool: $50,000 sGREEN

Execution:
1. Use $60,000 GREEN LP → Endaoment (6% discount = $3,600)
2. Use $40,000 sGREEN → burned (6% discount = $2,400)
3. Your total cost: $6,000 (exactly your liquidation fee)
```

## Phase 2 Priority

Stability pool swaps happen in Phase 2:
- After Phase 1: GREEN/sGREEN burning and Endaoment transfers
- Before Phase 3: Dutch auctions

This ordering maximizes value preservation while ensuring rapid liquidation.

## Key Takeaways

1. **Primary liquidation method** - Most liquidations use stability pools
2. **Your liquidation fee = Pool discount** - The fee you pay is what depositors earn
3. **Current assets** - GREEN LP and sGREEN provide the liquidity
4. **Total cost** - Just your weighted liquidation fee (no additional costs)
5. **Win-win design** - Depositors earn your fee as their discount

Stability pools create a sustainable liquidation system where everyone benefits: liquidated users get fair treatment, depositors earn returns, and the protocol maintains stability.

Next: Learn about [Dutch Auctions](dutch-auctions.md) →