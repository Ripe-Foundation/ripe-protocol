# MissionControl Technical Documentation

[📄 View Source Code](../../contracts/data/MissionControl.vy)

## Overview

MissionControl is the central configuration hub for Ripe Protocol, storing all operational parameters, permissions, and behavioral rules. Every critical protocol decision - from asset deposits to liquidation strategies - is determined by configuration data stored here and accessed through its extensive query interface.

**Core Responsibilities**:
- **Global Configuration**: Protocol-wide permissions, user limits, and operational rules
- **Asset Configuration**: Per-asset settings for deposits, debt terms, LTVs, and liquidations
- **Delegation System**: User permission grants for borrowing, withdrawals, and rewards
- **Rewards Configuration**: Points allocation across borrowers, stakers, voters, and depositors
- **Advanced Features**: Priority vaults, stability pools, bond markets, and dynamic rates

MissionControl implements read-only access for queries with writes restricted to [Switchboard](../registries/Switchboard.md)-registered contracts. Extensive bundling functions package related configurations for efficient consumption, while automatic asset registration and validation ensure data integrity across the protocol. It serves all major protocol components including [CreditEngine](../core/CreditEngine.md), [AuctionHouse](../core/AuctionHouse.md), [PriceDesk](../registries/PriceDesk.md), and vault systems.

## Architecture & Modules

MissionControl is built using a modular architecture that provides foundational department functionality:

### Addys Module

- **Location**: `contracts/modules/Addys.vy`
- **Purpose**: Provides protocol-wide address resolution and validation
- **Documentation**: See [Addys Technical Documentation](../modules/Addys.md)
- **Key Features**:
  - Access to all protocol contract addresses
  - Validation that only Switchboard-registered contracts can modify configurations
  - Centralized address management
- **Exported Interface**: Address utilities via `addys.__interface__`

### DeptBasics Module

- **Location**: `contracts/modules/DeptBasics.vy`
- **Purpose**: Provides department-level basic functionality
- **Documentation**: See [DeptBasics Technical Documentation](../modules/DeptBasics.md)
- **Key Features**:
  - Pause mechanism for emergency stops
  - Department interface compliance
  - **No minting capabilities** (disabled for MissionControl)
- **Exported Interface**: Department basics via `deptBasics.__interface__`

### Module Initialization

```vyper
initializes: addys
initializes: deptBasics[addys := addys]
```

## System Architecture Diagram

```
+------------------------------------------------------------------------+
|                      MissionControl Contract                          |
+------------------------------------------------------------------------+
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Configuration Categories                      |  |
|  |                                                                  |  |
|  |  +----------------+ +----------------+ +----------------+       |  |
|  |  | Global Config  | | Asset Config   | | User Config    |       |  |
|  |  |                | |                | |                |       |  |
|  |  | * genConfig    | | * assetConfig  | * userConfig     |       |  |
|  |  | * genDebtConfig| | * assets[]     | * userDelegation |       |  |
|  |  | * hrConfig     | | * indexOfAsset | * ActionDelegation      |  |
|  |  | * ripeBondConfig| | * numAssets   |                |       |  |
|  |  +----------------+ +----------------+ +----------------+       |  |
|  |                                                                  |  |
|  |  +----------------+ +----------------+ +----------------+       |  |
|  |  | Rewards Config | | Vault Config   | | Access Control |       |  |
|  |  |                | |                | |                |       |  |
|  |  | * rewardsConfig| | * ripeGovVault | | * canPerform   |       |  |
|  |  | * totalPoints  | |   Config       | |   LiteAction   |       |  |
|  |  |   Allocs       | | * priorityLiq  | | * trainingWheels       |  |
|  |  |                | |   AssetVaults  | | * underscore   |       |  |
|  |  |                | | * priorityStab | |   Registry     |       |  |
|  |  |                | |   Vaults       | |                |       |  |
|  |  +----------------+ +----------------+ +----------------+       |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Configuration Query Interface                 |  |
|  |                                                                  |  |
|  |  Teller Operations:     Borrowing & Debt:     Liquidations:     |  |
|  |  * getTellerDeposit     * getBorrowConfig      * getGenLiq       |  |
|  |  * getTellerWithdraw    * getDebtTerms         * getAssetLiq     |  |
|  |  * getRedeemCollateral  * getRepayConfig       * getGenAuction   |  |
|  |                         * getDynamicBorrow     * getAuctionBuy   |  |
|  |                                                                  |  |
|  |  Stability Pools:       Rewards System:       Bonds & Prices:   |  |
|  |  * getStabPoolClaims    * getRewardsConfig     * getPurchaseRipe |  |
|  |  * getStabPoolRedeem    * getDepositPoints     * getPriceConfig  |  |
|  |  * getClaimLoot         * getTotalPointsAllocs * getPriceStale   |  |
|  +------------------------------------------------------------------+  |
+------------------------------------------------------------------------+
                                    |
        +---------------------------+---------------------------+
        |                           |                           |
        v                           v                           v
+------------------+    +-------------------+    +------------------+
| Switchboard      |    | Protocol          |    | Whitelist &      |
| Contracts        |    | Contracts         |    | Validation       |
| * Config updates |    | * Query configs   |    | * User permissions |
| * Write access   |    | * Read operations |    | * Asset whitelists |
| * Authorized by  |    | * Behavior based  |    | * Delegation      |
|   Switchboard    |    |   on MC settings  |    |   checking        |
+------------------+    +-------------------+    +------------------+
```

## Data Structures

### Configuration Bundles

#### TellerDepositConfig Struct

Complete deposit operation configuration:

```vyper
struct TellerDepositConfig:
    canDepositGeneral: bool           # Global deposit permission
    canDepositAsset: bool             # Asset-specific deposit permission
    doesVaultSupportAsset: bool       # Vault supports this asset
    isUserAllowed: bool               # User whitelist status
    perUserDepositLimit: uint256      # Individual deposit limit
    globalDepositLimit: uint256       # Protocol-wide deposit limit
    perUserMaxAssetsPerVault: uint256 # Max assets per vault per user
    perUserMaxVaults: uint256         # Max vaults per user
    canAnyoneDeposit: bool            # User allows anyone to deposit for them
    minDepositBalance: uint256        # Minimum required deposit
```

#### TellerWithdrawConfig Struct

Complete withdrawal operation configuration:

```vyper
struct TellerWithdrawConfig:
    canWithdrawGeneral: bool          # Global withdrawal permission
    canWithdrawAsset: bool            # Asset-specific withdrawal permission
    isUserAllowed: bool               # User whitelist status
    canWithdrawForUser: bool          # Caller can withdraw for user
    minDepositBalance: uint256        # Minimum balance to maintain
```

#### BorrowConfig Struct

Complete borrowing operation configuration:

```vyper
struct BorrowConfig:
    canBorrow: bool                   # Global borrowing permission
    canBorrowForUser: bool            # Caller can borrow for user
    numAllowedBorrowers: uint256      # Maximum number of borrowers
    maxBorrowPerInterval: uint256     # Maximum borrow amount per interval
    numBlocksPerInterval: uint256     # Interval length in blocks
    perUserDebtLimit: uint256         # Individual debt limit
    globalDebtLimit: uint256          # Protocol-wide debt limit
    minDebtAmount: uint256            # Minimum borrow amount
    isDaowryEnabled: bool             # Daowry feature enabled
```

#### GenLiqConfig Struct

Complete general liquidation configuration:

```vyper
struct GenLiqConfig:
    canLiquidate: bool                # Global liquidation permission
    keeperFeeRatio: uint256           # Liquidation keeper fee percentage
    minKeeperFee: uint256             # Minimum keeper fee amount
    maxKeeperFee: uint256             # Maximum keeper fee amount
    ltvPaybackBuffer: uint256         # LTV restoration buffer
    genAuctionParams: cs.AuctionParams # Default auction parameters
    priorityLiqAssetVaults: DynArray[VaultData, PRIORITY_VAULT_DATA] # Priority liquidation vaults
    priorityStabVaults: DynArray[VaultData, PRIORITY_VAULT_DATA]     # Priority stability vaults
```

#### AssetLiqConfig Struct

Asset-specific liquidation configuration:

```vyper
struct AssetLiqConfig:
    hasConfig: bool                   # Has custom liquidation config
    shouldBurnAsPayment: bool         # Burn asset as debt repayment
    shouldTransferToEndaoment: bool   # Transfer asset to [Endaoment](../core/Endaoment.md)
    shouldSwapInStabPools: bool       # Allow stability pool swaps
    shouldAuctionInstantly: bool      # Create auctions immediately
    customAuctionParams: cs.AuctionParams # Asset-specific auction params
    specialStabPool: VaultData        # Preferred stability pool
```

#### RewardsConfig Struct

Complete rewards system configuration:

```vyper
struct RewardsConfig:
    arePointsEnabled: bool            # Points system active
    ripePerBlock: uint256             # Ripe tokens minted per block
    borrowersAlloc: uint256           # Allocation to borrowers
    stakersAlloc: uint256             # Allocation to stakers
    votersAlloc: uint256              # Allocation to voters
    genDepositorsAlloc: uint256       # Allocation to depositors
    stakersPointsAllocTotal: uint256  # Total staker point allocations
    voterPointsAllocTotal: uint256    # Total voter point allocations
```

### Utility Structures

#### VaultData Struct

Vault identification and information:

```vyper
struct VaultData:
    vaultId: uint256                  # Registry ID of vault
    vaultAddr: address                # Vault contract address
    asset: address                    # Primary asset address
```

#### PriceConfig Struct

Price oracle configuration:

```vyper
struct PriceConfig:
    staleTime: uint256                # Maximum age for valid prices
    priorityPriceSourceIds: DynArray[uint256, MAX_PRIORITY_PRICE_SOURCES] # Priority oracle IDs
```

#### PurchaseRipeBondConfig Struct

Bond market configuration:

```vyper
struct PurchaseRipeBondConfig:
    asset: address                    # Bond payment asset
    amountPerEpoch: uint256           # Amount available per epoch
    canBond: bool                     # Bonds enabled
    minRipePerUnit: uint256           # Minimum Ripe per unit
    maxRipePerUnit: uint256           # Maximum Ripe per unit
    maxRipePerUnitLockBonus: uint256  # Maximum bonus for locking
    epochLength: uint256              # Epoch duration
    shouldAutoRestart: bool           # Auto restart epochs
    restartDelayBlocks: uint256       # Delay between epochs
    minLockDuration: uint256          # Minimum lock time
    maxLockDuration: uint256          # Maximum lock time
    canAnyoneBondForUser: bool        # Anyone can bond for user
    isUserAllowed: bool               # User whitelist status
```

## State Variables

### Global Configuration

- `genConfig: cs.GenConfig` - Protocol-wide operational settings
- `genDebtConfig: cs.GenDebtConfig` - Global debt and liquidation parameters
- `hrConfig: cs.HrConfig` - Human resources configuration
- `ripeBondConfig: cs.RipeBondConfig` - Bond market settings

### Asset Management

- `assetConfig: HashMap[address, cs.AssetConfig]` - Asset-specific configurations
- `assets: HashMap[uint256, address]` - Asset registry (index to address)
- `indexOfAsset: HashMap[address, uint256]` - Asset index lookup
- `numAssets: uint256` - Total registered assets

### User Configuration

- `userConfig: HashMap[address, cs.UserConfig]` - User-specific settings
- `userDelegation: HashMap[address, HashMap[address, cs.ActionDelegation]]` - Delegation permissions

### Rewards System

- `rewardsConfig: cs.RipeRewardsConfig` - Rewards distribution settings
- `totalPointsAllocs: TotalPointsAllocs` - Global point allocation tracking

### Vault Configuration

- `ripeGovVaultConfig: HashMap[address, cs.RipeGovVaultConfig]` - Governance vault settings
- `priorityLiqAssetVaults: DynArray[cs.VaultLite, PRIORITY_VAULT_DATA]` - Priority liquidation vaults
- `priorityStabVaults: DynArray[cs.VaultLite, PRIORITY_VAULT_DATA]` - Priority stability vaults

### Access Control

- `canPerformLiteAction: HashMap[address, bool]` - Lite action permissions
- `underscoreRegistry: address` - Underscore registry address
- `trainingWheels: address` - Training wheels contract address
- `shouldCheckLastTouch: bool` - One-action-per-block enforcement

### Price Configuration

- `priorityPriceSourceIds: DynArray[uint256, MAX_PRIORITY_PRICE_SOURCES]` - Priority oracle IDs

### Constants

- `MAX_VAULTS_PER_ASSET: uint256 = 10` - Maximum vaults per asset
- `MAX_PRIORITY_PRICE_SOURCES: uint256 = 10` - Maximum priority price sources
- `PRIORITY_VAULT_DATA: uint256 = 20` - Maximum priority vault entries
- `HUNDRED_PERCENT: uint256 = 100_00` - 100.00% in basis points

### Inherited State Variables

From [DeptBasics](../modules/DeptBasics.md):

- `isPaused: bool` - Department pause state
- `canMintGreen: bool` - Set to `False`
- `canMintRipe: bool` - Set to `False`

## Constructor

### `__init__`

Initializes MissionControl with RipeHq reference and default configurations.

```vyper
@deploy
def __init__(_ripeHq: address, _defaults: address):
```

#### Parameters

| Name        | Type      | Description                                             |
| ----------- | --------- | ------------------------------------------------------- |
| `_ripeHq`   | `address` | RipeHq contract address                                 |
| `_defaults` | `address` | Defaults contract for initial configurations (optional) |

#### Returns

_Constructor does not return any values_

#### Access

Called only during deployment

#### Example Usage

```python
# Deploy MissionControl with defaults
mission_control = boa.load(
    "contracts/data/MissionControl.vy",
    ripe_hq.address,
    defaults_contract.address
)

# Deploy without defaults
mission_control = boa.load(
    "contracts/data/MissionControl.vy",
    ripe_hq.address,
    empty(address)
)
```

**Example Output**: Contract deployed with no minting capabilities, asset registry initialized at index 1, default configurations loaded if provided

## Global Configuration Functions

### `setGeneralConfig`

Updates the protocol's global operational configuration.

```vyper
@external
def setGeneralConfig(_config: cs.GenConfig):
```

#### Parameters

| Name      | Type           | Description               |
| --------- | -------------- | ------------------------- |
| `_config` | `cs.GenConfig` | New general configuration |

#### Returns

_Function does not return any values_

#### Access

Only callable by [Switchboard](../registries/Switchboard.md)-registered contracts

#### Example Usage

```python
# Update global permissions
new_config = GenConfig(
    canDeposit=True,
    canWithdraw=True,
    canBorrow=True,
    canRepay=True,
    canLiquidate=True,
    canRedeemCollateral=True,
    canBuyInAuction=True,
    canClaimInStabPool=True,
    canRedeemInStabPool=True,
    canClaimLoot=True,
    priceStaleTime=3600,  # 1 hour
    perUserMaxVaults=10,
    perUserMaxAssetsPerVault=5
)

mission_control.setGeneralConfig(
    new_config,
    sender=config_manager.address  # Must be in Switchboard
)
```

### `setGeneralDebtConfig`

Updates global debt and liquidation parameters.

```vyper
@external
def setGeneralDebtConfig(_config: cs.GenDebtConfig):
```

#### Parameters

| Name      | Type               | Description            |
| --------- | ------------------ | ---------------------- |
| `_config` | `cs.GenDebtConfig` | New debt configuration |

#### Returns

_Function does not return any values_

#### Access

Only callable by [Switchboard](../registries/Switchboard.md)-registered contracts

#### Example Usage

```python
# Update debt parameters
debt_config = GenDebtConfig(
    numAllowedBorrowers=1000,
    maxBorrowPerInterval=1000000_000000000000000000,  # 1M tokens
    numBlocksPerInterval=7200,  # ~1 day
    perUserDebtLimit=100000_000000000000000000,  # 100K limit
    globalDebtLimit=50000000_000000000000000000,  # 50M total
    minDebtAmount=1000_000000000000000000,  # 1K minimum
    ltvPaybackBuffer=500,  # 5% buffer
    keeperFeeRatio=300,  # 3% keeper fee
    minKeeperFee=100_000000000000000000,  # 100 min fee
    maxKeeperFee=10000_000000000000000000  # 10K max fee
)

mission_control.setGeneralDebtConfig(
    debt_config,
    sender=config_manager.address
)
```

### `setHrConfig`

Updates human resources configuration.

```vyper
@external
def setHrConfig(_config: cs.HrConfig):
```

#### Parameters

| Name      | Type          | Description          |
| --------- | ------------- | -------------------- |
| `_config` | `cs.HrConfig` | New HR configuration |

#### Access

Only callable by [Switchboard](../registries/Switchboard.md)-registered contracts

### `setRipeBondConfig`

Updates bond market configuration.

```vyper
@external
def setRipeBondConfig(_config: cs.RipeBondConfig):
```

#### Parameters

| Name      | Type                | Description            |
| --------- | ------------------- | ---------------------- |
| `_config` | `cs.RipeBondConfig` | New bond configuration |

#### Access

Only callable by [Switchboard](../registries/Switchboard.md)-registered contracts

## Asset Configuration Functions

### `setAssetConfig`

Updates configuration for a specific asset, automatically registering it if new.

```vyper
@external
def setAssetConfig(_asset: address, _config: cs.AssetConfig):
```

#### Parameters

| Name      | Type             | Description         |
| --------- | ---------------- | ------------------- |
| `_asset`  | `address`        | Asset address       |
| `_config` | `cs.AssetConfig` | Asset configuration |

#### Returns

_Function does not return any values_

#### Access

Only callable by [Switchboard](../registries/Switchboard.md)-registered contracts

#### Example Usage

```python
# Configure USDC asset
usdc_config = AssetConfig(
    canDeposit=True,
    canWithdraw=True,
    canRedeemCollateral=True,
    canBuyInAuction=True,
    canClaimInStabPool=True,
    canRedeemInStabPool=True,
    vaultIds=[1, 2],  # Supported vaults
    debtTerms=DebtTerms(
        baseRate=200,  # 2% base rate
        maxLtv=8000,   # 80% max LTV
        liqThreshold=8500  # 85% liquidation threshold
    ),
    perUserDepositLimit=1000000_000000,  # 1M USDC limit
    globalDepositLimit=100000000_000000,  # 100M USDC global
    minDepositBalance=100_000000,  # 100 USDC minimum
    stakersPointsAlloc=1000,  # Point allocation
    voterPointsAlloc=500,
    whitelist=empty(address),  # No whitelist
    shouldBurnAsPayment=True,
    shouldTransferToEndaoment=False,
    shouldSwapInStabPools=True,
    shouldAuctionInstantly=False
)

mission_control.setAssetConfig(
    usdc.address,
    usdc_config,
    sender=config_manager.address
)
```

### `deregisterAsset`

Removes an asset from the registry.

```vyper
@external
def deregisterAsset(_asset: address) -> bool:
```

#### Parameters

| Name     | Type      | Description                 |
| -------- | --------- | --------------------------- |
| `_asset` | `address` | Asset address to deregister |

#### Returns

| Type   | Description                       |
| ------ | --------------------------------- |
| `bool` | True if successfully deregistered |

#### Access

Only callable by [Switchboard](../registries/Switchboard.md)-registered contracts

#### Example Usage

```python
# Deregister deprecated asset
success = mission_control.deregisterAsset(
    deprecated_token.address,
    sender=config_manager.address
)
```

## User Configuration Functions

### `setUserConfig`

Updates a user's personal configuration settings.

```vyper
@external
def setUserConfig(_user: address, _config: cs.UserConfig):
```

#### Parameters

| Name      | Type            | Description        |
| --------- | --------------- | ------------------ |
| `_user`   | `address`       | User address       |
| `_config` | `cs.UserConfig` | User configuration |

#### Access

Only callable by [Switchboard](../registries/Switchboard.md)-registered contracts or Teller

#### Example Usage

```python
# Update user permissions
user_config = UserConfig(
    canAnyoneDeposit=True,   # Allow deposits on behalf
    canAnyoneRepayDebt=True, # Allow debt repayment
    canAnyoneBondForUser=False  # Restrict bond purchases
)

mission_control.setUserConfig(
    user.address,
    user_config,
    sender=teller.address
)
```

### `setUserDelegation`

Sets delegation permissions allowing another address to act on behalf of a user.

```vyper
@external
def setUserDelegation(_user: address, _delegate: address, _config: cs.ActionDelegation):
```

#### Parameters

| Name        | Type                  | Description                  |
| ----------- | --------------------- | ---------------------------- |
| `_user`     | `address`             | User granting delegation     |
| `_delegate` | `address`             | Address receiving delegation |
| `_config`   | `cs.ActionDelegation` | Delegation permissions       |

#### Access

Only callable by [Switchboard](../registries/Switchboard.md)-registered contracts or Teller

#### Example Usage

```python
# Grant delegation to trading bot
delegation = ActionDelegation(
    canWithdraw=True,        # Can withdraw user's funds
    canBorrow=True,          # Can borrow on behalf
    canClaimLoot=True,       # Can claim rewards
    canClaimFromStabPool=False  # Cannot claim from stability pool
)

mission_control.setUserDelegation(
    user.address,
    trading_bot.address,
    delegation,
    sender=teller.address
)
```

## Rewards Configuration Functions

### `setRipeRewardsConfig`

Updates the Ripe token rewards distribution configuration.

```vyper
@external
def setRipeRewardsConfig(_config: cs.RipeRewardsConfig):
```

#### Parameters

| Name      | Type                   | Description           |
| --------- | ---------------------- | --------------------- |
| `_config` | `cs.RipeRewardsConfig` | Rewards configuration |

#### Access

Only callable by [Switchboard](../registries/Switchboard.md)-registered contracts

#### Example Usage

```python
# Update rewards distribution
rewards_config = RipeRewardsConfig(
    arePointsEnabled=True,
    ripePerBlock=100_000000000000000000,  # 100 RIPE per block
    borrowersAlloc=2500,      # 25% to borrowers
    stakersAlloc=4000,        # 40% to stakers
    votersAlloc=1500,         # 15% to voters
    genDepositorsAlloc=2000,  # 20% to depositors
    autoStakeRatio=5000,      # 50% auto-staked
    autoStakeDurationRatio=7500,  # 75% of max duration
    stabPoolRipePerDollarClaimed=1_000000000000000000  # 1 RIPE per $
)

mission_control.setRipeRewardsConfig(
    rewards_config,
    sender=config_manager.address
)
```

## Vault Configuration Functions

### `setRipeGovVaultConfig`

Configures governance vault parameters for a specific asset.

```vyper
@external
def setRipeGovVaultConfig(
    _asset: address,
    _assetWeight: uint256,
    _shouldFreezeWhenBadDebt: bool,
    _lockTerms: cs.LockTerms,
):
```

#### Parameters

| Name                       | Type           | Description                 |
| -------------------------- | -------------- | --------------------------- |
| `_asset`                   | `address`      | Asset address               |
| `_assetWeight`             | `uint256`      | Voting weight of asset      |
| `_shouldFreezeWhenBadDebt` | `bool`         | Freeze when bad debt exists |
| `_lockTerms`               | `cs.LockTerms` | Lock duration parameters    |

#### Access

Only callable by [Switchboard](../registries/Switchboard.md)-registered contracts

### `setPriorityLiqAssetVaults`

Sets priority vaults for liquidation asset processing.

```vyper
@external
def setPriorityLiqAssetVaults(_priorityLiqAssetVaults: DynArray[cs.VaultLite, PRIORITY_VAULT_DATA]):
```

#### Parameters

| Name                      | Type                                          | Description         |
| ------------------------- | --------------------------------------------- | ------------------- |
| `_priorityLiqAssetVaults` | `DynArray[cs.VaultLite, PRIORITY_VAULT_DATA]` | Priority vault list |

#### Access

Only callable by [Switchboard](../registries/Switchboard.md)-registered contracts

### `setPriorityStabVaults`

Sets priority vaults for stability pool operations.

```vyper
@external
def setPriorityStabVaults(_priorityStabVaults: DynArray[cs.VaultLite, PRIORITY_VAULT_DATA]):
```

#### Parameters

| Name                  | Type                                          | Description                   |
| --------------------- | --------------------------------------------- | ----------------------------- |
| `_priorityStabVaults` | `DynArray[cs.VaultLite, PRIORITY_VAULT_DATA]` | Priority stability vault list |

#### Access

Only callable by [Switchboard](../registries/Switchboard.md)-registered contracts

## Access Control Functions

### `setCanPerformLiteAction`

Grants or revokes permission for lite actions.

```vyper
@external
def setCanPerformLiteAction(_user: address, _canDo: bool):
```

#### Parameters

| Name     | Type      | Description                   |
| -------- | --------- | ----------------------------- |
| `_user`  | `address` | User address                  |
| `_canDo` | `bool`    | Permission to grant or revoke |

#### Access

Only callable by [Switchboard](../registries/Switchboard.md)-registered contracts

### `setTrainingWheels`

Updates the training wheels contract address.

```vyper
@external
def setTrainingWheels(_trainingWheels: address):
```

#### Parameters

| Name              | Type      | Description                      |
| ----------------- | --------- | -------------------------------- |
| `_trainingWheels` | `address` | Training wheels contract address |

#### Access

Only callable by [Switchboard](../registries/Switchboard.md)-registered contracts

### `setUnderscoreRegistry`

Updates the underscore registry address.

```vyper
@external
def setUnderscoreRegistry(_underscoreRegistry: address):
```

#### Parameters

| Name                  | Type      | Description                 |
| --------------------- | --------- | --------------------------- |
| `_underscoreRegistry` | `address` | Underscore registry address |

#### Access

Only callable by [Switchboard](../registries/Switchboard.md)-registered contracts

### `setPriorityPriceSourceIds`

Sets the priority order for price sources.

```vyper
@external
def setPriorityPriceSourceIds(_priorityIds: DynArray[uint256, MAX_PRIORITY_PRICE_SOURCES]):
```

#### Parameters

| Name           | Type                                            | Description                      |
| -------------- | ----------------------------------------------- | -------------------------------- |
| `_priorityIds` | `DynArray[uint256, MAX_PRIORITY_PRICE_SOURCES]` | Ordered list of price source IDs |

#### Access

Only callable by [Switchboard](../registries/Switchboard.md)-registered contracts

### `setShouldCheckLastTouch`

Enables or disables one-action-per-block enforcement.

```vyper
@external
def setShouldCheckLastTouch(_shouldCheck: bool):
```

#### Parameters

| Name           | Type   | Description                             |
| -------------- | ------ | --------------------------------------- |
| `_shouldCheck` | `bool` | Whether to enforce one-action-per-block |

#### Access

Only callable by [Switchboard](../registries/Switchboard.md)-registered contracts

## Asset Query Functions

### `isSupportedAsset`

Checks if an asset is registered in the protocol.

```vyper
@view
@external
def isSupportedAsset(_asset: address) -> bool:
```

#### Parameters

| Name     | Type      | Description            |
| -------- | --------- | ---------------------- |
| `_asset` | `address` | Asset address to check |

#### Returns

| Type   | Description                |
| ------ | -------------------------- |
| `bool` | True if asset is supported |

#### Access

Public view function

#### Example Usage

```python
# Check asset support
is_supported = mission_control.isSupportedAsset(usdc.address)
# Returns: True if USDC is configured
```

### `isSupportedAssetInVault`

Checks if an asset is supported in a specific vault.

```vyper
@view
@external
def isSupportedAssetInVault(_vaultId: uint256, _asset: address) -> bool:
```

#### Parameters

| Name       | Type      | Description   |
| ---------- | --------- | ------------- |
| `_vaultId` | `uint256` | Vault ID      |
| `_asset`   | `address` | Asset address |

#### Returns

| Type   | Description                         |
| ------ | ----------------------------------- |
| `bool` | True if asset is supported in vault |

#### Access

Public view function

### `getNumAssets`

Returns the number of registered assets.

```vyper
@view
@external
def getNumAssets() -> uint256:
```

#### Returns

| Type      | Description                 |
| --------- | --------------------------- |
| `uint256` | Number of registered assets |

#### Access

Public view function

### `getFirstVaultIdForAsset`

Returns the first vault ID that supports an asset.

```vyper
@view
@external
def getFirstVaultIdForAsset(_asset: address) -> uint256:
```

#### Parameters

| Name     | Type      | Description   |
| -------- | --------- | ------------- |
| `_asset` | `address` | Asset address |

#### Returns

| Type      | Description                                   |
| --------- | --------------------------------------------- |
| `uint256` | First vault ID (0 if no vaults support asset) |

#### Access

Public view function

## Teller Configuration Functions

### `getTellerDepositConfig`

Returns complete configuration for deposit operations.

```vyper
@view
@external
def getTellerDepositConfig(_vaultId: uint256, _asset: address, _user: address) -> TellerDepositConfig:
```

#### Parameters

| Name       | Type      | Description         |
| ---------- | --------- | ------------------- |
| `_vaultId` | `uint256` | Target vault ID     |
| `_asset`   | `address` | Asset to deposit    |
| `_user`    | `address` | User making deposit |

#### Returns

| Type                  | Description                           |
| --------------------- | ------------------------------------- |
| `TellerDepositConfig` | Complete deposit configuration bundle |

#### Access

Public view function

#### Example Usage

```python
# Get deposit configuration
deposit_config = mission_control.getTellerDepositConfig(
    1,  # Vault ID
    usdc.address,
    user.address
)

# Check if deposit is allowed
if (deposit_config.canDepositGeneral and
    deposit_config.canDepositAsset and
    deposit_config.doesVaultSupportAsset and
    deposit_config.isUserAllowed):
    # Proceed with deposit
```

### `getTellerWithdrawConfig`

Returns complete configuration for withdrawal operations.

```vyper
@view
@external
def getTellerWithdrawConfig(_asset: address, _user: address, _caller: address) -> TellerWithdrawConfig:
```

#### Parameters

| Name      | Type      | Description                   |
| --------- | --------- | ----------------------------- |
| `_asset`  | `address` | Asset to withdraw             |
| `_user`   | `address` | User owning the funds         |
| `_caller` | `address` | Address initiating withdrawal |

#### Returns

| Type                   | Description                              |
| ---------------------- | ---------------------------------------- |
| `TellerWithdrawConfig` | Complete withdrawal configuration bundle |

#### Access

Public view function

## Borrowing Configuration Functions

### `getDebtTerms`

Returns debt terms for a specific asset.

```vyper
@view
@external
def getDebtTerms(_asset: address) -> cs.DebtTerms:
```

#### Parameters

| Name     | Type      | Description              |
| -------- | --------- | ------------------------ |
| `_asset` | `address` | Collateral asset address |

#### Returns

| Type           | Description                             |
| -------------- | --------------------------------------- |
| `cs.DebtTerms` | Debt parameters including rates and LTV |

#### Access

Public view function

### `getBorrowConfig`

Returns complete borrowing configuration.

```vyper
@view
@external
def getBorrowConfig(_user: address, _caller: address) -> BorrowConfig:
```

#### Parameters

| Name      | Type      | Description               |
| --------- | --------- | ------------------------- |
| `_user`   | `address` | User to borrow for        |
| `_caller` | `address` | Address initiating borrow |

#### Returns

| Type           | Description                             |
| -------------- | --------------------------------------- |
| `BorrowConfig` | Complete borrowing configuration bundle |

#### Access

Public view function

### `maxLtvDeviation`

Returns the maximum allowed LTV deviation.

```vyper
@view
@external
def maxLtvDeviation() -> uint256:
```

#### Returns

| Type      | Description                           |
| --------- | ------------------------------------- |
| `uint256` | Maximum LTV deviation in basis points |

#### Access

Public view function

### `getRepayConfig`

Returns repayment configuration for a user.

```vyper
@view
@external
def getRepayConfig(_user: address) -> RepayConfig:
```

#### Parameters

| Name    | Type      | Description  |
| ------- | --------- | ------------ |
| `_user` | `address` | User address |

#### Returns

| Type          | Description             |
| ------------- | ----------------------- |
| `RepayConfig` | Repayment configuration |

#### Access

Public view function

## Liquidation Configuration Functions

### `getGenLiqConfig`

Returns complete general liquidation configuration.

```vyper
@view
@external
def getGenLiqConfig() -> GenLiqConfig:
```

#### Returns

| Type           | Description                                             |
| -------------- | ------------------------------------------------------- |
| `GenLiqConfig` | Complete liquidation configuration with priority vaults |

#### Access

Public view function

#### Example Usage

```python
# Get liquidation configuration
liq_config = mission_control.getGenLiqConfig()

# Check if liquidations are enabled
if liq_config.canLiquidate:
    # Process liquidation with keeper fee
    keeper_fee = min(
        liq_config.maxKeeperFee,
        max(liq_config.minKeeperFee, debt * liq_config.keeperFeeRatio // 10000)
    )
```

### `getAssetLiqConfig`

Returns asset-specific liquidation configuration.

```vyper
@view
@external
def getAssetLiqConfig(_asset: address) -> AssetLiqConfig:
```

#### Parameters

| Name     | Type      | Description   |
| -------- | --------- | ------------- |
| `_asset` | `address` | Asset address |

#### Returns

| Type             | Description                              |
| ---------------- | ---------------------------------------- |
| `AssetLiqConfig` | Asset-specific liquidation configuration |

#### Access

Public view function

### `getGenAuctionParams`

Returns general auction parameters.

```vyper
@view
@external
def getGenAuctionParams() -> cs.AuctionParams:
```

#### Returns

| Type               | Description                |
| ------------------ | -------------------------- |
| `cs.AuctionParams` | Default auction parameters |

#### Access

Public view function

### `getRedeemCollateralConfig`

Returns configuration for collateral redemption.

```vyper
@view
@external
def getRedeemCollateralConfig(_asset: address, _recipient: address) -> RedeemCollateralConfig:
```

#### Parameters

| Name         | Type      | Description       |
| ------------ | --------- | ----------------- |
| `_asset`     | `address` | Asset to redeem   |
| `_recipient` | `address` | Recipient address |

#### Returns

| Type                     | Description                         |
| ------------------------ | ----------------------------------- |
| `RedeemCollateralConfig` | Collateral redemption configuration |

#### Access

Public view function

### `getLtvPaybackBuffer`

Returns the LTV payback buffer.

```vyper
@view
@external
def getLtvPaybackBuffer() -> uint256:
```

#### Returns

| Type      | Description                        |
| --------- | ---------------------------------- |
| `uint256` | LTV payback buffer in basis points |

#### Access

Public view function

### `getAuctionBuyConfig`

Returns configuration for auction purchases.

```vyper
@view
@external
def getAuctionBuyConfig(_asset: address, _recipient: address) -> AuctionBuyConfig:
```

#### Parameters

| Name         | Type      | Description           |
| ------------ | --------- | --------------------- |
| `_asset`     | `address` | Asset being auctioned |
| `_recipient` | `address` | Purchase recipient    |

#### Returns

| Type               | Description                    |
| ------------------ | ------------------------------ |
| `AuctionBuyConfig` | Auction purchase configuration |

#### Access

Public view function

## Stability Pool Configuration Functions

### `getStabPoolClaimsConfig`

Returns configuration for stability pool claims.

```vyper
@view
@external
def getStabPoolClaimsConfig(_claimAsset: address, _claimer: address, _caller: address, _ripeToken: address) -> StabPoolClaimsConfig:
```

#### Parameters

| Name          | Type      | Description              |
| ------------- | --------- | ------------------------ |
| `_claimAsset` | `address` | Asset being claimed      |
| `_claimer`    | `address` | User claiming rewards    |
| `_caller`     | `address` | Address initiating claim |
| `_ripeToken`  | `address` | Ripe token address       |

#### Returns

| Type                   | Description                         |
| ---------------------- | ----------------------------------- |
| `StabPoolClaimsConfig` | Stability pool claims configuration |

#### Access

Public view function

### `getStabPoolRedemptionsConfig`

Returns configuration for stability pool redemptions.

```vyper
@view
@external
def getStabPoolRedemptionsConfig(_asset: address, _recipient: address) -> StabPoolRedemptionsConfig:
```

#### Parameters

| Name         | Type      | Description       |
| ------------ | --------- | ----------------- |
| `_asset`     | `address` | Asset to redeem   |
| `_recipient` | `address` | Recipient address |

#### Returns

| Type                        | Description                             |
| --------------------------- | --------------------------------------- |
| `StabPoolRedemptionsConfig` | Stability pool redemption configuration |

#### Access

Public view function

## Rewards Query Functions

### `getClaimLootConfig`

Returns configuration for loot (rewards) claiming.

```vyper
@view
@external
def getClaimLootConfig(_user: address, _caller: address, _ripeToken: address) -> ClaimLootConfig:
```

#### Parameters

| Name         | Type      | Description              |
| ------------ | --------- | ------------------------ |
| `_user`      | `address` | User claiming rewards    |
| `_caller`    | `address` | Address initiating claim |
| `_ripeToken` | `address` | Ripe token address       |

#### Returns

| Type              | Description                 |
| ----------------- | --------------------------- |
| `ClaimLootConfig` | Loot claiming configuration |

#### Access

Public view function

### `getRewardsConfig`

Returns complete rewards system configuration.

```vyper
@view
@external
def getRewardsConfig() -> RewardsConfig:
```

#### Returns

| Type            | Description                                           |
| --------------- | ----------------------------------------------------- |
| `RewardsConfig` | Complete rewards configuration with point allocations |

#### Access

Public view function

### `getDepositPointsConfig`

Returns deposit points configuration for an asset.

```vyper
@view
@external
def getDepositPointsConfig(_asset: address) -> DepositPointsConfig:
```

#### Parameters

| Name     | Type      | Description   |
| -------- | --------- | ------------- |
| `_asset` | `address` | Asset address |

#### Returns

| Type                  | Description                  |
| --------------------- | ---------------------------- |
| `DepositPointsConfig` | Deposit points configuration |

#### Access

Public view function

## Price and Bond Configuration Functions

### `getPriceConfig`

Returns price oracle configuration.

```vyper
@view
@external
def getPriceConfig() -> PriceConfig:
```

#### Returns

| Type          | Description                                              |
| ------------- | -------------------------------------------------------- |
| `PriceConfig` | Price configuration with stale time and priority sources |

#### Access

Public view function

### `getPriceStaleTime`

Returns the maximum allowed price age.

```vyper
@view
@external
def getPriceStaleTime() -> uint256:
```

#### Returns

| Type      | Description                 |
| --------- | --------------------------- |
| `uint256` | Price stale time in seconds |

#### Access

Public view function

### `getPurchaseRipeBondConfig`

Returns bond market configuration for a user.

```vyper
@view
@external
def getPurchaseRipeBondConfig(_user: address) -> PurchaseRipeBondConfig:
```

#### Parameters

| Name    | Type      | Description  |
| ------- | --------- | ------------ |
| `_user` | `address` | User address |

#### Returns

| Type                     | Description                        |
| ------------------------ | ---------------------------------- |
| `PurchaseRipeBondConfig` | Complete bond market configuration |

#### Access

Public view function

### `getDynamicBorrowRateConfig`

Returns dynamic borrow rate configuration.

```vyper
@view
@external
def getDynamicBorrowRateConfig() -> DynamicBorrowRateConfig:
```

#### Returns

| Type                      | Description             |
| ------------------------- | ----------------------- |
| `DynamicBorrowRateConfig` | Dynamic rate parameters |

#### Access

Public view function

## Priority Data Functions

### `getPriorityPriceSourceIds`

Returns the priority order of price sources.

```vyper
@view
@external
def getPriorityPriceSourceIds() -> DynArray[uint256, MAX_PRIORITY_PRICE_SOURCES]:
```

#### Returns

| Type                                            | Description                      |
| ----------------------------------------------- | -------------------------------- |
| `DynArray[uint256, MAX_PRIORITY_PRICE_SOURCES]` | Ordered list of price source IDs |

#### Access

Public view function

### `getPriorityLiqAssetVaults`

Returns priority vaults for liquidation asset processing.

```vyper
@view
@external
def getPriorityLiqAssetVaults() -> DynArray[cs.VaultLite, PRIORITY_VAULT_DATA]:
```

#### Returns

| Type                                          | Description                 |
| --------------------------------------------- | --------------------------- |
| `DynArray[cs.VaultLite, PRIORITY_VAULT_DATA]` | Priority liquidation vaults |

#### Access

Public view function

### `getPriorityStabVaults`

Returns priority vaults for stability pool operations.

```vyper
@view
@external
def getPriorityStabVaults() -> DynArray[cs.VaultLite, PRIORITY_VAULT_DATA]:
```

#### Returns

| Type                                          | Description               |
| --------------------------------------------- | ------------------------- |
| `DynArray[cs.VaultLite, PRIORITY_VAULT_DATA]` | Priority stability vaults |

#### Access

Public view function

## Utility Functions

### `doesUndyLegoHaveAccess`

Checks if an underscore lego contract has full access to a user's account.

```vyper
@view
@external
def doesUndyLegoHaveAccess(_wallet: address, _legoAddr: address) -> bool:
```

#### Parameters

| Name        | Type      | Description           |
| ----------- | --------- | --------------------- |
| `_wallet`   | `address` | User wallet address   |
| `_legoAddr` | `address` | Lego contract address |

#### Returns

| Type   | Description                  |
| ------ | ---------------------------- |
| `bool` | True if lego has full access |

#### Access

Public view function

#### Example Usage

```python
# Check if lego has access
has_access = mission_control.doesUndyLegoHaveAccess(
    user.address,
    lego_contract.address
)

# Requires user to allow anyone to deposit/repay AND
# delegate withdraw/borrow/claim permissions to lego
```

## Testing

For comprehensive test examples, see: [`tests/data/test_mission_control.py`](../../tests/data/test_mission_control.py)
