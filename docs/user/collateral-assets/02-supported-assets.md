# Supported Assets

Ripe Protocol supports diverse asset types through its universal collateral system, ranging from established crypto assets to tokenized real-world assets.

## Asset Categories Overview

### 1. Stablecoins

Stablecoins provide value stability and elevated loan-to-value ratios.

**Examples:**
- **USDC**: Circle's regulated dollar stablecoin
- **USDT**: Tether's widely-used stablecoin
- **USDS**: Sky's decentralized stablecoin (formerly MakerDAO)
- **Yield-bearing stables**: Interest-earning stable assets

Stablecoins typically offer high loan-to-value ratios and reduced liquidation risk due to price stability.

### 2. Blue-Chip Crypto Assets

Established crypto assets with deep liquidity and proven track records.

**Examples:**
- **WETH**: Wrapped Ethereum
- **cbBTC**: Coinbase Wrapped Bitcoin
- **Major DeFi Tokens**: Leading protocol governance tokens
- **Layer 1 tokens**: Native blockchain assets
- **Established altcoins**: Top market cap crypto assets

These assets provide substantial borrowing capacity with moderate risk parameters.

### 3. Yield-Bearing Assets

Assets generating returns while serving as collateral enable simultaneous yield and borrowing.

**Examples:**
- **Liquid Staking Tokens**: stETH, rETH, cbETH
- **LP Tokens**: Uniswap, Curve, Balancer positions
- **Vault Tokens**: Yearn, Aave aTokens, Compound cTokens
- **Staked governance tokens**: Locked protocol tokens

**Key Mechanics:**
- **Share-based accounting** preserves yield accumulation
- **Automatic compounding** continues while collateralized
- **Positive carry** possible when yields exceed borrow rates
- **No opportunity cost** - earn yields while borrowing GREEN

**Example**: Deposit 100 stETH earning 4% → Borrow GREEN at 3% → Net 1% positive carry while accessing liquidity.

### 4. Tokenized Real-World Assets

Tokenized representations of traditional assets enable real-world value integration.

**Examples:**
- **Tokenized Securities**: Stocks, bonds, ETFs
- **Commodity Tokens**: Gold, silver, oil backed tokens
- **Real Estate Tokens**: Property-backed digital assets
- **Treasury Tokens**: Government bond representations

**Key Differences:**
- **KYC/AML required** for most RWA deposits
- **No public liquidations** - direct redemption only
- **Geographic restrictions** may apply
- **Conservative parameters** due to settlement times

These assets bridge traditional finance with DeFi while maintaining regulatory compliance.

### 5. NFTs & Unique Assets

Non-fungible tokens and unique digital assets can serve as collateral with specialized handling.

**Examples:**
- **Blue-chip NFTs**: CryptoPunks, BAYC, Pudgy Penguins
- **Art NFTs**: Generative art, 1/1 pieces
- **Gaming Assets**: In-game items, virtual land
- **Tokenized Collectibles**: Physical items represented on-chain

**Key Considerations:**
- **Lower LTVs** (30-50%) due to illiquidity
- **Floor price valuations** for collections
- **Longer liquidation timelines**
- **Best combined with fungible collateral** for stability

## The Expanding Universe of Collateral

Ripe's architecture is designed to accommodate any tokenized value. The protocol can adapt to support new asset types as they emerge:

**Emerging Digital Assets:**
- **Meme Coins**: Community-driven tokens like SHIB, PEPE
- **Gaming Tokens**: In-game currencies and reward tokens
- **Community Tokens**: DAO and social tokens
- **New Protocol Tokens**: Recently launched DeFi projects

**Future Asset Categories:**
- **Prediction Market Shares**: Tokenized outcomes and betting positions
- **Carbon Credits**: Environmental assets and sustainability tokens
- **Intellectual Property**: Tokenized royalties and content rights
- **Synthetic Assets**: Derivatives and synthetic representations
- **Cross-chain Assets**: Tokens bridged from other blockchains
- **Privacy Tokens**: Assets with enhanced privacy features
- **And More**: If it's tokenized and has value, it can potentially serve as collateral

Emerging and experimental assets receive conservative parameters reflecting their volatility profiles and market characteristics.

Asset expansion balances innovation with safety, ensuring additions enhance protocol stability.

## How Assets Are Stored

Ripe uses specialized vaults to store different asset types:
- **Standard vaults** for regular tokens (ETH, USDC)
- **Share-based vaults** for yield-bearing assets that preserve earnings
- **Special vaults** for unique requirements (NFTs, governance tokens)

Your assets remain in these secure vaults until withdrawal, with the vault type automatically selected based on the asset's characteristics.

## Special Asset Handling

### Whitelisted Assets
Some assets require approval before deposits:
- **Tokenized securities** - KYC/AML verification
- **Institutional assets** - Accredited investor checks
- **New experimental tokens** - Gradual rollout for safety

### Rebasing Tokens
Elastic supply tokens (like AMPL) use share-based accounting to capture supply changes while maintaining your ownership percentage.

### LP and Vault Tokens
DEX LP tokens and yield vault tokens continue earning fees and yields while serving as collateral, creating capital efficiency through productive collateral.

## Related Documentation

- [Asset Parameters](03-asset-parameters.md) - Detailed parameter mechanics