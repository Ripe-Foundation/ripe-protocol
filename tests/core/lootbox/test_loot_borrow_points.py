import boa

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS


def test_loot_borrow_points_basic(
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
):
    # basic setup
    setGeneralConfig()
    setRipeRewardsConfig(True)

    # set up user debt
    debt_terms = createDebtTerms()
    user_debt = (100 * EIGHTEEN_DECIMALS, 100 * EIGHTEEN_DECIMALS, debt_terms, 0, False)
    ledger.setUserDebt(bob, user_debt, 0, (0, 0), sender=credit_engine.address)

    # First update
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Time travel
    elapsed = 20
    boa.env.time_travel(blocks=elapsed)

    # Update again
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Check results
    up = ledger.userBorrowPoints(bob)
    gp = ledger.globalBorrowPoints()
    
    # User points should be debt * elapsed
    assert up.points == (100 * EIGHTEEN_DECIMALS // EIGHTEEN_DECIMALS) * elapsed
    assert up.lastPrincipal == 100 * EIGHTEEN_DECIMALS // EIGHTEEN_DECIMALS
    assert up.lastUpdate == boa.env.evm.patch.block_number

    # Global points should match user points (only one user)
    assert gp.points == up.points
    assert gp.lastPrincipal == up.lastPrincipal
    assert gp.lastUpdate == boa.env.evm.patch.block_number


def test_loot_borrow_points_debt_changes(
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
):
    # basic setup
    setGeneralConfig()
    setRipeRewardsConfig(True)

    # Initial debt
    debt_terms = createDebtTerms()
    initial_debt = (100 * EIGHTEEN_DECIMALS, 100 * EIGHTEEN_DECIMALS, debt_terms, 0, False)
    ledger.setUserDebt(bob, initial_debt, 0, (0, 0), sender=credit_engine.address)

    # First update
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Time travel
    elapsed1 = 10
    boa.env.time_travel(blocks=elapsed1)

    # Increase debt
    increased_debt = (200 * EIGHTEEN_DECIMALS, 200 * EIGHTEEN_DECIMALS, debt_terms, 0, False)
    ledger.setUserDebt(bob, increased_debt, 0, (0, 0), sender=credit_engine.address)
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Time travel
    elapsed2 = 10
    boa.env.time_travel(blocks=elapsed2)

    # Update again
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Check results
    up = ledger.userBorrowPoints(bob)
    gp = ledger.globalBorrowPoints()
    
    # Points should be (initial_debt * elapsed1) + (increased_debt * elapsed2)
    expected_points = (100 * elapsed1) + (200 * elapsed2)
    assert up.points == expected_points
    assert up.lastPrincipal == 200  # Last principal should be increased debt
    assert gp.points == expected_points
    assert gp.lastPrincipal == 200


def test_loot_borrow_points_disabled(
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
):
    # basic setup with points disabled
    setGeneralConfig()
    setRipeRewardsConfig(False)

    # set up user debt
    debt_terms = createDebtTerms()
    user_debt = (100 * EIGHTEEN_DECIMALS, 100 * EIGHTEEN_DECIMALS, debt_terms, 0, False)
    ledger.setUserDebt(bob, user_debt, 0, (0, 0), sender=credit_engine.address)

    # First update
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Time travel
    elapsed = 20
    boa.env.time_travel(blocks=elapsed)

    # Update again
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Check results - no points should accumulate when disabled
    up = ledger.userBorrowPoints(bob)
    gp = ledger.globalBorrowPoints()
    
    assert up.points == 0
    assert up.lastPrincipal == 100  # Principal should still be tracked
    assert gp.points == 0
    assert gp.lastPrincipal == 100


def test_loot_borrow_points_multiple_users(
    bob,
    alice,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
):
    # basic setup
    setGeneralConfig()
    setRipeRewardsConfig(True)

    # set up user debts
    debt_terms = createDebtTerms()
    bob_debt = (100 * EIGHTEEN_DECIMALS, 100 * EIGHTEEN_DECIMALS, debt_terms, 0, False)
    alice_debt = (200 * EIGHTEEN_DECIMALS, 200 * EIGHTEEN_DECIMALS, debt_terms, 0, False)
    ledger.setUserDebt(bob, bob_debt, 0, (0, 0), sender=credit_engine.address)
    ledger.setUserDebt(alice, alice_debt, 0, (0, 0), sender=credit_engine.address)

    # First update for both users
    lootbox.updateBorrowPoints(bob, sender=teller.address)
    lootbox.updateBorrowPoints(alice, sender=teller.address)

    # Time travel
    elapsed = 20
    boa.env.time_travel(blocks=elapsed)

    # Update both users again
    lootbox.updateBorrowPoints(bob, sender=teller.address)
    lootbox.updateBorrowPoints(alice, sender=teller.address)

    # Check results
    up_bob = ledger.userBorrowPoints(bob)
    up_alice = ledger.userBorrowPoints(alice)
    gp = ledger.globalBorrowPoints()
    
    # Bob's points
    assert up_bob.points == 100 * elapsed
    assert up_bob.lastPrincipal == 100

    # Alice's points
    assert up_alice.points == 200 * elapsed
    assert up_alice.lastPrincipal == 200

    # Global points should be sum of both users
    assert gp.points == (100 + 200) * elapsed
    assert gp.lastPrincipal == 300  # Sum of both principals


def test_loot_borrow_points_zero_debt(
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
):
    # basic setup
    setGeneralConfig()
    setRipeRewardsConfig(True)

    # set up initial debt
    debt_terms = createDebtTerms()
    initial_debt = (100 * EIGHTEEN_DECIMALS, 100 * EIGHTEEN_DECIMALS, debt_terms, 0, False)
    ledger.setUserDebt(bob, initial_debt, 0, (0, 0), sender=credit_engine.address)

    # First update
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Time travel
    elapsed1 = 10
    boa.env.time_travel(blocks=elapsed1)

    # Set debt to zero
    zero_debt = (0, 0, debt_terms, 0, False)
    ledger.setUserDebt(bob, zero_debt, 0, (0, 0), sender=credit_engine.address)
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Time travel
    elapsed2 = 10
    boa.env.time_travel(blocks=elapsed2)

    # Update again
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Check results
    up = ledger.userBorrowPoints(bob)
    gp = ledger.globalBorrowPoints()
    
    # Points should only accumulate for first period
    assert up.points == 100 * elapsed1
    assert up.lastPrincipal == 0  # Last principal should be zero
    assert gp.points == 100 * elapsed1
    assert gp.lastPrincipal == 0


def test_loot_borrow_points_large_numbers(
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
):
    # basic setup
    setGeneralConfig()
    setRipeRewardsConfig(True)

    # set up very large debt
    debt_terms = createDebtTerms()
    large_debt = (1000000 * EIGHTEEN_DECIMALS, 1000000 * EIGHTEEN_DECIMALS, debt_terms, 0, False)
    ledger.setUserDebt(bob, large_debt, 0, (0, 0), sender=credit_engine.address)

    # First update
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Time travel
    elapsed = 1000
    boa.env.time_travel(blocks=elapsed)

    # Update again
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Check results
    up = ledger.userBorrowPoints(bob)
    gp = ledger.globalBorrowPoints()
    
    # Points should be large_debt * elapsed
    expected_points = 1000000 * elapsed
    assert up.points == expected_points
    assert up.lastPrincipal == 1000000
    assert gp.points == expected_points
    assert gp.lastPrincipal == 1000000


def test_loot_borrow_points_permission_checks(
    bob,
    alice,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
    switchboard_alpha,
):
    # basic setup
    setGeneralConfig()
    setRipeRewardsConfig(True)

    # set up user debt
    debt_terms = createDebtTerms()
    user_debt = (100 * EIGHTEEN_DECIMALS, 100 * EIGHTEEN_DECIMALS, debt_terms, 0, False)
    ledger.setUserDebt(bob, user_debt, 0, (0, 0), sender=credit_engine.address)

    # Test unauthorized caller
    with boa.reverts("no perms"):
        lootbox.updateBorrowPoints(bob, sender=alice)

    # Test paused state
    lootbox.pause(True, sender=switchboard_alpha.address)
    with boa.reverts("contract paused"):
        lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Unpause and verify it works
    lootbox.pause(False, sender=switchboard_alpha.address)
    lootbox.updateBorrowPoints(bob, sender=teller.address)


def test_loot_borrow_points_rapid_debt_changes(
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
    setRipeRewardsConfig(True)
    debt_terms = createDebtTerms()
    # Set initial debt
    ledger.setUserDebt(bob, (100 * EIGHTEEN_DECIMALS, 100 * EIGHTEEN_DECIMALS, debt_terms, 0, False), 0, (0, 0), sender=credit_engine.address)
    lootbox.updateBorrowPoints(bob, sender=teller.address)
    # Change debt multiple times before next update
    boa.env.time_travel(blocks=5)
    ledger.setUserDebt(bob, (200 * EIGHTEEN_DECIMALS, 200 * EIGHTEEN_DECIMALS, debt_terms, 0, False), 0, (0, 0), sender=credit_engine.address)
    ledger.setUserDebt(bob, (300 * EIGHTEEN_DECIMALS, 300 * EIGHTEEN_DECIMALS, debt_terms, 0, False), 0, (0, 0), sender=credit_engine.address)
    lootbox.updateBorrowPoints(bob, sender=teller.address)
    up = ledger.userBorrowPoints(bob)
    assert up.points == 100 * 5
    assert up.lastPrincipal == 300


def test_loot_borrow_points_staggered_user_updates(
    bob,
    alice,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
):
    setGeneralConfig()
    setRipeRewardsConfig(True)
    debt_terms = createDebtTerms()
    ledger.setUserDebt(bob, (100 * EIGHTEEN_DECIMALS, 100 * EIGHTEEN_DECIMALS, debt_terms, 0, False), 0, (0, 0), sender=credit_engine.address)
    ledger.setUserDebt(alice, (200 * EIGHTEEN_DECIMALS, 200 * EIGHTEEN_DECIMALS, debt_terms, 0, False), 0, (0, 0), sender=credit_engine.address)
    lootbox.updateBorrowPoints(bob, sender=teller.address)
    lootbox.updateBorrowPoints(alice, sender=teller.address)
    # Bob updates every 5 blocks, Alice only after 20
    boa.env.time_travel(blocks=5)
    lootbox.updateBorrowPoints(bob, sender=teller.address)
    boa.env.time_travel(blocks=5)
    lootbox.updateBorrowPoints(bob, sender=teller.address)
    boa.env.time_travel(blocks=10)
    lootbox.updateBorrowPoints(alice, sender=teller.address)
    up_bob = ledger.userBorrowPoints(bob)
    up_alice = ledger.userBorrowPoints(alice)
    # Bob: 100*5 + 100*5 = 100*10
    # Alice: 200*20
    assert up_bob.points == 100 * 10
    assert up_alice.points == 200 * 20


def test_loot_borrow_points_enabled_disabled_transitions(
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
    setRipeRewardsConfig(True)
    debt_terms = createDebtTerms()
    ledger.setUserDebt(bob, (100 * EIGHTEEN_DECIMALS, 100 * EIGHTEEN_DECIMALS, debt_terms, 0, False), 0, (0, 0), sender=credit_engine.address)
    lootbox.updateBorrowPoints(bob, sender=teller.address)
    boa.env.time_travel(blocks=10)
    lootbox.updateBorrowPoints(bob, sender=teller.address)
    # Disable points
    setRipeRewardsConfig(False)
    boa.env.time_travel(blocks=10)
    lootbox.updateBorrowPoints(bob, sender=teller.address)
    # Re-enable points
    setRipeRewardsConfig(True)
    boa.env.time_travel(blocks=10)
    lootbox.updateBorrowPoints(bob, sender=teller.address)
    up = ledger.userBorrowPoints(bob)
    # Only periods with points enabled should count
    assert up.points == 100 * 20


def test_loot_borrow_points_global_zero_debt(
    bob,
    alice,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
):
    setGeneralConfig()
    setRipeRewardsConfig(True)
    debt_terms = createDebtTerms()
    ledger.setUserDebt(bob, (100 * EIGHTEEN_DECIMALS, 100 * EIGHTEEN_DECIMALS, debt_terms, 0, False), 0, (0, 0), sender=credit_engine.address)
    ledger.setUserDebt(alice, (200 * EIGHTEEN_DECIMALS, 200 * EIGHTEEN_DECIMALS, debt_terms, 0, False), 0, (0, 0), sender=credit_engine.address)
    lootbox.updateBorrowPoints(bob, sender=teller.address)
    lootbox.updateBorrowPoints(alice, sender=teller.address)
    boa.env.time_travel(blocks=10)
    # Set both debts to zero
    ledger.setUserDebt(bob, (0, 0, debt_terms, 0, False), 0, (0, 0), sender=credit_engine.address)
    ledger.setUserDebt(alice, (0, 0, debt_terms, 0, False), 0, (0, 0), sender=credit_engine.address)
    lootbox.updateBorrowPoints(bob, sender=teller.address)
    lootbox.updateBorrowPoints(alice, sender=teller.address)
    gp = ledger.globalBorrowPoints()
    # Global points should be sum of both users' points
    assert gp.points == (100 + 200) * 10
    assert gp.lastPrincipal == 0


def test_loot_borrow_points_multiple_updates_same_block(
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
    setRipeRewardsConfig(True)
    debt_terms = createDebtTerms()
    ledger.setUserDebt(bob, (100 * EIGHTEEN_DECIMALS, 100 * EIGHTEEN_DECIMALS, debt_terms, 0, False), 0, (0, 0), sender=credit_engine.address)
    lootbox.updateBorrowPoints(bob, sender=teller.address)
    # Call update again in the same block
    lootbox.updateBorrowPoints(bob, sender=teller.address)
    up = ledger.userBorrowPoints(bob)
    # Points should not double-count for the same block
    assert up.points == 0


# reset borrow points


def test_reset_user_borrow_points_basic(
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
    switchboard_alpha,
):
    # basic setup
    setGeneralConfig()
    setRipeRewardsConfig(True)

    # set up user debt
    debt_terms = createDebtTerms()
    user_debt = (100 * EIGHTEEN_DECIMALS, 100 * EIGHTEEN_DECIMALS, debt_terms, 0, False)
    ledger.setUserDebt(bob, user_debt, 0, (0, 0), sender=credit_engine.address)

    # First update
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Time travel to accumulate points
    elapsed = 20
    boa.env.time_travel(blocks=elapsed)

    # Update again to finalize points
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Check points before reset
    up_before = ledger.userBorrowPoints(bob)
    gp_before = ledger.globalBorrowPoints()
    
    assert up_before.points == 100 * elapsed
    assert gp_before.points == 100 * elapsed

    # Reset user borrow points
    lootbox.resetUserBorrowPoints(bob, sender=switchboard_alpha.address)

    # Check points after reset
    up_after = ledger.userBorrowPoints(bob)
    gp_after = ledger.globalBorrowPoints()
    
    # User points should be reset to 0
    assert up_after.points == 0
    assert up_after.lastPrincipal == 100  # Principal should remain unchanged
    assert up_after.lastUpdate == boa.env.evm.patch.block_number
    
    # Global points should be reduced by the user's points
    assert gp_after.points == 0  # Since bob was the only user
    assert gp_after.lastPrincipal == 100
    assert gp_after.lastUpdate == boa.env.evm.patch.block_number


def test_reset_user_borrow_points_multiple_users(
    bob,
    alice,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
    switchboard_alpha,
):
    # basic setup
    setGeneralConfig()
    setRipeRewardsConfig(True)

    # set up user debts
    debt_terms = createDebtTerms()
    bob_debt = (100 * EIGHTEEN_DECIMALS, 100 * EIGHTEEN_DECIMALS, debt_terms, 0, False)
    alice_debt = (200 * EIGHTEEN_DECIMALS, 200 * EIGHTEEN_DECIMALS, debt_terms, 0, False)
    ledger.setUserDebt(bob, bob_debt, 0, (0, 0), sender=credit_engine.address)
    ledger.setUserDebt(alice, alice_debt, 0, (0, 0), sender=credit_engine.address)

    # First update for both users
    lootbox.updateBorrowPoints(bob, sender=teller.address)
    lootbox.updateBorrowPoints(alice, sender=teller.address)

    # Time travel
    elapsed = 20
    boa.env.time_travel(blocks=elapsed)

    # Update both users again
    lootbox.updateBorrowPoints(bob, sender=teller.address)
    lootbox.updateBorrowPoints(alice, sender=teller.address)

    # Check points before reset
    up_bob = ledger.userBorrowPoints(bob)
    up_alice = ledger.userBorrowPoints(alice)
    gp_before = ledger.globalBorrowPoints()
    
    assert up_bob.points == 100 * elapsed
    assert up_alice.points == 200 * elapsed
    assert gp_before.points == 300 * elapsed

    # Reset only Bob's points
    lootbox.resetUserBorrowPoints(bob, sender=switchboard_alpha.address)

    # Check points after reset
    up_bob_after = ledger.userBorrowPoints(bob)
    up_alice_after = ledger.userBorrowPoints(alice)
    gp_after = ledger.globalBorrowPoints()
    
    # Bob's points should be reset
    assert up_bob_after.points == 0
    assert up_bob_after.lastPrincipal == 100
    
    # Alice's points should remain unchanged
    assert up_alice_after.points == 200 * elapsed
    assert up_alice_after.lastPrincipal == 200
    
    # Global points should only be reduced by Bob's points
    assert gp_after.points == 200 * elapsed  # Only Alice's points remain
    assert gp_after.lastPrincipal == 300  # Total principal unchanged


def test_reset_user_borrow_points_permissions(
    bob,
    alice,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
    switchboard_alpha,
):
    # basic setup
    setGeneralConfig()
    setRipeRewardsConfig(True)

    # set up user debt
    debt_terms = createDebtTerms()
    user_debt = (100 * EIGHTEEN_DECIMALS, 100 * EIGHTEEN_DECIMALS, debt_terms, 0, False)
    ledger.setUserDebt(bob, user_debt, 0, (0, 0), sender=credit_engine.address)

    # Accumulate some points
    lootbox.updateBorrowPoints(bob, sender=teller.address)
    boa.env.time_travel(blocks=20)
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Test unauthorized caller
    with boa.reverts("no perms"):
        lootbox.resetUserBorrowPoints(bob, sender=alice)
    
    # Test unauthorized caller (teller)
    with boa.reverts("no perms"):
        lootbox.resetUserBorrowPoints(bob, sender=teller.address)

    # Test paused state
    lootbox.pause(True, sender=switchboard_alpha.address)
    with boa.reverts("contract paused"):
        lootbox.resetUserBorrowPoints(bob, sender=switchboard_alpha.address)

    # Unpause and verify it works
    lootbox.pause(False, sender=switchboard_alpha.address)
    lootbox.resetUserBorrowPoints(bob, sender=switchboard_alpha.address)
    
    up = ledger.userBorrowPoints(bob)
    assert up.points == 0


def test_reset_user_borrow_points_zero_points(
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
    switchboard_alpha,
):
    # basic setup
    setGeneralConfig()
    setRipeRewardsConfig(True)

    # set up user debt
    debt_terms = createDebtTerms()
    user_debt = (100 * EIGHTEEN_DECIMALS, 100 * EIGHTEEN_DECIMALS, debt_terms, 0, False)
    ledger.setUserDebt(bob, user_debt, 0, (0, 0), sender=credit_engine.address)

    # First update (no points accumulated yet)
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Reset when user has zero points
    lootbox.resetUserBorrowPoints(bob, sender=switchboard_alpha.address)

    # Check results
    up = ledger.userBorrowPoints(bob)
    gp = ledger.globalBorrowPoints()
    
    assert up.points == 0
    assert up.lastPrincipal == 100
    assert gp.points == 0
    assert gp.lastPrincipal == 100


def test_reset_user_borrow_points_empty_address(
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    switchboard_alpha,
):
    # basic setup
    setGeneralConfig()
    setRipeRewardsConfig(True)

    # Get initial global points
    gp_before = ledger.globalBorrowPoints()

    # Call reset with empty address - should return early
    lootbox.resetUserBorrowPoints(ZERO_ADDRESS, sender=switchboard_alpha.address)

    # Global points should remain unchanged
    gp_after = ledger.globalBorrowPoints()
    assert gp_after.points == gp_before.points
    assert gp_after.lastPrincipal == gp_before.lastPrincipal


def test_reset_user_borrow_points_after_debt_change(
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
    switchboard_alpha,
):
    # basic setup
    setGeneralConfig()
    setRipeRewardsConfig(True)

    # Initial debt
    debt_terms = createDebtTerms()
    initial_debt = (100 * EIGHTEEN_DECIMALS, 100 * EIGHTEEN_DECIMALS, debt_terms, 0, False)
    ledger.setUserDebt(bob, initial_debt, 0, (0, 0), sender=credit_engine.address)

    # First update
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Time travel
    elapsed1 = 10
    boa.env.time_travel(blocks=elapsed1)

    # Increase debt
    increased_debt = (200 * EIGHTEEN_DECIMALS, 200 * EIGHTEEN_DECIMALS, debt_terms, 0, False)
    ledger.setUserDebt(bob, increased_debt, 0, (0, 0), sender=credit_engine.address)
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Time travel
    elapsed2 = 10
    boa.env.time_travel(blocks=elapsed2)

    # Update again
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Check accumulated points
    up_before = ledger.userBorrowPoints(bob)
    expected_points = (100 * elapsed1) + (200 * elapsed2)
    assert up_before.points == expected_points

    # Reset points
    lootbox.resetUserBorrowPoints(bob, sender=switchboard_alpha.address)

    # Check after reset
    up_after = ledger.userBorrowPoints(bob)
    gp_after = ledger.globalBorrowPoints()
    
    assert up_after.points == 0
    assert up_after.lastPrincipal == 200  # Should maintain current principal
    assert gp_after.points == 0


def test_reset_user_borrow_points_consecutive_resets(
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
    switchboard_alpha,
):
    # basic setup
    setGeneralConfig()
    setRipeRewardsConfig(True)

    # set up user debt
    debt_terms = createDebtTerms()
    user_debt = (100 * EIGHTEEN_DECIMALS, 100 * EIGHTEEN_DECIMALS, debt_terms, 0, False)
    ledger.setUserDebt(bob, user_debt, 0, (0, 0), sender=credit_engine.address)

    # Accumulate points
    lootbox.updateBorrowPoints(bob, sender=teller.address)
    boa.env.time_travel(blocks=20)
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # First reset
    lootbox.resetUserBorrowPoints(bob, sender=switchboard_alpha.address)
    
    up_after_first = ledger.userBorrowPoints(bob)
    assert up_after_first.points == 0

    # Second reset immediately
    lootbox.resetUserBorrowPoints(bob, sender=switchboard_alpha.address)
    
    up_after_second = ledger.userBorrowPoints(bob)
    assert up_after_second.points == 0

    # Accumulate more points
    boa.env.time_travel(blocks=10)
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    up_after_accumulation = ledger.userBorrowPoints(bob)
    assert up_after_accumulation.points == 100 * 10

    # Reset again
    lootbox.resetUserBorrowPoints(bob, sender=switchboard_alpha.address)
    
    up_final = ledger.userBorrowPoints(bob)
    gp_final = ledger.globalBorrowPoints()
    
    assert up_final.points == 0
    assert gp_final.points == 0


