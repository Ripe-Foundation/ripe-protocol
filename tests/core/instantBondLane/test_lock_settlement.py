import boa
import pytest

from conf_utils import filter_logs


def test_unlocked_request_stays_unlocked_when_lane_min_is_zero(lane_env):
    lane_env.setup_lock_terms(min_lock=100, max_lock=1_000)
    quote = lane_env.quote(lane_env.scale, 0)
    assert quote.available is True
    assert quote.actualLock == 0
    assert quote.bonusRipe == 0
    payout = lane_env.buy(lane_env.scale, requested_lock=0)
    assert payout == quote.totalRipe
    assert lane_env.ripe_token.balanceOf(lane_env.bob) >= payout


def test_effective_min_lock_is_the_stricter_of_lane_and_vault(lane_env):
    lane_env.setup_lock_terms(min_lock=300, max_lock=1_000)
    lane_env.set_config(minLockDuration=150, maxLockBonus=10_000)
    vault_stricter = lane_env.quote(lane_env.scale, 0)
    assert vault_stricter.actualLock == 300

    lane_env.set_config(minLockDuration=450, maxLockBonus=10_000)
    lane_stricter = lane_env.quote(lane_env.scale, 10)
    assert lane_stricter.actualLock == 450
    assert lane_stricter.bonusRatio == 0


def test_lane_min_lock_clamps_zero_request(lane_env):
    lane_env.setup_lock_terms(min_lock=50, max_lock=1_000)
    lane_env.set_config(minLockDuration=200, maxLockBonus=5_000)
    quote = lane_env.quote(lane_env.scale, 0)
    assert quote.available is True
    assert quote.actualLock == 200
    assert quote.bonusRatio == 0
    assert quote.ripeGovVaultId == lane_env.mission_control.coreRipeGovVaultId()
    payout = lane_env.buy(lane_env.scale, requested_lock=0)
    assert payout == quote.totalRipe
    purchased = filter_logs(lane_env.lane, "InstantBondPurchased")[-1]
    assert purchased.actualLock == 200
    assert purchased.bonusRipe == 0
    locked = lane_env.ripe_gov_vault.getTotalAmountForUser(
        lane_env.bob, lane_env.ripe_token
    )
    assert locked == payout


def test_request_below_floor_clamps_up_and_above_ceiling_clamps_down(lane_env):
    lane_env.setup_lock_terms(min_lock=100, max_lock=1_000)
    lane_env.set_config(minLockDuration=250, maxLockBonus=10_000)

    below = lane_env.quote(lane_env.scale, 10)
    assert below.actualLock == 250
    assert below.bonusRatio == 0

    mid = lane_env.quote(lane_env.scale, 625)
    assert mid.actualLock == 625
    assert mid.bonusRatio == 10_000 * (625 - 250) // (1_000 - 250)

    above = lane_env.quote(lane_env.scale, 50_000)
    assert above.actualLock == 1_000
    assert above.bonusRatio == 10_000

    payout = lane_env.buy(lane_env.scale, requested_lock=50_000)
    assert payout == above.totalRipe
    purchased = filter_logs(lane_env.lane, "InstantBondPurchased")[-1]
    assert purchased.actualLock == 1_000
    assert purchased.bonusRatio == 10_000


def test_equal_min_and_max_lock_pays_full_bonus(lane_env):
    lane_env.setup_lock_terms(min_lock=400, max_lock=400)
    lane_env.set_config(minLockDuration=400, maxLockBonus=7_500)
    quote = lane_env.quote(lane_env.scale, 1)
    assert quote.actualLock == 400
    assert quote.bonusRatio == 7_500
    assert quote.bonusRipe == quote.baseRipe * 7_500 // 10_000
    lane_env.buy(lane_env.scale, requested_lock=1)


def test_no_vault_range_with_zero_limits_settles_unlocked(lane_env):
    lane_env.setup_lock_terms(min_lock=0, max_lock=0)
    lane_env.set_config(minLockDuration=0, maxLockBonus=5_000)
    quote = lane_env.quote(lane_env.scale, 500)
    assert quote.actualLock == 0
    assert quote.bonusRipe == 0
    payout = lane_env.buy(lane_env.scale, requested_lock=500)
    assert payout == quote.totalRipe
    assert lane_env.ripe_gov_vault.getTotalAmountForUser(
        lane_env.bob, lane_env.ripe_token
    ) == 0


def test_impossible_range_with_lane_min_still_settles_unlocked(lane_env):
    lane_env.setup_lock_terms(min_lock=10, max_lock=20)
    lane_env.set_config(minLockDuration=100, maxLockBonus=5_000)
    quote = lane_env.quote(lane_env.scale, 0)
    assert quote.actualLock == 0
    assert quote.available is True
    lane_env.buy(lane_env.scale, requested_lock=0)


def test_exit_disclosure_and_bad_debt_freeze(lane_env):
    lane_env.setup_lock_terms(
        min_lock=100,
        max_lock=1_000,
        can_exit=True,
        exit_fee=333,
        freeze_on_bad_debt=True,
    )
    quote = lane_env.quote(lane_env.scale, 1_000)
    assert quote.canExitEarly is True
    assert quote.exitFee == 333
    assert quote.isExitFrozen is False

    lane_env.ledger.setBadDebt(1, sender=lane_env.switchboard.address)
    frozen = lane_env.quote(lane_env.scale, 1_000)
    assert frozen.isExitFrozen is True
    assert frozen.available is True


def test_locked_settlement_is_exact_and_leaves_no_lane_ripe(lane_env):
    lane_env.setup_lock_terms(min_lock=100, max_lock=1_000)
    ripe_before = lane_env.ripe_token.balanceOf(lane_env.lane)
    quote = lane_env.quote(lane_env.scale, 500)
    payout = lane_env.buy(lane_env.scale, requested_lock=500)
    assert payout == quote.totalRipe
    assert lane_env.ripe_token.balanceOf(lane_env.lane) == ripe_before
    assert lane_env.ripe_token.allowance(lane_env.lane, lane_env.teller) == 0
    assert (
        lane_env.ripe_gov_vault.getTotalAmountForUser(
            lane_env.bob, lane_env.ripe_token
        )
        == payout
    )


def test_requested_lock_with_zero_vault_max_stays_unlocked(lane_env):
    lane_env.setup_lock_terms(min_lock=100, max_lock=0)
    lane_env.set_config(minLockDuration=50, maxLockBonus=5_000)
    quote = lane_env.quote(lane_env.scale, 500)
    assert quote.actualLock == 0
    assert quote.available is True
    lane_env.buy(lane_env.scale, requested_lock=500)


def test_vault_min_does_not_force_lock_when_lane_min_is_zero(lane_env):
    lane_env.setup_lock_terms(min_lock=400, max_lock=1_000)
    lane_env.set_config(minLockDuration=0)
    quote = lane_env.quote(lane_env.scale, 0)
    assert quote.actualLock == 0
    lane_env.buy(lane_env.scale, requested_lock=0)
    assert lane_env.ripe_gov_vault.getTotalAmountForUser(
        lane_env.bob, lane_env.ripe_token
    ) == 0


@pytest.mark.parametrize(
    "requested, expected_lock, expected_ratio",
    [
        (100, 100, 0),
        (550, 550, 5_000),
        (1_000, 1_000, 10_000),
    ],
)
def test_linear_bonus_between_vault_min_and_max(
    lane_env, requested, expected_lock, expected_ratio
):
    lane_env.setup_lock_terms(min_lock=100, max_lock=1_000)
    lane_env.set_config(minLockDuration=0, maxLockBonus=10_000)
    quote = lane_env.quote(lane_env.scale, requested)
    assert quote.actualLock == expected_lock
    assert quote.bonusRatio == expected_ratio
    assert quote.bonusRipe == quote.baseRipe * expected_ratio // 10_000
    lane_env.buy(lane_env.scale, requested_lock=requested)
