# The Endaoment: Ripe's Protocol Treasury

The Endaoment is Ripe Protocol's intelligent treasury system that manages protocol assets, maintains GREEN's stability, and generates yield to support sustainable operations.

## Core Functions

### 1. Asset Management

**Inflows:**
- Stablecoins from liquidations
- GREEN LP tokens from stability pools
- Protocol fees and bond proceeds
- Partner contributions

**Management:**
- Deploys to yield strategies via Underscore Protocol's Legos
- Optimizes asset composition
- Maintains liquidity reserves
- Handles emergency operations

### 2. GREEN Price Stabilization

The **Green Stabilizer** maintains GREEN's $1 peg automatically:

**Below peg (GREEN > 50% of Curve pool):**
- Removes GREEN liquidity to restore balance
- Repays pool debt first
- Burns excess GREEN after debt repayment

**Above peg (GREEN < 50% of Curve pool):**
- Adds GREEN liquidity
- May mint new GREEN (creates tracked "pool debt")
- Weighted adjustments (e.g., 20% of needed amount)

All operations ensure profitability and respect debt limits.

### 3. Yield Generation via Legos

The Endaoment uses **Underscore Protocol's Lego system** - plug-and-play adapters for DeFi protocols:

**Current Integrations:**
- **Lending**: Aave V3, Compound V3, Morpho, Euler, Fluid
- **DEX/AMM**: Uniswap V2/V3, Curve, Aerodrome

**Example Optimization:**
```
$10M USDC to deploy:
- Morpho: 7% → $5M
- Aave: 6% → $3M  
- Compound: 5.5% → $2M
Result: 6.5% weighted yield (+$50k/year vs single protocol)
```

**Key Benefits:**
- Auto-access to new protocols
- Risk isolation per strategy
- Cross-protocol optimization
- No contract upgrades needed

### 4. Partner Liquidity Program

Creates strategic liquidity partnerships:

```
Partner provides: $1M USDC
Endaoment mints: $1M GREEN
Creates: $2M liquidity pool
Split: 50/50 LP tokens
```

Benefits: Deeper liquidity, strategic alliances, shared revenues

## Who Benefits?

**GREEN Holders**: Stable peg, deep liquidity, no inflation
**Borrowers**: Better liquidations, system stability, lower fees
**sGREEN Holders**: Higher yields from treasury earnings
**Stability Pool Depositors**: Productive use of LP tokens

## Treasury Holdings

- **Core**: Stablecoins, GREEN/sGREEN, LP tokens
- **Strategic**: Partner tokens, concentrated liquidity NFTs
- **Reserves**: Quick-access stables, ETH for operations

## Special Features

- **Internal Liquidity**: Can act as own partner (keeps 100% LP)
- **NFT Management**: Handles Uniswap v3 positions
- **Modular Design**: New strategies easily added

## Real-World Examples

### Market Crash Response
```
Event: ETH -40% in 24 hours
Inflow: $10M USDC from liquidations
Actions:
- 60% → Lending protocols (4% yield)
- 20% → GREEN/USDC liquidity
- 20% → Liquid reserves
Result: GREEN peg maintained, +$400k annual yield
```

### Stabilizer in Action
```
Situation: GREEN at $0.97 (below peg)
Pool: 55% GREEN, 45% USDC
Action: Remove 500k GREEN (300k to repay debt, 200k burned)
Result: Pool balanced, price → $0.995
```

## Governance & Security

- **Governance controls**: Strategy parameters, risk limits, partner approvals
- **Security**: Multi-layered access, safety checks, emergency pauses
- **Transparency**: All holdings on-chain, regular reporting

## FAQ

**Who controls it?** Governance sets strategy; operations are automated

**Can it mint unlimited GREEN?** No - only for stabilization (with debt) or partnerships (with backing)

**Where do yields go?** Support operations, boost sGREEN returns, build reserves

**What if a strategy fails?** Risk isolated per Lego; others continue normally

## Key Takeaways

The Endaoment is an active treasury that:
- Generates yield through diverse DeFi strategies
- Maintains GREEN stability automatically
- Grows stronger with each liquidation
- Operates transparently on-chain

It transforms Ripe from a simple lending protocol into a self-sustaining financial ecosystem, ensuring long-term success for all participants.