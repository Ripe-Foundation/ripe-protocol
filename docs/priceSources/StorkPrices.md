# StorkPrices Technical Documentation

## Overview

StorkPrices serves as the integration layer for Stork Network's oracle services within the Ripe Protocol ecosystem. Think of it as a specialized connector that brings institutional-grade price feeds from Stork's network of data providers directly into the protocol. Similar to Pyth, Stork uses a pull-based oracle design where prices are published off-chain and brought on-chain only when needed, but with its own unique approach to temporal data representation and quantized values.

At its core, StorkPrices manages five fundamental responsibilities:

**1. Temporal Price Data**: Handles Stork's temporal numeric value system which provides prices with nanosecond-precision timestamps, enabling highly accurate time-based price tracking and staleness checks for financial applications.

**2. Quantized Value Processing**: Works with Stork's quantized value representation that provides prices in a standardized 18-decimal format, eliminating the need for complex decimal conversions while maintaining precision.

**3. Pull-Based Updates**: Implements the efficient pull oracle pattern where fresh price data is brought on-chain through signed payloads, with automatic fee calculation and payment to maintain oracle sustainability.

**4. Feed Management**: Maintains mappings between protocol assets and Stork feed IDs through a time-locked governance system, ensuring secure and deliberate oracle configuration changes.

**5. Batch Update Capability**: Supports updating multiple price feeds in a single transaction, reducing gas costs and improving efficiency for protocols that need to refresh many prices simultaneously.

For technical readers, StorkPrices implements the PriceSource interface with LocalGov for governance, TimeLock for configuration changes, and PriceSourceData for asset registry. It interfaces with Stork Network using the V1 API including getTemporalNumericValueUnsafeV1 for efficient price queries and updateTemporalNumericValuesV1 for on-chain updates. The contract processes TemporalNumericValue structs containing timestamp in nanoseconds and quantized values in 18 decimals. Unlike other oracles that require decimal conversions, Stork's quantized values are already normalized. The contract includes ETH balance management for update fees, batch processing for up to 20 simultaneous updates, and comprehensive event logging for transparency.

## Architecture & Dependencies

StorkPrices is built using a modular architecture with direct Stork Network integration:

### Core Module Dependencies
- **LocalGov**: Provides governance functionality with access control
- **Addys**: Address resolution for protocol contracts
- **PriceSourceData**: Asset registration and pause state management
- **TimeLock**: Time-locked changes for feed management

### External Integration
- **Stork Network**: Direct integration with Stork oracle contracts
- **Pull Oracle Model**: Off-chain data brought on-chain as needed
- **V1 API**: Uses Stork's first version temporal API

### Module Initialization
```vyper
initializes: gov
initializes: addys
initializes: priceData[addys := addys]
initializes: timeLock[gov := gov]
```

### Immutable Configuration
```vyper
STORK: immutable(address)  # Stork Network contract address
```

## Data Structures

### TemporalNumericValue Struct
Stork's price data format:
```vyper
struct TemporalNumericValue:
    timestampNs: uint64      # Timestamp in nanoseconds
    quantizedValue: uint256  # Price in 18 decimals
```

### PendingStorkFeed Struct
Tracks pending feed changes:
```vyper
struct PendingStorkFeed:
    actionId: uint256        # TimeLock action ID
    feedId: bytes32          # Stork feed identifier
```

## State Variables

### Feed Configuration
- `feedConfig: HashMap[address, bytes32]` - Maps assets to Stork feed IDs
- `pendingUpdates: HashMap[address, PendingStorkFeed]` - Pending changes

### Constants
- `MAX_PRICE_UPDATES: constant(uint256) = 20` - Maximum batch updates

### Inherited State
From modules:
- Governance state (LocalGov)
- Pause state and asset registry (PriceSourceData)
- TimeLock configuration

## System Architecture Diagram

```
+------------------------------------------------------------------------+
|                         StorkPrices Contract                          |
+------------------------------------------------------------------------+
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Price Retrieval Flow                          |  |
|  |                                                                  |  |
|  |  getPrice(asset):                                                |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ 1. Load Stork feed ID for asset                            │ |  |
|  |  │ 2. Call getTemporalNumericValueUnsafeV1()                  │ |  |
|  |  │ 3. Validate temporal data:                                 │ |  |
|  |  │    - quantizedValue != 0 (has price)                       │ |  |
|  |  │    - Convert timestamp from nanoseconds                    │ |  |
|  |  │    - Check staleness vs block.timestamp                    │ |  |
|  |  │ 4. Return quantized value directly                         │ |  |
|  |  │    (Already in 18 decimals - no conversion needed)         │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                 Temporal Data Representation                     |  |
|  |                                                                  |  |
|  |  Nanosecond Precision:                                          |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ timestampNs: 1,700,000,000,000,000,000                     │ |  |
|  |  │                    ↓                                        │ |  |
|  |  │ Unix timestamp: 1,700,000,000 (divide by 10^9)             │ |  |
|  |  │                                                             │ |  |
|  |  │ Benefits:                                                   │ |  |
|  |  │ • Ultra-precise timing for HFT applications                │ |  |
|  |  │ • Accurate ordering of rapid price updates                 │ |  |
|  |  │ • Compatible with institutional systems                    │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  |                                                                  |  |
|  |  Quantized Values:                                              |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ Price: $1,234.56789012345678                               │ |  |
|  |  │ Quantized: 1234567890123456780000 (18 decimals)            │ |  |
|  |  │                                                             │ |  |
|  |  │ No conversion needed - direct use in protocol              │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Pull Oracle Update Flow                       |  |
|  |                                                                  |  |
|  |  updateStorkPrice(payload):                                      |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ 1. Query update fee from Stork (getUpdateFeeV1)            │ |  |
|  |  │ 2. Verify contract ETH balance >= fee                      │ |  |
|  |  │ 3. Call updateTemporalNumericValuesV1 with fee             │ |  |
|  |  │ 4. Stork validates signatures and updates prices           │ |  |
|  |  │ 5. Emit StorkPriceUpdated event                            │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  |                                                                  |  |
|  |  Batch Updates:                                                  |  |
|  |  • Process up to 20 updates in one transaction                  |  |
|  |  • Stop on first failure to save gas                            |  |
|  |  • Return count of successful updates                           |  |
|  +------------------------------------------------------------------+  |
+------------------------------------------------------------------------+
                                    |
                                    ▼
+------------------------------------------------------------------------+
|                         Stork Network Oracle                          |
+------------------------------------------------------------------------+
| • Institutional-grade price feeds from professional providers         |
| • Nanosecond timestamp precision for accurate timing                  |
| • Pre-normalized 18-decimal quantized values                          |
| • Pull-based architecture for cost efficiency                         |
| • Cryptographic signatures ensure data authenticity                   |
+------------------------------------------------------------------------+
```

## Constructor

### `__init__`

Initializes StorkPrices with governance settings and Stork Network address.

```vyper
@deploy
def __init__(
    _ripeHq: address,
    _tempGov: address,
    _stork: address,
    _minPriceChangeTimeLock: uint256,
    _maxPriceChangeTimeLock: uint256,
):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_ripeHq` | `address` | RipeHq contract for protocol integration |
| `_tempGov` | `address` | Initial temporary governance address |
| `_stork` | `address` | Stork Network contract address |
| `_minPriceChangeTimeLock` | `uint256` | Minimum timelock for feed changes |
| `_maxPriceChangeTimeLock` | `uint256` | Maximum timelock for feed changes |

#### Deployment Requirements
- Stork Network address must not be empty
- Contract requires ETH balance for update fees

#### Example Usage
```python
stork_prices = boa.load(
    "contracts/priceSources/StorkPrices.vy",
    ripe_hq.address,
    deployer.address,
    stork_network.address,  # Chain-specific deployment
    100,   # Min 100 blocks timelock
    1000   # Max 1000 blocks timelock
)

# Fund contract for update fees
deployer.transfer(stork_prices.address, eth_amount)
```

## Core Price Functions

### `getPrice`

Retrieves the current price for an asset from Stork Network.

```vyper
@view
@external
def getPrice(_asset: address, _staleTime: uint256 = 0, _priceDesk: address = empty(address)) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_asset` | `address` | Asset to get price for |
| `_staleTime` | `uint256` | Maximum age for price data (0 accepts any) |
| `_priceDesk` | `address` | Not used in Stork implementation |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Quantized price value (0 if invalid) |

#### Process Flow
1. **Feed Lookup**: Gets Stork feed ID for asset
2. **Temporal Query**: Calls getTemporalNumericValueUnsafeV1
3. **Validation**: Checks quantizedValue != 0
4. **Time Conversion**: Nanoseconds to seconds
5. **Staleness Check**: Compare with block timestamp

#### Example Usage
```python
# Get ETH price
eth_price = stork_prices.getPrice(eth.address)
print(f"ETH: ${eth_price / 10**18}")

# Get price with 1 minute staleness
btc_price = stork_prices.getPrice(
    btc.address,
    60  # 1 minute maximum age
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

### `updateStorkPrice`

Brings fresh price data on-chain for configured feeds.

```vyper
@external
def updateStorkPrice(_payload: Bytes[2048]) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_payload` | `Bytes[2048]` | Signed price update from Stork |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if update successful |

#### Process
1. **Fee Query**: Gets required fee from Stork
2. **Balance Check**: Ensures sufficient ETH
3. **Update Call**: Submits payload with fee
4. **Event Logging**: Records update details

#### Example Usage
```python
# Get update from Stork API
update_payload = fetch_stork_update(feed_ids)

# Submit on-chain
success = stork_prices.updateStorkPrice(update_payload)
```

### `updateManyStorkPrices`

Updates multiple price feeds efficiently.

```vyper
@external
def updateManyStorkPrices(_payloads: DynArray[Bytes[2048], MAX_PRICE_UPDATES]) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_payloads` | `DynArray[Bytes[2048], MAX_PRICE_UPDATES]` | Up to 20 updates |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Number of successful updates |

Processes updates sequentially, stopping on first failure.

## Feed Management Functions

### `addNewPriceFeed`

Initiates addition of a new Stork price feed.

```vyper
@external
def addNewPriceFeed(_asset: address, _feedId: bytes32) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_asset` | `address` | Asset to add price feed for |
| `_feedId` | `bytes32` | Stork Network feed identifier |

#### Access

Only callable by governance

#### Validation
- Asset must not have existing feed
- Feed must return valid temporal data
- Asset address must be valid

#### Events Emitted

- `NewStorkFeedPending` - Contains feed ID and timelock details

### `confirmNewPriceFeed`

Confirms pending feed addition after timelock.

```vyper
@external
def confirmNewPriceFeed(_asset: address) -> bool:
```

#### Process Flow
1. **Re-validation**: Ensures feed still valid
2. **Timelock Check**: Verifies time elapsed
3. **Configuration Save**: Stores feed mapping
4. **Asset Registration**: Adds to PriceSourceData

#### Events Emitted

- `NewStorkFeedAdded` - Confirms feed activation

### `updatePriceFeed`

Updates existing feed to new Stork feed ID.

```vyper
@external
def updatePriceFeed(_asset: address, _feedId: bytes32) -> bool:
```

Similar timelock process as additions.

### `disablePriceFeed`

Removes a price feed from the system.

```vyper
@external
def disablePriceFeed(_asset: address) -> bool:
```

Also requires time-locked confirmation.

## ETH Balance Management

### `recoverEthBalance`

Withdraws ETH from contract.

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

Used to recover excess ETH from update fees.

## Temporal Data Handling

### Timestamp Conversion

Stork uses nanosecond precision:
```vyper
# Convert nanoseconds to seconds
publishTime = convert(data.timestampNs, uint256) // 1_000_000_000
```

Benefits:
- Microsecond accuracy for HFT
- Precise event ordering
- Institutional compatibility

### Staleness Validation

```vyper
if _staleTime != 0 and block.timestamp - publishTime > _staleTime:
    return 0  # Price too stale
```

Uses publish time for accurate staleness checks.

## Validation Functions

### `isValidNewFeed`

Validates new feed configuration.

```vyper
@view
@external
def isValidNewFeed(_asset: address, _feedId: bytes32) -> bool:
```

#### Validation Checks
1. **No Existing Feed**: Asset must be new
2. **Valid Address**: Non-empty asset
3. **Feed Exists**: Returns temporal data
4. **Has Timestamp**: timestampNs != 0

### `isValidUpdateFeed`

Additional checks for updates:
- New feed must differ from current
- Asset must have existing feed

### `isValidDisablePriceFeed`

Ensures:
- Feed exists for asset
- Asset registered in PriceSourceData

## Events

### Feed Management Events
- `NewStorkFeedPending` - New feed initiated
- `NewStorkFeedAdded` - Feed confirmed
- `NewStorkFeedCancelled` - Addition cancelled
- `StorkFeedUpdatePending` - Update initiated
- `StorkFeedUpdated` - Update confirmed
- `StorkFeedUpdateCancelled` - Update cancelled
- `DisableStorkFeedPending` - Removal initiated
- `StorkFeedDisabled` - Feed removed
- `DisableStorkFeedCancelled` - Removal cancelled

### Operational Events
- `StorkPriceUpdated` - Price update submitted
- `EthRecoveredFromStork` - ETH withdrawn

All events include addresses, feed IDs, and action details.

## Security Considerations

### Access Control
- **Governance Only**: Feed management restricted
- **Public Updates**: Anyone can update (pays fee)
- **Time-locked Changes**: Prevents hasty decisions

### Data Integrity
- **Temporal Validation**: Timestamp verification
- **Zero Value Check**: Rejects invalid prices
- **Signature Verification**: Handled by Stork
- **Gas Efficiency**: Unsafe methods for views

### Integration Safety
- **Simple Decimals**: No conversion needed
- **Fee Management**: Automatic calculation
- **Balance Protection**: Checks before updates
- **Batch Limits**: Maximum 20 updates

## Common Integration Patterns

### Automated Updates
```python
# Service to maintain fresh prices
async def maintain_prices():
    assets = get_tracked_assets()
    feed_ids = [get_stork_feed_id(a) for a in assets]
    
    while True:
        # Check staleness
        for asset in assets:
            price = stork_prices.getPrice(asset, 300)  # 5 min
            if price == 0:
                # Get fresh update
                payload = await fetch_stork_update(feed_ids)
                stork_prices.updateStorkPrice(payload)
                break
        
        await asyncio.sleep(60)  # Check every minute
```

### Batch Processing
```python
# Update multiple feeds efficiently
def update_all_feeds(feed_ids):
    payloads = []
    
    # Get updates for each feed
    for feed_id in feed_ids:
        update = fetch_stork_update([feed_id])
        payloads.append(update)
    
    # Submit batch (max 20)
    if len(payloads) > 0:
        count = stork_prices.updateManyStorkPrices(payloads[:20])
        print(f"Updated {count} feeds")
```

### Feed Migration
```python
# Migrate to new Stork feed
def migrate_feed(asset, old_feed_id, new_feed_id):
    # 1. Initiate update
    stork_prices.updatePriceFeed(
        asset,
        new_feed_id,
        sender=governance
    )
    
    # 2. Wait for timelock
    wait_blocks(timelock_duration)
    
    # 3. Confirm update
    stork_prices.confirmPriceFeedUpdate(
        asset,
        sender=governance
    )
```

## Advantages of Stork Integration

### Simplified Decimals
- All values in 18 decimals
- No conversion logic needed
- Reduced complexity and gas costs

### Nanosecond Precision
- Ideal for high-frequency trading
- Accurate event sequencing
- Professional-grade timestamps

### Efficient Updates
- Pull-based model saves gas
- Batch updates reduce costs
- Pay only for what you use

## Testing

For comprehensive test examples, see: [`tests/priceSources/test_stork_prices.py`](../../tests/priceSources/test_stork_prices.py)