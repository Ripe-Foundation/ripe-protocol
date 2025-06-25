import pytest
import boa

from constants import ZERO_ADDRESS
from conf_utils import filter_logs


###############
# Test Fixtures
###############


@pytest.fixture(scope="function")
def training_wheels_empty(ripe_hq):
    """Training wheels contract with no initial users"""
    return boa.load("contracts/config/TrainingWheels.vy", ripe_hq.address, [])


@pytest.fixture(scope="function")
def training_wheels_with_initial(ripe_hq, alice, bob):
    """Training wheels contract with initial allowed users"""
    initial_list = [alice, bob]
    return boa.load("contracts/config/TrainingWheels.vy", ripe_hq.address, initial_list)


###############
# Initialization Tests
###############


def test_training_wheels_init_empty(training_wheels_empty, alice, bob):
    """Test initialization with empty initial list"""
    # No users should be allowed initially
    assert not training_wheels_empty.allowed(alice)
    assert not training_wheels_empty.allowed(bob)
    assert not training_wheels_empty.isUserAllowed(alice, ZERO_ADDRESS)
    assert not training_wheels_empty.isUserAllowed(bob, ZERO_ADDRESS)


def test_training_wheels_init_with_users(training_wheels_with_initial, alice, bob, sally):
    """Test initialization with initial allowed users"""
    # Alice and Bob should be allowed (from initial list)
    assert training_wheels_with_initial.allowed(alice)
    assert training_wheels_with_initial.allowed(bob)
    assert training_wheels_with_initial.isUserAllowed(alice, ZERO_ADDRESS)
    assert training_wheels_with_initial.isUserAllowed(bob, ZERO_ADDRESS)
    
    # Sally should not be allowed (not in initial list)
    assert not training_wheels_with_initial.allowed(sally)
    assert not training_wheels_with_initial.isUserAllowed(sally, ZERO_ADDRESS)


def test_training_wheels_init_events(ripe_hq, alice, bob):
    """Test that initialization emits proper events"""
    initial_list = [alice, bob]
    tw = boa.load("contracts/config/TrainingWheels.vy", ripe_hq.address, initial_list)
    
    # Verify events were emitted for initial users (must call filter_logs right after deployment)
    logs = filter_logs(tw, "TrainingWheelsModified")
    assert len(logs) == 2
    
    # Check first event (alice)
    assert logs[0].user == alice
    assert logs[0].shouldAllow == True
    
    # Check second event (bob)
    assert logs[1].user == bob
    assert logs[1].shouldAllow == True


def test_training_wheels_init_max_users(ripe_hq):
    """Test initialization at maximum user limit"""
    # Create 20 dummy addresses (MAX_INITIAL = 20)
    initial_list = [f"0x{i:040x}" for i in range(1, 21)]
    tw = boa.load("contracts/config/TrainingWheels.vy", ripe_hq.address, initial_list)
    
    # Must call filter_logs immediately after deployment to capture init events
    logs = filter_logs(tw, "TrainingWheelsModified")
    
    # All users should be allowed
    for addr in initial_list:
        assert tw.allowed(addr)
        assert tw.isUserAllowed(addr, ZERO_ADDRESS)
    
    # Should have emitted 20 events
    assert len(logs) == 20


def test_training_wheels_init_over_max_limit(ripe_hq):
    """Test that initialization fails when exceeding MAX_INITIAL limit"""
    # Try to create 21 users (exceeding MAX_INITIAL = 20)
    initial_list = [f"0x{i:040x}" for i in range(1, 22)]
    
    with boa.reverts():  # Should fail due to Vyper array size validation
        boa.load("contracts/config/TrainingWheels.vy", ripe_hq.address, initial_list)


###############
# Access Control Tests
###############


def test_training_wheels_set_allowed_access_control(
    training_wheels_empty,
    alice,
    bob,
    switchboard_charlie,
):
    """Test access control for setAllowed function"""
    # Non-switchboard users should be rejected
    with boa.reverts("no perms"):
        training_wheels_empty.setAllowed(alice, True, sender=bob)
    
    with boa.reverts("no perms"):
        training_wheels_empty.setAllowed(alice, True, sender=alice)
    
    # Switchboard should be allowed
    training_wheels_empty.setAllowed(alice, True, sender=switchboard_charlie.address)
    assert training_wheels_empty.allowed(alice)


def test_training_wheels_set_allowed_parameter_validation(
    training_wheels_empty,
    switchboard_charlie,
):
    """Test parameter validation for setAllowed"""
    # Test invalid user address (zero address)
    with boa.reverts("invalid user"):
        training_wheels_empty.setAllowed(ZERO_ADDRESS, True, sender=switchboard_charlie.address)
    
    # Valid address should work
    valid_addr = "0x1234567890123456789012345678901234567890"
    training_wheels_empty.setAllowed(valid_addr, True, sender=switchboard_charlie.address)
    assert training_wheels_empty.allowed(valid_addr)


###############
# Core Functionality Tests
###############


def test_training_wheels_set_allowed_functionality(
    training_wheels_empty,
    alice,
    bob,
    switchboard_charlie,
):
    """Test core setAllowed functionality"""
    # Initially no users allowed
    assert not training_wheels_empty.allowed(alice)
    assert not training_wheels_empty.allowed(bob)
    
    # Allow alice
    training_wheels_empty.setAllowed(alice, True, sender=switchboard_charlie.address)
    assert training_wheels_empty.allowed(alice)
    assert not training_wheels_empty.allowed(bob)  # Bob still not allowed
    
    # Allow bob
    training_wheels_empty.setAllowed(bob, True, sender=switchboard_charlie.address)
    assert training_wheels_empty.allowed(alice)
    assert training_wheels_empty.allowed(bob)
    
    # Disallow alice
    training_wheels_empty.setAllowed(alice, False, sender=switchboard_charlie.address)
    assert not training_wheels_empty.allowed(alice)
    assert training_wheels_empty.allowed(bob)  # Bob still allowed
    
    # Disallow bob
    training_wheels_empty.setAllowed(bob, False, sender=switchboard_charlie.address)
    assert not training_wheels_empty.allowed(alice)
    assert not training_wheels_empty.allowed(bob)


def test_training_wheels_is_user_allowed_functionality(
    training_wheels_empty,
    alice,
    bob,
    switchboard_charlie,
    alpha_token,
    bravo_token,
):
    """Test isUserAllowed functionality"""
    # Initially no users allowed
    assert not training_wheels_empty.isUserAllowed(alice, alpha_token.address)
    assert not training_wheels_empty.isUserAllowed(alice, bravo_token.address)
    assert not training_wheels_empty.isUserAllowed(alice, ZERO_ADDRESS)
    
    # Allow alice
    training_wheels_empty.setAllowed(alice, True, sender=switchboard_charlie.address)
    
    # Alice should be allowed for any asset (asset parameter is ignored)
    assert training_wheels_empty.isUserAllowed(alice, alpha_token.address)
    assert training_wheels_empty.isUserAllowed(alice, bravo_token.address)
    assert training_wheels_empty.isUserAllowed(alice, ZERO_ADDRESS)
    assert training_wheels_empty.isUserAllowed(alice, "0x1234567890123456789012345678901234567890")
    
    # Bob should still not be allowed for any asset
    assert not training_wheels_empty.isUserAllowed(bob, alpha_token.address)
    assert not training_wheels_empty.isUserAllowed(bob, bravo_token.address)
    assert not training_wheels_empty.isUserAllowed(bob, ZERO_ADDRESS)


def test_training_wheels_asset_parameter_ignored(
    training_wheels_with_initial,
    alice,
    alpha_token,
    bravo_token,
):
    """Test that asset parameter is completely ignored in isUserAllowed"""
    # Alice is allowed from initialization
    assert training_wheels_with_initial.allowed(alice)
    
    # Should return same result regardless of asset parameter
    assert training_wheels_with_initial.isUserAllowed(alice, alpha_token.address) == True
    assert training_wheels_with_initial.isUserAllowed(alice, bravo_token.address) == True
    assert training_wheels_with_initial.isUserAllowed(alice, ZERO_ADDRESS) == True
    assert training_wheels_with_initial.isUserAllowed(alice, "0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef") == True
    
    # Test with non-allowed user
    not_allowed_user = "0x1234567890123456789012345678901234567890"
    assert training_wheels_with_initial.isUserAllowed(not_allowed_user, alpha_token.address) == False
    assert training_wheels_with_initial.isUserAllowed(not_allowed_user, bravo_token.address) == False
    assert training_wheels_with_initial.isUserAllowed(not_allowed_user, ZERO_ADDRESS) == False


###############
# Event Emission Tests
###############


def test_training_wheels_set_allowed_events(
    training_wheels_empty,
    alice,
    bob,
    switchboard_charlie,
):
    """Test event emission for setAllowed calls"""
    # Allow alice
    training_wheels_empty.setAllowed(alice, True, sender=switchboard_charlie.address)
    
    logs = filter_logs(training_wheels_empty, "TrainingWheelsModified")
    assert len(logs) == 1
    assert logs[0].user == alice
    assert logs[0].shouldAllow == True
    
    # Allow bob
    training_wheels_empty.setAllowed(bob, True, sender=switchboard_charlie.address)
    
    logs = filter_logs(training_wheels_empty, "TrainingWheelsModified")
    assert len(logs) == 1  # Only the most recent event
    assert logs[0].user == bob
    assert logs[0].shouldAllow == True
    
    # Disallow alice
    training_wheels_empty.setAllowed(alice, False, sender=switchboard_charlie.address)
    
    logs = filter_logs(training_wheels_empty, "TrainingWheelsModified")
    assert len(logs) == 1
    assert logs[0].user == alice
    assert logs[0].shouldAllow == False


def test_training_wheels_multiple_operations_events(
    training_wheels_empty,
    alice,
    switchboard_charlie,
):
    """Test that multiple operations on same user emit events correctly"""
    # Allow alice
    training_wheels_empty.setAllowed(alice, True, sender=switchboard_charlie.address)
    logs1 = filter_logs(training_wheels_empty, "TrainingWheelsModified")
    assert len(logs1) == 1
    assert logs1[0].shouldAllow == True
    
    # Allow alice again (redundant operation)
    training_wheels_empty.setAllowed(alice, True, sender=switchboard_charlie.address)
    logs2 = filter_logs(training_wheels_empty, "TrainingWheelsModified")
    assert len(logs2) == 1
    assert logs2[0].shouldAllow == True
    
    # Disallow alice
    training_wheels_empty.setAllowed(alice, False, sender=switchboard_charlie.address)
    logs3 = filter_logs(training_wheels_empty, "TrainingWheelsModified")
    assert len(logs3) == 1
    assert logs3[0].shouldAllow == False
    
    # Disallow alice again (redundant operation)
    training_wheels_empty.setAllowed(alice, False, sender=switchboard_charlie.address)
    logs4 = filter_logs(training_wheels_empty, "TrainingWheelsModified")
    assert len(logs4) == 1
    assert logs4[0].shouldAllow == False


###############
# State Consistency Tests
###############


def test_training_wheels_state_consistency(
    training_wheels_empty,
    alice,
    bob,
    sally,
    switchboard_charlie,
    alpha_token,
):
    """Test state consistency across multiple operations"""
    users = [alice, bob, sally]
    
    # Initially all users should be disallowed
    for user in users:
        assert not training_wheels_empty.allowed(user)
        assert not training_wheels_empty.isUserAllowed(user, alpha_token.address)
    
    # Allow all users
    for user in users:
        training_wheels_empty.setAllowed(user, True, sender=switchboard_charlie.address)
    
    # Verify all users are allowed
    for user in users:
        assert training_wheels_empty.allowed(user)
        assert training_wheels_empty.isUserAllowed(user, alpha_token.address)
    
    # Disallow middle user (bob)
    training_wheels_empty.setAllowed(bob, False, sender=switchboard_charlie.address)
    
    # Verify state is correct
    assert training_wheels_empty.allowed(alice)
    assert not training_wheels_empty.allowed(bob)
    assert training_wheels_empty.allowed(sally)
    
    # Verify isUserAllowed reflects the same state
    assert training_wheels_empty.isUserAllowed(alice, alpha_token.address)
    assert not training_wheels_empty.isUserAllowed(bob, alpha_token.address)
    assert training_wheels_empty.isUserAllowed(sally, alpha_token.address)


def test_training_wheels_overwrite_initial_state(
    training_wheels_with_initial,
    alice,
    bob,
    switchboard_charlie,
):
    """Test that setAllowed can modify users that were initially allowed"""
    # Alice and Bob are initially allowed
    assert training_wheels_with_initial.allowed(alice)
    assert training_wheels_with_initial.allowed(bob)
    
    # Disallow alice (overwriting initial state)
    training_wheels_with_initial.setAllowed(alice, False, sender=switchboard_charlie.address)
    assert not training_wheels_with_initial.allowed(alice)
    assert training_wheels_with_initial.allowed(bob)  # Bob unchanged
    
    # Re-allow alice
    training_wheels_with_initial.setAllowed(alice, True, sender=switchboard_charlie.address)
    assert training_wheels_with_initial.allowed(alice)
    assert training_wheels_with_initial.allowed(bob)  # Bob still unchanged


###############
# Edge Cases and Integration Tests
###############


def test_training_wheels_init_with_zero_addresses(ripe_hq, alice, bob):
    """Test that zero addresses are skipped during initialization"""
    # Include zero addresses in initial list - they should be skipped
    initial_list = [alice, ZERO_ADDRESS, bob, ZERO_ADDRESS]
    tw = boa.load("contracts/config/TrainingWheels.vy", ripe_hq.address, initial_list)
    
    # Must call filter_logs immediately after deployment to capture init events
    logs = filter_logs(tw, "TrainingWheelsModified")
    
    # Only alice and bob should be allowed (zero addresses skipped)
    assert tw.allowed(alice)
    assert tw.allowed(bob)
    assert not tw.allowed(ZERO_ADDRESS)
    
    # Verify events were only emitted for valid addresses
    assert len(logs) == 2  # Only alice and bob, zero addresses skipped
    
    # Check events
    assert logs[0].user == alice
    assert logs[0].shouldAllow == True
    assert logs[1].user == bob
    assert logs[1].shouldAllow == True


def test_training_wheels_init_only_zero_addresses(ripe_hq):
    """Test initialization with only zero addresses in the list"""
    # List with only zero addresses - all should be skipped
    initial_list = [ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS]
    tw = boa.load("contracts/config/TrainingWheels.vy", ripe_hq.address, initial_list)
    
    # Must call filter_logs immediately after deployment to capture init events
    logs = filter_logs(tw, "TrainingWheelsModified")
    
    # No users should be allowed
    assert not tw.allowed(ZERO_ADDRESS)
    
    # No events should be emitted since all addresses were skipped
    assert len(logs) == 0


def test_training_wheels_zero_address_queries(training_wheels_empty, switchboard_charlie):
    """Test behavior with zero address queries"""
    # Zero address should not be allowed initially
    assert not training_wheels_empty.allowed(ZERO_ADDRESS)
    assert not training_wheels_empty.isUserAllowed(ZERO_ADDRESS, ZERO_ADDRESS)
    
    # Cannot set zero address as allowed (should revert in setAllowed)
    with boa.reverts("invalid user"):
        training_wheels_empty.setAllowed(ZERO_ADDRESS, True, sender=switchboard_charlie.address)


def test_training_wheels_same_user_multiple_assets(
    training_wheels_empty,
    alice,
    switchboard_charlie,
    alpha_token,
    bravo_token,
):
    """Test that same user works consistently across different assets"""
    # Allow alice
    training_wheels_empty.setAllowed(alice, True, sender=switchboard_charlie.address)
    
    # Alice should be allowed for all assets
    test_assets = [
        alpha_token.address,
        bravo_token.address,
        ZERO_ADDRESS,
        "0x1111111111111111111111111111111111111111",
        "0x2222222222222222222222222222222222222222"
    ]
    
    for asset in test_assets:
        assert training_wheels_empty.isUserAllowed(alice, asset)
    
    # Disallow alice
    training_wheels_empty.setAllowed(alice, False, sender=switchboard_charlie.address)
    
    # Alice should be disallowed for all assets
    for asset in test_assets:
        assert not training_wheels_empty.isUserAllowed(alice, asset)


def test_training_wheels_department_interface_compliance(training_wheels_empty):
    """Test that contract properly implements Department interface"""
    # The contract should be deployed and accessible
    assert training_wheels_empty.address != ZERO_ADDRESS
    
    # Should have the expected public functions
    assert hasattr(training_wheels_empty, 'isUserAllowed')
    assert hasattr(training_wheels_empty, 'setAllowed')
    assert hasattr(training_wheels_empty, 'allowed')


def test_training_wheels_comprehensive_workflow(
    ripe_hq,
    alice,
    bob,
    sally,
    switchboard_charlie,
    alpha_token,
):
    """Test a comprehensive workflow combining initialization and runtime operations"""
    # Start with alice and bob in initial list
    initial_list = [alice, bob]
    tw = boa.load("contracts/config/TrainingWheels.vy", ripe_hq.address, initial_list)
    
    # Verify initial state
    assert tw.allowed(alice) and tw.isUserAllowed(alice, alpha_token.address)
    assert tw.allowed(bob) and tw.isUserAllowed(bob, alpha_token.address)
    assert not tw.allowed(sally) and not tw.isUserAllowed(sally, alpha_token.address)
    
    # Add sally
    tw.setAllowed(sally, True, sender=switchboard_charlie.address)
    assert tw.allowed(sally) and tw.isUserAllowed(sally, alpha_token.address)
    
    # Remove bob
    tw.setAllowed(bob, False, sender=switchboard_charlie.address)
    
    # Get the event from the most recent transaction (bob removal)
    logs = filter_logs(tw, "TrainingWheelsModified")
    
    assert not tw.allowed(bob) and not tw.isUserAllowed(bob, alpha_token.address)
    
    # Final state: alice and sally allowed, bob not allowed
    assert tw.allowed(alice) and tw.isUserAllowed(alice, alpha_token.address)
    assert not tw.allowed(bob) and not tw.isUserAllowed(bob, alpha_token.address)
    assert tw.allowed(sally) and tw.isUserAllowed(sally, alpha_token.address)
    
    # Verify the most recent event (bob removal)
    assert len(logs) == 1  # Only the most recent event (bob removal)
    assert logs[0].user == bob
    assert logs[0].shouldAllow == False


# Run the tests
if __name__ == "__main__":
    print("Comprehensive tests for TrainingWheels.vy")
    print("These tests cover:")
    print("- Initialization with and without initial users")
    print("- Initialization with zero addresses (skipped properly)")
    print("- Access control for setAllowed function")
    print("- Core functionality of allowed/disallowed users")
    print("- Asset parameter being ignored in isUserAllowed")
    print("- Event emission for all operations")
    print("- State consistency across multiple operations")
    print("- Edge cases and comprehensive workflows")
