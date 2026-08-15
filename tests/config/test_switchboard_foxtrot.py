from types import SimpleNamespace

import boa
import pytest
from vyper.compiler.output import build_abi_output

from conf_utils import filter_logs
from constants import MAX_UINT256, ZERO_ADDRESS


ACTION_INSTANT_BOND_CONFIG = 1
ACTION_RATE_OVERRIDE_SET = 2
ACTION_RATE_OVERRIDE_CANCEL = 4
MIN_BASE_RATE = 10_000


def travel(blocks):
    if blocks:
        boa.env.time_travel(blocks=blocks)


def make_config(scale, **overrides):
    values = {
        "canBuyNow": True,
        "paymentCapPerEpoch": 1_000 * scale,
        "minPaymentAmount": scale,
        "mintBudget": 1_000_000 * 10**18,
        "maxEffectiveRate": 2 * 10**18,
        "seedRate": 10**18,
        "uHighBps": 8_000,
        "uLowBps": 2_000,
        "minUpBps": 1_000,
        "maxUpBps": 1_000,
        "minDownBps": 500,
        "maxDownBps": 500,
        "decayBps": 900,
        "maxDecayEpochs": 4,
        "maxLockBonus": 5_000,
    }
    values.update(overrides)
    return (
        values["canBuyNow"],
        values["paymentCapPerEpoch"],
        values["minPaymentAmount"],
        values["mintBudget"],
        values["maxEffectiveRate"],
        values["seedRate"],
        values["uHighBps"],
        values["uLowBps"],
        values["minUpBps"],
        values["maxUpBps"],
        values["minDownBps"],
        values["maxDownBps"],
        values["decayBps"],
        values["maxDecayEpochs"],
        values["maxLockBonus"],
    )


@pytest.fixture
def foxtrot_env(
    ripe_hq,
    switchboard,
    switchboard_alpha,
    governance,
    charlie_token,
    charlie_token_whale,
    bob,
):
    with boa.env.anchor():
        scale = 10 ** charlie_token.decimals()
        registry_lock = ripe_hq.registryChangeTimeLock()
        genesis = boa.env.evm.patch.block_number + registry_lock * 2 + 5
        lane = boa.load(
            "contracts/core/InstantBondLane.vy",
            ripe_hq,
            charlie_token,
            genesis,
            100,
            name="foxtrot_test_lane",
        )

        assert ripe_hq.startAddNewAddressToRegistry(
            lane, "Foxtrot Test Lane", sender=governance.address
        )
        travel(registry_lock)
        lane_reg_id = ripe_hq.confirmNewAddressToRegistry(
            lane, sender=governance.address
        )
        ripe_hq.initiateHqConfigChange(
            lane_reg_id, False, True, False, sender=governance.address
        )
        travel(registry_lock)
        assert ripe_hq.confirmHqConfigChange(
            lane_reg_id, sender=governance.address
        )
        travel(genesis - boa.env.evm.patch.block_number)
        lane.pause(False, sender=switchboard_alpha.address)

        foxtrot = boa.load(
            "contracts/config/SwitchboardFoxtrot.vy",
            ripe_hq,
            ZERO_ADDRESS,
            2,
            20,
            lane,
            name="switchboard_foxtrot",
        )
        assert switchboard.startAddNewAddressToRegistry(
            foxtrot, "Foxtrot", sender=governance.address
        )
        travel(switchboard.registryChangeTimeLock())
        foxtrot_reg_id = switchboard.confirmNewAddressToRegistry(
            foxtrot, sender=governance.address
        )

        charlie_token.transfer(
            bob,
            10_000 * scale,
            sender=charlie_token_whale,
        )
        charlie_token.approve(lane, MAX_UINT256, sender=bob)

        yield SimpleNamespace(
            lane=lane,
            foxtrot=foxtrot,
            scale=scale,
            governance=governance,
            bob=bob,
            switchboard_alpha=switchboard_alpha,
            lane_reg_id=lane_reg_id,
            foxtrot_reg_id=foxtrot_reg_id,
            payment_token=charlie_token,
        )


def enable_actions(ctx):
    assert ctx.foxtrot.setActionTimeLockAfterSetup(sender=ctx.governance.address)
    assert ctx.foxtrot.actionTimeLock() == 2


def initialize_lane(ctx, config=None):
    if config is None:
        config = make_config(ctx.scale)

    expected_version = ctx.lane.configVersion()
    assert (
        ctx.lane.setConfig(
            config,
            expected_version,
            sender=ctx.switchboard_alpha.address,
        )
        == expected_version + 1
    )
    quote = ctx.lane.previewBuyNow(ctx.scale, 0)
    assert quote.available
    ctx.lane.buyNow(
        ctx.scale,
        0,
        quote.epoch,
        quote.totalRipe,
        boa.env.evm.patch.block_number,
        sender=ctx.bob,
    )
    assert ctx.lane.isInitialized()
    return config


def install_override(ctx, target_rate):
    action_id = ctx.foxtrot.setInstantBondRateOverride(
        target_rate,
        ctx.lane.configVersion(),
        ctx.lane.overrideVersion(),
        sender=ctx.governance.address,
    )
    travel(ctx.foxtrot.actionTimeLock())
    assert ctx.foxtrot.executePendingAction(
        action_id,
        sender=ctx.governance.address,
    )
    return action_id


def travel_to_next_lane_epoch(ctx):
    block_number = boa.env.evm.patch.block_number
    offset = (block_number - ctx.lane.GENESIS_BLOCK()) % ctx.lane.EPOCH_LENGTH()
    travel(ctx.lane.EPOCH_LENGTH() - offset)


def assert_pending_cleared(ctx, action_id):
    assert not ctx.foxtrot.hasPendingAction(action_id)
    assert ctx.foxtrot.actionType(action_id) == 0

    pending_config = ctx.foxtrot.pendingConfig(action_id)
    assert pending_config.expectedVersion == 0
    assert tuple(pending_config.config) == (False,) + (0,) * 14

    pending_override = ctx.foxtrot.pendingRateOverride(action_id)
    assert pending_override.targetRate == 0
    assert pending_override.expectedConfigVersion == 0
    assert pending_override.expectedOverrideVersion == 0


def contract_abi():
    compiler_data = boa.load_partial(
        "contracts/config/SwitchboardFoxtrot.vy"
    ).compiler_data
    return build_abi_output(compiler_data)


def test_constructor_target_and_immutables(ripe_hq, governance, alice, mock_rando_contract):
    with boa.env.anchor():
        with boa.reverts("invalid lane"):
            boa.load(
                "contracts/config/SwitchboardFoxtrot.vy",
                ripe_hq,
                ZERO_ADDRESS,
                2,
                20,
                ZERO_ADDRESS,
            )
        with boa.reverts("invalid lane"):
            boa.load(
                "contracts/config/SwitchboardFoxtrot.vy",
                ripe_hq,
                ZERO_ADDRESS,
                2,
                20,
                alice,
            )

        foxtrot = boa.load(
            "contracts/config/SwitchboardFoxtrot.vy",
            ripe_hq,
            ZERO_ADDRESS,
            2,
            20,
            mock_rando_contract,
        )
        assert foxtrot.LANE() == mock_rando_contract.address
        assert foxtrot.actionId() == 1
        assert foxtrot.actionTimeLock() == 0
        assert foxtrot.expiration() == 20


def test_rate_override_function_and_event_abi():
    abi = contract_abi()
    functions = {
        item["name"]: item
        for item in abi
        if item.get("type") == "function"
    }
    events = {
        item["name"]: item
        for item in abi
        if item.get("type") == "event"
    }

    set_override = functions["setInstantBondRateOverride"]
    assert [item["name"] for item in set_override["inputs"]] == [
        "_targetRate",
        "_expectedConfigVersion",
        "_expectedOverrideVersion",
    ]
    assert [item["type"] for item in set_override["outputs"]] == ["uint256"]
    assert set_override["stateMutability"] == "nonpayable"

    cancel_override = functions["cancelInstantBondRateOverride"]
    assert [item["name"] for item in cancel_override["inputs"]] == [
        "_expectedOverrideVersion"
    ]
    assert [item["type"] for item in cancel_override["outputs"]] == ["uint256"]
    assert cancel_override["stateMutability"] == "nonpayable"

    expected_event_fields = {
        "PendingRateOverrideSet": [
            "actionId",
            "confirmationBlock",
            "targetRate",
            "expectedConfigVersion",
            "expectedOverrideVersion",
        ],
        "PendingRateOverrideCancellationSet": [
            "actionId",
            "confirmationBlock",
            "expectedOverrideVersion",
        ],
        "RateOverrideExecuted": ["actionId", "newVersion"],
        "RateOverrideCancellationExecuted": ["actionId", "newVersion"],
        "RateOverrideActionCancelled": ["actionId", "isCancellation"],
    }
    for event_name, expected_fields in expected_event_fields.items():
        assert [item["name"] for item in events[event_name]["inputs"]] == expected_fields
        assert not any(item["indexed"] for item in events[event_name]["inputs"])


def test_initiation_requires_governance_nonzero_timelock_valid_config_and_version(
    foxtrot_env, alice
):
    ctx = foxtrot_env
    config = make_config(ctx.scale)

    with boa.reverts("no perms"):
        ctx.foxtrot.setInstantBondConfig(config, 0, sender=alice)
    with boa.reverts("action time lock not set"):
        ctx.foxtrot.setInstantBondConfig(config, 0, sender=ctx.governance.address)

    enable_actions(ctx)
    with boa.reverts("invalid config"):
        ctx.foxtrot.setInstantBondConfig(
            make_config(ctx.scale, minDownBps=0),
            0,
            sender=ctx.governance.address,
        )
    with boa.reverts("stale config version"):
        ctx.foxtrot.setInstantBondConfig(
            config,
            1,
            sender=ctx.governance.address,
        )


def test_pending_config_round_trip_and_execution_readback(foxtrot_env):
    ctx = foxtrot_env
    enable_actions(ctx)
    config = make_config(
        ctx.scale,
        paymentCapPerEpoch=1_234 * ctx.scale,
        minPaymentAmount=2 * ctx.scale,
        mintBudget=987_654 * 10**18,
        maxEffectiveRate=7 * 10**18,
        seedRate=3 * 10**18,
        uHighBps=8_765,
        uLowBps=1_234,
        minUpBps=777,
        maxUpBps=888,
        minDownBps=111,
        maxDownBps=222,
        decayBps=333,
        maxDecayEpochs=17,
        maxLockBonus=4_321,
    )

    action_id = ctx.foxtrot.setInstantBondConfig(
        config, 0, sender=ctx.governance.address
    )
    pending_event = filter_logs(ctx.foxtrot, "PendingInstantBondConfigSet")[0]
    pending = ctx.foxtrot.pendingConfig(action_id)

    assert action_id == 1
    assert ctx.foxtrot.actionType(action_id) == ACTION_INSTANT_BOND_CONFIG
    assert tuple(pending.config) == config
    assert pending.expectedVersion == 0
    assert pending_event.actionId == action_id
    assert pending_event.confirmationBlock == ctx.foxtrot.getActionConfirmationBlock(
        action_id
    )
    assert pending_event.expectedVersion == 0
    assert pending_event.paymentCapPerEpoch == config[1]
    assert pending_event.minPaymentAmount == config[2]
    assert pending_event.mintBudget == config[3]
    assert pending_event.maxEffectiveRate == config[4]
    assert pending_event.seedRate == config[5]
    assert pending_event.uHighBps == config[6]
    assert pending_event.uLowBps == config[7]
    assert pending_event.minUpBps == config[8]
    assert pending_event.maxUpBps == config[9]
    assert pending_event.minDownBps == config[10]
    assert pending_event.maxDownBps == config[11]
    assert pending_event.decayBps == config[12]
    assert pending_event.maxDecayEpochs == config[13]
    assert pending_event.maxLockBonus == config[14]

    assert not ctx.foxtrot.executePendingAction(
        action_id, sender=ctx.governance.address
    )
    assert ctx.foxtrot.hasPendingAction(action_id)

    travel(ctx.foxtrot.actionTimeLock())
    assert ctx.foxtrot.executePendingAction(
        action_id, sender=ctx.governance.address
    )
    executed = filter_logs(ctx.foxtrot, "InstantBondConfigExecuted")[0]
    assert executed.actionId == action_id
    assert executed.newVersion == ctx.lane.configVersion() == 1
    assert tuple(ctx.lane.config()) == config
    assert ctx.foxtrot.actionType(action_id) == 0
    assert_pending_cleared(ctx, action_id)


def test_stale_parallel_action_reverts_at_lane_and_can_be_cancelled(foxtrot_env):
    ctx = foxtrot_env
    enable_actions(ctx)
    first = ctx.foxtrot.setInstantBondConfig(
        make_config(ctx.scale), 0, sender=ctx.governance.address
    )
    second = ctx.foxtrot.setInstantBondConfig(
        make_config(ctx.scale, mintBudget=2_000_000 * 10**18),
        0,
        sender=ctx.governance.address,
    )
    travel(ctx.foxtrot.actionTimeLock())

    assert ctx.foxtrot.executePendingAction(first, sender=ctx.governance.address)
    with boa.reverts("stale config version"):
        ctx.foxtrot.executePendingAction(second, sender=ctx.governance.address)
    assert ctx.foxtrot.hasPendingAction(second)
    assert ctx.foxtrot.cancelPendingAction(second, sender=ctx.governance.address)
    assert_pending_cleared(ctx, second)


def test_out_of_order_parallel_execution_makes_earlier_action_stale(foxtrot_env):
    ctx = foxtrot_env
    enable_actions(ctx)
    first = ctx.foxtrot.setInstantBondConfig(
        make_config(ctx.scale), 0, sender=ctx.governance.address
    )
    second_config = make_config(
        ctx.scale,
        mintBudget=2_000_000 * 10**18,
        maxDecayEpochs=17,
    )
    second = ctx.foxtrot.setInstantBondConfig(
        second_config, 0, sender=ctx.governance.address
    )
    travel(ctx.foxtrot.actionTimeLock())

    assert ctx.foxtrot.executePendingAction(second, sender=ctx.governance.address)
    assert tuple(ctx.lane.config()) == second_config
    assert ctx.lane.configVersion() == 1
    with boa.reverts("stale config version"):
        ctx.foxtrot.executePendingAction(first, sender=ctx.governance.address)
    assert ctx.foxtrot.hasPendingAction(first)
    assert ctx.foxtrot.cancelPendingAction(first, sender=ctx.governance.address)
    assert_pending_cleared(ctx, first)


def test_cancel_permissions_cleanup_and_event(foxtrot_env, alice):
    ctx = foxtrot_env
    enable_actions(ctx)
    action_id = ctx.foxtrot.setInstantBondConfig(
        make_config(ctx.scale), 0, sender=ctx.governance.address
    )

    with boa.reverts("no perms"):
        ctx.foxtrot.cancelPendingAction(action_id, sender=alice)
    assert ctx.foxtrot.cancelPendingAction(
        action_id, sender=ctx.governance.address
    )
    cancelled = filter_logs(ctx.foxtrot, "InstantBondConfigCancelled")[0]
    assert cancelled.actionId == action_id
    assert_pending_cleared(ctx, action_id)
    with boa.reverts("cannot cancel action"):
        ctx.foxtrot.cancelPendingAction(action_id, sender=ctx.governance.address)


def test_expired_execution_auto_cancels_both_pending_records(foxtrot_env):
    ctx = foxtrot_env
    enable_actions(ctx)
    action_id = ctx.foxtrot.setInstantBondConfig(
        make_config(ctx.scale), 0, sender=ctx.governance.address
    )
    pending_action = ctx.foxtrot.pendingActions(action_id)
    travel(pending_action.expiration - boa.env.evm.patch.block_number)

    assert ctx.foxtrot.isExpired(action_id)
    assert not ctx.foxtrot.executePendingAction(
        action_id, sender=ctx.governance.address
    )
    cancelled = filter_logs(ctx.foxtrot, "InstantBondConfigCancelled")[0]
    assert cancelled.actionId == action_id
    assert_pending_cleared(ctx, action_id)


def test_execution_revalidates_budget_after_intervening_purchase(foxtrot_env):
    ctx = foxtrot_env
    initial = make_config(ctx.scale)
    ctx.lane.setConfig(initial, 0, sender=ctx.switchboard_alpha.address)
    enable_actions(ctx)

    proposed = make_config(ctx.scale, mintBudget=2 * 10**18)
    action_id = ctx.foxtrot.setInstantBondConfig(
        proposed, 1, sender=ctx.governance.address
    )

    amount = 3 * ctx.scale
    quote = ctx.lane.previewBuyNow(amount, 0)
    assert quote.totalRipe == 3 * 10**18
    ctx.lane.buyNow(
        amount,
        0,
        quote.epoch,
        quote.totalRipe,
        boa.env.evm.patch.block_number,
        sender=ctx.bob,
    )
    travel(ctx.foxtrot.actionTimeLock())

    with boa.reverts("invalid config"):
        ctx.foxtrot.executePendingAction(action_id, sender=ctx.governance.address)
    assert ctx.lane.configVersion() == 1
    assert ctx.foxtrot.hasPendingAction(action_id)
    assert ctx.foxtrot.pendingConfig(action_id).expectedVersion == 1


def test_rate_override_initiation_guards(foxtrot_env, alice):
    ctx = foxtrot_env
    target_rate = 11 * 10**17

    with boa.reverts("no perms"):
        ctx.foxtrot.setInstantBondRateOverride(
            target_rate,
            0,
            0,
            sender=alice,
        )
    with boa.reverts("action time lock not set"):
        ctx.foxtrot.setInstantBondRateOverride(
            target_rate,
            0,
            0,
            sender=ctx.governance.address,
        )

    enable_actions(ctx)
    with boa.reverts("invalid rate override"):
        ctx.foxtrot.setInstantBondRateOverride(
            target_rate,
            0,
            0,
            sender=ctx.governance.address,
        )

    config = initialize_lane(ctx)
    config_version = ctx.lane.configVersion()
    override_version = ctx.lane.overrideVersion()
    ceiling = config[4] * 10_000 // (10_000 + config[14])

    for rate, expected_config, expected_override in (
        (MIN_BASE_RATE - 1, config_version, override_version),
        (ceiling + 1, config_version, override_version),
        (target_rate, config_version + 1, override_version),
        (target_rate, config_version, override_version + 1),
    ):
        with boa.reverts("invalid rate override"):
            ctx.foxtrot.setInstantBondRateOverride(
                rate,
                expected_config,
                expected_override,
                sender=ctx.governance.address,
            )

    action_id = ctx.foxtrot.setInstantBondRateOverride(
        target_rate,
        config_version,
        override_version,
        sender=ctx.governance.address,
    )
    travel(ctx.foxtrot.actionTimeLock())
    assert ctx.foxtrot.executePendingAction(
        action_id,
        sender=ctx.governance.address,
    )

    with boa.reverts("invalid rate override"):
        ctx.foxtrot.setInstantBondRateOverride(
            target_rate,
            config_version,
            ctx.lane.overrideVersion(),
            sender=ctx.governance.address,
        )


def test_rate_override_cancellation_initiation_guards(foxtrot_env, alice):
    ctx = foxtrot_env

    with boa.reverts("no perms"):
        ctx.foxtrot.cancelInstantBondRateOverride(0, sender=alice)
    with boa.reverts("action time lock not set"):
        ctx.foxtrot.cancelInstantBondRateOverride(
            0,
            sender=ctx.governance.address,
        )

    enable_actions(ctx)
    initialize_lane(ctx)
    with boa.reverts("no rate override"):
        ctx.foxtrot.cancelInstantBondRateOverride(
            0,
            sender=ctx.governance.address,
        )

    target_rate = 11 * 10**17
    install_override(ctx, target_rate)
    with boa.reverts("no rate override"):
        ctx.foxtrot.cancelInstantBondRateOverride(
            ctx.lane.overrideVersion() - 1,
            sender=ctx.governance.address,
        )

    action_id = ctx.foxtrot.cancelInstantBondRateOverride(
        ctx.lane.overrideVersion(),
        sender=ctx.governance.address,
    )
    assert ctx.foxtrot.actionType(action_id) == ACTION_RATE_OVERRIDE_CANCEL


def test_pending_rate_override_round_trip_execution_and_events(foxtrot_env):
    ctx = foxtrot_env
    enable_actions(ctx)
    initialize_lane(ctx)
    target_rate = 11 * 10**17

    action_id = ctx.foxtrot.setInstantBondRateOverride(
        target_rate,
        1,
        0,
        sender=ctx.governance.address,
    )
    queued = filter_logs(ctx.foxtrot, "PendingRateOverrideSet")[-1]
    pending = ctx.foxtrot.pendingRateOverride(action_id)

    assert action_id == 1
    assert ctx.foxtrot.actionType(action_id) == ACTION_RATE_OVERRIDE_SET
    assert pending.targetRate == target_rate
    assert pending.expectedConfigVersion == 1
    assert pending.expectedOverrideVersion == 0
    assert queued.actionId == action_id
    assert queued.confirmationBlock == ctx.foxtrot.getActionConfirmationBlock(action_id)
    assert queued.targetRate == target_rate
    assert queued.expectedConfigVersion == 1
    assert queued.expectedOverrideVersion == 0

    assert not ctx.foxtrot.executePendingAction(
        action_id,
        sender=ctx.governance.address,
    )
    assert ctx.lane.rateOverride() == 0
    assert ctx.foxtrot.hasPendingAction(action_id)

    travel(ctx.foxtrot.actionTimeLock())
    assert ctx.foxtrot.executePendingAction(
        action_id,
        sender=ctx.governance.address,
    )
    executed = filter_logs(ctx.foxtrot, "RateOverrideExecuted")[-1]
    assert executed.actionId == action_id
    assert executed.newVersion == 1
    assert ctx.lane.rateOverride() == target_rate
    assert ctx.lane.overrideVersion() == 1
    assert_pending_cleared(ctx, action_id)


def test_pending_rate_override_cancellation_round_trip_execution_and_events(
    foxtrot_env,
):
    ctx = foxtrot_env
    enable_actions(ctx)
    initialize_lane(ctx)
    target_rate = 11 * 10**17
    install_override(ctx, target_rate)

    action_id = ctx.foxtrot.cancelInstantBondRateOverride(
        1,
        sender=ctx.governance.address,
    )
    queued = filter_logs(ctx.foxtrot, "PendingRateOverrideCancellationSet")[-1]
    pending = ctx.foxtrot.pendingRateOverride(action_id)

    assert ctx.foxtrot.actionType(action_id) == ACTION_RATE_OVERRIDE_CANCEL
    assert pending.targetRate == 0
    assert pending.expectedConfigVersion == 0
    assert pending.expectedOverrideVersion == 1
    assert queued.actionId == action_id
    assert queued.confirmationBlock == ctx.foxtrot.getActionConfirmationBlock(action_id)
    assert queued.expectedOverrideVersion == 1

    assert not ctx.foxtrot.executePendingAction(
        action_id,
        sender=ctx.governance.address,
    )
    assert ctx.lane.rateOverride() == target_rate

    travel(ctx.foxtrot.actionTimeLock())
    assert ctx.foxtrot.executePendingAction(
        action_id,
        sender=ctx.governance.address,
    )
    executed = filter_logs(ctx.foxtrot, "RateOverrideCancellationExecuted")[-1]
    assert executed.actionId == action_id
    assert executed.newVersion == 2
    assert ctx.lane.rateOverride() == 0
    assert ctx.lane.overrideVersion() == 2
    assert_pending_cleared(ctx, action_id)


def test_manual_cancellation_distinguishes_override_set_and_cancel_actions(foxtrot_env):
    ctx = foxtrot_env
    enable_actions(ctx)
    initialize_lane(ctx)
    target_rate = 11 * 10**17

    set_action = ctx.foxtrot.setInstantBondRateOverride(
        target_rate,
        1,
        0,
        sender=ctx.governance.address,
    )
    assert ctx.foxtrot.cancelPendingAction(
        set_action,
        sender=ctx.governance.address,
    )
    set_cancelled = filter_logs(ctx.foxtrot, "RateOverrideActionCancelled")[-1]
    assert set_cancelled.actionId == set_action
    assert not set_cancelled.isCancellation
    assert ctx.lane.rateOverride() == 0
    assert ctx.lane.overrideVersion() == 0
    assert_pending_cleared(ctx, set_action)

    install_override(ctx, target_rate)
    cancel_action = ctx.foxtrot.cancelInstantBondRateOverride(
        1,
        sender=ctx.governance.address,
    )
    assert ctx.foxtrot.cancelPendingAction(
        cancel_action,
        sender=ctx.governance.address,
    )
    cancel_cancelled = filter_logs(ctx.foxtrot, "RateOverrideActionCancelled")[-1]
    assert cancel_cancelled.actionId == cancel_action
    assert cancel_cancelled.isCancellation
    assert ctx.lane.rateOverride() == target_rate
    assert ctx.lane.overrideVersion() == 1
    assert_pending_cleared(ctx, cancel_action)


def test_expired_rate_override_set_action_cleans_without_changing_lane(foxtrot_env):
    ctx = foxtrot_env
    enable_actions(ctx)
    initialize_lane(ctx)
    target_rate = 11 * 10**17
    action_id = ctx.foxtrot.setInstantBondRateOverride(
        target_rate,
        1,
        0,
        sender=ctx.governance.address,
    )
    pending_action = ctx.foxtrot.pendingActions(action_id)
    travel(pending_action.expiration - boa.env.evm.patch.block_number)

    assert ctx.foxtrot.isExpired(action_id)
    assert not ctx.foxtrot.executePendingAction(
        action_id,
        sender=ctx.governance.address,
    )
    cancelled = filter_logs(ctx.foxtrot, "RateOverrideActionCancelled")[-1]
    assert cancelled.actionId == action_id
    assert not cancelled.isCancellation
    assert ctx.lane.rateOverride() == 0
    assert ctx.lane.overrideVersion() == 0
    assert_pending_cleared(ctx, action_id)


def test_expired_rate_override_cancel_action_preserves_installed_override(foxtrot_env):
    ctx = foxtrot_env
    enable_actions(ctx)
    initialize_lane(ctx)
    target_rate = 11 * 10**17
    install_override(ctx, target_rate)
    action_id = ctx.foxtrot.cancelInstantBondRateOverride(
        1,
        sender=ctx.governance.address,
    )
    pending_action = ctx.foxtrot.pendingActions(action_id)
    travel(pending_action.expiration - boa.env.evm.patch.block_number)

    assert ctx.foxtrot.isExpired(action_id)
    assert not ctx.foxtrot.executePendingAction(
        action_id,
        sender=ctx.governance.address,
    )
    cancelled = filter_logs(ctx.foxtrot, "RateOverrideActionCancelled")[-1]
    assert cancelled.actionId == action_id
    assert cancelled.isCancellation
    assert ctx.lane.rateOverride() == target_rate
    assert ctx.lane.overrideVersion() == 1
    assert_pending_cleared(ctx, action_id)


def test_parallel_rate_override_sets_leave_stale_action_pending(foxtrot_env):
    ctx = foxtrot_env
    enable_actions(ctx)
    initialize_lane(ctx)
    first_target = 11 * 10**17
    second_target = 12 * 10**17
    first = ctx.foxtrot.setInstantBondRateOverride(
        first_target,
        1,
        0,
        sender=ctx.governance.address,
    )
    second = ctx.foxtrot.setInstantBondRateOverride(
        second_target,
        1,
        0,
        sender=ctx.governance.address,
    )
    travel(ctx.foxtrot.actionTimeLock())

    assert ctx.foxtrot.executePendingAction(first, sender=ctx.governance.address)
    with boa.reverts("stale override version"):
        ctx.foxtrot.executePendingAction(second, sender=ctx.governance.address)
    assert ctx.lane.rateOverride() == first_target
    assert ctx.lane.overrideVersion() == 1
    assert ctx.foxtrot.hasPendingAction(second)
    assert ctx.foxtrot.actionType(second) == ACTION_RATE_OVERRIDE_SET
    assert ctx.foxtrot.pendingRateOverride(second).targetRate == second_target
    assert ctx.foxtrot.cancelPendingAction(second, sender=ctx.governance.address)
    assert ctx.lane.overrideVersion() == 1
    assert_pending_cleared(ctx, second)


def test_parallel_rate_override_cancellations_leave_stale_action_pending(
    foxtrot_env,
):
    ctx = foxtrot_env
    enable_actions(ctx)
    initialize_lane(ctx)
    target_rate = 11 * 10**17
    install_override(ctx, target_rate)
    first = ctx.foxtrot.cancelInstantBondRateOverride(
        1,
        sender=ctx.governance.address,
    )
    second = ctx.foxtrot.cancelInstantBondRateOverride(
        1,
        sender=ctx.governance.address,
    )
    travel(ctx.foxtrot.actionTimeLock())

    assert ctx.foxtrot.executePendingAction(first, sender=ctx.governance.address)
    with boa.reverts("stale override version"):
        ctx.foxtrot.executePendingAction(second, sender=ctx.governance.address)
    assert ctx.lane.rateOverride() == 0
    assert ctx.lane.overrideVersion() == 2
    assert ctx.foxtrot.hasPendingAction(second)
    assert ctx.foxtrot.actionType(second) == ACTION_RATE_OVERRIDE_CANCEL
    assert ctx.foxtrot.pendingRateOverride(second).expectedOverrideVersion == 1
    assert ctx.foxtrot.cancelPendingAction(second, sender=ctx.governance.address)
    assert ctx.lane.overrideVersion() == 2
    assert_pending_cleared(ctx, second)


def test_config_first_makes_queued_rate_override_stale(foxtrot_env):
    ctx = foxtrot_env
    enable_actions(ctx)
    initialize_lane(ctx)
    target_rate = 11 * 10**17
    override_action = ctx.foxtrot.setInstantBondRateOverride(
        target_rate,
        1,
        0,
        sender=ctx.governance.address,
    )
    new_config = make_config(ctx.scale, mintBudget=2_000_000 * 10**18)
    config_action = ctx.foxtrot.setInstantBondConfig(
        new_config,
        1,
        sender=ctx.governance.address,
    )
    travel(ctx.foxtrot.actionTimeLock())

    assert ctx.foxtrot.executePendingAction(
        config_action,
        sender=ctx.governance.address,
    )
    assert ctx.lane.configVersion() == 2
    assert ctx.lane.overrideVersion() == 0
    with boa.reverts("stale config version"):
        ctx.foxtrot.executePendingAction(
            override_action,
            sender=ctx.governance.address,
        )
    assert ctx.foxtrot.hasPendingAction(override_action)
    assert ctx.foxtrot.pendingRateOverride(override_action).targetRate == target_rate
    assert ctx.foxtrot.cancelPendingAction(
        override_action,
        sender=ctx.governance.address,
    )
    assert_pending_cleared(ctx, override_action)


def test_override_first_then_config_invalidates_installed_override(foxtrot_env):
    ctx = foxtrot_env
    enable_actions(ctx)
    initialize_lane(ctx)
    target_rate = 11 * 10**17
    override_action = ctx.foxtrot.setInstantBondRateOverride(
        target_rate,
        1,
        0,
        sender=ctx.governance.address,
    )
    new_config = make_config(ctx.scale, mintBudget=2_000_000 * 10**18)
    config_action = ctx.foxtrot.setInstantBondConfig(
        new_config,
        1,
        sender=ctx.governance.address,
    )
    travel(ctx.foxtrot.actionTimeLock())

    assert ctx.foxtrot.executePendingAction(
        override_action,
        sender=ctx.governance.address,
    )
    assert ctx.lane.rateOverride() == target_rate
    assert ctx.lane.overrideVersion() == 1
    assert ctx.foxtrot.executePendingAction(
        config_action,
        sender=ctx.governance.address,
    )
    executed = filter_logs(ctx.foxtrot, "InstantBondConfigExecuted")[-1]
    assert executed.actionId == config_action
    assert executed.newVersion == 2
    assert ctx.lane.configVersion() == 2
    assert ctx.lane.rateOverride() == 0
    assert ctx.lane.overrideVersion() == 2
    assert_pending_cleared(ctx, override_action)
    assert_pending_cleared(ctx, config_action)


def test_config_invalidation_makes_queued_override_cancellation_stale(foxtrot_env):
    ctx = foxtrot_env
    enable_actions(ctx)
    initialize_lane(ctx)
    target_rate = 11 * 10**17
    install_override(ctx, target_rate)
    cancel_action = ctx.foxtrot.cancelInstantBondRateOverride(
        1,
        sender=ctx.governance.address,
    )
    config_action = ctx.foxtrot.setInstantBondConfig(
        make_config(ctx.scale, mintBudget=2_000_000 * 10**18),
        1,
        sender=ctx.governance.address,
    )
    travel(ctx.foxtrot.actionTimeLock())

    assert ctx.foxtrot.executePendingAction(
        config_action,
        sender=ctx.governance.address,
    )
    assert ctx.lane.rateOverride() == 0
    assert ctx.lane.overrideVersion() == 2
    with boa.reverts("stale override version"):
        ctx.foxtrot.executePendingAction(
            cancel_action,
            sender=ctx.governance.address,
        )
    assert ctx.foxtrot.hasPendingAction(cancel_action)
    assert ctx.foxtrot.pendingRateOverride(cancel_action).expectedOverrideVersion == 1
    assert ctx.foxtrot.cancelPendingAction(
        cancel_action,
        sender=ctx.governance.address,
    )
    assert_pending_cleared(ctx, cancel_action)


def test_override_cancellation_before_config_does_not_double_bump_version(
    foxtrot_env,
):
    ctx = foxtrot_env
    enable_actions(ctx)
    initialize_lane(ctx)
    target_rate = 11 * 10**17
    install_override(ctx, target_rate)
    cancel_action = ctx.foxtrot.cancelInstantBondRateOverride(
        1,
        sender=ctx.governance.address,
    )
    config_action = ctx.foxtrot.setInstantBondConfig(
        make_config(ctx.scale, mintBudget=2_000_000 * 10**18),
        1,
        sender=ctx.governance.address,
    )
    travel(ctx.foxtrot.actionTimeLock())

    assert ctx.foxtrot.executePendingAction(
        cancel_action,
        sender=ctx.governance.address,
    )
    assert ctx.lane.overrideVersion() == 2
    assert ctx.foxtrot.executePendingAction(
        config_action,
        sender=ctx.governance.address,
    )
    assert ctx.lane.configVersion() == 2
    assert ctx.lane.rateOverride() == 0
    assert ctx.lane.overrideVersion() == 2
    assert_pending_cleared(ctx, cancel_action)
    assert_pending_cleared(ctx, config_action)


def test_override_applies_only_on_next_successful_rollover(foxtrot_env):
    ctx = foxtrot_env
    enable_actions(ctx)
    initialize_lane(ctx)
    target_rate = 11 * 10**17
    install_override(ctx, target_rate)
    stored_epoch = ctx.lane.currentEpoch()
    stored_rate = ctx.lane.epochRate()

    same_epoch_quote = ctx.lane.previewBuyNow(ctx.scale, 0)
    assert same_epoch_quote.epoch == stored_epoch
    assert same_epoch_quote.rate == stored_rate
    ctx.lane.buyNow(
        ctx.scale,
        0,
        same_epoch_quote.epoch,
        same_epoch_quote.totalRipe,
        boa.env.evm.patch.block_number,
        sender=ctx.bob,
    )
    assert ctx.lane.rateOverride() == target_rate
    assert ctx.lane.overrideVersion() == 1

    travel_to_next_lane_epoch(ctx)
    rollover_quote = ctx.lane.previewBuyNow(ctx.scale, 0)
    assert rollover_quote.epoch > stored_epoch
    assert rollover_quote.rate == target_rate
    assert ctx.lane.rateOverride() == target_rate
    assert ctx.lane.overrideVersion() == 1

    ctx.lane.buyNow(
        ctx.scale,
        0,
        rollover_quote.epoch,
        rollover_quote.totalRipe,
        boa.env.evm.patch.block_number,
        sender=ctx.bob,
    )
    applied = filter_logs(ctx.lane, "RateOverrideApplied")[-1]
    assert applied.newVersion == 2
    assert applied.fromEpoch == stored_epoch
    assert applied.toEpoch == rollover_quote.epoch
    assert applied.targetRate == target_rate
    assert ctx.lane.currentEpoch() == rollover_quote.epoch
    assert ctx.lane.epochRate() == target_rate
    assert ctx.lane.rateOverride() == 0
    assert ctx.lane.overrideVersion() == 2


def test_successful_rollover_makes_pending_override_cancellation_stale(foxtrot_env):
    ctx = foxtrot_env
    enable_actions(ctx)
    initialize_lane(ctx)
    target_rate = 11 * 10**17
    install_override(ctx, target_rate)
    travel_to_next_lane_epoch(ctx)
    cancel_action = ctx.foxtrot.cancelInstantBondRateOverride(
        1,
        sender=ctx.governance.address,
    )
    travel(ctx.foxtrot.actionTimeLock())

    quote = ctx.lane.previewBuyNow(ctx.scale, 0)
    assert quote.rate == target_rate
    ctx.lane.buyNow(
        ctx.scale,
        0,
        quote.epoch,
        quote.totalRipe,
        boa.env.evm.patch.block_number,
        sender=ctx.bob,
    )
    assert ctx.lane.rateOverride() == 0
    assert ctx.lane.overrideVersion() == 2

    with boa.reverts("stale override version"):
        ctx.foxtrot.executePendingAction(
            cancel_action,
            sender=ctx.governance.address,
        )
    assert ctx.foxtrot.hasPendingAction(cancel_action)
    assert ctx.foxtrot.actionType(cancel_action) == ACTION_RATE_OVERRIDE_CANCEL
    assert ctx.foxtrot.cancelPendingAction(
        cancel_action,
        sender=ctx.governance.address,
    )
    assert_pending_cleared(ctx, cancel_action)
