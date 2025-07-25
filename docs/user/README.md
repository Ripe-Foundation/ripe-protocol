# Ripe Protocol Documentation

This documentation explains the fundamental mechanisms and concepts underlying Ripe Protocol's multi-collateral lending system.

## Core Components

Understanding Ripe Protocol requires familiarity with these interconnected systems:

### 1. [GREEN Stablecoin](green.md)
The heart of Ripe - GREEN is the protocol's native overcollateralized stablecoin, minted through borrowing and maintained at dollar parity through multiple stability mechanisms.

### 2. [Collateral Assets](collateral-assets/README.md)
The foundation - Ripe's multi-collateral system enables multiple assets to back a single loan position, transforming how DeFi lending operates.

### 3. [Borrowing](borrowing/README.md)
The core function - Protocol's borrowing mechanism mints GREEN against deposited collateral through an overcollateralized debt system.

### 4. [Liquidations](liquidations/README.md)
The safety net - A three-phase liquidation system maintains protocol solvency while minimizing borrower losses through progressive mechanisms.

### 5. [Savings GREEN (sGREEN)](sgreen.md)
Value accrual - sGREEN represents the yield-bearing version of GREEN, automatically accruing value through protocol revenue distribution.

### 6. [Endaoment](endaoment.md)
The engine - Protocol treasury manages assets, maintains GREEN stability, and generates yield across DeFi strategies.

### 7. [RIPE Governance](ripe-governance.md)
Community control - RIPE token holders accumulate governance power through time-locked deposits, preparing for decentralized protocol management.

### 8. [Bonds](bonding.md)
Growth mechanism - Bond system exchanges stablecoins for RIPE tokens, building Endaoment reserves and liquidity.

## Protocol Architecture

```
                    RIPE PROTOCOL SYSTEM OVERVIEW
┌─────────────────────────────────────────────────────────────────────────────┐
│                                USERS                                        │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │   BORROWERS      │  │     LENDERS      │  │     TRADERS      │          │
│  │ (Multi-Asset     │  │  (sGREEN/Pools)  │  │   (GREEN/DEX)    │          │
│  │  Collateral)     │  │                  │  │                  │          │
│  └─────────┬────────┘  └─────────┬────────┘  └─────────┬────────┘          │
└───────────┼─────────────────────┼─────────────────────┼─────────────────────┘
            │                     │                     │
            v                     v                     v
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CORE PROTOCOL                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │  MULTI-ASSET    │  │   GREEN MINT/   │  │   LIQUIDATION   │             │
│  │   VAULTS        │  │     BURN        │  │     SYSTEM      │             │
│  │                 │  │                 │  │                 │             │
│  │ • Simple ERC20  │  │ • Overcollat.   │  │ • Phase 1: Burn │             │
│  │ • Yield-bearing │  │ • Dynamic Rates │  │ • Phase 2: Pools│             │
│  │ • Stability Pool│  │ • Peg Stability │  │ • Phase 3: Auct.│             │
│  │ • Governance    │  │                 │  │                 │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────┘
            │                     │                     │
            v                     v                     v
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SUPPORT SYSTEMS                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │   ENDAOMENT     │  │   ORACLES &     │  │   GOVERNANCE    │             │
│  │   TREASURY      │  │   KEEPERS       │  │   & BONDS       │             │
│  │                 │  │                 │  │                 │             │
│  │ • Asset Mgmt    │  │ • Price Feeds   │  │ • RIPE Voting   │             │
│  │ • Yield Gen     │  │ • Liquidations  │  │ • Bond Sales    │             │
│  │ • Peg Defense   │  │ • Rate Updates  │  │ • Parameters    │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Multi-Collateral Framework
Ripe unifies multiple collateral assets into single loan positions, enabling portfolio-based borrowing rather than isolated markets. This architecture supports diverse asset types while maintaining individual risk isolation.

### GREEN Stablecoin System
GREEN maintains its dollar peg through overcollateralization, dynamic interest rates, redemption mechanisms, and automated market operations managed by the Endaoment treasury.

### Liquidation Architecture
The three-phase system progressively attempts:
1. Internal recovery through token burning and treasury transfers
2. Stability pool exchanges at predetermined discounts
3. Dutch auctions for remaining collateral

This graduated approach minimizes market impact while ensuring protocol solvency.

### Value Accrual Mechanisms
The protocol generates value through:
- Interest payments flowing to sGREEN holders
- Liquidation fees captured by stability pools
- Treasury yield generation via DeFi strategies
- Bond sales building protocol reserves

## Key Concepts

### Unified Positions
Unlike traditional lending protocols, Ripe combines all collateral into a single borrowing position with weighted-average terms based on asset contributions.

### Risk Isolation
Each user's collateral backs only their own debt, preventing systemic contagion and enabling support for diverse asset types.

### Automated Stability
Market-driven mechanisms maintain GREEN's peg without governance intervention, using economic incentives to self-correct imbalances.

## Additional Resources

### Quick Access Documents

#### [Quick Reference Guide](quick-reference.md)
Essential parameters, formulas, and thresholds for protocol operations.

#### [Frequently Asked Questions](faq.md)
Comprehensive answers to common questions about protocol mechanics and safety features.

#### [Glossary](glossary.md)
Definitions of key terms and concepts used throughout the protocol documentation.

### For Developers

#### [Technical Documentation](../technical/README.md)
Implementation details and smart contract specifications for developers.

## Getting Started

### New to Ripe Protocol?
1. **Start with [GREEN Stablecoin](green.md)** - Understand the core asset
2. **Review [Multi-Collateral System](collateral-assets/multi-collateral-system.md)** - Learn the unified approach
3. **Check [Quick Reference](quick-reference.md)** - Get key parameters
4. **Browse [FAQ](faq.md)** - Address common questions

### Ready to Use the Protocol?
1. **[Supported Assets](collateral-assets/supported-assets.md)** - See what you can deposit
2. **[Deposit Mechanics](collateral-assets/deposit-withdrawal-mechanics.md)** - Understand the process
3. **[Borrowing Mechanics](borrowing/borrowing-mechanics.md)** - Learn to mint GREEN
4. **[Liquidation System](liquidations/README.md)** - Know the safety mechanisms