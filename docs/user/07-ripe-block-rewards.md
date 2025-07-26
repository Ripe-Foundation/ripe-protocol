# RIPE Block Rewards

RIPE block rewards are the primary incentive mechanism in Ripe Protocol, distributing RIPE tokens to participants who actively contribute to the protocol's health and growth. These rewards are emitted continuously at a per-block rate and allocated across four distinct participant categories based on their protocol activity.

## Token Allocation

**15% of total RIPE supply is allocated to block rewards** (150 million RIPE tokens from the 1 billion total supply). This allocation is planned to be distributed over approximately 5 years, though the emission rate and duration can be adjusted through governance once fully decentralized governance is activated.

## How Block Rewards Work

### Continuous Emission

The protocol mints new RIPE tokens at a fixed rate per block:
- **Emission Rate**: Configured as RIPE tokens per block
- **Distribution**: Occurs continuously, not in discrete intervals
- **Accumulation**: Rewards accrue in real-time based on user activity

### Time-Weighted Point System

Rewards are distributed using a points-based system that factors in both position size and time:

**Points = Balance × Blocks Held**

This mechanism ensures users with larger positions held for longer periods receive proportionally higher rewards, creating a fair distribution system that rewards commitment.

## Reward Categories

The total RIPE emissions are divided among four participant groups, each with a configurable percentage allocation:

### 1. Borrowers
Users who mint GREEN stablecoin against their collateral earn rewards based on:
- **Principal borrowed**: The amount of GREEN debt outstanding
- **Time borrowed**: Duration the loan remains active
- **Calculation**: Principal × Blocks = Borrower Points

### 2. Stakers
Users who stake assets in eligible vaults earn rewards from this category. This includes:

**A. Ripe Governance Vault Deposits (RIPE and RIPE LP tokens):**
- **Deposited amount**: Size of their governance vault position
- **Lock duration bonus**: Longer lock commitments earn bonus points (up to 200% bonus for maximum lock)
- **Asset weight**: RIPE LP tokens receive 150% weight compared to RIPE tokens (100% weight)
- **Asset allocation**: RIPE and RIPE LP tokens have configured staker points allocations
- **Time staked**: Duration tokens remain in governance vault
- **Calculation**: (Balance × Blocks × Asset Weight × Asset Staker Allocation) + Lock Duration Bonus

**B. Stability Pool Deposits (sGREEN and GREEN LP tokens):**
- **Deposited amount**: Size of their stability pool position
- **Asset allocation**: sGREEN and GREEN LP have configured staker points allocations
- **Time staked**: Duration tokens remain in stability pool
- **Calculation**: Balance × Blocks × Asset Staker Allocation
- **No lock bonus**: Stability pools have no lock periods, so no duration bonus applies

*Note: These staked assets (RIPE, RIPE LP, sGREEN, and GREEN LP in their respective vaults) earn rewards exclusively from the Stakers category and are not eligible for Vote Depositors or General Depositors rewards*

### 3. Vote Depositors
This category rewards deposits in assets chosen by governance voting (once fully activated):
- **Governance-selected assets**: When governance is active, token holders will vote which assets receive these rewards
- **Asset allocation**: Each voted asset receives a configured voter points allocation
- **Depositor rewards**: Users who deposit these governance-selected assets earn from this pool
- **Time-weighted**: Duration assets remain deposited
- **Calculation**: Balance × Blocks × Asset Voter Allocation = Voter Points

*Note: This category is for deposits in assets selected through governance voting, not for governance participation itself*

### 4. General Depositors
All vault deposits earn from this pool based on USD value proportions:
- **Universal eligibility**: All deposited assets participate
- **USD-weighted**: Rewards distributed proportionally based on USD value of deposits
- **Cross-asset fairness**: Ensures equal treatment regardless of asset type or decimals
- **Time-weighted**: Duration assets remain deposited
- **Calculation**: USD Value × Blocks = General Depositor Points

## Asset-Specific Allocations

Each supported asset has allocation percentages that determine its share of the top-level reward categories. These allocations split the category pools among eligible assets:

- **Staker Points Allocation**: Asset's share of the total Stakers category pool
  - Applies to staked assets: RIPE and RIPE LP (in Governance Vault), sGREEN and GREEN LP (in Stability Pools)
  - Example: If RIPE has 30%, RIPE LP has 20%, sGREEN has 25%, and GREEN LP has 25%, they split the Stakers pool accordingly
  - Non-staked assets have 0% staker allocation
  
- **Voter Points Allocation**: Asset's share of the total Vote Depositors category pool
  - Applies to assets selected through governance voting
  - Example: If Asset A has 50% and Asset B has 50%, each receives half of the Vote Depositors pool
  - Staked assets (RIPE, RIPE LP, sGREEN, GREEN LP) have 0% voter allocation
  - All voter allocations must sum to 100% across eligible assets

**Important**: These percentages determine how assets split their respective top-level categories. If the Vote Depositors category receives 20% of total emissions and Asset A has 50% voter allocation, then Asset A depositors share 10% of total emissions (50% of 20%).

## How User Claims Are Calculated

The protocol uses a two-tier calculation system to determine each user's claimable rewards:

### Tier 1: User Share of Asset
For each asset a user deposits, their share is calculated as:

**User Share = User Balance Points / Asset Total Balance Points**

Where Balance Points = Balance × Blocks Held

### Tier 2: Asset Share of Category
Each asset receives rewards from its eligible categories based on:

**Asset Rewards = (Asset Points / Global Category Points) × Category Pool**

### Combined Calculation

**User Rewards = User Share × Asset Rewards**

Breaking this down:
1. **Staker Rewards**: `(User Points / Asset Points) × (Asset Staker Points / Global Staker Points) × Stakers Pool`
2. **Vote Depositor Rewards**: `(User Points / Asset Points) × (Asset Voter Points / Global Voter Points) × Vote Depositors Pool`
3. **General Rewards**: `(User Points / Asset Points) × (Asset USD Points / Global USD Points) × General Pool`

### Borrowing Rewards Calculation

Borrowing rewards use a simpler single-tier system:

**User Borrowing Rewards = (User Borrow Points / Global Borrow Points) × Borrowers Pool**

Where Borrow Points = Principal × Blocks Borrowed

### Example Calculation

Let's say:
- Total RIPE per block: 100
- Stakers allocation: 30% (30 RIPE)
- RIPE token has 60% staker allocation
- RIPE LP token has 40% staker allocation
- Alice has 1,000 RIPE staked for 100 blocks
- Total RIPE staked: 10,000 for same period

Alice's calculation:
1. Alice's share of RIPE deposits: 1,000/10,000 = 10%
2. RIPE's share of staker rewards: 60% of 30 RIPE = 18 RIPE
3. Alice's staker rewards: 10% of 18 RIPE = 1.8 RIPE
4. Plus any lock duration bonus on her points

## Reward Distribution Example

Consider a simplified scenario:
- **Total RIPE per block**: 100 RIPE
- **Borrowers allocation**: 40%
- **Stakers allocation**: 30%
- **Vote Depositors allocation**: 20%
- **General depositors allocation**: 10%

Per block distribution:
- Borrowers pool: 40 RIPE
- Stakers pool: 30 RIPE
- Vote Depositors pool: 20 RIPE
- General depositors pool: 10 RIPE

Each user's share within their category equals:
**User Reward = (User Points / Total Category Points) × Category Pool**

## Claiming Rewards

### Claim Options

When claiming accumulated RIPE rewards, users have two choices:

1. **Direct Transfer**: Receive RIPE tokens directly to their wallet
2. **Auto-Stake**: Automatically deposit rewards into the Ripe Governance Vault

### Auto-Staking Parameters

The protocol configures two key parameters for auto-staking:

- **Auto-Stake Ratio**: Percentage of rewards automatically staked (0-100%)
  - Example: 70% ratio means 70% is staked, 30% sent to wallet
  
- **Auto-Stake Duration Ratio**: Determines lock duration as percentage of maximum
  - Example: 50% ratio with 3-year max = 1.5-year lock
  - Longer locks provide higher governance point bonuses

### Claiming Process

Users can claim rewards:
- **Individual claims**: Claim all rewards across all positions
- **Granular claims**: Claim from specific positions only
- **Batch claims**: Protocol can process multiple users simultaneously

## Integration with Protocol Activity

### Borrowing Rewards

Borrowers earn rewards continuously while maintaining GREEN debt:
- Rewards incentivize healthy borrowing activity
- Larger loans earn proportionally more rewards
- Repayment stops reward accumulation for that portion

### Deposit Rewards

Depositors earn across multiple categories simultaneously:
- Same deposit can earn staker, voter, and general rewards
- Depends on asset configuration and vault type
- Withdrawals proportionally reduce future rewards

### Governance and Stability Pool Participation

**RIPE governance vault deposits** earn enhanced rewards:
- Qualify for staker allocation percentage only
- **Staker rewards**: Lock duration provides bonus points (up to 200% bonus)
- **No vote depositor rewards**: RIPE and RIPE LP tokens have 0% voter allocation
- Can claim and auto-stake to compound positions

**Stability pool deposits** (sGREEN and GREEN LP) also earn staker rewards:
- Qualify for staker allocation percentage only
- **Staker rewards**: Based on deposit size and duration (no lock bonus)
- **No vote depositor rewards**: sGREEN and GREEN LP have 0% voter allocation
- Provide additional yield through liquidation profits

## Protocol Configuration

The reward system parameters are set through MissionControl:

### Global Settings
- **Points Enabled**: Master switch for entire reward system
- **RIPE Per Block**: Total emission rate
- **Category Allocations**: Percentage split between four categories

### Per-Asset Settings
- **Staker Points Allocation**: Asset's share of staker rewards (RIPE, RIPE LP, sGREEN, GREEN LP)
- **Voter Points Allocation**: Asset's share of vote depositor rewards
- **Asset Weight**: Multiplier for certain assets (e.g., RIPE LP tokens have 150% weight)

These configurations can be adjusted through governance once fully decentralized governance is activated.

---

RIPE block rewards create a sustainable incentive structure that rewards active protocol participation across borrowing, depositing, and governance activities. The time-weighted point system ensures fair distribution while the flexible claiming options allow users to choose between immediate liquidity or enhanced governance participation through auto-staking.

For technical implementation details, see [Lootbox Technical Documentation](technical/core/Lootbox.md).