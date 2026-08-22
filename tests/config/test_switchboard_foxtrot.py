import boa
import pytest
from types import SimpleNamespace
from vyper.compiler.output import build_abi_output

from conf_utils import filter_logs
from constants import INSTANT_BOND_LANE_HQ_ID, MAX_UINT256, ZERO_ADDRESS

from tests.core.instantBondLane.conftest import make_config


ACTION_INSTANT_BOND_CONFIG = 1
ACTION_RATE_OVERRIDE_SET = 2
ACTION_RATE_OVERRIDE_CANCEL = 4
MIN_BASE_RATE = 10_000

def travel(blocks):
    if blocks:
        boa.env.time_travel(blocks=blocks)


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
        config = make_config(scale, epoch_length=100)
        lane = boa.load(
            "contracts/core/InstantBondLane.vy",
            ripe_hq,
            charlie_token,
            config,
            name="foxtrot_test_lane",
        )

        assert ripe_hq.startAddNewAddressToRegistry(
            lane, "Foxtrot Test Lane", sender=governance.address
        )
        travel(registry_lock)
        lane_reg_id = ripe_hq.confirmNewAddressToRegistry(
            lane, sender=governance.address
        )
        assert lane_reg_id == INSTANT_BOND_LANE_HQ_ID
        ripe_hq.initiateHqConfigChange(
            lane_reg_id, False, True, False, sender=governance.address
        )
        travel(registry_lock)
        assert ripe_hq.confirmHqConfigChange(
            lane_reg_id, sender=governance.address
        )
        lane.pause(False, sender=switchboard_alpha.address)

        foxtrot = boa.load(
            "contracts/config/SwitchboardFoxtrot.vy",
            ripe_hq,
            ZERO_ADDRESS,
            2,
            20,
            name="switchboard_foxtrot",
        )
        assert switchboard.startAddNewAddressToRegistry(
            foxtrot, "Foxtrot", sender=governance.address
        )
        travel(switchboard.registryChangeTimeLock())
        foxtrot_reg_id = switchboard.confirmNewAddressToRegistry(
            foxtrot, sender=governance.address
        )

        foxtrot.startInstantBond(0, 100, sender=governance.address)

        charlie_token.transfer(
            bob,
            10_000 * scale,
            sender=charlie_token_whale,
        )
        charlie_token.approve(lane, MAX_UINT256, sender=bob)

        yield SimpleNamespace(
            lane=lane,
            foxtrot=foxtrot,
            ripe_hq=ripe_hq,
            scale=scale,
            governance=governance,
            bob=bob,
            switchboard_alpha=switchboard_alpha,
            lane_reg_id=lane_reg_id,
            foxtrot_reg_id=foxtrot_reg_id,
            payment_token=charlie_token,
            config=config,
        )


def enable_actions(ctx):
    assert ctx.foxtrot.setActionTimeLockAfterSetup(sender=ctx.governance.address)
    assert ctx.foxtrot.actionTimeLock() == 2


def initialize_lane(ctx, config=None):
    if config is None:
        config = make_config(ctx.scale, epoch_length=ctx.lane.epochLength())
        ctx.lane.setConfig(config, sender=ctx.switchboard_alpha.address)
    quote = ctx.lane.previewBuyNow(ctx.scale, 0, sender=ctx.bob)
    assert quote.available
    ctx.lane.buyNow(
        ctx.scale,
        0,
        quote.epoch,
        quote.totalRipe,
        boa.env.evm.patch.block_number,
        sender=ctx.bob,
    )
    assert ctx.lane.epochState().rate != 0
    return config


def install_override(ctx, target_rate):
    action_id = ctx.foxtrot.setInstantBondRateOverride(
        target_rate,
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
    length = ctx.lane.epochLength()
    offset = (block_number - ctx.lane.genesisBlock()) % length
    travel(length - offset)


def assert_pending_cleared(ctx, action_id):
    assert not ctx.foxtrot.hasPendingAction(action_id)
    assert ctx.foxtrot.actionType(action_id) == 0


def contract_abi():
    compiler_data = boa.load_partial(
        "contracts/config/SwitchboardFoxtrot.vy"
    ).compiler_data
    return build_abi_output(compiler_data)


def test_constructor_does_not_bind_a_lane_address(ripe_hq, governance):
    foxtrot = boa.load(
        "contracts/config/SwitchboardFoxtrot.vy",
        ripe_hq,
        ZERO_ADDRESS,
        2,
        20,
    )
    functions = {
        item["name"] for item in contract_abi() if item.get("type") == "function"
    }
    assert "LANE" not in functions
    assert ripe_hq.getAddr(INSTANT_BOND_LANE_HQ_ID) == ZERO_ADDRESS
    with boa.reverts("invalid lane"):
        foxtrot.startInstantBond(0, 100, sender=governance.address)
    with boa.reverts("invalid lane"):
        foxtrot.stopInstantBond(sender=governance.address)
    with boa.reverts("invalid lane"):
        foxtrot.setCanBuyNow(False, sender=governance.address)


def test_constructor_accepts_the_exact_lane_surface(foxtrot_env):
    assert foxtrot_env.lane_reg_id == INSTANT_BOND_LANE_HQ_ID
    assert (
        foxtrot_env.ripe_hq.getAddr(INSTANT_BOND_LANE_HQ_ID)
        == foxtrot_env.lane.address
    )
    assert foxtrot_env.lane.getRipeHq() == foxtrot_env.ripe_hq.address
    assert foxtrot_env.lane.epochLength() != 0
    assert foxtrot_env.lane.isRunning() is True


def test_rate_override_function_and_event_abi():
    abi = contract_abi()
    functions = {
        item["name"]: item for item in abi if item.get("type") == "function"
    }
    events = {
        item["name"]: item for item in abi if item.get("type") == "event"
    }
    constructor = next(item for item in abi if item.get("type") == "constructor")
    assert [item["name"] for item in constructor["inputs"]] == [
        "_ripeHq",
        "_tempGov",
        "_minConfigTimeLock",
        "_maxConfigTimeLock",
    ]

    assert [item["name"] for item in functions["setInstantBondRateOverride"]["inputs"]] == [
        "_targetRate"
    ]
    assert [item["name"] for item in functions["cancelInstantBondRateOverride"]["inputs"]] == []
    assert [item["name"] for item in functions["startInstantBond"]["inputs"]] == [
        "_genesisBlock",
        "_epochLength",
    ]
    assert [item["name"] for item in functions["setCanBuyNow"]["inputs"]] == [
        "_canBuyNow"
    ]
    assert "setCanPurchaseRipeBond" not in functions
    assert [item["name"] for item in events["InstantBondCanBuyNowSet"]["inputs"]] == [
        "canBuyNow"
    ]

    assert [item["name"] for item in events["PendingRateOverrideSet"]["inputs"]] == [
        "actionId",
        "confirmationBlock",
        "targetRate",
    ]
    assert [item["name"] for item in events["PendingRateOverrideCancellationSet"]["inputs"]] == [
        "actionId",
        "confirmationBlock",
    ]
    assert [item["name"] for item in events["RateOverrideExecuted"]["inputs"]] == ["actionId"]
    assert [item["name"] for item in events["RateOverrideCancellationExecuted"]["inputs"]] == [
        "actionId"
    ]
    assert "InstantBondConfigCancelled" not in events
    assert "RateOverrideActionCancelled" not in events
    assert "LANE" not in functions


def test_initiation_requires_governance_and_valid_config(foxtrot_env, alice):
    ctx = foxtrot_env
    config = make_config(ctx.scale, epoch_length=ctx.lane.epochLength())

    assert ctx.foxtrot.actionTimeLock() == 0
    with boa.reverts("no perms"):
        ctx.foxtrot.setInstantBondConfig(config, sender=alice)
    with boa.reverts("invalid config"):
        ctx.foxtrot.setInstantBondConfig(
            make_config(ctx.scale, epoch_length=ctx.lane.epochLength(), minDownBps=0),
            sender=ctx.governance.address,
        )

    action_id = ctx.foxtrot.setInstantBondConfig(
        config, sender=ctx.governance.address
    )
    pending = filter_logs(ctx.foxtrot, "PendingInstantBondConfigSet")[0]
    assert pending.actionId == action_id
    assert pending.confirmationBlock == boa.env.evm.patch.block_number


def test_pending_config_round_trip_and_execution_readback(foxtrot_env):
    ctx = foxtrot_env
    enable_actions(ctx)
    config = make_config(
        ctx.scale,
        epoch_length=ctx.lane.epochLength(),
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
        minLockDuration=9,
    )

    action_id = ctx.foxtrot.setInstantBondConfig(
        config, sender=ctx.governance.address
    )
    pending_event = filter_logs(ctx.foxtrot, "PendingInstantBondConfigSet")[0]
    pending = ctx.foxtrot.pendingConfig(action_id)

    assert action_id == 1
    assert ctx.foxtrot.actionType(action_id) == ACTION_INSTANT_BOND_CONFIG
    assert tuple(pending) == config
    assert pending_event.minLockDuration == 9
    assert pending_event.epochLength == ctx.lane.epochLength()

    assert not ctx.foxtrot.executePendingAction(
        action_id, sender=ctx.governance.address
    )
    travel(ctx.foxtrot.actionTimeLock())
    assert ctx.foxtrot.executePendingAction(
        action_id, sender=ctx.governance.address
    )
    executed = filter_logs(ctx.foxtrot, "InstantBondConfigExecuted")[-1]
    assert tuple(ctx.lane.bondConfig()) == config
    assert_pending_cleared(ctx, action_id)
    assert executed.actionId == action_id


def test_parallel_config_actions_are_last_write_wins(foxtrot_env):
    ctx = foxtrot_env
    enable_actions(ctx)
    first = make_config(
        ctx.scale,
        epoch_length=ctx.lane.epochLength(),
        seedRate=10**18,
    )
    second = make_config(
        ctx.scale,
        epoch_length=ctx.lane.epochLength(),
        seedRate=11 * 10**17,
    )
    first_id = ctx.foxtrot.setInstantBondConfig(first, sender=ctx.governance.address)
    second_id = ctx.foxtrot.setInstantBondConfig(second, sender=ctx.governance.address)
    travel(ctx.foxtrot.actionTimeLock())
    assert ctx.foxtrot.executePendingAction(second_id, sender=ctx.governance.address)
    assert ctx.lane.bondConfig().seedRate == 11 * 10**17
    assert ctx.foxtrot.executePendingAction(first_id, sender=ctx.governance.address)
    assert ctx.lane.bondConfig().seedRate == 10**18


def test_cancel_permissions_and_clears_action_type(foxtrot_env, alice):
    ctx = foxtrot_env
    enable_actions(ctx)
    config = make_config(ctx.scale, epoch_length=ctx.lane.epochLength())
    action_id = ctx.foxtrot.setInstantBondConfig(config, sender=ctx.governance.address)
    with boa.reverts("no perms"):
        ctx.foxtrot.cancelPendingAction(action_id, sender=alice)
    assert ctx.foxtrot.cancelPendingAction(action_id, sender=ctx.governance.address)
    assert_pending_cleared(ctx, action_id)


def test_expired_execution_auto_cancels(foxtrot_env):
    ctx = foxtrot_env
    enable_actions(ctx)
    config = make_config(ctx.scale, epoch_length=ctx.lane.epochLength())
    action_id = ctx.foxtrot.setInstantBondConfig(config, sender=ctx.governance.address)
    travel(ctx.foxtrot.actionTimeLock() + ctx.foxtrot.expiration())
    assert not ctx.foxtrot.executePendingAction(
        action_id, sender=ctx.governance.address
    )
    assert_pending_cleared(ctx, action_id)


def test_execution_revalidates_budget_after_intervening_purchase(foxtrot_env):
    ctx = foxtrot_env
    enable_actions(ctx)
    initialize_lane(ctx)
    minted = ctx.lane.cumulativeMinted()
    queued = make_config(
        ctx.scale,
        epoch_length=ctx.lane.epochLength(),
        mintBudget=minted + 1,
    )
    action_id = ctx.foxtrot.setInstantBondConfig(
        queued, sender=ctx.governance.address
    )
    ctx.lane.buyNow(
        ctx.scale,
        0,
        ctx.lane.previewBuyNow(ctx.scale, 0, sender=ctx.bob).epoch,
        0,
        boa.env.evm.patch.block_number,
        sender=ctx.bob,
    )
    assert ctx.lane.cumulativeMinted() > minted + 1
    travel(ctx.foxtrot.actionTimeLock())
    with boa.reverts("invalid config"):
        ctx.foxtrot.executePendingAction(action_id, sender=ctx.governance.address)


def test_rate_override_initiation_and_execution(foxtrot_env, alice):
    ctx = foxtrot_env
    target = 11 * 10**17
    assert ctx.foxtrot.actionTimeLock() == 0
    with boa.reverts("no perms"):
        ctx.foxtrot.setInstantBondRateOverride(target, sender=alice)
    with boa.reverts("invalid rate override"):
        ctx.foxtrot.setInstantBondRateOverride(target, sender=ctx.governance.address)

    enable_actions(ctx)
    initialize_lane(ctx)
    with boa.reverts("invalid rate override"):
        ctx.foxtrot.setInstantBondRateOverride(
            MIN_BASE_RATE - 1, sender=ctx.governance.address
        )

    action_id = ctx.foxtrot.setInstantBondRateOverride(
        target, sender=ctx.governance.address
    )
    queued = filter_logs(ctx.foxtrot, "PendingRateOverrideSet")[-1]
    assert queued.targetRate == target
    assert ctx.foxtrot.pendingRateOverride(action_id) == target
    travel(ctx.foxtrot.actionTimeLock())
    assert ctx.foxtrot.executePendingAction(action_id, sender=ctx.governance.address)
    assert ctx.lane.rateOverride() == target
    assert_pending_cleared(ctx, action_id)


def test_rate_override_cancel_round_trip(foxtrot_env, alice):
    ctx = foxtrot_env
    enable_actions(ctx)
    initialize_lane(ctx)
    with boa.reverts("no rate override"):
        ctx.foxtrot.cancelInstantBondRateOverride(sender=ctx.governance.address)

    install_override(ctx, 11 * 10**17)
    with boa.reverts("no perms"):
        ctx.foxtrot.cancelInstantBondRateOverride(sender=alice)

    action_id = ctx.foxtrot.cancelInstantBondRateOverride(
        sender=ctx.governance.address
    )
    assert ctx.foxtrot.actionType(action_id) == ACTION_RATE_OVERRIDE_CANCEL
    travel(ctx.foxtrot.actionTimeLock())
    assert ctx.foxtrot.executePendingAction(action_id, sender=ctx.governance.address)
    executed = filter_logs(ctx.foxtrot, "RateOverrideCancellationExecuted")[-1]
    assert ctx.lane.rateOverride() == 0
    assert executed.actionId == action_id


def test_config_invalidates_installed_override(foxtrot_env):
    ctx = foxtrot_env
    enable_actions(ctx)
    initialize_lane(ctx)
    install_override(ctx, 11 * 10**17)
    config = make_config(
        ctx.scale,
        epoch_length=ctx.lane.epochLength(),
        maxLockBonus=0,
    )
    action_id = ctx.foxtrot.setInstantBondConfig(config, sender=ctx.governance.address)
    travel(ctx.foxtrot.actionTimeLock())
    assert ctx.foxtrot.executePendingAction(action_id, sender=ctx.governance.address)
    assert ctx.lane.rateOverride() == 0


def test_override_applies_only_on_next_successful_rollover(foxtrot_env):
    ctx = foxtrot_env
    enable_actions(ctx)
    initialize_lane(ctx)
    install_override(ctx, 9 * 10**17)
    travel_to_next_lane_epoch(ctx)
    quote = ctx.lane.previewBuyNow(ctx.scale, 0, sender=ctx.bob)
    assert quote.rate == 9 * 10**17
    ctx.lane.buyNow(
        ctx.scale,
        0,
        quote.epoch,
        quote.totalRipe,
        boa.env.evm.patch.block_number,
        sender=ctx.bob,
    )
    assert ctx.lane.epochState().rate == 9 * 10**17
    assert ctx.lane.rateOverride() == 0


def test_start_stop_payment_token_and_cumulative(foxtrot_env, governance):
    ctx = foxtrot_env
    with boa.reverts("already running"):
        ctx.foxtrot.startInstantBond(0, 100, sender=ctx.governance.address)

    ctx.foxtrot.stopInstantBond(sender=ctx.governance.address)
    assert ctx.lane.isRunning() is False

    other = boa.load(
        "contracts/mock/MockErc20.vy",
        governance,
        "Other",
        "OTH",
        8,
        1_000_000,
    )
    ctx.foxtrot.setInstantBondPaymentToken(other.address, sender=ctx.governance.address)
    token_event = filter_logs(ctx.foxtrot, "InstantBondPaymentTokenSet")[-1]
    assert token_event.token == other.address
    assert ctx.lane.paymentDecimals() == 8

    # restore a valid 8-decimal config, then start again
    ctx.lane.setConfig(
        make_config(10**8, epoch_length=ctx.lane.epochLength()),
        sender=ctx.switchboard_alpha.address,
    )
    ctx.foxtrot.startInstantBond(0, ctx.lane.epochLength(), sender=ctx.governance.address)
    assert ctx.lane.isRunning() is True

    ctx.foxtrot.setInstantBondCumulativeMinted(50, sender=ctx.governance.address)
    minted_event = filter_logs(ctx.foxtrot, "InstantBondCumulativeMintedSet")[-1]
    assert minted_event.amount == 50
    assert ctx.lane.cumulativeMinted() == 50

    with boa.reverts("exceeds mint budget"):
        ctx.foxtrot.setInstantBondCumulativeMinted(
            ctx.lane.bondConfig().mintBudget + 1,
            sender=ctx.governance.address,
        )


def test_start_rejects_invalid_length_and_invalid_config(foxtrot_env, governance):
    ctx = foxtrot_env
    ctx.foxtrot.stopInstantBond(sender=ctx.governance.address)
    with boa.reverts("invalid epoch length"):
        ctx.foxtrot.startInstantBond(0, 0, sender=ctx.governance.address)

    other = boa.load(
        "contracts/mock/MockErc20.vy",
        governance,
        "Other",
        "OTH",
        18,
        1,
    )
    ctx.foxtrot.setInstantBondPaymentToken(other.address, sender=ctx.governance.address)
    with boa.reverts("not configured"):
        ctx.foxtrot.startInstantBond(
            0, ctx.lane.epochLength(), sender=ctx.governance.address
        )


def test_foxtrot_cannot_queue_a_different_epoch_length(foxtrot_env):
    ctx = foxtrot_env
    enable_actions(ctx)
    with boa.reverts("invalid config"):
        ctx.foxtrot.setInstantBondConfig(
            make_config(ctx.scale, epoch_length=ctx.lane.epochLength() + 1),
            sender=ctx.governance.address,
        )


def test_immediate_actions_require_governance(foxtrot_env, alice):
    ctx = foxtrot_env
    with boa.reverts("no perms"):
        ctx.foxtrot.stopInstantBond(sender=alice)
    ctx.foxtrot.stopInstantBond(sender=ctx.governance.address)
    with boa.reverts("no perms"):
        ctx.foxtrot.startInstantBond(0, 100, sender=alice)
    with boa.reverts("no perms"):
        ctx.foxtrot.setInstantBondPaymentToken(
            ctx.payment_token.address, sender=alice
        )
    with boa.reverts("no perms"):
        ctx.foxtrot.setInstantBondCumulativeMinted(1, sender=alice)
    with boa.reverts("no perms"):
        ctx.foxtrot.setCanBuyNow(False, sender=alice)
    ctx.foxtrot.startInstantBond(0, 100, sender=ctx.governance.address)


def test_parallel_override_actions_are_last_write_wins(foxtrot_env):
    ctx = foxtrot_env
    enable_actions(ctx)
    initialize_lane(ctx)
    first = ctx.foxtrot.setInstantBondRateOverride(
        8 * 10**17, sender=ctx.governance.address
    )
    second = ctx.foxtrot.setInstantBondRateOverride(
        9 * 10**17, sender=ctx.governance.address
    )
    travel(ctx.foxtrot.actionTimeLock())
    assert ctx.foxtrot.executePendingAction(second, sender=ctx.governance.address)
    assert ctx.lane.rateOverride() == 9 * 10**17
    assert ctx.foxtrot.executePendingAction(first, sender=ctx.governance.address)
    assert ctx.lane.rateOverride() == 8 * 10**17


def test_foxtrot_start_logs_raw_genesis_zero(foxtrot_env):
    ctx = foxtrot_env
    ctx.foxtrot.stopInstantBond(sender=ctx.governance.address)
    length = ctx.lane.epochLength()
    before = boa.env.evm.patch.block_number
    ctx.foxtrot.startInstantBond(0, length, sender=ctx.governance.address)
    foxtrot_event = filter_logs(ctx.foxtrot, "InstantBondStarted")[-1]
    genesis = ctx.lane.genesisBlock()
    assert foxtrot_event.genesisBlock == 0
    assert foxtrot_event.epochLength == length
    assert genesis == before != 0


def test_execute_queued_override_fails_after_stop_and_stays_pending(foxtrot_env):
    ctx = foxtrot_env
    enable_actions(ctx)
    initialize_lane(ctx)
    action_id = ctx.foxtrot.setInstantBondRateOverride(
        9 * 10**17, sender=ctx.governance.address
    )
    ctx.foxtrot.stopInstantBond(sender=ctx.governance.address)
    travel(ctx.foxtrot.actionTimeLock())
    with boa.reverts("invalid rate override"):
        ctx.foxtrot.executePendingAction(action_id, sender=ctx.governance.address)
    assert ctx.foxtrot.hasPendingAction(action_id)
    assert ctx.foxtrot.actionType(action_id) == ACTION_RATE_OVERRIDE_SET
    assert ctx.foxtrot.pendingRateOverride(action_id) == 9 * 10**17
    assert ctx.lane.rateOverride() == 0


def test_execute_queued_override_fails_after_restart_before_first_buy(foxtrot_env):
    ctx = foxtrot_env
    enable_actions(ctx)
    initialize_lane(ctx)
    action_id = ctx.foxtrot.setInstantBondRateOverride(
        9 * 10**17, sender=ctx.governance.address
    )
    ctx.foxtrot.stopInstantBond(sender=ctx.governance.address)
    ctx.foxtrot.startInstantBond(
        0, ctx.lane.epochLength(), sender=ctx.governance.address
    )
    travel(ctx.foxtrot.actionTimeLock())
    with boa.reverts("invalid rate override"):
        ctx.foxtrot.executePendingAction(action_id, sender=ctx.governance.address)
    assert ctx.lane.rateOverride() == 0
    assert ctx.lane.epochState().rate == 0


def test_execute_queued_cancel_fails_after_override_is_consumed(foxtrot_env):
    ctx = foxtrot_env
    enable_actions(ctx)
    initialize_lane(ctx)
    install_override(ctx, 9 * 10**17)
    travel_to_next_lane_epoch(ctx)
    cancel_id = ctx.foxtrot.cancelInstantBondRateOverride(
        sender=ctx.governance.address
    )
    quote = ctx.lane.previewBuyNow(ctx.scale, 0, sender=ctx.bob)
    ctx.lane.buyNow(
        ctx.scale,
        0,
        quote.epoch,
        quote.totalRipe,
        boa.env.evm.patch.block_number,
        sender=ctx.bob,
    )
    assert ctx.lane.rateOverride() == 0
    travel(ctx.foxtrot.actionTimeLock())
    with boa.reverts("no rate override"):
        ctx.foxtrot.executePendingAction(cancel_id, sender=ctx.governance.address)
    assert ctx.foxtrot.hasPendingAction(cancel_id)
    assert ctx.foxtrot.actionType(cancel_id) == ACTION_RATE_OVERRIDE_CANCEL


def test_set_can_buy_now_is_immediate_and_does_not_need_timelock(foxtrot_env, alice):
    ctx = foxtrot_env
    assert ctx.lane.bondConfig().canBuyNow is True
    with boa.reverts("no perms"):
        ctx.foxtrot.setCanBuyNow(False, sender=alice)
    ctx.foxtrot.setCanBuyNow(False, sender=ctx.governance.address)
    assert filter_logs(ctx.foxtrot, "InstantBondCanBuyNowSet")[-1].canBuyNow is False
    assert ctx.lane.bondConfig().canBuyNow is False
    with boa.reverts("disabled"):
        ctx.lane.buyNow(
            ctx.scale,
            0,
            0,
            0,
            boa.env.evm.patch.block_number,
            sender=ctx.bob,
        )
    with boa.reverts("no change"):
        ctx.foxtrot.setCanBuyNow(False, sender=ctx.governance.address)

    ctx.foxtrot.setCanBuyNow(True, sender=ctx.governance.address)
    assert filter_logs(ctx.foxtrot, "InstantBondCanBuyNowSet")[-1].canBuyNow is True
    assert ctx.lane.bondConfig().canBuyNow is True
    quote = ctx.lane.previewBuyNow(ctx.scale, 0, sender=ctx.bob)
    payout = ctx.lane.buyNow(
        ctx.scale,
        0,
        quote.epoch,
        quote.totalRipe,
        boa.env.evm.patch.block_number,
        sender=ctx.bob,
    )
    assert payout == quote.totalRipe


def test_zero_timelock_config_executes_in_the_same_block(foxtrot_env):
    ctx = foxtrot_env
    assert ctx.foxtrot.actionTimeLock() == 0
    config = make_config(
        ctx.scale,
        epoch_length=ctx.lane.epochLength(),
        minLockDuration=7,
    )
    action_id = ctx.foxtrot.setInstantBondConfig(
        config, sender=ctx.governance.address
    )
    assert ctx.foxtrot.executePendingAction(
        action_id, sender=ctx.governance.address
    )
    assert filter_logs(ctx.foxtrot, "InstantBondConfigExecuted")[-1].actionId == action_id
    assert ctx.lane.bondConfig().minLockDuration == 7
    assert_pending_cleared(ctx, action_id)
    assert tuple(ctx.foxtrot.pendingConfig(action_id)) == config


def test_execute_and_cancel_leave_pending_payloads(foxtrot_env):
    ctx = foxtrot_env
    enable_actions(ctx)
    initialize_lane(ctx)
    config = make_config(
        ctx.scale,
        epoch_length=ctx.lane.epochLength(),
        minLockDuration=4,
    )
    config_id = ctx.foxtrot.setInstantBondConfig(
        config, sender=ctx.governance.address
    )
    travel(ctx.foxtrot.actionTimeLock())
    assert ctx.foxtrot.executePendingAction(
        config_id, sender=ctx.governance.address
    )
    assert_pending_cleared(ctx, config_id)
    assert tuple(ctx.foxtrot.pendingConfig(config_id)) == config

    override_id = ctx.foxtrot.setInstantBondRateOverride(
        11 * 10**17, sender=ctx.governance.address
    )
    travel(ctx.foxtrot.actionTimeLock())
    assert ctx.foxtrot.executePendingAction(
        override_id, sender=ctx.governance.address
    )
    assert_pending_cleared(ctx, override_id)
    assert ctx.foxtrot.pendingRateOverride(override_id) == 11 * 10**17

    cancel_id = ctx.foxtrot.cancelInstantBondRateOverride(
        sender=ctx.governance.address
    )
    assert ctx.foxtrot.cancelPendingAction(cancel_id, sender=ctx.governance.address)
    assert_pending_cleared(ctx, cancel_id)
    assert ctx.lane.rateOverride() == 11 * 10**17


def test_unknown_or_cancelled_execute_returns_false(foxtrot_env):
    ctx = foxtrot_env
    enable_actions(ctx)
    assert ctx.foxtrot.executePendingAction(99, sender=ctx.governance.address) is False

    action_id = ctx.foxtrot.setInstantBondConfig(
        make_config(ctx.scale, epoch_length=ctx.lane.epochLength()),
        sender=ctx.governance.address,
    )
    assert ctx.foxtrot.cancelPendingAction(action_id, sender=ctx.governance.address)
    assert ctx.foxtrot.executePendingAction(
        action_id, sender=ctx.governance.address
    ) is False


def test_running_lane_rejects_payment_token_and_double_stop(foxtrot_env, governance):
    ctx = foxtrot_env
    other = boa.load(
        "contracts/mock/MockErc20.vy",
        governance,
        "Other",
        "OTH",
        8,
        1,
    )
    with boa.reverts("invalid payment token"):
        ctx.foxtrot.setInstantBondPaymentToken(
            other.address, sender=ctx.governance.address
        )
    ctx.foxtrot.stopInstantBond(sender=ctx.governance.address)
    with boa.reverts("not running"):
        ctx.foxtrot.stopInstantBond(sender=ctx.governance.address)


def test_foxtrot_follows_the_hq_lane_id(foxtrot_env, charlie_token):
    ctx = foxtrot_env
    original = ctx.lane
    ctx.foxtrot.stopInstantBond(sender=ctx.governance.address)

    replacement = boa.load(
        "contracts/core/InstantBondLane.vy",
        ctx.ripe_hq,
        charlie_token,
        make_config(ctx.scale, epoch_length=100),
        name="foxtrot_replacement_lane",
    )
    replacement.pause(False, sender=ctx.switchboard_alpha.address)
    lock = ctx.ripe_hq.registryChangeTimeLock()
    assert ctx.ripe_hq.startAddressUpdateToRegistry(
        INSTANT_BOND_LANE_HQ_ID,
        replacement,
        sender=ctx.governance.address,
    )
    travel(lock)
    assert ctx.ripe_hq.confirmAddressUpdateToRegistry(
        INSTANT_BOND_LANE_HQ_ID, sender=ctx.governance.address
    )
    assert ctx.ripe_hq.getAddr(INSTANT_BOND_LANE_HQ_ID) == replacement.address

    ctx.foxtrot.startInstantBond(0, 100, sender=ctx.governance.address)
    assert replacement.isRunning() is True
    assert original.isRunning() is False
    assert replacement.genesisBlock() != 0
    assert original.genesisBlock() == 0
