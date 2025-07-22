# TimeLock Technical Documentation

[📄 View Source Code](../../contracts/modules/TimeLock.vy)

## Overview

TimeLock is a flexible time-delay module for managing sensitive operations within the Ripe Protocol. It provides a universal timer mechanism that enforces waiting periods before action execution while preventing stale operations
through expiration windows, ensuring transparent and secure protocol changes.

**Key Features**:
- **Action Scheduling**: Sequential ID assignment with configurable delays before confirmation
- **Expiration Management**: Actions expire if not executed within the window, preventing indefinite pending operations
- **Flexible Configuration**: Adjustable time-lock and expiration parameters within governance-set bounds

The module integrates with LocalGov for access control, maintains pending action mappings, provides validation functions, and includes special setup procedures for initial deployment, promoting secure time-delayed operations
across protocol components.

## System Architecture Diagram

```
+---------------------------------------------------------------+
|                      TimeLock Module                          |
+---------------------------------------------------------------+
|                                                               |
|  +----------------------------------------------------------+ |
|  |                   Action Lifecycle                       | |
|  |                                                          | |
|  |  1. Initiate Action (returns actionId)                   | |
|  |     * Records initiatedBlock                             | |
|  |     * Sets confirmBlock = current + timeLock             | |
|  |     * Sets expiration = confirmBlock + expirationWindow  | |
|  |                                                          | |
|  |  2. Wait for Time-lock Period                            | |
|  |     * Action cannot be confirmed before confirmBlock     | |
|  |                                                          | |
|  |  3. Confirmation Window Opens                            | |
|  |     * Between confirmBlock and expiration                | |
|  |     * Action can be confirmed or cancelled               | |
|  |                                                          | |
|  |  4. Expiration (if not confirmed)                        | |
|  |     * After expiration block, action becomes invalid     | |
|  +----------------------------------------------------------+ |
|                                                               |
|  +----------------------------------------------------------+ |
|  |                  Core Components                         | |
|  |                                                          | |
|  |  * pendingActions: actionId -> PendingAction mapping     | |
|  |  * actionId: Sequential counter (starts at 1)            | |
|  |  * actionTimeLock: Current time-lock setting             | |
|  |  * expiration: Window after confirmBlock                 | |
|  +----------------------------------------------------------+ |
|                                                               |
|  +----------------------------------------------------------+ |
|  |               Governance Integration                     | |
|  |                                                          | |
|  |  * Uses LocalGov module for access control               | |
|  |  * Time-lock and expiration adjustable by governance     | |
|  |  * Bounded by MIN/MAX_ACTION_TIMELOCK                    | |
|  +----------------------------------------------------------+ |
+---------------------------------------------------------------+
                               |
                               v
+---------------------------------------------------------------+
|                 Parent Contract Integration                   |
|                                                               |
|  Example Usage:                                               |
|  1. Parent calls _initiateAction() -> gets actionId           |
|  2. Parent stores actionId with operation details             |
|  3. After time-lock, parent calls _confirmAction(actionId)    |
|  4. Parent executes operation if confirmation succeeds        |
+---------------------------------------------------------------+
```

## Data Structures

### PendingAction Struct
Tracks timing information for each pending action:
```vyper
struct PendingAction:
    initiatedBlock: uint256    # Block when action was initiated
    confirmBlock: uint256      # Block when action can be confirmed
    expiration: uint256        # Block when action expires
```

## State Variables

### Public State Variables
- `pendingActions: HashMap[uint256, PendingAction]` - Maps action ID to pending action data
- `actionId: uint256` - Next available action ID (sequential counter)
- `actionTimeLock: uint256` - Current time-lock setting in blocks
- `expiration: uint256` - Expiration window in blocks after confirmation time

### Immutable Variables
- `MIN_ACTION_TIMELOCK: uint256` - Minimum allowed time-lock period
- `MAX_ACTION_TIMELOCK: uint256` - Maximum allowed time-lock period

## Constructor

### `__init__`

Initializes the TimeLock module with time-lock bounds and expiration settings.

```vyper
@deploy
def __init__(
    _minActionTimeLock: uint256,
    _maxActionTimeLock: uint256,
    _initialTimeLock: uint256,
    _expiration: uint256,
):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_minActionTimeLock` | `uint256` | Minimum time-lock blocks allowed |
| `_maxActionTimeLock` | `uint256` | Maximum time-lock blocks allowed |
| `_initialTimeLock` | `uint256` | Initial time-lock setting (0 for setup phase) |
| `_expiration` | `uint256` | Expiration window in blocks after confirm time |

#### Returns

*Constructor does not return any values*

#### Access

Called only during deployment by parent contract

#### Example Usage
```python
# Initialize TimeLock module
time_lock.__init__(
    10,    # Min timelock: 10 blocks
    1000,  # Max timelock: 1000 blocks
    100,   # Initial timelock: 100 blocks
    500    # Expiration window: 500 blocks after confirm time
)
```

**Example Output**: Module initialized with actionId counter at 1, time-lock and expiration set

## Action Query Functions

### `canConfirmAction`

Checks if an action can be confirmed (time-lock passed, not expired).

```vyper
@view
@external
def canConfirmAction(_actionId: uint256) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_actionId` | `uint256` | The action ID to check |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if action can be confirmed |

#### Access

Public view function

#### Example Usage
```python
# Check if action 5 can be confirmed
can_confirm = time_lock.canConfirmAction(5)
# Returns: True if confirmBlock reached and not expired
```

### `isExpired`

Checks if an action has expired.

```vyper
@view
@external
def isExpired(_actionId: uint256) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_actionId` | `uint256` | The action ID to check |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if action has expired |

#### Access

Public view function

#### Example Usage
```python
# Check if action 5 has expired
expired = time_lock.isExpired(5)
# Returns: True if current block >= expiration block
```

### `hasPendingAction`

Checks if an action ID has a pending action.

```vyper
@view
@external
def hasPendingAction(_actionId: uint256) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_actionId` | `uint256` | The action ID to check |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if action is pending |

#### Access

Public view function

#### Example Usage
```python
# Check if action 5 is pending
has_pending = time_lock.hasPendingAction(5)
# Returns: True if action exists and not yet confirmed/cancelled
```

### `getActionConfirmationBlock`

Gets the confirmation block for a pending action.

```vyper
@view
@external
def getActionConfirmationBlock(_actionId: uint256) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_actionId` | `uint256` | The action ID |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | The block number when action can be confirmed (0 if not found) |

#### Access

Public view function

#### Example Usage
```python
# Get confirmation block for action 5
confirm_block = time_lock.getActionConfirmationBlock(5)
# Returns: Block number when confirmation is allowed
```

## Time-lock Configuration Functions

### `setActionTimeLock`

Updates the time-lock period for future actions.

```vyper
@external
def setActionTimeLock(_newTimeLock: uint256) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_newTimeLock` | `uint256` | New time-lock period in blocks |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if successfully updated |

#### Access

Only callable by governance (see [LocalGov](./LocalGov.md) for governance details)

#### Events Emitted

- `ActionTimeLockSet` - Contains previous and new time-lock values

#### Example Usage
```python
# Update time-lock to 200 blocks
success = time_lock.setActionTimeLock(
    200,
    sender=governance.address
)
assert success == True
```

**Example Output**: Time-lock updated, emits `ActionTimeLockSet`

### `isValidActionTimeLock`

Validates if a proposed time-lock value is acceptable.

```vyper
@view
@external
def isValidActionTimeLock(_newTimeLock: uint256) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_newTimeLock` | `uint256` | Proposed time-lock value |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if time-lock value is valid |

#### Access

Public view function

#### Example Usage
```python
# Check if 200 blocks is valid time-lock
is_valid = time_lock.isValidActionTimeLock(200)
# Returns: True if within bounds and different from current
```

### `minActionTimeLock`

Returns the minimum allowed time-lock period.

```vyper
@view
@external
def minActionTimeLock() -> uint256:
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
min_lock = time_lock.minActionTimeLock()
# Returns: 10 (example minimum)
```

### `maxActionTimeLock`

Returns the maximum allowed time-lock period.

```vyper
@view
@external
def maxActionTimeLock() -> uint256:
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
max_lock = time_lock.maxActionTimeLock()
# Returns: 1000 (example maximum)
```

### `setActionTimeLockAfterSetup`

Special function to set time-lock after initial setup phase (when time-lock is 0).

```vyper
@external
def setActionTimeLockAfterSetup(_newTimeLock: uint256 = 0) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_newTimeLock` | `uint256` | Time-lock value (0 uses minimum) |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if successfully set |

#### Access

Only callable by governance when time-lock is currently 0

#### Events Emitted

- `ActionTimeLockSet` - Contains previous (0) and new time-lock values

#### Example Usage
```python
# Complete setup with specific time-lock
success = time_lock.setActionTimeLockAfterSetup(
    150,  # Set to 150 blocks
    sender=governance.address
)

# Or use minimum
success = time_lock.setActionTimeLockAfterSetup(
    0,  # Use minimum
    sender=governance.address
)
```

**Example Output**: Time-lock set from 0 to specified value

## Expiration Configuration Functions

### `setExpiration`

Updates the expiration window for future actions.

```vyper
@external
def setExpiration(_expiration: uint256) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_expiration` | `uint256` | New expiration window in blocks |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if successfully updated |

#### Access

Only callable by governance (see [LocalGov](./LocalGov.md) for governance details)

#### Events Emitted

- `ExpirationSet` - Contains the new expiration value

#### Example Usage
```python
# Update expiration window to 1000 blocks
success = time_lock.setExpiration(
    1000,
    sender=governance.address
)
assert success == True
```

**Example Output**: Expiration updated, emits `ExpirationSet`

## Internal Functions

Note: The TimeLock module includes several internal functions that are called by the parent contract to manage actions:

- `_initiateAction()` - Creates a new pending action and returns its ID
- `_confirmAction(_actionId)` - Confirms a pending action if timing allows
- `_cancelAction(_actionId)` - Cancels a pending action
- `_canConfirmAction(_actionId)` - Internal check for confirmation validity
- `_isExpired(_actionId)` - Internal check for expiration
- `_hasPendingAction(_actionId)` - Internal check for pending status
- `_getActionConfirmationBlock(_actionId)` - Internal getter for confirm block

These functions do not emit events directly but are used by parent contracts to implement time-locked operations.

## Usage Pattern

```python
# Example parent contract usage
class ParentContract:
    def initiate_sensitive_operation(self):
        # Start time-locked action
        action_id = self._initiateAction()
        # Store action_id with operation details
        self.pending_operations[action_id] = operation_data
        return action_id
    
    def execute_sensitive_operation(self, action_id):
        # Verify action can be confirmed
        if not self._confirmAction(action_id):
            raise "Action cannot be confirmed"
        
        # Execute the operation
        operation_data = self.pending_operations[action_id]
        # ... perform operation ...
        
    def cancel_operation(self, action_id):
        # Cancel if needed
        if self._cancelAction(action_id):
            del self.pending_operations[action_id]
```

## Testing

For comprehensive test examples, see: [`tests/modules/test_time_lock.py`](../tests/modules/test_time_lock.py)