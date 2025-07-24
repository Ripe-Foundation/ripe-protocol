# StabVault Module Technical Documentation

[📄 View Source Code](../../../contracts/vaults/modules/StabVault.vy)

## Overview

StabVault is the most sophisticated vault module in Ripe Protocol, implementing stability pool functionality for liquidation absorption. Users provide stablecoin liquidity and receive liquidated collateral at discounts plus RIPE rewards, acting as the protocol's insurance fund.

**Core Functions**:
- **Stability Operations**: Stablecoin deposits absorb liquidations for discounted collateral
- **USD-Based Shares**: Value accounting includes deposits plus accumulated collateral
- **Claimable Tracking**: Detailed records of liquidated assets available for claiming
- **Redemption System**: Exchange GREEN for claimable assets at market rates
- **Automated Rewards**: RIPE rewards distributed and locked in governance vault

StabVault implements USD value-based accounting with PriceDesk integration, comprehensive asset tracking with automatic cleanup, and sophisticated AuctionHouse liquidation swaps. It handles complex multi-asset operations while maintaining accurate accounting for fair distribution among participants.

## Architecture & Dependencies

StabVault is built as a complex vault module with multiple external dependencies:

### Core Dependencies
- **VaultData**: State management for shares and user assets
- **Addys**: Address resolution for protocol contracts
- **MissionControl**: Configuration and permission management
- **PriceDesk**: USD value calculations for all assets
- **VaultBook**: Ripe token minting for rewards
- **Teller**: Deposit automation and user validation
- **Ledger**: Reward availability tracking

### Module Dependencies
```vyper
uses: vaultData
uses: addys
import contracts.vaults.modules.VaultData as vaultData
import contracts.modules.Addys as addys
```

### Key Constants
- `DECIMAL_OFFSET: constant(uint256) = 10 ** 8` - Donation attack prevention
- `EIGHTEEN_DECIMALS: constant(uint256) = 10 ** 18` - Reward calculations
- `RIPE_GOV_VAULT_ID: constant(uint256) = 2` - Governance vault for rewards
- `MAX_STAB_CLAIMS: constant(uint256) = 15` - Maximum batch claims
- `MAX_STAB_REDEMPTIONS: constant(uint256) = 15` - Maximum batch redemptions

## Data Structures

### StabPoolClaim
Structure for claiming liquidated assets:
```vyper
struct StabPoolClaim:
    stabAsset: address      # Stability pool asset (GREEN, sGREEN, etc.)
    claimAsset: address     # Asset to claim (liquidated collateral)
    maxUsdValue: uint256    # Maximum USD value to claim
```

### StabPoolRedemption
Structure for redeeming GREEN for claimable assets:
```vyper
struct StabPoolRedemption:
    claimAsset: address     # Asset to redeem for
    maxGreenAmount: uint256 # Maximum GREEN to spend
```

### Configuration Structures
Various config structures from MissionControl:
- `StabPoolClaimsConfig` - Claim permissions and reward settings
- `StabPoolRedemptionsConfig` - Redemption permissions
- `TellerDepositConfig` - Auto-deposit validation

## State Variables

### Claimable Asset Tracking
- `claimableBalances: HashMap[address, HashMap[address, uint256]]` - Maps stab asset → claimable asset → balance
- `totalClaimableBalances: HashMap[address, uint256]` - Total claimable balance per asset
- `claimableAssets: HashMap[address, HashMap[uint256, address]]` - Iterable claimable assets per stab asset
- `indexOfClaimableAsset: HashMap[address, HashMap[address, uint256]]` - Asset index lookup
- `numClaimableAssets: HashMap[address, uint256]` - Count of claimable assets per stab asset

### Inherited State (from VaultData)
- User share balances (stored as shares representing USD value)
- Total share balances per stability pool asset
- User asset registrations and indexing
- Vault pause state and configuration

## System Architecture Diagram

```
+------------------------------------------------------------------------+
|                        StabVault Module                               |
+------------------------------------------------------------------------+
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                   USD Value-Based Share Accounting              |  |
|  |                                                                  |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ _depositTokensInVault(_user, _asset, _amount, _addys)       │ |  |
|  |  │ 1. Calculate USD value of deposit using PriceDesk           │ |  |
|  |  │ 2. Calculate total pool value (stab assets + claimables)    │ |  |
|  |  │ 3. Mint shares based on USD value contribution:             │ |  |
|  |  │    shares = (depositValue * totalShares) / totalPoolValue   │ |  |
|  |  │ 4. Store shares in VaultData (not asset amounts)            │ |  |
|  |  │ 5. Return deposit amount and shares minted                  │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  |                                                                  |  |
|  |  Share Value Calculation Components:                             |  |
|  |  • Stability Asset Value: USD value of deposited stablecoins    |  |
|  |  • Claimable Asset Value: USD value of liquidated collateral    |  |
|  |  • Total Pool Value = Stability Value + Claimable Value         |  |
|  |  • Share Price = Total Pool Value / Total Shares                |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Liquidation Integration                       |  |
|  |                                                                  |  |
|  |  AuctionHouse Integration:                                       |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ swapForLiquidatedCollateral(stab, amount, liq, liqSent, ...) │ |  |
|  |  │ 1. Receive liquidated collateral from AuctionHouse          │ |  |
|  |  │ 2. Add to claimableBalances[stabAsset][liqAsset]             │ |  |
|  |  │ 3. Either burn GREEN/sGREEN or transfer stablecoin           │ |  |
|  |  │ 4. Update total pool value (increases share value)          │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  |                                                                  |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ swapWithClaimableGreen(stab, green, liq, liqSent, ...)       │ |  |
|  |  │ 1. Use claimable GREEN to purchase liquidated collateral     │ |  |
|  |  │ 2. Reduce claimableBalances[stabAsset][greenToken]           │ |  |
|  |  │ 3. Add new collateral to claimable balances                 │ |  |
|  |  │ 4. Burn the GREEN tokens used in swap                       │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                      Claim System                               |  |
|  |                                                                  |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ claimFromStabilityPool(claimer, stab, claim, maxUSD, ...)    │ |  |
|  |  │ 1. Validate claim permissions via MissionControl             │ |  |
|  |  │ 2. Calculate user's proportional share of claimable asset   │ |  |
|  |  │    userShare = userShares * claimableBalance / totalShares   │ |  |
|  |  │ 3. Burn user shares proportionally                          │ |  |
|  |  │ 4. Reduce claimable balances                                │ |  |
|  |  │ 5. Transfer asset to user or auto-deposit                   │ |  |
|  |  │ 6. Mint and distribute Ripe rewards                         │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  |                                                                  |  |
|  |  Batch Claims: claimManyFromStabilityPool()                      |  |
|  |  • Process multiple claims in single transaction                |  |
|  |  • Aggregate rewards for single governance deposit              |  |
|  |  • Fail gracefully if individual claims fail                    |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Redemption System                            |  |
|  |                                                                  |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ redeemFromStabilityPool(asset, green, recipient, ...)        │ |  |
|  |  │ 1. Validate redemption permissions                          │ |  |
|  |  │ 2. Check available claimable assets across all stab pools   │ |  |
|  |  │ 3. Exchange GREEN 1:1 for USD value of claimable assets     │ |  |
|  |  │ 4. For sGREEN pools: Convert GREEN to sGREEN directly       │ |  |
|  |  │ 5. For other pools: Add GREEN to claimable balances         │ |  |
|  |  │ 6. Transfer redeemed assets to user or auto-deposit         │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  |                                                                  |  |
|  |  Batch Redemptions: redeemManyFromStabilityPool()               |  |
|  |  • Redeem across multiple asset types in priority order         |  |
|  |  • Stop when GREEN is exhausted                                 |  |
|  |  • Return unused GREEN as GREEN or sGREEN per user preference   |  |
|  +------------------------------------------------------------------+  |
+------------------------------------------------------------------------+
                                    |
                                    |
                                    v
+------------------------------------------------------------------------+
|                        External Dependencies                          |
+------------------------------------------------------------------------+
|                                                                        |
|  VaultData Module:                MissionControl:                      |
|  • Share storage (USD values)    • Claim permissions                   |
|  • User asset tracking          • Redemption permissions               |
|  • Registration functions       • Reward configurations                |
|                                  • Auto-deposit validation             |
|  PriceDesk:                                                            |
|  • USD value calculations       Teller:                                |
|  • Asset amount conversions     • Auto-deposit execution               |
|                                 • User relationship validation          |
|  AuctionHouse:                                                         |
|  • Liquidation swaps           VaultBook:                              |
|  • Collateral distribution     • Ripe token minting                    |
|                                                                        |
|  Ledger:                        Token Contracts:                       |
|  • Reward availability         • GREEN/sGREEN operations               |
|  • Protocol accounting         • ERC4626 conversions                   |
+------------------------------------------------------------------------+
```

## Core Functions

### `_depositTokensInVault`

Handles deposits into stability pools with USD value-based share accounting.

```vyper
@internal
def _depositTokensInVault(
    _user: address,
    _asset: address,
    _amount: uint256,
    _a: addys.Addys,
) -> (uint256, uint256):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User making the deposit |
| `_asset` | `address` | Stability pool asset (GREEN, sGREEN, etc.) |
| `_amount` | `uint256` | Amount to deposit |
| `_a` | `addys.Addys` | Protocol address struct |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Actual amount deposited |
| `uint256` | Number of shares minted |

#### Process Flow
1. **USD Value Calculation**: Converts asset amount to USD value using PriceDesk
2. **Pool Value Assessment**: Calculates total pool value including claimable assets
3. **Share Minting**: Uses USD values for precise share calculation:
   ```
   shares = (depositUsdValue * totalShares) / (stabValue + claimableValue)
   ```
4. **Balance Update**: Stores shares (not amounts) in VaultData
5. **Return**: Returns deposited amount and shares minted

#### Key Differences from Other Vault Types
- Uses USD values instead of asset amounts for share calculations
- Accounts for claimable asset value in total pool value
- Supports multiple stablecoin types (GREEN, sGREEN, others)

### `_withdrawTokensFromVault`

Handles withdrawals from stability pools with share burning and asset calculation.

```vyper
@internal
def _withdrawTokensFromVault(
    _user: address,
    _asset: address,
    _amount: uint256,
    _recipient: address,
    _a: addys.Addys,
) -> (uint256, uint256, bool):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User making withdrawal |
| `_asset` | `address` | Stability pool asset |
| `_amount` | `uint256` | Amount to withdraw |
| `_recipient` | `address` | Withdrawal recipient |
| `_a` | `addys.Addys` | Protocol address struct |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Actual amount withdrawn |
| `uint256` | Number of shares burned |
| `bool` | True if user's position is depleted |

#### Process Flow
1. **Share/Amount Calculation**: Determines shares needed for requested amount
2. **Balance Verification**: Ensures user has sufficient shares
3. **Share Burning**: Reduces user shares in VaultData
4. **Asset Transfer**: Transfers calculated amount to recipient
5. **Return**: Returns withdrawal details

### `_transferBalanceWithinVault`

Transfers share balances between users (used for liquidations).

```vyper
@internal
def _transferBalanceWithinVault(
    _asset: address,
    _fromUser: address,
    _toUser: address,
    _transferAmount: uint256,
    _a: addys.Addys,
) -> (uint256, uint256, bool):
```

Similar to withdrawal but transfers shares between users instead of removing from vault.

## Liquidation Integration Functions

### `swapForLiquidatedCollateral`

Receives liquidated collateral from AuctionHouse in exchange for stability pool assets.

```vyper
@external
def swapForLiquidatedCollateral(
    _stabAsset: address,
    _stabAssetAmount: uint256,
    _liqAsset: address,
    _liqAmountSent: uint256,
    _recipient: address,
    _greenToken: address,
    _savingsGreenToken: address,
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_stabAsset` | `address` | Stability pool asset to use |
| `_stabAssetAmount` | `uint256` | Amount of stability asset to exchange |
| `_liqAsset` | `address` | Liquidated collateral received |
| `_liqAmountSent` | `uint256` | Amount of liquidated asset received |
| `_recipient` | `address` | Recipient (empty for burn) |
| `_greenToken` | `address` | GREEN token address |
| `_savingsGreenToken` | `address` | sGREEN token address |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Amount of stability asset used |

#### Access

Only callable by [AuctionHouse](../../core/AuctionHouse.md)

#### Process Flow
1. **Validation**: Ensures stab asset is supported and liq asset is not a vault asset
2. **Claimable Balance Addition**: Adds received collateral to claimable balances
3. **Asset Handling**: Either burns GREEN/sGREEN or transfers to recipient
4. **Value Increase**: Claimable asset addition increases total pool value

#### Example Integration
```python
# Called by AuctionHouse during liquidation
amount_used = stab_vault.swapForLiquidatedCollateral(
    green_token.address,      # Use GREEN from stability pool
    1000_000000000000000000,  # 1000 GREEN
    weth.address,             # Received WETH collateral
    500_000000000000000000,   # 0.5 WETH received
    empty(address),           # Burn GREEN (don't send to recipient)
    green_token.address,
    savings_green.address,
    sender=auction_house.address
)
```

### `swapWithClaimableGreen`

Uses claimable GREEN tokens to purchase additional liquidated collateral.

```vyper
@external
def swapWithClaimableGreen(
    _stabAsset: address,
    _greenAmount: uint256,
    _liqAsset: address,
    _liqAmountSent: uint256,
    _greenToken: address,
) -> uint256:
```

#### Process Flow
1. **Claimable Check**: Verifies sufficient claimable GREEN available
2. **Asset Addition**: Adds new liquidated collateral to claimable balances
3. **GREEN Reduction**: Reduces claimable GREEN balance
4. **GREEN Burning**: Burns the GREEN tokens used in swap

## Claim System Functions

### `claimFromStabilityPool`

Allows users to claim their proportional share of liquidated collateral.

```vyper
@external
def claimFromStabilityPool(
    _claimer: address,
    _stabAsset: address,
    _claimAsset: address,
    _maxUsdValue: uint256,
    _caller: address,
    _shouldAutoDeposit: bool,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_claimer` | `address` | User claiming assets |
| `_stabAsset` | `address` | Stability pool asset user deposited |
| `_claimAsset` | `address` | Liquidated asset to claim |
| `_maxUsdValue` | `uint256` | Maximum USD value to claim |
| `_caller` | `address` | Address initiating claim |
| `_shouldAutoDeposit` | `bool` | Whether to auto-deposit claimed assets |
| `_a` | `addys.Addys` | Protocol addresses |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | USD value claimed |

#### Access

Only callable by [Teller](../../core/Teller.md)

#### Process Flow
1. **Permission Validation**: Checks claim permissions via MissionControl
2. **Share Calculation**: Determines user's proportional share:
   ```
   userClaimShare = userShares / totalShares * claimableBalance
   ```
3. **Balance Updates**: Burns user shares and reduces claimable balances
4. **Asset Transfer**: Either transfers to user or auto-deposits
5. **Reward Distribution**: Mints and stakes Ripe rewards
6. **Event Emission**: Logs claim details

#### Example Usage
```python
# User claims WETH from GREEN stability pool
usd_value_claimed = stab_vault.claimFromStabilityPool(
    user.address,             # Claimer
    green_token.address,      # Stability pool asset
    weth.address,             # Asset to claim
    500_000000000000000000,   # Max $500 USD value
    user.address,             # Caller
    True,                     # Auto-deposit to WETH vault
    empty(addys.Addys),       # Use default addresses
    sender=teller.address
)
```

### `claimManyFromStabilityPool`

Batch claiming from multiple stability pools or multiple assets.

```vyper
@external
def claimManyFromStabilityPool(
    _claimer: address,
    _claims: DynArray[StabPoolClaim, MAX_STAB_CLAIMS],
    _caller: address,
    _shouldAutoDeposit: bool,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
```

#### Features
- Processes up to 15 claims in single transaction
- Aggregates rewards for single governance deposit
- Continues processing if individual claims fail
- Returns total USD value claimed

## Redemption System Functions

### `redeemFromStabilityPool`

Exchanges GREEN tokens for available claimable assets at fair market rates.

```vyper
@external
def redeemFromStabilityPool(
    _asset: address,
    _greenAmount: uint256,
    _recipient: address,
    _caller: address,
    _shouldAutoDeposit: bool,
    _shouldRefundSavingsGreen: bool,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_asset` | `address` | Asset to redeem for |
| `_greenAmount` | `uint256` | GREEN tokens to spend |
| `_recipient` | `address` | Redemption recipient |
| `_caller` | `address` | Address initiating redemption |
| `_shouldAutoDeposit` | `bool` | Auto-deposit redeemed assets |
| `_shouldRefundSavingsGreen` | `bool` | Return unused GREEN as sGREEN |
| `_a` | `addys.Addys` | Protocol addresses |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Amount of GREEN spent |

#### Process Flow
1. **Permission Validation**: Checks redemption permissions
2. **Asset Availability**: Verifies claimable assets available
3. **Rate Calculation**: Uses PriceDesk for fair exchange rates
4. **Cross-Pool Redemption**: Searches across all stability pools
5. **Asset Distribution**: Either transfers or auto-deposits
6. **GREEN Handling**: Returns unused GREEN as requested

#### Example Usage
```python
# Redeem GREEN for WETH across all stability pools
green_spent = stab_vault.redeemFromStabilityPool(
    weth.address,             # Want WETH
    1000_000000000000000000,  # Spend up to 1000 GREEN
    user.address,             # Recipient
    user.address,             # Caller
    False,                    # Don't auto-deposit
    True,                     # Refund unused as sGREEN
    empty(addys.Addys),       # Use default addresses
    sender=teller.address
)
```

### `redeemManyFromStabilityPool`

Batch redemption across multiple asset types with priority ordering.

```vyper
@external
def redeemManyFromStabilityPool(
    _redemptions: DynArray[StabPoolRedemption, MAX_STAB_REDEMPTIONS],
    _greenAmount: uint256,
    _recipient: address,
    _caller: address,
    _shouldAutoDeposit: bool,
    _shouldRefundSavingsGreen: bool,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
```

## Share Conversion Functions

### `valueToShares`

Converts USD values to shares for external queries.

```vyper
@view
@external
def valueToShares(_asset: address, _usdValue: uint256, _shouldRoundUp: bool) -> uint256:
```

### `sharesToValue`

Converts shares to USD values for external queries.

```vyper
@view
@external
def sharesToValue(_asset: address, _shares: uint256, _shouldRoundUp: bool) -> uint256:
```

### Internal Conversion Functions

#### `_valueToShares`
Core USD value to shares conversion with donation attack prevention:
```vyper
# Dead shares / decimal offset -- preventing donation attacks
totalUsdValue += 1
totalShares += DECIMAL_OFFSET

# Calculate shares
shares = (usdValue * totalShares) / totalUsdValue
```

#### `_sharesToValue`
Core shares to USD value conversion with same protection mechanisms.

## Utility Functions

### USD Value Calculations

#### `_getUsdValue`
Converts asset amounts to USD values using PriceDesk:
- GREEN tokens: 1:1 USD
- sGREEN tokens: Uses ERC4626 conversion then 1:1 USD
- Other assets: Uses PriceDesk oracle

#### `_getAssetAmount`
Converts USD values to asset amounts:
- GREEN tokens: 1:1 USD
- sGREEN tokens: Uses ERC4626 conversion
- Other assets: Uses PriceDesk oracle

### Pool Value Functions

#### `getTotalValue`
Returns total USD value of stability pool (stab assets + claimable assets).

#### `getTotalUserValue`
Returns USD value of user's stability pool position.

#### `_getTotalValue`
Internal function calculating total pool value:
```vyper
totalStabValue = _getUsdValue(stabAsset, stabBalance, ...)
claimableValue = _getValueOfClaimableAssets(stabAsset, ...)
return totalStabValue + claimableValue
```

## Integration Support Functions

### `_getUserAssetAndAmountAtIndex`

**Important**: Returns `empty(address), 0` to prevent borrowing against stability pool positions.

```vyper
@view
@internal
def _getUserAssetAndAmountAtIndex(_user: address, _index: uint256) -> (address, uint256):
    # NOTE: cannot borrow against stability pool positions, returning empty/0 to ensure this
    return empty(address), 0
```

This is a critical security feature that prevents users from using stability pool shares as collateral for borrowing.

### `_getTotalAmountForUser`

Returns the USD value of user's position converted to the stability pool asset amount.

**Note**: The returned amount represents USD value, not actual asset balance in the vault.

### `_getTotalAmountForVault`

Returns total stability pool value converted to asset amount for display purposes.

## Claimable Asset Management

### Registration and Tracking

#### `_addClaimableBalance`
Adds received liquidated assets to claimable balances:
```vyper
self.claimableBalances[_stabAsset][_claimAsset] += claimAmount
self.totalClaimableBalances[_claimAsset] += claimAmount
```

#### `_registerClaimableAsset`
Automatically registers new claimable assets for iteration.

#### `_reduceClaimableBalances`
Reduces claimable balances when assets are claimed or redeemed.

#### `_removeClaimableAsset`
Automatically deregisters claimable assets when balance reaches zero.

### Asset Handling

#### `_handleAssetForUser`
Handles claimed/redeemed assets:
- Attempts auto-deposit if requested and permitted
- Falls back to direct transfer if auto-deposit not available

#### `_handleGreenForUser`
Handles GREEN token distributions:
- Converts to sGREEN if requested and amount is sufficient
- Transfers as GREEN if sGREEN not wanted or amount too small

## Reward System

### `_handleClaimRewards`

Automatically distributes Ripe rewards to users who claim from stability pools:

```vyper
@internal
def _handleClaimRewards(
    _claimer: address,
    _claimUsdValue: uint256,
    _lockDuration: uint256,
    _ripePerDollarClaimed: uint256,
    _a: addys.Addys,
):
```

#### Process Flow
1. **Reward Calculation**: `ripeRewards = claimUsdValue * ripePerDollarClaimed`
2. **Availability Check**: Ensures sufficient Ripe available in Ledger
3. **Minting**: Mints Ripe tokens via VaultBook
4. **Governance Deposit**: Auto-deposits into Ripe governance vault with lock
5. **Permission Cleanup**: Clears token approvals after deposit

## Security Considerations

### Access Controls
- **AuctionHouse Only**: Liquidation swaps restricted to AuctionHouse
- **Teller Only**: Claims and redemptions only through Teller
- **Permission Validation**: All operations check MissionControl permissions

### Share Accounting Safety
- **USD Value Based**: Uses stable USD values instead of volatile asset amounts
- **Donation Attack Prevention**: DECIMAL_OFFSET prevents share price manipulation
- **Precise Calculations**: Handles rounding consistently across operations

### Asset Isolation
- **No Borrowing**: Stability pool positions cannot be used as collateral
- **Proper Segregation**: Claimable assets tracked separately from user deposits
- **Balance Consistency**: Maintains invariants across complex operations

### Graceful Degradation
- **Batch Operation Safety**: Individual failures don't break batch operations
- **Price Oracle Dependencies**: Handles price failures gracefully
- **Reward Availability**: Continues operation even when rewards unavailable

## Testing

For comprehensive test examples, see: [`tests/vaults/test_stab_vault.py`](../../tests/vaults/test_stab_vault.py)