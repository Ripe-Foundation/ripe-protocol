# Savings GREEN (sGREEN)

Savings GREEN (sGREEN) is the yield-bearing version of GREEN stablecoin, allowing holders to earn protocol revenues automatically without any active management. It represents a share of the growing sGREEN pool and maintains full redeemability for GREEN at any time.

## What is sGREEN?

### Core Concept

sGREEN is a wrapped version of GREEN that:
- **Automatically compounds yield** from protocol revenues
- **Maintains 1:1+ GREEN redeemability** (always worth at least 1 GREEN)
- **No lock-up periods** - redeem anytime
- **ERC-4626 compliant** - standard yield-bearing token interface

### How Value Accrues

Unlike rebasing tokens, sGREEN uses an exchange rate model:

```
Exchange Rate = Total GREEN in Pool / Total sGREEN Supply
```

**Example Growth:**
- Day 1: 1 sGREEN = 1.00 GREEN
- Day 30: 1 sGREEN = 1.01 GREEN
- Day 365: 1 sGREEN = 1.08 GREEN

The exchange rate only increases, never decreases.

## Yield Sources

### 1. Borrowing Interest

The primary yield source comes from GREEN borrowers:
- Borrowers pay interest on their GREEN loans
- Interest accumulates in the sGREEN pool
- Distributed proportionally to all sGREEN holders

### 2. Daowry Fees

One-time origination fees from new loans:
- Typically 0.5% of borrowed amount
- Paid to sGREEN holders
- Provides immediate yield boost

### 3. Liquidation Fees

Revenue from liquidation events:
- Base liquidation fees go to sGREEN holders
- **Note**: Only if you deposit sGREEN into stability pools do you earn additional liquidation premiums
- Simply holding sGREEN earns base protocol fees, not liquidation discounts

## How to Get sGREEN

### Method 1: Direct Conversion

Convert existing GREEN to sGREEN:

1. **Approve GREEN spending** for sGREEN contract
2. **Deposit GREEN** into sGREEN pool
3. **Receive sGREEN** at current exchange rate

**Example:**
```
Current rate: 1 sGREEN = 1.05 GREEN
Deposit: 1,050 GREEN
Receive: 1,000 sGREEN
```

### Method 2: Borrow Directly to sGREEN

When taking a loan, receive sGREEN instead of GREEN:

**Benefits:**
- Start earning immediately
- No conversion needed
- Gas efficient
- Offset borrowing costs

**Example Strategy:**
```
Borrow Rate: 5% APR
sGREEN Yield: 8% APR
Net Benefit: +3% APR (self-paying loan)
```

## Key Features and Benefits

### Automatic Compounding

**No Action Required:**
- Yield compounds continuously
- No claiming or restaking needed
- Gas-efficient for all holders
- Set and forget simplicity

### Full Liquidity

**Instant Redemption:**
- Convert sGREEN → GREEN anytime
- No withdrawal fees
- No waiting periods
- Always receive at least 1:1

### Tax Efficiency

**Potential Benefits:**
- No taxable events from auto-compounding
- Single transaction for redemption
- Cleaner reporting vs. multiple claims
- *Consult your tax advisor*

### Composability

**DeFi Integration:**
- Use as collateral (where accepted)
- LP with GREEN for stable pairs
- Integration with yield aggregators
- Cross-protocol strategies

## sGREEN Strategies

### 1. Simple Holding

**Best For:** Passive income seekers

**Strategy:**
- Convert GREEN to sGREEN
- Hold long-term
- Benefit from compound growth
- Redeem when needed

**Expected Returns:** Base protocol yield (typically 5-10% APR)

### 2. Borrow and Hold

**Best For:** Active borrowers

**Strategy:**
- Borrow directly to sGREEN
- Hold while loan is active
- Yield offsets interest costs
- May achieve net positive returns

**Example Math:**
```
Collateral: $20,000 WETH
Borrow: 10,000 GREEN → sGREEN
Cost: 5% APR = $500/year
Yield: 8% APR = $800/year
Net Profit: $300/year
```

### 3. Stability Pool Stacking

**Best For:** Yield maximizers

**Strategy:**
- Deposit sGREEN into stability pools
- Earn base sGREEN yield (from holding sGREEN)
- Plus liquidation discounts (from stability pool participation)
- Plus RIPE rewards (if applicable)

**Important Distinction:**
- Holding sGREEN alone: Earns protocol fees and interest
- sGREEN in stability pools: Additionally earns liquidation premiums

**Potential Returns:** 15-25% APR during active liquidation periods

### 4. Liquidity Provision

**Best For:** Liquidity providers

**Strategy:**
- Create sGREEN/GREEN LP positions
- Minimal impermanent loss (correlated assets)
- Earn trading fees
- Plus sGREEN appreciation

**Benefits:**
- Stable pair dynamics
- Additional fee income
- Deep liquidity support

## Technical Details

### ERC-4626 Compliance

sGREEN follows the standard vault token interface:
- `deposit()` - Convert GREEN to sGREEN
- `redeem()` - Convert sGREEN to GREEN
- `convertToAssets()` - Check current exchange rate
- `totalAssets()` - View total GREEN in pool

For developers and technical users, see the contract documentation:
- [SavingsGreen.md](../../contracts/tokens/SavingsGreen.md) - Implementation details
- [Erc4626Token.md](../../contracts/tokens/Erc4626Token.md) - Base vault standard

### Exchange Rate Updates

The rate increases when:
- Interest payments received
- Daowry fees collected
- Liquidation fees added
- Any protocol revenue distributed

### Integration Guidelines

For developers and protocols:
- Standard ERC-20 functions supported
- Additional ERC-4626 vault functions
- Easy integration with existing DeFi
- Detailed documentation available

## Frequently Asked Questions

### Is there a minimum holding period?
No, you can redeem sGREEN for GREEN instantly at any time.

### Can the exchange rate ever decrease?
No, the exchange rate only increases. It cannot go down by design.

### What happens during protocol emergencies?
sGREEN maintains full backing by GREEN in the pool. Emergency procedures protect user funds.

### How often does yield compound?
Continuously with each protocol revenue event - borrowing interest, fees, etc.

### Can I transfer sGREEN?
Yes, sGREEN is a standard ERC-20 token that can be transferred, traded, or used in DeFi.

### Is sGREEN affected by GREEN's peg?
sGREEN maintains its GREEN exchange rate regardless of GREEN's USD peg. If GREEN = $0.95, 1 sGREEN still redeems for 1.05+ GREEN (at the current rate).

sGREEN represents the simplest way to earn yield on your stablecoins within the Ripe ecosystem, providing sustainable returns while maintaining full liquidity and composability.