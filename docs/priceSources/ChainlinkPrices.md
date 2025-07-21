# ChainlinkPrices Technical Documentation

## Overview

ChainlinkPrices serves as the primary oracle integration for real-time asset pricing within the Ripe Protocol ecosystem. Think of it as the protocol's connection to the most widely-used decentralized oracle network, providing reliable and tamper-resistant price feeds for cryptocurrencies and other digital assets. Unlike traditional price feeds that rely on single sources, Chainlink aggregates data from multiple providers to ensure accuracy and resist manipulation.

At its core, ChainlinkPrices manages four fundamental responsibilities:

**1. Direct Oracle Integration**: Connects directly to Chainlink price feed contracts to retrieve latest price data, including validation of round IDs, timestamps, and answer values to ensure data integrity before using prices in the protocol.

**2. Cross-Rate Conversions**: Supports assets priced in ETH or BTC by automatically converting to USD using additional Chainlink feeds, enabling pricing for a wider range of assets that may not have direct USD pairs.

**3. Decimal Normalization**: Handles the varying decimal formats used by different Chainlink feeds, normalizing all prices to 18 decimals for consistent use throughout the Ripe Protocol.

**4. Staleness Protection**: Implements configurable staleness checks that reject prices older than acceptable thresholds, protecting the protocol from using outdated data during oracle outages or market disruptions.

For technical readers, ChainlinkPrices implements the standard Chainlink aggregator interface with `latestRoundData()` calls, validates all oracle responses including round ID progression and timestamp checks, supports both direct USD feeds and cross-rate calculations through ETH/USD or BTC/USD conversions, normalizes varying decimal formats (commonly 8 decimals) to the protocol's standard 18 decimals, includes time-locked governance for all feed additions and updates, and provides special handling for core assets (ETH, WETH, BTC) that cannot be disabled. The contract is designed to be the most reliable and battle-tested price source for the protocol.

## Architecture & Dependencies

ChainlinkPrices is built using a modular architecture with direct oracle integration:

### Core Module Dependencies
- **LocalGov**: Provides governance functionality with access control
- **Addys**: Address resolution for protocol contracts
- **PriceSourceData**: Asset registration and pause state management
- **TimeLock**: Time-locked changes for feed management

### External Integrations
- **Chainlink Oracles**: Direct integration with Chainlink aggregator contracts
- **MissionControl**: Retrieves global price staleness configuration

### Module Initialization
```vyper
initializes: gov
initializes: addys
initializes: priceData[addys := addys]
initializes: timeLock[gov := gov]
```

### Immutable Assets
```vyper
WETH: immutable(address)  # Wrapped ETH address
ETH: immutable(address)   # Native ETH representation
BTC: immutable(address)   # Bitcoin representation
```

## Data Structures

### ChainlinkRound Struct
Raw data returned from Chainlink oracles:
```vyper
struct ChainlinkRound:
    roundId: uint80         # Unique round identifier
    answer: int256          # Price value (can be negative)
    startedAt: uint256      # Round start timestamp
    updatedAt: uint256      # Last update timestamp
    answeredInRound: uint80 # Round when answer was computed
```

### ChainlinkConfig Struct
Configuration for each asset's price feed:
```vyper
struct ChainlinkConfig:
    feed: address           # Chainlink aggregator address
    decimals: uint256       # Feed's decimal places
    needsEthToUsd: bool     # Convert ETH price to USD
    needsBtcToUsd: bool     # Convert BTC price to USD
```

### PendingChainlinkConfig Struct
Tracks pending changes during timelock:
```vyper
struct PendingChainlinkConfig:
    actionId: uint256       # TimeLock action ID
    config: ChainlinkConfig # New configuration
```

## State Variables

### Feed Configuration
- `feedConfig: HashMap[address, ChainlinkConfig]` - Active Chainlink configurations
- `pendingUpdates: HashMap[address, PendingChainlinkConfig]` - Pending changes

### Constants
- `NORMALIZED_DECIMALS: constant(uint256) = 18` - Standard decimal format

### Inherited State
From modules:
- Governance state (LocalGov)
- Pause state and asset registry (PriceSourceData)
- TimeLock configuration

## System Architecture Diagram

```
+------------------------------------------------------------------------+
|                      ChainlinkPrices Contract                         |
+------------------------------------------------------------------------+
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Price Retrieval Flow                          |  |
|  |                                                                  |  |
|  |  getPrice(asset):                                                |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ 1. Load ChainlinkConfig for asset                          │ |  |
|  |  │ 2. Call Chainlink oracle's latestRoundData()               │ |  |
|  |  │ 3. Validate oracle response:                               │ |  |
|  |  │    - answer > 0 (has valid price)                          │ |  |
|  |  │    - roundId > 0 and answeredInRound >= roundId            │ |  |
|  |  │    - updatedAt <= current time (not future)                │ |  |
|  |  │    - updatedAt within staleness threshold                  │ |  |
|  |  │ 4. Normalize decimals to 18                                │ |  |
|  |  │ 5. Apply cross-rate conversion if needed:                  │ |  |
|  |  │    - ETH/USD: price * ETH_USD_price                        │ |  |
|  |  │    - BTC/USD: price * BTC_USD_price                        │ |  |
|  |  │ 6. Return final normalized price                           │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Oracle Validation Logic                       |  |
|  |                                                                  |  |
|  |  Data Quality Checks:                                            |  |
|  |  • answer > 0: Ensures price is positive                        |  |
|  |  • roundId > 0: Valid round identifier                          |  |
|  |  • answeredInRound >= roundId: Answer is fresh                  |  |
|  |  • updatedAt <= block.timestamp: No future timestamps           |  |
|  |  • decimals <= 18: Supported decimal range                      |  |
|  |                                                                  |  |
|  |  Staleness Protection:                                           |  |
|  |  if (staleTime != 0 && block.timestamp - updatedAt > staleTime):|  |
|  |      return 0  // Price too old                                 |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Cross-Rate Conversion                         |  |
|  |                                                                  |  |
|  |  Direct USD Feeds:                                               |  |
|  |  ┌─────────────┐                                                 |  |
|  |  │   Asset     │──────> Chainlink ──────> USD Price             |  |
|  |  └─────────────┘         Oracle                                  |  |
|  |                                                                  |  |
|  |  Cross-Rate Feeds (needsEthToUsd):                              |  |
|  |  ┌─────────────┐        ┌─────────────┐                         |  |
|  |  │   Asset     │────┐   │   ETH/USD   │                         |  |
|  |  └─────────────┘    │   └─────────────┘                         |  |
|  |          │          │          │                                 |  |
|  |          ▼          │          ▼                                 |  |
|  |     Asset/ETH   ────┴───>  USD Price                            |  |
|  |      Oracle                                                      |  |
|  |                                                                  |  |
|  |  Cross-Rate Feeds (needsBtcToUsd):                              |  |
|  |  Similar pattern but using BTC/USD conversion                    |  |
|  +------------------------------------------------------------------+  |
+------------------------------------------------------------------------+
                                    |
                                    ▼
+------------------------------------------------------------------------+
|                        Chainlink Oracle Network                       |
+------------------------------------------------------------------------+
| • Decentralized price aggregation from multiple data providers        |
| • Cryptographic signatures and reputation system                      |
| • Regular updates based on price deviation or heartbeat               |
| • Industry standard for DeFi price feeds                              |
+------------------------------------------------------------------------+
```

## Constructor

### `__init__`

Initializes ChainlinkPrices with core asset feeds and governance settings.

```vyper
@deploy
def __init__(
    _ripeHq: address,
    _tempGov: address,
    _minPriceChangeTimeLock: uint256,
    _maxPriceChangeTimeLock: uint256,
    _wethAddr: address,
    _ethAddr: address,
    _btcAddr: address,
    _ethUsdFeed: address,
    _btcUsdFeed: address,
):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_ripeHq` | `address` | RipeHq contract for protocol integration |
| `_tempGov` | `address` | Initial temporary governance address |
| `_minPriceChangeTimeLock` | `uint256` | Minimum timelock for feed changes |
| `_maxPriceChangeTimeLock` | `uint256` | Maximum timelock for feed changes |
| `_wethAddr` | `address` | Wrapped ETH token address |
| `_ethAddr` | `address` | ETH representation address |
| `_btcAddr` | `address` | BTC representation address |
| `_ethUsdFeed` | `address` | Chainlink ETH/USD feed address |
| `_btcUsdFeed` | `address` | Chainlink BTC/USD feed address |

#### Deployment Behavior
- Sets ETH/USD feed for both ETH and WETH if provided
- Sets BTC/USD feed for BTC if provided
- Validates feeds during deployment
- Registers default assets in PriceSourceData

#### Example Usage
```python
chainlink_prices = boa.load(
    "contracts/priceSources/ChainlinkPrices.vy",
    ripe_hq.address,
    deployer.address,
    100,   # Min 100 blocks timelock
    1000,  # Max 1000 blocks timelock
    weth_token.address,
    eth_address,
    wbtc_token.address,
    "0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419",  # ETH/USD Mainnet
    "0xF4030086522a5bEEa4988F8cA5B36dbC97BeE88c"   # BTC/USD Mainnet
)
```

## Core Price Functions

### `getPrice`

Retrieves the current price for an asset from Chainlink oracles.

```vyper
@view
@external
def getPrice(_asset: address, _staleTime: uint256 = 0, _priceDesk: address = empty(address)) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_asset` | `address` | Asset to get price for |
| `_staleTime` | `uint256` | Maximum age for price data (0 uses default) |
| `_priceDesk` | `address` | Not used in Chainlink implementation |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Normalized price in 18 decimals (0 if invalid) |

#### Process Flow
1. **Config Load**: Retrieves ChainlinkConfig for asset
2. **Oracle Call**: Queries Chainlink aggregator
3. **Validation**: Checks answer validity and staleness
4. **Normalization**: Converts to 18 decimals
5. **Cross-Rate**: Applies ETH/USD or BTC/USD if needed

#### Example Usage
```python
# Get USDC price (direct USD feed)
usdc_price = chainlink_prices.getPrice(usdc.address)

# Get token priced in ETH (needs conversion)
token_price = chainlink_prices.getPrice(
    token.address,
    3600  # 1 hour staleness threshold
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

### `getChainlinkData`

Direct access to Chainlink oracle data with normalization.

```vyper
@view
@external
def getChainlinkData(_feed: address, _decimals: uint256, _staleTime: uint256 = 0) -> uint256:
```

Useful for debugging or accessing feeds not registered in the contract.

## Feed Management Functions

### `addNewPriceFeed`

Initiates addition of a new Chainlink price feed.

```vyper
@external
def addNewPriceFeed(
    _asset: address, 
    _newFeed: address, 
    _needsEthToUsd: bool = False,
    _needsBtcToUsd: bool = False,
) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_asset` | `address` | Asset to add price feed for |
| `_newFeed` | `address` | Chainlink aggregator address |
| `_needsEthToUsd` | `bool` | Convert ETH price to USD |
| `_needsBtcToUsd` | `bool` | Convert BTC price to USD |

#### Access

Only callable by governance

#### Validation
- Feed must return valid price data
- Cannot set both ETH and BTC conversion
- Asset must not already have a feed

#### Events Emitted

- `NewChainlinkFeedPending` - Contains feed details and confirmation block

#### Example Usage
```python
# Add direct USD feed
chainlink_prices.addNewPriceFeed(
    dai.address,
    "0xAed0c38402a5d19df6E4c03F4E2DceD6e29c1ee9",  # DAI/USD
    sender=governance
)

# Add ETH-denominated feed
chainlink_prices.addNewPriceFeed(
    token.address,
    token_eth_feed.address,
    True,  # needsEthToUsd
    False,
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
1. **Re-validation**: Ensures feed still returns valid data
2. **Timelock Check**: Verifies sufficient time passed
3. **Configuration Save**: Stores feed config
4. **Asset Registration**: Adds to PriceSourceData

#### Events Emitted

- `NewChainlinkFeedAdded` - Confirms feed is active

### `updatePriceFeed`

Updates existing feed configuration.

```vyper
@external
def updatePriceFeed(
    _asset: address, 
    _newFeed: address, 
    _needsEthToUsd: bool = False,
    _needsBtcToUsd: bool = False,
) -> bool:
```

Used when Chainlink migrates to new aggregator addresses.

### `disablePriceFeed`

Removes a price feed (except core assets).

```vyper
@external
def disablePriceFeed(_asset: address) -> bool:
```

#### Restrictions
- Cannot disable ETH, WETH, or BTC feeds
- Requires time-locked confirmation

## Oracle Interaction

### Internal Price Retrieval

```vyper
def _getChainlinkData(_feed: address, _decimals: uint256, _staleTime: uint256) -> uint256:
    oracle = ChainlinkFeed(_feed).latestRoundData()
    
    # Validation checks
    if oracle.answer <= 0:
        return 0  # No valid price
    if oracle.updatedAt > block.timestamp:
        return 0  # Future timestamp
    if oracle.roundId == 0:
        return 0  # Invalid round
    if oracle.answeredInRound < oracle.roundId:
        return 0  # Stale answer
    
    # Staleness check
    if _staleTime != 0 and block.timestamp - oracle.updatedAt > _staleTime:
        return 0  # Too old
    
    # Decimal normalization
    price = uint256(oracle.answer)
    if _decimals < 18:
        price = price * 10**(18 - _decimals)
    
    return price
```

### Cross-Rate Conversion

```vyper
def _getPrice(...) -> uint256:
    price = _getChainlinkData(feed, decimals, staleTime)
    
    if _needsEthToUsd:
        ethPrice = _getChainlinkData(ethFeed, ethDecimals, staleTime)
        price = price * ethPrice / 10**18
    
    elif _needsBtcToUsd:
        btcPrice = _getChainlinkData(btcFeed, btcDecimals, staleTime)
        price = price * btcPrice / 10**18
    
    return price
```

## Validation Functions

### `isValidNewFeed`

Validates new feed configuration.

```vyper
@view
@external
def isValidNewFeed(_asset: address, _newFeed: address, _decimals: uint256, _needsEthToUsd: bool, _needsBtcToUsd: bool) -> bool:
```

#### Validation Checks
1. **No Existing Feed**: Asset must not have active feed
2. **Valid Addresses**: Neither asset nor feed can be empty
3. **Single Conversion**: Cannot use both ETH and BTC conversion
4. **Working Feed**: Must return valid price with staleness check

### `isValidUpdateFeed`

Validates feed updates.

Additional checks:
- New feed must differ from current
- Asset must have existing feed

### `isValidDisablePriceFeed`

Validates feed removal.

Checks:
- Feed must exist
- Cannot disable core assets (ETH, WETH, BTC)

## Staleness Management

### Default Staleness

Retrieved from MissionControl:
```vyper
staleTime = MissionControl(missionControl).getPriceStaleTime()
```

### Per-Call Staleness

Can override default:
```python
# Use custom 5 minute staleness
price = chainlink_prices.getPrice(asset.address, 300)
```

### Staleness in Validation

Feed validation uses MissionControl staleness to ensure feeds work with protocol settings.

## Security Considerations

### Oracle Security
- **Round ID Validation**: Ensures answers are from current round
- **Timestamp Checks**: Prevents future-dated prices
- **Positive Price**: Rejects zero or negative prices
- **Answer Freshness**: Uses answeredInRound for staleness

### Access Control
- **Governance Only**: All feed management restricted
- **Time-locked Changes**: Prevents rushed modifications
- **Core Asset Protection**: ETH/WETH/BTC cannot be disabled

### Cross-Rate Security
- **Single Conversion**: Prevents compound conversion errors
- **Dependency Validation**: Ensures ETH/BTC feeds exist
- **Atomic Calculation**: No partial conversions

### Integration Safety
- **Decimal Handling**: Safe normalization to 18 decimals
- **Overflow Protection**: Vyper's built-in checks
- **Zero Returns**: Invalid data returns 0, not reverts

## Common Integration Patterns

### Multi-Asset Pricing
```python
# Get prices for multiple assets
assets = [dai.address, usdc.address, weth.address]
prices = []

for asset in assets:
    price, has_feed = chainlink_prices.getPriceAndHasFeed(asset)
    if has_feed:
        prices.append(price)
    else:
        # Handle missing feed
        pass
```

### Cross-Rate Setup
```python
# Setup token with ETH pricing
# 1. Add ETH-denominated feed
chainlink_prices.addNewPriceFeed(
    token.address,
    token_eth_feed.address,
    True,  # needsEthToUsd
    sender=governance
)

# 2. Wait for timelock
boa.env.time_travel(seconds=timelock_duration)

# 3. Confirm feed
chainlink_prices.confirmNewPriceFeed(token.address, sender=governance)
```

### Feed Migration
```python
# When Chainlink updates aggregator
# 1. Initiate update
chainlink_prices.updatePriceFeed(
    asset.address,
    new_aggregator.address,
    sender=governance
)

# 2. Confirm after timelock
chainlink_prices.confirmPriceFeedUpdate(asset.address, sender=governance)
```

## Events

### Feed Management Events
- `NewChainlinkFeedPending` - New feed initiated
- `NewChainlinkFeedAdded` - Feed confirmed and active
- `NewChainlinkFeedCancelled` - Pending feed cancelled
- `ChainlinkFeedUpdatePending` - Update initiated
- `ChainlinkFeedUpdated` - Update confirmed
- `ChainlinkFeedUpdateCancelled` - Update cancelled
- `DisableChainlinkFeedPending` - Removal initiated
- `ChainlinkFeedDisabled` - Feed removed
- `DisableChainlinkFeedCancelled` - Removal cancelled

All events include relevant addresses, configuration flags, and timelock details.

## Testing

For comprehensive test examples, see: [`tests/priceSources/test_chainlink_prices.py`](../../tests/priceSources/test_chainlink_prices.py)