# Teller Technical Documentation

[📄 View Source Code](../../contracts/core/Teller.vy)

## Overview

Teller is the primary gateway to the Ripe Protocol, serving as a unified interface for all user operations. Like a comprehensive banking teller, it orchestrates complex multi-contract operations while providing user-friendly
interfaces and robust permission management.

**Unified Operations**:
- **Asset Management**: Deposits, withdrawals with automatic vault selection, configurable limits, and batch operations
- **Credit Services**: Borrowing against collateral and debt repayment with support for both Green and Savings Green tokens
- **Market Participation**: Liquidations, auction purchases, stability pool interactions, and collateral redemption
- **Rewards & Governance**: Loot claiming, Ripe bond purchases, and governance vault management
- **Delegation System**: Comprehensive permissions allowing authorized proxy operations with Underscore wallet integration

The contract abstracts protocol complexity through automatic vault selection, batch processing for gas efficiency, flexible payment handling, sophisticated permission hierarchies, and comprehensive event logging while maintaining security through thoughtful validation layers. It interfaces with [CreditEngine](CreditEngine.md) for borrowing operations, [VaultBook](../registries/VaultBook.md) for vault validation, and [Lootbox](Lootbox.md) for rewards coordination.

## Architecture & Modules

Teller is built using a modular architecture with the following components:

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
  - No minting capabilities (Teller is interface only)
- **Exported Interface**: Department basics via `deptBasics.__interface__`

### Module Initialization
```vyper
initializes: addys
initializes: deptBasics[addys := addys]
```

## System Architecture Diagram

```
+------------------------------------------------------------------------+
|                         Teller Contract                                |
+------------------------------------------------------------------------+
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    User Interface Layer                          |  |
|  |                                                                  |  |
|  |  Single Entry Point for All User Operations:                    |  |
|  |  - Deposits & Withdrawals                                        |  |
|  |  - Borrowing & Repayment                                         |  |
|  |  - Liquidations & Auctions                                       |  |
|  |  - Stability Pool Operations                                     |  |
|  |  - Reward Claims & Bond Purchases                                |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                   Permission & Validation                        |  |
|  |                                                                  |  |
|  |  Access Controls:                                                |  |
|  |  - User ownership verification                                   |  |
|  |  - Delegation system support                                     |  |
|  |  - Underscore wallet integration                                 |  |
|  |  - Operation-specific permissions                                |  |
|  |                                                                  |  |
|  |  Validation Logic:                                               |  |
|  |  - Deposit limits (per-user, global)                            |  |
|  |  - Asset compatibility checks                                    |  |
|  |  - Vault capacity validation                                     |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                      Operation Routing                          |  |
|  |                                                                  |  |
|  |  Smart Contract Orchestration:                                   |  |
|  |  - Automatic vault selection                                     |  |
|  |  - Multi-contract operation coordination                         |  |
|  |  - Batch processing optimization                                 |  |
|  |  - Event emission & logging                                      |  |
|  +------------------------------------------------------------------+  |
+------------------------------------------------------------------------+
                                    |
        +---------------------------+---------------------------+
        |                           |                           |
        v                           v                           v
+------------------+    +-------------------+    +------------------+
| Vault System     |    | CreditEngine      |    | AuctionHouse     |
| * Asset storage  |    | * Borrowing       |    | * Liquidations   |
| * User deposits  |    | * Debt management |    | * Auctions       |
| * Yield tracking |    | * Collateral calc |    | * Price discover |
+------------------+    +-------------------+    +------------------+
        |                           |                           |
        v                           v                           v
+------------------+    +-------------------+    +------------------+
| StabVault        |    | Lootbox           |    | BondRoom         |
| * Stability pool |    | * Reward claims   |    | * Bond sales     |
| * Green claims   |    | * Points tracking |    | * Ripe purchase  |
+------------------+    +-------------------+    +------------------+
```

## Data Structures

### TellerDepositConfig Struct
Deposit validation configuration:
```vyper
struct TellerDepositConfig:
    canDepositGeneral: bool          # Global deposits enabled
    canDepositAsset: bool            # Asset deposits enabled
    doesVaultSupportAsset: bool      # Vault-asset compatibility
    isUserAllowed: bool              # User whitelist check
    perUserDepositLimit: uint256     # Per-user deposit cap
    globalDepositLimit: uint256      # Protocol-wide cap
    perUserMaxAssetsPerVault: uint256  # Asset diversity limit
    perUserMaxVaults: uint256        # Vault count limit
    canAnyoneDeposit: bool           # Allow proxy deposits
    minDepositBalance: uint256       # Minimum position size
```

### TellerWithdrawConfig Struct
Withdrawal validation configuration:
```vyper
struct TellerWithdrawConfig:
    canWithdrawGeneral: bool         # Global withdrawals enabled
    canWithdrawAsset: bool           # Asset withdrawals enabled
    isUserAllowed: bool              # User whitelist check
    canWithdrawForUser: bool         # Allow proxy withdrawals
    minDepositBalance: uint256       # Minimum remaining balance
```

### DepositAction Struct
Batch deposit specification:
```vyper
struct DepositAction:
    asset: address                   # Asset to deposit
    amount: uint256                  # Amount to deposit
    vaultAddr: address               # Target vault address
    vaultId: uint256                 # Target vault ID
```

### WithdrawalAction Struct
Batch withdrawal specification:
```vyper
struct WithdrawalAction:
    asset: address                   # Asset to withdraw
    amount: uint256                  # Amount to withdraw
    vaultAddr: address               # Source vault address
    vaultId: uint256                 # Source vault ID
```

## State Variables

### Constants
- `MAX_BALANCE_ACTION: uint256 = 20` - Batch operation limit
- `MAX_CLAIM_USERS: uint256 = 25` - Batch claim limit
- `MAX_COLLATERAL_REDEMPTIONS: uint256 = 20` - Redemption batch limit
- `MAX_AUCTION_PURCHASES: uint256 = 20` - Auction batch limit
- `MAX_LIQ_USERS: uint256 = 50` - Liquidation batch limit
- `MAX_STAB_CLAIMS: uint256 = 15` - Stability pool claim limit
- `MAX_STAB_REDEMPTIONS: uint256 = 15` - Stability pool redemption limit
- `STABILITY_POOL_ID: uint256 = 1` - Stability pool vault ID
- `RIPE_GOV_VAULT_ID: uint256 = 2` - Governance vault ID

### Inherited State Variables
From [DeptBasics](../modules/DeptBasics.md):
- `isPaused: bool` - Department pause state

## Constructor

### `__init__`

Initializes Teller as the protocol's user interface layer.

```vyper
@deploy
def __init__(_ripeHq: address, _shouldPause: bool):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_ripeHq` | `address` | RipeHq contract address |
| `_shouldPause` | `bool` | Whether to start paused |

#### Returns

*Constructor does not return any values*

#### Access

Called only during deployment

#### Example Usage
```python
# Deploy Teller
teller = boa.load(
    "contracts/core/Teller.vy",
    ripe_hq.address,
    False  # Don't start paused
)
```

**Example Output**: Contract deployed as protocol interface layer

## Deposit Functions

### `deposit`

Deposits assets into vaults with automatic vault selection.

```vyper
@nonreentrant
@external
def deposit(
    _asset: address,
    _amount: uint256 = max_value(uint256),
    _user: address = msg.sender,
    _vaultAddr: address = empty(address),
    _vaultId: uint256 = 0,
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_asset` | `address` | Asset to deposit |
| `_amount` | `uint256` | Amount to deposit (max for all balance) |
| `_user` | `address` | Recipient user (defaults to caller) |
| `_vaultAddr` | `address` | Specific vault address (optional) |
| `_vaultId` | `uint256` | Specific vault ID (optional) |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Actual amount deposited |

#### Access

Public function with permission checks

#### Events Emitted

- `TellerDeposit` - Complete deposit details including user, depositor, asset, amount, and vault info

#### Example Usage
```python
# Simple deposit - auto-selects vault
amount_deposited = teller.deposit(
    usdc.address,
    1000_000000  # 1000 USDC
)

# Deposit for another user (if permitted)
amount_deposited = teller.deposit(
    weth.address,
    5_000000000000000000,  # 5 ETH
    recipient.address,
    vault_addr,
    vault_id
)
```

**Example Output**: Validates permissions, transfers tokens, updates vault balances

### `depositMany`

Batch deposits multiple assets/amounts in single transaction.

```vyper
@nonreentrant
@external
def depositMany(_user: address, _deposits: DynArray[DepositAction, MAX_BALANCE_ACTION]) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | Recipient user |
| `_deposits` | `DynArray[DepositAction, 20]` | Deposit specifications |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Number of deposits executed |

#### Access

Public function with permission checks

#### Example Usage
```python
# Batch deposit multiple assets
deposits = [
    DepositAction(usdc.address, 1000_000000, vault1, 0),
    DepositAction(weth.address, 5e18, vault2, 0),
    DepositAction(wbtc.address, 2e8, vault3, 0)
]
count = teller.depositMany(user.address, deposits)
```

### `depositFromTrusted`

Internal deposit function for protocol contracts.

```vyper
@external
def depositFromTrusted(
    _user: address,
    _vaultId: uint256,
    _asset: address,
    _amount: uint256,
    _lockDuration: uint256,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User receiving deposit |
| `_vaultId` | `uint256` | Target vault ID |
| `_asset` | `address` | Asset to deposit |
| `_amount` | `uint256` | Amount to deposit |
| `_lockDuration` | `uint256` | Lock duration (for governance vault) |
| `_a` | `addys.Addys` | Cached addresses (optional) |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Amount deposited |

#### Access

Only callable by valid Ripe addresses

## Withdrawal Functions

### `withdraw`

Withdraws assets from vaults with health checks.

```vyper
@nonreentrant
@external
def withdraw(
    _asset: address,
    _amount: uint256 = max_value(uint256),
    _user: address = msg.sender,
    _vaultAddr: address = empty(address),
    _vaultId: uint256 = 0,
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_asset` | `address` | Asset to withdraw |
| `_amount` | `uint256` | Amount to withdraw (max for all) |
| `_user` | `address` | User to withdraw from |
| `_vaultAddr` | `address` | Specific vault address (optional) |
| `_vaultId` | `uint256` | Specific vault ID (optional) |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Actual amount withdrawn |

#### Access

Public function with permission checks

#### Events Emitted

- `TellerWithdrawal` - Complete withdrawal details including depletion status

#### Example Usage
```python
# Withdraw USDC
amount_withdrawn = teller.withdraw(
    usdc.address,
    500_000000  # 500 USDC
)

# Withdraw all of an asset
amount_withdrawn = teller.withdraw(
    weth.address,
    sender=user.address
)
```

### `withdrawMany`

Batch withdrawals in single transaction.

```vyper
@nonreentrant
@external
def withdrawMany(_user: address, _withdrawals: DynArray[WithdrawalAction, MAX_BALANCE_ACTION]) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User to withdraw from |
| `_withdrawals` | `DynArray[WithdrawalAction, 20]` | Withdrawal specifications |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Number of withdrawals executed |

#### Access

Public function with permission checks

## Credit Functions

### `borrow`

Borrows Green tokens against collateral.

```vyper
@nonreentrant
@external
def borrow(
    _user: address,
    _greenAmount: uint256,
    _wantsSavingsGreen: bool = False,
    _shouldEnterStabPool: bool = False,
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User to borrow for |
| `_greenAmount` | `uint256` | Amount to borrow |
| `_wantsSavingsGreen` | `bool` | Receive as sGreen |
| `_shouldEnterStabPool` | `bool` | Auto-deposit to stability pool |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Amount borrowed after fees |

#### Access

Public function with permission checks

#### Example Usage
```python
# Borrow Green tokens
amount_borrowed = teller.borrow(
    user.address,
    1000e18,  # 1000 Green
    True,     # Want sGreen
    False     # Don't enter stability pool
)
```

### `repay`

Repays debt using Green or Savings Green tokens.

```vyper
@nonreentrant
@external
def repay(
    _user: address,
    _greenAmount: uint256,
    _isPaymentSavingsGreen: bool = False,
    _shouldRefundSavingsGreen: bool = False,
) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User whose debt to repay |
| `_greenAmount` | `uint256` | Amount to repay |
| `_isPaymentSavingsGreen` | `bool` | Paying with sGreen |
| `_shouldRefundSavingsGreen` | `bool` | Refund excess as sGreen |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if debt health restored |

#### Access

Public function with permission checks

## Liquidation Functions

### `liquidateUser`

Liquidates a single unhealthy position.

```vyper
@external
def liquidateUser(_liqUser: address, _keeper: address, _wantsSavingsGreen: bool) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_liqUser` | `address` | User to liquidate |
| `_keeper` | `address` | Keeper receiving rewards |
| `_wantsSavingsGreen` | `bool` | Receive rewards as sGreen |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Keeper rewards received |

#### Access

Public function

#### Example Usage
```python
# Liquidate unhealthy position
keeper_rewards = teller.liquidateUser(
    underwater_user.address,
    keeper.address,
    True  # Want sGreen rewards
)
```

### `liquidateManyUsers`

Batch liquidates multiple positions.

```vyper
@external
def liquidateManyUsers(
    _liqUsers: DynArray[address, MAX_LIQ_USERS], 
    _keeper: address, 
    _wantsSavingsGreen: bool
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_liqUsers` | `DynArray[address, 50]` | Users to liquidate |
| `_keeper` | `address` | Keeper receiving rewards |
| `_wantsSavingsGreen` | `bool` | Receive rewards as sGreen |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Total keeper rewards |

#### Access

Public function

## Auction Functions

### `buyFungibleAuction`

Purchases collateral from liquidation auction.

```vyper
@external
def buyFungibleAuction(
    _liqUser: address,
    _vaultId: uint256,
    _asset: address,
    _greenAmount: uint256,
    _isPaymentSavingsGreen: bool = False,
    _recipient: address = msg.sender,
    _shouldTransferBalance: bool = False,
    _shouldRefundSavingsGreen: bool = False,
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_liqUser` | `address` | User being liquidated |
| `_vaultId` | `uint256` | Vault containing asset |
| `_asset` | `address` | Asset to purchase |
| `_greenAmount` | `uint256` | Max Green to spend |
| `_isPaymentSavingsGreen` | `bool` | Paying with sGreen |
| `_recipient` | `address` | Collateral recipient |
| `_shouldTransferBalance` | `bool` | Transfer vs withdraw |
| `_shouldRefundSavingsGreen` | `bool` | Refund as sGreen |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Green spent on purchase |

#### Access

Public function

### `buyManyFungibleAuctions`

Batch purchases from multiple auctions.

```vyper
@external
def buyManyFungibleAuctions(
    _purchases: DynArray[FungAuctionPurchase, MAX_AUCTION_PURCHASES],
    _greenAmount: uint256,
    _isPaymentSavingsGreen: bool = False,
    _recipient: address = msg.sender,
    _shouldTransferBalance: bool = False,
    _shouldRefundSavingsGreen: bool = False,
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_purchases` | `DynArray[FungAuctionPurchase, 20]` | Auction purchase specs |
| `_greenAmount` | `uint256` | Total Green budget |
| `_isPaymentSavingsGreen` | `bool` | Paying with sGreen |
| `_recipient` | `address` | Collateral recipient |
| `_shouldTransferBalance` | `bool` | Transfer vs withdraw |
| `_shouldRefundSavingsGreen` | `bool` | Refund as sGreen |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Total Green spent |

#### Access

Public function

## Stability Pool Functions

### `convertToSavingsGreenAndDepositIntoStabPool`

Converts Green tokens to Savings Green and deposits into the stability pool.

```vyper
@nonreentrant
@external
def convertToSavingsGreenAndDepositIntoStabPool(
    _user: address,
    _greenAmount: uint256,
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User to deposit for |
| `_greenAmount` | `uint256` | Amount of Green to convert and deposit |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Amount of Savings Green deposited |

#### Access

Public function with permission checks

#### Example Usage
```python
# Convert 1000 Green to sGreen and deposit into stability pool
amount_deposited = teller.convertToSavingsGreenAndDepositIntoStabPool(
    user.address,
    1000_000000000000000000  # 1000 Green
)
```

### `claimFromStabilityPool`

Claims rewards from a single stability pool position.

```vyper
@nonreentrant
@external
def claimFromStabilityPool(
    _user: address,
    _stabVaultAddr: address,
    _wantsSavingsGreen: bool = False,
) -> (uint256, uint256):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User claiming rewards |
| `_stabVaultAddr` | `address` | Stability pool vault address |
| `_wantsSavingsGreen` | `bool` | Receive rewards as sGreen |

#### Returns

| Type | Description |
|------|-------------|
| `(uint256, uint256)` | (greenRewards, ripeRewards) |

#### Access

Public function with permission checks

#### Example Usage
```python
# Claim stability pool rewards
green_rewards, ripe_rewards = teller.claimFromStabilityPool(
    user.address,
    stab_vault.address,
    True  # Want rewards as sGreen
)
```

### `claimManyFromStabilityPool`

Batch claims rewards from multiple stability pool positions.

```vyper
@nonreentrant
@external
def claimManyFromStabilityPool(
    _user: address,
    _stabVaults: DynArray[address, MAX_STAB_CLAIMS],
    _wantsSavingsGreen: bool = False,
) -> (uint256, uint256):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User claiming rewards |
| `_stabVaults` | `DynArray[address, 15]` | List of stability pool vaults |
| `_wantsSavingsGreen` | `bool` | Receive rewards as sGreen |

#### Returns

| Type | Description |
|------|-------------|
| `(uint256, uint256)` | (totalGreenRewards, totalRipeRewards) |

#### Access

Public function with permission checks

#### Example Usage
```python
# Claim from multiple stability pools
vaults = [stab_vault1.address, stab_vault2.address, stab_vault3.address]
green_total, ripe_total = teller.claimManyFromStabilityPool(
    user.address,
    vaults,
    False  # Want Green tokens
)
```

### `redeemFromStabilityPool`

Redeems collateral from liquidations using stability pool position.

```vyper
@nonreentrant
@external
def redeemFromStabilityPool(
    _user: address,
    _stabVaultAddr: address,
    _redemptions: DynArray[StabVaultRedemption, MAX_BALANCE_ACTION],
    _shouldTransferBalance: bool = False,
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User redeeming collateral |
| `_stabVaultAddr` | `address` | Stability pool vault |
| `_redemptions` | `DynArray[StabVaultRedemption, 20]` | Redemption specifications |
| `_shouldTransferBalance` | `bool` | Transfer vs withdraw collateral |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Total collateral value redeemed |

#### Access

Public function with permission checks

#### Example Usage
```python
# Redeem collateral from stability pool
redemptions = [
    StabVaultRedemption(weth.address, 2e18),    # 2 ETH
    StabVaultRedemption(wbtc.address, 0.5e8),   # 0.5 BTC
]
value_redeemed = teller.redeemFromStabilityPool(
    user.address,
    stab_vault.address,
    redemptions,
    False  # Withdraw to user
)
```

### `redeemManyFromStabilityPool`

Batch redeems collateral from multiple stability pools.

```vyper
@nonreentrant
@external
def redeemManyFromStabilityPool(
    _user: address,
    _stabRedemptions: DynArray[StabPoolRedemptions, MAX_STAB_REDEMPTIONS],
    _shouldTransferBalance: bool = False,
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User redeeming collateral |
| `_stabRedemptions` | `DynArray[StabPoolRedemptions, 15]` | Pool redemption specs |
| `_shouldTransferBalance` | `bool` | Transfer vs withdraw |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Total collateral value redeemed |

#### Access

Public function with permission checks

## Collateral Redemption Functions

### `redeemCollateral`

Redeems collateral from unhealthy positions using Green tokens.

```vyper
@nonreentrant
@external
def redeemCollateral(
    _userToRedeemFrom: address,
    _vaultId: uint256,
    _asset: address,
    _greenAmount: uint256,
    _recipient: address = msg.sender,
    _isPaymentSavingsGreen: bool = False,
    _shouldTransferBalance: bool = False,
    _shouldRefundSavingsGreen: bool = False,
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_userToRedeemFrom` | `address` | User with unhealthy position |
| `_vaultId` | `uint256` | Vault containing collateral |
| `_asset` | `address` | Collateral asset to redeem |
| `_greenAmount` | `uint256` | Green to spend on redemption |
| `_recipient` | `address` | Collateral recipient |
| `_isPaymentSavingsGreen` | `bool` | Paying with sGreen |
| `_shouldTransferBalance` | `bool` | Transfer vs withdraw |
| `_shouldRefundSavingsGreen` | `bool` | Refund excess as sGreen |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Green amount used for redemption |

#### Access

Public function

#### Example Usage
```python
# Redeem ETH from unhealthy position
green_spent = teller.redeemCollateral(
    unhealthy_user.address,
    1,  # Vault ID
    weth.address,
    500_000000000000000000,  # 500 Green budget
    redeemer.address,
    False,  # Paying with Green
    False,  # Withdraw collateral
    True    # Refund excess as sGreen
)
```

### `redeemCollateralFromMany`

Batch redeems collateral from multiple unhealthy positions.

```vyper
@nonreentrant
@external
def redeemCollateralFromMany(
    _redemptions: DynArray[CollateralRedemption, MAX_COLLATERAL_REDEMPTIONS],
    _greenAmount: uint256,
    _recipient: address = msg.sender,
    _isPaymentSavingsGreen: bool = False,
    _shouldTransferBalance: bool = False,
    _shouldRefundSavingsGreen: bool = False,
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_redemptions` | `DynArray[CollateralRedemption, 20]` | Redemption specifications |
| `_greenAmount` | `uint256` | Total Green budget |
| `_recipient` | `address` | Collateral recipient |
| `_isPaymentSavingsGreen` | `bool` | Paying with sGreen |
| `_shouldTransferBalance` | `bool` | Transfer vs withdraw |
| `_shouldRefundSavingsGreen` | `bool` | Refund excess as sGreen |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Total Green spent |

#### Access

Public function

#### Example Usage
```python
# Redeem from multiple positions
redemptions = [
    CollateralRedemption(user1.address, 1, weth.address, 100e18),
    CollateralRedemption(user2.address, 1, wbtc.address, 50e18)
]
total_spent = teller.redeemCollateralFromMany(
    redemptions,
    1000_000000000000000000,  # 1000 Green budget
    redeemer.address,
    True,   # Paying with sGreen
    False,  # Withdraw
    False   # Refund as Green
)
```

## Permission Management Functions

### `setUserConfig`

Sets user's general permission configuration.

```vyper
@external
def setUserConfig(
    _user: address,
    _canAnyoneDeposit: bool,
    _canAnyoneRepayDebt: bool,
    _canAnyoneBondForUser: bool,
):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User to configure |
| `_canAnyoneDeposit` | `bool` | Allow proxy deposits |
| `_canAnyoneRepayDebt` | `bool` | Allow proxy debt repayment |
| `_canAnyoneBondForUser` | `bool` | Allow proxy bond purchases |

#### Access

Only callable by user or authorized delegates

#### Events Emitted

- `UserConfigSet` - New configuration details

### `setUserDelegation`

Sets operation-specific delegation permissions.

```vyper
@external
def setUserDelegation(
    _user: address,
    _delegate: address,
    _canWithdraw: bool,
    _canBorrow: bool,
    _canClaimFromStabPool: bool,
    _canClaimLoot: bool,
):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User granting permissions |
| `_delegate` | `address` | Delegate receiving permissions |
| `_canWithdraw` | `bool` | Allow withdrawal operations |
| `_canBorrow` | `bool` | Allow borrowing operations |
| `_canClaimFromStabPool` | `bool` | Allow stability pool claims |
| `_canClaimLoot` | `bool` | Allow reward claims |

#### Access

Only callable by user or authorized delegates

#### Events Emitted

- `UserDelegationSet` - Delegation configuration details

## Utility Functions

### `isUnderscoreWalletOwner`

Checks if caller owns an Underscore smart wallet.

```vyper
@view
@external
def isUnderscoreWalletOwner(_user: address, _caller: address, _mc: address = empty(address)) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | Smart wallet address |
| `_caller` | `address` | Potential owner |
| `_mc` | `address` | MissionControl address (optional) |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if caller owns the wallet |

#### Access

Public view function

## Reward Claiming Functions

### `claimLoot`

Claims Ripe token rewards from the Lootbox contract.

```vyper
@nonreentrant
@external
def claimLoot(
    _user: address,
    _wantsSavingsGreen: bool = False,
) -> (uint256, uint256):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User claiming rewards |
| `_wantsSavingsGreen` | `bool` | Receive rewards as sGreen |

#### Returns

| Type | Description |
|------|-------------|
| `(uint256, uint256)` | (greenTokenRewards, ripeTokenRewards) |

#### Access

Public function with permission checks

#### Example Usage
```python
# Claim loot rewards
green_rewards, ripe_rewards = teller.claimLoot(
    user.address,
    True  # Want sGreen
)
```

### `claimLootForManyUsers`

Batch claims Ripe token rewards for multiple users.

```vyper
@nonreentrant
@external
def claimLootForManyUsers(
    _users: DynArray[address, MAX_CLAIM_USERS],
    _wantsSavingsGreen: bool = False,
) -> (uint256, uint256):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_users` | `DynArray[address, 25]` | Users to claim for |
| `_wantsSavingsGreen` | `bool` | Receive rewards as sGreen |

#### Returns

| Type | Description |
|------|-------------|
| `(uint256, uint256)` | (totalGreenRewards, totalRipeRewards) |

#### Access

Public function with permission checks for each user

#### Example Usage
```python
# Claim for multiple users
users = [user1.address, user2.address, user3.address]
total_green, total_ripe = teller.claimLootForManyUsers(
    users,
    False  # Want Green tokens
)
```

## Ripe Governance Vault Functions

### `adjustLock`

Adjusts lock duration for Ripe tokens in the governance vault.

```vyper
@nonreentrant
@external
def adjustLock(
    _user: address,
    _newUnlockTime: uint256,
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User adjusting lock |
| `_newUnlockTime` | `uint256` | New unlock timestamp |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | New unlock time |

#### Access

Public function with permission checks

#### Example Usage
```python
# Extend lock to 1 year from now
new_unlock_time = teller.adjustLock(
    user.address,
    block.timestamp + 365 * 24 * 60 * 60
)
```

### `releaseLock`

Releases unlocked Ripe tokens from the governance vault.

```vyper
@nonreentrant
@external
def releaseLock(
    _user: address,
    _amount: uint256 = max_value(uint256),
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User releasing lock |
| `_amount` | `uint256` | Amount to release (max for all) |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Amount released |

#### Access

Public function with permission checks

#### Example Usage
```python
# Release all unlocked Ripe
released = teller.releaseLock(
    user.address
)

# Release specific amount
released = teller.releaseLock(
    user.address,
    100_000000000000000000  # 100 RIPE
)
```

## Bond Purchase Functions

### `purchaseRipeBond`

Purchases Ripe bonds from the BondRoom.

```vyper
@nonreentrant
@external
def purchaseRipeBond(
    _bondUser: address,
    _greenAmount: uint256,
    _isPaymentSavingsGreen: bool = False,
    _shouldRefundSavingsGreen: bool = False,
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_bondUser` | `address` | User purchasing bond |
| `_greenAmount` | `uint256` | Green to spend on bond |
| `_isPaymentSavingsGreen` | `bool` | Paying with sGreen |
| `_shouldRefundSavingsGreen` | `bool` | Refund excess as sGreen |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Ripe tokens received from bond |

#### Access

Public function with permission checks

#### Example Usage
```python
# Purchase Ripe bond with Green
ripe_received = teller.purchaseRipeBond(
    user.address,
    1000_000000000000000000,  # 1000 Green
    False,  # Paying with Green
    True    # Refund excess as sGreen
)
```

## Underscore Wallet Utilities

### `setUndyLegoAccess`

Utility function for Underscore smart wallet users to grant permissions.

```vyper
@external
def setUndyLegoAccess(
    _user: address,
    _undyLegoId: uint256,
    _hasAccess: bool,
):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | Smart wallet address |
| `_undyLegoId` | `uint256` | Lego strategy ID |
| `_hasAccess` | `bool` | Grant or revoke access |

#### Access

Only callable by smart wallet owner

#### Example Usage
```python
# Grant Lego access to smart wallet
teller.setUndyLegoAccess(
    smart_wallet.address,
    5,     # Lego ID
    True   # Grant access
)

# Revoke Lego access
teller.setUndyLegoAccess(
    smart_wallet.address,
    5,      # Lego ID
    False   # Revoke access
)
```

## Key Validation Logic

### Deposit Limits

The contract enforces multiple deposit limits:

1. **Per-User Limits**: Maximum deposit per user per asset
2. **Global Limits**: Protocol-wide deposit caps per asset
3. **Vault Limits**: Maximum assets per vault, maximum vaults per user
4. **Minimum Balance**: Ensures positions meet minimum thresholds

### Permission Hierarchy

Access control follows this hierarchy:

1. **Direct User**: Always has full permissions
2. **Ripe Departments**: Trusted protocol contracts bypass most limits
3. **Delegated Users**: Specific operation permissions
4. **Underscore Owners**: Smart wallet ownership verification
5. **General Permissions**: Configurable proxy permissions

### Automatic Vault Selection

When no vault is specified:

```
vaultId = getFirstVaultIdForAsset(asset)
vaultAddr = getAddr(vaultId)
```

This provides seamless UX by automatically routing to appropriate vaults.

## Testing

For comprehensive test examples, see: [`tests/core/test_teller.py`](../../tests/core/test_teller.py)