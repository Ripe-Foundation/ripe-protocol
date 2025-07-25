# Supported Assets

Ripe Protocol supports diverse asset types through its universal collateral system, ranging from established cryptocurrencies to experimental tokens and real-world asset representations.

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
- **Liquid Staking Tokens**:
  - stETH (Lido Staked ETH)
  - rETH (Rocket Pool ETH)
  - Various LST providers
- **LP Tokens**: From DEX liquidity provision
- **Vault Tokens**: From yield aggregators
- **Interest-bearing tokens**: Lending protocol deposits (Aave, Morpho, Euler, etc)
- **Staked governance tokens**: Locked protocol tokens

**Yield Continuity**: Collateral maintains its productive characteristics:
- Liquid staking tokens accrue staking rewards
- LP tokens collect trading fees
- Vault tokens continue compounding
- Yield generation occurs simultaneously with borrowing

Positive carry scenarios emerge when asset yields exceed borrowing costs.

### 4. Emerging Assets

Community-driven and experimental assets represent crypto innovation.

**Examples:**
- **Meme Coins**: Community-driven tokens like SHIB, PEPE
- **Gaming Tokens**: In-game currencies and reward tokens
- **Community Tokens**: DAO and social tokens
- **New Protocol Tokens**: Recently launched DeFi projects
- **Experimental Assets**: Novel token mechanisms

These assets receive conservative parameters reflecting their volatility profiles and market characteristics.

### 5. Tokenized Real-World Assets

Tokenized representations of traditional assets enable real-world value integration.

**Examples:**
- **Tokenized Securities**: Digital representations of stocks, bonds
- **Commodity Tokens**: Gold, silver, oil backed tokens
- **Real Estate Tokens**: Property-backed digital assets
- **Treasury Tokens**: Government bond representations
- **Invoice/Trade Finance**: Tokenized business receivables

**Compliance Features:**
- KYC verification requirements
- Accredited investor status checks
- Geographic restrictions
- Transfer limitations

**Special Handling:**
- Cannot be freely auctioned during liquidations
- Specific liquidator whitelists
- Direct redemption mechanisms only
- Compliance preserved throughout lifecycle

**Compliance Integration:**
- DeFi liquidity access with regulatory compliance
- Institutional infrastructure requirements
- Regulatory framework adherence
- Segregation from permissionless systems

Parameters vary based on underlying asset characteristics and applicable regulations.

### 6. NFTs & Tokenized Unique Assets

Non-fungible tokens represent unique digital assets, collectibles, and tokenized real-world items.

**Examples:**
- **PFP Collections**: Popular avatar projects (CryptoPunks, BAYC, Pudgy Penguins, etc)
- **Art NFTs**: Digital art and generative pieces (Ringers, Fidenzas, etc)
- **Utility NFTs**: Membership and access tokens
- **Gaming NFTs**: In-game assets, land, and items
- **Tokenized Luxury Items**: High-end watches, rare wines, classic cars
- **Tokenized Collectibles**: Sports memorabilia, trading cards, historical artifacts
- **Tokenized Real Estate**: Individual properties, fractional ownership tokens

**Key Characteristics:**
- Specialized valuation models
- Collection-based or individual appraisal parameters
- Different liquidation mechanisms
- Floor price or third-party valuation considerations

## Asset Addition Process

New asset integration follows a structured process:

1. **Community Proposal**: Asset suggestions from participants
2. **Risk Assessment**: Volatility, liquidity, and market analysis
3. **Parameter Setting**: LTV, rate, and limit determination
4. **Governance Vote**: RIPE holder approval
5. **Technical Integration**: Contract updates and testing
6. **Gradual Rollout**: Conservative initial parameters with adjustments

## The Expanding Universe of Collateral

Ripe's architecture is designed to accommodate any tokenized value. The protocol can adapt to support new asset types as they emerge:

- **Prediction Market Shares**: Tokenized outcomes and betting positions
- **Carbon Credits**: Environmental assets and sustainability tokens
- **Intellectual Property**: Tokenized royalties and content rights
- **Synthetic Assets**: Derivatives and synthetic representations
- **Cross-chain Assets**: Tokens bridged from other blockchains
- **Privacy Tokens**: Assets with enhanced privacy features
- **And More**: If it's tokenized and has value, it can potentially serve as collateral

Asset expansion balances innovation with safety, ensuring additions enhance protocol stability.

## Checking Asset Support

### Asset Support Verification

The protocol maintains a comprehensive list of supported assets with their associated parameters:

1. **Supported Asset Registry**: On-chain list of approved tokens
2. **Asset Parameters**: Each asset has defined LTV ratios, interest rates, and deposit limits
3. **Access Restrictions**: Certain assets require whitelist approval for regulatory compliance
4. **Vault Assignment**: Each asset maps to a specific vault type for proper handling

### Current Asset Status

Assets fall into categories:

**Fully Supported** ✅
- Immediate deposits
- No restrictions
- Standard parameters

**Whitelist Required** 🔐
- KYC/compliance needed
- Apply for access
- Then deposit normally

**Coming Soon** ⏳
- Approved by governance
- Awaiting deployment
- Join waitlist

**Not Yet Supported** ❌
- Propose through governance
- Community discussion
- Technical integration

## Adding New Assets

### Community Process

Asset addition follows this process:

1. **Research Phase**
   - Analyze token metrics
   - Check liquidity depth
   - Review smart contract
   - Assess market demand

2. **Proposal Creation**
   - Submit governance proposal
   - Include risk analysis
   - Suggest parameters
   - Provide integration plan

3. **Community Discussion**
   - Forum deliberation
   - Risk assessment
   - Parameter refinement
   - Technical review

4. **Governance Vote**
   - RIPE holders decide
   - Requires quorum
   - Majority approval
   - Time-locked execution

5. **Technical Integration**
   - Smart contract updates
   - Oracle configuration
   - Vault assignment
   - Testing phase

6. **Gradual Rollout**
   - Conservative initial parameters
   - Limited deposits first
   - Monitor performance
   - Expand over time

### Typical Timeline

- Research & Proposal: 1-2 weeks
- Discussion: 1 week
- Voting: 3-7 days
- Integration: 1-2 weeks
- Total: 4-6 weeks average

### What Makes a Good Candidate?

**Technical Requirements**:
- ERC-20 compliant
- Reliable price oracles
- Sufficient liquidity
- Clean audit history

**Market Requirements**:
- Active trading volume
- Multiple exchanges
- Established community
- Clear use case

**Risk Considerations**:
- Volatility profile
- Correlation to other assets
- Potential for manipulation
- Regulatory clarity

## Special Considerations by Type

### For Yield-Bearing Assets
- Must have share-based vault
- Yield mechanism understood
- No negative rebases (ideally)
- Audited yield source

### For NFT Collections
- Floor price oracle needed
- Sufficient trading volume
- Clear valuation method
- Liquidation buyers exist

### For RWAs
- Legal structure clear
- Compliance framework
- Redemption mechanism
- Transfer restrictions handled

### For New Tokens
- Initial conservative parameters
- Higher collateral requirements
- Lower debt ceilings
- Gradual parameter improvement

## Stay Updated

Asset support evolves constantly:

Asset support evolution includes:
- Regular asset additions
- Governance participation opportunities
- Parameter improvements over time
- Community proposal mechanisms

## Related Documentation

- [Asset Parameters](asset-parameters.md) - Detailed parameter mechanics
- [Deposit & Withdrawal Mechanics](deposit-withdrawal-mechanics.md) - Asset flow processes