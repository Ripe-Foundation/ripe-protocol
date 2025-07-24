# RebaseErc20 Vault Technical Documentation

[📄 View Source Code](../../contracts/vaults/RebaseErc20.vy)

## Overview

RebaseErc20 is a yield-optimized vault designed for rebase tokens and yield-generating assets like stETH, rETH, and aTokens. It automatically captures rebases and compounds yield through share-based accounting, providing depositors with passive growth without active management.

**Core Functions**:
- **Share-Based Accounting**: Converts deposits to shares representing proportional vault ownership
- **Automatic Compounding**: Captures rebases and yield without user intervention
- **Fair Distribution**: Maintains accurate ownership percentages as vault value grows

Built on the SharesVault module, RebaseErc20 implements sophisticated yield capture mechanics. Share values appreciate as underlying assets rebase or generate rewards, donation attack protection ensures vault security, and seamless protocol integration enables use as collateral while earning yield.

## Architecture & Dependencies

RebaseErc20 is built using a modular architecture with delegation to yield-focused modules:

### Core Module Dependencies
- **SharesVault**: Provides yield-bearing vault functionality with share-based accounting
- **VaultData**: Manages user share balances, asset registration, and vault state
- **[Addys](../modules/Addys.md)**: Handles protocol address resolution and permission management

### Module Initialization
```vyper
exports: addys.__interface__
exports: vaultData.__interface__
exports: sharesVault.__interface__

initializes: addys
initializes: vaultData[addys := addys]
initializes: sharesVault[vaultData := vaultData]
```

## System Architecture Diagram

```
+------------------------------------------------------------------------+
|                        RebaseErc20 Vault                              |
+------------------------------------------------------------------------+
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Share-Based Operations                        |  |
|  |                                                                  |  |
|  |  depositTokensInVault():                                         |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ 1. Access Control: Only Teller allowed                     │ |  |
|  |  │ 2. Delegate to SharesVault._depositTokensInVault()          │ |  |
|  |  │ 3. Share Calculation:                                       │ |  |
|  |  │    shares = (amount * totalShares) / totalAssetBalance      │ |  |
|  |  │ 4. Store shares (not amounts) in user balance               │ |  |
|  |  │ 5. Emit RebaseErc20VaultDeposit with amount and shares      │ |  |
|  |  │ 6. Return deposit amount                                    │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  |                                                                  |  |
|  |  withdrawTokensFromVault():                                      |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ 1. Access Control: Teller, AuctionHouse, CreditEngine      │ |  |
|  |  │ 2. Delegate to SharesVault._withdrawTokensFromVault()       │ |  |
|  |  │ 3. Share-to-Asset Conversion:                               │ |  |
|  |  │    amount = (shares * totalAssetBalance) / totalShares      │ |  |
|  |  │ 4. Burn user shares and transfer assets                     │ |  |
|  |  │ 5. Emit RebaseErc20VaultWithdrawal with shares burned       │ |  |
|  |  │ 6. Return withdrawal amount and depletion status            │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  |                                                                  |  |
|  |  transferBalanceWithinVault():                                   |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ 1. Access Control: AuctionHouse, CreditEngine              │ |  |
|  |  │ 2. Delegate to SharesVault._transferBalanceWithinVault()    │ |  |
|  |  │ 3. Transfer shares between users (not asset amounts)        │ |  |
|  |  │ 4. Emit RebaseErc20VaultTransfer with shares transferred    │ |  |
|  |  │ 5. Return transfer amount and depletion status              │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Yield Accumulation Mechanics                 |  |
|  |                                                                  |  |
|  |  Share Price Appreciation:                                       |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ Initial State:                                              │ |  |
|  |  │ • User deposits 1000 tokens                                 │ |  |
|  |  │ • Vault has 1000 total tokens, 1000 total shares           │ |  |
|  |  │ • Share price = 1000 / 1000 = 1.0 token per share          │ |  |
|  |  │                                                             │ |  |
|  |  │ After Rebase/Yield (vault now has 1100 tokens):            │ |  |
|  |  │ • Total tokens = 1100, total shares = 1000 (unchanged)     │ |  |
|  |  │ • Share price = 1100 / 1000 = 1.1 tokens per share        │ |  |
|  |  │ • User's 1000 shares now worth 1100 tokens (10% gain)      │ |  |
|  |  │                                                             │ |  |
|  |  │ New User Deposits 100 tokens:                               │ |  |
|  |  │ • New shares = (100 * 1000) / 1100 = 90.9 shares           │ |  |
|  |  │ • Total tokens = 1200, total shares = 1090.9               │ |  |
|  |  │ • Share price maintained at ~1.1 tokens per share          │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Integration Support                           |  |
|  |                                                                  |  |
|  |  getVaultDataOnDeposit():                                        |  |
|  |  • Delegates to SharesVault for Teller integration              |  |
|  |  • Returns share-based vault data with yield considerations     |  |
|  |                                                                  |  |
|  |  getUserLootBoxShare():                                          |  |
|  |  • Delegates to SharesVault for reward calculations             |  |
|  |  • Uses share amounts for proportional reward distribution      |  |
|  |                                                                  |  |
|  |  getUserAssetAndAmountAtIndex():                                 |  |
|  |  • Delegates to SharesVault for CreditEngine integration        |  |
|  |  • Converts shares to current asset amounts for collateral      |  |
|  |                                                                  |  |
|  |  getTotalAmountForUser():                                        |  |
|  |  • Returns current asset value of user's shares                 |  |
|  |  • Amount increases as vault accumulates yield                   |  |
|  +------------------------------------------------------------------+  |
+------------------------------------------------------------------------+
                                    |
                                    | Delegates all core functionality
                                    v
+------------------------------------------------------------------------+
|                        SharesVault Module                             |
+------------------------------------------------------------------------+
|                                                                        |
| • Share-based accounting with automatic yield capture                 |
| • Donation attack prevention through decimal offset                   |
| • Precise share-to-asset conversion calculations                      |
| • Support for rebasing tokens and yield-generating assets             |
| • Integration with VaultData for share balance storage                |
+------------------------------------------------------------------------+
```

## Constructor

### `__init__`

Initializes RebaseErc20 vault with protocol address configuration.

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
3. **SharesVault Setup**: Initializes share-based vault functionality

#### Example Usage
```python
# Deploy rebase ERC20 vault
rebase_erc20_vault = boa.load(
    "contracts/vaults/RebaseErc20.vy",
    ripe_hq.address
)
```

## Core Functions

### `depositTokensInVault`

Handles deposits of rebase tokens with share-based accounting for yield capture.

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
| `_asset` | `address` | Rebase/yield-generating token to deposit |
| `_amount` | `uint256` | Amount of tokens to deposit |
| `_a` | `addys.Addys` | Protocol addresses struct (unused) |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Actual amount deposited |

#### Access

Only callable by Teller

#### Process Flow
1. **Access Validation**: Ensures caller is Teller contract
2. **SharesVault Delegation**: Calls `sharesVault._depositTokensInVault()` for core functionality
3. **Share Calculation**: Converts deposited amount to shares based on current share price:
   ```
   shares = (depositAmount * totalShares) / totalAssetBalance
   ```
4. **Balance Storage**: Stores shares (not amounts) in VaultData user balances
5. **Event Emission**: Logs deposit with user, asset, amount, and shares minted
6. **Return**: Returns actual deposit amount

#### Events Emitted

- `RebaseErc20VaultDeposit` - Contains user, asset, amount deposited, and shares minted

#### Share Price Dynamics
- **First Deposit**: Creates initial 1:1 share-to-asset ratio
- **Subsequent Deposits**: Share price reflects accumulated yield/rebases
- **Yield Accumulation**: As vault's asset balance grows from rebases, share price increases
- **Fair Entry**: New depositors pay current share price, ensuring fair distribution

#### Example Usage
```python
# Deposit stETH (a rebase token) into vault through Teller
deposit_amount = rebase_erc20_vault.depositTokensInVault(
    user.address,
    steth_token.address,
    1_000000000000000000,  # 1 stETH
    empty(addys.Addys),
    sender=teller.address
)

# User receives shares representing proportional vault ownership
# Share amount depends on current share price (influenced by accumulated yield)
```

### `withdrawTokensFromVault`

Handles withdrawals from yield-bearing vault with share burning and asset conversion.

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
| `_asset` | `address` | Rebase token to withdraw |
| `_amount` | `uint256` | Amount of tokens to withdraw |
| `_recipient` | `address` | Address to receive withdrawn tokens |
| `_a` | `addys.Addys` | Protocol addresses struct (unused) |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Actual amount withdrawn (may include accumulated yield) |
| `bool` | True if user's position is now depleted |

#### Access

Only callable by Teller, AuctionHouse, or CreditEngine

#### Process Flow
1. **Access Validation**: Ensures caller is authorized contract
2. **SharesVault Delegation**: Calls `sharesVault._withdrawTokensFromVault()` for core functionality
3. **Share Calculation**: Determines shares needed for requested amount:
   ```
   sharesToBurn = (requestedAmount * totalShares) / totalAssetBalance
   ```
4. **Share Burning**: Reduces user's share balance in VaultData
5. **Asset Transfer**: Transfers calculated amount (may be more than originally deposited due to yield)
6. **Event Emission**: Logs withdrawal with shares burned and depletion status
7. **Return**: Returns actual withdrawal amount and depletion status

#### Events Emitted

- `RebaseErc20VaultWithdrawal` - Contains user, asset, amount, depletion status, and shares burned

#### Yield Realization
- **More Than Deposited**: Users may receive more tokens than deposited due to accumulated yield/rebases
- **Proportional Share**: Withdrawal amount reflects user's proportional share of current vault assets
- **Automatic Compounding**: No manual action required to realize yield gains

#### Example Usage
```python
# User withdraws stETH after yield accumulation
withdrawal_amount, is_depleted = rebase_erc20_vault.withdrawTokensFromVault(
    user.address,
    steth_token.address,
    500_000000000000000,  # Request 0.5 stETH
    user.address,         # Recipient
    empty(addys.Addys),
    sender=teller.address
)

# User may receive more than 0.5 stETH if yield has accumulated
# withdrawal_amount could be 0.52 stETH if vault has gained 4% yield
```

### `transferBalanceWithinVault`

Transfers share-based positions between users (used for liquidations).

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
| `_asset` | `address` | Rebase token to transfer |
| `_fromUser` | `address` | User losing the position |
| `_toUser` | `address` | User gaining the position |
| `_transferAmount` | `uint256` | Asset amount to transfer |
| `_a` | `addys.Addys` | Protocol addresses struct (unused) |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Actual amount transferred |
| `bool` | True if from user's position is now depleted |

#### Access

Only callable by AuctionHouse or CreditEngine (for liquidations)

#### Process Flow
1. **Access Validation**: Ensures caller is liquidation contract
2. **SharesVault Delegation**: Calls `sharesVault._transferBalanceWithinVault()` for share transfers
3. **Share Transfer**: Transfers shares (not amounts) between users
4. **Yield Preservation**: Both users maintain their proportional yield benefits
5. **Event Emission**: Logs transfer with shares transferred and depletion status
6. **Return**: Returns transfer amount and from user depletion status

#### Events Emitted

- `RebaseErc20VaultTransfer` - Contains fromUser, toUser, asset, transferAmount, depletion status, and shares transferred

#### Liquidation Integration
During liquidations, collateral positions (including accumulated yield) are transferred:

#### Example Integration
```python
# Called by AuctionHouse during liquidation
transfer_amount, is_depleted = rebase_erc20_vault.transferBalanceWithinVault(
    steth_token.address,
    borrower.address,      # User being liquidated
    liquidator.address,    # User receiving collateral
    1_000000000000000000,  # 1 stETH worth of position
    empty(addys.Addys),
    sender=auction_house.address
)

# Liquidator receives shares representing 1 stETH worth of position
# This includes any accumulated stETH yield/rebases
```

## Integration Support Functions

### `getVaultDataOnDeposit`

Provides share-based vault data needed by Teller for deposit operations.

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

Used by Teller.vy to validate deposits and calculate fees. For RebaseErc20 vault, this accounts for current share price in calculations.

### `getUserLootBoxShare`

Returns user's share amount for Lootbox reward calculations.

```vyper
@view
@external
def getUserLootBoxShare(_user: address, _asset: address) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User to get share for |
| `_asset` | `address` | Asset to check shares for |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | User's share amount (used for proportional reward calculations) |

#### Usage

Used by Lootbox.vy for reward distribution calculations. Uses share amounts rather than asset amounts to ensure fair reward distribution regardless of yield accumulation timing.

### `getUserAssetAndAmountAtIndex`

Returns asset and current value at specific index for CreditEngine collateral calculations.

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
| `uint256` | Current asset value of user's shares |

#### Usage

Used by CreditEngine.vy for collateral evaluation. This function converts user's shares to current asset amounts, including accumulated yield, for borrowing capacity calculations.

#### Important Yield Consideration
The returned amount includes accumulated yield, so collateral value increases over time as the vault accumulates yield:

#### Example Integration
```python
# CreditEngine evaluates collateral including yield
asset, amount = rebase_erc20_vault.getUserAssetAndAmountAtIndex(user.address, 1)
# amount = user's shares converted to current asset value (includes accumulated yield)
collateral_value = price_desk.getUsdValue(asset, amount)
```

### `getUserAssetAtIndexAndHasBalance`

Returns asset at index and whether user has shares.

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
| `bool` | True if user has positive share balance |

#### Usage

Used by Lootbox.vy and AuctionHouse.vy for position validation and efficient iteration.

## Utility Functions

### `getTotalAmountForUser`

Returns current asset value of user's shares (including accumulated yield).

```vyper
@view
@external
def getTotalAmountForUser(_user: address, _asset: address) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User to query |
| `_asset` | `address` | Asset to get value for |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Current asset value of user's share position |

#### Yield Reflection
The returned amount reflects accumulated yield and grows over time:

#### Example Usage
```python
# Check user's current stETH value (includes accumulated rewards)
current_value = rebase_erc20_vault.getTotalAmountForUser(user.address, steth_token.address)

# User deposited 1.0 stETH, but current_value might be 1.05 stETH due to staking rewards
print(f"User's stETH position is worth {current_value / 10**18} stETH")
```

### `getTotalAmountForVault`

Returns total asset value held by the vault (includes all accumulated yield/rebases).

```vyper
@view
@external
def getTotalAmountForVault(_asset: address) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_asset` | `address` | Asset to get total value for |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Total asset balance including accumulated yield |

#### Characteristics
- Includes all rebases and yield that have accrued to the vault
- Should equal sum of all users' current asset values
- Grows automatically as rebase tokens adjust balances

## Events

### `RebaseErc20VaultDeposit`

Emitted when users deposit tokens into the yield-bearing vault.

#### Event Data

| Field | Type | Description |
|-------|------|-------------|
| `user` | `indexed(address)` | User making deposit |
| `asset` | `indexed(address)` | Rebase token deposited |
| `amount` | `uint256` | Amount of tokens deposited |
| `shares` | `uint256` | Number of shares minted |

### `RebaseErc20VaultWithdrawal`

Emitted when users withdraw tokens from the yield-bearing vault.

#### Event Data

| Field | Type | Description |
|-------|------|-------------|
| `user` | `indexed(address)` | User making withdrawal |
| `asset` | `indexed(address)` | Rebase token withdrawn |
| `amount` | `uint256` | Amount of tokens withdrawn (may include yield) |
| `isDepleted` | `bool` | True if user's position is now zero |
| `shares` | `uint256` | Number of shares burned |

### `RebaseErc20VaultTransfer`

Emitted when share positions are transferred between users (liquidations).

#### Event Data

| Field | Type | Description |
|-------|------|-------------|
| `fromUser` | `indexed(address)` | User losing position |
| `toUser` | `indexed(address)` | User gaining position |
| `asset` | `indexed(address)` | Rebase token transferred |
| `transferAmount` | `uint256` | Asset amount transferred |
| `isFromUserDepleted` | `bool` | True if from user's position is now zero |
| `transferShares` | `uint256` | Number of shares transferred |

## Yield Mechanics

### Share Price Calculation

The core of RebaseErc20's yield capture mechanism:

```python
# Share price calculation
totalAssetBalance = vault_contract.balance_of(asset)  # Includes accumulated yield
totalShares = vault_data.totalBalances[asset]         # Total shares outstanding

if totalShares > 0:
    sharePrice = totalAssetBalance / totalShares
else:
    sharePrice = 1.0  # Initial price for first deposit
```

### Yield Accumulation Process

1. **Initial State**: User deposits 100 tokens, receives 100 shares (1:1 ratio)
2. **Yield Accrual**: Token rebases to 105 balance in vault
3. **Share Price Increase**: Share price now 105/100 = 1.05 tokens per share
4. **User Benefit**: User's 100 shares worth 105 tokens (5% gain)
5. **New Deposits**: New depositor gets fewer shares per token due to higher share price

### Rebase Token Compatibility

RebaseErc20 vault works with various rebase mechanisms:

#### Positive Rebase (stETH, aTokens)
- Token balance increases automatically
- Share price increases proportionally
- All users benefit from yield automatically

#### Negative Rebase (rare)
- Token balance decreases
- Share price decreases proportionally
- Losses shared proportionally among users

#### Fixed Supply + External Rewards
- Token balance stays same
- External rewards added to vault
- Share price increases from reward accumulation

## Security Considerations

### Share-Based Protection
- **Donation Attack Prevention**: Decimal offset prevents share price manipulation
- **Proportional Fairness**: All users benefit from yield proportionally to their holdings
- **No Yield Theft**: Impossible for one user to claim another's accumulated yield

### Access Controls
- **Teller Only**: Deposits restricted to Teller contract
- **Authorized Withdrawals**: Withdrawals restricted to authorized protocol contracts
- **Liquidation Safety**: Share transfers maintain proportional ownership

### Yield Safety
- **Automatic Compounding**: No user action required to capture yield
- **No Timing Exploitation**: Share price reflects current state, preventing timing attacks
- **Fair Entry/Exit**: New and exiting users transact at current fair share price

### Integration Safety
- **Module Delegation**: Core logic handled by battle-tested SharesVault module
- **Event Consistency**: Contract-specific events provide clear audit trails
- **Collateral Accuracy**: CreditEngine receives accurate yield-inclusive valuations

## Usage Patterns

### Yield Farming
```python
# User deposits rebase token for automatic yield
teller.depositToVault(
    rebase_erc20_vault.address,
    steth_token.address,
    1_000000000000000000,  # 1 stETH
    sender=user.address
)

# Yield accumulates automatically over time
# User can check current value periodically
current_value = rebase_erc20_vault.getTotalAmountForUser(user.address, steth_token.address)
```

### Collateral with Yield
```python
# User's collateral value increases over time due to yield
# CreditEngine automatically considers current value including yield
credit_engine.borrow(
    user.address,
    green_token.address,
    1000_000000000000000000,  # Borrow GREEN
    sender=user.address
    # Collateral value includes accumulated stETH rewards
)
```

### Liquidation with Yield Transfer
```python
# During liquidation, accumulated yield transfers to liquidator
auction_house.liquidate(
    borrower.address,
    liquidator.address
    # Liquidator receives borrower's vault position including accumulated yield
)
```

## Differences from Other Vault Types

### vs. SimpleErc20 Vault
- **Share vs. Balance**: RebaseErc20 uses shares, SimpleErc20 uses direct balances
- **Yield Capture**: RebaseErc20 automatically captures yield, SimpleErc20 does not
- **Complexity**: RebaseErc20 requires share price calculations, SimpleErc20 is 1:1

### vs. StabilityPool Vault
- **Accounting Basis**: RebaseErc20 uses asset-based shares, StabilityPool uses USD-based shares
- **Yield Source**: RebaseErc20 from token rebases, StabilityPool from liquidation proceeds
- **Purpose**: RebaseErc20 for yield farming, StabilityPool for liquidation insurance

### vs. RipeGov Vault
- **Lock Mechanisms**: RebaseErc20 has no locking, RipeGov has time locks
- **Governance Features**: RebaseErc20 focuses on yield, RipeGov on governance participation
- **Reward Types**: RebaseErc20 captures asset yield, RipeGov earns governance points

## Best Practices

### For Users
- **Long-term Holding**: Yield compounds automatically, ideal for set-and-forget strategies
- **Monitor Share Price**: Track share price appreciation to understand yield generation
- **Consider Gas Costs**: Frequent deposits/withdrawals may erode yield gains

### For Integrators
- **Use Current Values**: Always query current asset values for accurate collateral assessment
- **Account for Yield**: Consider that user balances increase over time
- **Share-based Calculations**: When possible, work with shares rather than converting to assets

## Testing

For comprehensive test examples, see: [`tests/vaults/test_rebase_erc20.py`](../../tests/vaults/test_rebase_erc20.py)