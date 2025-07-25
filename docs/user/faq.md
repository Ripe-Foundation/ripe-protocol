# Frequently Asked Questions

This document addresses common questions about Ripe Protocol's mechanics, safety features, and operational details.

## Protocol Basics

### What makes Ripe different from other lending protocols?

Ripe combines multiple collateral assets into a single borrowing position, unlike isolated lending markets. This enables support for diverse asset types (including meme coins, NFTs, and RWAs) through individual risk isolation - one user's risky collateral choices don't affect others.

### How does GREEN maintain its dollar peg?

GREEN uses five complementary mechanisms:
1. **Dynamic Rate Protection**: Automatic borrowing rate adjustments
2. **Stability Pools**: Immediate liquidity during stress
3. **Direct Redemptions**: Exchange GREEN for collateral at par value
4. **Endaoment Operations**: Treasury-managed market interventions
5. **Liquidation System**: Bad debt removal before peg impact

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

Each asset has a base rate reflecting its risk profile. The Dynamic Rate Protection system can increase rates during market stress to maintain GREEN's peg. Multiple assets create blended rates weighted by borrowing power contribution.

### When do borrowing rates update?

Rates update when borrowers interact with the protocol:
- Taking new loans
- Repaying existing debt
- Modifying collateral positions
- Explicit rate refresh calls

Existing borrowers remain insulated from temporary rate spikes unless they choose to interact.

### What triggers liquidation?

Liquidation occurs when debt exceeds the liquidation threshold percentage of collateral value. This threshold is always higher than the LTV to provide a safety buffer. For example:
- LTV: 80% (maximum borrowing)
- Liquidation threshold: 85% (liquidation trigger)

### How does partial liquidation work?

The protocol aims to restore position health rather than complete closure:
- Liquidation targets the minimum amount needed to return above thresholds
- Asset selection prioritizes minimizing user losses
- Multiple liquidation phases operate simultaneously
- Borrowers retain maximum possible collateral

## Liquidations and Safety

### What is the three-phase liquidation system?

1. **Phase 1: Internal Recovery**
   - GREEN/sGREEN burning mechanisms
   - Stablecoin transfers to Endaoment treasury

2. **Phase 2: Stability Pool Integration**
   - Collateral swaps with stability pool participants
   - Predetermined discount rates

3. **Phase 3: Market Mechanisms**
   - Dutch auctions with declining prices
   - Public market-based liquidation

All phases operate concurrently based on asset type and availability.

### How do stability pools work?

Stability pools hold sGREEN that can instantly swap for liquidated collateral at discounts. Participants earn:
- **Base sGREEN yield**: Protocol revenue distribution
- **Liquidation premiums**: Discounted collateral purchases
- **RIPE rewards**: Additional protocol incentives

### What happens during redemptions?

GREEN holders can redeem tokens against positions in the redemption zone (between redemption threshold and liquidation threshold). This provides:
- Par value exchange (no discount)
- Automatic deleveraging for risky positions
- Gradual position improvement before liquidation

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

### How do points and rewards work?

Deposited assets earn points each block based on:
- **Token amount**: Balance-based point accumulation
- **USD value**: Dollar-denominated calculations
- **Asset type**: Risk-adjusted multipliers
- **Special positions**: Governance stakes earn maximum rates

Points convert to RIPE token distributions through the rewards system.

## Technical Operations

### How are asset prices determined?

The protocol uses a priority-based oracle system:
1. **Chainlink** (typically first priority)
2. **Pyth Network** (backup)
3. **Stork** (backup)
4. **DEX integration** (direct pricing)

The system uses the first available valid price without averaging, automatically falling back through the hierarchy.

### What are vaults and how do they work?

Assets store in specialized vaults optimized for different token types:

**Simple ERC-20 Vaults**: Direct balance tracking for standard tokens
**Share-Based Vaults**: Percentage ownership for yield-bearing assets
**Stability Pool Vault**: Special handling for sGREEN liquidation backstops
**Governance Vault**: Time-locked RIPE deposits with voting power

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

**Individual Level**: Immediate delegation revocation, liquidation protection through diversification
**Protocol Level**: Emergency pause capabilities, governance intervention mechanisms
**System Level**: Multiple oracle fallbacks, redundant liquidation phases

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

### "Multi-collateral is the same as money markets"

While both support multiple assets, Ripe's individual risk isolation enables support for assets too risky for shared pools. Money markets require conservative, blue-chip assets to protect all depositors.

### "Dynamic rates mean unpredictable costs"

Dynamic Rate Protection responds predictably to market conditions with transparent triggers. Rates only update when borrowers interact, providing control over timing.

### "Liquidation means losing everything"

The system prioritizes partial liquidation to restore health while preserving maximum collateral. Three-phase mechanisms minimize losses through progressive approaches.

### "Delegation gives others control of funds"

Delegates can only perform authorized actions with all value flows returning to the original owner. Ownership never transfers and permissions are instantly revocable.

### "Exotic assets make the protocol risky"

Individual risk isolation means one user's asset choices don't affect others. The protocol can safely support experimental assets through personalized risk management.

---

For technical implementation details, see the [Technical Documentation](../technical/README.md) section.