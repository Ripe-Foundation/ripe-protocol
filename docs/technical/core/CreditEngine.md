# CreditEngine Technical Documentation

[📄 View Source Code](../../contracts/core/CreditEngine.vy)

## Overview

CreditEngine is the lending and borrowing powerhouse of Ripe Protocol, managing the entire credit lifecycle from collateralized borrowing to liquidations. It enables users to borrow GREEN stablecoins against deposited collateral while maintaining strict risk parameters and efficient capital utilization.

**Core Functions**:
- **Collateralized Borrowing**: Borrow GREEN against multi-asset collateral with weighted LTV calculations
- **Debt Management**: Track principal/interest separately with dynamic rates based on stability pool health
- **Collateral Redemption**: Allow GREEN holders to redeem unhealthy positions directly
- **Risk Controls**: Enforce debt ceilings, interval-based limits, and automatic liquidation triggers

CreditEngine implements advanced DeFi mechanics including position-weighted risk parameters, transient storage for gas optimization, atomic debt updates with compounding, and integration with boost systems. It ensures capital efficiency while maintaining robust protections against flash attacks and bad debt, working closely with [AuctionHouse](AuctionHouse.md) for liquidations, [Ledger](../data/Ledger.md) for debt tracking, and [Lootbox](Lootbox.md) for points updates.

## Architecture & Modules

CreditEngine is built using a modular architecture with the following components:

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
  - Green token minting capability (for borrowing)
  - No Ripe minting capability
- **Exported Interface**: Department basics via `deptBasics.__interface__`

### Module Initialization

```vyper
initializes: addys
initializes: deptBasics[addys := addys]
```

## System Architecture Diagram

```
+------------------------------------------------------------------------+
|                        CreditEngine Contract                           |
+------------------------------------------------------------------------+
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                      Borrowing Flow                              |  |
|  |                                                                  |  |
|  |  1. Calculate Borrowing Power                                    |  |
|  |     - Aggregate collateral across all vaults                     |  |
|  |     - Apply weighted LTV ratios                                  |  |
|  |     - Check interval limits                                      |  |
|  |                                                                  |  |
|  |  2. Validate Borrow Request                                      |  |
|  |     - User/global debt limits                                    |  |
|  |     - Minimum debt threshold                                     |  |
|  |     - Health factor check                                         |  |
|  |                                                                  |  |
|  |  3. Execute Borrow                                               |  |
|  |     - Update debt records                                         |  |
|  |     - Mint Green tokens                                          |  |
|  |     - Distribute daowry fees                                     |  |
|  |     - Send to user/savings/stability                             |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Weighted Debt Terms Calculation               |  |
|  |                                                                  |  |
|  |  For each user position:                                         |  |
|  |  - Asset A: $10k @ 80% LTV, 5% rate                              |  |
|  |  - Asset B: $5k @ 60% LTV, 8% rate                               |  |
|  |  - Asset C: $15k @ 70% LTV, 6% rate                              |  |
|  |                                                                  |  |
|  |  Weighted Average:                                                |  |
|  |  - LTV = (8k + 3k + 10.5k) / 30k = 71.7%                        |  |
|  |  - Rate = weighted by max debt                                   |  |
|  |  - All terms weighted similarly                                   |  |
|  +------------------------------------------------------------------+  |
+------------------------------------------------------------------------+
                                    |
        +---------------------------+---------------------------+
        |                           |                           |
        v                           v                           v
+------------------+    +-------------------+    +------------------+
| Ledger           |    | MissionControl    |    | Vault System     |
| * Debt tracking  |    | * Risk params     |    | * Collateral     |
| * Interest calc  |    | * Debt terms      |    | * User balances  |
| * User vaults    |    | * Rate configs    |    | * Asset tracking |
+------------------+    +-------------------+    +------------------+
        |                           |                           |
        v                           v                           v
+------------------+    +-------------------+    +------------------+
| Green Token      |    | PriceDesk         |    | LootBox          |
| * Mint/Burn      |    | * USD pricing     |    | * Points update  |
| * Stablecoin     |    | * Asset values    |    | * Rewards calc   |
+------------------+    +-------------------+    +------------------+
```

## Data Structures

### UserDebt Struct

Current debt state for a user:

```vyper
struct UserDebt:
    amount: uint256             # Total debt (principal + interest)
    principal: uint256          # Original borrowed amount
    debtTerms: cs.DebtTerms     # Current weighted debt terms
    lastTimestamp: uint256      # Last update timestamp
    inLiquidation: bool         # Liquidation status flag
```

### UserBorrowTerms Struct

Aggregated borrowing parameters across all positions:

```vyper
struct UserBorrowTerms:
    collateralVal: uint256      # Total USD collateral value
    totalMaxDebt: uint256       # Maximum borrowing power
    debtTerms: cs.DebtTerms     # Weighted average terms
```

### IntervalBorrow Struct

Tracks borrowing within time intervals:

```vyper
struct IntervalBorrow:
    start: uint256              # Interval start block
    amount: uint256             # Amount borrowed in interval
```

### BorrowConfig Struct

Protocol-wide borrowing configuration:

```vyper
struct BorrowConfig:
    canBorrow: bool                    # Global borrow toggle
    canBorrowForUser: bool             # Allow proxy borrowing
    numAllowedBorrowers: uint256       # Max borrower count
    maxBorrowPerInterval: uint256      # Per-interval limit
    numBlocksPerInterval: uint256      # Interval duration
    perUserDebtLimit: uint256          # Per-user cap
    globalDebtLimit: uint256           # Protocol-wide cap
    minDebtAmount: uint256             # Minimum position size
    isDaowryEnabled: bool              # Origination fee toggle
```

### CollateralRedemption Struct

Redemption request parameters:

```vyper
struct CollateralRedemption:
    user: address               # Position to redeem from
    vaultId: uint256           # Vault containing collateral
    asset: address             # Asset to redeem
    maxGreenAmount: uint256    # Max Green to spend
```

## State Variables

### Constants

- `ONE_YEAR: uint256 = 60 * 60 * 24 * 365` - Seconds in a year
- `HUNDRED_PERCENT: uint256 = 100_00` - 100.00% in basis points
- `DANGER_BLOCKS_DENOMINATOR: uint256 = 100_0000` - For danger calculations
- `ONE_PERCENT: uint256 = 1_00` - 1.00% in basis points
- `MAX_DEBT_UPDATES: uint256 = 25` - Batch update limit
- `MAX_COLLATERAL_REDEMPTIONS: uint256 = 20` - Batch redemption limit
- `STABILITY_POOL_ID: uint256 = 1` - Stability pool vault ID
- `CURVE_PRICES_ID: uint256 = 2` - Curve prices registry ID

### Inherited State Variables

From [DeptBasics](../modules/DeptBasics.md):

- `isPaused: bool` - Department pause state
- `canMintGreen: bool` - Set to `True` for borrowing

## Constructor

### `__init__`

Initializes CreditEngine with Green minting capability.

```vyper
@deploy
def __init__(_ripeHq: address):
```

#### Parameters

| Name      | Type      | Description             |
| --------- | --------- | ----------------------- |
| `_ripeHq` | `address` | RipeHq contract address |

#### Returns

_Constructor does not return any values_

#### Access

Called only during deployment

#### Example Usage

```python
# Deploy CreditEngine
credit_engine = boa.load(
    "contracts/core/CreditEngine.vy",
    ripe_hq.address
)
```

**Example Output**: Contract deployed with Green minting enabled

## Borrowing Functions

### `borrowForUser`

Borrows Green stablecoins against user's collateral.

```vyper
@external
def borrowForUser(
    _user: address,
    _greenAmount: uint256,
    _wantsSavingsGreen: bool,
    _shouldEnterStabPool: bool,
    _caller: address,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
```

#### Parameters

| Name                   | Type          | Description                    |
| ---------------------- | ------------- | ------------------------------ |
| `_user`                | `address`     | User borrowing                 |
| `_greenAmount`         | `uint256`     | Amount to borrow               |
| `_wantsSavingsGreen`   | `bool`        | Receive as Savings Green       |
| `_shouldEnterStabPool` | `bool`        | Auto-deposit to stability pool |
| `_caller`              | `address`     | Transaction initiator          |
| `_a`                   | `addys.Addys` | Cached addresses (optional)    |

#### Returns

| Type      | Description                |
| --------- | -------------------------- |
| `uint256` | Amount borrowed after fees |

#### Access

Only callable by Teller contract

#### Events Emitted

- `NewBorrow` - Complete borrowing details including:
  - Loan amount and daowry fee
  - Outstanding debt and collateral value
  - Maximum debt capacity
  - Global yield realized

#### Example Usage

```python
# Borrow 1000 Green as Savings Green
amount_received = credit_engine.borrowForUser(
    user.address,
    1000e18,
    True,   # Want sGreen
    False,  # Don't enter stability pool
    user.address,
    sender=teller.address
)
```

**Example Output**: Mints Green, deducts fees, delivers to user

### `getMaxBorrowAmount`

Calculates maximum borrowable amount for a user.

```vyper
@view
@external
def getMaxBorrowAmount(_user: address) -> uint256:
```

#### Parameters

| Name    | Type      | Description   |
| ------- | --------- | ------------- |
| `_user` | `address` | User to check |

#### Returns

| Type      | Description              |
| --------- | ------------------------ |
| `uint256` | Maximum borrowable Green |

#### Access

Public view function

#### Example Usage

```python
# Check borrowing capacity
max_borrow = credit_engine.getMaxBorrowAmount(user.address)
# Returns: 5000e18 (can borrow up to 5000 Green)
```

## Repayment Functions

### `repayForUser`

Repays user's debt with Green tokens.

```vyper
@external
def repayForUser(
    _user: address,
    _greenAmount: uint256,
    _shouldRefundSavingsGreen: bool,
    _caller: address,
    _a: addys.Addys = empty(addys.Addys),
) -> bool:
```

#### Parameters

| Name                        | Type          | Description                 |
| --------------------------- | ------------- | --------------------------- |
| `_user`                     | `address`     | User whose debt to repay    |
| `_greenAmount`              | `uint256`     | Amount to repay             |
| `_shouldRefundSavingsGreen` | `bool`        | Refund excess as sGreen     |
| `_caller`                   | `address`     | Transaction initiator       |
| `_a`                        | `addys.Addys` | Cached addresses (optional) |

#### Returns

| Type   | Description                  |
| ------ | ---------------------------- |
| `bool` | True if debt health restored |

#### Access

Only callable by Teller contract

#### Events Emitted

- `RepayDebt` - Repayment details including:
  - Repay amount and type
  - Refund amount if any
  - Updated debt status
  - Health factor status

#### Example Usage

```python
# Repay 500 Green of debt
is_healthy = credit_engine.repayForUser(
    user.address,
    500e18,
    True,  # Refund as sGreen
    user.address,
    sender=teller.address
)
```

### `repayDuringLiquidation`

Special repayment path for liquidations.

```vyper
@external
def repayDuringLiquidation(
    _liqUser: address,
    _userDebt: UserDebt,
    _repayValue: uint256,
    _newInterest: uint256,
    _a: addys.Addys = empty(addys.Addys),
) -> bool:
```

#### Parameters

| Name           | Type          | Description                 |
| -------------- | ------------- | --------------------------- |
| `_liqUser`     | `address`     | User being liquidated       |
| `_userDebt`    | `UserDebt`    | Current debt state          |
| `_repayValue`  | `uint256`     | Amount to repay             |
| `_newInterest` | `uint256`     | Accrued interest            |
| `_a`           | `addys.Addys` | Cached addresses (optional) |

#### Returns

| Type   | Description                  |
| ------ | ---------------------------- |
| `bool` | True if debt health restored |

#### Access

Only callable by AuctionHouse contract

### `repayDuringAuctionPurchase`

Repayment when collateral is purchased from auction.

```vyper
@external
def repayDuringAuctionPurchase(
    _liqUser: address,
    _repayValue: uint256,
    _a: addys.Addys = empty(addys.Addys)
) -> bool:
```

#### Parameters

| Name          | Type          | Description                 |
| ------------- | ------------- | --------------------------- |
| `_liqUser`    | `address`     | User being liquidated       |
| `_repayValue` | `uint256`     | Green from auction sale     |
| `_a`          | `addys.Addys` | Cached addresses (optional) |

#### Returns

| Type   | Description                  |
| ------ | ---------------------------- |
| `bool` | True if debt health restored |

#### Access

Only callable by AuctionHouse contract

## Collateral Redemption Functions

### `redeemCollateralFromMany`

Redeems collateral from multiple positions using Green.

```vyper
@external
def redeemCollateralFromMany(
    _redemptions: DynArray[CollateralRedemption, MAX_COLLATERAL_REDEMPTIONS],
    _greenAmount: uint256,
    _recipient: address,
    _caller: address,
    _shouldTransferBalance: bool,
    _shouldRefundSavingsGreen: bool,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
```

#### Parameters

| Name                        | Type                                 | Description                 |
| --------------------------- | ------------------------------------ | --------------------------- |
| `_redemptions`              | `DynArray[CollateralRedemption, 20]` | Redemption requests         |
| `_greenAmount`              | `uint256`                            | Total Green to spend        |
| `_recipient`                | `address`                            | Collateral recipient        |
| `_caller`                   | `address`                            | Transaction initiator       |
| `_shouldTransferBalance`    | `bool`                               | Transfer vs withdraw        |
| `_shouldRefundSavingsGreen` | `bool`                               | Refund excess as sGreen     |
| `_a`                        | `addys.Addys`                        | Cached addresses (optional) |

#### Returns

| Type      | Description       |
| --------- | ----------------- |
| `uint256` | Total Green spent |

#### Access

Only callable by Teller contract

#### Events Emitted

- `CollateralRedeemed` - Per redemption including:
  - User, vault, and asset details
  - Amount redeemed
  - Repay value applied
  - Health status

#### Example Usage

```python
# Redeem collateral from unhealthy positions
redemptions = [
    CollateralRedemption(user1, vault1, weth, 1000e18),
    CollateralRedemption(user2, vault1, wbtc, 500e18)
]
green_spent = credit_engine.redeemCollateralFromMany(
    redemptions,
    1500e18,  # Total budget
    redeemer.address,
    redeemer.address,
    False,    # Withdraw
    True,     # Refund as sGreen
    sender=teller.address
)
```

### `getMaxRedeemValue`

Calculates maximum redeemable value for a position.

```vyper
@view
@external
def getMaxRedeemValue(_user: address) -> uint256:
```

#### Parameters

| Name    | Type      | Description            |
| ------- | --------- | ---------------------- |
| `_user` | `address` | User position to check |

#### Returns

| Type      | Description                    |
| --------- | ------------------------------ |
| `uint256` | Maximum Green value redeemable |

#### Access

Public view function

## Borrowing Terms Functions

### `getUserBorrowTerms`

Gets aggregated borrowing terms across all user positions.

```vyper
@view
@external
def getUserBorrowTerms(
    _user: address,
    _shouldRaise: bool,
    _skipVaultId: uint256 = 0,
    _skipAsset: address = empty(address),
    _a: addys.Addys = empty(addys.Addys),
) -> UserBorrowTerms:
```

#### Parameters

| Name           | Type          | Description                 |
| -------------- | ------------- | --------------------------- |
| `_user`        | `address`     | User to analyze             |
| `_shouldRaise` | `bool`        | Raise on price errors       |
| `_skipVaultId` | `uint256`     | Vault to exclude (optional) |
| `_skipAsset`   | `address`     | Asset to exclude (optional) |
| `_a`           | `addys.Addys` | Cached addresses (optional) |

#### Returns

| Type              | Description                 |
| ----------------- | --------------------------- |
| `UserBorrowTerms` | Aggregated terms and values |

#### Access

Public view function

#### Example Usage

```python
# Get user's borrowing terms
terms = credit_engine.getUserBorrowTerms(
    user.address,
    True  # Raise on errors
)
# Returns: Weighted LTV, rates, collateral value
```

### `getCollateralValue`

Gets total USD value of user's collateral.

```vyper
@view
@external
def getCollateralValue(_user: address) -> uint256:
```

#### Parameters

| Name    | Type      | Description   |
| ------- | --------- | ------------- |
| `_user` | `address` | User to check |

#### Returns

| Type      | Description                   |
| --------- | ----------------------------- |
| `uint256` | Total collateral value in USD |

#### Access

Public view function

### `updateDebtForUser`

Manually recalculates and updates a user's debt state, including interest accrual and debt term weighting.

```vyper
@external
def updateDebtForUser(_user: address) -> bool:
```

#### Parameters

| Name    | Type      | Description               |
| ------- | --------- | ------------------------- |
| `_user` | `address` | User whose debt to update |

#### Returns

| Type   | Description               |
| ------ | ------------------------- |
| `bool` | True if update successful |

#### Access

Callable by any valid Ripe address (not just Teller or AuctionHouse)

#### Example Usage

```python
# Update user's debt state
success = credit_engine.updateDebtForUser(
    user.address,
    sender=keeper.address  # Any valid Ripe address
)
```

## Debt Health Check Functions

### `hasGoodDebtHealth`

Checks if a user's collateral value is sufficient to cover their debt based on the LTV.

```vyper
@view
@external
def hasGoodDebtHealth(_user: address) -> bool:
```

#### Parameters

| Name    | Type      | Description   |
| ------- | --------- | ------------- |
| `_user` | `address` | User to check |

#### Returns

| Type   | Description                            |
| ------ | -------------------------------------- |
| `bool` | True if user has healthy debt position |

#### Access

Public view function

#### Example Usage

```python
# Check if user position is healthy
is_healthy = credit_engine.hasGoodDebtHealth(user.address)
# Returns: True if collateral value > debt * LTV
```

### `canLiquidateUser`

Checks if a user's collateral value has fallen below their liquidation threshold.

```vyper
@view
@external
def canLiquidateUser(_user: address) -> bool:
```

#### Parameters

| Name    | Type      | Description   |
| ------- | --------- | ------------- |
| `_user` | `address` | User to check |

#### Returns

| Type   | Description                    |
| ------ | ------------------------------ |
| `bool` | True if user can be liquidated |

#### Access

Public view function

#### Example Usage

```python
# Check if user can be liquidated
can_liquidate = credit_engine.canLiquidateUser(user.address)
# Returns: True if collateral < liquidation threshold
```

### `canRedeemUserCollateral`

Checks if a user's collateral value has fallen below their redemption threshold.

```vyper
@view
@external
def canRedeemUserCollateral(_user: address) -> bool:
```

#### Parameters

| Name    | Type      | Description   |
| ------- | --------- | ------------- |
| `_user` | `address` | User to check |

#### Returns

| Type   | Description                               |
| ------ | ----------------------------------------- |
| `bool` | True if user's collateral can be redeemed |

#### Access

Public view function

#### Example Usage

```python
# Check if collateral can be redeemed
can_redeem = credit_engine.canRedeemUserCollateral(user.address)
# Returns: True if collateral < redemption threshold
```

## Threshold Getter Functions

### `getLiquidationThreshold`

Returns the USD collateral value at which a user becomes eligible for liquidation.

```vyper
@view
@external
def getLiquidationThreshold(_user: address) -> uint256:
```

#### Parameters

| Name    | Type      | Description   |
| ------- | --------- | ------------- |
| `_user` | `address` | User to check |

#### Returns

| Type      | Description                         |
| --------- | ----------------------------------- |
| `uint256` | USD value threshold for liquidation |

#### Access

Public view function

#### Example Usage

```python
# Get liquidation threshold
liq_threshold = credit_engine.getLiquidationThreshold(user.address)
# Returns: 110000000000000000000 ($110 if debt is $100)
```

### `getRedemptionThreshold`

Returns the USD collateral value at which a user's collateral becomes eligible for redemption.

```vyper
@view
@external
def getRedemptionThreshold(_user: address) -> uint256:
```

#### Parameters

| Name    | Type      | Description   |
| ------- | --------- | ------------- |
| `_user` | `address` | User to check |

#### Returns

| Type      | Description                        |
| --------- | ---------------------------------- |
| `uint256` | USD value threshold for redemption |

#### Access

Public view function

#### Example Usage

```python
# Get redemption threshold
redeem_threshold = credit_engine.getRedemptionThreshold(user.address)
# Returns: 105000000000000000000 ($105 if debt is $100)
```

## Dynamic Rate Functions

### `getDynamicBorrowRate`

Takes a base borrow rate and returns the final, adjusted rate after applying dynamic boosts based on market conditions.

```vyper
@view
@external
def getDynamicBorrowRate(_baseBorrowRate: uint256) -> uint256:
```

#### Parameters

| Name              | Type      | Description                         |
| ----------------- | --------- | ----------------------------------- |
| `_baseBorrowRate` | `uint256` | Base borrow rate before adjustments |

#### Returns

| Type      | Description                              |
| --------- | ---------------------------------------- |
| `uint256` | Adjusted borrow rate with dynamic boosts |

#### Access

Public view function

#### Example Usage

```python
# Get dynamic rate based on stability pool health
base_rate = 500  # 5%
dynamic_rate = credit_engine.getDynamicBorrowRate(base_rate)
# Returns: 700 (7% if stability pool in danger)
```

## Key Mathematical Functions

### Weighted Terms Calculation

The contract calculates weighted average terms across heterogeneous collateral:

```
For each position:
weight = maxDebt (based on asset LTV)

Weighted term = Σ(term_i * weight_i) / Σ(weight_i)
```

This ensures positions with higher borrowing power have proportionally greater influence on aggregate terms.

### Interest Accrual

Compound interest calculation:

```
timeElapsed = currentTime - lastUpdateTime
interestMultiplier = (borrowRate * timeElapsed) / ONE_YEAR
newInterest = principal * interestMultiplier / 100%
totalDebt = principal + accruedInterest + newInterest
```

### Health Factor

Position health calculation:

```
healthFactor = (collateralValue * 100%) / debtAmount
isHealthy = healthFactor >= (100% / LTV)
```

### Dynamic Borrow Rate

Adjusts rates based on stability pool health:

```
If pool in danger:
  boost = min(maxBoost, dangerBlocks * increasePerBlock)
  dynamicRate = min(maxRate, baseRate + boost)
```

## Security Considerations

1. **Access Control**: All critical functions are protected by RipeHq authorization checks
2. **Debt Manipulation**: Only authorized contracts can modify debt positions
3. **Interest Accrual**: Interest calculations use safe math to prevent overflows
4. **Liquidation Protection**: Positions can only be liquidated by AuctionHouse
5. **Time-based Attacks**: Uses block.timestamp for interest, subject to miner manipulation
6. **Reentrancy**: External calls follow checks-effects-interactions pattern
7. **Oracle Dependency**: Relies on PriceDesk for accurate collateral valuations

## Testing

For comprehensive test examples, see: [`tests/core/test_credit_engine.py`](../../tests/core/test_credit_engine.py)
