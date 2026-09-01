import boa
import pytest

from constants import EIGHTEEN_DECIMALS, MAX_UINT256


def _configure_frozen_borrow_rewards(setGeneralConfig, setRipeRewardsConfig):
    setGeneralConfig()
    setRipeRewardsConfig(
        _arePointsEnabled=False,
        _ripePerBlock=0,
        _borrowersAlloc=100_00,
        _stakersAlloc=0,
        _votersAlloc=0,
        _genDepositorsAlloc=0,
    )


def _seed_borrow_state(
    ledger,
    lootbox,
    user,
    borrower_bucket,
    user_points,
    global_points,
    user_last_principal=0,
    global_last_principal=0,
):
    block_number = boa.env.evm.patch.block_number
    ledger.setBorrowPointsAndRipeRewards(
        user,
        (user_last_principal, user_points, block_number),
        (global_last_principal, global_points, block_number),
        (borrower_bucket, 0, 0, 0, 0, block_number),
        sender=lootbox.address,
    )


def test_sub_basis_point_borrower_receives_exact_nonzero_share(
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    ripe_token,
):
    _configure_frozen_borrow_rewards(setGeneralConfig, setRipeRewardsConfig)
    borrower_bucket = 10**12
    user_points = 99
    global_points = 1_000_000
    expected = borrower_bucket * user_points // global_points
    assert user_points * 10_000 < global_points
    assert expected > 0

    _seed_borrow_state(
        ledger,
        lootbox,
        bob,
        borrower_bucket,
        user_points,
        global_points,
    )

    balance_before = ripe_token.balanceOf(bob)
    assert lootbox.getClaimableBorrowLoot(bob) == expected
    assert lootbox.claimBorrowLoot(bob, sender=teller.address) == expected
    assert ripe_token.balanceOf(bob) - balance_before == expected
    assert ledger.userBorrowPoints(bob).points == 0
    assert ledger.globalBorrowPoints().points == global_points - user_points
    remaining_bucket = ledger.getRipeRewardsBundle().ripeRewards.borrowers
    assert remaining_bucket == borrower_bucket - expected
    assert expected + remaining_bucket == borrower_bucket


def test_exact_borrow_share_composes_with_live_point_accrual(
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
):
    setGeneralConfig()
    setRipeRewardsConfig(
        _arePointsEnabled=True,
        _ripePerBlock=0,
        _borrowersAlloc=100_00,
        _stakersAlloc=0,
        _votersAlloc=0,
        _genDepositorsAlloc=0,
    )
    borrower_bucket = 10**12
    initial_user_points = 199
    initial_global_points = 1_000_000
    user_last_principal = 1
    global_last_principal = 1_000
    elapsed_blocks = 10
    debt_principal = user_last_principal * EIGHTEEN_DECIMALS
    ledger.setUserDebt(
        bob,
        (debt_principal, debt_principal, createDebtTerms(), 0, False),
        0,
        (0, 0),
        sender=credit_engine.address,
    )
    _seed_borrow_state(
        ledger,
        lootbox,
        bob,
        borrower_bucket,
        initial_user_points,
        initial_global_points,
        user_last_principal,
        global_last_principal,
    )

    boa.env.time_travel(blocks=elapsed_blocks)
    accrued_user_points = initial_user_points + user_last_principal * elapsed_blocks
    accrued_global_points = initial_global_points + global_last_principal * elapsed_blocks
    expected = borrower_bucket * accrued_user_points // accrued_global_points

    assert lootbox.getClaimableBorrowLoot(bob) == expected
    assert lootbox.claimBorrowLoot(bob, sender=teller.address) == expected
    user_points_after = ledger.userBorrowPoints(bob)
    global_points_after = ledger.globalBorrowPoints()
    assert user_points_after.points == 0
    assert user_points_after.lastPrincipal == user_last_principal
    assert global_points_after.points == accrued_global_points - accrued_user_points
    assert global_points_after.lastPrincipal == global_last_principal
    assert ledger.getRipeRewardsBundle().ripeRewards.borrowers == borrower_bucket - expected


def test_truncated_threshold_claim_consumes_only_exact_proportional_state(
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
):
    _configure_frozen_borrow_rewards(setGeneralConfig, setRipeRewardsConfig)
    borrower_bucket = 10**12
    user_points = 199
    global_points = 1_000_000
    expected = borrower_bucket * user_points // global_points
    old_one_basis_point_payout = borrower_bucket // 10_000
    assert expected != old_one_basis_point_payout

    _seed_borrow_state(
        ledger,
        lootbox,
        bob,
        borrower_bucket,
        user_points,
        global_points,
    )

    assert lootbox.getClaimableBorrowLoot(bob) == expected
    assert lootbox.claimBorrowLoot(bob, sender=teller.address) == expected
    assert ledger.userBorrowPoints(bob).points == 0
    assert ledger.globalBorrowPoints().points == global_points - user_points
    remaining_bucket = ledger.getRipeRewardsBundle().ripeRewards.borrowers
    assert remaining_bucket == borrower_bucket - expected
    assert expected + remaining_bucket == borrower_bucket


def test_borrow_claim_order_is_independent_except_for_integer_dust(
    bob,
    alice,
    charlie,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
):
    _configure_frozen_borrow_rewards(setGeneralConfig, setRipeRewardsConfig)
    borrower_bucket = 10**18 + 7
    points = {
        bob: 99,
        alice: 333_333,
        charlie: 666_568,
    }
    global_points = sum(points.values())
    exact = {
        user: borrower_bucket * user_points // global_points
        for user, user_points in points.items()
    }
    assert points[bob] * 10_000 < global_points

    for user, user_points in points.items():
        _seed_borrow_state(
            ledger,
            lootbox,
            user,
            borrower_bucket,
            user_points,
            global_points,
        )

    outcomes = []
    for order in ((bob, alice, charlie), (charlie, alice, bob)):
        with boa.env.anchor():
            claims = {
                user: lootbox.claimBorrowLoot(user, sender=teller.address)
                for user in order
            }
            remaining = ledger.getRipeRewardsBundle().ripeRewards.borrowers
            assert sum(claims.values()) + remaining == borrower_bucket
            assert ledger.globalBorrowPoints().points == 0
            for user in points:
                assert abs(claims[user] - exact[user]) <= 1
            assert claims[bob] > 0
            outcomes.append(claims)

    for user in points:
        assert abs(outcomes[0][user] - outcomes[1][user]) <= 1
    assert outcomes[0][bob] < borrower_bucket // 10_000
    assert outcomes[1][bob] < borrower_bucket // 10_000


def test_borrow_view_and_mutation_are_consistent(
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    ripe_token,
):
    _configure_frozen_borrow_rewards(setGeneralConfig, setRipeRewardsConfig)
    borrower_bucket = 987_654_321
    user_points = 37
    global_points = 1_000
    expected = borrower_bucket * user_points // global_points
    _seed_borrow_state(
        ledger,
        lootbox,
        bob,
        borrower_bucket,
        user_points,
        global_points,
    )

    balance_before = ripe_token.balanceOf(bob)
    claimable = lootbox.getClaimableBorrowLoot(bob)
    claimed = lootbox.claimBorrowLoot(bob, sender=teller.address)

    assert claimable == expected
    assert claimed == claimable
    assert ripe_token.balanceOf(bob) - balance_before == claimed
    assert ledger.getRipeRewardsBundle().ripeRewards.borrowers == borrower_bucket - claimed


@pytest.mark.parametrize(
    "borrower_bucket,user_points,global_points,expected,remaining_user_points,remaining_global_points,remaining_bucket",
    (
        (0, 5, 10, 0, 5, 10, 0),
        (100, 0, 10, 0, 0, 10, 100),
        (100, 5, 0, 0, 5, 0, 100),
        (777, 101, 100, 777, 0, 0, 0),
        (777, 100, 100, 777, 0, 0, 0),
        (1, 1, 2, 0, 1, 2, 1),
    ),
)
def test_borrow_claim_edge_behavior(
    borrower_bucket,
    user_points,
    global_points,
    expected,
    remaining_user_points,
    remaining_global_points,
    remaining_bucket,
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
):
    _configure_frozen_borrow_rewards(setGeneralConfig, setRipeRewardsConfig)
    _seed_borrow_state(
        ledger,
        lootbox,
        bob,
        borrower_bucket,
        user_points,
        global_points,
    )

    assert lootbox.getClaimableBorrowLoot(bob) == expected
    assert lootbox.claimBorrowLoot(bob, sender=teller.address) == expected
    assert ledger.userBorrowPoints(bob).points == remaining_user_points
    assert ledger.globalBorrowPoints().points == remaining_global_points
    assert ledger.getRipeRewardsBundle().ripeRewards.borrowers == remaining_bucket


@pytest.mark.parametrize(
    "borrower_bucket,user_points,global_points",
    (
        (100, 1, 10),
        (99, 1, 10),
        (101, 1, 10),
        (1_234_567, 999_999, 1_000_000),
    ),
)
def test_partial_share_arithmetic_boundaries_use_exact_floor(
    borrower_bucket,
    user_points,
    global_points,
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
):
    _configure_frozen_borrow_rewards(setGeneralConfig, setRipeRewardsConfig)
    assert 0 < user_points < global_points
    expected = borrower_bucket * user_points // global_points
    _seed_borrow_state(
        ledger,
        lootbox,
        bob,
        borrower_bucket,
        user_points,
        global_points,
    )

    assert lootbox.getClaimableBorrowLoot(bob) == expected
    assert lootbox.claimBorrowLoot(bob, sender=teller.address) == expected
    assert ledger.userBorrowPoints(bob).points == 0
    assert ledger.globalBorrowPoints().points == global_points - user_points
    assert ledger.getRipeRewardsBundle().ripeRewards.borrowers == borrower_bucket - expected


def test_large_partial_share_uses_full_precision_mul_div(
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    ripe_token,
):
    _configure_frozen_borrow_rewards(setGeneralConfig, setRipeRewardsConfig)
    borrower_bucket = 10**24
    user_points = 10**62
    global_points = 10**63
    assert user_points < global_points
    # This basis-point-exact ratio does not distinguish the legacy formula. It
    # protects the partial-share path from a future checked x * y rewrite.
    assert borrower_bucket * user_points > MAX_UINT256
    expected = borrower_bucket * user_points // global_points
    assert expected <= MAX_UINT256
    _seed_borrow_state(
        ledger,
        lootbox,
        bob,
        borrower_bucket,
        user_points,
        global_points,
    )

    balance_before = ripe_token.balanceOf(bob)
    assert lootbox.getClaimableBorrowLoot(bob) == expected
    assert lootbox.claimBorrowLoot(bob, sender=teller.address) == expected
    assert ripe_token.balanceOf(bob) - balance_before == expected
    assert ledger.userBorrowPoints(bob).points == 0
    assert ledger.globalBorrowPoints().points == global_points - user_points
    remaining_bucket = ledger.getRipeRewardsBundle().ripeRewards.borrowers
    assert remaining_bucket == borrower_bucket - expected
    assert expected + remaining_bucket == borrower_bucket
