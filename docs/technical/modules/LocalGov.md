# LocalGov Technical Documentation

[📄 View Source Code](../../contracts/modules/LocalGov.vy)

## Overview

LocalGov is a flexible governance module implementing a two-tier system for the Ripe Protocol. It enables contracts to maintain local governance while respecting the protocol's global hierarchy, allowing both independent
management and centralized control through RipeHq when needed.

**Governance Structure**:
- **Hierarchical Control**: Supports both local governance (contract-specific) and global governance (RipeHq override)
- **Time-locked Transitions**: Two-step process with delays for all changes, requiring new governors to confirm their role
- **Flexible Operation**: Functions as either top-level governance (RipeHq) or subordinate module (departments)

The module implements secure transitions with configurable time-locks, supports governance relinquishment for decentralization, and includes special setup procedures for RipeHq initialization, balancing autonomy with
protocol-wide control.

## Governance Change Flow

```
Governance Change Process:
+--------------+      +--------------+      +--------------+
|   Initiate   |      |    Wait      |      |   Confirm    |
|   Change     | ---> |  Timelock    | ---> | (by new gov) |
+--------------+      +--------------+      +--------------+
       |                                             |
       |                    OR                       |
       v                                             v
+--------------+                            +--------------+
|   Cancel     |                            |   Applied    |
|   Change     |                            |   Change     |
+--------------+                            +--------------+

Special Cases:
* Setting to 0x0: Only allowed for non-RipeHq contracts
* Relinquish: Immediate transfer to 0x0 (local gov only)
* Initial Setup: Special one-time setup for RipeHq
```

## Data Structures

### PendingGovernance Struct
Tracks pending governance changes during the timelock period:
```vyper
struct PendingGovernance:
    newGov: address           # The new governance address
    initiatedBlock: uint256   # Block when change was initiated
    confirmBlock: uint256     # Block when change can be confirmed
```

## State Variables

### Public State Variables
- `governance: address` - Current local governance address
- `pendingGov: PendingGovernance` - Details of pending governance change
- `numGovChanges: uint256` - Total number of governance changes
- `govChangeTimeLock: uint256` - Current time-lock setting in blocks

### Immutable Variables
- `RIPE_HQ_FOR_GOV: address` - RipeHq address (empty for top-level governance)
- `MIN_GOV_TIME_LOCK: uint256` - Minimum allowed time-lock period
- `MAX_GOV_TIME_LOCK: uint256` - Maximum allowed time-lock period

## Constructor

### `__init__`

Initializes the LocalGov module with governance settings and time-lock parameters. Behavior differs based on whether this is for RipeHq (top-level) or a department (subordinate).

```vyper
@deploy
def __init__(
    _ripeHq: address,
    _initialGov: address,
    _minTimeLock: uint256,
    _maxTimeLock: uint256,
    _initialTimeLock: uint256,
):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_ripeHq` | `address` | RipeHq address (or empty for top-level governance) |
| `_initialGov` | `address` | Initial governance address |
| `_minTimeLock` | `uint256` | Minimum time-lock blocks (0 to inherit from [RipeHq](../../registries/RipeHq.md)) |
| `_maxTimeLock` | `uint256` | Maximum time-lock blocks (0 to inherit from [RipeHq](../../registries/RipeHq.md)) |
| `_initialTimeLock` | `uint256` | Initial time-lock setting |

#### Returns

*Constructor does not return any values*

#### Access

Called only during deployment

#### Example Usage
```python
# Deploy for RipeHq (top-level governance)
local_gov = boa.load(
    "contracts/modules/LocalGov.vy",
    empty(address),    # No RipeHq (this IS RipeHq)
    deployer.address,  # Initial governor
    100,              # Min timelock
    1000,             # Max timelock
    0                 # Initial timelock (skipped for RipeHq)
)

# Deploy for a department
dept_gov = boa.load(
    "contracts/modules/LocalGov.vy",
    ripe_hq.address,  # RipeHq address
    dept_owner,       # Initial local governor
    0,                # Inherit min from [RipeHq](../../registries/RipeHq.md)
    0,                # Inherit max from [RipeHq](../../registries/RipeHq.md)
    200               # Initial timelock
)
```

**Example Output**: Module deployed with governance settings. For RipeHq deployments, time-lock is not set initially. For departments, time-lock is set to max of minimum and requested initial value.

## Governance Query Functions

### `getRipeHqFromGov`

Returns the RipeHq address associated with this governance module.

```vyper
@view
@external
def getRipeHqFromGov() -> address:
```

#### Parameters

*Function has no parameters*

#### Returns

| Type | Description |
|------|-------------|
| `address` | The RipeHq address (or empty if this is top-level) |

#### Access

Public view function

#### Example Usage
```python
ripe_hq_addr = local_gov.getRipeHqFromGov()
# Returns: empty(address) for RipeHq itself
# Returns: ripe_hq.address for departments
```

### `canGovern`

Checks if an address has governance permissions (either local or from [RipeHq](../../registries/RipeHq.md)).

```vyper
@view
@external
def canGovern(_addr: address) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_addr` | `address` | The address to check |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if address can govern |

#### Access

Public view function

#### Example Usage
```python
# Check if an address can govern
can_gov = local_gov.canGovern(alice.address)
# Returns: True if alice is local gov or RipeHq gov
```

### `getGovernors`

Returns all addresses that can currently govern this contract.

```vyper
@view
@external
def getGovernors() -> DynArray[address, 2]:
```

#### Parameters

*Function has no parameters*

#### Returns

| Type | Description |
|------|-------------|
| `DynArray[address, 2]` | List of governors (max 2: local and RipeHq) |

#### Access

Public view function

#### Example Usage
```python
governors = local_gov.getGovernors()
# For RipeHq: returns [local_gov_address]
# For departments: returns [local_gov_address, ripe_hq_gov_address]
```

## Governance Change Functions

### `hasPendingGovChange`

Checks if there's a pending governance change.

```vyper
@view
@external
def hasPendingGovChange() -> bool:
```

#### Parameters

*Function has no parameters*

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if a governance change is pending |

#### Access

Public view function

#### Example Usage
```python
has_pending = local_gov.hasPendingGovChange()
# Returns: True if pendingGov.confirmBlock != 0
```

### `startGovernanceChange`

Initiates a governance change with time-lock protection.

```vyper
@external
def startGovernanceChange(_newGov: address):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_newGov` | `address` | The new governance address (can be empty for non-RipeHq) |

#### Returns

*Function does not return any values*

#### Access

Only callable by current governors

#### Events Emitted

- `GovChangeStarted` - Contains previous governor (indexed), new governor (indexed), and confirmation block

#### Example Usage
```python
# Start governance transfer
local_gov.startGovernanceChange(
    new_governor.address,
    sender=current_governor.address
)
```

**Example Output**: Emits `GovChangeStarted` event with confirmation block

### `confirmGovernanceChange`

Confirms a pending governance change after timelock. Must be called by the new governor.

```vyper
@external
def confirmGovernanceChange():
```

#### Parameters

*Function has no parameters*

#### Returns

*Function does not return any values*

#### Access

Only callable by the pending new governor (or current governors if setting to empty)

#### Events Emitted

- `GovChangeConfirmed` - Contains previous governor (indexed), new governor (indexed), initiation block, and confirmation block

#### Example Usage
```python
# Wait for timelock
boa.env.time_travel(blocks=time_lock)

# New governor confirms
local_gov.confirmGovernanceChange(sender=new_governor.address)
```

**Example Output**: Governance transferred, `numGovChanges` incremented

### `cancelGovernanceChange`

Cancels a pending governance change.

```vyper
@external
def cancelGovernanceChange():
```

#### Parameters

*Function has no parameters*

#### Returns

*Function does not return any values*

#### Access

Only callable by current governors

#### Events Emitted

- `GovChangeCancelled` - Contains cancelled governor (indexed), initiation block, and confirmation block

#### Example Usage
```python
# Cancel pending change
local_gov.cancelGovernanceChange(sender=current_governor.address)
```

**Example Output**: Pending change cleared, emits `GovChangeCancelled`

### `relinquishGov`

Immediately transfers governance to empty address. Only available for non-RipeHq contracts.

```vyper
@external
def relinquishGov():
```

#### Parameters

*Function has no parameters*

#### Returns

*Function does not return any values*

#### Access

Only callable by current local governance

#### Events Emitted

- `GovRelinquished` - Contains previous governor (indexed)

#### Example Usage
```python
# Local governor gives up control
dept_gov.relinquishGov(sender=local_governor.address)
```

**Example Output**: Governance set to empty, `numGovChanges` incremented

## Time-lock Configuration Functions

### `setGovTimeLock`

Updates the governance change time-lock period.

```vyper
@external
def setGovTimeLock(_numBlocks: uint256) -> bool:
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

Only callable by current governors

#### Events Emitted

- `GovChangeTimeLockModified` - Contains previous and new time-lock values

#### Example Usage
```python
# Update time-lock to 500 blocks
success = local_gov.setGovTimeLock(500, sender=governor.address)
assert success == True
```

**Example Output**: Time-lock updated, emits `GovChangeTimeLockModified`

### `isValidGovTimeLock`

Validates if a proposed time-lock value is acceptable.

```vyper
@view
@external
def isValidGovTimeLock(_newTimeLock: uint256) -> bool:
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
# Check if 500 blocks is valid
is_valid = local_gov.isValidGovTimeLock(500)
# Returns: True if within bounds and no pending change
```

### `minGovChangeTimeLock`

Returns the minimum allowed time-lock period.

```vyper
@view
@external
def minGovChangeTimeLock() -> uint256:
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
min_lock = local_gov.minGovChangeTimeLock()
# Returns: MIN_GOV_TIME_LOCK value
```

### `maxGovChangeTimeLock`

Returns the maximum allowed time-lock period.

```vyper
@view
@external
def maxGovChangeTimeLock() -> uint256:
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
max_lock = local_gov.maxGovChangeTimeLock()
# Returns: MAX_GOV_TIME_LOCK value
```

## RipeHq Setup Function

### `finishRipeHqSetup`

Special one-time setup function for RipeHq to set initial governance and time-lock.

```vyper
@external
def finishRipeHqSetup(_newGov: address, _timeLock: uint256 = 0) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_newGov` | `address` | The new governance address (must be a contract) |
| `_timeLock` | `uint256` | Initial time-lock (0 uses minimum) |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if setup completed successfully |

#### Access

Only callable by initial governance of RipeHq (one-time use)

#### Events Emitted

- `RipeHqSetupFinished` - Contains previous governor (indexed), new governor (indexed), and time-lock value

#### Example Usage
```python
# Complete RipeHq setup
success = ripe_hq.finishRipeHqSetup(
    final_governance.address,
    500,  # 500 block timelock
    sender=deployer.address
)
```

**Example Output**: Governance transferred, time-lock set, `numGovChanges` = 1

## Testing

For comprehensive test examples, see: [`tests/modules/test_local_gov.py`](../tests/modules/test_local_gov.py)