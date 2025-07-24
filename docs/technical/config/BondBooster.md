# BondBooster Technical Documentation

[📄 View Source Code](../../contracts/config/BondBooster.vy)

## Overview

BondBooster is a dynamic discount mechanism that incentivizes strategic bond purchases in the Ripe Protocol. It allows authorized users to purchase Ripe bonds at boosted rates during designated time periods, creating targeted
incentives for protocol participants.

**Core Functions**:
- **Boost Configuration**: Manages individual boost settings (ratios, limits, expiration) for authorized users
- **Usage Tracking**: Monitors boost consumption to enforce limits and prevent abuse
- **Validation & Limits**: Enforces protocol-wide and per-user constraints on boost ratios and usage

The contract implements time-based expiration, unit-based consumption tracking, configurable limits, batch operations, and comprehensive event logging to ensure controlled bond distribution while incentivizing strategic
participation.

## Architecture & Modules

BondBooster is built using a modular architecture with the following components:

### Addys Module
- **Location**: `contracts/modules/Addys.vy`
- **Purpose**: Provides protocol-wide address resolution
- **Documentation**: See [Addys Technical Documentation](../modules/Addys.md)
- **Key Features**:
  - Access to BondRoom address for permission validation
  - Switchboard validation for configuration updates
- **Exported Interface**: Address utilities via `addys.__interface__`

### DeptBasics Module
- **Location**: `contracts/modules/DeptBasics.vy`
- **Purpose**: Provides department-level functionality
- **Documentation**: See [DeptBasics Technical Documentation](../modules/DeptBasics.md)
- **Key Features**:
  - Department interface compliance
  - No minting capabilities (boost only affects ratios)
- **Exported Interface**: Department basics via `deptBasics.__interface__`

### Module Initialization
```vyper
initializes: addys
initializes: deptBasics[addys := addys]
```

## System Architecture Diagram

```
+------------------------------------------------------------------------+
|                        BondBooster Contract                            |
+------------------------------------------------------------------------+
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Boost Configuration Flow                      |  |
|  |                                                                  |  |
|  |  1. Switchboard sets boost configuration                         |  |
|  |     - User address                                               |  |
|  |     - Boost ratio (e.g., 2x normal rate)                         |  |
|  |     - Max units allowed                                          |  |
|  |     - Expiration block                                           |  |
|  |                                                                  |  |
|  |  2. User purchases bonds from BondRoom                           |  |
|  |     - BondRoom queries boost ratio                               |  |
|  |     - Applies boost to Ripe output                               |  |
|  |                                                                  |  |
|  |  3. BondRoom reports units used                                  |  |
|  |     - Updates consumption tracking                               |  |
|  |     - Enforces unit limits                                       |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                      Validation Logic                           |  |
|  |                                                                  |  |
|  |  Global Limits:                                                  |  |
|  |  - maxBoostRatio: Protocol-wide maximum boost                    |  |
|  |  - maxUnits: Maximum units per user                              |  |
|  |                                                                  |  |
|  |  Per-User Checks:                                                |  |
|  |  - Valid user address                                            |  |
|  |  - Boost ratio within limits                                     |  |
|  |  - Not expired                                                   |  |
|  |  - Units available                                               |  |
|  +------------------------------------------------------------------+  |
+------------------------------------------------------------------------+
                                    |
        +---------------------------+---------------------------+
        |                           |                           |
        v                           v                           v
+------------------+    +-------------------+    +------------------+
| Switchboard      |    | BondRoom          |    | Users            |
| * Set configs    |    | * Query boosts    |    | * Buy bonds      |
| * Manage users   |    | * Apply ratios    |    | * Get boosted    |
| * Remove boosts  |    | * Report usage    |    |   Ripe output    |
+------------------+    +-------------------+    +------------------+
```

## Data Structures

### BoosterConfig Struct
Individual user boost configuration:
```vyper
struct BoosterConfig:
    user: address               # User address eligible for boost
    boostRatio: uint256         # Boost multiplier (e.g., 20000 = 2x)
    maxUnitsAllowed: uint256    # Maximum units user can consume
    expireBlock: uint256        # Block when boost expires
```

## State Variables

### Public State Variables
- `config: HashMap[address, BoosterConfig]` - Maps user addresses to boost configurations
- `unitsUsed: HashMap[address, uint256]` - Tracks units consumed per user
- `maxBoostRatio: uint256` - Protocol-wide maximum boost ratio
- `maxUnits: uint256` - Protocol-wide maximum units per user

### Constants
- `MAX_BOOSTERS: uint256 = 50` - Maximum boosters in batch operations

## Constructor

### `__init__`

Initializes BondBooster with global limits.

```vyper
@deploy
def __init__(
    _ripeHq: address,
    _maxBoostRatio: uint256,
    _maxUnits: uint256,
):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_ripeHq` | `address` | RipeHq registry address |
| `_maxBoostRatio` | `uint256` | Maximum allowed boost ratio |
| `_maxUnits` | `uint256` | Maximum units per user |

#### Returns

*Constructor does not return any values*

#### Access

Called only during deployment

#### Example Usage
```python
# Deploy BondBooster
bond_booster = boa.load(
    "contracts/config/BondBooster.vy",
    ripe_hq.address,
    30000,  # 3x max boost
    1000    # 1000 max units
)
```

**Example Output**: Contract deployed with boost system ready

## Query Functions

### `getBoostRatio`

Gets the current boost ratio for a user.

```vyper
@view
@external
def getBoostRatio(_user: address, _units: uint256) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User to check |
| `_units` | `uint256` | Units being requested (currently unused) |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Boost ratio (0 if no boost or expired) |

#### Access

Public view function

#### Example Usage
```python
# Check user's boost ratio
boost = bond_booster.getBoostRatio(user.address, 100)
# Returns: 20000 (2x boost) or 0 if no/expired boost
```

**Example Output**: Returns configured boost ratio or 0

### `isValidBooster`

Validates a boost configuration.

```vyper
@view
@external
def isValidBooster(_config: BoosterConfig) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_config` | `BoosterConfig` | Configuration to validate |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if configuration is valid |

#### Access

Public view function

#### Example Usage
```python
# Validate boost configuration
config = BoosterConfig(
    user=user.address,
    boostRatio=20000,  # 2x
    maxUnitsAllowed=500,
    expireBlock=block.number + 100000
)
is_valid = bond_booster.isValidBooster(config)
```

## Usage Tracking Functions

### `addNewUnitsUsed`

Records units consumed during bond purchase.

```vyper
@external
def addNewUnitsUsed(_user: address, _newUnits: uint256):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User who consumed units |
| `_newUnits` | `uint256` | Units to add to consumption |

#### Access

Only callable by BondRoom contract

#### Example Usage
```python
# BondRoom reports 50 units used
bond_booster.addNewUnitsUsed(
    user.address,
    50,
    sender=bond_room.address
)
```

## Configuration Management Functions

### `setBondBooster`

Sets boost configuration for a single user.

```vyper
@external
def setBondBooster(_config: BoosterConfig):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_config` | `BoosterConfig` | Boost configuration |

#### Access

Only callable by Switchboard-registered contracts

#### Events Emitted

- `BondBoostModified` - Contains user, ratio, max units, and expiry

#### Example Usage
```python
# Set 2x boost for user
config = BoosterConfig(
    user=strategic_user.address,
    boostRatio=20000,  # 2x
    maxUnitsAllowed=1000,
    expireBlock=block.number + 100000
)
bond_booster.setBondBooster(
    config,
    sender=switchboard.address
)
```

### `setManyBondBoosters`

Batch sets boost configurations.

```vyper
@external
def setManyBondBoosters(_boosters: DynArray[BoosterConfig, MAX_BOOSTERS]):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_boosters` | `DynArray[BoosterConfig, 50]` | List of configurations |

#### Access

Only callable by Switchboard-registered contracts

#### Events Emitted

- `BondBoostModified` - One per configuration
- `ManyBondBoostersSet` - Summary event

#### Example Usage
```python
# Set boosts for multiple users
configs = [
    BoosterConfig(user1.address, 20000, 500, expire1),
    BoosterConfig(user2.address, 15000, 300, expire2),
    BoosterConfig(user3.address, 25000, 1000, expire3)
]
bond_booster.setManyBondBoosters(
    configs,
    sender=switchboard.address
)
```

### `removeBondBooster`

Removes boost configuration for a user.

```vyper
@external
def removeBondBooster(_user: address):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User to remove boost |

#### Access

Only callable by Switchboard-registered contracts

#### Events Emitted

- `BondBoostRemoved` - Contains user address

#### Example Usage
```python
# Remove user's boost
bond_booster.removeBondBooster(
    user.address,
    sender=switchboard.address
)
```

### `removeManyBondBoosters`

Batch removes boost configurations.

```vyper
@external
def removeManyBondBoosters(_users: DynArray[address, MAX_BOOSTERS]):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_users` | `DynArray[address, 50]` | Users to remove |

#### Access

Only callable by Switchboard-registered contracts

#### Events Emitted

- `BondBoostRemoved` - One per user removed

### `setMaxBoostAndMaxUnits`

Updates global boost limits.

```vyper
@external
def setMaxBoostAndMaxUnits(_maxBoostRatio: uint256, _maxUnitsAvail: uint256):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_maxBoostRatio` | `uint256` | New maximum boost ratio |
| `_maxUnitsAvail` | `uint256` | New maximum units per user |

#### Access

Only callable by Switchboard-registered contracts

#### Events Emitted

- `MaxBoostAndMaxUnitsSet` - Contains new limits

#### Example Usage
```python
# Update global limits
bond_booster.setMaxBoostAndMaxUnits(
    40000,  # 4x max boost
    2000,   # 2000 max units
    sender=switchboard.address
)
```

## Validation Logic

### Configuration Validation

A boost configuration is valid if:
1. User address is not empty
2. Boost ratio is between 1 and maxBoostRatio
3. Expiration block is in the future
4. Max units allowed is between 1 and maxUnits

### Usage Validation

A user can receive boost if:
1. They have a valid configuration
2. Configuration hasn't expired
3. They haven't exceeded their unit limit

## Key Mathematical Functions

### Boost Application

When BondRoom applies boost:
```
boostedRipeOutput = baseRipeOutput * boostRatio / 10000
```

Where boostRatio of 20000 = 2x multiplier

### Unit Consumption

Units typically represent Green tokens spent:
```
unitsConsumed = greenSpent / UNIT_SIZE
```

## Security Considerations

1. **Permission Control**: Only Switchboard can set configurations
2. **BondRoom Authority**: Only BondRoom can update usage
3. **Limit Enforcement**: Global and per-user limits prevent abuse
4. **Expiration**: Time-based expiry prevents perpetual boosts
5. **Zero Prevention**: Validates against zero values

## Testing

For comprehensive test examples, see: [`tests/config/test_bond_booster.py`](../../tests/config/test_bond_booster.py)