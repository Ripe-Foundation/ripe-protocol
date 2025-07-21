# Teller Technical Documentation

## Overview

Teller serves as the primary user interface and entry point for the Ripe Protocol ecosystem. Think of it as a comprehensive banking teller that handles all user-facing operations including deposits, withdrawals, borrowing, repayment, liquidations, and advanced DeFi operations like auction participation and stability pool interactions. It orchestrates complex multi-contract operations while providing user-friendly interfaces and robust permission management.

At its core, Teller manages five fundamental responsibilities:

**1. Deposit & Withdrawal Management**: Handles all user deposits into vaults with configurable limits, asset restrictions, and permission controls. Supports both individual and batch operations, manages vault selection automatically, and includes sophisticated validation for user limits, global limits, and minimum balance requirements.

**2. Credit Operations**: Facilitates borrowing against collateral and debt repayment with support for different Green token types (Green vs Savings Green). Integrates with CreditEngine for all credit calculations while providing user-friendly interfaces for complex operations.

**3. Liquidation & Auction Interface**: Provides user access to liquidation and auction systems, enabling participation in protocol stability mechanisms. Users can liquidate unhealthy positions, purchase discounted collateral from auctions, and participate in automated liquidation systems.

**4. Advanced DeFi Operations**: Supports sophisticated operations like stability pool interactions, collateral redemption, reward claiming, and Ripe bond purchases. Each operation includes appropriate permission checks and delegated access controls.

**5. Permission & Delegation Management**: Implements comprehensive delegation systems allowing users to authorize others to perform actions on their behalf. Supports both general permissions and operation-specific delegations with integration into Underscore wallet systems.

For technical readers, Teller implements advanced DeFi UX patterns including automatic vault selection based on asset compatibility, batch operations for gas efficiency, comprehensive event logging for transparency, flexible payment handling (Green vs sGreen), and sophisticated permission systems supporting both EOA and smart wallet interactions. The contract ensures security while maximizing user experience through thoughtful abstraction layers.

## Architecture & Modules

Teller is built using a modular architecture with the following components:

### Addys Module
- **Location**: `contracts/modules/Addys.vy`
- **Purpose**: Provides protocol-wide address resolution
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