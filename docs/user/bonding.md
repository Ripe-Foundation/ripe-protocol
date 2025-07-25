# Ripe Bonds

Ripe Bonds are a protocol mechanism that exchanges stablecoins for RIPE tokens at dynamic prices. This system builds Endaoment reserves and liquidity for the GREEN stablecoin.

## Bond Mechanism

The bond system operates through:
- **Token Exchange**: Stablecoins convert to RIPE tokens
- **Dynamic Pricing**: Rates vary based on epoch parameters
- **Lock Options**: Additional tokens awarded for time commitments
- **Treasury Routing**: All proceeds flow to the [Endaoment](endaoment.md)

## Bond Economics

### Treasury Impact

Bonds create a capital formation mechanism for the protocol:

**Capital Flow:**
1. Bond purchases convert stablecoins to treasury assets
2. Treasury deploys capital to:
   - GREEN/stablecoin liquidity pools
   - Yield-generating strategies
   - Reserve holdings
   - Peg stability operations

**Alternative Mechanisms:**
- Fee accumulation (gradual treasury growth)
- Token emissions (dilutive funding)
- External investment (centralized dependencies)

### Economic Design

The bond system creates value through:
- **Price Discovery**: Market-based token valuation
- **Time Incentives**: Lock bonuses reward commitment
- **Activity Recognition**: Protocol usage affects pricing
- **Treasury Growth**: Direct capital accumulation

## Bond Mechanics

### Epoch System

Bonds are sold in **epochs** (time periods):
- Each epoch has limited availability
- Once sold out, new epoch may start
- Prevents unlimited token distribution
- Creates fair access for all users

**Epoch Parameters:**
- Duration: Configurable time periods (e.g., 7 days)
- Availability: Limited token allocation per epoch
- Price Range: Minimum and maximum RIPE per dollar
- Progress Tracking: Real-time availability updates

### Dynamic Pricing

Within each epoch, prices follow a curve:
- **Start of epoch**: Higher price (less discount)
- **End of epoch**: Lower price (more discount)
- **Linear decrease**: Predictable pricing

This mechanism creates:
- Availability certainty at epoch start
- Progressive discount incentives
- Transparent pricing throughout

### Lock-Up Multipliers

The protocol implements time-based bonuses through governance-controlled multipliers:

**Multiplier Structure:**
- No lock: Base rate (1x)
- Short-term locks: Minor multipliers (e.g., 1.1x-1.25x)
- Medium-term locks: Moderate multipliers (e.g., 1.25x-1.5x)
- Long-term locks: Maximum multipliers (e.g., 1.5x-2x)

**Lock Mechanics:**
- Tokens transfer to governance vault during lock period
- Voting power remains active throughout lock
- Automatic release at lock expiration
- Multipliers adjust via governance proposals

### Ripe Radness Mechanism

The protocol recognizes early testnet participation through the Ripe Radness system:

**Mechanism Design:**
- Testnet participants receive bonus multipliers
- Configurable boost ratios (e.g., 2x base amount)
- Unit limits cap total boost usage
- Block-based expiration ensures time bounds
- Multipliers stack with lock bonuses

**Boost Parameters:**
- Eligibility: Testnet participation record
- Magnitude: Governance-set multiplier
- Capacity: Maximum applicable units
- Expiration: Specific block number

**System Properties:**
- Non-transferable boost allocation
- Automatic application during bond purchase
- One-time usage up to unit limit
- No renewal after expiration

## Bond Calculation Mechanics

The protocol determines bond payouts through:

**Base Calculation:**
- Payment amount divided by current epoch price
- Results in base RIPE allocation

**Multiplier Application:**
- Lock multiplier applied to base amount
- Ripe Radness boost (if eligible) applied to base
- Multipliers combine additively or multiplicatively per configuration

**Final Distribution:**
- Total RIPE calculated from all multipliers
- Lock duration determines vault routing
- Immediate distribution for unlocked tokens
- Governance vault custody for locked tokens

## Bad Debt Consideration

If the protocol has bad debt from liquidations:
- Your full payment still goes to the treasury
- Part of your RIPE payout is allocated to clear bad debt
- You receive fewer RIPE tokens proportionally
- Helps maintain protocol solvency
- Temporary until debt is cleared

**Bad Debt Allocation:**
- Payment amounts: Full value to treasury
- RIPE allocation: Proportional reduction for debt coverage
- Debt clearing: Automatic via reduced distribution
- Calculation: Debt percentage applied to payout

## Treasury Capital Flow

Bond proceeds create systematic protocol improvements:

**Capital Deployment:**
- Direct treasury funding from bond sales
- Yield strategy allocation for returns
- Annual revenue generation from deployed capital

**Liquidity Formation:**
- Capital enables liquidity pool creation
- Trading depth increases with treasury size
- Price stability improves through deeper markets

**Ecosystem Effects:**
- Treasury strength correlates with protocol stability
- Liquidity depth affects user capacity
- Protocol growth influences token dynamics

## Bond System Architecture

The bond mechanism creates:

**Economic Exchange**: Stablecoin capital converts to protocol tokens at market-discovered rates

**Time Flexibility**: Lock duration options with corresponding multipliers

**Treasury Growth**: Direct capital accumulation for protocol operations

**Transparent Pricing**: Epoch-based systems with clear parameters

**Sustainable Funding**: Non-dilutive capital formation through voluntary exchange

The bond system transforms external capital into protocol resources, establishing treasury reserves that support GREEN stability and protocol operations through market-based token distribution.

For technical implementation details, see [BondRoom Technical Documentation](../technical/core/BondRoom.md).