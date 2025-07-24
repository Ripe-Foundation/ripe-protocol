# StabilityPool Vault Technical Documentation

[📄 View Source Code](../../contracts/vaults/StabilityPool.vy)

## Overview

StabilityPool is a specialized vault that acts as the protocol's liquidation backstop. Users deposit stablecoins (GREEN, sGREEN) to earn discounted collateral from liquidations, typically receiving 5-10% instant profit while helping maintain protocol solvency.

**How It Works**:
- **Deposit Stablecoins**: Provide GREEN or sGREEN to the stability pool
- **Receive Liquidated Assets**: Automatically get ETH, BTC, or other collateral at discount
- **Earn RIPE Rewards**: Additional incentives for providing stability

Built on the StabVault module, StabilityPool uses USD-based share accounting to fairly distribute liquidation proceeds. It integrates directly with [AuctionHouse](../core/AuctionHouse.md) for collateral distribution and tracks both original deposits and accumulated rewards for transparent accounting. The stability pool is managed through [VaultBook](../registries/VaultBook.md) and configuration is handled via [MissionControl](../data/MissionControl.md).

## Architecture & Dependencies

StabilityPool is built using a modular architecture with delegation to specialized modules:

### Core Module Dependencies

- **StabVault**: Provides sophisticated stability pool functionality with USD value-based accounting
- **VaultData**: Manages user balances, asset registration, and vault state
- **[Addys](../modules/Addys.md)**: Handles protocol address resolution and permission management

### Module Initialization

```vyper
exports: addys.__interface__
exports: vaultData.__interface__
exports: stabVault.__interface__

initializes: addys
initializes: vaultData[addys := addys]
initializes: stabVault[addys := addys, vaultData := vaultData]
```

## System Architecture Diagram

```
+------------------------------------------------------------------------+
|                       StabilityPool Vault                             |
+------------------------------------------------------------------------+
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Contract-Level Operations                     |  |
|  |                                                                  |  |
|  |  depositTokensInVault():                                         |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ 1. Access Control: Only Teller allowed                     │ |  |
|  |  │ 2. Delegate to StabVault._depositTokensInVault()            │ |  |
|  |  │ 3. Emit StabilityPoolDeposit event                         │ |  |
|  |  │ 4. Return deposit amount                                    │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  |                                                                  |  |
|  |  withdrawTokensFromVault():                                      |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ 1. Access Control: Teller, AuctionHouse, CreditEngine      │ |  |
|  |  │ 2. Delegate to StabVault._withdrawTokensFromVault()         │ |  |
|  |  │ 3. Emit StabilityPoolWithdrawal event                      │ |  |
|  |  │ 4. Return withdrawal amount and depletion status           │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  |                                                                  |  |
|  |  transferBalanceWithinVault():                                   |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ 1. Access Control: AuctionHouse, CreditEngine              │ |  |
|  |  │ 2. Delegate to StabVault._transferBalanceWithinVault()      │ |  |
|  |  │ 3. Emit StabilityPoolTransfer event                        │ |  |
|  |  │ 4. Return transfer amount and depletion status             │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Integration Support                           |  |
|  |                                                                  |  |
|  |  getVaultDataOnDeposit():                                        |  |
|  |  • Delegates to StabVault for Teller integration                |  |
|  |                                                                  |  |
|  |  getUserLootBoxShare():                                          |  |
|  |  • Delegates to StabVault for Lootbox reward calculations       |  |
|  |                                                                  |  |
|  |  getUserAssetAndAmountAtIndex():                                 |  |
|  |  • Delegates to StabVault for CreditEngine integration          |  |
|  |                                                                  |  |
|  |  getUserAssetAtIndexAndHasBalance():                             |  |
|  |  • Delegates to StabVault for Lootbox and AuctionHouse          |  |
|  +------------------------------------------------------------------+  |
+------------------------------------------------------------------------+
                                    |
                                    | Delegates all core functionality
                                    v
+------------------------------------------------------------------------+
|                          StabVault Module                             |
+------------------------------------------------------------------------+
|                                                                        |
| • USD value-based share accounting                                     |
| • Claimable asset management and tracking                              |
| • Liquidation integration with AuctionHouse                           |
| • Claim and redemption system implementation                           |
| • Reward distribution and governance vault integration                 |
| • Complex pool value calculations with PriceDesk integration          |
+------------------------------------------------------------------------+
```

## Constructor

### `__init__`

Initializes StabilityPool with protocol address configuration.

```vyper
@deploy
def __init__(_ripeHq: address):
```

#### Parameters

| Name      | Type      | Description                                      |
| --------- | --------- | ------------------------------------------------ |
| `_ripeHq` | `address` | RipeHq contract address for protocol integration |

#### Process Flow

1. **Address Setup**: Initializes Addys module with RipeHq address
2. **VaultData Setup**: Initializes with non-paused state (`False`)
3. **StabVault Setup**: Initializes stability pool functionality

#### Example Usage

```python
# Deploy stability pool vault
stability_pool = boa.load(
    "contracts/vaults/StabilityPool.vy",
    ripe_hq.address
)
```

## Core Functions

### `depositTokensInVault`

Handles deposits into the stability pool with USD value-based share accounting.

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

| Name      | Type          | Description                                |
| --------- | ------------- | ------------------------------------------ |
| `_user`   | `address`     | User making the deposit                    |
| `_asset`  | `address`     | Stability pool asset (GREEN, sGREEN, etc.) |
| `_amount` | `uint256`     | Amount to deposit                          |
| `_a`      | `addys.Addys` | Protocol addresses struct                  |

#### Returns

| Type      | Description             |
| --------- | ----------------------- |
| `uint256` | Actual amount deposited |

#### Access

Only callable by [Teller](../core/Teller.md)

#### Process Flow

1. **Access Validation**: Ensures caller is Teller contract
2. **StabVault Delegation**: Calls `stabVault._depositTokensInVault()` for core functionality
3. **Event Emission**: Logs deposit with user, asset, amount, and shares
4. **Return**: Returns actual deposit amount

#### Events Emitted

- `StabilityPoolDeposit` - Contains user, asset, amount, and shares minted

#### Example Usage

```python
# Deposit GREEN into stability pool through Teller
deposit_amount = stability_pool.depositTokensInVault(
    user.address,
    green_token.address,
    1000_000000000000000000,  # 1000 GREEN
    empty(addys.Addys),       # Use default addresses
    sender=teller.address
)
```

### `withdrawTokensFromVault`

Handles withdrawals from the stability pool with share burning and liquidated asset claims.

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

| Name         | Type          | Description                         |
| ------------ | ------------- | ----------------------------------- |
| `_user`      | `address`     | User making withdrawal              |
| `_asset`     | `address`     | Stability pool asset to withdraw    |
| `_amount`    | `uint256`     | Amount to withdraw                  |
| `_recipient` | `address`     | Address to receive withdrawn assets |
| `_a`         | `addys.Addys` | Protocol addresses struct           |

#### Returns

| Type      | Description                         |
| --------- | ----------------------------------- |
| `uint256` | Actual amount withdrawn             |
| `bool`    | True if user's position is depleted |

#### Access

Only callable by [Teller](../core/Teller.md), AuctionHouse, or CreditEngine

#### Process Flow

1. **Access Validation**: Ensures caller is authorized contract
2. **StabVault Delegation**: Calls `stabVault._withdrawTokensFromVault()` for core functionality
3. **Event Emission**: Logs withdrawal with depletion status and shares burned
4. **Return**: Returns withdrawal amount and depletion status

#### Events Emitted

- `StabilityPoolWithdrawal` - Contains user, asset, amount, depletion status, and shares burned

#### Example Usage

```python
# Withdraw GREEN from stability pool through AuctionHouse
withdrawal_amount, is_depleted = stability_pool.withdrawTokensFromVault(
    liquidated_user.address,    # User being liquidated
    green_token.address,        # Asset to withdraw
    500_000000000000000000,     # 500 GREEN
    auction_house.address,      # Recipient
    empty(addys.Addys),         # Use default addresses
    sender=auction_house.address
)
```

### `transferBalanceWithinVault`

Transfers stability pool positions between users (used for liquidations).

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

| Name              | Type          | Description                      |
| ----------------- | ------------- | -------------------------------- |
| `_asset`          | `address`     | Stability pool asset to transfer |
| `_fromUser`       | `address`     | User losing the position         |
| `_toUser`         | `address`     | User gaining the position        |
| `_transferAmount` | `uint256`     | Amount to transfer               |
| `_a`              | `addys.Addys` | Protocol addresses struct        |

#### Returns

| Type      | Description                              |
| --------- | ---------------------------------------- |
| `uint256` | Actual amount transferred                |
| `bool`    | True if from user's position is depleted |

#### Access

Only callable by [AuctionHouse](../core/AuctionHouse.md) or CreditEngine (for liquidations)

#### Process Flow

1. **Access Validation**: Ensures caller is liquidation contract
2. **StabVault Delegation**: Calls `stabVault._transferBalanceWithinVault()` for share transfers
3. **Event Emission**: Logs transfer with from/to users and depletion status
4. **Return**: Returns transfer details

#### Events Emitted

- `StabilityPoolTransfer` - Contains fromUser, toUser, asset, transferAmount, depletion status, and shares transferred

## Integration Support Functions

### `getVaultDataOnDeposit`

Provides vault data needed by Teller for deposit operations.

```vyper
@view
@external
def getVaultDataOnDeposit(_user: address, _asset: address) -> Vault.VaultDataOnDeposit:
```

#### Parameters

| Name     | Type      | Description           |
| -------- | --------- | --------------------- |
| `_user`  | `address` | User making deposit   |
| `_asset` | `address` | Asset being deposited |

#### Returns

| Type                       | Description                                 |
| -------------------------- | ------------------------------------------- |
| `Vault.VaultDataOnDeposit` | Vault data structure for Teller integration |

#### Usage

Used by Teller.vy to validate deposits and calculate fees

### `getUserLootBoxShare`

Returns user's share for Lootbox reward calculations.

```vyper
@view
@external
def getUserLootBoxShare(_user: address, _asset: address) -> uint256:
```

#### Parameters

| Name     | Type      | Description           |
| -------- | --------- | --------------------- |
| `_user`  | `address` | User to get share for |
| `_asset` | `address` | Stability pool asset  |

#### Returns

| Type      | Description                           |
| --------- | ------------------------------------- |
| `uint256` | User's proportional share for rewards |

#### Usage

Used by Lootbox.vy for reward distribution calculations

### `getUserAssetAndAmountAtIndex`

Returns asset and amount at specific index for CreditEngine collateral calculations.

```vyper
@view
@external
def getUserAssetAndAmountAtIndex(_user: address, _index: uint256) -> (address, uint256):
```

#### Parameters

| Name     | Type      | Description   |
| -------- | --------- | ------------- |
| `_user`  | `address` | User to query |
| `_index` | `uint256` | Asset index   |

#### Returns

| Type      | Description        |
| --------- | ------------------ |
| `address` | Asset address      |
| `uint256` | Asset amount/value |

#### Usage

Used by CreditEngine.vy for collateral evaluation

#### **Important Note**

The underlying StabVault module returns `empty(address), 0` to prevent borrowing against stability pool positions, ensuring they cannot be used as collateral.

### `getUserAssetAtIndexAndHasBalance`

Returns asset at index and whether user has balance.

```vyper
@view
@external
def getUserAssetAtIndexAndHasBalance(_user: address, _index: uint256) -> (address, bool):
```

#### Parameters

| Name     | Type      | Description   |
| -------- | --------- | ------------- |
| `_user`  | `address` | User to query |
| `_index` | `uint256` | Asset index   |

#### Returns

| Type      | Description              |
| --------- | ------------------------ |
| `address` | Asset address            |
| `bool`    | True if user has balance |

#### Usage

Used by Lootbox.vy and AuctionHouse.vy for position validation

## Utility Functions

### `getTotalAmountForUser`

Returns total USD value of user's stability pool position converted to asset amount.

```vyper
@view
@external
def getTotalAmountForUser(_user: address, _asset: address) -> uint256:
```

**Note**: The returned amount represents USD value worth of the asset, not actual asset balance stored in the vault.

### `getTotalAmountForVault`

Returns total stability pool value converted to asset amount for display purposes.

```vyper
@view
@external
def getTotalAmountForVault(_asset: address) -> uint256:
```

**Note**: This includes both deposited stablecoin value and claimable liquidated asset value.

## Events

### `StabilityPoolDeposit`

Emitted when users deposit into the stability pool.

#### Event Data

| Field    | Type               | Description         |
| -------- | ------------------ | ------------------- |
| `user`   | `indexed(address)` | User making deposit |
| `asset`  | `indexed(address)` | Asset deposited     |
| `amount` | `uint256`          | Amount deposited    |
| `shares` | `uint256`          | Shares minted       |

### `StabilityPoolWithdrawal`

Emitted when users withdraw from the stability pool.

#### Event Data

| Field        | Type               | Description                    |
| ------------ | ------------------ | ------------------------------ |
| `user`       | `indexed(address)` | User making withdrawal         |
| `asset`      | `indexed(address)` | Asset withdrawn                |
| `amount`     | `uint256`          | Amount withdrawn               |
| `isDepleted` | `bool`             | True if user position depleted |
| `shares`     | `uint256`          | Shares burned                  |

### `StabilityPoolTransfer`

Emitted when positions are transferred between users (liquidations).

#### Event Data

| Field                | Type               | Description                         |
| -------------------- | ------------------ | ----------------------------------- |
| `fromUser`           | `indexed(address)` | User losing position                |
| `toUser`             | `indexed(address)` | User gaining position               |
| `asset`              | `indexed(address)` | Asset transferred                   |
| `transferAmount`     | `uint256`          | Amount transferred                  |
| `isFromUserDepleted` | `bool`             | True if from user position depleted |
| `transferShares`     | `uint256`          | Shares transferred                  |

## Advanced Functionality

### Liquidation Integration

StabilityPool integrates seamlessly with the AuctionHouse through the underlying StabVault module:

1. **Collateral Reception**: When liquidations occur, the AuctionHouse calls StabVault functions to exchange stability pool assets for liquidated collateral
2. **Automatic Distribution**: Liquidated assets are automatically distributed proportionally among all stability pool participants
3. **Share Value Increase**: Addition of liquidated collateral increases the total pool value, benefiting all depositors

### Claim and Redemption System

Through the StabVault module, users can:

1. **Claim Liquidated Assets**: Users can claim their proportional share of accumulated liquidated collateral
2. **Redeem with GREEN**: GREEN token holders can redeem for available claimable assets across all stability pools
3. **Automatic Rewards**: Claims trigger automatic Ripe token rewards locked in the governance vault

### USD Value-Based Accounting

Unlike traditional vaults that use 1:1 asset accounting, StabilityPool uses sophisticated USD value-based share calculations:

1. **Deposit Shares**: Calculated based on USD value contribution to total pool value
2. **Pool Value**: Includes both deposited stablecoin value and accumulated liquidated asset value
3. **Fair Distribution**: Ensures all participants benefit proportionally from liquidation proceeds

## Security Considerations

### Access Controls

- **Teller Only**: Deposits restricted to Teller contract
- **Liquidation Contracts**: Withdrawals and transfers restricted to authorized liquidation contracts
- **StabVault Delegation**: All complex logic handled by battle-tested StabVault module

### Position Safety

- **No Borrowing**: Stability pool positions cannot be used as collateral for borrowing
- **Proportional Distribution**: All liquidation proceeds distributed fairly based on pool participation
- **Share Protection**: USD value-based accounting prevents manipulation through volatile asset prices

### Integration Safety

- **Event Consistency**: Contract-specific events provide clear audit trails
- **Module Isolation**: Core functionality isolated in StabVault module for security and upgradability
- **Access Validation**: All external calls validate caller permissions through Addys module

## Usage Patterns

### Depositing to Stability Pool

```python
# User deposits GREEN through Teller
result = teller.depositToVault(
    stability_pool.address,
    green_token.address,
    1000_000000000000000000,  # 1000 GREEN
    sender=user.address
)
```

### Claiming Liquidated Assets

```python
# User claims accumulated WETH from GREEN stability pool
result = teller.claimFromStabilityPool(
    stability_pool.address,
    green_token.address,      # Stability pool asset
    weth.address,             # Asset to claim
    500_000000000000000000,   # Max $500 value
    True,                     # Auto-deposit
    sender=user.address
)
```

### Redeeming GREEN for Assets

```python
# Redeem GREEN for available claimable assets
result = teller.redeemFromStabilityPool(
    stability_pool.address,
    weth.address,             # Asset to redeem for
    1000_000000000000000000,  # GREEN to spend
    False,                    # Don't auto-deposit
    True,                     # Refund as sGREEN
    sender=user.address
)
```

## Testing

For comprehensive test examples, see: [`tests/vaults/test_stability_pool.py`](../../tests/vaults/test_stability_pool.py)
