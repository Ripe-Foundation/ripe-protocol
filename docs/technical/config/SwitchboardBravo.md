# SwitchboardBravo Technical Documentation

[📄 View Source Code](../../contracts/config/SwitchboardBravo.vy)

## Overview

SwitchboardBravo manages asset-specific configurations for the Ripe Protocol. While SwitchboardAlpha handles protocol-wide settings, SwitchboardBravo focuses exclusively on individual asset parameters through time-locked
governance.

**Core Functions**:
- **Asset Onboarding**: Manages complete asset integration including vault assignments, point allocations, deposit limits, debt terms, and liquidation settings
- **Parameter Updates**: Controls modifications to existing assets (deposit limits, liquidation settings, debt terms, whitelist changes) with independent time-locks
- **Emergency Controls**: Provides rapid-response disabling of asset functions via lite action permissions
- **Validation**: Enforces complex rules ensuring asset configurations are internally consistent and protocol-compatible

The contract implements categorized time-locked changes, immediate emergency response, comprehensive validation, LTV deviation protection, and modular updates to ensure asset stability with operational flexibility.

## Architecture & Modules

SwitchboardBravo is built using a modular architecture with the following components:

### LocalGov Module
- **Location**: `contracts/modules/LocalGov.vy`
- **Purpose**: Provides governance functionality
- **Documentation**: See [LocalGov Technical Documentation](../modules/LocalGov.md)
- **Key Features**:
  - Governance address management
  - Permission validation
  - RipeHq integration
- **Exported Interface**: All governance functions via `gov.__interface__`

### TimeLock Module
- **Location**: `contracts/modules/TimeLock.vy`
- **Purpose**: Manages time-locked configuration changes
- **Documentation**: See [TimeLock Technical Documentation](../modules/TimeLock.md)
- **Key Features**:
  - Action ID generation
  - Time-lock enforcement
  - Action confirmation/cancellation
- **Exported Interface**: All timelock functions via `timeLock.__interface__`

### Module Initialization
```vyper
initializes: gov
initializes: timeLock[gov := gov]
```

## System Architecture Diagram

```
+------------------------------------------------------------------------+
|                      SwitchboardBravo Contract                         |
+------------------------------------------------------------------------+
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Asset Onboarding Flow                         |  |
|  |                                                                  |  |
|  |  1. Governance proposes new asset                                |  |
|  |     - Vault assignments                                          |  |
|  |     - Point allocations                                          |  |
|  |     - Deposit limits                                             |  |
|  |     - Debt terms (LTV, liquidation)                              |  |
|  |     - Liquidation configuration                                  |  |
|  |     - Initial enable/disable flags                               |  |
|  |                                                                  |  |
|  |  2. Comprehensive validation                                     |  |
|  |     - Vault registry checks                                      |  |
|  |     - Parameter consistency                                       |  |
|  |     - Special asset rules                                        |  |
|  |                                                                  |  |
|  |  3. Time-lock period enforced                                    |  |
|  |     - Action ID generated                                        |  |
|  |     - Pending configuration stored                               |  |
|  |                                                                  |  |
|  |  4. Governance executes after time-lock                          |  |
|  |     - Final validation                                           |  |
|  |     - Configuration written to MissionControl                    |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                 Configuration Update Categories                  |  |
|  |                                                                  |  |
|  |  Deposit Parameters:          Liquidation Config:               |  |
|  |  - Vault assignments          - Burn vs transfer                |  |
|  |  - Point allocations          - Stability pool swaps            |  |
|  |  - User/global limits         - Auction parameters              |  |
|  |                                                                  |  |
|  |  Debt Terms:                  Whitelist:                        |  |
|  |  - LTV ratios                 - Access control contract         |  |
|  |  - Liquidation thresholds     - User permissions                |  |
|  |  - Borrowing rates                                              |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Emergency Control Flow                        |  |
|  |                                                                  |  |
|  |  Enable Functions:                                                |  |
|  |  - Only governance can enable                                     |  |
|  |  - Immediate execution                                            |  |
|  |                                                                  |  |
|  |  Disable Functions:                                               |  |
|  |  - Governance OR lite action users                               |  |
|  |  - Immediate execution                                            |  |
|  |  - Per-asset granularity:                                        |  |
|  |    • canDeposit / canWithdraw                                    |  |
|  |    • canRedeemCollateral / canRedeemInStabPool                   |  |
|  |    • canBuyInAuction / canClaimInStabPool                        |  |
|  +------------------------------------------------------------------+  |
+------------------------------------------------------------------------+
                                    |
        +---------------------------+---------------------------+
        |                           |                           |
        v                           v                           v
+------------------+    +-------------------+    +------------------+
| MissionControl   |    | VaultBook         |    | SwitchboardAlpha |
| * Stores configs |    | * Validates vaults|    | * Validates      |
| * Enforces rules |    | * Registry data   |    |   auction params |
| * Asset registry |    |                   |    |                  |
+------------------+    +-------------------+    +------------------+
```

## Data Structures

### ActionType Flag
Categorizes pending asset configuration changes:
```vyper
flag ActionType:
    ASSET_ADD_NEW               # Complete new asset configuration
    ASSET_DEPOSIT_PARAMS        # Vault and deposit settings
    ASSET_LIQ_CONFIG            # Liquidation behavior
    ASSET_DEBT_TERMS            # LTV and borrowing parameters
    ASSET_WHITELIST             # Access control updates
```

### AssetFlag Flag
Asset-specific enable/disable switches:
```vyper
flag AssetFlag:
    CAN_DEPOSIT                 # Allow deposits
    CAN_WITHDRAW                # Allow withdrawals
    CAN_REDEEM_IN_STAB_POOL     # Allow stability pool redemptions
    CAN_BUY_IN_AUCTION          # Allow auction purchases
    CAN_CLAIM_IN_STAB_POOL      # Allow stability pool claims
    CAN_REDEEM_COLLATERAL       # Allow direct collateral redemption
```

### AssetUpdate Struct
Pending asset configuration update:
```vyper
struct AssetUpdate:
    asset: address              # Asset being configured
    config: cs.AssetConfig      # Complete configuration
```

## State Variables

### Public State Variables
- `actionType: HashMap[uint256, ActionType]` - Maps action IDs to configuration types
- `pendingAssetConfig: HashMap[uint256, AssetUpdate]` - Stores pending configurations

### Constants
- `MAX_VAULTS_PER_ASSET: uint256 = 10` - Maximum vaults per asset
- `HUNDRED_PERCENT: uint256 = 100_00` - 100.00% in basis points
- `GREEN_TOKEN_ID: uint256 = 1` - Green token registry ID
- `SAVINGS_GREEN_ID: uint256 = 2` - Savings Green registry ID
- `MISSION_CONTROL_ID: uint256 = 5` - MissionControl registry ID
- `VAULT_BOOK_ID: uint256 = 8` - VaultBook registry ID
- `SWITCHBOARD_ID: uint256 = 6` - Switchboard registry ID
- `SWITCHBOARD_ALPHA_ID: uint256 = 1` - SwitchboardAlpha registry ID

## Constructor

### `__init__`

Initializes SwitchboardBravo with governance and time-lock settings.

```vyper
@deploy
def __init__(
    _ripeHq: address,
    _tempGov: address,
    _minConfigTimeLock: uint256,
    _maxConfigTimeLock: uint256,
):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_ripeHq` | `address` | RipeHq registry address |
| `_tempGov` | `address` | Initial governance address |
| `_minConfigTimeLock` | `uint256` | Minimum time-lock for changes |
| `_maxConfigTimeLock` | `uint256` | Maximum time-lock for changes |

#### Returns

*Constructor does not return any values*

#### Access

Called only during deployment

#### Example Usage
```python
# Deploy SwitchboardBravo
switchboard_bravo = boa.load(
    "contracts/config/SwitchboardBravo.vy",
    ripe_hq.address,
    governance.address,
    100,    # Min config timelock
    10000   # Max config timelock
)
```

## Asset Onboarding Functions

### `addAsset`

Adds a new asset to the protocol with complete configuration.

```vyper
@external
def addAsset(
    _asset: address,
    _vaultIds: DynArray[uint256, MAX_VAULTS_PER_ASSET],
    _stakersPointsAlloc: uint256,
    _voterPointsAlloc: uint256,
    _perUserDepositLimit: uint256,
    _globalDepositLimit: uint256,
    _minDepositBalance: uint256 = 0,
    _debtTerms: cs.DebtTerms = empty(cs.DebtTerms),
    _shouldBurnAsPayment: bool = False,
    _shouldTransferToEndaoment: bool = False,
    _shouldSwapInStabPools: bool = True,
    _shouldAuctionInstantly: bool = True,
    _canDeposit: bool = True,
    _canWithdraw: bool = True,
    _canRedeemCollateral: bool = True,
    _canRedeemInStabPool: bool = True,
    _canBuyInAuction: bool = True,
    _canClaimInStabPool: bool = True,
    _specialStabPoolId: uint256 = 0,
    _customAuctionParams: cs.AuctionParams = empty(cs.AuctionParams),
    _whitelist: address = empty(address),
    _isNft: bool = False,
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_asset` | `address` | Token contract address |
| `_vaultIds` | `DynArray[uint256, 10]` | Vault IDs for deposits |
| `_stakersPointsAlloc` | `uint256` | Points allocation for stakers |
| `_voterPointsAlloc` | `uint256` | Points allocation for voters |
| `_perUserDepositLimit` | `uint256` | Maximum deposit per user |
| `_globalDepositLimit` | `uint256` | Total protocol deposit limit |
| `_minDepositBalance` | `uint256` | Minimum deposit amount |
| `_debtTerms` | `cs.DebtTerms` | Borrowing and liquidation parameters |
| `_shouldBurnAsPayment` | `bool` | Burn on liquidation (Green/sGreen only) |
| `_shouldTransferToEndaoment` | `bool` | Transfer to Endaoment on liquidation |
| `_shouldSwapInStabPools` | `bool` | Allow stability pool swaps |
| `_shouldAuctionInstantly` | `bool` | Skip delay for auctions |
| `_canDeposit` | `bool` | Initial deposit permission |
| `_canWithdraw` | `bool` | Initial withdrawal permission |
| `_canRedeemCollateral` | `bool` | Initial collateral redemption permission |
| `_canRedeemInStabPool` | `bool` | Initial stability pool redemption permission |
| `_canBuyInAuction` | `bool` | Initial auction purchase permission |
| `_canClaimInStabPool` | `bool` | Initial stability pool claim permission |
| `_specialStabPoolId` | `uint256` | Custom stability pool ID |
| `_customAuctionParams` | `cs.AuctionParams` | Custom auction parameters |
| `_whitelist` | `address` | Access control contract |
| `_isNft` | `bool` | Whether asset is an NFT |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Action ID for tracking |

#### Access

Only callable by governance

#### Events Emitted

- `NewAssetPending` - Comprehensive event with all configuration details

#### Example Usage
```python
# Add WETH as collateral
debt_terms = DebtTerms(
    ltv=8000,                    # 80% LTV
    redemptionThreshold=8500,    # 85% redemption threshold
    liqThreshold=9000,           # 90% liquidation threshold
    liqFee=500,                  # 5% liquidation fee
    borrowRate=200,              # 2% borrow rate
    daowry=0                     # No daowry
)

action_id = switchboard_bravo.addAsset(
    weth.address,
    [1, 2],                      # Vault IDs
    5000,                        # 50% to stakers
    5000,                        # 50% to voters
    1000 * 10**18,               # 1000 WETH per user limit
    100000 * 10**18,             # 100k WETH global limit
    0,                           # No minimum
    debt_terms,
    sender=governance.address
)
```

## Asset Configuration Update Functions

### `setAssetDepositParams`

Updates deposit-related parameters for an existing asset.

```vyper
@external
def setAssetDepositParams(
    _asset: address,
    _vaultIds: DynArray[uint256, MAX_VAULTS_PER_ASSET],
    _stakersPointsAlloc: uint256,
    _voterPointsAlloc: uint256,
    _perUserDepositLimit: uint256,
    _globalDepositLimit: uint256,
    _minDepositBalance: uint256,
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_asset` | `address` | Asset to update |
| `_vaultIds` | `DynArray[uint256, 10]` | New vault assignments |
| `_stakersPointsAlloc` | `uint256` | New staker allocation |
| `_voterPointsAlloc` | `uint256` | New voter allocation |
| `_perUserDepositLimit` | `uint256` | New per-user limit |
| `_globalDepositLimit` | `uint256` | New global limit |
| `_minDepositBalance` | `uint256` | New minimum deposit |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Action ID |

#### Access

Only callable by governance

#### Events Emitted

- `PendingAssetDepositParamsChange` - Contains new parameters and confirmation block

### `setAssetLiqConfig`

Updates liquidation configuration for an asset.

```vyper
@external
def setAssetLiqConfig(
    _asset: address,
    _shouldBurnAsPayment: bool,
    _shouldTransferToEndaoment: bool,
    _shouldSwapInStabPools: bool,
    _shouldAuctionInstantly: bool,
    _specialStabPoolId: uint256 = 0,
    _customAuctionParams: cs.AuctionParams = empty(cs.AuctionParams),
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_asset` | `address` | Asset to update |
| `_shouldBurnAsPayment` | `bool` | Burn on liquidation |
| `_shouldTransferToEndaoment` | `bool` | Transfer to Endaoment |
| `_shouldSwapInStabPools` | `bool` | Allow stability swaps |
| `_shouldAuctionInstantly` | `bool` | Skip auction delay |
| `_specialStabPoolId` | `uint256` | Custom pool ID |
| `_customAuctionParams` | `cs.AuctionParams` | Custom auction settings |

#### Access

Only callable by governance

### `setAssetDebtTerms`

Updates borrowing and liquidation parameters.

```vyper
@external
def setAssetDebtTerms(
    _asset: address,
    _ltv: uint256,
    _redemptionThreshold: uint256,
    _liqThreshold: uint256,
    _liqFee: uint256,
    _borrowRate: uint256,
    _daowry: uint256,
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_asset` | `address` | Asset to update |
| `_ltv` | `uint256` | Loan-to-value ratio |
| `_redemptionThreshold` | `uint256` | Redemption trigger |
| `_liqThreshold` | `uint256` | Liquidation trigger |
| `_liqFee` | `uint256` | Liquidation bonus |
| `_borrowRate` | `uint256` | Interest rate |
| `_daowry` | `uint256` | Protocol fee |

#### Access

Only callable by governance

#### Validation

- Enforces LTV deviation limits to prevent market manipulation
- Ensures threshold ordering: LTV < redemption < liquidation

### `setWhitelistForAsset`

Updates access control whitelist.

```vyper
@external
def setWhitelistForAsset(_asset: address, _whitelist: address) -> uint256:
```

## Asset Enable/Disable Functions

Multiple functions control asset operations:
- `setCanDepositAsset(_asset: address, _shouldEnable: bool)` - Control deposits
- `setCanWithdrawAsset(_asset: address, _shouldEnable: bool)` - Control withdrawals
- `setCanRedeemCollateralAsset(_asset: address, _shouldEnable: bool)` - Control redemptions
- `setCanRedeemInStabPoolAsset(_asset: address, _shouldEnable: bool)` - Control stability redemptions
- `setCanBuyInAuctionAsset(_asset: address, _shouldEnable: bool)` - Control auction participation
- `setCanClaimInStabPoolAsset(_asset: address, _shouldEnable: bool)` - Control stability claims

#### Access

- **To Enable**: Only governance
- **To Disable**: Governance OR users with lite action permission

#### Example Usage
```python
# Emergency: disable WETH deposits
switchboard_bravo.setCanDepositAsset(
    weth.address,
    False,
    sender=emergency_user.address  # Has lite action permission
)

# Re-enable WETH deposits
switchboard_bravo.setCanDepositAsset(
    weth.address,
    True,
    sender=governance.address  # Only governance can enable
)
```

## Execution Functions

### `executePendingAction`

Executes a pending configuration change after time-lock.

```vyper
@external
def executePendingAction(_aid: uint256) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_aid` | `uint256` | Action ID to execute |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if executed successfully |

#### Access

Only callable by governance

#### Example Usage
```python
# Execute after time-lock
boa.env.time_travel(blocks=timelock_period)
success = switchboard_bravo.executePendingAction(
    action_id,
    sender=governance.address
)
```

### `cancelPendingAction`

Cancels a pending configuration change.

```vyper
@external
def cancelPendingAction(_aid: uint256) -> bool:
```

## Key Validation Logic

### Asset Configuration Validation

Each asset configuration must pass comprehensive checks:

1. **Vault Validation**:
   - All vault IDs must be registered in VaultBook
   - Staker allocations require staker vaults (ID 1 or 2)

2. **Allocation Validation**:
   - Staker + voter allocations ≤ 100%
   - No max uint256 values

3. **Limit Validation**:
   - Per-user limit ≤ global limit
   - Minimum deposit ≤ per-user limit
   - Non-zero limits required

4. **Debt Terms Validation**:
   - LTV < redemption threshold < liquidation threshold ≤ 100%
   - Liquidation fee + threshold ≤ 100%
   - Non-zero fees if LTV > 0

5. **Special Asset Rules**:
   - Only Green/sGreen can use burn on payment
   - NFTs cannot use stability pools or collateral redemption
   - Stable assets cannot be redeemed as collateral

### LTV Deviation Protection

Prevents sudden LTV changes that could harm users:
```
maxDeviation = protocol setting
upperBound = min(currentLTV + maxDeviation, 100%)
lowerBound = max(currentLTV - maxDeviation, 0)
newLTV must be within [lowerBound, upperBound]
```

## Security Considerations

1. **Time-lock Protection**: All configuration changes require time-lock
2. **Emergency Response**: Quick disable capability for crisis management
3. **Parameter Validation**: Comprehensive checks prevent invalid configurations
4. **Access Control**: Strict governance requirements for enabling functions
5. **Asset Isolation**: Each asset configured independently
6. **LTV Protection**: Deviation limits prevent market manipulation

## Testing

For comprehensive test examples, see: [`tests/config/test_switchboard_bravo.py`](../../tests/config/test_switchboard_bravo.py)