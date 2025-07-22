# VaultBook Technical Documentation

[📄 View Source Code](../../contracts/registries/VaultBook.vy)

## Overview

VaultBook is the central registry for all deposit vaults in Ripe Protocol. It maintains the authoritative list of approved vaults while enforcing critical safety checks and managing RIPE reward distribution for stability pool participants.

**Core Functions**:
- **Vault Registry**: Maintains approved vault contracts with unique IDs and descriptions
- **Safety Validation**: Prevents vault updates when user funds are present
- **Reward Distribution**: Exclusive RIPE minting authority for stability pool rewards

Built on LocalGov, AddressRegistry, and DeptBasics modules, VaultBook ensures vault integrity through automated fund checks before modifications. Its unique role as the sole RIPE minter for stability rewards creates a secure, controlled distribution mechanism with proper Ledger accounting.

## Architecture & Modules

VaultBook is built using a modular architecture that inherits functionality from multiple base modules:

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
- **Purpose**: Manages the registry of vault addresses
- **Documentation**: See [AddressRegistry Technical Documentation](../modules/AddressRegistry.md)
- **Key Features**:
  - Sequential registry ID assignment for vaults
  - Time-locked address additions, updates, and disabling
  - Descriptive labels for each vault
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
  - **Ripe token minting capability enabled** (unique to VaultBook)
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
+-----------------------------------------------------------------------+
|                         VaultBook Contract                            |
+-----------------------------------------------------------------------+
|                                                                       |
|  +-------------------------------------------------------------------+|
|  |                      Vault Management Flow                        ||
|  |                                                                   ||
|  |  1. Vault Registration                                            ||
|  |     - New vaults added with time-lock                             ||
|  |     - Assigned sequential registry IDs                            ||
|  |                                                                   ||
|  |  2. Safety Checks for Updates/Disables                            ||
|  |     - Check vault.doesVaultHaveAnyFunds()                         ||
|  |     - Block changes if funds present                              ||
|  |     - Protect user deposits                                       ||
|  |                                                                   ||
|  |  3. Stability Pool Reward Flow                                    ||
|  |     +------------------+                                          ||
|  |     | Registered Vault |                                          ||
|  |     | (Stability Pool) |                                          ||
|  |     +--------+---------+                                          ||
|  |              |                                                    ||
|  |              v                                                    ||
|  |     +------------------+                                          ||
|  |     | VaultBook       |                                           ||
|  |     | - Verify caller |                                           ||
|  |     | - Mint RIPE     |                                           ||
|  |     | - Update Ledger |                                           ||
|  |     +--------+---------+                                          ||
|  |              |                                                    ||
|  |              +--------+--------+                                  ||
|  |              |                 |                                  ||
|  |              v                 v                                  ||
|  |     +------------------+  +------------------+                    ||
|  |     | Ripe Token      |  | Ledger           |                     ||
|  |     | - Mint rewards  |  | - Track rewards  |                     ||
|  |     +------------------+  +------------------+                    ||
|  |                                                                   ||
|  +-------------------------------------------------------------------+|
|                                                                       |
|  +-------------------------------------------------------------------+|
|  |                     Module Components                             ||
|  |                                                                   ||
|  |  +----------------+  +------------------+  +------------------+   ||
|  |  | LocalGov      |  | AddressRegistry  |  | Addys            |    ||
|  |  | * Governance  |  | * Vault registry |  | * RipeHq lookup  |    ||
|  |  | * Time-locks  |  | * ID management  |  | * Validation     |    ||
|  |  +----------------+  +------------------+  +------------------+   ||
|  |                                                                   ||
|  |  +------------------+                                             ||
|  |  | DeptBasics      |                                              ||
|  |  | * Pause state   |                                              ||
|  |  | * RIPE minting  |  <-- Enabled for rewards                     ||
|  |  +------------------+                                             ||
|  +-------------------------------------------------------------------+|
+-----------------------------------------------------------------------+
                                    |
         +--------------------------+--------------------------+
         |                          |                          |
         v                          v                          v
+-------------------+    +-------------------+    +-------------------+
| Collateral Vault  |    | Stability Pool    |    | Ripe Token       |
| * User deposits   |    | * RIPE rewards    |    | * Minted for     |
| * No RIPE minting |    | * Claims trigger  |    |   stab rewards   |
| * Registry ID: 1  |    |   VaultBook call  |    +-------------------+
+-------------------+    | * Registry ID: 2  |
                         +-------------------+
```

## State Variables

### Inherited State Variables

From [LocalGov](../modules/LocalGov.md):

- `governance: address` - Current governance address
- `govChangeTimeLock: uint256` - Timelock for governance changes

From [AddressRegistry](../modules/AddressRegistry.md):

- `registryChangeTimeLock: uint256` - Timelock for registry changes
- Registry mappings for vault management

From Addys:

- RipeHq address reference

From [DeptBasics](../modules/DeptBasics.md):

- `isPaused: bool` - Department pause state
- `canMintRipe: bool` - Set to `True` for VaultBook

## Constructor

### `__init__`

Initializes VaultBook with governance settings and Ripe minting capability.

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
# Deploy VaultBook
vault_book = boa.load(
    "contracts/registries/VaultBook.vy",
    ripe_hq.address,
    deployer.address,     # Temp governance
    100,                  # Min registry timelock
    1000                  # Max registry timelock
)
```

**Example Output**: Contract deployed with vault registry ready, Ripe minting enabled

## Query Functions

### `isVaultBookAddr`

Checks if an address is registered as a valid vault.

```vyper
@view
@external
def isVaultBookAddr(_addr: address) -> bool:
```

#### Parameters

| Name    | Type      | Description          |
| ------- | --------- | -------------------- |
| `_addr` | `address` | The address to check |

#### Returns

| Type   | Description                           |
| ------ | ------------------------------------- |
| `bool` | True if address is a registered vault |

#### Access

Public view function

#### Example Usage

```python
# Check if collateral vault is registered
is_vault = vault_book.isVaultBookAddr(collateral_vault.address)
# Returns: True if registered

# Check random address
is_vault = vault_book.isVaultBookAddr(random_addr)
# Returns: False
```

## Registry Management Functions

### `startAddNewAddressToRegistry`

Initiates adding a new vault to the registry.

```vyper
@external
def startAddNewAddressToRegistry(_addr: address, _description: String[64]) -> bool:
```

#### Parameters

| Name           | Type         | Description                |
| -------------- | ------------ | -------------------------- |
| `_addr`        | `address`    | The vault contract address |
| `_description` | `String[64]` | Description of the vault   |

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
# Add new collateral vault
success = vault_book.startAddNewAddressToRegistry(
    eth_vault.address,
    "ETH Collateral Vault",
    sender=governance.address
)
```

**Example Output**: Returns `True`, emits event with timelock confirmation block

### `confirmNewAddressToRegistry`

Confirms adding a new vault after timelock.

```vyper
@external
def confirmNewAddressToRegistry(_addr: address) -> uint256:
```

#### Parameters

| Name    | Type      | Description                  |
| ------- | --------- | ---------------------------- |
| `_addr` | `address` | The vault address to confirm |

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
vault_id = vault_book.confirmNewAddressToRegistry(
    eth_vault.address,
    sender=governance.address
)
# Returns: 1 (first vault registered)
```

### `cancelNewAddressToRegistry`

Cancels a pending vault addition.

```vyper
@external
def cancelNewAddressToRegistry(_addr: address) -> bool:
```

#### Parameters

| Name    | Type      | Description                 |
| ------- | --------- | --------------------------- |
| `_addr` | `address` | The vault address to cancel |

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
success = vault_book.cancelNewAddressToRegistry(
    eth_vault.address,
    sender=governance.address
)
```

### `startAddressUpdateToRegistry`

Initiates updating a vault address. **Note: Blocked if vault has funds.**

```vyper
@external
def startAddressUpdateToRegistry(_regId: uint256, _newAddr: address) -> bool:
```

#### Parameters

| Name       | Type      | Description           |
| ---------- | --------- | --------------------- |
| `_regId`   | `uint256` | Registry ID to update |
| `_newAddr` | `address` | New vault address     |

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
# Update vault to new version (only if empty)
success = vault_book.startAddressUpdateToRegistry(
    1,  # ETH vault ID
    eth_vault_v2.address,
    sender=governance.address
)
# Reverts with "vault has funds" if vault not empty
```

### `confirmAddressUpdateToRegistry`

Confirms a vault update after timelock.

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
success = vault_book.confirmAddressUpdateToRegistry(
    1,
    sender=governance.address
)
```

### `cancelAddressUpdateToRegistry`

Cancels a pending vault update.

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

Initiates disabling a vault. **Note: Blocked if vault has funds.**

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
# Start disabling deprecated vault (only if empty)
success = vault_book.startAddressDisableInRegistry(
    2,  # Old vault ID
    sender=governance.address
)
# Reverts with "vault has funds" if vault not empty
```

### `confirmAddressDisableInRegistry`

Confirms disabling a vault after timelock.

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

## Stability Pool Reward Functions

### `mintRipeForStabPoolClaims`

Mints Ripe tokens as rewards for stability pool participants and updates the Ledger.

```vyper
@external
def mintRipeForStabPoolClaims(_amount: uint256, _ripeToken: address, _ledger: address) -> bool:
```

#### Parameters

| Name         | Type      | Description                    |
| ------------ | --------- | ------------------------------ |
| `_amount`    | `uint256` | Amount of Ripe tokens to mint  |
| `_ripeToken` | `address` | Ripe token contract address    |
| `_ledger`    | `address` | Ledger contract for accounting |

#### Returns

| Type   | Description                 |
| ------ | --------------------------- |
| `bool` | True if successfully minted |

#### Access

Only callable by registered vaults (typically the Stability Pool)

#### Example Usage

```python
# Stability pool claims rewards
success = vault_book.mintRipeForStabPoolClaims(
    1000_000000000000000000,  # 1000 RIPE
    ripe_token.address,
    ledger.address,
    sender=stability_pool.address  # Must be registered vault
)
```

**Example Output**:

1. Mints Ripe tokens to the calling vault
2. Calls `didGetRewardsFromStabClaims` on Ledger to record the reward
3. Returns `True`

## Testing

For comprehensive test examples, see: [`tests/registries/test_vault_book.py`](../../tests/registries/test_vault_book.py)
