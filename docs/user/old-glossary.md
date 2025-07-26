# Glossary

## Core Terms

### Collateral
Assets deposited into Ripe Protocol vaults to secure borrowing positions. Includes cryptocurrencies, stablecoins, yield-bearing tokens, NFTs, and other supported assets.

### Debt
The amount owed to the protocol, consisting of principal (borrowed GREEN) plus accrued interest at current rates.

### Delegation
Permission system allowing third parties to perform specific actions on your behalf (borrow, withdraw, claim) while maintaining your ownership. All funds always return to the original owner.

### Endaoment
Ripe Protocol's treasury system that manages protocol assets, maintains GREEN stability through automated Curve pool management, and generates yield using Underscore Protocol's Lego adapters.

### GREEN
The protocol's native overcollateralized stablecoin, minted when users borrow against collateral and burned upon repayment or liquidation.

### GREEN LP
Liquidity provider tokens from GREEN/USDC pools. Can be deposited in stability pools and earns from the Stakers reward category.

### Keeper
Automated bots that trigger liquidations for profit. They monitor all positions 24/7 and execute liquidations instantly when thresholds are breached, earning 1-2% of liquidated debt.

### Position
A user's complete borrowing state including all deposited collateral, outstanding debt, and weighted-average parameters. Each address has one unified position.

### RIPE
The protocol's governance token. 1 billion total supply with 15% allocated to block rewards over ~5 years.

### RIPE LP
Liquidity provider tokens from RIPE pools. Receives 150% weight in governance and rewards compared to regular RIPE tokens.

### sGREEN
Savings GREEN - the yield-bearing version of GREEN that automatically appreciates through protocol revenue distribution. Used in stability pools for liquidation defense.

### Vault
Smart contracts that hold deposited collateral. Different vault types handle standard tokens, yield-bearing assets, NFTs, and special mechanisms like stability pools.

## Parameters

### Asset Weight
Multipliers applied to certain assets for reward calculations. RIPE has 100% weight, RIPE LP has 150% weight.

### Liquidation Threshold
The minimum collateral percentage required for your debt level. Works inversely - defines how much collateral you need. Example: 95% threshold means you need $105.26 collateral per $100 debt.

### Loan-to-Value (LTV)
Maximum borrowing capacity as a percentage of collateral value. 80% LTV means you can borrow up to $8,000 against $10,000 collateral.

### Lock Duration Bonus
Additional governance points earned by locking RIPE/RIPE LP longer. Scales from 0% (1 day) to 200% (3 years).

### Redemption Threshold
The collateralization level (e.g., 90%) where GREEN holders can redeem tokens for exactly $1 of collateral from at-risk positions, creating peg stability.

## Mechanisms

### Block Rewards
RIPE tokens distributed per block across four categories: Borrowers, Stakers, Vote Depositors, and General Depositors. Based on time-weighted point accumulation.

### Dutch Auction
Phase 3 liquidation where collateral starts at 5% discount and increases to 25% over hours. Anyone can buy portions instantly with GREEN (which gets burned).

### Dynamic Rate Protection
Interest rate multiplier (1.5x-3.0x) that activates when GREEN exceeds 60% of reference liquidity pools, plus time-based increases to restore peg.

### Liquidation
The three-phase process of repaying debt using collateral when positions fall below minimum requirements. Keepers trigger this instantly.

### Multi-Collateral System
Ripe's innovation allowing 10+ different assets to back a single loan with unified weighted-average parameters, unlike isolated lending requiring separate positions.

### Stability Pool
Pools holding sGREEN and GREEN LP tokens that instantly swap for liquidated collateral at 5-15% discounts. Participants earn yields plus RIPE staker rewards.

### Three-Phase Liquidation
Concurrent liquidation routing: Phase 1 (burns user's GREEN/sGREEN, transfers stables to Endaoment), Phase 2 (swaps with stability pools), Phase 3 (Dutch auctions).

### Unified Repayment Formula
Mathematical calculation determining exactly how much liquidation is needed to restore position health - nothing more, nothing less. Replaces fixed percentage liquidations.

## Asset Categories

### Blue-Chip Assets
Established cryptocurrencies with deep liquidity and proven track records (WETH, WBTC) receiving favorable parameters like 80%+ LTV.

### Exotic Assets
Higher-risk tokens like meme coins or new projects. Receive conservative parameters (30-50% LTV) to ensure protocol safety.

### Permissioned Assets
Tokens requiring whitelist access due to regulatory requirements (tokenized securities, real estate). Maintain compliance through liquidation.

### Yield-Bearing Assets
Tokens generating returns while serving as collateral (stETH, LP tokens, vault tokens). Yields accrue to depositors through share-based vault accounting.

## Reward Categories

### Borrowers
Users earning RIPE rewards based on debt amount × time borrowed. Incentivizes healthy borrowing activity.

### General Depositors
All vault deposits earn from this pool based on USD value × time. Universal category for fair cross-asset rewards.

### Stakers
RIPE/RIPE LP in governance vault and sGREEN/GREEN LP in stability pools earn from this category. Based on balance × time × asset weight.

### Vote Depositors
Future category for assets selected by governance voting. Currently inactive until full governance launches.

## Technical Terms

### Borrowing Power
Maximum GREEN mintable based on sum of (each collateral value × its LTV ratio). Determines position capacity.

### Debt Health
Position safety metric comparing current collateralization to liquidation threshold. Below 100% triggers liquidation eligibility.

### Governance Points
Accumulated score from locking RIPE/RIPE LP tokens. Calculated as balance × blocks × asset weight × lock bonus. Determines future voting power.

### Oracle Priority
Fallback system for price feeds: Chainlink → Pyth → Stork → DEX. Uses first available valid price without averaging.

### Points
Time-weighted accumulation units for reward distribution. Balance × blocks held = points. Converted to RIPE rewards based on category allocations.

### Ripe Governance Vault
Special vault where RIPE/RIPE LP tokens are time-locked to earn governance points and enhanced staker rewards.

### Weighted Average
Method calculating unified position parameters. Each asset's contribution weighted by its share of total borrowing power.

## Protocol Mechanisms

### Daowry Fee
One-time 0.5% origination fee on initial GREEN borrowed, paid to Endaoment treasury.

### Early Exit
Withdrawing from Ripe Governance Vault before lock expiry. Costs 80% of deposited tokens (forfeited to other depositors) and 100% slash of all governance points.

### Hightop Integration
Underscore Protocol feature requiring delegation permissions for advanced vault strategies and automated position management.

### Lego System
Underscore Protocol's modular DeFi adapters enabling Endaoment to deploy capital across yield strategies efficiently.

### Per-Asset Limits
Maximum deposits per user for risk management (e.g., $100k PEPE per address).

### Global Limits
Total protocol exposure caps for each asset (e.g., $10M PEPE system-wide).

### Pool Health
GREEN/USDC liquidity pool balance monitored for Dynamic Rate Protection. Above 60% GREEN triggers rate multipliers.

### Reference Pool
The GREEN/USDC liquidity pool monitored by Dynamic Rate Protection. When GREEN exceeds 60% of this pool, borrowing rate multipliers activate.

### Ripe Radness
Bonus multiplier system (up to 2x) for early testnet participants when purchasing bonds.

### Slash
Proportional reduction of governance points when withdrawing from governance vault. Withdraw 10% of tokens = lose 10% of points. Early exit = 100% slash.