# Stability Pools: Buy the Rip at 90 Cents on the Dollar

Forget hunting for dips. Forget timing the market. Forget competing with MEV bots.

Stability pools put you first in line to buy liquidated collateral at guaranteed discounts. When leveraged degens get rekt, you get their ETH at 5-15% off. Automatically. Passively. While earning triple-stacked yields on top.

This is wholesale DeFi liquidations, democratized.

## The Core Proposition

### Instant Arbitrage Opportunities

Unlike traditional liquidation systems that require active monitoring and complex bot infrastructure, stability pools democratize liquidation profits:

- **Passive Participation**: Deposit once and automatically participate in liquidations
- **Fair Distribution**: Profits shared proportionally among all depositors
- **No Technical Barriers**: No bots, no gas wars, no timing games
- **Guaranteed Discounts**: Fixed liquidation fees ensure profitable swaps

When liquidations occur, your deposited assets instantly convert to discounted collateral — creating immediate, realized profit without any action on your part.

### Multiple Revenue Streams

Stability pool participants benefit from three distinct yield sources that compound together:

1. **Base Asset Yield**: [sGREEN](04-sgreen.md) continues earning protocol revenue while in the pool
2. **Liquidation Premiums**: Purchase collateral at 5-15% below market value
3. **[RIPE Rewards](06-ripe-rewards.md)**: Earn protocol tokens from the Stakers allocation

This triple-yield structure can generate returns significantly exceeding traditional DeFi strategies.

## How Stability Pools Work

### The Deposit Process

You can deposit two types of assets into stability pools:

**GREEN LP Tokens** (GREEN/USDC liquidity positions)

- Earn trading fees while waiting for liquidations
- First priority in liquidation hierarchy
- Transferred to [Endaoment](11-endaoment.md) treasury when used

**[sGREEN](04-sgreen.md)** (Savings GREEN)

- Continues earning base yield in the pool
- Used after GREEN LP tokens
- Redeemed and burned during liquidations

Your deposits are converted to shares representing your proportional claim on the pool's total value — including both deposited assets and accumulated liquidated collateral.

### The Liquidation Flow

When a borrower's position needs liquidation:

1. **Protocol checks stability pools** for available liquidity
2. **Your pool assets swap for collateral** at the liquidation discount
3. **You receive collateral worth more** than the assets spent
4. **The discount becomes your profit** — instantly realized

Example: If ETH is worth $2,000 and liquidation fee is 10%, the pool buys ETH at $1,800. You get $2,000 of ETH for $1,800 worth of pool assets — a $200 instant profit per ETH.

### USD Value-Based Accounting

Unlike simple token vaults, stability pools use sophisticated USD value-based share accounting:

- **Share Price = Total Pool Value / Total Shares**
- **Pool Value = Deposited Asset Value + All Claimable Asset Values**
- **Your Value = Your Shares × Current Share Price**

This ensures fair distribution regardless of which assets the pool holds at any moment.

## The Economics of Liquidation Profits

### How Liquidation Fees Become Your Profit

The protocol's liquidation fee structure directly determines your returns. When a position liquidates:

- **5% liquidation fee** = You buy collateral at 95% of market value
- **10% liquidation fee** = You buy collateral at 90% of market value
- **15% liquidation fee** = You buy collateral at 85% of market value

Higher-risk collateral types carry higher liquidation fees, meaning bigger profits for stability pool participants. The protocol calibrates these fees to ensure profitability even during volatile markets.

### Real-World Scenarios

**During Market Volatility**: Liquidations increase as prices swing, generating more profit opportunities. Your passive position captures value from market stress without active trading.

**In Stable Markets**: Fewer liquidations occur, but you continue earning base yields from sGREEN or GREEN LP tokens plus RIPE rewards. The triple-yield structure ensures returns even in quiet periods.

**Portfolio Effect**: As liquidations occur across different collateral types, you build a diversified basket of assets acquired at discount — essentially dollar-cost averaging into multiple positions at below-market prices.

## Advanced Features

### Claiming Liquidated Collateral

After liquidations, you can claim your proportional share of accumulated collateral:

- **Flexible Claims**: Choose which assets to claim and when
- **Value Preservation**: Your share value remains constant whether claimed or not
- **Auto-Deposit Option**: Claimed assets can automatically enter Ripe deposit vaults
- **Dynamic RIPE Rewards**: Claims trigger RIPE token rewards based on USD value claimed

#### Claim Incentives: Keeping Pools Healthy

The protocol uses a dynamic reward system to maintain optimal pool composition. When stability pools accumulate too much liquidated collateral, the protocol can activate claim incentives:

- **RIPE per Dollar Claimed**: Each asset can have a specific reward rate (e.g., 0.1 RIPE per $1 of ETH claimed)
- **Strategic Timing**: Higher rewards when pools need rebalancing with fresh sGREEN or GREEN LP
- **Automatic Distribution**: Rewards paid instantly when you claim, locked in [governance vault](08-governance.md)
- **Pool Health Mechanism**: Ensures pools always have liquidity for new liquidations

This creates a market-driven rebalancing system — when collateral accumulates, increased rewards incentivize claims, replenishing the pool with fresh deposits.

### GREEN Redemption Mechanism

Stability pools also serve as a stability mechanism for GREEN. When the pool holds liquidated collateral, any GREEN holder can:

1. **Redeem GREEN for collateral** at exactly $1 value
2. **Help stabilize GREEN price** through arbitrage
3. **Pool maintains value** as GREEN replaces claimed collateral

This creates a powerful peg defense mechanism while preserving depositor value.

### Multi-Asset Accumulation

Over time, stability pools accumulate diverse collateral types:

- ETH from liquidated Ethereum positions
- cbBTC from Bitcoin-backed loans
- Various DeFi tokens from other collateral types
- GREEN from redemption operations

You maintain exposure to this diversified basket while earning on all components.

## Why Participate in Stability Pools?

### For Yield Seekers

- **Triple-stacked returns** from base yield, liquidations, and rewards
- **Passive income** requiring no active management
- **Predictable profits** from fixed liquidation discounts

### For Risk-Conscious Users

- **Senior position** in liquidation hierarchy
- **Instant liquidity** with no lockups
- **Protocol protection** role enhances system stability

### For GREEN Ecosystem Supporters

- **Strengthen the protocol** by providing liquidation liquidity
- **Earn while protecting** the system from bad debt
- **Accumulate governance power** through RIPE rewards

## The Liquidation Game, Simplified

Every market crash. Every overleveraged position. Every liquidation event.

They all flow through stability pools first. While others panic sell, you're automatically buying at protocol-enforced discounts. While others chase yields, you're stacking three revenue streams simultaneously.

No bots. No gas wars. No coding required.

Just deposit, wait for the inevitable liquidations, and collect your discounted crypto. The degen's loss is quite literally your gain.

---

_Stop watching liquidations happen. Start profiting from them._

_For technical implementation details, see the [StabilityPool Technical Documentation](../technical/vaults/StabilityPool.md)._
