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
    ):
        return boa.load(
            "contracts/mock/MockWithTimeLock.vy",
            _ripeHq,
            _minTimeLock,
            _maxTimeLock,
            _initialTimeLock,
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

    # Success case with valid parameters
    mock = createMockTimeLock(
        _minTimeLock = 100,
        _maxTimeLock = 200,
        _initialTimeLock = 150,
    )

    assert mock.minActionTimeLock() == 100
    assert mock.maxActionTimeLock() == 200
    assert mock.actionTimeLock() == 150
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
    pending = mock.pendingData(mock_rando_contract)
    
    # Try to confirm with wrong action ID
    with boa.reverts("time lock not reached"):
        mock.confirmThing(mock_rando_contract, sender=governance.address)
    
    # Cancel action
    mock.cancelThing(mock_rando_contract, sender=governance.address)
    
    # Try to confirm cancelled action
    with boa.reverts("time lock not reached"):
        mock.confirmThing(mock_rando_contract, sender=governance.address)
