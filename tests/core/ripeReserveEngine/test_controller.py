import boa
import pytest

from conf_utils import filter_logs

from tests.core.ripeReserveEngine.conftest import controller_rate


@pytest.mark.parametrize(
    "accepted_units, branch",
    [
        (80, "high"),
        (20, "low"),
        (50, "deadband"),
    ],
)
def test_controller_exact_thresholds_and_deadband(lane_env, accepted_units, branch):
    cap = 100 * lane_env.scale
    config = lane_env.set_config(
        paymentCapPerEpoch=cap,
        minPaymentAmount=lane_env.scale,
    )
    amount = accepted_units * lane_env.scale
    lane_env.buy(amount)
    old_rate = lane_env.lane.epochState().basePayoutRate
    boa.env.time_travel(blocks=lane_env.epoch_length)
    quote = lane_env.quote(lane_env.scale)
    expected, utilization, _, _ = controller_rate(
        old_rate,
        amount,
        cap,
        1,
        config,
    )
    assert quote.basePayoutRate == expected
    if branch == "high":
        assert utilization >= 8_000
        assert quote.basePayoutRate < old_rate
    elif branch == "low":
        assert utilization <= 2_000
        assert quote.basePayoutRate > old_rate
    else:
        assert 2_000 < utilization < 8_000
        assert quote.basePayoutRate == old_rate
    lane_env.buy(lane_env.scale)
    rolled = filter_logs(lane_env.lane, "EpochRolled")[-1]
    assert rolled.controllerBasePayoutRate == expected
    assert rolled.newBasePayoutRate == expected


def test_high_utilization_lowers_rate(lane_env):
    cap = 100 * lane_env.scale
    config = lane_env.set_config(
        paymentCapPerEpoch=cap,
        minPaymentAmount=lane_env.scale,
    )
    lane_env.buy(80 * lane_env.scale)
    old = lane_env.lane.epochState().basePayoutRate
    boa.env.time_travel(blocks=lane_env.epoch_length)
    quote = lane_env.quote(lane_env.scale)
    expected, _, _, _ = controller_rate(old, 80 * lane_env.scale, cap, 1, config)
    assert quote.basePayoutRate == expected
    assert quote.basePayoutRate < old


def test_low_utilization_raises_rate(lane_env):
    cap = 100 * lane_env.scale
    config = lane_env.set_config(
        paymentCapPerEpoch=cap,
        minPaymentAmount=lane_env.scale,
    )
    lane_env.buy(20 * lane_env.scale)
    old = lane_env.lane.epochState().basePayoutRate
    boa.env.time_travel(blocks=lane_env.epoch_length)
    quote = lane_env.quote(lane_env.scale)
    expected, _, _, _ = controller_rate(old, 20 * lane_env.scale, cap, 1, config)
    assert quote.basePayoutRate == expected
    assert quote.basePayoutRate > old


def test_deadband_keeps_rate(lane_env):
    cap = 100 * lane_env.scale
    config = lane_env.set_config(
        paymentCapPerEpoch=cap,
        minPaymentAmount=lane_env.scale,
    )
    lane_env.buy(50 * lane_env.scale)
    old = lane_env.lane.epochState().basePayoutRate
    boa.env.time_travel(blocks=lane_env.epoch_length)
    quote = lane_env.quote(lane_env.scale)
    expected, _, _, _ = controller_rate(old, 50 * lane_env.scale, cap, 1, config)
    assert quote.basePayoutRate == expected == old


def test_skipped_empty_epochs_apply_bounded_decay(lane_env):
    cap = 100 * lane_env.scale
    config = lane_env.set_config(
        paymentCapPerEpoch=cap,
        minPaymentAmount=lane_env.scale,
        maxDecayEpochs=4,
    )
    lane_env.buy(50 * lane_env.scale)
    old = lane_env.lane.epochState().basePayoutRate
    boa.env.time_travel(blocks=40 * lane_env.epoch_length)
    quote = lane_env.quote(lane_env.scale)
    expected, _, decay_steps, _ = controller_rate(
        old, 50 * lane_env.scale, cap, 40, config
    )
    assert decay_steps == 4
    assert quote.basePayoutRate == expected
    assert quote.epoch == 40


def test_first_purchase_many_epochs_after_genesis_uses_seed(lane_factory):
    ctx = lane_factory(auto_start=False)
    ctx.start(0)
    boa.env.time_travel(blocks=25 * ctx.epoch_length)
    quote = ctx.quote(ctx.scale)
    assert quote.epoch == 25
    assert quote.basePayoutRate == ctx.lane.engineConfig().seedBasePayoutRate
    ctx.buy(ctx.scale)
    assert ctx.lane.epochState().basePayoutRate == ctx.lane.engineConfig().seedBasePayoutRate
    assert ctx.lane.epochState().epoch == 25


def test_tighter_ceiling_clamps_at_rollover(lane_env):
    lane_env.buy(lane_env.scale)
    old = lane_env.lane.epochState().basePayoutRate
    ceiling_config = lane_env.set_config(
        maxAllInPayoutRate=15_000,
        maxVestingBonus=0,
        seedBasePayoutRate=10_000,
    )
    boa.env.time_travel(blocks=lane_env.epoch_length)
    quote = lane_env.quote(lane_env.scale)
    expected, _, _, _ = controller_rate(
        old,
        lane_env.scale,
        ceiling_config[0],
        1,
        ceiling_config,
    )
    assert quote.basePayoutRate == expected
    assert quote.basePayoutRate <= 15_000


def test_weighted_lateness_is_amount_weighted(lane_env):
    cap = 100 * lane_env.scale
    lane_env.set_config(paymentCapPerEpoch=cap, minPaymentAmount=lane_env.scale)
    early = 10 * lane_env.scale
    lane_env.buy(early)
    boa.env.time_travel(blocks=lane_env.epoch_length - 1)
    late = 10 * lane_env.scale
    lane_env.buy(late)
    state = lane_env.lane.epochState()
    assert state.acceptedPayment == early + late
    # late fill should dominate lateness vs two early fills of the same total
    assert state.weightedLateness == late * 10_000


def test_single_block_epoch_has_zero_lateness(lane_factory):
    ctx = lane_factory(epoch_length=1)
    ctx.buy(ctx.scale)
    assert ctx.lane.epochState().weightedLateness == 0
    boa.env.time_travel(blocks=1)
    quote = ctx.quote(ctx.scale)
    assert quote.available is True


def test_lateness_at_first_and_last_block(lane_env):
    cap = 100 * lane_env.scale
    lane_env.set_config(paymentCapPerEpoch=cap, minPaymentAmount=lane_env.scale)
    lane_env.buy(lane_env.scale)
    assert lane_env.lane.epochState().weightedLateness == 0

    lane_env.stop()
    lane_env.start(0)
    boa.env.time_travel(blocks=lane_env.epoch_length - 1)
    lane_env.buy(lane_env.scale)
    assert lane_env.lane.epochState().weightedLateness == 10_000 * lane_env.scale


def test_partial_first_epoch_is_not_timing_eligible(lane_factory):
    ctx = lane_factory(auto_start=False)
    ctx.start(0)
    boa.env.time_travel(blocks=1)
    ctx.buy(ctx.scale)
    assert ctx.lane.epochState().timingEligible is False
    assert ctx.lane.epochState().epoch == 0
