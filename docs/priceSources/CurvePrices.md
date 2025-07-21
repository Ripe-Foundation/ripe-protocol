# CurvePrices Technical Documentation

## Overview

CurvePrices serves as a specialized oracle for pricing Curve Finance assets within the Ripe Protocol ecosystem. Think of it as a sophisticated price calculator that understands the complex mathematics behind Curve's automated market maker (AMM) pools - from stable pools that minimize slippage for similar assets to crypto pools that handle volatile pairs. Unlike simple token pricing, Curve pools require specialized calculations to derive accurate prices from their bonding curves, virtual prices, and liquidity balances.

At its core, CurvePrices manages five fundamental responsibilities:

**1. Multi-Pool Type Support**: Handles diverse Curve pool types including StableSwap NG, TwoCrypto NG, Tricrypto NG, and custom implementations, each with their own pricing mechanisms and interfaces for extracting accurate price data.

**2. LP Token Pricing**: Calculates the value of liquidity provider (LP) tokens by combining pool's virtual price with underlying asset values, providing accurate NAV (Net Asset Value) for liquidity positions across different pool types.

**3. Single Asset Pricing**: Retrieves individual token prices directly from Curve's internal price oracles, which use exponential moving averages (EMAs) to provide manipulation-resistant price feeds for pool assets.

**4. GREEN Reference Pool Monitoring**: Maintains special handling for the GREEN/USDC pool as a critical system reference, tracking its price stability through a snapshot system and implementing stabilizer mechanisms to maintain protocol health.

**5. Supply-Weighted Price Averaging**: For LP tokens, calculates supply-weighted average prices across underlying assets, ensuring the price reflects the actual composition and value of the liquidity pool.

For technical readers, CurvePrices implements the PriceSource interface with LocalGov for governance, TimeLock for configuration changes, and PriceSourceData for asset registry. It interfaces directly with Curve pool contracts using multiple interfaces (ICurvePool, ICurveStableSwapNG, ICurveTwoCryptoNG) to handle different pool implementations. The contract manages complex data structures including pool configurations with up to 4 underlying assets, pool type enumeration for proper interface selection, and special GREEN pool monitoring with snapshot-based stability tracking. Price calculations involve virtual price queries for stable pools, individual asset pricing via price_oracle functions, and decimal normalization across different token standards. The contract includes comprehensive validation, graceful handling of pool query failures, and time-locked governance for all configuration changes.

## Architecture & Dependencies

CurvePrices is built using a modular architecture with direct Curve protocol integration:

### Core Module Dependencies
- **LocalGov**: Provides governance functionality with access control
- **Addys**: Address resolution for protocol contracts
- **PriceSourceData**: Asset registration and pause state management
- **TimeLock**: Time-locked changes for configuration updates

### External Dependencies
- **PriceDesk**: Retrieves underlying asset prices for LP calculations
- **Curve Pools**: Direct integration with various Curve pool contracts
- **GREEN Pool**: Special reference pool for protocol stability

### Module Initialization
```vyper
initializes: gov
initializes: addys
initializes: priceData[addys := addys]
initializes: timeLock[gov := gov]
```

### Immutable Configuration
```vyper
GREEN: immutable(address)  # GREEN token address
```

## Data Structures

### PoolType Enum
Identifies different Curve pool implementations:
```vyper
enum PoolType:
    NONE                # Not configured
    STABLE_SWAP_NG      # Next-gen stable pools
    TWO_CRYPTO_NG       # Two-asset crypto pools
    TRI_CRYPTO_NG       # Three-asset crypto pools
    CUSTOM              # Custom implementations
```

### CurvePriceConfig Struct
Complete configuration for a Curve asset:
```vyper
struct CurvePriceConfig:
    pool: address                   # Curve pool contract
    lpToken: address                # LP token address
    numUnderlying: uint256          # Number of assets (0-4)
    underlying: address[4]          # Underlying assets
    poolType: PoolType              # Pool implementation type
    hasEcoToken: bool               # Contains ECO token
```

### PendingCurvePriceConfig Struct
Tracks configuration changes during timelock:
```vyper
struct PendingCurvePriceConfig:
    actionId: uint256               # TimeLock action ID
    config: CurvePriceConfig        # New configuration
```

### GreenPriceSnapshot Struct
Monitors GREEN pool stability:
```vyper
struct GreenPriceSnapshot:
    timestamp: uint256              # Snapshot time
    price: uint256                  # GREEN price at snapshot
```

### StabilizerConfig Struct
Controls GREEN price stabilization:
```vyper
struct StabilizerConfig:
    isActive: bool                  # Stabilizer enabled
    minPrice: uint256               # Minimum allowed price
    maxPrice: uint256               # Maximum allowed price
```

## State Variables

### Configuration Storage
- `priceConfigs: HashMap[address, CurvePriceConfig]` - Active configurations
- `pendingPriceConfigs: HashMap[address, PendingCurvePriceConfig]` - Pending changes
- `greenPoolConfig: CurvePriceConfig` - GREEN/USDC pool configuration
- `pendingGreenPoolConfig: PendingCurvePriceConfig` - Pending GREEN pool changes

### GREEN Pool Monitoring
- `greenPriceSnapshots: GreenPriceSnapshot[100]` - Circular buffer of snapshots
- `nextGreenSnapshotIndex: uint256` - Next snapshot position
- `greenSnapshotDelay: uint256` - Minimum blocks between snapshots
- `stabilizerConfig: StabilizerConfig` - Price stabilization settings

### Constants
- `NORMALIZED_DECIMALS: constant(uint256) = 18` - Standard decimals
- `HUNDRED_PERCENT: constant(uint256) = 100_00` - 100.00% for calculations
- `STALE_ORACLE_THRESHOLD: constant(uint256) = 86400 * 7` - 7 days

## System Architecture Diagram

```
+------------------------------------------------------------------------+
|                        CurvePrices Contract                           |
+------------------------------------------------------------------------+
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Price Calculation Flow                        |  |
|  |                                                                  |  |
|  |  getPrice(asset):                                                |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ 1. Load CurvePriceConfig for asset                         │ |  |
|  |  │ 2. Route to appropriate pricing method:                    │ |  |
|  |  │    - LP Token: Calculate via virtual price                 │ |  |
|  |  │    - Single Asset: Query pool's price oracle               │ |  |
|  |  │ 3. For LP tokens with multiple underlying:                  │ |  |
|  |  │    - Get each underlying price from PriceDesk              │ |  |
|  |  │    - Calculate supply-weighted average                      │ |  |
|  |  │    - Multiply by virtual price                              │ |  |
|  |  │ 4. Apply decimal normalization                              │ |  |
|  |  │ 5. Return final price in 18 decimals                       │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Pool Type Routing                             |  |
|  |                                                                  |  |
|  |  StableSwap NG Pools:                                            |  |
|  |  • get_virtual_price() for LP token value                       |  |
|  |  • price_oracle(i) for individual assets                        |  |
|  |  • Handles 2-4 assets with different decimals                    |  |
|  |                                                                  |  |
|  |  TwoCrypto NG Pools:                                             |  |
|  |  • virtual_price() for LP calculations                          |  |
|  |  • price_oracle() for asset prices                              |  |
|  |  • Optimized for two-asset volatile pairs                        |  |
|  |                                                                  |  |
|  |  TriCrypto NG Pools:                                             |  |
|  |  • virtual_price() with three assets                            |  |
|  |  • price_oracle(i) for each asset                               |  |
|  |  • Complex three-way price calculations                          |  |
|  |                                                                  |  |
|  |  Custom Pools:                                                   |  |
|  |  • Flexible interface for unique implementations                 |  |
|  |  • Fallback to standard methods                                  |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                  GREEN Reference Pool System                     |  |
|  |                                                                  |  |
|  |  GREEN/USDC Pool Monitoring:                                      |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │                  Snapshot Timeline                          │ |  |
|  |  │  T-3    T-2    T-1    T0 (current)                         │ |  |
|  |  │   │      │      │      │                                    │ |  |
|  |  │   ▼      ▼      ▼      ▼                                    │ |  |
|  |  │  S97    S98    S99    S0  (circular buffer wraps)          │ |  |
|  |  │                                                             │ |  |
|  |  │  Price Stability Tracking:                                  │ |  |
|  |  │  • Snapshot every N blocks (configurable delay)             │ |  |
|  |  │  • 100 snapshots in circular buffer                         │ |  |
|  |  │  • Used for protocol health monitoring                      │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  |                                                                  |  |
|  |  Stabilizer Mechanism:                                           |  |
|  |  • Enforces min/max price bounds for GREEN                      |  |
|  |  • Returns bounded price when stabilizer active                  |  |
|  |  • Protects protocol during extreme volatility                   |  |
|  +------------------------------------------------------------------+  |
+------------------------------------------------------------------------+
                                    |
                  ┌─────────────────┴─────────────────┐
                  ▼                                   ▼
+----------------------------------+  +----------------------------------+
|         Curve Pools              |  |         PriceDesk Oracle         |
+----------------------------------+  +----------------------------------+
| • StableSwap: USDC/USDT/DAI     |  | • Provides underlying prices     |
| • Crypto: ETH/BTC pools          |  | • Used for LP NAV calculation    |
| • Tricrypto: USDT/BTC/ETH        |  | • Chainlink integration          |
| • GREEN/USDC reference pool      |  +----------------------------------+
+----------------------------------+
```

## Constructor

### `__init__`

Initializes CurvePrices with governance settings and GREEN token configuration.

```vyper
@deploy
def __init__(
    _ripeHq: address,
    _tempGov: address,
    _minPriceChangeTimeLock: uint256,
    _maxPriceChangeTimeLock: uint256,
    _greenAddr: address,
):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_ripeHq` | `address` | RipeHq contract for protocol integration |
| `_tempGov` | `address` | Initial temporary governance address |
| `_minPriceChangeTimeLock` | `uint256` | Minimum timelock for config changes |
| `_maxPriceChangeTimeLock` | `uint256` | Maximum timelock for config changes |
| `_greenAddr` | `address` | GREEN token address for reference pool |

#### Example Usage
```python
curve_prices = boa.load(
    "contracts/priceSources/CurvePrices.vy",
    ripe_hq.address,
    deployer.address,
    100,   # Min 100 blocks timelock
    1000,  # Max 1000 blocks timelock
    green_token.address
)
```

## Core Price Functions

### `getPrice`

Returns the calculated price for a Curve asset (LP token or single asset).

```vyper
@view
@external
def getPrice(_asset: address, _staleTime: uint256 = 0, _priceDesk: address = empty(address)) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_asset` | `address` | Asset to get price for |
| `_staleTime` | `uint256` | Not used in current implementation |
| `_priceDesk` | `address` | Optional PriceDesk override |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Calculated price in 18 decimals |

#### Price Calculation Process

1. **Configuration Load**: Retrieves CurvePriceConfig for asset
2. **GREEN Handling**: Special logic for GREEN token with stabilizer
3. **Routing**: Determines if asset is LP token or single asset
4. **LP Calculation**: Virtual price × weighted underlying prices
5. **Single Asset**: Direct price oracle query from pool

#### Example Usage
```python
# Get LP token price
lp_price = curve_prices.getPrice(curve_3pool_lp.address)

# Get single asset price from pool
dai_price = curve_prices.getPrice(
    dai.address,
    0,
    custom_price_desk.address
)
```

### `getPriceAndHasFeed`

Returns price and whether a feed exists for the asset.

```vyper
@view
@external
def getPriceAndHasFeed(_asset: address, _staleTime: uint256 = 0, _priceDesk: address = empty(address)) -> (uint256, bool):
```

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Calculated price (0 if no feed) |
| `bool` | True if price feed exists |

## Price Feed Management

### `addNewPriceFeed`

Initiates addition of a new Curve price feed with time-locked approval.

```vyper
@external
def addNewPriceFeed(
    _asset: address,
    _pool: address,
    _lpToken: address,
    _numUnderlying: uint256,
    _underlying: address[4],
    _poolType: PoolType,
    _hasEcoToken: bool = False,
) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_asset` | `address` | Asset to price |
| `_pool` | `address` | Curve pool contract |
| `_lpToken` | `address` | LP token address (can be empty) |
| `_numUnderlying` | `uint256` | Number of underlying assets (0-4) |
| `_underlying` | `address[4]` | Underlying asset addresses |
| `_poolType` | `PoolType` | Pool implementation type |
| `_hasEcoToken` | `bool` | Whether pool contains ECO token |

#### Access

Only callable by governance

#### Validation
- Pool and asset addresses must be valid
- Underlying count must match provided addresses
- Asset must not already have a feed
- Pool type must be valid

#### Events Emitted

- `NewCurvePriceConfigPending` - Contains all configuration details

### `confirmNewPriceFeed`

Confirms a pending price feed addition after timelock.

```vyper
@external
def confirmNewPriceFeed(_asset: address) -> bool:
```

#### Process Flow
1. **Validation**: Re-validates configuration is still valid
2. **Timelock Check**: Ensures sufficient time has passed
3. **Configuration Save**: Stores price config
4. **Asset Registration**: Adds to PriceSourceData registry

#### Events Emitted

- `NewCurvePriceConfigAdded` - Confirms feed is active

### `updatePriceFeed`

Updates configuration for existing price feed.

```vyper
@external
def updatePriceFeed(
    _asset: address,
    _pool: address,
    _lpToken: address,
    _numUnderlying: uint256,
    _underlying: address[4],
    _poolType: PoolType,
    _hasEcoToken: bool = False,
) -> bool:
```

Updates require time-locked approval similar to additions.

### `disablePriceFeed`

Initiates removal of a price feed.

```vyper
@external
def disablePriceFeed(_asset: address) -> bool:
```

Removal also requires time-locked confirmation.

## GREEN Pool Management

### `setGreenReferencePool`

Configures the GREEN/USDC reference pool for protocol stability monitoring.

```vyper
@external
def setGreenReferencePool(
    _pool: address,
    _lpToken: address,
    _poolType: PoolType,
) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_pool` | `address` | GREEN/USDC pool address |
| `_lpToken` | `address` | Pool's LP token |
| `_poolType` | `PoolType` | Pool implementation type |

#### Special Behavior
- Requires time-locked confirmation
- Automatically detects GREEN and USDC positions
- Initializes snapshot system

### `addGreenPriceSnapshot`

Manually triggers a GREEN price snapshot.

```vyper
@external
def addGreenPriceSnapshot() -> bool:
```

#### Access

Only callable by Ripe protocol contracts

#### Snapshot Rules
- Minimum delay between snapshots enforced
- Circular buffer of 100 snapshots
- Each snapshot stores timestamp and price

### `configureStabilizer`

Configures the GREEN price stabilizer mechanism.

```vyper
@external
def configureStabilizer(
    _isActive: bool,
    _minPrice: uint256,
    _maxPrice: uint256,
) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_isActive` | `bool` | Enable/disable stabilizer |
| `_minPrice` | `uint256` | Minimum allowed GREEN price |
| `_maxPrice` | `uint256` | Maximum allowed GREEN price |

#### Stabilizer Effect
When active, GREEN price is bounded between min and max values regardless of pool price.

## Pool-Specific Pricing

### StableSwap NG Pricing

```vyper
def _getStableSwapNGPrice(...) -> uint256:
    if isLpToken:
        # LP token price = virtual_price × weighted_underlying
        virtualPrice = pool.get_virtual_price()
        weightedPrice = _calculateWeightedPrice(underlying)
        return virtualPrice * weightedPrice / 10**18
    else:
        # Single asset from price oracle
        return pool.price_oracle(assetIndex)
```

### TwoCrypto NG Pricing

```vyper
def _getTwoCryptoNGPrice(...) -> uint256:
    if isLpToken:
        # Similar to StableSwap but different interface
        virtualPrice = pool.virtual_price()
        # Calculate with 2 underlying assets
    else:
        # Single oracle price
        return pool.price_oracle()
```

### TriCrypto NG Pricing

Handles three-asset pools with similar logic but three underlying assets.

## Validation Functions

### `isValidNewFeed`

Validates new price feed configuration.

```vyper
@view
@external
def isValidNewFeed(
    _asset: address,
    _pool: address,
    _lpToken: address,
    _numUnderlying: uint256,
    _underlying: address[4],
    _poolType: PoolType,
    _hasEcoToken: bool,
) -> bool:
```

#### Validation Checks
1. **Address Validation**: Pool and asset must be valid
2. **No Existing Feed**: Asset must not have active feed
3. **Pool Type**: Must be valid non-NONE type
4. **Underlying Match**: Count must match addresses
5. **LP Token Logic**: If LP token, must have underlying

## Price Calculation Helpers

### Supply-Weighted Average

For LP tokens with multiple underlying assets:
```vyper
def _calculateWeightedPrice(underlying, priceDesk) -> uint256:
    totalValue = 0
    for asset in underlying:
        if asset != empty(address):
            price = PriceDesk(priceDesk).getPrice(asset)
            supply = pool.balances(i)  # Normalized
            totalValue += price * supply
    
    return totalValue / totalSupply
```

### Decimal Normalization

Handles varying decimal formats:
```vyper
def _normalizeDecimals(value, fromDecimals, toDecimals) -> uint256:
    if fromDecimals < toDecimals:
        return value * 10**(toDecimals - fromDecimals)
    elif fromDecimals > toDecimals:
        return value / 10**(fromDecimals - toDecimals)
    return value
```

## Events

### Configuration Events
- `NewCurvePriceConfigPending` - New feed initiated
- `NewCurvePriceConfigAdded` - Feed confirmed
- `CurvePriceConfigUpdatePending` - Update initiated
- `CurvePriceConfigUpdated` - Update confirmed
- `DisableCurvePriceConfigPending` - Removal initiated
- `CurvePriceConfigDisabled` - Feed removed

### GREEN Pool Events
- `GreenReferencePoolPending` - GREEN pool config initiated
- `GreenReferencePoolSet` - GREEN pool configured
- `GreenPriceSnapshot` - New snapshot recorded
- `StabilizerConfigured` - Stabilizer settings changed

All events include relevant addresses, configuration details, and timestamps.

## Security Considerations

### Access Control
- **Governance Only**: All configuration changes restricted
- **Ripe Contracts**: Snapshot additions allowed by protocol
- **Time-locked Changes**: Prevents rushed modifications

### Price Manipulation Protection
- **EMA Oracles**: Curve uses exponential moving averages
- **Virtual Price**: Resistant to single-trade manipulation
- **Stabilizer Bounds**: Limits GREEN price movement
- **Snapshot System**: Historical tracking for analysis

### Integration Safety
- **Graceful Failures**: Returns 0 for invalid queries
- **Pool Validation**: Ensures pools are properly configured
- **Decimal Handling**: Safe normalization logic
- **Reentrancy Protection**: View functions only

## Testing

For comprehensive test examples, see: [`tests/priceSources/test_curve_prices.py`](../../tests/priceSources/test_curve_prices.py)