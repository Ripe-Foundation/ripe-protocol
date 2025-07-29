# Frequently Asked Questions

Quick answers to what actually matters.

## Getting Started

### What is Ripe Protocol?

One loan backed by everything you own. While other protocols make you juggle five vaults for five assets, Ripe combines your entire portfolio — crypto, tokenized stocks, blue-chip NFTs, everything — into ONE position. Borrow GREEN stablecoins against it all.

### What makes Ripe different from other lending protocols?

**One loan, many assets.** While other protocols force you to manage separate positions for each collateral type, Ripe lets you deposit multiple different assets that all work together to back a single GREEN loan. This means you can use your USDC, ETH, tokenized stocks, treasury bills, and even NFTs all in one [borrowing position](03-borrowing.md).

### What is GREEN?

[GREEN](01-green-stablecoin.md) is Ripe's overcollateralized stablecoin, always worth $1. Every GREEN is backed by at least 110% in collateral value (often much more). You create GREEN by borrowing against your deposited assets and destroy it by repaying your loan.

### Is my money safe?

Your [deposits](02-collateral-assets.md) back only your own loans — not a shared lending pool. If someone else's risky position fails, it doesn't affect you. The protocol uses multiple safety mechanisms including redemptions before [liquidations](07-liquidations.md), partial liquidations (not full), and a four-phase liquidation system designed to minimize losses.

## Borrowing Basics

### How much can I borrow?

Each asset has its own Loan-to-Value (LTV) ratio:

- **Stablecoins**: Up to 90% of value
- **ETH/WBTC**: Up to 70-80% of value
- **Volatile assets**: 30-50% of value

Your total [borrowing power](03-borrowing.md) combines all assets weighted by their individual LTVs.

### How do interest rates work?

You pay a single weighted-average rate based on your [collateral mix](02-collateral-assets.md). If you deposit mostly stablecoins (lower rates) with some ETH (medium rates), your rate will be closer to the stablecoin rate. Rates only change when you interact with your loan — existing borrowers aren't affected by market fluctuations unless they choose to update.

### What are dynamic rates?

Dynamic rates are an emergency mechanism that activates only when GREEN trades significantly below $1. Under normal conditions, you simply pay your weighted base rate. If GREEN exceeds 60% in liquidity pools (indicating oversupply), rates may temporarily increase to incentivize repayment and restore balance.

### Can I repay anytime?

Yes! There are no prepayment penalties, fixed terms, or lockups. Repay any amount at any time to reduce your debt and improve your position health.

## Managing Risk

### When do I get liquidated?

[Liquidation](07-liquidations.md) happens when your collateral value drops below the required minimum for your debt. There are three key thresholds to monitor:

1. **Max LTV (e.g., 70%)**: Your borrowing limit - cannot borrow more beyond this
2. **Redemption threshold (e.g., 80%)**: Early warning - GREEN holders can redeem against your position
3. **Liquidation threshold (e.g., 90%)**: Danger zone - automatic liquidation begins

**Quick Example**: With $6,000 debt and 90% liquidation threshold, you need at least $6,667 collateral ($6,000 ÷ 0.90). If collateral drops below this, liquidation starts.

Monitor your position and add collateral or repay debt before reaching these zones. For a visual guide showing all risk zones, see [How Thresholds Work Together](03-borrowing.md#how-thresholds-work-together-a-visual-guide).

### What's the difference between redemption and liquidation?

**Redemption** (happens first):

- No penalty or discount
- GREEN holders pay off your debt at exactly $1 value
- Helps you deleverage automatically
- Better outcome than liquidation

**Liquidation** (last resort):

- Incurs liquidation fees (5-15%)
- Four-phase process: Your own assets → Stability pools → Dutch auctions
- Only liquidates enough to restore health (partial, not full)

### How does partial liquidation work?

Ripe only liquidates the minimum amount needed to make your position healthy again — not your entire position. If you need 20% debt reduction to be safe, that's all that gets liquidated. You keep the rest of your collateral.

## Earning with Ripe

### What is sGREEN?

[sGREEN](04-sgreen.md) is yield-bearing GREEN that automatically captures protocol revenues. Your sGREEN balance stays the same while its GREEN value increases over time through:

- Borrower interest payments
- Origination fees from new loans
- Protocol revenue distributions

No staking or claiming needed — just hold and earn.

### How do stability pools work?

[Stability pools](05-stability-pools.md) hold sGREEN and GREEN LP tokens that get swapped for liquidated collateral at discount. As a depositor, you:

- Continue earning sGREEN yield
- Get liquidated collateral at 5-15% discount
- Earn RIPE rewards
- Can withdraw anytime

It's like being a liquidator without running any bots.

### How do I earn RIPE rewards?

[RIPE rewards](06-ripe-rewards.md) currently flow to two groups (90% stakers, 10% borrowers):

1. **Stakers (90%)**: 
   - GREEN LP: 65% of staker rewards (best returns!)
   - RIPE LP: 15% of staker rewards
   - sGREEN: 10% of staker rewards
   - RIPE: 10% of staker rewards
2. **Borrowers (10%)**: Based on debt size and duration

Future categories (not active yet): General depositors and vote-selected assets.

**Important**: Current emissions are ramping up from 0.0025 RIPE/block to target 100 RIPE/block. When claiming rewards, 75% auto-stakes with a 1-year lock.

## GREEN Stability

### How does GREEN maintain its $1 peg?

Five mechanisms work together:

1. **Overcollateralization**: Every GREEN backed by 110%+ collateral
2. **Dynamic rates**: Borrowing costs increase if GREEN weakens
3. **Direct redemption**: Arbitrageurs can always redeem GREEN for $1 of collateral
4. **Stability pool redemption**: Additional redemption path through liquidated collateral
5. **[Endaoment](11-endaoment.md) operations**: Treasury automatically rebalances liquidity pools

### What happens if GREEN trades below $1?

Arbitrageurs immediately profit by:

1. Buying GREEN cheap (e.g., $0.97)
2. Redeeming for exactly $1 of collateral
3. Pocketing the difference

This creates instant buying pressure that pushes GREEN back to $1.

### Can GREEN lose its peg permanently?

The protocol's design makes this extremely unlikely. As long as loans remain overcollateralized, arbitrage mechanisms ensure GREEN returns to $1. The worse the depeg, the bigger the profit opportunity for arbitrageurs to fix it.

## Advanced Features

### Can I use yield-bearing tokens as collateral?

Yes! Tokens like stETH, aTokens, and LP positions continue earning their underlying yields while serving as collateral. The protocol uses share-based accounting to capture all rewards, rebases, and fee accruals.

### Can I use tokenized real-world assets?

Yes! Ripe is built for the $16 trillion in real-world assets being tokenized by 2030. Tokenized stocks, real estate, treasury bills, gold — if it has value, you can borrow against it. This is the core vision: unlocking liquidity for assets that traditional DeFi ignores.

### What's the delegation system?

You can grant specific permissions to other addresses:

- **Deposit permission**: Let others add collateral for you
- **Borrow permission**: Enable automated leverage strategies
- **Withdraw permission**: Allow rebalancing

Delegates can never steal funds — withdrawals always go to the original owner.

### Can I use my borrowed GREEN to earn yield?

Absolutely! When borrowing, you can:

- Receive GREEN directly for any use
- Auto-convert to sGREEN to start earning immediately
- Deposit straight to stability pools for maximum yield

Many users borrow at 5% to earn 8%+ in sGREEN.

## Governance & RIPE Token

### What is RIPE?

RIPE is the protocol's [governance](08-governance.md) token. Lock it in the governance vault to:

- Accumulate voting power for future governance
- Earn rewards from the staker allocation
- Get up to 3x rewards with longer lock periods

### When does governance go live?

Governance points are accumulating now, but on-chain voting hasn't launched yet. Governance will activate once sufficient RIPE tokens have been distributed through block rewards and the holder base has grown to ensure decentralized decision-making. Early participants who lock RIPE are building voting power that will control the protocol when governance activates.

### What's the RIPE token distribution?

1 billion RIPE total supply:
- **25%** Community incentives (only allocation unlocking at TGE)
- **22.2%** Ripe Foundation treasury
- **20.6%** Core contributors (locked 1 year, then 4-year vest)
- **17.2%** Early backers ($550k seed at $0.02)
- **15%** Distribution partner (Hightop)

All vesting happens on-chain with transparent contracts. See full details in [RIPE Tokenomics](09-tokenomics.md).

### What are Ripe Bonds?

[Bonds](10-bonds.md) let you exchange stablecoins (like USDC) for RIPE tokens at dynamic prices. Lock your bonded RIPE for up to 3 years to get up to 3x more tokens. All proceeds build the [Endaoment](11-endaoment.md) treasury that backs GREEN and generates protocol revenue.

### What are Bond Boosters?

Bond Boosters multiply your bond allocation based on ecosystem contributions (like testnet participation). They work through a unit system:
- 1 unit = 1 USDC of boost capacity
- Units are consumed permanently when bonding
- Example: 1,000 units + 200% booster = first 1,000 USDC bonded gets 3x RIPE

Combined with lock bonuses, top contributors can get up to 5x multipliers.

### What's the Endaoment?

The [Endaoment](11-endaoment.md) is Ripe's treasury system that combines automated mechanisms with strategic oversight. It:

- Manages protocol-owned liquidity from bond sales
- Generates yield across DeFi via Underscore Protocol
- Defends GREEN's peg through market operations
- Funds operations without token inflation

All bond proceeds become permanent productive capital working 24/7.

## Safety & Security

### What are the main risks?

- **Smart contract risk**: Bugs could affect funds
- **Liquidation risk**: Collateral value dropping too fast
- **Oracle risk**: Incorrect price feeds (mitigated by multiple sources)
- **Interest rate risk**: Dynamic rates during market stress

### Is Ripe audited?

ChainSecurity reviewed the code last year, but lessons from Underscore and real-world usage in Hightop pushed us to refactor. We removed onchain governance, Juice Score, NFTs, GREEN bonds, and complex DeFi adapters. The slimmer v1 launching today has not yet been re-audited — please keep this in mind when deciding position sizes.

### How does Ripe price assets accurately?

Ripe uses a [multi-oracle system](12-price-oracles.md) with automatic fallback. We check Chainlink, Pyth, Stork, and Curve in priority order, taking the first valid price. If one oracle fails, we instantly switch to the next — no manual intervention needed. This prevents single points of failure that have destroyed other protocols.

### How does Ripe handle bad debt?

The protocol has multiple defenses:

1. Conservative collateral ratios
2. Redemption mechanism before [liquidation](07-liquidations.md)
3. [Stability pools](05-stability-pools.md) absorb liquidations
4. Keeper network ensures fast execution
5. [Endaoment](11-endaoment.md) treasury as final backstop

If bad debt does occur, the protocol can sell [bonds](10-bonds.md) to raise funds. This creates RIPE tokens beyond the 1 billion cap (e.g., if 1M RIPE covers bad debt, total supply becomes 1.001 billion). The extra minting dilutes all RIPE holders proportionally, distributing the cost fairly while ensuring the protocol remains solvent.

### What happens in a market crash?

During extreme volatility:

- Redemptions help positions deleverage automatically
- Stability pools provide instant liquidation liquidity
- Partial liquidations minimize user losses
- Dynamic rates incentivize debt repayment
- Multiple oracle sources prevent manipulation

## Getting Help

### Where can I learn more?

- **[Documentation](README.md)**: Detailed guides in our docs
- **[Discord](https://discord.gg/Y6PWmndNaC)**: Active community and team support
- **[Twitter](https://x.com/ripe_dao)**: Protocol updates and announcements
- **[GitHub](https://github.com/Ripe-Foundation/ripe-protocol)**: Open source code and development
- **[Homepage](https://www.ripe.finance/)**: Ripe Homepage

### How do I report bugs or issues?

Security issues: Please report privately to ripefinance@proton.me
General bugs: Open an issue on GitHub or report in Discord

---

_This FAQ covers common questions. For detailed technical information, see our comprehensive documentation._
