# HumanResources Technical Documentation

## Overview

HumanResources serves as the compensation management system for human contributors within the Ripe Protocol ecosystem. Think of it as a sophisticated payroll department that handles the creation, management, and distribution of token-based compensation packages for protocol contributors. Unlike traditional payroll systems that deal with fiat currency, HumanResources manages vesting schedules, cliff periods, and automated RIPE token distributions through individually deployed Contributor contracts.

At its core, HumanResources manages five fundamental responsibilities:

**1. Contributor Contract Deployment**: Creates individual Contributor contracts for each team member with customized compensation terms including vesting schedules, cliff periods, and unlock timelines, ensuring transparent and immutable compensation agreements.

**2. Compensation Management**: Oversees the minting and distribution of RIPE tokens according to predefined vesting schedules, handling both the initial allocation and ongoing vesting calculations through the Ripe Gov Vault system.

**3. Two-Phase Security**: Implements time-locked deployment of new contributors requiring both initiation and confirmation phases, preventing rushed decisions and ensuring careful consideration of compensation commitments.

**4. Token Lifecycle Management**: Facilitates the full lifecycle of contributor tokens including minting paychecks, transferring vested tokens to owners, and handling cancellations with appropriate refunds to maintain protocol treasury balance.

**5. Aggregate Tracking**: Provides protocol-wide visibility into total compensation committed and claimed, enabling governance to monitor human capital investments and ensure sustainable tokenomics.

For technical readers, HumanResources implements the Department interface with governance controls, time-locked operations, and integration with multiple protocol components. It uses Vyper's create_from_blueprint for gas-efficient deployment of Contributor contracts from a template stored in MissionControl. The contract manages compensation through the Ripe Gov Vault (ID: 2) with automatic Ledger updates for tracking. It includes sophisticated validation logic for contributor terms based on protocol-wide HR configuration limits. The system supports manager/owner separation for operational flexibility and includes emergency functions for canceling unvested compensation. All operations emit comprehensive events for transparency and integrate with the Lootbox point system for engagement tracking.

## Architecture & Dependencies

HumanResources is built as a Department with modular architecture:

### Core Module Dependencies
- **LocalGov**: Provides governance functionality with access control
- **DeptBasics**: Department fundamentals (can mint RIPE only)
- **TimeLock**: Time-locked changes for contributor deployment

### Addys Module
- **Location**: `contracts/modules/Addys.vy`
- **Purpose**: Provides protocol-wide address resolution
- **Documentation**: See [Addys Technical Documentation](../modules/Addys.md)
- **Key Features**:
  - Access to all protocol contract addresses
  - Resolution of Ledger, RipeGovVault, VaultBook, etc.
  - Validation for authorized callers
- **Exported Interface**: Address utilities via `addys.__interface__`

### External Contract Interfaces
- **Ledger**: Tracks contributors and available RIPE for HR
- **RipeGovVault**: Manages vested RIPE token positions
- **RipeToken**: RIPE token minting and burning
- **Teller**: Deposits tokens into vaults
- **Lootbox**: Updates deposit points for engagement
- **VaultBook**: Resolves vault addresses
- **MissionControl**: Provides HR configuration and templates

### Module Initialization
```vyper
initializes: addys
initializes: deptBasics[addys := addys]
initializes: gov
initializes: timeLock[gov := gov]
```

### Department Configuration
```vyper
# In constructor
deptBasics.__init__(False, False, True)  # canMintGreen=False, canMintRipe=True
```

## Data Structures

### ContributorTerms Struct
Complete specification for a contributor's compensation:
```vyper
struct ContributorTerms:
    owner: address              # Who receives the tokens
    manager: address            # Who can manage the position
    compensation: uint256       # Total RIPE tokens allocated
    startDelay: uint256         # Delay before vesting starts
    vestingLength: uint256      # Total vesting duration
    cliffLength: uint256        # Cliff period before any vesting
    unlockLength: uint256       # When tokens become transferable
    depositLockDuration: uint256 # Lock duration in Ripe Gov Vault
```

### HrConfig Struct (from MissionControl)
Protocol-wide HR limits and configuration:
```vyper
struct HrConfig:
    contribTemplate: address    # Blueprint for Contributor contracts
    maxCompensation: uint256    # Maximum allowed compensation
    minCliffLength: uint256     # Minimum cliff period
    minVestingLength: uint256   # Minimum vesting duration
    maxVestingLength: uint256   # Maximum vesting duration
    maxStartDelay: uint256      # Maximum delay before start
```

## State Variables

### Pending Operations
- `pendingContributor: HashMap[uint256, ContributorTerms]` - Maps action ID to pending terms

### Constants
- `RIPE_GOV_VAULT_ID: constant(uint256) = 2` - Vault for contributor positions

## System Architecture Diagram

```
+------------------------------------------------------------------------+
|                      HumanResources Contract                          |
+------------------------------------------------------------------------+
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                 Contributor Deployment Flow                      |  |
|  |                                                                  |  |
|  |  initiateNewContributor():                                      |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ 1. Validate contributor terms against HR config             │ |  |
|  |  │ 2. Check available RIPE balance for compensation            │ |  |
|  |  │ 3. Create time-locked action with ContributorTerms          │ |  |
|  |  │ 4. Store pending contributor with action ID                 │ |  |
|  |  │ 5. Emit NewContributorInitiated event                       │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  |                            ↓ (timelock)                          |  |
|  |  confirmNewContributor():                                        |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ 1. Re-validate terms (config may have changed)              │ |  |
|  |  │ 2. Deploy Contributor contract from blueprint                │ |  |
|  |  │ 3. Update Ledger with new contributor                       │ |  |
|  |  │ 4. Clear pending data                                        │ |  |
|  |  │ 5. Emit NewContributorConfirmed event                       │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Compensation Timeline                         |  |
|  |                                                                  |  |
|  |  Start    Cliff        Unlock           End                      |  |
|  |    │        │             │              │                       |  |
|  |    ▼        ▼             ▼              ▼                       |  |
|  |  ──┬────────┬─────────────┬──────────────┬──                    |  |
|  |    │   No   │   Vesting   │   Vesting    │                      |  |
|  |    │ Vesting│   No Xfer   │   Can Xfer   │                      |  |
|  |    └────────┴─────────────┴──────────────┘                      |  |
|  |                                                                  |  |
|  |  • Start: Vesting begins (block.timestamp + startDelay)         |  |
|  |  • Cliff: First tokens become claimable                         |  |
|  |  • Unlock: Vested tokens become transferable                    |  |
|  |  • End: Full compensation vested                                |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Token Flow Management                         |  |
|  |                                                                  |  |
|  |  cashRipeCheck (from Contributor):                              |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ HR mints RIPE → Deposits to Ripe Gov Vault → Locked tokens  │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  |                                                                  |  |
|  |  transferContributorRipeTokens (from Contributor):              |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ Ripe Gov Vault → Transfer position → Update Lootbox points  │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  |                                                                  |  |
|  |  refundAfterCancelPaycheck (from Contributor):                  |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ Return unvested to Ledger → Optionally burn tokens         │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  +------------------------------------------------------------------+  |
+------------------------------------------------------------------------+
                                    |
                  ┌─────────────────┴─────────────────┐
                  ▼                                   ▼
+----------------------------------+  +----------------------------------+
|        Contributor Contracts     |  |      Protocol Components         |
+----------------------------------+  +----------------------------------+
| • Individual vesting contracts   |  | • Ledger: Tracks allocations    |
| • Owner/Manager permissions      |  | • Ripe Gov Vault: Holds tokens  |
| • Cliff and unlock enforcement   |  | • MissionControl: HR config      |
| • Delegation capabilities        |  | • Lootbox: Engagement points     |
+----------------------------------+  +----------------------------------+
```

## Constructor

### `__init__`

Initializes HumanResources with governance and timelock settings.

```vyper
@deploy
def __init__(
    _ripeHq: address,
    _minConfigTimeLock: uint256,
    _maxConfigTimeLock: uint256,
):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_ripeHq` | `address` | RipeHq contract for protocol integration |
| `_minConfigTimeLock` | `uint256` | Minimum blocks for contributor deployment |
| `_maxConfigTimeLock` | `uint256` | Maximum blocks for contributor deployment |

#### Deployment Behavior
- Initializes as a Department that can only mint RIPE
- Sets up governance through RipeHq
- Configures timelock bounds for operations

#### Example Usage
```python
hr = boa.load(
    "contracts/core/HumanResources.vy",
    ripe_hq.address,
    100,   # Min 100 blocks for changes
    1000   # Max 1000 blocks for changes
)
```

## Contributor Management Functions

### `initiateNewContributor`

Starts the process of deploying a new Contributor contract with specified terms.

```vyper
@external
def initiateNewContributor(
    _owner: address,
    _manager: address,
    _compensation: uint256,
    _startDelay: uint256,
    _vestingLength: uint256,
    _cliffLength: uint256,
    _unlockLength: uint256,
    _depositLockDuration: uint256,
) -> uint256:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_owner` | `address` | Who receives the vested tokens |
| `_manager` | `address` | Who can manage the contributor contract |
| `_compensation` | `uint256` | Total RIPE tokens to vest |
| `_startDelay` | `uint256` | Seconds until vesting starts |
| `_vestingLength` | `uint256` | Total vesting duration in seconds |
| `_cliffLength` | `uint256` | Cliff period in seconds |
| `_unlockLength` | `uint256` | When tokens become transferable |
| `_depositLockDuration` | `uint256` | Lock duration in blocks for vault |

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Action ID for the pending deployment |

#### Access

Only callable by governance

#### Validation
- Compensation must not exceed available RIPE for HR
- Terms must comply with HrConfig limits
- Cliff ≤ Unlock ≤ Vesting length
- Addresses must be valid

#### Events Emitted

- `NewContributorInitiated` - Contains all terms and confirmation block

#### Example Usage
```python
# Deploy contributor with 1M RIPE over 4 years
action_id = hr.initiateNewContributor(
    alice.address,      # owner
    alice.address,      # manager (can be different)
    10**6 * 10**18,     # 1M RIPE
    0,                  # Start immediately
    4 * 365 * 86400,    # 4 year vesting
    365 * 86400,        # 1 year cliff
    2 * 365 * 86400,    # 2 year unlock
    26000,              # ~3 month lock in vault
    sender=governance
)
```

### `confirmNewContributor`

Confirms and deploys a pending Contributor contract after timelock.

```vyper
@external
def confirmNewContributor(_aid: uint256) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_aid` | `uint256` | Action ID from initiation |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | True if deployment successful |

#### Process Flow
1. **Re-validation**: Terms still valid with current config
2. **Timelock Check**: Sufficient time has passed
3. **Blueprint Deploy**: Creates Contributor from template
4. **Ledger Update**: Registers contributor and compensation
5. **Cleanup**: Clears pending data

#### Events Emitted

- `NewContributorConfirmed` - Includes deployed address and terms

### `cancelNewContributor`

Cancels a pending contributor deployment.

```vyper
@external
def cancelNewContributor(_aid: uint256) -> bool:
```

## Contributor Operations

### `cashRipeCheck`

Called by Contributor contracts to mint and deposit vested RIPE.

```vyper
@external
def cashRipeCheck(_amount: uint256, _lockDuration: uint256) -> bool:
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_amount` | `uint256` | Amount of RIPE to mint |
| `_lockDuration` | `uint256` | Lock duration in blocks |

#### Access

Only callable by registered HR contributors

#### Process
1. Mints RIPE tokens to HumanResources
2. Approves Teller for deposit
3. Deposits into Ripe Gov Vault for caller
4. Resets approval to zero

### `transferContributorRipeTokens`

Transfers a contributor's vested position to their owner.

```vyper
@external
def transferContributorRipeTokens(_owner: address, _lockDuration: uint256) -> uint256:
```

#### Process
1. Validates caller is HR contributor
2. Transfers position in Ripe Gov Vault
3. Updates Ledger for new owner
4. Updates Lootbox points

### `refundAfterCancelPaycheck`

Handles refunds when a contributor's paycheck is cancelled.

```vyper
@external
def refundAfterCancelPaycheck(_amount: uint256, _shouldBurnPosition: bool):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_amount` | `uint256` | Unvested amount to refund |
| `_shouldBurnPosition` | `bool` | Whether to burn existing position |

## Validation Functions

### `areValidContributorTerms`

Public validation of contributor terms.

```vyper
@view
@external
def areValidContributorTerms(
    _owner: address,
    _manager: address,
    _compensation: uint256,
    _startDelay: uint256,
    _vestingLength: uint256,
    _cliffLength: uint256,
    _unlockLength: uint256,
    _depositLockDuration: uint256,
) -> bool:
```

#### Validation Rules
1. **Template Exists**: HR config has contributor template
2. **Compensation Valid**: 
   - Greater than zero
   - Within available RIPE balance
   - Below max compensation limit
3. **Time Periods**:
   - Cliff > 0 and >= minimum
   - Vesting > 0 and within min/max
   - Unlock ≤ Vesting
   - Cliff ≤ Unlock
   - Start delay ≤ maximum
4. **Addresses**: Owner and manager not empty

## View Functions

### `canModifyHrContributor`

Checks if an address can modify contributor contracts.

```vyper
@view
@external
def canModifyHrContributor(_addr: address) -> bool:
```

Returns true for Switchboard addresses.

### `hasRipeBalance`

Checks if a contributor has RIPE in the gov vault.

```vyper
@view
@external
def hasRipeBalance(_contributor: address) -> bool:
```

### `getTotalClaimed`

Returns total RIPE claimed by all contributors.

```vyper
@view
@external
def getTotalClaimed() -> uint256:
```

Iterates through all contributors summing claimed amounts.

### `getTotalCompensation`

Returns total RIPE allocated to all contributors.

```vyper
@view
@external
def getTotalCompensation() -> uint256:
```

## Events

### Deployment Events
- `NewContributorInitiated` - Deployment started
- `NewContributorConfirmed` - Contributor deployed
- `NewContributorCancelled` - Deployment cancelled

All events include complete ContributorTerms and action details.

## Security Considerations

### Access Control
- **Governance Only**: Contributor deployment restricted
- **Contributor Registry**: Only registered contributors can mint
- **Switchboard Override**: Emergency admin capabilities

### Economic Security
- **Balance Checks**: Cannot exceed available RIPE
- **Time Locks**: Prevents rushed deployments
- **Validation**: Re-checks on confirmation

### Integration Safety
- **Blueprint Deploy**: Gas-efficient, deterministic
- **Approval Management**: Resets after operations
- **Event Logging**: Full transparency

## Common Integration Patterns

### Deploying a Contributor
```python
# 1. Check available balance
available = ledger.ripeAvailForHr()
print(f"Available for HR: {available / 10**18} RIPE")

# 2. Initiate deployment
aid = hr.initiateNewContributor(
    contributor.address,
    manager.address,
    compensation,
    0,  # Start immediately
    4 * 365 * 86400,  # 4 years
    365 * 86400,      # 1 year cliff
    365 * 86400,      # 1 year unlock
    26000,            # 3 month lock
    sender=governance
)

# 3. Wait for timelock
wait_blocks(timelock_duration)

# 4. Confirm deployment
success = hr.confirmNewContributor(aid, sender=governance)
```

### Monitoring Contributors
```python
# Get all contributors
num_contributors = ledger.numContributors()
for i in range(1, num_contributors + 1):
    addr = ledger.contributors(i)
    comp = contributor_contract.compensation()
    claimed = contributor_contract.totalClaimed()
    print(f"Contributor {addr}: {comp/10**18} allocated, {claimed/10**18} claimed")

# Protocol totals
total_comp = hr.getTotalCompensation()
total_claimed = hr.getTotalClaimed()
print(f"Total: {total_comp/10**18} allocated, {total_claimed/10**18} claimed")
```

## Testing

For comprehensive test examples, see: [`tests/core/test_human_resources.py`](../../tests/core/test_human_resources.py)