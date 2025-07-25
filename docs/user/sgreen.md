# Savings GREEN (sGREEN)

sGREEN is the yield-bearing representation of GREEN stablecoin that automatically accrues value through protocol revenue distribution. It operates as a share-based token where each unit represents a proportional claim on the underlying GREEN pool.

## sGREEN Mechanism

### Fundamental Design

sGREEN implements a share-based value accrual system where:
- Protocol revenues automatically increase share value
- Each sGREEN maintains minimum 1:1 GREEN backing
- Redemption remains available without time restrictions
- Implements ERC-4626 vault standard for interoperability

### Value Accrual Mechanism

sGREEN employs an exchange rate model rather than rebasing:

**Exchange Rate Calculation:**
The rate equals total GREEN in the pool divided by total sGREEN supply.

**Rate Progression:**
The exchange rate increases as protocol revenues flow into the pool. This creates a monotonically increasing value per share, where the rate can only increase or remain stable, never decrease.

## Revenue Sources

### 1. Borrowing Interest

The protocol collects interest from GREEN borrowers:
- Interest payments flow into the sGREEN pool
- Pool growth increases the exchange rate
- All sGREEN holders benefit proportionally

### 2. Origination Fees

Daowry fees charged on loan origination:
- One-time fee on new borrowing positions
- Typically configured around 0.5% of borrowed amount
- Immediate contribution to pool value

### 3. Protocol Fee Distribution

Liquidation-related revenues:
- Base protocol fees from liquidation events accrue to sGREEN
- Distinct from liquidation discounts earned by stability pool participants
- Holding sGREEN captures protocol fees while stability pools capture liquidation premiums

## sGREEN Acquisition Methods

### Direct Conversion Mechanism

GREEN tokens convert to sGREEN through the vault interface:
- GREEN deposits into the sGREEN pool
- sGREEN minted based on current exchange rate
- Proportional share ownership established

**Conversion Dynamics:**
When the exchange rate exceeds 1:1, depositors receive fewer sGREEN tokens than GREEN deposited, but each sGREEN represents more GREEN value.

### Direct Borrowing Option

The protocol allows borrowers to receive loans directly as sGREEN:
- Borrowed amount mints directly into sGREEN
- Immediate participation in yield generation
- Single transaction efficiency

**Economic Implications:**
Borrowers receiving sGREEN may benefit if sGREEN yield exceeds borrowing costs, creating a positive carry position where loans partially self-amortize through yield.

## System Characteristics

### Automatic Value Accrual

The protocol design enables:
- Continuous compounding without user interaction
- No manual claiming or restaking requirements
- Gas efficiency through pooled operations
- Passive value accumulation

### Liquidity Properties

Redemption mechanics:
- Unrestricted GREEN redemption availability
- No exit fees or penalties
- No mandatory waiting periods
- Minimum 1:1 value preservation

### Tax Considerations

Structural implications:
- Value accrual through price appreciation rather than distribution
- Single redemption event for realized gains
- Simplified tracking compared to multiple distributions
- Tax treatment varies by jurisdiction

### Protocol Composability

Integration capabilities:
- Potential collateral asset in lending protocols
- Liquidity pairing with GREEN or other stables
- Compatible with yield aggregation protocols
- Cross-protocol utility expansion

## sGREEN Economic Dynamics

### Holding Mechanics

Basic sGREEN ownership provides:
- Automatic capture of protocol revenues
- Compound growth through exchange rate appreciation
- Flexible redemption timing
- Passive yield generation

Typical yields derive from aggregate protocol activity including borrowing demand and fee generation.

### Borrowing Integration

Direct sGREEN borrowing creates:
- Immediate yield exposure on borrowed funds
- Potential interest cost offset
- Single-transaction efficiency
- Dynamic position management

The economic outcome depends on the relationship between borrowing costs and sGREEN appreciation rates.

### Stability Pool Deployment

sGREEN in [stability pools](../liquidations/stability-pool-mechanics.md) generates:
- Base sGREEN appreciation (protocol revenues)
- Liquidation discount capture (pool participation)
- Additional protocol incentives when available

**Revenue Distinction:**
Holding sGREEN captures protocol fee distribution while [stability pool participation](../liquidations/stability-pool-swaps.md) adds liquidation premiums.

### Liquidity Pool Participation

sGREEN/GREEN liquidity positions feature:
- Highly correlated asset pairing
- Reduced impermanent loss risk
- Trading fee accumulation
- Combined yield sources

The stable relationship between sGREEN and GREEN creates favorable liquidity provision dynamics.

## Implementation Architecture

### Vault Standard Compliance

sGREEN implements the ERC-4626 tokenized vault standard, providing:
- Standardized deposit and withdrawal interfaces
- Share-to-asset conversion functions
- Predictable integration patterns
- Industry-standard vault mechanics

### Exchange Rate Dynamics

Rate appreciation occurs through:
- Interest payment accumulation
- Origination fee collection
- Protocol fee distribution
- Revenue stream aggregation

### Protocol Integration

The system supports:
- Full ERC-20 token functionality
- ERC-4626 vault operations
- Standard DeFi composability
- Transparent value accounting

For technical implementation details, see:
- [SavingsGreen Technical Documentation](../technical/tokens/SavingsGreen.md)
- [ERC-4626 Token Module Documentation](../technical/tokens/modules/Erc4626Token.md)

## Operational Characteristics

### Holding Period Requirements
The protocol imposes no minimum holding periods or lock-up requirements. Redemption remains available at any time.

### Exchange Rate Stability
The system design ensures monotonic rate growth - the exchange rate can only increase or remain stable, never decrease.

### Emergency Scenarios
Protocol emergency mechanisms maintain the GREEN backing of all sGREEN tokens. The vault structure preserves asset segregation.

### Compounding Frequency
Value accrual occurs continuously as protocol revenues flow into the system, with no discrete compounding events.

### Token Transferability
sGREEN functions as a standard ERC-20 token with full transfer capabilities and DeFi compatibility.

### Peg Independence
The sGREEN-to-GREEN exchange rate operates independently of GREEN's USD value. Market fluctuations in GREEN's dollar price do not affect the sGREEN exchange rate.

## System Summary

sGREEN provides automated yield generation on GREEN holdings through a share-based vault mechanism. The system captures protocol revenues, maintains full liquidity, and integrates with broader DeFi infrastructure through standard interfaces.

The architecture creates sustainable value accrual while preserving capital flexibility and compositional utility across the ecosystem.