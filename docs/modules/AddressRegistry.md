# AddressRegistry Technical Documentation

[📄 View Source Code](../../contracts/modules/AddressRegistry.vy)

## Overview

AddressRegistry is a flexible registry module for managing protocol addresses within the Ripe ecosystem. It provides a standardized interface for registering, updating, and disabling addresses with built-in time-lock protection,
functioning as an authoritative directory that can be embedded into any contract.

**Core Features**:
- **Address Registration**: Sequential ID assignment with descriptive labels, ensuring unique contract registrations
- **Address Management**: Time-locked updates and disabling of registry entries for secure upgrades
- **Security Controls**: Two-step process for all changes with configurable delays, preventing rushed modifications

The module implements bidirectional mappings for efficient lookups, comprehensive query functions, configurable time-lock bounds with zero-timelock during setup, and promotes code reuse across different registry implementations.

## System Architecture Diagram

```
+-------------------------------------------------------------+
|                    AddressRegistry Module                   |
+-------------------------------------------------------------+
|                                                             |
|  +-------------------------------------------------------+  |
|  |                  Core Data Structures                 |  |
|  |                                                       |  |
|  |  * addrInfo: ID -> AddressInfo mapping                |  |
|  |  * addrToRegId: address -> ID reverse lookup          |  |
|  |  * numAddrs: sequential ID counter (starts at 1)      |  |
|  +-------------------------------------------------------+  |
|                                                             |
|  +-------------------------------------------------------+  |
|  |               Time-locked Operations                  |  |
|  |                                                       |  |
|  |  Add New Address:                                     |  |
|  |    pendingNewAddr: address -> PendingNewAddress       |  |
|  |                                                       |  |
|  |  Update Address:                                      |  |
|  |    pendingAddrUpdate: ID -> PendingAddressUpdate      |  |
|  |                                                       |  |
|  |  Disable Address:                                     |  |
|  |    pendingAddrDisable: ID -> PendingAddressDisable    |  |
|  +-------------------------------------------------------+  |
|                                                             |
|  +-------------------------------------------------------+  |
|  |                 Governance Integration                |  |
|  |                                                       |  |
|  |  * Uses LocalGov module for access control            |  |
|  |  * All modifications require governance permission    |  |
|  |  * Time-lock configuration requires governance        |  |
|  +-------------------------------------------------------+  |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                    Parent Contract (e.g., RipeHq)           |
|                                                             |
|  * Imports and initializes AddressRegistry                  |
|  * Exposes registry functions with access control           |
|  * Can add custom validation logic                          |
+-------------------------------------------------------------+
```

## Data Structures

### AddressInfo Struct
Stores complete information about a registered address:
```vyper
struct AddressInfo:
    addr: address           # The registered address
    version: uint256        # Version number (increments on updates)
    lastModified: uint256   # Timestamp of last modification
    description: String[64] # Human-readable description
```

### PendingNewAddress Struct
Tracks pending new address registrations:
```vyper
struct PendingNewAddress:
    description: String[64]    # Description for the new address
    initiatedBlock: uint256    # Block when addition was initiated
    confirmBlock: uint256      # Block when addition can be confirmed
```

### PendingAddressUpdate Struct
Tracks pending address updates:
```vyper
struct PendingAddressUpdate:
    newAddr: address          # The new address to update to
    initiatedBlock: uint256   # Block when update was initiated
    confirmBlock: uint256     # Block when update can be confirmed
```

### PendingAddressDisable Struct
Tracks pending address disabling:
```vyper
struct PendingAddressDisable:
    initiatedBlock: uint256   # Block when disable was initiated
    confirmBlock: uint256     # Block when disable can be confirmed
```

## State Variables

### Public State Variables
- `registryChangeTimeLock: uint256` - Current time-lock setting for registry changes in blocks
- `addrInfo: HashMap[uint256, AddressInfo]` - Maps registry ID to address information
- `addrToRegId: HashMap[address, uint256]` - Maps address to its registry ID
- `numAddrs: uint256` - Next available registry ID (starts at 1)
- `pendingNewAddr: HashMap[address, PendingNewAddress]` - Pending new address additions
- `pendingAddrUpdate: HashMap[uint256, PendingAddressUpdate]` - Pending address updates
- `pendingAddrDisable: HashMap[uint256, PendingAddressDisable]` - Pending address disables

### Immutable Variables
- `REGISTRY_STR: String[28]` - Registry description string
- `MIN_REG_TIME_LOCK: uint256` - Minimum allowed time-lock period
- `MAX_REG_TIME_LOCK: uint256` - Maximum allowed time-lock period

## Constructor

### `__init__`

Initializes the AddressRegistry module with time-lock parameters and a descriptive string.

```vyper
@deploy
def __init__(
    _minTimeLock: uint256,
    _maxTimeLock: uint256,
    _initialTimeLock: uint256,
    _registryStr: String[28],
):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_minTimeLock` | `uint256` | Minimum time-lock blocks allowed |
| `_maxTimeLock` | `uint256` | Maximum time-lock blocks allowed |
| `_initialTimeLock` | `uint256` | Initial time-lock setting (0 for setup phase) |
| `_registryStr` | `String[28]` | Description of this registry instance |

#### Returns

*Constructor does not return any values*

#### Access

Called only during deployment by parent contract

#### Example Usage
```python
# Initialize within RipeHq contract
registry.__init__(
    50,           # Min timelock
    500,          # Max timelock  
    0,            # Initial timelock (0 for setup)
    "RipeHq.vy"   # Registry description
)
```

**Example Output**: Registry initialized with ID counter at 1, ready for address registration

## Registry Query Functions

### `getRegistryDescription`

Returns the description string for this registry instance.

```vyper
@view
@external
def getRegistryDescription() -> String[28]:
```

#### Parameters

*Function has no parameters*

#### Returns

| Type | Description |
|------|-------------|
| `String[28]` | The registry description string |

#### Access

Public view function

#### Example Usage
```python
description = registry.getRegistryDescription()
# Returns: "RipeHq.vy"
```

### `isValidAddr`

Checks if an address is registered in the registry.

```vyper
@view
@external
def isValidAddr(_addr: address) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_addr` | `address` | The address to check |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if address is registered |

#### Access

Public view function

#### Example Usage
```python
is_registered = registry.isValidAddr(treasury.address)
# Returns: True if treasury is in registry
```

### `isValidRegId`

Checks if a registry ID is valid (exists).

```vyper
@view
@external
def isValidRegId(_regId: uint256) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_regId` | `uint256` | The registry ID to check |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if ID exists |

#### Access

Public view function

#### Example Usage
```python
is_valid = registry.isValidRegId(4)
# Returns: True if ID 4 has been assigned
```

### `getRegId`

Gets the registry ID for a given address.

```vyper
@view
@external
def getRegId(_addr: address) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_addr` | `address` | The address to look up |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | The registry ID (0 if not found) |

#### Access

Public view function

#### Example Usage
```python
reg_id = registry.getRegId(treasury.address)
# Returns: 4 (if treasury is ID 4)
```

### `getAddr`

Gets the address associated with a registry ID.

```vyper
@view
@external
def getAddr(_regId: uint256) -> address:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_regId` | `uint256` | The registry ID |

#### Returns

| Type | Description |
|------|-------------|
| `address` | The registered address (empty if not found) |

#### Access

Public view function

#### Example Usage
```python
addr = registry.getAddr(4)
# Returns: treasury.address
```

### `getAddrInfo`

Gets complete information about a registered address.

```vyper
@view
@external
def getAddrInfo(_regId: uint256) -> AddressInfo:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_regId` | `uint256` | The registry ID |

#### Returns

| Type | Description |
|------|-------------|
| `AddressInfo` | Complete address information struct |

#### Access

Public view function

#### Example Usage
```python
info = registry.getAddrInfo(4)
# Returns: AddressInfo with addr, version, lastModified, description
```

### `getAddrDescription`

Gets the description for a registered address.

```vyper
@view
@external
def getAddrDescription(_regId: uint256) -> String[64]:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_regId` | `uint256` | The registry ID |

#### Returns

| Type | Description |
|------|-------------|
| `String[64]` | The address description |

#### Access

Public view function

#### Example Usage
```python
description = registry.getAddrDescription(4)
# Returns: "Treasury Department"
```

### `getNumAddrs`

Gets the total number of registered addresses.

```vyper
@view
@external
def getNumAddrs() -> uint256:
```

#### Parameters

*Function has no parameters*

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Total registered addresses |

#### Access

Public view function

#### Example Usage
```python
count = registry.getNumAddrs()
# Returns: 5 (if 5 addresses registered)
```

### `getLastAddr`

Gets the most recently registered address.

```vyper
@view
@external
def getLastAddr() -> address:
```

#### Parameters

*Function has no parameters*

#### Returns

| Type | Description |
|------|-------------|
| `address` | The last registered address |

#### Access

Public view function

#### Example Usage
```python
last_addr = registry.getLastAddr()
# Returns: lootbox.address (if most recent)
```

### `getLastRegId`

Gets the ID of the most recently registered address.

```vyper
@view
@external
def getLastRegId() -> uint256:
```

#### Parameters

*Function has no parameters*

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | The last assigned registry ID |

#### Access

Public view function

#### Example Usage
```python
last_id = registry.getLastRegId()
# Returns: 5 (if 5 addresses registered)
```

## New Address Functions

### `isValidNewAddress`

Validates if an address can be added to the registry.

```vyper
@view
@external
def isValidNewAddress(_addr: address) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_addr` | `address` | The address to validate |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if address can be registered |

#### Access

Public view function

#### Example Usage
```python
can_add = registry.isValidNewAddress(new_dept.address)
# Returns: True if contract and not already registered
```

## Address Update Functions

### `isValidAddressUpdate`

Validates if an address update is valid.

```vyper
@view
@external
def isValidAddressUpdate(_regId: uint256, _newAddr: address) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_regId` | `uint256` | The registry ID to update |
| `_newAddr` | `address` | The new address |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if update is valid |

#### Access

Public view function

#### Example Usage
```python
can_update = registry.isValidAddressUpdate(4, new_treasury.address)
# Returns: True if valid ID, new address is contract and not registered
```

## Address Disable Functions

### `isValidAddressDisable`

Validates if an address can be disabled.

```vyper
@view
@external
def isValidAddressDisable(_regId: uint256) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_regId` | `uint256` | The registry ID to disable |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if can be disabled |

#### Access

Public view function

#### Example Usage
```python
can_disable = registry.isValidAddressDisable(5)
# Returns: True if valid ID with non-empty address
```

## Time-lock Configuration Functions

### `setRegistryTimeLock`

Updates the registry change time-lock period.

```vyper
@external
def setRegistryTimeLock(_numBlocks: uint256) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_numBlocks` | `uint256` | New time-lock period in blocks |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if successfully updated |

#### Access

Only callable by governance (via LocalGov module)

#### Events Emitted

- `RegistryTimeLockModified` - Contains previous and new time-lock values

#### Example Usage
```python
# Update time-lock to 200 blocks
success = registry.setRegistryTimeLock(
    200,
    sender=governance.address
)
assert success == True
```

**Example Output**: Time-lock updated, emits `RegistryTimeLockModified`

### `isValidRegistryTimeLock`

Validates if a proposed time-lock value is acceptable.

```vyper
@view
@external
def isValidRegistryTimeLock(_numBlocks: uint256) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_numBlocks` | `uint256` | Proposed time-lock value |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if time-lock value is valid |

#### Access

Public view function

#### Example Usage
```python
is_valid = registry.isValidRegistryTimeLock(200)
# Returns: True if within bounds and different from current
```

### `setRegistryTimeLockAfterSetup`

Special function to set time-lock after initial setup phase (when time-lock is 0).

```vyper
@external
def setRegistryTimeLockAfterSetup(_numBlocks: uint256 = 0) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_numBlocks` | `uint256` | Time-lock value (0 uses minimum) |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if successfully set |

#### Access

Only callable by governance when time-lock is currently 0

#### Events Emitted

- `RegistryTimeLockModified` - Contains previous (0) and new time-lock values

#### Example Usage
```python
# Complete setup with minimum time-lock
success = registry.setRegistryTimeLockAfterSetup(
    0,  # Use minimum
    sender=governance.address
)
```

**Example Output**: Time-lock set to minimum value

### `minRegistryTimeLock`

Returns the minimum allowed time-lock period.

```vyper
@view
@external
def minRegistryTimeLock() -> uint256:
```

#### Parameters

*Function has no parameters*

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Minimum time-lock in blocks |

#### Access

Public view function

#### Example Usage
```python
min_lock = registry.minRegistryTimeLock()
# Returns: 50 (example minimum)
```

### `maxRegistryTimeLock`

Returns the maximum allowed time-lock period.

```vyper
@view
@external
def maxRegistryTimeLock() -> uint256:
```

#### Parameters

*Function has no parameters*

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Maximum time-lock in blocks |

#### Access

Public view function

#### Example Usage
```python
max_lock = registry.maxRegistryTimeLock()
# Returns: 500 (example maximum)
```

## Internal Functions

Note: The AddressRegistry module includes several internal functions that are called by the parent contract (e.g., RipeHq) to perform registry operations with proper access control:

- `_startAddNewAddressToRegistry(_addr, _description)` - Initiates adding a new address
- `_confirmNewAddressToRegistry(_addr)` - Confirms a pending addition
- `_cancelNewAddressToRegistry(_addr)` - Cancels a pending addition
- `_startAddressUpdateToRegistry(_regId, _newAddr)` - Initiates an update
- `_confirmAddressUpdateToRegistry(_regId)` - Confirms a pending update
- `_cancelAddressUpdateToRegistry(_regId)` - Cancels a pending update
- `_startAddressDisableInRegistry(_regId)` - Initiates disabling
- `_confirmAddressDisableInRegistry(_regId)` - Confirms disabling
- `_cancelAddressDisableInRegistry(_regId)` - Cancels pending disable

These functions emit the following events:
- `NewAddressPending` - When new address addition is initiated
- `NewAddressConfirmed` - When new address is confirmed
- `NewAddressCancelled` - When pending addition is cancelled
- `AddressUpdatePending` - When update is initiated
- `AddressUpdateConfirmed` - When update is confirmed
- `AddressUpdateCancelled` - When update is cancelled
- `AddressDisablePending` - When disable is initiated
- `AddressDisableConfirmed` - When disable is confirmed
- `AddressDisableCancelled` - When disable is cancelled

## Testing

For comprehensive test examples, see: [`tests/registries/modules/test_address_registry.py`](../tests/registries/modules/test_address_registry.py)