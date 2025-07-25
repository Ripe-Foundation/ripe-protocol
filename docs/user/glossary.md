# Glossary

## Core Terms

### Collateral
Assets deposited into Ripe Protocol to secure borrowing positions. Can include cryptocurrencies, stablecoins, yield-bearing tokens, and other supported assets.

### Debt
The total amount owed to the protocol, consisting of principal (borrowed amount) and accrued interest.

### Endaoment
Ripe Protocol's treasury system that manages protocol assets, maintains GREEN stability, and generates yield through DeFi strategies.

### GREEN
The protocol's native overcollateralized stablecoin, minted when users borrow and burned upon repayment.

### Keeper
External actors who execute protocol operations (liquidations, rate updates, auctions) in exchange for economic rewards.

### Position
A user's complete borrowing state including all deposited collateral, outstanding debt, and associated parameters. One user has one position.

### sGREEN
Savings GREEN - the yield-bearing version of GREEN that automatically accrues value through protocol revenue distribution.

## Parameters

### Liquidation Threshold
The collateralization ratio at which a position becomes eligible for liquidation. Higher percentages mean tighter requirements (e.g., 95% threshold = 105.3% minimum collateralization).

### Loan-to-Value (LTV)
The maximum percentage of collateral value that can be borrowed. Determines initial borrowing capacity (e.g., 80% LTV = can borrow up to 80% of collateral value).

### Redemption Threshold
The collateralization level where GREEN holders can redeem tokens against positions at par value, before liquidation becomes possible.

## Mechanisms

### Dutch Auction
A declining price auction where collateral starts at a small discount and progressively becomes cheaper until purchased.

### Dynamic Rate Protection
Automated interest rate adjustments based on market conditions to maintain GREEN's dollar peg.

### Liquidation
The process of selling collateral to repay debt when positions become undercollateralized.

### Multi-Collateral System
Ripe's architecture allowing multiple asset types to back a single borrowing position with weighted-average terms.

### Stability Pool
Liquidity pools holding sGREEN that can instantly swap for liquidated collateral at predetermined discounts.

### Three-Phase Liquidation
The progressive liquidation system: Phase 1 (burns/transfers), Phase 2 (stability pools), Phase 3 (auctions).

## Asset Categories

### Blue-Chip Assets
Established cryptocurrencies with deep liquidity and proven track records (e.g., WETH, WBTC).

### Permissioned Assets
Tokens requiring whitelist access due to regulatory requirements (e.g., tokenized securities).

### Yield-Bearing Assets
Tokens that generate returns while serving as collateral (e.g., stETH, LP tokens).

## Technical Terms

### Borrowing Power
Maximum GREEN mintable based on aggregate collateral value and loan-to-value ratios.

### Debt Health
Metric indicating position safety relative to liquidation thresholds.

### Weighted Average
Method of calculating unified position parameters based on each asset's proportional contribution to borrowing power.

### Daowry Fee
One-time origination fee charged when creating new borrowing positions.

### Pool Health
Measure of GREEN/USDC liquidity pool balance used by Dynamic Rate Protection to adjust borrowing rates.

### Ripe Radness
Bonus multiplier system for early testnet participants when purchasing bonds.

### Lego System
Underscore Protocol's modular DeFi adapters used by the Endaoment for yield generation.