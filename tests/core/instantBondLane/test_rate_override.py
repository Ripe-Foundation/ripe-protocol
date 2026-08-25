import boa
import pytest

from conf_utils import filter_logs, get_boa_dev_reasons


def test_override_requires_running_committed_epoch(lane_factory, alice):
    ctx = lane_factory(auto_start=False)
    assert ctx.lane.isValidRateOverride(10**18) is False
    ctx.start(0)
    assert ctx.lane.isValidRateOverride(10**18) is False
    ctx.buy(ctx.scale)
    assert ctx.lane.isValidRateOverride(10**18) is True
    assert ctx.lane.isValidRateOverride(9_999) is False

    with boa.reverts("no perms"):
        ctx.lane.setRateOverride(10**18, sender=alice)
    with boa.reverts("invalid rate override"):
        ctx.lane.setRateOverride(9_999, sender=ctx.switchboard.address)


def test_override_is_one_shot_on_next_rollover(lane_env):
    lane_env.buy(lane_env.scale)
    target = 9 * 10**17
    lane_env.set_rate_override(target)
    logs = filter_logs(lane_env.lane, "RateOverrideInstalled")
    assert logs[-1].targetRate == target
    assert lane_env.lane.rateOverride() == target
    assert lane_env.lane.overrideTargetBasePayoutRate() != 0

    same_epoch = lane_env.quote(lane_env.scale)
    assert same_epoch.rate == lane_env.lane.epochState().rate

    boa.env.time_travel(blocks=lane_env.epoch_length)
    preview = lane_env.quote(lane_env.scale)
    assert preview.rate == target
    assert lane_env.lane.rateOverride() == target

    lane_env.buy(lane_env.scale)
    applied = filter_logs(lane_env.lane, "RateOverrideApplied")
    rolled = filter_logs(lane_env.lane, "EpochRolled")
    assert applied[-1].targetRate == target
    assert applied[-1].controllerRate == rolled[-1].controllerRate
    assert rolled[-1].newRate == target
    assert lane_env.lane.epochState().rate == target
    assert lane_env.lane.rateOverride() == 0
    assert lane_env.lane.overrideTargetBasePayoutRate() == 0


def test_override_cancel_and_config_invalidation(lane_env):
    lane_env.buy(lane_env.scale)
    lane_env.set_rate_override(9 * 10**17)
    lane_env.cancel_rate_override()
    logs = filter_logs(lane_env.lane, "RateOverrideCancelled")
    assert logs[-1].targetRate == 9 * 10**17
    assert lane_env.lane.rateOverride() == 0

    with pytest.raises(boa.BoaError) as err:
        lane_env.cancel_rate_override()
    assert "no override" in get_boa_dev_reasons(err.value)

    lane_env.set_rate_override(8 * 10**17)
    lane_env.set_config(maxLockBonus=0)
    invalidated = filter_logs(lane_env.lane, "RateOverrideInvalidated")
    assert invalidated[-1].targetRate == 8 * 10**17
    assert lane_env.lane.rateOverride() == 0


def test_override_survives_skipped_epochs_and_applies_once(lane_env):
    lane_env.buy(lane_env.scale)
    target = 9 * 10**17
    lane_env.set_rate_override(target)
    boa.env.time_travel(blocks=7 * lane_env.epoch_length)
    quote = lane_env.quote(lane_env.scale)
    assert quote.rate == target
    assert lane_env.lane.rateOverride() == target
    lane_env.buy(lane_env.scale)
    assert lane_env.lane.epochState().rate == target
    assert lane_env.lane.rateOverride() == 0
    boa.env.time_travel(blocks=lane_env.epoch_length)
    assert lane_env.quote(lane_env.scale).rate != target


def test_override_above_ceiling_is_rejected(lane_env):
    lane_env.buy(lane_env.scale)
    lane_env.set_config(maxEffectiveRate=15_000, maxLockBonus=0, seedRate=10_000)
    assert lane_env.lane.isValidRateOverride(15_001) is False
    with boa.reverts("invalid rate override"):
        lane_env.set_rate_override(15_001)


def test_stop_and_start_clear_override(lane_env):
    lane_env.buy(lane_env.scale)
    lane_env.set_rate_override(9 * 10**17)
    lane_env.stop()
    assert lane_env.lane.rateOverride() == 0
    lane_env.start(0)
    assert lane_env.lane.isValidRateOverride(9 * 10**17) is False
