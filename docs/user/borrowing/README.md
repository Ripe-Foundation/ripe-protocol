# Borrowing

This section explains how Ripe Protocol's borrowing system works, from GREEN stablecoin creation to debt management and repayment mechanisms.

Borrowing in Ripe Protocol involves minting GREEN stablecoin against deposited collateral. The protocol creates GREEN tokens when loans originate and burns them upon repayment, maintaining supply-demand equilibrium.

## Borrowing System Overview

The protocol's borrowing mechanism features:

- **Unified Positions**: All collateral backs a single loan
- **GREEN Creation**: Stablecoin minted against collateral value
- **Dynamic Rates**: Interest rates adjust based on market conditions
- **Flexible Repayment**: No prepayment penalties or time restrictions
- **Safety Mechanisms**: Multiple systems prevent bad debt accumulation

## Documentation Structure

1. **[GREEN Stablecoin](green.md)** - The protocol's native stablecoin mechanics
2. **[Borrowing Mechanics](01-borrowing-mechanics.md)** - Core borrowing system functionality
3. **[Understanding Your Debt](02-understanding-debt.md)** - Debt composition and management
4. **[Dynamic Rate Protection](03-dynamic-rate-protection.md)** - Interest rate adjustment mechanisms
5. **[Borrowing Limits](04-borrowing-limits.md)** - Protocol constraints and parameters

## Core Concepts

### Borrowing Power
Maximum GREEN mintable based on aggregate collateral value multiplied by respective loan-to-value ratios.

### Debt Health
Metric indicating position safety relative to liquidation thresholds. Calculated as the ratio of collateral value to outstanding debt.

### Interest Rate Dynamics
Rates adjust algorithmically based on market conditions, pool health, and asset-specific parameters. The Dynamic Rate Protection system maintains GREEN stability through automated adjustments.

### Liquidation Process
Collateral liquidation occurs when positions breach minimum collateralization ratios, executed through the three-phase system to minimize losses.