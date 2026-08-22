import boa
import pytest

from conf_utils import filter_logs, get_boa_dev_reasons


def test_uncommitted_cap_change_is_live_on_the_first_buy(lane_env):
    first = lane_env.quote(100 * lane_env.scale)
    assert first.available is True
    assert first.remainingPayment == 1_000 * lane_env.scale

    lane_env.set_config(
        paymentCapPerEpoch=10 * lane_env.scale,
        minPaymentAmount=lane_env.scale,
    )
    tightened = lane_env.quote(100 * lane_env.scale)
    assert tightened.available is False
    assert tightened.remainingPayment == 10 * lane_env.scale
    assert tightened.totalRipe == 0

    with pytest.raises(boa.BoaError) as err:
        lane_env.buy(100 * lane_env.scale)
    assert "exceeds available amount" in get_boa_dev_reasons(err.value)

    payout = lane_env.buy(10 * lane_env.scale)
    assert payout > 0
    assert lane_env.lane.epochState().paymentCap == 10 * lane_env.scale


def test_uncommitted_bonus_and_seed_apply_on_the_opening_buy(lane_env):
    lane_env.setup_lock_terms(min_lock=100, max_lock=1_000)
    lane_env.set_config(maxLockBonus=0, seedRate=10**18)
    unlocked = lane_env.quote(lane_env.scale, 1_000)
    assert unlocked.rate == 10**18
    assert unlocked.bonusRipe == 0

    lane_env.set_config(
        maxEffectiveRate=3 * 10**18,
        maxLockBonus=10_000,
        seedRate=11 * 10**17,
    )
    live = lane_env.quote(lane_env.scale, 1_000)
    assert live.rate == 11 * 10**17
    assert live.bonusRatio == 10_000
    assert live.totalRipe > unlocked.totalRipe

    payout = lane_env.buy(
        lane_env.scale,
        requested_lock=1_000,
        min_ripe_out=unlocked.totalRipe,
    )
    purchased = filter_logs(lane_env.lane, "InstantBondPurchased")[-1]
    assert payout == live.totalRipe
    assert purchased.epochRate == 11 * 10**17
    assert purchased.bonusRatio == 10_000


def test_min_lock_change_between_preview_and_buy_locks_despite_unlocked_quote(
    lane_env,
):
    lane_env.setup_lock_terms(min_lock=100, max_lock=1_000)
    lane_env.set_config(minLockDuration=0, maxLockBonus=5_000)
    unlocked = lane_env.quote(lane_env.scale, 0)
    assert unlocked.available is True
    assert unlocked.actualLock == 0
    ripe_before = lane_env.ripe_token.balanceOf(lane_env.bob)

    lane_env.set_config(minLockDuration=200, maxLockBonus=5_000)
    payout = lane_env.buy(
        lane_env.scale,
        requested_lock=0,
        min_ripe_out=unlocked.totalRipe,
    )
    purchased = filter_logs(lane_env.lane, "InstantBondPurchased")[-1]
    assert purchased.actualLock == 200
    assert payout >= unlocked.totalRipe
    assert lane_env.ripe_token.balanceOf(lane_env.bob) == ripe_before
    assert (
        lane_env.ripe_gov_vault.getTotalAmountForUser(
            lane_env.bob, lane_env.ripe_token
        )
        == payout
    )


def test_after_first_fill_later_config_changes_do_not_move_the_committed_epoch(
    lane_env,
):
    lane_env.setup_lock_terms(min_lock=100, max_lock=1_000)
    lane_env.set_config(maxLockBonus=5_000, minLockDuration=0)
    lane_env.buy(lane_env.scale, requested_lock=1_000)
    committed = lane_env.lane.epochState()

    lane_env.set_config(
        paymentCapPerEpoch=20 * lane_env.scale,
        minPaymentAmount=5 * lane_env.scale,
        maxLockBonus=0,
        seedRate=11 * 10**17,
        minLockDuration=400,
    )
    quote = lane_env.quote(lane_env.scale, 1_000)
    assert quote.remainingPayment == committed.paymentCap - lane_env.scale
    assert quote.minPaymentAmount == committed.minPaymentAmount
    assert quote.rate == committed.rate
    assert quote.bonusRatio == 5_000

    unlocked_request = lane_env.quote(lane_env.scale, 0)
    assert unlocked_request.actualLock == 400
    assert unlocked_request.available is True


def test_uncommitted_min_payment_hike_invalidates_the_opening_size(lane_env):
    first = lane_env.quote(lane_env.scale)
    assert first.available is True
    lane_env.set_config(minPaymentAmount=10 * lane_env.scale)
    hiked = lane_env.quote(lane_env.scale)
    assert hiked.available is False
    assert hiked.totalRipe == 0
    assert hiked.minPaymentAmount == 10 * lane_env.scale
    with pytest.raises(boa.BoaError) as err:
        lane_env.buy(lane_env.scale)
    assert "below minimum payment" in get_boa_dev_reasons(err.value)
    assert lane_env.buy(10 * lane_env.scale) > 0
