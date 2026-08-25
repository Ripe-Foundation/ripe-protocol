import boa


def test_preview_before_genesis_is_empty(lane_factory):
    ctx = lane_factory()
    ctx.stop()
    future = boa.env.evm.patch.block_number + 20
    ctx.start(future)
    quote = ctx.quote(ctx.scale)
    assert tuple(quote) == (False,) + (0,) * 14


def test_preview_when_not_running_is_empty(lane_factory):
    ctx = lane_factory(auto_start=False)
    assert tuple(ctx.quote(ctx.scale)) == (False,) + (0,) * 14


def test_preview_illegal_size_keeps_market_and_payout_disclosure(lane_env):
    quote = lane_env.quote(lane_env.scale - 1)
    assert quote.available is False
    assert quote.epoch == 0
    assert quote.basePayoutRate == lane_env.lane.bondConfig().seedBasePayoutRate
    assert quote.remainingPayment == lane_env.lane.bondConfig().paymentCapPerEpoch
    assert quote.minPaymentAmount == lane_env.scale
    assert quote.totalRipe > 0


def test_preview_matches_successful_purchase_terms(lane_env):
    requested = 550
    quote = lane_env.quote(2 * lane_env.scale, requested)
    payout = lane_env.buy(
        2 * lane_env.scale,
        requested,
        min_ripe_out=quote.totalRipe,
    )
    position = lane_env.claims.positions(lane_env.bob, 1)
    assert payout == quote.totalRipe
    assert position.ripePayout == quote.totalRipe
    assert position.creationBlock == quote.creationBlock
    assert position.maturityBlock == quote.maturityBlock


def test_preview_does_not_require_wallet_balance_or_allowance(lane_env, alice):
    assert lane_env.payment_token.balanceOf(alice) == 0
    assert lane_env.payment_token.allowance(alice, lane_env.lane) == 0
    quote = lane_env.quote(lane_env.scale, sender=alice)
    assert quote.available is True
    assert quote.totalRipe > 0


def test_preview_clamps_vesting_and_computes_linear_bonus(lane_env):
    config = lane_env.lane.bondConfig()
    below = lane_env.quote(lane_env.scale, 1)
    midpoint_length = (config.minVestingLength + config.maxVestingLength) // 2
    midpoint = lane_env.quote(lane_env.scale, midpoint_length)
    above = lane_env.quote(lane_env.scale, config.maxVestingLength + 1)

    assert below.vestingLength == config.minVestingLength
    assert below.bonusRatio == 0
    assert midpoint.vestingLength == midpoint_length
    assert midpoint.bonusRatio == (
        config.maxVestingBonus
        * (midpoint_length - config.minVestingLength)
        // (config.maxVestingLength - config.minVestingLength)
    )
    assert above.vestingLength == config.maxVestingLength
    assert above.bonusRatio == config.maxVestingBonus
    assert above.totalRipe == above.baseRipe + above.bonusRipe


def test_zero_requested_vesting_uses_minimum(lane_env):
    quote = lane_env.quote(lane_env.scale, 0)
    assert quote.vestingLength == lane_env.lane.bondConfig().minVestingLength
    assert quote.bonusRatio == 0


def test_equal_vesting_bounds_pay_full_configured_bonus(lane_env):
    lane_env.set_config(
        minVestingLength=50,
        maxVestingLength=50,
        maxVestingBonus=2_500,
    )
    quote = lane_env.quote(lane_env.scale, 0)
    assert quote.vestingLength == 50
    assert quote.bonusRatio == 2_500
    assert quote.bonusRipe == quote.baseRipe * 2_500 // 10_000


def test_preview_budget_exhaustion_keeps_payout_math(lane_env):
    lane_env.set_budget(0)
    quote = lane_env.quote(lane_env.scale)
    assert quote.available is False
    assert quote.budgetRemaining == 0
    assert quote.totalRipe > 0


def test_preview_missing_claims_fails_closed(lane_factory):
    ctx = lane_factory(register_claims=False)
    quote = ctx.quote(ctx.scale)
    assert quote.available is False
    assert quote.budgetRemaining == 0
    assert quote.totalRipe > 0


def test_preview_is_read_only_for_epoch_override_and_claims(lane_env):
    target = 9 * 10**17
    resolved = lane_env.set_rate_override(target, 0)
    state_before = tuple(lane_env.lane.epochState())
    budget_before = lane_env.claims.remainingAllocationBudget()
    next_id_before = lane_env.claims.nextPositionId()

    quote = lane_env.quote(lane_env.scale)
    assert quote.epoch == resolved
    assert quote.basePayoutRate == target
    assert quote.rateSource == lane_env.lane.RATE_SOURCE_OVERRIDE()
    assert tuple(lane_env.lane.epochState()) == state_before
    assert lane_env.lane.overrideTargetBasePayoutRate() == target
    assert lane_env.claims.remainingAllocationBudget() == budget_before
    assert lane_env.claims.nextPositionId() == next_id_before
