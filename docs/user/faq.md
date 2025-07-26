# Frequently Asked Questions

This document addresses common questions about Ripe Protocol's mechanics, safety features, and operational details.

## Protocol Basics

### What makes Ripe different from other lending protocols?

Ripe lets you deposit 10+ different assets as collateral for a single loan - from stablecoins to meme coins to NFTs. Unlike other protocols where each asset requires a separate position, Ripe unifies everything into one manageable loan with blended parameters. This multi-collateral innovation enables support for assets too risky for traditional lending pools.

### How does GREEN maintain its dollar peg?

GREEN uses five complementary mechanisms:
1. **Dynamic Rate Protection**: Rates increase when GREEN exceeds 60% of liquidity pools
2. **Stability Pools**: Provide instant liquidity and enable par value redemptions
3. **Direct Redemptions**: GREEN holders can redeem $1 of collateral per GREEN
4. **Endaoment Operations**: Treasury automatically manages Curve pool ratios
5. **Liquidation System**: Three-phase system removes bad debt efficiently

### What's the difference between GREEN and sGREEN?

- **GREEN**: The protocol's stablecoin, minted through borrowing
- **sGREEN**: Yield-bearing version that automatically accrues protocol revenues

sGREEN implements an exchange rate model where each token represents an increasing claim on the underlying GREEN pool.

## Collateral and Assets

### Can delegates steal deposited funds?

No. The delegation system enforces strict limitations:
- Withdrawals always route to the original owner's address
- Delegates cannot change destination addresses
- Asset ownership never transfers to delegates
- All delegation permissions are instantly revocable

### How does multi-collateral borrowing work?

The protocol calculates weighted-average parameters based on each asset's contribution to borrowing power:
- Higher LTV assets (stablecoins) have greater influence on terms
- Interest rates blend proportionally across all collateral
- Liquidation considers the entire portfolio, not individual assets

### What happens to yield from deposited assets?

Yield-bearing assets continue generating returns while serving as collateral:
- **Liquid staking tokens** (stETH): Accrue staking rewards
- **LP tokens**: Collect trading fees
- **Vault tokens**: Continue compounding strategies

Assets deposit into share-based vaults that capture all yields, rebases, and rewards.

### Why do different assets have different parameters?

Parameters reflect risk characteristics:
- **Volatility**: More volatile assets receive lower LTV ratios
- **Liquidity**: Deeper markets support higher borrowing capacity
- **Track Record**: Established assets earn more favorable terms
- **Liquidation Complexity**: Harder-to-liquidate assets get conservative treatment

## Borrowing and Debt

### How are borrowing rates determined?

Base rates reflect asset risk profiles. When GREEN exceeds 60% of reference liquidity pools, rates progressively increase with a multiplier (1.5x-3.0x) plus time-based boosts. Multiple collateral assets create weighted-average rates based on borrowing power contribution.

### When do borrowing rates update?

Rates update when borrowers interact with the protocol:
- Taking new loans
- Repaying existing debt
- Modifying collateral positions
- Explicit rate refresh calls

Existing borrowers remain insulated from temporary rate spikes unless they choose to interact.

### What triggers liquidation?

Liquidation occurs when your collateral value drops below the minimum required for your debt level. The liquidation threshold works inversely - it defines minimum collateral needed:
- LTV: 80% (borrow up to $8,000 on $10,000 collateral)
- Liquidation threshold: 95% (need $8,421 collateral for $8,000 debt)

### How does partial liquidation work?

Ripe uses a unified repayment formula that calculates exactly what's needed to restore health - nothing more:
- Only liquidates the mathematically required amount
- Includes fees and small safety buffer
- Same formula across all three phases
- You keep maximum possible collateral

### Who executes liquidations?

Keepers (automated bots) monitor all positions 24/7 and trigger liquidations instantly when thresholds are breached:
- Compete for 1-2% rewards of liquidated debt
- Execute within blocks of eligibility
- No delays or grace periods - liquidation is immediate
- You can't negotiate or delay once eligible

## Liquidations and Safety

### What is the three-phase liquidation system?

1. **Phase 1: Internal Recovery**
   - Burns your GREEN/sGREEN deposits to reduce debt
   - Transfers stablecoins and GREEN LP to Endaoment at full value

2. **Phase 2: Stability Pool Swaps**
   - Exchanges collateral for sGREEN/GREEN LP at discount
   - Pool participants get your collateral, you get debt reduction

3. **Phase 3: Dutch Auctions**
   - Time-based discounts (5% to 25% over hours)
   - Anyone can buy portions with GREEN (which gets burned)
   - Instant settlement for fungible assets

All phases run simultaneously - protocol routes each asset optimally.

### How do stability pools work?

Stability pools hold sGREEN and GREEN LP tokens that swap for liquidated collateral. Participants earn:
- **Base yield**: sGREEN appreciation and LP trading fees
- **Liquidation profits**: Acquire collateral at 5-15% discounts
- **RIPE rewards**: Staker category rewards (not general depositor)
- **GREEN redemptions**: When GREEN < $1, arbitrageurs buy and redeem against pool

### What happens during redemptions?

When positions enter the redemption zone, GREEN holders can redeem tokens for exactly $1 of collateral. This creates:
- **Peg stabilization**: Arbitrage opportunity when GREEN < $1
- **Automatic deleveraging**: Reduces debt for at-risk positions
- **No liquidation fees**: Better than liquidation for borrowers
- **Risk-based priority**: Only affects positions approaching liquidation

## Protocol Economics

### How does the Endaoment work?

The Endaoment serves as the protocol's treasury system:
- **Asset Management**: Deploys capital across DeFi strategies
- **GREEN Stabilization**: Manages Curve pool ratios automatically
- **Yield Generation**: Uses Underscore Protocol's Lego adapters
- **Partner Programs**: Facilitates liquidity partnerships

### What are Ripe Bonds?

Bonds exchange stablecoins for RIPE tokens at dynamic prices:
- **Treasury Building**: All proceeds flow to the Endaoment
- **Time Incentives**: Lock bonuses reward longer commitments
- **Epoch System**: Limited availability prevents unlimited issuance
- **Fair Access**: Equal opportunities across all participants

### How do RIPE block rewards work?

15% of RIPE supply (150M tokens) distributed over ~5 years across four categories:
- **Borrowers**: Based on debt amount × time
- **Stakers**: RIPE/RIPE LP in governance vault + sGREEN/GREEN LP in stability pools
- **Vote Depositors**: Assets selected by governance (when active)
- **General Depositors**: All vault deposits based on USD value

Rewards accumulate per block and can be claimed or auto-staked.

## Technical Operations

### How are asset prices determined?

The protocol uses a priority-based oracle system:
1. **Chainlink** (typically first priority)
2. **Pyth Network** (backup)
3. **Stork** (backup)
4. **DEX integration** (direct pricing)

The system uses the first available valid price without averaging, automatically falling back through the hierarchy.

### What are vaults and how do they work?

Vaults are smart contracts that hold your deposited assets. Each asset type gets an appropriate vault:
- **Standard tokens**: Simple balance tracking
- **Yield-bearing assets**: Share-based to capture all yields/rebases
- **Stability pools**: Hold sGREEN/GREEN LP for liquidation swaps
- **Governance vault**: Locks RIPE/RIPE LP with time bonuses

### How does whitelist access work for restricted assets?

Certain assets require approval for regulatory compliance:
- **KYC/AML verification**: Identity confirmation through issuers
- **Accreditation checks**: Income/asset requirements for securities
- **Geographic restrictions**: Residency-based access controls
- **On-chain enforcement**: Smart contract permission validation

## Risk and Safety

### What are the main protocol risks?

**Smart Contract Risk**: Bugs could affect fund security
**Oracle Risk**: Price feed failures or manipulation
**Liquidation Risk**: Market conditions preventing orderly liquidations
**Governance Risk**: Parameter changes affecting positions
**Composability Risk**: Interactions with external protocols

All risks are mitigated through audits, redundant systems, and conservative parameters.

### How does risk isolation work?

Each borrower's collateral backs only their own debt:
- Bad debt from one position doesn't affect others
- Individual parameter calculations prevent contagion
- Asset diversity becomes personal protection, not systemic risk
- Failed strategies remain contained to the affected user

### What emergency mechanisms exist?

- **For users**: Instant delegation revocation, multi-collateral diversification
- **For liquidations**: Keepers compete to execute instantly, preventing bad debt
- **For oracles**: Priority hierarchy with automatic fallbacks
- **For governance**: Emergency pause and parameter updates (when active)

## RIPE Governance

### How does RIPE governance work?

RIPE token holders can lock their tokens in the Ripe Governance Vault to accumulate governance points. Governance power equals a user's total points divided by the protocol's total points. When full governance launches, this power will control asset support, protocol parameters, and treasury management.

### Is governance active now?

Full on-chain governance is not yet active, but governance points are accumulating. Early participants who lock RIPE tokens now are building the voting power they'll use when decentralized governance launches in the coming months.

### How do governance points accumulate?

Points are calculated using: Token Balance × Blocks Elapsed × Asset Weight × Lock Bonus

Asset weights:
- RIPE tokens: 100% weight
- RIPE LP tokens: 150% weight

Lock bonuses reward longer commitments:
- 1 day (minimum): 0% bonus
- 6 months: ~35% bonus  
- 1 year: ~65% bonus
- 2 years: ~130% bonus
- 3 years: 200% bonus (maximum)

### Can I exit my governance lock early?

Early exit is possible but extremely costly:
- **Exit fee**: 80% of your deposited tokens are forfeited
- **Distribution**: The 80% penalty stays in the vault for other depositors
- **You receive**: Only 20% of your original deposit back
- **Governance points**: 100% LOST (complete slash of all accumulated points)
- **Smart protection**: Prevents costly exits during bad debt when withdrawals would fail anyway

### Do I lose governance points when withdrawing?

**Yes - ALL withdrawals proportionally slash your governance points:**
- Withdraw 10% of tokens → Lose 10% of governance points
- Withdraw 50% of tokens → Lose 50% of governance points  
- Withdraw 100% of tokens → Lose ALL governance points

This applies to both normal withdrawals (after lock expires) and early exits. Governance power is always tied to your current deposit.

### What will governance control?

When activated, RIPE holders will govern:
- **Asset Support**: Which tokens can serve as collateral
- **Risk Parameters**: LTV ratios, liquidation thresholds, interest rates
- **Treasury Strategy**: How Endaoment funds are invested
- **Protocol Economics**: Fee structures, revenue distribution, reward emissions
- **System Parameters**: Dynamic rates, liquidation configuration, stability mechanisms

## Advanced Features

### Can positions be automated?

The delegation system enables sophisticated automation:
- **Borrow permission**: Automated leverage management
- **Withdraw permission**: Rebalancing and deleveraging
- **Claims permissions**: Reward harvesting and compounding
- **Smart contract delegates**: Complex strategy implementations

### How do NFTs work as collateral?

NFTs receive specialized handling:
- **Valuation methods**: Floor price, oracles, individual appraisals
- **Conservative parameters**: Lower LTV ratios (30-50% vs 80%+ for crypto)
- **Extended liquidation**: Longer settlement periods
- **Collection-based limits**: Risk management per NFT project

### What about real-world assets (RWAs)?

RWAs integrate with compliance requirements:
- **Regulatory framework**: KYC/AML throughout asset lifecycle
- **Special liquidation**: Direct redemption, no public auctions
- **Transfer restrictions**: Maintained during collateralization
- **Institutional infrastructure**: Segregated from permissionless systems

## Getting Started

### What's the minimum deposit amount?

Most assets have minimum deposit requirements to prevent dust accumulation and ensure gas efficiency, typically $100-500 equivalent. Specific minimums vary by asset type and current parameters.

### How do deposit limits work?

Two types of limits protect protocol growth:
- **Per-user limits**: Prevent concentration risk (e.g., max $100k PEPE per address)
- **Global limits**: Total protocol exposure (e.g., max $10M PEPE system-wide)

Limits may increase over time through governance decisions.

### What's the best way to start?

1. **Understand the system**: Review core documentation sections
2. **Start conservative**: Use established assets initially
3. **Monitor health**: Track position status regularly
4. **Explore features**: Gradually utilize advanced capabilities

The protocol supports everything from simple borrowing to complex automated strategies.

## Common Misconceptions

### "Multi-collateral is the same as isolated lending markets"

Isolated markets force you to manage 10 separate loans for 10 assets. Ripe combines all collateral into ONE loan with weighted-average parameters. This unified position makes complex strategies simple while enabling support for exotic assets.

### "Dynamic rates mean unpredictable costs"

Rates follow clear rules: when GREEN exceeds 60% of reference pools, multipliers kick in (1.5x-3.0x). You control when rates apply - they only update when you interact with your position.

### "Liquidation means losing everything"

Ripe's unified formula only liquidates what's mathematically needed to restore health. Unlike protocols that take fixed 50% chunks, Ripe might only need to liquidate 20-30% to fix your position.

### "Delegation gives others control of funds"

Delegates can only perform authorized actions with all value flows returning to the original owner. Ownership never transfers and permissions are instantly revocable.

### "Exotic assets make the protocol risky"

Each user's collateral backs only their own debt - your PEPE doesn't affect my loan. Conservative parameters for risky assets (30% LTV vs 90% for stables) ensure protocol safety while enabling innovation.

---

For technical implementation details, see the [Technical Documentation](technical/README.md) section.