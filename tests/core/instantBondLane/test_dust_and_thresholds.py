import boa
import pytest

from conf_utils import filter_logs, get_boa_dev_reasons

from tests.core.instantBondLane.conftest import controller_rate


def test_remainder_below_min_payment_is_unbuyable(lane_env):
    cap = 100 * lane_env.scale
    minimum = 10 * lane_env.scale
    lane_env.set_config(paymentCapPerEpoch=cap, minPaymentAmount=minimum)
    lane_env.buy(95 * lane_env.scale)

    remaining = lane_env.quote(minimum).remainingPayment
    assert remaining == 5 * lane_env.scale

    too_small = lane_env.quote(5 * lane_env.scale)
    assert too_small.available is False
    assert too_small.totalRipe > 0
    assert too_small.basePayoutRate == lane_env.lane.epochState().basePayoutRate

    too_big = lane_env.quote(minimum)
    assert too_big.available is False
    assert too_big.totalRipe > 0

    with pytest.raises(boa.BoaError) as err:
        lane_env.buy(5 * lane_env.scale)
    assert "below minimum payment" in get_boa_dev_reasons(err.value)
    with pytest.raises(boa.BoaError) as err:
        lane_env.buy(minimum)
    assert "exceeds available amount" in get_boa_dev_reasons(err.value)


def test_remainder_exactly_at_min_payment_is_still_buyable(lane_env):
    cap = 100 * lane_env.scale
    minimum = 10 * lane_env.scale
    lane_env.set_config(paymentCapPerEpoch=cap, minPaymentAmount=minimum)
    lane_env.buy(90 * lane_env.scale)
    last = lane_env.quote(minimum)
    assert last.available is True
    assert last.remainingPayment == minimum
    assert lane_env.buy(minimum) == last.totalRipe
    assert lane_env.lane.epochState().acceptedPayment == cap
    assert lane_env.quote(minimum).remainingPayment == 0


@pytest.mark.parametrize(
    "accepted_units, expected_branch",
    [
        (19, "low"),
        (20, "low"),
        (21, "deadband"),
        (79, "deadband"),
        (80, "high"),
        (81, "high"),
    ],
)
def test_controller_uses_inclusive_high_and_low_thresholds(
    lane_env, accepted_units, expected_branch
):
    cap = 100 * lane_env.scale
    config = lane_env.set_config(
        paymentCapPerEpoch=cap,
        minPaymentAmount=lane_env.scale,
        uHighBps=8_000,
        uLowBps=2_000,
    )
    amount = accepted_units * lane_env.scale
    lane_env.buy(amount)
    old = lane_env.lane.epochState().basePayoutRate
    boa.env.time_travel(blocks=lane_env.epoch_length)
    quote = lane_env.quote(lane_env.scale)
    expected, utilization, _, _ = controller_rate(old, amount, cap, 1, config)

    assert quote.basePayoutRate == expected
    if expected_branch == "high":
        assert utilization >= 8_000
        assert quote.basePayoutRate < old
    elif expected_branch == "low":
        assert utilization <= 2_000
        assert quote.basePayoutRate > old
    else:
        assert 2_000 < utilization < 8_000
        assert quote.basePayoutRate == old

    lane_env.buy(lane_env.scale)
    rolled = filter_logs(lane_env.lane, "EpochRolled")[-1]
    assert rolled.utilizationBps == utilization
    assert rolled.controllerBasePayoutRate == expected


def test_weighted_lateness_matches_amount_times_offset(lane_env):
    cap = 100 * lane_env.scale
    lane_env.set_config(paymentCapPerEpoch=cap, minPaymentAmount=lane_env.scale)
    early = 10 * lane_env.scale
    late = 30 * lane_env.scale
    lane_env.buy(early)
    boa.env.time_travel(blocks=50)
    lane_env.buy(late)

    lateness = 50 * 10_000 // (lane_env.epoch_length - 1)
    state = lane_env.lane.epochState()
    assert state.acceptedPayment == early + late
    assert state.weightedLateness == late * lateness
