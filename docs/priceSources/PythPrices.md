# PythPrices Technical Documentation

[📄 View Source Code](../../contracts/priceSources/PythPrices.vy)

## Overview

PythPrices integrates the Pyth Network oracle for high-frequency, low-latency price feeds. It provides real-time USD pricing with confidence intervals and exponential notation support for maximum precision.

**Core Features**:
- **Pull-Based Updates**: On-demand price updates with fee optimization
- **Confidence Intervals**: Price uncertainty metrics for risk assessment
- **Batch Processing**: Multi-asset updates in single transaction
- **Exponential Pricing**: Handles both positive and negative exponents

The module implements automatic fee calculation for updates, strict validation of price freshness and confidence, efficient caching to minimize update costs, and comprehensive error handling for failed updates.

## Architecture & Dependencies

PythPrices is built using a modular architecture with direct Pyth Network integration:

### Core Module Dependencies
- **LocalGov**: Provides governance functionality with access control
- **Addys**: Address resolution for protocol contracts
- **PriceSourceData**: Asset registration and pause state management
- **TimeLock**: Time-locked changes for feed management

### External Integration
- **Pyth Network**: Direct integration with Pyth oracle contracts
- **Pull Oracle Model**: Off-chain prices brought on-chain as needed
- **Update Fee System**: Automatic fee payment for price updates

### Module Initialization
```vyper
initializes: gov
initializes: addys
initializes: priceData[addys := addys]
initializes: timeLock[gov := gov]
```

### Immutable Configuration
```vyper
PYTH: immutable(address)  # Pyth Network contract address
```

## Data Structures

### PythPrice Struct
Raw price data from Pyth Network:
```vyper
struct PythPrice:
    price: int64          # Price value (can be negative)
    confidence: uint64    # Confidence interval
    exponent: int32       # Decimal exponent
    publishTime: uint64   # When price was published
```

### PythFeedConfig Struct
Configuration for each asset's price feed:
```vyper
struct PythFeedConfig:
    feedId: bytes32       # Pyth price feed ID
    staleTime: uint256    # Maximum age for price data in seconds
```

### PendingPythFeed Struct
Tracks pending feed changes during timelock:
```vyper
struct PendingPythFeed:
    actionId: uint256     # TimeLock action ID
    config: PythFeedConfig # New configuration
```

## State Variables

### Feed Configuration
- `feedConfig: HashMap[address, PythFeedConfig]` - Maps assets to Pyth feed configurations
- `pendingUpdates: HashMap[address, PendingPythFeed]` - Pending changes

### Constants
- `NORMALIZED_DECIMALS: constant(uint256) = 18` - Standard decimals
- `MAX_PRICE_UPDATES: constant(uint256) = 20` - Max batch updates

### Inherited State
From modules:
- Governance state (LocalGov)
- Pause state and asset registry (PriceSourceData)
- TimeLock configuration

## System Architecture Diagram

```
+------------------------------------------------------------------------+
|                        PythPrices Contract                            |
+------------------------------------------------------------------------+
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Price Retrieval Flow                          |  |
|  |                                                                  |  |
|  |  getPrice(asset):                                                |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ 1. Load Pyth feed ID for asset                             │ |  |
|  |  │ 2. Call Pyth Network's getPriceUnsafe()                    │ |  |
|  |  │ 3. Validate price data:                                     │ |  |
|  |  │    - price > 0 (has valid price)                           │ |  |
|  |  │    - publishTime not stale                                 │ |  |
|  |  │    - confidence < price (quality check)                    │ |  |
|  |  │ 4. Convert price based on exponent:                         │ |  |
|  |  │    - Negative exp: price × 10^(18-|exp|)                   │ |  |
|  |  │    - Positive exp: price × 10^(18+exp)                     │ |  |
|  |  │ 5. Apply confidence adjustment:                             │ |  |
|  |  │    final_price = price - confidence                        │ |  |
|  |  │ 6. Return price in 18 decimals                             │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Pull Oracle Update System                     |  |
|  |                                                                  |  |
|  |  Off-Chain Price Flow:                                           |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │   Pyth Publishers  ──> Aggregation ──> Signed Updates       │ |  |
|  |  │         ↓                                   ↓                │ |  |
|  |  │   Market Data                        Price Attestations     │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  |                                                                  |  |
|  |  On-Chain Update Flow:                                           |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ updatePythPrice(payload):                                   │ |  |
|  |  │ 1. Get required fee from Pyth                               │ |  |
|  |  │ 2. Check contract has sufficient ETH                        │ |  |
|  |  │ 3. Call updatePriceFeeds with fee payment                  │ |  |
|  |  │ 4. Pyth verifies signatures and updates prices              │ |  |
|  |  │ 5. Emit PythPriceUpdated event                             │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Confidence Interval System                    |  |
|  |                                                                  |  |
|  |  Price with Confidence:                                          |  |
|  |  ├────────────────────────────────────────────────┤             |  |
|  |  │←── confidence ──→│←──── price ────→│←── conf ──→│             |  |
|  |  └────────────────────────────────────────────────┘             |  |
|  |           ↓                   ↓              ↓                   |  |
|  |      Lower Bound      Best Estimate    Upper Bound              |  |
|  |                                                                  |  |
|  |  Conservative Pricing:                                           |  |
|  |  • final_price = price - confidence                             |  |
|  |  • Accounts for data provider disagreement                      |  |
|  |  • More conservative during volatile markets                    |  |
|  |  • Rejects if confidence >= price                               |  |
|  +------------------------------------------------------------------+  |
+------------------------------------------------------------------------+
                                    |
                                    ▼
+------------------------------------------------------------------------+
|                        Pyth Network Oracle                            |
+------------------------------------------------------------------------+
| • Decentralized network of professional data providers                |
| • Sub-second price updates with cryptographic attestations            |
| • Pull-based architecture for cost efficiency                         |
| • Cross-chain price feeds with unified interface                      |
+------------------------------------------------------------------------+
```

## Constructor

### `__init__`

Initializes PythPrices with governance settings and Pyth Network address.

```vyper
@deploy
def __init__(
    _ripeHq: address,
    _tempGov: address,
    _pythNetwork: address,
    _minPriceChangeTimeLock: uint256,
    _maxPriceChangeTimeLock: uint256,
):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_ripeHq` | `address` | RipeHq contract for protocol integration |
| `_tempGov` | `address` | Initial temporary governance address |
| `_pythNetwork` | `address` | Pyth Network contract address |
| `_minPriceChangeTimeLock` | `uint256` | Minimum timelock for feed changes |
| `_maxPriceChangeTimeLock` | `uint256` | Maximum timelock for feed changes |

#### Deployment Requirements
- Pyth Network address must not be empty
- Contract requires ETH balance for update fees

#### Example Usage
```python
pyth_prices = boa.load(
    "contracts/priceSources/PythPrices.vy",
    ripe_hq.address,
    deployer.address,
    pyth_network.address,  # Chain-specific Pyth deployment
    100,   # Min 100 blocks timelock
    1000   # Max 1000 blocks timelock
)

# Fund contract for update fees
deployer.transfer(pyth_prices.address, eth_amount)
```

## Core Price Functions

### `getPrice`

Retrieves the current price for an asset from Pyth Network.

```vyper
@view
@external
def getPrice(_asset: address, _staleTime: uint256 = 0, _priceDesk: address = empty(address)) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_asset` | `address` | Asset to get price for |
| `_staleTime` | `uint256` | Maximum age for price data in seconds. The caller is responsible for providing this value. A value of 0 disables the staleness check for this call. |
| `_priceDesk` | `address` | Not used in Pyth implementation |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Normalized price in 18 decimals (0 if invalid) |

#### Process Flow
1. **Feed Lookup**: Gets Pyth feed ID for asset
2. **Price Query**: Calls getPriceUnsafe for gas efficiency
3. **Validation**: Checks price > 0 and not stale
4. **Exponent Handling**: Normalizes to 18 decimals
5. **Confidence Adjustment**: Subtracts confidence interval

#### Example Usage
```python
# Get BTC price
btc_price = pyth_prices.getPrice(btc.address)

# Get price with 5 minute staleness check
eth_price = pyth_prices.getPrice(
    eth.address,
    300  # 5 minutes
)
```

### `getPriceAndHasFeed`

Returns price and feed existence status.

```vyper
@view
@external
def getPriceAndHasFeed(_asset: address, _staleTime: uint256 = 0, _priceDesk: address = empty(address)) -> (uint256, bool):
```

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Current price (0 if no feed) |
| `bool` | True if feed exists |

## Price Update Functions

### `updatePythPrice`

Brings fresh price data on-chain for configured feeds.

```vyper
@external
def updatePythPrice(_payload: Bytes[2048]) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_payload` | `Bytes[2048]` | Signed price update from Pyth |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if update successful |

#### Process
1. **Fee Calculation**: Gets required fee from Pyth
2. **Balance Check**: Ensures contract has ETH
3. **Update Call**: Submits payload with fee
4. **Event Emission**: Logs update details

#### Example Usage
```python
# Get price update from Pyth API
update_data = get_pyth_price_update(["0xabc123..."])  # Feed IDs

# Submit update on-chain
success = pyth_prices.updatePythPrice(update_data)
```

### `updateManyPythPrices`

Updates multiple price feeds in a single transaction.

```vyper
@external
def updateManyPythPrices(_payloads: DynArray[Bytes[2048], MAX_PRICE_UPDATES]) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_payloads` | `DynArray[Bytes[2048], MAX_PRICE_UPDATES]` | Multiple updates (max 20) |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Number of successful updates |

Stops processing on first failure to save gas.

## Feed Management Functions

### `addNewPriceFeed`

Initiates addition of a new Pyth price feed.

```vyper
@external
def addNewPriceFeed(_asset: address, _feedId: bytes32, _staleTime: uint256 = 0) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_asset` | `address` | Asset to add price feed for |
| `_feedId` | `bytes32` | Pyth Network price feed ID |
| `_staleTime` | `uint256` | Maximum age for price data in seconds (0 uses MissionControl default) |

#### Access

Only callable by governance

#### Validation
- Feed must exist in Pyth Network
- Asset must not already have a feed
- Feed must return valid price

#### Events Emitted

- `NewPythFeedPending` - Contains feed ID and confirmation block

#### Example Usage
```python
# Add ETH/USD feed with custom stale time
pyth_prices.addNewPriceFeed(
    eth.address,
    "0xff61491a931112ddf1bd8147cd1b641375f79f5825126d665480874634fd0ace",  # ETH/USD
    300,  # 5 minute stale time
    sender=governance
)
```

### `confirmNewPriceFeed`

Confirms a pending feed addition after timelock.

```vyper
@external
def confirmNewPriceFeed(_asset: address) -> bool:
```

#### Process Flow
1. **Re-validation**: Ensures feed still valid
2. **Timelock Check**: Verifies time passed
3. **Configuration Save**: Stores feed ID
4. **Asset Registration**: Adds to PriceSourceData

#### Events Emitted

- `NewPythFeedAdded` - Confirms feed is active

### `updatePriceFeed`

Updates existing feed to new Pyth feed ID.

```vyper
@external
def updatePriceFeed(_asset: address, _feedId: bytes32, _staleTime: uint256 = 0) -> bool:
```

Used when Pyth migrates feeds or better feeds become available.

### `disablePriceFeed`

Removes a price feed from the system.

```vyper
@external
def disablePriceFeed(_asset: address) -> bool:
```

Requires time-locked confirmation like other changes.

## ETH Balance Management

### `recoverEthBalance`

Withdraws ETH from contract (for excess update fees).

```vyper
@external
def recoverEthBalance(_recipient: address) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_recipient` | `address` | Address to receive ETH |

#### Access

Only callable by governance

#### Example Usage
```python
# Recover excess ETH
pyth_prices.recoverEthBalance(
    treasury.address,
    sender=governance
)
```

## Price Processing Details

### Exponent Handling

Pyth uses flexible decimal representation:
```vyper
# Negative exponent: divide by 10^|exponent|
if data.exponent < 0:
    exponent = convert(-data.exponent, uint256)
    price = price * 10**18 / 10**exponent

# Positive exponent: multiply by 10^exponent  
else:
    exponent = convert(data.exponent, uint256)
    price = price * 10**18 * 10**exponent
```

### Confidence Adjustment

Conservative pricing approach:
```vyper
# Subtract confidence interval from price
if confidence >= price:
    return 0  # Invalid price
    
return price - confidence
```

### Staleness Check

Uses publish time, not block time:
```vyper
publishTime = convert(data.publishTime, uint256)
if _staleTime != 0 and block.timestamp - publishTime > _staleTime:
    return 0  # Too stale
```

## Validation Functions

### `isValidNewFeed`

Checks if a new feed configuration is valid.

```vyper
@view
@external
def isValidNewFeed(_asset: address, _feedId: bytes32, _staleTime: uint256) -> bool:
```

#### Validation Checks
1. **No Existing Feed**: Asset must not have feed
2. **Feed Exists**: Must exist in Pyth Network
3. **Valid Price**: Must return non-zero price
4. **Asset Valid**: Non-empty address

### `isValidUpdateFeed`

Validates feed updates with additional checks:
- New feed must differ from current
- Asset must have existing feed

### `isValidDisablePriceFeed`

Ensures:
- Feed exists
- Asset is registered in PriceSourceData

## Events

### Feed Management Events
- `NewPythFeedPending` - New feed initiated
- `NewPythFeedAdded` - Feed confirmed
- `NewPythFeedCancelled` - Addition cancelled
- `PythFeedUpdatePending` - Update initiated
- `PythFeedUpdated` - Update confirmed
- `PythFeedUpdateCancelled` - Update cancelled
- `DisablePythFeedPending` - Removal initiated
- `PythFeedDisabled` - Feed removed
- `DisablePythFeedCancelled` - Removal cancelled

### Operational Events
- `PythPriceUpdated` - Price update submitted
- `EthRecoveredFromPyth` - ETH withdrawn

All events include relevant addresses, feed IDs, and action details.

## Security Considerations

### Access Control
- **Governance Only**: All feed management restricted
- **Public Updates**: Anyone can update prices (pays fee)
- **Time-locked Changes**: Prevents rushed modifications

### Price Security
- **Confidence Intervals**: Built-in uncertainty handling
- **Staleness Protection**: Publish time validation
- **Signature Verification**: Handled by Pyth Network
- **Conservative Estimates**: Subtracts confidence

### Integration Safety
- **Gas Efficiency**: Uses getPriceUnsafe for views
- **Fee Management**: Automatic fee calculation
- **Balance Checks**: Prevents failed updates
- **Batch Limits**: Max 20 updates per transaction

## Common Integration Patterns

### Price Update Automation
```python
# Off-chain service to keep prices fresh
def update_prices_if_stale():
    assets = [eth, btc, usdc]
    feed_ids = [get_feed_id(a) for a in assets]
    
    # Check if any price is stale
    for asset in assets:
        price, _ = pyth_prices.getPriceAndHasFeed(asset, 300)
        if price == 0:  # Stale or no price
            # Get fresh update data
            update = get_pyth_update(feed_ids)
            pyth_prices.updatePythPrice(update)
            break
```

### Multi-Asset Updates
```python
# Update multiple prices efficiently
updates = []
for feed_id in important_feeds:
    update = get_pyth_update([feed_id])
    updates.append(update)

# Submit all at once
num_updated = pyth_prices.updateManyPythPrices(updates[:20])
```

### Feed Migration
```python
# When Pyth provides new feed
# 1. Initiate update
pyth_prices.updatePriceFeed(
    asset.address,
    new_feed_id,
    sender=governance
)

# 2. Wait for timelock
boa.env.time_travel(seconds=timelock_duration)

# 3. Confirm update
pyth_prices.confirmPriceFeedUpdate(asset.address, sender=governance)
```

## Testing

For comprehensive test examples, see: [`tests/priceSources/test_pyth_prices.py`](../../tests/priceSources/test_pyth_prices.py)