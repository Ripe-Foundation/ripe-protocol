# Lootbox Technical Documentation

[📄 View Source Code](../../contracts/core/Lootbox.vy)

## Overview

Lootbox is the rewards distribution engine for Ripe Protocol, implementing a sophisticated points-based system that tracks user activity and distributes Ripe tokens proportionally. It incentivizes productive protocol usage
through time-weighted participation scoring across multiple activities.

**Core Mechanics**:
- **Points Calculation**: Time-weighted scoring (balance × blocks) across borrowing, staking, voting, and general deposits for fair distribution
- **Multi-Tier Rewards**: Distributes block-based Ripe emissions across four user categories with configurable allocation percentages
- **Flexible Claiming**: Users can receive rewards directly or auto-stake in governance vault with configurable lock durations
- **Gas Optimization**: Intelligent storage cleanup removes empty positions, reducing gas costs for all users

The system implements block-level precision for point accumulation, USD value normalization for cross-asset fairness, fractional share calculations to prevent dust, batch processing for efficiency, and comprehensive event
logging for transparency.

## Architecture & Modules

Lootbox is built using a modular architecture with the following components:

### Addys Module
- **Location**: `contracts/modules/Addys.vy`
- **Purpose**: Provides protocol-wide address resolution
- **Documentation**: See [Addys Technical Documentation](../modules/Addys.md)
- **Key Features**:
  - Access to all protocol contract addresses
  - Validation of caller permissions
  - Centralized address management
- **Exported Interface**: Address utilities via `addys.__interface__`

### DeptBasics Module
- **Location**: `contracts/modules/DeptBasics.vy`
- **Purpose**: Provides department-level functionality
- **Documentation**: See [DeptBasics Technical Documentation](../modules/DeptBasics.md)
- **Key Features**:
  - Pause mechanism for emergency stops
  - Ripe token minting capability (for rewards)
  - No Green minting capability
- **Exported Interface**: Department basics via `deptBasics.__interface__`

### Module Initialization
```vyper
initializes: addys
initializes: deptBasics[addys := addys]
```

## System Architecture Diagram

```
+------------------------------------------------------------------------+
|                         Lootbox Contract                               |
+------------------------------------------------------------------------+
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Points Accumulation System                    |  |
|  |                                                                  |  |
|  |  Time-Weighted Scoring:                                          |  |
|  |  - User points = balance × elapsed_blocks                        |  |
|  |  - Asset points = total_balance × elapsed_blocks                 |  |
|  |  - Global points = total_usd_value × elapsed_blocks              |  |
|  |                                                                  |  |
|  |  Four Activity Types:                                            |  |
|  |  1. Borrowing: principal × blocks                                |  |
|  |  2. Staking: staked_amount × blocks                              |  |
|  |  3. Voting: governance_deposits × blocks                         |  |
|  |  4. General: other_deposits × blocks                             |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                  Reward Distribution Flow                        |  |
|  |                                                                  |  |
|  |  Block-Based Emissions:                                          |  |
|  |  - ripePerBlock × elapsed_blocks = total_new_ripe                |  |
|  |                                                                  |  |
|  |  Allocation Percentages:                                         |  |
|  |  - Borrowers: X%                                                 |  |
|  |  - Stakers: Y%                                                   |  |
|  |  - Voters: Z%                                                    |  |
|  |  - Gen Depositors: W%                                            |  |
|  |                                                                  |  |
|  |  User Share Calculation:                                         |  |
|  |  user_share = (user_points / total_points) × category_rewards    |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                   Auto-Staking & Distribution                    |  |
|  |                                                                  |  |
|  |  Claim Options:                                                  |  |
|  |  1. Direct Transfer: Ripe → user wallet                         |  |
|  |  2. Auto-Stake: Ripe → governance vault (locked)                |  |
|  |                                                                  |  |
|  |  Auto-Stake Ratio:                                               |  |
|  |  - Configurable percentage (0-100%)                             |  |
|  |  - Remainder sent directly to user                               |  |
|  |  - Lock duration per config                                      |  |
|  +------------------------------------------------------------------+  |
+------------------------------------------------------------------------+
                                    |
        +---------------------------+---------------------------+
        |                           |                           |
        v                           v                           v
+------------------+    +-------------------+    +------------------+
| Ledger           |    | MissionControl    |    | Vault System     |
| * Points storage |    | * Reward configs  |    | * User balances  |
| * Reward data    |    | * Allocations     |    | * Share calc     |
| * User tracking  |    | * Per-asset rules |    | * Balance track  |
+------------------+    +-------------------+    +------------------+
        |                           |                           |
        v                           v                           v
+------------------+    +-------------------+    +------------------+
| Ripe Token       |    | PriceDesk         |    | Teller           |
| * Mint rewards   |    | * USD valuations  |    | * Auto-stake     |
| * Governance     |    | * Value tracking  |    | * Proxy claims   |
+------------------+    +-------------------+    +------------------+
```

## Data Structures

### RipeRewards Struct
Global reward allocation tracking:
```vyper
struct RipeRewards:
    borrowers: uint256        # Rewards allocated to borrowers
    stakers: uint256         # Rewards for staking deposits
    voters: uint256          # Rewards for governance deposits  
    genDepositors: uint256   # Rewards for general deposits
    newRipeRewards: uint256  # New rewards this update
    lastUpdate: uint256      # Last update block
```

### UserDepositPoints Struct
Individual user deposit scoring:
```vyper
struct UserDepositPoints:
    balancePoints: uint256   # Accumulated balance × time
    lastBalance: uint256     # Last recorded balance
    lastUpdate: uint256      # Last update block
```

### AssetDepositPoints Struct
Per-asset deposit scoring:
```vyper
struct AssetDepositPoints:
    balancePoints: uint256      # Total balance × time for asset
    lastBalance: uint256        # Total balance last update
    lastUsdValue: uint256       # USD value at last update
    ripeStakerPoints: uint256   # Points for staker rewards
    ripeVotePoints: uint256     # Points for voter rewards
    ripeGenPoints: uint256      # Points for general rewards
    lastUpdate: uint256         # Last update block
    precision: uint256          # Decimal precision for calculations
```

### BorrowPoints Struct
Borrowing activity scoring:
```vyper
struct BorrowPoints:
    lastPrincipal: uint256   # Principal amount at last update
    points: uint256          # Accumulated principal × time
    lastUpdate: uint256      # Last update block
```

### RewardsConfig Struct
Protocol-wide reward configuration:
```vyper
struct RewardsConfig:
    arePointsEnabled: bool             # Global points toggle
    ripePerBlock: uint256              # Ripe emissions per block
    borrowersAlloc: uint256            # % for borrowers
    stakersAlloc: uint256              # % for stakers
    votersAlloc: uint256               # % for voters
    genDepositorsAlloc: uint256        # % for general deposits
    stakersPointsAllocTotal: uint256   # Total staker points allocation
    voterPointsAllocTotal: uint256     # Total voter points allocation
```

### ClaimLootConfig Struct
User claiming configuration:
```vyper
struct ClaimLootConfig:
    canClaimLoot: bool          # Global claiming enabled
    canClaimLootForUser: bool   # Allow proxy claiming
    autoStakeRatio: uint256     # Auto-stake percentage
    rewardsLockDuration: uint256  # Lock duration for staked rewards
```

## State Variables

### Constants
- `EIGHTEEN_DECIMALS: uint256 = 10 ** 18` - Standard precision
- `HUNDRED_PERCENT: uint256 = 100_00` - 100.00% in basis points
- `MAX_ASSETS_TO_CLEAN: uint256 = 20` - Cleanup batch limit
- `MAX_VAULTS_TO_CLEAN: uint256 = 10` - Vault cleanup limit
- `MAX_CLAIM_USERS: uint256 = 25` - Batch claim limit
- `RIPE_GOV_VAULT_ID: uint256 = 2` - Governance vault ID for staking

### Inherited State Variables
From [DeptBasics](../modules/DeptBasics.md):
- `isPaused: bool` - Department pause state
- `canMintRipe: bool` - Set to `True` for reward distribution

## Constructor

### `__init__`

Initializes Lootbox with Ripe minting capability for rewards.

```vyper
@deploy
def __init__(_ripeHq: address):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_ripeHq` | `address` | RipeHq contract address |

#### Returns

*Constructor does not return any values*

#### Access

Called only during deployment

#### Example Usage
```python
# Deploy Lootbox
lootbox = boa.load(
    "contracts/core/Lootbox.vy",
    ripe_hq.address
)
```

**Example Output**: Contract deployed with rewards distribution capability

## Reward Claiming Functions

### `claimLootForUser`

Claims all accumulated rewards for a single user.

```vyper
@external
def claimLootForUser(
    _user: address,
    _caller: address,
    _shouldStake: bool,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User to claim rewards for |
| `_caller` | `address` | Transaction initiator |
| `_shouldStake` | `bool` | Whether to auto-stake rewards |
| `_a` | `addys.Addys` | Cached addresses (optional) |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Total Ripe tokens claimed |

#### Access

Only callable by valid Ripe addresses

#### Events Emitted

- `BorrowLootClaimed` - Borrowing rewards claimed
- `DepositLootClaimed` - Deposit rewards claimed (per vault/asset)

#### Example Usage
```python
# User claims their rewards
total_ripe = lootbox.claimLootForUser(
    user.address,
    user.address,
    True,  # Auto-stake rewards
    sender=teller.address
)
```

**Example Output**: Calculates and distributes accumulated rewards across all user positions

### `claimLootForManyUsers`

Claims rewards for multiple users in batch.

```vyper
@external
def claimLootForManyUsers(
    _users: DynArray[address, MAX_CLAIM_USERS],
    _caller: address,
    _shouldStake: bool,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_users` | `DynArray[address, 25]` | Users to claim for |
| `_caller` | `address` | Transaction initiator |
| `_shouldStake` | `bool` | Auto-stake all rewards |
| `_a` | `addys.Addys` | Cached addresses (optional) |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Total Ripe tokens claimed for all users |

#### Access

Only callable by valid Ripe addresses

#### Example Usage
```python
# Batch claim for multiple users
users = [user1.address, user2.address, user3.address]
total_claimed = lootbox.claimLootForManyUsers(
    users,
    reward_claimer.address,
    False,  # Don't auto-stake
    sender=rewards_bot.address
)
```

### `getClaimableLoot`

Previews total claimable rewards for a user.

```vyper
@view
@external
def getClaimableLoot(_user: address) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User to check |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Total claimable Ripe tokens |

#### Access

Public view function

#### Example Usage
```python
# Check claimable rewards
claimable = lootbox.getClaimableLoot(user.address)
# Returns: Total Ripe tokens available to claim
```

## Granular Claiming Functions

### `claimDepositLootForAsset`

Claims rewards for a single deposit position rather than all positions.

```vyper
@external
def claimDepositLootForAsset(
    _user: address,
    _vaultId: uint256,
    _asset: address
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User to claim rewards for |
| `_vaultId` | `uint256` | Specific vault ID |
| `_asset` | `address` | Specific asset to claim for |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Ripe tokens claimed for this position |

#### Access

Only callable by valid Ripe addresses

#### Events Emitted

- `DepositLootClaimed` - Deposit rewards claimed for specific position

#### Example Usage
```python
# Claim rewards for only USDC deposits in vault 1
claimed = lootbox.claimDepositLootForAsset(
    user.address,
    1,  # Vault ID
    usdc.address,
    sender=teller.address
)
```

**Example Output**: Claims and distributes rewards for a single deposit position

### `claimBorrowLoot`

Claims only borrowing-related rewards for a user.

```vyper
@external
def claimBorrowLoot(_user: address) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User to claim borrowing rewards for |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Ripe tokens claimed from borrowing |

#### Access

Only callable by valid Ripe addresses

#### Events Emitted

- `BorrowLootClaimed` - Borrowing rewards claimed

#### Example Usage
```python
# Claim only borrowing rewards
borrow_rewards = lootbox.claimBorrowLoot(
    user.address,
    sender=teller.address
)
```

**Example Output**: Claims rewards accumulated from borrowing activities only

### `getClaimableDepositLootForAsset`

Previews claimable rewards for a specific deposit position.

```vyper
@view
@external
def getClaimableDepositLootForAsset(
    _user: address,
    _vaultId: uint256,
    _asset: address
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User to check |
| `_vaultId` | `uint256` | Vault ID |
| `_asset` | `address` | Asset to check |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Claimable Ripe tokens for this position |

#### Access

Public view function

#### Example Usage
```python
# Check rewards for specific position
position_rewards = lootbox.getClaimableDepositLootForAsset(
    user.address,
    1,  # Vault ID
    usdc.address
)
```

### `getClaimableBorrowLoot`

Previews claimable borrowing rewards.

```vyper
@view
@external
def getClaimableBorrowLoot(_user: address) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User to check |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Claimable Ripe tokens from borrowing |

#### Access

Public view function

#### Example Usage
```python
# Check borrowing rewards
borrow_rewards = lootbox.getClaimableBorrowLoot(user.address)
```

## Points Update Functions

### `updateDepositPoints`

Updates deposit-related points for a user position.

```vyper
@external
def updateDepositPoints(
    _user: address,
    _vaultId: uint256,
    _vaultAddr: address,
    _asset: address,
    _a: addys.Addys = empty(addys.Addys),
):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User whose points to update |
| `_vaultId` | `uint256` | Vault ID |
| `_vaultAddr` | `address` | Vault contract address |
| `_asset` | `address` | Asset being deposited |
| `_a` | `addys.Addys` | Cached addresses (optional) |

#### Access

Only callable by valid Ripe addresses

#### Example Usage
```python
# Update points after deposit
lootbox.updateDepositPoints(
    user.address,
    1,  # Vault ID
    vault.address,
    usdc.address,
    sender=teller.address
)
```

### `updateBorrowPoints`

Updates borrowing-related points for a user.

```vyper
@external
def updateBorrowPoints(_user: address, _a: addys.Addys = empty(addys.Addys)):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User whose points to update |
| `_a` | `addys.Addys` | Cached addresses (optional) |

#### Access

Only callable by valid Ripe addresses

#### Example Usage
```python
# Update points after borrow
lootbox.updateBorrowPoints(
    user.address,
    sender=credit_engine.address
)
```

### `resetUserBorrowPoints`

Resets a user's borrowing points (used for liquidations).

```vyper
@external
def resetUserBorrowPoints(_user: address):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User whose points to reset |

#### Access

Only callable by Switchboard-registered contracts

#### Example Usage
```python
# Reset points on liquidation
lootbox.resetUserBorrowPoints(
    liquidated_user.address,
    sender=liquidation_manager.address
)
```

## Administrative Reset Functions

### `resetUserBalancePoints`

Resets a single user's deposit points for one specific asset. Used for maintenance or correcting state.

```vyper
@external
def resetUserBalancePoints(
    _user: address,
    _asset: address,
    _vaultId: uint256
):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User whose points to reset |
| `_asset` | `address` | Specific asset to reset |
| `_vaultId` | `uint256` | Vault ID for the position |

#### Access

Only callable by Switchboard-registered contracts

#### Example Usage
```python
# Reset user's USDC points in vault 1
lootbox.resetUserBalancePoints(
    user.address,
    usdc.address,
    1,  # Vault ID
    sender=admin_contract.address
)
```

**Example Output**: Resets the user's accumulated points for the specified position to zero

### `resetAssetPoints`

Resets the entire points cache for a specific asset within a vault. Affects all users holding this asset.

```vyper
@external
def resetAssetPoints(
    _asset: address,
    _vaultId: uint256
):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_asset` | `address` | Asset to reset points for |
| `_vaultId` | `uint256` | Vault ID containing the asset |

#### Access

Only callable by Switchboard-registered contracts

#### Example Usage
```python
# Reset all USDC points in vault 1
lootbox.resetAssetPoints(
    usdc.address,
    1,  # Vault ID
    sender=admin_contract.address
)
```

**Example Output**: Resets accumulated points for all users holding this asset in the specified vault

## View Functions

### `getLatestDepositPoints`

Gets current deposit points for a user position.

```vyper
@view
@external
def getLatestDepositPoints(
    _user: address,
    _vaultId: uint256,
    _asset: address,
    _a: addys.Addys = empty(addys.Addys),
) -> (UserDepositPoints, AssetDepositPoints, GlobalDepositPoints):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User to check |
| `_vaultId` | `uint256` | Vault ID |
| `_asset` | `address` | Asset in vault |
| `_a` | `addys.Addys` | Cached addresses (optional) |

#### Returns

| Type | Description |
|------|-------------|
| `(UserDepositPoints, AssetDepositPoints, GlobalDepositPoints)` | Current points data |

#### Access

Public view function

### `getLatestBorrowPoints`

Gets current borrowing points for a user.

```vyper
@view
@external
def getLatestBorrowPoints(
    _user: address, 
    _a: addys.Addys = empty(addys.Addys)
) -> (BorrowPoints, BorrowPoints):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User to check |
| `_a` | `addys.Addys` | Cached addresses (optional) |

#### Returns

| Type | Description |
|------|-------------|
| `(BorrowPoints, BorrowPoints)` | (userPoints, globalPoints) |

#### Access

Public view function

## Global Rewards Update Functions

### `updateRipeRewards`

Manually triggers an update of the global Ripe reward buckets based on block-based emissions. This function calculates new rewards and distributes them across the four reward categories.

```vyper
@external
def updateRipeRewards():
```

#### Parameters

*This function takes no parameters*

#### Access

Only callable by valid Ripe addresses

#### Example Usage
```python
# Manually update global rewards
lootbox.updateRipeRewards(sender=rewards_updater.address)
```

**Example Output**: Updates global reward pools based on `ripePerBlock` emissions and allocation percentages

### `getLatestGlobalRipeRewards`

Previews the state of global reward buckets after accounting for block-based emissions. This is a view function that shows what the rewards would be if updated now.

```vyper
@view
@external
def getLatestGlobalRipeRewards() -> RipeRewards:
```

#### Parameters

*This function takes no parameters*

#### Returns

| Type | Description |
|------|-------------|
| `RipeRewards` | Current global rewards state including borrowers, stakers, voters, and general depositors allocations |

#### Access

Public view function

#### Example Usage
```python
# Check current global rewards state
rewards = lootbox.getLatestGlobalRipeRewards()
# Returns RipeRewards struct with:
# - borrowers: Total rewards for borrowers
# - stakers: Total rewards for stakers
# - voters: Total rewards for voters
# - genDepositors: Total rewards for general depositors
# - newRipeRewards: New rewards since last update
# - lastUpdate: Block number of last update
```

## Key Mathematical Functions

### Time-Weighted Points

Points accumulate based on balance × time:

```
points = balance × elapsed_blocks
```

This ensures users who hold larger positions for longer periods receive proportionally higher rewards.

### Reward Share Calculation

User's share of category rewards:

```
user_share = (user_points / total_category_points) × category_allocation
```

Categories are independent, so a user can earn from multiple categories simultaneously.

### Auto-Stake Distribution

When auto-staking is enabled:

```
stake_amount = total_rewards × auto_stake_ratio / 100%
direct_amount = total_rewards - stake_amount
```

### USD Value Normalization

To prevent overflow in calculations:

```
normalized_usd_value = raw_usd_value / 10^18
```

This reduces precision but prevents arithmetic overflow in long-running calculations.

## Storage Optimization

The contract implements automatic cleanup:

1. **Asset Cleanup**: Removes user-asset associations when balance reaches zero
2. **Vault Cleanup**: Removes user-vault associations when no assets remain
3. **Batch Processing**: Limits cleanup operations to prevent gas issues

## Testing

For comprehensive test examples, see: [`tests/core/test_lootbox.py`](../../tests/core/test_lootbox.py)