# Endaoment Technical Documentation

[📄 View Source Code](../../contracts/core/Endaoment.vy)

## Overview

Endaoment is the protocol-owned treasury and liquidity management hub for Ripe Protocol, actively managing funds across DeFi strategies while maintaining Green token stability. It serves as the financial nerve center, optimizing
capital efficiency through yield generation and automated market operations.

**Core Functions**:
- **Yield Management**: Deploys funds across modular "Lego" strategies including lending protocols, AMMs, and liquid staking for optimal returns
- **Green Stabilization**: Automated peg maintenance through Curve pool liquidity adjustments based on Green trading ratios
- **Partner Programs**: Facilitates liquidity partnerships with external parties providing assets alongside protocol-minted Green
- **Treasury Operations**: Receives and manages liquidation proceeds, bond sales, fees, and handles ETH/WETH conversions

The contract implements pluggable yield strategies, automated rebalancing, sophisticated AMM management, comprehensive event logging, and debt tracking for leveraged positions while ensuring protocol solvency.

## Architecture & Modules

Endaoment is built using a modular architecture with the following components:

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
  - Green token minting capability (for stabilizer)
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
|                         Endaoment Contract                             |
+------------------------------------------------------------------------+
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                  Yield Strategy Management                       |  |
|  |                                                                  |  |
|  |  UndyLego Interface (Pluggable Strategies):                     |  |
|  |  - Lego 1: Aave Lending                                          |  |
|  |  - Lego 2: Compound v3                                          |  |
|  |  - Lego 3: Uniswap v3 LP                                        |  |
|  |  - Lego 4: Curve Pools                                          |  |
|  |  - Lego 5: Liquid Staking                                       |  |
|  |                                                                  |  |
|  |  Operations:                                                     |  |
|  |  1. depositForYield() -> Higher yield                            |  |
|  |  2. withdrawFromYield() -> Retrieve funds                        |  |
|  |  3. rebalanceYieldPosition() -> Switch strategies                |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                   Green Stabilizer System                       |  |
|  |                                                                  |  |
|  |  Automated Peg Maintenance:                                     |  |
|  |  - Monitor Green ratio in Curve pools                            |  |
|  |  - If ratio < 50%: Add Green liquidity                          |  |
|  |  - If ratio > 50%: Remove Green liquidity                       |  |
|  |                                                                  |  |
|  |  Profit Calculation:                                             |  |
|  |  LP Value + Leftover Green - Pool Debt = Net Position           |  |
|  |                                                                  |  |
|  |  Debt Management:                                                |  |
|  |  - Track minted Green for liquidity                             |  |
|  |  - Repay debt when removing liquidity                           |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                  Partner Liquidity Programs                     |  |
|  |                                                                  |  |
|  |  Two Models:                                                     |  |
|  |  1. Mint & Pair: Protocol mints Green, partner provides asset   |  |
|  |     - Equal value pairing                                       |  |
|  |     - Shared IL risk                                            |  |
|  |                                                                  |  |
|  |  2. Add Liquidity: Both sides provide existing tokens           |  |
|  |     - Flexible ratios                                           |  |
|  |     - Existing pool participation                               |  |
|  +------------------------------------------------------------------+  |
+------------------------------------------------------------------------+
                                    |
        +---------------------------+---------------------------+
        |                           |                           |
        v                           v                           v
+------------------+    +-------------------+    +------------------+
| UndyLego Strats  |    | Curve Pools       |    | Partner Wallets  |
| * Yield farming  |    | * Green/USDC      |    | * External funds |
| * LP management  |    | * Peg maintenance |    | * Shared rewards |
| * Rebalancing    |    | * Debt tracking   |    | * IL sharing     |
+------------------+    +-------------------+    +------------------+
        |                           |                           |
        v                           v                           v
+------------------+    +-------------------+    +------------------+
| Ledger           |    | PriceDesk         |    | Green Token      |
| * Pool debt      |    | * USD values      |    | * Mint for liq   |
| * Yield tracking |    | * Profit calc     |    | * Stabilization  |
+------------------+    +-------------------+    +------------------+
```

## Data Structures

### StabilizerConfig Struct
Configuration for Green stabilizer (from CurvePrices):
```vyper
struct StabilizerConfig:
    pool: address                    # Curve pool address
    lpToken: address                 # LP token address
    greenBalance: uint256            # Current Green in pool
    greenRatio: uint256              # Green percentage (basis points)
    greenIndex: uint256              # Green token index in pool
    stabilizerAdjustWeight: uint256  # Adjustment aggressiveness
    stabilizerMaxPoolDebt: uint256   # Maximum debt allowed
```

## State Variables

### Immutable Variables
- `WETH: public(immutable(address))` - Wrapped Ether address
- `ETH: public(immutable(address))` - ETH representation address

### Constants
- `HUNDRED_PERCENT: uint256 = 100_00` - 100.00% in basis points
- `FIFTY_PERCENT: uint256 = 50_00` - 50.00% target ratio
- `EIGHTEEN_DECIMALS: uint256 = 10 ** 18` - Standard precision
- `MAX_SWAP_INSTRUCTIONS: uint256 = 5` - Batch swap limit
- `MAX_TOKEN_PATH: uint256 = 5` - Multi-hop path limit
- `MAX_ASSETS: uint256 = 10` - Asset batch limit
- `MAX_LEGOS: uint256 = 10` - Strategy limit
- `LEGO_BOOK_ID: uint256 = 4` - Lego registry ID
- `CURVE_PRICES_ID: uint256 = 2` - Curve prices registry ID

### Inherited State Variables
From [DeptBasics](../modules/DeptBasics.md):
- `isPaused: bool` - Department pause state
- `canMintGreen: bool` - Set to `True` for stabilizer

## Constructor

### `__init__`

Initializes Endaoment with Green minting capability and ETH handling.

```vyper
@deploy
def __init__(_ripeHq: address, _weth: address, _eth: address):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_ripeHq` | `address` | RipeHq contract address |
| `_weth` | `address` | WETH token contract |
| `_eth` | `address` | ETH representation address |

#### Returns

*Constructor does not return any values*

#### Access

Called only during deployment

#### Example Usage
```python
# Deploy Endaoment
endaoment = boa.load(
    "contracts/core/Endaoment.vy",
    ripe_hq.address,
    weth.address,
    eth_address
)
```

**Example Output**: Contract deployed with treasury management capabilities

## Yield Strategy Functions

### `depositForYield`

Deposits assets into yield-generating strategies via Lego contracts.

```vyper
@nonreentrant
@external
def depositForYield(
    _legoId: uint256,
    _asset: address,
    _vaultAddr: address = empty(address),
    _amount: uint256 = max_value(uint256),
    _extraData: bytes32 = empty(bytes32),
) -> (uint256, address, uint256, uint256):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_legoId` | `uint256` | Strategy ID from registry |
| `_asset` | `address` | Asset to deposit |
| `_vaultAddr` | `address` | Specific vault (optional) |
| `_amount` | `uint256` | Amount to deposit (max for all) |
| `_extraData` | `bytes32` | Strategy-specific data |

#### Returns

| Type | Description |
|------|-------------|
| `(uint256, address, uint256, uint256)` | (assetAmount, vaultToken, vaultTokenAmount, usdValue) |

#### Access

Only callable by Switchboard-registered contracts

#### Events Emitted

- `WalletAction` - Operation details including:
  - Operation code (10 for deposit)
  - Input/output assets and amounts
  - USD value and strategy ID

#### Example Usage
```python
# Deposit USDC into Aave
asset_used, vault_token, vault_amount, usd_val = endaoment.depositForYield(
    1,  # Aave Lego ID
    usdc.address,
    aave_usdc_vault.address,
    1000_000000,  # 1000 USDC
    b"",
    sender=treasury_manager.address
)
```

### `withdrawFromYield`

Withdraws assets from yield strategies.

```vyper
@nonreentrant
@external
def withdrawFromYield(
    _legoId: uint256,
    _vaultToken: address,
    _amount: uint256 = max_value(uint256),
    _extraData: bytes32 = empty(bytes32),
) -> (uint256, address, uint256, uint256):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_legoId` | `uint256` | Strategy ID |
| `_vaultToken` | `address` | Vault token to redeem |
| `_amount` | `uint256` | Amount to withdraw |
| `_extraData` | `bytes32` | Strategy-specific data |

#### Returns

| Type | Description |
|------|-------------|
| `(uint256, address, uint256, uint256)` | (vaultTokenBurned, underlyingAsset, underlyingAmount, usdValue) |

#### Access

Only callable by Switchboard-registered contracts

#### Events Emitted

- `WalletAction` - Withdrawal details (op code 11)

### `rebalanceYieldPosition`

Moves funds between different yield strategies.

```vyper
@nonreentrant
@external
def rebalanceYieldPosition(
    _fromLegoId: uint256,
    _fromVaultToken: address,
    _toLegoId: uint256,
    _toVaultAddr: address = empty(address),
    _fromVaultAmount: uint256 = max_value(uint256),
    _extraData: bytes32 = empty(bytes32),
) -> (uint256, address, uint256, uint256):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_fromLegoId` | `uint256` | Source strategy ID |
| `_fromVaultToken` | `address` | Source vault token |
| `_toLegoId` | `uint256` | Destination strategy ID |
| `_toVaultAddr` | `address` | Destination vault |
| `_fromVaultAmount` | `uint256` | Amount to move |
| `_extraData` | `bytes32` | Strategy-specific data |

#### Returns

| Type | Description |
|------|-------------|
| `(uint256, address, uint256, uint256)` | New position details |

#### Access

Only callable by Switchboard-registered contracts

## Liquidity Management Functions

### `addLiquidity`

Adds liquidity to AMM pools.

```vyper
@nonreentrant
@external
def addLiquidity(
    _legoId: uint256,
    _pool: address,
    _tokenA: address,
    _tokenB: address,
    _amountA: uint256 = max_value(uint256),
    _amountB: uint256 = max_value(uint256),
    _minLpAmount: uint256 = 0,
    _extraData: bytes32 = empty(bytes32),
) -> (uint256, uint256, uint256, uint256):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_legoId` | `uint256` | AMM strategy ID |
| `_pool` | `address` | Pool address |
| `_tokenA` | `address` | First token |
| `_tokenB` | `address` | Second token |
| `_amountA` | `uint256` | Amount of token A |
| `_amountB` | `uint256` | Amount of token B |
| `_minLpAmount` | `uint256` | Minimum LP tokens |
| `_extraData` | `bytes32` | Pool-specific data |

#### Returns

| Type | Description |
|------|-------------|
| `(uint256, uint256, uint256, uint256)` | (amountAUsed, amountBUsed, lpReceived, usdValue) |

#### Access

Only callable by Switchboard-registered contracts

#### Events Emitted

- `WalletAction` - Liquidity addition details (op code 30)

### `removeLiquidity`

Removes liquidity from AMM pools.

```vyper
@nonreentrant
@external
def removeLiquidity(
    _legoId: uint256,
    _pool: address,
    _tokenA: address,
    _tokenB: address,
    _lpToken: address,
    _lpAmount: uint256 = max_value(uint256),
    _minAmountA: uint256 = 0,
    _minAmountB: uint256 = 0,
    _extraData: bytes32 = empty(bytes32),
) -> (uint256, uint256, uint256, uint256):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_legoId` | `uint256` | AMM strategy ID |
| `_pool` | `address` | Pool address |
| `_tokenA` | `address` | First token |
| `_tokenB` | `address` | Second token |
| `_lpToken` | `address` | LP token address |
| `_lpAmount` | `uint256` | LP tokens to burn |
| `_minAmountA` | `uint256` | Minimum token A |
| `_minAmountB` | `uint256` | Minimum token B |
| `_extraData` | `bytes32` | Pool-specific data |

#### Returns

| Type | Description |
|------|-------------|
| `(uint256, uint256, uint256, uint256)` | (amountAReceived, amountBReceived, lpBurned, usdValue) |

#### Access

Only callable by Switchboard-registered contracts

#### Events Emitted

- `WalletAction` - Liquidity removal details (op code 31)

## Green Stabilizer Functions

### `stabilizeGreenRefPool`

Automatically adjusts Green liquidity to maintain peg stability.

```vyper
@external
def stabilizeGreenRefPool() -> bool:
```

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if adjustment was made |

#### Access

Only callable by Switchboard-registered contracts

#### Events Emitted

- `StabilizerPoolLiqAdded` - When adding Green liquidity
- `StabilizerPoolLiqRemoved` - When removing Green liquidity

#### Example Usage
```python
# Automated stabilization call
was_adjusted = endaoment.stabilizeGreenRefPool(
    sender=stabilizer_bot.address
)
# Returns: True if pool was rebalanced
```

**Example Output**: Adjusts Green liquidity based on current pool ratio

### `getGreenAmountToAddInStabilizer`

Previews how much Green would be added to stabilizer.

```vyper
@view
@external
def getGreenAmountToAddInStabilizer() -> uint256:
```

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Green amount that would be added |

#### Access

Public view function

#### Example Usage
```python
# Preview stabilizer action
green_to_add = endaoment.getGreenAmountToAddInStabilizer()
# Returns: Amount of Green that would be added to pool
```

### `getGreenAmountToRemoveInStabilizer`

Previews how much Green would be removed from the stabilizer pool.

```vyper
@view
@external
def getGreenAmountToRemoveInStabilizer() -> uint256:
```

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Green amount that would be removed |

#### Access

Public view function

#### Example Usage
```python
# Preview stabilizer removal
green_to_remove = endaoment.getGreenAmountToRemoveInStabilizer()
# Returns: Amount of Green that would be removed from pool
```

## Partner Liquidity Functions

### `mintPartnerLiquidity`

Takes a partner's asset, gets its USD value, and mints an equivalent amount of Green tokens. The partner can be an external wallet or the Endaoment itself.

```vyper
@nonreentrant
@external
def mintPartnerLiquidity(
    _partner: address,
    _asset: address,
    _amount: uint256,
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_partner` | `address` | Partner wallet providing asset (can be Endaoment itself) |
| `_asset` | `address` | Asset being provided |
| `_amount` | `uint256` | Amount of asset |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Amount of Green tokens minted |

#### Access

Only callable by Switchboard-registered contracts

#### Events Emitted

- `PartnerLiquidityMinted` - Contains partner address, asset, amount, and Green minted

#### Special Behavior - Self as Partner

When `_partner` is the Endaoment contract address itself:
- **No token transfer**: Assets are used directly from Endaoment's existing balance
- **Internal operation**: Functions as an internal mint operation using treasury funds
- **Same events**: Events are still emitted with Endaoment as the partner address

#### Example Usage
```python
# External partner provides 10 ETH for liquidity
green_minted = endaoment.mintPartnerLiquidity(
    partner.address,
    weth.address,
    10_000000000000000000,  # 10 ETH
    sender=treasury_manager.address
)
# Returns: Amount of Green minted (e.g., 15000e18 if ETH = $1500)

# Endaoment using its own funds
green_minted = endaoment.mintPartnerLiquidity(
    endaoment.address,  # Self as partner
    usdc.address,
    1000_000000,  # 1000 USDC from treasury
    sender=treasury_manager.address
)
# Returns: 1000e18 Green minted (assuming $1 USDC)
```

### `addPartnerLiquidity`

Takes a partner's asset, mints equivalent Green tokens, and adds both to a liquidity pool. LP tokens are shared between the partner and Endaoment, except when the partner is Endaoment itself.

```vyper
@nonreentrant
@external
def addPartnerLiquidity(
    _legoId: uint256,
    _pool: address,
    _partner: address,
    _asset: address,
    _amount: uint256 = max_value(uint256),
    _minLpAmount: uint256 = 0,
) -> (uint256, uint256, uint256):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_legoId` | `uint256` | AMM strategy ID |
| `_pool` | `address` | Pool address |
| `_partner` | `address` | Partner wallet address (can be Endaoment itself) |
| `_asset` | `address` | Partner's asset |
| `_amount` | `uint256` | Partner's asset contribution (max = all available) |
| `_minLpAmount` | `uint256` | Minimum LP tokens |

#### Returns

| Type | Description |
|------|-------------|
| `(uint256, uint256, uint256)` | (lpAmountReceived, liqAmountA, liqAmountB) |

#### Access

Only callable by Switchboard-registered contracts

#### Events Emitted

- `PartnerLiquidityAdded` - Partnership liquidity details

#### Special Behavior - Self as Partner

When `_partner` is the Endaoment contract address itself:
- **No token transfer**: Assets used directly from Endaoment's balance
- **All LP tokens to Endaoment**: No 50/50 split - all LP tokens remain with Endaoment
- **Same pool debt tracking**: Pool debt is still tracked for newly minted Green tokens
- **Treasury operation**: Functions as an internal treasury liquidity operation

#### Example Usage
```python
# External partner liquidity (50/50 LP split)
lp_tokens, amount_a, amount_b = endaoment.addPartnerLiquidity(
    2,  # Curve Lego ID
    curve_pool.address,
    partner.address,
    usdc.address,
    1000_000000,  # 1000 USDC from partner
    950_000000000000000000,  # Min LP tokens
    sender=treasury_manager.address
)
# LP tokens split: 50% to partner, 50% to Endaoment

# Endaoment self-liquidity (all LP to Endaoment)
lp_tokens, amount_a, amount_b = endaoment.addPartnerLiquidity(
    2,  # Curve Lego ID
    curve_pool.address,
    endaoment.address,  # Self as partner
    usdc.address,
    2000_000000,  # 2000 USDC from treasury
    1900_000000000000000000,  # Min LP tokens
    sender=treasury_manager.address
)
# LP tokens: 100% remain with Endaoment
```

## Swap and Exchange Functions

### `swapTokens`

Executes a series of token swaps through different DeFi protocols (Lego contracts).

```vyper
@nonreentrant
@external
def swapTokens(
    _inputAsset: address,
    _outputAsset: address,
    _inputAmount: uint256,
    _minOutputAmount: uint256,
    _swapInstructions: DynArray[SwapInstruction, MAX_SWAP_INSTRUCTIONS],
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_inputAsset` | `address` | Token to swap from |
| `_outputAsset` | `address` | Token to swap to |
| `_inputAmount` | `uint256` | Amount to swap |
| `_minOutputAmount` | `uint256` | Minimum output expected |
| `_swapInstructions` | `DynArray[SwapInstruction, 5]` | Routing instructions |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Amount of output tokens received |

#### Access

Only callable by Switchboard-registered contracts

#### Events Emitted

- `WalletAction` - Swap details (op code 20)

#### Example Usage
```python
# Swap USDC to ETH through multiple DEXes
instructions = [
    SwapInstruction(1, curve_pool, 500_000000),  # 50% through Curve
    SwapInstruction(2, uniswap_pool, 500_000000) # 50% through Uniswap
]
eth_received = endaoment.swapTokens(
    usdc.address,
    weth.address,
    1000_000000,  # 1000 USDC
    650000000000000000,  # Min 0.65 ETH
    instructions,
    sender=treasury_manager.address
)
```

### `mintOrRedeemAsset`

A generic function for complex operations like minting rETH from ETH via Rocket Pool.

```vyper
@nonreentrant
@external
def mintOrRedeemAsset(
    _legoId: uint256,
    _inputAsset: address,
    _outputAsset: address,
    _inputAmount: uint256,
    _minOutputAmount: uint256,
    _extraData: bytes32 = empty(bytes32),
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_legoId` | `uint256` | Protocol strategy ID |
| `_inputAsset` | `address` | Asset to provide |
| `_outputAsset` | `address` | Asset to receive |
| `_inputAmount` | `uint256` | Amount to convert |
| `_minOutputAmount` | `uint256` | Minimum output |
| `_extraData` | `bytes32` | Protocol-specific data |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Amount of output asset received |

#### Access

Only callable by Switchboard-registered contracts

#### Events Emitted

- `WalletAction` - Mint/redeem details (op code 21)

#### Example Usage
```python
# Mint rETH from ETH via Rocket Pool
reth_received = endaoment.mintOrRedeemAsset(
    5,  # Rocket Pool Lego ID
    weth.address,
    reth.address,
    10_000000000000000000,  # 10 ETH
    9_800000000000000000,   # Min 9.8 rETH
    b"",
    sender=treasury_manager.address
)
```

### `confirmMintOrRedeemAsset`

Confirms a pending mint/redeem operation if the Lego contract has a time delay.

```vyper
@nonreentrant
@external
def confirmMintOrRedeemAsset(
    _legoId: uint256,
    _outputAsset: address,
    _extraData: bytes32 = empty(bytes32),
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_legoId` | `uint256` | Protocol strategy ID |
| `_outputAsset` | `address` | Asset to claim |
| `_extraData` | `bytes32` | Protocol-specific data |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Amount of output asset received |

#### Access

Only callable by Switchboard-registered contracts

#### Events Emitted

- `WalletAction` - Confirmation details (op code 22)

## Yield and Reward Functions

### `claimRewards`

A generic function to claim accumulated rewards from any yield strategy.

```vyper
@nonreentrant
@external
def claimRewards(
    _legoId: uint256,
    _vaultToken: address,
    _rewardAssets: DynArray[address, MAX_ASSETS],
    _extraData: bytes32 = empty(bytes32),
) -> DynArray[uint256, MAX_ASSETS]:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_legoId` | `uint256` | Strategy ID with rewards |
| `_vaultToken` | `address` | Vault token earning rewards |
| `_rewardAssets` | `DynArray[address, 10]` | Expected reward tokens |
| `_extraData` | `bytes32` | Strategy-specific data |

#### Returns

| Type | Description |
|------|-------------|
| `DynArray[uint256, 10]` | Amounts of each reward token claimed |

#### Access

Only callable by Switchboard-registered contracts

#### Events Emitted

- `WalletAction` - Reward claim details (op code 12)

#### Example Usage
```python
# Claim rewards from Aave position
reward_assets = [aave_token.address, stkAAVE.address]
rewards_claimed = endaoment.claimRewards(
    1,  # Aave Lego ID
    aUSDC.address,
    reward_assets,
    b"",
    sender=treasury_manager.address
)
# Returns: [1000e18, 500e18] (1000 AAVE, 500 stkAAVE)
```

## ETH and WETH Conversion

### `convertEthToWeth`

A payable function to wrap ETH into WETH.

```vyper
@payable
@nonreentrant
@external
def convertEthToWeth(_amount: uint256 = max_value(uint256)) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_amount` | `uint256` | Amount to wrap (max = msg.value) |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Amount of WETH received |

#### Access

Only callable by Switchboard-registered contracts

#### Events Emitted

- `WalletAction` - ETH wrap details (op code 80)

#### Example Usage
```python
# Wrap 5 ETH to WETH
weth_amount = endaoment.convertEthToWeth(
    5_000000000000000000,
    value=5_000000000000000000,  # Send 5 ETH
    sender=treasury_manager.address
)
# Returns: 5000000000000000000 (5 WETH)
```

### `convertWethToEth`

Unwraps WETH back into ETH.

```vyper
@nonreentrant
@external
def convertWethToEth(_amount: uint256 = max_value(uint256)) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_amount` | `uint256` | Amount to unwrap (max = balance) |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Amount of ETH received |

#### Access

Only callable by Switchboard-registered contracts

#### Events Emitted

- `WalletAction` - ETH unwrap details (op code 81)

#### Example Usage
```python
# Unwrap all WETH to ETH
eth_amount = endaoment.convertWethToEth(
    sender=treasury_manager.address
)
# Returns: Amount of ETH received
```

## Concentrated Liquidity Functions

### `addLiquidityConcentrated`

Adds liquidity to a concentrated liquidity position, represented by an NFT.

```vyper
@nonreentrant
@external
def addLiquidityConcentrated(
    _legoId: uint256,
    _pool: address,
    _nftTokenId: uint256,
    _tokenA: address,
    _tokenB: address,
    _amountA: uint256 = max_value(uint256),
    _amountB: uint256 = max_value(uint256),
    _minAmountA: uint256 = 0,
    _minAmountB: uint256 = 0,
    _extraData: bytes32 = empty(bytes32),
) -> (uint256, uint256, uint256):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_legoId` | `uint256` | Concentrated AMM strategy ID |
| `_pool` | `address` | Pool address |
| `_nftTokenId` | `uint256` | Position NFT ID (0 for new) |
| `_tokenA` | `address` | First token |
| `_tokenB` | `address` | Second token |
| `_amountA` | `uint256` | Amount of token A |
| `_amountB` | `uint256` | Amount of token B |
| `_minAmountA` | `uint256` | Minimum token A to use |
| `_minAmountB` | `uint256` | Minimum token B to use |
| `_extraData` | `bytes32` | Position parameters |

#### Returns

| Type | Description |
|------|-------------|
| `(uint256, uint256, uint256)` | (amountAUsed, amountBUsed, nftTokenId) |

#### Access

Only callable by Switchboard-registered contracts

#### Events Emitted

- `WalletAction` - Concentrated liquidity details (op code 32)

#### Example Usage
```python
# Add to Uniswap V3 position
amount_a, amount_b, nft_id = endaoment.addLiquidityConcentrated(
    3,  # UniV3 Lego ID
    univ3_pool.address,
    0,  # Create new position
    usdc.address,
    weth.address,
    1000_000000,  # 1000 USDC
    1_000000000000000000,  # 1 ETH
    950_000000,  # Min 950 USDC
    950000000000000000,  # Min 0.95 ETH
    encode_tick_range(-887220, 887220),  # Full range
    sender=treasury_manager.address
)
```

### `removeLiquidityConcentrated`

Removes liquidity from a concentrated liquidity position.

```vyper
@nonreentrant
@external
def removeLiquidityConcentrated(
    _legoId: uint256,
    _pool: address,
    _nftTokenId: uint256,
    _liquidity: uint256 = max_value(uint256),
    _minAmountA: uint256 = 0,
    _minAmountB: uint256 = 0,
    _extraData: bytes32 = empty(bytes32),
) -> (uint256, uint256):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_legoId` | `uint256` | Concentrated AMM strategy ID |
| `_pool` | `address` | Pool address |
| `_nftTokenId` | `uint256` | Position NFT ID |
| `_liquidity` | `uint256` | Liquidity to remove |
| `_minAmountA` | `uint256` | Minimum token A out |
| `_minAmountB` | `uint256` | Minimum token B out |
| `_extraData` | `bytes32` | Strategy-specific data |

#### Returns

| Type | Description |
|------|-------------|
| `(uint256, uint256)` | (amountAReceived, amountBReceived) |

#### Access

Only callable by Switchboard-registered contracts

#### Events Emitted

- `WalletAction` - Removal details (op code 33)

## Utility Functions

### `onERC721Received`

ERC721 receiver implementation for NFT handling.

```vyper
@view
@external
def onERC721Received(
    _operator: address, 
    _owner: address, 
    _tokenId: uint256, 
    _data: Bytes[1024]
) -> bytes4:
```

#### Access

Public view function (ERC721 standard)

### `recoverNft`

Recovers accidentally sent NFTs.

```vyper
@external
def recoverNft(_collection: address, _nftTokenId: uint256, _recipient: address):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_collection` | `address` | NFT collection |
| `_nftTokenId` | `uint256` | Token ID to recover |
| `_recipient` | `address` | Recovery recipient |

#### Access

Only callable by Switchboard-registered contracts

#### Events Emitted

- `EndaomentNftRecovered` - NFT recovery details

## Treasury Management

### `repayPoolDebt`

Repays the debt that was created when minting Green for the stabilizer pool.

```vyper
@nonreentrant
@external
def repayPoolDebt(_amount: uint256 = max_value(uint256)) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_amount` | `uint256` | Amount to repay (max = full debt) |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Amount of debt repaid |

#### Access

Only callable by Switchboard-registered contracts

#### Events Emitted

- `PoolDebtRepaid` - Contains amount repaid and remaining debt

#### Example Usage
```python
# Repay all stabilizer pool debt
debt_repaid = endaoment.repayPoolDebt(
    sender=treasury_manager.address
)
# Returns: Amount of Green burned to repay debt

# Repay partial debt
debt_repaid = endaoment.repayPoolDebt(
    500_000000000000000000,  # Repay 500 Green
    sender=treasury_manager.address
)
```

## Key Mathematical Functions

### Stabilizer Profit Calculation

Calculates net position value for stabilizer operations:

```
profit = lpValue + leftoverGreen - poolDebt
```

Where:
- lpValue = LP tokens × virtual price
- leftoverGreen = Green token balance
- poolDebt = Minted Green for liquidity

### Green Amount Calculation

For adding liquidity when Green ratio < 50%:

```
totalPoolBalance = greenBalance × 100% / greenRatio
targetBalance = totalPoolBalance / 2
greenAdjustFull = (targetBalance - greenBalance) × 2
greenAdjustWeighted = greenAdjustFull × adjustWeight / 100%
```

For removing liquidity when Green ratio > 50%:

```
greenAdjustFull = (greenBalance - targetBalance) × 2
maxRemovable = max(poolDebt, userLpShare × greenBalance)
```

## Testing

For comprehensive test examples, see: [`tests/core/test_endaoment.py`](../../tests/core/test_endaoment.py)