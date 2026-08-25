import boa

from conf_utils import filter_logs


def test_uncommitted_cap_change_is_live_on_opening_buy(lane_env):
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
    assert tightened.totalRipe > 0
    with boa.reverts("exceeds available amount"):
        lane_env.buy(100 * lane_env.scale)

    lane_env.buy(10 * lane_env.scale)
    assert lane_env.lane.epochState().paymentCap == 10 * lane_env.scale


def test_uncommitted_bonus_seed_and_vesting_terms_apply_on_opening_buy(lane_env):
    original = lane_env.quote(lane_env.scale, 1_000)
    lane_env.set_config(
        maxAllInPayoutRate=3 * 10**18,
        maxVestingBonus=10_000,
        seedBasePayoutRate=11 * 10**17,
        minVestingLength=200,
        maxVestingLength=2_000,
    )
    live = lane_env.quote(lane_env.scale, 2_000)
    assert live.basePayoutRate == 11 * 10**17
    assert live.vestingLength == 2_000
    assert live.bonusRatio == 10_000
    assert live.totalRipe > original.totalRipe

    payout = lane_env.buy(
        lane_env.scale,
        requested_vesting=2_000,
        min_ripe_out=original.totalRipe,
    )
    event = filter_logs(lane_env.lane, "InstantBondPurchased")[-1]
    assert payout == live.totalRipe
    assert event.basePayoutRate == 11 * 10**17
    assert event.bonusRatio == 10_000
    assert event.vestingLength == 2_000


def test_expected_vesting_length_detects_live_config_race(lane_env):
    old = lane_env.quote(lane_env.scale, 0)
    lane_env.set_config(minVestingLength=200, maxVestingLength=2_000)
    with boa.reverts("vesting length moved"):
        lane_env.lane.buyNow(
            lane_env.scale,
            0,
            old.vestingLength,
            old.epoch,
            old.totalRipe,
            boa.env.evm.patch.block_number,
            sender=lane_env.bob,
        )
    assert lane_env.claims.getNumUserPositions(lane_env.bob) == 0

    current = lane_env.quote(lane_env.scale, 0)
    assert lane_env.buy(
        lane_env.scale,
        expected_vesting=current.vestingLength,
        min_ripe_out=current.totalRipe,
    ) == current.totalRipe


def test_committed_epoch_freezes_rate_cap_minimum_and_vesting_terms(lane_env):
    lane_env.set_config(
        maxVestingBonus=5_000,
        minVestingLength=100,
        maxVestingLength=1_000,
    )
    lane_env.buy(lane_env.scale, requested_vesting=1_000)
    committed = lane_env.lane.epochState()

    lane_env.set_config(
        paymentCapPerEpoch=20 * lane_env.scale,
        minPaymentAmount=5 * lane_env.scale,
        maxVestingBonus=0,
        seedBasePayoutRate=11 * 10**17,
        minVestingLength=400,
        maxVestingLength=500,
    )
    quote = lane_env.quote(lane_env.scale, 1_000)
    assert quote.remainingPayment == committed.paymentCap - lane_env.scale
    assert quote.minPaymentAmount == committed.minPaymentAmount
    assert quote.basePayoutRate == committed.basePayoutRate
    assert quote.vestingLength == committed.maxVestingLength
    assert quote.bonusRatio == committed.maxVestingBonus


def test_uncommitted_minimum_hike_invalidates_opening_size(lane_env):
    first = lane_env.quote(lane_env.scale)
    assert first.available is True
    lane_env.set_config(minPaymentAmount=10 * lane_env.scale)
    hiked = lane_env.quote(lane_env.scale)
    assert hiked.available is False
    assert hiked.totalRipe > 0
    assert hiked.minPaymentAmount == 10 * lane_env.scale
    with boa.reverts("below minimum payment"):
        lane_env.buy(lane_env.scale)
    assert lane_env.buy(10 * lane_env.scale) > 0
