# RIPE Token & Governance

RIPE is Ripe Protocol's governance token that enables community control over protocol operations. The Ripe Governance Vault provides a mechanism for token holders to lock RIPE tokens in exchange for governance power that will ultimately determine protocol parameters, asset support, and treasury management.

## Current Status & Future Governance

The protocol does not yet have full on-chain decentralized governance, but **governance power is actively accruing**. Community members who lock RIPE tokens now are accumulating governance points that will translate directly into voting power when full governance launches in the coming months.

```
CURRENT STATE                    FUTURE GOVERNANCE
┌─────────────────────┐         ┌─────────────────────┐
│   RIPE DEPOSITS     │         │    FULL VOTING      │
│      ↓              │   →     │                     │
│ GOVERNANCE POINTS   │         │ • Asset Support     │
│   ACCUMULATING      │         │ • Debt Parameters   │
│                     │         │ • Treasury Strategy │
│  (Preparing for     │         │ • Protocol Limits   │
│   Future Voting)    │         │ • Revenue Splits    │
└─────────────────────┘         └─────────────────────┘
```

## Governance Power Calculation

Individual governance power equals the portion of total points held:

**Governance Power = User's Total Points / Protocol Total Points**

This proportional system ensures fair representation based on contribution and commitment to the protocol.

## The Ripe Governance Vault System

### What is the Ripe Governance Vault?

The Ripe Governance Vault is a specialized vault where RIPE token holders deposit and lock their tokens to earn governance points. Unlike regular deposits, governance vault positions require time-based commitments that increase governance influence.

### Supported Assets

The Ripe Governance Vault accepts:
- **RIPE tokens**: The primary governance asset (100% weight)
- **RIPE LP tokens**: Liquidity provider tokens from RIPE trading pairs (150% weight)

LP tokens receive a 50% bonus in point calculations compared to RIPE tokens, reflecting their dual contribution to protocol liquidity and governance.

## Governance Point Mechanics

**⚠️ Key Principle: Governance points are tied to deposited tokens. Any withdrawal or transfer proportionally reduces your points.**

### Base Point Calculation

Governance points accumulate based on a time-weighted formula:

**Base Points = Token Balance × Blocks Elapsed × Asset Weight**

- **Token Balance**: Amount of RIPE or RIPE LP tokens deposited
- **Blocks Elapsed**: Time since last point update
- **Asset Weight**: 100% for RIPE, 150% for RIPE LP tokens

### Lock Duration Bonuses

The vault rewards longer commitments with additional governance points:

```
LOCK DURATION BONUS STRUCTURE
┌─────────────────────────────────────────┐
│  Duration     │  Bonus Multiplier       │
│─────────────────────────────────────────│
│  1 day (min)  │  0% bonus               │
│  3 months     │  ~15% bonus             │
│  6 months     │  ~35% bonus             │
│  1 year       │  ~65% bonus             │
│  2 years      │  ~130% bonus            │
│  3 years      │  200% bonus (maximum)   │
└─────────────────────────────────────────┘
```

**Lock Bonus Formula:**
1. Calculate remaining lock duration
2. Determine position within min-max range
3. Apply proportional bonus up to maximum (200%)
4. Add bonus points to base points

### Example Calculation

**Scenario**: 1,000 RIPE tokens locked for 1 year (with 3-year max and 200% max bonus)

- Base points per 100 blocks: 1,000 × 100 = 100,000
- Lock duration bonus: ~65% = 65,000 additional points
- **Total points earned**: 165,000 per 100 blocks

**LP Token Example**: 1,000 RIPE LP tokens locked for 1 year

- Asset weight: 150% (compared to 100% for RIPE)
- Base points per 100 blocks: 1,000 × 100 × 1.5 = 150,000
- Lock duration bonus: ~65% = 97,500 additional points
- **Total points earned**: 247,500 per 100 blocks

## Lock Management

### Initial Lock Requirements

When depositing RIPE tokens:
- **Minimum lock duration**: 1 day
- Lock duration determines bonus multiplier
- Cannot reduce lock time, only extend

### Lock Extension

Token holders can extend their lock duration at any time:
- **Extension only**: Cannot shorten existing locks
- **Immediate effect**: Bonus calculations update instantly
- **No penalties**: Extending locks has no downside

### Early Exit Mechanism

The protocol allows early lock release with severe penalties:
- **Exit fee**: 80% of deposited tokens forfeited
- **Fee distribution**: The 80% penalty remains in the vault for other depositors
- **Remaining balance**: Exiter receives only 20% of their original deposit
- **Governance point slash**: ALL governance points are lost (100% slash on 100% withdrawal)
- **Governance protection**: System prevents exits during bad debt when withdrawals would fail anyway

Note: Even though you only receive 20% of tokens back, this counts as a 100% withdrawal for governance points, resulting in complete loss of accumulated points.

### Lock Expiration

When locks expire:
- **Automatic unlock**: Tokens become withdrawable
- **Continued accrual**: Governance points continue accumulating at base rate
- **Re-lock option**: Can establish new locks for additional bonuses

## Deposit and Withdrawal Process

### Making Deposits

**Standard Deposits** (via Teller):
- Uses minimum lock duration from protocol configuration
- Applies current asset weight for point calculations
- Automatically begins governance point accumulation

**Advanced Deposits** (protocol-directed):
- May specify custom lock durations
- Used for reward distributions and special allocations
- Weighted averaging with existing positions

### Withdrawal Process

**Withdrawal Requirements:**
1. **Lock expiration**: Must wait until unlock block
2. **No bad debt**: Some configurations freeze withdrawals during protocol stress
3. **Governance point slash**: Withdrawing reduces governance points proportionally

**⚠️ Important: Proportional Point Slashing**

When you withdraw ANY amount from the governance vault, your governance points are reduced proportionally:

**Points Lost = Total User Points × (Shares Withdrawn ÷ Total User Shares)**

Examples:
- Withdraw 50% of your tokens → Lose 50% of your governance points
- Withdraw 10% of your tokens → Lose 10% of your governance points
- Withdraw 100% of your tokens → Lose ALL governance points

This ensures governance power always reflects current stake in the protocol. There is no way to withdraw tokens while maintaining governance points.

## Future Governance Scope

When full governance activates, RIPE holders will control:

### Asset and Parameter Management
- **Collateral asset approval**: Which tokens can serve as collateral
- **Risk parameters**: Loan-to-value ratios, liquidation thresholds, interest rates
- **Deposit limits**: Per-user and global caps for new assets
- **Oracle configuration**: Price feed priorities and backup systems

### Treasury Operations
- **Investment strategies**: How Endaoment funds are deployed
- **Yield optimization**: Capital allocation across DeFi protocols
- **Partnership programs**: Liquidity partnerships and revenue sharing
- **Emergency procedures**: Crisis response and fund protection

### Protocol Economics
- **Debt ceilings**: Maximum borrowing limits per asset
- **Fee structures**: Origination fees, liquidation penalties
- **Revenue distribution**: Split between sGREEN holders and RIPE stakers
- **Reward emissions**: RIPE token distribution rates and targets

### System Parameters
- **Dynamic rate parameters**: Thresholds and multipliers for rate protection
- **Liquidation configuration**: Phase priorities and discount rates
- **Stability pool parameters**: Rewards and participation incentives

## Integration with Rewards

### RIPE Block Rewards

The Lootbox system distributes RIPE tokens to various participant categories:
- **Borrowers**: Users minting GREEN against collateral
- **Depositors**: Users providing assets to vaults
- **Governance participants**: RIPE token stakers in the governance vault
- **Stability pool providers**: sGREEN holders in liquidation pools

### Reward Claiming Options

When claiming RIPE rewards:
- **Direct receipt**: Tokens sent to user address immediately
- **Auto-staking**: Automatic deposit into Ripe Governance Vault with lock
- **Lock customization**: Specify desired lock duration for governance bonuses

### Compound Benefits

Participants can maximize returns through:
- **Reward auto-staking**: Claim rewards directly into governance vault
- **Extended locks**: Higher bonuses on both existing and new deposits
- **Multi-asset participation**: Earn rewards while building governance power

## Preparing for Full Governance

### Building Position Now

Early participants can:
- **Accumulate points**: Start building governance power before competition increases
- **Optimize locks**: Establish long lock periods for maximum future influence
- **Monitor developments**: Stay informed about governance system progress

### Understanding Future Power

Current points will directly translate to future voting power. The proportional system means early participants with longer locks will have the strongest influence when governance launches.

---

The Ripe Governance Vault represents the foundation of community control over Ripe Protocol. By locking RIPE tokens now, participants are not only earning governance points but also positioning themselves to shape the protocol's future development and parameters when full decentralized governance activates.

For technical implementation details, see [RipeGov Technical Documentation](technical/vaults/RipeGov.md).