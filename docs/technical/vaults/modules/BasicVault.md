# BasicVault Module Technical Documentation

[📄 View Source Code](../../../contracts/vaults/modules/BasicVault.vy)

## Overview

BasicVault is the foundational vault module in Ripe Protocol, providing essential deposit, withdrawal, and transfer operations for all vault types. It handles the core mechanics of asset movement while maintaining accurate balance tracking through integration with VaultData.

**Core Functions**:
- **Asset Operations**: Secure deposits, withdrawals, and internal transfers with balance accounting
- **State Management**: User balances and asset registrations via VaultData interface
- **Protocol Integration**: Utility functions for Teller, CreditEngine, Lootbox, and AuctionHouse

Built as a base layer for other vault modules, BasicVault implements pause-aware operations for emergency control and validates all token transfers. It serves as the fundamental building block that specialized vaults like SharesVault and StabVault extend with additional functionality.

## Architecture & Dependencies

BasicVault is built as a foundational module that depends on VaultData for all state management:

### VaultData Module
- **Location**: `contracts/vaults/modules/VaultData.vy`
- **Purpose**: Provides comprehensive state management for vault operations
- **Key Features**:
  - User balance tracking (`userBalances`)
  - Asset registration and enumeration
  - Pause state management
  - Total balance accounting
  - User asset indexing and iteration
- **Relationship**: BasicVault uses VaultData for all balance modifications and state queries

### Module Dependencies
```vyper
uses: vaultData
import contracts.vaults.modules.VaultData as vaultData
```

## System Architecture Diagram

```
+------------------------------------------------------------------------+
|                        BasicVault Module                              |
+------------------------------------------------------------------------+
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                      Core Operations                             |  |
|  |                                                                  |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ _depositTokensInVault(_user, _asset, _amount)               │ |  |
|  |  │ 1. Check vault not paused                                   │ |  |
|  |  │ 2. Validate user, asset, and amount                         │ |  |
|  |  │ 3. Calculate actual deposit (min of amount and balance)     │ |  |
|  |  │ 4. Call vaultData._addBalanceOnDeposit()                    │ |  |
|  |  │    - Updates user balance                                   │ |  |
|  |  │    - Updates total balance                                  │ |  |
|  |  │    - Registers user asset if needed                         │ |  |
|  |  │    - Registers vault asset if needed                        │ |  |
|  |  │ 5. Return actual deposit amount                             │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  |                                                                  |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ _withdrawTokensFromVault(_user, _asset, _amount, _recipient)│ |  |
|  |  │ 1. Check vault not paused                                   │ |  |
|  |  │ 2. Validate user, asset, recipient, and amount              │ |  |
|  |  │ 3. Call vaultData._reduceBalanceOnWithdrawal()              │ |  |
|  |  │    - Reduces user balance                                   │ |  |
|  |  │    - Updates total balance                                  │ |  |
|  |  │    - Returns actual amount and depletion status            │ |  |
|  |  │ 4. Transfer tokens to recipient                             │ |  |
|  |  │ 5. Return withdrawal amount and depletion status           │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  |                                                                  |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ _transferBalanceWithinVault(_asset, _from, _to, _amount)    │ |  |
|  |  │ 1. Check vault not paused                                   │ |  |
|  |  │ 2. Validate from/to users, asset, and amount               │ |  |
|  |  │ 3. Reduce balance from sender (no token transfer)          │ |  |
|  |  │ 4. Add balance to recipient (no token transfer)            │ |  |
|  |  │ 5. Return transfer amount and sender depletion status      │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Integration Support Functions                 |  |
|  |                                                                  |  |
|  |  For Teller:                                                     |  |
|  |  * _getVaultDataOnDeposit() -> VaultDataOnDeposit struct         |  |
|  |                                                                  |  |
|  |  For Lootbox:                                                    |  |
|  |  * _getUserLootBoxShare() -> user asset balance                  |  |
|  |  * _getUserAssetAtIndexAndHasBalance() -> asset and balance flag |  |
|  |                                                                  |  |
|  |  For CreditEngine:                                               |  |
|  |  * _getUserAssetAndAmountAtIndex() -> asset and amount           |  |
|  |                                                                  |  |
|  |  For AuctionHouse:                                               |  |
|  |  * _getUserAssetAtIndexAndHasBalance() -> asset and balance flag |  |
|  |                                                                  |  |
|  |  General Utilities:                                              |  |
|  |  * _getTotalAmountForUser() -> user's asset balance             |  |
|  |  * _getTotalAmountForVault() -> vault's total asset balance     |  |
|  +------------------------------------------------------------------+  |
+------------------------------------------------------------------------+
                                    |
                                    |
                                    v
+------------------------------------------------------------------------+
|                        VaultData Module                               |
+------------------------------------------------------------------------+
|                                                                        |
|  State Storage:                   Asset Management:                    |
|  * userBalances                   * userAssets (indexed)               |
|  * totalBalances                  * indexOfUserAsset                   |
|  * isPaused                       * numUserAssets                      |
|                                   * vaultAssets (indexed)              |
|  Balance Operations:              * indexOfAsset                       |
|  * _addBalanceOnDeposit()         * numAssets                          |
|  * _reduceBalanceOnWithdrawal()                                        |
|                                   Registration:                        |
|  Query Functions:                 * _registerUserAsset()               |
|  * isUserInVaultAsset()           * _registerVaultAsset()              |
|  * doesUserHaveBalance()          * deregisterUserAsset()              |
|  * getNumUserAssets()             * deregisterVaultAsset()             |
+------------------------------------------------------------------------+
```

## Core Functions

### `_depositTokensInVault`

Handles token deposits into the vault with balance tracking and asset registration.

```vyper
@internal
def _depositTokensInVault(
    _user: address,
    _asset: address,
    _amount: uint256,
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User making the deposit |
| `_asset` | `address` | Asset being deposited |
| `_amount` | `uint256` | Amount to deposit |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Actual amount deposited |

#### Access

Internal function (called by extending vault contracts)

#### Process Flow
1. **Pause Check**: Ensures vault is not paused
2. **Validation**: Validates user, asset, and amount parameters
3. **Amount Calculation**: Uses minimum of requested amount and contract's asset balance
4. **Balance Update**: Calls `vaultData._addBalanceOnDeposit()` which:
   - Updates user's asset balance
   - Updates vault's total asset balance
   - Registers user asset if first deposit
   - Registers vault asset if first time seeing asset
5. **Return**: Returns actual deposited amount

#### Example Integration
```python
# In an extending vault contract
@external
def deposit(_asset: address, _amount: uint256):
    # Transfer tokens to vault first
    assert extcall IERC20(_asset).transferFrom(msg.sender, self, _amount)
    
    # Process deposit through BasicVault
    deposited = self._depositTokensInVault(msg.sender, _asset, _amount)
    
    # Emit deposit event
    log Deposit(user=msg.sender, asset=_asset, amount=deposited)
```

### `_withdrawTokensFromVault`

Handles token withdrawals from the vault with balance reduction and token transfers.

```vyper
@internal
def _withdrawTokensFromVault(
    _user: address,
    _asset: address,
    _amount: uint256,
    _recipient: address,
) -> (uint256, bool):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User making the withdrawal |
| `_asset` | `address` | Asset being withdrawn |
| `_amount` | `uint256` | Amount to withdraw |
| `_recipient` | `address` | Address to receive the tokens |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Actual amount withdrawn |
| `bool` | True if user's asset balance is now depleted |

#### Access

Internal function (called by extending vault contracts)

#### Process Flow
1. **Pause Check**: Ensures vault is not paused
2. **Validation**: Validates all address parameters and amount
3. **Balance Reduction**: Calls `vaultData._reduceBalanceOnWithdrawal()` which:
   - Reduces user's asset balance
   - Updates vault's total asset balance
   - Returns actual withdrawal amount and depletion status
4. **Token Transfer**: Transfers tokens from vault to recipient
5. **Return**: Returns withdrawal amount and depletion status

#### Example Integration
```python
# In an extending vault contract
@external
def withdraw(_asset: address, _amount: uint256, _recipient: address):
    # Process withdrawal through BasicVault
    withdrawn, is_depleted = self._withdrawTokensFromVault(
        msg.sender, _asset, _amount, _recipient
    )
    
    # Handle post-withdrawal logic if user balance is depleted
    if is_depleted:
        self._handleUserAssetDepletion(msg.sender, _asset)
    
    # Emit withdrawal event
    log Withdraw(user=msg.sender, asset=_asset, amount=withdrawn)
```

### `_transferBalanceWithinVault`

Transfers asset balances between users within the vault without moving tokens.

```vyper
@internal
def _transferBalanceWithinVault(
    _asset: address,
    _fromUser: address,
    _toUser: address,
    _transferAmount: uint256,
) -> (uint256, bool):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_asset` | `address` | Asset being transferred |
| `_fromUser` | `address` | User sending the balance |
| `_toUser` | `address` | User receiving the balance |
| `_transferAmount` | `uint256` | Amount to transfer |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Actual amount transferred |
| `bool` | True if sender's asset balance is now depleted |

#### Access

Internal function (called by extending vault contracts)

#### Process Flow
1. **Pause Check**: Ensures vault is not paused
2. **Validation**: Validates all address parameters and amount
3. **Balance Transfer**: 
   - Reduces sender's balance via `vaultData._reduceBalanceOnWithdrawal()` (no total update)
   - Increases recipient's balance via `vaultData._addBalanceOnDeposit()` (no total update)
   - Registers recipient's asset if needed
4. **Return**: Returns transfer amount and sender depletion status

#### Example Integration
```python
# Used in liquidation or internal rebalancing
def _transferCollateralToLiquidator(_user: address, _asset: address, _amount: uint256):
    transferred, is_depleted = self._transferBalanceWithinVault(
        _asset, _user, liquidator.address, _amount
    )
    return transferred, is_depleted
```

## Integration Support Functions

### `_getVaultDataOnDeposit`

Provides vault data needed by Teller contract for deposit operations.

```vyper
@view
@internal
def _getVaultDataOnDeposit(_user: address, _asset: address) -> Vault.VaultDataOnDeposit:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User making deposit |
| `_asset` | `address` | Asset being deposited |

#### Returns

| Type | Description |
|------|-------------|
| `Vault.VaultDataOnDeposit` | Struct with position info, asset counts, and balances |

#### Struct Fields
- `hasPosition: bool` - Whether user already has this asset
- `numAssets: uint256` - Number of assets user has in vault
- `userBalance: uint256` - User's current balance of this asset
- `totalBalance: uint256` - Vault's total balance of this asset

#### Access

Internal view function (used by Teller)

### `_getUserLootBoxShare`

Returns a user's asset balance for Lootbox reward calculations.

```vyper
@view
@internal
def _getUserLootBoxShare(_user: address, _asset: address) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User to query |
| `_asset` | `address` | Asset to query |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | User's balance of the asset |

#### Access

Internal view function (used by Lootbox)

### `_getUserAssetAndAmountAtIndex`

Returns asset and amount at a specific index for a user (used by CreditEngine).

```vyper
@view
@internal
def _getUserAssetAndAmountAtIndex(_user: address, _index: uint256) -> (address, uint256):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User to query |
| `_index` | `uint256` | Asset index to query |

#### Returns

| Type | Description |
|------|-------------|
| `address` | Asset address at index |
| `uint256` | User's balance of that asset |

#### Access

Internal view function (used by CreditEngine)

### `_getUserAssetAtIndexAndHasBalance`

Returns asset and balance status at a specific index for a user.

```vyper
@view
@internal
def _getUserAssetAtIndexAndHasBalance(_user: address, _index: uint256) -> (address, bool):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User to query |
| `_index` | `uint256` | Asset index to query |

#### Returns

| Type | Description |
|------|-------------|
| `address` | Asset address at index |
| `bool` | Whether user has non-zero balance |

#### Access

Internal view function (used by Lootbox and AuctionHouse)

## Utility Functions

### `_getTotalAmountForUser`

Returns a user's total balance for a specific asset.

```vyper
@view
@internal
def _getTotalAmountForUser(_user: address, _asset: address) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User to query |
| `_asset` | `address` | Asset to query |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | User's balance of the asset |

#### Access

Internal view function

### `_getTotalAmountForVault`

Returns the vault's total balance for a specific asset.

```vyper
@view
@internal
def _getTotalAmountForVault(_asset: address) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_asset` | `address` | Asset to query |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Vault's total balance of the asset |

#### Access

Internal view function

## Key Features

### Pause-Aware Operations
All core functions check `vaultData.isPaused` before proceeding, allowing for emergency stops.

### Automatic Asset Registration
- User assets are automatically registered on first deposit
- Vault assets are automatically registered when first seen
- Proper indexing maintained for efficient iteration

### Balance Consistency
- User balances and vault total balances are kept in sync
- Withdrawal amounts are capped by available balances
- Transfer operations maintain balance invariants

### Integration Points
- Designed for extension by other vault modules
- Provides utility functions for protocol contract integration
- Maintains clean separation between balance logic and token transfers

## Security Considerations

### Validation Checks
- All address parameters validated against empty addresses
- Amount parameters validated against zero
- Asset existence validated before operations

### Pause Protection
- All state-modifying operations respect pause state
- Emergency pause capability through VaultData module

### Balance Safety
- Withdrawal amounts capped by user balance
- Token transfer amounts capped by contract balance
- Internal transfers don't affect vault total balances

## Testing

For comprehensive test examples, see: [`tests/vaults/test_basic_vault.py`](../../tests/vaults/test_basic_vault.py)