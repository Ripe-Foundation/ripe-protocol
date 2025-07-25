# Collateral Assets

This section covers how Ripe Protocol's multi-collateral system works, including asset types, deposit mechanics, and portfolio management features.

Ripe Protocol accepts diverse tokenized assets as collateral through a unified system that enables portfolio-based borrowing. The protocol's architecture supports assets ranging from major crypto assets to tokenized real-world assets.

## Collateral System Architecture

The protocol's collateral framework operates through:

- **Unified Positions**: Multiple assets backing single loans
- **Portfolio Diversification**: Risk distribution across asset types
- **Yield Preservation**: Productive assets maintain earning capabilities
- **Extensible Design**: New asset types integrate without core changes

## Documentation Structure

1. **[Multi-Collateral System](01-multi-collateral-system.md)** - Portfolio-based collateral mechanics
2. **[Supported Assets](02-supported-assets.md)** - Asset categories and special handling
3. **[Asset Parameters](03-asset-parameters.md)** - Risk parameters and configuration
4. **[Delegation & Permissions](04-delegation-permissions.md)** - Access control systems

## What Makes Ripe Different

**Borrow against ANY asset** - Unlike Aave or Compound which only accept a handful of blue-chip assets, Ripe enables borrowing against:
- Yield-bearing positions (stETH, LP/vault tokens)
- Tokenized real-world assets
- Meme coins (PEPE, SHIB, DOGE)
- Gaming tokens and NFTs
- Any future tokenized value

This universal collateral support is possible because Ripe doesn't pool user funds. In Aave/Compound, all lenders share risk - one bad asset can hurt everyone. In Ripe, each position is independent, and our three-phase liquidation system (stability pool → auction → direct redemption) ensures positions are resolved before bad debt occurs. This architecture enables safe support for volatile assets that would create systemic risk in pooled lending protocols.

## Core Principles

### Unified Position Management
All deposited assets contribute to a single borrowing position, eliminating the complexity of managing multiple isolated loans.

### Dynamic Collateral Composition
Assets can be added or removed subject to maintaining adequate collateralization ratios.

### Yield Continuity
Yield-bearing assets maintain their productive characteristics while serving as collateral.

### Individual Risk Containment
Each user's collateral choices affect only their position, preventing systemic contagion.

### Immediate Liquidity
No mandatory lock-up periods or withdrawal delays under normal operating conditions.