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
2. **[Deposit & Withdrawal Mechanics](02-deposit-withdrawal-mechanics.md)** - Asset flow mechanisms and processes
3. **[Supported Assets](03-supported-assets.md)** - Asset categories and parameters
4. **[Asset Parameters](04-asset-parameters.md)** - Configuration and vault architecture
5. **[Delegation & Permissions](05-delegation-permissions.md)** - Access control systems
6. **[Special Asset Types](06-special-asset-types.md)** - NFT and RWA collateral handling

## Asset Diversity Through Risk Isolation

Ripe's ability to accept diverse asset types stems from its individual risk isolation architecture. Unlike pooled lending protocols where all users share bad debt risk, Ripe isolates each borrower's risk profile.

This isolation combines with:
- Three-phase liquidation mechanisms
- Asset-specific parameter configuration
- Progressive liquidation approaches

The result enables support for assets ranging from blue-chip cryptocurrencies to experimental tokens while maintaining protocol solvency.

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