import pytest
import boa

from config.BluePrint import PARAMS
from constants import MAX_UINT256, ZERO_ADDRESS
from conf_utils import filter_logs


@pytest.fixture(scope="module")
def createMockTimeLock(ripe_hq_deploy, fork):
    def createMockTimeLock(
        _ripeHq = ripe_hq_deploy,
        _minTimeLock = PARAMS[fork]["RIPE_HQ_MIN_GOV_TIMELOCK"],
        _maxTimeLock = PARAMS[fork]["RIPE_HQ_MAX_GOV_TIMELOCK"],
        _initialTimeLock = PARAMS[fork]["RIPE_HQ_MIN_GOV_TIMELOCK"],
        _expiration = PARAMS[fork]["RIPE_HQ_MIN_GOV_TIMELOCK"] * 2,  # Default to 2x time lock
    ):
        return boa.load(
            "contracts/mock/MockWithTimeLock.vy",
            _ripeHq,
            _minTimeLock,
            _maxTimeLock,
            _initialTimeLock,
            _expiration,
        )
    yield createMockTimeLock


def test_time_lock_deploy(createMockTimeLock):
    # Test invalid time lock values
    with boa.reverts("invalid time lock boundaries"):
        mock = createMockTimeLock(
            _minTimeLock = 200,  # min > max
            _maxTimeLock = 100,
        )

    with boa.reverts("invalid time lock boundaries"):
        mock = createMockTimeLock(
            _minTimeLock = 0,
            _maxTimeLock = 200,
        )

    with boa.reverts("invalid time lock boundaries"):
        mock = createMockTimeLock(
            _minTimeLock = 100,
            _maxTimeLock = MAX_UINT256,
        )

    # Test invalid expiration values
    with boa.reverts("invalid expiration"):
        mock = createMockTimeLock(
            _minTimeLock = 100,
            _maxTimeLock = 200,
            _initialTimeLock = 150,
            _expiration = 0,  # Invalid expiration
        )

    with boa.reverts("invalid expiration"):
        mock = createMockTimeLock(
            _minTimeLock = 100,
            _maxTimeLock = 200,
            _initialTimeLock = 150,
            _expiration = MAX_UINT256,  # Invalid expiration
        )

    with boa.reverts("invalid expiration"):
        mock = createMockTimeLock(
            _minTimeLock = 100,
            _maxTimeLock = 200,
            _initialTimeLock = 150,
            _expiration = 50,  # Expiration less than time lock
        )

    # Success case with valid parameters
    mock = createMockTimeLock(
        _minTimeLock = 100,
        _maxTimeLock = 200,
        _initialTimeLock = 150,
        _expiration = 300,
    )

    assert mock.minActionTimeLock() == 100
    assert mock.maxActionTimeLock() == 200
    assert mock.actionTimeLock() == 150
    assert mock.expiration() == 300
    assert mock.actionId() == 1  # starts at 1


def test_time_lock_basic_flow(
    createMockTimeLock,
    governance,
    mock_rando_contract,
):
    mock = createMockTimeLock()
    time_lock = mock.actionTimeLock()

    # Start action
    mock.addThing(mock_rando_contract, 100, sender=governance.address)
    
    # Verify pending state
    pending = mock.pendingData(mock_rando_contract)
    assert pending.actionId == 1
    assert pending.value == 100
    assert mock.hasPendingAction(pending.actionId)
    assert mock.getActionConfirmationBlock(pending.actionId) == boa.env.evm.patch.block_number + time_lock

    # Try to confirm before time lock
    with boa.reverts("time lock not reached"):
        mock.confirmThing(mock_rando_contract, sender=governance.address)

    # Time travel
    boa.env.time_travel(blocks=time_lock)

    # Confirm action
    mock.confirmThing(mock_rando_contract, sender=governance.address)

    # Verify state after confirmation
    assert mock.data(mock_rando_contract) == 100
    assert not mock.hasPendingAction(pending.actionId)
    assert mock.getActionConfirmationBlock(pending.actionId) == 0


def test_time_lock_cancel(
    createMockTimeLock,
    governance,
    mock_rando_contract,
):
    mock = createMockTimeLock()

    # Start action
    mock.addThing(mock_rando_contract, 100, sender=governance.address)
    pending = mock.pendingData(mock_rando_contract)

    # Cancel action
    mock.cancelThing(mock_rando_contract, sender=governance.address)

    # Verify state after cancellation
    assert not mock.hasPendingAction(pending.actionId)
    assert mock.getActionConfirmationBlock(pending.actionId) == 0
    assert mock.data(mock_rando_contract) == 0  # unchanged


def test_time_lock_validation(
    createMockTimeLock,
    governance,
    mock_rando_contract,
    bob,
):
    mock = createMockTimeLock()

    # Test permissions
    with boa.reverts("no perms"):
        mock.addThing(mock_rando_contract, 100, sender=bob)
    with boa.reverts("no perms"):
        mock.confirmThing(mock_rando_contract, sender=bob)
    with boa.reverts("no perms"):
        mock.cancelThing(mock_rando_contract, sender=bob)

    # Start action
    mock.addThing(mock_rando_contract, 100, sender=governance.address)

    # Try to cancel non-existent action
    with boa.reverts("cannot cancel action"):
        mock.cancelThing(ZERO_ADDRESS, sender=governance.address)

    # Try to confirm non-existent action
    with boa.reverts("time lock not reached"):
        mock.confirmThing(ZERO_ADDRESS, sender=governance.address)


def test_time_lock_time_lock_management(
    createMockTimeLock,
    governance,
):
    mock = createMockTimeLock()

    # Test setting time lock
    prev_time_lock = mock.actionTimeLock()
    new_time_lock = prev_time_lock + 10

    # no change
    with boa.reverts("invalid time lock"):
        mock.setActionTimeLock(prev_time_lock, sender=governance.address)

    # success
    assert mock.setActionTimeLock(new_time_lock, sender=governance.address)
    
    # Verify time lock modified event
    time_lock_log = filter_logs(mock, "ActionTimeLockSet")[0]
    assert time_lock_log.prevTimeLock == prev_time_lock
    assert time_lock_log.newTimeLock == new_time_lock
    
    assert mock.actionTimeLock() == new_time_lock

    # Test invalid time locks
    with boa.reverts("invalid time lock"):
        mock.setActionTimeLock(mock.minActionTimeLock() - 1, sender=governance.address)
    with boa.reverts("invalid time lock"):
        mock.setActionTimeLock(mock.maxActionTimeLock() + 1, sender=governance.address)


def test_time_lock_sequential_actions(
    createMockTimeLock,
    governance,
    mock_rando_contract,
    mock_whitelist,
):
    mock = createMockTimeLock()
    time_lock = mock.actionTimeLock()

    # First action
    mock.addThing(mock_rando_contract, 100, sender=governance.address)
    pending1 = mock.pendingData(mock_rando_contract)
    assert pending1.actionId == 1

    # Second action with different address
    mock.addThing(mock_whitelist, 200, sender=governance.address)
    pending2 = mock.pendingData(mock_whitelist)
    assert pending2.actionId == 2

    # Time travel
    boa.env.time_travel(blocks=time_lock)

    # Confirm first action
    mock.confirmThing(mock_rando_contract, sender=governance.address)
    assert mock.data(mock_rando_contract) == 100
    assert mock.data(mock_whitelist) == 0  # second action not confirmed yet

    # Confirm second action
    mock.confirmThing(mock_whitelist, sender=governance.address)
    assert mock.data(mock_rando_contract) == 100  # first action unchanged
    assert mock.data(mock_whitelist) == 200  # second action confirmed


def test_time_lock_setup(
    createMockTimeLock,
    governance,
    bob,
):
    # Create without initial time lock
    mock = createMockTimeLock(_initialTimeLock=0)
    assert mock.actionTimeLock() == 0

    # Try to set again
    with boa.reverts("no perms"):
        mock.setActionTimeLockAfterSetup(sender=bob)

    # Set time lock after setup
    newTimeLock = mock.minActionTimeLock() + 10
    assert mock.setActionTimeLockAfterSetup(newTimeLock, sender=governance.address)
    assert mock.actionTimeLock() == newTimeLock

    # Try to set again
    with boa.reverts("already set"):
        mock.setActionTimeLockAfterSetup(200, sender=governance.address)

    # Create with initial time lock
    new_mock = createMockTimeLock(_initialTimeLock=newTimeLock)
    assert new_mock.actionTimeLock() == newTimeLock

    # Try to set after setup
    with boa.reverts("already set"):
        new_mock.setActionTimeLockAfterSetup(200, sender=governance.address)


def test_time_lock_action_id_increment(
    createMockTimeLock,
    governance,
    mock_rando_contract,
    mock_whitelist,
):
    mock = createMockTimeLock()
    
    # First action
    mock.addThing(mock_rando_contract, 100, sender=governance.address)
    assert mock.actionId() == 2  # increments after first action
    
    # Second action
    mock.addThing(mock_whitelist, 200, sender=governance.address)
    assert mock.actionId() == 3  # increments again
    
    # Cancel first action
    mock.cancelThing(mock_rando_contract, sender=governance.address)
    
    # Third action - should still increment
    mock.addThing(mock_rando_contract, 300, sender=governance.address)
    assert mock.actionId() == 4  # continues incrementing regardless of cancellations


def test_time_lock_pending_action_state(
    createMockTimeLock,
    governance,
    mock_rando_contract,
):
    mock = createMockTimeLock()
    time_lock = mock.actionTimeLock()
    
    # Start action
    mock.addThing(mock_rando_contract, 100, sender=governance.address)
    pending = mock.pendingData(mock_rando_contract)
    
    # Verify pending state
    assert mock.hasPendingAction(pending.actionId)
    assert mock.getActionConfirmationBlock(pending.actionId) == boa.env.evm.patch.block_number + time_lock
    
    # Time travel half way
    boa.env.time_travel(blocks=time_lock // 2)
    
    # Verify state unchanged
    assert mock.hasPendingAction(pending.actionId)
    assert mock.getActionConfirmationBlock(pending.actionId) == boa.env.evm.patch.block_number + (time_lock // 2)
    
    # Time travel past confirmation
    boa.env.time_travel(blocks=time_lock)
    
    # Confirm action
    mock.confirmThing(mock_rando_contract, sender=governance.address)
    
    # Verify state cleared
    assert not mock.hasPendingAction(pending.actionId)
    assert mock.getActionConfirmationBlock(pending.actionId) == 0


def test_time_lock_multiple_pending_actions(
    createMockTimeLock,
    governance,
    mock_rando_contract,
    mock_whitelist,
):
    mock = createMockTimeLock()
    time_lock = mock.actionTimeLock()
    
    # Start multiple actions
    mock.addThing(mock_rando_contract, 100, sender=governance.address)
    mock.addThing(mock_whitelist, 200, sender=governance.address)
    
    # Verify both pending
    pending1 = mock.pendingData(mock_rando_contract)
    pending2 = mock.pendingData(mock_whitelist)
    assert mock.hasPendingAction(pending1.actionId)
    assert mock.hasPendingAction(pending2.actionId)
    
    # Cancel one action
    mock.cancelThing(mock_rando_contract, sender=governance.address)
    assert not mock.hasPendingAction(pending1.actionId)
    assert mock.hasPendingAction(pending2.actionId)
    
    # Time travel
    boa.env.time_travel(blocks=time_lock)
    
    # Confirm remaining action
    mock.confirmThing(mock_whitelist, sender=governance.address)
    assert not mock.hasPendingAction(pending2.actionId)
    assert mock.data(mock_whitelist) == 200


def test_time_lock_invalid_action_handling(
    createMockTimeLock,
    governance,
    mock_rando_contract,
):
    mock = createMockTimeLock()
    
    # Try to confirm non-existent action
    with boa.reverts("time lock not reached"):
        mock.confirmThing(mock_rando_contract, sender=governance.address)
    
    # Try to cancel non-existent action
    with boa.reverts("cannot cancel action"):
        mock.cancelThing(mock_rando_contract, sender=governance.address)
    
    # Start action
    mock.addThing(mock_rando_contract, 100, sender=governance.address)
    mock.pendingData(mock_rando_contract)
    
    # Try to confirm with wrong action ID
    with boa.reverts("time lock not reached"):
        mock.confirmThing(mock_rando_contract, sender=governance.address)
    
    # Cancel action
    mock.cancelThing(mock_rando_contract, sender=governance.address)
    
    # Try to confirm cancelled action
    with boa.reverts("time lock not reached"):
        mock.confirmThing(mock_rando_contract, sender=governance.address)


def test_time_lock_expiration_expired_action(
    createMockTimeLock,
    governance,
    mock_rando_contract,
):
    """Test that expired actions cannot be confirmed"""
    time_lock = 100
    expiration = 150
    mock = createMockTimeLock(
        _minTimeLock = 50,
        _maxTimeLock = 200,
        _initialTimeLock = time_lock,
        _expiration = expiration,
    )

    # Start action
    mock.addThing(mock_rando_contract, 100, sender=governance.address)
    mock.pendingData(mock_rando_contract)

    # Time travel past expiration (time_lock + expiration)
    boa.env.time_travel(blocks=time_lock + expiration + 1)
    
    # Should not be able to confirm expired action
    with boa.reverts("time lock not reached"):
        mock.confirmThing(mock_rando_contract, sender=governance.address)

    # Verify data unchanged
    assert mock.data(mock_rando_contract) == 0


def test_time_lock_expiration_window(
    createMockTimeLock,
    governance,
    mock_rando_contract,
    mock_whitelist,
):
    """Test confirmation window between time lock and expiration"""
    time_lock = 100
    expiration = 150
    mock = createMockTimeLock(
        _minTimeLock = 50,
        _maxTimeLock = 200,
        _initialTimeLock = time_lock,
        _expiration = expiration,
    )

    # Start two actions
    mock.addThing(mock_rando_contract, 100, sender=governance.address)
    mock.addThing(mock_whitelist, 200, sender=governance.address)
    
    mock.pendingData(mock_rando_contract)
    mock.pendingData(mock_whitelist)

    # Time travel to middle of confirmation window
    boa.env.time_travel(blocks=time_lock + (expiration // 2))
    
    # Should be able to confirm first action in window
    mock.confirmThing(mock_rando_contract, sender=governance.address)
    assert mock.data(mock_rando_contract) == 100

    # Time travel past expiration for second action
    boa.env.time_travel(blocks=expiration)
    
    # Second action should be expired
    with boa.reverts("time lock not reached"):
        mock.confirmThing(mock_whitelist, sender=governance.address)


def test_time_lock_expiration_management(
    createMockTimeLock,
    governance,
    bob,
):
    """Test setting and validating expiration values"""
    mock = createMockTimeLock()
    
    # Test permissions
    with boa.reverts("no perms"):
        mock.setExpiration(500, sender=bob)

    # Test invalid expiration values
    with boa.reverts("invalid expiration"):
        mock.setExpiration(0, sender=governance.address)  # zero
    
    with boa.reverts("invalid expiration"):
        mock.setExpiration(MAX_UINT256, sender=governance.address)  # max uint256
    
    current_time_lock = mock.actionTimeLock()
    with boa.reverts("invalid expiration"):
        mock.setExpiration(current_time_lock - 1, sender=governance.address)  # less than time lock

    # Test valid expiration
    new_expiration = current_time_lock + 100
    assert mock.setExpiration(new_expiration, sender=governance.address)
    
    # Verify expiration set event
    expiration_log = filter_logs(mock, "ExpirationSet")[0]
    assert expiration_log.expiration == new_expiration
    
    assert mock.expiration() == new_expiration


def test_time_lock_expiration_edge_cases(
    createMockTimeLock,
    governance,
    mock_rando_contract,
):
    """Test expiration edge cases"""
    time_lock = 100
    expiration = 200
    mock = createMockTimeLock(
        _minTimeLock = 50,
        _maxTimeLock = 300,
        _initialTimeLock = time_lock,
        _expiration = expiration,
    )

    # Start action
    mock.addThing(mock_rando_contract, 100, sender=governance.address)
    
    # Time travel to exact confirmation block
    boa.env.time_travel(blocks=time_lock)
    
    # Should be able to confirm at exact confirmation block
    mock.confirmThing(mock_rando_contract, sender=governance.address)
    assert mock.data(mock_rando_contract) == 100

    # Start another action to test exact expiration
    mock.addThing(mock_rando_contract, 200, sender=governance.address)
    
    # Calculate blocks to reach exact expiration:
    # expiration = start_block + time_lock + expiration = start_block + 100 + 200 = start_block + 300
    # current_block = start_block, so need to travel 300 blocks to reach expiration
    boa.env.time_travel(blocks=time_lock + expiration)
    
    # Should not be able to confirm at exact expiration block
    with boa.reverts("time lock not reached"):
        mock.confirmThing(mock_rando_contract, sender=governance.address)


def test_time_lock_expiration_with_cancellation(
    createMockTimeLock,
    governance,
    mock_rando_contract,
):
    """Test that cancelled actions can't be confirmed even if not expired"""
    time_lock = 100
    expiration = 200
    mock = createMockTimeLock(
        _minTimeLock = 50,
        _maxTimeLock = 300,
        _initialTimeLock = time_lock,
        _expiration = expiration,
    )

    # Start action
    mock.addThing(mock_rando_contract, 100, sender=governance.address)
    mock.pendingData(mock_rando_contract)

    # Time travel to middle of confirmation window
    boa.env.time_travel(blocks=time_lock + 50)
    
    # Cancel action while in confirmation window
    mock.cancelThing(mock_rando_contract, sender=governance.address)
    
    # Should not be able to confirm cancelled action
    with boa.reverts("time lock not reached"):
        mock.confirmThing(mock_rando_contract, sender=governance.address)


def test_time_lock_expiration_multiple_actions_timing(
    createMockTimeLock,
    governance,
    mock_rando_contract,
    mock_whitelist,
):
    """Test multiple actions with different timing and expiration"""
    time_lock = 100
    expiration = 150
    mock = createMockTimeLock(
        _minTimeLock = 50,
        _maxTimeLock = 300,
        _initialTimeLock = time_lock,
        _expiration = expiration,
    )

    # Start first action
    mock.addThing(mock_rando_contract, 100, sender=governance.address)
    
    # Time travel halfway through time lock
    boa.env.time_travel(blocks=time_lock // 2)
    
    # Start second action (will have later confirmation/expiration)
    mock.addThing(mock_whitelist, 200, sender=governance.address)
    
    # Time travel to where first action can be confirmed
    boa.env.time_travel(blocks=time_lock // 2)
    
    # Confirm first action
    mock.confirmThing(mock_rando_contract, sender=governance.address)
    assert mock.data(mock_rando_contract) == 100
    
    # Second action should still be in time lock
    with boa.reverts("time lock not reached"):
        mock.confirmThing(mock_whitelist, sender=governance.address)
    
    # Time travel to where second action can be confirmed
    boa.env.time_travel(blocks=time_lock // 2)
    
    # Confirm second action
    mock.confirmThing(mock_whitelist, sender=governance.address)
    assert mock.data(mock_whitelist) == 200


def test_time_lock_expiration_boundary_timing(
    createMockTimeLock,
    governance,
    mock_rando_contract,
):
    """Test timing boundaries for expiration"""
    time_lock = 100
    expiration = 200
    mock = createMockTimeLock(
        _minTimeLock = 50,
        _maxTimeLock = 300,
        _initialTimeLock = time_lock,
        _expiration = expiration,
    )

    # Start action
    mock.addThing(mock_rando_contract, 100, sender=governance.address)
    
    # Time travel to one block before confirmation
    boa.env.time_travel(blocks=time_lock - 1)
    
    # Should not be able to confirm yet
    with boa.reverts("time lock not reached"):
        mock.confirmThing(mock_rando_contract, sender=governance.address)
    
    # Time travel one more block to reach confirmation
    boa.env.time_travel(blocks=1)
    
    # Should be able to confirm now
    mock.confirmThing(mock_rando_contract, sender=governance.address)
    assert mock.data(mock_rando_contract) == 100

    # Start another action to test exact expiration
    mock.addThing(mock_rando_contract, 200, sender=governance.address)
    
    # Time travel to one block before expiration
    # expiration = start_block2 + time_lock + expiration = start_block2 + 100 + 200 = start_block2 + 300
    # So travel 299 blocks to be one before expiration
    boa.env.time_travel(blocks=time_lock + expiration - 1)
    
    # Should still be able to confirm one block before expiration
    mock.confirmThing(mock_rando_contract, sender=governance.address)
    assert mock.data(mock_rando_contract) == 200

    # Start a third action to test exact expiration
    mock.addThing(mock_rando_contract, 300, sender=governance.address)
    
    # Time travel to exact expiration block
    boa.env.time_travel(blocks=time_lock + expiration)
    
    # Should not be able to confirm at exact expiration block
    with boa.reverts("time lock not reached"):
        mock.confirmThing(mock_rando_contract, sender=governance.address)


def test_time_lock_expiration_validation_edge_cases(
    createMockTimeLock,
    governance,
):
    """Test expiration validation edge cases"""
    mock = createMockTimeLock()
    current_time_lock = mock.actionTimeLock()
    
    # Test setting expiration equal to time lock (should work)
    assert mock.setExpiration(current_time_lock, sender=governance.address)
    assert mock.expiration() == current_time_lock
    
    # Test setting expiration to just above time lock
    assert mock.setExpiration(current_time_lock + 1, sender=governance.address)
    assert mock.expiration() == current_time_lock + 1
