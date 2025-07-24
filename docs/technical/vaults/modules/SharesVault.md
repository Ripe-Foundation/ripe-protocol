# SharesVault Module Technical Documentation

[📄 View Source Code](../../../contracts/vaults/modules/SharesVault.vy)

## Overview

SharesVault is an advanced vault module implementing share-based accounting for yield-bearing positions. Users receive shares representing proportional ownership of vault assets, enabling automatic yield distribution as share values appreciate over time.

**Core Functions**:
- **Share-Based Accounting**: Deposits receive shares; value changes affect all holders proportionally
- **Attack Prevention**: Dead shares and decimal offsets protect against donation attacks
- **Precise Conversions**: Configurable rounding for share-to-asset calculations
- **Yield Integration**: Specialized functions account for share appreciation in rewards

Extending VaultData with ERC4626-style mechanics, SharesVault maintains share balances while calculating asset values dynamically. It provides yield-aware utilities for protocol integration, making it ideal for vaults where assets appreciate through rebasing or external yield generation.

## Architecture & Dependencies

SharesVault is built as an advanced vault module that depends on VaultData for state management:

### VaultData Module
- **Location**: `contracts/vaults/modules/VaultData.vy`
- **Purpose**: Provides comprehensive state management for vault operations
- **Key Features**:
  - Share balance tracking (`userBalances` stores shares, not amounts)
  - Share registration and enumeration
  - Pause state management
  - Total share accounting (`totalBalances` stores total shares)
  - User asset indexing and iteration
- **Relationship**: SharesVault uses VaultData but interprets balances as shares

### Module Dependencies
```vyper
uses: vaultData
import contracts.vaults.modules.VaultData as vaultData
```

### Key Constants
- `DECIMAL_OFFSET: constant(uint256) = 10 ** 8` - Used for donation attack prevention

## System Architecture Diagram

```
+------------------------------------------------------------------------+
|                       SharesVault Module                              |
+------------------------------------------------------------------------+
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                      Core Operations                             |  |
|  |                                                                  |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ _depositTokensInVault(_user, _asset, _amount)               │ |  |
|  |  │ 1. Check vault not paused                                   │ |  |
|  |  │ 2. Validate user, asset, and amount                         │ |  |
|  |  │ 3. Calculate previous total balance (before deposit)        │ |  |
|  |  │ 4. Calculate shares to mint:                                │ |  |
|  |  │    shares = (amount * totalShares) / totalBalance           │ |  |
|  |  │ 5. Add shares to user balance via VaultData                 │ |  |
|  |  │ 6. Return deposit amount and shares minted                  │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  |                                                                  |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ _withdrawTokensFromVault(_user, _asset, _amount, _recipient)│ |  |
|  |  │ 1. Check vault not paused                                   │ |  |
|  |  │ 2. Calculate withdrawal shares and actual amount:           │ |  |
|  |  │    - Convert amount to required shares                      │ |  |
|  |  │    - Cap by user's actual shares                            │ |  |
|  |  │    - Convert back to exact withdrawal amount                │ |  |
|  |  │ 3. Reduce user shares via VaultData                         │ |  |
|  |  │ 4. Transfer tokens to recipient                             │ |  |
|  |  │ 5. Return amount, shares burned, and depletion status      │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  |                                                                  |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ _transferBalanceWithinVault(_asset, _from, _to, _amount)    │ |  |
|  |  │ 1. Check vault not paused                                   │ |  |
|  |  │ 2. Calculate transfer shares and actual amount              │ |  |
|  |  │ 3. Transfer shares from sender to recipient                 │ |  |
|  |  │ 4. Return amount, shares, and sender depletion status      │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Share Calculation Engine                      |  |
|  |                                                                  |  |
|  |  Amount to Shares:                                               |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ _amountToShares(amount, totalShares, totalBalance, roundUp) │ |  |
|  |  │ 1. Add decimal offset for donation attack prevention:       │ |  |
|  |  │    totalShares += DECIMAL_OFFSET (10^8)                     │ |  |
|  |  │    totalBalance += 1                                        │ |  |
|  |  │ 2. Calculate: shares = (amount * totalShares) / totalBalance│ |  |
|  |  │ 3. Apply rounding if requested                              │ |  |
|  |  │ 4. Return calculated shares                                 │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  |                                                                  |  |
|  |  Shares to Amount:                                               |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ _sharesToAmount(shares, totalShares, totalBalance, roundUp) │ |  |
|  |  │ 1. Add decimal offset for donation attack prevention        │ |  |
|  |  │ 2. Calculate: amount = (shares * totalBalance) / totalShares│ |  |
|  |  │ 3. Apply rounding if requested                              │ |  |
|  |  │ 4. Return calculated amount                                 │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Integration Support Functions                 |  |
|  |                                                                  |  |
|  |  For Teller:                                                     |  |
|  |  * _getVaultDataOnDeposit() -> includes current asset value      |  |
|  |                                                                  |  |
|  |  For Lootbox:                                                    |  |
|  |  * _getUserLootBoxShare() -> shares / DECIMAL_OFFSET             |  |
|  |  * _getUserAssetAtIndexAndHasBalance() -> asset and share status |  |
|  |                                                                  |  |
|  |  For CreditEngine:                                               |  |
|  |  * _getUserAssetAndAmountAtIndex() -> converts shares to amount  |  |
|  |                                                                  |  |
|  |  General Utilities:                                              |  |
|  |  * _getTotalAmountForUser() -> converts user shares to amount    |  |
|  |  * _getTotalAmountForVault() -> actual token balance            |  |
|  +------------------------------------------------------------------+  |
+------------------------------------------------------------------------+
                                    |
                                    |
                                    v
+------------------------------------------------------------------------+
|                        VaultData Module                               |
+------------------------------------------------------------------------+
|                                                                        |
|  Share Storage:                   Asset Management:                    |
|  * userBalances (SHARES)          * userAssets (indexed)               |
|  * totalBalances (SHARES)         * indexOfUserAsset                   |
|  * isPaused                       * numUserAssets                      |
|                                   * vaultAssets (indexed)              |
|  Share Operations:                * indexOfAsset                       |
|  * _addBalanceOnDeposit()         * numAssets                          |
|  * _reduceBalanceOnWithdrawal()                                        |
|                                   Registration:                        |
|  Query Functions:                 * _registerUserAsset()               |
|  * isUserInVaultAsset()           * _registerVaultAsset()              |
|  * doesUserHaveBalance()          * deregisterUserAsset()              |
|  * getNumUserAssets()             * deregisterVaultAsset()             |
+------------------------------------------------------------------------+
                                    ^
                                    |
                    Note: VaultData stores SHARES, not asset amounts
                    SharesVault converts between shares and amounts dynamically
```

## Core Functions

### `_depositTokensInVault`

Handles token deposits into the vault with share minting and yield accounting.

```vyper
@internal
def _depositTokensInVault(
    _user: address,
    _asset: address,
    _amount: uint256,
) -> (uint256, uint256):
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
| `uint256` | Number of shares minted |

#### Access

Internal function (called by extending vault contracts)

#### Process Flow
1. **Pause Check**: Ensures vault is not paused
2. **Validation**: Validates user, asset, and amount parameters
3. **Balance Calculation**: Calculates actual deposit amount (min of requested and available)
4. **Previous Balance**: Calculates balance before deposit for accurate share calculation
5. **Share Minting**: Calls `_amountToShares()` to determine shares to mint
6. **Balance Update**: Adds shares to user balance via `vaultData._addBalanceOnDeposit()`
7. **Return**: Returns deposit amount and shares minted

#### Share Calculation
The share calculation uses the formula:
```
shares = (depositAmount * currentTotalShares) / previousTotalBalance
```

This ensures that:
- First depositor gets 1:1 shares to amount ratio
- Subsequent depositors get shares proportional to their contribution
- Yield accumulation increases asset value per share

#### Example Integration
```python
# In an extending shares vault contract
@external
def deposit(_asset: address, _amount: uint256):
    # Transfer tokens to vault first
    assert extcall IERC20(_asset).transferFrom(msg.sender, self, _amount)
    
    # Process deposit through SharesVault
    deposited, shares_minted = self._depositTokensInVault(msg.sender, _asset, _amount)
    
    # Emit deposit event with shares
    log Deposit(user=msg.sender, asset=_asset, amount=deposited, shares=shares_minted)
```

### `_withdrawTokensFromVault`

Handles token withdrawals from the vault with share burning and precise amount calculation.

```vyper
@internal
def _withdrawTokensFromVault(
    _user: address,
    _asset: address,
    _amount: uint256,
    _recipient: address,
) -> (uint256, uint256, bool):
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
| `uint256` | Number of shares burned |
| `bool` | True if user's share balance is now depleted |

#### Access

Internal function (called by extending vault contracts)

#### Process Flow
1. **Pause Check**: Ensures vault is not paused
2. **Validation**: Validates all address parameters
3. **Share/Amount Calculation**: Calls `_calcWithdrawalSharesAndAmount()` to determine:
   - Required shares to burn for requested amount
   - Actual withdrawal amount (may be less if insufficient shares)
4. **Share Reduction**: Burns shares via `vaultData._reduceBalanceOnWithdrawal()`
5. **Token Transfer**: Transfers calculated amount to recipient
6. **Return**: Returns amount, shares burned, and depletion status

#### Example Integration
```python
# In an extending shares vault contract
@external
def withdraw(_asset: address, _amount: uint256, _recipient: address):
    # Process withdrawal through SharesVault
    withdrawn, shares_burned, is_depleted = self._withdrawTokensFromVault(
        msg.sender, _asset, _amount, _recipient
    )
    
    # Handle post-withdrawal logic if user shares depleted
    if is_depleted:
        self._handleUserShareDepletion(msg.sender, _asset)
    
    # Emit withdrawal event with shares
    log Withdraw(user=msg.sender, asset=_asset, amount=withdrawn, shares=shares_burned)
```

### `_transferBalanceWithinVault`

Transfers share balances between users within the vault without moving tokens.

```vyper
@internal
def _transferBalanceWithinVault(
    _asset: address,
    _fromUser: address,
    _toUser: address,
    _transferAmount: uint256,
) -> (uint256, uint256, bool):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_asset` | `address` | Asset being transferred |
| `_fromUser` | `address` | User sending the shares |
| `_toUser` | `address` | User receiving the shares |
| `_transferAmount` | `uint256` | Asset amount to transfer |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Actual amount transferred |
| `uint256` | Number of shares transferred |
| `bool` | True if sender's share balance is now depleted |

#### Access

Internal function (called by extending vault contracts)

#### Process Flow
1. **Pause Check**: Ensures vault is not paused
2. **Validation**: Validates all address parameters
3. **Share/Amount Calculation**: Determines shares needed for requested amount
4. **Share Transfer**: 
   - Reduces sender's shares (no total share change)
   - Increases recipient's shares (no total share change)
   - Registers recipient's asset if needed
5. **Return**: Returns transfer amount, shares, and sender depletion status

## Share Calculation Functions

### `_calcWithdrawalSharesAndAmount`

Calculates the shares and amount for withdrawal operations.

```vyper
@view
@internal
def _calcWithdrawalSharesAndAmount(
    _user: address,
    _asset: address,
    _amount: uint256,
) -> (uint256, uint256):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User making withdrawal |
| `_asset` | `address` | Asset to withdraw |
| `_amount` | `uint256` | Requested amount |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Shares to burn |
| `uint256` | Actual withdrawal amount |

#### Access

Internal view function

#### Logic
1. Gets user's total shares for the asset
2. Converts user's shares to maximum withdrawable amount
3. If requested amount ≤ max amount:
   - Converts requested amount to required shares
   - Returns (required_shares, requested_amount)
4. If requested amount > max amount:
   - Returns (all_user_shares, max_withdrawable_amount)

### `_amountToShares`

Converts asset amounts to share amounts with donation attack prevention.

```vyper
@view
@internal
def _amountToShares(
    _amount: uint256,
    _totalShares: uint256,
    _totalBalance: uint256,
    _shouldRoundUp: bool,
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_amount` | `uint256` | Asset amount to convert |
| `_totalShares` | `uint256` | Current total shares in vault |
| `_totalBalance` | `uint256` | Current total asset balance |
| `_shouldRoundUp` | `bool` | Whether to round up partial shares |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Equivalent number of shares |

#### Access

Internal view function

#### Donation Attack Prevention
```vyper
# Add decimal offset to prevent donation attacks
totalBalance += 1
totalShares += DECIMAL_OFFSET  # 10^8
```

This prevents attackers from manipulating share prices through small donations.

#### Formula
```
shares = (amount * totalShares) / totalBalance
```

With optional rounding up for partial shares.

### `_sharesToAmount`

Converts share amounts to asset amounts with donation attack prevention.

```vyper
@view
@internal
def _sharesToAmount(
    _shares: uint256,
    _totalShares: uint256,
    _totalBalance: uint256,
    _shouldRoundUp: bool,
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_shares` | `uint256` | Share amount to convert |
| `_totalShares` | `uint256` | Current total shares in vault |
| `_totalBalance` | `uint256` | Current total asset balance |
| `_shouldRoundUp` | `bool` | Whether to round up partial amounts |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Equivalent asset amount |

#### Formula
```
amount = (shares * totalBalance) / totalShares
```

With donation attack prevention and optional rounding.

## Public Conversion Functions

### `amountToShares`

Public function to convert asset amounts to shares.

```vyper
@view
@external
def amountToShares(_asset: address, _amount: uint256, _shouldRoundUp: bool) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_asset` | `address` | Asset to convert |
| `_amount` | `uint256` | Asset amount |
| `_shouldRoundUp` | `bool` | Rounding preference |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Equivalent shares |

#### Access

Public view function

#### Example Usage
```python
# Check how many shares 1000 tokens would get
shares = shares_vault.amountToShares(asset.address, 1000_000000000000000000, False)
print(f"1000 tokens = {shares / 1e18} shares")
```

### `sharesToAmount`

Public function to convert shares to asset amounts.

```vyper
@view
@external
def sharesToAmount(_asset: address, _shares: uint256, _shouldRoundUp: bool) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_asset` | `address` | Asset to convert |
| `_shares` | `uint256` | Share amount |
| `_shouldRoundUp` | `bool` | Rounding preference |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Equivalent asset amount |

#### Access

Public view function

#### Example Usage
```python
# Check current value of user's shares
user_shares = vault_data.userBalances(user.address, asset.address)
asset_value = shares_vault.sharesToAmount(asset.address, user_shares, False)
print(f"User's shares are worth {asset_value / 1e18} tokens")
```

## Integration Support Functions

### `_getVaultDataOnDeposit`

Provides vault data needed by Teller contract, accounting for share values.

```vyper
@view
@internal
def _getVaultDataOnDeposit(_user: address, _asset: address) -> Vault.VaultDataOnDeposit:
```

#### Key Difference from BasicVault
- `userBalance` field shows current asset value of user's shares, not share count
- `totalBalance` field shows actual asset balance in the vault

### `_getUserLootBoxShare`

Returns user's share count adjusted for Lootbox calculations.

```vyper
@view
@internal
def _getUserLootBoxShare(_user: address, _asset: address) -> uint256:
```

#### Returns

User's shares divided by `DECIMAL_OFFSET` to normalize for reward calculations.

### `_getUserAssetAndAmountAtIndex`

Returns asset and current value for CreditEngine collateral calculations.

```vyper
@view
@internal
def _getUserAssetAndAmountAtIndex(_user: address, _index: uint256) -> (address, uint256):
```

#### Key Feature
Converts user's shares to current asset value for accurate collateral accounting.

## Utility Functions

### `_getTotalAmountForUser`

Returns the current asset value of a user's shares.

```vyper
@view
@internal
def _getTotalAmountForUser(_user: address, _asset: address) -> uint256:
```

### `_getTotalAmountForUserWithTotalBal`

Optimized version when total balance is already known.

```vyper
@view
@internal
def _getTotalAmountForUserWithTotalBal(_user: address, _asset: address, _totalBalance: uint256) -> uint256:
```

### `_getTotalAmountForVault`

Returns the actual asset balance held by the vault.

```vyper
@view
@internal
def _getTotalAmountForVault(_asset: address) -> uint256:
```

## Key Features

### Yield Distribution
- Share values appreciate as vault generates yield
- No need for explicit yield distribution transactions
- Proportional sharing of gains and losses

### Donation Attack Prevention
- Dead shares mechanism through `DECIMAL_OFFSET`
- Prevents manipulation of share prices
- Maintains fairness for all depositors

### Precise Calculations
- Configurable rounding for different scenarios
- Exact share-to-asset conversions
- Handles edge cases like empty vaults

### Share-Based Accounting
- Stores shares in VaultData, calculates amounts dynamically
- Enables yield compounding without explicit distributions
- Compatible with existing vault infrastructure

## Security Considerations

### Rounding Modes
- Deposits typically round down (favorable to vault)
- Withdrawals typically round up (favorable to user)
- Consistent rounding prevents manipulation

### Donation Attack Protection
- `DECIMAL_OFFSET` prevents share price manipulation
- Dead shares absorb small donation attempts
- First depositor doesn't get unfair advantage

### Share Precision
- High precision calculations prevent dust accumulation
- Proper handling of edge cases (zero balances, empty vaults)
- Maintains share accounting invariants

## Testing

For comprehensive test examples, see: [`tests/vaults/test_shares_vault.py`](../../tests/vaults/test_shares_vault.py)