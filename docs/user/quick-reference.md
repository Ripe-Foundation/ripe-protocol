# Quick Reference Guide

Essential parameters, formulas, and thresholds for Ripe Protocol operations.

## Core Concepts

### Asset Parameters by Category

| Asset Type | Typical LTV | Liquidation Threshold | Interest Rate Range | Example Assets |
|------------|-------------|----------------------|---------------------|----------------|
| **Stablecoins** | 85-95% | 90-98% | 2-5% APR | USDC, USDT, USDS |
| **Blue-Chip Crypto** | 75-85% | 80-90% | 4-8% APR | WETH, WBTC, cbBTC |
| **Yield-Bearing** | 70-80% | 75-85% | 3-7% APR | stETH, rETH, aUSDC |
| **Established DeFi** | 60-75% | 70-85% | 6-12% APR | UNI, LINK, AAVE |
| **Emerging Assets** | 40-60% | 55-75% | 10-25% APR | PEPE, SHIB, Gaming tokens |
| **NFTs** | 30-50% | 60-70% | 8-20% APR | BAYC, Punks, Art NFTs |
| **RWAs** | 70-95% | 80-98% | 1-8% APR | Tokenized T-bills, Gold |

### Key Formulas

#### Borrowing Power Calculation
```
Borrowing Power = Σ(Asset Value × Asset LTV)
```

#### Weighted Parameter Calculation
```
Weight = Asset's Max Borrowing Power / Total Borrowing Power
Weighted Parameter = Σ(Asset Parameter × Weight)
```

#### Health Factor
```
Health Factor = Total Collateral Value / (Outstanding Debt / Liquidation Threshold)
```
- **Above 1.0**: Position is healthy
- **Below 1.0**: Position eligible for liquidation

#### sGREEN Exchange Rate
```
Exchange Rate = Total GREEN in Pool / Total sGREEN Supply
```
- Rate can only increase or remain stable, never decrease

## System Thresholds

### Liquidation Triggers

| Metric | Threshold | Action |
|--------|-----------|--------|
| **Health Factor** | < 1.0 | Liquidation eligible |
| **Redemption Zone** | Health Factor 1.0-1.05 | GREEN redemption possible |
| **Pool Imbalance** | GREEN > 60% of pool | Dynamic rates activate |
| **Critical Imbalance** | GREEN > 80% of pool | Maximum rate multipliers |

### Dynamic Rate Protection

| Pool GREEN Ratio | Rate Multiplier | Urgency Level |
|------------------|----------------|---------------|
| < 60% | 1.0x | Normal |
| 60-65% | 1.5x | Warning |
| 65-70% | 2.0x | Stressed |
| 70-75% | 2.5x | Critical |
| > 75% | 3.0x | Emergency |

**Time Boost**: Additional rate increase based on blocks in danger zone
- Typical increment: +0.1% APR per 1,000 blocks

## Vault Types

| Vault Type | Purpose | Assets | Key Features |
|------------|---------|--------|--------------|
| **Simple ERC-20** | Standard tokens | WETH, USDC, WBTC | 1:1 deposit/withdrawal |
| **Share-Based** | Yield-bearing | stETH, aTokens, LP tokens | Captures yields/rebases |
| **Stability Pool** | Liquidation backstop | sGREEN only | Earns liquidation premiums |
| **Governance** | Protocol voting | RIPE only | Time-locked with multipliers |

## Liquidation System

### Three-Phase Process

| Phase | Mechanism | Assets | Discount | Speed |
|-------|-----------|--------|----------|-------|
| **Phase 1** | Internal recovery | GREEN, sGREEN, Stablecoins | None | Instant |
| **Phase 2** | Stability pools | Most crypto assets | 5-15% | Instant |
| **Phase 3** | Dutch auctions | All remaining | Variable | Time-based |

### Liquidation Penalties

| Asset Category | Typical Penalty |
|----------------|----------------|
| Stablecoins | 5% |
| Blue-chip crypto | 8-12% |
| Volatile assets | 10-20% |
| NFTs | 15-25% |

## Delegation Permissions

| Permission Type | Capability | Risk Level |
|----------------|------------|------------|
| **Withdraw** | Remove collateral | Medium |
| **Borrow** | Mint GREEN | High |
| **Stability Claims** | Harvest pool rewards | Low |
| **Loot Claims** | Collect RIPE rewards | Low |

**Security**: All funds always route to original owner address

## Fee Structure

| Action | Fee Type | Typical Rate |
|--------|----------|--------------|
| **Loan Origination** | Daowry fee | ~0.5% of borrowed amount |
| **Liquidation** | Penalty fee | 5-25% depending on asset |
| **Stability Pool** | No fees | Earn premiums instead |
| **Bond Purchase** | No fees | Market-based pricing |

## Important Addresses & Identifiers

### Vault IDs
- Primary vaults typically use ID: 0
- Stability pool vault: Special ID
- Governance vault: Special ID
- Asset-specific vaults: Sequential numbering

### Permission Flags
```solidity
struct Permissions {
    bool canWithdraw;    // Collateral withdrawal
    bool canBorrow;      // GREEN minting
    bool canClaimStab;   // Stability pool rewards
    bool canClaimLoot;   // RIPE protocol rewards
}
```

## Rate Environment Examples

### Normal Market Conditions
- Pool ratio: GREEN 45% / USDC 55%
- Rate multiplier: 1.0x
- Example rates: USDC 3%, WETH 5%, PEPE 15%

### Stressed Market Conditions
- Pool ratio: GREEN 72% / USDC 28%
- Rate multiplier: 2.5x + time boost
- Example rates: USDC 8%, WETH 13%, PEPE 40%

## Position Health Examples

### Healthy Position
```
Collateral: $10,000 WETH (80% LTV)
Debt: $6,000 GREEN
Health Factor: 1.33
Status: Safe borrowing capacity remaining
```

### At-Risk Position
```
Collateral: $10,000 WETH (85% liquidation threshold)
Debt: $8,400 GREEN
Health Factor: 1.01
Status: Near liquidation, consider deleveraging
```

### Liquidation-Eligible Position
```
Collateral: $10,000 WETH
Debt: $8,600 GREEN
Health Factor: 0.99
Status: Liquidation may begin
```

## Time Parameters

| Action | Duration |
|--------|----------|
| **Governance voting** | 3-7 days |
| **Rate updates** | Immediate on interaction |
| **Liquidation processing** | Blocks to minutes |
| **Dutch auction decay** | Hours |
| **Bond epoch** | Days to weeks |
| **Governance timelock** | 24-48 hours |

## Useful Calculations

### Maximum Safe Borrowing
```
Max Safe Debt = (Collateral Value × Liquidation Threshold) × Safety Buffer
Safety Buffer recommendation: 0.90-0.95 (10-5% cushion)
```

### Liquidation Price Calculation
```
Liquidation Price = Current Price × (Outstanding Debt / (Collateral Amount × Liquidation Threshold))
```

### Break-Even sGREEN Holding
```
Break-Even Period = Current Exchange Rate Premium / Annual Yield Rate
```

## Emergency Procedures

### Position at Risk
1. Monitor health factor closely
2. Add collateral or repay debt
3. Consider delegation for automated management
4. Review liquidation thresholds

### Market Stress Response
1. Expect dynamic rate increases
2. Consider deleveraging volatile positions
3. Monitor pool ratios and multipliers
4. Evaluate arbitrage opportunities

### Protocol Issues
1. Check official announcements
2. Review governance proposals
3. Consider emergency exits if needed
4. Monitor technical documentation updates

## Protocol Comparisons

### Ripe vs Other Lending Protocols

| Feature | Ripe Protocol | Aave/Compound | MakerDAO | Isolated Markets |
|---------|---------------|---------------|----------|------------------|
| **Collateral Model** | Multi-asset unified | Multi-asset pooled | Single-asset isolated | Single-asset isolated |
| **Risk Isolation** | Individual borrower | Shared pool | Individual borrower | Individual borrower |
| **Asset Diversity** | Universal support | Conservative only | Limited selection | Asset-specific |
| **Position Management** | Single unified loan | Multiple positions | Multiple CDPs | Multiple positions |
| **Liquidation** | Three-phase system | Pool-based | Auction-based | Asset-specific |
| **Yield Preservation** | Full yield capture | No yield on collateral | No yield on collateral | No yield on collateral |
| **Parameter Flexibility** | Asset-specific + weighted | Pool-wide parameters | Vault-specific | Market-specific |

### Token Comparison

| Token | Purpose | Yield Generation | Peg Mechanism | Use Cases |
|-------|---------|------------------|---------------|-----------|
| **GREEN** | Protocol stablecoin | No (stable) | Multi-layered stability | Borrowing, trading, DeFi |
| **sGREEN** | Yield-bearing GREEN | Yes (protocol revenue) | Tracks GREEN + yield | Yield farming, liquidity |
| **RIPE** | Governance token | Via staking/delegation | Free floating | Voting, rewards, bonds |

### Vault Type Comparison

| Vault Type | Best For | Complexity | Yield Capture | Gas Efficiency |
|------------|----------|------------|---------------|----------------|
| **Simple ERC-20** | Standard tokens | Low | No | High |
| **Share-Based** | Yield-bearing assets | Medium | Yes | Medium |
| **Stability Pool** | Liquidation participation | High | Yes + premiums | Medium |
| **Governance** | Protocol participation | Medium | Yes + voting power | Low |

---

For comprehensive details, refer to the full documentation sections for each topic.