import boa
import pytest

from constants import MAX_UINT256
from conf_utils import filter_logs


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


def test_global_debt_limits_default_target_rejects_min_above_interval(
    switchboard_alpha,
    mission_control,
    governance,
):
    _set_debt_config(
        mission_control,
        switchboard_alpha,
        min_debt_amount=100,
        max_borrow_per_interval=500,
    )
    config_before = mission_control.genDebtConfig()
    next_action_id = switchboard_alpha.actionId()

    with boa.reverts("invalid debt limits"):
        switchboard_alpha.setGlobalDebtLimits(
            5_000,
            50_000,
            501,
            100,
            sender=governance.address,
        )

    assert switchboard_alpha.actionId() == next_action_id
    assert not switchboard_alpha.hasPendingAction(next_action_id)
    assert mission_control.genDebtConfig() == config_before


def test_global_debt_limits_default_target_allows_equality(
    switchboard_alpha,
    mission_control,
    governance,
):
    _set_debt_config(
        mission_control,
        switchboard_alpha,
        min_debt_amount=100,
        max_borrow_per_interval=500,
        num_blocks_per_interval=100,
    )
    config_before = mission_control.genDebtConfig()

    action_id = switchboard_alpha.setGlobalDebtLimits(
        5_000,
        50_000,
        500,
        100,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    assert switchboard_alpha.executePendingAction(action_id, sender=governance.address)

    config_after = mission_control.genDebtConfig()
    assert config_after == config_before._replace(
        perUserDebtLimit=5_000,
        globalDebtLimit=50_000,
        minDebtAmount=500,
        numAllowedBorrowers=100,
    )
    assert config_after.minDebtAmount == config_after.maxBorrowPerInterval == 500


def test_global_debt_limits_zero_bootstrap_boundary(
    switchboard_alpha,
    mission_control,
    governance,
):
    _set_debt_config(
        mission_control,
        switchboard_alpha,
        min_debt_amount=0,
        max_borrow_per_interval=0,
        num_blocks_per_interval=0,
    )
    config_before = mission_control.genDebtConfig()
    assert config_before.minDebtAmount == 0
    assert config_before.maxBorrowPerInterval == 0

    action_id = switchboard_alpha.setGlobalDebtLimits(
        5_000,
        50_000,
        0,
        100,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    assert switchboard_alpha.executePendingAction(action_id, sender=governance.address)

    config_after = mission_control.genDebtConfig()
    assert config_after == config_before._replace(
        perUserDebtLimit=5_000,
        globalDebtLimit=50_000,
        minDebtAmount=0,
        numAllowedBorrowers=100,
    )
    assert config_after.minDebtAmount == config_after.maxBorrowPerInterval == 0


def test_global_debt_limits_explicit_target_validation_and_equality_execution(
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
        min_debt_amount=100,
        max_borrow_per_interval=500,
        num_blocks_per_interval=200,
    )
    current_before = mission_control.genDebtConfig()
    target_before = target_mission_control.genDebtConfig()
    next_action_id = switchboard_alpha.actionId()

    with boa.reverts("invalid debt limits"):
        switchboard_alpha.setGlobalDebtLimits(
            5_000,
            50_000,
            600,
            100,
            target_mission_control.address,
            sender=governance.address,
        )

    assert switchboard_alpha.actionId() == next_action_id
    assert not switchboard_alpha.hasPendingAction(next_action_id)
    assert mission_control.genDebtConfig() == current_before
    assert target_mission_control.genDebtConfig() == target_before

    action_id = switchboard_alpha.setGlobalDebtLimits(
        5_000,
        50_000,
        500,
        100,
        target_mission_control.address,
        sender=governance.address,
    )
    pending_log = filter_logs(switchboard_alpha, "PendingGlobalDebtLimitsChange")[0]
    assert pending_log.perUserDebtLimit == 5_000
    assert pending_log.globalDebtLimit == 50_000
    assert pending_log.minDebtAmount == 500
    assert pending_log.numAllowedBorrowers == 100
    assert pending_log.actionId == action_id
    assert action_id == next_action_id
    assert switchboard_alpha.pendingMissionControl(action_id) == target_mission_control.address

    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    assert switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    executed_log = filter_logs(switchboard_alpha, "GlobalDebtLimitsSet")[0]
    assert executed_log.perUserDebtLimit == 5_000
    assert executed_log.globalDebtLimit == 50_000
    assert executed_log.minDebtAmount == 500
    assert executed_log.numAllowedBorrowers == 100

    target_after = target_mission_control.genDebtConfig()
    assert target_after == target_before._replace(
        perUserDebtLimit=5_000,
        globalDebtLimit=50_000,
        minDebtAmount=500,
        numAllowedBorrowers=100,
    )
    assert target_after.minDebtAmount == target_after.maxBorrowPerInterval == 500
    assert target_after.numBlocksPerInterval == 200
    assert mission_control.genDebtConfig() == current_before


def test_global_debt_limits_revalidates_after_borrow_interval_executes(
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
    initial_config = mission_control.genDebtConfig()
    global_limits_action_id = switchboard_alpha.setGlobalDebtLimits(
        5_000,
        50_000,
        600,
        100,
        sender=governance.address,
    )
    pending_before = switchboard_alpha.pendingDebtConfig(global_limits_action_id)
    pending_target = switchboard_alpha.pendingMissionControl(global_limits_action_id)
    confirmation_block = switchboard_alpha.getActionConfirmationBlock(
        global_limits_action_id
    )

    interval_action_id = switchboard_alpha.setBorrowIntervalConfig(
        500,
        50,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    assert switchboard_alpha.executePendingAction(
        interval_action_id,
        sender=governance.address,
    )
    interval_config = initial_config._replace(
        maxBorrowPerInterval=500,
        numBlocksPerInterval=50,
    )
    assert mission_control.genDebtConfig() == interval_config

    with boa.reverts("invalid debt limits"):
        switchboard_alpha.executePendingAction(
            global_limits_action_id,
            sender=governance.address,
        )

    assert mission_control.genDebtConfig() == interval_config
    assert mission_control.genDebtConfig().minDebtAmount == 100
    assert mission_control.genDebtConfig().maxBorrowPerInterval == 500
    assert switchboard_alpha.pendingDebtConfig(global_limits_action_id) == pending_before
    assert switchboard_alpha.pendingMissionControl(global_limits_action_id) == pending_target
    assert switchboard_alpha.hasPendingAction(global_limits_action_id)
    assert switchboard_alpha.getActionConfirmationBlock(global_limits_action_id) == confirmation_block
    assert switchboard_alpha.canConfirmAction(global_limits_action_id)
    assert not switchboard_alpha.isExpired(global_limits_action_id)

    restore_interval_action_id = switchboard_alpha.setBorrowIntervalConfig(
        1_000,
        100,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    assert switchboard_alpha.executePendingAction(
        restore_interval_action_id,
        sender=governance.address,
    )
    assert switchboard_alpha.canConfirmAction(global_limits_action_id)
    assert switchboard_alpha.executePendingAction(
        global_limits_action_id,
        sender=governance.address,
    )

    assert mission_control.genDebtConfig() == initial_config._replace(
        perUserDebtLimit=5_000,
        globalDebtLimit=50_000,
        minDebtAmount=600,
        numAllowedBorrowers=100,
    )
    assert not switchboard_alpha.hasPendingAction(global_limits_action_id)


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
