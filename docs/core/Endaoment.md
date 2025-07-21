# Endaoment Technical Documentation

## Overview

Endaoment serves as the protocol-owned treasury and liquidity management hub for the Ripe Protocol ecosystem. Think of it as a sophisticated DeFi treasury that actively manages protocol funds across diverse yield-generating strategies, maintains stablecoin peg stability through automated market making, handles partner liquidity agreements, and processes liquidation proceeds. It acts as the protocol's financial nerve center, ensuring optimal capital efficiency while maintaining Green token stability.

At its core, Endaoment manages four fundamental responsibilities:

**1. Yield Strategy Management**: Deploys protocol funds across various DeFi yield sources using modular "Lego" contracts. These include lending protocols (Aave, Compound), automated market makers (Uniswap, Curve), liquid staking derivatives, and other yield-bearing assets. The system supports both simple yield farming and complex concentrated liquidity positions.

**2. Green Token Stabilization**: Implements an automated stabilizer mechanism that maintains Green's peg by managing liquidity in Curve pools. When Green trades below peg, the system adds more Green liquidity to absorb sell pressure. When Green trades above peg, it removes Green liquidity to reduce supply pressure.

**3. Partner Liquidity Programs**: Facilitates partnerships where external parties provide assets alongside protocol-minted Green tokens in liquidity pools. This creates deeper markets while sharing IL risk with strategic partners.

**4. Treasury Operations**: Receives proceeds from liquidations, bond sales, and protocol fees. Manages ETH/WETH conversions, handles NFT recovery for accidentally sent tokens, and provides comprehensive asset management capabilities with full event logging for transparency.

For technical readers, Endaoment implements advanced treasury mechanics including pluggable yield strategy architecture via UndyLego interface, automated rebalancing algorithms for yield optimization, sophisticated AMM liquidity management with slippage protection, debt tracking for leveraged liquidity provision, and comprehensive event logging for all treasury operations. The contract ensures protocol solvency while maximizing yield generation.

## Architecture & Modules

Endaoment is built using a modular architecture with the following components:

### Addys Module
- **Location**: `contracts/modules/Addys.vy`
- **Purpose**: Provides protocol-wide address resolution
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

## Partner Liquidity Functions

### `addPartnerLiquidity`

Adds liquidity in partnership with external providers.

```vyper
@nonreentrant
@external
def addPartnerLiquidity(
    _partner: address,
    _legoId: uint256,
    _pool: address,
    _asset: address,
    _partnerAmount: uint256,
    _greenAmount: uint256,
    _minLpAmount: uint256 = 0,
    _extraData: bytes32 = empty(bytes32),
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_partner` | `address` | Partner wallet address |
| `_legoId` | `uint256` | AMM strategy ID |
| `_pool` | `address` | Pool address |
| `_asset` | `address` | Partner's asset |
| `_partnerAmount` | `uint256` | Partner contribution |
| `_greenAmount` | `uint256` | Green contribution |
| `_minLpAmount` | `uint256` | Minimum LP tokens |
| `_extraData` | `bytes32` | Pool-specific data |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | LP tokens received |

#### Access

Only callable by Switchboard-registered contracts

#### Events Emitted

- `PartnerLiquidityAdded` - Partnership liquidity details

### `addPartnerLiquidityWithMint`

Creates liquidity by minting Green to pair with partner assets.

```vyper
@nonreentrant
@external
def addPartnerLiquidityWithMint(
    _partner: address,
    _legoId: uint256,
    _pool: address,
    _asset: address,
    _partnerAmount: uint256,
    _minLpAmount: uint256 = 0,
    _extraData: bytes32 = empty(bytes32),
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_partner` | `address` | Partner wallet |
| `_legoId` | `uint256` | Strategy ID |
| `_pool` | `address` | Pool address |
| `_asset` | `address` | Partner asset |
| `_partnerAmount` | `uint256` | Partner contribution |
| `_minLpAmount` | `uint256` | Minimum LP tokens |
| `_extraData` | `bytes32` | Pool-specific data |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | LP tokens received |

#### Access

Only callable by Switchboard-registered contracts

#### Events Emitted

- `PartnerLiquidityMinted` - Mint-and-pair details

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