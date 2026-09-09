import boa
import pytest

from conf_utils import filter_logs, get_boa_dev_reasons

from tests.core.ripeReserveEngine.conftest import (
    MIN_BASE_PAYOUT_RATE,
    controller_rate,
)


def test_fractional_token_minimum_is_valid_and_enforced(lane_env):
    cap = 10 * lane_env.scale
    minimum = lane_env.scale // 10
    lane_env.set_config(paymentCapPerEpoch=cap, minPaymentAmount=minimum)

    quote = lane_env.quote(minimum)
    assert quote.available is True
    assert quote.minPaymentAmount == minimum
    assert quote.totalRipe > 0
    assert lane_env.buy(minimum) == quote.totalRipe

    below_minimum = minimum - 1
    assert lane_env.quote(below_minimum).available is False
    with pytest.raises(boa.BoaError) as err:
        lane_env.buy(below_minimum)
    assert "below minimum payment" in get_boa_dev_reasons(err.value)


def test_minimum_payment_always_produces_ripe_at_minimum_rate(lane_env):
    minimum = (
        lane_env.scale + MIN_BASE_PAYOUT_RATE - 1
    ) // MIN_BASE_PAYOUT_RATE
    common = {
        "maxAllInPayoutRate": MIN_BASE_PAYOUT_RATE,
        "seedBasePayoutRate": MIN_BASE_PAYOUT_RATE,
        "maxVestingBonus": 0,
    }
    invalid = lane_env.make_config(
        minPaymentAmount=minimum - 1,
        **common,
    )
    assert lane_env.lane.isValidConfig(invalid) is False
    with boa.reverts("invalid config"):
        lane_env.lane.setConfig(
            invalid,
            sender=lane_env.switchboard.address,
        )

    lane_env.set_config(minPaymentAmount=minimum, **common)
    quote = lane_env.quote(minimum)
    assert quote.available is True
    assert quote.baseRipe == 1
    assert quote.totalRipe == 1
    assert lane_env.buy(minimum) == 1


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
