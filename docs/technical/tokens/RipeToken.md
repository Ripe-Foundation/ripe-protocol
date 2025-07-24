# RipeToken Technical Documentation

[📄 View Source Code](../../contracts/tokens/RipeToken.vy)

## Overview

RipeToken (RIPE) is the governance token powering the Ripe DAO, granting holders voting rights over protocol parameters, treasury allocation, and strategic direction. Distributed through rewards, bonding, and initial allocations, RIPE aligns stakeholder incentives with long-term protocol success.

**Governance Powers**:
- **Protocol Parameters**: Vote on collateral ratios, fee structures, and risk parameters
- **Treasury Management**: Direct allocation of protocol revenues and strategic reserves
- **Contract Upgrades**: Approve new modules and protocol improvements through governance
- **Reward Distribution**: Control emission rates and allocation across protocol activities

RIPE implements controlled minting through [RipeHq](../registries/RipeHq.md) authorization, ensuring transparent distribution according to DAO-approved rules. The token features EIP-2612 permits, emergency controls, and time-locked transitions for secure decentralized governance. RIPE is distributed via [Lootbox](../core/Lootbox.md) rewards, [BondRoom](../core/BondRoom.md) purchases, and can be locked in [RipeGov](../vaults/RipeGov.md) for enhanced governance power.

## Architecture & Modules

RipeToken is built using a modular architecture that inherits comprehensive ERC20 functionality:

### Erc20Token Module

- **Location**: `contracts/tokens/modules/Erc20Token.vy`
- **Purpose**: Provides complete ERC20 token functionality with advanced features
- **Key Features**:
  - Standard ERC20 operations (transfer, approve, allowance)
  - EIP-2612 permit functionality for gasless approvals
  - Blacklist system for compliance
  - Pause mechanism for emergency stops
  - Time-locked governance transitions
  - Secure minting and burning capabilities
- **Exported Interface**: Complete token interface via `token.__interface__`

### Module Initialization

```vyper
exports: token.__interface__
initializes: token
```

## System Architecture Diagram

```
+------------------------------------------------------------------------+
|                         RipeToken Contract                            |
+------------------------------------------------------------------------+
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                     Erc20Token Module                            |  |
|  |                                                                  |  |
|  |  +----------------+ +----------------+ +----------------+       |  |
|  |  | Core ERC20     | | Advanced       | | Security       |       |  |
|  |  | Functions      | | Features       | | Features       |       |  |
|  |  |                | |                | |                |       |  |
|  |  | * transfer     | | * permit       | | * blacklist    |       |  |
|  |  | * transferFrom | | * EIP-712      | | * pause        |       |  |
|  |  | * approve      | | * nonces       | | * timelock     |       |  |
|  |  | * allowance    | | * domain sep   | | * governance   |       |  |
|  |  | * balanceOf    | | * signatures   | | * validation   |       |  |
|  |  | * totalSupply  | |                | |                |       |  |
|  |  +----------------+ +----------------+ +----------------+       |  |
|  |                                                                  |  |
|  |  +----------------+ +----------------+ +----------------+       |  |
|  |  | Token Info     | | Mint/Burn      | | RipeHq         |       |  |
|  |  |                | |                | | Integration    |       |  |
|  |  | * name         | | * _mint        | |                |       |  |
|  |  | * symbol       | | * burn         | | * canMintRipe  |       |  |
|  |  | * decimals     | | * _burn        | | * governance   |       |  |
|  |  | * version      | |                | | * validation   |       |  |
|  |  +----------------+ +----------------+ +----------------+       |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    RipeToken Specific Layer                      |  |
|  |                                                                  |  |
|  |  Ripe Token Minting:                                             |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ mint(_recipient, _amount)                                   │ |  |
|  |  │ 1. Check RipeHq.canMintRipe(msg.sender)                     │ |  |
|  |  │    - Validates global minting enabled                       │ |  |
|  |  │    - Checks caller has minting permission                   │ |  |
|  |  │    - Confirms caller's contract supports Ripe minting      │ |  |
|  |  │ 2. Call token._mint(_recipient, _amount)                    │ |  |
|  |  │    - Validates recipient not blacklisted                    │ |  |
|  |  │    - Ensures token not paused                               │ |  |
|  |  │    - Updates balances and total supply                      │ |  |
|  |  │    - Emits Transfer event from zero address                 │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  +------------------------------------------------------------------+  |
+------------------------------------------------------------------------+
                                    |
        +---------------------------+---------------------------+
        |                           |                           |
        v                           v                           v
+------------------+    +-------------------+    +------------------+
| RipeHq           |    | Protocol          |    | Users &          |
| Validation       |    | Contracts         |    | External         |
|                  |    |                   |    | Interfaces       |
| * canMintRipe    |    | * Lootbox         |    |                  |
| * governance     |    | * BondRoom        |    | * ERC20 ops      |
| * blacklist      |    | * Endaoment       |    | * Permit         |
| * permissions    |    | * Teller          |    | * Transfers      |
+------------------+    | * CreditEngine    |    | * Approvals      |
                        +-------------------+    +------------------+
```

## Data Structures

### PendingHq Struct

Tracks pending RipeHq address changes:

```vyper
struct PendingHq:
    newHq: address                    # New RipeHq address
    initiatedBlock: uint256           # Block when change was initiated
    confirmBlock: uint256             # Block when change can be confirmed
```

## State Variables

### Token Information (Immutable)

- `TOKEN_NAME: String[64]` - "Ripe DAO Governance Token"
- `TOKEN_SYMBOL: String[32]` - "RIPE"
- `TOKEN_DECIMALS: uint8` - 18 decimals
- `VERSION: String[8]` - "v1.0.0"

### Core ERC20 State

- `balanceOf: HashMap[address, uint256]` - Token balances
- `allowance: HashMap[address, HashMap[address, uint256]]` - Spending approvals
- `totalSupply: uint256` - Total token supply

### Security and Governance

- `ripeHq: address` - Current RipeHq contract address
- `blacklisted: HashMap[address, bool]` - Blacklisted addresses
- `isPaused: bool` - Token pause state
- `pendingHq: PendingHq` - Pending RipeHq change data
- `hqChangeTimeLock: uint256` - Time lock for RipeHq changes

### EIP-712 Support

- `nonces: HashMap[address, uint256]` - Permit nonces for each address
- Domain separator components for signature validation

### Constants and Immutable

- `MIN_HQ_TIME_LOCK: uint256` - Minimum time lock for RipeHq changes
- `MAX_HQ_TIME_LOCK: uint256` - Maximum time lock for RipeHq changes
- Various EIP-712 and cryptographic constants

## Constructor

### `__init__`

Initializes the RipeToken with comprehensive configuration parameters.

```vyper
@deploy
def __init__(
    _ripeHq: address,
    _initialGov: address,
    _minHqTimeLock: uint256,
    _maxHqTimeLock: uint256,
    _initialSupply: uint256,
    _initialSupplyRecipient: address,
):
```

#### Parameters

| Name                      | Type      | Description                                            |
| ------------------------- | --------- | ------------------------------------------------------ |
| `_ripeHq`                 | `address` | RipeHq contract address (empty for initial deployment) |
| `_initialGov`             | `address` | Initial governance address (for setup phase)           |
| `_minHqTimeLock`          | `uint256` | Minimum time lock for RipeHq changes                   |
| `_maxHqTimeLock`          | `uint256` | Maximum time lock for RipeHq changes                   |
| `_initialSupply`          | `uint256` | Initial token supply to mint                           |
| `_initialSupplyRecipient` | `address` | Recipient of initial supply                            |

#### Returns

_Constructor does not return any values_

#### Access

Called only during deployment

#### Example Usage

```python
# Deploy Ripe token with initial governance
ripe_token = boa.load(
    "contracts/tokens/RipeToken.vy",
    empty(address),           # No RipeHq initially
    deployer.address,         # Initial governance
    100,                      # Min timelock: 100 blocks
    1000,                     # Max timelock: 1000 blocks
    1000000_000000000000000000,  # 1M initial supply
    treasury.address          # Initial supply recipient
)
```

**Example Output**: Token deployed with name "Ripe DAO Governance Token", symbol "RIPE", 18 decimals, initial supply minted to recipient

## Core ERC20 Functions

### `name`

Returns the token name.

```vyper
@view
@external
def name() -> String[64]:
```

#### Returns

| Type         | Description                 |
| ------------ | --------------------------- |
| `String[64]` | "Ripe DAO Governance Token" |

#### Access

Public view function

### `symbol`

Returns the token symbol.

```vyper
@view
@external
def symbol() -> String[32]:
```

#### Returns

| Type         | Description |
| ------------ | ----------- |
| `String[32]` | "RIPE"      |

#### Access

Public view function

### `decimals`

Returns the number of decimal places.

```vyper
@view
@external
def decimals() -> uint8:
```

#### Returns

| Type    | Description |
| ------- | ----------- |
| `uint8` | 18 decimals |

#### Access

Public view function

### `totalSupply`

Returns the total token supply.

```vyper
@view
@external
def totalSupply() -> uint256:
```

#### Returns

| Type      | Description                 |
| --------- | --------------------------- |
| `uint256` | Total supply of Ripe tokens |

#### Access

Public view function

### `balanceOf`

Returns the token balance of an account.

```vyper
@view
@external
def balanceOf(_account: address) -> uint256:
```

#### Parameters

| Name       | Type      | Description      |
| ---------- | --------- | ---------------- |
| `_account` | `address` | Account to check |

#### Returns

| Type      | Description                  |
| --------- | ---------------------------- |
| `uint256` | Token balance of the account |

#### Access

Public view function

## Transfer Functions

### `transfer`

Transfers tokens from caller to recipient.

```vyper
@external
def transfer(_recipient: address, _amount: uint256) -> bool:
```

#### Parameters

| Name         | Type      | Description               |
| ------------ | --------- | ------------------------- |
| `_recipient` | `address` | Address to receive tokens |
| `_amount`    | `uint256` | Amount to transfer        |

#### Returns

| Type   | Description                 |
| ------ | --------------------------- |
| `bool` | True if transfer successful |

#### Access

Public function (requires caller not blacklisted, token not paused)

#### Events Emitted

- `Transfer` - Contains sender, recipient, and amount

#### Example Usage

```python
# Transfer 100 Ripe tokens
success = ripe_token.transfer(
    recipient.address,
    100_000000000000000000,  # 100 RIPE
    sender=user.address
)
assert success == True
```

### `transferFrom`

Transfers tokens from one address to another using allowance.

```vyper
@external
def transferFrom(_sender: address, _recipient: address, _amount: uint256) -> bool:
```

#### Parameters

| Name         | Type      | Description               |
| ------------ | --------- | ------------------------- |
| `_sender`    | `address` | Address to send from      |
| `_recipient` | `address` | Address to receive tokens |
| `_amount`    | `uint256` | Amount to transfer        |

#### Returns

| Type   | Description                 |
| ------ | --------------------------- |
| `bool` | True if transfer successful |

#### Access

Public function (requires sufficient allowance, parties not blacklisted)

#### Events Emitted

- `Transfer` - Contains sender, recipient, and amount
- `Approval` - If allowance is updated

#### Example Usage

```python
# Transfer on behalf of user
success = ripe_token.transferFrom(
    user.address,
    recipient.address,
    50_000000000000000000,  # 50 RIPE
    sender=approved_spender.address
)
```

## Approval Functions

### `approve`

Sets spending allowance for a spender.

```vyper
@external
def approve(_spender: address, _amount: uint256) -> bool:
```

#### Parameters

| Name       | Type      | Description                  |
| ---------- | --------- | ---------------------------- |
| `_spender` | `address` | Address authorized to spend  |
| `_amount`  | `uint256` | Amount approved for spending |

#### Returns

| Type   | Description                 |
| ------ | --------------------------- |
| `bool` | True if approval successful |

#### Access

Public function (requires parties not blacklisted, token not paused)

#### Events Emitted

- `Approval` - Contains owner, spender, and amount

#### Example Usage

```python
# Approve spending
success = ripe_token.approve(
    spender.address,
    1000_000000000000000000,  # 1000 RIPE
    sender=owner.address
)
```

### `allowance`

Returns the spending allowance.

```vyper
@view
@external
def allowance(_owner: address, _spender: address) -> uint256:
```

#### Parameters

| Name       | Type      | Description        |
| ---------- | --------- | ------------------ |
| `_owner`   | `address` | Token owner        |
| `_spender` | `address` | Authorized spender |

#### Returns

| Type      | Description              |
| --------- | ------------------------ |
| `uint256` | Current allowance amount |

#### Access

Public view function

### `increaseAllowance`

Increases the spending allowance.

```vyper
@external
def increaseAllowance(_spender: address, _amount: uint256) -> bool:
```

#### Parameters

| Name       | Type      | Description                       |
| ---------- | --------- | --------------------------------- |
| `_spender` | `address` | Address to increase allowance for |
| `_amount`  | `uint256` | Amount to increase by             |

#### Returns

| Type   | Description                 |
| ------ | --------------------------- |
| `bool` | True if increase successful |

#### Access

Public function (requires parties not blacklisted, token not paused)

### `decreaseAllowance`

Decreases the spending allowance.

```vyper
@external
def decreaseAllowance(_spender: address, _amount: uint256) -> bool:
```

#### Parameters

| Name       | Type      | Description                       |
| ---------- | --------- | --------------------------------- |
| `_spender` | `address` | Address to decrease allowance for |
| `_amount`  | `uint256` | Amount to decrease by             |

#### Returns

| Type   | Description                 |
| ------ | --------------------------- |
| `bool` | True if decrease successful |

#### Access

Public function (requires parties not blacklisted, token not paused)

## Minting and Burning Functions

### `mint`

Mints new Ripe tokens (RipeToken-specific function).

```vyper
@external
def mint(_recipient: address, _amount: uint256) -> bool:
```

#### Parameters

| Name         | Type      | Description                   |
| ------------ | --------- | ----------------------------- |
| `_recipient` | `address` | Address to receive new tokens |
| `_amount`    | `uint256` | Amount of tokens to mint      |

#### Returns

| Type   | Description             |
| ------ | ----------------------- |
| `bool` | True if mint successful |

#### Access

Only callable by addresses authorized through [RipeHq](../registries/RipeHq.md)'s `canMintRipe` validation

#### Events Emitted

- `Transfer` - Contains zero address as sender, recipient, and amount

#### Example Usage

```python
# Mint Ripe tokens (only authorized contracts)
success = ripe_token.mint(
    user.address,
    500_000000000000000000,  # 500 RIPE
    sender=lootbox.address  # Must be authorized
)
```

**Example Output**: Mints 500 RIPE to user, increases total supply

### `burn`

Burns tokens from caller's balance.

```vyper
@external
def burn(_amount: uint256) -> bool:
```

#### Parameters

| Name      | Type      | Description              |
| --------- | --------- | ------------------------ |
| `_amount` | `uint256` | Amount of tokens to burn |

#### Returns

| Type   | Description             |
| ------ | ----------------------- |
| `bool` | True if burn successful |

#### Access

Public function (requires token not paused, sufficient balance)

#### Events Emitted

- `Transfer` - Contains sender, zero address as recipient, and amount

#### Example Usage

```python
# Burn own tokens
success = ripe_token.burn(
    100_000000000000000000,  # 100 RIPE
    sender=user.address
)
```

## EIP-2612 Permit Functions

### `DOMAIN_SEPARATOR`

Returns the EIP-712 domain separator.

```vyper
@view
@external
def DOMAIN_SEPARATOR() -> bytes32:
```

#### Returns

| Type      | Description                   |
| --------- | ----------------------------- |
| `bytes32` | Current domain separator hash |

#### Access

Public view function

### `nonces`

Returns the current permit nonce for an address.

```vyper
@view
@external
def nonces(_owner: address) -> uint256:
```

#### Parameters

| Name     | Type      | Description                |
| -------- | --------- | -------------------------- |
| `_owner` | `address` | Address to check nonce for |

#### Returns

| Type      | Description         |
| --------- | ------------------- |
| `uint256` | Current nonce value |

#### Access

Public view function

### `permit`

Sets approval using a signed message (gasless approval).

```vyper
@external
def permit(
    _owner: address,
    _spender: address,
    _value: uint256,
    _deadline: uint256,
    _signature: Bytes[65],
) -> bool:
```

#### Parameters

| Name         | Type        | Description                    |
| ------------ | ----------- | ------------------------------ |
| `_owner`     | `address`   | Token owner granting approval  |
| `_spender`   | `address`   | Address authorized to spend    |
| `_value`     | `uint256`   | Approval amount                |
| `_deadline`  | `uint256`   | Signature expiration timestamp |
| `_signature` | `Bytes[65]` | EIP-712 signature              |

#### Returns

| Type   | Description               |
| ------ | ------------------------- |
| `bool` | True if permit successful |

#### Access

Public function (signature must be valid and not expired)

#### Events Emitted

- `Approval` - Contains owner, spender, and value

#### Example Usage

```python
# Create permit signature off-chain, then use it
success = ripe_token.permit(
    owner.address,
    spender.address,
    1000_000000000000000000,  # 1000 RIPE
    block.timestamp + 3600,   # 1 hour deadline
    signature,                # EIP-712 signature
    sender=anyone.address     # Can be submitted by anyone
)
```

## Blacklist Functions

### `blacklisted`

Checks if an address is blacklisted.

```vyper
@view
@external
def blacklisted(_addr: address) -> bool:
```

#### Parameters

| Name    | Type      | Description      |
| ------- | --------- | ---------------- |
| `_addr` | `address` | Address to check |

#### Returns

| Type   | Description                    |
| ------ | ------------------------------ |
| `bool` | True if address is blacklisted |

#### Access

Public view function

### `setBlacklist`

Adds or removes an address from the blacklist.

```vyper
@external
def setBlacklist(_addr: address, _shouldBlacklist: bool) -> bool:
```

#### Parameters

| Name               | Type      | Description                        |
| ------------------ | --------- | ---------------------------------- |
| `_addr`            | `address` | Address to blacklist/unblacklist   |
| `_shouldBlacklist` | `bool`    | True to blacklist, False to remove |

#### Returns

| Type   | Description                  |
| ------ | ---------------------------- |
| `bool` | True if operation successful |

#### Access

Only callable by addresses authorized through [RipeHq](../registries/RipeHq.md)'s `canSetTokenBlacklist`

#### Events Emitted

- `BlacklistModified` - Contains address and blacklist status

#### Example Usage

```python
# Blacklist an address (only authorized contracts)
success = ripe_token.setBlacklist(
    bad_actor.address,
    True,  # Blacklist
    sender=compliance_manager.address  # Must be authorized
)
```

### `burnBlacklistTokens`

Burns tokens from a blacklisted address.

```vyper
@external
def burnBlacklistTokens(_addr: address, _amount: uint256 = max_value(uint256)) -> bool:
```

#### Parameters

| Name      | Type      | Description                              |
| --------- | --------- | ---------------------------------------- |
| `_addr`   | `address` | Blacklisted address to burn from         |
| `_amount` | `uint256` | Amount to burn (default: entire balance) |

#### Returns

| Type   | Description             |
| ------ | ----------------------- |
| `bool` | True if burn successful |

#### Access

Only callable by [RipeHq](../registries/RipeHq.md) governance

#### Events Emitted

- `Transfer` - Contains address, zero address, and amount burned

## RipeHq Management Functions

### `ripeHq`

Returns the current RipeHq contract address.

```vyper
@view
@external
def ripeHq() -> address:
```

#### Returns

| Type      | Description                     |
| --------- | ------------------------------- |
| `address` | Current RipeHq contract address |

#### Access

Public view function

### `hasPendingHqChange`

Checks if there's a pending RipeHq address change.

```vyper
@view
@external
def hasPendingHqChange() -> bool:
```

#### Returns

| Type   | Description                      |
| ------ | -------------------------------- |
| `bool` | True if RipeHq change is pending |

#### Access

Public view function

### `initiateHqChange`

Initiates a time-locked change of RipeHq address.

```vyper
@external
def initiateHqChange(_newHq: address):
```

#### Parameters

| Name     | Type      | Description                 |
| -------- | --------- | --------------------------- |
| `_newHq` | `address` | New RipeHq contract address |

#### Returns

_Function does not return any values_

#### Access

Only callable by [RipeHq](../registries/RipeHq.md) governance

#### Events Emitted

- `HqChangeInitiated` - Contains previous HQ, new HQ, and confirmation block

#### Example Usage

```python
# Initiate RipeHq change
ripe_token.initiateHqChange(
    new_ripe_hq.address,
    sender=governance.address
)
```

### `confirmHqChange`

Confirms a pending RipeHq change after time lock.

```vyper
@external
def confirmHqChange() -> bool:
```

#### Returns

| Type   | Description                                          |
| ------ | ---------------------------------------------------- |
| `bool` | True if change confirmed, False if validation failed |

#### Access

Only callable by [RipeHq](../registries/RipeHq.md) governance

#### Events Emitted

- `HqChangeConfirmed` - Contains previous HQ, new HQ, initiation block, and confirmation block

#### Example Usage

```python
# Wait for time lock
boa.env.time_travel(blocks=time_lock)

# Confirm change
success = ripe_token.confirmHqChange(sender=governance.address)
```

### `cancelHqChange`

Cancels a pending RipeHq change.

```vyper
@external
def cancelHqChange():
```

#### Access

Only callable by [RipeHq](../registries/RipeHq.md) governance

#### Events Emitted

- `HqChangeCancelled` - Contains cancelled HQ, initiation block, and confirmation block

### `isValidNewRipeHq`

Validates if an address can be set as the new RipeHq.

```vyper
@view
@external
def isValidNewRipeHq(_newHq: address) -> bool:
```

#### Parameters

| Name     | Type      | Description         |
| -------- | --------- | ------------------- |
| `_newHq` | `address` | Address to validate |

#### Returns

| Type   | Description                     |
| ------ | ------------------------------- |
| `bool` | True if address is valid RipeHq |

#### Access

Public view function

## Time Lock Configuration Functions

### `hqChangeTimeLock`

Returns the current time lock for RipeHq changes.

```vyper
@view
@external
def hqChangeTimeLock() -> uint256:
```

#### Returns

| Type      | Description                 |
| --------- | --------------------------- |
| `uint256` | Current time lock in blocks |

#### Access

Public view function

### `setHqChangeTimeLock`

Updates the RipeHq change time lock.

```vyper
@external
def setHqChangeTimeLock(_newTimeLock: uint256) -> bool:
```

#### Parameters

| Name           | Type      | Description                    |
| -------------- | --------- | ------------------------------ |
| `_newTimeLock` | `uint256` | New time lock period in blocks |

#### Returns

| Type   | Description               |
| ------ | ------------------------- |
| `bool` | True if update successful |

#### Access

Only callable by [RipeHq](../registries/RipeHq.md) governance (when no pending governance changes)

#### Events Emitted

- `HqChangeTimeLockModified` - Contains previous and new time lock values

### `isValidHqChangeTimeLock`

Validates a proposed time lock value.

```vyper
@view
@external
def isValidHqChangeTimeLock(_newTimeLock: uint256) -> bool:
```

#### Parameters

| Name           | Type      | Description              |
| -------------- | --------- | ------------------------ |
| `_newTimeLock` | `uint256` | Proposed time lock value |

#### Returns

| Type   | Description                |
| ------ | -------------------------- |
| `bool` | True if time lock is valid |

#### Access

Public view function

### `minHqTimeLock`

Returns the minimum allowed time lock.

```vyper
@view
@external
def minHqTimeLock() -> uint256:
```

#### Returns

| Type      | Description                 |
| --------- | --------------------------- |
| `uint256` | Minimum time lock in blocks |

#### Access

Public view function

### `maxHqTimeLock`

Returns the maximum allowed time lock.

```vyper
@view
@external
def maxHqTimeLock() -> uint256:
```

#### Returns

| Type      | Description                 |
| --------- | --------------------------- |
| `uint256` | Maximum time lock in blocks |

#### Access

Public view function

## Pause Functions

### `isPaused`

Returns the token's pause state.

```vyper
@view
@external
def isPaused() -> bool:
```

#### Returns

| Type   | Description             |
| ------ | ----------------------- |
| `bool` | True if token is paused |

#### Access

Public view function

### `pause`

Pauses or unpauses all token operations.

```vyper
@external
def pause(_shouldPause: bool):
```

#### Parameters

| Name           | Type   | Description                     |
| -------------- | ------ | ------------------------------- |
| `_shouldPause` | `bool` | True to pause, False to unpause |

#### Access

Only callable by [RipeHq](../registries/RipeHq.md) governance

#### Events Emitted

- `TokenPauseModified` - Contains new pause state

#### Example Usage

```python
# Emergency pause
ripe_token.pause(True, sender=governance.address)

# Resume operations
ripe_token.pause(False, sender=governance.address)
```

## Setup Functions

### `finishTokenSetup`

Completes initial token setup by setting RipeHq (one-time use).

```vyper
@external
def finishTokenSetup(_newHq: address, _timeLock: uint256 = 0) -> bool:
```

#### Parameters

| Name        | Type      | Description                         |
| ----------- | --------- | ----------------------------------- |
| `_newHq`    | `address` | RipeHq contract address             |
| `_timeLock` | `uint256` | Time lock duration (0 uses minimum) |

#### Returns

| Type   | Description              |
| ------ | ------------------------ |
| `bool` | True if setup successful |

#### Access

Only callable by initial governance (one-time use during deployment)

#### Events Emitted

- `InitialRipeHqSet` - Contains HQ address and time lock value

#### Example Usage

```python
# Complete token setup
success = ripe_token.finishTokenSetup(
    ripe_hq.address,
    500,  # 500 block time lock
    sender=initial_gov.address
)
```

## Testing

For comprehensive test examples, see: [`tests/tokens/test_erc20.py`](../../tests/tokens/test_erc20.py)
