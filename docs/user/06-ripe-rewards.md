# RIPE Rewards: Get Paid to Use the Protocol

Every block. Every transaction. Every dollar borrowed or staked.

Ripe Protocol is watching. And paying.

150 million RIPE tokens are flowing to users who actually use the protocol. Not VCs. Not insiders. Users. Borrow GREEN? Get paid. Stake in pools? Get paid more. Lock your rewards? Get paid even more.

The best part? Early users are sharing a tiny pool. More rewards per person until the masses arrive.

> **📊 Rewards at a Glance**
>
> - **Total RIPE for rewards**: 150M (15% of supply)
> - **Target daily emissions**: ~4,320,000 RIPE (when fully ramped on Base)
> - **Current emissions**: Starting at 0.0025 RIPE/block (ramping up)
> - **Best earning strategy**: GREEN LP (65% of staker rewards)
> - **Current split**: 90% to stakers, 10% to borrowers
> - **Auto-stake requirement**: 75% of claimed rewards locked for 1 year
> - **Claim anytime**: No minimum, no lockup for earning

## Quick Start: Understanding Your Rewards

**🎯 The One-Minute Version:**

```
YOUR ACTIVITY          →  REWARD POOL  →  YOUR SHARE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Staking (All Types)    →  90% of RIPE  →  Based on asset type + position
  • RIPE/RIPE LP      →  Governance   →  Lock bonus up to 3x
  • sGREEN/GREEN LP   →  Stability    →  Size × time × weight
Borrowing GREEN        →  10% of RIPE  →  Based on debt size

FUTURE ALLOCATIONS (Not Active Yet):
Depositing any asset   →  TBD % of RIPE  →  Based on USD value
Future voted assets    →  TBD % of RIPE  →  Community decides

SIMPLE FORMULA: Your % of pool × Pool rewards = Your RIPE
```

**💡 Key Insight**: You don't compete with all users — only those in your specific pool. A borrower doesn't dilute a staker's rewards!

## The Reward Engine

### Continuous Token Flow

Unlike traditional yield farming with discrete epochs, Ripe's rewards flow continuously:

- **Every Block Counts**: New RIPE tokens mint with each blockchain block
- **Real-Time Accumulation**: Your rewards grow second by second, not weekly or monthly
- **No Waiting Periods**: Start earning immediately upon participation
- **Fair Distribution**: Time-weighted system prevents gaming or manipulation

### The Points System

Ripe uses an elegant points mechanism that rewards both size and commitment:

```
Points = Position Size × Time Held (in blocks)
```

This simple formula creates profound fairness — a smaller position held longer can earn more than a whale's brief deposit. It's democracy through mathematics.

### Emission Schedule Ramp-Up

**Important Context**: The protocol is currently in its emission ramp-up phase:

- **Starting emissions**: 0.0025 RIPE per block (~108 RIPE per day on Base)
- **Target emissions**: ~100 RIPE per block (~4,320,000 RIPE per day on Base)
- **Ramp-up period**: Gradual increase to match 5-year distribution schedule
- **Why this matters**: Current rewards are ~40,000x lower than examples shown

This conservative start ensures:

1. **Sustainable token distribution** over the full 5-year period
2. **Time for liquidity to build** before major emissions
3. **Gradual market absorption** of new RIPE tokens
4. **Protection against early dumping** when liquidity is thin

**Note**: All reward calculations in this document assume target emission rates for illustration. Multiply by current emission rate (0.0025/100 = 0.0025%) for actual current rewards.

## Current Reward Categories

The protocol currently distributes rewards to two participant groups:

### 1. Stakers (90% of Emissions) 💎

Staking in protocol vaults earns the lion's share of rewards:

**[Governance Vault](08-governance.md) (RIPE & RIPE LP)**

- **Base Rewards**: Size × time × asset weight
- **Lock Multiplier**: Up to 3x boost for maximum duration locks
- **LP Advantage**: RIPE LP tokens earn 50% more points than RIPE
- **Compound Strategy**: Auto-stake rewards for exponential growth

**[Stability Pools](05-stability-pools.md) ([sGREEN](04-sgreen.md) & GREEN LP)**

- **Dual Yield**: RIPE rewards plus liquidation profits
- **No Lock Required**: Flexible liquidity with full rewards
- **Risk Buffer**: Help secure the protocol while earning

### 2. Borrowers (10% of Emissions) 💰

Taking out GREEN loans earns rewards proportional to your debt:

- **Reward Basis**: Outstanding GREEN principal × time borrowed
- **Why It Matters**: Borrowing creates GREEN demand and protocol revenue
- **Smart Strategy**: Larger, longer-term loans maximize rewards
- **Real Benefit**: Offset borrowing costs with RIPE earnings

## Future Reward Categories (Not Active Yet)

### Vote Depositors (Future)

When governance activates, token holders may vote to allocate rewards to specific assets:

- **Democratic Selection**: Community chooses reward-earning assets
- **Targeted Incentives**: Direct liquidity where protocol needs it most
- **Strategic Deposits**: Align your holdings with governance decisions

### General Depositors (Future)

May be activated to reward all vault deposits:

- **USD-Weighted**: Fair distribution based on deposit value
- **Asset Agnostic**: All supported assets participate equally
- **Passive Income**: Earn just by holding assets in Ripe vaults

## Understanding Your Share

### Asset-Specific Allocations

Each supported asset has its own configuration that determines how it splits the top-level reward pools:

- **Staker Points Allocation**: Percentage of the total Stakers pool this asset receives
  - Only applies to staked assets (RIPE, RIPE LP in [Governance Vault](08-governance.md); [sGREEN](04-sgreen.md), GREEN LP in [Stability Pools](05-stability-pools.md))
  - Current allocations:
    - GREEN LP: 65% (highest rewards!)
    - RIPE LP: 15%
    - sGREEN: 10%
    - RIPE: 10%
- **Voter Points Allocation**: Percentage of the Vote Depositors pool this asset receives
  - Only for assets selected through governance voting
  - All voter allocations across eligible assets must sum to 100%
  - Staked assets have 0% voter allocation since they earn from the Stakers pool

**Important**: These percentages split their respective category pools. If Vote Depositors receive 20% of total emissions and Asset A has 50% voter allocation, Asset A depositors share 10% of total emissions (50% of 20%).

### How Rewards Actually Flow (Simplified)

Think of RIPE rewards like a waterfall with two splits:

```
Total RIPE Emissions (100 RIPE/block)
            ↓
    ┌───────┴───────┐
    │ First Split  │ (by user type)
    └───────┬───────┘
            ↓
    90% → Stakers Pool
    10% → Borrowers Pool

    Future: Vote & General Pools
    (Currently 0%, may change)
            ↓
    ┌───────┴───────┐
    │ Second Split │ (by asset within pool)
    └───────┬───────┘
            ↓
    Each asset gets its
    configured percentage
            ↓
    Your share based on
    your points vs total

```

### Step-by-Step Calculation Guide

Let's follow your RIPE rewards step by step:

**🎯 Step 1: Where Do Your Rewards Come From?**

```
If you're staking RIPE → You earn from the Stakers pool (90%)
If you're borrowing → You earn from the Borrowers pool (10%)
Future: General deposits and voted assets (not active yet)
```

**🎯 Step 2: What's Your Asset's Share?**

```
Within the Stakers pool (90 RIPE/block):
- GREEN LP tokens get 65% (largest share!)
- RIPE LP tokens get 15%
- sGREEN gets 10%
- RIPE tokens get 10%

So stakers share 90 RIPE/block:
- GREEN LP stakers: 90 × 65% = 58.5 RIPE
- RIPE LP stakers: 90 × 15% = 13.5 RIPE
- sGREEN holders: 90 × 10% = 9 RIPE
- RIPE stakers: 90 × 10% = 9 RIPE
```

**🎯 Step 3: What's YOUR Share of Your Asset Pool?**

```
Your Points = Amount × Time
Your Share = Your Points ÷ Total Points for that asset

Example: You stake 1,000 RIPE for 100 blocks
- Your points: 1,000 × 100 = 100,000
- Total RIPE points: 1,000,000
- Your share: 100,000 ÷ 1,000,000 = 10%
```

**🎯 Step 4: Calculate Your Rewards**

```
Your rewards = Your share × Asset's allocation

From above: 10% × 9 RIPE = 0.9 RIPE per block
Over 100 blocks: 0.9 × 100 = 90 RIPE earned!
```

### Quick Reference Table

| Your Action              | Pool You Earn From        | How to Maximize                      |
| ------------------------ | ------------------------- | ------------------------------------ |
| Provide GREEN LP         | Stakers (90%) - 65% share | Larger positions earn more           |
| Provide RIPE LP          | Stakers (90%) - 15% share | Larger positions earn more           |
| Stake RIPE               | Stakers (90%) - 10% share | Lock for 3 years (+200% bonus)       |
| Deposit sGREEN           | Stakers (90%) - 10% share | Combine with stability pool benefits |
| Borrow GREEN             | Borrowers (10%)           | Larger, longer loans                 |
| Future: General deposits | Not active yet            | TBD                                  |
| Future: Voted assets     | Not active yet            | TBD                                  |

### Simple Rewards Estimator

**"How much will I earn?"** - Quick formulas for common scenarios:

⚠️ **Note**: Examples below use TARGET emission rates (100 RIPE/block). Current emissions are 0.0025 RIPE/block, so multiply results by 0.0025% for actual current rewards.

**For GREEN LP (Highest Rewards - 65% of stakers):**

```
Daily Rewards ≈ (Your LP Value / Total GREEN LP) × 2,527,200

Example: $100,000 in GREEN LP (1% of total)
= 1% × 2,527,200 = ~25,272 RIPE per day
= ~$2,527.20 per day (at $0.10 RIPE)
= ~92.2% APR in USD terms
```

**For RIPE Staking (10% of stakers):**

```
Daily Rewards ≈ (Your RIPE / Total RIPE Staked) × 388,800 × Lock Multiplier

Example: 100,000 RIPE staked (0.1% of total) with 3-year lock
= 0.1% × 388,800 × 3.0 = ~1,166 RIPE per day
= ~$116.60 per day (at $0.10 RIPE)
= Your stake worth $10,000, earning $116.60/day = ~425% APR
With compounding: ~1,000% APY
```

**For sGREEN Deposits (10% of stakers):**

```
Daily Rewards ≈ (Your sGREEN Value / Total sGREEN) × 388,800

Example: $100,000 in sGREEN (0.5% of total)
= 0.5% × 388,800 = ~1,944 RIPE per day
= ~$194.40 per day (at $0.10 RIPE)
= ~71% APR in USD terms
```

**For Borrowing GREEN (10% of emissions):**

```
Daily Rewards ≈ (Your Debt / Total Debt) × 432,000

Example: $500,000 borrowed (0.25% of total debt)
= 0.25% × 432,000 = ~1,080 RIPE per day
= ~$108.00 per day (at $0.10 RIPE)
= ~7.9% APR in rewards (offsetting borrowing costs!)
```

## Auto-Staking Mechanism

### How Auto-Staking Works

The protocol enforces auto-staking to balance token distribution with long-term alignment:

- **Stake Ratio**: 75% must be auto-staked
  - Only 25% goes to your wallet as liquid RIPE
  - Prevents market flooding while building committed participants
- **Duration Ratio**: 33% × 3-year max = 1-year lock
  - All auto-staked rewards are locked for 1 year
  - Ensures reward recipients become long-term stakeholders

**Why This Matters**: Rather than dumping tokens on the market, auto-staking creates a community of invested participants who earn governance power alongside their rewards. You're not just earning tokens — you're earning a voice in the protocol's future.

## Protocol Configuration

### Flexible Parameters

Mission Control governs all reward settings:

- **Emission Rate**: RIPE tokens minted per block
- **Category Splits**: Percentage to each participant type
- **Asset Allocations**: Individual asset point multipliers
- **Auto-Stake Settings**: Default ratios and durations

### Governance Evolution

Once activated, RIPE holders will control:

- Emission schedules and rates
- Category allocation adjustments
- Asset-specific incentives
- New reward mechanisms

## Common Questions About Rewards

### "Why do I calculate my share twice?"

You don't! Think of it as one calculation with two inputs:

1. **Which pie you're eating from** (Staker, Borrower, etc.)
2. **How big your slice is** (Your percentage of that pie)

It's like a buffet where desserts are on one table and mains on another — you only compete with people at your table, not the whole restaurant!

### "How do I estimate my rewards?"

**Simple Method:**

1. Find your pool's daily RIPE allocation (at target emissions):
   - Stakers total: 3,888,000 RIPE/day (90% of emissions)
   - Borrowers total: 432,000 RIPE/day (10% of emissions)
2. For stakers, find your asset's share:
   - GREEN LP: 2,527,200 RIPE/day (65% of stakers)
   - RIPE LP: 583,200 RIPE/day (15% of stakers)
   - sGREEN: 388,800 RIPE/day (10% of stakers)
   - RIPE: 388,800 RIPE/day (10% of stakers)
3. Multiply: asset allocation × your percentage = daily rewards

**Example**: You have 1% of all staked RIPE → 388,800 × 1% = 3,888 RIPE per day

### "What happens when I claim?"

The protocol enforces auto-staking parameters to align incentives:

**Current Settings (Protocol-Controlled):**

- **Auto-stake percentage**: 75% must be auto-staked
- **Lock duration**: 1 year (33% of max 3-year duration)
- **Your choice**: Only whether to claim now or wait

**Example Claim:**

- You have 1,000 RIPE rewards to claim
- Protocol requires 75% auto-stake with 1-year lock
- Result: 250 RIPE to your wallet + 750 RIPE locked in governance vault

**Why This Matters**: Auto-staking prevents market flooding and ensures reward recipients become long-term stakeholders with governance power. You're earning both tokens AND future influence!

### "Do different assets in the same pool compete?"

Yes, within each pool! For example, in the Stakers pool:

- RIPE stakers compete with other RIPE stakers
- RIPE LP stakers compete with other RIPE LP stakers
- But they share the total Stakers allocation based on configured percentages

### "What happens if nobody stakes/borrows?"

More rewards for those who do! If you're the only RIPE staker, you get 100% of RIPE's allocation in the Stakers pool. Early participants often see highest returns.

## The Early Bird Gets the RIPE

Right now, emissions are ramping up. TVL is growing. But it's still early.

Those juicy GREEN LP yields? They'll shrink when billions pour in. That insane RIPE staking APY? Only while the participant pool stays small.

Every block you wait is rewards you're not earning. Every day you delay is yield going to someone else.

The protocol pays those who show up. Are you showing up?

---

_For technical implementation details, see [Lootbox Technical Documentation](../technical/core/Lootbox.md)._
