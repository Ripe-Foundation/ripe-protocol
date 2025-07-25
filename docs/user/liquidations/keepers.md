# Keepers

Keepers are external participants who trigger various protocol operations in exchange for economic rewards. They form a decentralized network that maintains protocol health without central coordination.

## What Keepers Do

### Liquidation Execution

Keepers monitor all borrowing positions continuously:
- Identify positions that fall below liquidation thresholds
- Trigger liquidations immediately when eligible
- Process multiple positions in single transactions for efficiency
- Compete with other keepers for execution rights

### Rate Updates

The protocol allows keepers to update borrowing rates for any position:
- Refresh rates to current market conditions
- Apply dynamic rate adjustments based on pool health
- Update positions before liquidation for accurate calculations
- No permission required - anyone can update any position

### Auction Management

Keepers interact with the Dutch auction system:
- Start auctions for liquidated collateral after configured delays
- Pause active auctions when necessary
- Participate as buyers in auctions they didn't initiate
- Batch multiple auction operations for gas efficiency

## Economic Rewards

### Liquidation Compensation

Keepers earn a percentage of the debt they help resolve:
- **Base reward**: 1-2% of repaid debt amount
- **Minimum amount**: $50-100 ensures small position profitability
- **Maximum cap**: Limits prevent excessive rewards on large liquidations
- **Payment options**: Receive rewards as GREEN or sGREEN tokens

### Additional Value Capture

Beyond direct rewards, keepers often extract value through:
- Purchasing discounted collateral from triggered auctions
- Arbitrage between liquidation rewards and market prices
- Combining multiple protocol actions in single transactions
- Cross-protocol strategies involving Ripe liquidations

## Market Dynamics

### Competition Effects

Multiple keepers create an efficient market:
- Fastest execution wins the entire reward
- Competition drives liquidations within blocks of eligibility
- Geographic distribution ensures global coverage
- No single point of failure in the system

### Infrastructure Requirements

Professional keepers typically operate:
- Automated monitoring systems for position tracking
- Direct blockchain connections for speed
- Capital reserves for gas costs and purchases
- Risk management systems for volatile markets

### Economic Considerations

Keeper profitability depends on:
- Gas costs versus liquidation rewards
- Competition from other keepers
- Market volatility creating opportunities
- Network congestion affecting execution costs

## System Benefits

### Protocol Health

Keepers provide essential services:
- Immediate liquidation prevents bad debt accumulation
- Rate updates ensure accurate interest calculations
- Auction management maintains orderly collateral sales
- Decentralized execution removes operational risk

### Market Efficiency

The keeper system creates:
- Rapid response to market movements
- Competitive pricing through keeper competition
- 24/7 coverage without downtime
- Permissionless participation enabling innovation

## Becoming a Keeper

### Basic Requirements

Participating as a keeper requires:
- Understanding of the protocol's liquidation mechanisms
- Technical ability to monitor blockchain state
- Capital for gas costs and potential collateral purchases
- Risk tolerance for competitive environment

### Participation Levels

Different scales of keeper operation:
- **Individual**: Manual monitoring and execution
- **Semi-automated**: Scripts for specific opportunities
- **Professional**: Full automation with sophisticated strategies
- **Institutional**: Large-scale operations across multiple protocols

The keeper ecosystem ensures Ripe Protocol operates efficiently through economic incentives that align individual profit with system health. This decentralized approach creates a robust system that functions continuously without central control.