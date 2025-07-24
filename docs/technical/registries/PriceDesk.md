# PriceDesk Technical Documentation

[📄 View Source Code](../../contracts/registries/PriceDesk.vy)

## Overview

PriceDesk is the centralized oracle registry that aggregates multiple price sources to provide reliable USD valuations across Ripe Protocol. It intelligently routes price requests through prioritized oracles, ensuring accurate pricing even when individual sources fail.

**Core Functions**:
- **Oracle Registry**: Manages approved price sources with unique IDs and descriptions
- **Smart Aggregation**: Checks priority sources first, then falls back to all registered oracles
- **Value Conversions**: Automatic USD/asset conversions with decimal normalization

Built on LocalGov and AddressRegistry modules, PriceDesk implements resilient price discovery through priority-based oracle selection. It handles diverse token decimals automatically and provides specialized ETH conversion utilities, ensuring protocol-wide access to accurate pricing data. It integrates with price sources like [ChainlinkPrices](../priceSources/ChainlinkPrices.md), [CurvePrices](../priceSources/CurvePrices.md), and [PythPrices](../priceSources/PythPrices.md), with configuration managed through [MissionControl](../data/MissionControl.md).

## Architecture & Modules

PriceDesk is built using a modular architecture that inherits functionality from multiple base modules:

### LocalGov Module

- **Location**: `contracts/modules/LocalGov.vy`
- **Purpose**: Provides governance functionality with time-locked changes
- **Documentation**: See [LocalGov Technical Documentation](../modules/LocalGov.md)
- **Key Features**:
  - Governance address management
  - Time-locked transitions
  - Access control for administrative functions
- **Exported Interface**: All governance functions via `gov.__interface__`

### AddressRegistry Module

- **Location**: `contracts/registries/modules/AddressRegistry.vy`
- **Purpose**: Manages the registry of price source addresses
- **Documentation**: See [AddressRegistry Technical Documentation](../modules/AddressRegistry.md)
- **Key Features**:
  - Sequential registry ID assignment for price sources
  - Time-locked address additions, updates, and disabling
  - Descriptive labels for each price source
- **Exported Interface**: All registry functions via `registry.__interface__`

### Addys Module

- **Location**: `contracts/modules/Addys.vy`
- **Purpose**: Provides RipeHq integration for address lookups
- **Documentation**: See [Addys Technical Documentation](../modules/Addys.md)
- **Key Features**:
  - Access to MissionControl address
  - Validation of Ripe protocol addresses
- **Exported Interface**: Address utilities via `addys.__interface__`

### DeptBasics Module

- **Location**: `contracts/modules/DeptBasics.vy`
- **Purpose**: Provides department-level basic functionality
- **Documentation**: See [DeptBasics Technical Documentation](../modules/DeptBasics.md)
- **Key Features**:
  - Pause mechanism
  - Department interface compliance
  - No minting capabilities (disabled for PriceDesk)
- **Exported Interface**: Department basics via `deptBasics.__interface__`

### Module Initialization

```vyper
initializes: gov
initializes: registry[gov := gov]
initializes: addys
initializes: deptBasics[addys := addys]
```

## System Architecture Diagram

```
+------------------------------------------------------------------------+
|                          PriceDesk Contract                            |
+------------------------------------------------------------------------+
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                      Price Discovery Flow                        |  |
|  |                                                                  |  |
|  |  1. getPrice(_asset) called                                      |  |
|  |     |                                                            |  |
|  |     v                                                            |  |
|  |  2. Fetch PriceConfig from MissionControl                        |  |
|  |     - staleTime threshold                                        |  |
|  |     - priorityPriceSourceIds list                                |  |
|  |     |                                                            |  |
|  |     v                                                            |  |
|  |  3. Check Priority Sources (in order)                            |  |
|  |     - Query each priority oracle                                 |  |
|  |     - Return first valid price found                             |  |
|  |     |                                                            |  |
|  |     v (if no price found)                                        |  |
|  |  4. Check All Registered Sources                                 |  |
|  |     - Iterate through registry (skip already checked)            |  |
|  |     - Return first valid price found                             |  |
|  |     |                                                            |  |
|  |     v                                                            |  |
|  |  5. Return price or 0 (optionally raise if feed exists)          |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Module Components                             |  |
|  |                                                                  |  |
|  |  +----------------+   +------------------+  +-----------------+  |  |
|  |  | LocalGov       |  | AddressRegistry   |  | Addys           |  |  |
|  |  | * Governance   |  | * Oracle registry |  | * RipeHq lookup |  |  |
|  |  | * Time-locks   |  | * ID management   |  | * MC address    |  |  |
|  |  +----------------+  +-------------------+  +-----------------+  |  |
|  |                                                                  |  |
|  |  +----------------+                                              |  |
|  |  | DeptBasics     |                                              |  |
|  |  | * Pause state  |                                              |  |
|  |  | * No minting   |                                              |  |
|  |  +----------------+                                              |  |
|  +------------------------------------------------------------------+  |
+------------------------------------------------------------------------+
                                    |
        +---------------------------+---------------------------+
        |                           |                           |
        v                           v                           v
+----------------+       +------------------+       +-------------------+
| MissionControl |       | Priority Oracles |       | Standard Oracles  |
| * PriceConfig  |       | * Chainlink      |       | * Backup sources  |
| * Priority IDs |       | * Primary feeds  |       | * Alternative     |
+----------------+       +------------------+       |   providers       |
                                                    +-------------------+
```

## Data Structures

### PriceConfig Struct

Configuration for price discovery (fetched from MissionControl):

```vyper
struct PriceConfig:
    staleTime: uint256                                              # Maximum age for valid prices
    priorityPriceSourceIds: DynArray[uint256, MAX_PRIORITY_PRICE_SOURCES]  # Priority oracle IDs
```

## State Variables

### Constants

- `MAX_PRIORITY_PRICE_SOURCES: uint256 = 10` - Maximum priority sources in config
- `UNDERSCORE_APPRAISER_ID: uint256 = 8` - Registry ID for underscore appraiser

### Immutable Variables

- `ETH: address` - Address representing ETH for pricing

### Inherited State Variables

From [LocalGov](../modules/LocalGov.md):

- `governance: address` - Current governance address
- `govChangeTimeLock: uint256` - Timelock for governance changes

From [AddressRegistry](../modules/AddressRegistry.md):

- `registryChangeTimeLock: uint256` - Timelock for registry changes
- Registry mappings for oracle management

From Addys:

- RipeHq address reference

From [DeptBasics](../modules/DeptBasics.md):

- `isPaused: bool` - Department pause state

## Constructor

### `__init__`

Initializes PriceDesk with governance settings and ETH address configuration.

```vyper
@deploy
def __init__(
    _ripeHq: address,
    _tempGov: address,
    _ethAddr: address,
    _minRegistryTimeLock: uint256,
    _maxRegistryTimeLock: uint256,
):
```

#### Parameters

| Name                   | Type      | Description                            |
| ---------------------- | --------- | -------------------------------------- |
| `_ripeHq`              | `address` | RipeHq contract address                |
| `_tempGov`             | `address` | Initial temporary governance address   |
| `_ethAddr`             | `address` | Address representing ETH for pricing   |
| `_minRegistryTimeLock` | `uint256` | Minimum time-lock for registry changes |
| `_maxRegistryTimeLock` | `uint256` | Maximum time-lock for registry changes |

#### Returns

_Constructor does not return any values_

#### Access

Called only during deployment

#### Example Usage

```python
# Deploy PriceDesk
price_desk = boa.load(
    "contracts/registries/PriceDesk.vy",
    ripe_hq.address,
    deployer.address,     # Temp governance
    weth_token.address,   # ETH representation
    100,                  # Min registry timelock
    1000                  # Max registry timelock
)
```

**Example Output**: Contract deployed with oracle registry ready, no minting capabilities

## Price Query Functions

### `getPrice`

Gets the current USD price for an asset by checking registered oracles.

```vyper
@view
@external
def getPrice(_asset: address, _shouldRaise: bool = False) -> uint256:
```

#### Parameters

| Name           | Type      | Description                                            |
| -------------- | --------- | ------------------------------------------------------ |
| `_asset`       | `address` | The asset to price                                     |
| `_shouldRaise` | `bool`    | Whether to raise exception if feed exists but no price |

#### Returns

| Type      | Description                                 |
| --------- | ------------------------------------------- |
| `uint256` | USD price with 18 decimals (0 if not found) |

#### Access

Public view function

#### Example Usage

```python
# Get USDC price
usdc_price = price_desk.getPrice(usdc.address)
# Returns: 1000000000000000000 (1e18 = $1.00)

# Get price with exception on stale
btc_price = price_desk.getPrice(
    wbtc.address,
    True  # Raise if feed exists but price is stale
)
```

**Example Output**: Returns price in 18 decimal format or 0 if not found

### `getUsdValue`

Converts an asset amount to its USD value.

```vyper
@view
@external
def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool = False) -> uint256:
```

#### Parameters

| Name           | Type      | Description                       |
| -------------- | --------- | --------------------------------- |
| `_asset`       | `address` | The asset address                 |
| `_amount`      | `uint256` | Amount in asset's native decimals |
| `_shouldRaise` | `bool`    | Whether to raise on stale price   |

#### Returns

| Type      | Description                |
| --------- | -------------------------- |
| `uint256` | USD value with 18 decimals |

#### Access

Public view function

#### Example Usage

```python
# Get USD value of 100 USDC (6 decimals)
usd_value = price_desk.getUsdValue(
    usdc.address,
    100_000000  # 100 USDC
)
# Returns: 100000000000000000000 (100e18 = $100)

# Get USD value of 2 WBTC (8 decimals)
btc_value = price_desk.getUsdValue(
    wbtc.address,
    2_00000000  # 2 BTC
)
# Returns: 60000000000000000000000 (if BTC = $30,000)
```

### `getAssetAmount`

Converts a USD value to the equivalent asset amount.

```vyper
@view
@external
def getAssetAmount(_asset: address, _usdValue: uint256, _shouldRaise: bool = False) -> uint256:
```

#### Parameters

| Name           | Type      | Description                     |
| -------------- | --------- | ------------------------------- |
| `_asset`       | `address` | The asset address               |
| `_usdValue`    | `uint256` | USD value with 18 decimals      |
| `_shouldRaise` | `bool`    | Whether to raise on stale price |

#### Returns

| Type      | Description                     |
| --------- | ------------------------------- |
| `uint256` | Asset amount in native decimals |

#### Access

Public view function

#### Example Usage

```python
# Get USDC amount for $500
usdc_amount = price_desk.getAssetAmount(
    usdc.address,
    500_000000000000000000  # $500
)
# Returns: 500_000000 (500 USDC with 6 decimals)

# Get WBTC amount for $15,000
btc_amount = price_desk.getAssetAmount(
    wbtc.address,
    15000_000000000000000000  # $15,000
)
# Returns: 50000000 (0.5 BTC with 8 decimals if BTC = $30,000)
```

### `hasPriceFeed`

Checks if any registered oracle has a price feed for an asset.

```vyper
@view
@external
def hasPriceFeed(_asset: address) -> bool:
```

#### Parameters

| Name     | Type      | Description        |
| -------- | --------- | ------------------ |
| `_asset` | `address` | The asset to check |

#### Returns

| Type   | Description                   |
| ------ | ----------------------------- |
| `bool` | True if any oracle has a feed |

#### Access

Public view function

#### Example Usage

```python
# Check if USDC has a price feed
has_feed = price_desk.hasPriceFeed(usdc.address)
# Returns: True

# Check if random token has feed
has_feed = price_desk.hasPriceFeed(unknown_token.address)
# Returns: False
```

## ETH-Specific Functions

### `getEthUsdValue`

Converts ETH amount to USD value.

```vyper
@view
@external
def getEthUsdValue(_amount: uint256, _shouldRaise: bool = False) -> uint256:
```

#### Parameters

| Name           | Type      | Description                     |
| -------------- | --------- | ------------------------------- |
| `_amount`      | `uint256` | ETH amount in wei (18 decimals) |
| `_shouldRaise` | `bool`    | Whether to raise on stale price |

#### Returns

| Type      | Description                |
| --------- | -------------------------- |
| `uint256` | USD value with 18 decimals |

#### Access

Public view function

#### Example Usage

```python
# Get USD value of 1.5 ETH
usd_value = price_desk.getEthUsdValue(
    1_500000000000000000  # 1.5 ETH
)
# Returns: 2250000000000000000000 (if ETH = $1,500)
```

### `getEthAmount`

Converts USD value to ETH amount.

```vyper
@view
@external
def getEthAmount(_usdValue: uint256, _shouldRaise: bool = False) -> uint256:
```

#### Parameters

| Name           | Type      | Description                     |
| -------------- | --------- | ------------------------------- |
| `_usdValue`    | `uint256` | USD value with 18 decimals      |
| `_shouldRaise` | `bool`    | Whether to raise on stale price |

#### Returns

| Type      | Description       |
| --------- | ----------------- |
| `uint256` | ETH amount in wei |

#### Access

Public view function

#### Example Usage

```python
# Get ETH amount for $3,000
eth_amount = price_desk.getEthAmount(
    3000_000000000000000000  # $3,000
)
# Returns: 2000000000000000000 (2 ETH if ETH = $1,500)
```

## Registry Management Functions

### `startAddNewAddressToRegistry`

Initiates adding a new price source to the registry.

```vyper
@external
def startAddNewAddressToRegistry(_addr: address, _description: String[64]) -> bool:
```

#### Parameters

| Name           | Type         | Description                       |
| -------------- | ------------ | --------------------------------- |
| `_addr`        | `address`    | The price source contract address |
| `_description` | `String[64]` | Description of the price source   |

#### Returns

| Type   | Description                    |
| ------ | ------------------------------ |
| `bool` | True if successfully initiated |

#### Access

Only callable by governance AND only when the contract is not paused (see [LocalGov](../modules/LocalGov.md) for governance details)

#### Events Emitted

- `NewAddressPending` (from [AddressRegistry](../modules/AddressRegistry.md)) - Contains address, description, and confirmation block

#### Example Usage

```python
# Add Chainlink oracle
success = price_desk.startAddNewAddressToRegistry(
    chainlink_oracle.address,
    "Chainlink Price Oracle",
    sender=governance.address
)
```

**Example Output**: Returns `True`, emits event with timelock confirmation block

### `confirmNewAddressToRegistry`

Confirms adding a new price source after timelock.

```vyper
@external
def confirmNewAddressToRegistry(_addr: address) -> uint256:
```

#### Parameters

| Name    | Type      | Description                         |
| ------- | --------- | ----------------------------------- |
| `_addr` | `address` | The price source address to confirm |

#### Returns

| Type      | Description              |
| --------- | ------------------------ |
| `uint256` | The assigned registry ID |

#### Access

Only callable by governance AND only when the contract is not paused

#### Events Emitted

- `NewAddressConfirmed` (from [AddressRegistry](../modules/AddressRegistry.md)) - Contains registry ID, address, description

#### Example Usage

```python
# Confirm after timelock
boa.env.time_travel(blocks=time_lock)
oracle_id = price_desk.confirmNewAddressToRegistry(
    chainlink_oracle.address,
    sender=governance.address
)
# Returns: 1 (first oracle registered)
```

### `cancelNewAddressToRegistry`

Cancels a pending price source addition.

```vyper
@external
def cancelNewAddressToRegistry(_addr: address) -> bool:
```

#### Parameters

| Name    | Type      | Description                        |
| ------- | --------- | ---------------------------------- |
| `_addr` | `address` | The price source address to cancel |

#### Returns

| Type   | Description                    |
| ------ | ------------------------------ |
| `bool` | True if successfully cancelled |

#### Access

Only callable by governance AND only when the contract is not paused

#### Events Emitted

- `NewAddressCancelled` (from [AddressRegistry](../modules/AddressRegistry.md))

#### Example Usage

```python
success = price_desk.cancelNewAddressToRegistry(
    chainlink_oracle.address,
    sender=governance.address
)
```

### `startAddressUpdateToRegistry`

Initiates updating a price source address.

```vyper
@external
def startAddressUpdateToRegistry(_regId: uint256, _newAddr: address) -> bool:
```

#### Parameters

| Name       | Type      | Description              |
| ---------- | --------- | ------------------------ |
| `_regId`   | `uint256` | Registry ID to update    |
| `_newAddr` | `address` | New price source address |

#### Returns

| Type   | Description                    |
| ------ | ------------------------------ |
| `bool` | True if successfully initiated |

#### Access

Only callable by governance AND only when the contract is not paused

#### Events Emitted

- `AddressUpdatePending` (from [AddressRegistry](../modules/AddressRegistry.md))

#### Example Usage

```python
# Update oracle to new version
success = price_desk.startAddressUpdateToRegistry(
    1,  # Chainlink oracle ID
    chainlink_v2.address,
    sender=governance.address
)
```

### `confirmAddressUpdateToRegistry`

Confirms a price source update after timelock.

```vyper
@external
def confirmAddressUpdateToRegistry(_regId: uint256) -> bool:
```

#### Parameters

| Name     | Type      | Description               |
| -------- | --------- | ------------------------- |
| `_regId` | `uint256` | Registry ID being updated |

#### Returns

| Type   | Description                    |
| ------ | ------------------------------ |
| `bool` | True if successfully confirmed |

#### Access

Only callable by governance AND only when the contract is not paused

#### Events Emitted

- `AddressUpdateConfirmed` (from [AddressRegistry](../modules/AddressRegistry.md))

#### Example Usage

```python
# Confirm update after timelock
boa.env.time_travel(blocks=time_lock)
success = price_desk.confirmAddressUpdateToRegistry(
    1,
    sender=governance.address
)
```

### `cancelAddressUpdateToRegistry`

Cancels a pending price source update.

```vyper
@external
def cancelAddressUpdateToRegistry(_regId: uint256) -> bool:
```

#### Parameters

| Name     | Type      | Description                  |
| -------- | --------- | ---------------------------- |
| `_regId` | `uint256` | Registry ID to cancel update |

#### Returns

| Type   | Description                    |
| ------ | ------------------------------ |
| `bool` | True if successfully cancelled |

#### Access

Only callable by governance AND only when the contract is not paused

#### Events Emitted

- `AddressUpdateCancelled` (from [AddressRegistry](../modules/AddressRegistry.md))

### `startAddressDisableInRegistry`

Initiates disabling a price source.

```vyper
@external
def startAddressDisableInRegistry(_regId: uint256) -> bool:
```

#### Parameters

| Name     | Type      | Description            |
| -------- | --------- | ---------------------- |
| `_regId` | `uint256` | Registry ID to disable |

#### Returns

| Type   | Description                    |
| ------ | ------------------------------ |
| `bool` | True if successfully initiated |

#### Access

Only callable by governance AND only when the contract is not paused

#### Events Emitted

- `AddressDisablePending` (from [AddressRegistry](../modules/AddressRegistry.md))

#### Example Usage

```python
# Start disabling compromised oracle
success = price_desk.startAddressDisableInRegistry(
    3,  # Compromised oracle ID
    sender=governance.address
)
```

### `confirmAddressDisableInRegistry`

Confirms disabling a price source after timelock.

```vyper
@external
def confirmAddressDisableInRegistry(_regId: uint256) -> bool:
```

#### Parameters

| Name     | Type      | Description            |
| -------- | --------- | ---------------------- |
| `_regId` | `uint256` | Registry ID to disable |

#### Returns

| Type   | Description                   |
| ------ | ----------------------------- |
| `bool` | True if successfully disabled |

#### Access

Only callable by governance AND only when the contract is not paused

#### Events Emitted

- `AddressDisableConfirmed` (from [AddressRegistry](../modules/AddressRegistry.md))

### `cancelAddressDisableInRegistry`

Cancels a pending disable operation.

```vyper
@external
def cancelAddressDisableInRegistry(_regId: uint256) -> bool:
```

#### Parameters

| Name     | Type      | Description                   |
| -------- | --------- | ----------------------------- |
| `_regId` | `uint256` | Registry ID to cancel disable |

#### Returns

| Type   | Description                    |
| ------ | ------------------------------ |
| `bool` | True if successfully cancelled |

#### Access

Only callable by governance AND only when the contract is not paused

#### Events Emitted

- `AddressDisableCancelled` (from [AddressRegistry](../modules/AddressRegistry.md))

## Price Snapshot Functions

### `addPriceSnapshot`

Triggers price snapshots across all oracles that have a feed for the asset.

```vyper
@external
def addPriceSnapshot(_asset: address) -> bool:
```

#### Parameters

| Name     | Type      | Description                  |
| -------- | --------- | ---------------------------- |
| `_asset` | `address` | Asset to snapshot prices for |

#### Returns

| Type   | Description                                                                                                                                         |
| ------ | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `bool` | Returns `True` if a snapshot was successfully triggered on at least one price source. Returns `False` if no price sources had a feed for the asset. |

#### Access

Only callable by valid Ripe addresses or the underscore appraiser

#### Example Usage

```python
# Trigger price snapshot for USDC
updated = price_desk.addPriceSnapshot(
    usdc.address,
    sender=credit_engine.address  # Valid Ripe address
)
# Returns: True if any oracle updated

# Underscore appraiser triggers snapshot
updated = price_desk.addPriceSnapshot(
    wbtc.address,
    sender=underscore_appraiser.address
)
```

**Example Output**: Calls `addPriceSnapshot` on all oracles with the asset feed

## Testing

For comprehensive test examples, see: [`tests/registries/test_price_desk.py`](../../tests/registries/test_price_desk.py)
