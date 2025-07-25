# Delegation & Permissions

Ripe Protocol allows addresses to grant specific operational permissions to other addresses or smart contracts, enabling automated strategies and professional management while maintaining security.

## Core Concept

Delegation enables you to grant specific permissions to other addresses without giving up ownership of your assets. All value flows (withdrawals, borrows, claims) always return to the original owner.

## The Four Permission Types

### 1. Withdraw Permission
- Allows withdrawal of collateral from your position
- Funds go to your address, not the delegate's
- Useful for automated rebalancing

### 2. Borrow Permission  
- Enables borrowing GREEN against your collateral
- Borrowed funds go to your address
- Common for managed accounts and strategies

### 3. Stability Pool Claims
- Permits claiming liquidation rewards from stability pools
- Includes both premiums and RIPE rewards
- Useful for automated harvesting

### 4. Loot Claims
- Allows claiming RIPE protocol rewards
- Covers all points-based distributions
- Often combined with stability pool claims

## Key Use Cases

### Automated Strategies
Smart contracts can manage positions based on market conditions:
- Rebalancing collateral ratios
- Stop-loss mechanisms
- Yield optimization
- **Hightop users**: Underscore protocol integration requires delegation to enable advanced features

### Multi-Signature Management
DAOs and institutions use delegation for:
- Treasury management with multiple approvers
- Separation of operational and ownership roles
- Transparent on-chain operations

### Professional Management
Fund managers can operate positions while clients retain ownership:
- Active position management
- Risk mitigation strategies
- Performance optimization

## Security Features

### Built-in Protections
- **No Asset Transfer**: Delegates cannot move assets to their addresses
- **No Sub-Delegation**: Delegates cannot grant permissions to others
- **Instant Revocation**: Remove permissions immediately at any time
- **Owner Control**: All value flows return to the original owner

### Important Considerations
- Smart contract delegates execute code automatically - audit carefully
- Multiple delegates can have different permission sets
- All delegated actions are traceable on-chain
- Delegation does not help with lost wallet recovery

## How It Works

1. **Grant Permissions**: Choose which permissions to grant to which address
2. **Delegate Acts**: The delegate can perform allowed actions on your behalf
3. **Value Returns**: All funds from actions return to your address
4. **Revoke Anytime**: Remove permissions instantly when needed

Delegation provides flexibility for advanced strategies while maintaining the security principle that only the owner can receive value from their position.