# Liquidations

This section details Ripe Protocol's three-phase liquidation system, explaining how different mechanisms work together to maintain protocol solvency while minimizing user losses.

The liquidation system maintains protocol solvency through a multi-phase mechanism designed to minimize borrower losses while ensuring debt repayment.

## Liquidation Overview

Liquidation occurs when borrowing positions breach minimum collateralization thresholds. The protocol executes collateral liquidation to repay outstanding debt, maintaining system stability and GREEN's peg.

The system's architecture enables:
- Bad debt prevention through timely intervention
- GREEN stability maintenance via supply reduction
- Protocol solvency protection
- Loss minimization through graduated approaches

## Redemption Mechanism

### Pre-Liquidation Protection

The redemption threshold creates a buffer zone before liquidation becomes possible. In this zone, GREEN holders can redeem tokens against collateral positions, providing an automatic deleveraging mechanism.

**Redemption Properties:**
- Activates at redemption threshold (below liquidation threshold)
- Enables 1:1 value exchange between GREEN and collateral
- Reduces position debt without liquidation penalties
- Operates automatically without borrower intervention

**Peg Stabilization Function:**
Importantly, this mechanism also serves as a peg stabilization tool. During market stress when GREEN trades below $1:
- Arbitrageurs can buy discounted GREEN on the market
- Redeem it at $1 par value against collateral positions
- This creates buying pressure that helps restore the peg
- Only profitable when GREEN is under peg, creating automatic stabilization

**Operational Example:**
When a position enters the redemption zone:
- GREEN holders may redeem against the position
- Collateral transfers at par value (no discount)
- Debt reduces by redemption amount
- Position may return to safe collateralization

This dual mechanism provides both gradual deleveraging for at-risk positions and market-driven peg stability during periods of stress.

## When Liquidation Occurs

### Liquidation Threshold Mechanics

The liquidation threshold determines when forced liquidation occurs. Unlike LTV which calculates how much you can borrow, the liquidation threshold works inversely - it defines the **minimum collateral required** for your debt level.

**How It Works:**
```
Minimum Collateral = Debt × 100% / Liquidation Threshold%
```

**Real Example:**
```
Your debt: $8,000 GREEN
Liquidation threshold: 95%
Liquidation triggers when collateral < $8,421
(Because $8,000 × 100% / 95% = $8,421)
```

**Risk Progression:**
Starting with $10,000 collateral and $7,000 debt:

1. **Healthy Zone** (Collateral > $8,750)
   - Below maximum LTV
   - No risk of liquidation
   
2. **Redemption Zone** (Collateral $7,778 - $7,368)
   - Redemption threshold: 90%
   - Others can redeem your collateral
   - Warning to add collateral or repay
   
3. **Liquidation Zone** (Collateral < $7,368)
   - Liquidation threshold: 95%
   - Three-phase liquidation activates

As your collateral value drops OR debt grows from interest, you move through these zones. Higher threshold percentages mean tighter requirements and less room for error.

## Three-Phase Liquidation System

The protocol routes liquidations through specialized mechanisms based on asset type and availability:

### Phase 1: Internal Recovery
User's own protocol deposits are used first:
- **[Stablecoin Burning](01-stablecoin-burning.md)** - GREEN/sGREEN burn mechanisms
- **[Endaoment Transfer](02-endaoment-transfer.md)** - Stablecoin and GREEN LP routing

### Phase 2: Stability Pool Integration  
Collateral swaps with stability pool participants:
- **[Stability Pool Swaps](03-stability-pool-swaps.md)** - Collateral-for-debt exchanges
- **[Pool Mechanics](04-stability-pool-mechanics.md)** - Pool operations and priorities

### Phase 3: Market Mechanisms
All other assets through time-based auctions:
- **[Dutch Auctions](05-dutch-auctions.md)** - Increasing discount mechanisms

## Supporting Systems

### **[Keepers](06-keepers.md)**
External actors who execute liquidations, update rates, and manage auctions for economic rewards.

### **[Unified Repayment Formula](07-unified-repayment-formula.md)**
The mathematical foundation calculating optimal liquidation amounts.

### **[Liquidation Configuration](08-liquidation-configuration.md)**
How protocol and asset-specific parameters determine liquidation behavior.

## System Properties

### Concurrent Processing
All three phases operate simultaneously, with assets routed based on type and availability. The system prioritizes methods that minimize market impact.

### Partial Liquidation Design
Liquidations target position health restoration rather than complete closure, preserving borrower value where possible.

### Market Integration
Stability pools provide immediate liquidity while dutch auctions ensure market-based price discovery for remaining collateral.

### Decentralized Execution
Keeper networks compete to execute liquidations, ensuring rapid response without central coordination.

## Documentation Structure

### Phase 1: Internal Recovery
1. **[Stablecoin Burning](01-stablecoin-burning.md)** - GREEN/sGREEN burn mechanisms
2. **[Endaoment Transfer](02-endaoment-transfer.md)** - Stablecoin handling

### Phase 2: Stability Pool Integration
3. **[Stability Pool Swaps](03-stability-pool-swaps.md)** - Collateral-for-debt exchanges
4. **[Stability Pool Mechanics](04-stability-pool-mechanics.md)** - Pool operations and economics

### Phase 3: Market Mechanisms
5. **[Dutch Auctions](05-dutch-auctions.md)** - Time-based price discovery

### Supporting Systems
6. **[Keepers](06-keepers.md)** - Decentralized actors maintaining protocol health
7. **[Unified Repayment Formula](07-unified-repayment-formula.md)** - Mathematical calculations
8. **[Liquidation Configuration](08-liquidation-configuration.md)** - Parameter framework

## System Design Principles

The liquidation system balances multiple objectives:
- Rapid debt resolution to maintain protocol solvency
- Value preservation through phased approaches
- Market efficiency via competitive mechanisms
- Decentralized execution without central control

These mechanisms work together to create a robust system that handles diverse asset types while maintaining GREEN stability.