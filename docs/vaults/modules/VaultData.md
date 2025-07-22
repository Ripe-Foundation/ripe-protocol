# VaultData Module Technical Documentation

[📄 View Source Code](../../../contracts/vaults/modules/VaultData.vy)

## Overview

VaultData is the foundational data management module for all vault operations in Ripe Protocol. It serves as the universal database layer handling balance tracking, asset registration, and state management for every vault type - from basic vaults to complex stability pools.

**Core Functions**:
- **Balance Tracking**: Precise records of user balances (amounts or shares) with atomic operations
- **Asset Management**: Automatic registration and indexed lookups for efficient enumeration
- **Security Controls**: Pause functionality and fund recovery for emergency operations
- **Storage Optimization**: Dual-layer tracking prevents bloat while enabling fast queries

VaultData implements vault-agnostic state management supporting basic amounts, shares, and USD values through a unified interface. It provides atomic modifications with validation, maintains clean indexed arrays, and enables both user-centric and vault-centric data views for maximum flexibility.

## Architecture & Dependencies

VaultData is built as a foundational module with minimal dependencies:

### Core Dependencies
- **Addys**: Address resolution for protocol contracts and permissions
- **IERC20**: Token balance queries and transfer operations

### Module Dependencies
```vyper
uses: addys
import contracts.modules.Addys as addys
```

### Key Constants
- `MAX_RECOVER_ASSETS: constant(uint256) = 20` - Maximum assets recoverable in batch

## Data Structures

VaultData maintains several interconnected data structures for comprehensive asset and user management:

### Balance Tracking
```vyper
# Core balance storage
userBalances: public(HashMap[address, HashMap[address, uint256]])  # user -> asset -> balance
totalBalances: public(HashMap[address, uint256])                    # asset -> total balance
```

### User Asset Management
```vyper
# User-centric asset tracking
userAssets: public(HashMap[address, HashMap[uint256, address]])     # user -> index -> asset
indexOfUserAsset: public(HashMap[address, HashMap[address, uint256]]) # user -> asset -> index
numUserAssets: public(HashMap[address, uint256])                    # user -> asset count
```

### Vault Asset Management
```vyper
# Vault-wide asset tracking
vaultAssets: public(HashMap[uint256, address])                      # index -> asset
indexOfAsset: public(HashMap[address, uint256])                     # asset -> index
numAssets: public(uint256)                                          # total asset count
```

### Configuration
```vyper
isPaused: public(bool)                                              # Emergency pause state
```

## System Architecture Diagram

```
+------------------------------------------------------------------------+
|                        VaultData Module                               |
+------------------------------------------------------------------------+
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                      Balance Management                          |  |
|  |                                                                  |  |
|  |  Core Storage:                                                   |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ userBalances[user][asset] = balance/shares/value             │ |  |
|  |  │ totalBalances[asset] = total_balance/shares/value            │ |  |
|  |  │                                                             │ |  |
|  |  │ Balance Operations:                                         │ |  |
|  |  │ • _addBalanceOnDeposit(user, asset, amount, updateTotal)    │ |  |
|  |  │   - Increases user balance                                  │ |  |
|  |  │   - Optionally updates total balance                       │ |  |
|  |  │   - Handles asset registration automatically               │ |  |
|  |  │                                                             │ |  |
|  |  │ • _reduceBalanceOnWithdrawal(user, asset, amount, updateTotal) │  |
|  |  │   - Decreases user balance (capped by available)           │ |  |
|  |  │   - Optionally updates total balance                       │ |  |
|  |  │   - Returns actual amount and depletion status             │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                     Asset Registration System                   |  |
|  |                                                                  |  |
|  |  User Asset Tracking:                                            |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ userAssets[user][1] = ETH                                   │ |  |
|  |  │ userAssets[user][2] = USDC                                  │ |  |
|  |  │ userAssets[user][3] = WBTC                                  │ |  |
|  |  │                                                             │ |  |
|  |  │ indexOfUserAsset[user][ETH] = 1                             │ |  |
|  |  │ indexOfUserAsset[user][USDC] = 2                            │ |  |
|  |  │ indexOfUserAsset[user][WBTC] = 3                            │ |  |
|  |  │                                                             │ |  |
|  |  │ numUserAssets[user] = 4 (actual count = 3, index starts at 1) │  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  |                                                                  |  |
|  |  Vault Asset Tracking:                                           |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ vaultAssets[1] = ETH                                        │ |  |
|  |  │ vaultAssets[2] = USDC                                       │ |  |
|  |  │ vaultAssets[3] = WBTC                                       │ |  |
|  |  │                                                             │ |  |
|  |  │ indexOfAsset[ETH] = 1                                       │ |  |
|  |  │ indexOfAsset[USDC] = 2                                      │ |  |
|  |  │ indexOfAsset[WBTC] = 3                                      │ |  |
|  |  │                                                             │ |  |
|  |  │ numAssets = 4 (actual count = 3, index starts at 1)        │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Administrative Functions                      |  |
|  |                                                                  |  |
|  |  Emergency Controls:                                             |  |
|  |  • pause(shouldPause) - Emergency pause/unpause                  |  |
|  |  • isPaused - State check for all operations                     |  |
|  |                                                                  |  |
|  |  Asset Cleanup:                                                  |  |
|  |  • deregisterUserAsset(user, asset) - Remove empty positions    |  |
|  |  • deregisterVaultAsset(asset) - Remove unused vault assets     |  |
|  |                                                                  |  |
|  |  Fund Recovery:                                                  |  |
|  |  • recoverFunds(recipient, asset) - Recover untracked assets     |  |
|  |  • recoverFundsMany(recipient, assets) - Batch recovery          |  |
|  +------------------------------------------------------------------+  |
+------------------------------------------------------------------------+
                                    |
                                    |
                                    v
+------------------------------------------------------------------------+
|                          Usage by Vault Types                         |
+------------------------------------------------------------------------+
|                                                                        |
|  BasicVault:                     SharesVault:                          |
|  • Stores actual asset amounts   • Stores share amounts               |
|  • 1:1 amount to balance ratio   • Share-to-asset conversion needed   |
|  • Direct balance operations     • Yield accumulation via shares      |
|                                                                        |
|  StabVault:                                                            |
|  • Stores shares representing USD value                                |
|  • Complex value calculations including claimable assets               |
|  • USD-based accounting with price oracle integration                  |
|                                                                        |
|  All vault types use identical VaultData interface:                    |
|  • Same balance modification functions                                 |
|  • Same asset registration system                                      |
|  • Same pause and recovery mechanisms                                  |
|  • Interpretation of 'balance' varies by vault type                    |
+------------------------------------------------------------------------+
```

## Constructor

### `__init__`

Initializes VaultData with pause state configuration.

```vyper
@deploy
def __init__(_shouldPause: bool):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_shouldPause` | `bool` | Whether to start in paused state |

#### Access

Called during deployment

#### Example Usage
```python
# Deploy with vault initially active
vault_data = boa.load("contracts/vaults/modules/VaultData.vy", False)

# Deploy with vault initially paused for setup
vault_data = boa.load("contracts/vaults/modules/VaultData.vy", True)
```

## Core Balance Functions

### `_addBalanceOnDeposit`

Adds balance to a user's position with automatic asset registration.

```vyper
@internal
def _addBalanceOnDeposit(
    _user: address,
    _asset: address,
    _depositBal: uint256,
    _shouldUpdateTotal: bool,
):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User receiving the balance |
| `_asset` | `address` | Asset being deposited |
| `_depositBal` | `uint256` | Balance amount to add (amount/shares/value) |
| `_shouldUpdateTotal` | `bool` | Whether to update total balance |

#### Access

Internal function (called by vault modules)

#### Process Flow
1. **Balance Update**: Increases `userBalances[_user][_asset]` by deposit amount
2. **Total Update**: Optionally increases `totalBalances[_asset]` by deposit amount
3. **User Asset Registration**: Automatically registers asset for user if first time
4. **Vault Asset Registration**: Automatically registers asset for vault if first time

#### Usage Context
- **BasicVault**: `_depositBal` represents actual asset amount, `_shouldUpdateTotal` = True
- **SharesVault**: `_depositBal` represents share amount, `_shouldUpdateTotal` = True  
- **StabVault**: `_depositBal` represents share amount, `_shouldUpdateTotal` = True
- **Internal Transfers**: `_shouldUpdateTotal` = False (no net change in vault total)

#### Example Integration
```python
# In a vault's deposit function
def _handleDeposit(user: address, asset: address, amount: uint256):
    # Calculate shares or use amount directly
    balance_to_add = self._calculateBalanceToAdd(amount)
    
    # Add balance with total update
    vault_data._addBalanceOnDeposit(user, asset, balance_to_add, True)
```

### `_reduceBalanceOnWithdrawal`

Reduces balance from a user's position with amount validation.

```vyper
@internal
def _reduceBalanceOnWithdrawal(
    _user: address,
    _asset: address,
    _withdrawBal: uint256,
    _shouldUpdateTotal: bool,
) -> (uint256, bool):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User losing the balance |
| `_asset` | `address` | Asset being withdrawn |
| `_withdrawBal` | `uint256` | Balance amount to remove |
| `_shouldUpdateTotal` | `bool` | Whether to update total balance |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Actual amount withdrawn (may be less than requested) |
| `bool` | True if user's balance is now depleted |

#### Access

Internal function (called by vault modules)

#### Process Flow
1. **Validation**: Ensures user has registered position in this asset
2. **Amount Capping**: Limits withdrawal to user's available balance
3. **Balance Update**: Decreases `userBalances[_user][_asset]`
4. **Total Update**: Optionally decreases `totalBalances[_asset]`
5. **Depletion Check**: Returns whether user balance is now zero

#### Example Integration
```python
# In a vault's withdrawal function
def _handleWithdrawal(user: address, asset: address, requested: uint256):
    # Attempt to reduce balance
    actual_withdrawn, is_depleted = vault_data._reduceBalanceOnWithdrawal(
        user, asset, requested, True
    )
    
    # Handle post-withdrawal cleanup if needed
    if is_depleted:
        self._handleUserPositionDepletion(user, asset)
    
    return actual_withdrawn
```

## Asset Registration Functions

### User Asset Registration

#### `_registerUserAsset`

Automatically registers a new asset for a user when they first deposit.

```vyper
@internal
def _registerUserAsset(_user: address, _asset: address):
```

#### Process Flow
1. **Index Calculation**: Gets next available index (starting from 1, not 0)
2. **Asset Storage**: Stores asset at `userAssets[_user][index]`
3. **Index Mapping**: Creates reverse lookup at `indexOfUserAsset[_user][_asset]`
4. **Count Update**: Increments `numUserAssets[_user]`

#### `deregisterUserAsset`

Removes an asset from a user's registered assets when balance is zero.

```vyper
@external
def deregisterUserAsset(_user: address, _asset: address) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User to deregister asset for |
| `_asset` | `address` | Asset to deregister |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if user still has other assets |

#### Access

Only callable by [Lootbox](../../core/Lootbox.md) (for reward cleanup)

#### Process Flow
1. **Balance Check**: Ensures user balance is zero before deregistering
2. **Array Compression**: Moves last asset to fill gap of removed asset
3. **Index Update**: Updates reverse lookup mappings
4. **Count Reduction**: Decrements user asset count
5. **Status Return**: Returns whether user has remaining assets

#### Example Usage
```python
# Called by Lootbox to clean up empty positions
has_remaining_assets = vault_data.deregisterUserAsset(
    user.address,
    empty_asset.address,
    sender=lootbox.address
)
```

### Vault Asset Registration

#### `_registerVaultAsset`

Automatically registers a new asset for the vault when first seen.

```vyper
@internal
def _registerVaultAsset(_asset: address):
```

#### Process Flow
1. **Index Calculation**: Gets next available index (starting from 1, not 0)
2. **Asset Storage**: Stores asset at `vaultAssets[index]`
3. **Index Mapping**: Creates reverse lookup at `indexOfAsset[_asset]`
4. **Count Update**: Increments `numAssets`

#### `deregisterVaultAsset`

Removes an asset from vault's registered assets when total balance is zero.

```vyper
@external
def deregisterVaultAsset(_asset: address) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_asset` | `address` | Asset to deregister |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if deregistration successful |

#### Access

Only callable by [Switchboard](../../registries/Switchboard.md) addresses (governance)

#### Process Flow
1. **Balance Check**: Ensures total balance is zero before deregistering
2. **Array Compression**: Moves last asset to fill gap of removed asset
3. **Index Update**: Updates reverse lookup mappings
4. **Count Reduction**: Decrements vault asset count

## Query Functions

### User Asset Queries

#### `isUserInVaultAsset`

Checks if a user has a registered position in an asset.

```vyper
@view
@external
def isUserInVaultAsset(_user: address, _asset: address) -> bool:
```

#### `doesUserHaveBalance`

Checks if a user has a non-zero balance in an asset.

```vyper
@view
@external
def doesUserHaveBalance(_user: address, _asset: address) -> bool:
```

#### `getNumUserAssets`

Returns the number of assets a user has positions in.

```vyper
@view
@external
def getNumUserAssets(_user: address) -> uint256:
```

### Vault Asset Queries

#### `isSupportedVaultAsset`

Checks if an asset is registered in the vault.

```vyper
@view
@external
def isSupportedVaultAsset(_asset: address) -> bool:
```

#### `getNumVaultAssets`

Returns the number of assets supported by the vault.

```vyper
@view
@external
def getNumVaultAssets() -> uint256:
```

### Vault State Queries

#### `doesVaultHaveAnyFunds`

Checks if the vault has any non-zero asset balances.

```vyper
@view
@external
def doesVaultHaveAnyFunds() -> bool:
```

#### Process Flow
1. **Asset Iteration**: Loops through all registered vault assets
2. **Balance Check**: Checks `totalBalances[asset]` for each asset
3. **Early Return**: Returns True on first non-zero balance found
4. **Default Return**: Returns False if all balances are zero

#### Example Usage
```python
# Check if vault has any deposits before allowing certain operations
if vault_data.doesVaultHaveAnyFunds():
    # Proceed with operation that requires vault funds
    pass
else:
    # Handle empty vault case
    pass
```

## Administrative Functions

### Pause Management

#### `pause`

Controls vault-wide pause state for emergency situations.

```vyper
@external
def pause(_shouldPause: bool):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_shouldPause` | `bool` | New pause state |

#### Access

Only callable by [Switchboard](../../registries/Switchboard.md) addresses (governance)

#### Events Emitted

- `VaultPauseModified` - Contains new pause state

#### Example Usage
```python
# Emergency pause all vault operations
vault_data.pause(True, sender=governance.address)

# Resume vault operations
vault_data.pause(False, sender=governance.address)
```

### Fund Recovery

#### `recoverFunds`

Recovers untracked tokens from the vault contract.

```vyper
@external
def recoverFunds(_recipient: address, _asset: address):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_recipient` | `address` | Address to receive recovered funds |
| `_asset` | `address` | Asset to recover |

#### Access

Only callable by [Switchboard](../../registries/Switchboard.md) addresses (governance)

#### Validation
- Asset must not be registered in vault (`indexOfAsset[_asset] == 0`)
- Asset must have zero total balance (`totalBalances[_asset] == 0`)
- Asset must have actual token balance in contract

#### Events Emitted

- `VaultFundsRecovered` - Contains asset, recipient, and amount

#### `recoverFundsMany`

Batch version of fund recovery for multiple assets.

```vyper
@external
def recoverFundsMany(_recipient: address, _assets: DynArray[address, MAX_RECOVER_ASSETS]):
```

#### Example Usage
```python
# Recover accidentally sent tokens
vault_data.recoverFunds(
    treasury.address,
    mistaken_token.address,
    sender=governance.address
)

# Batch recovery
vault_data.recoverFundsMany(
    treasury.address,
    [token1.address, token2.address, token3.address],
    sender=governance.address
)
```

## Internal Utility Functions

### `_getNumUserAssets`

Internal version of user asset count query.

```vyper
@view
@internal
def _getNumUserAssets(_user: address) -> uint256:
```

Returns actual count (subtracts 1 since indices start at 1).

### `_getNumVaultAssets`

Internal version of vault asset count query.

```vyper
@view
@internal
def _getNumVaultAssets() -> uint256:
```

Returns actual count (subtracts 1 since indices start at 1).

## Data Structure Design

### Index Management

VaultData uses a "1-based indexing" system to distinguish between "not registered" (index 0) and "first position" (index 1):

```python
# Registration example
if indexOfUserAsset[user][asset] == 0:
    # Asset not registered for user
    aid = numUserAssets[user]
    if aid == 0:
        aid = 1  # Start at index 1, not 0
    
    userAssets[user][aid] = asset
    indexOfUserAsset[user][asset] = aid
    numUserAssets[user] = aid + 1
```

### Array Compression

When assets are deregistered, arrays are compressed to avoid gaps:

```python
# Deregistration example
targetIndex = indexOfUserAsset[user][asset]
lastIndex = numUserAssets[user] - 1

# Move last item to fill gap
if targetIndex != lastIndex:
    lastItem = userAssets[user][lastIndex]
    userAssets[user][targetIndex] = lastItem
    indexOfUserAsset[user][lastItem] = targetIndex

# Clear the last position
numUserAssets[user] = lastIndex
indexOfUserAsset[user][asset] = 0
```

## Security Considerations

### Access Control
- **Switchboard Only**: Administrative functions restricted to governance
- **Lootbox Only**: User asset deregistration restricted to reward system
- **Internal Only**: Balance modification functions only callable by vault modules

### Balance Safety
- **Amount Capping**: Withdrawals cannot exceed available balances
- **Existence Validation**: Operations require pre-existing user positions
- **Atomic Operations**: Balance updates are atomic and consistent

### Recovery Protection
- **Asset Isolation**: Can only recover untracked assets
- **Balance Verification**: Ensures no legitimate user funds are recovered
- **Event Logging**: All recovery operations are logged for transparency

## Integration Patterns

### Vault Module Integration
```python
# Typical vault deposit pattern
@external
def deposit(_asset: address, _amount: uint256):
    # 1. Transfer tokens to vault
    # 2. Calculate balance/shares to add
    # 3. Update VaultData
    vault_data._addBalanceOnDeposit(msg.sender, _asset, balance_amount, True)
    # 4. Emit events
```

### Balance Query Pattern
```python
# Check user position before operations
if vault_data.isUserInVaultAsset(user, asset):
    user_balance = vault_data.userBalances(user, asset)
    # Proceed with balance-dependent operation
```

### Asset Enumeration Pattern
```python
# Iterate through user assets
num_assets = vault_data.getNumUserAssets(user)
for i in range(1, num_assets + 1):  # Start at 1, not 0
    asset = vault_data.userAssets(user, i)
    balance = vault_data.userBalances(user, asset)
    # Process each asset position
```

## Testing

For comprehensive test examples, see: [`tests/vaults/test_vault_data.py`](../../tests/vaults/test_vault_data.py)