import boa
import pytest

from constants import MAX_UINT256


TARGET_MISSION_CONTROL_SOURCE = """
# @version 0.4.3

import interfaces.ConfigStructs as cs

genDebtConfig: public(cs.GenDebtConfig)
switchboard: immutable(address)


@deploy
def __init__(_config: cs.GenDebtConfig, _switchboard: address):
    self.genDebtConfig = _config
    switchboard = _switchboard


@external
def setGeneralDebtConfig(_config: cs.GenDebtConfig):
    assert msg.sender == switchboard # dev: no perms
    self.genDebtConfig = _config
"""


def _debt_config(config, *, min_debt_amount, max_borrow_per_interval, num_blocks_per_interval):
    return config._replace(
        minDebtAmount=min_debt_amount,
        maxBorrowPerInterval=max_borrow_per_interval,
        numBlocksPerInterval=num_blocks_per_interval,
    )


def _set_debt_config(
    mission_control,
    switchboard_alpha,
    *,
    min_debt_amount,
    max_borrow_per_interval,
    num_blocks_per_interval=100,
):
    config = _debt_config(
        mission_control.genDebtConfig(),
        min_debt_amount=min_debt_amount,
        max_borrow_per_interval=max_borrow_per_interval,
        num_blocks_per_interval=num_blocks_per_interval,
    )
    mission_control.setGeneralDebtConfig(config, sender=switchboard_alpha.address)


@pytest.fixture
def target_mission_control(mission_control, switchboard_alpha):
    return boa.loads(
        TARGET_MISSION_CONTROL_SOURCE,
        mission_control.genDebtConfig(),
        switchboard_alpha.address,
        name="borrow_interval_target_mission_control",
    )


def test_explicit_target_uses_target_min_debt_amount(
    switchboard_alpha,
    mission_control,
    target_mission_control,
    governance,
):
    _set_debt_config(
        mission_control,
        switchboard_alpha,
        min_debt_amount=100,
        max_borrow_per_interval=1_000,
    )
    _set_debt_config(
        target_mission_control,
        switchboard_alpha,
        min_debt_amount=600,
        max_borrow_per_interval=1_000,
    )
    next_action_id = switchboard_alpha.actionId()

    with boa.reverts("invalid borrow interval config"):
        switchboard_alpha.setBorrowIntervalConfig(
            500,
            50,
            target_mission_control.address,
            sender=governance.address,
        )

    assert switchboard_alpha.actionId() == next_action_id
    assert not switchboard_alpha.hasPendingAction(next_action_id)


def test_valid_explicit_target_action_updates_only_target(
    switchboard_alpha,
    mission_control,
    target_mission_control,
    governance,
):
    _set_debt_config(
        mission_control,
        switchboard_alpha,
        min_debt_amount=100,
        max_borrow_per_interval=1_000,
        num_blocks_per_interval=100,
    )
    _set_debt_config(
        target_mission_control,
        switchboard_alpha,
        min_debt_amount=600,
        max_borrow_per_interval=1_200,
        num_blocks_per_interval=200,
    )

    action_id = switchboard_alpha.setBorrowIntervalConfig(
        700,
        50,
        target_mission_control.address,
        sender=governance.address,
    )
    assert switchboard_alpha.pendingMissionControl(action_id) == target_mission_control.address

    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    assert switchboard_alpha.executePendingAction(action_id, sender=governance.address)

    target_config = target_mission_control.genDebtConfig()
    assert target_config.maxBorrowPerInterval == 700
    assert target_config.numBlocksPerInterval == 50

    current_config = mission_control.genDebtConfig()
    assert current_config.maxBorrowPerInterval == 1_000
    assert current_config.numBlocksPerInterval == 100


def test_explicit_target_is_revalidated_at_execution_and_expires(
    switchboard_alpha,
    target_mission_control,
    governance,
):
    _set_debt_config(
        target_mission_control,
        switchboard_alpha,
        min_debt_amount=100,
        max_borrow_per_interval=1_000,
        num_blocks_per_interval=100,
    )
    action_id = switchboard_alpha.setBorrowIntervalConfig(
        500,
        50,
        target_mission_control.address,
        sender=governance.address,
    )

    _set_debt_config(
        target_mission_control,
        switchboard_alpha,
        min_debt_amount=600,
        max_borrow_per_interval=1_000,
        num_blocks_per_interval=100,
    )
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())

    with boa.reverts("invalid borrow interval config"):
        switchboard_alpha.executePendingAction(action_id, sender=governance.address)

    config = target_mission_control.genDebtConfig()
    assert config.maxBorrowPerInterval == 1_000
    assert config.minDebtAmount == 600
    assert config.numBlocksPerInterval == 100
    assert switchboard_alpha.hasPendingAction(action_id)
    assert switchboard_alpha.pendingDebtConfig(action_id).maxBorrowPerInterval == 500

    boa.env.time_travel(blocks=switchboard_alpha.expiration())
    assert not switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    assert not switchboard_alpha.hasPendingAction(action_id)
    assert switchboard_alpha.actionType(action_id) == 0

    config = target_mission_control.genDebtConfig()
    assert config.maxBorrowPerInterval == 1_000
    assert config.minDebtAmount == 600
    assert config.numBlocksPerInterval == 100


def test_default_target_still_uses_current_mission_control(
    switchboard_alpha,
    mission_control,
    governance,
):
    _set_debt_config(
        mission_control,
        switchboard_alpha,
        min_debt_amount=100,
        max_borrow_per_interval=1_000,
        num_blocks_per_interval=100,
    )

    action_id = switchboard_alpha.setBorrowIntervalConfig(
        500,
        50,
        sender=governance.address,
    )
    assert switchboard_alpha.pendingMissionControl(action_id) == mission_control.address

    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    assert switchboard_alpha.executePendingAction(action_id, sender=governance.address)

    config = mission_control.genDebtConfig()
    assert config.maxBorrowPerInterval == 500
    assert config.numBlocksPerInterval == 50


def test_default_target_is_revalidated_after_global_limits_execute(
    switchboard_alpha,
    mission_control,
    governance,
):
    _set_debt_config(
        mission_control,
        switchboard_alpha,
        min_debt_amount=100,
        max_borrow_per_interval=1_000,
        num_blocks_per_interval=100,
    )
    interval_action_id = switchboard_alpha.setBorrowIntervalConfig(
        500,
        50,
        sender=governance.address,
    )
    global_limits_action_id = switchboard_alpha.setGlobalDebtLimits(
        5_000,
        50_000,
        600,
        100,
        sender=governance.address,
    )

    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    assert switchboard_alpha.executePendingAction(
        global_limits_action_id,
        sender=governance.address,
    )

    with boa.reverts("invalid borrow interval config"):
        switchboard_alpha.executePendingAction(
            interval_action_id,
            sender=governance.address,
        )

    config = mission_control.genDebtConfig()
    assert config.minDebtAmount == 600
    assert config.maxBorrowPerInterval == 1_000
    assert config.numBlocksPerInterval == 100
    assert switchboard_alpha.hasPendingAction(interval_action_id)


def test_explicit_target_boundary_and_existing_validation(
    switchboard_alpha,
    target_mission_control,
    governance,
):
    _set_debt_config(
        target_mission_control,
        switchboard_alpha,
        min_debt_amount=500,
        max_borrow_per_interval=1_000,
    )

    action_id = switchboard_alpha.setBorrowIntervalConfig(
        500,
        50,
        target_mission_control.address,
        sender=governance.address,
    )
    assert switchboard_alpha.hasPendingAction(action_id)

    invalid_configs = (
        (0, 50),
        (500, 0),
        (MAX_UINT256, 50),
        (500, MAX_UINT256),
    )
    for max_borrow_per_interval, num_blocks_per_interval in invalid_configs:
        with boa.reverts("invalid borrow interval config"):
            switchboard_alpha.setBorrowIntervalConfig(
                max_borrow_per_interval,
                num_blocks_per_interval,
                target_mission_control.address,
                sender=governance.address,
            )


def test_nonconforming_explicit_target_fails_before_queue(
    switchboard_alpha,
    mission_control,
    governance,
):
    _set_debt_config(
        mission_control,
        switchboard_alpha,
        min_debt_amount=100,
        max_borrow_per_interval=1_000,
    )
    nonconforming_target = boa.env.generate_address()
    next_action_id = switchboard_alpha.actionId()

    with boa.reverts():
        switchboard_alpha.setBorrowIntervalConfig(
            500,
            50,
            nonconforming_target,
            sender=governance.address,
        )

    assert switchboard_alpha.actionId() == next_action_id
    assert not switchboard_alpha.hasPendingAction(next_action_id)
