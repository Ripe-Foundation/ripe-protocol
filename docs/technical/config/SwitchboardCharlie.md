# SwitchboardCharlie Technical Documentation

[📄 View Source Code](../../contracts/config/SwitchboardCharlie.vy)

## Overview

SwitchboardCharlie is the operational control center for day-to-day Ripe Protocol management, handling emergency responses, routine maintenance, and treasury operations that require either immediate action or careful time-locked
execution.

**Operational Domains**:
- **Emergency Response**: Rapid execution of pausing contracts, blacklisting addresses, locking accounts, and recovering funds via governance or lite action permissions
- **Protocol Maintenance**: Manages debt updates, reward distribution, loot claiming, and deposit point calculations to keep the protocol running smoothly
- **Auction Management**: Controls liquidation auction initiation and pausing with time-locked execution for orderly liquidations
- **Treasury Operations**: Manages yield farming, liquidity provision, token swaps, and partner integrations through time-locked transactions

The contract balances immediate execution for emergencies with time-locked execution for treasury operations, implementing batch processing, comprehensive logging, and flexible permissions for operational efficiency.

## Architecture & Modules

SwitchboardCharlie is built using a modular architecture with the following components:

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

### Addys Module (imported for interfaces)
- **Location**: `contracts/modules/Addys.vy`
- **Purpose**: Provides address resolution interfaces
- **Documentation**: See [Addys Technical Documentation](../modules/Addys.md)
- **Usage**: Used for UndyLego integration and type definitions

### Module Initialization
```vyper
initializes: gov
initializes: timeLock[gov := gov]
```

## System Architecture Diagram

```
+------------------------------------------------------------------------+
|                      SwitchboardCharlie Contract                       |
+------------------------------------------------------------------------+
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                   Emergency Response Layer                       |  |
|  |                                                                  |  |
|  |  Immediate Execution (No Time-lock):                             |  |
|  |  - Pause/Unpause contracts                                       |  |
|  |  - Blacklist/Unblacklist addresses                               |  |
|  |  - Lock/Unlock accounts                                          |  |
|  |  - Update user debt calculations                                 |  |
|  |  - Claim rewards and update points                               |  |
|  |                                                                  |  |
|  |  Permission Model:                                                |  |
|  |  - Enable actions: Governance only                               |  |
|  |  - Disable actions: Governance OR lite action users              |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                  Protocol Maintenance Layer                      |  |
|  |                                                                  |  |
|  |  Debt Management:              Reward Distribution:              |  |
|  |  - Update single user         - Claim loot for users            |  |
|  |  - Batch update users         - Update Ripe rewards             |  |
|  |                               - Claim deposit rewards           |  |
|  |                               - Update deposit points           |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                 Time-locked Operations Layer                     |  |
|  |                                                                  |  |
|  |  Fund Recovery:               Auction Control:                   |  |
|  |  - Recover single asset       - Start single auction             |  |
|  |  - Recover multiple assets    - Start many auctions              |  |
|  |  - Requires governance        - Pause single auction             |  |
|  |                               - Pause many auctions              |  |
|  |                                                                  |  |
|  |  Endaoment Operations:        Training Wheels:                   |  |
|  |  - Token swaps                - Set contract address             |  |
|  |  - Add/Remove liquidity       - Manage user access               |  |
|  |  - Partner minting                                               |  |
|  |  - NFT recovery                                                  |  |
|  +------------------------------------------------------------------+  |
+------------------------------------------------------------------------+
                                    |
        +---------------------------+---------------------------+
        |                           |                           |
        v                           v                           v
+------------------+    +-------------------+    +------------------+
| Protocol         |    | AuctionHouse      |    | Endaoment        |
| Contracts        |    | * Start auctions  |    | * Treasury ops   |
| * Pause/Unpause  |    | * Pause auctions  |    | * Yield farming  |
| * Fund recovery  |    |                   |    | * Liquidity mgmt |
+------------------+    +-------------------+    +------------------+
```

## Data Structures

### ActionType Flag
Categorizes pending time-locked operations:
```vyper
flag ActionType:
    RECOVER_FUNDS              # Single asset recovery
    RECOVER_FUNDS_MANY         # Multiple asset recovery
    START_AUCTION              # Start single liquidation
    START_MANY_AUCTIONS        # Start batch liquidations
    PAUSE_AUCTION              # Pause single auction
    PAUSE_MANY_AUCTIONS        # Pause batch auctions
    ENDAO_SWAP                 # Token swap operation
    ENDAO_ADD_LIQUIDITY        # Add LP position
    ENDAO_REMOVE_LIQUIDITY     # Remove LP position
    ENDAO_PARTNER_MINT         # Mint for partners
    ENDAO_PARTNER_POOL         # Partner liquidity
    ENDAO_REPAY                # Repay pool debt
    ENDOA_RECOVER_NFT          # Recover NFT
    TRAINING_WHEELS            # Set training wheels
```

### Key Operation Structures

```vyper
struct PauseAction:
    contractAddr: address
    shouldPause: bool

struct RecoverFundsAction:
    contractAddr: address
    recipient: address
    asset: address

struct FungAuctionConfig:
    liqUser: address
    vaultId: uint256
    asset: address

struct EndaoLiquidityAction:
    legoId: uint256
    pool: address
    tokenA: address
    tokenB: address
    amountA: uint256
    amountB: uint256
    minAmountA: uint256
    minAmountB: uint256
    minLpAmount: uint256
    extraData: bytes32
    lpToken: address
    lpAmount: uint256
```

## State Variables

### Public State Variables
- `actionType: HashMap[uint256, ActionType]` - Maps action IDs to operation types
- `pendingPauseActions: HashMap[uint256, PauseAction]` - Pending pause operations
- `pendingRecoverFundsActions: HashMap[uint256, RecoverFundsAction]` - Single asset recoveries
- `pendingRecoverFundsManyActions: HashMap[uint256, RecoverFundsManyAction]` - Batch recoveries
- `pendingStartAuctionActions: HashMap[uint256, FungAuctionConfig]` - Single auction starts
- `pendingStartManyAuctionsActions: HashMap[uint256, DynArray[FungAuctionConfig, 20]]` - Batch starts
- `pendingEndaoSwapActions: HashMap[uint256, DynArray[SwapInstruction, 5]]` - Swap operations
- `pendingTrainingWheels: HashMap[uint256, address]` - Training wheels updates

### Constants
- `MAX_RECOVER_ASSETS: uint256 = 20` - Max assets per recovery
- `MAX_AUCTIONS: uint256 = 20` - Max auctions per batch
- `MAX_TRAINING_WHEEL_ACCESS: uint256 = 25` - Max access updates
- `MAX_DEBT_UPDATES: uint256 = 50` - Max debt updates per batch
- `MAX_CLAIM_USERS: uint256 = 50` - Max users per claim batch
- `MAX_SWAP_INSTRUCTIONS: uint256 = 5` - Max swap steps

## Constructor

### `__init__`

Initializes SwitchboardCharlie with governance and time-lock settings.

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
| `_minConfigTimeLock` | `uint256` | Minimum time-lock for operations |
| `_maxConfigTimeLock` | `uint256` | Maximum time-lock for operations |

## Emergency Response Functions

### `pause`

Immediately pauses or unpauses a protocol contract.

```vyper
@external
def pause(_contractAddr: address, _shouldPause: bool) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_contractAddr` | `address` | Contract to pause/unpause |
| `_shouldPause` | `bool` | True to pause, false to unpause |

#### Access

- **To Pause**: Governance OR lite action users
- **To Unpause**: Only governance

#### Example Usage
```python
# Emergency pause
switchboard_charlie.pause(
    vulnerable_contract.address,
    True,
    sender=emergency_user.address
)

# Resume operations
switchboard_charlie.pause(
    vulnerable_contract.address,
    False,
    sender=governance.address
)
```

### `setBlacklist`

Blacklists or unblacklists an address for a specific token.

```vyper
@external
def setBlacklist(_tokenAddr: address, _addr: address, _shouldBlacklist: bool) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_tokenAddr` | `address` | Token contract |
| `_addr` | `address` | Address to blacklist |
| `_shouldBlacklist` | `bool` | True to blacklist |

#### Access

- **To Blacklist**: Governance OR lite action users
- **To Unblacklist**: Only governance

### `setLockedAccount`

Locks or unlocks a user account in the Ledger.

```vyper
@external
def setLockedAccount(_wallet: address, _shouldLock: bool) -> bool:
```

## Fund Recovery Functions

### `recoverFunds`

Initiates time-locked recovery of a single asset.

```vyper
@external
def recoverFunds(_contractAddr: address, _recipient: address, _asset: address) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_contractAddr` | `address` | Contract holding funds |
| `_recipient` | `address` | Recovery recipient |
| `_asset` | `address` | Asset to recover |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Action ID for tracking |

#### Access

Only callable by governance

#### Events Emitted

- `PendingRecoverFundsAction` - Contains recovery details and confirmation block

### `recoverFundsMany`

Initiates time-locked recovery of multiple assets.

```vyper
@external
def recoverFundsMany(
    _contractAddr: address,
    _recipient: address,
    _assets: DynArray[address, MAX_RECOVER_ASSETS]
) -> uint256:
```

## Debt Management Functions

### `updateDebtForUser`

Updates debt calculations for a single user.

```vyper
@external
def updateDebtForUser(_user: address) -> bool:
```

#### Access

Governance OR lite action users

#### Example Usage
```python
# Update user's debt
success = switchboard_charlie.updateDebtForUser(
    user.address,
    sender=keeper.address
)
```

### `updateDebtForManyUsers`

Batch updates debt for multiple users.

```vyper
@external
def updateDebtForManyUsers(_users: DynArray[address, MAX_DEBT_UPDATES]) -> bool:
```

## Reward Management Functions

### `claimLootForUser`

Claims rewards for a single user.

```vyper
@external
def claimLootForUser(_user: address, _shouldStake: bool) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User to claim for |
| `_shouldStake` | `bool` | Auto-stake rewards |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Ripe amount claimed |

### `claimLootForManyUsers`

Batch claims rewards for multiple users.

```vyper
@external
def claimLootForManyUsers(
    _users: DynArray[address, MAX_CLAIM_USERS],
    _shouldStake: bool
) -> uint256:
```

### `updateRipeRewards`

Updates global Ripe reward calculations.

```vyper
@external
def updateRipeRewards() -> bool:
```

### `claimDepositLootForAsset`

Claims deposit rewards for specific asset.

```vyper
@external
def claimDepositLootForAsset(
    _user: address,
    _vaultId: uint256,
    _asset: address
) -> uint256:
```

### `updateDepositPoints`

Updates deposit points for a specific user's vault position.

```vyper
@external
def updateDepositPoints(_user: address, _vaultId: uint256, _asset: address) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User whose points to update |
| `_vaultId` | `uint256` | Vault ID for the position |
| `_asset` | `address` | Asset to update points for |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if update successful |

#### Access

Governance OR lite action users

#### Example Usage
```python
# Update deposit points for user's position
success = switchboard_charlie.updateDepositPoints(
    user.address,
    vault_id,
    asset.address,
    sender=keeper.address
)
```

## Auction Management Functions

### `startAuction`

Initiates a time-locked auction start.

```vyper
@external
def startAuction(_liqUser: address, _vaultId: uint256, _asset: address) -> uint256:
```

#### Access

Only callable by governance

#### Validation

Checks if auction can be started before creating pending action

### `startManyAuctions`

Batch initiates auction starts.

```vyper
@external
def startManyAuctions(_auctions: DynArray[FungAuctionConfig, MAX_AUCTIONS]) -> uint256:
```

### `pauseAuction`

Initiates a time-locked auction pause.

```vyper
@external
def pauseAuction(_liqUser: address, _vaultId: uint256, _asset: address) -> uint256:
```

## Endaoment (Treasury) Functions

### Immediate Execution Functions

These functions execute immediately without time-lock:

#### `performEndaomentDeposit`
Deposits assets into yield strategies.

```vyper
@external
def performEndaomentDeposit(
    _legoId: uint256,
    _asset: address,
    _vaultAddr: address = empty(address),
    _amount: uint256 = max_value(uint256),
    _extraData: bytes32 = empty(bytes32),
) -> (uint256, address, uint256, uint256):
```

#### `performEndaomentWithdraw`
Withdraws from yield positions.

#### `performEndaomentRebalance`
Rebalances between yield strategies.

#### `performEndaomentEthToWeth`
Converts ETH to WETH.

#### `performEndaomentClaim`
Claims yield rewards.

### Time-locked Functions

These require governance and time-lock:

#### `performEndaomentSwap`
Executes token swaps.

```vyper
@external
def performEndaomentSwap(
    _instructions: DynArray[SwapInstruction, MAX_SWAP_INSTRUCTIONS]
) -> uint256:
```

#### `addLiquidityInEndaoment`
Adds liquidity to pools.

#### `removeLiquidityInEndaoment`
Removes liquidity from pools.

#### `mintPartnerLiquidityInEndaoment`
Mints Green tokens for partners.

## Training Wheels Functions

### `setTrainingWheels`

Sets the training wheels contract address (time-locked).

```vyper
@external
def setTrainingWheels(_trainingWheels: address) -> uint256:
```

### `setManyTrainingWheelsAccess`

Manages user access to training wheels (immediate).

```vyper
@external
def setManyTrainingWheelsAccess(
    _addr: address,
    _trainingWheels: DynArray[TrainingWheelAccess, MAX_TRAINING_WHEEL_ACCESS]
):
```

## Execution Functions

### `executePendingAction`

Executes a pending operation after time-lock.

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

Cancels a pending operation.

```vyper
@external
def cancelPendingAction(_aid: uint256) -> bool:
```

## Key Permission Models

### Lite Action Permissions

Functions requiring lite action permission:
- Pausing contracts (disable only)
- Blacklisting addresses (disable only)
- Locking accounts (disable only)
- Updating debt calculations
- Claiming rewards
- Updating deposit points
- Endaoment immediate operations

### Governance-Only Operations

Functions requiring governance:
- Unpausing contracts
- Removing blacklists
- Unlocking accounts
- Fund recovery
- Auction management
- Endaoment time-locked operations
- Training wheels configuration

## Security Considerations

1. **Permission Hierarchy**: Clear separation between emergency (lite) and governance actions
2. **Time-lock Protection**: High-value operations require time-locks
3. **Batch Limits**: Maximum sizes prevent gas exhaustion
4. **Parameter Validation**: Comprehensive checks on all inputs
5. **Event Logging**: Complete audit trail of all operations
6. **Fail-Safe Design**: Emergency functions prioritize safety over functionality

## Testing

For comprehensive test examples, see: [`tests/config/test_switchboard_charlie.py`](../../tests/config/test_switchboard_charlie.py)