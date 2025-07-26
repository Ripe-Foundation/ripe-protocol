# Stability Pool Mechanics

Stability pools hold assets that can instantly swap for liquidated collateral. This mechanism enables rapid liquidations without selling on external markets.

## Pool Composition

### Primary Assets (Depositable)

Users can only deposit these specific asset types into stability pools:

**GREEN LP Tokens**: Liquidity provider tokens from GREEN/USDC pools
- Used first in liquidation priority
- Sent to Endaoment treasury when consumed
- Represents protocol-owned liquidity

**sGREEN (Savings GREEN)**: Yield-bearing GREEN tokens
- Used after LP tokens are exhausted
- Redeemed to GREEN and burned during liquidation
- Earns yield while waiting in pool

Note: While users can only deposit GREEN LP and sGREEN, the pools accumulate many different types of collateral from liquidations (ETH, WBTC, etc.) which GREEN holders can later claim.

### GREEN Redemption Against Pool Collateral

When stability pools accumulate collateral from liquidations, any GREEN holder can redeem their GREEN for this collateral, creating a powerful peg stabilization mechanism:

**How Redemption Works**:
1. **Pool holds liquidated collateral** (ETH, WBTC, etc.) from previous liquidations
2. **GREEN holder redeems**: Burns GREEN to claim exactly $1 worth of collateral
3. **Pool now holds GREEN**: The redeemed GREEN replaces the claimed collateral
4. **Pool value unchanged**: Depositors maintain their share value (GREEN = $1)

**Peg Stabilization Effect**:
When GREEN trades below $1, arbitrageurs can:
1. Buy cheap GREEN on market (e.g., $0.95)
2. Redeem for $1 of collateral from stability pools
3. Profit creates buying pressure that restores peg

**Key Properties**:
- **Open to all**: Any GREEN holder can redeem (not just depositors)
- **Value neutral**: Pool depositors don't lose value when redemptions occur
- **Market-driven**: Pure arbitrage mechanism, no governance needed

## Swap Mechanics

### Basic Swap Process

When liquidation requires stability pool assets:

1. **Collateral Valuation**: System calculates liquidated asset value
2. **Discount Application**: Liquidation fee determines swap discount
3. **Pool Asset Selection**: LP tokens used before sGREEN
4. **Asset Transfer**: Pool receives collateral, liquidator receives debt reduction

### Discount Economics

The liquidation fee becomes pool participant profit:

- **Fee Translation**: 6% liquidation fee = 6% discount for pool
- **Immediate Settlement**: No waiting period or vesting
- **Risk Compensation**: Discount compensates for collateral volatility

### Partial Swaps

Pools may not have sufficient liquidity:

- **Available Liquidity**: Swap up to pool balance
- **Remainder Handling**: Excess collateral goes to auction
- **Multiple Pools**: System checks configured pools sequentially

## Pool Hierarchy

### Priority Ordering

The protocol checks pools in specific order:

1. **Asset-Specific Pools**: Custom pools for particular assets
2. **General Stability Pools**: Default pools for standard assets
3. **Permissioned Pools**: Restricted pools for regulated assets

### Pool Configuration

Each pool has defined parameters:

- **Supported Assets**: Which tokens the pool accepts as deposits (GREEN LP, sGREEN)
- **Eligible Collateral**: Which liquidated assets this pool can receive
- **Access Controls**: Open or permissioned participation

## Special Pool Types

### Permissioned Pools

For regulated or restricted assets:

- **Whitelist Requirements**: Only approved addresses participate
- **Compliance Preservation**: Maintains regulatory requirements
- **Isolated Operations**: Separate from general pools
- **Same Economics**: Identical swap mechanics with access limits

### Asset-Specific Pools

Dedicated liquidity for particular tokens:

- **Specialized Liquidity**: Focused on single asset types
- **Custom Parameters**: Tailored discount structures
- **Priority Processing**: Checked before general pools

## Economic Dynamics

### Pool Incentives and Yield Generation

Stability pools offer multiple reward sources to encourage participation:

**Direct Yields:**
- **Base Yield**: sGREEN appreciation while in pool
- **LP Token Value**: Trading fees from underlying GREEN/USDC liquidity
- **RIPE Block Rewards**: Time-weighted rewards from the Stakers category
  - sGREEN and GREEN LP in stability pools are considered staked assets
  - Earn based on balance and time deposited
  - Accumulates per block while assets remain in pool

**Liquidation Profits:**
- **Liquidation Premiums**: Acquire collateral at discount (typically 5-15%)
- **Profitable Spreads**: Discounts designed to exceed typical market volatility
- **Passive Income**: No active management required - liquidations happen automatically

**Compound Effects:** All yields stack together, creating multiple income streams from a single deposit.

## Withdrawal Mechanics

### Standard Withdrawals

Pool participants can exit positions anytime without restrictions:

- **Full Liquidity**: No lockup periods or time constraints
- **No Penalties**: Exit without fees or charges
- **Maintained Value**: Your share value includes all accumulated profits

### Asset Selection During Withdrawal

When you withdraw, the pool may contain a mix of assets:

**Available Assets**:
- Your original deposits (sGREEN, GREEN LP)
- Liquidated collateral (ETH, WBTC, etc.) acquired at discounts
- GREEN tokens from redemptions (when others redeemed GREEN for collateral)

**Withdrawal Process**:
- **Choose Your Assets**: Select which specific assets to withdraw up to your share value
- **First-Come, First-Served**: Subject to current pool composition
- **Oracle Pricing**: All assets valued at current prices for fair distribution
- **Flexible Combinations**: Mix and match any available assets

**Example**: If your share is worth $10,000 and the pool contains:
- $3,000 ETH
- $4,000 WBTC  
- $5,000 GREEN
- $2,000 sGREEN

You could withdraw $3,000 ETH + $4,000 WBTC + $3,000 GREEN, or any other combination up to $10,000.

### Value Preservation

**Your share value is protected**:
- Liquidation discounts become your profit
- GREEN redemptions don't dilute your value (GREEN = $1)
- All yields and rewards accrue to your position

The stability pool system creates a market-based liquidation mechanism that benefits both liquidated users and pool participants while maintaining protocol solvency.

For technical implementation details, see [StabilityPool Technical Documentation](technical/vaults/StabilityPool.md).