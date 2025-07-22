# Switchboard Technical Documentation

[📄 View Source Code](../../contracts/registries/Switchboard.vy)

## Overview

Switchboard is the authorization gateway controlling all protocol configuration changes in Ripe Protocol. It determines which contracts can modify Mission Control settings, creating a secure two-layer system where governance controls Switchboard access, and Switchboard controls configuration updates.

**Core Functions**:
- **Configuration Authority**: Registers approved contracts that can update protocol parameters
- **Parameter Control**: Guards access to critical settings including collateral ratios, liquidation thresholds, rewards distribution, and oracle configurations
- **Blacklist Gateway**: Manages token freeze/unfreeze operations through vetted contracts

Built on LocalGov and AddressRegistry modules, Switchboard enforces that only registered contracts can call Mission Control setters. This architecture creates an audit trail of authorized configurators while preventing unauthorized parameter changes through strict access control and emergency pause capabilities.

## Architecture & Modules

Switchboard is built using a modular architecture that inherits functionality from multiple base modules:

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
- **Purpose**: Manages the registry of configuration contract addresses
- **Documentation**: See [AddressRegistry Technical Documentation](../modules/AddressRegistry.md)
- **Key Features**:
  - Sequential registry ID assignment for config contracts
  - Time-locked address additions, updates, and disabling
  - Descriptive labels for each configuration contract
- **Exported Interface**: All registry functions via `registry.__interface__`

### Addys Module

- **Location**: `contracts/modules/Addys.vy`
- **Purpose**: Provides RipeHq integration for address lookups
- **Documentation**: See [Addys Technical Documentation](../modules/Addys.md)
- **Key Features**:
  - Access to RipeHq address
  - Protocol address validation
- **Exported Interface**: Address utilities via `addys.__interface__`

### DeptBasics Module

- **Location**: `contracts/modules/DeptBasics.vy`
- **Purpose**: Provides department-level basic functionality
- **Documentation**: See [DeptBasics Technical Documentation](../modules/DeptBasics.md)
- **Key Features**:
  - Pause mechanism
  - Department interface compliance
  - No minting capabilities (disabled for Switchboard)
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
+---------------------------------------------------------------------+
|                       Switchboard Contract                          |
+---------------------------------------------------------------------+
|                                                                     |
|  +-----------------------------------------------------------------+|
|  |              Configuration Authorization Flow                    ||
|  |                                                                 ||
|  |  1. Configuration Contract Registration                         ||
|  |     - Contract added to registry with time-lock                 ||
|  |     - Assigned unique registry ID                               ||
|  |     - Gains authority to modify protocol config                 ||
|  |                                                                 ||
|  |  2. Protocol Configuration Update Flow                          ||
|  |     +--------------------+                                      ||
|  |     | Config Manager     |                                      ||
|  |     | (Registered in     |                                      ||
|  |     |  Switchboard)      |                                      ||
|  |     +--------+-----------+                                      ||
|  |              |                                                  ||
|  |              | Calls setter functions                           ||
|  |              v                                                  ||
|  |     +--------------------+                                      ||
|  |     | Mission Control    |                                      ||
|  |     | - Validates caller |                                      ||
|  |     |   via Switchboard  |                                      ||
|  |     | - Updates config:  |                                      ||
|  |     |   * GenConfig      |                                      ||
|  |     |   * DebtConfig     |                                      ||
|  |     |   * RewardsConfig  |                                      ||
|  |     |   * AssetConfig    |                                      ||
|  |     |   * VaultConfig    |                                      ||
|  |     |   * PriceConfig    |                                      ||
|  |     +--------------------+                                      ||
|  |                                                                 ||
|  |  3. Token Blacklist Update Flow                                 ||
|  |     +--------------------+                                      ||
|  |     | Blacklist Manager  |                                      ||
|  |     | (Registered)       |                                      ||
|  |     +--------+-----------+                                      ||
|  |              |                                                  ||
|  |              v                                                  ||
|  |     +--------------------+                                      ||
|  |     | Switchboard        |                                      ||
|  |     | - Verify caller    |                                      ||
|  |     | - Pass through     |                                      ||
|  |     +--------+-----------+                                      ||
|  |              |                                                  ||
|  |              v                                                  ||
|  |     +--------------------+                                      ||
|  |     | Token Contracts    |                                      ||
|  |     | - Update blacklist |                                      ||
|  |     +--------------------+                                      ||
|  |                                                                 ||
|  +-----------------------------------------------------------------+|
|                                                                     |
|  +-----------------------------------------------------------------+|
|  |                    Module Components                            ||
|  |                                                                 ||
|  |  +----------------+  +------------------+  +-----------------+  ||
|  |  | LocalGov      |  | AddressRegistry  |  | Addys           |   ||
|  |  | * Governance  |  | * Config registry|  | * RipeHq lookup |   ||
|  |  | * Time-locks  |  | * ID management  |  | * Validation    |   ||
|  |  +----------------+  +------------------+  +-----------------+  ||
|  |                                                                 ||
|  |  +----------------+                                             ||
|  |  | DeptBasics    |                                              ||
|  |  | * Pause state |                                              ||
|  |  | * No minting  |                                              ||
|  |  +----------------+                                             ||
|  +-----------------------------------------------------------------+|
+---------------------------------------------------------------------+
                                   |
        +--------------------------+--------------------------+
        |                          |                          |
        v                          v                          v
+------------------+    +-------------------+    +------------------+
| Config Manager   |    | Mission Control   |    | Token Contracts  |
| * Updates MC     |    | * Stores all      |    | * Green Token    |
| * Blacklist mgmt |    |   protocol config |    | * Ripe Token     |
| * Registry ID: 1 |    | * GenConfig       |    | * Savings Green  |
| * Must be in     |    | * DebtConfig      |    +------------------+
|   Switchboard    |    | * AssetConfig     |
+------------------+    | * RewardsConfig   |
                        | * VaultConfig     |
                        | * PriceConfig     |
                        | * And many more   |
                        +-------------------+
```

## State Variables

### Inherited State Variables

From [LocalGov](../modules/LocalGov.md):

- `governance: address` - Current governance address
- `govChangeTimeLock: uint256` - Timelock for governance changes

From [AddressRegistry](../modules/AddressRegistry.md):

- `registryChangeTimeLock: uint256` - Timelock for registry changes
- Registry mappings for configuration contract management

From Addys:

- RipeHq address reference

From [DeptBasics](../modules/DeptBasics.md):

- `isPaused: bool` - Department pause state

## Constructor

### `__init__`

Initializes Switchboard with governance settings and registry time-locks.

```vyper
@deploy
def __init__(
    _ripeHq: address,
    _tempGov: address,
    _minRegistryTimeLock: uint256,
    _maxRegistryTimeLock: uint256,
):
```

#### Parameters

| Name                   | Type      | Description                            |
| ---------------------- | --------- | -------------------------------------- |
| `_ripeHq`              | `address` | RipeHq contract address                |
| `_tempGov`             | `address` | Initial temporary governance address   |
| `_minRegistryTimeLock` | `uint256` | Minimum time-lock for registry changes |
| `_maxRegistryTimeLock` | `uint256` | Maximum time-lock for registry changes |

#### Returns

_Constructor does not return any values_

#### Access

Called only during deployment

#### Example Usage

```python
# Deploy Switchboard
switchboard = boa.load(
    "contracts/registries/Switchboard.vy",
    ripe_hq.address,
    deployer.address,     # Temp governance
    100,                  # Min registry timelock
    1000                  # Max registry timelock
)
```

**Example Output**: Contract deployed with configuration registry ready, no minting capabilities

## Query Functions

### `isSwitchboardAddr`

Checks if an address is registered as a valid configuration contract.

```vyper
@view
@external
def isSwitchboardAddr(_addr: address) -> bool:
```

#### Parameters

| Name    | Type      | Description          |
| ------- | --------- | -------------------- |
| `_addr` | `address` | The address to check |

#### Returns

| Type   | Description                   |
| ------ | ----------------------------- |
| `bool` | True if address is registered |

#### Access

Public view function

#### Example Usage

```python
# Check if blacklist manager is registered
is_registered = switchboard.isSwitchboardAddr(blacklist_mgr.address)
# Returns: True if registered

# Check random address
is_registered = switchboard.isSwitchboardAddr(random_addr)
# Returns: False
```

## Registry Management Functions

### `startAddNewAddressToRegistry`

Initiates adding a new configuration contract to the registry.

```vyper
@external
def startAddNewAddressToRegistry(_addr: address, _description: String[64]) -> bool:
```

#### Parameters

| Name           | Type         | Description                               |
| -------------- | ------------ | ----------------------------------------- |
| `_addr`        | `address`    | The configuration contract address        |
| `_description` | `String[64]` | Description of the configuration contract |

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
# Add blacklist manager contract
success = switchboard.startAddNewAddressToRegistry(
    blacklist_manager.address,
    "Token Blacklist Manager",
    sender=governance.address
)
```

**Example Output**: Returns `True`, emits event with timelock confirmation block

### `confirmNewAddressToRegistry`

Confirms adding a new configuration contract after timelock.

```vyper
@external
def confirmNewAddressToRegistry(_addr: address) -> uint256:
```

#### Parameters

| Name    | Type      | Description                                   |
| ------- | --------- | --------------------------------------------- |
| `_addr` | `address` | The configuration contract address to confirm |

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
config_id = switchboard.confirmNewAddressToRegistry(
    blacklist_manager.address,
    sender=governance.address
)
# Returns: 1 (first config contract registered)
```

### `cancelNewAddressToRegistry`

Cancels a pending configuration contract addition.

```vyper
@external
def cancelNewAddressToRegistry(_addr: address) -> bool:
```

#### Parameters

| Name    | Type      | Description                                  |
| ------- | --------- | -------------------------------------------- |
| `_addr` | `address` | The configuration contract address to cancel |

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
success = switchboard.cancelNewAddressToRegistry(
    blacklist_manager.address,
    sender=governance.address
)
```

### `startAddressUpdateToRegistry`

Initiates updating a configuration contract address.

```vyper
@external
def startAddressUpdateToRegistry(_regId: uint256, _newAddr: address) -> bool:
```

#### Parameters

| Name       | Type      | Description                        |
| ---------- | --------- | ---------------------------------- |
| `_regId`   | `uint256` | Registry ID to update              |
| `_newAddr` | `address` | New configuration contract address |

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
# Update config contract to new version
success = switchboard.startAddressUpdateToRegistry(
    1,  # Blacklist manager ID
    blacklist_mgr_v2.address,
    sender=governance.address
)
```

### `confirmAddressUpdateToRegistry`

Confirms a configuration contract update after timelock.

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
success = switchboard.confirmAddressUpdateToRegistry(
    1,
    sender=governance.address
)
```

### `cancelAddressUpdateToRegistry`

Cancels a pending configuration contract update.

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

Initiates disabling a configuration contract.

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
# Start disabling compromised config contract
success = switchboard.startAddressDisableInRegistry(
    2,  # Compromised contract ID
    sender=governance.address
)
```

### `confirmAddressDisableInRegistry`

Confirms disabling a configuration contract after timelock.

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

## Blacklist Management Functions

### `setBlacklist`

Allows registered configuration contracts to update token blacklists.

```vyper
@external
def setBlacklist(_tokenAddr: address, _addr: address, _shouldBlacklist: bool) -> bool:
```

#### Parameters

| Name               | Type      | Description                          |
| ------------------ | --------- | ------------------------------------ |
| `_tokenAddr`       | `address` | The token contract to update         |
| `_addr`            | `address` | The address to blacklist/unblacklist |
| `_shouldBlacklist` | `bool`    | True to blacklist, False to remove   |

#### Returns

| Type   | Description                  |
| ------ | ---------------------------- |
| `bool` | True if successfully updated |

#### Access

Only callable by registered configuration contracts

#### Example Usage

```python
# Blacklist manager adds address to Green token blacklist
success = switchboard.setBlacklist(
    green_token.address,
    bad_actor.address,
    True,  # Add to blacklist
    sender=blacklist_manager.address  # Must be registered
)

# Remove from blacklist
success = switchboard.setBlacklist(
    green_token.address,
    reformed_actor.address,
    False,  # Remove from blacklist
    sender=blacklist_manager.address
)
```

**Example Output**: Calls `setBlacklist` on the token contract, returns `True`

## Security Considerations

1. **Configuration Authority**: Only registered contracts can modify Mission Control settings
2. **Time-Locked Registry**: All registry changes require time lock for security
3. **Pause Mechanism**: Can be paused by authorized contracts in emergencies
4. **Blacklist Power**: Can modify token blacklists - requires careful access control
5. **No Direct User Access**: All functions require governance or authorized contract access
6. **Registry Validation**: Validates configuration contracts before allowing registration
7. **Immutable Core**: Cannot modify its own registry after initial setup

## Testing

For comprehensive test examples, see: [`tests/registries/test_switchboard.py`](../../tests/registries/test_switchboard.py)
