# Contributor Technical Documentation

[📄 View Source Code](../../contracts/modules/Contributor.vy)

## Overview

Contributor contracts are personalized vesting vaults that manage individual token compensation agreements for protocol contributors. Each contract represents an immutable on-chain employment agreement that automatically handles
token distribution according to predefined schedules with built-in protections and governance capabilities.

**Core Functions**:
- **Vesting Management**: Linear vesting with cliff periods, automatically calculating and tracking earned amounts
- **Token Distribution**: Interfaces with HumanResources to mint and deposit vested RIPE tokens with appropriate locks
- **Access Control**: Dual-permission system with owner/manager roles plus time-delayed ownership transfers
- **Position Transfers**: Enables access to vested tokens after unlock periods with security delays
- **Governance Integration**: Allows voting power delegation from vested positions with protection controls

Deployed as blueprints for gas efficiency, each contract stores immutable vesting parameters and implements sophisticated time-based calculations with two-phase commit patterns for sensitive operations.

## Architecture & Dependencies

Contributor contracts are standalone vesting contracts with external dependencies:

### External Contract Interfaces
- **HumanResources**: Parent contract that deploys and manages contributors
- **RipeGovernance**: Handles voting delegation for vested positions  
- **RipeHq**: Registry for looking up protocol addresses

### Key Constants
- `HUMAN_RESOURCES_ID: constant(uint256) = 15` - Registry ID for HR lookup

### Immutable Values
Set during deployment and cannot be changed:
```vyper
RIPE_HQ: immutable(address)              # Protocol registry
MIN_KEY_ACTION_DELAY: immutable(uint256) # Minimum delay for actions
MAX_KEY_ACTION_DELAY: immutable(uint256) # Maximum delay for actions
```

## Data Structures

### PendingRipeTransfer Struct
Tracks pending position transfers:
```vyper
struct PendingRipeTransfer:
    recipient: address      # Who receives the position
    initiatedBlock: uint256 # When transfer started
    confirmBlock: uint256   # When transfer can be confirmed
```

### PendingOwnerChange Struct  
Tracks pending ownership changes:
```vyper
struct PendingOwnerChange:
    newOwner: address       # Proposed new owner
    initiatedBlock: uint256 # When change started
    confirmBlock: uint256   # When change can be confirmed
```

## State Variables

### Compensation Terms
Immutable after deployment:
- `compensation: uint256` - Total RIPE tokens allocated
- `startTime: uint256` - When vesting begins (timestamp)
- `endTime: uint256` - When vesting completes (timestamp)
- `cliffTime: uint256` - Earliest claim time (timestamp)
- `unlockTime: uint256` - When transfers allowed (timestamp)
- `depositLockDuration: uint256` - Lock duration in blocks for deposits

### Access Control
- `owner: address` - Beneficiary who receives tokens
- `manager: address` - Can operate on owner's behalf

### Tracking
- `totalClaimed: uint256` - Total RIPE claimed so far

### Configuration
- `keyActionDelay: uint256` - Blocks between initiate and confirm
- `isFrozen: bool` - Emergency freeze state

### Pending States
- `pendingOwner: PendingOwnerChange` - Pending ownership change
- `pendingRipeTransfer: PendingRipeTransfer` - Pending position transfer

## System Architecture Diagram

```
+------------------------------------------------------------------------+
|                         Contributor Contract                          |
+------------------------------------------------------------------------+
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                      Vesting Timeline                            |  |
|  |                                                                  |  |
|  |  Deploy    Start    Cliff      Unlock        End                |  |
|  |    │         │        │           │            │                 |  |
|  |    ▼         ▼        ▼           ▼            ▼                 |  |
|  |  ──┬─────────┬────────┬───────────┬───────────┬──               |  |
|  |    │  Delay  │   No   │  Vesting  │  Vesting  │                 |  |
|  |    │         │ Vesting│  No Xfer  │ Can Xfer  │                 |  |
|  |    └─────────┴────────┴───────────┴───────────┘                 |  |
|  |                                                                  |  |
|  |  Linear Vesting Formula:                                         |  |
|  |  vested = compensation × (now - start) / (end - start)          |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Core Operations Flow                          |  |
|  |                                                                  |  |
|  |  cashRipeCheck():                                                |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ 1. Calculate claimable (vested - claimed)                   │ |  |
|  |  │ 2. Call HR.cashRipeCheck(amount, lockDuration)              │ |  |
|  |  │ 3. HR mints RIPE and deposits to Ripe Gov Vault             │ |  |
|  |  │ 4. Update totalClaimed                                      │ |  |
|  |  │ 5. Emit RipeCheckCashed event                               │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  |                                                                  |  |
|  |  Token Transfer (Two-Phase):                                     |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ initiateRipeTransfer():                                     │ |  |
|  |  │ • Check unlock time passed                                  │ |  |
|  |  │ • Optionally cash latest check                              │ |  |
|  |  │ • Set pending transfer with delay                           │ |  |
|  |  │                    ↓ (keyActionDelay blocks)                 │ |  |
|  |  │ confirmRipeTransfer():                                      │ |  |
|  |  │ • Cash final check                                          │ |  |
|  |  │ • Transfer vault position to owner                          │ |  |
|  |  │ • Clear pending state                                       │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Permission Model                              |  |
|  |                                                                  |  |
|  |  Owner (Beneficiary):                                            |  |
|  |  • Change ownership (with delay)                                 |  |
|  |  • Set manager                                                   |  |
|  |  • Cash paychecks                                               |  |
|  |  • Transfer position (after unlock)                             |  |
|  |  • Delegate voting power                                        |  |
|  |  • Set key action delay                                         |  |
|  |                                                                  |  |
|  |  Manager (Operator):                                             |  |
|  |  • Cash paychecks on owner's behalf                             |  |
|  |  • Initiate/confirm transfers                                   |  |
|  |  • Remove delegations                                           |  |
|  |  • Cancel pending operations                                    |  |
|  |                                                                  |  |
|  |  HR/Switchboard (Protocol):                                      |  |
|  |  • Freeze/unfreeze contract                                     |  |
|  |  • Cancel paychecks                                             |  |
|  |  • Override certain operations                                  |  |
|  +------------------------------------------------------------------+  |
+------------------------------------------------------------------------+
                                    |
                  ┌─────────────────┴─────────────────┐
                  ▼                                   ▼
+----------------------------------+  +----------------------------------+
|         HumanResources           |  |       RipeGovernance             |
+----------------------------------+  +----------------------------------+
| • Mints RIPE for paychecks       |  | • Accepts delegation             |
| • Manages vault deposits         |  | • Voting power from position     |
| • Handles position transfers     |  | • Can remove all delegations     |
| • Processes cancellations        |  +----------------------------------+
+----------------------------------+
```

## Constructor

### `__init__`

Deployed by HumanResources with immutable vesting terms.

```vyper
@deploy
def __init__(
    _ripeHq: address,
    _owner: address,
    _manager: address,
    _compensation: uint256,
    _startDelay: uint256,
    _vestingLength: uint256,
    _cliffLength: uint256,
    _unlockLength: uint256,
    _depositLockDuration: uint256,
    _minKeyActionDelay: uint256,
    _maxKeyActionDelay: uint256,
):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_ripeHq` | `address` | Protocol registry contract |
| `_owner` | `address` | Beneficiary of vested tokens |
| `_manager` | `address` | Operator who can act for owner |
| `_compensation` | `uint256` | Total RIPE tokens to vest |
| `_startDelay` | `uint256` | Seconds until vesting starts |
| `_vestingLength` | `uint256` | Total vesting duration |
| `_cliffLength` | `uint256` | Cliff period before any vesting |
| `_unlockLength` | `uint256` | When transfers become allowed |
| `_depositLockDuration` | `uint256` | Vault lock duration in blocks |
| `_minKeyActionDelay` | `uint256` | Minimum delay for actions |
| `_maxKeyActionDelay` | `uint256` | Maximum delay for actions |

#### Validation
- All addresses must be non-empty
- Compensation > 0
- Vesting length > 0  
- Unlock ≤ Vesting
- Cliff ≤ Unlock
- Min delay < Max delay

## Core Functions

### `cashRipeCheck`

Claims vested RIPE tokens and deposits them to the vault.

```vyper
@external
def cashRipeCheck() -> uint256:
```

#### Returns

| Type | Description |
|------|-------------|
| `uint256` | Amount of RIPE claimed |

#### Access

- Owner
- Manager
- HR-authorized addresses (Switchboard)

#### Process
1. Calculates claimable amount (vested - claimed)
2. Calls HR to mint and deposit tokens
3. Updates totalClaimed
4. Emits RipeCheckCashed event

#### Example Usage
```python
# Owner claims vested tokens
amount = contributor.cashRipeCheck(sender=owner)
print(f"Claimed {amount / 10**18} RIPE")
```

## Position Transfer Functions

### `initiateRipeTransfer`

Starts the process of transferring the vested position to the owner.

```vyper
@nonreentrant
@external
def initiateRipeTransfer(_shouldCashCheck: bool = True):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_shouldCashCheck` | `bool` | Whether to claim before transfer |

#### Access

- Owner
- Manager

#### Requirements
- Not frozen
- No pending ownership change
- Past unlock time
- Has RIPE balance in vault

#### Events Emitted

- `RipeTransferInitiated` - Contains confirmation block

### `confirmRipeTransfer`

Completes the position transfer after delay.

```vyper
@nonreentrant
@external
def confirmRipeTransfer(_shouldCashCheck: bool = True):
```

#### Process
1. Validates delay has passed
2. Optionally claims final vested amount
3. Transfers vault position via HR
4. Clears pending state

#### Events Emitted

- `RipeTransferConfirmed` - Contains transfer amount

### `cancelRipeTransfer`

Cancels a pending position transfer.

```vyper
@nonreentrant
@external
def cancelRipeTransfer():
```

## Ownership Functions

### `changeOwnership`

Initiates ownership change with time delay.

```vyper
@external
def changeOwnership(_newOwner: address):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_newOwner` | `address` | Proposed new owner |

#### Access

Current owner only

#### Events Emitted

- `OwnershipChangeInitiated`

### `confirmOwnershipChange`

New owner confirms the ownership transfer.

```vyper
@external
def confirmOwnershipChange():
```

#### Access

New owner only (must wait for delay)

#### Events Emitted

- `OwnershipChangeConfirmed`

## Admin Functions

### `setManager`

Updates the manager address immediately.

```vyper
@external 
def setManager(_newManager: address):
```

#### Access

- Owner
- HR-authorized addresses

#### Requirements
- No pending ownership change
- Valid address

### `setKeyActionDelay`

Adjusts the delay for sensitive operations.

```vyper
@external
def setKeyActionDelay(_numBlocks: uint256):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_numBlocks` | `uint256` | New delay in blocks |

#### Access

Owner only

#### Validation

Must be between MIN and MAX bounds

## Governance Functions

### `delegateTo`

Delegates voting power to another address.

```vyper
@nonreentrant
@external
def delegateTo(_govAddr: address, _recipient: address, _ratio: uint256):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_govAddr` | `address` | Governance contract |
| `_recipient` | `address` | Delegate address |
| `_ratio` | `uint256` | Delegation ratio (10000 = 100%) |

#### Access

Owner only

#### Requirements

Not frozen

### `removeDelegationFor`

Removes voting delegation.

```vyper
@nonreentrant
@external
def removeDelegationFor(_govAddr: address, _recipient: address = empty(address)):
```

#### Access

- Owner
- Manager

Use empty address to remove all delegations.

## HR Admin Functions

### `setIsFrozen`

Freezes or unfreezes the contract.

```vyper
@external 
def setIsFrozen(_shouldFreeze: bool) -> bool:
```

#### Access

HR-authorized addresses only

When frozen:
- No claiming
- No transfers
- No delegation changes

### `cancelPaycheck`

Cancels remaining unvested compensation.

```vyper
@external
def cancelPaycheck():
```

#### Access

HR-authorized addresses only

#### Process
1. Can only cancel before end time
2. If past cliff, claims vested amount first
3. Reduces compensation to claimed amount
4. Sets end time to now
5. Refunds unvested amount to HR

#### Events Emitted

- `RipePaycheckCancelled` - Shows forfeited amount

## View Functions

### Vesting Calculations

#### `getClaimable`
```vyper
@view
@external
def getClaimable() -> uint256:
```
Returns amount that can be claimed now.

#### `getTotalVested`
```vyper
@view
@external
def getTotalVested() -> uint256:
```
Returns total vested based on linear formula.

#### `getUnvestedComp`
```vyper
@view
@external
def getUnvestedComp() -> uint256:
```
Returns remaining unvested compensation.

### Time Calculations

#### `getRemainingVestingLength`
```vyper
@view
@external
def getRemainingVestingLength() -> uint256:
```
Time until fully vested.

#### `getRemainingUnlockLength`
```vyper
@view
@external
def getRemainingUnlockLength() -> uint256:
```
Time until transfers allowed.

### State Checks

#### `hasPendingRipeTransfer`
```vyper
@view
@external
def hasPendingRipeTransfer() -> bool:
```

#### `hasPendingOwnerChange`
```vyper
@view
@external
def hasPendingOwnerChange() -> bool:
```

## Events

### Token Events
- `RipeCheckCashed` - Tokens claimed
- `RipeTransferInitiated` - Transfer started
- `RipeTransferConfirmed` - Transfer completed
- `RipeTransferCancelled` - Transfer cancelled

### Ownership Events
- `OwnershipChangeInitiated` - Change started
- `OwnershipChangeConfirmed` - Change completed
- `OwnershipChangeCancelled` - Change cancelled

### Admin Events
- `ManagerModified` - Manager updated
- `KeyActionDelaySet` - Delay changed
- `DelegationModified` - Voting delegated
- `DelegationRemoved` - Delegation cleared
- `FreezeModified` - Freeze state changed
- `RipePaycheckCancelled` - Compensation cancelled

## Security Considerations

### Time-Based Security
- **Cliff Protection**: No vesting before cliff
- **Unlock Protection**: No transfers before unlock
- **Action Delays**: Time between initiate and confirm

### Access Control
- **Role Separation**: Owner vs Manager permissions
- **HR Override**: Protocol can freeze and cancel
- **Ownership Transfer**: Two-phase with new owner confirmation

### Economic Security
- **Linear Vesting**: Predictable, manipulation-resistant
- **Cancellation Logic**: Protects vested amounts
- **Transfer Validation**: Ensures balance exists

## Common Usage Patterns

### Regular Claiming
```python
# Contributor claims monthly
def monthly_claim():
    claimable = contributor.getClaimable()
    if claimable > 0:
        contributor.cashRipeCheck(sender=owner)
```

### Position Transfer After Unlock
```python
# 1. Check unlock time passed
remaining = contributor.getRemainingUnlockLength()
if remaining == 0:
    # 2. Initiate transfer
    contributor.initiateRipeTransfer(sender=owner)
    
    # 3. Wait for delay
    wait_blocks(contributor.keyActionDelay())
    
    # 4. Confirm transfer
    contributor.confirmRipeTransfer(sender=owner)
```

### Emergency Cancellation
```python
# HR cancels unvested portion
if emergency_situation:
    # Will claim vested amount if past cliff
    # Returns unvested to protocol
    contributor.cancelPaycheck(sender=switchboard)
```

## Testing

For comprehensive test examples, see: [`tests/modules/test_contributor.py`](../../tests/modules/test_contributor.py)