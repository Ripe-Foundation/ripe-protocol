import boa
import pytest

from constants import EIGHTEEN_DECIMALS
from tests.vaults.ripe_gov_exit_fee_model import (
    DECIMAL_OFFSET,
    HUNDRED_PERCENT,
    UINT256_MAX,
    UInt256Overflow,
    assert_exact_exit_claim,
    checked_amount_to_shares,
    checked_closed_form_retained_shares,
    checked_shares_to_amount,
    checked_target_claim,
    claim,
    maximal_retained_shares,
    target_claim,
)


VAULT_ID = 2
LOCK_TERMS = (100, 1_000, 200_00, True, 10_00)


def _configure_asset(
    mission_control,
    setAssetConfig,
    switchboard_alpha,
    asset,
    *,
    exit_fee=10_00,
):
    lock_terms = (*LOCK_TERMS[:4], exit_fee)
    mission_control.setRipeGovVaultConfig(
        asset,
        100_00,
        False,
        lock_terms,
        sender=switchboard_alpha.address,
    )
    setAssetConfig(asset, _vaultIds=[VAULT_ID])


def _deposit(vault, token, funder, user, amount, teller, lock_duration=500):
    token.transfer(vault, amount, sender=funder)
    return vault.depositTokensWithLockDuration(
        user,
        token,
        amount,
        lock_duration,
        sender=teller.address,
    )


def _point_tuple(points):
    return tuple(points)


def _atomic_snapshot(vault, token, user, ledger):
    return (
        token.balanceOf(vault),
        vault.userBalances(user, token),
        vault.totalBalances(token),
        tuple(vault.userGovData(user, token)),
        vault.totalUserGovPoints(user),
        vault.totalGovPoints(),
        _point_tuple(ledger.userDepositPoints(user, VAULT_ID, token)),
        _point_tuple(ledger.assetDepositPoints(VAULT_ID, token)),
    )


@pytest.mark.parametrize(
    ("exiter_amount", "remaining_amount"),
    (
        pytest.param(
            1 * EIGHTEEN_DECIMALS,
            99 * EIGHTEEN_DECIMALS,
            id="small-holder",
        ),
        pytest.param(
            50 * EIGHTEEN_DECIMALS,
            50 * EIGHTEEN_DECIMALS,
            id="equal-holders",
        ),
        pytest.param(
            90 * EIGHTEEN_DECIMALS,
            10 * EIGHTEEN_DECIMALS,
            id="dominant-holder",
        ),
    ),
)
def test_early_exit_fee_matches_exact_live_claim_for_normal_holder_sizes(
    exiter_amount,
    remaining_amount,
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    alice,
    teller,
    mission_control,
    setAssetConfig,
    switchboard_alpha,
):
    _configure_asset(
        mission_control,
        setAssetConfig,
        switchboard_alpha,
        ripe_token,
    )
    _deposit(ripe_gov_vault, ripe_token, whale, bob, exiter_amount, teller)
    _deposit(ripe_gov_vault, ripe_token, whale, alice, remaining_amount, teller)

    custody_before = ripe_token.balanceOf(ripe_gov_vault)
    total_before = ripe_gov_vault.totalBalances(ripe_token)
    bob_before = ripe_gov_vault.userBalances(bob, ripe_token)
    alice_shares = ripe_gov_vault.userBalances(alice, ripe_token)
    bob_claim_before = claim(bob_before, total_before, custody_before)
    alice_claim_before = claim(alice_shares, total_before, custody_before)
    target = target_claim(bob_claim_before, 10_00)
    expected_after = maximal_retained_shares(
        bob_before,
        total_before - bob_before,
        custody_before,
        target,
    )
    ripe_gov_vault.releaseLock(bob, ripe_token, sender=teller.address)

    bob_after = ripe_gov_vault.userBalances(bob, ripe_token)
    total_after = ripe_gov_vault.totalBalances(ripe_token)
    burn = bob_before - bob_after
    claim_after = claim(bob_after, total_after, custody_before)
    assert ripe_token.balanceOf(ripe_gov_vault) == custody_before
    assert total_after == total_before - burn
    assert ripe_gov_vault.userBalances(alice, ripe_token) == alice_shares
    assert bob_after == expected_after
    assert claim_after <= target < claim(
        bob_after + 1,
        total_after + 1,
        custody_before,
    )
    assert claim(alice_shares, total_after, custody_before) > alice_claim_before


def test_early_exit_fee_benefits_multiple_remaining_holders_pro_rata(
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    alice,
    sally,
    teller,
    mission_control,
    setAssetConfig,
    switchboard_alpha,
):
    _configure_asset(mission_control, setAssetConfig, switchboard_alpha, ripe_token)
    _deposit(ripe_gov_vault, ripe_token, whale, bob, 600 * EIGHTEEN_DECIMALS, teller)
    _deposit(ripe_gov_vault, ripe_token, whale, alice, 250 * EIGHTEEN_DECIMALS, teller)
    _deposit(ripe_gov_vault, ripe_token, whale, sally, 150 * EIGHTEEN_DECIMALS, teller)

    custody = ripe_token.balanceOf(ripe_gov_vault)
    total_before = ripe_gov_vault.totalBalances(ripe_token)
    alice_shares = ripe_gov_vault.userBalances(alice, ripe_token)
    sally_shares = ripe_gov_vault.userBalances(sally, ripe_token)
    alice_before = claim(alice_shares, total_before, custody)
    sally_before = claim(sally_shares, total_before, custody)

    ripe_gov_vault.releaseLock(bob, ripe_token, sender=teller.address)

    total_after = ripe_gov_vault.totalBalances(ripe_token)
    alice_gain = claim(alice_shares, total_after, custody) - alice_before
    sally_gain = claim(sally_shares, total_after, custody) - sally_before
    assert alice_gain > 0
    assert sally_gain > 0
    assert abs(alice_gain * sally_shares - sally_gain * alice_shares) <= (
        alice_shares + sally_shares
    )


def test_sole_actual_holder_early_exit_reverts_atomically(
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    teller,
    lootbox,
    ledger,
    mission_control,
    setAssetConfig,
    switchboard_alpha,
):
    _configure_asset(mission_control, setAssetConfig, switchboard_alpha, ripe_token)
    _deposit(ripe_gov_vault, ripe_token, whale, bob, 100 * EIGHTEEN_DECIMALS, teller)
    lootbox.updateDepositPoints(
        bob,
        VAULT_ID,
        ripe_gov_vault,
        ripe_token,
        sender=teller.address,
    )
    boa.env.time_travel(blocks=10)
    before = _atomic_snapshot(ripe_gov_vault, ripe_token, bob, ledger)

    with boa.reverts("no remaining holders"):
        ripe_gov_vault.releaseLock(bob, ripe_token, sender=teller.address)

    assert _atomic_snapshot(ripe_gov_vault, ripe_token, bob, ledger) == before


def test_remaining_holder_guard_is_address_level_not_beneficial_owner_level(
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    alice,
    teller,
    mission_control,
    setAssetConfig,
    switchboard_alpha,
):
    """Two addresses can recapture a same-pool fee for one economic owner."""
    _configure_asset(mission_control, setAssetConfig, switchboard_alpha, ripe_token)
    _deposit(ripe_gov_vault, ripe_token, whale, bob, 90 * EIGHTEEN_DECIMALS, teller)
    _deposit(ripe_gov_vault, ripe_token, whale, alice, 10 * EIGHTEEN_DECIMALS, teller)

    custody = ripe_token.balanceOf(ripe_gov_vault)
    total_before = ripe_gov_vault.totalBalances(ripe_token)
    bob_shares = ripe_gov_vault.userBalances(bob, ripe_token)
    alice_shares = ripe_gov_vault.userBalances(alice, ripe_token)
    bob_before = claim(bob_shares, total_before, custody)
    alice_before = claim(alice_shares, total_before, custody)
    target = target_claim(bob_before, 10_00)

    ripe_gov_vault.releaseLock(bob, ripe_token, sender=teller.address)

    total_after = ripe_gov_vault.totalBalances(ripe_token)
    bob_after = claim(
        ripe_gov_vault.userBalances(bob, ripe_token),
        total_after,
        custody,
    )
    alice_after = claim(alice_shares, total_after, custody)
    alice_gain = alice_after - alice_before
    aggregate_rounding_loss = bob_before + alice_before - bob_after - alice_after

    assert bob_after <= target
    assert alice_gain > 0
    assert aggregate_rounding_loss >= 0
    assert bob_before - bob_after >= alice_gain
    assert bob_after + alice_after > target + alice_before


def test_economically_empty_dust_early_exit_reverts_atomically(
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    alice,
    teller,
    lootbox,
    ledger,
    mission_control,
    setAssetConfig,
    switchboard_alpha,
):
    _configure_asset(mission_control, setAssetConfig, switchboard_alpha, ripe_token)
    _deposit(ripe_gov_vault, ripe_token, whale, bob, 1, teller)
    _deposit(ripe_gov_vault, ripe_token, whale, alice, 100, teller)
    lootbox.updateDepositPoints(
        bob,
        VAULT_ID,
        ripe_gov_vault,
        ripe_token,
        sender=teller.address,
    )

    # Model a one-unit negative rebase/custody loss. Bob retains nonzero shares,
    # but their exact floored SharesVault claim becomes zero.
    ripe_token.burn(1, sender=ripe_gov_vault.address)
    assert ripe_gov_vault.userBalances(bob, ripe_token) != 0
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == 0
    boa.env.time_travel(blocks=10)
    before = _atomic_snapshot(ripe_gov_vault, ripe_token, bob, ledger)

    with boa.reverts("no fee-bearing claim"):
        ripe_gov_vault.releaseLock(bob, ripe_token, sender=teller.address)

    assert _atomic_snapshot(ripe_gov_vault, ripe_token, bob, ledger) == before


def test_full_fee_burns_economically_empty_dust_instead_of_waiving_fee(
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    alice,
    teller,
    mission_control,
    setAssetConfig,
    switchboard_alpha,
):
    _configure_asset(
        mission_control,
        setAssetConfig,
        switchboard_alpha,
        ripe_token,
        exit_fee=100_00,
    )
    _deposit(ripe_gov_vault, ripe_token, whale, bob, 1, teller)
    _deposit(ripe_gov_vault, ripe_token, whale, alice, 100, teller)
    ripe_token.burn(1, sender=ripe_gov_vault.address)

    custody = ripe_token.balanceOf(ripe_gov_vault)
    total_before = ripe_gov_vault.totalBalances(ripe_token)
    bob_before = ripe_gov_vault.userBalances(bob, ripe_token)
    assert bob_before != 0
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == 0

    ripe_gov_vault.releaseLock(bob, ripe_token, sender=teller.address)

    bob_after = ripe_gov_vault.userBalances(bob, ripe_token)
    total_after = ripe_gov_vault.totalBalances(ripe_token)
    assert ripe_token.balanceOf(ripe_gov_vault) == custody
    assert_exact_exit_claim(
        bob_before,
        total_before,
        custody,
        100_00,
        bob_after,
        total_after,
    )
    assert ripe_gov_vault.userGovData(bob, ripe_token).unlock == 0


def test_full_exit_fee_removes_position_and_checkpoints_post_burn_balance(
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    alice,
    teller,
    lootbox,
    ledger,
    mission_control,
    setAssetConfig,
    setRipeRewardsConfig,
    switchboard_alpha,
):
    _configure_asset(
        mission_control,
        setAssetConfig,
        switchboard_alpha,
        ripe_token,
        exit_fee=100_00,
    )
    setRipeRewardsConfig(True)
    _deposit(ripe_gov_vault, ripe_token, whale, bob, 60 * EIGHTEEN_DECIMALS, teller)
    _deposit(ripe_gov_vault, ripe_token, whale, alice, 40 * EIGHTEEN_DECIMALS, teller)
    lootbox.updateDepositPoints(
        bob,
        VAULT_ID,
        ripe_gov_vault,
        ripe_token,
        sender=teller.address,
    )

    custody = ripe_token.balanceOf(ripe_gov_vault)
    total_before = ripe_gov_vault.totalBalances(ripe_token)
    bob_shares = ripe_gov_vault.userBalances(bob, ripe_token)
    alice_shares = ripe_gov_vault.userBalances(alice, ripe_token)
    alice_claim_before = claim(alice_shares, total_before, custody)
    points_before = ledger.userDepositPoints(bob, VAULT_ID, ripe_token)
    gov_before = ripe_gov_vault.userGovData(bob, ripe_token)
    boa.env.time_travel(blocks=17)
    elapsed = boa.env.evm.patch.block_number - points_before.lastUpdate
    expected_new_gov_points = ripe_gov_vault.getLatestGovPoints(
        gov_before.lastShares,
        gov_before.lastPointsUpdate,
        gov_before.unlock,
        gov_before.lastTerms,
        100_00,
    )

    ripe_gov_vault.releaseLock(bob, ripe_token, sender=teller.address)

    points_after = ledger.userDepositPoints(bob, VAULT_ID, ripe_token)
    gov_after = ripe_gov_vault.userGovData(bob, ripe_token)
    assert ripe_token.balanceOf(ripe_gov_vault) == custody
    assert ripe_gov_vault.userBalances(bob, ripe_token) == 0
    assert ripe_gov_vault.totalBalances(ripe_token) == total_before - bob_shares
    assert ripe_gov_vault.userBalances(alice, ripe_token) == alice_shares
    assert claim(
        alice_shares,
        ripe_gov_vault.totalBalances(ripe_token),
        custody,
    ) > alice_claim_before
    assert points_after.balancePoints == (
        points_before.balancePoints + points_before.lastBalance * elapsed
    )
    assert points_after.lastBalance == 0
    assert gov_after.govPoints == gov_before.govPoints + expected_new_gov_points
    assert gov_after.lastShares == 0

    boa.env.time_travel(blocks=11)
    lootbox.updateDepositPoints(
        bob,
        VAULT_ID,
        ripe_gov_vault,
        ripe_token,
        sender=teller.address,
    )
    future_points = ledger.userDepositPoints(bob, VAULT_ID, ripe_token)
    assert future_points.balancePoints == points_after.balancePoints
    assert future_points.lastBalance == 0


def test_partial_exit_checkpoint_accrues_old_balance_then_uses_reduced_balance(
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    alice,
    teller,
    lootbox,
    ledger,
    mission_control,
    setAssetConfig,
    setRipeRewardsConfig,
    switchboard_alpha,
):
    _configure_asset(mission_control, setAssetConfig, switchboard_alpha, ripe_token)
    setRipeRewardsConfig(True)
    _deposit(ripe_gov_vault, ripe_token, whale, bob, 60 * EIGHTEEN_DECIMALS, teller)
    _deposit(ripe_gov_vault, ripe_token, whale, alice, 40 * EIGHTEEN_DECIMALS, teller)
    lootbox.updateDepositPoints(
        bob,
        VAULT_ID,
        ripe_gov_vault,
        ripe_token,
        sender=teller.address,
    )

    points_before = ledger.userDepositPoints(bob, VAULT_ID, ripe_token)
    assert points_before.lastBalance == ripe_gov_vault.getUserLootBoxShare(bob, ripe_token)
    boa.env.time_travel(blocks=17)
    first_elapsed = boa.env.evm.patch.block_number - points_before.lastUpdate

    ripe_gov_vault.releaseLock(bob, ripe_token, sender=teller.address)

    points_after = ledger.userDepositPoints(bob, VAULT_ID, ripe_token)
    post_burn_balance = ripe_gov_vault.getUserLootBoxShare(bob, ripe_token)
    assert 0 < post_burn_balance < points_before.lastBalance
    assert points_after.balancePoints == (
        points_before.balancePoints + points_before.lastBalance * first_elapsed
    )
    assert points_after.lastBalance == post_burn_balance

    boa.env.time_travel(blocks=11)
    second_elapsed = boa.env.evm.patch.block_number - points_after.lastUpdate
    lootbox.updateDepositPoints(
        bob,
        VAULT_ID,
        ripe_gov_vault,
        ripe_token,
        sender=teller.address,
    )
    future_points = ledger.userDepositPoints(bob, VAULT_ID, ripe_token)
    assert future_points.balancePoints == (
        points_after.balancePoints + post_burn_balance * second_elapsed
    )
    assert future_points.lastBalance == post_burn_balance


@pytest.mark.parametrize("exit_fee", (1, 99_99))
def test_exit_fee_boundaries_obey_exact_claim_invariant(
    exit_fee,
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    alice,
    teller,
    mission_control,
    setAssetConfig,
    switchboard_alpha,
):
    _configure_asset(
        mission_control,
        setAssetConfig,
        switchboard_alpha,
        ripe_token,
        exit_fee=exit_fee,
    )
    _deposit(ripe_gov_vault, ripe_token, whale, bob, 50 * EIGHTEEN_DECIMALS, teller)
    _deposit(ripe_gov_vault, ripe_token, whale, alice, 50 * EIGHTEEN_DECIMALS, teller)

    custody = ripe_token.balanceOf(ripe_gov_vault)
    total_before = ripe_gov_vault.totalBalances(ripe_token)
    bob_before = ripe_gov_vault.userBalances(bob, ripe_token)
    ripe_gov_vault.releaseLock(bob, ripe_token, sender=teller.address)

    bob_after = ripe_gov_vault.userBalances(bob, ripe_token)
    total_after = ripe_gov_vault.totalBalances(ripe_token)
    assert ripe_token.balanceOf(ripe_gov_vault) == custody
    assert total_before - total_after == bob_before - bob_after
    assert_exact_exit_claim(
        bob_before,
        total_before,
        custody,
        exit_fee,
        bob_after,
        total_after,
    )


def test_donation_heavy_state_uses_closest_attainable_claim_below_target(
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    alice,
    teller,
    mission_control,
    setAssetConfig,
    switchboard_alpha,
):
    _configure_asset(mission_control, setAssetConfig, switchboard_alpha, ripe_token)
    _deposit(ripe_gov_vault, ripe_token, whale, bob, 2, teller)
    _deposit(ripe_gov_vault, ripe_token, whale, alice, 1, teller)
    ripe_token.transfer(ripe_gov_vault, EIGHTEEN_DECIMALS, sender=whale)

    custody = ripe_token.balanceOf(ripe_gov_vault)
    total_before = ripe_gov_vault.totalBalances(ripe_token)
    bob_before = ripe_gov_vault.userBalances(bob, ripe_token)
    claim_before = claim(bob_before, total_before, custody)
    target = target_claim(claim_before, 10_00)

    ripe_gov_vault.releaseLock(bob, ripe_token, sender=teller.address)

    bob_after = ripe_gov_vault.userBalances(bob, ripe_token)
    total_after = ripe_gov_vault.totalBalances(ripe_token)
    claim_after = claim(bob_after, total_after, custody)
    assert_exact_exit_claim(
        bob_before,
        total_before,
        custody,
        10_00,
        bob_after,
        total_after,
    )
    assert target - claim_after > 1
    # The invariant is maximality, not one-asset-unit fee accuracy: burning one
    # fewer indivisible share is the next larger attainable state, and its
    # distinct claim exceeds the target.
    next_claim = claim(bob_after + 1, total_after + 1, custody)
    assert claim_after <= target < next_claim


def test_decimal_offset_significant_state_obeys_exact_claim_target(
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    alice,
    teller,
    mission_control,
    setAssetConfig,
    switchboard_alpha,
):
    _configure_asset(mission_control, setAssetConfig, switchboard_alpha, ripe_token)
    _deposit(ripe_gov_vault, ripe_token, whale, bob, 2, teller)
    _deposit(ripe_gov_vault, ripe_token, whale, alice, 1, teller)
    total_before = ripe_gov_vault.totalBalances(ripe_token)
    custody = ripe_token.balanceOf(ripe_gov_vault)
    bob_before = ripe_gov_vault.userBalances(bob, ripe_token)
    assert total_before == 3 * DECIMAL_OFFSET

    ripe_gov_vault.releaseLock(bob, ripe_token, sender=teller.address)

    bob_after = ripe_gov_vault.userBalances(bob, ripe_token)
    total_after = ripe_gov_vault.totalBalances(ripe_token)
    assert_exact_exit_claim(
        bob_before,
        total_before,
        custody,
        10_00,
        bob_after,
        total_after,
    )


def test_non_full_fee_zero_target_keeps_maximal_zero_claim_balance(
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    alice,
    teller,
    mission_control,
    setAssetConfig,
    switchboard_alpha,
):
    _configure_asset(
        mission_control,
        setAssetConfig,
        switchboard_alpha,
        ripe_token,
        exit_fee=99_99,
    )
    _deposit(ripe_gov_vault, ripe_token, whale, bob, 2, teller)
    _deposit(ripe_gov_vault, ripe_token, whale, alice, 1, teller)
    custody = ripe_token.balanceOf(ripe_gov_vault)
    total_before = ripe_gov_vault.totalBalances(ripe_token)
    bob_before = ripe_gov_vault.userBalances(bob, ripe_token)
    assert target_claim(claim(bob_before, total_before, custody), 99_99) == 0

    ripe_gov_vault.releaseLock(bob, ripe_token, sender=teller.address)

    bob_after = ripe_gov_vault.userBalances(bob, ripe_token)
    total_after = ripe_gov_vault.totalBalances(ripe_token)
    assert_exact_exit_claim(
        bob_before,
        total_before,
        custody,
        99_99,
        bob_after,
        total_after,
    )
    assert bob_after > 0


def test_early_exit_isolated_to_released_asset(
    ripe_gov_vault,
    ripe_token,
    bravo_token,
    bravo_token_whale,
    whale,
    bob,
    alice,
    teller,
    mission_control,
    setAssetConfig,
    switchboard_alpha,
):
    _configure_asset(mission_control, setAssetConfig, switchboard_alpha, ripe_token)
    _configure_asset(mission_control, setAssetConfig, switchboard_alpha, bravo_token)
    for token, funder in ((ripe_token, whale), (bravo_token, bravo_token_whale)):
        _deposit(ripe_gov_vault, token, funder, bob, 60 * EIGHTEEN_DECIMALS, teller)
        _deposit(ripe_gov_vault, token, funder, alice, 40 * EIGHTEEN_DECIMALS, teller)

    other_asset_before = (
        bravo_token.balanceOf(ripe_gov_vault),
        ripe_gov_vault.userBalances(bob, bravo_token),
        ripe_gov_vault.userBalances(alice, bravo_token),
        ripe_gov_vault.totalBalances(bravo_token),
        tuple(ripe_gov_vault.userGovData(bob, bravo_token)),
        tuple(ripe_gov_vault.userGovData(alice, bravo_token)),
    )

    ripe_gov_vault.releaseLock(bob, ripe_token, sender=teller.address)

    assert (
        bravo_token.balanceOf(ripe_gov_vault),
        ripe_gov_vault.userBalances(bob, bravo_token),
        ripe_gov_vault.userBalances(alice, bravo_token),
        ripe_gov_vault.totalBalances(bravo_token),
        tuple(ripe_gov_vault.userGovData(bob, bravo_token)),
        tuple(ripe_gov_vault.userGovData(alice, bravo_token)),
    ) == other_asset_before


def test_repeated_early_releases_remain_economically_coherent(
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    alice,
    teller,
    mission_control,
    setAssetConfig,
    switchboard_alpha,
):
    _configure_asset(mission_control, setAssetConfig, switchboard_alpha, ripe_token)
    _deposit(ripe_gov_vault, ripe_token, whale, bob, 70 * EIGHTEEN_DECIMALS, teller)
    _deposit(ripe_gov_vault, ripe_token, whale, alice, 30 * EIGHTEEN_DECIMALS, teller)

    for release_number in range(2):
        custody = ripe_token.balanceOf(ripe_gov_vault)
        total_before = ripe_gov_vault.totalBalances(ripe_token)
        bob_before = ripe_gov_vault.userBalances(bob, ripe_token)
        ripe_gov_vault.releaseLock(bob, ripe_token, sender=teller.address)

        bob_after = ripe_gov_vault.userBalances(bob, ripe_token)
        total_after = ripe_gov_vault.totalBalances(ripe_token)
        assert_exact_exit_claim(
            bob_before,
            total_before,
            custody,
            10_00,
            bob_after,
            total_after,
        )
        assert ripe_gov_vault.userGovData(bob, ripe_token).lastShares == bob_after

        if release_number == 0:
            ripe_gov_vault.adjustLock(bob, ripe_token, 500, sender=teller.address)


def test_independent_oracle_covers_virtual_term_denominator_boundary():
    user_shares = 2 * DECIMAL_OFFSET
    remaining_shares = DECIMAL_OFFSET
    total_balance = 3
    fee = 10_00
    pre_claim = claim(
        user_shares,
        user_shares + remaining_shares,
        total_balance,
    )
    target = target_claim(pre_claim, fee)

    expected = maximal_retained_shares(
        user_shares,
        remaining_shares,
        total_balance,
        target,
    )
    checked_result = checked_closed_form_retained_shares(
        user_shares,
        user_shares + remaining_shares,
        total_balance,
        fee,
    )

    assert checked_result == expected
    assert claim(
        expected,
        remaining_shares + expected,
        total_balance,
    ) <= target < claim(
        expected + 1,
        remaining_shares + expected + 1,
        total_balance,
    )


def test_checked_closed_form_matches_independent_oracle_on_bounded_grid():
    """Deterministically sweep ratios, fees, virtual terms, and share prices."""
    user_share_values = (1, DECIMAL_OFFSET // 2, DECIMAL_OFFSET, 5 * DECIMAL_OFFSET)
    remaining_share_values = (
        1,
        DECIMAL_OFFSET // 2,
        2 * DECIMAL_OFFSET,
        20 * DECIMAL_OFFSET,
    )
    balance_values = (1, 2, 10, DECIMAL_OFFSET, EIGHTEEN_DECIMALS)
    fee_values = (1, 1_00, 10_00, 50_00, 99_99, HUNDRED_PERCENT)
    covered = {
        "full_fee": False,
        "zero_target_non_full_fee": False,
        "nonzero_target": False,
        "virtual_share_significant": False,
        "high_share_price": False,
    }
    compared_cases = 0

    for user_shares in user_share_values:
        for remaining_shares in remaining_share_values:
            total_shares = user_shares + remaining_shares
            for total_balance in balance_values:
                claim_before = claim(user_shares, total_shares, total_balance)
                for exit_fee in fee_values:
                    if exit_fee == HUNDRED_PERCENT:
                        assert checked_closed_form_retained_shares(
                            user_shares,
                            total_shares,
                            total_balance,
                            exit_fee,
                        ) == 0
                        covered["full_fee"] = True
                        continue

                    if claim_before == 0:
                        with pytest.raises(ValueError, match="no claim"):
                            checked_closed_form_retained_shares(
                                user_shares,
                                total_shares,
                                total_balance,
                                exit_fee,
                            )
                        continue

                    target = target_claim(claim_before, exit_fee)
                    expected = maximal_retained_shares(
                        user_shares,
                        remaining_shares,
                        total_balance,
                        target,
                    )
                    actual = checked_closed_form_retained_shares(
                        user_shares,
                        total_shares,
                        total_balance,
                        exit_fee,
                    )
                    assert actual == expected
                    assert claim(
                        actual,
                        remaining_shares + actual,
                        total_balance,
                    ) <= target
                    if actual < user_shares:
                        assert target < claim(
                            actual + 1,
                            remaining_shares + actual + 1,
                            total_balance,
                        )

                    compared_cases += 1
                    covered["zero_target_non_full_fee"] |= target == 0
                    covered["nonzero_target"] |= target != 0
                    covered["virtual_share_significant"] |= (
                        total_shares <= DECIMAL_OFFSET
                    )
                    covered["high_share_price"] |= total_balance > total_shares

    assert compared_cases > 100
    assert all(covered.values())


@pytest.mark.parametrize(
    ("operation", "args"),
    (
        pytest.param(
            checked_shares_to_amount,
            (1, 1, UINT256_MAX),
            id="asset-virtual-term-addition",
        ),
        pytest.param(
            checked_shares_to_amount,
            (2, 2, UINT256_MAX - 1),
            id="claim-numerator-multiplication",
        ),
        pytest.param(
            checked_shares_to_amount,
            (1, UINT256_MAX, 0),
            id="share-denominator-addition",
        ),
        pytest.param(
            checked_target_claim,
            (UINT256_MAX, 1),
            id="target-numerator-multiplication",
        ),
        pytest.param(
            checked_amount_to_shares,
            (2, UINT256_MAX - DECIMAL_OFFSET, 0, False),
            id="inverse-numerator-multiplication",
        ),
        pytest.param(
            checked_closed_form_retained_shares,
            (1, UINT256_MAX, 0, 1),
            id="closed-form-denominator-boundary",
        ),
    ),
)
def test_checked_uint256_model_rejects_extreme_arithmetic_overflow(operation, args):
    with pytest.raises(UInt256Overflow):
        operation(*args)
