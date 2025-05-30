import pytest
import boa

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS, MAX_UINT256


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
    mission_control_gov,
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
    lootbox.pause(True, sender=mission_control_gov.address)
    with boa.reverts("contract paused"):
        lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Unpause and verify it works
    lootbox.pause(False, sender=mission_control_gov.address)
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