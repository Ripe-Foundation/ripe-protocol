# Addys Technical Documentation

[📄 View Source Code](../../contracts/modules/Addys.vy)

## Overview

Addys is the centralized address resolution module for the Ripe Protocol, functioning as a sophisticated directory service that provides instant access to all protocol contracts. It eliminates redundant address storage across
contracts while maintaining consistency and reducing gas costs through intelligent caching.

**Core Functions**:
- **Protocol Directory**: Unified interface returning all protocol addresses through a single struct
- **Address Validation**: Comprehensive checks for core departments, vaults, and configuration contracts
- **Gas Optimization**: Batch retrieval and caching mechanisms minimize external calls and storage reads

The module uses lazy loading, struct-based batch retrieval, immutable RipeHq reference, and comprehensive helper functions, ensuring efficient and consistent address resolution throughout the protocol.

## Architecture & Design

Addys is designed as a lightweight, inheritable module that other contracts can use to access protocol addresses:

### Core Components
- **RipeHq Integration**: Direct connection to the master registry
- **Address Struct**: Efficient batch retrieval mechanism
- **Validation Logic**: Multi-layer permission checking
- **Helper Functions**: Specific getters for each protocol component

### Module Pattern
```vyper
# Other contracts inherit Addys like this:
initializes: addys
```

This gives the inheriting contract access to all internal functions and the ability to efficiently retrieve protocol addresses.

## System Architecture Diagram

```
+------------------------------------------------------------------------+
|                           Addys Module                                 |
+------------------------------------------------------------------------+
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Address Resolution Flow                       |  |
|  |                                                                  |  |
|  |  1. Contract inherits Addys module                               |  |
|  |     initializes: addys                                           |  |
|  |                                                                  |  |
|  |  2. Calls _getAddys() or specific getter                         |  |
|  |     - Single call returns all addresses                          |  |
|  |     - Or get specific address directly                           |  |
|  |                                                                  |  |
|  |  3. Addys queries RipeHq registry                                |  |
|  |     - Uses constant IDs for each component                       |  |
|  |     - Returns current addresses                                  |  |
|  |                                                                  |  |
|  |  4. Returns structured data                                      |  |
|  |     - Addys struct with all addresses                           |  |
|  |     - Or individual address                                      |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                     Validation Logic Flow                        |  |
|  |                                                                  |  |
|  |  _isValidRipeAddr(_addr) checks:                                 |  |
|  |                                                                  |  |
|  |  1. Core Department Check                                        |  |
|  |     └─> RipeHq.isValidAddr(_addr)                               |  |
|  |                                                                  |  |
|  |  2. Vault Check                                                  |  |
|  |     └─> VaultBook.isVaultBookAddr(_addr)                        |  |
|  |                                                                  |  |
|  |  3. Switchboard Check                                            |  |
|  |     └─> Switchboard.isSwitchboardAddr(_addr)                    |  |
|  |                                                                  |  |
|  |  Returns: True if any check passes                              |  |
|  +------------------------------------------------------------------+  |
+------------------------------------------------------------------------+
                                    |
                                    v
                         +--------------------+
                         |      RipeHq        |
                         | (Master Registry)  |
                         +--------------------+
                                    |
        +---------------------------+---------------------------+
        |                           |                           |
        v                           v                           v
+------------------+    +-------------------+    +------------------+
| Core Contracts   |    | Vault System      |    | Config System    |
| * Green Token    |    | * VaultBook       |    | * Switchboard    |
| * [CreditEngine](../core/CreditEngine.md)   |    | * Registered      |    | * Registered     |
| * [Teller](../core/Teller.md), etc.   |    |   Vaults          |    |   Configs        |
+------------------+    +-------------------+    +------------------+
```

## Data Structures

### Addys Struct
Complete protocol address collection:
```vyper
struct Addys:
    hq: address                  # RipeHq master registry
    greenToken: address          # Green stablecoin
    savingsGreen: address        # Savings Green token
    ripeToken: address           # RIPE governance token
    ledger: address              # Accounting system
    missionControl: address      # Configuration storage
    switchboard: address         # Config access control
    priceDesk: address           # Price oracle registry
    vaultBook: address           # Vault registry
    auctionHouse: address        # Liquidation auctions
    auctionHouseNft: address     # NFT auction system
    boardroom: address           # Governance execution
    bondRoom: address            # Bond sales
    creditEngine: address        # Lending engine
    endaoment: address           # Treasury management
    humanResources: address      # Rewards distribution
    lootbox: address             # Points & rewards
    teller: address              # User interface
```

## State Variables

### Immutable Variables
- `RIPE_HQ_FOR_ADDYS: immutable(address)` - RipeHq registry address

### Constants (Registry IDs)
- `GREEN_TOKEN_ID: constant(uint256) = 1`
- `SAVINGS_GREEN_ID: constant(uint256) = 2`
- `RIPE_TOKEN_ID: constant(uint256) = 3`
- `LEDGER_ID: constant(uint256) = 4`
- `MISSION_CONTROL_ID: constant(uint256) = 5`
- `SWITCHBOARD_ID: constant(uint256) = 6`
- `PRICE_DESK_ID: constant(uint256) = 7`
- `VAULT_BOOK_ID: constant(uint256) = 8`
- `AUCTION_HOUSE_ID: constant(uint256) = 9`
- `AUCTION_HOUSE_NFT_ID: constant(uint256) = 10`
- `BOARDROOM_ID: constant(uint256) = 11`
- `BOND_ROOM_ID: constant(uint256) = 12`
- `CREDIT_ENGINE_ID: constant(uint256) = 13`
- `ENDAOMENT_ID: constant(uint256) = 14`
- `HUMAN_RESOURCES_ID: constant(uint256) = 15`
- `LOOTBOX_ID: constant(uint256) = 16`
- `TELLER_ID: constant(uint256) = 17`

## Constructor

### `__init__`

Initializes the Addys module with the RipeHq registry address.

```vyper
@deploy
def __init__(_ripeHq: address):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_ripeHq` | `address` | RipeHq master registry contract |

#### Returns

*Constructor does not return any values*

#### Access

Called only during module initialization

#### Example Usage
```python
# When deploying a contract that uses Addys
contract = boa.load(
    "contracts/core/SomeContract.vy",
    ripe_hq.address  # Passed to Addys module
)
```

## Core Functions

### `getAddys`

Returns all protocol addresses in a single struct.

```vyper
@view
@external
def getAddys() -> Addys:
```

#### Returns

| Type | Description |
|------|-------------|
| `Addys` | Struct containing all protocol addresses |

#### Access

Public view function

#### Example Usage
```python
# Get all protocol addresses
addys = contract.getAddys()
green_token = addys.greenToken
credit_engine = addys.creditEngine
```

### `getRipeHq`

Returns the RipeHq registry address.

```vyper
@view
@external
def getRipeHq() -> address:
```

#### Returns

| Type | Description |
|------|-------------|
| `address` | RipeHq registry address |

#### Access

Public view function

## Internal Helper Functions

### `_getAddys`

Internal function to get all addresses with caching support.

```vyper
@view
@internal
def _getAddys(_addys: Addys = empty(Addys)) -> Addys:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_addys` | `Addys` | Optional cached addresses |

#### Returns

| Type | Description |
|------|-------------|
| `Addys` | Complete address struct |

#### Usage Pattern
```vyper
# In inheriting contract
def someFunction():
    a: Addys = self._getAddys()
    green: address = a.greenToken
```

### `_generateAddys`

Creates a fresh Addys struct by querying RipeHq.

```vyper
@view
@internal
def _generateAddys() -> Addys:
```

#### Returns

| Type | Description |
|------|-------------|
| `Addys` | Newly generated address struct |

## Token Address Functions

### `_getGreenToken`

Returns the Green token address.

```vyper
@view
@internal
def _getGreenToken() -> address:
```

### `_getSavingsGreen`

Returns the Savings Green token address.

```vyper
@view
@internal
def _getSavingsGreen() -> address:
```

### `_getRipeToken`

Returns the Ripe token address.

```vyper
@view
@internal
def _getRipeToken() -> address:
```

## Validation Functions

### `_isValidRipeAddr`

Comprehensive validation to check if an address is a valid protocol participant.

```vyper
@view
@internal
def _isValidRipeAddr(_addr: address) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_addr` | `address` | Address to validate |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if valid Ripe address |

#### Validation Logic
1. Checks if address is a core department in RipeHq
2. Checks if address is a registered vault in VaultBook
3. Checks if address is a registered config in Switchboard

#### Example Usage
```vyper
# In inheriting contract
if not self._isValidRipeAddr(msg.sender):
    raise "unauthorized"
```

### `_isSwitchboardAddr`

Checks if an address is registered in Switchboard.

```vyper
@view
@internal
def _isSwitchboardAddr(_addr: address) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_addr` | `address` | Address to check |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if registered in Switchboard |

## Department-Specific Functions

Each department has a pair of functions for getting its ID and address:

### Ledger Functions
- `_getLedgerId() -> uint256` - Returns LEDGER_ID (4)
- `_getLedgerAddr() -> address` - Returns Ledger address

### Mission Control Functions
- `_getMissionControlId() -> uint256` - Returns MISSION_CONTROL_ID (5)
- `_getMissionControlAddr() -> address` - Returns Mission Control address

### Switchboard Functions
- `_getSwitchboardId() -> uint256` - Returns SWITCHBOARD_ID (6)
- `_getSwitchboardAddr() -> address` - Returns Switchboard address

### PriceDesk Functions
- `_getPriceDeskId() -> uint256` - Returns PRICE_DESK_ID (7)
- `_getPriceDeskAddr() -> address` - Returns PriceDesk address

### VaultBook Functions
- `_getVaultBookId() -> uint256` - Returns VAULT_BOOK_ID (8)
- `_getVaultBookAddr() -> address` - Returns VaultBook address

### [AuctionHouse](../core/AuctionHouse.md) Functions
- `_getAuctionHouseId() -> uint256` - Returns AUCTION_HOUSE_ID (9)
- `_getAuctionHouseAddr() -> address` - Returns [AuctionHouse](../core/AuctionHouse.md) address

### AuctionHouseNft Functions
- `_getAuctionHouseNftId() -> uint256` - Returns AUCTION_HOUSE_NFT_ID (10)
- `_getAuctionHouseNftAddr() -> address` - Returns AuctionHouseNft address

### Boardroom Functions
- `_getBoardroomId() -> uint256` - Returns BOARDROOM_ID (11)
- `_getBoardroomAddr() -> address` - Returns Boardroom address

### [BondRoom](../core/BondRoom.md) Functions
- `_getBondRoomId() -> uint256` - Returns BOND_ROOM_ID (12)
- `_getBondRoomAddr() -> address` - Returns BondRoom address

### [CreditEngine](../core/CreditEngine.md) Functions
- `_getCreditEngineId() -> uint256` - Returns CREDIT_ENGINE_ID (13)
- `_getCreditEngineAddr() -> address` - Returns CreditEngine address

### [Endaoment](../core/Endaoment.md) Functions
- `_getEndaomentId() -> uint256` - Returns ENDAOMENT_ID (14)
- `_getEndaomentAddr() -> address` - Returns Endaoment address

### [HumanResources](../core/HumanResources.md) Functions
- `_getHumanResourcesId() -> uint256` - Returns HUMAN_RESOURCES_ID (15)
- `_getHumanResourcesAddr() -> address` - Returns HumanResources address

### [Lootbox](../core/Lootbox.md) Functions
- `_getLootboxId() -> uint256` - Returns LOOTBOX_ID (16)
- `_getLootboxAddr() -> address` - Returns Lootbox address

### [Teller](../core/Teller.md) Functions
- `_getTellerId() -> uint256` - Returns TELLER_ID (17)
- `_getTellerAddr() -> address` - Returns Teller address

## Usage Patterns

### Basic Address Retrieval
```vyper
# Get all addresses at once
a: Addys = self._getAddys()
green: address = a.greenToken
ledger: address = a.ledger
```

### Individual Address Retrieval
```vyper
# Get specific address directly
mc: address = self._getMissionControlAddr()
```

### Address Validation
```vyper
# Validate caller
assert self._isValidRipeAddr(msg.sender), "unauthorized"
```

### Caching Pattern
```vyper
# Pass cached addresses to avoid redundant lookups
def someFunction(_a: Addys = empty(Addys)):
    a: Addys = self._getAddys(_a)
    # Use addresses from 'a'
```

## Gas Optimization

The Addys module implements several gas optimization strategies:

1. **Batch Retrieval**: Getting all addresses in one struct is more efficient than individual calls
2. **Caching Support**: Functions accept pre-fetched addresses to avoid redundant lookups
3. **Immutable Storage**: RipeHq address stored as immutable reduces SLOAD costs
4. **Constant IDs**: Using constants for registry IDs eliminates storage reads

## Security Considerations

1. **Immutable Registry**: RipeHq address cannot be changed after deployment
2. **Registry Authority**: All addresses come from the authoritative RipeHq registry
3. **Validation Layers**: Multiple validation checks ensure comprehensive coverage
4. **No Direct State**: Module has no mutable state, reducing attack surface

## Testing

For comprehensive test examples, see: [`tests/modules/test_addys.py`](../../tests/modules/test_addys.py)