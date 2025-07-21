# RipeHq Technical Documentation

## Overview

RipeHq serves as the master registry and governance hub for the Ripe Protocol ecosystem. Think of it as the central control tower at an airport - it coordinates all the critical components, maintains authoritative records of who's who, and ensures only authorized parties can perform sensitive operations.

At its core, RipeHq manages three fundamental responsibilities:

**1. Identity Management**: Every important contract in the Ripe ecosystem gets registered here with a unique ID and description. This creates a single source of truth for finding protocol components - from the Green token (ID: 1) to Savings Green (ID: 2) to the Ripe token (ID: 3), and beyond.

**2. Permission Control**: RipeHq implements a sophisticated two-factor authentication system for minting tokens. Departments (protocol components) must first be granted minting permissions through RipeHq's configuration system, and then they must also self-declare their minting capability. This double-check prevents unauthorized token creation.

**3. Safety Mechanisms**: The contract includes time-locked changes (preventing rushed decisions), a circuit breaker for minting operations (allowing emergency stops), and careful separation of powers between different protocol components.

For technical readers, RipeHq utilizes modular architecture with imported governance and registry modules, implements time-locked state changes, provides comprehensive event logging, and includes recovery mechanisms for misplaced funds. The contract's structure reflects common patterns in DeFi protocols where centralized registries help coordinate decentralized components.

## Architecture & Modules

RipeHq is built using a modular architecture that separates concerns and promotes code reusability:

### LocalGov Module
- **Location**: `contracts/modules/LocalGov.vy`
- **Purpose**: Provides governance functionality with time-locked changes
- **Key Features**:
  - Governance address management with time-locked transitions
  - Configurable min/max timelock periods for security
  - Two-phase commit pattern for governance changes
- **Exported Interface**: All governance functions are exposed via `gov.__interface__`

### AddressRegistry Module  
- **Location**: `contracts/registries/modules/AddressRegistry.vy`
- **Purpose**: Manages the registry of protocol addresses
- **Key Features**:
  - Sequential registry ID assignment (starting from 1)
  - Time-locked address additions, updates, and disabling
  - Descriptive labels for each registered address
  - Address lookup by ID or reverse lookup (ID by address)
- **Exported Interface**: All registry functions are exposed via `registry.__interface__`

### Module Initialization
```vyper
initializes: gov
initializes: registry[gov := gov]
```
This initialization pattern ensures the registry module has access to governance controls while maintaining separation of concerns.

## System Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────┐
│                            RipeHq Contract                         │
├────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐         ┌──────────────────────────────┐  │
│  │   LocalGov Module   │         │   AddressRegistry Module     │  │
│  │                     │         │                              │  │
│  │ • Governance mgmt   │         │ • Address registration       │  │
│  │ • Timelock control  │         │ • ID assignment (1,2,3...)   │  │
│  │ • Access control    │         │ • Update/disable functions   │  │
│  └─────────────────────┘         └──────────────────────────────┘  │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    HQ Configuration Layer                    │  │
│  │                                                              │  │
│  │  • Minting permissions (canMintGreen, canMintRipe)           │  │
│  │  • Blacklist permissions (canSetTokenBlacklist)              │  │
│  │  • Two-factor authentication with departments                │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Safety Mechanisms                         │  │
│  │                                                              │  │
│  │  • Global minting circuit breaker (mintEnabled)              │  │
│  │  • Fund recovery system (recoverFunds)                       │  │
│  │  • Timelock protection on all changes                        │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
                                     │
                     ┌───────────────┴───────────────┐
                     ▼                               ▼
        ┌─────────────────────┐          ┌─────────────────────┐
        │   Core Tokens       │          │   Departments       │
        │                     │          │                     │
        │ ID 1: Green Token   │          │ ID 4+: Various      │
        │ ID 2: Savings Green │          │ • Auction House     │
        │ ID 3: Ripe Token    │          │ • Credit Engine     │
        └─────────────────────┘          │ • Lootbox, etc.     │
                                         └─────────────────────┘
```

## Permission Flow Diagram

```
Can Department Mint Green Tokens?
┌─────────────────────┐
│ Request to Mint     │
└──────────┬──────────┘
           ▼
┌─────────────────────┐     NO
│ mintEnabled == true?├────────► DENIED
└──────────┬──────────┘
           │ YES
           ▼
┌─────────────────────┐     NO
│ Valid registry ID?  ├────────► DENIED
└──────────┬──────────┘
           │ YES
           ▼
┌─────────────────────┐     NO
│ hqConfig.canMintGreen├───────► DENIED
└──────────┬──────────┘
           │ YES
           ▼
┌─────────────────────┐     NO
│dept.canMintGreen()?├─────────► DENIED
└──────────┬──────────┘
           │ YES
           ▼
      ✓ APPROVED
```

## Timelock Change Flow

```
Registry/Config Change Process:
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Initiate   │      │    Wait      │      │   Confirm    │
│   Change     │ ───► │  Timelock    │ ───► │   Change     │
└──────────────┘      └──────────────┘      └──────────────┘
       │                                              │
       │                    OR                        │
       ▼                                              ▼
┌──────────────┐                            ┌──────────────┐
│   Cancel     │                            │   Applied    │
│   Change     │                            │   Change     │
└──────────────┘                            └──────────────┘
```

## Constructor

### `__init__`

**Description**: Initializes the RipeHq contract with core protocol addresses and timelock parameters. Automatically registers the Green token, Savings Green, and Ripe token with registry IDs 1, 2, and 3 respectively.

**Parameters**:
- `_greenToken` (address): The address of the Green token contract
- `_savingsGreen` (address): The address of the Savings Green contract
- `_ripeToken` (address): The address of the Ripe token contract
- `_initialGov` (address): The initial governance address
- `_minGovTimeLock` (uint256): Minimum time lock for governance changes in blocks
- `_maxGovTimeLock` (uint256): Maximum time lock for governance changes in blocks
- `_minRegistryTimeLock` (uint256): Minimum time lock for registry changes in blocks
- `_maxRegistryTimeLock` (uint256): Maximum time lock for registry changes in blocks

**Access**: Called only during deployment

**Example Usage**:
```python
# Deploy RipeHq with core protocol addresses
ripe_hq = boa.load(
    "contracts/registries/RipeHq.vy",
    green_token.address,
    savings_green.address,
    ripe_token.address,
    deployer_address,
    100,   # Min gov timelock (blocks)
    1000,  # Max gov timelock (blocks)
    50,    # Min registry timelock (blocks)
    500    # Max registry timelock (blocks)
)
```

**Example Output**: Contract deployed with Green token registered as ID 1, Savings Green as ID 2, and Ripe token as ID 3. Minting is enabled by default.

## Registry Management Functions

### `startAddNewAddressToRegistry`

**Description**: Initiates the process of adding a new address to the registry. This starts a time-locked change that must be confirmed after the timelock period.

**Parameters**:
- `_addr` (address): The address to add to the registry
- `_description` (String[64]): A human-readable description of the address (max 64 characters)

**Returns**: `bool` - True if the addition was successfully initiated

**Access**: Only callable by governance

**Example Usage**:
```python
# Governance initiates adding a new department
success = ripe_hq.startAddNewAddressToRegistry(
    treasury_dept.address,
    "Treasury Department",
    sender=governance.address
)
```

**Example Output**: Returns `True`, emits event indicating timelock confirmation block

### `confirmNewAddressToRegistry`

**Description**: Confirms a pending address addition after the timelock period has passed. Assigns the next available registry ID to the address.

**Parameters**:
- `_addr` (address): The address to confirm

**Returns**: `uint256` - The assigned registry ID

**Access**: Only callable by governance

**Example Usage**:
```python
# After timelock period, confirm the addition
boa.env.time_travel(blocks=time_lock)
reg_id = ripe_hq.confirmNewAddressToRegistry(
    treasury_dept.address,
    sender=governance.address
)
# Returns: 4 (next ID after the 3 core tokens)
```

**Example Output**: Returns registry ID 4, address is now registered

### `cancelNewAddressToRegistry`

**Description**: Cancels a pending address addition before it's confirmed.

**Parameters**:
- `_addr` (address): The address whose pending addition to cancel

**Returns**: `bool` - True if successfully cancelled

**Access**: Only callable by governance

**Example Usage**:
```python
# Cancel pending addition
success = ripe_hq.cancelNewAddressToRegistry(
    treasury_dept.address,
    sender=governance.address
)
```

**Example Output**: Returns `True`, pending addition removed

### `startAddressUpdateToRegistry`

**Description**: Initiates updating an existing registry entry to point to a new address. Useful for contract upgrades.

**Parameters**:
- `_regId` (uint256): The registry ID to update
- `_newAddr` (address): The new address to associate with this ID

**Returns**: `bool` - True if update was successfully initiated

**Access**: Only callable by governance

**Example Usage**:
```python
# Start updating Treasury Department to new implementation
success = ripe_hq.startAddressUpdateToRegistry(
    4,                           # Registry ID for Treasury
    new_treasury_dept.address,   # New Treasury contract
    sender=governance.address
)
```

**Example Output**: Returns `True`, update pending with timelock

### `confirmAddressUpdateToRegistry`

**Description**: Confirms a pending address update after the timelock period.

**Parameters**:
- `_regId` (uint256): The registry ID being updated

**Returns**: `bool` - True if successfully confirmed

**Access**: Only callable by governance

**Example Usage**:
```python
# Confirm the Treasury update after timelock
boa.env.time_travel(blocks=time_lock)
success = ripe_hq.confirmAddressUpdateToRegistry(
    4,
    sender=governance.address
)
```

**Example Output**: Returns `True`, registry ID 4 now points to new address

### `cancelAddressUpdateToRegistry`

**Description**: Cancels a pending address update.

**Parameters**:
- `_regId` (uint256): The registry ID whose update to cancel

**Returns**: `bool` - True if successfully cancelled

**Access**: Only callable by governance

**Example Usage**:
```python
# Cancel pending update
success = ripe_hq.cancelAddressUpdateToRegistry(
    4,
    sender=governance.address
)
```

**Example Output**: Returns `True`, update cancelled

### `startAddressDisableInRegistry`

**Description**: Initiates disabling a registry entry. Note: Core tokens (IDs 1-3) cannot be disabled.

**Parameters**:
- `_regId` (uint256): The registry ID to disable

**Returns**: `bool` - True if disable was successfully initiated

**Access**: Only callable by governance

**Example Usage**:
```python
# Start disabling a deprecated department
success = ripe_hq.startAddressDisableInRegistry(
    5,
    sender=governance.address
)
```

**Example Output**: Returns `True` if not a token ID, reverts with "cannot disable token" for IDs 1-3

### `confirmAddressDisableInRegistry`

**Description**: Confirms disabling a registry entry after timelock.

**Parameters**:
- `_regId` (uint256): The registry ID to confirm disabling

**Returns**: `bool` - True if successfully disabled

**Access**: Only callable by governance

**Example Usage**:
```python
# Confirm disabling after timelock
boa.env.time_travel(blocks=time_lock)
success = ripe_hq.confirmAddressDisableInRegistry(
    5,
    sender=governance.address
)
```

**Example Output**: Returns `True`, registry entry disabled

### `cancelAddressDisableInRegistry`

**Description**: Cancels a pending disable operation.

**Parameters**:
- `_regId` (uint256): The registry ID whose disable to cancel

**Returns**: `bool` - True if successfully cancelled

**Access**: Only callable by governance

**Example Usage**:
```python
# Cancel pending disable
success = ripe_hq.cancelAddressDisableInRegistry(
    5,
    sender=governance.address
)
```

**Example Output**: Returns `True`, disable cancelled

## HQ Configuration Functions

### `hasPendingHqConfigChange`

**Description**: Checks if a registry ID has a pending configuration change.

**Parameters**:
- `_regId` (uint256): The registry ID to check

**Returns**: `bool` - True if there's a pending change

**Access**: Public view function

**Example Usage**:
```python
# Check if Treasury has pending config changes
has_pending = ripe_hq.hasPendingHqConfigChange(4)
```

**Example Output**: Returns `True` if pending, `False` otherwise

### `initiateHqConfigChange`

**Description**: Starts a time-locked process to update a department's permissions for minting and blacklist management.

**Parameters**:
- `_regId` (uint256): The registry ID to configure
- `_canMintGreen` (bool): Whether this address can mint Green tokens
- `_canMintRipe` (bool): Whether this address can mint Ripe tokens
- `_canSetTokenBlacklist` (bool): Whether this address can modify token blacklists

**Access**: Only callable by governance

**Events Emitted**: 
- `HqConfigChangeInitiated` - Contains registry ID, description, permissions, and confirmation block

**Example Usage**:
```python
# Grant Treasury permission to mint Green tokens only
ripe_hq.initiateHqConfigChange(
    4,      # Treasury registry ID
    True,   # Can mint Green
    False,  # Cannot mint Ripe
    False,  # Cannot set blacklist
    sender=governance.address
)
```

**Example Output**: Emits `HqConfigChangeInitiated` event with confirmation block

### `confirmHqConfigChange`

**Description**: Confirms a pending configuration change after timelock. Validates that the department contract actually supports the requested minting permissions.

**Parameters**:
- `_regId` (uint256): The registry ID to confirm

**Returns**: `bool` - True if successfully confirmed

**Access**: Only callable by governance

**Events Emitted**:
- `HqConfigChangeConfirmed` - Contains registry ID, description, permissions, and both initiation and confirmation blocks

**Example Usage**:
```python
# Confirm Treasury's new permissions after timelock
boa.env.time_travel(blocks=time_lock)
success = ripe_hq.confirmHqConfigChange(
    4,
    sender=governance.address
)
```

**Example Output**: Returns `True` if valid, `False` if department doesn't support requested permissions

### `cancelHqConfigChange`

**Description**: Cancels a pending configuration change.

**Parameters**:
- `_regId` (uint256): The registry ID whose config change to cancel

**Returns**: `bool` - True if successfully cancelled

**Access**: Only callable by governance

**Events Emitted**:
- `HqConfigChangeCancelled` - Contains registry ID, description, permissions, and both initiation and confirmation blocks

**Example Usage**:
```python
# Cancel pending config change
success = ripe_hq.cancelHqConfigChange(
    4,
    sender=governance.address
)
```

**Example Output**: Returns `True`, emits `HqConfigChangeCancelled` event

### `isValidHqConfig`

**Description**: Validates whether a proposed configuration is valid for a given registry ID. Checks that non-token entries support the requested minting capabilities.

**Parameters**:
- `_regId` (uint256): The registry ID to validate
- `_canMintGreen` (bool): Proposed Green minting permission
- `_canMintRipe` (bool): Proposed Ripe minting permission

**Returns**: `bool` - True if configuration is valid

**Access**: Public view function

**Example Usage**:
```python
# Check if Treasury can be granted Green minting permission
is_valid = ripe_hq.isValidHqConfig(4, True, False)
# Returns True if Treasury contract has canMintGreen() returning True
```

**Example Output**: Returns `True` if valid, `False` if not a valid registry ID, address is empty, or department doesn't support requested permissions

## Token Getter Functions

### `greenToken`

**Description**: Returns the address of the Green token contract (registry ID 1).

**Returns**: `address` - The Green token contract address

**Access**: Public view function

**Example Usage**:
```python
green_addr = ripe_hq.greenToken()
# Returns: green_token.address
assert green_addr == ripe_hq.getAddr(1)
```

### `savingsGreen`

**Description**: Returns the address of the Savings Green contract (registry ID 2).

**Returns**: `address` - The Savings Green contract address

**Access**: Public view function

**Example Usage**:
```python
savings_addr = ripe_hq.savingsGreen()
# Returns: savings_green.address
assert savings_addr == ripe_hq.getAddr(2)
```

### `ripeToken`

**Description**: Returns the address of the Ripe token contract (registry ID 3).

**Returns**: `address` - The Ripe token contract address

**Access**: Public view function

**Example Usage**:
```python
ripe_addr = ripe_hq.ripeToken()
# Returns: ripe_token.address
assert ripe_addr == ripe_hq.getAddr(3)
```

## Minting Permission Functions

### `canMintGreen`

**Description**: Checks if an address has permission to mint Green tokens. Requires minting to be enabled globally, the address to be registered with Green minting permission, and the address's contract to return `True` from `canMintGreen()`.

**Parameters**:
- `_addr` (address): The address to check

**Returns**: `bool` - True if address can mint Green tokens

**Access**: Public view function

**Example Usage**:
```python
# Check if Credit Engine can mint Green
can_mint = ripe_hq.canMintGreen(credit_engine.address)
# Returns: True (if minting enabled, registered with permission, and dept supports it)
assert can_mint == True
```

**Example Output**: Returns `True` only if minting enabled, address registered with permission, and contract confirms capability

### `canMintRipe`

**Description**: Checks if an address has permission to mint Ripe tokens. Requires minting to be enabled globally, the address to be registered with Ripe minting permission, and the address's contract to return `True` from `canMintRipe()`.

**Parameters**:
- `_addr` (address): The address to check

**Returns**: `bool` - True if address can mint Ripe tokens

**Access**: Public view function

**Example Usage**:
```python
# Check if Lootbox can mint Ripe
can_mint = ripe_hq.canMintRipe(lootbox.address)
# Returns: True (if minting enabled, registered with permission, and dept supports it)
assert can_mint == True
```

**Example Output**: Returns `True` only if all three conditions are satisfied

### `canSetTokenBlacklist`

**Description**: Checks if an address has permission to modify token blacklists. Only requires the address to be registered with this permission in HQ config.

**Parameters**:
- `_addr` (address): The address to check

**Returns**: `bool` - True if address can set token blacklists

**Access**: Public view function

**Example Usage**:
```python
# Check if Switchboard can set blacklists
can_blacklist = ripe_hq.canSetTokenBlacklist(switchboard.address)
# Returns: True (if configured)
assert can_blacklist == True
```

**Example Output**: Returns `True` if address has blacklist permission in config

## Circuit Breaker Functions

### `setMintingEnabled`

**Description**: Enables or disables all minting operations across the protocol. Acts as an emergency circuit breaker.

**Parameters**:
- `_shouldEnable` (bool): True to enable minting, False to disable

**Access**: Only callable by governance

**Events Emitted**:
- `MintingEnabled` - Contains the new enabled state (isEnabled)

**Example Usage**:
```python
# Emergency: disable all minting
ripe_hq.setMintingEnabled(False, sender=governance.address)
assert ripe_hq.mintEnabled() == False

# Later: re-enable minting
ripe_hq.setMintingEnabled(True, sender=governance.address)
assert ripe_hq.mintEnabled() == True
```

**Example Output**: Emits `MintingEnabled` event with new state

## Recovery Functions

### `recoverFunds`

**Description**: Recovers tokens accidentally sent to the RipeHq contract. Transfers the full balance of a specified token to a recipient.

**Parameters**:
- `_recipient` (address): The address to receive recovered funds
- `_asset` (address): The token contract address to recover

**Access**: Only callable by governance

**Events Emitted**:
- `RipeHqFundsRecovered` - Contains the asset address (indexed), recipient address (indexed), and balance recovered

**Example Usage**:
```python
# Recover accidentally sent tokens
alpha_token.transfer(ripe_hq.address, 1000, sender=alpha_token_whale)
ripe_hq.recoverFunds(
    treasury.address,     # Send to Treasury
    alpha_token.address,  # Token to recover
    sender=governance.address
)
assert alpha_token.balanceOf(treasury.address) == 1000
```

**Example Output**: Transfers full USDC balance, emits `RipeHqFundsRecovered` event

### `recoverFundsMany`

**Description**: Recovers multiple tokens in a single transaction. Useful for batch recovery operations.

**Parameters**:
- `_recipient` (address): The address to receive all recovered funds
- `_assets` (DynArray[address, MAX_RECOVER_ASSETS]): List of token addresses to recover (max 20)

**Access**: Only callable by governance

**Events Emitted**:
- `RipeHqFundsRecovered` - One event per recovered asset with asset address (indexed), recipient (indexed), and balance

**Example Usage**:
```python
# Recover multiple tokens at once
alpha_token.transfer(ripe_hq.address, 2000, sender=alpha_token_whale)
bravo_token.transfer(ripe_hq.address, 2000, sender=bravo_token_whale)
charlie_token.transfer(ripe_hq.address, 2000, sender=charlie_token_whale)

assets = [alpha_token.address, bravo_token.address, charlie_token.address]
ripe_hq.recoverFundsMany(
    treasury.address,
    assets,
    sender=governance.address
)
assert alpha_token.balanceOf(treasury.address) == 2000
assert bravo_token.balanceOf(treasury.address) == 2000
assert charlie_token.balanceOf(treasury.address) == 2000
```

**Example Output**: Transfers all balances, emits `RipeHqFundsRecovered` for each token

**Note**: All registry-related events (for address additions, updates, and disabling) are emitted by the imported AddressRegistry module.

## Advanced Usage Examples

### Complete Department Registration Flow

```python
# Add a new department with full minting capabilities
time_lock = ripe_hq.registryChangeTimeLock()

# Step 1: Add the department to registry
ripe_hq.startAddNewAddressToRegistry(
    mock_dept_can_mint_green.address,
    "Green Minter",
    sender=governance.address
)

# Step 2: Wait for timelock and confirm
boa.env.time_travel(blocks=time_lock)
green_reg_id = ripe_hq.confirmNewAddressToRegistry(
    mock_dept_can_mint_green.address,
    sender=governance.address
)

# Step 3: Configure minting permissions
ripe_hq.initiateHqConfigChange(
    green_reg_id,
    True,   # Can mint Green
    False,  # Cannot mint Ripe
    False,  # Cannot set blacklist
    sender=governance.address
)

# Step 4: Wait for timelock and confirm config
boa.env.time_travel(blocks=time_lock)
assert ripe_hq.confirmHqConfigChange(green_reg_id, sender=governance.address)

# Verify configuration
assert ripe_hq.canMintGreen(mock_dept_can_mint_green.address)
```

### Testing Circuit Breaker with Actual Minting

```python
# Setup: User has collateral and can borrow
performDeposit(alice, 1000 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
max_borrow = credit_engine.getMaxBorrowAmount(alice)

# User can borrow when minting is enabled
teller.borrow(max_borrow // 2, alice, False, sender=alice)

# Disable minting via circuit breaker
ripe_hq.setMintingEnabled(False, sender=governance.address)

# User cannot borrow when minting is disabled
with boa.reverts("cannot mint"):
    teller.borrow(max_borrow // 4, alice, False, sender=alice)

# Re-enable minting
ripe_hq.setMintingEnabled(True, sender=governance.address)

# User can borrow again
teller.borrow(max_borrow // 4, alice, False, sender=alice)
```

### Handling Invalid Configurations

```python
# Token IDs (1-3) cannot have minting permissions
with boa.reverts("invalid hq config"):
    ripe_hq.initiateHqConfigChange(
        1,      # Green token ID
        True,   # Attempt to give minting permission
        False,
        False,
        sender=governance.address
    )

# Departments must support the permissions they're granted
with boa.reverts("invalid hq config"):
    ripe_hq.initiateHqConfigChange(
        green_minter_id,
        False,  # Can't mint Green
        True,   # But trying to grant Ripe minting (unsupported)
        False,
        sender=governance.address
    )
```

## Data Structures

### HqConfig Struct
Stores the configuration for each registered address:
```vyper
struct HqConfig:
    description: String[64]        # Human-readable description
    canMintGreen: bool            # Permission to mint Green tokens
    canMintRipe: bool             # Permission to mint Ripe tokens
    canSetTokenBlacklist: bool    # Permission to modify token blacklists
```

### PendingHqConfig Struct
Tracks pending configuration changes during the timelock period:
```vyper
struct PendingHqConfig:
    newHqConfig: HqConfig         # The new configuration to apply
    initiatedBlock: uint256       # Block when change was initiated
    confirmBlock: uint256         # Block when change can be confirmed
```

## State Variables

### Public State Variables
- `hqConfig: HashMap[uint256, HqConfig]` - Maps registry ID to its configuration
- `pendingHqConfig: HashMap[uint256, PendingHqConfig]` - Maps registry ID to pending config changes
- `mintEnabled: bool` - Global circuit breaker for all minting operations

### Constants
- `MAX_RECOVER_ASSETS: uint256 = 20` - Maximum number of assets recoverable in a single transaction

### Inherited State Variables (from modules)
From LocalGov:
- `governance: address` - Current governance address
- `govChangeTimeLock: uint256` - Timelock for governance changes

From AddressRegistry:
- `registryChangeTimeLock: uint256` - Timelock for registry changes
- Various internal registry mappings for address management

## Security Considerations

### Access Control
- All administrative functions require `msg.sender == gov.governance`
- Two-factor authentication for minting: both HQ config AND department must support minting
- Token contracts (IDs 1-3) cannot be granted minting permissions or blacklist control

### Timelock Protection
- All registry changes (add, update, disable) are subject to configurable timelocks
- All HQ configuration changes are subject to registry timelock
- Timelocks prevent rushed or malicious changes

### Circuit Breaker
- Global `mintEnabled` flag can instantly disable all minting across the protocol
- Only governance can toggle this emergency switch
- Affects both Green and Ripe token minting

### Validation Checks
- Departments must implement required interfaces (`canMintGreen()`, `canMintRipe()`)
- Zero address checks prevent invalid configurations
- Registry ID validation ensures operations on valid entries only

## Common Integration Patterns

### For New Departments
1. Deploy your department contract implementing the Department interface
2. Request governance to register your department via `startAddNewAddressToRegistry`
3. Wait for timelock and confirmation
4. Request appropriate permissions via `initiateHqConfigChange`
5. Implement required capability functions (`canMintGreen()`, etc.)

### For Token Integration
```python
# Check if an address can mint before attempting
if ripe_hq.canMintGreen(minter_address):
    green_token.mint(recipient, amount, sender=minter_address)
```

### For Governance Systems
```python
# Batch operations for efficiency
addresses = [dept1, dept2, dept3]
for addr in addresses:
    ripe_hq.startAddNewAddressToRegistry(addr, f"Department {i}", sender=governance)

# Wait for timelock
boa.env.time_travel(blocks=timelock)

# Confirm all
for addr in addresses:
    ripe_hq.confirmNewAddressToRegistry(addr, sender=governance)
```

## Error Messages Reference

### Common Reverts
- `"no perms"` - Caller is not governance
- `"invalid hq config"` - Configuration validation failed
- `"cannot disable token"` - Attempting to disable token contracts (IDs 1-3)
- `"time lock not reached"` - Attempting to confirm before timelock expires
- `"no pending change"` - No pending change to cancel
- `"already set"` - Attempting to set mint enabled to current state
- `"invalid recipient or asset"` - Invalid parameters for fund recovery
- `"nothing to recover"` - No balance to recover

## Testing

For comprehensive test examples, see: [`tests/registries/test_ripe_hq.py`](../tests/registries/test_ripe_hq.py)