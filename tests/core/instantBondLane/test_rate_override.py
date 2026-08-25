import boa

from conf_utils import filter_logs
from tests.core.instantBondLane.conftest import controller_rate


def _next_epoch(ctx):
    offset = (
        boa.env.evm.patch.block_number - ctx.lane.genesisBlock()
    ) % ctx.lane.epochLength()
    boa.env.time_travel(blocks=ctx.lane.epochLength() - offset)


def test_override_requires_running_valid_rate_and_governance(lane_factory, alice):
    ctx = lane_factory(auto_start=False)
    assert ctx.lane.isValidRateOverride(10**18, 0) is False
    with boa.reverts("no perms"):
        ctx.lane.setRateOverride(10**18, 0, sender=alice)

    ctx.start(0)
    assert ctx.lane.isValidRateOverride(9_999, 0) is False
    ceiling = (
        ctx.lane.engineConfig().maxAllInPayoutRate
        * 10_000
        // (10_000 + ctx.lane.engineConfig().maxVestingBonus)
    )
    assert ctx.lane.isValidRateOverride(ceiling, 0) is True
    assert ctx.lane.isValidRateOverride(ceiling + 1, 0) is False
    with boa.reverts("invalid rate override"):
        ctx.lane.setRateOverride(ceiling + 1, 0, sender=ctx.switchboard.address)


def test_zero_target_before_genesis_resolves_first_epoch(lane_factory):
    ctx = lane_factory(auto_start=False)
    future = boa.env.evm.patch.block_number + 50
    ctx.start(future)
    resolved = ctx.set_rate_override(9 * 10**17, 0)
    event = filter_logs(ctx.lane, "RateOverrideInstalled")[-1]
    assert resolved == 0
    assert ctx.lane.overrideTargetEpoch() == 0
    assert event.targetEpoch == 0
    assert event.targetBasePayoutRate == 9 * 10**17


def test_zero_target_uses_current_epoch_when_uncommitted(lane_env):
    target = 9 * 10**17
    resolved = lane_env.set_rate_override(target, 0)
    assert resolved == 0
    preview = lane_env.quote(lane_env.scale)
    assert preview.basePayoutRate == target
    assert preview.rateSource == lane_env.lane.RATE_SOURCE_OVERRIDE()
    assert lane_env.lane.overrideTargetBasePayoutRate() == target

    lane_env.buy(lane_env.scale)
    applied = filter_logs(lane_env.lane, "RateOverrideApplied")[-1]
    initialized = filter_logs(lane_env.lane, "EpochInitialized")[-1]
    assert applied.fromEpoch == 0
    assert applied.toEpoch == 0
    assert applied.targetBasePayoutRate == target
    assert initialized.basePayoutRate == target
    assert initialized.rateSource == lane_env.lane.RATE_SOURCE_OVERRIDE()
    assert lane_env.lane.overrideTargetBasePayoutRate() == 0
    assert lane_env.lane.overrideTargetEpoch() == 0


def test_zero_target_after_purchase_resolves_next_epoch(lane_env):
    lane_env.buy(lane_env.scale)
    target = 9 * 10**17
    resolved = lane_env.set_rate_override(target, 0)
    assert resolved == 1
    assert lane_env.lane.overrideTargetEpoch() == 1
    assert lane_env.quote(lane_env.scale).rateSource != lane_env.lane.RATE_SOURCE_OVERRIDE()

    _next_epoch(lane_env)
    preview = lane_env.quote(lane_env.scale)
    assert preview.epoch == 1
    assert preview.basePayoutRate == target
    assert lane_env.lane.overrideTargetBasePayoutRate() == target
    lane_env.buy(lane_env.scale)
    assert lane_env.lane.epochState().basePayoutRate == target
    assert lane_env.lane.overrideTargetBasePayoutRate() == 0


def test_explicit_current_epoch_allowed_only_before_commit(lane_env):
    target = 9 * 10**17
    boa.env.time_travel(blocks=lane_env.epoch_length)
    assert lane_env.lane.isValidRateOverride(target, 1) is True
    lane_env.buy(lane_env.scale)
    assert lane_env.lane.isValidRateOverride(target, 1) is False
    assert lane_env.lane.isValidRateOverride(target, 2) is True


def test_only_one_override_can_be_installed(lane_env):
    lane_env.set_rate_override(9 * 10**17, 1)
    assert lane_env.lane.isValidRateOverride(8 * 10**17, 2) is False
    with boa.reverts("invalid rate override"):
        lane_env.set_rate_override(8 * 10**17, 2)


def test_future_override_is_not_consumed_by_earlier_epochs(lane_env):
    target = 9 * 10**17
    lane_env.set_rate_override(target, 2)
    lane_env.buy(lane_env.scale)
    assert lane_env.lane.overrideTargetEpoch() == 2
    _next_epoch(lane_env)
    assert lane_env.quote(lane_env.scale).rateSource == lane_env.lane.RATE_SOURCE_CONTROLLER()
    lane_env.buy(lane_env.scale)
    assert lane_env.lane.overrideTargetEpoch() == 2
    _next_epoch(lane_env)
    assert lane_env.quote(lane_env.scale).basePayoutRate == target
    lane_env.buy(lane_env.scale)
    assert lane_env.lane.overrideTargetBasePayoutRate() == 0


def test_override_missed_when_first_later_purchase_skips_target(lane_env):
    target = 9 * 10**17
    lane_env.buy(lane_env.scale)
    lane_env.set_rate_override(target, 1)
    boa.env.time_travel(blocks=3 * lane_env.epoch_length)
    preview = lane_env.quote(lane_env.scale)
    assert preview.epoch == 3
    assert preview.rateSource == lane_env.lane.RATE_SOURCE_CONTROLLER()
    assert preview.basePayoutRate != target

    lane_env.buy(lane_env.scale)
    missed = filter_logs(lane_env.lane, "RateOverrideMissed")[-1]
    assert missed.targetEpoch == 1
    assert missed.committedEpoch == 3
    assert missed.targetBasePayoutRate == target
    assert lane_env.lane.overrideTargetBasePayoutRate() == 0


def test_applied_override_is_next_controller_historical_start(lane_env):
    cap = 100 * lane_env.scale
    config = lane_env.set_config(
        paymentCapPerEpoch=cap,
        minPaymentAmount=lane_env.scale,
    )
    lane_env.buy(50 * lane_env.scale)
    target = 9 * 10**17
    lane_env.set_rate_override(target, 1)
    _next_epoch(lane_env)
    lane_env.buy(50 * lane_env.scale)
    assert lane_env.lane.epochState().basePayoutRate == target

    _next_epoch(lane_env)
    expected, _, _, _ = controller_rate(
        target,
        50 * lane_env.scale,
        cap,
        1,
        config,
    )
    quote = lane_env.quote(lane_env.scale)
    assert quote.controllerBasePayoutRate == expected
    assert quote.basePayoutRate == expected


def test_cancel_is_immediate_and_preserves_target_in_event(lane_env):
    target = 9 * 10**17
    lane_env.set_rate_override(target, 2)
    lane_env.cancel_rate_override()
    event = filter_logs(lane_env.lane, "RateOverrideCancelled")[-1]
    assert event.targetEpoch == 2
    assert event.targetBasePayoutRate == target
    assert lane_env.lane.overrideTargetBasePayoutRate() == 0
    assert lane_env.lane.overrideTargetEpoch() == 0
    with boa.reverts("no override"):
        lane_env.cancel_rate_override()


def test_controller_config_and_stop_invalidate_override(lane_env):
    target = 9 * 10**17
    lane_env.set_rate_override(target, 2)
    lane_env.set_config(maxVestingBonus=0)
    event = filter_logs(lane_env.lane, "RateOverrideInvalidated")[-1]
    assert event.targetEpoch == 2
    assert event.targetBasePayoutRate == target

    lane_env.set_rate_override(target, 2)
    lane_env.stop()
    event = filter_logs(lane_env.lane, "RateOverrideInvalidated")[-1]
    assert event.targetEpoch == 2
    assert lane_env.lane.overrideTargetBasePayoutRate() == 0


def test_pause_and_purchase_disable_do_not_mutate_installed_override(lane_env):
    target = 9 * 10**17
    lane_env.set_rate_override(target, 2)
    lane_env.lane.pause(True, sender=lane_env.switchboard.address)
    lane_env.lane.setCanAcquireRipe(False, sender=lane_env.switchboard.address)
    assert lane_env.lane.overrideTargetBasePayoutRate() == target
    assert lane_env.lane.overrideTargetEpoch() == 2
