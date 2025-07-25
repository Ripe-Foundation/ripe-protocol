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

**Operational Example:**
When a position enters the redemption zone:
- GREEN holders may redeem against the position
- Collateral transfers at par value (no discount)
- Debt reduces by redemption amount
- Position may return to safe collateralization

This mechanism provides gradual deleveraging before liquidation becomes necessary.

## When Liquidation Occurs

### Liquidation Threshold Mechanics

The liquidation threshold determines the minimum collateralization ratio where positions become eligible for liquidation. This parameter defines the required collateral value relative to outstanding debt.

**Threshold Calculation:**
Minimum collateral value equals debt multiplied by (100% / liquidation threshold percentage).

**Parameter Relationships:**
- Higher threshold percentages create tighter collateralization requirements
- A 95% threshold requires 105.3% collateralization
- An 85% threshold requires 117.6% collateralization

The threshold mechanism ensures positions maintain adequate collateral buffers before liquidation becomes possible. These thresholds work in conjunction with [Dynamic Rate Protection](../borrowing/dynamic-rate-protection.md) to maintain system stability.

## Three-Phase Liquidation System

The protocol routes liquidations through specialized mechanisms based on asset type and availability:

### Phase 1: Internal Recovery
- [Stablecoin Burning](stablecoin-burning.md) - GREEN/sGREEN burn mechanisms
- [Endaoment Transfer](endaoment-transfer.md) - Stablecoin treasury routing

### Phase 2: Stability Pool Integration  
- [Stability Pool Swaps](stability-pool-swaps.md) - Collateral-for-debt exchanges
- [Pool Mechanics](stability-pool-mechanics.md) - Pool operations and priorities

### Phase 3: Market Mechanisms
- [Dutch Auctions](dutch-auctions.md) - Time-based discount auctions

## Core Liquidation Components

### **[Liquidation Phases](liquidation-phases.md)**
The three-phase system that routes assets to appropriate liquidation mechanisms.

### **[Liquidation Configuration](liquidation-configuration.md)**
How protocol and asset-specific parameters determine liquidation behavior.

### **[Unified Repayment Formula](unified-repayment-formula.md)**
The mathematical foundation calculating optimal liquidation amounts.

### **[Keepers](keepers.md)**
External actors who execute liquidations, update rates, and manage auctions for economic rewards.

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

### Core Mechanics
1. **[Liquidation Phases](liquidation-phases.md)** - Three-phase asset routing system
2. **[Liquidation Configuration](liquidation-configuration.md)** - Parameter framework
3. **[Unified Repayment Formula](unified-repayment-formula.md)** - Mathematical calculations

### Specific Mechanisms
1. **[Stablecoin Burning](stablecoin-burning.md)** - Phase 1 GREEN/sGREEN mechanism
2. **[Endaoment Transfer](endaoment-transfer.md)** - Phase 1 stablecoin handling
3. **[Stability Pool Swaps](stability-pool-swaps.md)** - Phase 2 liquidation method
4. **[Stability Pool Mechanics](stability-pool-mechanics.md)** - Pool operations and economics
5. **[Dutch Auctions](dutch-auctions.md)** - Phase 3 market mechanism

### System Participants
1. **[Keepers](keepers.md)** - Decentralized actors maintaining protocol health

## System Design Principles

The liquidation system balances multiple objectives:
- Rapid debt resolution to maintain protocol solvency
- Value preservation through phased approaches
- Market efficiency via competitive mechanisms
- Decentralized execution without central control

These mechanisms work together to create a robust system that handles diverse asset types while maintaining GREEN stability.