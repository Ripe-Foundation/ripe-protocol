# CurvePrices Technical Documentation

[📄 View Source Code](../../contracts/priceSources/CurvePrices.vy)

## Overview

CurvePrices provides specialized pricing for Curve LP tokens and manages the Green token stabilizer mechanism. It handles complex multi-asset pools while maintaining accurate USD valuations for protocol operations.

**Dual Functionality**:
- **LP Token Pricing**: Calculates USD values using virtual price and underlying asset prices
- **Green Stabilizer**: Monitors GREEN/USDC pool ratios for external stabilization mechanisms
- **Multi-Pool Support**: Handles stable pools, crypto pools, and metapool configurations
- **Automated Discovery**: Leverages Curve's Meta Registry for automatic pool configuration

The module implements distinct pricing methods for stable vs crypto pools, EMA-based price oracles for manipulation resistance, snapshot system for historical tracking, and special handling for ecosystem tokens (GREEN, sGREEN, RIPE).

## Architecture & Dependencies

CurvePrices is built using a modular architecture with deep Curve protocol integration:

### Core Module Dependencies
- **LocalGov**: Provides governance functionality with access control
- **Addys**: Address resolution for protocol contracts
- **PriceSourceData**: Asset registration and pause state management
- **TimeLock**: Time-locked changes for configuration updates

### External Dependencies
- **Curve Address Provider**: Gateway to all Curve registry contracts
- **Curve Meta Registry**: Pool configuration and asset discovery
- **PriceDesk**: Retrieves underlying asset prices for LP calculations
- **Curve Pools**: Direct integration with various pool implementations

### Module Initialization
```vyper
initializes: gov
initializes: addys
initializes: priceData[addys := addys]
initializes: timeLock[gov := gov]
```

### Immutable Configuration
```vyper
GREEN: immutable(address)          # GREEN token address
SAVINGS_GREEN: immutable(address)  # sGREEN token address
```

## Data Structures

### PoolType Flag
Identifies different Curve pool implementations:
```vyper
flag PoolType:
    STABLESWAP_NG    # Next-gen stable pools
    TWO_CRYPTO_NG    # Two-asset crypto pools
    TRICRYPTO_NG     # Three-asset crypto pools
    TWO_CRYPTO       # Legacy two-asset pools
    METAPOOL         # Stable metapools
    CRYPTO           # General crypto pools
```

### CurvePriceConfig Struct
Complete configuration for a Curve asset:
```vyper
struct CurvePriceConfig:
    pool: address                   # Curve pool contract
    lpToken: address               # LP token address
    numUnderlying: uint256         # Number of assets (1-4)
    underlying: address[4]         # Underlying assets
    poolType: PoolType            # Pool implementation type(s)
    hasEcoToken: bool             # Contains GREEN/sGREEN/RIPE
```

### PendingCurvePriceConfig Struct
Tracks configuration changes during timelock:
```vyper
struct PendingCurvePriceConfig:
    actionId: uint256              # TimeLock action ID
    config: CurvePriceConfig       # New configuration
```

### GreenRefPoolConfig Struct
Configuration for GREEN reference pool monitoring:
```vyper
struct GreenRefPoolConfig:
    pool: address                  # Pool contract address
    lpToken: address              # LP token address
    greenIndex: uint256           # GREEN position (0 or 1)
    altAsset: address             # Other asset in pool
    altAssetDecimals: uint256     # Alt asset decimal places
    maxNumSnapshots: uint256      # Maximum snapshots to store
    dangerTrigger: uint256        # Danger threshold (50-9999 bp)
    staleBlocks: uint256          # Blocks before snapshot stale
    stabilizerAdjustWeight: uint256    # Weight for adjustments
    stabilizerMaxPoolDebt: uint256     # Max debt allowed
```

### RefPoolSnapshot Struct
Snapshot of GREEN pool state:
```vyper
struct RefPoolSnapshot:
    greenBalance: uint256         # GREEN balance in pool
    ratio: uint256               # GREEN % of pool (basis points)
    update: uint256              # Block number of snapshot
    inDanger: bool               # Ratio exceeds danger trigger
```

### CurrentGreenPoolStatus Struct
Data structure returned by getCurrentGreenPoolStatus:
```vyper
struct CurrentGreenPoolStatus:
    weightedRatio: uint256           # Weighted average ratio
    dangerTrigger: uint256           # Danger threshold
    numBlocksInDanger: uint256       # Consecutive danger blocks
```

### StabilizerConfig Struct
Data structure returned by getGreenStabilizerConfig:
```vyper
struct StabilizerConfig:
    pool: address                    # Pool contract address
    lpToken: address                 # LP token address
    greenBalance: uint256            # GREEN balance in pool
    greenRatio: uint256              # GREEN ratio in pool
    greenIndex: uint256              # GREEN position (0 or 1)
    stabilizerAdjustWeight: uint256  # Weight for adjustments
    stabilizerMaxPoolDebt: uint256   # Maximum allowed debt
```

## State Variables

### Configuration Storage
- `priceConfigs: HashMap[address, CurvePriceConfig]` - Active configurations
- `pendingPriceConfigs: HashMap[address, PendingCurvePriceConfig]` - Pending changes
- `curveAddressProvider: ICurveAddressProvider` - Curve registry access

### GREEN Pool Monitoring
- `greenRefPoolConfig: GreenRefPoolConfig` - GREEN pool configuration
- `pendingGreenRefPoolConfig: GreenRefPoolConfig` - Pending config
- `pendingGreenRefPoolActionId: uint256` - Timelock action ID
- `refPoolSnapshots: RefPoolSnapshot[256]` - Circular snapshot buffer
- `nextSnapshotIndex: uint256` - Next snapshot position
- `blocksConsecInDanger: uint256` - Consecutive danger blocks

### Constants
- `NORMALIZED_DECIMALS: constant(uint256) = 18` - Standard decimals
- `HUNDRED_PERCENT: constant(uint256) = 100_00` - 100.00% basis points
- `STALE_ORACLE_THRESHOLD: constant(uint256) = 86400 * 7` - 7 days

## System Architecture Diagram

```
+------------------------------------------------------------------------+
|                        CurvePrices Contract                           |
+------------------------------------------------------------------------+
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |              Automated Pool Discovery Flow                       |  |
|  |                                                                  |  |
|  |  addNewPriceFeed(pool_address):                                  |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ 1. Query Curve Meta Registry with pool address              │ |  |
|  |  │ 2. Automatically discover:                                  │ |  |
|  |  │    - LP token address                                       │ |  |
|  |  │    - Number of underlying assets                            │ |  |
|  |  │    - All underlying asset addresses                         │ |  |
|  |  │    - Pool type from registry                                │ |  |
|  |  │ 3. Detect ecosystem tokens (GREEN/sGREEN/RIPE)              │ |  |
|  |  │ 4. Create pending configuration with timelock               │ |  |
|  |  │ 5. No manual configuration needed!                          │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Price Calculation Methods                     |  |
|  |                                                                  |  |
|  |  Stable Pool LP Tokens (_getStableLpPrice):                     |  |
|  |  • Get virtual_price from pool                                  |  |
|  |  • Find lowest price among all underlying assets                |  |
|  |  • Price = virtual_price × lowest_underlying_price              |  |
|  |  • Protects against depeg scenarios                             |  |
|  |                                                                  |  |
|  |  Crypto Pool LP Tokens (_getCryptoLpPrice):                     |  |
|  |  • Get lp_price from pool                                       |  |
|  |  • Get price of first underlying asset                          |  |
|  |  • Price = lp_price × first_asset_price                         |  |
|  |  • Optimized for volatile pairs                                 |  |
|  |                                                                  |  |
|  |  Single Assets (_getAssetPriceFromCurve):                       |  |
|  |  • Use pool's internal price oracle                             |  |
|  |  • Calculate relative to other asset in pool                    |  |
|  |  • Different methods for different pool types                   |  |
|  |                                                                  |  |
|  |  Savings GREEN (sGREEN):                                        |  |
|  |  • Get GREEN price first                                        |  |
|  |  • Query sGREEN.convertToAssets(1e18)                           |  |
|  |  • Price = GREEN_price × price_per_share                        |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |              GREEN Reference Pool Monitoring                     |  |
|  |                                                                  |  |
|  |  Snapshot System:                                                |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │         Circular Buffer (256 snapshots)                     │ |  |
|  |  │  [0] [1] [2] ... [254] [255] → [0] (wraps)                 │ |  |
|  |  │   ↑                       ↑                                  │ |  |
|  |  │  old                    newest                               │ |  |
|  |  │                                                             │ |  |
|  |  │  Each Snapshot Contains:                                    │ |  |
|  |  │  • greenBalance: Amount of GREEN in pool                    │ |  |
|  |  │  • ratio: GREEN as % of pool (basis points)                 │ |  |
|  |  │  • update: Block number                                     │ |  |
|  |  │  • inDanger: ratio > dangerTrigger                          │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  |                                                                  |  |
|  |  Weighted Ratio Calculation:                                     |  |
|  |  • Filters out stale snapshots (> staleBlocks old)              |  |
|  |  • Weights each snapshot by GREEN balance                        |  |
|  |  • Provides time-weighted average ratio                          |  |
|  |                                                                  |  |
|  |  Danger Monitoring:                                              |  |
|  |  • Tracks consecutive blocks where ratio > trigger               |  |
|  |  • Provides data to Endaoment for stabilization                  |  |
|  |  • Does NOT enforce price bounds directly                        |  |
|  +------------------------------------------------------------------+  |
+------------------------------------------------------------------------+
                                    |
        ┌───────────────────────────┴───────────────────────────┐
        ▼                           ▼                           ▼
+-------------------+   +----------------------+   +------------------+
| Curve Registries  |   | Curve Pools         |   | External Oracle  |
+-------------------+   +----------------------+   +------------------+
| • Address Provider|   | • get_virtual_price()|   | • PriceDesk      |
| • Meta Registry   |   | • lp_price()        |   | • Asset prices   |
| • Pool info       |   | • price_oracle()    |   | • Used for LP    |
+-------------------+   +----------------------+   +------------------+
```

## Constructor

### `__init__`

Initializes CurvePrices with Curve integration and GREEN token configuration.

```vyper
@deploy
def __init__(
    _ripeHq: address,
    _tempGov: address,
    _curveAddressProvider: address,
    _green: address,
    _savingsGreen: address,
    _minPriceChangeTimeLock: uint256,
    _maxPriceChangeTimeLock: uint256,
):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_ripeHq` | `address` | RipeHq contract for protocol integration |
| `_tempGov` | `address` | Initial temporary governance address |
| `_curveAddressProvider` | `address` | Curve's address provider for registry access |
| `_green` | `address` | GREEN token address (immutable) |
| `_savingsGreen` | `address` | sGREEN token address (immutable) |
| `_minPriceChangeTimeLock` | `uint256` | Minimum timelock for config changes |
| `_maxPriceChangeTimeLock` | `uint256` | Maximum timelock for config changes |

#### Example Usage
```python
curve_prices = boa.load(
    "contracts/priceSources/CurvePrices.vy",
    ripe_hq.address,
    deployer.address,
    curve_address_provider.address,
    green_token.address,
    savings_green.address,
    100,   # Min 100 blocks timelock
    1000,  # Max 1000 blocks timelock
)
```

## Core Price Functions

### `getPrice`

Returns the calculated price for a Curve asset (LP token, single asset, or sGREEN).

```vyper
@view
@external
def getPrice(_asset: address, _staleTime: uint256 = 0, _priceDesk: address = empty(address)) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_asset` | `address` | Asset to get price for |
| `_staleTime` | `uint256` | Not used in Curve implementation |
| `_priceDesk` | `address` | Optional PriceDesk override |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Calculated price in 18 decimals |

#### Price Calculation Process

1. **sGREEN Check**: Special handling for savings GREEN
2. **Configuration Load**: Retrieves CurvePriceConfig for asset
3. **Routing**: Determines pricing method based on asset type
4. **Calculation**: Uses appropriate method (_getStableLpPrice, _getCryptoLpPrice, or _getAssetPriceFromCurve)
5. **Normalization**: Ensures 18 decimal output

#### Example Usage
```python
# Get LP token price
lp_price = curve_prices.getPrice(curve_3pool_lp.address)

# Get single asset price from pool
dai_price = curve_prices.getPrice(dai.address)

# Get sGREEN price
sgreen_price = curve_prices.getPrice(savings_green.address)
```

## Price Feed Management

### `addNewPriceFeed`

Initiates addition of a new Curve price feed with automatic discovery.

```vyper
@external
def addNewPriceFeed(_asset: address, _pool: address) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_asset` | `address` | Asset address (LP token or single asset) |
| `_pool` | `address` | Curve pool contract address |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if successfully initiated |

#### Access

Only callable by governance

#### Process Flow

1. **Registry Query**: Fetches pool configuration from Meta Registry
2. **Auto Discovery**: Finds LP token and underlying assets
3. **Validation**: Ensures pool is valid and not already configured
4. **Eco Token Detection**: Checks for GREEN/sGREEN/RIPE
5. **Pending Creation**: Creates time-locked configuration

#### Events Emitted

- `NewCurvePricePending` - Contains discovered configuration

#### Example Usage
```python
# Add new price feed for LP token
success = curve_prices.addNewPriceFeed(
    curve_3pool_lp.address,  # LP token
    curve_3pool.address,     # Pool
    sender=governance
)

# Add new price feed for single asset
success = curve_prices.addNewPriceFeed(
    dai.address,             # Single asset
    curve_3pool.address,     # Pool containing the asset
    sender=governance
)
```

### `confirmNewPriceFeed`

Confirms a pending price feed addition after timelock.

```vyper
@external
def confirmNewPriceFeed(_asset: address) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_asset` | `address` | Asset to confirm feed for |

#### Access

Only callable by governance

#### Process Flow
1. **Timelock Check**: Ensures sufficient time has passed
2. **Configuration Save**: Stores price config
3. **Asset Registration**: Adds both LP and assets to registry
4. **Initial Price Check**: Validates pricing works

#### Events Emitted

- `NewCurvePriceAdded` - Confirms feed is active

### `updatePriceFeed`

Updates configuration for existing price feed.

```vyper
@external
def updatePriceFeed(_asset: address, _pool: address) -> bool:
```

Similar to addNewPriceFeed but for existing feeds. Validates that new pool differs from current.

#### Access

Only callable by governance

#### Events Emitted

- `UpdateCurvePricePending` - Update initiated with new configuration

### `disablePriceFeed`

Initiates removal of a price feed.

```vyper
@external
def disablePriceFeed(_asset: address) -> bool:
```

Removal requires time-locked confirmation via `confirmDisablePriceFeed`.

#### Access

Only callable by governance

#### Events Emitted

- `DisableCurvePricePending` - Removal initiated

### `confirmUpdatePriceFeed`

Confirms a pending price feed update after timelock.

```vyper
@external
def confirmUpdatePriceFeed(_asset: address) -> bool:
```

#### Access

Only callable by governance

#### Events Emitted

- `CurvePriceUpdated` - Update confirmed

### `confirmDisablePriceFeed`

Confirms a pending price feed removal after timelock.

```vyper
@external
def confirmDisablePriceFeed(_asset: address) -> bool:
```

#### Access

Only callable by governance

#### Events Emitted

- `CurvePriceDisabled` - Feed removed

## GREEN Pool Management

### `setGreenRefPoolConfig`

Configures the GREEN reference pool for monitoring.

```vyper
@external
def setGreenRefPoolConfig(
    _pool: address,
    _maxNumSnapshots: uint256,
    _dangerTrigger: uint256,
    _staleBlocks: uint256,
    _stabilizerAdjustWeight: uint256,
    _stabilizerMaxPoolDebt: uint256
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_pool` | `address` | GREEN pool address |
| `_maxNumSnapshots` | `uint256` | Max snapshots to consider (1-256) |
| `_dangerTrigger` | `uint256` | Danger threshold in basis points (5000-9999) |
| `_staleBlocks` | `uint256` | Blocks before snapshot stale |
| `_stabilizerAdjustWeight` | `uint256` | Weight for stabilizer |
| `_stabilizerMaxPoolDebt` | `uint256` | Maximum allowed debt |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | TimeLock action ID for confirmation |

#### Access

Only callable by governance

#### Special Behavior
- Automatically discovers GREEN position in pool
- Automatically determines alt asset and its decimals from pool
- Validates pool contains exactly GREEN and one other asset
- Requires time-locked confirmation via `confirmSetGreenRefPoolConfig`

#### Events Emitted

- `GreenRefPoolPending` - GREEN pool configuration initiated

### `confirmSetGreenRefPoolConfig`

Confirms pending GREEN reference pool configuration after timelock.

```vyper
@external
def confirmSetGreenRefPoolConfig() -> bool:
```

#### Access

Only callable by governance

#### Events Emitted

- `GreenRefPoolSet` - GREEN pool configured

### `addGreenRefPoolSnapshot`

Creates a new snapshot of GREEN pool state.

```vyper
@external
def addGreenRefPoolSnapshot():
```

#### Access

Only callable by Ripe protocol contracts

#### Snapshot Process
1. Queries current pool balances
2. Calculates GREEN ratio as basis points
3. Determines if ratio exceeds danger trigger
4. Updates consecutive danger block counter
5. Stores in circular buffer

#### Events Emitted

- `GreenRefPoolSnapshot` - New snapshot created with GREEN balance, ratio, and danger status

### `getCurrentGreenPoolStatus`

Returns current GREEN pool monitoring data.

```vyper
@view
@external
def getCurrentGreenPoolStatus() -> CurrentGreenPoolStatus:
```

#### Returns

| Type | Description |
|------|-------------|
| `CurrentGreenPoolStatus` | Struct containing weighted ratio, danger trigger, and blocks in danger |

### `getGreenStabilizerConfig`

Provides configuration data for stabilizer contracts.

```vyper
@view
@external
def getGreenStabilizerConfig() -> StabilizerConfig:
```

Returns complete stabilizer configuration including pool details, GREEN balance/ratio, and stabilizer parameters.

## Internal Pricing Methods

### `_getStableLpPrice`

Calculates price for stable pool LP tokens.

```vyper
@internal
@view
def _getStableLpPrice(
    _pool: address,
    _lp: address,
    _numUnderlying: uint256,
    _underlying: address[4],
    _priceDesk: address
) -> uint256:
```

#### Algorithm
1. Get virtual price from pool
2. Find lowest price among all underlying assets
3. Return: `virtual_price × lowest_price / 10^18`

### `_getCryptoLpPrice`

Calculates price for crypto pool LP tokens.

```vyper
@internal
@view
def _getCryptoLpPrice(
    _pool: address,
    _lp: address,
    _underlying0: address,
    _priceDesk: address
) -> uint256:
```

#### Algorithm
1. Get lp_price from pool
2. Get price of first underlying asset
3. Return: `lp_price × asset_price / 10^18`

### `_getAssetPriceFromCurve`

Gets single asset price from pool's oracle.

```vyper
@internal
@view
def _getAssetPriceFromCurve(
    _pool: address,
    _asset: address,
    _altAsset: address,
    _poolType: PoolType,
    _priceDesk: address
) -> uint256:
```

Uses pool-specific oracle methods to calculate relative prices.

## Security Considerations

### Access Control
- **Governance Only**: All configuration changes restricted
- **Ripe Contracts**: Snapshot additions allowed by protocol
- **Time-locked Changes**: Prevents rushed modifications

### Price Manipulation Protection
- **Pool Validation**: Ensures pools are properly configured
- **Oracle Security**: Uses Curve's manipulation-resistant oracles
- **Lowest Price Method**: Protects against depeg in stable pools
- **Decimal Handling**: Safe normalization logic

### Integration Safety
- **Graceful Failures**: Returns 0 for invalid queries
- **Automatic Discovery**: Reduces configuration errors
- **Registry Validation**: Cross-checks with Curve registries
- **Reentrancy Protection**: View functions only

## Testing

For comprehensive test examples, see: [`tests/priceSources/test_curve_prices.py`](../../tests/priceSources/test_curve_prices.py)