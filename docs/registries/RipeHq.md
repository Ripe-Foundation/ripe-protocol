# RipeHq Technical Documentation

[📄 View Source Code](../../contracts/registries/RipeHq.vy)

## Overview

RipeHq is the master registry and governance hub for Ripe Protocol, coordinating all critical components and controlling token minting permissions. It maintains the authoritative record of protocol contracts while enforcing strict security through two-factor authentication and time-locked changes.

**Core Functions**:
- **Identity Registry**: Maps every protocol contract to unique IDs (Green: 1, sGREEN: 2, RIPE: 3)
- **Two-Factor Minting**: Requires both RipeHq permission AND department self-declaration
- **Safety Controls**: Time-locked changes, circuit breaker for emergencies, and power separation

Built with modular governance and registry components, RipeHq prevents unauthorized token creation through double-verification. Its architecture ensures decentralized components coordinate safely through a trusted central registry with comprehensive event logging and fund recovery mechanisms.

## Architecture & Modules

RipeHq is built using a modular architecture that separates concerns and promotes code reusability:

### LocalGov Module
- **Location**: `contracts/modules/LocalGov.vy`
- **Purpose**: Provides governance functionality with time-locked changes
- **Documentation**: See [LocalGov Technical Documentation](../modules/LocalGov.md)
- **Key Features**:
  - Governance address management with time-locked transitions
  - Configurable min/max timelock periods for security
  - Two-phase commit pattern for governance changes
- **Exported Interface**: All governance functions are exposed via `gov.__interface__`

### AddressRegistry Module  
- **Location**: `contracts/registries/modules/AddressRegistry.vy`
- **Purpose**: Manages the registry of protocol addresses
- **Documentation**: See [AddressRegistry Technical Documentation](../modules/AddressRegistry.md)
- **Key Features**:
  - Sequential registry ID assignment (starting from 1)
  - Time-locked address additions, updates, and disabling
  - Descriptive labels for each registered address
  - Address lookup by ID or reverse lookup (ID by address)
- **Exported Interface**: All registry functions are exposed via `registry.__interface__`

### Module Initialization
```vyper
initializes: gov
initializes: registry[gov := gov]
```
This initialization pattern ensures the registry module has access to governance controls while maintaining separation of concerns.

## System Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────┐
│                            RipeHq Contract                         │
├────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐         ┌──────────────────────────────┐  │
│  │   LocalGov Module   │         │   AddressRegistry Module     │  │
│  │                     │         │                              │  │
│  │ • Governance mgmt   │         │ • Address registration       │  │
│  │ • Timelock control  │         │ • ID assignment (1,2,3...)   │  │
│  │ • Access control    │         │ • Update/disable functions   │  │
│  └─────────────────────┘         └──────────────────────────────┘  │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    HQ Configuration Layer                    │  │
│  │                                                              │  │
│  │  • Minting permissions (canMintGreen, canMintRipe)           │  │
│  │  • Blacklist permissions (canSetTokenBlacklist)              │  │
│  │  • Two-factor authentication with departments                │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Safety Mechanisms                         │  │
│  │                                                              │  │
│  │  • Global minting circuit breaker (mintEnabled)              │  │
│  │  • Fund recovery system (recoverFunds)                       │  │
│  │  • Timelock protection on all changes                        │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
                                     │
                     ┌───────────────┴───────────────┐
                     ▼                               ▼
        ┌─────────────────────┐          ┌─────────────────────┐
        │   Core Tokens       │          │   Departments       │
        │                     │          │                     │
        │ ID 1: Green Token   │          │ ID 4+: Various      │
        │ ID 2: Savings Green │          │ • Auction House     │
        │ ID 3: Ripe Token    │          │ • Credit Engine     │
        └─────────────────────┘          │ • Lootbox, etc.     │
                                         └─────────────────────┘
```

## Data Structures

### HqConfig Struct
Stores the configuration for each registered address:
```vyper
struct HqConfig:
    description: String[64]        # Human-readable description
    canMintGreen: bool            # Permission to mint Green tokens
    canMintRipe: bool             # Permission to mint Ripe tokens
    canSetTokenBlacklist: bool    # Permission to modify token blacklists
```

### PendingHqConfig Struct
Tracks pending configuration changes during the timelock period:
```vyper
struct PendingHqConfig:
    newHqConfig: HqConfig         # The new configuration to apply
    initiatedBlock: uint256       # Block when change was initiated
    confirmBlock: uint256         # Block when change can be confirmed
```

## State Variables

### Public State Variables
- `hqConfig: HashMap[uint256, HqConfig]` - Maps registry ID to its configuration
- `pendingHqConfig: HashMap[uint256, PendingHqConfig]` - Maps registry ID to pending config changes
- `mintEnabled: bool` - Global circuit breaker for all minting operations

### Constants
- `MAX_RECOVER_ASSETS: uint256 = 20` - Maximum number of assets recoverable in a single transaction

### Inherited State Variables (from modules)
From [LocalGov](./LocalGov.md):
- `governance: address` - Current governance address
- `govChangeTimeLock: uint256` - Timelock for governance changes

From [AddressRegistry](./AddressRegistry.md):
- `registryChangeTimeLock: uint256` - Timelock for registry changes
- Various internal registry mappings for address management

## Constructor

### `__init__`

Initializes the RipeHq contract with core protocol addresses and timelock parameters. Automatically registers the Green token, Savings Green, and Ripe token with registry IDs 1, 2, and 3 respectively.

```vyper
@deploy
def __init__(
    _greenToken: address,
    _savingsGreen: address,
    _ripeToken: address,
    _initialGov: address,
    _minGovTimeLock: uint256,
    _maxGovTimeLock: uint256,
    _minRegistryTimeLock: uint256,
    _maxRegistryTimeLock: uint256,
):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_greenToken` | `address` | The address of the Green token contract |
| `_savingsGreen` | `address` | The address of the Savings Green contract |
| `_ripeToken` | `address` | The address of the Ripe token contract |
| `_initialGov` | `address` | The initial governance address |
| `_minGovTimeLock` | `uint256` | Minimum time lock for governance changes in blocks |
| `_maxGovTimeLock` | `uint256` | Maximum time lock for governance changes in blocks |
| `_minRegistryTimeLock` | `uint256` | Minimum time lock for registry changes in blocks |
| `_maxRegistryTimeLock` | `uint256` | Maximum time lock for registry changes in blocks |

#### Returns

*Constructor does not return any values*

#### Access

Called only during deployment

#### Example Usage
```python
# Deploy RipeHq with core protocol addresses
ripe_hq = boa.load(
    "contracts/registries/RipeHq.vy",
    green_token.address,
    savings_green.address,
    ripe_token.address,
    deployer_address,
    100,   # Min gov timelock (blocks)
    1000,  # Max gov timelock (blocks)
    50,    # Min registry timelock (blocks)
    500    # Max registry timelock (blocks)
)
```

**Example Output**: Contract deployed with Green token registered as ID 1, Savings Green as ID 2, and Ripe token as ID 3. Minting is enabled by default.

## Registry Management Functions

### `startAddNewAddressToRegistry`

Initiates the process of adding a new address to the registry. This starts a time-locked change that must be confirmed after the timelock period.

```vyper
@external
def startAddNewAddressToRegistry(_addr: address, _description: String[64]) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_addr` | `address` | The address to add to the registry |
| `_description` | `String[64]` | A human-readable description of the address (max 64 characters) |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if the addition was successfully initiated |

#### Access

Only callable by governance (see [LocalGov](./LocalGov.md) for governance details)

#### Events Emitted

- `NewAddressPending` (from [AddressRegistry](./AddressRegistry.md)) - Contains address, description, and confirmation block

#### Example Usage
```python
# Governance initiates adding a new department
success = ripe_hq.startAddNewAddressToRegistry(
    treasury_dept.address,
    "Treasury Department",
    sender=governance.address
)
```

**Example Output**: Returns `True`, emits event indicating timelock confirmation block

### `confirmNewAddressToRegistry`

Confirms a pending address addition after the timelock period has passed. Assigns the next available registry ID to the address.

```vyper
@external
def confirmNewAddressToRegistry(_addr: address) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_addr` | `address` | The address to confirm |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | The assigned registry ID |

#### Access

Only callable by governance (see [LocalGov](./LocalGov.md) for governance details)

#### Events Emitted

- `NewAddressConfirmed` (from [AddressRegistry](./AddressRegistry.md)) - Contains registry ID, address, description

#### Example Usage
```python
# After timelock period, confirm the addition
boa.env.time_travel(blocks=time_lock)
reg_id = ripe_hq.confirmNewAddressToRegistry(
    treasury_dept.address,
    sender=governance.address
)
# Returns: 4 (next ID after the 3 core tokens)
```

**Example Output**: Returns registry ID 4, address is now registered

### `cancelNewAddressToRegistry`

Cancels a pending address addition before it's confirmed.

```vyper
@external
def cancelNewAddressToRegistry(_addr: address) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_addr` | `address` | The address whose pending addition to cancel |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if successfully cancelled |

#### Access

Only callable by governance (see [LocalGov](./LocalGov.md) for governance details)

#### Events Emitted

- `NewAddressCancelled` (from [AddressRegistry](./AddressRegistry.md)) - Contains address, description, initiation and confirmation blocks

#### Example Usage
```python
# Cancel pending addition
success = ripe_hq.cancelNewAddressToRegistry(
    treasury_dept.address,
    sender=governance.address
)
```

**Example Output**: Returns `True`, pending addition removed

### `startAddressUpdateToRegistry`

Initiates updating an existing registry entry to point to a new address. Useful for contract upgrades.

```vyper
@external
def startAddressUpdateToRegistry(_regId: uint256, _newAddr: address) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_regId` | `uint256` | The registry ID to update |
| `_newAddr` | `address` | The new address to associate with this ID |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if update was successfully initiated |

#### Access

Only callable by governance (see [LocalGov](./LocalGov.md) for governance details)

#### Events Emitted

- `AddressUpdatePending` (from [AddressRegistry](./AddressRegistry.md)) - Contains registry ID, old address, new address, and confirmation block

#### Example Usage
```python
# Start updating Treasury Department to new implementation
success = ripe_hq.startAddressUpdateToRegistry(
    4,                           # Registry ID for Treasury
    new_treasury_dept.address,   # New Treasury contract
    sender=governance.address
)
```

**Example Output**: Returns `True`, update pending with timelock

### `confirmAddressUpdateToRegistry`

Confirms a pending address update after the timelock period.

```vyper
@external
def confirmAddressUpdateToRegistry(_regId: uint256) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_regId` | `uint256` | The registry ID being updated |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if successfully confirmed |

#### Access

Only callable by governance (see [LocalGov](./LocalGov.md) for governance details)

#### Events Emitted

- `AddressUpdateConfirmed` (from [AddressRegistry](./AddressRegistry.md)) - Contains registry ID, old address, new address, version

#### Example Usage
```python
# Confirm the Treasury update after timelock
boa.env.time_travel(blocks=time_lock)
success = ripe_hq.confirmAddressUpdateToRegistry(
    4,
    sender=governance.address
)
```

**Example Output**: Returns `True`, registry ID 4 now points to new address

### `cancelAddressUpdateToRegistry`

Cancels a pending address update.

```vyper
@external
def cancelAddressUpdateToRegistry(_regId: uint256) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_regId` | `uint256` | The registry ID whose update to cancel |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if successfully cancelled |

#### Access

Only callable by governance (see [LocalGov](./LocalGov.md) for governance details)

#### Events Emitted

- `AddressUpdateCancelled` (from [AddressRegistry](./AddressRegistry.md)) - Contains registry ID, old address, new address, initiation and confirmation blocks

#### Example Usage
```python
# Cancel pending update
success = ripe_hq.cancelAddressUpdateToRegistry(
    4,
    sender=governance.address
)
```

**Example Output**: Returns `True`, update cancelled

### `startAddressDisableInRegistry`

Initiates disabling a registry entry. Note: Core tokens (IDs 1-3) cannot be disabled.

```vyper
@external
def startAddressDisableInRegistry(_regId: uint256) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_regId` | `uint256` | The registry ID to disable |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if disable was successfully initiated |

#### Access

Only callable by governance (see [LocalGov](./LocalGov.md) for governance details)

#### Events Emitted

- `AddressDisablePending` (from [AddressRegistry](./AddressRegistry.md)) - Contains registry ID, address, description, and confirmation block

#### Example Usage
```python
# Start disabling a deprecated department
success = ripe_hq.startAddressDisableInRegistry(
    5,
    sender=governance.address
)
```

**Example Output**: Returns `True` if not a token ID, reverts with "dev: cannot disable token" for IDs 1-3

### `confirmAddressDisableInRegistry`

Confirms disabling a registry entry after timelock.

```vyper
@external
def confirmAddressDisableInRegistry(_regId: uint256) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_regId` | `uint256` | The registry ID to confirm disabling |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if successfully disabled |

#### Access

Only callable by governance (see [LocalGov](./LocalGov.md) for governance details)

#### Events Emitted

- `AddressDisableConfirmed` (from [AddressRegistry](./AddressRegistry.md)) - Contains registry ID, address, description, version

#### Example Usage
```python
# Confirm disabling after timelock
boa.env.time_travel(blocks=time_lock)
success = ripe_hq.confirmAddressDisableInRegistry(
    5,
    sender=governance.address
)
```

**Example Output**: Returns `True`, registry entry disabled

### `cancelAddressDisableInRegistry`

Cancels a pending disable operation.

```vyper
@external
def cancelAddressDisableInRegistry(_regId: uint256) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_regId` | `uint256` | The registry ID whose disable to cancel |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if successfully cancelled |

#### Access

Only callable by governance (see [LocalGov](./LocalGov.md) for governance details)

#### Events Emitted

- `AddressDisableCancelled` (from [AddressRegistry](./AddressRegistry.md)) - Contains registry ID, address, description, initiation and confirmation blocks

#### Example Usage
```python
# Cancel pending disable
success = ripe_hq.cancelAddressDisableInRegistry(
    5,
    sender=governance.address
)
```

**Example Output**: Returns `True`, disable cancelled

## HQ Configuration Functions

### `hasPendingHqConfigChange`

Checks if a registry ID has a pending configuration change.

```vyper
@view
@external
def hasPendingHqConfigChange(_regId: uint256) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_regId` | `uint256` | The registry ID to check |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if there's a pending change |

#### Access

Public view function

#### Example Usage
```python
# Check if Treasury has pending config changes
has_pending = ripe_hq.hasPendingHqConfigChange(4)
```

**Example Output**: Returns `True` if pending, `False` otherwise

### `initiateHqConfigChange`

Starts a time-locked process to update a department's permissions for minting and blacklist management.

```vyper
@external
def initiateHqConfigChange(
    _regId: uint256,
    _canMintGreen: bool,
    _canMintRipe: bool,
    _canSetTokenBlacklist: bool,
):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_regId` | `uint256` | The registry ID to configure |
| `_canMintGreen` | `bool` | Whether this address can mint Green tokens |
| `_canMintRipe` | `bool` | Whether this address can mint Ripe tokens |
| `_canSetTokenBlacklist` | `bool` | Whether this address can modify token blacklists |

#### Returns

*Function does not return any values*

#### Access

Only callable by governance (see [LocalGov](./LocalGov.md) for governance details)

#### Events Emitted

- `HqConfigChangeInitiated` - Contains registry ID, description, permissions, and confirmation block

#### Example Usage
```python
# Grant Treasury permission to mint Green tokens only
ripe_hq.initiateHqConfigChange(
    4,      # Treasury registry ID
    True,   # Can mint Green
    False,  # Cannot mint Ripe
    False,  # Cannot set blacklist
    sender=governance.address
)
```

**Example Output**: Emits `HqConfigChangeInitiated` event with confirmation block

### `confirmHqConfigChange`

Confirms a pending configuration change after timelock. Validates that the department contract actually supports the requested minting permissions.

```vyper
@external
def confirmHqConfigChange(_regId: uint256) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_regId` | `uint256` | The registry ID to confirm |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if successfully confirmed, False if the configuration is invalid (in which case the pending configuration is deleted) |

#### Access

Only callable by governance (see [LocalGov](./LocalGov.md) for governance details)

#### Events Emitted

- `HqConfigChangeConfirmed` - Contains registry ID, description, permissions, and both initiation and confirmation blocks

#### Example Usage
```python
# Confirm Treasury's new permissions after timelock
boa.env.time_travel(blocks=time_lock)
success = ripe_hq.confirmHqConfigChange(
    4,
    sender=governance.address
)
```

**Example Output**: Returns `True` if valid, `False` if department doesn't support requested permissions

### `cancelHqConfigChange`

Cancels a pending configuration change.

```vyper
@external
def cancelHqConfigChange(_regId: uint256) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_regId` | `uint256` | The registry ID whose config change to cancel |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if successfully cancelled |

#### Access

Only callable by governance (see [LocalGov](./LocalGov.md) for governance details)

#### Events Emitted

- `HqConfigChangeCancelled` - Contains registry ID, description, permissions (canMintGreen, canMintRipe, canSetTokenBlacklist), initiatedBlock, and confirmBlock

#### Example Usage
```python
# Cancel pending config change
success = ripe_hq.cancelHqConfigChange(
    4,
    sender=governance.address
)
```

**Example Output**: Returns `True`, emits `HqConfigChangeCancelled` event

### `isValidHqConfig`

Validates whether a proposed configuration is valid for a given registry ID. Checks that non-token entries support the requested minting capabilities.

```vyper
@view
@external
def isValidHqConfig(
    _regId: uint256,
    _canMintGreen: bool,
    _canMintRipe: bool,
) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_regId` | `uint256` | The registry ID to validate |
| `_canMintGreen` | `bool` | Proposed Green minting permission |
| `_canMintRipe` | `bool` | Proposed Ripe minting permission |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if configuration is valid |

#### Access

Public external function (marked with `@view` decorator)

#### Example Usage
```python
# Check if Treasury can be granted Green minting permission
is_valid = ripe_hq.isValidHqConfig(4, True, False)
# Returns True if Treasury contract has canMintGreen() returning True
```

**Example Output**: Returns `True` if valid, `False` if not a valid registry ID, address is empty, or department doesn't support requested permissions

## Token Getter Functions

### `greenToken`

Returns the address of the Green token contract (registry ID 1).

```vyper
@view
@external
def greenToken() -> address:
```

#### Parameters

*Function has no parameters*

#### Returns

| Type | Description |
|------|-------------|
| `address` | The Green token contract address |

#### Access

Public view function

#### Example Usage
```python
green_addr = ripe_hq.greenToken()
# Returns: green_token.address
assert green_addr == ripe_hq.getAddr(1)
```

### `savingsGreen`

Returns the address of the Savings Green contract (registry ID 2).

```vyper
@view
@external
def savingsGreen() -> address:
```

#### Parameters

*Function has no parameters*

#### Returns

| Type | Description |
|------|-------------|
| `address` | The Savings Green contract address |

#### Access

Public view function

#### Example Usage
```python
savings_addr = ripe_hq.savingsGreen()
# Returns: savings_green.address
assert savings_addr == ripe_hq.getAddr(2)
```

### `ripeToken`

Returns the address of the Ripe token contract (registry ID 3).

```vyper
@view
@external
def ripeToken() -> address:
```

#### Parameters

*Function has no parameters*

#### Returns

| Type | Description |
|------|-------------|
| `address` | The Ripe token contract address |

#### Access

Public view function

#### Example Usage
```python
ripe_addr = ripe_hq.ripeToken()
# Returns: ripe_token.address
assert ripe_addr == ripe_hq.getAddr(3)
```

## Minting Permission Functions

### `canMintGreen`

Checks if an address has permission to mint Green tokens. Requires minting to be enabled globally, the address to be registered with Green minting permission, and the address's contract to return `True` from `canMintGreen()`.

```vyper
@view
@external
def canMintGreen(_addr: address) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_addr` | `address` | The address to check |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if address can mint Green tokens |

#### Access

Public view function

#### Example Usage
```python
# Check if Credit Engine can mint Green
can_mint = ripe_hq.canMintGreen(credit_engine.address)
# Returns: True (if minting enabled, registered with permission, and dept supports it)
assert can_mint == True
```

**Example Output**: Returns `True` only if minting enabled, address registered with permission, and contract confirms capability

### `canMintRipe`

Checks if an address has permission to mint Ripe tokens. Requires minting to be enabled globally, the address to be registered with Ripe minting permission, and the address's contract to return `True` from `canMintRipe()`.

```vyper
@view
@external
def canMintRipe(_addr: address) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_addr` | `address` | The address to check |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if address can mint Ripe tokens |

#### Access

Public view function

#### Example Usage
```python
# Check if Lootbox can mint Ripe
can_mint = ripe_hq.canMintRipe(lootbox.address)
# Returns: True (if minting enabled, registered with permission, and dept supports it)
assert can_mint == True
```

**Example Output**: Returns `True` only if all three conditions are satisfied

### `canSetTokenBlacklist`

Checks if an address has permission to modify token blacklists. Only requires the address to be registered with this permission in HQ config.

```vyper
@view
@external
def canSetTokenBlacklist(_addr: address) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_addr` | `address` | The address to check |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if address can set token blacklists |

#### Access

Public view function

#### Example Usage
```python
# Check if Switchboard can set blacklists
can_blacklist = ripe_hq.canSetTokenBlacklist(switchboard.address)
# Returns: True (if configured)
assert can_blacklist == True
```

**Example Output**: Returns `True` if address has blacklist permission in config

## Circuit Breaker Functions

### `setMintingEnabled`

Enables or disables all minting operations across the protocol. Acts as an emergency circuit breaker.

```vyper
@external
def setMintingEnabled(_shouldEnable: bool):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_shouldEnable` | `bool` | True to enable minting, False to disable |

#### Returns

*Function does not return any values*

#### Access

Only callable by governance (see [LocalGov](./LocalGov.md) for governance details)

#### Events Emitted

- `MintingEnabled` - Contains the new enabled state (isEnabled)

#### Example Usage
```python
# Emergency: disable all minting
ripe_hq.setMintingEnabled(False, sender=governance.address)
assert ripe_hq.mintEnabled() == False

# Later: re-enable minting
ripe_hq.setMintingEnabled(True, sender=governance.address)
assert ripe_hq.mintEnabled() == True
```

**Example Output**: Emits `MintingEnabled` event with new state

## Recovery Functions

### `recoverFunds`

Recovers tokens accidentally sent to the RipeHq contract. Transfers the full balance of a specified token to a recipient.

```vyper
@external
def recoverFunds(_recipient: address, _asset: address):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_recipient` | `address` | The address to receive recovered funds |
| `_asset` | `address` | The token contract address to recover |

#### Returns

*Function does not return any values*

#### Access

Only callable by governance (see [LocalGov](./LocalGov.md) for governance details)

#### Events Emitted

- `RipeHqFundsRecovered` - Contains the asset address (indexed), recipient address (indexed), and balance recovered

#### Example Usage
```python
# Recover accidentally sent tokens
alpha_token.transfer(ripe_hq.address, 1000, sender=alpha_token_whale)
ripe_hq.recoverFunds(
    treasury.address,     # Send to Treasury
    alpha_token.address,  # Token to recover
    sender=governance.address
)
assert alpha_token.balanceOf(treasury.address) == 1000
```

**Example Output**: Transfers full USDC balance, emits `RipeHqFundsRecovered` event

### `recoverFundsMany`

Recovers multiple tokens in a single transaction. Useful for batch recovery operations.

```vyper
@external
def recoverFundsMany(_recipient: address, _assets: DynArray[address, MAX_RECOVER_ASSETS]):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_recipient` | `address` | The address to receive all recovered funds |
| `_assets` | `DynArray[address, MAX_RECOVER_ASSETS]` | List of token addresses to recover (max 20) |

#### Returns

*Function does not return any values*

#### Access

Only callable by governance (see [LocalGov](./LocalGov.md) for governance details)

#### Events Emitted

- `RipeHqFundsRecovered` - One event per recovered asset with asset address (indexed), recipient (indexed), and balance

#### Example Usage
```python
# Recover multiple tokens at once
alpha_token.transfer(ripe_hq.address, 2000, sender=alpha_token_whale)
bravo_token.transfer(ripe_hq.address, 2000, sender=bravo_token_whale)
charlie_token.transfer(ripe_hq.address, 2000, sender=charlie_token_whale)

assets = [alpha_token.address, bravo_token.address, charlie_token.address]
ripe_hq.recoverFundsMany(
    treasury.address,
    assets,
    sender=governance.address
)
assert alpha_token.balanceOf(treasury.address) == 2000
assert bravo_token.balanceOf(treasury.address) == 2000
assert charlie_token.balanceOf(treasury.address) == 2000
```

**Example Output**: Transfers all balances, emits `RipeHqFundsRecovered` for each token

## Testing

For comprehensive test examples, see: [`tests/registries/test_ripe_hq.py`](../../tests/registries/test_ripe_hq.py)