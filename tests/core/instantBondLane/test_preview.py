import boa


def test_preview_before_genesis_is_empty(lane_factory):
    ctx = lane_factory(auto_start=False)
    ctx.start(boa.env.evm.patch.block_number + 30)
    quote = ctx.quote(ctx.scale)
    assert quote.available is False
    assert quote.epoch == 0
    assert quote.rate == 0
    assert quote.totalRipe == 0


def test_preview_fills_market_when_unavailable(lane_env):
    lane_env.set_config(canBuyNow=False)
    quote = lane_env.quote(lane_env.scale)
    assert quote.available is False
    assert quote.epoch == 0
    assert quote.rate == lane_env.lane.bondConfig().seedRate
    assert quote.remainingPayment == lane_env.lane.bondConfig().paymentCapPerEpoch
    assert quote.totalRipe == lane_env.scale * quote.rate // lane_env.scale


def test_preview_zeroes_payout_when_size_is_illegal(lane_env):
    too_small = lane_env.quote(lane_env.scale - 1)
    assert too_small.available is False
    assert too_small.totalRipe == 0
    assert too_small.rate == lane_env.lane.bondConfig().seedRate

    cap = lane_env.lane.bondConfig().paymentCapPerEpoch
    too_big = lane_env.quote(cap + 1)
    assert too_big.available is False
    assert too_big.totalRipe == 0


def test_preview_matches_buy_when_available(lane_env):
    quote = lane_env.quote(3 * lane_env.scale)
    payout = lane_env.buy(3 * lane_env.scale, min_ripe_out=quote.totalRipe)
    assert payout == quote.totalRipe
    assert quote.available is True


def test_preview_does_not_require_wallet_balance(lane_env, alice):
    quote = lane_env.lane.previewBuyNow(lane_env.scale, 0, sender=alice)
    assert quote.available is True
    assert quote.totalRipe > 0


def test_preview_lock_disclosure_does_not_block_availability(lane_env):
    lane_env.setup_lock_terms(min_lock=100, max_lock=1_000)
    quote = lane_env.quote(lane_env.scale, 500)
    assert quote.available is True
    assert quote.actualLock == 500
    assert quote.ripeGovVaultId != 0
    assert quote.canExitEarly is True


def test_preview_when_not_running_still_fills_market(lane_env):
    seed = lane_env.lane.bondConfig().seedRate
    lane_env.stop()
    quote = lane_env.quote(lane_env.scale)
    assert quote.available is False
    assert quote.rate == seed
    assert quote.totalRipe == lane_env.scale * seed // lane_env.scale


def test_preview_budget_exhaustion_keeps_payout_math(lane_env):
    first = lane_env.buy(lane_env.scale)
    lane_env.set_config(mintBudget=first)
    quote = lane_env.quote(lane_env.scale)
    assert quote.available is False
    assert quote.totalRipe > quote.budgetRemaining
    assert quote.baseRipe > 0
