# Erc20Token Technical Documentation

## Overview

Erc20Token serves as the foundational token module for the Ripe Protocol ecosystem, providing a feature-rich ERC20 implementation with additional security and governance capabilities. Think of it as an enhanced version of the standard ERC20 token that includes built-in blacklisting, pausability, and a sophisticated governance connection through [RipeHq](../../registries/RipeHq.md). Unlike basic ERC20 tokens, this module provides enterprise-grade features needed for a DeFi protocol including permit functionality for gasless approvals and time-locked governance changes.

At its core, Erc20Token manages five fundamental responsibilities:

**1. Standard ERC20 Operations**: Implements all standard token functions including transfers, approvals, minting, and burning with additional validation layers for blacklisted addresses and pause states.

**2. Governance Integration**: Connects to RipeHq for permission management, allowing only authorized addresses to perform sensitive operations like minting, blacklisting, and pausing based on protocol-wide governance rules.

**3. Blacklist Management**: Provides address blacklisting capabilities to comply with regulatory requirements or respond to security incidents, with special functions to burn tokens from blacklisted addresses.

**4. Permit Functionality**: Implements EIP-2612 permit system allowing users to approve token spending through signatures rather than transactions, enabling gasless token approvals and better UX.

**5. RipeHq Migration**: Supports time-locked migration to new RipeHq contracts, ensuring smooth protocol upgrades while preventing rushed changes that could compromise security.

For technical readers, Erc20Token implements the full IERC20 interface with additional features. It uses EIP-712 structured data signing for permits with support for both EOA signatures (via ecrecover) and smart contract signatures (via ERC-1271). The module includes comprehensive blacklist checks in all transfer paths and integrates deeply with RipeHq for permission validation. It supports initial supply distribution during deployment and includes a two-phase setup process for tokens deployed before RipeHq. The contract implements reentrancy protection where needed and includes extensive validation to prevent common attack vectors. All state changes emit detailed events for transparency and off-chain tracking.

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

#### `transferFrom`
```vyper
@external
def transferFrom(_sender: address, _recipient: address, _amount: uint256) -> bool:
```

Transfer on behalf of another address using allowance.

### Allowance Functions

#### `approve`
```vyper
@external
def approve(_spender: address, _amount: uint256) -> bool:
```

Set spending allowance with validation.

#### `increaseAllowance`
```vyper
@external
def increaseAllowance(_spender: address, _amount: uint256) -> bool:
```

Safely increase allowance (prevents race conditions).

#### `decreaseAllowance`
```vyper
@external
def decreaseAllowance(_spender: address, _amount: uint256) -> bool:
```

Safely decrease allowance (prevents underflow).

### Minting and Burning

#### `mint` (Internal)
```vyper
@internal
def _mint(_recipient: address, _amount: uint256) -> bool:
```

Mints new tokens. Must be called by inheriting contract with proper permissions.

#### `burn`
```vyper
@external
def burn(_amount: uint256) -> bool:
```

Burns tokens from caller's balance.

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

### `burnBlacklistTokens`

Burns tokens from blacklisted addresses.

```vyper
@external
def burnBlacklistTokens(_addr: address, _amount: uint256 = max_value(uint256)) -> bool:
```

#### Access

Only protocol governance.

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

### `confirmHqChange`

Completes HQ migration after timelock.

```vyper
@external
def confirmHqChange() -> bool:
```

Re-validates and updates RipeHq pointer.

### `setHqChangeTimeLock`

Adjusts timelock for future HQ changes.

```vyper
@external
def setHqChangeTimeLock(_newTimeLock: uint256) -> bool:
```

Must be within MIN/MAX bounds.

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

## Events

### Token Events
- `Transfer` - Token transfers
- `Approval` - Allowance changes

### Blacklist Events
- `BlacklistModified` - Address blacklist status changed

### Governance Events
- `HqChangeInitiated` - HQ migration started
- `HqChangeConfirmed` - HQ migration completed
- `HqChangeCancelled` - HQ migration cancelled
- `TokenPauseModified` - Pause state changed
- `InitialRipeHqSet` - Initial setup completed
- `HqChangeTimeLockModified` - Timelock adjusted

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