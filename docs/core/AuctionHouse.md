# AuctionHouse Technical Documentation

[📄 View Source Code](../../contracts/core/AuctionHouse.vy)

## Overview

AuctionHouse is the liquidation engine for Ripe Protocol, executing multi-phase strategies to recover value from under-collateralized positions. It prioritizes minimal market impact through phased liquidations: first burning borrower's stablecoins, then swapping with stability pools, and finally running Dutch auctions.

**Core Functions**:
- **Phased Liquidations**: Burns GREEN/sGREEN → Stability pool swaps → Dutch auctions
- **Auction Management**: Time-based discounts from 0% to maximum, paid in GREEN
- **Keeper Rewards**: Incentivizes decentralized position monitoring with debt-based rewards

Built with transient storage optimization, AuctionHouse implements unified repayment formulas across all liquidation types. It integrates with [CreditEngine](CreditEngine.md), [StabilityPool](../vaults/StabilityPool.md), and [Ledger](../data/Ledger.md) for atomic execution while maintaining strict value flow accounting and configurable per-asset auction parameters.

## Architecture & Modules

AuctionHouse is built using a modular architecture with the following components:

### Addys Module

- **Location**: `contracts/modules/Addys.vy`
- **Purpose**: Provides protocol-wide address resolution
- **Documentation**: See [Addys Technical Documentation](../modules/Addys.md)
- **Key Features**:
  - Access to all protocol contract addresses
  - Validation of Switchboard authorization
  - Centralized address management
- **Exported Interface**: Address utilities via `addys.__interface__`

### DeptBasics Module

- **Location**: `contracts/modules/DeptBasics.vy`
- **Purpose**: Provides department-level functionality
- **Documentation**: See [DeptBasics Technical Documentation](../modules/DeptBasics.md)
- **Key Features**:
  - Pause mechanism for emergency stops
  - Green token minting capability (for keeper rewards)
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
|                        AuctionHouse Contract                           |
+------------------------------------------------------------------------+
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                   Liquidation Flow (3 Phases)                    |  |
|  |                                                                  |  |
|  |  Phase 1: Stability Pool Assets                                  |  |
|  |  - Check if user has stablecoin positions                       |  |
|  |  - Burn Green/sGreen as repayment                               |  |
|  |  - Transfer other stables to Endaoment                          |  |
|  |                                                                  |  |
|  |  Phase 2: Priority Liquidation Assets                           |  |
|  |  - Process assets in MissionControl priority order              |  |
|  |  - Swap with stability pools for instant liquidity              |  |
|  |  - Handle special asset configurations                          |  |
|  |                                                                  |  |
|  |  Phase 3: Remaining User Vaults                                 |  |
|  |  - Iterate through all user positions                           |  |
|  |  - Apply same liquidation logic                                 |  |
|  |  - Create auctions for unsold collateral                        |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                      Auction Mechanism                           |  |
|  |                                                                  |  |
|  |  Dutch Auction Design:                                           |  |
|  |  - Start Discount: e.g., 2% (buyer pays 98%)                    |  |
|  |  - Max Discount: e.g., 20% (buyer pays 80%)                     |  |
|  |  - Linear progression over auction duration                      |  |
|  |                                                                  |  |
|  |  Purchase Flow:                                                  |  |
|  |  1. Buyer provides Green tokens                                  |  |
|  |  2. Discount calculated based on time                            |  |
|  |  3. Collateral transferred at discounted price                   |  |
|  |  4. Green sent to CreditEngine for debt repayment               |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Transient Storage Cache                       |  |
|  |                                                                  |  |
|  |  Gas Optimizations:                                              |  |
|  |  - vaultAddrs: Cache vault addresses during liquidation         |  |
|  |  - assetLiqConfig: Cache liquidation configs per asset          |  |
|  |  - didHandleLiqAsset: Prevent duplicate processing              |  |
|  |  - userAssetForAuction: Track assets needing auctions           |  |
|  +------------------------------------------------------------------+  |
+------------------------------------------------------------------------+
                                    |
        +---------------------------+---------------------------+
        |                           |                           |
        v                           v                           v
+------------------+    +-------------------+    +------------------+
| CreditEngine     |    | StabilityPool     |    | Ledger           |
| * Debt updates   |    | * Asset swaps     |    | * User tracking  |
| * Interest calc  |    | * Green claims    |    | * Auction data   |
| * Repayments     |    | * Liquidity       |    | * Vault info     |
+------------------+    +-------------------+    +------------------+
        |                           |                           |
        v                           v                           v
+------------------+    +-------------------+    +------------------+
| MissionControl   |    | PriceDesk         |    | Teller           |
| * Liq configs    |    | * Asset pricing   |    | * Entry point    |
| * Auction params |    | * USD values      |    | * Access control |
| * Asset configs  |    | * Price feeds     |    | * User actions   |
+------------------+    +-------------------+    +------------------+
```

## Data Structures

### AuctionBuyConfig Struct

Configuration for auction purchase permissions:

```vyper
struct AuctionBuyConfig:
    canBuyInAuctionGeneral: bool      # General auction participation allowed
    canBuyInAuctionAsset: bool        # Asset-specific auction allowed
    isUserAllowed: bool               # User whitelist check
    canAnyoneDeposit: bool            # Allow deposits on behalf of others
```

### UserBorrowTerms Struct

User's borrowing parameters:

```vyper
struct UserBorrowTerms:
    collateralVal: uint256            # Total collateral value in USD
    totalMaxDebt: uint256             # Maximum allowed debt
    debtTerms: cs.DebtTerms           # Detailed debt parameters
```

### UserDebt Struct

Current debt state:

```vyper
struct UserDebt:
    amount: uint256                   # Current debt amount
    principal: uint256                # Original borrowed amount
    debtTerms: cs.DebtTerms           # Debt configuration
    lastTimestamp: uint256            # Last update timestamp
    inLiquidation: bool               # Liquidation status flag
```

### GenLiqConfig Struct

General liquidation configuration:

```vyper
struct GenLiqConfig:
    canLiquidate: bool                # Global liquidation toggle
    keeperFeeRatio: uint256           # Keeper reward percentage
    minKeeperFee: uint256             # Minimum keeper reward
    maxKeeperFee: uint256             # Maximum keeper reward
    ltvPaybackBuffer: uint256         # LTV restoration buffer
    genAuctionParams: cs.AuctionParams # Default auction parameters
    priorityLiqAssetVaults: DynArray[VaultData, PRIORITY_LIQ_VAULT_DATA]
    priorityStabVaults: DynArray[VaultData, MAX_STAB_VAULT_DATA]
```

### AssetLiqConfig Struct

Asset-specific liquidation configuration:

```vyper
struct AssetLiqConfig:
    hasConfig: bool                   # Has custom configuration
    shouldBurnAsPayment: bool         # Burn stablecoins for repayment
    shouldTransferToEndaoment: bool   # Send to Endaoment
    shouldSwapInStabPools: bool       # Allow stability pool swaps
    shouldAuctionInstantly: bool      # Create auctions immediately
    customAuctionParams: cs.AuctionParams # Custom auction settings
    specialStabPool: VaultData        # Preferred stability pool
```

### FungibleAuction Struct

Active auction data:

```vyper
struct FungibleAuction:
    liqUser: address                  # User being liquidated
    vaultId: uint256                  # Vault containing asset
    asset: address                    # Asset being auctioned
    startDiscount: uint256            # Initial discount percentage
    maxDiscount: uint256              # Maximum discount percentage
    startBlock: uint256               # Auction start block
    endBlock: uint256                 # Auction end block
    isActive: bool                    # Active status flag
```

## State Variables

### Transient Storage (Gas Optimization)

- `vaultAddrs: transient(HashMap[uint256, address])` - Cached vault addresses
- `assetLiqConfig: transient(HashMap[address, AssetLiqConfig])` - Cached asset configs
- `didHandleLiqAsset: transient(HashMap[address, HashMap[uint256, HashMap[address, bool]]])` - Processing tracker
- `didHandleVaultId: transient(HashMap[address, HashMap[uint256, bool]])` - Vault processing tracker
- `numUserAssetsForAuction: transient(HashMap[address, uint256])` - Auction asset counter
- `userAssetForAuction: transient(HashMap[address, HashMap[uint256, VaultData]])` - Auction asset data

### Constants

- `HUNDRED_PERCENT: uint256 = 100_00` - 100.00% in basis points
- `ONE_PERCENT: uint256 = 1_00` - 1.00% in basis points
- `MAX_STAB_VAULT_DATA: uint256 = 10` - Max stability vaults
- `PRIORITY_LIQ_VAULT_DATA: uint256 = 20` - Max priority assets
- `MAX_LIQ_USERS: uint256 = 50` - Max batch liquidations
- `MAX_AUCTIONS: uint256 = 20` - Max batch auctions

### Inherited State Variables

From [DeptBasics](../modules/DeptBasics.md):

- `isPaused: bool` - Department pause state
- `canMintGreen: bool` - Set to `True` for keeper rewards

## Constructor

### `__init__`

Initializes AuctionHouse with RipeHq reference and minting capabilities.

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
# Deploy AuctionHouse
auction_house = boa.load(
    "contracts/core/AuctionHouse.vy",
    ripe_hq.address
)
```

**Example Output**: Contract deployed with Green minting enabled for keeper rewards

## Liquidation Functions

### `liquidateUser`

Liquidates a single under-collateralized position.

```vyper
@external
def liquidateUser(
    _liqUser: address,
    _keeper: address,
    _wantsSavingsGreen: bool,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
```

#### Parameters

| Name                 | Type          | Description                 |
| -------------------- | ------------- | --------------------------- |
| `_liqUser`           | `address`     | User to liquidate           |
| `_keeper`            | `address`     | Keeper receiving rewards    |
| `_wantsSavingsGreen` | `bool`        | Receive rewards as sGreen   |
| `_a`                 | `addys.Addys` | Cached addresses (optional) |

#### Returns

| Type      | Description          |
| --------- | -------------------- |
| `uint256` | Keeper reward amount |

#### Access

Only callable by Teller contract

#### Events Emitted

- `LiquidateUser` - Complete liquidation details including fees, repayments, and auction starts
- `StabAssetBurntAsRepayment` - When Green/sGreen is burned for debt repayment (Phase 1)
- `CollateralSentToEndaoment` - When stablecoins are sent to Endaoment (Phase 1)
- `CollateralSwappedWithStabPool` - When collateral is swapped with stability pools (Phase 2)
- `FungibleAuctionUpdated` - When auctions are created for remaining collateral (Phase 3)

#### Example Usage

```python
# Keeper triggers liquidation
keeper_rewards = auction_house.liquidateUser(
    underwater_user.address,
    keeper.address,
    True,  # Want sGreen rewards
    sender=teller.address
)
```

**Example Output**: Executes multi-phase liquidation, returns keeper rewards

### `liquidateManyUsers`

Batch liquidates multiple positions in one transaction.

```vyper
@external
def liquidateManyUsers(
    _liqUsers: DynArray[address, MAX_LIQ_USERS],
    _keeper: address,
    _wantsSavingsGreen: bool,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
```

#### Parameters

| Name                 | Type                               | Description                 |
| -------------------- | ---------------------------------- | --------------------------- |
| `_liqUsers`          | `DynArray[address, MAX_LIQ_USERS]` | Users to liquidate (max 50) |
| `_keeper`            | `address`                          | Keeper receiving rewards    |
| `_wantsSavingsGreen` | `bool`                             | Receive rewards as sGreen   |
| `_a`                 | `addys.Addys`                      | Cached addresses (optional) |

#### Returns

| Type      | Description          |
| --------- | -------------------- |
| `uint256` | Total keeper rewards |

#### Access

Only callable by Teller contract

#### Events Emitted

- `LiquidateUser` - Complete liquidation details for each user including fees, repayments, and auction starts
- `StabAssetBurntAsRepayment` - When Green/sGreen is burned for debt repayment (Phase 1)
- `CollateralSentToEndaoment` - When stablecoins are sent to Endaoment (Phase 1)  
- `CollateralSwappedWithStabPool` - When collateral is swapped with stability pools (Phase 2)
- `FungibleAuctionUpdated` - When auctions are created for remaining collateral (Phase 3)

#### Example Usage

```python
# Batch liquidation
users = [user1.address, user2.address, user3.address]
total_rewards = auction_house.liquidateManyUsers(
    users,
    keeper.address,
    False,  # Want Green rewards
    sender=teller.address
)
```

### `calcAmountOfDebtToRepayDuringLiq`

Calculates the target debt repayment amount for liquidation.

```vyper
@view
@external
def calcAmountOfDebtToRepayDuringLiq(_user: address) -> uint256:
```

#### Parameters

| Name    | Type      | Description           |
| ------- | --------- | --------------------- |
| `_user` | `address` | User to calculate for |

#### Returns

| Type      | Description             |
| --------- | ----------------------- |
| `uint256` | Target repayment amount |

#### Access

Public view function

#### Example Usage

```python
# Check liquidation repayment target
target_repay = auction_house.calcAmountOfDebtToRepayDuringLiq(
    underwater_user.address
)
# Returns: Amount needed to restore healthy LTV
```

## Auction Management Functions

### `startAuction`

Manually starts an auction for liquidated collateral.

```vyper
@external
def startAuction(
    _liqUser: address,
    _liqVaultId: uint256,
    _liqAsset: address,
    _a: addys.Addys = empty(addys.Addys),
) -> bool:
```

#### Parameters

| Name          | Type          | Description                 |
| ------------- | ------------- | --------------------------- |
| `_liqUser`    | `address`     | User in liquidation         |
| `_liqVaultId` | `uint256`     | Vault containing asset      |
| `_liqAsset`   | `address`     | Asset to auction            |
| `_a`          | `addys.Addys` | Cached addresses (optional) |

#### Returns

| Type   | Description             |
| ------ | ----------------------- |
| `bool` | True if auction started |

#### Access

Only callable by Switchboard-registered contracts

#### Events Emitted

- `FungibleAuctionUpdated` - Auction parameters and status

#### Example Usage

```python
# Start auction for remaining collateral
success = auction_house.startAuction(
    liquidated_user.address,
    1,  # Vault ID
    weth.address,
    sender=auction_manager.address
)
```

### `startManyAuctions`

Batch starts multiple auctions.

```vyper
@external
def startManyAuctions(
    _auctions: DynArray[FungAuctionConfig, MAX_AUCTIONS],
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
```

#### Parameters

| Name        | Type                                        | Description                 |
| ----------- | ------------------------------------------- | --------------------------- |
| `_auctions` | `DynArray[FungAuctionConfig, MAX_AUCTIONS]` | Auction configurations      |
| `_a`        | `addys.Addys`                               | Cached addresses (optional) |

#### Returns

| Type      | Description                |
| --------- | -------------------------- |
| `uint256` | Number of auctions started |

#### Access

Only callable by Switchboard-registered contracts

### `pauseAuction`

Pauses an active auction.

```vyper
@external
def pauseAuction(
    _liqUser: address,
    _liqVaultId: uint256,
    _liqAsset: address,
    _a: addys.Addys = empty(addys.Addys),
) -> bool:
```

#### Parameters

| Name          | Type          | Description                 |
| ------------- | ------------- | --------------------------- |
| `_liqUser`    | `address`     | User in liquidation         |
| `_liqVaultId` | `uint256`     | Vault containing asset      |
| `_liqAsset`   | `address`     | Asset being auctioned       |
| `_a`          | `addys.Addys` | Cached addresses (optional) |

#### Returns

| Type   | Description            |
| ------ | ---------------------- |
| `bool` | True if auction paused |

#### Access

Only callable by Switchboard-registered contracts

#### Events Emitted

- `FungibleAuctionPaused` - Auction pause details

### `pauseManyAuctions`

Batch pauses multiple auctions.

```vyper
@external
def pauseManyAuctions(
    _auctions: DynArray[FungAuctionConfig, MAX_AUCTIONS],
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
```

#### Parameters

| Name        | Type                                        | Description                 |
| ----------- | ------------------------------------------- | --------------------------- |
| `_auctions` | `DynArray[FungAuctionConfig, MAX_AUCTIONS]` | Auctions to pause           |
| `_a`        | `addys.Addys`                               | Cached addresses (optional) |

#### Returns

| Type      | Description               |
| --------- | ------------------------- |
| `uint256` | Number of auctions paused |

#### Access

Only callable by Switchboard-registered contracts

### `canStartAuction`

Checks if an auction can be started.

```vyper
@view
@external
def canStartAuction(
    _liqUser: address,
    _liqVaultId: uint256,
    _liqAsset: address,
) -> bool:
```

#### Parameters

| Name          | Type      | Description      |
| ------------- | --------- | ---------------- |
| `_liqUser`    | `address` | User to check    |
| `_liqVaultId` | `uint256` | Vault ID         |
| `_liqAsset`   | `address` | Asset to auction |

#### Returns

| Type   | Description               |
| ------ | ------------------------- |
| `bool` | True if auction can start |

#### Access

Public view function

## Auction Purchase Functions

### `buyFungibleAuction`

Purchases collateral from a single auction using Green tokens.

```vyper
@external
def buyFungibleAuction(
    _liqUser: address,
    _vaultId: uint256,
    _asset: address,
    _greenAmount: uint256,
    _recipient: address,
    _caller: address,
    _shouldTransferBalance: bool,
    _shouldRefundSavingsGreen: bool,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
```

#### Parameters

| Name                        | Type          | Description                       |
| --------------------------- | ------------- | --------------------------------- |
| `_liqUser`                  | `address`     | User being liquidated             |
| `_vaultId`                  | `uint256`     | Vault containing asset            |
| `_asset`                    | `address`     | Asset to purchase                 |
| `_greenAmount`              | `uint256`     | Max Green to spend                |
| `_recipient`                | `address`     | Collateral recipient              |
| `_caller`                   | `address`     | Transaction initiator             |
| `_shouldTransferBalance`    | `bool`        | Transfer within vault vs withdraw |
| `_shouldRefundSavingsGreen` | `bool`        | Refund excess as sGreen           |
| `_a`                        | `addys.Addys` | Cached addresses (optional)       |

#### Returns

| Type      | Description        |
| --------- | ------------------ |
| `uint256` | Green tokens spent |

#### Access

Only callable by Teller contract

#### Events Emitted

- `FungAuctionPurchased` - Purchase details including amounts and debt status

#### Example Usage

```python
# Buy discounted collateral
green_spent = auction_house.buyFungibleAuction(
    liquidated_user.address,
    1,  # Vault ID
    weth.address,
    1000e18,  # 1000 Green max
    buyer.address,
    buyer.address,
    False,  # Withdraw to buyer
    True,   # Refund as sGreen
    sender=teller.address
)
```

**Example Output**: Transfers discounted collateral, returns Green spent

### `buyManyFungibleAuctions`

Batch purchases from multiple auctions.

```vyper
@external
def buyManyFungibleAuctions(
    _purchases: DynArray[FungAuctionPurchase, MAX_AUCTIONS],
    _greenAmount: uint256,
    _recipient: address,
    _caller: address,
    _shouldTransferBalance: bool,
    _shouldRefundSavingsGreen: bool,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
```

#### Parameters

| Name                        | Type                                          | Description                       |
| --------------------------- | --------------------------------------------- | --------------------------------- |
| `_purchases`                | `DynArray[FungAuctionPurchase, MAX_AUCTIONS]` | Purchase configurations           |
| `_greenAmount`              | `uint256`                                     | Total Green budget                |
| `_recipient`                | `address`                                     | Collateral recipient              |
| `_caller`                   | `address`                                     | Transaction initiator             |
| `_shouldTransferBalance`    | `bool`                                        | Transfer within vault vs withdraw |
| `_shouldRefundSavingsGreen` | `bool`                                        | Refund excess as sGreen           |
| `_a`                        | `addys.Addys`                                 | Cached addresses (optional)       |

#### Returns

| Type      | Description       |
| --------- | ----------------- |
| `uint256` | Total Green spent |

#### Access

Only callable by Teller contract

#### Example Usage

```python
# Batch auction purchases
purchases = [
    FungAuctionPurchase(user1, vault1, weth, 500e18),
    FungAuctionPurchase(user2, vault2, wbtc, 300e18)
]
total_spent = auction_house.buyManyFungibleAuctions(
    purchases,
    1000e18,  # Total budget
    buyer.address,
    buyer.address,
    False,
    False,
    sender=teller.address
)
```


## Key Mathematical Functions

### Unified Repayment Formula

The contract uses a single mathematical formula for calculating optimal repayment amounts across all liquidation types:

```
R = (D - T*C) * (1-F) / (1 - F - T)
```

Where:

- R = Repayment amount
- D = Current debt
- C = Collateral value
- T = Target LTV
- F = Liquidation fee ratio

This formula ensures:

- Consistent behavior across liquidation types
- Conservative approach (may slightly over-repay)
- Guaranteed debt health restoration
- Works for future liquidation mechanisms

### Auction Discount Calculation

Linear discount progression:

```
discount = startDiscount + (progress * (maxDiscount - startDiscount))
```

Where progress is the percentage of auction duration elapsed.

## Security Considerations

1. **Access Control**: Only Teller can initiate liquidations, preventing unauthorized triggers
2. **Transient Storage**: Uses EIP-1153 transient storage for gas optimization without state pollution
3. **Unified Math**: Single repayment formula prevents calculation inconsistencies
4. **Price Oracle Dependency**: Relies heavily on PriceDesk for accurate valuations
5. **Keeper MEV**: Liquidation rewards may be subject to MEV extraction
6. **Auction Timing**: Dutch auction discounts increase linearly, potentially allowing manipulation
7. **Multi-Phase Safety**: Phased liquidation approach minimizes market impact

## Testing

For comprehensive test examples, see: [`tests/core/test_auction_house.py`](../../tests/core/test_auction_house.py)
