# Loan Repayment

Loan repayment in Ripe Protocol supports flexible partial or complete debt settlement without time restrictions or prepayment penalties.

## Repayment Options

### Full Repayment

Completely close your loan position:
- Repay entire debt (principal + accrued interest)
- All collateral becomes withdrawable
- Position fully cleared from protocol
- No further interest accumulation

### Partial Repayment

Reduce your debt while maintaining your position:
- Repay any amount of GREEN
- Improves debt health immediately
- Reduces interest burden
- Maintains collateral exposure

Partial repayments reduce outstanding debt, decrease interest accumulation, and improve position health metrics while maintaining collateral exposure.

## GREEN Acquisition Methods

### Market Sources

GREEN tokens for repayment can be obtained through:
- Decentralized exchange liquidity pools
- sGREEN redemption at current exchange rates
- Stability pool withdrawals

### Redemption Mechanics

sGREEN holders can redeem tokens for GREEN based on the current exchange rate, capturing any accumulated yield in the process. Stability pool participants may withdraw their positions to access GREEN for repayment.

## Repayment Mechanics

### Debt Calculation

Total repayment amounts comprise:
- Principal debt from initial borrowing
- Accumulated interest through current block
- Continuous interest accrual during transaction

### Transaction Process

Repayment executes through GREEN token transfers to the protocol, requiring standard ERC-20 approval patterns. The system calculates exact debt at transaction time, accounting for block-by-block interest accumulation.

The CreditEngine contract needs permission to use your GREEN:
1. Approve GREEN token for CreditEngine
2. Can approve exact amount or infinite approval
3. One-time setup per address

### Step 4: Execute Repayment

Call the repayment function:
- **Full Repayment**: Specify you want to close position entirely
- **Partial Repayment**: Specify exact GREEN amount to repay

**Transaction Details:**
- GREEN is burned (removed from circulation)
- Debt balance updates immediately
- Collateral becomes withdrawable (proportional to repayment)
- Gas costs: Typically $5-20 depending on network

### Step 5: Verify Results

After transaction confirms:
- Check new debt balance
- Verify debt health improvement
- Confirm collateral withdrawal availability
- Review transaction logs

## What Happens to Your Collateral

### After Full Repayment

All collateral becomes immediately withdrawable:
- 100% of deposited assets unlocked
- Can withdraw individually or all at once
- No time delays or penalties
- Position completely closed

### After Partial Repayment

Collateral handling depends on your remaining debt:
- **Excess Collateral**: Can withdraw amount above required collateralization
- **Improved Ratios**: Better debt health, more borrowing capacity
- **Flexible Management**: Choose which assets to withdraw

**Example:**
```
Before: $20,000 collateral, $10,000 debt (50% utilization)
Repay: $5,000
After: $20,000 collateral, $5,000 debt (25% utilization)
Can withdraw: Up to $13,750 (keeping 80% LTV)
```

## Emergency Repayment

If approaching liquidation thresholds:

**Priority Actions:**
1. Acquire GREEN immediately (any source)
2. Execute partial repayment to improve health
3. Don't wait for "perfect" price
4. Focus on position safety over optimization

**Quick GREEN Sources:**
- DEX spot purchases
- sGREEN redemption
- Sell other assets for GREEN
- Community OTC markets

## After Repayment

### Position Closed (Full Repayment)
- All collateral withdrawable
- No ongoing obligations
- Can start fresh position anytime
- Clean transaction history

### Position Maintained (Partial Repayment)
- Monitor improved debt health
- Consider re-optimization
- Track ongoing interest
- Plan next actions

Repayment in Ripe Protocol is designed to be flexible and user-friendly, allowing you to manage your debt according to your needs and market conditions.

---

*For more on debt management, see [Understanding Your Debt](understanding-debt.md)*