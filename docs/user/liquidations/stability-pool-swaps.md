# Stability Pool Swaps

Stability pool swaps are the primary liquidation mechanism in Ripe Protocol, allowing pool depositors to acquire liquidated collateral at discounts while protecting liquidated users from harsh market impacts.

## How It Works

When your collateral needs liquidation:

1. **Protocol checks stability pools** for available assets
2. **Swaps your collateral** with pool depositors at fixed discount
3. **Pool assets pay your debt** - GREEN LP tokens go to Endaoment, sGREEN is burned
4. **You avoid market selling** - no slippage or timing issues

## Pool Asset Types

**Available stability pool assets:**
- **GREEN LP tokens** - Liquidity provider tokens from GREEN/USDC pools
- **sGREEN** - Savings GREEN that earns yield while in pools

**Processing hierarchy:**
1. Claimable GREEN (from previous partial redemptions) → burned directly
2. GREEN LP tokens → transferred to Endaoment treasury
3. sGREEN → redeemed to GREEN and burned

### Permissioned Asset Pools

For regulated/whitelisted assets (tokenized securities, real estate):
- **Dedicated pools** can be created for compliant liquidations
- **Only whitelisted depositors** can provide liquidity
- **Only whitelisted users** can have these assets liquidated through the pool
- **Compliance maintained** throughout the liquidation process
- **Same swap mechanics** but restricted participant set

## Understanding Liquidation Fees & Discounts

**Key insight**: The liquidation fee you pay becomes the discount for stability pool depositors.

### Liquidation Fee Calculation

Multi-collateral positions calculate weighted liquidation fees based on borrowing power contribution:

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

## Economic Characteristics

### Liquidation Impact
The stability pool mechanism creates specific economic outcomes:
- **Fixed Discount**: Liquidation fee parameter determines exact discount
- **Instant Settlement**: No price discovery period or auction delays
- **Market Isolation**: Swaps occur without affecting spot markets

### Pool Participant Economics
Stability pool depositors experience:
- **Discount Capture**: Acquire assets below market price
- **Passive Execution**: No active management required
- **Portfolio Accumulation**: Build positions through liquidations
- **Volatility Exposure**: Hold acquired assets with market risk

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

## Mechanism Summary

1. **Primary liquidation pathway** - Configured assets route through stability pools
2. **Discount mechanism** - Liquidation fees translate directly to pool discounts
3. **Asset hierarchy** - Claimable GREEN, then LP tokens, then sGREEN
4. **Economic transfer** - Value flows from liquidated positions to pool participants
5. **System efficiency** - Automated swaps eliminate market friction

The stability pool system creates an internal liquidation market that operates independently of external exchanges while maintaining economic incentives for participation.

Next: Learn about [Dutch Auctions](dutch-auctions.md) →