# Dutch Auctions

Dutch auctions are Ripe's final liquidation method—when other mechanisms can't handle your collateral, it goes to auction where anyone can buy it at an increasing discount over time.

## Auction Mechanism

Dutch auctions implement time-based progressive discounting:

1. **Delayed start** - Configurable delay period after liquidation
2. **Linear progression** - Discount increases from start to maximum
3. **GREEN settlement** - All purchases require GREEN tokens
4. **Termination** - Ends on purchase or reaching maximum discount

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

## Auction Triggers

Collateral enters the auction system when:
- **No pool configuration** exists for the asset
- **Pool capacity exhausted** during liquidation
- **Asset configuration** specifies auction-only liquidation
- **Partial liquidation** leaves remainder after pool swaps
- **Keeper initiation** after liquidation with auction flag

## Cost to You

Dutch auctions typically cost more than stability pools:

**Stability Pools**: Your liquidation fee only (e.g., 6%)
**Dutch Auctions**: Your liquidation fee + auction discount (e.g., 6% + 15% = 21%)

The longer the auction runs, the bigger your loss.

## Auction Participants

Dutch auctions attract various market participants:
- Arbitrageurs seeking immediate profit opportunities
- Investors accumulating assets at discounts
- Protocol treasuries acquiring strategic positions
- General market participants with GREEN holdings

### Exception: Permissioned Assets

For whitelisted assets (like tokenized real estate or securities):
- **Only whitelisted addresses** can participate in auctions
- **Compliance maintained** throughout liquidation
- **Smaller buyer pool** may mean longer auctions
- **Same discount mechanics** apply to qualified buyers

## Auction Parameters

Each asset type has configured auction settings:

- **Delay blocks**: Time before auction starts (prevents instant arbitrage)
- **Start discount**: Initial percentage below market (e.g., 2-5%)
- **Maximum discount**: Final percentage if no buyers (e.g., 20-50%)
- **Duration blocks**: Total time for discount progression

Parameter selection reflects asset liquidity, volatility, and market depth.

## Phase 3 Priority

Dutch auctions are the last resort:
1. **Phase 1**: Burn your GREEN/sGREEN, transfer stablecoins
2. **Phase 2**: Swap with stability pools
3. **Phase 3**: Auction remaining collateral

## Liquidation Flow Integration

Auctions process collateral remaining after earlier phases:
- Phase 1 mechanisms reduce debt through burns and transfers
- Phase 2 stability pools handle liquid assets
- Phase 3 auctions clear remaining collateral at market-discovered prices

Excess collateral value returns to the original position holder after debt settlement.

## Auction Characteristics

Dutch auctions serve as the final liquidation mechanism with:
- Activation only when other methods cannot process collateral
- Progressive discounting over time
- Open participation for GREEN holders
- Higher effective costs than stability pool liquidations
- Guaranteed eventual liquidation through maximum discounts

## Auction System Design

Dutch auctions provide a market-based liquidation mechanism when other methods are unavailable or insufficient. The time-based discount structure creates economic incentives for market participants while ensuring all positions can eventually be liquidated.

The auction mechanism operates as the protocol's final liquidation method, guaranteeing debt resolution through progressive discounting that attracts buyers at market-clearing prices.

