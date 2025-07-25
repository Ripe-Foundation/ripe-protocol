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

1. **Dynamic Interest Rates**: Borrowing costs adjust to influence supply
2. **[Stability Pools](liquidations/stability-pool-mechanics.md)**: Provide liquidity during market stress
3. **Direct Redemptions**: Exchange GREEN for collateral at par
4. **[Endaoment](endaoment.md) Operations**: Treasury actions support peg
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

Ripe's most innovative stability mechanism continuously monitors market conditions and adjusts borrowing rates in real-time. This creates powerful economic incentives that maintain GREEN's peg without manual intervention.

**How Pool Health Monitoring Works**:
- **Reference Pool**: Monitors GREEN/USDC liquidity pool as market health indicator
- **Weighted Ratio**: Sophisticated calculation prevents manipulation
- **Danger Threshold**: Rates begin increasing when GREEN exceeds 60% of pool
- **Progressive Response**: Mild imbalance = mild adjustment, severe = strong response

**Rate Adjustment Tiers**:
```
Pool Status          GREEN Ratio    Rate Multiplier    Action
Healthy              <60%           1.0x               Normal rates
Warning              60-65%         1.5x               Discourage borrowing
Stressed             65-70%         2.0x               Strong disincentive
Critical             70-75%         2.5x               Urgent correction
Emergency            >75%           3.0x               Maximum response
```

**Two-Component System**:
1. **Ratio Boost**: Multiplier based on pool imbalance severity (1.5x-3.0x)
2. **Time Boost**: Additional increase based on blocks in danger zone

**Example with pool at 70% GREEN for 5,000 blocks**:
- Base rate: 5% APR
- Ratio boost: 5% × 2.25x = 11.25% APR
- Time boost: +0.5% APR (after 5,000 blocks)
- Total rate: 11.75% APR

This dual mechanism ensures immediate response to imbalances while creating increasing urgency for sustained stress.

For complete details on this system, see [Dynamic Rate Protection](dynamic-rate-protection.md).

### 2. Direct Redemption Mechanism

When GREEN trades below $1, holders can directly redeem:
- **Redemption Threshold**: Only targets users within redemption risk zone (approaching liquidation)
- **Risk-Based Priority**: Redeems from riskiest positions first, not arbitrary users
- **Protection for Healthy Loans**: Well-collateralized positions cannot be redeemed against
- **$1 Value Guarantee**: Always redeem GREEN for exactly $1 of collateral
- **Arbitrage Restoration**: Creates profitable opportunities that restore peg

**Important**: Redemptions only affect users whose debt health has deteriorated significantly. If your position is well-collateralized, you cannot be targeted for redemption.

### 3. Stability Pool Defense

Specialized pools that maintain peg stability:
- **First Line Defense**: Absorb liquidated collateral before other mechanisms
- **Instant Liquidity**: Provide immediate GREEN when needed
- **Fee Incentives**: Earn rewards for defending the peg
- **Depositor Protection**: Pool participants share in liquidation profits
- **Automatic Activation**: Engage without manual intervention

### 4. Endaoment Stabilizer

The protocol treasury actively manages stability:
- **Market Operations**: Can mint/burn GREEN based on specific conditions
- **Collateral Management**: Deploys treasury assets to support peg
- **Emergency Response**: Authorized to take rapid action during extreme events
- **Programmatic Rules**: Operates within pre-defined parameters
- **Transparent Actions**: All operations visible on-chain

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
- Multi-collateral innovation
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

## Stability Response Mechanisms

### Market Volatility Management

During significant market events, GREEN's automated systems activate sequentially:

- Liquidation mechanisms process underwater positions
- Stability pools provide immediate liquidity
- Dynamic rates adjust to market conditions
- Peg maintenance occurs without manual intervention

### System Characteristics

The multi-layered architecture provides:
- Rapid response to market changes through automated triggers
- Distributed risk management without single points of failure
- Transparent operations through on-chain execution
- Predictable behavior based on coded parameters

## GREEN Design Philosophy

GREEN implements proven collateralization models with modern automation:
- Overcollateralized backing ensures solvency
- Smart contract automation eliminates manual processes
- Economic incentives align participant interests
- Supply elasticity matches market demand

This architecture creates a decentralized stable value system operating through transparent, predictable mechanisms.

For technical implementation details, see [GreenToken Technical Documentation](../technical/tokens/GreenToken.md).