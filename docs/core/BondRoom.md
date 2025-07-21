# BondRoom Technical Documentation

## Overview

BondRoom serves as the decentralized bond marketplace for the Ripe Protocol ecosystem. Think of it as a sophisticated financial instrument that allows users to purchase Ripe tokens at a discount in exchange for providing stable assets to the protocol's treasury. It implements dynamic pricing based on epoch-based availability, provides lock-up bonuses for longer commitments, integrates boost mechanics for additional rewards, and automatically handles bad debt repayment when needed.

At its core, BondRoom manages three fundamental responsibilities:

**1. Epoch-Based Bond Sales**: Implements time-boxed sales periods (epochs) with limited availability per epoch. This creates predictable supply release and prevents market manipulation while ensuring fair access to bonds for all participants.

**2. Dynamic Pricing with Bonuses**: Calculates bond prices dynamically based on epoch progress (starting high, decreasing over time), offers lock-up bonuses for users who commit their Ripe tokens for longer periods, and integrates with external boost mechanics for additional rewards based on user activity.

**3. Bad Debt Management**: Automatically allocates a portion of bond proceeds to repay protocol bad debt when it exists. This creates a self-healing mechanism where bond sales help restore protocol health while still rewarding purchasers.

For technical readers, BondRoom implements sophisticated bond economics including linear pricing curves within epochs, configurable lock duration bonuses up to 10x, integration with BondBooster contracts for activity-based rewards, automatic epoch rollovers with configurable delays, and whitelist support for restricted access. The contract ensures atomic execution of bond purchases while maintaining strict accounting through the Ledger.

## Architecture & Modules

BondRoom is built using a modular architecture with the following components:

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
  - Ripe token minting capability (for bond payouts)
  - No Green minting capability
- **Exported Interface**: Department basics via `deptBasics.__interface__`

### Module Initialization
```vyper
initializes: addys
initializes: deptBasics[addys := addys]
```

## System Architecture Diagram

```
+------------------------------------------------------------------------+
|                         BondRoom Contract                              |
+------------------------------------------------------------------------+
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                      Bond Purchase Flow                          |  |
|  |                                                                  |  |
|  |  1. User Initiates Purchase                                      |  |
|  |     - Specify payment asset & amount                             |  |
|  |     - Optional lock duration for bonus                           |  |
|  |                                                                  |  |
|  |  2. Epoch & Availability Check                                   |  |
|  |     - Refresh epoch if expired                                   |  |
|  |     - Check remaining availability                               |  |
|  |     - Calculate purchase amount (min of request/available)       |  |
|  |                                                                  |  |
|  |  3. Price Calculation                                             |  |
|  |     - Base: ripePerUnit = min + (progress * (max - min))         |  |
|  |     - Lock bonus: up to maxRipePerUnitLockBonus                  |  |
|  |     - Boost bonus: from BondBooster contract                     |  |
|  |                                                                  |  |
|  |  4. Bad Debt Handling (if exists)                                |  |
|  |     - Calculate USD value of payment                             |  |
|  |     - Allocate portion to bad debt repayment                     |  |
|  |     - Reduce user's Ripe payout proportionally                   |  |
|  |                                                                  |  |
|  |  5. Token Distribution                                            |  |
|  |     - Payment → Endaoment treasury                               |  |
|  |     - Ripe → User (direct) or Gov Vault (if locked)             |  |
|  |     - Refund excess payment to caller                            |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                      Epoch Management                            |  |
|  |                                                                  |  |
|  |  Epoch States:                                                   |  |
|  |  - Not Started: No epochs configured yet                         |  |
|  |  - Active: Current block within [start, end)                     |  |
|  |  - Expired: Past end block, needs refresh                        |  |
|  |  - Auto-Restart: Triggered when epoch sells out                  |  |
|  |                                                                  |  |
|  |  Pricing Curve (within epoch):                                   |  |
|  |   Price                                                           |  |
|  |     ^                                                             |  |
|  |  max|.                                                            |  |
|  |     | '.                                                          |  |
|  |     |   '.                                                        |  |
|  |     |     '.                                                      |  |
|  |  min|-------'                                                     |  |
|  |     +---------> Progress (0% to 100%)                            |  |
|  +------------------------------------------------------------------+  |
+------------------------------------------------------------------------+
                                    |
        +---------------------------+---------------------------+
        |                           |                           |
        v                           v                           v
+------------------+    +-------------------+    +------------------+
| MissionControl   |    | Ledger            |    | Endaoment        |
| * Bond configs   |    | * Epoch tracking  |    | * Receives       |
| * User settings  |    | * Bad debt data   |    |   payments       |
| * Pricing params |    | * Bond accounting |    | * Treasury mgmt  |
+------------------+    +-------------------+    +------------------+
        |                           |                           |
        v                           v                           v
+------------------+    +-------------------+    +------------------+
| BondBooster      |    | Teller            |    | Ripe Token       |
| * Activity boost |    | * Deposit handler |    | * Minted for     |
| * Unit tracking  |    | * Lock management |    |   bond payouts   |
+------------------+    +-------------------+    +------------------+
```

## Data Structures

### PurchaseRipeBondConfig Struct
Configuration for bond purchases (from MissionControl):
```vyper
struct PurchaseRipeBondConfig:
    asset: address                    # Payment asset accepted
    amountPerEpoch: uint256          # Max payment amount per epoch
    canBond: bool                    # Global bond toggle
    minRipePerUnit: uint256          # Min Ripe per payment unit
    maxRipePerUnit: uint256          # Max Ripe per payment unit
    maxRipePerUnitLockBonus: uint256 # Max lock bonus percentage
    epochLength: uint256             # Blocks per epoch
    shouldAutoRestart: bool          # Auto-restart on sellout
    restartDelayBlocks: uint256      # Delay before new epoch
    minLockDuration: uint256         # Min lock for bonus
    maxLockDuration: uint256         # Max lock duration
    canAnyoneBondForUser: bool       # Allow proxy purchases
    isUserAllowed: bool              # Whitelist check
```

### RipeBondData Struct
Current bond sale state (from Ledger):
```vyper
struct RipeBondData:
    paymentAmountAvailInEpoch: uint256  # Remaining in current epoch
    ripeAvailForBonds: uint256          # Total Ripe available
    badDebt: uint256                    # Outstanding bad debt
```

## State Variables

### Contract State
- `bondBooster: public(address)` - Optional boost calculator contract

### Constants
- `HUNDRED_PERCENT: uint256 = 100_00` - 100.00% in basis points
- `RIPE_GOV_VAULT_ID: uint256 = 2` - Governance vault for locked Ripe

### Inherited State Variables
From [DeptBasics](../modules/DeptBasics.md):
- `isPaused: bool` - Department pause state
- `canMintRipe: bool` - Set to `True` for bond payouts

## Constructor

### `__init__`

Initializes BondRoom with Ripe minting capability and optional boost contract.

```vyper
@deploy
def __init__(_ripeHq: address, _bondBooster: address):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_ripeHq` | `address` | RipeHq contract address |
| `_bondBooster` | `address` | Optional boost calculator (can be empty) |

#### Returns

*Constructor does not return any values*

#### Access

Called only during deployment

#### Example Usage
```python
# Deploy BondRoom with boost mechanics
bond_room = boa.load(
    "contracts/core/BondRoom.vy",
    ripe_hq.address,
    bond_booster.address
)
```

**Example Output**: Contract deployed with Ripe minting enabled for bonds

## Bond Purchase Functions

### `purchaseRipeBond`

Purchases Ripe bonds using payment assets with optional lock-up.

```vyper
@external
def purchaseRipeBond(
    _recipient: address,
    _paymentAsset: address,
    _paymentAmount: uint256,
    _lockDuration: uint256,
    _caller: address,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_recipient` | `address` | Recipient of Ripe tokens |
| `_paymentAsset` | `address` | Asset used for payment |
| `_paymentAmount` | `uint256` | Amount to spend (max) |
| `_lockDuration` | `uint256` | Lock duration in blocks (0 for no lock) |
| `_caller` | `address` | Transaction initiator |
| `_a` | `addys.Addys` | Cached addresses (optional) |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Total Ripe tokens received |

#### Access

Only callable by Teller contract

#### Events Emitted

- `RipeBondPurchased` - Comprehensive purchase details including:
  - Payment and recipient information
  - Base payout and all bonuses
  - Bad debt allocation
  - Epoch progress
  - Refund amount

#### Example Usage
```python
# Purchase bonds with 1000 USDC, lock for 30 days
ripe_received = bond_room.purchaseRipeBond(
    user.address,
    usdc.address,
    1000_000000,  # 1000 USDC
    30 * 6650,    # ~30 days in blocks
    user.address,
    sender=teller.address
)
```

**Example Output**: Mints and distributes Ripe based on pricing and bonuses

### `previewRipeBondPayout`

Previews potential Ripe payout for given parameters.

```vyper
@view
@external
def previewRipeBondPayout(
    _recipient: address, 
    _lockDuration: uint256 = 0, 
    _paymentAmount: uint256 = max_value(uint256)
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_recipient` | `address` | Potential recipient (for boost calculation) |
| `_lockDuration` | `uint256` | Lock duration for bonus preview |
| `_paymentAmount` | `uint256` | Payment amount (defaults to max available) |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Estimated Ripe payout |

#### Access

Public view function

#### Example Usage
```python
# Preview payout for 1000 USDC with 30-day lock
estimated_ripe = bond_room.previewRipeBondPayout(
    user.address,
    30 * 6650,    # 30 days
    1000_000000   # 1000 USDC
)
# Returns: Estimated Ripe tokens including all bonuses
```

### `previewNextEpoch`

Gets the current or next epoch time boundaries.

```vyper
@view
@external
def previewNextEpoch() -> (uint256, uint256):
```

#### Returns

| Type | Description |
|------|-------------|
| `(uint256, uint256)` | (epochStart, epochEnd) block numbers |

#### Access

Public view function

#### Example Usage
```python
# Check current epoch timing
start_block, end_block = bond_room.previewNextEpoch()
# Returns: (15000000, 15100000) if epoch is active
```

## Epoch Management Functions

### `startBondEpochAtBlock`

Manually starts a new bond epoch at specified block.

```vyper
@external
def startBondEpochAtBlock(_block: uint256):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_block` | `uint256` | Starting block (uses current if in past) |

#### Access

Only callable by Switchboard-registered contracts

#### Example Usage
```python
# Start epoch at block 15000000
bond_room.startBondEpochAtBlock(
    15000000,
    sender=bond_manager.address
)
```

### `refreshBondEpoch`

Updates epoch if current one has expired.

```vyper
@external 
def refreshBondEpoch() -> (uint256, uint256):
```

#### Returns

| Type | Description |
|------|-------------|
| `(uint256, uint256)` | Updated (epochStart, epochEnd) |

#### Access

Only callable by valid Ripe addresses

#### Example Usage
```python
# Refresh expired epoch
start, end = bond_room.refreshBondEpoch(
    sender=credit_engine.address
)
```

### `getLatestEpochBlockTimes`

Calculates what the current epoch should be based on configuration.

```vyper
@view
@external
def getLatestEpochBlockTimes(
    _prevStartBlock: uint256, 
    _prevEndBlock: uint256, 
    _epochLength: uint256
) -> (uint256, uint256, bool):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_prevStartBlock` | `uint256` | Previous epoch start |
| `_prevEndBlock` | `uint256` | Previous epoch end |
| `_epochLength` | `uint256` | Length of epochs in blocks |

#### Returns

| Type | Description |
|------|-------------|
| `(uint256, uint256, bool)` | (newStart, newEnd, didChange) |

#### Access

Public view function

## Bond Booster Functions

### `setBondBooster`

Updates the bond booster contract address.

```vyper
@external
def setBondBooster(_bondBooster: address):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_bondBooster` | `address` | New booster contract (can be empty) |

#### Access

Only callable by Switchboard-registered contracts

#### Events Emitted

- `BondBoosterSet` - New booster address

#### Example Usage
```python
# Set new booster contract
bond_room.setBondBooster(
    new_booster.address,
    sender=bond_config.address
)
```

## Key Mathematical Functions

### Dynamic Pricing Formula

The contract implements linear interpolation for bond pricing within epochs:

```
ripePerUnit = minRipePerUnit + (epochProgress * (maxRipePerUnit - minRipePerUnit))
```

Where:
- epochProgress = (currentBlock - epochStart) / (epochEnd - epochStart)
- Prices start high (maxRipePerUnit) and decrease to minRipePerUnit

### Lock Bonus Calculation

Lock bonuses scale linearly with lock duration:

```
lockBonusRatio = maxLockBonusRatio * (lockDuration - minLock) / (maxLock - minLock)
ripeLockBonus = baseRipePayout * lockBonusRatio / 100%
```

### Bad Debt Allocation

When bad debt exists, bond proceeds are allocated proportionally:

```
If paymentValue <= badDebt:
    ripeForBadDebt = totalRipePayout (all goes to bad debt)
Else:
    ripeForBadDebt = totalRipePayout * badDebt / paymentValue
```

## Testing

For comprehensive test examples, see: [`tests/core/bondRoom/test_ripe_bonds.py`](../../tests/core/bondRoom/test_ripe_bonds.py)