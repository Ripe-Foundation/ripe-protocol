# Erc20Token Technical Documentation

[📄 View Source Code](../../../contracts/tokens/modules/Erc20Token.vy)

## Overview

Erc20Token is the foundational token module for Ripe Protocol, providing enhanced ERC20 functionality with built-in security and governance features. It extends standard ERC20 with blacklisting, pausability, permit functionality, and deep RipeHq integration for enterprise-grade token management.

**Core Features**:
- **Enhanced ERC20**: Standard operations with blacklist validation and pause checks
- **Governance Integration**: RipeHq controls minting, blacklisting, and pausing permissions
- **Permit System**: EIP-2612 gasless approvals via signatures (EOA and ERC-1271)
- **Blacklist Management**: Compliance tools with ability to burn blacklisted tokens
- **Safe Migrations**: Time-locked RipeHq updates prevent rushed protocol changes

The module implements comprehensive security including reentrancy protection, extensive validation, and detailed event logging. It supports initial supply distribution and two-phase setup for pre-RipeHq deployments, ensuring flexible yet secure token operations.

## Architecture & Dependencies

Erc20Token is designed as a standalone module with external dependencies:

### External Contract Interfaces
- **RipeHq**: Central registry for permissions and governance
- **ERC1271**: Smart contract signature validation interface

### Key Constants
```vyper
# EIP-712 Constants
EIP712_TYPEHASH: constant(bytes32) = keccak256("EIP712Domain(...)")
EIP2612_TYPEHASH: constant(bytes32) = keccak256("Permit(...)")
ECRECOVER_PRECOMPILE: constant(address) = 0x0000...0001
ERC1271_MAGIC_VAL: constant(bytes4) = 0x1626ba7e
VERSION: constant(String[8]) = "v1.0.0"
```

### Immutable Values
Set during deployment:
```vyper
TOKEN_NAME: immutable(String[64])
TOKEN_SYMBOL: immutable(String[32])
TOKEN_DECIMALS: immutable(uint8)
MIN_HQ_TIME_LOCK: immutable(uint256)
MAX_HQ_TIME_LOCK: immutable(uint256)
CACHED_DOMAIN_SEPARATOR: immutable(bytes32)
NAME_HASH: immutable(bytes32)
CACHED_CHAIN_ID: immutable(uint256)
```

## Data Structures

### PendingHq Struct
Tracks pending RipeHq changes:
```vyper
struct PendingHq:
    newHq: address           # Proposed new RipeHq
    initiatedBlock: uint256  # When change started
    confirmBlock: uint256    # When change can be confirmed
```

## State Variables

### Token State
- `balanceOf: HashMap[address, uint256]` - Token balances
- `allowance: HashMap[address, HashMap[address, uint256]]` - Spending allowances
- `totalSupply: uint256` - Total token supply

### Governance State
- `ripeHq: address` - Current RipeHq contract
- `pendingHq: PendingHq` - Pending RipeHq change
- `hqChangeTimeLock: uint256` - Blocks required for HQ changes
- `tempGov: address` - Temporary governance (before RipeHq set)

### Security State
- `blacklisted: HashMap[address, bool]` - Blacklisted addresses
- `isPaused: bool` - Global pause state

### EIP-712 State
- `nonces: HashMap[address, uint256]` - Permit nonces

## System Architecture Diagram

```
+------------------------------------------------------------------------+
|                         Erc20Token Module                             |
+------------------------------------------------------------------------+
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Token Operations Flow                         |  |
|  |                                                                  |  |
|  |  transfer/transferFrom:                                          |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ 1. Check not paused                                        │ |  |
|  |  │ 2. Validate amount > 0                                     │ |  |
|  |  │ 3. Check sender not blacklisted                            │ |  |
|  |  │ 4. Check recipient not blacklisted                         │ |  |
|  |  │ 5. Check recipient not token/0x0                           │ |  |
|  |  │ 6. Verify sufficient balance                               │ |  |
|  |  │ 7. Update balances                                         │ |  |
|  |  │ 8. Emit Transfer event                                     │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  |                                                                  |  |
|  |  Permission Checks:                                              |  |
|  |  • Minting: RipeHq.canMintGreen() or canMintRipe()             |  |
|  |  • Blacklist: RipeHq.canSetTokenBlacklist()                    |  |
|  |  • Pause: RipeHq.governance()                                   |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    Permit System (EIP-2612)                      |  |
|  |                                                                  |  |
|  |  Off-chain Signature:                                            |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ User signs: Permit(owner, spender, value, nonce, deadline) │ |  |
|  |  │                        ↓                                     │ |  |
|  |  │              EIP-712 Structured Data                        │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  |                                                                  |  |
|  |  On-chain Verification:                                          |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ 1. Check deadline not expired                               │ |  |
|  |  │ 2. Verify nonce matches                                     │ |  |
|  |  │ 3. EOA: ecrecover signature                                │ |  |
|  |  │    OR                                                       │ |  |
|  |  │    Contract: ERC-1271 validation                            │ |  |
|  |  │ 4. Update allowance                                         │ |  |
|  |  │ 5. Increment nonce                                          │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +------------------------------------------------------------------+  |
|  |                    RipeHq Integration                            |  |
|  |                                                                  |  |
|  |  Initial Setup (if deployed before RipeHq):                      |  |
|  |  Token Deploy → tempGov set → finishTokenSetup() → ripeHq set   |  |
|  |                                                                  |  |
|  |  RipeHq Migration (Two-Phase):                                   |  |
|  |  ┌─────────────────────────────────────────────────────────────┐ |  |
|  |  │ initiateHqChange():                                         │ |  |
|  |  │ • Validate new HQ (contracts, no pending changes)           │ |  |
|  |  │ • Set pending with timelock                                 │ |  |
|  |  │                    ↓ (hqChangeTimeLock blocks)              │ |  |
|  |  │ confirmHqChange():                                          │ |  |
|  |  │ • Re-validate new HQ                                        │ |  |
|  |  │ • Update ripeHq pointer                                     │ |  |
|  |  │ • Clear pending state                                       │ |  |
|  |  └─────────────────────────────────────────────────────────────┘ |  |
|  +------------------------------------------------------------------+  |
+------------------------------------------------------------------------+
                                    |
                                    ▼
+------------------------------------------------------------------------+
|                              RipeHq                                   |
+------------------------------------------------------------------------+
| • Permission validation (mint, blacklist, pause)                      |
| • Governance address resolution                                        |
| • Protocol-wide configuration                                          |
+------------------------------------------------------------------------+
```

## Constructor

### `__init__`

Initializes the ERC20 token with configuration and optional initial supply.

```vyper
@deploy
def __init__(
    _tokenName: String[64],
    _tokenSymbol: String[32],
    _tokenDecimals: uint8,
    _ripeHq: address,
    _initialGov: address,
    _minHqTimeLock: uint256,
    _maxHqTimeLock: uint256,
    _initialSupply: uint256,
    _initialSupplyRecipient: address,
):
```

#### Parameters

| Name | Type | Description |
|------|------|-------------|
| `_tokenName` | `String[64]` | Full token name (e.g., "Green Token") |
| `_tokenSymbol` | `String[32]` | Token symbol (e.g., "GREEN") |
| `_tokenDecimals` | `uint8` | Decimal places (typically 18) |
| `_ripeHq` | `address` | RipeHq contract (or empty if using tempGov) |
| `_initialGov` | `address` | Temporary governance (or empty if using RipeHq) |
| `_minHqTimeLock` | `uint256` | Minimum blocks for HQ changes |
| `_maxHqTimeLock` | `uint256` | Maximum blocks for HQ changes |
| `_initialSupply` | `uint256` | Initial token supply to mint |
| `_initialSupplyRecipient` | `address` | Who receives initial supply |

#### Deployment Modes
1. **With RipeHq**: Set `_ripeHq`, leave `_initialGov` empty
2. **With TempGov**: Set `_initialGov`, leave `_ripeHq` empty, call `finishTokenSetup` later

#### Example Usage
```python
# Deploy with RipeHq
green_token = boa.load(
    "path/to/Erc20Token.vy",
    "Green Token",
    "GREEN",
    18,
    ripe_hq.address,
    empty_address,  # No temp gov
    100,   # Min timelock
    1000,  # Max timelock
    10**9 * 10**18,  # 1B initial supply
    treasury.address
)

# Deploy with temporary governance
ripe_token = boa.load(
    "path/to/Erc20Token.vy",
    "Ripe Token",
    "RIPE",
    18,
    empty_address,  # No RipeHq yet
    deployer.address,  # Temp gov
    100,
    1000,
    0,  # No initial supply
    empty_address
)
```

## Core Token Functions

### Transfer Functions

#### `transfer`
```vyper
@external
def transfer(_recipient: address, _amount: uint256) -> bool:
```

Standard ERC20 transfer with blacklist and pause checks.

**Events Emitted**: `Transfer`

#### `transferFrom`
```vyper
@external
def transferFrom(_sender: address, _recipient: address, _amount: uint256) -> bool:
```

Transfer on behalf of another address using allowance.

**Events Emitted**: `Transfer`, `Approval`

### Allowance Functions

#### `approve`
```vyper
@external
def approve(_spender: address, _amount: uint256) -> bool:
```

Set spending allowance with validation.

**Events Emitted**: `Approval`

#### `increaseAllowance`
```vyper
@external
def increaseAllowance(_spender: address, _amount: uint256) -> bool:
```

Safely increase allowance (prevents race conditions).

**Events Emitted**: `Approval`

#### `decreaseAllowance`
```vyper
@external
def decreaseAllowance(_spender: address, _amount: uint256) -> bool:
```

Safely decrease allowance (prevents underflow).

**Events Emitted**: `Approval`

### Minting and Burning

#### `mint` (Internal)
```vyper
@internal
def _mint(_recipient: address, _amount: uint256) -> bool:
```

Mints new tokens. Must be called by inheriting contract with proper permissions.

**Events Emitted**: `Transfer`

#### `burn`
```vyper
@external
def burn(_amount: uint256) -> bool:
```

Burns tokens from caller's balance.

**Events Emitted**: `Transfer`

## Permit Function (EIP-2612)

### `permit`

Allows token approvals via signatures.

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

| Name | Type | Description |
|------|------|-------------|
| `_owner` | `address` | Token owner granting approval |
| `_spender` | `address` | Address receiving approval |
| `_value` | `uint256` | Approval amount |
| `_deadline` | `uint256` | Signature expiration timestamp |
| `_signature` | `Bytes[65]` | Signature (r,s,v format) |

#### Signature Validation
- **EOA**: Uses ecrecover with malleability checks
- **Contract**: Calls ERC-1271 `isValidSignature`

#### Example Usage
```python
# Off-chain signature creation
domain = {
    'name': 'Green Token',
    'version': 'v1.0.0',
    'chainId': 1,
    'verifyingContract': token.address
}

message = {
    'owner': owner.address,
    'spender': spender.address,
    'value': amount,
    'nonce': token.nonces(owner.address),
    'deadline': deadline
}

# Sign message
signature = sign_typed_data(owner_key, domain, types, message)

# On-chain permit
token.permit(
    owner.address,
    spender.address,
    amount,
    deadline,
    signature
)
```

**Events Emitted**: `Approval`

## Blacklist Functions

### `setBlacklist`

Adds or removes addresses from blacklist.

```vyper
@external
def setBlacklist(_addr: address, _shouldBlacklist: bool) -> bool:
```

#### Access

Only addresses with `canSetTokenBlacklist` permission in [RipeHq](../../registries/RipeHq.md).

#### Restrictions
- Cannot blacklist token contract itself
- Cannot blacklist zero address

**Events Emitted**: `BlacklistModified`

### `burnBlacklistTokens`

Burns tokens from blacklisted addresses.

```vyper
@external
def burnBlacklistTokens(_addr: address, _amount: uint256 = max_value(uint256)) -> bool:
```

#### Access

Only protocol governance.

**Events Emitted**: `Transfer`

#### Parameters
- `_amount`: Amount to burn (defaults to full balance)

## RipeHq Management

### `initiateHqChange`

Starts migration to new RipeHq contract.

```vyper
@external
def initiateHqChange(_newHq: address):
```

#### Access

Current governance only.

#### Validation
- New HQ must be valid contract
- No pending governance changes in either HQ
- Both tokens must be set in new HQ

**Events Emitted**: `HqChangeInitiated`

### `confirmHqChange`

Completes HQ migration after timelock.

```vyper
@external
def confirmHqChange() -> bool:
```

Re-validates and updates RipeHq pointer.

**Events Emitted**: `HqChangeConfirmed`

### `setHqChangeTimeLock`

Adjusts timelock for future HQ changes.

```vyper
@external
def setHqChangeTimeLock(_newTimeLock: uint256) -> bool:
```

Must be within MIN/MAX bounds.

**Events Emitted**: `HqChangeTimeLockModified`

## Pause Function

### `pause`

Pauses or unpauses all token operations.

```vyper
@external
def pause(_shouldPause: bool):
```

#### Access

Protocol governance only.

#### Effects When Paused
- No transfers
- No approvals
- No minting
- No burning

**Events Emitted**: `TokenPauseModified`

## Initial Setup Function

### `finishTokenSetup`

Completes token setup when deployed with temporary governance.

```vyper
@external
def finishTokenSetup(_newHq: address, _timeLock: uint256 = 0) -> bool:
```

#### Access

Temporary governance only.

#### Process
1. Validates new RipeHq
2. Sets RipeHq pointer
3. Configures timelock
4. Clears temporary governance

**Events Emitted**: `InitialRipeHqSet`

## View Functions

### Token Info
- `name() -> String[64]` - Token name
- `symbol() -> String[32]` - Token symbol
- `decimals() -> uint8` - Decimal places

### Domain Separator
- `DOMAIN_SEPARATOR() -> bytes32` - EIP-712 domain

### Validation
- `isValidNewRipeHq(_newHq: address) -> bool`
- `isValidHqChangeTimeLock(_newTimeLock: uint256) -> bool`
- `hasPendingHqChange() -> bool`

### Timelock Bounds
- `minHqTimeLock() -> uint256`
- `maxHqTimeLock() -> uint256`


## Security Considerations

### Transfer Security
- **Blacklist Checks**: All paths check blacklist
- **Pause Protection**: Transfers blocked when paused
- **Zero Checks**: Prevents zero amount transfers
- **Self Transfer**: Prevents token contract as recipient

### Signature Security
- **Replay Protection**: Nonces prevent replay
- **Deadline Validation**: Signatures expire
- **Malleability**: S value validation
- **Chain ID**: Prevents cross-chain replay

### Governance Security
- **Time Locks**: All HQ changes delayed
- **Re-validation**: Checks repeated on confirm
- **Permission Model**: RipeHq validates all permissions

## Common Integration Patterns

### Basic Token Operations
```python
# Transfer tokens
token.transfer(recipient.address, amount, sender=owner)

# Approve and transferFrom
token.approve(spender.address, amount, sender=owner)
token.transferFrom(owner.address, recipient.address, amount, sender=spender)
```

### Gasless Approvals
```python
# Create permit signature off-chain
sig = create_permit_signature(owner_key, token, spender, amount, deadline)

# Anyone can submit the permit
token.permit(owner.address, spender.address, amount, deadline, sig)
```

### Blacklist Management
```python
# Add to blacklist
token.setBlacklist(bad_actor.address, True, sender=authorized)

# Burn blacklisted tokens
token.burnBlacklistTokens(bad_actor.address, sender=governance)
```

## Testing

For comprehensive test examples, see: [`tests/tokens/modules/test_erc20_token.py`](../../tests/tokens/modules/test_erc20_token.py)