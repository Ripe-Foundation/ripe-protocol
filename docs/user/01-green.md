# GREEN Stablecoin

GREEN is Ripe Protocol's native stablecoin—a decentralized, overcollateralized digital dollar designed to maintain a stable value while providing the benefits of DeFi composability. Unlike algorithmic stablecoins that rely on complex mechanisms, GREEN's value comes from real collateral backing every unit in circulation.

## What Makes GREEN Different

### Born from Loans, Not Algorithms

Every GREEN token in existence was minted through a collateralized loan:
- No pre-mine or initial distribution
- No algorithmic expansion/contraction
- Supply grows with actual borrowing demand
- Burns upon repayment, maintaining balance

### Overcollateralized Security

GREEN maintains its peg through robust collateral requirements:
- Minimum 110% backing (often much higher)
- [Multiple asset types](collateral-assets/multi-collateral-system.md) provide diversification
- Real value locked in smart contracts
- Transparent on-chain verification

### Multiple Stability Mechanisms

The protocol employs several layers to maintain GREEN's $1 peg:

1. **[Dynamic Interest Rates](borrowing/dynamic-rate-protection.md)**: Borrowing costs adjust to influence supply
2. **[Stability Pools](liquidations/stability-pool-mechanics.md)**: Provide liquidity during market stress
3. **[Direct Redemptions](liquidations/README.md#pre-liquidation-protection)**: Exchange GREEN for collateral at par
4. **[Endaoment](06-endaoment.md) Operations**: Treasury actions support peg
5. **[Liquidation Mechanisms](liquidations/README.md)**: Remove bad debt before it impacts peg

## How GREEN is Created

### The Minting Process

1. **Deposit Collateral**: Users lock assets in [Ripe vaults](collateral-assets/asset-parameters.md#the-vault-system)
2. **Borrow Request**: Choose how much GREEN to mint
3. **Collateral Check**: Protocol verifies sufficient backing
4. **GREEN Minted**: New tokens created and sent to user
5. **Debt Recorded**: Loan tracked on-chain

### Example Creation

Alice wants to borrow $5,000:
- Deposits: 5 WETH (worth $10,000)
- LTV Limit: 80%
- Maximum Borrow: $8,000
- Alice Borrows: $5,000 GREEN
- Collateralization: 200%

The protocol mints exactly 5,000 GREEN for Alice's loan.

## How GREEN is Destroyed

### The Burning Process

When loans are repaid:
1. **Repayment Initiated**: User sends GREEN to protocol
2. **Debt Reduction**: Principal and interest calculated
3. **GREEN Burned**: Tokens permanently destroyed
4. **Collateral Released**: Proportional to repayment

This ensures GREEN supply contracts as demand decreases.

## GREEN's Stability Features

### 1. Dynamic Interest Rate Adjustment

The protocol continuously monitors market conditions and adjusts borrowing rates in real-time based on liquidity pool health. This creates economic incentives that help maintain GREEN's peg without manual intervention.

**How Pool Health Monitoring Works**:
- **Reference Pool**: Monitors GREEN/USDC liquidity pool as market health indicator
- **Weighted Calculation**: Considers pool depth, volume, and time-weighted prices to prevent manipulation
- **Danger Threshold**: Rates begin increasing when GREEN exceeds 60% of pool
- **Progressive Response**: Proportional scaling based on imbalance severity - the worse it gets, the higher rates go

**How Rates Adjust**:
- Below 60% GREEN: Normal rates (no multiplier)
- Above 60% GREEN: Progressive multiplier increases continuously
- Multiplier range: 1.5x to 3.0x based on imbalance severity
- The worse the imbalance, the higher the multiplier

**Three-Layer Response System**:
1. **Ratio Boost**: Multiplier based on pool imbalance severity (scales between min/max)
2. **Time Boost**: Additional rate increase per block in danger zone (+0.1% per 1000 blocks)
3. **Rate Caps**: Maximum rate protection (e.g., 50% APR)

**Example with pool at 70% GREEN for 5,000 blocks**:
- Base rate: 5% APR
- Ratio boost: 5% × 2.25x = 11.25% APR
- Time boost: +0.5% APR (0.1% × 5)
- Total rate: 11.75% APR (capped at maximum if exceeded)

This multi-layer system ensures immediate response to imbalances while creating increasing urgency for sustained stress.

For complete details on this system, see [Dynamic Rate Protection](borrowing/dynamic-rate-protection.md).

### 2. Direct Redemption Mechanism

When GREEN trades below $1, holders can directly redeem:
- **Redemption Threshold**: Only targets users within redemption risk zone (approaching liquidation)
- **Risk-Based Priority**: Redeems from riskiest positions first, not arbitrary users
- **Protection for Healthy Loans**: Well-collateralized positions cannot be redeemed against
- **$1 Value Guarantee**: Always redeem GREEN for exactly $1 of collateral
- **Arbitrage Restoration**: Creates profitable opportunities that restore peg

**Important**: Redemptions only affect users whose debt health has deteriorated significantly. If your position is well-collateralized, you cannot be targeted for redemption.

For more details on redemptions, see [Pre-Liquidation Protection](liquidations/README.md#pre-liquidation-protection).

### 3. Stability Pool Defense

Specialized pools that maintain peg stability:
- **First Line Defense**: Absorb liquidated collateral before other mechanisms
- **Instant Liquidity**: Provide immediate GREEN when needed
- **Fee Incentives**: Earn rewards for defending the peg
- **Depositor Protection**: Pool participants share in liquidation profits
- **Automatic Activation**: Engage without manual intervention

**Collateral Redemption Mechanism**: 
When stability pools accumulate liquidated collateral, any GREEN holder can redeem their GREEN for these assets at $1 par value. The pool then holds the redeemed GREEN instead of the collateral, maintaining the same total value. This creates a stabilization mechanism - when GREEN is under peg, arbitrageurs can:
1. Buy discounted GREEN on the market (e.g., at $0.95)
2. Redeem it for exactly $1 worth of collateral from stability pools
3. This buying pressure helps restore the peg

Learn more about [Stability Pool Mechanics](liquidations/04-stability-pool-mechanics.md).

### 4. Endaoment Stabilizer

The protocol treasury actively manages stability:
- **Market Operations**: Can mint/burn GREEN based on specific conditions
- **Collateral Management**: Deploys treasury assets to support peg
- **Emergency Response**: Authorized to take rapid action during extreme events
- **Programmatic Rules**: Operates within pre-defined parameters
- **Transparent Actions**: All operations visible on-chain

For details on treasury operations, see [The Endaoment](06-endaoment.md).

## GREEN vs Other Stablecoins

### Versus USDC/USDT
**Centralized Stablecoins**:
- Backed by bank dollars
- Require trust in companies
- Can be frozen or seized
- Limited transparency

**GREEN**:
- Backed by crypto collateral
- Decentralized issuance
- No custodial risk
- Complete transparency

### Versus USDS (formerly DAI)
**Sky (formerly MakerDAO)**:
- Single protocol risk
- Complex governance
- Limited collateral types
- Isolated positions

**GREEN**:
- Multi-collateral innovation (single loan)
- Streamlined mechanics
- Expanding asset support
- Unified positions

### Versus Algorithmic Stables
**LUNA/UST Style**:
- No real backing
- Death spiral risk
- Complex mechanisms
- Historical failures

**GREEN**:
- Always overcollateralized
- Simple economics
- Proven model
- Multiple safeguards

## GREEN Design Philosophy

GREEN implements proven collateralization models with modern automation:
- Overcollateralized backing ensures solvency
- Smart contract automation eliminates manual processes
- Economic incentives align participant interests
- Supply elasticity matches market demand

This architecture creates a decentralized stable value system operating through transparent, predictable mechanisms.

For technical implementation details, see [Green Token Technical Documentation](technical/tokens/GreenToken.md).