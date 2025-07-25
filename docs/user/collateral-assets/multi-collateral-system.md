# Multi-Collateral System

Ripe Protocol's multi-collateral system represents a fundamental shift in how DeFi lending works. Instead of managing multiple isolated positions across different assets, you maintain a single, unified loan backed by your entire portfolio.

## The Lending Landscape

### Isolated Lending Markets

Traditional lending protocols create separate borrowing positions for each asset:

- Deposit WETH → Borrow up to 80% in one position
- Deposit USDC → Borrow up to 90% in another position
- Monitor and manage each position independently
- One position's liquidation doesn't help the others

This approach creates unnecessary complexity and risk. A temporary price dip in one asset could liquidate that position, even if your other collateral remains healthy.

### Money Markets (Aave, Moonwell, etc.)

Modern money markets already allow multiple assets backing a single loan position. However, they face a critical limitation: **they can only support conservative, blue-chip assets**.

Why? Because in pooled lending:
- All depositors share the risk of bad debt
- One toxic asset can contaminate the entire pool
- Conservative parameters are necessary for pool safety
- New or volatile assets pose systemic risks

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

```
Your Portfolio:
├── 10 WETH ($20,000)        ← Blue-chip
├── 5,000 USDC ($5,000)      ← Stablecoin
├── 0.5 WBTC ($15,000)       ← Blue-chip
├── 100,000 PEPE ($100)      ← Meme coin (not possible in Aave!)
├── 50 stETH ($100,000)      ← Yield-bearing
└── 1,000 GAME ($500)        ← Gaming token
    
= One GREEN Loan Position
```

This architecture means one user's risky collateral choices don't affect other users, allowing Ripe to support assets that would be too dangerous for pooled lending protocols.

### How It Works

1. **Deposit Any Combination**: Add different assets to your collateral basket
2. **Unified Borrowing Power**: The protocol calculates your total borrowing capacity
3. **Single Debt Position**: Borrow GREEN against your entire portfolio
4. **Shared Risk Buffer**: Strong assets protect weaker ones

## Benefits of Multi-Collateral

### 1. Reduced Liquidation Risk

When assets work together, temporary price movements become less dangerous:

- **Isolated System**: WETH drops 20% → Position liquidated
- **Ripe System**: WETH drops 20% → Other assets maintain overall health

Your portfolio's diversity becomes your protection.

### 2. Simplified Management

Instead of juggling multiple loans:
- One position to monitor
- One debt health status to track
- One repayment to manage
- One liquidation threshold

### 3. Capital Efficiency

Every asset contributes to your borrowing power:
- Blue-chip assets provide high loan-to-value
- Stablecoins add stability
- Smaller positions still contribute
- No asset sits idle

### 4. Dynamic Optimization

The protocol automatically optimizes your position:
- Weighted average interest rates
- Blended risk parameters
- Optimal liquidation sequencing
- Efficient collateral utilization

## Real-World Example

Let's see how Sarah's diverse portfolio works across different protocols:

**Sarah's Portfolio:**
- 5 WETH (worth $10,000) - 80% LTV
- 10,000 USDC - 90% LTV
- 50,000 SHIB (worth $500) - 50% LTV
- 2 stETH (worth $4,000) - 75% LTV
- 1M PEPE (worth $1,000) - 40% LTV

**Isolated Lending (Compound-style):**
- WETH position: Can borrow $8,000
- USDC position: Can borrow $9,000
- SHIB position: Can borrow $250
- stETH position: Can borrow $3,000
- PEPE: Not supported
- Total: $20,250 across 4 separate loans

**Money Market (Aave/Moonwell):**
- WETH: ✓ Accepted
- USDC: ✓ Accepted
- SHIB: ✗ Too risky for the pool
- stETH: ✓ Accepted (select protocols)
- PEPE: ✗ Not established enough
- Result: Can only use $23,000 of $25,500 in assets

**Ripe Protocol (Current):**
- All assets accepted and working together
- Combined collateral: $25,500
- Weighted average LTV: ~78%
- Single borrowing capacity: $19,650
- One loan to manage
- Full portfolio utilization

**Ripe Protocol (Future with NFTs):**
- Will include NFT collateral
- Even more diverse portfolios
- Tokenized real-world assets
- True universal collateral

## Important Considerations

### Risk Weighting

Not all assets are equal. The protocol applies different parameters based on:
- Asset volatility
- Liquidity depth
- Historical performance
- Market conditions

Your overall terms reflect the weighted average of your portfolio.

### Liquidation Priority

If liquidation becomes necessary, the protocol intelligently chooses which assets to liquidate first, optimizing for:
- Minimal user loss
- Protocol safety
- Market impact
- Gas efficiency

### Adding and Removing Collateral

You can adjust your collateral mix anytime:
- Add new asset types to improve terms
- Remove excess collateral above safe thresholds
- Rebalance for optimal ratios
- Respond to market conditions

The multi-collateral system is designed to work with your natural portfolio, not against it. Whether you hold blue-chip assets, stablecoins, yield-bearing tokens, or emerging assets, they all contribute to your borrowing power in Ripe.

Next: Learn about [Asset Categories](supported-assets.md) →