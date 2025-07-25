# Liquidation Phases

Ripe Protocol implements a three-phase liquidation system that prioritizes different asset types and mechanisms based on their characteristics and protocol configuration. This system enables the [multi-collateral framework](../collateral-assets/multi-collateral-system.md) to support diverse asset types safely.

## The Three-Phase System

The protocol categorizes assets into three phases based on liquidation method:

```
LIQUIDATION TRIGGER
        |
        v
┌─────────────────────────────────────────────────────────┐
│                   ASSET ROUTING                         │
└─────────────────┬─────────────┬─────────────────────────┘
                  │             │
                  v             v
        ┌─────────────┐   ┌─────────────────┐
        │   PHASE 1   │   │     PHASE 2     │
        │             │   │                 │
        │ GREEN/sGREEN│   │ Stability Pools │
        │ Stablecoins │   │   (WETH, etc)   │
        │             │   │                 │
        │   INSTANT   │   │    INSTANT      │
        │  SETTLEMENT │   │   LIQUIDATION   │
        └─────────────┘   └─────────────────┘
                                     │
                                     v
                            ┌─────────────────┐
                            │     PHASE 3     │
                            │                 │
                            │ Dutch Auctions  │
                            │  (All Others)   │
                            │                 │
                            │  TIME-BASED     │
                            │   SETTLEMENT    │
                            └─────────────────┘
```

**Phase 1**: Protocol deposits and stablecoins
**Phase 2**: Major cryptocurrencies with stability pool support  
**Phase 3**: All other assets requiring auction mechanisms

All phases operate **concurrently** - assets route to appropriate mechanisms simultaneously.

## Phase 1: Protocol Deposits and Stablecoins

**Assets in this phase:**
- GREEN and sGREEN held in protocol vaults
- Stablecoins designated for treasury transfer (USDC, USDT, etc.)

**Mechanism:**
- GREEN/sGREEN burns directly to reduce debt
- Stablecoins transfer to Endaoment treasury at full value
- No market operations required

**Phase 1 Operation:**
When liquidation requires debt repayment, sGREEN burns at face value to reduce the debt. Any remaining debt after Phase 1 mechanisms proceeds to subsequent phases.

## Phase 2: Stability Pool Eligible Assets

**Assets in this phase:**
- Major cryptocurrencies configured with stability pools
- Assets explicitly marked for pool swaps in configuration

**Mechanism:**
- Collateral swaps with stability pool participants
- Discount equals the asset's liquidation fee parameter
- Pool liquidity determines processing capacity

**Phase 2 Operation:**
Stability pools exchange collateral for debt reduction at predetermined discounts. The liquidation fee parameter determines the economic loss during this exchange.

## Phase 3: Auction-Based Liquidation

**Assets in this phase:**
- Tokens without stability pool support
- NFTs and unique assets
- Assets configured for auction-only liquidation

**Mechanism:**
- Dutch auction with increasing discount over time
- Starting and maximum discounts set per asset type
- Market participants bid using GREEN tokens

**Example:**
```
Still need: $500
Your NFT: Worth $800

Result: NFT goes to auction
Expected sale: ~$600 (after discounts)
Debt cleared, but higher loss
```

## Phase Interaction Mechanics

The liquidation system processes assets until the position reaches target health:

### Quick Resolution
```
Total needed: $10,000

Phase 1: Burn $6,000 sGREEN ✓
Phase 2: Swap $4,000 WETH ✓
Phase 3: Not needed!

Your other assets: Safe
```

### Full Liquidation
```
Total needed: $50,000

Phase 1: Burn $5,000 GREEN
Phase 2: Swap $35,000 mixed crypto
Phase 3: Auction $10,000 in NFTs

All phases used to restore health
```

## Why This Matters

### For You
- **Smart positioning helps**: Keep sGREEN for protection
- **Asset choice matters**: Major tokens liquidate better
- **Phases stop when healthy**: Not everything gets liquidated

### What Triggers Each Phase
- System always starts with Phase 1
- Only moves to Phase 2 if more needed
- Phase 3 is truly last resort

## Phase Execution Details

**Asset Processing Order:**
1. Protocol deposits (GREEN/sGREEN) are consumed first
2. Priority liquidation assets defined in configuration
3. Remaining vault positions in order

**Simultaneous Processing:**
- All phases evaluate concurrently
- Each asset type routes to its designated mechanism
- Processing continues until debt is restored to health

## Key Mechanics

1. **Phase categorization** - Assets route to phases based on configuration
2. **Concurrent processing** - All phases evaluate simultaneously
3. **Partial liquidation** - Process stops when position reaches target health
4. **Priority ordering** - Within phases, specific assets process first
5. **Value preservation** - Earlier phases preserve more value than later ones

The three-phase system creates a hierarchy of liquidation mechanisms, each with different economic characteristics and market impacts.

Next: Learn about [Stablecoin Burning](stablecoin-burning.md) →