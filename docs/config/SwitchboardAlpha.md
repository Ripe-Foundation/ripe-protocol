# SwitchboardAlpha Technical Documentation

[📄 View Source Code](../../contracts/config/SwitchboardAlpha.vy)

## Overview

SwitchboardAlpha is the primary configuration management contract for the Ripe Protocol, controlling critical protocol parameters through time-locked changes to ensure careful governance and system stability.

**Key Responsibilities**:
- **Protocol Configuration**: Manages deposit/withdrawal limits, debt settings, liquidation parameters, and rewards distribution through time-locked changes
- **Emergency Controls**: Enables rapid disabling of protocol functions by authorized users (lite actions) while requiring governance for re-enabling
- **Priority Management**: Optimizes protocol operations by managing prioritized lists for vaults, stability pools, and price sources
- **Rewards Configuration**: Controls Ripe token emissions, allocation percentages, and auto-staking parameters

The contract implements time-locked changes with action IDs, immediate emergency disabling, batch validation, and comprehensive event logging to ensure protocol stability with operational flexibility.

## Architecture & Modules

SwitchboardAlpha is built using a modular architecture with the following components:

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
|                      SwitchboardAlpha Contract                         |
+------------------------------------------------------------------------+
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                 Configuration Change Flow                        |  |
|  |                                                                  |  |
|  |  1. Governance initiates configuration change                    |  |
|  |     - Validates parameters                                       |  |
|  |     - Creates pending action with time-lock                      |  |
|  |     - Emits pending change event                                 |  |
|  |                                                                  |  |
|  |  2. Time-lock period passes                                      |  |
|  |     - Minimum wait time enforced                                 |  |
|  |     - Maximum expiry time checked                                 |  |
|  |                                                                  |  |
|  |  3. Governance executes pending action                           |  |
|  |     - Fetches current config from MissionControl                 |  |
|  |     - Updates specific parameters                                 |  |
|  |     - Writes back to MissionControl/Ledger                       |  |
|  |     - Emits confirmation event                                   |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Emergency Control Flow                        |  |
|  |                                                                  |  |
|  |  Enable Functions:                                                |  |
|  |  - Only governance can enable                                     |  |
|  |  - Immediate execution                                            |  |
|  |                                                                  |  |
|  |  Disable Functions:                                               |  |
|  |  - Governance OR lite action users                               |  |
|  |  - Immediate execution                                            |  |
|  |  - Critical for emergency response                               |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                   Configuration Categories                       |  |
|  |                                                                  |  |
|  |  General Config:        Debt Config:         Rewards Config:     |  |
|  |  - Vault limits         - Global limits      - Ripe per block    |  |
|  |  - Price staleness      - Borrow intervals  - Allocations       |  |
|  |  - Enable/disable       - Dynamic rates     - Auto-staking      |  |
|  |                         - Keeper fees                            |  |
|  |                         - Auction params                         |  |
|  |                                                                  |  |
|  |  Other Config:                                                   |  |
|  |  - Priority vaults/sources                                       |  |
|  |  - Underscore registry                                           |  |
|  |  - Lite action permissions                                       |  |
|  |  - Ripe gov vault settings                                       |  |
|  +------------------------------------------------------------------+  |
+------------------------------------------------------------------------+
                                    |
        +---------------------------+---------------------------+
        |                           |                           |
        v                           v                           v
+------------------+    +-------------------+    +------------------+
| MissionControl   |    | Ledger            |    | Switchboard      |
| * Stores configs |    | * Token supplies  |    | * Validates      |
| * Enforces rules |    | * Accounting      |    |   SwitchboardAlpha|
| * Protocol logic |    | * Ripe tracking   |    | * Access control |
+------------------+    +-------------------+    +------------------+
```

## Data Structures

### ActionType Flag
Categorizes pending configuration changes:
```vyper
flag ActionType:
    GEN_CONFIG_VAULT_LIMITS      # Vault count/asset limits
    GEN_CONFIG_STALE_TIME        # Price staleness threshold
    DEBT_GLOBAL_LIMITS           # Debt ceilings and minimums
    DEBT_BORROW_INTERVAL         # Rate limiting for borrows
    DEBT_DYNAMIC_RATE_CONFIG     # Dynamic interest rates
    DEBT_MAX_LTV_DEVIATION       # LTV calculation tolerance
    DEBT_KEEPER_CONFIG           # Liquidation keeper fees
    DEBT_LTV_PAYBACK_BUFFER      # Repayment buffer
    DEBT_AUCTION_PARAMS          # Liquidation auction settings
    RIPE_REWARDS_BLOCK           # Emission rate
    RIPE_REWARDS_ALLOCS          # Distribution percentages
    RIPE_REWARDS_AUTO_STAKE_PARAMS # Auto-staking config
    RIPE_AVAIL_REWARDS           # Available for rewards
    RIPE_AVAIL_HR                # Available for HR
    RIPE_AVAIL_BONDS             # Available for bonds
    OTHER_PRIORITY_LIQ_ASSET_VAULTS # Priority liquidation vaults
    OTHER_PRIORITY_STAB_VAULTS   # Priority stability vaults
    OTHER_PRIORITY_PRICE_SOURCE_IDS # Priority price sources
    OTHER_UNDERSCORE_REGISTRY    # Underscore protocol address
    OTHER_CAN_PERFORM_LITE_ACTION # Emergency permissions
    OTHER_SHOULD_CHECK_LAST_TOUCH # Touch validation
    RIPE_VAULT_CONFIG            # Governance vault settings
```

### GenConfigFlag Flag
Protocol enable/disable switches:
```vyper
flag GenConfigFlag:
    CAN_DEPOSIT
    CAN_WITHDRAW
    CAN_BORROW
    CAN_REPAY
    CAN_CLAIM_LOOT
    CAN_LIQUIDATE
    CAN_REDEEM_COLLATERAL
    CAN_REDEEM_IN_STAB_POOL
    CAN_BUY_IN_AUCTION
    CAN_CLAIM_IN_STAB_POOL
```

### GenConfigLite Struct
Simplified general configuration:
```vyper
struct GenConfigLite:
    perUserMaxVaults: uint256
    perUserMaxAssetsPerVault: uint256
    priceStaleTime: uint256
```

### CanPerform Struct
Lite action permission:
```vyper
struct CanPerform:
    user: address
    canDo: bool
```

### PendingRipeGovVaultConfig Struct
Governance vault configuration:
```vyper
struct PendingRipeGovVaultConfig:
    asset: address
    assetWeight: uint256
    shouldFreezeWhenBadDebt: bool
    lockTerms: cs.LockTerms
```

## State Variables

### Public State Variables
- `actionType: HashMap[uint256, ActionType]` - Maps action IDs to types
- `pendingRipeRewardsConfig: HashMap[uint256, RipeRewardsConfig]` - Pending rewards configs
- `pendingGeneralConfig: HashMap[uint256, GenConfigLite]` - Pending general configs
- `pendingDebtConfig: HashMap[uint256, GenDebtConfig]` - Pending debt configs
- `pendingPriorityLiqAssetVaults: HashMap[uint256, DynArray[VaultLite, 20]]` - Pending priority vaults
- `pendingPriorityStabVaults: HashMap[uint256, DynArray[VaultLite, 20]]` - Pending stability vaults
- `pendingPriorityPriceSourceIds: HashMap[uint256, DynArray[uint256, 10]]` - Pending price sources
- `pendingUnderscoreRegistry: HashMap[uint256, address]` - Pending Underscore address
- `pendingCanPerformLiteAction: HashMap[uint256, CanPerform]` - Pending permissions
- `pendingShouldCheckLastTouch: HashMap[uint256, bool]` - Pending touch settings
- `pendingRipeGovVaultConfig: HashMap[uint256, PendingRipeGovVaultConfig]` - Pending gov vault configs
- `pendingRipeAvailable: HashMap[uint256, uint256]` - Pending token availability

### Immutable Variables
- `MIN_STALE_TIME: immutable(uint256)` - Minimum price staleness allowed
- `MAX_STALE_TIME: immutable(uint256)` - Maximum price staleness allowed

### Transient Variables
- `vaultDedupe: transient(HashMap[uint256, HashMap[address, bool]])` - Deduplication helper

### Constants
- `MAX_PRIORITY_PRICE_SOURCES: uint256 = 10` - Max priority price sources
- `PRIORITY_VAULT_DATA: uint256 = 20` - Max priority vaults
- `UNDERSCORE_LEDGER_ID: uint256 = 2` - Underscore ledger registry ID
- `HUNDRED_PERCENT: uint256 = 100_00` - 100.00%
- `EIGHTEEN_DECIMALS: uint256 = 10 ** 18` - Standard decimals
- `LEDGER_ID: uint256 = 4` - Ledger registry ID
- `MISSION_CONTROL_ID: uint256 = 5` - MissionControl registry ID
- `PRICE_DESK_ID: uint256 = 7` - PriceDesk registry ID
- `VAULT_BOOK_ID: uint256 = 8` - VaultBook registry ID

## Constructor

### `__init__`

Initializes SwitchboardAlpha with governance and time-lock settings.

```vyper
@deploy
def __init__(
    _ripeHq: address,
    _tempGov: address,
    _minStaleTime: uint256,
    _maxStaleTime: uint256,
    _minConfigTimeLock: uint256,
    _maxConfigTimeLock: uint256,
):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_ripeHq` | `address` | RipeHq registry address |
| `_tempGov` | `address` | Initial governance address |
| `_minStaleTime` | `uint256` | Minimum allowed price staleness |
| `_maxStaleTime` | `uint256` | Maximum allowed price staleness |
| `_minConfigTimeLock` | `uint256` | Minimum time-lock for changes |
| `_maxConfigTimeLock` | `uint256` | Maximum time-lock for changes |

#### Returns

*Constructor does not return any values*

#### Access

Called only during deployment

#### Example Usage
```python
# Deploy SwitchboardAlpha
switchboard_alpha = boa.load(
    "contracts/config/SwitchboardAlpha.vy",
    ripe_hq.address,
    governance.address,
    300,    # 5 minutes min staleness
    3600,   # 1 hour max staleness
    100,    # Min config timelock
    10000   # Max config timelock
)
```

## General Configuration Functions

### `setVaultLimits`

Sets per-user vault and asset limits.

```vyper
@external
def setVaultLimits(_perUserMaxVaults: uint256, _perUserMaxAssetsPerVault: uint256) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_perUserMaxVaults` | `uint256` | Maximum vaults per user |
| `_perUserMaxAssetsPerVault` | `uint256` | Maximum assets per vault |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Action ID for tracking |

#### Access

Only callable by governance

#### Events Emitted

- `PendingVaultLimitsChange` - Contains limits and confirmation block

#### Example Usage
```python
# Set vault limits
action_id = switchboard_alpha.setVaultLimits(
    5,   # Max 5 vaults per user
    10,  # Max 10 assets per vault
    sender=governance.address
)
```

### `setStaleTime`

Sets price staleness threshold.

```vyper
@external
def setStaleTime(_staleTime: uint256) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_staleTime` | `uint256` | Maximum age for valid prices (seconds) |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Action ID |

#### Access

Only callable by governance

#### Events Emitted

- `PendingStaleTimeChange` - Contains stale time and confirmation block

### Enable/Disable Functions

Multiple functions control protocol operations:
- `setCanDeposit(_shouldEnable: bool)` - Enable/disable deposits
- `setCanWithdraw(_shouldEnable: bool)` - Enable/disable withdrawals
- `setCanBorrow(_shouldEnable: bool)` - Enable/disable borrowing
- `setCanRepay(_shouldEnable: bool)` - Enable/disable repayments
- `setCanClaimLoot(_shouldEnable: bool)` - Enable/disable loot claims
- `setCanLiquidate(_shouldEnable: bool)` - Enable/disable liquidations
- `setCanRedeemCollateral(_shouldEnable: bool)` - Enable/disable redemptions
- `setCanRedeemInStabPool(_shouldEnable: bool)` - Enable/disable stability pool redemptions
- `setCanBuyInAuction(_shouldEnable: bool)` - Enable/disable auction purchases
- `setCanClaimInStabPool(_shouldEnable: bool)` - Enable/disable stability pool claims

#### Access

- **To Enable**: Only governance
- **To Disable**: Governance OR users with lite action permission

#### Example Usage
```python
# Emergency: disable borrowing
switchboard_alpha.setCanBorrow(
    False,
    sender=emergency_user.address  # Has lite action permission
)

# Re-enable borrowing
switchboard_alpha.setCanBorrow(
    True,
    sender=governance.address  # Only governance can enable
)
```

## Debt Configuration Functions

### `setGlobalDebtLimits`

Sets protocol-wide debt limits.

```vyper
@external
def setGlobalDebtLimits(
    _perUserDebtLimit: uint256,
    _globalDebtLimit: uint256,
    _minDebtAmount: uint256,
    _numAllowedBorrowers: uint256
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_perUserDebtLimit` | `uint256` | Maximum debt per user |
| `_globalDebtLimit` | `uint256` | Total protocol debt ceiling |
| `_minDebtAmount` | `uint256` | Minimum borrowing amount |
| `_numAllowedBorrowers` | `uint256` | Maximum active borrowers |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Action ID |

#### Access

Only callable by governance

### `setBorrowIntervalConfig`

Sets rate limiting for borrowing.

```vyper
@external
def setBorrowIntervalConfig(
    _maxBorrowPerInterval: uint256,
    _numBlocksPerInterval: uint256
) -> uint256:
```

### `setDynamicRateConfig`

Configures dynamic interest rates.

```vyper
@external
def setDynamicRateConfig(
    _minDynamicRateBoost: uint256,
    _maxDynamicRateBoost: uint256,
    _increasePerDangerBlock: uint256,
    _maxBorrowRate: uint256
) -> uint256:
```

### `setKeeperConfig`

Sets liquidation keeper incentives.

```vyper
@external
def setKeeperConfig(
    _keeperFeeRatio: uint256,
    _minKeeperFee: uint256,
    _maxKeeperFee: uint256
) -> uint256:
```

### `setGenAuctionParams`

Configures liquidation auction parameters.

```vyper
@external
def setGenAuctionParams(
    _startDiscount: uint256,
    _maxDiscount: uint256,
    _delay: uint256,
    _duration: uint256
) -> uint256:
```

## Rewards Configuration Functions

### `setRipePerBlock`

Sets Ripe token emission rate.

```vyper
@external
def setRipePerBlock(_ripePerBlock: uint256) -> uint256:
```

### `setRipeRewardsAllocs`

Sets reward distribution percentages.

```vyper
@external
def setRipeRewardsAllocs(
    _borrowersAlloc: uint256,
    _stakersAlloc: uint256,
    _votersAlloc: uint256,
    _genDepositorsAlloc: uint256
) -> uint256:
```

### `setAutoStakeParams`

Configures automatic staking parameters.

```vyper
@external
def setAutoStakeParams(
    _autoStakeRatio: uint256,
    _autoStakeDurationRatio: uint256,
    _stabPoolRipePerDollarClaimed: uint256
) -> uint256:
```

## Priority Configuration Functions

### `setPriorityLiqAssetVaults`

Sets priority vaults for liquidations.

```vyper
@external
def setPriorityLiqAssetVaults(
    _priorityLiqAssetVaults: DynArray[VaultLite, PRIORITY_VAULT_DATA]
) -> uint256:
```

### `setPriorityStabVaults`

Sets priority stability pool vaults.

```vyper
@external
def setPriorityStabVaults(
    _priorityStabVaults: DynArray[VaultLite, PRIORITY_VAULT_DATA]
) -> uint256:
```

### `setPriorityPriceSourceIds`

Sets priority price sources.

```vyper
@external
def setPriorityPriceSourceIds(
    _priorityIds: DynArray[uint256, MAX_PRIORITY_PRICE_SOURCES]
) -> uint256:
```

## Execution Functions

### `executePendingAction`

Executes a pending configuration change after time-lock.

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

#### Example Usage
```python
# Execute after time-lock
boa.env.time_travel(blocks=timelock_period)
success = switchboard_alpha.executePendingAction(
    action_id,
    sender=governance.address
)
```

### `cancelPendingAction`

Cancels a pending configuration change.

```vyper
@external
def cancelPendingAction(_aid: uint256) -> bool:
```

## Validation Functions

### `areValidAuctionParams`

Validates auction parameters.

```vyper
@view
@external
def areValidAuctionParams(_params: AuctionParams) -> bool:
```

## Key Validation Logic

### Parameter Validation

Each setter validates parameters:
- Non-zero where required
- Within acceptable ranges
- Logical consistency (e.g., min < max)
- Not exceeding protocol limits

### Time-lock Enforcement

All configuration changes (except emergency disables):
1. Create pending action with unique ID
2. Set confirmation block based on time-lock
3. Require waiting period before execution
4. Allow cancellation before execution

### Emergency Response

Disable functions bypass time-lock when called by:
- Governance address
- Users with lite action permission

## Security Considerations

1. **Time-lock Protection**: All configuration changes require time-lock
2. **Emergency Response**: Quick disable capability for crisis management
3. **Parameter Validation**: Comprehensive checks prevent invalid configurations
4. **Access Control**: Strict governance requirements for enabling functions
5. **Event Logging**: Complete audit trail of all changes

## Testing

For comprehensive test examples, see: [`tests/config/test_switchboard_alpha.py`](../../tests/config/test_switchboard_alpha.py)