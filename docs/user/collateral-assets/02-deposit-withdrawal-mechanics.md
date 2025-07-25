# Deposit & Withdrawal Mechanics

Ripe Protocol's deposit and withdrawal system operates through a unified architecture that supports diverse asset types while maintaining security and efficiency.

## System Architecture

### The Teller Contract

The Teller serves as the protocol's universal entry point, abstracting away complexity while maintaining flexibility. This design pattern enables:

- Single interface for all asset operations
- Automatic vault routing based on asset type
- Unified accounting across heterogeneous assets
- Permission management and access control

### Deposit Flow Mechanics

When assets enter the protocol:

1. **Token Approval**: Standard ERC-20 approval mechanism to Teller
2. **Deposit Execution**: Teller receives assets and determines routing
3. **Vault Assignment**: Assets routed to appropriate vault type
4. **Ledger Update**: Position recorded in global accounting system
5. **Points Accrual**: Immediate participation in rewards system

## Deposit Mechanisms

### Token Approval Pattern

The protocol follows standard ERC-20 patterns:
- Address approves Teller contract for specific amounts
- Approval can be exact or higher for future deposits
- Standard security considerations apply

### Asset Reception

The Teller contract:
- Validates deposit parameters
- Transfers tokens from depositor
- Routes to appropriate vault
- Updates global accounting

### Deposit Types

**Standard Deposits**
- Single asset operations
- Exact amount specification
- Most common interaction pattern

**Batch Operations** 
- Multiple assets in one transaction
- Significant gas optimization (60-70% savings)
- Atomic execution guarantees

**Maximum Balance Deposits**
- Deposits entire token balance
- Eliminates precision calculations
- Useful for complete position transfers

## Withdrawal Mechanics

### Withdrawal Process

Asset withdrawal follows similar patterns to deposits:
- Request processed through Teller
- Vault releases assets
- Direct transfer to user address
- No time locks or penalties

### Withdrawal Constraints

The protocol enforces safety checks:
- Remaining collateral must maintain debt coverage
- Minimum balance requirements must be met
- Positions in liquidation are restricted
- Health factor calculations prevent unsafe withdrawals

### Collateral Release Logic

Withdrawable amounts depend on:
- Current debt obligations
- Asset-specific LTV ratios
- Overall position health
- Minimum balance requirements

## Advanced Features

### Batch Operation Economics

The protocol supports atomic multi-asset operations:

**Technical Implementation**:
- Array of deposit/withdrawal structs
- Single transaction execution
- All-or-nothing atomicity
- Significant gas optimization

**Economic Benefits**:
- 60-70% gas reduction versus sequential operations
- Reduced MEV exposure through atomic execution
- Simplified portfolio management

### Vault Routing Logic

The protocol implements intelligent vault selection:

**Automatic Routing** (Default)
- Primary vault assignment per asset type
- Gas-optimized selection algorithm
- Handles most use cases efficiently

**Manual Vault Specification**
- Direct vault ID targeting
- Enables specialized strategies
- Required for non-primary vaults

### Specialized Deposit Flows

**GREEN to Stability Pool Pipeline**

The protocol enables atomic conversion and deposit:
- GREEN receipt by Teller
- Automatic sGREEN conversion
- Direct stability pool deposit
- Immediate premium eligibility

This design minimizes transaction costs and MEV exposure.

**Governance Token Locking**

RIPE tokens support time-locked deposits:
- Lock duration: 3-24 months
- Voting power scales with duration
- Enhanced rewards for longer commitments
- Early exit penalties maintain alignment

## Understanding Deposit Limits

### Per-User Limits

Each asset may have personal deposit caps:
- Protects protocol during growth phases
- Higher limits for established assets
- Can be increased through governance

**Limit Mechanics**:
- Each address has tracked deposit amounts per asset
- Remaining capacity equals per-user limit minus current deposits
- Limits enforce at the contract level

### Global Limits

Protocol-wide caps for risk management:
- Total value locked per asset
- Prevents overexposure
- Adjusted as protocol grows

**Limit Scenarios**:
- Different assets may have available capacity
- Global limits depend on total protocol deposits
- Governance can adjust limits based on risk assessment

### Minimum Balances

Some assets require minimum deposits:
- Prevents dust amounts
- Ensures gas efficiency
- Typically $100-500 minimum

## Points and Rewards

### Point Accumulation Mechanics

Deposited assets generate points each block through:
1. Balance point accumulation
2. USD value calculation
3. Asset-type allocation
4. RIPE reward contribution

**Point Allocation Framework**:

Assets receive differentiated point rates based on risk profiles:
- Established cryptocurrencies: baseline rates
- Stablecoins: reduced rates reflecting lower risk
- Volatile assets: elevated rates compensating for risk
- Governance positions: maximum rates incentivizing participation

## System Behavior Patterns

### Portfolio Construction

Multi-asset deposits create unified positions with aggregate borrowing capacity, weighted parameters, and optimized transaction efficiency through batching.

### Position Optimization

Collateral composition adjustments modify risk parameters, borrowing costs, and liquidation thresholds without disrupting active loans.

### Withdrawal Constraints

The protocol enforces health factor maintenance during withdrawals, calculating maximum safe amounts based on remaining collateralization requirements.

## System Constraints

### Operational Boundaries

The protocol enforces:
- Non-zero deposit requirements
- Per-user and global deposit limits
- Balance sufficiency validations
- Asset-specific access controls

These constraints ensure system integrity and risk management while preventing exploitation vectors.

## Economic Considerations

### Economic Design Principles

**Transaction Efficiency**: Batch operations and optimized routing minimize gas consumption while maintaining atomicity.

**Risk Mitigation**: Health checks, minimum balances, and access controls create multiple safety layers.

**Capital Optimization**: Immediate utilization, yield preservation, and flexible management maximize capital efficiency.

The deposit and withdrawal architecture balances security requirements with operational flexibility, creating a robust foundation for multi-asset collateral management.

