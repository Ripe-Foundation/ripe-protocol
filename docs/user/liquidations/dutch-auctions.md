# Dutch Auctions

Dutch auctions are Ripe's final liquidation method—when other mechanisms can't handle your collateral, it goes to auction where anyone can buy it at an increasing discount over time.

## How It Works

Think of it like a clearance sale that gets cheaper every hour:

1. **Auction starts** at near market price (small discount)
2. **Price drops gradually** over time (linear decrease)
3. **Anyone can buy** with GREEN tokens at current price
4. **Auction ends** when someone buys or max discount reached

## Real Example

```
Your 5 WETH going to auction
Market price: $2,000 each

Hour 0: $1,900 (5% off)
Hour 1: $1,833 (8% off)
Hour 2: $1,767 (12% off)
Hour 3: $1,700 (15% off)
Hour 4: $1,633 (18% off)
Hour 5: $1,567 (22% off)
Hour 6: $1,500 (25% off - max discount)
```

Someone buys at Hour 3 for $8,500 total → Your debt reduced by $8,500

## When Auctions Happen

Your collateral goes to auction when:
- **No stability pools available** for that asset
- **Pools are full** and can't take more
- **Exotic assets** without other liquidation options
- **Remainder collateral** after partial pool swaps

## Cost to You

Dutch auctions typically cost more than stability pools:

**Stability Pools**: Your liquidation fee only (e.g., 6%)
**Dutch Auctions**: Your liquidation fee + auction discount (e.g., 6% + 15% = 21%)

The longer the auction runs, the bigger your loss.

## Who Buys at Auctions?

**Arbitrageurs**: Buy below market, sell immediately for profit
**Investors**: Accumulate assets at discounts
**Protocols**: May buy strategic assets
**Anyone**: Open market—anyone with GREEN can participate

### Exception: Permissioned Assets

For whitelisted assets (like tokenized real estate or securities):
- **Only whitelisted addresses** can participate in auctions
- **Compliance maintained** throughout liquidation
- **Smaller buyer pool** may mean longer auctions
- **Same discount mechanics** apply to qualified buyers

## Asset-Specific Settings

Different assets have different auction parameters:

- **Blue-chip (ETH, BTC)**: 5% → 20% over 6 hours
- **Major tokens**: 10% → 30% over 8 hours
- **Volatile assets**: 15% → 40% over 12 hours
- **NFTs**: 20% → 50% over 24 hours

Riskier assets = Bigger discounts needed

## Phase 3 Priority

Dutch auctions are the last resort:
1. **Phase 1**: Burn your GREEN/sGREEN, transfer stablecoins
2. **Phase 2**: Swap with stability pools
3. **Phase 3**: Auction remaining collateral

## Multi-Phase Example

```
You need $60,000 liquidation:

Phase 1: Burn your 20,000 sGREEN → $20,000 repaid
Phase 2: Stability pools take WETH → $25,000 repaid
Phase 3: Auction your rare NFT → $18,000 repaid

Result: Liquidation complete, $3,000 surplus returned
```

## Key Points

1. **Last resort mechanism** - Only when other methods unavailable
2. **Time = Money** - Longer auction = bigger discount
3. **Open market** - Anyone can buy your collateral
4. **Higher cost** - Typically 15-25% total loss vs 6% in pools
5. **Guaranteed liquidation** - Ensures debt gets repaid eventually

## Tips to Avoid Auctions

- **Maintain sGREEN reserves** - Phase 1 protection
- **Use common collateral** - Better pool availability
- **Monitor debt health** - Repay before liquidation
- **Act fast if liquidated** - Buy your own auction early

Dutch auctions ensure every position can be liquidated, but at a cost. They're the safety net that keeps the protocol solvent while giving markets time to find fair prices for your collateral.

Next: Learn about [Unified Repayment Formula](unified-repayment-formula.md) →