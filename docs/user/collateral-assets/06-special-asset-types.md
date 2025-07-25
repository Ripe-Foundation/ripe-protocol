# Special Asset Types

While Ripe Protocol accepts virtually any tokenized asset, some categories require special handling due to their unique characteristics, compliance requirements, or technical properties. These specialized mechanisms ensure proper valuation, risk management, and regulatory compliance across diverse asset types.

## Yield-Bearing Assets

### Understanding Yield Tokens

Yield-bearing assets increase in value through various mechanisms. Ripe's architecture preserves yield accumulation during collateralization.

**Common Types**:
- **Liquid Staking Tokens**: stETH, rETH, cbETH
- **Lending Pool Tokens**: aUSDC, cDAI
- **Vault Tokens**: yvUSDC, Yearn vaults
- **LP Tokens**: Curve, Balancer pool tokens

### Yield Capture Mechanism

**Share-Based Vaults** implement:
1. Percentage ownership tracking
2. Underlying value growth
3. Rebase and reward capture
4. Principal plus yield withdrawal

**stETH Example**:
Initial deposit: 10 stETH (10 ETH value)
After 180 days with 2% staking yield
Withdrawal amount: 10.2 stETH (10.2 ETH value)
Result: Yield accumulation during borrowing

### Yield-Bearing Collateral Economics

**Rate Differential Mechanics**:
When yield-bearing assets earn higher rates than borrowing costs, the position generates positive carry. For example:
- stETH earning 4% APR as collateral
- GREEN borrowing at 3% APR
- Net differential: 1% APR

**Compound Effects**:
Yield-bearing collateral exhibits compound growth patterns:
- Principal value remains constant
- Yield accumulates continuously
- Collateral value increases over time
- Health factor improves without intervention

## NFT Collateral

### How NFTs Work as Collateral

Ripe Protocol's architecture supports NFT collateral through specialized handling:

**Valuation Methods**:
- **Floor Price**: Conservative collection floor
- **Oracle Pricing**: Third-party appraisals
- **TWAP**: Time-weighted average prices
- **Individual Appraisal**: For rare items

**Supported NFT Types**:
- Blue-chip collections (Punks, Apes, etc.)
- Gaming assets and metaverse land
- Art NFTs with established markets
- Utility NFTs with clear value

### NFT-Specific Parameters

NFTs have different risk parameters than fungible tokens:

**Typical NFT Parameters**:
- LTV: 30-50% (compared to 80%+ for ETH)
- Liquidation threshold: 60-70%
- Interest rates: Include risk premium
- Deposit limits: Per-collection caps

**Conservative Parameter Rationale**:
- Reduced liquidity
- Elevated volatility
- Extended liquidation periods
- Limited market depth

### NFT Risk Mitigation

**Protocol Design Considerations**:
NFT collateral parameters reflect illiquidity risk through conservative LTV ratios and higher interest rates. Combining NFT collateral with fungible assets creates more resilient positions.

**Multi-Asset Position Example**:
Collateral components:
- 1 NFT (30 ETH floor value) with 30% LTV
- 10 ETH with 80% LTV
- 5,000 USDC with 90% LTV

Weighted parameters reflect aggregate risk profile

## Tokenized Real-World Assets (RWAs)

### Understanding RWAs

Real-world assets bring traditional finance onto blockchain:

**Asset Categories**:
- **Securities**: Tokenized stocks, bonds
- **Commodities**: Gold, silver, oil tokens
- **Real Estate**: Property-backed tokens
- **Receivables**: Invoice financing tokens
- **Art & Collectibles**: Physical items tokenized

### Compliance and Restrictions

RWAs require special handling for regulatory compliance:

**KYC/AML Requirements**:
1. Identity verification required
2. Accreditation checks (if applicable)
3. Geographic restrictions enforced
4. Transfer limitations maintained

**Compliance Integration**:
The protocol maintains compliance through issuer-level KYC verification, on-chain whitelisting mechanisms, and transfer restrictions that persist throughout the asset lifecycle.

### RWA Liquidation Differences

RWAs cannot be liquidated like crypto assets:

**Special Handling**:
- No public auction (compliance)
- Direct redemption only
- Issuer buyback mechanisms
- Longer settlement times

**What This Means**:
- More conservative LTVs
- Different liquidation timeline
- May require manual intervention
- Higher stability requirements

### Benefits of RWA Collateral

**Portfolio Diversification**:
- Uncorrelated to crypto markets
- Stable value (some assets)
- Real-world cash flows
- Institutional grade assets

**RWA Portfolio Composition**:
- $100k tokenized T-bills: 1% yield, 95% LTV
- $50k tokenized gold: Commodity backing, 70% LTV
- $50k WETH: Cryptocurrency, 80% LTV

Combination of traditional and digital asset exposure

## Restricted and Whitelisted Assets

### Why Some Assets Need Approval

Certain assets require whitelist approval for:
- **Regulatory Compliance**: Securities laws
- **Risk Management**: New or untested assets
- **Technical Integration**: Complex mechanisms
- **Community Protection**: Gradual rollout

### Whitelist Mechanisms

**Access Control Framework**:
Restricted assets implement permission layers that enforce regulatory requirements including KYC/AML verification, accreditation status, geographic restrictions, and minimum deposit thresholds. These controls are maintained at the smart contract level.

### Types of Restrictions

**Geographic Restrictions Example**:
- Asset: Tokenized US Treasury
- Access: US persons only
- Requirement: US residency verification
- Process: Issuer KYC compliance

**Accreditation Requirements Example**:
- Asset: Private equity token
- Access: Accredited investors
- Requirement: Income/asset verification
- Process: Third-party validation

**Time-Based Restrictions Example**:
- Asset: Vesting tokens
- Access: Post-cliff period
- Requirement: Vesting confirmation
- Process: Automated verification

## Rebasing and Elastic Supply Tokens

### Rebase Mechanism

Tokens with elastic supply adjust balances to maintain price targets:

- **Positive Rebase**: Balance increases
- **Negative Rebase**: Balance decreases
- **Protocol Handling**: Share-based tracking

**Examples**:
- Ampleforth (AMPL)
- Olympus (OHM)
- Various algorithmic stablecoins

### Special Considerations

**Vault Mechanics**:
- Share-based accounting essential
- Captures all supply changes
- Your percentage stays constant
- Withdrawable amount fluctuates

**Risk Factors**:
- High volatility
- Complex mechanisms
- Potential for losses
- Conservative parameters

## LP and Vault Tokens

### Liquidity Provider Tokens

LP tokens represent positions in DEX pools:

**LP Token Collateralization**:
1. LP token deposit to protocol
2. Trading fee accumulation continues
3. Impermanent loss exposure remains
4. Value tracks underlying assets

**Supported LP Tokens**:
- Uniswap V2/V3 positions
- Curve pool tokens
- Balancer pool tokens
- Other major DEX LPs

### Yield Aggregator Tokens

Tokens from yield vaults (Yearn, etc.):

**Benefits**:
- Auto-compounding continues
- Strategy yields maintained
- No need to exit positions
- Stack yields with borrowing

**Considerations**:
- Underlying strategy risks
- Potential for losses
- Variable yields
- Smart contract risks

## Gaming and Metaverse Assets

### In-Game Assets

Gaming tokens and items as collateral:

**Types Supported**:
- Governance tokens
- In-game currencies
- Virtual land/property
- Gaming NFTs

**Special Characteristics**:
- High volatility
- Game-dependent value
- Community driven
- Utility premiums

### Metaverse Real Estate

Virtual land and properties:

**Valuation Factors**:
- Location/proximity
- Development status
- Rental income
- Platform growth

**Risk Management**:
- Conservative LTVs
- Platform diversification
- Activity requirements
- Market depth analysis

## Special Asset Considerations

### Portfolio Diversification

Special asset integration benefits from:
1. Traditional crypto asset combination
2. Yield and stability balance
3. Correlation analysis
4. Regular monitoring

### Risk Parameters for Special Assets

Special asset types incorporate additional risk factors into their parameter calculations, including liquidity depth, price discovery mechanisms, regulatory constraints, and technical complexity. These factors result in adjusted LTV ratios and borrowing rates.

### Dynamic Parameter Management

Special asset parameters adjust based on market conditions, regulatory changes, and governance decisions. The protocol's modular architecture enables parameter updates without system-wide changes, allowing responsive risk management for emerging asset classes.

## Future Asset Types

Ripe's architecture can accommodate:
- **Carbon Credits**: Environmental assets
- **Intellectual Property**: Royalty streams
- **Prediction Shares**: Outcome tokens
- **Synthetic Assets**: Derivatives
- **Privacy Tokens**: zk-assets
- **Cross-chain Assets**: Bridged tokens

As tokenization expands, Ripe will be ready to support new innovations while maintaining security and stability.

## Summary

Specialized handling mechanisms enable universal collateral support while maintaining appropriate risk controls for each asset category through tailored parameters and compliance frameworks.