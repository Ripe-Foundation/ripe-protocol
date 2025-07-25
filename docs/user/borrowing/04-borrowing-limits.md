# Borrowing Limits

Ripe Protocol implements multiple borrowing constraints to ensure system stability and prevent exploitation.

## Types of Limits

### 1. Collateral-Based Limits

The fundamental limit based on your deposited assets:

**How it works**:
- Each asset has a maximum loan-to-value (LTV) ratio
- Your total borrowing power = Sum of (Asset Value × LTV)
- Cannot borrow more than this calculated maximum

Maximum borrowing capacity equals the sum of each asset's value multiplied by its loan-to-value ratio. This creates the fundamental borrowing constraint.

### 2. Per-User Debt Limits

Individual borrowing cap per address:

**How it works**:
- Fixed maximum debt per user
- Same limit applies to all users
- Temporary measure for controlled growth
- Will be removed as protocol matures

When per-user limits are active, borrowing capacity becomes the minimum of collateral-based limits and per-user caps. This mechanism enables controlled protocol growth.

### 3. Global Protocol Limits

System-wide caps for overall stability:

**Total Debt Ceiling**:
- Maximum GREEN that can exist
- Prevents unlimited minting
- Adjusted by governance

The protocol maintains a global debt ceiling that caps total GREEN supply. New borrowing becomes unavailable when this system-wide limit is reached.

### 4. Time-Based (Interval) Limits

Anti-manipulation mechanism using time windows:

**How Intervals Work**:
- Borrowing tracked per time period
- Typically 1,000-5,000 blocks
- Resets after interval expires

Interval limits track borrowing within rolling time windows, preventing rapid protocol exploitation while maintaining legitimate usage patterns. These windows reset automatically, creating temporary borrowing constraints that smooth demand.

## Additional Considerations

### Per-Asset Deposit Limits

Note: Some assets may have deposit limits (not borrowing limits):

**Purpose**:
- Control exposure to new or volatile assets
- Gradual integration of new collateral types
- Risk management during trial periods

**Example**:
```
PEPE: Max $1M total deposits protocol-wide
NEW_TOKEN: Max $100k during trial period
```

These affect how much collateral you can deposit, indirectly limiting borrowing power.

## Understanding Limit Interactions

### Hierarchy of Limits

When borrowing, the protocol checks in order:
1. **Collateral Limit**: Do you have enough collateral?
2. **Minimum Debt**: Is the loan above minimum size?
3. **User Limit**: Are you under your personal cap?
4. **Global Limit**: Is protocol capacity available?
5. **Interval Limit**: Is current period capacity available?

The most restrictive limit applies.

### Example Scenario

**Your Situation**:
- Collateral allows: $100,000 borrow
- Your user limit: $75,000
- Global space available: $50,000
- Current interval space: $30,000

**Maximum you can borrow now**: $30,000

You'd need to wait for:
- Next interval for more immediate capacity
- Other users to repay for global space
- Governance to raise your user limit

## Additional Limit Types

### Minimum Debt Requirement

Small loans aren't economical due to gas costs:
- **Typical Minimum**: $100-500
- **Purpose**: Prevents dust attacks and reduces complexity
- **Impact**: Must consolidate small borrowing needs

### Emergency Circuit Breakers

During extreme market events, temporary restrictions may apply:
- Rapid borrowing surge → Temporary pause
- Oracle issues → Reduced limits
- Liquidation cascade → Borrowing freeze

---

Next: Learn about [Repaying Your Loan](05-repaying-loans.md) →