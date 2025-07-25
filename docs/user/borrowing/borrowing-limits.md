# Borrowing Limits & Controls

Ripe Protocol implements multiple borrowing limits to ensure system stability, prevent manipulation, and protect users. Understanding these limits helps you plan your borrowing strategy and avoid unexpected restrictions.

## Types of Limits

### 1. Collateral-Based Limits

The fundamental limit based on your deposited assets:

**How it works**:
- Each asset has a maximum loan-to-value (LTV) ratio
- Your total borrowing power = Sum of (Asset Value × LTV)
- Cannot borrow more than this calculated maximum

**Example**:
```
Deposited: $50,000 in various assets
Weighted Average LTV: 75%
Maximum Borrow: $37,500
```

This is your hard ceiling regardless of other limits.

### 2. Per-User Debt Limits

Individual borrowing cap per address:

**How it works**:
- Fixed maximum debt per user
- Same limit applies to all users
- Temporary measure for controlled growth
- Will be removed as protocol matures

**Example**:
```
Per-user limit: $100,000
Your collateral allows: $200,000
Maximum you can borrow: $100,000
```

This ensures gradual protocol scaling during early stages.

### 3. Global Protocol Limits

System-wide caps for overall stability:

**Total Debt Ceiling**:
- Maximum GREEN that can exist
- Prevents unlimited minting
- Adjusted by governance

**Current Example**:
- Global Limit: 50,000,000 GREEN
- Current Supply: 35,000,000 GREEN
- Available: 15,000,000 GREEN

When the global limit is reached, no new borrowing is possible until debt is repaid or limits increase.

### 4. Time-Based (Interval) Limits

Anti-manipulation mechanism using time windows:

**How Intervals Work**:
- Borrowing tracked per time period
- Typically 1,000-5,000 blocks
- Resets after interval expires

**Example**:
```
Interval: 1,000 blocks (~33 minutes on Base)
Limit: 1,000,000 GREEN per interval
Current Interval Used: 750,000 GREEN
Available This Interval: 250,000 GREEN
```

**Purpose**:
- Prevent flash loan attacks
- Smooth borrowing demand
- Allow system monitoring

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

Next: Learn about [Repaying Your Loan](repaying-loans.md) →