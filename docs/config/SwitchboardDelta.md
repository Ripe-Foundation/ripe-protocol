# SwitchboardDelta Technical Documentation

[📄 View Source Code](../../contracts/config/SwitchboardDelta.vy)

## Overview

SwitchboardDelta specializes in HR operations and Ripe bond mechanics for the Ripe Protocol, managing contributor compensation, bond sales parameters, and reward system maintenance as a dedicated control panel for human capital
and tokenomics.

**Management Areas**:
- **HR Configuration**: Controls contributor compensation templates, limits, vesting schedules, cliff periods, and start delays to ensure fair treatment while preventing exploitation
- **Contributor Operations**: Manages individual settings including manager assignments, paycheck cancellations, ownership transfers, and account freezing with both governance and lite action permissions
- **Bond Configuration**: Controls bond sale mechanics including asset selection, epoch parameters, pricing curves, lock bonuses, and auto-restart settings for sustainable token distribution
- **Reward Maintenance**: Provides cleanup and reset functions for the loot distribution system to correct errors or prepare for upgrades

The contract implements time-locked HR/bond configurations, immediate emergency actions, bond booster integration, comprehensive validation, and batch operations to ensure proper incentive alignment with operational flexibility.

## Architecture & Modules

SwitchboardDelta is built using a modular architecture with the following components:

### LocalGov Module
- **Location**: `contracts/modules/LocalGov.vy`
- **Purpose**: Provides governance functionality
- **Documentation**: See [LocalGov Technical Documentation](../modules/LocalGov.md)
- **Key Features**:
  - Governance address management
  - Permission validation
  - RipeHq integration
- **Exported Interface**: All governance functions via `gov.__interface__`

### TimeLock Module
- **Location**: `contracts/modules/TimeLock.vy`
- **Purpose**: Manages time-locked configuration changes
- **Documentation**: See [TimeLock Technical Documentation](../modules/TimeLock.md)
- **Key Features**:
  - Action ID generation
  - Time-lock enforcement
  - Action confirmation/cancellation
- **Exported Interface**: All timelock functions via `timeLock.__interface__`

### Module Initialization
```vyper
initializes: gov
initializes: timeLock[gov := gov]
```

## System Architecture Diagram

```
+------------------------------------------------------------------------+
|                       SwitchboardDelta Contract                        |
+------------------------------------------------------------------------+
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    HR Configuration Layer                        |  |
|  |                                                                  |  |
|  |  Template Management:          Compensation Limits:              |  |
|  |  - Contributor contract        - Max compensation amount         |  |
|  |  - Deployment template         - Min cliff period                |  |
|  |                                - Max start delay                 |  |
|  |                                - Vesting boundaries              |  |
|  |                                                                  |  |
|  |  Validation Rules:                                               |  |
|  |  - Cliff > 1 week minimum                                        |  |
|  |  - Vesting > 1 month minimum                                     |  |
|  |  - Max comp < 20M RIPE                                           |  |
|  |  - Start delay < 3 months                                        |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                  Contributor Operations Layer                    |  |
|  |                                                                  |  |
|  |  Time-locked Operations:       Immediate Operations:             |  |
|  |  - Set manager                - Cash Ripe check                 |  |
|  |  - Cancel paycheck            - Cancel transfers                |  |
|  |                                - Cancel ownership                |  |
|  |                                - Freeze/unfreeze                 |  |
|  |                                                                  |  |
|  |  Permission Model:                                               |  |
|  |  - Time-locked: Governance only                                  |  |
|  |  - Immediate: Governance OR lite action users                    |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                   Bond Configuration Layer                       |  |
|  |                                                                  |  |
|  |  Bond Parameters:             Epoch Management:                  |  |
|  |  - Asset selection            - Epoch length                     |  |
|  |  - Amount per epoch           - Start block                      |  |
|  |  - Min/max Ripe per unit      - Auto-restart                     |  |
|  |  - Lock bonus multiplier      - Restart delay                    |  |
|  |                                                                  |  |
|  |  Booster Integration:         Controls:                          |  |
|  |  - Set booster contract       - Enable/disable bonding           |  |
|  |  - Configure boost ratios     - Restart running epoch            |  |
|  |  - Set max units              - Set bad debt amount              |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                   Loot System Maintenance                        |  |
|  |                                                                  |  |
|  |  Reset Functions:                                                |  |
|  |  - User balance points (per asset/vault)                         |  |
|  |  - Asset points (global per asset/vault)                         |  |
|  |  - User borrow points                                            |  |
|  |                                                                  |  |
|  |  Use Cases:                                                      |  |
|  |  - Correct calculation errors                                    |  |
|  |  - Prepare for system upgrades                                   |  |
|  |  - Handle edge cases                                             |  |
|  +------------------------------------------------------------------+  |
+------------------------------------------------------------------------+
                                    |
        +---------------------------+---------------------------+
        |                           |                           |
        v                           v                           v
+------------------+    +-------------------+    +------------------+
| HrContributor    |    | BondRoom          |    | Lootbox          |
| * Manage vesting |    | * Execute bonds   |    | * Track rewards  |
| * Process checks |    | * Apply boosts    |    | * Calculate pts  |
| * Transfer RIPE  |    | * Manage epochs   |    | * Distribute     |
+------------------+    +-------------------+    +------------------+
```

## Data Structures

### ActionType Flag
Categorizes pending configuration changes:
```vyper
flag ActionType:
    HR_CONFIG_TEMPLATE         # Contributor contract template
    HR_CONFIG_MAX_COMP         # Maximum compensation
    HR_CONFIG_MIN_CLIFF        # Minimum cliff period
    HR_CONFIG_MAX_START_DELAY  # Maximum start delay
    HR_CONFIG_VESTING          # Vesting length boundaries
    HR_MANAGER                 # Set contributor manager
    HR_CANCEL_PAYCHECK         # Cancel contributor paycheck
    RIPE_BOND_CONFIG           # Main bond configuration
    RIPE_BOND_EPOCH_LENGTH     # Epoch duration
    RIPE_BOND_START_EPOCH      # Start epoch at block
    RIPE_BAD_DEBT              # Set bad debt amount
    RIPE_BOND_BOOSTER          # Set booster contract
    BOND_BOOSTER_ADD           # Add boost configs
    BOND_BOOSTER_BOUNDARIES    # Set boost limits
    LOOT_USER_BALANCE_RESET    # Reset user points
    LOOT_ASSET_RESET           # Reset asset points
    LOOT_USER_BORROW_RESET     # Reset borrow points
```

### Key Configuration Structures

```vyper
struct PendingManager:
    contributor: address
    pendingManager: address

struct BoosterConfig:
    user: address
    boostRatio: uint256
    maxUnitsAllowed: uint256
    expireBlock: uint256

struct UserBalanceReset:
    user: address
    asset: address
    vaultId: uint256

struct AssetReset:
    asset: address
    vaultId: uint256

struct BoosterBoundaries:
    maxBoostRatio: uint256
    maxUnits: uint256
```

## State Variables

### Public State Variables
- `actionType: HashMap[uint256, ActionType]` - Maps action IDs to types
- `pendingHrConfig: HashMap[uint256, cs.HrConfig]` - Pending HR configurations
- `pendingManager: HashMap[uint256, PendingManager]` - Pending manager assignments
- `pendingCancelPaycheck: HashMap[uint256, address]` - Pending paycheck cancellations
- `pendingRipeBondConfig: HashMap[uint256, cs.RipeBondConfig]` - Pending bond configs
- `pendingRipeBondConfigValue: HashMap[uint256, uint256]` - Pending numeric values
- `pendingBondBooster: HashMap[uint256, address]` - Pending booster contracts
- `pendingBoosterConfigs: HashMap[uint256, DynArray[BoosterConfig, 50]]` - Pending boosts
- `pendingUserBalanceReset: HashMap[uint256, DynArray[UserBalanceReset, 40]]` - User resets
- `pendingAssetReset: HashMap[uint256, DynArray[AssetReset, 20]]` - Asset resets

### Constants
- `HUNDRED_PERCENT: uint256 = 100_00` - 100.00% in basis points
- `MAX_BOOSTERS: uint256 = 50` - Maximum boost configurations
- `MAX_USERS: uint256 = 40` - Maximum users per reset
- `MAX_ASSETS: uint256 = 20` - Maximum assets per reset
- `DAY_IN_SECONDS: uint256 = 86400` - Time constants
- `WEEK_IN_SECONDS: uint256 = 604800`
- `MONTH_IN_SECONDS: uint256 = 2592000`
- `YEAR_IN_SECONDS: uint256 = 31536000`

## Constructor

### `__init__`

Initializes SwitchboardDelta with governance and time-lock settings.

```vyper
@deploy
def __init__(
    _ripeHq: address,
    _tempGov: address,
    _minConfigTimeLock: uint256,
    _maxConfigTimeLock: uint256,
):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_ripeHq` | `address` | RipeHq registry address |
| `_tempGov` | `address` | Initial governance address |
| `_minConfigTimeLock` | `uint256` | Minimum time-lock duration |
| `_maxConfigTimeLock` | `uint256` | Maximum time-lock duration |

## HR Configuration Functions

### `setContributorTemplate`

Sets the template contract for new contributors.

```vyper
@external
def setContributorTemplate(_contribTemplate: address) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_contribTemplate` | `address` | Template contract address |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Action ID for tracking |

#### Access

Only callable by governance

#### Validation

- Must be a deployed contract
- Cannot be empty address

### `setMaxCompensation`

Sets maximum allowed compensation per contributor.

```vyper
@external
def setMaxCompensation(_maxComp: uint256) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_maxComp` | `uint256` | Maximum RIPE compensation |

#### Validation

- Must be > 0 and ≤ 20 million RIPE

### `setMinCliffLength`

Sets minimum cliff period for vesting.

```vyper
@external
def setMinCliffLength(_minCliffLength: uint256) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_minCliffLength` | `uint256` | Minimum cliff in seconds |

#### Validation

- Must be > 1 week

### `setMaxStartDelay`

Sets maximum delay before vesting starts.

```vyper
@external
def setMaxStartDelay(_maxStartDelay: uint256) -> uint256:
```

#### Validation

- Must be ≤ 3 months

### `setVestingLengthBoundaries`

Sets minimum and maximum vesting periods.

```vyper
@external
def setVestingLengthBoundaries(
    _minVestingLength: uint256,
    _maxVestingLength: uint256
) -> uint256:
```

#### Validation

- Min > 1 month
- Max ≤ 5 years
- Min < Max

## Contributor Operation Functions

### Time-locked Operations

#### `setManagerForContributor`

Assigns a manager to a contributor.

```vyper
@external
def setManagerForContributor(
    _contributor: address,
    _manager: address
) -> uint256:
```

#### `cancelPaycheckForContributor`

Cancels a contributor's paycheck.

```vyper
@external
def cancelPaycheckForContributor(_contributor: address) -> uint256:
```

### Immediate Operations

#### `cashRipeCheckForContributor`

Immediately cashes a contributor's Ripe check.

```vyper
@external
def cashRipeCheckForContributor(_contributor: address) -> bool:
```

#### Access

Governance OR lite action users

#### `cancelRipeTransferForContributor`

Cancels pending Ripe transfer.

```vyper
@external
def cancelRipeTransferForContributor(_contributor: address) -> bool:
```

#### `cancelOwnershipChangeForContributor`

Cancels pending ownership change.

```vyper
@external
def cancelOwnershipChangeForContributor(_contributor: address) -> bool:
```

#### `freezeContributor`

Freezes or unfreezes a contributor account.

```vyper
@external
def freezeContributor(_contributor: address, _shouldFreeze: bool) -> bool:
```

#### Access

- **To Freeze**: Governance OR lite action users
- **To Unfreeze**: Only governance

## Ripe Bond Configuration Functions

### `setRipeBondConfig`

Sets comprehensive bond sale parameters.

```vyper
@external
def setRipeBondConfig(
    _asset: address,
    _amountPerEpoch: uint256,
    _minRipePerUnit: uint256,
    _maxRipePerUnit: uint256,
    _maxRipePerUnitLockBonus: uint256,
    _shouldAutoRestart: bool,
    _restartDelayBlocks: uint256,
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_asset` | `address` | Asset accepted for bonds |
| `_amountPerEpoch` | `uint256` | Asset amount per epoch |
| `_minRipePerUnit` | `uint256` | Minimum Ripe per asset |
| `_maxRipePerUnit` | `uint256` | Maximum Ripe per asset |
| `_maxRipePerUnitLockBonus` | `uint256` | Max lock bonus (1000% max) |
| `_shouldAutoRestart` | `bool` | Auto-restart epochs |
| `_restartDelayBlocks` | `uint256` | Blocks between epochs |

#### Access

Only callable by governance

#### Side Effects

Resets current epoch when executed

### `setRipeBondEpochLength`

Sets duration of bond epochs.

```vyper
@external
def setRipeBondEpochLength(_epochLength: uint256) -> uint256:
```

### `restartBondEpoch`

Immediately restarts the current epoch.

```vyper
@external
def restartBondEpoch() -> bool:
```

#### Validation

- Epoch must be in progress
- Current block must be within epoch range

### `setStartEpochAtBlock`

Schedules epoch start at specific block.

```vyper
@external
def setStartEpochAtBlock(_block: uint256 = 0) -> uint256:
```

### `setCanPurchaseRipeBond`

Enables or disables bond purchases.

```vyper
@external
def setCanPurchaseRipeBond(_canBond: bool) -> bool:
```

#### Access

- **To Disable**: Governance OR lite action users
- **To Enable**: Only governance

### `setBadDebt`

Sets protocol bad debt amount.

```vyper
@external
def setBadDebt(_amount: uint256) -> uint256:
```

## Bond Booster Functions

### `setRipeBondBooster`

Sets the bond booster contract.

```vyper
@external
def setRipeBondBooster(_bondBooster: address) -> uint256:
```

#### Validation

Contract must implement booster interface

### `setManyBondBoosters`

Configures multiple boost settings.

```vyper
@external
def setManyBondBoosters(
    _boosters: DynArray[BoosterConfig, MAX_BOOSTERS]
) -> uint256:
```

### `removeManyBondBoosters`

Removes boost configurations.

```vyper
@external
def removeManyBondBoosters(
    _users: DynArray[address, MAX_BOOSTERS]
) -> bool:
```

#### Access

Governance OR lite action users

### `setBoosterBoundaries`

Sets global boost limits.

```vyper
@external
def setBoosterBoundaries(
    _maxBoostRatio: uint256,
    _maxUnits: uint256
) -> uint256:
```

## Loot Cleanup Functions

### `resetManyUserBalancePoints`

Resets user balance points for specific assets/vaults.

```vyper
@external
def resetManyUserBalancePoints(
    _users: DynArray[UserBalanceReset, MAX_USERS]
) -> uint256:
```

### `resetManyAssetPoints`

Resets global asset points.

```vyper
@external
def resetManyAssetPoints(
    _assets: DynArray[AssetReset, MAX_ASSETS]
) -> uint256:
```

### `resetManyUserBorrowPoints`

Resets user borrowing points.

```vyper
@external
def resetManyUserBorrowPoints(
    _users: DynArray[address, MAX_USERS]
) -> uint256:
```

#### Access

All reset functions require governance

## Execution Functions

### `executePendingAction`

Executes a pending action after time-lock.

```vyper
@external
def executePendingAction(_aid: uint256) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_aid` | `uint256` | Action ID to execute |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if executed successfully |

#### Access

Only callable by governance

### `cancelPendingAction`

Cancels a pending action.

```vyper
@external
def cancelPendingAction(_aid: uint256) -> bool:
```

## Key Validation Logic

### HR Validation

1. **Compensation**: 0 < amount ≤ 20M RIPE
2. **Cliff Period**: > 1 week minimum
3. **Start Delay**: ≤ 3 months maximum
4. **Vesting Period**: 1 month < period ≤ 5 years

### Bond Configuration Validation

1. **Asset**: Must not be empty address
2. **Amounts**: Must be non-zero
3. **Price Range**: min < max
4. **Lock Bonus**: ≤ 1000% (10x)
5. **Epoch**: Must be in valid state for operations

### Booster Validation

1. **Contract**: Must implement interface
2. **Users**: Valid addresses
3. **Ratios**: Within protocol limits

## Security Considerations

1. **Time-lock Protection**: Critical HR and bond changes require time-locks
2. **Emergency Controls**: Lite actions for freezing and disabling
3. **Parameter Validation**: Comprehensive checks prevent exploitation
4. **Access Hierarchy**: Clear separation of governance vs operational permissions
5. **Contributor Protection**: Multiple safeguards for vesting contracts
6. **Economic Guards**: Limits on compensation and bond parameters

## Testing

For comprehensive test examples, see: [`tests/config/test_switchboard_delta.py`](../../tests/config/test_switchboard_delta.py)