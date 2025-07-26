# Collateral Assets

Ripe Protocol transforms traditional lending by creating a unified multi-collateral system where all your deposited assets work together to back a single GREEN loan. Instead of managing multiple isolated positions, your entire portfolio — from stablecoins to blue-chip crypto to emerging tokens — combines into one powerful borrowing position. Every asset you deposit contributes to your total borrowing capacity, creating unprecedented capital efficiency while maintaining individual risk isolation.

## Why Ripe's Approach is Different

### The Problem with Traditional Lending

Most DeFi protocols force you into one of two suboptimal models:

**Isolated Markets**: Each asset creates a separate loan position
- Deposit ETH → Manage one position
- Deposit USDC → Manage another position  
- One liquidation doesn't help the others
- Complex management across multiple positions

**Pooled Lending**: Shared risk limits asset acceptance
- Only blue-chip assets allowed
- Your deposits back everyone's loans
- Bad actors affect all depositors
- Innovation stifled by conservative parameters

### Ripe's Solution: Best of Both Worlds

Ripe combines portfolio efficiency with individual risk isolation:

```
Your Multi-Asset Portfolio = One GREEN Loan
┌───────────────────────────────────────────┐
│  ETH    USDC    WBTC    PEPE    stETH     │
│  $10k   $5k     $15k    $100    $50k      │
│  80%    90%     80%     50%     85%       │ <- Individual LTVs
│  ↓      ↓       ↓       ↓       ↓         │
│  ═══════════════════════════════════════  │
│           COMBINED COLLATERAL             │
│           Total Value: $80,100            │
│           Borrowing Power: $67,585        │
│                     ↓                     │
│         SINGLE GREEN LOAN POSITION        │
│         Up to $67,585 GREEN               │
│                                           │
│  • One loan, one interest rate            │
│  • One health factor to monitor           │
│  • All assets contribute to backing       │
│  • Your risk isolated from others         │
└───────────────────────────────────────────┘
```

This architecture enables support for virtually any asset while maintaining protocol safety — your collateral backs only your loans, not a shared pool.

## The Universe of Supported Assets

Ripe's extensible architecture can support a vast and growing universe of tokenized value:

**1. Stablecoins** - The foundation of stability
- **USDC, USDT**: Major centralized stablecoins with deep liquidity
- **USDS**: Decentralized stablecoin from Sky Protocol
- **Yield-bearing stables**: Interest-earning stable assets
- Typically offer 80-90% LTV ratios due to price stability

**2. Blue-Chip Crypto** - Established digital assets
- **WETH**: Wrapped Ethereum, the DeFi standard
- **WBTC/cbBTC**: Bitcoin representations on Ethereum
- **Major DeFi tokens**: AAVE, UNI, CRV, and other protocol tokens
- **Layer 1 tokens**: SOL, AVAX, MATIC (when bridged)
- Provide strong borrowing power with proven track records

**3. Yield-Bearing Assets** - Earn while you borrow
- **Liquid staking**: stETH, rETH, cbETH continue earning staking rewards
- **LP tokens**: Uniswap, Curve, Balancer positions keep earning fees
- **Vault tokens**: Yearn, Aave aTokens compound while collateralized
- Share-based accounting preserves all accumulated yields

**4. Tokenized Real-World Assets** - Bridging traditional finance
- **Securities**: Tokenized stocks, bonds, ETFs
- **Commodities**: Gold, silver, oil representations
- **Real estate**: Property-backed tokens
- **Carbon credits**: Environmental assets
- Special handling for regulatory compliance

**5. NFTs & Unique Assets** - Beyond fungible tokens
- **Blue-chip collections**: Punks, Apes, Penguins as collateral
- **Art NFTs**: Generative and 1/1 pieces
- **Gaming items**: Weapons, land, characters
- **Music/Media**: Royalty-bearing NFTs
- Lower LTVs (30-50%) but still productive capital

**6. Emerging Digital Assets** - The new frontier
- **Prediction shares**: Tokenized prediction market positions
- **Meme coins**: PEPE, SHIB, and community tokens
- **Social tokens**: Creator coins and DAO tokens
- **AI tokens**: Emerging AI protocol tokens
- Conservative parameters reflect higher volatility

## How Deposits Work

### The Deposit Process

1. **Asset Selection**: Choose from any supported token
2. **Automatic Vault Routing**: Protocol selects optimal vault type
3. **Instant Activation**: Start earning rewards immediately
4. **Portfolio Building**: Add more assets anytime

### Vault Types Explained

Ripe automatically routes your deposits to specialized vaults:

**Simple Erc20 Vaults** - Standard tokens (ETH, USDC, most assets)
- Direct 1:1 balance tracking
- Simple deposit/withdraw mechanics
- Most common vault type

**Rebase Erc20 Vaults** - Yield-bearing assets (stETH, aTokens)
- Share-based accounting preserves yields
- Compound earnings while deposited
- No opportunity cost from collateralization

**Special Purpose Vaults**
- **[Ripe Gov Vault](08-governance.md)**: Lock RIPE tokens for governance power
- **[Stability Pools](05-stability-pools.md)**: Earn from liquidations with sGREEN/LP tokens
- **Future Vaults**: NFTs, RWAs, and emerging asset types

### The Power of Extensibility

Ripe's vault system is designed to be infinitely extensible. As new asset types emerge or special requirements arise, the protocol can deploy new vault implementations without disrupting existing operations:

- **Custom Logic**: Each vault type can implement specific behaviors for its assets
- **Future-Proof**: Support for assets that don't exist yet
- **Seamless Integration**: New vaults plug into the existing ecosystem
- **Innovation Ready**: From NFT fractionalization to real-world asset settlements

This extensibility ensures Ripe can adapt to any tokenized value the future brings — whether it's gaming assets requiring special metadata, regulated securities needing compliance hooks, or entirely new token standards we haven't imagined yet.

The protocol automatically selects the right vault — you just deposit.

### Deposit Limits and Controls

Each asset has configurable parameters that protect the stability of GREEN, our stablecoin:

**Why Limits Matter**

Since deposited assets serve as collateral backing GREEN loans, the protocol must prevent any single asset from becoming too dominant. If 90% of GREEN were backed by one volatile asset, its price swings could destabilize the entire system. Limits ensure diversified, resilient backing.

**Per-User Limits**
- Maximum deposit per user per asset
- Prevents whale dominance in specific assets
- Ensures broad distribution of risk
- Maintains fair access for all participants

**Global Limits**  
- Protocol-wide caps per asset type
- Controls each asset's percentage of total GREEN backing
- Gradual increases as assets prove stability and liquidity
- Protects stablecoin integrity during market stress

**Minimum Balances**
- Small position requirements (often ~$100)
- Prevents dust accumulation
- Ensures meaningful participation
- Reduces computational overhead

These limits adapt over time through governance, balancing growth opportunities with prudent risk management. As assets demonstrate stability and liquidity deepens, limits can expand while maintaining GREEN's robust backing.

### Multi-Asset Advantages

Building a diversified collateral portfolio provides:

1. **Reduced Liquidation Risk**: Asset correlation protection
2. **Optimized Borrowing Power**: Each asset contributes its best LTV
3. **Simplified Management**: One position, one health factor
4. **Flexible Composition**: Add/remove assets as needed

## Making Withdrawals

### Withdrawal Mechanics

Withdrawals respect your overall position health:

1. **Free Collateral**: Withdraw assets above borrowing needs
2. **Health Check**: Ensure position remains safe
3. **Instant Processing**: No waiting periods or queues
4. **Partial or Full**: Take what you need, leave the rest

### Understanding Available Withdrawals

Your withdrawal capacity depends on:
- **Unused collateral** not backing loans
- **Asset-specific LTVs** determining borrowing power
- **Current debt levels** and interest accrued
- **Overall health factor** maintaining safety

Example:
```
Deposited: $10,000 ETH
Borrowed: $5,000 GREEN (at 80% LTV)
Required: $6,250 collateral
Available to withdraw: $3,750 worth of ETH
```

## Earning While Deposited

### Automatic Reward Accumulation

Every deposit earns RIPE rewards through the protocol's points system:

```
Points = Deposit Value × Blocks Held
Share = Your Points / Total Points
Rewards = Your Share × Emissions
```

Time matters as much as size — smaller deposits held longer can out-earn whale positions.

### Reward Categories

**General Depositors** - All deposits earn base rewards
- USD-weighted fair distribution
- No special requirements
- Passive income on all assets

**Vote Depositors** - Community-selected bonus rewards
- Higher allocations for chosen assets
- Governance participation benefits
- Strategic deposit opportunities

**Special Rewards** - Enhanced earnings in specific vaults
- [Stability pool](10-stability-pools.md) deposits earning dual yields
- [Governance Vault](08-governance.md) staking with multipliers
- Future special purpose incentives

For a detailed exploration of the RIPE rewards system, including emission schedules, point calculations, and maximization strategies, see [RIPE Block Rewards](07-ripe-rewards.md).

## Advanced Features

### Delegation System

Grant specific permissions to other addresses:
- **Deposit Rights**: Allow others to add collateral
- **Withdrawal Rights**: Delegate withdrawal capabilities
- **Full Flexibility**: Revoke permissions anytime
- **Smart Wallet Compatible**: Works with Underscore wallets (Hightop app)

Use cases:
- Team treasury management
- Automated strategy execution
- Family account structures
- Protocol integrations

### Whitelisted Assets

Some assets require special access:
- **Tokenized Securities**: KYC/AML verification
- **Institutional Assets**: Accredited investor status
- **Beta Features**: Early access programs
- **Regulated Tokens**: Compliance requirements

The protocol handles permissions transparently — you'll know if an asset requires approval.

### Emergency Features

Safety mechanisms protect your assets:
- **Pause Functionality**: Temporary halts during emergencies
- **Asset Isolation**: Problems don't spread between assets
- **Graceful Degradation**: Withdrawals prioritized in crises
- **User Protection**: Your assets remain yours

## Why Deposit in Ripe?

### Immediate Benefits
- **Earn RIPE rewards** on all deposits automatically
- **No lock-ups** on general deposits (withdraw anytime)
- **Productive collateral** - yields continue accumulating
- **Portfolio approach** reduces liquidation risk

### Long-term Value
- **Early participant advantages** in growing protocol
- **Governance participation** shapes the future
- **Network effects** as more assets join
- **Innovation pipeline** supporting new asset types

### Capital Efficiency
- **One position** instead of many to manage
- **Cross-collateralization** maximizes borrowing power
- **Lower liquidation risk** through diversification
- **Optimized parameters** for each asset type

## Conclusion

Ripe Protocol's deposit and withdrawal system represents the next evolution in DeFi lending. By combining the simplicity of unified positions with the flexibility of universal collateral acceptance, the protocol creates unprecedented opportunities for capital efficiency.

Whether you're a conservative saver earning on stablecoins, a DeFi veteran maximizing yield-bearing positions, or an innovator exploring emerging assets, Ripe provides the infrastructure to make your assets work harder while maintaining the security and flexibility you demand.

Start your journey today — every block counts toward your future rewards.

---

*For technical implementation details, see the [Technical Documentation](../technical/core/Teller.md)*