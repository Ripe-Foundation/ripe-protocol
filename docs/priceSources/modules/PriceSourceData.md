# PriceSourceData Module Technical Documentation

## Overview

PriceSourceData serves as the foundational data management module for all price source contracts within the Ripe Protocol ecosystem. Think of it as the universal database layer that handles asset registration, pause states, and fund recovery for every price oracle integration in the system. Whether it's Chainlink, Pyth, Stork, or custom price sources, they all rely on PriceSourceData for consistent state management and administrative controls.

At its core, PriceSourceData manages four fundamental responsibilities:

**1. Asset Registration and Tracking**: Maintains a registry of all assets that have pricing information available through the price source, with automatic registration and deregistration capabilities to ensure accurate tracking of supported assets across oracle integrations.

**2. Pause State Management**: Implements contract-wide pause functionality that allows emergency halting of price feed operations, providing critical circuit breaker capabilities for handling oracle malfunctions or market anomalies.

**3. Fund Recovery Operations**: Provides secure mechanisms for recovering any tokens accidentally sent to price source contracts, ensuring no funds are permanently locked while maintaining strict access controls.

**4. Indexed Asset Enumeration**: Maintains optimized data structures for efficient asset iteration and querying, supporting up to 50 assets per price source with proper indexing and array compression to prevent storage gaps.

For technical readers, PriceSourceData implements a 1-based indexing system to distinguish between "not registered" (index 0) and registered assets, provides atomic asset registration and deregistration with automatic array compression, maintains pause states that can be checked by all price query functions, implements secure fund recovery restricted to Switchboard governance addresses, and offers comprehensive asset enumeration for integration with PriceDesk and other protocol components. The module is designed to be oracle-agnostic, supporting any price source implementation while maintaining consistent administrative controls.

## Architecture & Dependencies

PriceSourceData is built as a foundational module with minimal dependencies:

### Core Dependencies
- **Addys**: Address resolution for protocol contracts and permission management
- **IERC20**: Token interface for balance queries and fund recovery operations

### Module Dependencies
```vyper
uses: addys
import contracts.modules.Addys as addys
from ethereum.ercs import IERC20
```

### Key Constants
- `MAX_ASSETS: constant(uint256) = 50` - Maximum supported assets per price source
- `MAX_RECOVER_ASSETS: constant(uint256) = 20` - Maximum assets recoverable in batch

## Data Structures

### Asset Registry
```vyper
# Asset tracking with 1-based indexing
assets: public(HashMap[uint256, address])          # index -> asset
indexOfAsset: public(HashMap[address, uint256])    # asset -> index  
numAssets: public(uint256)                         # total asset count
```

### Configuration State
```vyper
isPaused: public(bool)                             # Emergency pause state
```

## State Variables

### Asset Management
- **assets**: Maps indices to asset addresses (1-based indexing)
- **indexOfAsset**: Reverse lookup from asset address to index
- **numAssets**: Total number of registered assets (actual count = numAssets - 1)

### Configuration
- **isPaused**: Global pause state for price source operations

## System Architecture Diagram

```
+------------------------------------------------------------------------+
|                      PriceSourceData Module                           |
+------------------------------------------------------------------------+
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                     Asset Registration System                    |  |
|  |                                                                  |  |
|  |  Asset Registry (1-based indexing):                              |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ assets[1] = WETH                                           │ |  |
|  |  │ assets[2] = USDC                                           │ |  |
|  |  │ assets[3] = WBTC                                           │ |  |
|  |  │ assets[4] = DAI                                            │ |  |
|  |  │                                                             │ |  |
|  |  │ indexOfAsset[WETH] = 1                                     │ |  |
|  |  │ indexOfAsset[USDC] = 2                                     │ |  |
|  |  │ indexOfAsset[WBTC] = 3                                     │ |  |
|  |  │ indexOfAsset[DAI] = 4                                      │ |  |
|  |  │                                                             │ |  |
|  |  │ numAssets = 5 (actual count = 4, index starts at 1)       │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  |                                                                  |  |
|  |  Registration Process:                                           |  |
|  |  • _addPricedAsset(asset): Adds new asset to registry           |  |
|  |  • Automatically assigns next available index                   |  |
|  |  • Creates bidirectional mapping for efficient lookups          |  |
|  |                                                                  |  |
|  |  Deregistration Process:                                         |  |
|  |  • _removePricedAsset(asset): Removes asset from registry       |  |
|  |  • Compresses array by moving last item to fill gap            |  |
|  |  • Updates all relevant mappings and indices                    |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Administrative Functions                      |  |
|  |                                                                  |  |
|  |  Pause Management:                                               |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ pause(shouldPause):                                        │ |  |
|  |  │ • Only callable by Switchboard addresses                   │ |  |
|  |  │ • Updates isPaused state                                   │ |  |
|  |  │ • Emits PriceSourcePauseModified event                     │ |  |
|  |  │ • Price source contracts check this before returning prices │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  |                                                                  |  |
|  |  Fund Recovery:                                                  |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ recoverFunds(recipient, asset):                            │ |  |
|  |  │ • Recovers accidentally sent tokens                        │ |  |
|  |  │ • Only callable by Switchboard addresses                   │ |  |
|  |  │ • Transfers entire balance to recipient                    │ |  |
|  |  │ • Emits PriceSourceFundsRecovered event                    │ |  |
|  |  │                                                             │ |  |
|  |  │ recoverFundsMany(recipient, assets[]):                     │ |  |
|  |  │ • Batch version for multiple assets                        │ |  |
|  |  │ • Processes up to 20 assets in single transaction          │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                      Query Functions                            |  |
|  |                                                                  |  |
|  |  getPricedAssets():                                               |  |
|  |  • Returns array of all registered assets                        |  |
|  |  • Supports up to 50 assets                                      |  |
|  |  • Used by PriceDesk for asset discovery                         |  |
|  |  • Efficient iteration with 1-based indexing                     |  |
|  +------------------------------------------------------------------+  |
+------------------------------------------------------------------------+
                                    |
                                    | Used by all price source contracts
                                    v
+------------------------------------------------------------------------+
|                     Price Source Implementations                      |
+------------------------------------------------------------------------+
|                                                                        |
| ChainlinkPrices:          PythPrices:           StorkPrices:          |
| • Uses PriceSourceData    • Uses PriceSourceData • Uses PriceSourceData |
| • Checks isPaused         • Checks isPaused      • Checks isPaused     |
| • Manages assets          • Manages assets       • Manages assets      |
|                                                                        |
| CurvePrices:              BlueChipYieldPrices:                        |
| • Uses PriceSourceData    • Uses PriceSourceData                      |
| • Checks isPaused         • Checks isPaused                           |
| • Manages assets          • Manages assets                            |
+------------------------------------------------------------------------+
```

## Constructor

### `__init__`

Initializes PriceSourceData with initial pause state.

```vyper
@deploy
def __init__(_shouldPause: bool):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_shouldPause` | `bool` | Whether to start in paused state |

#### Access

Called during deployment

#### Example Usage
```python
# Deploy with price source initially active
price_source_data = boa.load(
    "contracts/priceSources/modules/PriceSourceData.vy",
    False  # Not paused
)

# Deploy with price source initially paused for setup
price_source_data = boa.load(
    "contracts/priceSources/modules/PriceSourceData.vy", 
    True   # Paused
)
```

## Core Asset Management Functions

### `_addPricedAsset`

Registers a new asset for price tracking.

```vyper
@internal
def _addPricedAsset(_asset: address):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_asset` | `address` | Asset address to register |

#### Access

Internal function (called by price source contracts)

#### Process Flow
1. **Index Assignment**: Gets next available index (starting from 1, not 0)
2. **Asset Storage**: Stores asset at `assets[index]`
3. **Reverse Mapping**: Creates lookup at `indexOfAsset[_asset]`
4. **Count Update**: Increments `numAssets`

#### 1-Based Indexing
The module uses 1-based indexing to distinguish between:
- Index 0: Asset not registered
- Index 1+: Valid registered asset

#### Example Integration
```python
# In a price source contract's initialization
def _setupAssets():
    price_source_data._addPricedAsset(weth_address)
    price_source_data._addPricedAsset(usdc_address)
    price_source_data._addPricedAsset(wbtc_address)
```

### `_removePricedAsset`

Deregisters an asset from price tracking.

```vyper
@internal
def _removePricedAsset(_asset: address):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_asset` | `address` | Asset address to deregister |

#### Access

Internal function (called by price source contracts)

#### Process Flow
1. **Existence Check**: Verifies asset is registered (`indexOfAsset[_asset] != 0`)
2. **Array Compression**: Moves last asset to fill the gap:
   ```vyper
   if targetIndex != lastIndex:
       lastItem = assets[lastIndex]
       assets[targetIndex] = lastItem
       indexOfAsset[lastItem] = targetIndex
   ```
3. **Cleanup**: Clears mappings and decrements count
4. **No Gaps**: Ensures array remains contiguous

#### Array Compression Example
```
Before removing USDC (index 2):
assets[1] = WETH
assets[2] = USDC  <- Remove this
assets[3] = WBTC
assets[4] = DAI

After removal:
assets[1] = WETH
assets[2] = DAI   <- Moved from index 4
assets[3] = WBTC
numAssets = 4 (was 5)
```

### `getPricedAssets`

Returns all assets supported by this price source.

```vyper
@view
@external
def getPricedAssets() -> DynArray[address, MAX_ASSETS]:
```

#### Returns

| Type | Description |
|------|-------------|
| `DynArray[address, MAX_ASSETS]` | Array of all registered asset addresses |

#### Process Flow
1. **Empty Check**: Returns empty array if no assets registered
2. **Iteration**: Loops from index 1 to numAssets (1-based)
3. **Collection**: Appends each asset to result array
4. **Return**: Complete list of supported assets

#### Example Usage
```python
# Query all assets with pricing available
supported_assets = price_source.getPricedAssets()

# Iterate through assets to get prices
for asset in supported_assets:
    price = price_source.getPrice(asset)
    print(f"{asset}: ${price}")
```

## Administrative Functions

### `pause`

Controls the operational state of the price source.

```vyper
@external
def pause(_shouldPause: bool):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_shouldPause` | `bool` | New pause state |

#### Access

Only callable by Switchboard addresses (governance)

#### Validation
- Requires caller to be valid Switchboard address
- Requires state change (cannot set to current state)

#### Events Emitted

- `PriceSourcePauseModified` - Contains new pause state

#### Usage Context
Price source contracts check `isPaused` before returning prices:
```vyper
# In price source contract
def getPrice(asset: address) -> uint256:
    assert not self.isPaused  # Reverts if paused
    # ... return price
```

#### Example Usage
```python
# Emergency pause during oracle issues
price_source.pause(True, sender=governance.address)

# Resume operations after issue resolved
price_source.pause(False, sender=governance.address)
```

### `recoverFunds`

Recovers tokens accidentally sent to the price source contract.

```vyper
@external
def recoverFunds(_recipient: address, _asset: address):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_recipient` | `address` | Address to receive recovered funds |
| `_asset` | `address` | Token to recover |

#### Access

Only callable by Switchboard addresses (governance)

#### Validation
- Recipient and asset must not be empty addresses
- Asset must have non-zero balance in contract

#### Process Flow
1. **Balance Check**: Queries token balance of contract
2. **Validation**: Ensures balance > 0
3. **Transfer**: Sends entire balance to recipient
4. **Event**: Logs recovery details

#### Events Emitted

- `PriceSourceFundsRecovered` - Contains asset, recipient, and amount

### `recoverFundsMany`

Batch version of fund recovery for multiple assets.

```vyper
@external
def recoverFundsMany(_recipient: address, _assets: DynArray[address, MAX_RECOVER_ASSETS]):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_recipient` | `address` | Address to receive all recovered funds |
| `_assets` | `DynArray[address, MAX_RECOVER_ASSETS]` | List of tokens to recover |

#### Access

Only callable by Switchboard addresses (governance)

#### Process Flow
Iterates through assets array and calls `_recoverFunds` for each

#### Example Usage
```python
# Recover multiple accidentally sent tokens
tokens_to_recover = [weth.address, usdc.address, dai.address]
price_source.recoverFundsMany(
    treasury.address,
    tokens_to_recover,
    sender=governance.address
)
```

## Internal Utility Functions

### `_recoverFunds`

Internal implementation of fund recovery logic.

```vyper
@internal
def _recoverFunds(_recipient: address, _asset: address):
```

#### Process Flow
1. **Validation**: Ensures valid recipient and asset addresses
2. **Balance Query**: Gets current token balance
3. **Zero Check**: Reverts if no funds to recover
4. **Transfer**: Executes ERC20 transfer
5. **Event Emission**: Logs recovery details

## Data Structure Design

### 1-Based Indexing Rationale

The module uses 1-based indexing for asset arrays:

```python
# Registration starts at index 1
if numAssets == 0:
    aid = 1  # First asset gets index 1, not 0

# This allows:
if indexOfAsset[asset] == 0:
    # Asset is NOT registered
else:
    # Asset IS registered at the given index
```

Benefits:
- Clear distinction between unregistered (0) and registered (1+)
- Simplifies existence checks
- Prevents accidental operations on index 0

### Array Compression Algorithm

When removing assets, the module prevents gaps:

```python
# Move last item to fill the gap
if targetIndex != lastIndex:
    lastItem = assets[lastIndex]
    assets[targetIndex] = lastItem
    indexOfAsset[lastItem] = targetIndex
```

This ensures:
- No storage gaps wasting gas
- Continuous iteration from 1 to numAssets
- Consistent array state

## Security Considerations

### Access Control
- **Switchboard Only**: All administrative functions restricted to governance
- **Internal Asset Management**: Asset registration/deregistration only via internal functions
- **No Direct Manipulation**: External parties cannot modify asset registry

### Fund Safety
- **Recovery Only**: Can only recover untracked funds
- **Balance Verification**: Checks actual token balance before recovery
- **Event Logging**: All recoveries logged for transparency

### Pause Protection
- **Circuit Breaker**: Allows immediate halting of price feeds
- **State Validation**: Cannot set pause to current state
- **Integration Point**: Price sources must check pause state

## Integration Patterns

### Price Source Implementation
```vyper
# Price source contract using PriceSourceData
implements: PriceSource

uses: priceSourceData
initializes: priceSourceData

from interfaces import PriceSource
import contracts.priceSources.modules.PriceSourceData as priceSourceData

@deploy
def __init__():
    priceSourceData.__init__(False)  # Start unpaused
    
    # Register supported assets
    priceSourceData._addPricedAsset(WETH)
    priceSourceData._addPricedAsset(USDC)

@external
def getPrice(_asset: address) -> uint256:
    # Check pause state
    assert not priceSourceData.isPaused
    
    # Verify asset is supported
    assert priceSourceData.indexOfAsset[_asset] != 0
    
    # Return price...
```

### Asset Discovery Pattern
```python
# PriceDesk discovering available assets
assets = price_source.getPricedAssets()
for asset in assets:
    try:
        price = price_source.getPrice(asset)
        # Store price...
    except:
        # Handle pricing error
        pass
```

## Events

### `PriceSourcePauseModified`

Emitted when pause state changes.

| Field | Type | Description |
|-------|------|-------------|
| `isPaused` | `bool` | New pause state |

### `PriceSourceFundsRecovered`

Emitted when funds are recovered from contract.

| Field | Type | Description |
|-------|------|-------------|
| `asset` | `indexed(address)` | Token recovered |
| `recipient` | `indexed(address)` | Address receiving funds |
| `balance` | `uint256` | Amount recovered |

## Testing

For comprehensive test examples, see: [`tests/priceSources/test_price_source_data.py`](../../tests/priceSources/test_price_source_data.py)