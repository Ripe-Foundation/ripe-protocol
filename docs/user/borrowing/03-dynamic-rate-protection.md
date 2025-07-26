# Dynamic Rate Protection

Dynamic Rate Protection automatically adjusts borrowing rates based on market conditions to maintain [GREEN's](green.md) dollar peg. The system monitors liquidity pool health and responds proportionally to imbalances, working alongside other [stability mechanisms](green.md#stability-mechanisms) to ensure peg maintenance.

## Dynamic Rate Architecture

The system provides:
- Automated response to market conditions
- Proportional scaling based on imbalance severity
- Self-correcting mechanisms as conditions normalize
- Protocol-wide stability maintenance

## How Pool Health Monitoring Works

### The GREEN/USDC Reference Pool

Ripe monitors the primary GREEN/USDC liquidity pool as a real-time indicator of market demand:

The protocol monitors pool composition:
- Balanced state: Equal GREEN/USDC composition  
- Danger zone: GREEN exceeds 60% of pool (rate multipliers activate)

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
1. System takes snapshots of pool state over time
2. Weighted average smooths out temporary spikes
3. If imbalance persists across multiple snapshots:
   - Rates gradually increase based on weighted average
   - Time-based boosts begin accumulating
4. Flash events that quickly reverse have minimal impact
5. Only sustained imbalances trigger significant rate changes

**Result**: System resists manipulation while responding to genuine market stress

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
