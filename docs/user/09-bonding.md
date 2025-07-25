# Ripe Bonds

Ripe Bonds provide an open marketplace where anyone can exchange their stablecoins for RIPE tokens at dynamic, market-driven prices. This decentralized mechanism allows users to acquire RIPE while simultaneously helping the protocol build Endaoment reserves and liquidity for the GREEN stablecoin.

## Open Participation

**Anyone can participate** in Ripe Bonds:
- No whitelist or special permissions required
- Market-driven pricing responds to user demand
- Users decide when and how much to bond
- Transparent pricing visible to all participants

## Token Allocation

**15% of total RIPE supply is allocated to bonding programs** (150 million RIPE tokens from the 1 billion total supply). This allocation enables the protocol to acquire strategic assets and build treasury reserves while distributing RIPE tokens to committed participants.

## Bond Mechanism

The bond system operates through:
- **Token Exchange**: Stablecoins convert to RIPE tokens
- **Dynamic Pricing**: Rates vary based on epoch parameters
- **Lock Options**: Additional tokens awarded for time commitments
- **Treasury Routing**: All proceeds flow to the [Endaoment](06-endaoment.md)

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
- **Supply Control**: Limited tokens per epoch manage distribution
- **Treasury Growth**: Direct capital accumulation

## Bond Mechanics

### Epoch System

Bonds are sold in **epochs** (time periods):
- Each epoch has limited availability
- Once sold out, new epoch may start
- Prevents unlimited token distribution
- Creates fair access for all users

**Epoch Parameters:**
- Duration: Configurable time periods (e.g., 24 hours)
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

The protocol rewards users who commit to locking their bonded RIPE in the [Ripe Governance Vault](08-ripe-governance.md) with percentage-based bonuses:

**How Lock Boosts Work:**
- Lock boosts are percentages added to your base bond amount
- Locked tokens are deposited into the Ripe Governance Vault
- Example: 200% boost = 2x additional RIPE (3x total including base)
- Formula: Total RIPE = Base Amount + (Base Amount × Lock Boost %)

**Boost Structure:**
- No lock: 0% boost (1x total - base only)
- Short-term locks: 10-25% boost (1.1x-1.25x total)
- Medium-term locks: 25-50% boost (1.25x-1.5x total)
- Maximum 3-year lock: 200% boost (3x total)

**Lock Mechanics:**
- Maximum lock duration: 3 years
- Lock boost increases proportionally with duration
- All locked tokens automatically deposit into [Ripe Governance Vault](08-ripe-governance.md)
- Locked tokens earn governance points and staker rewards
- Voting power remains active throughout lock period
- Automatic release at lock expiration
- Boost percentages adjust via governance proposals

### Ripe Radness Bond Booster

The protocol rewards early testnet participants with additional percentage-based bonuses:

**How Radness Boosts Work:**
- Radness boosts are percentages added to your base bond amount
- Works identically to lock boosts: adds extra RIPE based on base amount
- Example: 200% radness boost = 2x additional RIPE
- Formula: Radness Bonus = Base Amount × Radness Boost %

**Boost Mechanism:**
- Testnet participants receive percentage-based bonus (e.g., 200%)
- Boost applies to base bond amount before any other multipliers
- Stacks additively with lock duration boosts
- Example: 200% lock + 200% radness = 400% total boost (5x total RIPE)

**Boost Parameters:**
- Eligibility: Testnet participation record (Discord roles)
- Magnitude: Governance-set percentage (typically 200% of base)
- Capacity: Maximum applicable units per user
- Expiration: Specific block number deadline

**System Properties:**
- Non-transferable boost allocation
- Automatic application during bond purchase
- One-time usage up to unit limit
- No renewal after expiration

### Complete Bonding Example

**Scenario**: Alice (a testnet participant) wants to bond $1,000 USDC

**Step 1 - Base Bond Calculation:**
- Bond price: $0.50 per RIPE
- Base RIPE amount: $1,000 ÷ $0.50 = 2,000 RIPE

**Step 2 - Lock Duration Bonus (3-year maximum lock):**
- Lock boost: 200% of base amount
- Lock bonus RIPE: 2,000 × 200% = 4,000 RIPE
- Subtotal: 2,000 + 4,000 = 6,000 RIPE

**Step 3 - Ripe Radness Boost (for testnet participants):**
- Radness boost: 200% of base amount
- Radness bonus: 2,000 × 200% = 4,000 RIPE
- Final total: 6,000 + 4,000 = 10,000 RIPE

**Summary:**
- Alice bonds: $1,000 USDC
- Alice receives: 10,000 RIPE (locked for 3 years)
- Effective price: $0.10 per RIPE (80% discount from $0.50)
- Total boost: 400% (base 100% + lock 200% + radness 200% = 500% total)

## Bad Debt Consideration

When the protocol has bad debt from liquidations:
- **You receive your full RIPE allocation** - bad debt doesn't reduce your bond payout
- Your USDC payment is used to pay off the bad debt
- Protocol tracks how much RIPE was "sold" to cover this debt
- **Additional RIPE is minted beyond the 1 billion cap** to account for debt coverage
- This dilutes all RIPE holders proportionally

**How It Works:**
- Bond payments: USDC goes to pay off bad debt
- RIPE payout: Full amount as calculated (no reduction)
- Supply impact: Total RIPE supply can exceed 1B by the debt amount
- Dilution effect: All RIPE holders share the cost through dilution
- Transparency: Additional minted RIPE is tracked on-chain

## Bond Proceeds to Endaoment

All stablecoins from bond sales flow directly to the [Endaoment](06-endaoment.md), Ripe Protocol's treasury and liquidity management system:

**How Bond Proceeds Are Used:**
- **Yield Generation**: Deployed across DeFi strategies via Underscore Protocol
- **GREEN Stability**: Maintains stablecoin peg through market operations
- **Liquidity Depth**: Creates deeper markets for protocol tokens
- **Emergency Reserves**: Provides backstop during market stress

**Value Creation:**
- Bond sales build protocol-owned liquidity
- Treasury yields support protocol operations
- Capital accumulation strengthens GREEN backing
- Sustainable funding without token inflation

The bond system transforms user capital into productive protocol resources, with the Endaoment actively managing these assets to support GREEN stability and generate returns for the protocol.

For technical implementation details, see [BondRoom Technical Documentation](technical/core/BondRoom.md).