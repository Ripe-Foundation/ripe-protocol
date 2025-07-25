# Repaying Your Loan

Repaying your loan in Ripe Protocol is straightforward and flexible. You can repay any amount at any time, from small partial payments to complete loan closure. This guide covers everything you need to know about the repayment process.

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

**Benefits of Partial Repayment:**
- Reduce liquidation risk
- Lower ongoing interest costs
- Maintain leveraged position
- Flexibility to re-borrow later

## Where to Get GREEN for Repayment

### 1. Decentralized Exchanges (DEXs)

Purchase GREEN on supported exchanges:
- **Primary Pairs**: GREEN/USDC (Curve)
- **Check Multiple DEXs**: Prices may vary
- **Consider Slippage**: Large purchases may impact price

### 2. Redeem from sGREEN

If you hold sGREEN (Savings GREEN):
1. Convert sGREEN → GREEN at current exchange rate
2. Use redeemed GREEN for repayment
3. Benefits from any accumulated yield
4. No slippage or trading fees

**Example:**
```
Holding: 1,000 sGREEN
Current rate: 1 sGREEN = 1.05 GREEN
Redeem for: 1,050 GREEN
Extra 50 GREEN from yield earnings
```

### 3. Withdraw from Stability Pools

If participating in stability pools:
1. Withdraw your sGREEN from pool
2. Redeem to GREEN if needed
3. May forfeit ongoing rewards
4. Consider timing for optimal returns

## The Repayment Process

### Step 1: Check Current Debt

Before repaying, verify your total debt:
- **Principal**: Original borrowed amount
- **Accrued Interest**: Interest accumulated to current block
- **Total Due**: Principal + Interest

**Important**: Interest accrues every block (~2 seconds), so your exact repayment amount changes constantly.

### Step 2: Acquire GREEN

Obtain enough GREEN to cover your intended repayment:
- For full repayment: Get slightly more than shown debt (to cover accruing interest)
- For partial repayment: Any amount helps improve position

### Step 3: Approve GREEN Spending

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