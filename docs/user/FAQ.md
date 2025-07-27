# Frequently Asked Questions

## Getting Started

### What is Ripe Protocol?

Ripe is a DeFi lending protocol where you can borrow GREEN stablecoins using your entire crypto portfolio as collateral. Unlike traditional lending where each asset needs its own loan, Ripe combines everything — from ETH to stablecoins to meme coins — into one unified position with a single interest rate and health factor to monitor.

### What makes Ripe different from other lending protocols?

**One loan, many assets.** While other protocols force you to manage separate positions for each collateral type, Ripe lets you deposit 10+ different assets that all work together to back a single GREEN loan. This means you can use your USDC, ETH, PEPE, and even NFTs all in one [borrowing position](03-borrowing.md).

### What is GREEN?

[GREEN](01-green-stablecoin.md) is Ripe's overcollateralized stablecoin, always worth $1. Every GREEN is backed by at least 110% in collateral value (often much more). You create GREEN by borrowing against your deposited assets and destroy it by repaying your loan.

### Is my money safe?

Your [deposits](02-collateral-assets.md) back only your own loans — not a shared lending pool. If someone else's risky position fails, it doesn't affect you. The protocol uses multiple safety mechanisms including redemptions before [liquidations](06-liquidations.md), partial liquidations (not full), and a three-phase liquidation system designed to minimize losses.

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

[Liquidation](06-liquidations.md) happens when your collateral value drops below the required minimum for your debt. Key thresholds:
- **Max LTV**: Your borrowing limit
- **Redemption threshold**: Others can swap GREEN for your collateral at par
- **Liquidation threshold**: Forced liquidation begins

Monitor your position and add collateral or repay debt before reaching these zones.

### What's the difference between redemption and liquidation?

**Redemption** (happens first):
- No penalty or discount
- GREEN holders pay off your debt at exactly $1 value
- Helps you deleverage automatically
- Better outcome than liquidation

**Liquidation** (last resort):
- Incurs liquidation fees (5-15%)
- Three-phase process to minimize impact
- Only liquidates enough to restore health

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

[RIPE rewards](07-ripe-rewards.md) flow to four groups:
1. **Borrowers**: Based on debt size and duration
2. **Stakers**: RIPE/LP in governance vault, sGREEN/LP in stability pools
3. **General Depositors**: All collateral deposits earn baseline rewards
4. **Vote Depositors**: Future governance-selected assets

Rewards accumulate every block based on your position size and time held.

## GREEN Stability

### How does GREEN maintain its $1 peg?

Five mechanisms work together:
1. **Overcollateralization**: Every GREEN backed by 110%+ collateral
2. **Dynamic rates**: Borrowing costs increase if GREEN weakens
3. **Direct redemption**: Arbitrageurs can always redeem GREEN for $1 of collateral
4. **Stability pool redemption**: Additional redemption path through liquidated collateral
5. **[Endaoment](10-endaoment.md) operations**: Treasury automatically rebalances liquidity pools

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

### What are Ripe Bonds?

[Bonds](09-bonds.md) let you exchange stablecoins (like USDC) for RIPE tokens at dynamic prices. Lock your bonded RIPE for up to 3 years to get up to 3x more tokens. All proceeds build the [Endaoment](10-endaoment.md) treasury that backs GREEN and generates protocol revenue.

### What's the Endaoment?

The [Endaoment](10-endaoment.md) is Ripe's autonomous treasury system. It:
- Manages protocol-owned liquidity
- Generates yield across DeFi
- Defends GREEN's peg automatically
- Funds operations without token inflation

Think of it as an AI treasurer that never sleeps.

## Safety & Security

### What are the main risks?

- **Smart contract risk**: Bugs could affect funds (mitigated by audits)
- **Liquidation risk**: Collateral value dropping too fast
- **Oracle risk**: Incorrect price feeds (mitigated by multiple sources)
- **Interest rate risk**: Dynamic rates during market stress

### How does Ripe handle bad debt?

The protocol has multiple defenses:
1. Conservative collateral ratios
2. Redemption mechanism before [liquidation](06-liquidations.md)
3. [Stability pools](05-stability-pools.md) absorb liquidations
4. Keeper network ensures fast execution
5. [Endaoment](10-endaoment.md) treasury as final backstop

If bad debt does occur, the protocol can sell [bonds](09-bonds.md) to raise funds. This creates RIPE tokens beyond the 1 billion cap (e.g., if 1M RIPE covers bad debt, total supply becomes 1.001 billion). The extra minting dilutes all RIPE holders proportionally, distributing the cost fairly while ensuring the protocol remains solvent.

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
- **[Homepage](https://www.ripe.finance/)**: Ripe Homepage

### How do I report bugs or issues?

Security issues: Please report privately to ripefinance@proton.me
General bugs: Open an issue on GitHub or report in Discord

---

*This FAQ covers common questions. For detailed technical information, see our comprehensive documentation.*