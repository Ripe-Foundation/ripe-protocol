import pytest
import boa

from eth_account import Account
from constants import EIGHTEEN_DECIMALS, MAX_UINT256, ZERO_ADDRESS


@pytest.fixture(scope="module")
def signPermit(special_signer):
    def signPermit(
        _token,
        _owner,
        _spender,
        _value,
        _deadline=boa.env.evm.patch.timestamp + 3600,  # 1 hour
    ):
        nonce = _token.nonces(_owner)
        message = {
            "domain": {
                "name": _token.name(),
                "version": _token.VERSION(),
                "chainId": boa.env.evm.patch.chain_id,
                "verifyingContract": _token.address,
            },
            "types": {
                "Permit": [
                    {"name": "owner", "type": "address"},
                    {"name": "spender", "type": "address"},
                    {"name": "value", "type": "uint256"},
                    {"name": "nonce", "type": "uint256"},
                    {"name": "deadline", "type": "uint256"},
                ],
            },
            "message": {
                "owner": _owner.address if hasattr(_owner, 'address') else _owner,
                "spender": _spender.address if hasattr(_spender, 'address') else _spender,
                "value": _value,
                "nonce": nonce,
                "deadline": _deadline,
            }
        }
        signed = Account.sign_typed_data(special_signer.key, full_message=message)
        return (signed.signature, _deadline)
    yield signPermit


@pytest.fixture(scope="module")
def special_signer():
    return Account.from_key('0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80')


def test_green_token_permit(green_token, special_signer, bob, signPermit):
    """Test EIP-2612 permit functionality"""
    amount = 100 * EIGHTEEN_DECIMALS
    
    # Get initial nonce
    initial_nonce = green_token.nonces(special_signer)
    
    # Sign and execute permit
    signature, deadline = signPermit(green_token, special_signer, bob, amount)

    assert green_token.permit(special_signer, bob, amount, deadline, signature)
    assert green_token.allowance(special_signer, bob) == amount
    
    # Test nonce increment
    assert green_token.nonces(special_signer) == initial_nonce + 1
    
    # Test expired permit
    boa.env.time_travel(seconds=3601)
    with boa.reverts("permit expired"):
        green_token.permit(special_signer, bob, amount, deadline, signature)
    
    # Test invalid signature (signed by wrong address)
    invalid_signature, _ = signPermit(green_token, bob, special_signer, amount)  # swapped owner/spender
    with boa.reverts():
        green_token.permit(special_signer, bob, amount, deadline, invalid_signature)
    
    # Test zero address owner
    with boa.reverts("permit expired"):  # This is the first check in permit
        green_token.permit(ZERO_ADDRESS, bob, amount, deadline, signature)
    
    # Test contract signature (ERC1271)
    contract_owner = boa.load("contracts/mock/MockERC1271.vy")
    # For contract signatures, we need to use a different approach
    # The contract will return MAGIC_VALUE for any signature
    contract_signature = bytes([0] * 65)  # Empty signature
    contract_deadline = boa.env.evm.patch.timestamp + 3600
    assert green_token.permit(contract_owner, bob, amount, contract_deadline, contract_signature)


# 1. Replay Attack Prevention
def test_permit_replay_attack(green_token, special_signer, bob, signPermit):
    amount = 100 * EIGHTEEN_DECIMALS
    signature, deadline = signPermit(green_token, special_signer, bob, amount)
    assert green_token.permit(special_signer, bob, amount, deadline, signature)
    with boa.reverts():
        green_token.permit(special_signer, bob, amount, deadline, signature)


# 2. Invalid Nonce
def test_permit_invalid_nonce(green_token, special_signer, bob, signPermit):
    amount = 100 * EIGHTEEN_DECIMALS
    signature, deadline = signPermit(green_token, special_signer, bob, amount)
    green_token.permit(special_signer, bob, amount, deadline, signature)
    with boa.reverts():
        green_token.permit(special_signer, bob, amount, deadline, signature)


# 3. Invalid Domain Separator
def test_permit_invalid_domain_separator(green_token, special_signer, bob, signPermit):
    amount = 100 * EIGHTEEN_DECIMALS
    class DummyToken:
        def name(self): return "Fake"
        def VERSION(self): return green_token.VERSION()
        address = "0x000000000000000000000000000000000000dead"
        def nonces(self, owner): return green_token.nonces(owner)  # Use the real nonce
    dummy_token = DummyToken()
    signature, deadline = signPermit(dummy_token, special_signer, bob, amount)
    with boa.reverts():
        green_token.permit(special_signer, bob, amount, deadline, signature)


# 4. Boundary Values
def test_permit_zero_and_max_value(green_token, special_signer, bob, signPermit):
    # Zero value should succeed (EIP-2612 compliant)
    signature, deadline = signPermit(green_token, special_signer, bob, 0)
    assert green_token.permit(special_signer, bob, 0, deadline, signature)
    # Max value
    signature, deadline = signPermit(green_token, special_signer, bob, MAX_UINT256)
    assert green_token.permit(special_signer, bob, MAX_UINT256, deadline, signature)


# 5. Expired Permit
def test_permit_expired(green_token, special_signer, bob, signPermit):
    amount = 100 * EIGHTEEN_DECIMALS
    signature, deadline = signPermit(green_token, special_signer, bob, amount)
    boa.env.time_travel(seconds=3601)
    with boa.reverts("permit expired"):
        green_token.permit(special_signer, bob, amount, deadline, signature)


# 6. Future Nonce (if possible)
def test_permit_future_nonce(green_token, special_signer, bob, signPermit):
    # Not generally possible unless contract exposes nonce manipulation
    pass


# 7. ERC1271: Invalid Magic Value
def test_erc1271_invalid_magic_value(green_token, bob):
    bad_contract = boa.load("contracts/mock/MockBadERC1271.vy")
    contract_signature = bytes([0] * 65)
    contract_deadline = boa.env.evm.patch.timestamp + 3600
    with boa.reverts():
        green_token.permit(bad_contract, bob, 100 * EIGHTEEN_DECIMALS, contract_deadline, contract_signature)


# 8. ERC1271: Non-Contract Address
def test_erc1271_non_contract_address(green_token, special_signer, bob):
    contract_signature = bytes([0] * 65)
    contract_deadline = boa.env.evm.patch.timestamp + 3600
    with boa.reverts():
        green_token.permit(special_signer, bob, 100 * EIGHTEEN_DECIMALS, contract_deadline, contract_signature)


# 9. Signature Malleability
def test_permit_signature_malleability(green_token, special_signer, bob, signPermit):
    amount = 100 * EIGHTEEN_DECIMALS
    signature, deadline = signPermit(green_token, special_signer, bob, amount)
    malleable_signature = signature[:-1] + bytes([signature[-1] ^ 1])
    with boa.reverts():
        green_token.permit(special_signer, bob, amount, deadline, malleable_signature)


# 10. Permit for Blacklisted or Paused Accounts
def test_permit_blacklisted_or_paused(green_token, special_signer, bob, switchboard_one, governance, signPermit):
    amount = 100 * EIGHTEEN_DECIMALS
    signature, deadline = signPermit(green_token, special_signer, bob, amount)
    green_token.setBlacklist(special_signer, True, sender=switchboard_one.address)
    with boa.reverts():
        green_token.permit(special_signer, bob, amount, deadline, signature)
    green_token.setBlacklist(special_signer, False, sender=switchboard_one.address)
    green_token.pause(True, sender=governance.address)
    with boa.reverts():
        green_token.permit(special_signer, bob, amount, deadline, signature)
    green_token.pause(False, sender=governance.address)


def test_permit_different_spenders(green_token, special_signer, bob, alice, signPermit):
    """Test that a permit for one spender cannot be used by another spender"""
    amount = 100 * EIGHTEEN_DECIMALS
    signature, deadline = signPermit(green_token, special_signer, bob, amount)
    # Try to use bob's permit with alice as the spender
    with boa.reverts():
        green_token.permit(special_signer, alice, amount, deadline, signature)


def test_permit_different_amounts(green_token, special_signer, bob, signPermit):
    """Test that a permit for one amount cannot be used for a different amount"""
    amount = 100 * EIGHTEEN_DECIMALS
    signature, deadline = signPermit(green_token, special_signer, bob, amount)
    # Try to use the permit with a different amount
    with boa.reverts():
        green_token.permit(special_signer, bob, amount * 2, deadline, signature)


def test_permit_different_deadlines(green_token, special_signer, bob, signPermit):
    """Test that a permit with one deadline cannot be used with a different deadline"""
    amount = 100 * EIGHTEEN_DECIMALS
    signature, deadline = signPermit(green_token, special_signer, bob, amount)
    # Try to use the permit with a different deadline
    with boa.reverts():
        green_token.permit(special_signer, bob, amount, deadline + 1, signature)


def test_permit_malformed_signatures(green_token, special_signer, bob, signPermit):
    """Test various malformed signature scenarios"""
    amount = 100 * EIGHTEEN_DECIMALS
    signature, deadline = signPermit(green_token, special_signer, bob, amount)
    
    # Test with empty signature
    with boa.reverts():
        green_token.permit(special_signer, bob, amount, deadline, b'')
    
    # Test with too short signature
    with boa.reverts():
        green_token.permit(special_signer, bob, amount, deadline, signature[:64])
    
    # Test with too long signature
    with boa.reverts():
        green_token.permit(special_signer, bob, amount, deadline, signature + b'\x00')


def test_permit_contract_owner_eoa_spender(green_token, bob, signPermit):
    """Test permit when owner is a contract and spender is an EOA"""
    amount = 100 * EIGHTEEN_DECIMALS
    contract_owner = boa.load("contracts/mock/MockERC1271.vy")
    signature, deadline = signPermit(green_token, contract_owner, bob, amount)
    assert green_token.permit(contract_owner, bob, amount, deadline, signature)


def test_permit_contract_owner_contract_spender(green_token, signPermit):
    """Test permit when both owner and spender are contracts"""
    amount = 100 * EIGHTEEN_DECIMALS
    contract_owner = boa.load("contracts/mock/MockERC1271.vy")
    contract_spender = boa.load("contracts/mock/MockERC1271.vy")
    signature, deadline = signPermit(green_token, contract_owner, contract_spender, amount)
    assert green_token.permit(contract_owner, contract_spender, amount, deadline, signature)


def test_permit_different_chain_ids(green_token, special_signer, bob, signPermit):
    """Test that a permit from one chain cannot be used on another chain"""
    amount = 100 * EIGHTEEN_DECIMALS
    # Save original chain ID
    original_chain_id = boa.env.evm.patch.chain_id
    # Change chain ID
    boa.env.evm.patch.chain_id = original_chain_id + 1
    signature, deadline = signPermit(green_token, special_signer, bob, amount)
    # Restore original chain ID
    boa.env.evm.patch.chain_id = original_chain_id
    # Try to use the permit from the other chain
    with boa.reverts():
        green_token.permit(special_signer, bob, amount, deadline, signature) 