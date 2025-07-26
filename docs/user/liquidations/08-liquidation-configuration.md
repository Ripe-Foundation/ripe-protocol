# Liquidation Configuration

The liquidation system operates according to parameters set at both the protocol and asset levels. These configurations determine liquidation behavior, mechanism selection, and economic outcomes.

## General Liquidation Configuration

The protocol maintains global liquidation settings that apply across all positions:

### Keeper Fee Structure

Liquidation keepers receive compensation based on the debt they help resolve:

- **Fee Ratio**: Percentage of repaid debt paid as keeper reward (typically 1-2%)
- **Minimum Fee**: Floor amount to ensure small liquidations remain profitable ($50-100)
- **Maximum Fee**: Cap to prevent excessive rewards on large positions ($10,000+)

### Position Health Target

The protocol aims to restore positions to a safe collateralization level:

- **Safety Buffer**: Additional margin beyond minimum requirements
- **Health Restoration**: Positions reach stable levels after liquidation
- **Conservative Sizing**: Calculations may slightly exceed minimum needs

### Processing Order

Certain assets receive priority treatment during liquidations:

**Priority Assets**: Major cryptocurrencies liquidated before others
**Priority Pools**: Specific stability pools checked first

## Asset-Specific Configuration

Each supported asset has individual liquidation parameters:

### Liquidation Routing

Assets are configured to use specific liquidation mechanisms:

- **Burn as Payment**: GREEN and sGREEN tokens burn directly for debt reduction
- **Transfer to Endaoment**: Stablecoins move to treasury reserves
- **Stability Pool Swaps**: Major cryptocurrencies swap with pool participants
- **Instant Auctions**: Assets immediately create auctions if not fully liquidated

### Custom Auction Parameters

Assets can override default auction settings:

- **Start Discount**: Initial discount percentage (e.g., 2-5%)
- **Maximum Discount**: Final discount at auction end (e.g., 20-50%)
- **Delay Period**: Blocks before auction starts after liquidation
- **Duration**: Total blocks for discount progression (entire auction duration)

### Special Stability Pools

Some assets may have designated stability pools:

- **Asset-Specific Pools**: Dedicated liquidity for particular tokens
- **Permissioned Pools**: Restricted access for regulated assets
- **Priority Routing**: Checked before general stability pools

## Liquidation Thresholds

Each asset defines critical risk parameters:

### Liquidation Threshold

The collateralization ratio where liquidation becomes possible:

- **Calculation**: Minimum collateral value = Debt × 100% / Liquidation Threshold%
- **Higher Percentages**: More restrictive (95% threshold = 105.3% minimum collateralization)
- **Asset Variance**: Stable assets have tighter thresholds than volatile ones

### Liquidation Fee

The cost charged during liquidation, which becomes the discount for buyers:

- **Base Fee**: Percentage of liquidated value (typically 5-15%)
- **Risk-Based**: Higher fees for volatile or illiquid assets
- **Weighted Average**: Multi-collateral positions blend fees proportionally

### Redemption Threshold

The earlier warning level where GREEN holders can redeem against positions:

- **Pre-Liquidation**: Activates before liquidation threshold
- **No Loss Mechanism**: 1:1 value exchange for position holders
- **Peg Protection**: Helps maintain GREEN stability

## Configuration Hierarchy

Parameters follow a specific precedence order:

1. **Asset-Specific Settings**: Custom configurations take priority
2. **General Parameters**: Default values for unconfigured aspects
3. **Protocol Minimums**: Safety limits that cannot be overridden

## Dynamic Adjustments

Some parameters adjust based on market conditions:

- **Rate Multipliers**: Affect borrowing costs during pool stress
- **Auction Extensions**: May lengthen during high volatility
- **Fee Scaling**: Keeper rewards may increase during cascading liquidations

The configuration system enables fine-tuned control over liquidation behavior while maintaining consistent protocol-wide safety standards.