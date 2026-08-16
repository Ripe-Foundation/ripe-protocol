import boa
import pytest

from conf_utils import filter_logs


def controller_rate(
    rate,
    accepted,
    cap,
    elapsed,
    config,
    weighted_lateness=0,
    timing_eligible=True,
):
    (
        _,
        _,
        _,
        _,
        max_effective_rate,
        _,
        u_high,
        u_low,
        min_up_bps,
        max_up_bps,
        min_down_bps,
        max_down_bps,
        decay_bps,
        max_decay_epochs,
        max_lock_bonus,
    ) = config
    ceiling = max_effective_rate * 10_000 // (10_000 + max_lock_bonus)
    rate = min(rate, ceiling)
    utilization = accepted * 10_000 // cap

    if utilization >= u_high:
        utilization_strength = (utilization - u_high) * 10_000 // (10_000 - u_high)
        earliness = 0
        if timing_eligible:
            earliness = 10_000 - weighted_lateness // accepted
        demand_strength = utilization_strength * earliness // 10_000
        step = min_up_bps + (max_up_bps - min_up_bps) * demand_strength // 10_000
        rate = max(rate * 10_000 // (10_000 + step), 10_000)
    elif utilization <= u_low:
        weakness = (u_low - utilization) * 10_000 // u_low
        step = min_down_bps + (max_down_bps - min_down_bps) * weakness // 10_000
        rate = min(rate * 10_000 // (10_000 - step), ceiling)

    decay_steps = min(elapsed - 1, max_decay_epochs)
    for _ in range(decay_steps):
        rate = min(rate * 10_000 // (10_000 - decay_bps), ceiling)
    return rate, utilization, decay_steps


def lateness_bps(offset, epoch_length):
    if epoch_length == 1:
        return 0
    return offset * 10_000 // (epoch_length - 1)


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


def test_minimum_up_step_followed_by_empty_decay_cannot_lower_price(lane_env):
    cap = 100 * lane_env.scale
    amount = 80 * lane_env.scale
    config = lane_env.set_config(
        paymentCapPerEpoch=cap,
        maxLockBonus=0,
        minUpBps=1_000,
        maxUpBps=2_000,
        minDownBps=500,
        maxDownBps=500,
        decayBps=900,
    )
    lane_env.buy(amount)
    old_rate = lane_env.lane.epochRate()

    boa.env.time_travel(blocks=2 * lane_env.epoch_length)
    quote = lane_env.quote(lane_env.scale)
    expected_rate, utilization, decay_steps = controller_rate(
        old_rate,
        amount,
        cap,
        2,
        config,
    )

    assert utilization == config[6]
    assert decay_steps == 1
    assert quote.rate == expected_rate
    assert quote.rate <= old_rate


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
        uHighBps=9_999,
        uLowBps=1,
        minUpBps=10_000,
        maxUpBps=10_000,
        minDownBps=1,
        maxDownBps=1,
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
        minUpBps=2,
        maxUpBps=2,
        minDownBps=1,
        maxDownBps=1,
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
        minDownBps=100,
        maxDownBps=100,
        decayBps=500,
    )
    lane_env.buy(lane_env.scale)
    old_rate = lane_env.lane.epochRate()
    boa.env.time_travel(blocks=lane_env.epoch_length)

    quote = lane_env.quote(lane_env.scale)
    low_step = old_rate * 10_000 // (10_000 - config[10])
    empty_step = old_rate * 10_000 // (10_000 - config[12])
    assert low_step < empty_step
    assert quote.rate == low_step


def test_maximum_decay_loop_bound_executes_all_32_steps(lane_env):
    cap = 100 * lane_env.scale
    amount = 50 * lane_env.scale
    config = lane_env.set_config(
        paymentCapPerEpoch=cap,
        minPaymentAmount=lane_env.scale,
        maxEffectiveRate=100 * 10**18,
        maxLockBonus=0,
        minDownBps=50,
        maxDownBps=100,
        decayBps=100,
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
    ceiling = config[4] * 10_000 // (10_000 + config[14])
    trace = [old_rate]
    for _ in range(32):
        trace.append(trace[-1] * 10_000 // (10_000 - config[12]))
    assert len(set(trace)) == 33
    assert trace[-1] == expected_rate < ceiling
    assert quote.rate == expected_rate
    lane_env.buy(lane_env.scale, expected_epoch=quote.epoch)
    event = filter_logs(lane_env.lane, "EpochRolled")[0]
    assert event.utilizationBps == utilization
    assert event.decaySteps == 32
    assert event.newRate == expected_rate


@pytest.mark.parametrize("offset", [0, 49, 99])
def test_full_epoch_upward_step_is_amount_weighted_by_block_offset(
    lane_env, offset
):
    cap = 100 * lane_env.scale
    config = lane_env.set_config(
        paymentCapPerEpoch=cap,
        minPaymentAmount=lane_env.scale,
        maxLockBonus=0,
        uHighBps=8_000,
        uLowBps=2_000,
        minUpBps=200,
        maxUpBps=800,
        minDownBps=100,
        maxDownBps=100,
        decayBps=100,
    )
    lane_env.buy(50 * lane_env.scale)

    boa.env.time_travel(blocks=lane_env.epoch_length + offset)
    epoch_one = lane_env.quote(cap)
    lane_env.buy(cap, expected_epoch=epoch_one.epoch)

    boa.env.time_travel(blocks=lane_env.epoch_length - offset)
    epoch_two = lane_env.quote(lane_env.scale)
    lateness = lateness_bps(offset, lane_env.epoch_length)
    earliness = 10_000 - lateness
    expected_step = config[8] + (config[9] - config[8]) * earliness // 10_000
    expected_rate = epoch_one.rate * 10_000 // (10_000 + expected_step)

    assert lane_env.lane.epochWeightedLateness() == cap * lateness
    assert lane_env.lane.epochTimingEligible()
    assert epoch_two.rate == expected_rate

    lane_env.buy(lane_env.scale, expected_epoch=epoch_two.epoch)
    rolled = filter_logs(lane_env.lane, "EpochRolled")[0]
    assert rolled.previousWeightedLateness == cap * lateness
    assert rolled.previousTimingEligible
    assert rolled.effectiveAdjustmentBps == expected_step
    assert rolled.controllerRate == expected_rate


@pytest.mark.parametrize(
    "accepted_units, expected_step_bps",
    [
        (80, 200),
        (90, 500),
    ],
)
def test_early_high_utilization_scales_from_minimum_to_midpoint(
    lane_env,
    accepted_units,
    expected_step_bps,
):
    cap = 100 * lane_env.scale
    config = lane_env.set_config(
        paymentCapPerEpoch=cap,
        maxLockBonus=0,
        minUpBps=200,
        maxUpBps=800,
        minDownBps=100,
        maxDownBps=100,
        decayBps=100,
    )
    amount = accepted_units * lane_env.scale
    lane_env.buy(amount)
    old_rate = lane_env.lane.epochRate()
    boa.env.time_travel(blocks=lane_env.epoch_length)

    quote = lane_env.quote(lane_env.scale)
    assert expected_step_bps == config[8] + (
        (config[9] - config[8]) * (accepted_units - 80) // 20
    )
    assert quote.rate == old_rate * 10_000 // (10_000 + expected_step_bps)


def test_weighted_lateness_is_split_merge_and_same_block_order_invariant(lane_env):
    cap = 100 * lane_env.scale
    lane_env.set_config(
        paymentCapPerEpoch=cap,
        maxLockBonus=0,
        minUpBps=200,
        maxUpBps=800,
        minDownBps=100,
        maxDownBps=100,
        decayBps=100,
    )
    lane_env.buy(50 * lane_env.scale)

    def run(split):
        boa.env.time_travel(blocks=lane_env.epoch_length + 10)
        if split:
            lane_env.buy(30 * lane_env.scale)
            lane_env.buy(50 * lane_env.scale)
        else:
            lane_env.buy(80 * lane_env.scale)
        boa.env.time_travel(blocks=80)
        if split:
            lane_env.buy(15 * lane_env.scale)
            lane_env.buy(5 * lane_env.scale)
        else:
            lane_env.buy(20 * lane_env.scale)
        weighted = lane_env.lane.epochWeightedLateness()
        boa.env.time_travel(blocks=10)
        return weighted, lane_env.quote(lane_env.scale).rate

    with boa.env.anchor():
        merged = run(False)
    with boa.env.anchor():
        split = run(True)

    expected = (
        80 * lane_env.scale * lateness_bps(10, lane_env.epoch_length)
        + 20 * lane_env.scale * lateness_bps(90, lane_env.epoch_length)
    )
    assert merged == split
    assert merged[0] == expected


def test_partial_first_initialized_epoch_forces_minimum_up_step(lane_factory):
    ctx = lane_factory(start_at_genesis=False, genesis_delay=5)
    cap = 100 * ctx.scale
    config = ctx.set_config(
        paymentCapPerEpoch=cap,
        maxLockBonus=0,
        minUpBps=200,
        maxUpBps=800,
        minDownBps=100,
        maxDownBps=100,
        decayBps=100,
    )
    boa.env.time_travel(
        blocks=ctx.genesis + ctx.epoch_length // 2 - boa.env.evm.patch.block_number
    )
    ctx.buy(cap)
    initialized = filter_logs(ctx.lane, "EpochInitialized")[0]

    assert not ctx.lane.epochTimingEligible()
    assert ctx.lane.epochWeightedLateness() > 0
    assert not initialized.timingEligible

    boa.env.time_travel(blocks=ctx.epoch_length)
    quote = ctx.quote(ctx.scale)
    expected = config[5] * 10_000 // (10_000 + config[8])
    assert quote.rate == expected


def test_single_block_epoch_treats_all_demand_as_fully_early(lane_factory):
    ctx = lane_factory(epoch_length=1)
    cap = 100 * ctx.scale
    config = ctx.set_config(
        paymentCapPerEpoch=cap,
        maxLockBonus=0,
        minUpBps=200,
        maxUpBps=800,
        minDownBps=100,
        maxDownBps=100,
        decayBps=100,
    )
    ctx.buy(cap)
    assert ctx.lane.epochWeightedLateness() == 0
    assert ctx.lane.epochTimingEligible()

    boa.env.time_travel(blocks=1)
    quote = ctx.quote(ctx.scale)
    expected = config[5] * 10_000 // (10_000 + config[9])
    assert quote.rate == expected


@pytest.mark.parametrize(
    "cap_units, accepted_units, expected_step_index",
    [
        (100, 20, 10),
        (10_001, 1, 11),
    ],
)
def test_downward_strength_uses_utilization_and_reaches_range_endpoints(
    lane_env, cap_units, accepted_units, expected_step_index
):
    cap = cap_units * lane_env.scale
    config = lane_env.set_config(
        paymentCapPerEpoch=cap,
        maxLockBonus=0,
        minUpBps=800,
        maxUpBps=800,
        minDownBps=100,
        maxDownBps=400,
        decayBps=400,
    )
    lane_env.buy(accepted_units * lane_env.scale)
    old_rate = lane_env.lane.epochRate()
    boa.env.time_travel(blocks=lane_env.epoch_length)

    quote = lane_env.quote(lane_env.scale)
    step = config[expected_step_index]
    assert quote.rate == old_rate * 10_000 // (10_000 - step)
