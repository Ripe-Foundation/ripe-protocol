# RipeGov Vault Technical Documentation

[📄 View Source Code](../../contracts/vaults/RipeGov.vy)

## Overview

RipeGov is the protocol's governance vault where users lock RIPE tokens or RIPE LP tokens to gain voting power. Lock duration determines governance points - longer locks earn exponentially more power, creating alignment between token holders and protocol success.

**Core Mechanics**:
- **Time-Locked Staking**: Lock RIPE for 3 months to 2 years for voting rights
- **Governance Points**: Earn points based on amount × duration × asset weight
- **Lock Management**: Extend locks for bonuses or exit early with penalties
- **Real-Time Voting Power**: Automatic Boardroom integration updates governance weight

Built on SharesVault with specialized governance calculations, RipeGov incentivizes long-term participation. Example: Lock 1000 RIPE for 2 years to get 50% more voting power than a 6-month lock. The vault also handles contributor token transfers and supports protocol-wide governance operations.

## Architecture & Dependencies

RipeGov is built using a sophisticated modular architecture with multiple external integrations:

### Core Module Dependencies
- **SharesVault**: Provides yield-bearing vault functionality with share-based accounting
- **VaultData**: Manages user balances, asset registration, and vault state
- **[Addys](../modules/Addys.md)**: Handles protocol address resolution and permission management

### External Integrations
- **MissionControl**: Configuration management for lock terms and asset weights
- **BoardRoom**: Receives governance power updates for voting systems
- **[Lootbox](../core/Lootbox.md)**: Integrates with reward distribution and points tracking
- **VaultBook**: Provides vault registration and identification
- **Ledger**: Checks bad debt status for withdrawal restrictions
- **[HumanResources](../core/HumanResources.md)**: Manages contributor tokens and transfers

### Module Initialization
```vyper
exports: addys.__interface__
exports: vaultData.__interface__
exports: sharesVault.__interface__

initializes: addys
initializes: vaultData[addys := addys]
initializes: sharesVault[vaultData := vaultData]
```

## Data Structures

### GovData Struct
Tracks comprehensive governance data for each user-asset combination:
```vyper
struct GovData:
    govPoints: uint256          # Accumulated governance points
    lastShares: uint256         # Last known share balance
    lastPointsUpdate: uint256   # Block of last points update
    unlock: uint256             # Block when position unlocks
    lastTerms: cs.LockTerms     # Last known lock terms
```

### Lock Terms Configuration (from MissionControl)
```vyper
struct LockTerms:
    minLockDuration: uint256    # Minimum lock period in blocks
    maxLockDuration: uint256    # Maximum lock period in blocks
    maxLockBoost: uint256       # Maximum bonus percentage for max lock
    exitFee: uint256           # Fee percentage for early exit
    canExit: bool              # Whether early exit is allowed
```

### RipeGovVaultConfig (from MissionControl)
```vyper
struct RipeGovVaultConfig:
    lockTerms: LockTerms       # Lock configuration
    assetWeight: uint256       # Asset weight for point calculations
    shouldFreezeWhenBadDebt: bool # Whether to freeze withdrawals during bad debt
```

## State Variables

### Governance Point Tracking
- `userGovData: HashMap[address, HashMap[address, GovData]]` - User → asset → governance data
- `totalUserGovPoints: HashMap[address, uint256]` - Total governance points per user
- `totalGovPoints: uint256` - Global total governance points

### Inherited State (from SharesVault/VaultData)
- User share balances representing deposited assets
- Total share balances per asset
- Asset registration and enumeration
- Pause state and configuration

### Constants
- `PRECISION: constant(uint256) = 10 ** 18` - Precision for share calculations
- `HUNDRED_PERCENT: constant(uint256) = 100_00` - 100.00% for percentage calculations

## System Architecture Diagram

```
+------------------------------------------------------------------------+
|                         RipeGov Vault                                 |
+------------------------------------------------------------------------+
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Governance Point System                      |  |
|  |                                                                  |  |
|  |  Point Calculation Formula:                                      |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ Base Points = shares * blocks_elapsed * asset_weight         │ |  |
|  |  │ Lock Bonus = base_points * lock_boost_ratio                  │ |  |
|  |  │ Total Points = Base Points + Lock Bonus                     │ |  |
|  |  │                                                             │ |  |
|  |  │ Lock Boost Ratio Calculation:                               │ |  |
|  |  │ remaining_duration = unlock_block - current_block           │ |  |
|  |  │ duration_ratio = (remaining - min) / (max - min)            │ |  |
|  |  │ lock_boost_ratio = max_lock_boost * duration_ratio          │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  |                                                                  |  |
|  |  Points Update Triggers:                                         |  |
|  |  • Every deposit (accumulate + add new lock)                     |  |
|  |  • Every withdrawal (accumulate + penalty)                       |  |
|  |  • Manual updates (accumulate + no change)                       |  |
|  |  • Lock adjustments (accumulate + extend)                        |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                      Deposit Operations                          |  |
|  |                                                                  |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ _depositTokensInRipeGovVault(user, asset, amount, lock)      │ |  |
|  |  │ 1. Use SharesVault to handle token deposit and share mint   │ |  |
|  |  │ 2. Get lock configuration from MissionControl               │ |  |
|  |  │ 3. Calculate weighted lock duration:                        │ |  |
|  |  │    new_unlock = weighted_average(old_lock, new_lock)        │ |  |
|  |  │ 4. Accumulate pending governance points                     │ |  |
|  |  │ 5. Update user governance data with new shares/lock        │ |  |
|  |  │ 6. Update total governance points                           │ |  |
|  |  │ 7. Notify Boardroom of governance power change             │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  |                                                                  |  |
|  |  Weighted Lock Calculation:                                      |  |
|  |  • First deposit: Use provided lock duration                     |  |
|  |  • Additional deposits: Weight by share amounts                  |  |
|  |  • Formula: ((old_shares * old_duration) + (new_shares * new_duration)) / total_shares |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                     Withdrawal Operations                        |  |
|  |                                                                  |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ _withdrawTokensFromVault(user, asset, amount, recipient)     │ |  |
|  |  │ 1. Validate unlock conditions:                              │ |  |
|  |  │    - Check current_block >= unlock_block                    │ |  |
|  |  │    - Check bad debt restrictions if configured              │ |  |
|  |  │ 2. Use SharesVault to handle token withdrawal               │ |  |
|  |  │ 3. Accumulate pending governance points                     │ |  |
|  |  │ 4. Calculate governance point penalty:                      │ |  |
|  |  │    penalty = total_points * shares_withdrawn / total_shares │ |  |
|  |  │ 5. Reduce user governance points by penalty                 │ |  |
|  |  │ 6. Update total governance points                           │ |  |
|  |  │ 7. Notify Boardroom of governance power change             │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  |                                                                  |  |
|  |  Special Withdrawal Types:                                       |  |
|  |  • Regular withdrawal: Full restrictions + point penalty         |  |
|  |  • Contributor burn: HR only, no restrictions, full withdrawal   |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                      Lock Management                            |  |
|  |                                                                  |  |
|  |  Lock Extension (adjustLock):                                    |  |
|  |  • Can only extend lock duration, not reduce                     |  |
|  |  • Updates Lootbox points for extended commitment               |  |
|  |  • Immediately applies new lock duration                        |  |
|  |                                                                  |  |
|  |  Early Exit (releaseLock):                                       |  |
|  |  • Requires canExit = true in lock terms                        |  |
|  |  • Charges exit fee as share penalty                            |  |
|  |  • Smart protection: prevents costly exit during bad debt       |  |
|  |  • Immediately removes lock duration                            |  |
|  |                                                                  |  |
|  |  Lock Terms Refresh:                                             |  |
|  |  • Automatically updates when terms change                       |  |
|  |  • Resets lock if key terms become unfavorable                  |  |
|  |  • Protects users from governance parameter attacks             |  |
|  +------------------------------------------------------------------+  |
+------------------------------------------------------------------------+
                                    |
                                    |
                                    v
+------------------------------------------------------------------------+
|                        External Integrations                          |
+------------------------------------------------------------------------+
|                                                                        |
|  SharesVault Module:              MissionControl:                      |
|  • Token deposits/withdrawals     • Lock term configuration            |
|  • Share minting/burning         • Asset weight settings               |
|  • Yield accumulation            • Bad debt freeze settings            |
|                                                                        |
|  Boardroom Integration:           Lootbox Integration:                  |
|  • Real-time governance updates  • Deposit points tracking             |
|  • Voting power notifications    • Lock bonus point calculation        |
|                                                                        |
|  VaultData Foundation:            Human Resources:                      |
|  • User balance tracking         • Contributor token management        |
|  • Asset registration           • Token transfers and burning          |
|  • State management                                                     |
+------------------------------------------------------------------------+
```

## Core Functions

### `depositTokensInVault`

Standard deposit function for regular users through Teller.

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
| `_asset` | `address` | Asset to deposit (RIPE or RIPE LP) |
| `_amount` | `uint256` | Amount to deposit |
| `_a` | `addys.Addys` | Protocol addresses struct |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Actual amount deposited |

#### Access

Only callable by [Teller](../core/Teller.md)

#### Process Flow
1. **SharesVault Deposit**: Uses SharesVault module for token handling and share minting
2. **Configuration**: Gets lock terms and asset weight from MissionControl
3. **Lock Duration**: Uses minimum lock duration from configuration (no custom lock)
4. **Governance Update**: Calls `_handleGovDataOnDeposit` for point calculations
5. **Boardroom Notification**: Updates governance power in voting system

#### Events Emitted

- `RipeGovVaultDeposit` - Contains user, asset, amount, shares, and lock duration

### `depositTokensWithLockDuration`

Advanced deposit function allowing custom lock durations for protocol contracts.

```vyper
@nonreentrant
@external
def depositTokensWithLockDuration(
    _user: address,
    _asset: address,
    _amount: uint256,
    _lockDuration: uint256,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User receiving the deposit |
| `_asset` | `address` | Asset to deposit |
| `_amount` | `uint256` | Amount to deposit |
| `_lockDuration` | `uint256` | Lock duration in blocks |
| `_a` | `addys.Addys` | Protocol addresses struct |

#### Access

Only callable by valid Ripe protocol addresses

#### Lock Duration Handling
- Clamps duration between configured min and max values
- Uses weighted averaging with existing position lock
- Longer locks provide higher governance point bonuses

#### Example Usage
```python
# Deposit Ripe rewards with 1 year lock
deposit_amount = ripe_gov.depositTokensWithLockDuration(
    user.address,
    ripe_token.address,
    1000_000000000000000000,  # 1000 RIPE
    BLOCKS_PER_YEAR,          # 1 year lock
    empty(addys.Addys),       # Use default addresses
    sender=stability_pool.address  # Valid Ripe address
)
```

### `withdrawTokensFromVault`

Withdraws tokens from governance vault with lock period and bad debt checks.

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
| `_asset` | `address` | Asset to withdraw |
| `_amount` | `uint256` | Amount to withdraw |
| `_recipient` | `address` | Address to receive tokens |
| `_a` | `addys.Addys` | Protocol addresses struct |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Actual amount withdrawn |
| `bool` | True if user's position is depleted |

#### Access

Only callable by [Teller](../core/Teller.md), AuctionHouse, or CreditEngine

#### Withdrawal Restrictions
1. **Lock Period**: Must wait until `unlock` block is reached
2. **Bad Debt**: If `shouldFreezeWhenBadDebt` is true, no withdrawals during bad debt
3. **Governance Points**: Withdrawal reduces points proportionally

#### Process Flow
1. **SharesVault Withdrawal**: Handles token transfer and share burning
2. **Restriction Validation**: Checks unlock time and bad debt conditions
3. **Governance Penalty**: Reduces governance points proportionally:
   ```
   points_penalty = user_points * shares_withdrawn / total_user_shares
   ```
4. **State Updates**: Updates user and total governance points
5. **Boardroom Notification**: Updates voting power

### `transferBalanceWithinVault`

Transfers governance positions between users (used for liquidations).

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

#### Access

Only callable by [AuctionHouse](../core/AuctionHouse.md) or CreditEngine (for liquidations)

#### Process Flow
1. **SharesVault Transfer**: Moves shares between users
2. **From User**: Loses governance points proportionally (no point transfer)
3. **To User**: Gains shares with minimum lock duration
4. **Boardroom Updates**: Updates governance power for both users

#### Example Integration
```python
# Called during liquidation to transfer collateral
transferred, is_depleted = ripe_gov.transferBalanceWithinVault(
    ripe_token.address,
    borrower.address,
    liquidator.address,
    collateral_amount,
    empty(addys.Addys),
    sender=credit_engine.address
)
```

## Contributor Management Functions

### `withdrawContributorTokensToBurn`

Special withdrawal function for burning contributor tokens.

```vyper
@nonreentrant
@external
def withdrawContributorTokensToBurn(_user: address, _a: addys.Addys = empty(addys.Addys)) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | Contributor to withdraw from |
| `_a` | `addys.Addys` | Protocol addresses struct |

#### Access

Only callable by Human Resources contract

#### Special Behaviors
- **No Restrictions**: Bypasses lock periods and bad debt freezes
- **Full Withdrawal**: Withdraws entire RIPE token position
- **HR Recipient**: Tokens sent to HR contract for burning
- **Governance Impact**: Removes all governance points for position

### `transferContributorRipeTokens`

Transfers RIPE tokens from contributor to another user.

```vyper
@nonreentrant
@external
def transferContributorRipeTokens(
    _contributor: address,
    _toUser: address,
    _lockDuration: uint256,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_contributor` | `address` | Contributor transferring tokens |
| `_toUser` | `address` | Recipient of transferred tokens |
| `_lockDuration` | `uint256` | Lock duration for recipient |
| `_a` | `addys.Addys` | Protocol addresses struct |

#### Access

Only callable by Human Resources contract

#### Special Behaviors
- **Point Transfer**: Unlike regular transfers, governance points move with tokens
- **Full Transfer**: Transfers entire RIPE token position
- **Lock Assignment**: Recipient gets specified lock duration
- **HR Events**: Emits special contributor transfer event

## Lock Management Functions

### `adjustLock`

Extends lock duration for additional governance point bonuses.

```vyper
@external
def adjustLock(
    _user: address,
    _asset: address,
    _newLockDuration: uint256,
    _a: addys.Addys = empty(addys.Addys),
):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User adjusting lock |
| `_asset` | `address` | Asset to adjust lock for |
| `_newLockDuration` | `uint256` | New lock duration in blocks |
| `_a` | `addys.Addys` | Protocol addresses struct |

#### Access

Only callable by valid Ripe protocol addresses

#### Restrictions
- **Extension Only**: New unlock time must be later than current
- **Position Required**: User must have non-zero share balance
- **Terms Required**: Asset must have configured lock terms

#### Process Flow
1. **Full Update**: Accumulates all pending governance points
2. **Lootbox Update**: Updates deposit points for extended commitment
3. **Lock Extension**: Sets new unlock block (current + new duration)
4. **Event Emission**: Logs lock modification

#### Events Emitted

- `LockModified` - Contains user, asset, and new lock duration

#### Example Usage
```python
# Extend lock for maximum governance bonus
ripe_gov.adjustLock(
    user.address,
    ripe_token.address,
    BLOCKS_PER_TWO_YEARS,  # Extend to 2 years
    empty(addys.Addys),
    sender=user.address    # User extending their own lock
)
```

### `releaseLock`

Allows early exit from lock period with penalty fee.

```vyper
@external
def releaseLock(
    _user: address,
    _asset: address,
    _a: addys.Addys = empty(addys.Addys),
):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_user` | `address` | User releasing lock |
| `_asset` | `address` | Asset to release lock for |
| `_a` | `addys.Addys` | Protocol addresses struct |

#### Access

Only callable by valid Ripe protocol addresses

#### Smart Protection Logic
```vyper
# Protect users from costly exit during bad debt when they couldn't withdraw anyway
if staticcall Ledger(a.ledger).badDebt() != 0:
    assert not config.shouldFreezeWhenBadDebt # dev: saving user money
```

#### Exit Fee Calculation
```vyper
# Remove shares as penalty for early exit
sharesToRemove = userShares * exitFee / HUNDRED_PERCENT
```

#### Process Flow
1. **Protection Check**: Prevents costly exit when withdrawal would fail anyway
2. **Full Update**: Accumulates all pending governance points  
3. **Validation**: Ensures position is locked and exit is allowed
4. **Lootbox Update**: Updates points for lock release
5. **Fee Payment**: Burns shares equal to exit fee percentage
6. **Lock Removal**: Sets unlock time to 0 (immediately unlocked)

#### Events Emitted

- `LockReleased` - Contains user, asset, and exit fee charged

## Governance Point Functions

### `getLatestGovPoints`

Calculates accumulated governance points for a position.

```vyper
@view
@external
def getLatestGovPoints(
    _lastShares: uint256,
    _lastPointsUpdate: uint256,
    _unlock: uint256,
    _terms: cs.LockTerms,
    _weight: uint256,
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_lastShares` | `uint256` | Share balance at last update |
| `_lastPointsUpdate` | `uint256` | Block of last points update |
| `_unlock` | `uint256` | Unlock block number |
| `_terms` | `cs.LockTerms` | Lock term configuration |
| `_weight` | `uint256` | Asset weight percentage |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | New governance points earned since last update |

#### Calculation Formula
```vyper
# Base points = shares * time * weight
base_points = (shares / PRECISION) * (blocks_elapsed) * (weight / HUNDRED_PERCENT)

# Lock bonus points = base_points * lock_bonus_ratio  
lock_bonus = base_points * getLockBonusPoints(base_points, unlock, terms) / HUNDRED_PERCENT

# Total new points
total_points = base_points + lock_bonus
```

### `getLockBonusPoints`

Calculates additional points awarded for locked positions.

```vyper
@view
@external
def getLockBonusPoints(
    _points: uint256,
    _unlock: uint256,
    _terms: cs.LockTerms,
) -> uint256:
```

#### Lock Bonus Formula
```vyper
remaining_lock = unlock - current_block
effective_duration = min(remaining_lock, max_lock_duration)

if effective_duration > min_lock_duration:
    duration_ratio = (effective_duration - min_lock_duration) / (max_lock_duration - min_lock_duration)
    lock_bonus_ratio = max_lock_boost * duration_ratio
    bonus_points = base_points * lock_bonus_ratio / HUNDRED_PERCENT
```

#### Example Calculation
```python
# User has 1000 shares locked for 1 year with 50% max bonus
shares = 1000 * 10**18
blocks_elapsed = 100
unlock_block = current_block + BLOCKS_PER_YEAR
terms = LockTerms(
    minLockDuration=BLOCKS_PER_MONTH,
    maxLockDuration=BLOCKS_PER_TWO_YEARS,
    maxLockBoost=5000,  # 50.00%
    exitFee=500,        # 5.00%
    canExit=True
)

base_points = (shares // PRECISION) * blocks_elapsed  # = 1000 * 100 = 100,000
remaining_duration = BLOCKS_PER_YEAR
duration_ratio = (BLOCKS_PER_YEAR - BLOCKS_PER_MONTH) / (BLOCKS_PER_TWO_YEARS - BLOCKS_PER_MONTH)
# Approximately 0.48 for 1 year lock in 2 year range
lock_bonus_ratio = 5000 * 0.48 = 2400  # 24.00%
bonus_points = 100,000 * 2400 / 10000 = 24,000

total_new_points = 100,000 + 24,000 = 124,000
```

### `getWeightedLockOnTokenDeposit`

Calculates weighted lock duration when adding to existing position.

```vyper
@view
@external
def getWeightedLockOnTokenDeposit(
    _newShares: uint256,
    _newLockDuration: uint256,
    _lockTerms: cs.LockTerms,
    _prevShares: uint256,
    _prevUnlock: uint256,
) -> uint256:
```

#### Weighted Average Formula
```vyper
# Convert to normalized values
prev_normalized = prev_shares // PRECISION
new_normalized = new_shares // PRECISION

# Calculate previous remaining duration
prev_duration = prev_unlock - current_block (capped by max)

# Weighted average
weighted_duration = ((prev_normalized * prev_duration) + (new_normalized * new_lock_duration)) / (prev_normalized + new_normalized)

new_unlock = current_block + weighted_duration
```

### `updateUserGovPoints`

Manually updates governance points for a user across all assets.

```vyper
@external
def updateUserGovPoints(_user: address, _a: addys.Addys = empty(addys.Addys)):
```

#### Access

Only callable by valid Ripe protocol addresses

#### Process Flow
1. **Asset Iteration**: Loops through all user's assets in vault
2. **Points Update**: Accumulates pending points for each asset
3. **State Update**: Updates stored governance points
4. **Boardroom Notification**: Updates voting power

## Integration Support Functions

### `getVaultDataOnDeposit`

Provides vault data needed by Teller for deposit operations.

```vyper
@view
@external
def getVaultDataOnDeposit(_user: address, _asset: address) -> Vault.VaultDataOnDeposit:
```

Delegates to SharesVault for consistent vault data.

### `getUserLootBoxShare`

Returns governance point-based share for Lootbox reward calculations.

```vyper
@view
@external
def getUserLootBoxShare(_user: address, _asset: address) -> uint256:
```

#### Calculation
```vyper
# Base points from shares
base_points = last_shares // PRECISION

# Add lock bonus if applicable
if lock_terms_configured:
    lock_bonus = getLockBonusPoints(base_points, unlock, terms)
    return base_points + lock_bonus

return base_points
```

This ensures Lootbox rewards account for both deposit size and lock commitment.

### `getUserAssetAndAmountAtIndex`

Returns asset and amount at specific index for CreditEngine collateral calculations.

```vyper
@view
@external
def getUserAssetAndAmountAtIndex(_user: address, _index: uint256) -> (address, uint256):
```

Delegates to SharesVault for consistent asset valuation.

## Lock Terms Management

### `refreshUnlock`

Updates unlock time when lock terms change to protect users.

```vyper
@view
@external
def refreshUnlock(_prevUnlock: uint256, _newTerms: cs.LockTerms, _prevTerms: cs.LockTerms) -> uint256:
```

#### Protection Logic
```vyper
# Reset lock if key terms become unfavorable
if not areKeyTermsSame(new_terms, prev_terms):
    unlock = 0  # Immediately unlock to protect user

# Cap unlock by new max duration
return min(unlock, current_block + new_terms.maxLockDuration)
```

### `areKeyTermsSame`

Determines if lock terms changes are favorable or unfavorable to users.

```vyper
@view
@external
def areKeyTermsSame(_newTerms: cs.LockTerms, _prevTerms: cs.LockTerms) -> bool:
```

#### Unfavorable Changes (returns False)
- **Exit Removal**: `canExit` changes from True to False
- **Bonus Reduction**: `maxLockBoost` decreases
- **Duration Increase**: `minLockDuration` increases  
- **Fee Increase**: `exitFee` increases

#### User Protection
When terms become unfavorable, users' locks are automatically released to prevent being trapped by governance parameter changes.

## Events

### `RipeGovVaultDeposit`
Emitted on successful deposits with lock information.

### `RipeGovVaultWithdrawal`  
Emitted on withdrawals with depletion status.

### `RipeGovVaultBurnContributorTokens`
Emitted when HR burns contributor tokens.

### `RipeGovVaultTransfer`
Emitted on internal transfers (liquidations).

### `RipeTokensTransferred`
Emitted when HR transfers contributor tokens.

### `LockModified`
Emitted when user extends lock duration.

### `LockReleased`
Emitted when user exits early with fee.

## Security Considerations

### Access Controls
- **Teller Only**: Regular deposits restricted to Teller
- **HR Only**: Contributor management restricted to Human Resources
- **Valid Ripe Addresses**: Advanced functions restricted to protocol contracts
- **Liquidation Contracts**: Transfers restricted to AuctionHouse and CreditEngine

### Lock Period Enforcement
- **Withdrawal Blocking**: Strict enforcement of lock periods for regular withdrawals
- **Bad Debt Protection**: Additional freeze during protocol bad debt if configured
- **Smart Exit Protection**: Prevents costly early exits when withdrawal would fail anyway

### Governance Point Integrity
- **Proportional Penalties**: Point reduction proportional to share withdrawal
- **Time-Based Accrual**: Points only accumulate over time, not instantly
- **Lock Bonus Validation**: Lock bonuses based on remaining time, not initial lock
- **Terms Protection**: Automatic unlock when terms become unfavorable

### Economic Incentives
- **Long-Term Alignment**: Higher rewards for longer commitments
- **Exit Costs**: Economic penalty for early exit discourages gaming
- **Weighted Averaging**: Fair blending of multiple deposits with different locks

## Testing

For comprehensive test examples, see: [`tests/vaults/test_ripe_gov_vault.py`](../../tests/vaults/test_ripe_gov_vault.py)