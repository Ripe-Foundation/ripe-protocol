# GREEN: The Stablecoin That Works Harder

Your USDC sits there doing nothing. Your DAI requires a new vault for every asset. Your LUSD only accepts ETH.

GREEN? It's built different. Mint it against your entire portfolio — ETH, stablecoins, NFTs, whatever you've got. Earn yield automatically through [sGREEN](04-sgreen.md). Score liquidation profits in [stability pools](05-stability-pools.md). Watch five different mechanisms defend the peg while you sleep.

This is what happens when you stop asking "how do we make another stablecoin?" and start asking "how should stablecoins actually work?"

## Why GREEN Exists

### The Problem with Current Stablecoin Borrowing

Traditional lending protocols force inefficient choices that limit how you can use stablecoins:

**Isolated Positions (MakerDAO/Liquity Model)**:
- Open ETH vault → Borrow DAI
- Open WBTC vault → Manage separate loan
- Add new asset? → Yet another position
- Result: Portfolio fragmentation, constant juggling

**Pooled Risk (Aave/Compound Model)**:
- Limited to "safe" assets only
- Your collateral backs everyone's loans
- One bad actor affects all users
- Result: Restricted innovation, systemic risk

**Isolated Money Markets (Morpho/Euler Model)**:
- Deposit ETH → One USDC loan
- Deposit WBTC → Another separate USDC loan
- Multiple positions to track and manage
- Each market needs lenders providing capital
- Result: Portfolio fragmentation AND rate inefficiency

### Ripe's Solution: Unified Multi-Collateral Borrowing

GREEN represents a fundamental rethink of stablecoin creation:

```
Traditional:  ETH → DAI Position 1
              WBTC → DAI Position 2
              USDC → Can't use

Ripe:         ETH + WBTC + USDC + stETH + NFTs + Anything
              ↓ (all combined)
              One GREEN Loan at Weighted Terms
```

Your entire portfolio — from blue-chip crypto assets to yield-bearing positions, from stablecoins to tokenized stocks — backs a single GREEN loan. This creates unmatched capital efficiency while keeping your risk isolated from other users.

### Complementary, Not Competitive

While these other lending protocols have borrowing limitations, they excel at generating yield — and Ripe turns their yield-bearing tokens into powerful collateral. Instead of choosing between earning yield OR borrowing, you can do both:

- **Aave aTokens**: Earn lending yield while using as Ripe collateral
- **Compound cTokens**: Your supplied assets keep compounding
- **Morpho positions**: Optimized rates become productive collateral
- **Maker sDAI**: Savings rate continues while backing GREEN loans

The best strategy? Lend on these protocols for yield, then use those yield-bearing positions as collateral on Ripe. You get their yields AND our capital efficiency — truly the best of both worlds.

### Built for the Entire Ecosystem

GREEN isn't just another stablecoin. It's the cornerstone of Ripe Protocol:

```
                        GREEN ECOSYSTEM
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  BORROWING          YIELD              STABILITY        │
│  ┌─────────┐       ┌──────────┐       ┌──────────┐      │
│  │ Mint    │       │ sGREEN   │       │ Stability│      │
│  │ GREEN   │  ───> │ Auto-    │  ───> │ Pools    │      │
│  │ Against │       │ Compound │       │ Earn     │      │
│  │ Assets  │       │ Yield    │       │ Discounts│      │
│  └─────────┘       └──────────┘       └──────────┘      │
│       │                  │                   │          │
│       └──────────────────┴───────────────────┘          │
│                          │                              │
│                    ┌─────▼──────┐                       │
│                    │  TREASURY  │                       │
│                    │  Endaoment │                       │
│                    │  Stabilizer│                       │
│                    └────────────┘                       │
│                                                         │
│  Every GREEN serves multiple purposes simultaneously    │
└─────────────────────────────────────────────────────────┘
```

## How GREEN Works

### Creation Through Borrowing

Every GREEN token represents real value locked in Ripe Protocol:

1. **Deposit Collateral**: Lock any [supported asset](02-collateral-types.md) (ETH, WBTC, stablecoins, etc.)
2. **Borrow GREEN**: Mint new GREEN against your collateral
3. **Overcollateralized Always**: Minimum 110% backing, often much higher
4. **Pay Interest**: [Dynamic rates](03-borrowing.md#dynamic-interest-rates) that respond to market conditions
5. **Origination Fee (Daowry)**: One-time fee that flows to sGREEN holders (currently 0.5%)

**Example Multi-Asset Borrowing**:
```
Your Unified Portfolio:
- 5 ETH worth $10,000 (70% LTV = $7,000 borrowing power)
- 10,000 USDC (90% LTV = $9,000 borrowing power)  
- 2 stETH worth $4,000 (85% LTV = $3,400 borrowing power)
- 1M PEPE worth $1,000 (50% LTV = $500 borrowing power)
- 1 Bored Ape worth $50,000 (40% LTV = $20,000 borrowing power)

Total Borrowing Power: $39,900 GREEN
Single Loan, Single Interest Rate, All Assets Working Together
```

### Destruction Through Repayment

GREEN supply contracts automatically when loans are repaid:

1. **Send GREEN**: Return borrowed amount plus interest
2. **Burn Forever**: GREEN is permanently destroyed
3. **Unlock Collateral**: Get your assets back proportionally

This elegant mechanism ensures GREEN supply expands and contracts with real borrowing demand.

## The Five Pillars of Stability

GREEN maintains its $1 peg through multiple interconnected mechanisms that activate automatically based on market conditions. Notably, GREEN features two distinct redemption mechanisms that create powerful arbitrage loops, ensuring the peg is defended from multiple angles:

### 1. Overcollateralization Foundation

The bedrock of GREEN's stability:
- **150%+ Average**: Most positions maintain much higher collateral ratios
- **Extreme Asset Diversity**: Unlike other stables limited to ETH/WBTC, GREEN is backed by everything from stETH earning staking yields to PEPE memes to tokenized Tesla stock
- **Portfolio Effect**: When one asset drops, others may rise — true diversification
- **Real-Time Monitoring**: Continuous health checks on all positions using [price oracles](12-price-oracles.md)
- **Buffer Zones**: Multiple warning levels before [liquidation](07-liquidations.md)

### 2. Dynamic Interest Rate Response

When GREEN trades below peg, borrowing rates increase to encourage repayment. For complete details on how dynamic rates work, see [Dynamic Interest Rates](03-borrowing.md#dynamic-interest-rates) in the borrowing documentation.

**Normal Conditions (Balanced Pool)**:
- 50% GREEN / 50% USDC in reference pool
- Borrowers pay only their weighted base rates
- No dynamic adjustments needed

**Below Peg Response (GREEN Weak)**:
- Pool imbalanced with >60% GREEN (too much GREEN supply)
- Dynamic rate multipliers activate progressively
- Higher rates incentivize borrowers to repay (buy GREEN)
- Repayment creates buying pressure, restoring peg

**Above Peg Response (GREEN Strong)**:
- Normal base rates apply (no increase needed)
- Endaoment can mint GREEN to add liquidity
- Increased supply brings price back down

**Emergency Rate Escalation**:
When GREEN exceeds 60% in reference pools:
- Base rates multiply progressively (1.5x to 3x based on severity)
- Time-based penalties accumulate (+0.01% per 100 blocks = ~3.3 minutes on Base)
- Creates powerful incentive to restore balance through repayment

### 3. Direct Redemption Mechanism

Redemptions create an automatic arbitrage loop that restores GREEN's peg whenever it trades below $1. For a detailed explanation of how redemptions work as a protective buffer, see [The Redemption Buffer](07-liquidations.md#the-redemption-buffer) in the liquidations documentation.

**The $1 Guarantee**:
- GREEN can always be redeemed for exactly $1 worth of collateral
- Targets only positions in the "Redemption Zone" (below redemption threshold)
- No committees, no voting, no delays — instant execution
- Creates a hard floor for GREEN's market price

**How Arbitrage Restores the Peg**:
```
GREEN trading at $0.97? Here's what happens:

1. Arbitrageurs spot the 3% discount
2. Buy 10,000 GREEN for $9,700 on the market
3. Instantly redeem for $10,000 worth of collateral
4. Profit: $300 risk-free
5. This buying pressure pushes GREEN back to $1
```

**Important Constraint**: Redemptions are only possible when positions exist in the Redemption Zone. During stable markets with healthy collateral ratios, direct redemptions may be unavailable.

This mechanism activates when market stress pushes positions toward liquidation, providing buying pressure precisely when GREEN needs support most.

### 4. Stability Pool Redemption Mechanism

A second powerful redemption path exists through [stability pools](05-stability-pools.md) that hold liquidated collateral:

**How Pool Redemptions Work**:
- Stability pools accumulate ETH, WBTC, and other assets from liquidations
- GREEN holders can redeem 1 GREEN for exactly $1 worth of pool assets
- **Availability Dependent**: Only possible when pools contain liquidated collateral
- Creates arbitrage opportunities during periods of liquidation activity

**Important Constraint**: Pool redemptions require the stability pools to hold collateral from recent liquidations. During calm markets with no liquidations, this redemption path may be unavailable.

**Complementary Redemption Paths**:
```
GREEN at $0.96? Potential redemption options:
1. Direct redemption (if positions in Redemption Zone)
2. Pool redemption (if liquidated collateral available)

Both paths subject to availability
```

**When Pool Redemptions Are Most Effective**:
- **Market Stress**: Liquidations increase, filling pools with collateral
- **Price Volatility**: More positions fail, creating redemption opportunities
- **Cascading Events**: Each liquidation enables more GREEN redemptions
- **Self-Balancing**: Redemptions occur precisely when GREEN needs support

### 5. Endaoment Treasury Operations

The [Endaoment](11-endaoment.md) serves as GREEN's financial fortress — a protocol-owned treasury with vast capabilities to defend the peg:

**Capital Arsenal from Bond Sales**:
- Bond proceeds provide stablecoin reserves for immediate deployment
- Treasury assets work 24/7 across DeFi earning yield
- Growing war chest ensures firepower during any market condition
- No reliance on external capital or emergency fundraising

**Automated Stabilizer System**:
```
The 50/50 Rule in Action:

GREEN below peg (pool >50% GREEN)?
→ Remove excess GREEN liquidity
→ Burn GREEN tokens permanently
→ Restore pool balance to support price

GREEN above peg (pool <50% GREEN)?
→ Mint new GREEN (tracked as debt)
→ Add liquidity to deepen markets
→ Restore pool balance to stabilize price
```

**Liquidity Management Powers**:
- **Multi-DEX Operations**: Deploy liquidity across Curve, Uniswap, Aerodrome simultaneously
- **Concentrated Positions**: Use Uniswap V3 or Aero Slipstream for capital-efficient price support
- **Partner Programs**: Mint GREEN paired with partner assets for deeper markets
- **Instant Rebalancing**: Move capital between pools in single transactions

**Strategic Market Making**:
- Can provide buy-side support when GREEN weak
- Can provide sell-side liquidity when GREEN strong
- Profits from spreads flow back to treasury
- Self-funded operations through yield generation

**Why This Matters**:
- **Deep Resources**: Treasury can mint GREEN when needed (always tracked as debt)
- **Multiple Fronts**: Operates across all major DEXes simultaneously
- **Always Active**: No governance votes or delays — instant response
- **Self-Strengthening**: Every intervention generates fees that grow the treasury

The Endaoment transforms from passive treasury to active market participant, with the resources and authority to maintain GREEN's peg against any market conditions.

## Additional GREEN Ecosystem Features

### Bad Debt Resolution
If extreme conditions create bad debt, the protocol can sell [bonds](10-bonds.md) to raise recovery funds. This mints RIPE beyond the 1B cap (e.g., becoming 1.001B), with dilution shared proportionally by all holders — ensuring GREEN always remains fully backed.

### Protocol-Wide Integration
- GREEN is the only borrowable asset in Ripe Protocol
- All liquidations settle in GREEN
- Fee flows strengthen the ecosystem
- Designed for maximum composability with DeFi

### [Keeper Network](06-liquidation-keepers.md) Protection
- Automated bots monitor all GREEN loans 24/7
- Trigger liquidations when positions become unsafe
- Keepers earn 0.1-0.5% rewards (paid in GREEN)
- Minimizes bad debt through rapid liquidation execution

## GREEN Throughout Ripe Protocol

### Transform to sGREEN for Automatic Yield

[sGREEN](04-sgreen.md) is GREEN's yield-bearing twin:
- **Set and Forget**: Deposit GREEN, receive sGREEN
- **Auto-Compounding**: Value grows through exchange rate, not rebasing
- **Protocol Revenue**: Captures fees from borrowing, liquidations, and more
- **Instant Liquidity**: Redeem for GREEN anytime
- **Use Everywhere**: Stability pools accept sGREEN for enhanced returns

### Participate in Stability Pools

Deploy sGREEN or GREEN LP tokens in [stability pools](05-stability-pools.md) for liquidation profits:
- **Triple Yield**: Base sGREEN rate + liquidation profits + RIPE rewards
- **Guaranteed Discounts**: Buy collateral 5-15% below market
- **Support Protocol**: Your deposits enable smooth liquidations
- **Flexible Withdrawal**: No lockups or penalties

### Enable Borrowing Options

When taking loans, receive GREEN flexibly:
- **Direct GREEN**: Standard stablecoin for any use
- **Auto-sGREEN**: Start earning immediately on borrowed funds
- **Stability Pool Entry**: Maximum yield from day one

### Earn RIPE Block Rewards

Multiple ways to earn [RIPE rewards](09-ripe-rewards.md) through GREEN:
- **Borrowing GREEN**: Larger, longer-term loans earn more rewards
- **Stability Pool Deposits**: sGREEN and GREEN LP deposits earn additional RIPE
- **Time-Weighted System**: Points accumulate based on position size × time
- **Offset Costs**: Rewards help reduce effective borrowing rates or boost stability pool returns

## GREEN vs The Competition: A Clear Winner

When you need to borrow stablecoins, GREEN offers fundamental advantages:

**vs Centralized Stables (USDC/USDT)**:
- Can't borrow USDC/USDT — you must buy them
- GREEN: Mint by borrowing against any asset you own
- Bonus: GREEN earns yield via sGREEN, USDC sits idle

**vs Traditional Crypto Stables (DAI/LUSD)**:
- DAI: Separate vaults for each collateral type
- LUSD: Only accepts ETH (or similar) as collateral
- GREEN: One loan backed by your entire portfolio

**vs Algorithmic Experiments (UST)**:
- No real backing = inevitable collapse
- GREEN: Every token 150%+ overcollateralized

**The Key Difference**: GREEN is built for borrowers who want to use their entire portfolio efficiently. Whether you hold ETH, stablecoins, NFTs, tokenized stocks or emerging tokens, everything works together to back a single, manageable loan position.

## Why This Matters

Every other stablecoin makes you choose: safety or efficiency, yield or liquidity, simplicity or power.

GREEN breaks the tradeoffs. One position backed by everything you own. Automatic yield that compounds while you sleep. Liquidation profits when others get rekt. A peg that defends itself through pure economics, not faith.

Stop settling for stablecoins designed for 2020. This is how money works in DeFi now.

---

*For technical implementation details, see the [GreenToken Technical Documentation](../technical/tokens/GreenToken.md).*