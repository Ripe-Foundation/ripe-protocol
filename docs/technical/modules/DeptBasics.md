# DeptBasics Technical Documentation

[📄 View Source Code](../../contracts/modules/DeptBasics.vy)

## Overview

DeptBasics is a foundational module providing essential department-level functionality for Ripe Protocol contracts. It standardizes common operations across all departments including pause mechanisms, token recovery, and minting
capability declarations, ensuring consistency while allowing deployment-time customization.

**Core Capabilities**:
- **Pause Functionality**: Circuit breaker for emergencies, allowing Switchboard-authorized contracts to halt operations
- **Token Recovery**: Secure retrieval of accidentally sent tokens with batch support for efficiency
- **Minting Declarations**: Immutable capability flags for Green/Ripe token minting, supporting RipeHq's two-factor authentication

The module implements the Department interface standard, integrates with Addys for validation, and promotes operational consistency across all protocol departments.

## System Architecture Diagram

```
+---------------------------------------------------------------+
|                      DeptBasics Module                        |
+---------------------------------------------------------------+
|                                                               |
|  +----------------------------------------------------------+ |
|  |                   Core Capabilities                      | |
|  |                                                          | |
|  |  1. Pause Management                                     | |
|  |     * isPaused state variable                            | |
|  |     * Toggle via Switchboard-authorized contracts        | |
|  |     * Emits DepartmentPauseModified events               | |
|  |                                                          | |
|  |  2. Token Recovery                                       | |
|  |     * Recover individual tokens                          | |
|  |     * Batch recovery (up to 20 tokens)                   | |
|  |     * Only via Switchboard authorization                 | |
|  |     * Emits DepartmentFundsRecovered events              | |
|  |                                                          | |
|  |  3. Minting Capabilities                                 | |
|  |     * CAN_MINT_GREEN (immutable)                         | |
|  |     * CAN_MINT_RIPE (immutable)                          | |
|  |     * Set once at deployment                             | |
|  |     * Queried by RipeHq for permissions                  | |
|  +----------------------------------------------------------+ |
|                                                               |
|  +----------------------------------------------------------+ |
|  |                 Integration Pattern                      | |
|  |                                                          | |
|  |  Parent Contract                                         | |
|  |  initializes: deptBasics[addys := addys]                 | |
|  |                                                          | |
|  |  deptBasics.__init__(                                    | |
|  |      _shouldPause,    // Initial pause state             | |
|  |      _canMintGreen,   // Green minting capability        | |
|  |      _canMintRipe     // Ripe minting capability         | |
|  |  )                                                       | |
|  +----------------------------------------------------------+ |
+---------------------------------------------------------------+
                              |
                              v
+---------------------------------------------------------------+
|               Department Contract Examples                    |
|                                                               |
|  +------------------+  +------------------+  +--------------+ |
|  | PriceDesk        |  | Switchboard      |  | VaultBook    | |
|  | * No minting     |  | * No minting     |  | * RIPE only  | |
|  | * Can pause      |  | * Can pause      |  | * Can pause  | |
|  +------------------+  +------------------+  +--------------+ |
|                                                               |
|  +------------------+  +------------------+                   |
|  | Credit Engine    |  | Treasury         |                   |
|  | * GREEN minting  |  | * No minting     |                   |
|  | * Can pause      |  | * Can pause      |                   |
|  +------------------+  +------------------+                   |
+---------------------------------------------------------------+
```

## State Variables

### Public State Variables
- `isPaused: bool` - Current pause state of the department

### Immutable Variables
- `CAN_MINT_GREEN: bool` - Whether this department can mint Green tokens
- `CAN_MINT_RIPE: bool` - Whether this department can mint Ripe tokens

### Constants
- `MAX_RECOVER_ASSETS: uint256 = 20` - Maximum tokens recoverable in batch operation

## Constructor

### `__init__`

Initializes the DeptBasics module with pause state and minting capabilities.

```vyper
@deploy
def __init__(_shouldPause: bool, _canMintGreen: bool, _canMintRipe: bool):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_shouldPause` | `bool` | Initial pause state for the department |
| `_canMintGreen` | `bool` | Whether department can mint Green tokens |
| `_canMintRipe` | `bool` | Whether department can mint Ripe tokens |

#### Returns

*Constructor does not return any values*

#### Access

Called only during deployment by parent contract

#### Example Usage
```python
# Initialize for a non-minting department (e.g., PriceDesk)
deptBasics.__init__(
    False,  # Not paused initially
    False,  # Cannot mint Green
    False   # Cannot mint Ripe
)

# Initialize for VaultBook (can mint Ripe for rewards)
deptBasics.__init__(
    False,  # Not paused initially
    False,  # Cannot mint Green
    True    # Can mint Ripe
)

# Initialize for Credit Engine (can mint Green)
deptBasics.__init__(
    False,  # Not paused initially
    True,   # Can mint Green
    False   # Cannot mint Ripe
)
```

**Example Output**: Module initialized with specified capabilities

## Minting Query Functions

### `canMintGreen`

Returns whether this department has Green token minting capability.

```vyper
@view
@external
def canMintGreen() -> bool:
```

#### Parameters

*Function has no parameters*

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if department can mint Green tokens |

#### Access

Public view function

#### Example Usage
```python
# Check if Credit Engine can mint Green
can_mint = credit_engine.canMintGreen()
# Returns: True

# Check if PriceDesk can mint Green
can_mint = price_desk.canMintGreen()
# Returns: False
```

### `canMintRipe`

Returns whether this department has Ripe token minting capability.

```vyper
@view
@external
def canMintRipe() -> bool:
```

#### Parameters

*Function has no parameters*

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if department can mint Ripe tokens |

#### Access

Public view function

#### Example Usage
```python
# Check if VaultBook can mint Ripe
can_mint = vault_book.canMintRipe()
# Returns: True (for stability pool rewards)

# Check if Switchboard can mint Ripe
can_mint = switchboard.canMintRipe()
# Returns: False
```

## Pause Management Functions

### `pause`

Toggles the pause state of the department.

```vyper
@external
def pause(_shouldPause: bool):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_shouldPause` | `bool` | New pause state (must be different from current) |

#### Returns

*Function does not return any values*

#### Access

Only callable by Switchboard-registered contracts

#### Events Emitted

- `DepartmentPauseModified` - Contains the new pause state

#### Example Usage
```python
# Pause a department in emergency
switchboard.pause(
    True,
    sender=emergency_manager.address  # Must be in Switchboard
)

# Resume operations
switchboard.pause(
    False,
    sender=emergency_manager.address
)
```

**Example Output**: Department paused/unpaused, emits `DepartmentPauseModified`

## Recovery Functions

### `recoverFunds`

Recovers tokens accidentally sent to the department contract.

```vyper
@external
def recoverFunds(_recipient: address, _asset: address):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_recipient` | `address` | Address to receive recovered funds |
| `_asset` | `address` | Token contract address to recover |

#### Returns

*Function does not return any values*

#### Access

Only callable by Switchboard-registered contracts

#### Events Emitted

- `DepartmentFundsRecovered` - Contains asset address (indexed), recipient (indexed), and balance recovered

#### Example Usage
```python
# Recover accidentally sent USDC
dept_basics.recoverFunds(
    treasury.address,      # Send to treasury
    usdc_token.address,    # Token to recover
    sender=recovery_mgr.address  # Must be in Switchboard
)
```

**Example Output**: Transfers full token balance, emits `DepartmentFundsRecovered`

### `recoverFundsMany`

Recovers multiple tokens in a single transaction.

```vyper
@external
def recoverFundsMany(_recipient: address, _assets: DynArray[address, MAX_RECOVER_ASSETS]):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_recipient` | `address` | Address to receive all recovered funds |
| `_assets` | `DynArray[address, MAX_RECOVER_ASSETS]` | List of token addresses (max 20) |

#### Returns

*Function does not return any values*

#### Access

Only callable by Switchboard-registered contracts

#### Events Emitted

- `DepartmentFundsRecovered` - One event per recovered asset

#### Example Usage
```python
# Recover multiple tokens at once
tokens = [usdc.address, dai.address, weth.address]
dept_basics.recoverFundsMany(
    treasury.address,
    tokens,
    sender=recovery_mgr.address
)
```

**Example Output**: Transfers all token balances, emits event for each

## Usage Pattern

```python
# Example parent contract implementation
class DepartmentContract:
    # Initialize module
    def __init__(self):
        deptBasics.__init__(
            False,  # Not paused
            True,   # Can mint Green
            False   # Cannot mint Ripe
        )
    
    # Check pause in operations
    def sensitive_operation(self):
        if deptBasics.isPaused:
            raise "Department is paused"
        # Perform operation
    
    # RipeHq checks minting capability
    def can_mint_check(self):
        # RipeHq calls canMintGreen() as part of
        # two-factor authentication for minting
        return deptBasics.canMintGreen()
```

## Integration with RipeHq

RipeHq uses DeptBasics minting declarations as part of its two-factor authentication:

1. **Configuration Check**: RipeHq checks if department has minting permission in HQ config
2. **Capability Check**: RipeHq calls `canMintGreen()` or `canMintRipe()` on the department
3. **Both Must Pass**: Minting only allowed if both checks return true

This ensures departments explicitly declare their minting intentions and prevents unauthorized minting even if misconfigured in RipeHq.

## Testing

For comprehensive test examples, see: [`tests/modules/test_dept_basics.py`](../tests/modules/test_dept_basics.py)