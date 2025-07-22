# SimpleErc20 Vault Technical Documentation

[📄 View Source Code](../../contracts/vaults/SimpleErc20.vy)

## Overview

SimpleErc20 is the most straightforward vault in Ripe Protocol, providing basic deposit and withdrawal for any ERC20 token. With direct 1:1 balance tracking and no yield mechanics, it's ideal for collateral storage, basic custody, and scenarios requiring predictable asset management.

**What Makes It Simple**:
- **No Shares**: Direct asset amounts, not share calculations
- **No Yield**: Assets don't grow or compound
- **No Complexity**: Just deposit, withdraw, and track balances

Built on the BasicVault module, SimpleErc20 is perfect for USDC, DAI, WETH, or any standard token where users want transparent custody. It integrates seamlessly with protocol systems for collateral evaluation and liquidations while maintaining maximum simplicity.

## Architecture & Dependencies

SimpleErc20 is built using a modular architecture with delegation to foundational modules:

### Core Module Dependencies
- **BasicVault**: Provides fundamental vault operations with direct asset-amount accounting
- **VaultData**: Manages user balances, asset registration, and vault state
- **[Addys](../modules/Addys.md)**: Handles protocol address resolution and permission management

### Module Initialization
```vyper
exports: addys.__interface__
exports: vaultData.__interface__

initializes: addys
initializes: vaultData[addys := addys]
initializes: basicVault[vaultData := vaultData]
```

## System Architecture Diagram

```
+------------------------------------------------------------------------+
|                        SimpleErc20 Vault                              |
+------------------------------------------------------------------------+
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Contract-Level Operations                     |  |
|  |                                                                  |  |
|  |  depositTokensInVault():                                         |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ 1. Access Control: Only Teller allowed                     │ |  |
|  |  │ 2. Delegate to BasicVault._depositTokensInVault()           │ |  |
|  |  │ 3. Emit SimpleErc20VaultDeposit event                      │ |  |
|  |  │ 4. Return deposit amount (1:1 with user balance)           │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  |                                                                  |  |
|  |  withdrawTokensFromVault():                                      |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ 1. Access Control: Teller, AuctionHouse, CreditEngine      │ |  |
|  |  │ 2. Delegate to BasicVault._withdrawTokensFromVault()        │ |  |
|  |  │ 3. Emit SimpleErc20VaultWithdrawal event                   │ |  |
|  |  │ 4. Return withdrawal amount and depletion status           │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  |                                                                  |  |
|  |  transferBalanceWithinVault():                                   |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ 1. Access Control: AuctionHouse, CreditEngine              │ |  |
|  |  │ 2. Delegate to BasicVault._transferBalanceWithinVault()     │ |  |
|  |  │ 3. Emit SimpleErc20VaultTransfer event                     │ |  |
|  |  │ 4. Return transfer amount and depletion status             │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  +------------------------------------------------------------------+  |
|  |                                                                  |  |
|  |  Key Characteristics:                                            |  |
|  |  • 1:1 Asset-to-Balance Ratio: No shares or yield calculation   |  |
|  |  • Direct Token Custody: Vault holds actual tokens deposited    |  |
|  |  • Simple Withdrawals: Amount out = Amount requested (max=bal)   |  |
|  |  • No Complex Logic: Pure custody without additional features    |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Integration Support                           |  |
|  |                                                                  |  |
|  |  getVaultDataOnDeposit():                                        |  |
|  |  • Delegates to BasicVault for Teller integration               |  |
|  |  • Returns direct balance amounts (no share conversion)         |  |
|  |                                                                  |  |
|  |  getUserLootBoxShare():                                          |  |
|  |  • Delegates to BasicVault for Lootbox reward calculations      |  |
|  |  • Uses actual balance amounts for reward share calculation     |  |
|  |                                                                  |  |
|  |  getUserAssetAndAmountAtIndex():                                 |  |
|  |  • Delegates to BasicVault for CreditEngine integration         |  |
|  |  • Returns actual asset amounts for collateral calculations     |  |
|  |                                                                  |  |
|  |  getUserAssetAtIndexAndHasBalance():                             |  |
|  |  • Delegates to BasicVault for position validation              |  |
|  |  • Simple balance existence check (> 0)                         |  |
|  +------------------------------------------------------------------+  |
+------------------------------------------------------------------------+
                                    |
                                    | Delegates all core functionality
                                    v
+------------------------------------------------------------------------+
|                          BasicVault Module                            |
+------------------------------------------------------------------------+
|                                                                        |
| • Direct asset-amount accounting (no shares)                          |
| • Token custody with 1:1 deposit-to-balance mapping                   |
| • Simple withdrawal mechanics (amount capped by balance)              |
| • Straightforward balance tracking via VaultData                      |
| • No yield calculation, price oracle dependency, or complexity        |
+------------------------------------------------------------------------+
```

## Constructor

### `__init__`

Initializes SimpleErc20 vault with protocol address configuration.

```vyper
@deploy
def __init__(_ripeHq: address):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_ripeHq` | `address` | RipeHq contract address for protocol integration |

#### Process Flow
1. **Address Setup**: Initializes Addys module with RipeHq address
2. **VaultData Setup**: Initializes with non-paused state (`False`)
3. **BasicVault Setup**: Initializes basic vault functionality

#### Example Usage
```python
# Deploy simple ERC20 vault
simple_erc20_vault = boa.load(
    "contracts/vaults/SimpleErc20.vy",
    ripe_hq.address
)
```

## Core Functions

### `depositTokensInVault`

Handles direct deposits of ERC20 tokens with 1:1 balance accounting.

```vyper
@nonreentrant
@external
def depositTokensInVault(
    _user: address,
    _asset: address,
    _amount: uint256,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User making the deposit |
| `_asset` | `address` | ERC20 token to deposit |
| `_amount` | `uint256` | Amount of tokens to deposit |
| `_a` | `addys.Addys` | Protocol addresses struct (unused) |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Actual amount deposited (equals user balance increase) |

#### Access

Only callable by Teller

#### Process Flow
1. **Access Validation**: Ensures caller is Teller contract
2. **BasicVault Delegation**: Calls `basicVault._depositTokensInVault()` for core functionality
3. **Direct Accounting**: Deposited amount directly increases user balance 1:1
4. **Event Emission**: Logs deposit with user, asset, and amount
5. **Return**: Returns actual deposit amount

#### Events Emitted

- `SimpleErc20VaultDeposit` - Contains user, asset, and amount deposited

#### Key Characteristics
- **No Share Calculation**: Balance increases exactly by deposited amount
- **No Yield Accumulation**: Vault simply holds tokens without generating additional value
- **Direct Token Transfer**: Vault receives actual tokens from user

#### Example Usage
```python
# Deposit USDC into simple vault through Teller
deposit_amount = simple_erc20_vault.depositTokensInVault(
    user.address,
    usdc_token.address,
    1000_000000,  # 1000 USDC (6 decimals)
    empty(addys.Addys),
    sender=teller.address
)

# User's balance in vault is now exactly 1000_000000 USDC
assert simple_erc20_vault.getTotalAmountForUser(user.address, usdc_token.address) == 1000_000000
```

### `withdrawTokensFromVault`

Handles direct withdrawals of ERC20 tokens with balance deduction.

```vyper
@nonreentrant
@external
def withdrawTokensFromVault(
    _user: address,
    _asset: address,
    _amount: uint256,
    _recipient: address,
    _a: addys.Addys = empty(addys.Addys),
) -> (uint256, bool):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User making withdrawal |
| `_asset` | `address` | ERC20 token to withdraw |
| `_amount` | `uint256` | Amount to withdraw |
| `_recipient` | `address` | Address to receive withdrawn tokens |
| `_a` | `addys.Addys` | Protocol addresses struct (unused) |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Actual amount withdrawn |
| `bool` | True if user's balance is now depleted (zero) |

#### Access

Only callable by Teller, AuctionHouse, or CreditEngine

#### Process Flow
1. **Access Validation**: Ensures caller is authorized contract
2. **BasicVault Delegation**: Calls `basicVault._withdrawTokensFromVault()` for core functionality
3. **Amount Capping**: Withdrawal amount capped by user's available balance
4. **Direct Transfer**: Tokens transferred directly from vault to recipient
5. **Balance Deduction**: User balance reduced by withdrawal amount
6. **Event Emission**: Logs withdrawal with depletion status
7. **Return**: Returns actual withdrawal amount and depletion status

#### Events Emitted

- `SimpleErc20VaultWithdrawal` - Contains user, asset, amount, and depletion status

#### Example Usage
```python
# User withdraws half their USDC position through Teller
withdrawal_amount, is_depleted = simple_erc20_vault.withdrawTokensFromVault(
    user.address,
    usdc_token.address,
    500_000000,  # 500 USDC
    user.address,  # Recipient
    empty(addys.Addys),
    sender=teller.address
)

# Withdrawal amount is exactly 500 USDC, not depleted
assert withdrawal_amount == 500_000000
assert is_depleted == False
```

### `transferBalanceWithinVault`

Transfers token balances between users (used for liquidations).

```vyper
@nonreentrant
@external
def transferBalanceWithinVault(
    _asset: address,
    _fromUser: address,
    _toUser: address,
    _transferAmount: uint256,
    _a: addys.Addys = empty(addys.Addys),
) -> (uint256, bool):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_asset` | `address` | ERC20 token to transfer |
| `_fromUser` | `address` | User losing the balance |
| `_toUser` | `address` | User gaining the balance |
| `_transferAmount` | `uint256` | Amount to transfer |
| `_a` | `addys.Addys` | Protocol addresses struct (unused) |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Actual amount transferred |
| `bool` | True if from user's balance is now depleted |

#### Access

Only callable by AuctionHouse or CreditEngine (for liquidations)

#### Process Flow
1. **Access Validation**: Ensures caller is liquidation contract
2. **BasicVault Delegation**: Calls `basicVault._transferBalanceWithinVault()` for balance transfer
3. **Amount Capping**: Transfer amount capped by from user's available balance
4. **Balance Update**: From user balance decreased, to user balance increased
5. **Event Emission**: Logs transfer with users and depletion status
6. **Return**: Returns transfer amount and from user depletion status

#### Events Emitted

- `SimpleErc20VaultTransfer` - Contains fromUser, toUser, asset, transferAmount, and depletion status

#### Usage Context

This function is called during liquidations to transfer collateral from borrowers to liquidators:

#### Example Integration
```python
# Called by AuctionHouse during liquidation
transfer_amount, is_depleted = simple_erc20_vault.transferBalanceWithinVault(
    weth.address,
    borrower.address,      # User being liquidated
    liquidator.address,    # User receiving collateral
    1_000000000000000000,  # 1 WETH
    empty(addys.Addys),
    sender=auction_house.address
)
```

## Integration Support Functions

### `getVaultDataOnDeposit`

Provides vault data needed by Teller for deposit operations.

```vyper
@view
@external
def getVaultDataOnDeposit(_user: address, _asset: address) -> Vault.VaultDataOnDeposit:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User making deposit |
| `_asset` | `address` | Asset being deposited |

#### Returns

| Type | Description |
|------|-------------|
| `Vault.VaultDataOnDeposit` | Vault data structure for Teller integration |

#### Usage

Used by Teller.vy to validate deposits and calculate fees. For SimpleErc20 vault, this returns straightforward balance information without share calculations.

### `getUserLootBoxShare`

Returns user's balance amount for Lootbox reward calculations.

```vyper
@view
@external
def getUserLootBoxShare(_user: address, _asset: address) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User to get share for |
| `_asset` | `address` | Asset to check balance for |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | User's asset balance amount (used for reward calculations) |

#### Usage

Used by Lootbox.vy for reward distribution calculations. Unlike share-based vaults, this returns the actual token balance amount.

### `getUserAssetAndAmountAtIndex`

Returns asset and amount at specific index for CreditEngine collateral calculations.

```vyper
@view
@external
def getUserAssetAndAmountAtIndex(_user: address, _index: uint256) -> (address, uint256):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User to query assets for |
| `_index` | `uint256` | Asset index to retrieve |

#### Returns

| Type | Description |
|------|-------------|
| `address` | Asset address at the specified index |
| `uint256` | User's balance amount for that asset |

#### Usage

Used by CreditEngine.vy for collateral evaluation. This function enables the CreditEngine to iterate through all of a user's vault assets and use them as collateral for borrowing.

#### Example Integration
```python
# CreditEngine iterates through user's vault assets
num_assets = simple_erc20_vault.getTotalAmountForUser(user.address, zero_address)  # Gets count
for i in range(num_assets):
    asset, amount = simple_erc20_vault.getUserAssetAndAmountAtIndex(user.address, i + 1)  # 1-based indexing
    collateral_value += price_desk.getUsdValue(asset, amount)
```

### `getUserAssetAtIndexAndHasBalance`

Returns asset at index and whether user has a positive balance.

```vyper
@view
@external
def getUserAssetAtIndexAndHasBalance(_user: address, _index: uint256) -> (address, bool):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User to query |
| `_index` | `uint256` | Asset index |

#### Returns

| Type | Description |
|------|-------------|
| `address` | Asset address |
| `bool` | True if user has positive balance |

#### Usage

Used by Lootbox.vy and AuctionHouse.vy for position validation and efficient iteration.

## Utility Functions

### `getTotalAmountForUser`

Returns user's total balance for a specific asset.

```vyper
@view
@external
def getTotalAmountForUser(_user: address, _asset: address) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User to query |
| `_asset` | `address` | Asset to get balance for |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | User's balance amount for the asset |

#### Characteristics

For SimpleErc20 vault:
- Returns exactly the amount of tokens deposited minus any withdrawals
- No yield accumulation or share conversion
- Direct 1:1 correspondence with deposited tokens

#### Example Usage
```python
# Check user's USDC balance in vault
usdc_balance = simple_erc20_vault.getTotalAmountForUser(user.address, usdc_token.address)
print(f"User has {usdc_balance / 10**6} USDC in vault")
```

### `getTotalAmountForVault`

Returns total balance of all users for a specific asset.

```vyper
@view
@external
def getTotalAmountForVault(_asset: address) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_asset` | `address` | Asset to get total balance for |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Total vault balance for the asset |

#### Characteristics

- Represents total tokens held by the vault contract
- Should equal sum of all user balances
- No additional assets from yield or rewards

## Events

### `SimpleErc20VaultDeposit`

Emitted when users deposit tokens into the vault.

#### Event Data

| Field | Type | Description |
|-------|------|-------------|
| `user` | `indexed(address)` | User making deposit |
| `asset` | `indexed(address)` | ERC20 token deposited |
| `amount` | `uint256` | Amount of tokens deposited |

### `SimpleErc20VaultWithdrawal`

Emitted when users withdraw tokens from the vault.

#### Event Data

| Field | Type | Description |
|-------|------|-------------|
| `user` | `indexed(address)` | User making withdrawal |
| `asset` | `indexed(address)` | ERC20 token withdrawn |
| `amount` | `uint256` | Amount of tokens withdrawn |
| `isDepleted` | `bool` | True if user's balance is now zero |

### `SimpleErc20VaultTransfer`

Emitted when balances are transferred between users (liquidations).

#### Event Data

| Field | Type | Description |
|-------|------|-------------|
| `fromUser` | `indexed(address)` | User losing balance |
| `toUser` | `indexed(address)` | User gaining balance |
| `asset` | `indexed(address)` | ERC20 token transferred |
| `transferAmount` | `uint256` | Amount transferred |
| `isFromUserDepleted` | `bool` | True if from user's balance is now zero |

## Key Differences from Other Vault Types

### vs. SharesVault (RipeGov, SavingsGreen)
- **No Share Calculation**: SimpleErc20 uses direct 1:1 balance accounting
- **No Yield**: Doesn't generate additional value over time
- **No Lock Mechanisms**: No time-locking or governance features

### vs. StabVault (StabilityPool)
- **No USD Value Accounting**: Uses direct token amounts, not USD values
- **No Liquidated Assets**: Doesn't accumulate assets from liquidations
- **No Complex Claims**: Simple deposit/withdraw, no claiming systems

### vs. BasicVault Module
SimpleErc20 IS a BasicVault implementation with:
- **Contract-Specific Events**: Provides SimpleErc20-specific event signatures
- **Access Controls**: Implements specific access restrictions at contract level
- **Interface Compliance**: Meets Vault interface requirements

## Security Considerations

### Access Controls
- **Teller Only**: Deposits restricted to Teller contract
- **Authorized Withdrawals**: Withdrawals restricted to Teller, AuctionHouse, and CreditEngine
- **Liquidation Transfers**: Internal transfers only allowed for liquidation contracts

### Balance Safety
- **Direct Accounting**: No complex calculations that could introduce errors
- **Amount Capping**: All operations capped by available balances
- **Atomic Operations**: All balance changes are atomic through VaultData

### Simplicity Benefits
- **No Yield Complexity**: Eliminates risks from yield calculations or share price manipulation
- **No Oracle Dependencies**: Doesn't rely on price oracles for basic operations
- **Transparent Operations**: Users know exactly what they'll receive on withdrawal

### Integration Safety
- **Module Delegation**: Core logic handled by battle-tested BasicVault module
- **Event Consistency**: Contract-specific events provide clear audit trails
- **Collateral Compatibility**: Works seamlessly with CreditEngine for borrowing

## Usage Patterns

### Basic Deposit/Withdrawal
```python
# User deposits tokens
teller.depositToVault(
    simple_erc20_vault.address,
    usdc_token.address,
    1000_000000,  # 1000 USDC
    sender=user.address
)

# User withdraws tokens
teller.withdrawFromVault(
    simple_erc20_vault.address,
    usdc_token.address,
    500_000000,   # 500 USDC
    user.address,  # Recipient
    sender=user.address
)
```

### Collateral Usage
```python
# User borrows against vault collateral
credit_engine.borrow(
    user.address,
    green_token.address,  # Borrow GREEN
    1000_000000000000000000,  # 1000 GREEN
    sender=user.address
    # CreditEngine automatically evaluates SimpleErc20 vault collateral
)
```

### Liquidation Integration
```python
# During liquidation, collateral is transferred to liquidator
auction_house.liquidate(
    borrower.address,
    liquidator.address
    # AuctionHouse calls transferBalanceWithinVault automatically
)
```

## Testing

For comprehensive test examples, see: [`tests/vaults/test_simple_erc20.py`](../../tests/vaults/test_simple_erc20.py)