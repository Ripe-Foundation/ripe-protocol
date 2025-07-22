# SavingsGreen Technical Documentation

[📄 View Source Code](../../contracts/tokens/SavingsGreen.vy)

## Overview

SavingsGreen (sGREEN) is an ERC4626 yield-bearing vault that automatically compounds returns on deposited GREEN stablecoins. By pooling GREEN tokens and deploying them across protocol yield strategies, sGREEN shares appreciate over time without user intervention.

**Yield Generation**:
- **Automated Compounding**: Share value increases as vault generates returns from protocol activities
- **ERC4626 Standard**: Full compatibility with DeFi infrastructure for seamless integrations
- **Flexible Access**: Deposit and withdraw GREEN anytime with proportional share calculations
- **Transparent Accounting**: Real-time price-per-share tracking for accurate yield reporting

The vault combines ERC20 and ERC4626 modules to provide a secure, efficient savings mechanism. Features include permit functionality for gasless operations, comprehensive security controls, and integration with protocol-wide governance systems.

## Architecture & Modules

SavingsGreen is built using a modular architecture that combines ERC20 token functionality with ERC4626 vault capabilities:

### Erc20Token Module

- **Location**: `contracts/tokens/modules/Erc20Token.vy`
- **Purpose**: Provides complete ERC20 token functionality for sGREEN shares
- **Key Features**:
  - Standard ERC20 operations (transfer, approve, allowance)
  - EIP-2612 permit functionality for gasless approvals
  - Blacklist system for compliance
  - Pause mechanism for emergency stops
  - Time-locked governance transitions
  - Secure minting and burning capabilities

### Erc4626Token Module

- **Location**: `contracts/tokens/modules/Erc4626Token.vy`
- **Purpose**: Provides complete ERC4626 vault functionality
- **Key Features**:
  - Standardized deposit/withdraw interface
  - Mint/redeem share operations
  - Share-to-asset conversion calculations
  - Yield tracking through price-per-share
  - Nonreentrant deposit/withdrawal protection
  - Maximum limits and preview functions

### Module Initialization

```vyper
exports: token.__interface__
exports: erc4626.__interface__
initializes: token
initializes: erc4626[token := token]
```

## System Architecture Diagram

```
+------------------------------------------------------------------------+
|                       SavingsGreen Contract                           |
+------------------------------------------------------------------------+
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                     Erc20Token Module                            |  |
|  |                                                                  |  |
|  |  +----------------+ +----------------+ +----------------+       |  |
|  |  | Core ERC20     | | Advanced       | | Security       |       |  |
|  |  | Functions      | | Features       | | Features       |       |  |
|  |  |                | |                | |                |       |  |
|  |  | * transfer     | | * permit       | | * blacklist    |       |  |
|  |  | * transferFrom | | * EIP-712      | | * pause        |       |  |
|  |  | * approve      | | * nonces       | | * timelock     |       |  |
|  |  | * allowance    | | * domain sep   | | * governance   |       |  |
|  |  | * balanceOf    | | * signatures   | | * validation   |       |  |
|  |  | * totalSupply  | |                | |                |       |  |
|  |  +----------------+ +----------------+ +----------------+       |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Erc4626Token Module                           |  |
|  |                                                                  |  |
|  |  +----------------+ +----------------+ +----------------+       |  |
|  |  | Deposit        | | Withdrawal     | | Share          |       |  |
|  |  | Functions      | | Functions      | | Conversion     |       |  |
|  |  |                | |                | |                |       |  |
|  |  | * deposit      | | * withdraw     | | * convertTo-   |       |  |
|  |  | * mint         | | * redeem       | |   Shares       |       |  |
|  |  | * preview-     | | * preview-     | | * convertTo-   |       |  |
|  |  |   Deposit      | |   Withdraw     | |   Assets       |       |  |
|  |  | * maxDeposit   | | * maxWithdraw  | | * pricePerShare|       |  |
|  |  +----------------+ +----------------+ +----------------+       |  |
|  |                                                                  |  |
|  |  +----------------+ +----------------+ +----------------+       |  |
|  |  | Asset Info     | | Yield Tracking | | Security       |       |  |
|  |  |                | |                | |                |       |  |
|  |  | * asset        | | * totalAssets  | | * nonreentrant |       |  |
|  |  | * totalAssets  | | * lastPrice-   | | * access       |       |  |
|  |  | * underlying   | |   PerShare     | |   control      |       |  |
|  |  | * balance      | | * getLastUnder-| | * validation   |       |  |
|  |  |                | |   lying        | |                |       |  |
|  |  +----------------+ +----------------+ +----------------+       |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                  SavingsGreen Specific Layer                     |  |
|  |                                                                  |  |
|  |  Asset: GREEN Token (Green USD Stablecoin)                       |  |
|  |  Shares: sGREEN Token (Savings Green USD)                        |  |
|  |  Name: \"Savings Green USD\"                                        |  |
|  |  Symbol: \"sGREEN\"                                                  |  |
|  |  Decimals: Matches GREEN decimals (18)                           |  |
|  +------------------------------------------------------------------+  |
+------------------------------------------------------------------------+
                                    |
        +---------------------------+---------------------------+
        |                           |                           |
        v                           v                           v
+------------------+    +-------------------+    +------------------+
| Green Token      |    | Yield Generation  |    | Users &          |
| (Underlying)     |    | Sources           |    | External         |
|                  |    |                   |    | Interfaces       |
| * GREEN balance  |    | * Protocol fees   |    |                  |
| * Vault deposits |    | * Trading fees    |    | * ERC20 ops      |
| * Yield accrual  |    | * Lending yield   |    | * ERC4626 ops    |
| * Asset backing  |    | * Staking rewards |    | * Deposits       |
+------------------+    +-------------------+    | * Withdrawals    |
                                                  | * Share trading  |
                                                  +------------------+
```

## Data Structures

### PendingHq Struct (Inherited)

Tracks pending RipeHq address changes:

```vyper
struct PendingHq:
    newHq: address                    # New RipeHq address
    initiatedBlock: uint256           # Block when change was initiated
    confirmBlock: uint256             # Block when change can be confirmed
```

## State Variables

### Token Information (Immutable)

- `TOKEN_NAME: String[64]` - "Savings Green USD"
- `TOKEN_SYMBOL: String[32]` - "sGREEN"
- `TOKEN_DECIMALS: uint8` - Matches underlying Green token decimals (18)
- `VERSION: String[8]` - "v1.0.0"

### ERC4626 Vault State

- `ASSET: immutable(address)` - Green token contract address (underlying asset)
- `lastPricePerShare: uint256` - Last recorded price per share for yield tracking

### Core ERC20 State (Inherited)

- `balanceOf: HashMap[address, uint256]` - sGREEN share balances
- `allowance: HashMap[address, HashMap[address, uint256]]` - Spending approvals
- `totalSupply: uint256` - Total sGREEN share supply

### Security and Governance (Inherited)

- `ripeHq: address` - Current RipeHq contract address
- `blacklisted: HashMap[address, bool]` - Blacklisted addresses
- `isPaused: bool` - Token pause state
- `pendingHq: PendingHq` - Pending RipeHq change data
- `hqChangeTimeLock: uint256` - Time lock for RipeHq changes

### EIP-712 Support (Inherited)

- `nonces: HashMap[address, uint256]` - Permit nonces for each address
- Domain separator components for signature validation

### Constants and Immutable (Inherited)

- `MIN_HQ_TIME_LOCK: uint256` - Minimum time lock for RipeHq changes
- `MAX_HQ_TIME_LOCK: uint256` - Maximum time lock for RipeHq changes
- Various EIP-712 and cryptographic constants

## Constructor

### `__init__`

Initializes the SavingsGreen vault with comprehensive configuration parameters.

```vyper
@deploy
def __init__(
    _asset: address,
    _ripeHq: address,
    _initialGov: address,
    _minHqTimeLock: uint256,
    _maxHqTimeLock: uint256,
    _initialSupply: uint256,
    _initialSupplyRecipient: address,
):
```

#### Parameters

| Name                      | Type      | Description                                            |
| ------------------------- | --------- | ------------------------------------------------------ |
| `_asset`                  | `address` | Green token contract address (underlying asset)        |
| `_ripeHq`                 | `address` | RipeHq contract address (empty for initial deployment) |
| `_initialGov`             | `address` | Initial governance address (for setup phase)           |
| `_minHqTimeLock`          | `uint256` | Minimum time lock for RipeHq changes                   |
| `_maxHqTimeLock`          | `uint256` | Maximum time lock for RipeHq changes                   |
| `_initialSupply`          | `uint256` | Initial sGREEN supply to mint                          |
| `_initialSupplyRecipient` | `address` | Recipient of initial supply                            |

#### Returns

_Constructor does not return any values_

#### Access

Called only during deployment

#### Example Usage

```python
# Deploy SavingsGreen vault
savings_green = boa.load(
    "contracts/tokens/SavingsGreen.vy",
    green_token.address,      # Underlying GREEN asset
    empty(address),           # No RipeHq initially
    deployer.address,         # Initial governance
    100,                      # Min timelock: 100 blocks
    1000,                     # Max timelock: 1000 blocks
    0,                        # No initial supply
    empty(address)            # No initial recipient
)
```

**Example Output**: Vault deployed with name "Savings Green USD", symbol "sGREEN", using GREEN as underlying asset

## Core ERC20 Functions (Inherited)

### `name`

Returns the token name.

```vyper
@view
@external
def name() -> String[64]:
```

#### Returns

| Type         | Description         |
| ------------ | ------------------- |
| `String[64]` | "Savings Green USD" |

#### Access

Public view function

### `symbol`

Returns the token symbol.

```vyper
@view
@external
def symbol() -> String[32]:
```

#### Returns

| Type         | Description |
| ------------ | ----------- |
| `String[32]` | "sGREEN"    |

#### Access

Public view function

### `decimals`

Returns the number of decimal places (matches underlying asset).

```vyper
@view
@external
def decimals() -> uint8:
```

#### Returns

| Type    | Description                 |
| ------- | --------------------------- |
| `uint8` | 18 decimals (matches GREEN) |

#### Access

Public view function

### `totalSupply`

Returns the total sGREEN share supply.

```vyper
@view
@external
def totalSupply() -> uint256:
```

#### Returns

| Type      | Description                   |
| --------- | ----------------------------- |
| `uint256` | Total supply of sGREEN shares |

#### Access

Public view function

### `balanceOf`

Returns the sGREEN share balance of an account.

```vyper
@view
@external
def balanceOf(_account: address) -> uint256:
```

#### Parameters

| Name       | Type      | Description      |
| ---------- | --------- | ---------------- |
| `_account` | `address` | Account to check |

#### Returns

| Type      | Description                         |
| --------- | ----------------------------------- |
| `uint256` | sGREEN share balance of the account |

#### Access

Public view function

## ERC4626 Vault Functions

### `asset`

Returns the underlying asset contract address.

```vyper
@view
@external
def asset() -> address:
```

#### Returns

| Type      | Description                  |
| --------- | ---------------------------- |
| `address` | Green token contract address |

#### Access

Public view function

### `totalAssets`

Returns the total amount of underlying assets held by the vault.

```vyper
@view
@external
def totalAssets() -> uint256:
```

#### Returns

| Type      | Description                          |
| --------- | ------------------------------------ |
| `uint256` | Total GREEN tokens held in the vault |

#### Access

Public view function

#### Example Usage

```python
# Check total assets in vault
total_green = savings_green.totalAssets()
print(f"Vault holds {total_green / 1e18} GREEN tokens")
```

## Deposit Functions

### `maxDeposit`

Returns the maximum amount of assets that can be deposited.

```vyper
@view
@external
def maxDeposit(_receiver: address) -> uint256:
```

#### Parameters

| Name        | Type      | Description                       |
| ----------- | --------- | --------------------------------- |
| `_receiver` | `address` | Address that would receive shares |

#### Returns

| Type      | Description                        |
| --------- | ---------------------------------- |
| `uint256` | Maximum deposit amount (unlimited) |

#### Access

Public view function

### `previewDeposit`

Preview the number of shares that would be minted for a given asset amount.

```vyper
@view
@external
def previewDeposit(_assets: uint256) -> uint256:
```

#### Parameters

| Name      | Type      | Description                       |
| --------- | --------- | --------------------------------- |
| `_assets` | `uint256` | Amount of GREEN tokens to deposit |

#### Returns

| Type      | Description                                  |
| --------- | -------------------------------------------- |
| `uint256` | Number of sGREEN shares that would be minted |

#### Access

Public view function

#### Example Usage

```python
# Preview deposit of 1000 GREEN
shares_preview = savings_green.previewDeposit(1000_000000000000000000)
print(f"Depositing 1000 GREEN would mint {shares_preview / 1e18} sGREEN")
```

### `deposit`

Deposits GREEN tokens and receives sGREEN shares.

```vyper
@nonreentrant
@external
def deposit(_assets: uint256, _receiver: address = msg.sender) -> uint256:
```

#### Parameters

| Name        | Type      | Description                                           |
| ----------- | --------- | ----------------------------------------------------- |
| `_assets`   | `uint256` | Amount of GREEN tokens to deposit                     |
| `_receiver` | `address` | Address to receive sGREEN shares (defaults to caller) |

#### Returns

| Type      | Description                    |
| --------- | ------------------------------ |
| `uint256` | Number of sGREEN shares minted |

#### Access

Public function (requires GREEN token approval)

#### Events Emitted

- `Deposit` - Contains sender, owner, assets, and shares
- `Transfer` - sGREEN share mint event

#### Example Usage

```python
# First approve GREEN tokens
green_token.approve(savings_green.address, 1000_000000000000000000, sender=user)

# Deposit GREEN tokens
shares_received = savings_green.deposit(
    1000_000000000000000000,  # 1000 GREEN
    user.address,             # Receiver
    sender=user
)
print(f"Received {shares_received / 1e18} sGREEN shares")
```

### `maxMint`

Returns the maximum number of shares that can be minted.

```vyper
@view
@external
def maxMint(_receiver: address) -> uint256:
```

#### Parameters

| Name        | Type      | Description                       |
| ----------- | --------- | --------------------------------- |
| `_receiver` | `address` | Address that would receive shares |

#### Returns

| Type      | Description                                   |
| --------- | --------------------------------------------- |
| `uint256` | Maximum shares that can be minted (unlimited) |

#### Access

Public view function

### `previewMint`

Preview the amount of assets needed to mint a given number of shares.

```vyper
@view
@external
def previewMint(_shares: uint256) -> uint256:
```

#### Parameters

| Name      | Type      | Description                     |
| --------- | --------- | ------------------------------- |
| `_shares` | `uint256` | Number of sGREEN shares to mint |

#### Returns

| Type      | Description                     |
| --------- | ------------------------------- |
| `uint256` | Amount of GREEN tokens required |

#### Access

Public view function

### `mint`

Mints exact number of sGREEN shares by depositing required GREEN tokens.

```vyper
@nonreentrant
@external
def mint(_shares: uint256, _receiver: address = msg.sender) -> uint256:
```

#### Parameters

| Name        | Type      | Description                                    |
| ----------- | --------- | ---------------------------------------------- |
| `_shares`   | `uint256` | Number of sGREEN shares to mint                |
| `_receiver` | `address` | Address to receive shares (defaults to caller) |

#### Returns

| Type      | Description                      |
| --------- | -------------------------------- |
| `uint256` | Amount of GREEN tokens deposited |

#### Access

Public function (requires GREEN token approval)

#### Events Emitted

- `Deposit` - Contains sender, owner, assets, and shares
- `Transfer` - sGREEN share mint event

#### Example Usage

```python
# Mint exactly 500 sGREEN shares
assets_required = savings_green.mint(
    500_000000000000000000,  # 500 sGREEN shares
    user.address,            # Receiver
    sender=user
)
```

## Withdrawal Functions

### `maxWithdraw`

Returns the maximum amount of assets that can be withdrawn by an owner.

```vyper
@view
@external
def maxWithdraw(_owner: address) -> uint256:
```

#### Parameters

| Name     | Type      | Description         |
| -------- | --------- | ------------------- |
| `_owner` | `address` | Share owner address |

#### Returns

| Type      | Description                                |
| --------- | ------------------------------------------ |
| `uint256` | Maximum GREEN tokens that can be withdrawn |

#### Access

Public view function

### `previewWithdraw`

Preview the number of shares needed to withdraw a given amount of assets.

```vyper
@view
@external
def previewWithdraw(_assets: uint256) -> uint256:
```

#### Parameters

| Name      | Type      | Description                        |
| --------- | --------- | ---------------------------------- |
| `_assets` | `uint256` | Amount of GREEN tokens to withdraw |

#### Returns

| Type      | Description                      |
| --------- | -------------------------------- |
| `uint256` | Number of sGREEN shares required |

#### Access

Public view function

### `withdraw`

Withdraws exact amount of GREEN tokens by burning required sGREEN shares.

```vyper
@external
def withdraw(_assets: uint256, _receiver: address = msg.sender, _owner: address = msg.sender) -> uint256:
```

#### Parameters

| Name        | Type      | Description                        |
| ----------- | --------- | ---------------------------------- |
| `_assets`   | `uint256` | Amount of GREEN tokens to withdraw |
| `_receiver` | `address` | Address to receive GREEN tokens    |
| `_owner`    | `address` | Share owner (defaults to caller)   |

#### Returns

| Type      | Description                    |
| --------- | ------------------------------ |
| `uint256` | Number of sGREEN shares burned |

#### Access

Public function (requires sufficient shares or allowance)

#### Events Emitted

- `Withdraw` - Contains sender, receiver, owner, assets, and shares
- `Transfer` - sGREEN share burn event

#### Example Usage

```python
# Withdraw exactly 500 GREEN tokens
shares_burned = savings_green.withdraw(
    500_000000000000000000,  # 500 GREEN
    user.address,            # Receiver
    user.address,            # Owner
    sender=user
)
```

### `maxRedeem`

Returns the maximum number of shares that can be redeemed by an owner.

```vyper
@view
@external
def maxRedeem(_owner: address) -> uint256:
```

#### Parameters

| Name     | Type      | Description         |
| -------- | --------- | ------------------- |
| `_owner` | `address` | Share owner address |

#### Returns

| Type      | Description                                |
| --------- | ------------------------------------------ |
| `uint256` | Maximum sGREEN shares that can be redeemed |

#### Access

Public view function

### `previewRedeem`

Preview the amount of assets received for redeeming a given number of shares.

```vyper
@view
@external
def previewRedeem(_shares: uint256) -> uint256:
```

#### Parameters

| Name      | Type      | Description                       |
| --------- | --------- | --------------------------------- |
| `_shares` | `uint256` | Number of sGREEN shares to redeem |

#### Returns

| Type      | Description                                   |
| --------- | --------------------------------------------- |
| `uint256` | Amount of GREEN tokens that would be received |

#### Access

Public view function

### `redeem`

Redeems sGREEN shares for GREEN tokens.

```vyper
@external
def redeem(_shares: uint256, _receiver: address = msg.sender, _owner: address = msg.sender) -> uint256:
```

#### Parameters

| Name        | Type      | Description                       |
| ----------- | --------- | --------------------------------- |
| `_shares`   | `uint256` | Number of sGREEN shares to redeem |
| `_receiver` | `address` | Address to receive GREEN tokens   |
| `_owner`    | `address` | Share owner (defaults to caller)  |

#### Returns

| Type      | Description                     |
| --------- | ------------------------------- |
| `uint256` | Amount of GREEN tokens received |

#### Access

Public function (requires sufficient shares or allowance)

#### Events Emitted

- `Withdraw` - Contains sender, receiver, owner, assets, and shares
- `Transfer` - sGREEN share burn event

#### Example Usage

```python
# Redeem all sGREEN shares
user_shares = savings_green.balanceOf(user.address)
assets_received = savings_green.redeem(
    user_shares,      # All shares
    user.address,     # Receiver
    user.address,     # Owner
    sender=user
)
```

## Share Conversion Functions

### `convertToShares`

Converts an asset amount to the equivalent number of shares.

```vyper
@view
@external
def convertToShares(_assets: uint256) -> uint256:
```

#### Parameters

| Name      | Type      | Description            |
| --------- | --------- | ---------------------- |
| `_assets` | `uint256` | Amount of GREEN tokens |

#### Returns

| Type      | Description                        |
| --------- | ---------------------------------- |
| `uint256` | Equivalent number of sGREEN shares |

#### Access

Public view function

### `convertToAssets`

Converts a share amount to the equivalent number of underlying assets.

```vyper
@view
@external
def convertToAssets(_shares: uint256) -> uint256:
```

#### Parameters

| Name      | Type      | Description             |
| --------- | --------- | ----------------------- |
| `_shares` | `uint256` | Number of sGREEN shares |

#### Returns

| Type      | Description                       |
| --------- | --------------------------------- |
| `uint256` | Equivalent amount of GREEN tokens |

#### Access

Public view function

#### Example Usage

```python
# Convert 1000 GREEN to shares
shares_equivalent = savings_green.convertToShares(1000_000000000000000000)

# Convert 500 sGREEN to assets
assets_equivalent = savings_green.convertToAssets(500_000000000000000000)
```

## Yield Tracking Functions

### `pricePerShare`

Returns the current price per share (how much GREEN each sGREEN is worth).

```vyper
@view
@external
def pricePerShare() -> uint256:
```

#### Returns

| Type      | Description                                            |
| --------- | ------------------------------------------------------ |
| `uint256` | Current GREEN tokens per sGREEN share (scaled by 1e18) |

#### Access

Public view function

#### Example Usage

```python
# Check current yield
price = savings_green.pricePerShare()
print(f"1 sGREEN = {price / 1e18} GREEN")

# Calculate yield if initial price was 1.0
if price > 1e18:
    yield_percent = ((price - 1e18) / 1e18) * 100
    print(f"Yield earned: {yield_percent:.2f}%")
```

### `lastPricePerShare`

Returns the last recorded price per share.

```vyper
@view
@external
def lastPricePerShare() -> uint256:
```

#### Returns

| Type      | Description                                 |
| --------- | ------------------------------------------- |
| `uint256` | Last recorded GREEN tokens per sGREEN share |

#### Access

Public view function

### `getLastUnderlying`

Returns the underlying asset value of shares based on last recorded price.

```vyper
@view
@external
def getLastUnderlying(_shares: uint256) -> uint256:
```

#### Parameters

| Name      | Type      | Description             |
| --------- | --------- | ----------------------- |
| `_shares` | `uint256` | Number of sGREEN shares |

#### Returns

| Type      | Description                              |
| --------- | ---------------------------------------- |
| `uint256` | GREEN token value at last recorded price |

#### Access

Public view function

## Transfer Functions (Inherited)

SavingsGreen inherits all standard ERC20 transfer functionality for trading sGREEN shares:

### `transfer`

Transfers sGREEN shares from caller to recipient.

```vyper
@external
def transfer(_recipient: address, _amount: uint256) -> bool:
```

### `transferFrom`

Transfers sGREEN shares using allowance.

```vyper
@external
def transferFrom(_sender: address, _recipient: address, _amount: uint256) -> bool:
```

### `approve`

Sets spending allowance for sGREEN shares.

```vyper
@external
def approve(_spender: address, _amount: uint256) -> bool:
```

### `allowance`

Returns the spending allowance for sGREEN shares.

```vyper
@view
@external
def allowance(_owner: address, _spender: address) -> uint256:
```

## Governance Functions (Inherited)

SavingsGreen inherits all RipeHq management and governance functions from the ERC20 base module:

- `ripeHq()` - Current RipeHq address
- `hasPendingHqChange()` - Pending governance changes
- `initiateHqChange()` - Start governance transition
- `confirmHqChange()` - Complete governance transition
- `cancelHqChange()` - Cancel pending transition
- `setHqChangeTimeLock()` - Update time lock settings
- `pause()` - Emergency pause functionality
- `setBlacklist()` - Compliance controls
- `finishTokenSetup()` - Initial deployment setup

## Security Features (Inherited)

SavingsGreen inherits comprehensive security features:

- **Blacklist System**: Compliance controls for restricted addresses
- **Pause Mechanism**: Emergency stop for all operations
- **Time-locked Governance**: Secure transitions with proper delays
- **Nonreentrant Deposits/Withdrawals**: Protection against reentrancy attacks
- **Access Controls**: RipeHq-based permission system

## Testing

For comprehensive test examples, see: [`tests/tokens/test_erc4626.py`](../../tests/tokens/test_erc4626.py)
