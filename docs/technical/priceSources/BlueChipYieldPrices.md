# BlueChipYieldPrices Technical Documentation

[📄 View Source Code](../../contracts/priceSources/BlueChipYieldPrices.vy)

## Overview

BlueChipYieldPrices provides accurate USD pricing for yield-bearing vault tokens across major DeFi protocols. It calculates prices by combining the underlying asset's USD value with the vault's exchange rate, ensuring precise valuations for protocol operations.

**Key Features**:
- **Multi-Protocol Support**: Integrates with Morpho, Euler, Moonwell, Sky, Fluid, Aave V3, and Compound V3
- **Snapshot System**: Time-series price tracking with supply-weighted averaging for manipulation resistance
- **Safety Throttling**: Configurable upside deviation limits prevent sudden price spikes
- **Time-Locked Updates**: All feed modifications require governance approval with enforced delays

The module implements protocol-specific adapters for each integration, maintains up to 25 historical price points per asset, and uses weighted averages based on total supply for reliable pricing data in collateral evaluation and risk management.

## Architecture & Dependencies

BlueChipYieldPrices is built using a modular architecture with multiple protocol integrations:

### Core Module Dependencies
- **LocalGov**: Provides governance functionality with access control
- **Addys**: Address resolution for protocol contracts (PriceDesk)
- **PriceSourceData**: Asset registration and pause state management
- **TimeLock**: Time-locked changes for configuration updates

### Protocol Integrations
- **Morpho**: MetaMorpho vault detection via registry contracts
- **Euler**: EVC vault validation through proxy checks
- **Fluid**: fToken registry for lending markets
- **Compound V3**: Base token pricing for cTokens
- **Moonwell**: Exchange rate based pricing
- **Aave V3**: Direct underlying asset pricing

### Module Initialization
```vyper
initializes: gov
initializes: addys
initializes: priceData[addys := addys]
initializes: timeLock[gov := gov]
```

### External Dependencies
```vyper
# Protocol registries stored as immutables
MORPHO_ADDRS: immutable(address[2])
EULER_ADDRS: immutable(address[2])
FLUID_ADDR: immutable(address)
COMPOUND_V3_ADDR: immutable(address)
MOONWELL_ADDR: immutable(address)
AAVE_V3_ADDR: immutable(address)
```

## Data Structures

### Protocol Enum
Identifies which DeFi protocol a vault token belongs to:
```vyper
flag Protocol:
    MORPHO
    EULER
    MOONWELL
    SKY
    FLUID
    AAVE_V3
    COMPOUND_V3
```

### PriceConfig Struct
Complete configuration for a vault token price feed:
```vyper
struct PriceConfig:
    protocol: Protocol              # Which DeFi protocol
    underlyingAsset: address        # Asset the vault holds
    underlyingDecimals: uint256     # Decimals of underlying
    vaultTokenDecimals: uint256     # Decimals of vault token
    minSnapshotDelay: uint256       # Min blocks between snapshots
    maxNumSnapshots: uint256        # Max snapshots to store
    maxUpsideDeviation: uint256     # Max allowed price increase %
    staleTime: uint256              # When snapshots become stale
    lastSnapshot: PriceSnapshot     # Most recent snapshot
    nextIndex: uint256              # Next snapshot storage index
```

### PriceSnapshot Struct
Point-in-time record of vault token metrics:
```vyper
struct PriceSnapshot:
    totalSupply: uint256            # Vault token supply
    pricePerShare: uint256          # Price per vault share
    lastUpdate: uint256             # Timestamp of snapshot
```

### PendingPriceConfig Struct
Tracks configuration changes during timelock:
```vyper
struct PendingPriceConfig:
    actionId: uint256               # TimeLock action ID
    config: PriceConfig             # New configuration
```

## State Variables

### Configuration Storage
- `priceConfigs: HashMap[address, PriceConfig]` - Active price feed configurations
- `snapShots: HashMap[address, HashMap[uint256, PriceSnapshot]]` - Historical snapshots
- `pendingPriceConfigs: HashMap[address, PendingPriceConfig]` - Pending changes

### Constants
- `HUNDRED_PERCENT: constant(uint256) = 100_00` - 100.00% for calculations
- `MAX_MARKETS: constant(uint256) = 50` - Maximum markets per protocol

### Inherited State
From modules:
- Governance state (LocalGov)
- Pause state and asset registry (PriceSourceData)
- TimeLock configuration and action tracking

## System Architecture Diagram

```
+------------------------------------------------------------------------+
|                    BlueChipYieldPrices Contract                       |
+------------------------------------------------------------------------+
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Price Calculation Flow                        |  |
|  |                                                                  |  |
|  |  getPrice(vaultToken):                                           |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ 1. Load PriceConfig for vault token                        │ |  |
|  |  │ 2. Get underlying asset price from PriceDesk               │ |  |
|  |  │ 3. For Aave/Compound: Return underlying price directly     │ |  |
|  |  │ 4. For others: Calculate weighted price per share          │ |  |
|  |  │ 5. Get current price per share from protocol               │ |  |
|  |  │ 6. Use minimum of weighted and current (allow downside)    │ |  |
|  |  │ 7. Calculate: underlying_price * price_per_share           │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Snapshot Management System                    |  |
|  |                                                                  |  |
|  |  Price Snapshot Timeline:                                        |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ T0    T1    T2    T3    T4    T5 (current)                 │ |  |
|  |  │ │     │     │     │     │     │                            │ |  |
|  |  │ ▼     ▼     ▼     ▼     ▼     ▼                            │ |  |
|  |  │ S0────S1────S2────S3────S4────?                            │ |  |
|  |  │       └─────┴─────┴─────┴─────┘                            │ |  |
|  |  │         Weighted Average Price                              │ |  |
|  |  │                                                             │ |  |
|  |  │ Weight = totalSupply at each snapshot                      │ |  |
|  |  │ Price = Σ(supply_i * price_i) / Σ(supply_i)               │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  |                                                                  |  |
|  |  Snapshot Storage (Circular Buffer):                             |  |
|  |  • Up to maxNumSnapshots stored (max 25)                        |  |
|  |  • Minimum minSnapshotDelay between snapshots                   |  |
|  |  • Automatic overwrite of oldest when full                      |  |
|  |  • Stale snapshots excluded from calculations                   |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Protocol Adapters                            |  |
|  |                                                                  |  |
|  |  ERC4626 Vaults (Morpho, Euler, Fluid):                         |  |
|  |  • convertToAssets(shares) → underlying amount                  |  |
|  |  • Standard interface for share/asset conversion                |  |
|  |                                                                  |  |
|  |  Moonwell (Compound Fork):                                      |  |
|  |  • exchangeRateStored() → rate with 18 decimals                |  |
|  |  • Custom calculation for price per share                       |  |
|  |                                                                  |  |
|  |  Aave V3 / Compound V3:                                         |  |
|  |  • Direct 1:1 pricing with underlying                           |  |
|  |  • No yield accumulation in price                              |  |
|  +------------------------------------------------------------------+  |
+------------------------------------------------------------------------+
                                    |
                  ┌─────────────────┴─────────────────┐
                  ▼                                   ▼
+----------------------------------+  +----------------------------------+
|        Protocol Registries       |  |         PriceDesk Oracle         |
+----------------------------------+  +----------------------------------+
| • Morpho: MetaMorpho vaults      |  | • Provides underlying prices     |
| • Euler: EVC proxy validation    |  | • GREEN, USDC, ETH, etc.         |
| • Fluid: fToken registry         |  | • Used for final calculation     |
| • Moonwell: Market registry      |  +----------------------------------+
| • Aave: aToken registry          |
| • Compound: cToken factory       |
+----------------------------------+
```

## Constructor

### `__init__`

Initializes BlueChipYieldPrices with governance settings and protocol registry addresses.

```vyper
@deploy
def __init__(
    _ripeHq: address,
    _tempGov: address,
    _minPriceChangeTimeLock: uint256,
    _maxPriceChangeTimeLock: uint256,
    _morphoAddrs: address[2],
    _eulerAddrs: address[2],
    _fluidAddr: address,
    _compoundV3Addr: address,
    _moonwellAddr: address,
    _aaveV3Addr: address,
):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_ripeHq` | `address` | RipeHq contract for protocol integration |
| `_tempGov` | `address` | Initial temporary governance address |
| `_minPriceChangeTimeLock` | `uint256` | Minimum timelock for price config changes |
| `_maxPriceChangeTimeLock` | `uint256` | Maximum timelock for price config changes |
| `_morphoAddrs` | `address[2]` | Morpho registry addresses |
| `_eulerAddrs` | `address[2]` | Euler registry addresses |
| `_fluidAddr` | `address` | Fluid registry address |
| `_compoundV3Addr` | `address` | Compound V3 registry address |
| `_moonwellAddr` | `address` | Moonwell registry address |
| `_aaveV3Addr` | `address` | Aave V3 registry address |

#### Example Usage
```python
blue_chip_prices = boa.load(
    "contracts/priceSources/BlueChipYieldPrices.vy",
    ripe_hq.address,
    deployer.address,  # Temp governance
    100,   # Min 100 blocks for changes
    1000,  # Max 1000 blocks for changes
    [morpho_reg1, morpho_reg2],
    [euler_reg1, euler_reg2],
    fluid_registry,
    compound_v3_registry,
    moonwell_registry,
    aave_v3_registry
)
```

## Core Price Functions

### `getPrice`

Returns the calculated price for a vault token.

```vyper
@view
@external
def getPrice(_asset: address, _staleTime: uint256 = 0, _priceDesk: address = empty(address)) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_asset` | `address` | Vault token to get price for |
| `_staleTime` | `uint256` | Not used (each config has own stale time) |
| `_priceDesk` | `address` | Optional PriceDesk override |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Calculated vault token price |

#### Price Calculation Process

1. **Underlying Price**: Fetches current price of underlying asset from PriceDesk
2. **Direct Pricing**: Aave V3 and Compound V3 return underlying price directly
3. **Weighted Average**: For other protocols, calculates supply-weighted average price per share
4. **Current Price**: Gets latest price per share from protocol
5. **Downside Allowance**: Uses minimum of weighted and current to allow losses
6. **Final Calculation**: `price = underlying_price * price_per_share / decimals`

#### Example Usage
```python
# Get price for Morpho USDC vault
vault_price = blue_chip_prices.getPrice(morpho_usdc_vault.address)

# With custom PriceDesk
vault_price = blue_chip_prices.getPrice(
    morpho_usdc_vault.address,
    0,  # Stale time not used
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

Initiates addition of a new vault token price feed with time-locked approval.

```vyper
@external
def addNewPriceFeed(
    _asset: address,
    _protocol: Protocol,
    _minSnapshotDelay: uint256 = 60 * 5,  # 5 minutes
    _maxNumSnapshots: uint256 = 20,
    _maxUpsideDeviation: uint256 = 10_00,  # 10%
    _staleTime: uint256 = 0,
) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_asset` | `address` | Vault token address |
| `_protocol` | `Protocol` | Which DeFi protocol |
| `_minSnapshotDelay` | `uint256` | Min blocks between snapshots |
| `_maxNumSnapshots` | `uint256` | Max snapshots to store (≤25) |
| `_maxUpsideDeviation` | `uint256` | Max price increase per snapshot |
| `_staleTime` | `uint256` | When snapshots become stale |

#### Access

Only callable by governance

#### Validation
- Asset must be valid for specified protocol
- Underlying asset must have price in PriceDesk
- Parameters must be within acceptable ranges
- Asset must not already have a feed

#### Events Emitted

- `NewPriceConfigPending` - Contains all configuration details and confirmation block

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
5. **Initial Snapshot**: Creates first price snapshot

#### Events Emitted

- `NewPriceConfigAdded` - Confirms feed is active

### `updatePriceConfig`

Updates configuration for existing price feed.

```vyper
@external
def updatePriceConfig(
    _asset: address,
    _minSnapshotDelay: uint256 = 60 * 5,
    _maxNumSnapshots: uint256 = 20,
    _maxUpsideDeviation: uint256 = 10_00,
    _staleTime: uint256 = 0,
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

## Snapshot Management

### `addPriceSnapshot`

Manually triggers a new price snapshot for a vault token.

```vyper
@external 
def addPriceSnapshot(_asset: address) -> bool:
```

#### Access

Only callable by valid Ripe protocol addresses

#### Snapshot Restrictions
- Minimum delay between snapshots must be met
- No duplicate snapshots for same timestamp
- Aave/Compound don't use snapshots

#### Snapshot Storage
- Circular buffer with `maxNumSnapshots` slots
- Oldest snapshot overwritten when full
- Each snapshot stores: totalSupply, pricePerShare, timestamp

### `getWeightedPrice`

Returns the supply-weighted average price per share.

```vyper
@view
@external
def getWeightedPrice(_asset: address) -> uint256:
```

#### Calculation Formula
```
weightedPrice = Σ(supply_i * pricePerShare_i) / Σ(supply_i)
```

Where:
- Only non-stale snapshots are included
- More supply = more weight in average
- Falls back to last snapshot if no valid data

## Protocol-Specific Functions

### ERC4626 Vaults (Morpho, Euler, Fluid)

#### Price Calculation
```vyper
def _getErc4626Price(...) -> uint256:
    # Get weighted average from snapshots
    pricePerShare = _getWeightedPrice(asset, config)
    
    # Allow downside - use current if lower
    currentPrice = IERC4626(asset).convertToAssets(10**decimals)
    pricePerShare = min(pricePerShare, currentPrice)
    
    # Calculate final price
    return underlyingPrice * pricePerShare / 10**underlyingDecimals
```

### Moonwell

#### Price Calculation
```vyper
def _getMoonwellPrice(...) -> uint256:
    # Similar to ERC4626 but uses exchangeRateStored()
    # Rate is in 18 decimals, needs conversion
    currentPrice = 10**decimals * exchangeRate / 10**18
```

### Aave V3 & Compound V3

These protocols use direct 1:1 pricing with underlying asset - no yield accumulation in oracle price.

## Validation Functions

### `isValidNewFeed`

Checks if a new price feed configuration is valid.

```vyper
@view
@external
def isValidNewFeed(
    _asset: address,
    _protocol: Protocol,
    _minSnapshotDelay: uint256,
    _maxNumSnapshots: uint256,
    _maxUpsideDeviation: uint256,
    _staleTime: uint256,
) -> bool:
```

#### Validation Checks
1. **Protocol Match**: Asset must be valid for specified protocol
2. **Registry Validation**: Must be registered in protocol's registry
3. **Underlying Asset**: Must be retrievable and have PriceDesk price
4. **Parameter Ranges**:
   - minSnapshotDelay ≤ 1 week
   - 0 < maxNumSnapshots ≤ 25
   - maxUpsideDeviation ≤ 100%
   - Decimals must be valid

## Safety Mechanisms

### Upside Throttling

Prevents sudden price spikes:
```vyper
def _throttleUpside(newValue, prevValue, maxUpside) -> uint256:
    if maxUpside == 0 or prevValue == 0:
        return newValue
    
    maxAllowed = prevValue + (prevValue * maxUpside / 100_00)
    return min(newValue, maxAllowed)
```

### Stale Data Handling

Snapshots older than `staleTime` are excluded from calculations:
- Each snapshot has timestamp
- Weighted average only includes fresh data
- Falls back to last snapshot if all stale

### Pause Functionality

Inherited from PriceSourceData:
- Contract can be paused by governance
- All price queries fail when paused
- Allows emergency response to issues

## Events

### Configuration Events

- `NewPriceConfigPending` - New feed initiated
- `NewPriceConfigAdded` - New feed confirmed
- `PriceConfigUpdatePending` - Update initiated
- `PriceConfigUpdated` - Update confirmed
- `DisablePriceConfigPending` - Removal initiated
- `DisablePriceConfigConfirmed` - Feed removed

### Operational Events

- `PricePerShareSnapshotAdded` - New snapshot created

All configuration events include full details: asset, protocol, underlying, parameters, and timelock information.

## Security Considerations

### Access Control
- **Governance Only**: All configuration changes restricted to governance
- **Ripe Addresses**: Snapshot additions allowed by protocol contracts
- **Time-locked Changes**: All modifications require waiting period

### Price Manipulation Protection
- **Weighted Averaging**: Reduces impact of single manipulated snapshot
- **Supply Weighting**: Higher liquidity periods have more influence
- **Upside Throttling**: Limits maximum price increase per snapshot
- **Downside Allowance**: Allows losses to be reflected immediately

### Protocol Integration Safety
- **Registry Validation**: Only accepts registered protocol vaults
- **Underlying Verification**: Ensures underlying asset is valid
- **Decimal Handling**: Proper conversion between different decimal scales

## Testing

For comprehensive test examples, see: [`tests/priceSources/test_blue_chip_yield_prices.py`](../../tests/priceSources/test_blue_chip_yield_prices.py)