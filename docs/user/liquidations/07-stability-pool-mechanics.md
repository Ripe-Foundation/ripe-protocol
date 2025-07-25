# Stability Pool Mechanics

Stability pools hold assets that can instantly swap for liquidated collateral. This mechanism enables rapid liquidations without selling on external markets.

## Pool Composition

### Primary Assets

Stability pools can hold different asset types:

**GREEN LP Tokens**: Liquidity provider tokens from GREEN/USDC pools
- Used first in liquidation priority
- Sent to Endaoment treasury when consumed
- Represents protocol-owned liquidity

**sGREEN (Savings GREEN)**: Yield-bearing GREEN tokens
- Used after LP tokens are exhausted
- Redeemed to GREEN and burned during liquidation
- Earns yield while waiting in pool

### Claimable GREEN

A special mechanism for pending redemptions:

- **Accumulated GREEN**: From previous partial redemptions
- **Priority Usage**: Consumed before touching depositor assets
- **Zero Impact**: Burns directly without affecting pool participants

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

- **Supported Assets**: Which tokens the pool accepts
- **Capacity Limits**: Maximum holdings per asset
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

### Yield Generation

Pool participants earn from multiple sources:

- **Base Yield**: sGREEN appreciation while in pool
- **Liquidation Premiums**: Discounts on acquired collateral
- **LP Token Value**: Trading fees from underlying liquidity

### Risk Factors

Participants face several risks:

- **Collateral Volatility**: Acquired assets may decline in value
- **Timing Risk**: Cannot control when liquidations occur
- **Liquidity Lock**: Assets committed until withdrawn
- **Opportunity Cost**: Capital could be deployed elsewhere

### Pool Incentives

The system encourages participation through:

- **Profitable Spreads**: Discounts typically exceed market volatility
- **Passive Income**: No active management required
- **Protocol Rewards**: Additional RIPE token incentives
- **Compound Effects**: Yields stack with liquidation profits

## Withdrawal Mechanics

### Standard Withdrawals

Pool participants can exit positions:

- **Full Liquidity**: Withdraw deposited assets anytime
- **No Penalties**: Exit without fees or restrictions
- **Proportional Share**: Receive percentage of pool assets

### Post-Liquidation State

After pools participate in liquidations:

- **Asset Composition**: Pool holds acquired collateral
- **Value Preservation**: Total value includes discount gains
- **Rebalancing Options**: Swap collateral back to original assets

## System Integration

### Price Discovery

Stability pools rely on accurate asset pricing:

- **Current Values**: Real-time prices determine exchange ratios
- **Multiple Sources**: Several price feeds ensure accuracy
- **Continuous Updates**: Prices refresh to reflect market conditions

### System Integration

Stability pools connect with other protocol components:

- **Liquidation Process**: Pools provide liquidity during Phase 2
- **Asset Management**: Vaults hold and track pool deposits
- **Value Flows**: LP tokens move to treasury, sGREEN gets burned

The stability pool system creates a market-based liquidation mechanism that benefits both liquidated users and pool participants while maintaining protocol solvency.

For technical implementation details, see [StabilityPool Technical Documentation](technical/vaults/StabilityPool.md).