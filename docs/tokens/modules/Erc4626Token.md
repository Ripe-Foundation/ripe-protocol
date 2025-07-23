# Erc4626Token Technical Documentation

[📄 View Source Code](../../../contracts/tokens/modules/Erc4626Token.vy)

## Overview

Erc4626Token is a tokenized vault module that extends Erc20Token to implement the EIP-4626 standard. It transforms any ERC20 token into a yield-bearing vault token, enabling standardized interactions with DeFi aggregators and yield optimizers.

**Core Functions**:
- **Asset/Share Conversion**: Bidirectional exchange with accurate rate calculations
- **Flexible Operations**: Multiple deposit/withdrawal methods (asset or share-based)
- **Price Tracking**: Current and historical price-per-share for valuation and security
- **EIP-4626 Compliance**: Full standard implementation for protocol composability
- **Attack Protection**: Careful rounding logic prevents precision loss exploits

Built on Vyper's module system, Erc4626Token inherits all Erc20Token features while adding vault logic. It implements reentrancy protection, handles edge cases gracefully, and maintains lastPricePerShare for security. All operations emit standard events for transparency and integration.

## Architecture & Dependencies

Erc4626Token extends Erc20Token as a module with additional vault functionality:

### Module Inheritance
```vyper
uses: token
from contracts.tokens.modules import Erc20Token as token
```

This means Erc4626Token has access to all Erc20Token functionality including:
- Standard ERC20 operations
- Blacklist management
- Permit functionality
- RipeHq integration

### External Interfaces
- **IERC20**: For interacting with the underlying asset
- **IERC4626**: Standard vault interface implementation

### Immutable Configuration
```vyper
ASSET: immutable(address)  # Underlying asset token
```

## Data Structures

The module extends Erc20Token's state with vault-specific additions:

### Additional State Variables
- `lastPricePerShare: uint256` - Cached price per share for security checks

## System Architecture Diagram

```
+------------------------------------------------------------------------+
|                        Erc4626Token Module                            |
+------------------------------------------------------------------------+
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Vault Operations Flow                         |  |
|  |                                                                  |  |
|  |  Deposit Flow:                                                   |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ User chooses entry method:                                  │ |  |
|  |  │                                                             │ |  |
|  |  │ deposit(assets):               mint(shares):               │ |  |
|  |  │ 1. Calculate shares            1. Calculate assets needed  │ |  |
|  |  │ 2. Transfer assets in          2. Transfer assets in       │ |  |
|  |  │ 3. Mint shares to user         3. Mint exact shares        │ |  |
|  |  │ 4. Update lastPricePerShare    4. Update lastPricePerShare │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  |                                                                  |  |
|  |  Withdrawal Flow:                                                |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ User chooses exit method:                                   │ |  |
|  |  │                                                             │ |  |
|  |  │ withdraw(assets):              redeem(shares):             │ |  |
|  |  │ 1. Calculate shares needed     1. Calculate assets to give │ |  |
|  |  │ 2. Burn shares from owner      2. Burn exact shares        │ |  |
|  |  │ 3. Transfer assets out         3. Transfer assets out      │ |  |
|  |  │ 4. Update lastPricePerShare    4. Update lastPricePerShare │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                 Asset/Share Conversion Logic                     |  |
|  |                                                                  |  |
|  |  Price Per Share = Total Assets / Total Shares                   |  |
|  |                                                                  |  |
|  |  Assets to Shares:                                               |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ If first deposit: shares = assets (1:1 ratio)               │ |  |
|  |  │ Else: shares = assets * totalShares / totalAssets           │ |  |
|  |  │                                                             │ |  |
|  |  │ Rounding: Down for deposits, Up for withdrawals             │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  |                                                                  |  |
|  |  Shares to Assets:                                               |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ If no shares exist: assets = shares (1:1 ratio)             │ |  |
|  |  │ Else: assets = shares * totalAssets / totalShares           │ |  |
|  |  │                                                             │ |  |
|  |  │ Rounding: Up for minting, Down for redeeming                │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Security Considerations                       |  |
|  |                                                                  |  |
|  |  First Deposit Attack Protection:                                |  |
|  |  • 1:1 ratio for initial deposit prevents manipulation           |  |
|  |  • lastPricePerShare tracking for monitoring                     |  |
|  |                                                                  |  |
|  |  Rounding Protection:                                             |  |
|  |  • Conservative rounding favors protocol                         |  |
|  |  • Prevents dust attacks and precision loss                      |  |
|  |                                                                  |  |
|  |  Reentrancy Protection:                                           |  |
|  |  • @nonreentrant on deposit() and mint()                         |  |
|  |  • State updates before external calls                           |  |
|  +------------------------------------------------------------------+  |
+------------------------------------------------------------------------+
                    |                                   |
                    ▼                                   ▼
+----------------------------------+  +----------------------------------+
|         Erc20Token Module        |  |        Underlying Asset          |
+----------------------------------+  +----------------------------------+
| • Provides ERC20 functionality   |  | • Any ERC20 token                |
| • Minting/burning of shares      |  | • Held by vault contract         |
| • Transfer/approval logic        |  | • Generates yield (potentially)  |
| • Blacklist and pause features   |  +----------------------------------+
+----------------------------------+
```

## Constructor

### `__init__`

Initializes the vault with an underlying asset.

```vyper
@deploy
def __init__(_asset: address):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_asset` | `address` | The ERC20 token this vault will accept |

#### Validation
- Asset address cannot be empty

#### Note
The Erc4626Token module must be combined with Erc20Token initialization to create a complete vault token.

#### Example Usage
```python
# Deploy a vault for USDC
# This would be in a contract that uses both modules
usdc_vault = deploy_vault_contract(
    asset=usdc.address,
    name="USDC Vault",
    symbol="vUSDC",
    decimals=usdc.decimals()
)
```

## Core Vault Functions

### Deposit Functions

#### `deposit`

Deposit exact amount of assets for shares.

```vyper
@nonreentrant
@external
def deposit(_assets: uint256, _receiver: address = msg.sender) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_assets` | `uint256` | Amount of assets to deposit (max_value for full balance) |
| `_receiver` | `address` | Who receives the minted shares |

#### Returns
- `uint256`: Amount of shares minted

#### Process
1. Calculate shares to mint based on current ratio
2. Transfer assets from depositor
3. Mint shares to receiver
4. Update price per share

**Events Emitted**: `Deposit`, `Transfer`

#### `mint`

Mint exact amount of shares for assets.

```vyper
@nonreentrant
@external
def mint(_shares: uint256, _receiver: address = msg.sender) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_shares` | `uint256` | Exact shares to mint |
| `_receiver` | `address` | Who receives the shares |

#### Returns
- `uint256`: Amount of assets deposited

**Events Emitted**: `Deposit`, `Transfer`

### Withdrawal Functions

#### `withdraw`

Withdraw exact amount of assets by burning shares.

```vyper
@external
def withdraw(_assets: uint256, _receiver: address = msg.sender, _owner: address = msg.sender) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_assets` | `uint256` | Exact assets to withdraw |
| `_receiver` | `address` | Who receives the assets |
| `_owner` | `address` | Whose shares to burn |

#### Returns
- `uint256`: Amount of shares burned

**Events Emitted**: `Withdraw`, `Transfer`

#### `redeem`

Redeem exact amount of shares for assets.

```vyper
@external
def redeem(_shares: uint256, _receiver: address = msg.sender, _owner: address = msg.sender) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_shares` | `uint256` | Shares to redeem (max_value for all) |
| `_receiver` | `address` | Who receives the assets |
| `_owner` | `address` | Whose shares to redeem |

#### Returns
- `uint256`: Amount of assets withdrawn

**Events Emitted**: `Withdraw`, `Transfer`

## Preview Functions

### `previewDeposit`
```vyper
@view
@external
def previewDeposit(_assets: uint256) -> uint256:
```
Returns shares that would be minted for asset deposit.

### `previewMint`
```vyper
@view
@external
def previewMint(_shares: uint256) -> uint256:
```
Returns assets needed to mint exact shares.

### `previewWithdraw`
```vyper
@view
@external
def previewWithdraw(_assets: uint256) -> uint256:
```
Returns shares needed to withdraw exact assets.

### `previewRedeem`
```vyper
@view
@external
def previewRedeem(_shares: uint256) -> uint256:
```
Returns assets that would be withdrawn for shares.

## Conversion Functions

### `convertToShares`
```vyper
@view
@external
def convertToShares(_assets: uint256) -> uint256:
```
Converts asset amount to equivalent shares.

### `convertToAssets`
```vyper
@view
@external
def convertToAssets(_shares: uint256) -> uint256:
```
Converts share amount to equivalent assets.

## Vault State Functions

### `asset`
```vyper
@view
@external
def asset() -> address:
```
Returns the underlying asset address.

### `totalAssets`
```vyper
@view
@external
def totalAssets() -> uint256:
```
Returns total assets held by vault.

### `pricePerShare`
```vyper
@view
@external
def pricePerShare() -> uint256:
```
Returns current price per share scaled by token decimals.

### `getLastUnderlying`
```vyper
@view
@external
def getLastUnderlying(_shares: uint256) -> uint256:
```
Returns asset value using cached price per share.

## Maximum Functions

### `maxDeposit`
```vyper
@view
@external
def maxDeposit(_receiver: address) -> uint256:
```
Always returns `max_value(uint256)` - no deposit limit.

### `maxMint`
```vyper
@view
@external
def maxMint(_receiver: address) -> uint256:
```
Always returns `max_value(uint256)` - no mint limit.

### `maxWithdraw`
```vyper
@view
@external
def maxWithdraw(_owner: address) -> uint256:
```
Returns total vault assets - practical withdrawal limit.

### `maxRedeem`
```vyper
@view
@external
def maxRedeem(_owner: address) -> uint256:
```
Returns owner's share balance.

## Internal Conversion Logic

### Asset to Share Conversion
```vyper
def _amountToShares(
    _amount: uint256,
    _totalShares: uint256,
    _totalBalance: uint256,
    _shouldRoundUp: bool,
) -> uint256:
```

Key Logic:
- First deposit: 1:1 ratio
- Zero balance: Returns 0 (protects against division)
- Normal: `shares = amount * totalShares / totalBalance`
- Rounding: Up for withdrawals, down for deposits

### Share to Asset Conversion
```vyper
def _sharesToAmount(
    _shares: uint256,
    _totalShares: uint256,
    _totalBalance: uint256,
    _shouldRoundUp: bool,
) -> uint256:
```

Key Logic:
- No shares exist: 1:1 ratio
- Normal: `amount = shares * totalBalance / totalShares`
- Rounding: Up for minting, down for redeeming


## Security Considerations

### First Depositor Attack Prevention
- Initial deposits use 1:1 ratio
- Cannot manipulate exchange rate before users join
- lastPricePerShare tracking for monitoring

### Rounding Protection
- Conservative rounding favors vault
- Deposits round shares down
- Withdrawals round shares up
- Prevents accumulation of dust

### Reentrancy Protection
- `@nonreentrant` on deposit/mint
- State updates before external calls
- Follows checks-effects-interactions

### Integration Safety
- Handles max_value inputs gracefully
- Zero amount validation
- Proper allowance handling for operators

## Common Integration Patterns

### Basic Vault Usage
```python
# Deposit assets
usdc.approve(vault.address, amount, sender=user)
shares = vault.deposit(amount, sender=user)

# Withdraw assets
assets = vault.redeem(shares, sender=user)
```

### Deposit Entire Balance
```python
# Use max_value to deposit everything
usdc.approve(vault.address, max_value, sender=user)
shares = vault.deposit(max_value, sender=user)
```

### Third-Party Operations
```python
# Deposit for someone else
vault.deposit(amount, alice.address, sender=bob)

# Withdraw using allowance
vault.redeem(shares, bob.address, alice.address, sender=bob)
```

### Preview Calculations
```python
# Check before depositing
shares_expected = vault.previewDeposit(assets)
print(f"Will receive {shares_expected} shares")

# Check before withdrawing
assets_expected = vault.previewRedeem(shares)
print(f"Will receive {assets_expected} assets")
```

## Yield Strategies

While Erc4626Token provides the vault interface, yield generation would be implemented by contracts inheriting this module:

```python
# Example: Lending vault pseudocode
class LendingVault(Erc4626Token):
    def _earnYield():
        # Deposit idle assets to lending protocol
        assets = totalAssets()
        lending_protocol.deposit(assets)
    
    def totalAssets():
        # Include assets in lending protocol
        return balance + lending_deposits + accrued_interest
```

## Testing

For comprehensive test examples, see: [`tests/tokens/modules/test_erc4626_token.py`](../../tests/tokens/modules/test_erc4626_token.py)