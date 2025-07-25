# Multi-Collateral System

Ripe Protocol's multi-collateral system transforms DeFi lending through portfolio-based borrowing. The system unifies multiple assets into a single loan position backed by an entire collateral portfolio.

## The Lending Landscape

### Isolated Lending Markets

Traditional lending protocols create separate borrowing positions for each asset:

- Deposit WETH → Borrow up to 80% in one position
- Deposit USDC → Borrow up to 90% in another position
- Monitor and manage each position independently
- One position's liquidation doesn't help the others

This approach creates complexity and isolated risk exposure. Price volatility in one asset triggers liquidation regardless of other healthy positions.

### Money Markets (Aave, Moonwell, etc.)

Modern money markets already allow multiple assets backing a single loan position. However, they face a critical limitation: **they can only support conservative, blue-chip assets**.

Why? Because in pooled lending:
- All depositors share bad debt risk
- Single asset failures affect entire pools
- Conservative parameters maintain pool safety
- Volatile assets create systemic risks

This limits these protocols to:
- Major cryptocurrencies (ETH, BTC)
- Established stablecoins
- Select blue-chip DeFi tokens
- Highly liquid, battle-tested assets only

## Ripe's Solution: Universal Collateral, Individual Risk

Ripe combines the best of both worlds: the simplicity of a single loan position with the ability to accept virtually any asset as collateral.

**The Key Difference**: Ripe isolates risk at the individual borrower level, not the protocol level. Your collateral backs only your loan, not a shared pool. This enables:

- Support for emerging assets (meme coins, gaming tokens)
- Acceptance of yield-bearing positions
- Integration of tokenized real-world assets
- Future-proofing for new asset types

Example portfolio composition:
- 10 WETH ($20,000) - Blue-chip asset
- 5,000 USDC ($5,000) - Stablecoin
- 0.5 WBTC ($15,000) - Blue-chip asset
- 100,000 PEPE ($100) - Volatile asset
- 50 stETH ($100,000) - Yield-bearing asset
- 1,000 GAME ($500) - Gaming token

Result: Single unified GREEN loan position

This architecture isolates individual risk profiles, enabling support for assets unsuitable for pooled lending protocols.

### System Mechanics

```
TRADITIONAL ISOLATED LENDING
├── ETH Position: $10k → Max borrow $8k (80% LTV)
├── USDC Position: $5k → Max borrow $4.5k (90% LTV)
└── WBTC Position: $15k → Max borrow $12k (80% LTV)
    Total: 3 separate loans, isolated risk

RIPE MULTI-COLLATERAL SYSTEM
┌─────────────────────────────────────────────────┐
│              UNIFIED POSITION                   │
│  ┌─────────┬─────────┬─────────┬─────────────┐  │
│  │   ETH   │  USDC   │  WBTC   │    PEPE     │  │
│  │  $10k   │   $5k   │  $15k   │    $100     │  │
│  │  80%LTV │ 90%LTV  │ 80%LTV  │   50%LTV    │  │
│  └─────────┴─────────┴─────────┴─────────────┘  │
│              ↓ WEIGHTED AVERAGE ↓               │
│        Single GREEN Loan: $24.1k capacity      │
│        Blended Rate: 5.2% APR                   │
│        Unified Health Factor: 1.25              │
└─────────────────────────────────────────────────┘
```

1. **Multi-Asset Deposits**: Various assets form collateral basket
2. **Aggregated Borrowing Power**: Protocol calculates total capacity
3. **Unified Debt Position**: GREEN borrowed against entire portfolio
4. **Cross-Asset Support**: Strong assets buffer weaker positions

## Benefits of Multi-Collateral

### 1. Reduced Liquidation Risk

Asset diversification reduces liquidation risk:

- **Isolated System**: 20% WETH decline triggers liquidation
- **Unified System**: 20% WETH decline absorbed by portfolio

Portfolio diversity provides systemic protection.

### 2. Simplified Management

Unified position management:
- Single position monitoring
- Consolidated health metrics
- Unified repayment structure
- Aggregate liquidation threshold

### 3. Capital Efficiency

All assets contribute to borrowing capacity:
- Blue-chip assets maximize loan-to-value
- Stablecoins enhance stability
- Small positions remain productive
- Full capital utilization

### 4. Dynamic Optimization

Automatic position optimization includes:
- Weighted average interest rates
- Blended risk parameters
- Optimized liquidation sequencing
- Efficient collateral utilization

## Architectural Comparison

### Isolated Lending Models
Traditional protocols create separate positions per asset, requiring independent management and limiting capital efficiency. Each position faces liquidation risk independently.

### Pooled Money Markets
Shared risk pools restrict asset acceptance to established, low-volatility tokens. System-wide risk sharing prevents inclusion of experimental or volatile assets.

### Ripe's Unified System
Individual risk isolation enables universal asset acceptance while portfolio aggregation creates capital efficiency. All assets contribute to a single position with optimized parameters.

The architecture supports future expansion to non-fungible tokens and tokenized real-world assets without compromising existing functionality.

The multi-collateral architecture maximizes capital efficiency through portfolio aggregation while maintaining individual risk isolation, creating a resilient lending system adaptable to diverse asset types. This system's robustness enables the [three-phase liquidation system](../liquidations/01-liquidation-phases.md) to handle any asset type safely.