# Ledger Technical Documentation

[📄 View Source Code](../../contracts/data/Ledger.vy)

## Overview

Ledger is the comprehensive data storage engine for Ripe Protocol, maintaining all critical state information from user positions to protocol metrics. It acts as the single source of truth for tracking interactions, financial positions, and rewards calculations across all protocol components.

**Core Functions**:
- **User Tracking**: Vault participation, one-action-per-block enforcement, and account locking
- **Debt Management**: Positions, principals, interest accrual, and liquidation status
- **Rewards System**: Complex points calculations for deposits and borrows
- **Auction Storage**: Active liquidation data with lifecycle management
- **Protocol Data**: Contributor allocations, bond epochs, and pool debt tracking

Built with Addys and DeptBasics modules, Ledger implements a read-heavy, write-controlled architecture. Only authorized contracts can modify state, while extensive bundling functions enable efficient data retrieval for protocol operations.

## Architecture & Modules

Ledger is built using a modular architecture that provides foundational department functionality:

### Addys Module

- **Location**: `contracts/modules/Addys.vy`
- **Purpose**: Provides protocol-wide address resolution and validation
- **Documentation**: See [Addys Technical Documentation](../modules/Addys.md)
- **Key Features**:
  - Access to all protocol contract addresses
  - Validation of authorized callers for state modifications
  - Centralized address management
- **Exported Interface**: Address utilities via `addys.__interface__`

### DeptBasics Module

- **Location**: `contracts/modules/DeptBasics.vy`
- **Purpose**: Provides department-level basic functionality
- **Documentation**: See [DeptBasics Technical Documentation](../modules/DeptBasics.md)
- **Key Features**:
  - Pause mechanism for emergency stops
  - Department interface compliance
  - **No minting capabilities** (disabled for Ledger)
- **Exported Interface**: Department basics via `deptBasics.__interface__`

### Module Initialization

```vyper
initializes: addys
initializes: deptBasics[addys := addys]
```

## System Architecture Diagram

```
+------------------------------------------------------------------------+
|                           Ledger Contract                              |
+------------------------------------------------------------------------+
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                     Data Storage Categories                      |  |
|  |                                                                  |  |
|  |  +--------------+ +--------------+ +--------------+             |  |
|  |  | User Vault   | | Debt Mgmt    | | Points &     |             |  |
|  |  | Tracking     | |              | | Rewards      |             |  |
|  |  | * userVaults | | * userDebt   | | * userDeposit|             |  |
|  |  | * numUser    | | * totalDebt  | |   Points     |             |  |
|  |  |   Vaults     | | * borrowers  | | * globalDep  |             |  |
|  |  | * indexOfV   | | * intervals  | |   Points     |             |  |
|  |  |   ault       | | * unrealized | | * userBorrow |             |  |
|  |  |              | |   Yield      | |   Points     |             |  |
|  |  +--------------+ +--------------+ +--------------+             |  |
|  |                                                                  |  |
|  |  +--------------+ +--------------+ +--------------+             |  |
|  |  | Auction Data | | HR Contrib   | | Bond & Bad   |             |  |
|  |  |              | |              | | Debt Data    |             |  |
|  |  | * fungible   | | * contrib    | | * epochStart |             |  |
|  |  |   Auctions   | |   utors      | | * epochEnd   |             |  |
|  |  | * numFung    | | * indexOfC   | | * badDebt    |             |  |
|  |  |   Auctions   | |   ontrib     | | * ripeAvail  |             |  |
|  |  | * fungLiq    | | * ripeAvail  | |   ForBonds   |             |  |
|  |  |   Users      | |   ForHr      | | * greenPool  |             |  |
|  |  |              | |              | |   Debt       |             |  |
|  |  +--------------+ +--------------+ +--------------+             |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Access Control Matrix                         |  |
|  |                                                                  |  |
|  |  CreditEngine:    debt mgmt, vault registration                 |  |
|  |  AuctionHouse:    auction CRUD, vault registration              |  |
|  |  Lootbox:         points/rewards, vault removal                 |  |
|  |  VaultBook:       stability pool rewards                        |  |
|  |  Teller:          last touch validation, vault registration     |  |
|  |  BondRoom:        bond data, epoch management                   |  |
|  |  HumanResources:  contributor management                        |  |
|  |  Endaoment:       green pool debt tracking                     |  |
|  |  Switchboard:     config updates, account locking              |  |
|  +------------------------------------------------------------------+  |
+------------------------------------------------------------------------+
                                    |
        +---------------------------+---------------------------+
        |                           |                           |
        v                           v                           v
+------------------+    +-------------------+    +------------------+
| Protocol         |    | Data Bundling     |    | Safety           |
| Contracts        |    | Functions         |    | Mechanisms       |
| * Read/Write     |    | * BorrowData      |    | * One action     |
| * State queries  |    |   Bundle          |    |   per block      |
| * Batch updates  |    | * DepositPoints   |    | * Account        |
+------------------+    |   Bundle          |    |   locking        |
                        | * RipeRewards     |    | * Pause control  |
                        |   Bundle          |    +------------------+
                        +-------------------+
```

## Data Structures

### User Debt Information

#### UserDebt Struct

Current debt state for a user:

```vyper
struct UserDebt:
    amount: uint256                   # Current debt amount with interest
    principal: uint256                # Original borrowed amount
    debtTerms: cs.DebtTerms           # Debt configuration parameters
    lastTimestamp: uint256            # Last update timestamp
    inLiquidation: bool               # Liquidation status flag
```

#### IntervalBorrow Struct

Tracks borrowing intervals for analytics:

```vyper
struct IntervalBorrow:
    start: uint256                    # Interval start timestamp
    amount: uint256                   # Amount borrowed in interval
```

#### BorrowDataBundle Struct

Comprehensive borrowing information:

```vyper
struct BorrowDataBundle:
    userDebt: UserDebt
    userBorrowInterval: IntervalBorrow
    isUserBorrower: bool
    numUserVaults: uint256
    totalDebt: uint256
    numBorrowers: uint256
```

### Points and Rewards System

#### RipeRewards Struct

Ripe token reward distribution tracking:

```vyper
struct RipeRewards:
    borrowers: uint256                # Rewards allocated to borrowers
    stakers: uint256                  # Rewards allocated to stakers
    voters: uint256                   # Rewards allocated to voters
    genDepositors: uint256            # Rewards for general depositors
    newRipeRewards: uint256           # New rewards added this update
    lastUpdate: uint256               # Last update timestamp
```

#### UserDepositPoints Struct

Individual user deposit tracking:

```vyper
struct UserDepositPoints:
    balancePoints: uint256            # Accumulated balance points
    lastBalance: uint256              # Last recorded balance
    lastUpdate: uint256               # Last update timestamp
```

#### AssetDepositPoints Struct

Asset-specific deposit metrics:

```vyper
struct AssetDepositPoints:
    balancePoints: uint256            # Total balance points for asset
    lastBalance: uint256              # Last total balance
    lastUsdValue: uint256             # Last USD value
    ripeStakerPoints: uint256         # Points for Ripe stakers
    ripeVotePoints: uint256           # Points for Ripe voters
    ripeGenPoints: uint256            # Points for general participants
    lastUpdate: uint256               # Last update timestamp
    precision: uint256                # Precision for calculations
```

#### GlobalDepositPoints Struct

Protocol-wide deposit metrics:

```vyper
struct GlobalDepositPoints:
    lastUsdValue: uint256             # Total protocol USD value
    ripeStakerPoints: uint256         # Global staker points
    ripeVotePoints: uint256           # Global voter points
    ripeGenPoints: uint256            # Global general points
    lastUpdate: uint256               # Last update timestamp
```

### Auction System

#### FungibleAuction Struct

Active auction information:

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

### Utility Bundles

#### DepositLedgerData Struct

Basic deposit participation info:

```vyper
struct DepositLedgerData:
    isParticipatingInVault: bool
    numUserVaults: uint256
```

#### RipeBondData Struct

Bond market information:

```vyper
struct RipeBondData:
    paymentAmountAvailInEpoch: uint256 # Available payment amount
    ripeAvailForBonds: uint256         # Ripe tokens available for bonds
    badDebt: uint256                   # Current bad debt amount
```

## State Variables

### User Activity Tracking

- `lastTouch: HashMap[address, uint256]` - Last interaction block per user
- `isLockedAccount: HashMap[address, bool]` - Account lock status
- `userVaults: HashMap[address, HashMap[uint256, uint256]]` - User vault participation
- `indexOfVault: HashMap[address, HashMap[uint256, uint256]]` - Vault index mapping
- `numUserVaults: HashMap[address, uint256]` - Count of user's vaults

### Debt Management

- `userDebt: HashMap[address, UserDebt]` - Individual user debt positions
- `totalDebt: uint256` - Protocol-wide total debt
- `borrowers: HashMap[uint256, address]` - Indexed list of borrowers
- `indexOfBorrower: HashMap[address, uint256]` - Borrower index mapping
- `numBorrowers: uint256` - Total number of borrowers
- `borrowIntervals: HashMap[address, IntervalBorrow]` - Borrowing intervals
- `unrealizedYield: uint256` - Accumulated unrealized yield

### Points and Rewards

- `ripeRewards: RipeRewards` - Current reward distribution
- `ripeAvailForRewards: uint256` - Available Ripe for rewards
- `globalDepositPoints: GlobalDepositPoints` - Protocol-wide deposit metrics
- `assetDepositPoints: HashMap[uint256, HashMap[address, AssetDepositPoints]]` - Asset-specific points
- `userDepositPoints: HashMap[address, HashMap[uint256, HashMap[address, UserDepositPoints]]]` - User deposit points
- `userBorrowPoints: HashMap[address, BorrowPoints]` - User borrowing points
- `globalBorrowPoints: BorrowPoints` - Protocol borrowing metrics

### Auction Data

- `fungibleAuctions: HashMap[address, HashMap[uint256, FungibleAuction]]` - Active auctions
- `fungibleAuctionIndex: HashMap[address, HashMap[uint256, HashMap[address, uint256]]]` - Auction indexing
- `numFungibleAuctions: HashMap[address, uint256]` - Auction count per user
- `fungLiqUsers: HashMap[uint256, address]` - Indexed liquidation users
- `indexOfFungLiqUser: HashMap[address, uint256]` - Liquidation user indexing
- `numFungLiqUsers: uint256` - Total liquidation users

### Bond and Contributor Data

- `epochStart: uint256` - Current epoch start time
- `epochEnd: uint256` - Current epoch end time
- `badDebt: uint256` - Outstanding bad debt
- `ripeAvailForBonds: uint256` - Ripe tokens available for bonds
- `contributors: HashMap[uint256, address]` - Indexed contributors
- `ripeAvailForHr: uint256` - Ripe tokens for human resources
- `greenPoolDebt: HashMap[address, uint256]` - Green pool debt tracking

### Inherited State Variables

From [DeptBasics](../modules/DeptBasics.md):

- `isPaused: bool` - Department pause state
- `canMintGreen: bool` - Set to `False`
- `canMintRipe: bool` - Set to `False`

## Constructor

### `__init__`

Initializes the Ledger with RipeHq reference and default values.

```vyper
@deploy
def __init__(_ripeHq: address, _defaults: address):
```

#### Parameters

| Name        | Type      | Description                                     |
| ----------- | --------- | ----------------------------------------------- |
| `_ripeHq`   | `address` | RipeHq contract address                         |
| `_defaults` | `address` | Defaults contract for initial values (optional) |

#### Returns

_Constructor does not return any values_

#### Access

Called only during deployment

#### Example Usage

```python
# Deploy Ledger with defaults
ledger = boa.load(
    "contracts/data/Ledger.vy",
    ripe_hq.address,
    defaults_contract.address
)

# Deploy without defaults
ledger = boa.load(
    "contracts/data/Ledger.vy",
    ripe_hq.address,
    empty(address)
)
```

**Example Output**: Contract deployed with no minting capabilities, reward allocations initialized if defaults provided

## User Activity Management Functions

### `checkAndUpdateLastTouch`

Validates and updates user's last interaction, enforcing one-action-per-block rule.

```vyper
@external
def checkAndUpdateLastTouch(_user: address, _shouldCheck: bool, _mc: address = empty(address)):
```

#### Parameters

| Name           | Type      | Description                                |
| -------------- | --------- | ------------------------------------------ |
| `_user`        | `address` | User address to check/update               |
| `_shouldCheck` | `bool`    | Whether to enforce one-action-per-block    |
| `_mc`          | `address` | Mission Control address (unused parameter) |

#### Returns

_Function does not return any values_

#### Access

Only callable by Teller contract

#### Example Usage

```python
# Enforce one action per block
ledger.checkAndUpdateLastTouch(
    user.address,
    True,  # Check last touch
    sender=teller.address
)

# Update without checking
ledger.checkAndUpdateLastTouch(
    user.address,
    False,  # Skip check
    sender=teller.address
)
```

**Example Output**: Updates `lastTouch[user]` to current block, reverts if already interacted this block

### `setLockedAccount`

Locks or unlocks a user account to prevent interactions.

```vyper
@external
def setLockedAccount(_wallet: address, _shouldLock: bool):
```

#### Parameters

| Name          | Type      | Description                   |
| ------------- | --------- | ----------------------------- |
| `_wallet`     | `address` | Wallet address to lock/unlock |
| `_shouldLock` | `bool`    | True to lock, False to unlock |

#### Returns

_Function does not return any values_

#### Access

Only callable by Switchboard-registered contracts

#### Example Usage

```python
# Lock suspicious account
ledger.setLockedAccount(
    suspicious_user.address,
    True,  # Lock account
    sender=security_manager.address  # Must be in Switchboard
)

# Unlock account
ledger.setLockedAccount(
    reformed_user.address,
    False,  # Unlock
    sender=security_manager.address
)
```

## User Vault Management Functions

### `isParticipatingInVault`

Checks if a user is participating in a specific vault.

```vyper
@view
@external
def isParticipatingInVault(_user: address, _vaultId: uint256) -> bool:
```

#### Parameters

| Name       | Type      | Description           |
| ---------- | --------- | --------------------- |
| `_user`    | `address` | User address to check |
| `_vaultId` | `uint256` | Vault ID to check     |

#### Returns

| Type   | Description                        |
| ------ | ---------------------------------- |
| `bool` | True if user participates in vault |

#### Access

Public view function

#### Example Usage

```python
# Check vault participation
is_participant = ledger.isParticipatingInVault(
    user.address,
    1  # Vault ID
)
# Returns: True if user has deposits in vault 1
```

### `getNumUserVaults`

Returns the number of vaults a user participates in.

```vyper
@view
@external
def getNumUserVaults(_user: address) -> uint256:
```

#### Parameters

| Name    | Type      | Description  |
| ------- | --------- | ------------ |
| `_user` | `address` | User address |

#### Returns

| Type      | Description                           |
| --------- | ------------------------------------- |
| `uint256` | Number of vaults user participates in |

#### Access

Public view function

#### Example Usage

```python
# Get user's vault count
vault_count = ledger.getNumUserVaults(user.address)
# Returns: 3 (if user participates in 3 vaults)
```

### `addVaultToUser`

Adds a vault to user's participation list.

```vyper
@external
def addVaultToUser(_user: address, _vaultId: uint256):
```

#### Parameters

| Name       | Type      | Description     |
| ---------- | --------- | --------------- |
| `_user`    | `address` | User address    |
| `_vaultId` | `uint256` | Vault ID to add |

#### Returns

_Function does not return any values_

#### Access

Only callable by Teller, CreditEngine, AuctionHouse, or HumanResources

#### Example Usage

```python
# Add user to vault (typically called during deposit)
ledger.addVaultToUser(
    user.address,
    2,  # Vault ID
    sender=teller.address
)
```

**Example Output**: User registered in vault, fails gracefully if already participating

### `removeVaultFromUser`

Removes a vault from user's participation list.

```vyper
@external
def removeVaultFromUser(_user: address, _vaultId: uint256):
```

#### Parameters

| Name       | Type      | Description        |
| ---------- | --------- | ------------------ |
| `_user`    | `address` | User address       |
| `_vaultId` | `uint256` | Vault ID to remove |

#### Returns

_Function does not return any values_

#### Access

Only callable by Lootbox contract

#### Example Usage

```python
# Remove user from vault (typically called during full withdrawal)
ledger.removeVaultFromUser(
    user.address,
    2,  # Vault ID
    sender=lootbox.address
)
```

### `getDepositLedgerData`

Returns comprehensive deposit information for a user and vault.

```vyper
@view
@external
def getDepositLedgerData(_user: address, _vaultId: uint256) -> DepositLedgerData:
```

#### Parameters

| Name       | Type      | Description  |
| ---------- | --------- | ------------ |
| `_user`    | `address` | User address |
| `_vaultId` | `uint256` | Vault ID     |

#### Returns

| Type                | Description                                      |
| ------------------- | ------------------------------------------------ |
| `DepositLedgerData` | Struct with participation status and vault count |

#### Access

Public view function

#### Example Usage

```python
# Get deposit data
deposit_data = ledger.getDepositLedgerData(user.address, 1)
# Returns: DepositLedgerData with participation status and vault count
```

## Debt Management Functions

### `setUserDebt`

Updates a user's debt position and related metrics.

```vyper
@external
def setUserDebt(_user: address, _userDebt: UserDebt, _newYield: uint256, _interval: IntervalBorrow):
```

#### Parameters

| Name        | Type             | Description             |
| ----------- | ---------------- | ----------------------- |
| `_user`     | `address`        | User address            |
| `_userDebt` | `UserDebt`       | New debt information    |
| `_newYield` | `uint256`        | Additional yield to add |
| `_interval` | `IntervalBorrow` | Borrowing interval data |

#### Returns

_Function does not return any values_

#### Access

Only callable by CreditEngine contract

#### Example Usage

```python
# Update user debt after borrowing
new_debt = UserDebt(
    amount=5000_000000000000000000,     # 5000 debt with interest
    principal=4800_000000000000000000,  # 4800 original borrow
    debtTerms=debt_terms,
    lastTimestamp=block.timestamp,
    inLiquidation=False
)

ledger.setUserDebt(
    user.address,
    new_debt,
    50_000000000000000000,  # 50 additional yield
    borrow_interval,
    sender=credit_engine.address
)
```

**Example Output**: Updates debt, registers as borrower if new, removes auctions if exiting liquidation

### `flushUnrealizedYield`

Retrieves and resets unrealized yield accumulation.

```vyper
@external
def flushUnrealizedYield() -> uint256:
```

#### Parameters

_Function has no parameters_

#### Returns

| Type      | Description                |
| --------- | -------------------------- |
| `uint256` | Amount of unrealized yield |

#### Access

Only callable by CreditEngine contract

#### Example Usage

```python
# Get unrealized yield for distribution
yield_amount = ledger.flushUnrealizedYield(sender=credit_engine.address)
# Returns: 1000000000000000000 (1 token of accumulated yield)
```

### `hasDebt`

Checks if a user has outstanding debt.

```vyper
@view
@external
def hasDebt(_user: address) -> bool:
```

#### Parameters

| Name    | Type      | Description           |
| ------- | --------- | --------------------- |
| `_user` | `address` | User address to check |

#### Returns

| Type   | Description           |
| ------ | --------------------- |
| `bool` | True if user has debt |

#### Access

Public view function

#### Example Usage

```python
# Check if user has debt
has_debt = ledger.hasDebt(user.address)
# Returns: True if user.debt.amount > 0
```

### `getBorrowDataBundle`

Returns comprehensive borrowing information for a user.

```vyper
@view
@external
def getBorrowDataBundle(_user: address) -> BorrowDataBundle:
```

#### Parameters

| Name    | Type      | Description  |
| ------- | --------- | ------------ |
| `_user` | `address` | User address |

#### Returns

| Type               | Description                    |
| ------------------ | ------------------------------ |
| `BorrowDataBundle` | Complete borrowing information |

#### Access

Public view function

#### Example Usage

```python
# Get complete borrow data
borrow_data = ledger.getBorrowDataBundle(user.address)
# Returns: BorrowDataBundle with debt, intervals, and protocol metrics
```

### `getRepayDataBundle`

Returns debt information needed for repayment calculations.

```vyper
@view
@external
def getRepayDataBundle(_user: address) -> RepayDataBundle:
```

#### Parameters

| Name    | Type      | Description  |
| ------- | --------- | ------------ |
| `_user` | `address` | User address |

#### Returns

| Type              | Description                |
| ----------------- | -------------------------- |
| `RepayDataBundle` | Debt and vault information |

#### Access

Public view function

#### Example Usage

```python
# Get repayment data
repay_data = ledger.getRepayDataBundle(user.address)
# Returns: RepayDataBundle with current debt and vault count
```

### `isBorrower`

Checks if a user is registered as a borrower.

```vyper
@view
@external
def isBorrower(_user: address) -> bool:
```

#### Parameters

| Name    | Type      | Description  |
| ------- | --------- | ------------ |
| `_user` | `address` | User address |

#### Returns

| Type   | Description                         |
| ------ | ----------------------------------- |
| `bool` | True if user is registered borrower |

#### Access

Public view function

### `isUserInLiquidation`

Checks if a user is currently in liquidation.

```vyper
@view
@external
def isUserInLiquidation(_user: address) -> bool:
```

#### Parameters

| Name    | Type      | Description  |
| ------- | --------- | ------------ |
| `_user` | `address` | User address |

#### Returns

| Type   | Description                    |
| ------ | ------------------------------ |
| `bool` | True if user is in liquidation |

#### Access

Public view function

## Points and Rewards Functions

### `setRipeRewards`

Updates the Ripe token reward distribution.

```vyper
@external
def setRipeRewards(_ripeRewards: RipeRewards):
```

#### Parameters

| Name           | Type          | Description             |
| -------------- | ------------- | ----------------------- |
| `_ripeRewards` | `RipeRewards` | New reward distribution |

#### Returns

_Function does not return any values_

#### Access

Only callable by Lootbox contract

#### Example Usage

```python
# Update reward distribution
new_rewards = RipeRewards(
    borrowers=1000_000000000000000000,
    stakers=2000_000000000000000000,
    voters=500_000000000000000000,
    genDepositors=1500_000000000000000000,
    newRipeRewards=5000_000000000000000000,
    lastUpdate=block.timestamp
)

ledger.setRipeRewards(
    new_rewards,
    sender=lootbox.address
)
```

### `setRipeAvailForRewards`

Sets the amount of Ripe tokens available for rewards.

```vyper
@external
def setRipeAvailForRewards(_amount: uint256):
```

#### Parameters

| Name      | Type      | Description                     |
| --------- | --------- | ------------------------------- |
| `_amount` | `uint256` | Amount of Ripe tokens available |

#### Returns

_Function does not return any values_

#### Access

Only callable by Switchboard-registered contracts

#### Example Usage

```python
# Set available rewards
ledger.setRipeAvailForRewards(
    10000_000000000000000000,  # 10,000 RIPE
    sender=rewards_manager.address
)
```

### `didGetRewardsFromStabClaims`

Reduces available rewards after stability pool claims.

```vyper
@external
def didGetRewardsFromStabClaims(_amount: uint256):
```

#### Parameters

| Name      | Type      | Description               |
| --------- | --------- | ------------------------- |
| `_amount` | `uint256` | Amount of rewards claimed |

#### Returns

_Function does not return any values_

#### Access

Only callable by VaultBook contract

#### Example Usage

```python
# Record stability pool reward claim
ledger.didGetRewardsFromStabClaims(
    500_000000000000000000,  # 500 RIPE claimed
    sender=vault_book.address
)
```

### `setDepositPointsAndRipeRewards`

Updates deposit points and reward calculations.

```vyper
@external
def setDepositPointsAndRipeRewards(
    _user: address,
    _vaultId: uint256,
    _asset: address,
    _userPoints: UserDepositPoints,
    _assetPoints: AssetDepositPoints,
    _globalPoints: GlobalDepositPoints,
    _ripeRewards: RipeRewards,
):
```

#### Parameters

| Name            | Type                  | Description                                    |
| --------------- | --------------------- | ---------------------------------------------- |
| `_user`         | `address`             | User address (can be empty for global updates) |
| `_vaultId`      | `uint256`             | Vault ID                                       |
| `_asset`        | `address`             | Asset address                                  |
| `_userPoints`   | `UserDepositPoints`   | User-specific point data                       |
| `_assetPoints`  | `AssetDepositPoints`  | Asset-specific point data                      |
| `_globalPoints` | `GlobalDepositPoints` | Protocol-wide point data                       |
| `_ripeRewards`  | `RipeRewards`         | Updated reward distribution                    |

#### Access

Only callable by Lootbox contract

### `setBorrowPointsAndRipeRewards`

Updates borrowing points and reward calculations.

```vyper
@external
def setBorrowPointsAndRipeRewards(
    _user: address,
    _userPoints: BorrowPoints,
    _globalPoints: BorrowPoints,
    _ripeRewards: RipeRewards,
):
```

#### Parameters

| Name            | Type           | Description                                    |
| --------------- | -------------- | ---------------------------------------------- |
| `_user`         | `address`      | User address (can be empty for global updates) |
| `_userPoints`   | `BorrowPoints` | User borrowing points                          |
| `_globalPoints` | `BorrowPoints` | Global borrowing points                        |
| `_ripeRewards`  | `RipeRewards`  | Updated reward distribution                    |

#### Access

Only callable by Lootbox contract

### `getRipeRewardsBundle`

Returns current reward distribution and availability.

```vyper
@view
@external
def getRipeRewardsBundle() -> RipeRewardsBundle:
```

#### Returns

| Type                | Description                      |
| ------------------- | -------------------------------- |
| `RipeRewardsBundle` | Current rewards and availability |

#### Access

Public view function

### `getBorrowPointsBundle`

Returns borrowing points data for a user.

```vyper
@view
@external
def getBorrowPointsBundle(_user: address) -> BorrowPointsBundle:
```

#### Parameters

| Name    | Type      | Description  |
| ------- | --------- | ------------ |
| `_user` | `address` | User address |

#### Returns

| Type                 | Description                      |
| -------------------- | -------------------------------- |
| `BorrowPointsBundle` | User and global borrowing points |

#### Access

Public view function

### `getDepositPointsBundle`

Returns deposit points data for a user, vault, and asset.

```vyper
@view
@external
def getDepositPointsBundle(_user: address, _vaultId: uint256, _asset: address) -> DepositPointsBundle:
```

#### Parameters

| Name       | Type      | Description                 |
| ---------- | --------- | --------------------------- |
| `_user`    | `address` | User address (can be empty) |
| `_vaultId` | `uint256` | Vault ID                    |
| `_asset`   | `address` | Asset address               |

#### Returns

| Type                  | Description                            |
| --------------------- | -------------------------------------- |
| `DepositPointsBundle` | User, asset, and global deposit points |

#### Access

Public view function

## Auction Management Functions

### `hasFungibleAuctions`

Checks if a liquidated user has active auctions.

```vyper
@view
@external
def hasFungibleAuctions(_liqUser: address) -> bool:
```

#### Parameters

| Name       | Type      | Description             |
| ---------- | --------- | ----------------------- |
| `_liqUser` | `address` | Liquidated user address |

#### Returns

| Type   | Description                      |
| ------ | -------------------------------- |
| `bool` | True if user has active auctions |

#### Access

Public view function

### `createNewFungibleAuction`

Creates a new fungible auction for liquidated collateral.

```vyper
@external
def createNewFungibleAuction(_auc: FungibleAuction) -> uint256:
```

#### Parameters

| Name   | Type              | Description           |
| ------ | ----------------- | --------------------- |
| `_auc` | `FungibleAuction` | Auction configuration |

#### Returns

| Type      | Description                              |
| --------- | ---------------------------------------- |
| `uint256` | Auction ID (0 if auction already exists) |

#### Access

Only callable by AuctionHouse contract

#### Example Usage

```python
# Create new auction
auction = FungibleAuction(
    liqUser=underwater_user.address,
    vaultId=1,
    asset=weth.address,
    startDiscount=200,      # 2% start discount
    maxDiscount=2000,       # 20% max discount
    startBlock=block.number,
    endBlock=block.number + 1000,
    isActive=True
)

auction_id = ledger.createNewFungibleAuction(
    auction,
    sender=auction_house.address
)
```

### `removeFungibleAuction`

Removes a specific fungible auction.

```vyper
@external
def removeFungibleAuction(_liqUser: address, _vaultId: uint256, _asset: address):
```

#### Parameters

| Name       | Type      | Description             |
| ---------- | --------- | ----------------------- |
| `_liqUser` | `address` | Liquidated user address |
| `_vaultId` | `uint256` | Vault ID                |
| `_asset`   | `address` | Asset address           |

#### Access

Only callable by AuctionHouse contract

### `setFungibleAuction`

Updates an existing fungible auction.

```vyper
@external
def setFungibleAuction(
    _liqUser: address,
    _vaultId: uint256,
    _asset: address,
    _auc: FungibleAuction,
) -> bool:
```

#### Parameters

| Name       | Type              | Description             |
| ---------- | ----------------- | ----------------------- |
| `_liqUser` | `address`         | Liquidated user address |
| `_vaultId` | `uint256`         | Vault ID                |
| `_asset`   | `address`         | Asset address           |
| `_auc`     | `FungibleAuction` | Updated auction data    |

#### Returns

| Type   | Description                                     |
| ------ | ----------------------------------------------- |
| `bool` | True if auction was updated, False if not found |

#### Access

Only callable by AuctionHouse contract

### `removeAllFungibleAuctions`

Removes all auctions for a liquidated user.

```vyper
@external
def removeAllFungibleAuctions(_liqUser: address):
```

#### Parameters

| Name       | Type      | Description             |
| ---------- | --------- | ----------------------- |
| `_liqUser` | `address` | Liquidated user address |

#### Access

Only callable by AuctionHouse or CreditEngine contracts

### `getFungibleAuction`

Returns auction data for a specific asset.

```vyper
@view
@external
def getFungibleAuction(_liqUser: address, _vaultId: uint256, _asset: address) -> FungibleAuction:
```

#### Parameters

| Name       | Type      | Description             |
| ---------- | --------- | ----------------------- |
| `_liqUser` | `address` | Liquidated user address |
| `_vaultId` | `uint256` | Vault ID                |
| `_asset`   | `address` | Asset address           |

#### Returns

| Type              | Description  |
| ----------------- | ------------ |
| `FungibleAuction` | Auction data |

#### Access

Public view function

### `getFungibleAuctionDuringPurchase`

Returns auction data only if user is still in liquidation.

```vyper
@view
@external
def getFungibleAuctionDuringPurchase(_liqUser: address, _vaultId: uint256, _asset: address) -> FungibleAuction:
```

#### Parameters

| Name       | Type      | Description             |
| ---------- | --------- | ----------------------- |
| `_liqUser` | `address` | Liquidated user address |
| `_vaultId` | `uint256` | Vault ID                |
| `_asset`   | `address` | Asset address           |

#### Returns

| Type              | Description                                |
| ----------------- | ------------------------------------------ |
| `FungibleAuction` | Auction data (empty if not in liquidation) |

#### Access

Public view function

### `hasFungibleAuction`

Checks if a specific auction exists.

```vyper
@view
@external
def hasFungibleAuction(_liqUser: address, _vaultId: uint256, _asset: address) -> bool:
```

#### Parameters

| Name       | Type      | Description             |
| ---------- | --------- | ----------------------- |
| `_liqUser` | `address` | Liquidated user address |
| `_vaultId` | `uint256` | Vault ID                |
| `_asset`   | `address` | Asset address           |

#### Returns

| Type   | Description            |
| ------ | ---------------------- |
| `bool` | True if auction exists |

#### Access

Public view function

## Human Resources Functions

### `isHrContributor`

Checks if an address is registered as a contributor.

```vyper
@view
@external
def isHrContributor(_contributor: address) -> bool:
```

#### Parameters

| Name           | Type      | Description         |
| -------------- | --------- | ------------------- |
| `_contributor` | `address` | Contributor address |

#### Returns

| Type   | Description                    |
| ------ | ------------------------------ |
| `bool` | True if registered contributor |

#### Access

Public view function

### `addHrContributor`

Registers a new contributor and allocates compensation.

```vyper
@external
def addHrContributor(_contributor: address, _compensation: uint256):
```

#### Parameters

| Name            | Type      | Description                   |
| --------------- | --------- | ----------------------------- |
| `_contributor`  | `address` | Contributor address           |
| `_compensation` | `uint256` | Compensation amount to deduct |

#### Returns

_Function does not return any values_

#### Access

Only callable by HumanResources contract

#### Example Usage

```python
# Add new contributor
ledger.addHrContributor(
    contributor.address,
    5000_000000000000000000,  # 5000 RIPE compensation
    sender=human_resources.address
)
```

### `setRipeAvailForHr`

Sets the amount of Ripe tokens available for human resources.

```vyper
@external
def setRipeAvailForHr(_amount: uint256):
```

#### Parameters

| Name      | Type      | Description             |
| --------- | --------- | ----------------------- |
| `_amount` | `uint256` | Amount available for HR |

#### Access

Only callable by Switchboard-registered contracts

### `refundRipeAfterCancelPaycheck`

Refunds Ripe tokens after canceling a paycheck.

```vyper
@external
def refundRipeAfterCancelPaycheck(_amount: uint256):
```

#### Parameters

| Name      | Type      | Description      |
| --------- | --------- | ---------------- |
| `_amount` | `uint256` | Amount to refund |

#### Access

Only callable by HumanResources contract

## Bond Market Functions

### `getEpochData`

Returns current epoch start and end times.

```vyper
@view
@external
def getEpochData() -> (uint256, uint256):
```

#### Returns

| Type                 | Description                    |
| -------------------- | ------------------------------ |
| `(uint256, uint256)` | Epoch start and end timestamps |

#### Access

Public view function

### `getRipeBondData`

Returns comprehensive bond market information.

```vyper
@view
@external
def getRipeBondData() -> RipeBondData:
```

#### Returns

| Type           | Description                                               |
| -------------- | --------------------------------------------------------- |
| `RipeBondData` | Bond market data including available amounts and bad debt |

#### Access

Public view function

### `setRipeAvailForBonds`

Sets the amount of Ripe tokens available for bonds.

```vyper
@external
def setRipeAvailForBonds(_amount: uint256):
```

#### Parameters

| Name      | Type      | Description                |
| --------- | --------- | -------------------------- |
| `_amount` | `uint256` | Amount available for bonds |

#### Access

Only callable by Switchboard-registered contracts

### `setBadDebt`

Updates the current bad debt amount.

```vyper
@external
def setBadDebt(_amount: uint256):
```

#### Parameters

| Name      | Type      | Description         |
| --------- | --------- | ------------------- |
| `_amount` | `uint256` | New bad debt amount |

#### Access

Only callable by Switchboard-registered contracts

### `didClearBadDebt`

Records bad debt clearance through bond purchases.

```vyper
@external
def didClearBadDebt(_amount: uint256, _ripeAmount: uint256):
```

#### Parameters

| Name          | Type      | Description                |
| ------------- | --------- | -------------------------- |
| `_amount`     | `uint256` | Amount of bad debt cleared |
| `_ripeAmount` | `uint256` | Amount of Ripe paid out    |

#### Access

Only callable by BondRoom contract

### `didPurchaseRipeBond`

Records a Ripe bond purchase transaction.

```vyper
@external
def didPurchaseRipeBond(_amountPaid: uint256, _ripePayout: uint256):
```

#### Parameters

| Name          | Type      | Description             |
| ------------- | --------- | ----------------------- |
| `_amountPaid` | `uint256` | Amount paid for bonds   |
| `_ripePayout` | `uint256` | Amount of Ripe received |

#### Access

Only callable by BondRoom contract

### `setEpochData`

Updates epoch timing and available payment amounts.

```vyper
@external
def setEpochData(_epochStart: uint256, _epochEnd: uint256, _amountAvailInEpoch: uint256):
```

#### Parameters

| Name                  | Type      | Description                       |
| --------------------- | --------- | --------------------------------- |
| `_epochStart`         | `uint256` | Epoch start timestamp             |
| `_epochEnd`           | `uint256` | Epoch end timestamp               |
| `_amountAvailInEpoch` | `uint256` | Payment amount available in epoch |

#### Access

Only callable by BondRoom contract

## Endaoment Functions

### `updateGreenPoolDebt`

Updates debt tracking for Green token pools.

```vyper
@external
def updateGreenPoolDebt(_pool: address, _amount: uint256, _isIncrement: bool):
```

#### Parameters

| Name           | Type      | Description                    |
| -------------- | --------- | ------------------------------ |
| `_pool`        | `address` | Pool address                   |
| `_amount`      | `uint256` | Amount to add or subtract      |
| `_isIncrement` | `bool`    | True to add, False to subtract |

#### Returns

_Function does not return any values_

#### Access

Only callable by Endaoment contract

#### Example Usage

```python
# Increase pool debt
ledger.updateGreenPoolDebt(
    green_pool.address,
    1000_000000000000000000,  # 1000 tokens
    True,  # Increment
    sender=endaoment.address
)

# Decrease pool debt
ledger.updateGreenPoolDebt(
    green_pool.address,
    500_000000000000000000,   # 500 tokens
    False,  # Decrement
    sender=endaoment.address
)
```

## Security Considerations

1. **Write Protection**: Only authorized protocol contracts can modify state
2. **One-Action-Per-Block**: Prevents flash loan attacks and ensures state consistency
3. **No User Access**: All functions require protocol contract authorization
4. **Account Locking**: Provides mechanism to lock compromised accounts
5. **Data Integrity**: Read-only contract ensures data cannot be corrupted
6. **Points Manipulation**: Reward calculations must be carefully validated by callers
7. **No Token Handling**: Ledger never handles tokens directly, only tracks data

## Testing

For comprehensive test examples, see: [`tests/data/test_ledger.py`](../../tests/data/test_ledger.py)
