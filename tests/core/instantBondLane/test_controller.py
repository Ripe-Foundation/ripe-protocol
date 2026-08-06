import boa
import pytest

from conf_utils import filter_logs


def controller_rate(rate, accepted, cap, elapsed, config):
    (
        _,
        _,
        _,
        _,
        max_effective_rate,
        _,
        u_high,
        u_low,
        up_bps,
        down_bps,
        decay_bps,
        max_decay_epochs,
        max_lock_bonus,
    ) = config
    ceiling = max_effective_rate * 10_000 // (10_000 + max_lock_bonus)
    rate = min(rate, ceiling)
    utilization = accepted * 10_000 // cap

    if utilization >= u_high:
        rate = max(rate * 10_000 // (10_000 + up_bps), 10_000)
    elif utilization <= u_low:
        rate = min(rate * 10_000 // (10_000 - down_bps), ceiling)

    decay_steps = min(elapsed - 1, max_decay_epochs)
    for _ in range(decay_steps):
        rate = min(rate * 10_000 // (10_000 - decay_bps), ceiling)
    return rate, utilization, decay_steps


@pytest.mark.parametrize(
    "accepted_units, expected_branch",
    [
        (80, "high"),
        (20, "low"),
        (50, "deadband"),
    ],
)
def test_controller_exact_thresholds_and_deadband(
    lane_env, accepted_units, expected_branch
):
    cap = 100 * lane_env.scale
    config = lane_env.set_config(
        paymentCapPerEpoch=cap,
        minPaymentAmount=lane_env.scale,
    )
    amount = accepted_units * lane_env.scale
    lane_env.buy(amount)
    old_rate = lane_env.lane.epochRate()

    boa.env.time_travel(blocks=lane_env.epoch_length)
    quote = lane_env.quote(lane_env.scale)
    expected_rate, utilization, decay_steps = controller_rate(
        old_rate, amount, cap, 1, config
    )

    assert quote.rate == expected_rate
    assert decay_steps == 0
    if expected_branch == "high":
        assert utilization == config[6]
        assert quote.rate < old_rate
    elif expected_branch == "low":
        assert utilization == config[7]
        assert quote.rate > old_rate
    else:
        assert config[7] < utilization < config[6]
        assert quote.rate == old_rate


@pytest.mark.parametrize("elapsed", [1, 2, 5, 40])
def test_sold_epoch_plus_skipped_empty_epochs_apply_bounded_decay(lane_env, elapsed):
    cap = 100 * lane_env.scale
    amount = 50 * lane_env.scale
    config = lane_env.set_config(
        paymentCapPerEpoch=cap,
        minPaymentAmount=lane_env.scale,
        maxDecayEpochs=4,
    )
    lane_env.buy(amount)
    old_rate = lane_env.lane.epochRate()

    boa.env.time_travel(blocks=elapsed * lane_env.epoch_length)
    quote = lane_env.quote(lane_env.scale)
    expected_rate, utilization, decay_steps = controller_rate(
        old_rate, amount, cap, elapsed, config
    )

    assert quote.epoch == elapsed
    assert quote.rate == expected_rate
    assert utilization == 5_000
    assert decay_steps == min(elapsed - 1, 4)

    lane_env.buy(lane_env.scale, expected_epoch=quote.epoch)
    event = filter_logs(lane_env.lane, "EpochRolled")[0]
    assert event.fromEpoch == 0
    assert event.toEpoch == elapsed
    assert event.previousAcceptedPayment == amount
    assert event.previousPaymentCap == cap
    assert event.utilizationBps == utilization
    assert event.decaySteps == decay_steps
    assert event.newRate == expected_rate


def test_paused_disabled_and_budget_exhausted_gaps_follow_same_decay(lane_env):
    cap = 100 * lane_env.scale
    amount = 50 * lane_env.scale
    config = lane_env.set_config(paymentCapPerEpoch=cap)
    lane_env.buy(amount)
    old_rate = lane_env.lane.epochRate()

    lane_env.lane.pause(True, sender=lane_env.switchboard.address)
    boa.env.time_travel(blocks=3 * lane_env.epoch_length)
    paused_quote = lane_env.quote(lane_env.scale)
    expected, _, _ = controller_rate(old_rate, amount, cap, 3, config)
    assert paused_quote.rate == expected
    assert not paused_quote.available

    lane_env.lane.pause(False, sender=lane_env.switchboard.address)
    disabled_config = lane_env.set_config(canBuyNow=False)
    boa.env.time_travel(blocks=2 * lane_env.epoch_length)
    disabled_quote = lane_env.quote(lane_env.scale)
    expected, _, _ = controller_rate(old_rate, amount, cap, 5, disabled_config)
    assert disabled_quote.rate == expected
    assert not disabled_quote.available

    minted = lane_env.lane.cumulativeMinted()
    exhausted_config = lane_env.set_config(canBuyNow=True, mintBudget=minted)
    boa.env.time_travel(blocks=2 * lane_env.epoch_length)
    exhausted_quote = lane_env.quote(lane_env.scale)
    expected, _, _ = controller_rate(old_rate, amount, cap, 7, exhausted_config)
    assert exhausted_quote.rate == expected
    assert not exhausted_quote.available


def test_first_purchase_many_epochs_after_genesis_uses_seed_without_decay(lane_factory):
    ctx = lane_factory(start_at_genesis=False, genesis_delay=5)
    config = ctx.set_config(seedRate=777_777_777_777_777_777)
    target_epoch = 9
    target_block = ctx.genesis + target_epoch * ctx.epoch_length
    boa.env.time_travel(blocks=target_block - boa.env.evm.patch.block_number)

    quote = ctx.quote(ctx.scale)
    assert quote.epoch == target_epoch
    assert quote.rate == config[5]
    assert quote.pricingConfigVersion == 1
    assert not ctx.lane.isInitialized()

    ctx.buy(ctx.scale, expected_epoch=target_epoch)
    assert ctx.lane.currentEpoch() == target_epoch
    assert ctx.lane.epochRate() == config[5]


def test_repeated_high_utilization_saturates_at_min_base_rate(lane_env):
    config = lane_env.set_config(
        paymentCapPerEpoch=lane_env.scale,
        minPaymentAmount=lane_env.scale,
        maxEffectiveRate=2 * 10**18,
        seedRate=10**18,
        uHighBps=10_000,
        uLowBps=0,
        upBps=10_000,
        downBps=1,
        decayBps=1,
        maxDecayEpochs=1,
        maxLockBonus=0,
    )

    rates = []
    for _ in range(55):
        quote = lane_env.quote(lane_env.scale)
        rates.append(quote.rate)
        assert quote.rate >= 10_000
        lane_env.buy(lane_env.scale, expected_epoch=quote.epoch)
        boa.env.time_travel(blocks=lane_env.epoch_length)

    final_quote = lane_env.quote(lane_env.scale)
    assert final_quote.rate == 10_000
    assert all(next_rate <= rate for rate, next_rate in zip(rates, rates[1:]))
    assert lane_env.lane.cumulativeMinted() <= config[3]


def test_low_utilization_strictly_recovers_sub_ceiling_rate(lane_env):
    cap = 100 * lane_env.scale
    lane_env.set_config(
        paymentCapPerEpoch=cap,
        minPaymentAmount=lane_env.scale,
        maxEffectiveRate=10**18,
        seedRate=10_000,
        uHighBps=8_000,
        uLowBps=100,
        upBps=2,
        downBps=1,
        decayBps=1,
        maxLockBonus=0,
    )
    lane_env.buy(lane_env.scale)
    boa.env.time_travel(blocks=lane_env.epoch_length)

    quote = lane_env.quote(lane_env.scale)
    assert quote.rate == 10_001
    assert quote.rate > lane_env.lane.epochRate()


def test_tighter_ceiling_clamps_at_rollover_and_looser_ceiling_does_not_reset(lane_env):
    cap = 100 * lane_env.scale
    lane_env.set_config(
        paymentCapPerEpoch=cap,
        maxLockBonus=0,
        seedRate=10**18,
        maxEffectiveRate=2 * 10**18,
    )
    lane_env.buy(50 * lane_env.scale)

    lane_env.set_config(
        paymentCapPerEpoch=cap,
        maxLockBonus=0,
        seedRate=5 * 10**17,
        maxEffectiveRate=5 * 10**17,
    )
    boa.env.time_travel(blocks=lane_env.epoch_length)
    tight = lane_env.quote(50 * lane_env.scale)
    assert tight.rate == 5 * 10**17
    lane_env.buy(50 * lane_env.scale, expected_epoch=tight.epoch)

    lane_env.set_config(
        paymentCapPerEpoch=cap,
        maxLockBonus=0,
        seedRate=2 * 10**18,
        maxEffectiveRate=3 * 10**18,
    )
    boa.env.time_travel(blocks=lane_env.epoch_length)
    loose = lane_env.quote(lane_env.scale)
    assert loose.rate == tight.rate


def test_minimum_purchase_cannot_select_stronger_step_than_empty_decay(lane_env):
    cap = 100 * lane_env.scale
    config = lane_env.set_config(
        paymentCapPerEpoch=cap,
        minPaymentAmount=lane_env.scale,
        uLowBps=100,
        downBps=100,
        decayBps=500,
    )
    lane_env.buy(lane_env.scale)
    old_rate = lane_env.lane.epochRate()
    boa.env.time_travel(blocks=lane_env.epoch_length)

    quote = lane_env.quote(lane_env.scale)
    low_step = old_rate * 10_000 // (10_000 - config[9])
    empty_step = old_rate * 10_000 // (10_000 - config[10])
    assert low_step < empty_step
    assert quote.rate == low_step


def test_maximum_decay_loop_bound_executes_all_32_steps(lane_env):
    cap = 100 * lane_env.scale
    amount = 50 * lane_env.scale
    config = lane_env.set_config(
        paymentCapPerEpoch=cap,
        minPaymentAmount=lane_env.scale,
        maxDecayEpochs=32,
    )
    lane_env.buy(amount)
    old_rate = lane_env.lane.epochRate()

    elapsed = 40
    boa.env.time_travel(blocks=elapsed * lane_env.epoch_length)
    quote = lane_env.quote(lane_env.scale)
    expected_rate, utilization, decay_steps = controller_rate(
        old_rate,
        amount,
        cap,
        elapsed,
        config,
    )

    assert decay_steps == 32
    assert quote.rate == expected_rate
    lane_env.buy(lane_env.scale, expected_epoch=quote.epoch)
    event = filter_logs(lane_env.lane, "EpochRolled")[0]
    assert event.utilizationBps == utilization
    assert event.decaySteps == 32
    assert event.newRate == expected_rate
