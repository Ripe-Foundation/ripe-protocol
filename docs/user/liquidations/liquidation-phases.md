# Liquidation Phases

Ripe processes liquidations in three phases, always trying the gentlest methods first to minimize your losses.

## The Three-Phase System

Think of it like emergency medical care—start with the least invasive treatment:

**Phase 1**: Use your protocol deposits (GREEN/sGREEN)
**Phase 2**: Liquidate priority collateral (ETH, BTC, etc.)
**Phase 3**: Liquidate everything else if needed

## Phase 1: Your Protocol Deposits

**What's used first:**
- sGREEN in stability pools
- GREEN tokens you've deposited
- Stablecoins eligible for Endaoment

**Why it's best:**
- Zero loss (burns at full value)
- Instant processing
- No market impact

**Example:**
```
Need to repay: $5,000
Your sGREEN: 3,000 ($3,000 value)

Result: Burn sGREEN → $3,000 repaid
Remaining: $2,000 (moves to Phase 2)
```

## Phase 2: Priority Collateral

**What's used second:**
- Major cryptocurrencies (WETH, WBTC)
- High-liquidity tokens
- Assets with stability pools

**Why it's middle ground:**
- Fixed discounts (your liquidation fee)
- Quick processing via pools
- Predictable outcomes

**Example:**
```
Remaining debt: $2,000
Your WETH: 1 ETH ($2,500 value)

Result: Stability pool takes 1 WETH
You lose: ~$300 (liquidation fee + discount)
Debt: Fully repaid ✅
```

## Phase 3: Everything Else

**What's used last:**
- Exotic tokens
- NFTs
- Assets without pools
- New collateral types

**Why it's last resort:**
- May require auctions
- Higher discounts possible
- Slower processing

**Example:**
```
Still need: $500
Your NFT: Worth $800

Result: NFT goes to auction
Expected sale: ~$600 (after discounts)
Debt cleared, but higher loss
```

## How Phases Work Together

The system moves through phases until your debt is healthy again:

### Quick Resolution
```
Total needed: $10,000

Phase 1: Burn $6,000 sGREEN ✓
Phase 2: Swap $4,000 WETH ✓
Phase 3: Not needed!

Your other assets: Safe
```

### Full Liquidation
```
Total needed: $50,000

Phase 1: Burn $5,000 GREEN
Phase 2: Swap $35,000 mixed crypto
Phase 3: Auction $10,000 in NFTs

All phases used to restore health
```

## Why This Matters

### For You
- **Smart positioning helps**: Keep sGREEN for protection
- **Asset choice matters**: Major tokens liquidate better
- **Phases stop when healthy**: Not everything gets liquidated

### What Triggers Each Phase
- System always starts with Phase 1
- Only moves to Phase 2 if more needed
- Phase 3 is truly last resort

## Optimization Tips

**Best protection strategy:**
1. Maintain sGREEN reserves (Phase 1 shield)
2. Use blue-chip collateral (Phase 2 efficiency)
3. Limit exotic assets (avoid Phase 3)

**During liquidation:**
- Phase 1 happens automatically
- Phase 2 uses available pools
- Phase 3 creates auctions as needed

## Key Takeaways

1. **Three phases, increasing severity** - Gentle → Standard → Harsh
2. **Phases stop when debt healthy** - Not everything gets liquidated
3. **Your deposits used first** - Best possible outcome
4. **Priority assets next** - Stability pool swaps
5. **Everything else last** - Auctions if necessary

The phase system protects you by trying the least painful methods first. Understanding these phases helps you position your collateral for the best possible liquidation outcome.

Next: Learn about [Stablecoin Burning](stablecoin-burning.md) →