# Dynamic Rate Protection

Dynamic Rate Protection automatically adjusts borrowing rates based on market conditions to maintain [GREEN's](../green.md) dollar peg. The system monitors liquidity pool health and responds proportionally to imbalances, working alongside other [stability mechanisms](../green.md#stability-mechanisms) to ensure peg maintenance.

## Dynamic Rate Architecture

The system provides:
- Automated response to market conditions
- Proportional scaling based on imbalance severity
- Self-correcting mechanisms as conditions normalize
- Protocol-wide stability maintenance

## How Pool Health Monitoring Works

### The GREEN/USDC Reference Pool

Ripe monitors the primary GREEN/USDC liquidity pool as a real-time indicator of market demand:

The protocol defines operational zones:
- Balanced state: Equal GREEN/USDC composition
- Warning threshold: GREEN exceeds 60% of pool
- Critical threshold: GREEN exceeds 80% of pool

### Weighted Ratio Calculation

The protocol doesn't just look at simple ratios—it uses a weighted calculation that considers:
- Pool depth and liquidity
- Recent trading volume
- Time-weighted average prices
- External market conditions

This sophisticated approach prevents manipulation and ensures accurate market readings.

## The Three-Layer Response System

```
GREEN/USDC POOL MONITORING
┌────────────────────────────────────────────────────────────┐
│  Pool Composition: [GREEN 45%] [USDC 55%] ← HEALTHY        │
└────────────────────────┬───────────────────────────────────┘
                         │
                 GREEN increases to 65%
                         │
                         v
┌────────────────────────────────────────────────────────────┐
│                 DANGER ZONE TRIGGERED                     │
│  ┌──────────────┬─────────────────┬─────────────────────┐  │
│  │   LAYER 1    │     LAYER 2     │      LAYER 3       │  │
│  │ Ratio Boost  │  Time Boost     │   Rate Caps        │  │
│  │              │                 │                    │  │
│  │ 65% = 2.0x   │ +0.1% per       │ Max: 50% APR      │  │
│  │ multiplier   │ 1000 blocks     │ Protection        │  │
│  └──────────────┴─────────────────┴─────────────────────┘  │
│                         │                                  │
│  Final Rate = (Base × Ratio Boost) + Time Boost ≤ Cap     │
│  Example: (5% × 2.0x) + 0.5% = 10.5% APR                 │
└────────────────────────────────────────────────────────────┘
```

### Layer 1: Ratio-Based Rate Boost

When the pool enters the danger zone (>60% GREEN), a rate multiplier is applied based on how severe the imbalance is:

Rate multipliers activate when pool composition exceeds thresholds:
- Below threshold: Standard rates apply
- Above threshold: Multiplier scales between minimum and maximum
- Deeper imbalances trigger higher multipliers
- Multipliers remain constant for given pool ratios

### Layer 2: Time-Based Danger Boost

This is separate from the ratio multiplier! The protocol tracks how many blocks the pool has been in the danger zone and adds an additional rate increase:

Time-based adjustments compound with ratio multipliers:
- Duration in danger zone affects rates
- Incremental increases per block create urgency
- Cumulative effect incentivizes rapid correction
- Boost accumulates while imbalance persists

### Layer 3: Maximum Rate Protection

Despite dynamic adjustments, rates are capped to prevent excessive burden:
- Protocol maximum (e.g., 50% APR)
- Asset-specific maximums
- User protection thresholds

## Real-World Scenarios

### Scenario 1: Mild Market Pressure

**Situation**: Large GREEN borrowing spree pushes pool to 62% GREEN

**Protocol Response**:
1. New borrow rates increase from 5% → 7.5%
2. Existing borrowers unaffected until they interact
3. Higher rates discourage additional borrowing
4. Some borrowers repay to avoid higher rates
5. Pool rebalances to 58% within hours
6. Rates normalize back to 5%

**Result**: Smooth correction without drama

### Scenario 2: Sustained Imbalance

**Situation**: Market conditions keep pool at 70% GREEN for 10,000 blocks

**Protocol Response**:
1. Immediate ratio boost: 5% base × 2.25x = 11.25%
2. After 1,000 blocks: 11.25% + 0.1% = 11.35%
3. After 5,000 blocks: 11.25% + 0.5% = 11.75%
4. After 10,000 blocks: 11.25% + 1.0% = 12.25%
5. Total rate = Ratio boost + Time boost
6. Strong incentive to repay debt
7. Arbitrageurs buy cheap GREEN to repay loans
8. Pool gradually rebalances

**Result**: Persistent pressure addressed through combined ratio and time-based response

### Scenario 3: Flash Stress Event

**Situation**: Sudden market move pushes pool to 85% GREEN

**Protocol Response**:
1. Immediate rate spike: 5% → 15% (3x multiplier)
2. New borrows essentially paused (too expensive)
3. Massive arbitrage opportunity created
4. Professional traders quickly rebalance pool
5. Rates drop as quickly as they rose

**Result**: Extreme conditions trigger extreme response, enabling rapid recovery

## Impact on Borrowing

### Rate Updates and Timing

Interest rates update when borrowers interact with the protocol:
- Taking new loans
- Repaying existing debt
- Modifying collateral positions
- Explicit rate refresh calls

This design means existing borrowers are insulated from temporary rate spikes unless they choose to interact. The protocol doesn't force rate updates, giving users control over when to accept new market conditions.

### Economic Incentives

The dynamic rate system creates natural market forces:

**During Pool Stress**:
- Higher borrowing costs discourage new debt
- Existing borrowers incentivized to repay
- Arbitrageurs motivated to rebalance pools
- sGREEN yields increase proportionally

**During Normal Conditions**:
- Competitive rates encourage borrowing
- Stable costs for planning
- Predictable protocol revenue
- Balanced ecosystem growth

## Technical Implementation

### How The Math Works (Simply)

The protocol watches the GREEN/USDC pool and adjusts rates based on two factors:

**Factor 1: How Bad Is It?**
- Just slightly off balance (60% GREEN): Small rate increase
- Getting worse (70% GREEN): Medium rate increase  
- Really bad (80%+ GREEN): Large rate increase

**Factor 2: How Long Has It Been Bad?**
- The longer the pool stays unbalanced, the more urgent the fix becomes
- Every ~30 minutes in the danger zone adds a bit more to rates
- This creates increasing pressure to restore balance

**Real Example**:
- Your normal rate: 5% per year
- Pool hits 70% GREEN: Rate jumps to ~11%
- Stays bad for 3 hours: Rate creeps up to ~12%
- Pool fixed: Rates drop back to 5%

The beauty is this happens automatically - no committees, no votes, just market incentives doing their job.

### Configuration Parameters

Protocol governance can adjust:
- Danger threshold (default: 60%)
- Minimum/maximum multipliers (default: 1.5x-3.0x)
- Time escalation rates
- Maximum rate caps

These parameters are carefully calibrated and rarely need adjustment.

## Benefits of Dynamic Protection

### For Borrowers
- Predictable rate adjustments based on clear metrics
- Protection from prolonged high rates via caps
- Opportunity to earn offsetting yields in sGREEN

### For GREEN Holders
- Stronger peg stability
- Reduced volatility
- Confidence in long-term value

### For the Protocol
- Autonomous stability management
- Reduced governance overhead
- Market-driven equilibrium

## System Monitoring

The protocol exposes key metrics for rate conditions:

- **Pool Ratios**: Real-time GREEN/USDC balance data
- **Current Multipliers**: Active rate adjustments 
- **Historical Data**: Past rate patterns and stress events
- **Blocks in Danger**: Duration of current stress period

## Frequently Asked Questions

**Q: Can rates change while I'm borrowing?**
A: Your rate only updates when you interact with the protocol. Monitor conditions to time your interactions optimally.

**Q: What if rates spike to maximum?**
A: This indicates severe stress and creates massive arbitrage incentives. Historical data shows these conditions resolve quickly.

**Q: How often are pools checked?**
A: Every block (~2 seconds), ensuring near-instant response to changes.

**Q: Can this system be gamed?**
A: The weighted calculations and on-chain implementation make manipulation economically unfeasible.

---

Dynamic Rate Protection represents a breakthrough in stablecoin design, creating a resilient system that maintains stability through market incentives rather than manual intervention.

Next: Learn about [Advanced Borrowing Mechanics](advanced-borrowing-mechanics.md) →